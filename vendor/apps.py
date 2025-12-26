from django.apps import AppConfig


class VendorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vendor'


    def ready(self):
        import vendor.signals
        # Verify signal is registered
        from django.db.models.signals import post_save
        from vendor.models import Purchase
        try:
            receivers = post_save._live_receivers(sender=Purchase)
            print(f"[VENDOR_APPS] Purchase signal receivers: {len(receivers)}")
            for receiver in receivers:
                print(f"[VENDOR_APPS] Receiver: {receiver.__name__ if hasattr(receiver, '__name__') else receiver}")
        except Exception as e:
            print(f"[VENDOR_APPS] Error checking signal registration: {e}")
