"""
LanguageDetectionMiddleware — PROMPT section 3 priority chain.
Must be AFTER LocaleMiddleware so explicit cookie/?lang wins over auto.

Order:
  1. ?lang=bn|en|ar  -> activate + set cookie (sticky, 1y)
  2. rivin_lang cookie already present -> LocaleMiddleware already activated; we just annotate source
  3. (if TRUST_COUNTRY_HEADER) CDN country header -> activate
  4. Accept-Language -> activate
  5. DEFAULT_LANGUAGE -> activate

Sets request.language_source for /api/v1/geo/language/ debug.
"""
from django.conf import settings
from django.utils import translation
from .geo import (
    SUPPORTED, DEFAULT_LANGUAGE,
    language_for_country, language_from_accept_language, country_from_request,
)

class LanguageDetectionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.cookie_name = getattr(settings, 'LANGUAGE_COOKIE_NAME', 'rivin_lang')

    def __call__(self, request):
        # 1. ?lang= override — highest priority
        wanted = request.GET.get('lang')
        if wanted in SUPPORTED:
            source = 'query-param'
            translation.activate(wanted)
            request.LANGUAGE_CODE = wanted
            request.language_source = source
            request._rivin_set_cookie = wanted
            response = self.get_response(request)
            response.set_cookie(
                self.cookie_name, wanted,
                max_age=getattr(settings, 'LANGUAGE_COOKIE_AGE', 365*24*3600),
                samesite=getattr(settings, 'LANGUAGE_COOKIE_SAMESITE', 'Lax'),
                httponly=getattr(settings, 'LANGUAGE_COOKIE_HTTPONLY', False),
            )
            # also vary header hint
            response['Content-Language'] = wanted
            return response

        # 2. explicit cookie -> LocaleMiddleware already did activate; just annotate
        if request.COOKIES.get(self.cookie_name):
            # LANGUAGE_CODE set by LocaleMiddleware (or fallback)
            current = translation.get_language() or getattr(request, 'LANGUAGE_CODE', DEFAULT_LANGUAGE)
            # normalize to supported
            if current[:2] not in SUPPORTED:
                current = DEFAULT_LANGUAGE
                translation.activate(current)
            else:
                current = current[:2]
            request.LANGUAGE_CODE = current
            request.language_source = 'user-cookie'
            request._rivin_set_cookie = None
            response = self.get_response(request)
            response['Content-Language'] = current
            return response

        # 3. & 4. & 5. auto-detect (no explicit choice)
        trust_geo = getattr(settings, 'TRUST_COUNTRY_HEADER', False)
        detected = None
        source = None
        country = None

        if trust_geo:
            country = country_from_request(request)
            if country:
                lang = language_for_country(country)
                if lang:
                    detected = lang
                    source = f'country:{country}'

        if not detected:
            hdr = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
            lang = language_from_accept_language(hdr)
            if lang:
                detected = lang
                source = 'accept-language'

        if not detected:
            detected = DEFAULT_LANGUAGE
            source = 'default'

        translation.activate(detected)
        request.LANGUAGE_CODE = detected
        request.language_source = source
        request._rivin_country = country
        request._rivin_set_cookie = None
        response = self.get_response(request)
        response['Content-Language'] = detected
        return response
