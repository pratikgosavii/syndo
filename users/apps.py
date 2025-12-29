from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        # Register user-related signals (e.g., seed default expense categories for new vendors)
        import users.signals  # noqa: F401
