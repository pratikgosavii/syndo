from .models import VendorNotification


def header_notifications(request):
    """Add recent notifications and unread count for the header dropdown (vendor dashboard)."""
    if request.user.is_authenticated:
        notifications = VendorNotification.objects.filter(user=request.user).order_by("-created_at")[:10]
        unread_count = VendorNotification.objects.filter(user=request.user, is_read=False).count()
        return {
            "header_notifications": notifications,
            "header_notification_count": unread_count,
        }
    return {
        "header_notifications": [],
        "header_notification_count": 0,
    }
