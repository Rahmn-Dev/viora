from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from .models import WatchHistory # Sesuaikan dengan nama file models-mu
from .models import Watchlist

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

