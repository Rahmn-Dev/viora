from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
import time
import uuid
import requests
import base64
import os
from datetime import timedelta
from django.utils import timezone
from .models import WatchHistory, Watchlist, VIPSubscription


def get_user_subscription_payload(user):
    """Ambil data VIP Subscription langsung dari Database Django & Xendit Invoice."""
    # 👑 Rule 1: Admin / Staff / Superuser di Database
    if user.is_staff or user.is_superuser:
        return {
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email or f"{user.username}@viora.stream",
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'is_active': user.is_active,
            'vip_plan': 'admin',
            'vip_expiry': 'Lifetime Access (Forever)',
            'invoice_no': 'VIORA-ADMIN-LIFETIME-ACCESS',
            'payment_status': 'PAID & VERIFIED',
            'payment_gateway': 'System Developer Pass',
            'payment_date': 'Lifetime Granted'
        }
    
    # ⭐ Rule 2: Cek Catatan VIPSubscription di DB
    try:
        sub = user.vip_subscription
        
        # Check Expiration Logic
        if sub.valid_until and timezone.now() > sub.valid_until:
            sub.status = 'EXPIRED'
            sub.plan = 'none'
            sub.save()

        return {
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email or f"{user.username}@viora.stream",
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'is_active': user.is_active,
            'vip_plan': sub.plan,
            'vip_expiry': sub.valid_until.strftime("%b %d, %Y %H:%M") if sub.valid_until else "No Active Subscription",
            'invoice_no': sub.invoice_no,
            'checkout_token': sub.checkout_token,
            'reference_id': f"viora-vip-{sub.plan}-{int(sub.created_at.timestamp())}",
            'payment_status': sub.status,
            'payment_gateway': sub.payment_gateway,
            'payment_date': sub.created_at.strftime("%b %d, %Y") if hasattr(sub.created_at, 'strftime') else str(sub.created_at)
        }
    except Exception:
        # 🔒 Rule 3: Pengguna Tanpa Pembayaran / Belum Bayar
        return {
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email or f"{user.username}@viora.stream",
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'is_active': user.is_active,
            'vip_plan': 'none',
            'vip_expiry': 'No Active Subscription',
            'invoice_no': '',
            'payment_status': 'UNPAID',
            'payment_gateway': 'N/A',
            'payment_date': 'Payment Required'
        }


@api_view(['POST'])
@ensure_csrf_cookie
@throttle_classes([AnonRateThrottle, UserRateThrottle])
@permission_classes([AllowAny])
def api_login(request):
    """Login using username/email + password with Django session auth."""
    identifier = request.data.get('username') or request.data.get('email') or ''
    password = request.data.get('password') or ''

    if not identifier or not password:
        return Response({'detail': 'Username/Email and Password are required.'}, status=400)

    # Try authenticating via username first, then fallback to email
    user = authenticate(request, username=identifier, password=password)
    if user is None:
        try:
            user_by_email = User.objects.get(email__iexact=identifier)
            user = authenticate(request, username=user_by_email.username, password=password)
        except User.DoesNotExist:
            pass

    if user is None:
        return Response({'detail': 'Invalid username/email or password.'}, status=400)

    if not user.is_active:
        return Response({'detail': 'This account has been deactivated by an administrator.'}, status=400)

    login(request, user)
    payload = get_user_subscription_payload(user)
    payload['csrf_token'] = get_token(request)
    return Response(payload)


@api_view(['POST'])
@ensure_csrf_cookie
@permission_classes([AllowAny])
def api_logout(request):
    """Logout session and issue fresh CSRF token."""
    logout(request)
    return Response({'detail': 'Logged out successfully.', 'csrf_token': get_token(request)})


@api_view(['GET'])
@ensure_csrf_cookie
@permission_classes([AllowAny])
def api_me(request):
    """Check session authentication status."""
    if request.user.is_authenticated:
        payload = get_user_subscription_payload(request.user)
        payload['csrf_token'] = get_token(request)
        return Response(payload)
    return Response({'detail': 'Not authenticated.', 'csrf_token': get_token(request)}, status=401)


@api_view(['POST'])
def api_update_profile(request):
    """Update User profile (First Name, Last Name, Email) in Django Database."""
    if not request.user.is_authenticated:
        return Response({'detail': 'Authentication required.'}, status=401)
    
    first_name = request.data.get('first_name', '').strip()
    last_name = request.data.get('last_name', '').strip()
    email = request.data.get('email', '').strip()

    user = request.user
    if first_name is not None:
        user.first_name = first_name
    if last_name is not None:
        user.last_name = last_name
    if email:
        user.email = email
    user.save()

    payload = get_user_subscription_payload(user)
    payload['detail'] = 'Profile updated successfully.'
    return Response(payload)


