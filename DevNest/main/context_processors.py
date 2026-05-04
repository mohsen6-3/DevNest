from .models import Notification


def notifications_context(request):
    if not getattr(request.user, 'is_authenticated', False):
        return {
            'unread_notifications': [],
            'unread_notifications_count': 0,
        }

    unread_qs = Notification.objects.filter(user=request.user, is_read=False)
    return {
        'unread_notifications': list(unread_qs[:8]),
        'unread_notifications_count': unread_qs.count(),
    }
