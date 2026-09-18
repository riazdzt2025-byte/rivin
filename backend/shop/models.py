"""
RIVIN shop models — 12 models, trilingual, state-machine, collision-safe order_no.
Mirrors school-management-system patterns: receipt_no, status history, AuditLog.
"""
from __future__ import annotations
import secrets
from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.db import models, transaction, IntegrityError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# ---------- helpers ----------

MONEY_VALIDATORS = [MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('99999999.99'))]
MAX_IMAGE_BYTES = 2 * 1024 * 1024

def money_field(verbose_name=None, **kwargs):
    kwargs.setdefault('max_digits', 10)
    kwargs.setdefault('decimal_places', 2)
    kwargs.setdefault('validators', MONEY_VALIDATORS)
    kwargs.setdefault('default', Decimal('0.00'))
    if verbose_name is not None:
        return models.DecimalField(verbose_name, **kwargs)
    return models.DecimalField(**kwargs)

def validate_product_image(value):
    if value and hasattr(value, 'size') and value.size and value.size > MAX_IMAGE_BYTES:
        raise ValidationError(_('Image must be ≤ 2 MB.'))

def _display_name_for(obj, lang: str | None) -> str:
    """Pick name_bn/en/ar with fallback to bn."""
    if not lang:
        from django.utils.translation import get_language
        lang = (get_language() or settings.LANGUAGE_CODE or 'bn')[:2]
    else:
        lang = lang[:2].lower()
    if lang not in ('bn', 'en', 'ar'):
        lang = 'bn'
    field = f'name_{lang}'
    val = getattr(obj, field, '') or ''
    val = val.strip()
    if val:
        return val
    # fallback chain bn -> en -> ar
    for fb in ('bn', 'en', 'ar'):
        v = (getattr(obj, f'name_{fb}', '') or '').strip()
        if v:
            return v
    return ''

class TrilingualNameMixin(models.Model):
    name_bn = models.CharField(_('name (BN)'), max_length=200)
    name_en = models.CharField(_('name (EN)'), max_length=200, blank=True)
    name_ar = models.CharField(_('name (AR)'), max_length=200, blank=True)

    class Meta:
        abstract = True

    def display_name(self, lang: str | None = None) -> str:
        return _display_name_for(self, lang)

# ---------- Category ----------

class Category(TrilingualNameMixin):
    code = models.SlugField(_('code'), max_length=50, unique=True, help_text=_('e.g. stationery'))
    emoji = models.CharField(_('emoji'), max_length=10, blank=True, default='📦')
    sort_order = models.IntegerField(_('sort order'), default=0)
    is_active = models.BooleanField(_('active'), default=True)

    class Meta:
        ordering = ['sort_order', 'name_bn']
        verbose_name_plural = _('categories')

    def __str__(self):
        return self.display_name() or self.code

# ---------- Product ----------

class Product(TrilingualNameMixin):
    sku = models.SlugField(_('SKU'), max_length=50, unique=True, db_index=True, help_text=_('unique, e.g. rivin-0001'))
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products', verbose_name=_('category'))
    price = money_field(_('price'))
    mrp = money_field(_('MRP'), blank=True, null=True, help_text=_('compare-at price'))
    stock = models.IntegerField(_('stock'), default=0, validators=[MinValueValidator(0)])
    emoji = models.CharField(_('emoji'), max_length=10, blank=True, default='🛍️')
    image = models.ImageField(_('image'), upload_to='products/%Y/%m/', blank=True, null=True, validators=[validate_product_image])
    link = models.URLField(_('external link'), blank=True)
    is_active = models.BooleanField(_('active'), default=True)
    is_bestseller = models.BooleanField(_('bestseller'), default=False)
    sort_order = models.IntegerField(_('sort order'), default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'name_bn']

    def __str__(self):
        return f'{self.sku} — {self.display_name()}'

    def clean(self):
        super().clean()
        if self.mrp is not None and self.mrp < self.price:
            # allow mrp < price? keep warning not error; but enforce mrp >=0 done by validator
            pass

# ---------- Customer ----------

mobile_validator = RegexValidator(r'^[0-9+\-\s]{7,20}$', _('Enter a valid mobile number.'))