@api_view(['POST'])
def api_change_password(request):
    """Change or reset password securely in Django Database."""
    if not request.user.is_authenticated:
        return Response({'detail': 'Authentication required.'}, status=401)
    
    current_password = request.data.get('current_password', '')
    new_password = request.data.get('new_password', '')

    user = request.user
    if not user.check_password(current_password):
        return Response({'detail': 'Current password is incorrect.'}, status=400)

    if not new_password or len(new_password) < 6:
        return Response({'detail': 'New password must be at least 6 characters long.'}, status=400)

    user.set_password(new_password)
    user.save()
    login(request, user)

    return Response({'detail': 'Password successfully changed.'})


@api_view(['POST'])
def api_save_vip_subscription(request):
    """Save or update official VIP Subscription to Django Database."""
    if not request.user.is_authenticated:
        return Response({'detail': 'Authentication required.'}, status=401)
    
    plan = request.data.get('plan', 'annual')
    invoice_no = request.data.get('invoice_no', f"viora-vip-{plan}-{int(time.time())}")
    expiry_date = request.data.get('expiry_date', 'Aug 20, 2027')
    amount_paid = request.data.get('amount_paid', '$11.99 USD' if plan == 'annual' else '$1.99 USD')
    gateway = request.data.get('payment_gateway', 'Xendit Official Gateway')

    # Default to 365 days if no explicit date given
    if not expiry_date or expiry_date == 'Aug 20, 2027':
        calculated_expiry = timezone.now() + timedelta(days=365) if plan == 'annual' else timezone.now() + timedelta(days=30)
    else:
        calculated_expiry = timezone.now() + timedelta(days=365)

    sub, created = VIPSubscription.objects.update_or_create(
        user=request.user,
        defaults={
            'plan': plan,
            'invoice_no': invoice_no,
            'status': 'PAID',
            'payment_gateway': gateway,
            'amount_paid': amount_paid,
            'valid_until': calculated_expiry
        }
    )

    return Response({
        'detail': 'VIP Subscription successfully saved to database.',
        'subscription': {
            'plan': sub.plan,
            'invoice_no': sub.invoice_no,
            'status': sub.status,
            'valid_until': sub.valid_until
        }
    })


@api_view(['POST'])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
@permission_classes([AllowAny])
def api_register(request):
    """Register a new user account."""
    username = request.data.get('username', '').strip()
    email = request.data.get('email', '').strip()
    password = request.data.get('password', '')
    confirm = request.data.get('confirm_password', '')

    if not username or not password:
        return Response({'detail': 'Username and password are required.'}, status=400)
    if password != confirm:
        return Response({'detail': 'Passwords do not match.'}, status=400)
    if len(password) < 6:
        return Response({'detail': 'Password must be at least 6 characters long.'}, status=400)
    if User.objects.filter(username__iexact=username).exists():
        return Response({'detail': 'Username is already taken.'}, status=400)
    if email and User.objects.filter(email__iexact=email).exists():
        return Response({'detail': 'Email address is already registered.'}, status=400)

    user = User.objects.create_user(username=username, email=email, password=password)
    login(request, user)
    return Response({
        'username': user.username,
        'email': user.email,
        'csrf_token': get_token(request)
    }, status=201)


class UpdateWatchHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        histories = WatchHistory.objects.filter(user=request.user)

        data = [
            {
                "tmdb_id": item.tmdb_id,
                "media_type": item.media_type,
                "season": item.season,
                "episode": item.episode,
                "progress_percentage": item.progress_percentage,
                "current_time_seconds": item.current_time_seconds,
                "total_duration": item.total_duration,
                "is_finished": item.is_finished
            }
            for item in histories
        ]

        return Response(data)

    def post(self, request):
        print(request.data)

        tmdb_id = request.data.get('tmdb_id')
        media_type = request.data.get('media_type')
        progress = request.data.get('progress_percentage', 0.0)
        current_time = request.data.get('current_time_seconds', 0)
        duration = request.data.get('total_duration', None)
        season = request.data.get('season')
        episode = request.data.get('episode')

        is_finished = False
        if duration and current_time:
            is_finished = current_time >= duration * 0.95

        if not tmdb_id or not media_type:
            return Response(
                {'error': 'tmdb_id and media_type are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        history, created = WatchHistory.objects.update_or_create(
            user=request.user,
            tmdb_id=tmdb_id,
            media_type=media_type,
            defaults={
                'progress_percentage': progress,
                'season': season,
                'episode': episode,
                'current_time_seconds': current_time,
                'total_duration': duration,
                'is_finished': is_finished
            }
        )

        return Response({
            'message': 'Watch progress saved successfully!',
            'progress': history.progress_percentage
        }, status=status.HTTP_200_OK)

    def delete(self, request):
        tmdb_id = request.data.get('tmdb_id')
        media_type = request.data.get('media_type')

        WatchHistory.objects.filter(
            user=request.user,
            tmdb_id=tmdb_id,
            media_type=media_type
        ).delete()

        return Response({"status": "deleted"})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_watchlist(request):
    items = Watchlist.objects.filter(user=request.user)

    data = [
        {
            "id": item.tmdb_id,
            "media_type": item.media_type,
            "title": item.title,
            "poster_path": item.poster_path,
            "backdrop_path": item.backdrop_path,
            "vote_average": item.rating,
            "year": item.year
        }
        for item in items
    ]

    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_watchlist(request):
    user = request.user
    tmdb_id = request.data.get('tmdb_id')

    obj, created = Watchlist.objects.get_or_create(
        user=user,
        tmdb_id=tmdb_id,
        defaults={
            "media_type": request.data.get("media_type"),
            "title": request.data.get("title"),
            "poster_path": request.data.get("poster_path"),
            "backdrop_path": request.data.get("backdrop_path"),
            "rating": request.data.get("rating"),
            "year": request.data.get("year"),
        }
    )

    if not created:
        obj.delete()
        return Response({"status": "removed"})

    return Response({"status": "added"})


@api_view(['POST'])
@permission_classes([AllowAny])
def api_create_invoice(request):
    plan = request.data.get('plan', 'monthly')
    
    amount = 249000 if plan == 'annual' else 29000
    description = "Viora VIP 1-Year Pass" if plan == 'annual' else "Viora VIP Monthly Pass"
    
    xendit_key = os.environ.get('XENDIT_API_KEY', 'xnd_development_elq1dZXUsFhaHeIVOZUZopKMC8jcDV7mgBlMwYMWrqT1FdOnGBNJWQ8S4Y49V')
    
    external_id = f"viora-vip-{plan}-{int(time.time())}"
    
    auth_str = f"{xendit_key}:"
    b64_auth = base64.b64encode(auth_str.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {b64_auth}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'external_id': external_id,
        'amount': amount,
        'description': description,
        'invoice_duration': 86400,
        'currency': 'IDR'
    }
    
    resp = requests.post('https://api.xendit.co/v2/invoices', json=payload, headers=headers)
    
    if resp.status_code != 200:
        return Response({'detail': 'Failed to create invoice with Xendit'}, status=500)
        
    data = resp.json()
    invoice_no = data.get('id')
    invoice_url = data.get('invoice_url')
    
    # Generate secret checkout token
    checkout_token = str(uuid.uuid4())
    
    # Create PENDING VIP Subscription
    VIPSubscription.objects.create(
        user=None, # anonymous for now
        plan=plan,
        invoice_no=invoice_no,
        status='PENDING',
        payment_gateway='Xendit Official Gateway',
        amount_paid='$11.99 USD' if plan == 'annual' else '$1.99 USD',
        valid_until=timezone.now() + timedelta(days=365) if plan == 'annual' else timezone.now() + timedelta(days=30), 
        checkout_token=checkout_token,
        is_claimed=False
    )
    
    return Response({
        'invoice_id': invoice_no,
        'invoice_url': invoice_url,
        'checkout_token': checkout_token
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def api_check_invoice_status(request):
    invoice_id = request.data.get('invoice_id')
    checkout_token = request.data.get('checkout_token')
    
    try:
        sub = VIPSubscription.objects.get(invoice_no=invoice_id, checkout_token=checkout_token)
    except VIPSubscription.DoesNotExist:
        return Response({'detail': 'Invalid invoice or token'}, status=403)
        
    if sub.status == 'PAID':
        return Response({'status': 'PAID'})
        
    # Ask Xendit server-to-server
    xendit_key = os.environ.get('XENDIT_API_KEY', 'xnd_development_elq1dZXUsFhaHeIVOZUZopKMC8jcDV7mgBlMwYMWrqT1FdOnGBNJWQ8S4Y49V')
    auth_str = f"{xendit_key}:"
    b64_auth = base64.b64encode(auth_str.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {b64_auth}'
    }
    
    resp = requests.get(f'https://api.xendit.co/v2/invoices/{invoice_id}', headers=headers)
    
    if resp.status_code == 200:
        data = resp.json()
        xendit_status = data.get('status')
        if xendit_status in ['PAID', 'SETTLED']:
            sub.status = 'PAID'
            sub.save()
            return Response({'status': 'PAID'})
            
    return Response({'status': 'PENDING'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_link_invoice(request):
    invoice_id = request.data.get('invoice_id')
    checkout_token = request.data.get('checkout_token')
    
    try:
        sub = VIPSubscription.objects.get(invoice_no=invoice_id, checkout_token=checkout_token)
    except VIPSubscription.DoesNotExist:
        return Response({'detail': 'Invoice not found or invalid token'}, status=403)
        
    if sub.is_claimed:
        return Response({'detail': 'Invoice already claimed'}, status=403)
        
    if sub.status != 'PAID':
        return Response({'detail': 'Invoice not paid yet'}, status=400)
        
    # Remove any existing subscription for this user just in case (OneToOneField replacement logic)
    VIPSubscription.objects.filter(user=request.user).exclude(id=sub.id).delete()
    
    # Link it!
    sub.user = request.user
    sub.is_claimed = True
    sub.save()
    
    return Response({'detail': 'Invoice linked successfully'})
