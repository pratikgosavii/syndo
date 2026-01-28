from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Order


@receiver(pre_save, sender=Order)
def set_delivery_date_on_completed(sender, instance: Order, **kwargs):
    """
    Whenever an order is marked as delivered/completed (status -> 'completed'),
    automatically store the delivery date/time in Order.delivery_date.
    """
    # New orders (no pk yet): nothing to compare against
    if instance.pk is None:
        return

    try:
        old = Order.objects.get(pk=instance.pk)
    except Order.DoesNotExist:
        return

    # Transition to completed from any other status
    if old.status != "completed" and instance.status == "completed":
        # Only set once (don't overwrite if already set)
        if not instance.delivery_date:
            instance.delivery_date = timezone.now()