class Customer(models.Model):
    name = models.CharField(_('name'), max_length=120)
    mobile = models.CharField(_('mobile'), max_length=20, db_index=True, validators=[mobile_validator])
    email = models.EmailField(_('email'), blank=True)
    address = models.TextField(_('address'), blank=True)
    preferred_language = models.CharField(_('preferred language'), max_length=5, choices=[('bn','বাংলা'),('en','English'),('ar','العربية')], default='bn')
    country_code = models.CharField(_('country'), max_length=2, blank=True, help_text=_('ISO2, e.g. BD'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['mobile'])]

    def __str__(self):
        return f'{self.name} ({self.mobile})'

# ---------- Order ----------

class InvalidOrderTransition(Exception):
    pass

class Order(models.Model):
    PLACED = 'placed'
    CONFIRMED = 'confirmed'
    PACKED = 'packed'
    OUT_FOR_DELIVERY = 'out_for_delivery'
    DELIVERED = 'delivered'
    CANCELLED = 'cancelled'
    RETURNED = 'returned'

    STATUS_CHOICES = [
        (PLACED, _('Placed')),
        (CONFIRMED, _('Confirmed')),
        (PACKED, _('Packed')),
        (OUT_FOR_DELIVERY, _('Out for delivery')),
        (DELIVERED, _('Delivered')),
        (CANCELLED, _('Cancelled')),
        (RETURNED, _('Returned')),
    ]

    ALLOWED_TRANSITIONS = {
        PLACED: {CONFIRMED, CANCELLED},
        CONFIRMED: {PACKED, CANCELLED},
        PACKED: {OUT_FOR_DELIVERY, CANCELLED},
        OUT_FOR_DELIVERY: {DELIVERED, CANCELLED},
        DELIVERED: {RETURNED},
        CANCELLED: set(),
        RETURNED: set(),
    }

    order_no = models.CharField(_('order no'), max_length=32, unique=True, editable=False, db_index=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='orders')
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default=PLACED, db_index=True)
    subtotal = money_field(_('subtotal'))
    delivery_fee = money_field(_('delivery fee'))
    discount = money_field(_('discount'))
    total = money_field(_('total'))
    payment_method = models.CharField(_('payment method'), max_length=20, default='cod', choices=[('cod','COD'),('bkash','bKash'),('nagad','Nagad'),('card','Card')])
    payment_status = models.CharField(_('payment status'), max_length=20, default='unpaid', choices=[('unpaid','Unpaid'),('paid','Paid'),('failed','Failed')])
    coupon_code = models.CharField(_('coupon'), max_length=30, blank=True)
    notes = models.TextField(_('notes'), blank=True)
    ordered_at = models.DateTimeField(_('ordered at'), default=timezone.now)
    delivered_at = models.DateTimeField(_('delivered at'), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ['-ordered_at', '-created_at']

    def __str__(self):
        return self.order_no

    def _generate_order_no(self) -> str:
        year = timezone.now().year
        prefix = f'ORD-{year}-'
        # try sequential
        base_qs = Order.objects.filter(order_no__startswith=prefix)
        # count is cheap for sqlite; for postgres we still use count (low volume)
        nxt = base_qs.count() + 1
        for offset in range(25):
            cand = f'{prefix}{nxt + offset:06d}'
            if not base_qs.filter(order_no=cand).exists():
                return cand
        # fallback random
        return f'{prefix}{secrets.token_hex(4).upper()}'

    def save(self, *args, **kwargs):
        # keep total consistent (must be before any early return)
        self.total = (self.subtotal or Decimal('0')) + (self.delivery_fee or Decimal('0')) - (self.discount or Decimal('0'))
        if self.total < 0:
            self.total = Decimal('0')
        if not self.order_no:
            # collision-safe: retry on IntegrityError
            for _ in range(5):
                self.order_no = self._generate_order_no()
                try:
                    with transaction.atomic():
                        return super().save(*args, **kwargs)
                except IntegrityError:
                    continue
            # last try random
            self.order_no = f'ORD-{timezone.now().year}-{secrets.token_hex(4).upper()}'
        return super().save(*args, **kwargs)

    def transition_to(self, new_status: str, *, actor=None, note: str = ''):
        if new_status == self.status:
            raise InvalidOrderTransition(_('Already in this status.'))
        allowed = self.ALLOWED_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise InvalidOrderTransition(_(f'Cannot go from {self.status} to {new_status}.'))
        old = self.status
        self.status = new_status
        if new_status == self.DELIVERED and not self.delivered_at:
            self.delivered_at = timezone.now()
        self.save(update_fields=['status','delivered_at','updated_at'])
        OrderStatusHistory.objects.create(order=self, from_status=old, to_status=new_status, changed_by=actor, note=note)
        return self

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items')
    product_name_snapshot = models.JSONField(_('name snapshot'), default=dict, help_text=_('{"bn": "...", "en": "...", "ar": "..."}'))
    unit_price_snapshot = money_field(_('unit price snapshot'))
    qty = models.PositiveIntegerField(_('qty'), validators=[MinValueValidator(1)])
    line_total = money_field(_('line total'))

    def save(self, *args, **kwargs):
        if not self.product_name_snapshot:
            self.product_name_snapshot = {
                'bn': self.product.name_bn,
                'en': self.product.name_en,
                'ar': self.product.name_ar,
            }
        self.line_total = (self.unit_price_snapshot or Decimal('0')) * self.qty
        super().save(*args, **kwargs)

    def display_name(self, lang=None):
        if isinstance(self.product_name_snapshot, dict):
            lang = (lang or 'bn')[:2]
            return self.product_name_snapshot.get(lang) or self.product_name_snapshot.get('bn') or ''
        return str(self.product)

class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='history')
    from_status = models.CharField(max_length=20)
    to_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    note = models.CharField(max_length=300, blank=True)
    at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['at']

