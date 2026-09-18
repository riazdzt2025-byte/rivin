# RIVIN — রিভিন

**Trilingual e-commerce — বাংলা / English / العربية — দেশ অনুযায়ী অটো ভাষা**

> Rebrand: **RIAZ Shop → RIVIN**. Repo may stay `riaz-shop-app` until merge, then rename to `rivin-shop` on GitHub (Settings → Rename). Product brand is RIVIN everywhere (title, manifest, OG tags, share URLs).

- **PWA frontend:** `index.html` (339 lines) + `manifest.webmanifest` — mobile-first, Bangladesh market, now with 3-language switcher + RTL.
- **Backend:** Django 5.2+ in `backend/` — mirrors `school-management-system` discipline (550 tests, Postgres-ready, backup, CI matrix, AuditLog).
- **Catalog:** 311 products baseline (fallback in PWA, real in DB after `import_products`).
- **Delivery:** ৳60 • Min order ৳300 • COD + bKash (manual TrxID → SSLCommerz roadmap).

## Quick start (backend)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env  # set SECRET_KEY!
python backend/manage.py makemigrations core shop
python backend/manage.py migrate
python backend/manage.py createsuperuser
python backend/manage.py compilemessages  # needs gettext
python backend/manage.py runserver 0.0.0.0:8000
# then open http://localhost:8000/ (PWA) or /admin/ or /api/v1/products/?lang=ar
```

## Languages (PROMPT section 2-3)

`bn` default • `en` • `ar` (RTL). Auto chain: `?lang=` > `rivin_lang` cookie > (if `TRUST_COUNTRY_HEADER=True`) `CF-IPCountry`/`X-Vercel-IP-Country` → `language_for_country()` > `Accept-Language` (q-values) > `bn`.
- Products store `name_bn/en/ar` + `display_name(lang)` + snapshot in `OrderItem`.
- `GET /api/v1/geo/language/` debug: `{detected, source, country}`.
- Frontend sets `rivin_lang` cookie (1y, Lax) and `<html dir="rtl">` for Arabic.

## API (no DRF)

```
GET  /api/v1/categories/?lang=ar
GET  /api/v1/products/?category=stationery&q=খাতা&lang=bn
GET  /api/v1/products/<sku>/?lang=en
GET  /api/v1/settings/
POST /api/v1/orders/                 {customer:{name,mobile,address}, items:[{sku,qty}]}
GET  /api/v1/orders/<order_no>/
GET  /api/v1/orders/mine/?mobile=017...
POST /api/v1/orders/<order_no>/review/
POST /api/v1/geo/language/set/        {lang}
GET  /api/v1/geo/language/
```

## What was wrong before (fixed by this scaffold)

- `ADMIN_PIN='1234'` client-side → Django auth + `ensure_default_groups` (ShopAdmin/Catalog/OrderDesk/Accounts/Delivery)
- `handleProductImageUpload` disabled → `Product.image` + S3-ready `USE_S3`
- Share URLs `yoursite.com/example.com` placeholder → canonical `rivin.example.com` (set in env/deploy)
- README 3× duplicated → this single file
- No `stock` field → `Product.stock` + `StockMovement` + low-stock admin
- COD only → `Coupon` + `payment_method` (bkash/nagad/card) + `payment_status`

## Project tree

```
index.html, manifest.webmanifest, PROMPT_RIVIN.md
backend/
  rivin/settings.py  (i18n, TRUST_COUNTRY_HEADER, dj-database-url, WhiteNoise, CACHES)
  core/  geo.py, middleware.py, checks.py, tests_geo.py, views.py
  shop/  models.py (12 models), api.py, tests_models.py, admin.py, permissions.py
  locale/{bn,en,ar}/LC_MESSAGES/django.po
  requirements.txt, manage.py, README.md
.github/workflows/backend.yml  (sqlite + postgres:16 matrix)
```

## Env

See `backend/.env.example`. Key: `TRUST_COUNTRY_HEADER=False` in dev, `True` behind Cloudflare.

## Tests

```bash
python backend/manage.py test --verbosity=2
```

Covers: country→lang, Accept-Language q-order, spoofing ignored when `TRUST=False`, cookie wins, `?lang` sets cookie, trilingual fallback, money/stock validation, `order_no` collision-safe, state machine, coupon, `?lang=ar`→`rtl`.


## Demo Curls (live)

```bash
curl http://localhost:8000/api/v1/products/?lang=bn  # ltr খাতা A4
curl http://localhost:8000/api/v1/products/?lang=ar  # rtl صمغ
curl http://localhost:8000/api/v1/geo/language/  # {detected: bn, source: default}
curl -H "Accept-Language: ar-EG" http://localhost:8000/api/v1/geo/language/  # ar
curl -H "CF-IPCountry: SA" http://localhost:8000/api/v1/geo/language/  # TRUST=True → ar
curl -X POST http://localhost:8000/api/v1/orders/ -H "Content-Type: application/json" -d '{"customer":{"name":"Test","mobile":"01711111111","address":"Dhaka"},"items":[{"sku":"rivin-0001","qty":4}]}'
```

## Deploy (Render + Cloudflare Free, No Paid)

- **Render Dashboard:** https://dashboard.render.com → New → Web Service → Connect GitHub `rivin-shop`
  - Build: `pip install -r backend/requirements.txt`
  - Start: `gunicorn rivin.wsgi:application --chdir backend`
  - Env: `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS=rivin-shop.onrender.com`, `DATABASE_URL=<Render Postgres Free>`, `TRUST_COUNTRY_HEADER=True`
- **Cloudflare Free:** https://dash.cloudflare.com → Add site → CNAME `rivin → rivin-shop.onrender.com` (proxy ☁️ orange) → `CF-IPCountry` header auto
- **Live URL (after push):** `https://rivin-shop.onrender.com/` + `/api/v1/products/?lang=bn`
- **Current sandbox preview:** Arena LIVE PREVIEW `https://8000-*.e2b.app` (RIVIN Phase4 TRUST) — click above terminal

## Tests

```bash
python backend/manage.py test core shop --verbosity=2  # 20 tests
python backend/manage.py check  # 0 issues
python backend/manage.py check --deploy  # 6 security warnings (expected with DEBUG True)
```

## Roadmap

- P0: Firestore rules audit (if Firebase still live), `makemigrations` commit, set `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS`, reset any exposed `SECRET_KEY`
- P1: `Product.image` pipeline + low-stock alert + bKash TrxID verification + SMS on status (SSL Wireless/Alpha SMS)
- P2: Excel bulk import (311) + server-rendered SEO + sitemap + daily sales Excel export

License: private.
