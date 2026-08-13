from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from .models import WatchHistory, Watchlist


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    """Login menggunakan username/email + password, pakai Django session."""
    identifier = request.data.get('username') or request.data.get('email') or ''
    password = request.data.get('password') or ''

    if not identifier or not password:
        return Response({'detail': 'Username dan password harus diisi.'}, status=400)

    # Coba login via username dulu, kalau gagal coba via email
    user = authenticate(request, username=identifier, password=password)
    if user is None:
        # Coba cari user berdasarkan email
        try:
            user_by_email = User.objects.get(email__iexact=identifier)
            user = authenticate(request, username=user_by_email.username, password=password)
        except User.DoesNotExist:
            pass

    if user is None:
        return Response({'detail': 'Username/email atau password salah.'}, status=400)

    if not user.is_active:
        return Response({'detail': 'Akun ini telah dinonaktifkan.'}, status=400)

    login(request, user)
    return Response({
        'username': user.username,
        'email': user.email,
        'is_staff': user.is_staff,
    })


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def api_logout(request):
    """Logout — hapus session."""
    logout(request)
    return Response({'detail': 'Logged out.'})


@api_view(['GET'])
@permission_classes([AllowAny])
def api_me(request):
    """Cek siapa yang sedang login berdasarkan session cookie."""
    if request.user.is_authenticated:
        return Response({
            'username': request.user.username,
            'email': request.user.email,
            'is_staff': request.user.is_staff,
        })
    return Response({'detail': 'Not authenticated.'}, status=401)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def api_register(request):
    """Registrasi akun baru."""
    username = request.data.get('username', '').strip()
    email = request.data.get('email', '').strip()
    password = request.data.get('password', '')
    confirm = request.data.get('confirm_password', '')

    if not username or not password:
        return Response({'detail': 'Username dan password harus diisi.'}, status=400)
    if password != confirm:
        return Response({'detail': 'Password tidak cocok.'}, status=400)
    if len(password) < 6:
        return Response({'detail': 'Password minimal 6 karakter.'}, status=400)
    if User.objects.filter(username__iexact=username).exists():
        return Response({'detail': 'Username sudah digunakan.'}, status=400)
    if email and User.objects.filter(email__iexact=email).exists():
        return Response({'detail': 'Email sudah terdaftar.'}, status=400)

    user = User.objects.create_user(username=username, email=email, password=password)
    login(request, user)
    return Response({
        'username': user.username,
        'email': user.email,
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
