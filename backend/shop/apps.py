from django.apps import AppConfig

class ShopConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shop'
    verbose_name = 'RIVIN Shop'

    def ready(self):
        # connect post_migrate to create groups
        from django.db.models.signals import post_migrate
        from .permissions import ensure_default_groups
        post_migrate.connect(ensure_default_groups, sender=self)
