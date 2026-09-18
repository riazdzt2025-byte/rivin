from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.http import FileResponse, Http404
from pathlib import Path
import os

def serve_frontend(request):
    # Serve repo root index.html (PWA) — same origin as API so fetch() works without CORS
    p = Path(settings.BASE_DIR).parent / 'index.html'
    if not p.exists():
        raise Http404("index.html not found")
    return FileResponse(open(p, 'rb'), content_type='text/html')

def serve_manifest(request):
    p = Path(settings.BASE_DIR).parent / 'manifest.webmanifest'
    if not p.exists():
        raise Http404("manifest not found")
    return FileResponse(open(p, 'rb'), content_type='application/manifest+json')


def sitemap_xml(request):
    from django.http import HttpResponse
    from shop.models import Product
    from django.utils import timezone
    prods = Product.objects.filter(is_active=True).order_by('sku')[:100]
    urls = ['<url><loc>https://rivin-shop.onrender.com/</loc></url>']
    for prod in prods:
        urls.append(f'<url><loc>https://rivin-shop.onrender.com/api/v1/products/{prod.sku}/</loc><lastmod>{timezone.now().date()}</lastmod></url>')
    xml = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(urls) + '</urlset>'
    return HttpResponse(xml, content_type='application/xml')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('shop.urls')),
    path('api/v1/geo/', include('core.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
    path('manifest.webmanifest', serve_manifest, name='manifest'),
    path('sitemap.xml', sitemap_xml, name='sitemap'),
    path('', serve_frontend, name='frontend'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
