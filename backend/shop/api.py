"""
JSON API — PROMPT section 7. No DRF, plain Django.
Language-aware: ?lang= or Accept-Language, returns dir + localized name.
"""
import json
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import translation
from django.core.cache import cache
from django.conf import settings
from django.db import transaction
from .models import Category, Product, Order, OrderItem, Customer, Coupon, SiteSetting, Review

def _lang(request):
    lang = request.GET.get('lang')
    if lang in ('bn','en','ar'):
        return lang
    cur = translation.get_language() or settings.LANGUAGE_CODE
    return cur[:2] if cur else 'bn'

def _dir(lang):
    return 'rtl' if lang == 'ar' else 'ltr'

def _serialize_category(c, lang):
    return {
        'code': c.code,
        'name': c.display_name(lang),
        'name_bn': c.name_bn, 'name_en': c.name_en, 'name_ar': c.name_ar,
        'emoji': c.emoji,
        'dir': _dir(lang), 'lang': lang,
    }

def _serialize_product(p, lang):
    return {
        'sku': p.sku,
        'name': p.display_name(lang),
        'name_bn': p.name_bn, 'name_en': p.name_en, 'name_ar': p.name_ar,
        'category': p.category.code if p.category_id else None,
        'price': str(p.price),
        'mrp': str(p.mrp) if p.mrp is not None else None,
        'stock': p.stock,
        'emoji': p.emoji,
        'image': p.image.url if p.image else None,
        'link': p.link,
        'is_bestseller': p.is_bestseller,
        'is_active': p.is_active,
        'dir': _dir(lang), 'lang': lang,
    }

def models_Q_name(q):
    from django.db.models import Q
    return Q(name_bn__icontains=q) | Q(name_en__icontains=q) | Q(name_ar__icontains=q) | Q(sku__icontains=q)

@require_GET
def categories_api(request):
    lang = _lang(request)
    qs = Category.objects.filter(is_active=True).order_by('sort_order','name_bn')
    return JsonResponse({'categories': [_serialize_category(c, lang) for c in qs], 'lang': lang, 'dir': _dir(lang)})

@require_GET
def products_api(request):
    lang = _lang(request)
    qs = Product.objects.filter(is_active=True).select_related('category')
    q = request.GET.get('q')
    cat = request.GET.get('category')
    best = request.GET.get('is_bestseller')
    if cat:
        qs = qs.filter(category__code=cat)
    if best in ('1','true','yes'):
        qs = qs.filter(is_bestseller=True)
    if q:
        qs = qs.filter(models_Q_name(q))
    qs = qs.order_by('sort_order','name_bn')[:200]
    return JsonResponse({'products': [_serialize_product(p, lang) for p in qs], 'lang': lang, 'dir': _dir(lang)})

@require_GET
def product_detail_api(request, sku):
    lang = _lang(request)
    try:
        p = Product.objects.select_related('category').get(sku=sku, is_active=True)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'not found'}, status=404)
    return JsonResponse({'product': _serialize_product(p, lang), 'lang': lang, 'dir': _dir(lang)})

@require_GET
def settings_api(request):
    s = SiteSetting.get_solo()
    lang = _lang(request)
    best = [_serialize_product(p, lang) for p in s.bestsellers.filter(is_active=True)[:8]]
    return JsonResponse({
        'delivery_charge': str(s.delivery_charge),
        'min_order': str(s.min_order),
        'theme': s.theme,
        'bestsellers': best,
        'lang': lang, 'dir': _dir(lang),
    })

def _rate_limited(request):
    ip = request.META.get('REMOTE_ADDR','unknown')
    key = f'rivin:order:{ip}'
    count = cache.get(key, 0)
    limit = getattr(settings, 'RIVIN_ORDER_RATE_LIMIT', 5)
    window = getattr(settings, 'RIVIN_ORDER_RATE_WINDOW', 600)
    if count >= limit:
        return True
    cache.set(key, count+1, timeout=window)
    return False

