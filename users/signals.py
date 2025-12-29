from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from masters.models import expense_category
from users.models import User


DEFAULT_EXPENSE_CATEGORIES = [
    "Salary",
    "Employee Expenses",
    "Stationery",
    "Operational",
    "Commission",
    "Rent",
    "Utility bills",
    "Marketing & ads",
    "Transport",
    "Travel",
    "Tax",
    "Professional charges",
    "Software",
    "Banking & Finance",
    "Assets",
    "Maintenance",
    "Miscellaneous",
]


@receiver(pre_save, sender=User)
def _track_previous_vendor_flag(sender, instance: User, **kwargs):
    """
    Track prior is_vendor so we can detect when a user becomes a vendor.
    We avoid re-creating categories on unrelated saves (or after a vendor deletes categories).
    """
    if not instance.pk:
        instance._was_vendor = False
        return
    try:
        old = sender.objects.get(pk=instance.pk)
        instance._was_vendor = bool(getattr(old, "is_vendor", False))
    except sender.DoesNotExist:
        instance._was_vendor = False


@receiver(post_save, sender=User)
def create_default_expense_categories_for_new_vendor(sender, instance: User, created: bool, **kwargs):
    """
    When a user is created as a vendor, or toggled into vendor role,
    create a default set of expense categories for that vendor.
    """
    became_vendor = bool(getattr(instance, "is_vendor", False)) and (created or not getattr(instance, "_was_vendor", False))
    if not became_vendor:
        return

    for name in DEFAULT_EXPENSE_CATEGORIES:
        expense_category.objects.get_or_create(user=instance, name=name)


