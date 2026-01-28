from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import OrderItem


@receiver(pre_save, sender=OrderItem)
def set_item_delivery_date_on_delivered(sender, instance: OrderItem, **kwargs):
    """
    Whenever an OrderItem is marked as delivered (status -> 'delivered'),
    automatically store the delivery date/time in OrderItem.delivery_date.
    """
    # New items: nothing to compare against
    if instance.pk is None:
        return

    try:
        old = OrderItem.objects.get(pk=instance.pk)
    except OrderItem.DoesNotExist:
        return

    # Transition to delivered from any other status
    if old.status != "delivered" and instance.status == "delivered":
        # Only set once (don't overwrite if already set)
        if not instance.delivery_date:
            instance.delivery_date = timezone.now()

