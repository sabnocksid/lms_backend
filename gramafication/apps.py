from django.apps import AppConfig


class GramaficationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gramafication'


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'

    def ready(self):
        import gramafication.signals