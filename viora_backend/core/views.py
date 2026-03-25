from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from .models import WatchHistory # Sesuaikan dengan nama file models-mu
from .models import Watchlist

class UpdateWatchHistoryView(APIView):
    # Wajib login agar kita tahu siapa usernya dari Token JWT
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print(request.data)
        # Ambil data yang dikirim dari Vue
        tmdb_id = request.data.get('tmdb_id')
        media_type = request.data.get('media_type')
        progress = request.data.get('progress_percentage', 0.0)

        # Validasi sederhana
        if not tmdb_id or not media_type:
            return Response(
                {'error': 'tmdb_id and media_type are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Logika Inti: Kalau belum pernah nonton, buat baru (Create).
        # Kalau sudah pernah nonton, update progress-nya (Update).
        history, created = WatchHistory.objects.update_or_create(
            user=request.user,
            tmdb_id=tmdb_id,
            media_type=media_type,
            defaults={'progress_percentage': progress}
        )

        return Response({
            'message': 'Watch progress saved successfully!',
            'progress': history.progress_percentage
        }, status=status.HTTP_200_OK)

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