# ---------- Stock / Audit / Review / Zone / Coupon / SiteSetting ----------

class StockMovement(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_movements')
    delta = models.IntegerField(_('delta'), help_text=_('positive = in, negative = out'))
    reason = models.CharField(_('reason'), max_length=200, blank=True)
    at = models.DateTimeField(auto_now_add=True)
    by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ['-at']

class AuditLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=50)  # create/update/transition
    object_type = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    changed_fields = models.JSONField(default=dict, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-at']

class Review(models.Model):
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.CASCADE, related_name='reviews')
    order = models.ForeignKey(Order, null=True, blank=True, on_delete=models.CASCADE, related_name='reviews')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    emoji = models.CharField(max_length=10, blank=True, default='⭐')
    comment = models.TextField(blank=True)
    at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-at']

class DeliveryZone(models.Model):
    name = models.CharField(max_length=100, unique=True)
    charge = money_field(_('charge'))
    min_order = money_field(_('min order'))
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Coupon(models.Model):
    PERCENT = 'percent'
    FIXED = 'fixed'
    TYPE_CHOICES = [(PERCENT, _('Percent')), (FIXED, _('Fixed'))]
    code = models.CharField(max_length=30, unique=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=PERCENT)
    value = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)
    min_subtotal = money_field(_('min subtotal'), default=Decimal('0.00'))
    usage_limit = models.PositiveIntegerField(null=True, blank=True, help_text=_('null = unlimited'))
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code

    def is_valid_for(self, subtotal: Decimal) -> bool:
        now = timezone.now()
        if not self.is_active:
            return False
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_to and now > self.valid_to:
            return False
        if subtotal < (self.min_subtotal or Decimal('0')):
            return False
        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            return False
        return True

    def discount_for(self, subtotal: Decimal) -> Decimal:
        if not self.is_valid_for(subtotal):
            return Decimal('0.00')
        if self.type == self.PERCENT:
            return (subtotal * self.value / Decimal('100')).quantize(Decimal('0.01'))
        return min(self.value, subtotal)

class SiteSetting(models.Model):
    """Singleton-ish. PK=1 is canonical."""
    delivery_charge = money_field(_('default delivery charge'), default=Decimal('60.00'))
    min_order = money_field(_('min order'), default=Decimal('300.00'))
    bestsellers = models.ManyToManyField(Product, blank=True, related_name='bestseller_in')
    theme = models.CharField(max_length=50, default='light')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return 'SiteSetting'

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