@csrf_exempt
@require_POST
def create_order_api(request):
    # rate limit
    try:
        if _rate_limited(request):
            return JsonResponse({'error': 'Too many orders, try again later.'}, status=429)
    except Exception:
        pass  # cache not configured -> skip

    try:
        data = json.loads(request.body.decode() or '{}')
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    cust_data = data.get('customer') or {}
    name = (cust_data.get('name') or '').strip()
    mobile = (cust_data.get('mobile') or '').strip()
    address = (cust_data.get('address') or '').strip()
    if not name or not mobile:
        return JsonResponse({'error': 'name and mobile required'}, status=400)

    items = data.get('items') or []
    if not items:
        return JsonResponse({'error': 'items required'}, status=400)

    coupon_code = (data.get('coupon_code') or '').strip()
    # fetch products
    skus = [ (it.get('sku') or '').strip() for it in items ]
    prods = {p.sku: p for p in Product.objects.filter(sku__in=skus, is_active=True)}
    # validate
    subtotal = Decimal('0.00')
    order_items_data = []
    for it in items:
        sku = (it.get('sku') or '').strip()
        qty = int(it.get('qty') or 1)
        if qty < 1:
            return JsonResponse({'error': f'Invalid qty for {sku}'}, status=400)
        p = prods.get(sku)
        if not p:
            return JsonResponse({'error': f'Product not found: {sku}'}, status=400)
        if p.stock < qty:
            return JsonResponse({'error': f'Out of stock: {p.display_name()} (stock {p.stock})'}, status=400)
        line = p.price * qty
        subtotal += line
        order_items_data.append((p, qty, line))

    # delivery & coupon
    site = SiteSetting.get_solo()
    delivery_fee = site.delivery_charge
    discount = Decimal('0.00')
    coupon = None
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code__iexact=coupon_code)
            if coupon.is_valid_for(subtotal):
                discount = coupon.discount_for(subtotal)
            else:
                return JsonResponse({'error': 'Invalid or expired coupon'}, status=400)
        except Coupon.DoesNotExist:
            return JsonResponse({'error': 'Invalid coupon code'}, status=400)

    if subtotal < site.min_order:
        return JsonResponse({'error': f'Minimum order ৳{site.min_order} not met (subtotal ৳{subtotal})'}, status=400)

    # create
    with transaction.atomic():
        cust, _ = Customer.objects.get_or_create(
            mobile=mobile,
            defaults={'name': name, 'address': address, 'preferred_language': _lang(request)}
        )
        # update name/address if changed
        if cust.name != name or cust.address != address:
            cust.name = name
            if address:
                cust.address = address
            cust.save(update_fields=['name','address','updated_at'] if hasattr(cust,'updated_at') else ['name','address'])

        order = Order(
            customer=cust,
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            discount=discount,
            coupon_code=coupon.code if coupon else '',
            payment_method=data.get('payment_method','cod'),
        )
        order.save()  # generates order_no

        for p, qty, line in order_items_data:
            OrderItem.objects.create(
                order=order, product=p,
                product_name_snapshot={'bn': p.name_bn, 'en': p.name_en, 'ar': p.name_ar},
                unit_price_snapshot=p.price, qty=qty,
            )
            # decrement stock + movement
            p.stock -= qty
            p.save(update_fields=['stock','updated_at'])
            from .models import StockMovement
            StockMovement.objects.create(product=p, delta=-qty, reason=f'order {order.order_no}')

        if coupon:
            coupon.used_count = (coupon.used_count or 0) + 1
            coupon.save(update_fields=['used_count'])

    return JsonResponse({
        'ok': True,
        'order_no': order.order_no,
        'total': str(order.total),
        'subtotal': str(order.subtotal),
        'delivery_fee': str(order.delivery_fee),
        'discount': str(order.discount),
        'status': order.status,
    }, status=201)

@require_GET
def order_detail_api(request, order_no):
    lang = _lang(request)
    try:
        o = Order.objects.select_related('customer').prefetch_related('items__product','history').get(order_no=order_no)
    except Order.DoesNotExist:
        return JsonResponse({'error': 'not found'}, status=404)
    items = []
    for it in o.items.all():
        items.append({
            'sku': it.product.sku,
            'name': it.display_name(lang),
            'name_snapshot': it.product_name_snapshot,
            'qty': it.qty,
            'unit_price': str(it.unit_price_snapshot),
            'line_total': str(it.line_total),
        })
    hist = [{'from': h.from_status, 'to': h.to_status, 'note': h.note, 'at': h.at.isoformat()} for h in o.history.all()]
    return JsonResponse({
        'order_no': o.order_no,
        'status': o.status,
        'customer': {'name': o.customer.name, 'mobile': o.customer.mobile, 'address': o.customer.address},
        'subtotal': str(o.subtotal), 'delivery_fee': str(o.delivery_fee), 'discount': str(o.discount), 'total': str(o.total),
        'payment_method': o.payment_method, 'payment_status': o.payment_status,
        'coupon_code': o.coupon_code,
        'items': items,
        'history': hist,
        'ordered_at': o.ordered_at.isoformat(),
        'lang': lang, 'dir': _dir(lang),
    })

@require_GET
def my_orders_api(request):
    mobile = (request.GET.get('mobile') or '').strip()
    if not mobile:
        return JsonResponse({'error': 'mobile required'}, status=400)
    qs = Order.objects.filter(customer__mobile=mobile).order_by('-ordered_at')[:20]
    return JsonResponse({'orders': [{'order_no': o.order_no, 'status': o.status, 'total': str(o.total), 'ordered_at': o.ordered_at.isoformat()} for o in qs]})

@csrf_exempt
@require_POST
def review_api(request, order_no):
    try:
        o = Order.objects.get(order_no=order_no)
    except Order.DoesNotExist:
        return JsonResponse({'error': 'order not found'}, status=404)
    try:
        data = json.loads(request.body.decode() or '{}')
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    rating = int(data.get('rating') or 0)
    if rating < 1 or rating > 5:
        return JsonResponse({'error': 'rating 1-5 required'}, status=400)
    comment = (data.get('comment') or '').strip()
    emoji = (data.get('emoji') or '⭐').strip()[:4]
    # find customer from order
    Review.objects.create(order=o, product=None, customer=o.customer, rating=rating, emoji=emoji, comment=comment)
    return JsonResponse({'ok': True})
