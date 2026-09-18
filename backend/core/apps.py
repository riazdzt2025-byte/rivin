from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core (i18n / geo)'

    def ready(self):
        # Register system checks
        from . import checks  # noqa
