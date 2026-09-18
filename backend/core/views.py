import json
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import translation
from .geo import SUPPORTED, country_from_request

@require_GET
def geo_language_debug(request):
    lang = getattr(request, 'LANGUAGE_CODE', translation.get_language() or settings.LANGUAGE_CODE)
    source = getattr(request, 'language_source', 'unknown')
    country = None
    if getattr(settings, 'TRUST_COUNTRY_HEADER', False):
        country = country_from_request(request)
    return JsonResponse({
        'detected': lang[:2] if lang else lang,
        'source': source,
        'country': country,
        'supported': list(SUPPORTED),
        'accept_language': request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
        'cookie': request.COOKIES.get(getattr(settings, 'LANGUAGE_COOKIE_NAME', 'rivin_lang')),
    })

@csrf_exempt
@require_POST
def set_language_api(request):
    try:
        data = json.loads(request.body.decode() or '{}') if request.body else {}
    except Exception:
        data = {}
    lang = data.get('lang') or request.POST.get('lang') or request.GET.get('lang')
    if lang not in SUPPORTED:
        return JsonResponse({'error': f'lang must be one of {SUPPORTED}'}, status=400)
    translation.activate(lang)
    resp = JsonResponse({'ok': True, 'lang': lang, 'dir': 'rtl' if lang == 'ar' else 'ltr'})
    resp.set_cookie(
        getattr(settings, 'LANGUAGE_COOKIE_NAME', 'rivin_lang'), lang,
        max_age=getattr(settings, 'LANGUAGE_COOKIE_AGE', 365*24*3600),
        samesite=getattr(settings, 'LANGUAGE_COOKIE_SAMESITE', 'Lax'),
        httponly=getattr(settings, 'LANGUAGE_COOKIE_HTTPONLY', False),
    )
    resp['Content-Language'] = lang
    return resp
