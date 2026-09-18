from django.test import TestCase, RequestFactory, override_settings
from django.conf import settings
from django.utils import translation
from .geo import language_for_country, language_from_accept_language, normalize_country
from .middleware import LanguageDetectionMiddleware

class GeoPureTests(TestCase):
    def test_normalize_country(self):
        self.assertEqual(normalize_country(' bd '), 'BD')
        self.assertEqual(normalize_country('sa'), 'SA')
        self.assertIsNone(normalize_country(''))
        self.assertIsNone(normalize_country('B'))
        self.assertIsNone(normalize_country('123'))

    def test_language_for_country(self):
        self.assertEqual(language_for_country('BD'), 'bn')
        self.assertEqual(language_for_country('SA'), 'ar')
        self.assertEqual(language_for_country('AE'), 'ar')
        self.assertEqual(language_for_country('EG'), 'ar')
        self.assertEqual(language_for_country('US'), 'en')
        self.assertEqual(language_for_country('GB'), 'en')
        self.assertIsNone(language_for_country('FR'))  # unknown -> None, fallback to Accept-Language

    def test_accept_language_basic(self):
        self.assertEqual(language_from_accept_language('bn-BD,bn;q=0.9,en;q=0.8'), 'bn')
        self.assertEqual(language_from_accept_language('ar-EG,ar;q=0.9'), 'ar')
        self.assertEqual(language_from_accept_language('en-US,en;q=0.9'), 'en')
        self.assertEqual(language_from_accept_language('fr, de;q=0.8'), None)
        self.assertIsNone(language_from_accept_language(''))
        self.assertIsNone(language_from_accept_language(None))

    def test_accept_language_q_order(self):
        # q values matter: ar higher despite order
        self.assertEqual(language_from_accept_language('en;q=0.5, ar;q=0.9, bn;q=0.7'), 'ar')
        self.assertEqual(language_from_accept_language('en;q=0.9, bn;q=0.1'), 'en')

class MiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.mw = LanguageDetectionMiddleware(lambda r: r)

    def _req(self, path='/?', **meta):
        # helper returns request after middleware (we fake get_response to return request)
        # but our middleware returns response via get_response; we set get_response to echo
        req = self.factory.get(path, **meta)
        # Simulate LocaleMiddleware not setting LANGUAGE_CODE; our middleware will set it
        return req

    @override_settings(TRUST_COUNTRY_HEADER=True)
    def test_country_bd_maps_to_bn(self):
        req = self.factory.get('/', HTTP_CF_IPCOUNTRY='BD')
        def get_resp(r): from django.http import HttpResponse; return HttpResponse('ok')
        mw = LanguageDetectionMiddleware(get_resp)
        resp = mw(req)
        self.assertEqual(resp['Content-Language'], 'bn')
        self.assertEqual(req.language_source, 'country:BD')

    @override_settings(TRUST_COUNTRY_HEADER=True)
    def test_country_sa_maps_to_ar(self):
        req = self.factory.get('/', HTTP_CF_IPCOUNTRY='SA')
        def get_resp(r): from django.http import HttpResponse; return HttpResponse('ok')
        mw = LanguageDetectionMiddleware(get_resp)
        resp = mw(req)
        self.assertEqual(resp['Content-Language'], 'ar')

    @override_settings(TRUST_COUNTRY_HEADER=False)
    def test_spoofed_country_ignored_when_not_trusted(self):
        req = self.factory.get('/', HTTP_CF_IPCOUNTRY='SA', HTTP_ACCEPT_LANGUAGE='bn-BD')
        def get_resp(r): from django.http import HttpResponse; return HttpResponse('ok')
        mw = LanguageDetectionMiddleware(get_resp)
        resp = mw(req)
        # should ignore SA and use Accept-Language -> bn
        self.assertEqual(resp['Content-Language'], 'bn')
        self.assertEqual(req.language_source, 'accept-language')

    def test_query_param_wins_and_sets_cookie(self):
        req = self.factory.get('/?lang=ar')
        def get_resp(r): from django.http import HttpResponse; return HttpResponse('ok')
        mw = LanguageDetectionMiddleware(get_resp)
        resp = mw(req)
        self.assertEqual(resp['Content-Language'], 'ar')
        self.assertIn(settings.LANGUAGE_COOKIE_NAME, resp.cookies)

    def test_cookie_wins_over_country(self):
        factory = RequestFactory()
        req = factory.get('/', HTTP_CF_IPCOUNTRY='SA')
        req.COOKIES[settings.LANGUAGE_COOKIE_NAME] = 'en'
        # Simulate LocaleMiddleware already activated en
        translation.activate('en')
        def get_resp(r): from django.http import HttpResponse; return HttpResponse('ok')
        mw = LanguageDetectionMiddleware(get_resp)
        resp = mw(req)
        self.assertEqual(resp['Content-Language'], 'en')
        self.assertEqual(req.language_source, 'user-cookie')
        translation.activate(settings.LANGUAGE_CODE)

    def test_default_when_no_headers(self):
        req = self.factory.get('/')
        def get_resp(r): from django.http import HttpResponse; return HttpResponse('ok')
        mw = LanguageDetectionMiddleware(get_resp)
        resp = mw(req)
        self.assertEqual(resp['Content-Language'], 'bn')
