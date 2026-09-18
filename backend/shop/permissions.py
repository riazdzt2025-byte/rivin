from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

DEFAULT_GROUPS = {
    "ShopAdmin":  "__all__",
    "Catalog":    ["category", "product", "stockmovement"],
    "OrderDesk":  ["order", "orderitem", "orderstatushistory", "customer", "review"],
    "Accounts":   ["order", "coupon", "deliveryzone"],
    "Delivery":   ["order", "orderstatushistory"],
}

def ensure_default_groups(sender, **kwargs):
    for name, models in DEFAULT_GROUPS.items():
        group, created = Group.objects.get_or_create(name=name)
        if models == "__all__":
            # ShopAdmin: all shop + core perms
            cts = ContentType.objects.filter(app_label__in=["shop", "core"])
            perms = Permission.objects.filter(content_type__in=cts)
            group.permissions.set(perms)
        else:
            cts = ContentType.objects.filter(app_label="shop", model__in=models)
            perms = Permission.objects.filter(content_type__in=cts)
            # add without removing existing
            group.permissions.add(*perms)
