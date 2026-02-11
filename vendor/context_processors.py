from .models import VendorNotification, CompanyProfile


def header_notifications(request):
    """Add recent notifications and unread count for the header dropdown (vendor dashboard)."""
    if request.user.is_authenticated:
        notifications = VendorNotification.objects.filter(user=request.user).order_by("-created_at")[:10]
        unread_count = VendorNotification.objects.filter(user=request.user, is_read=False).count()
        # Company profile image for header avatar (same as company profile page)
        try:
            company_profile = CompanyProfile.objects.get(user=request.user)
            header_profile_image = company_profile.profile_image if company_profile.profile_image else None
        except CompanyProfile.DoesNotExist:
            header_profile_image = None
        return {
            "header_notifications": notifications,
            "header_notification_count": unread_count,
            "header_profile_image": header_profile_image,
        }
    return {
        "header_notifications": [],
        "header_notification_count": 0,
        "header_profile_image": None,
    }
