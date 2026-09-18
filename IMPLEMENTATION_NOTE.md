# RIVIN — Implementation Note — 2026-09-17

> Honest status per PROJECT_STATUS rule 7: everything below was **execution-verified** (not claimed).

## What was built (per PROMPT_RIVIN.md)

### 1. Prompt
- `PROMPT_RIVIN.md` — 11 sections, the single source of truth for RIVIN. Copied to workspace and executed verbatim.

### 2. Backend `backend/` — Django 5.2.17 on Python 3.13, SQLite fallback
- `rivin/settings.py` — i18n bn(default)/en/ar, `LANGUAGE_COOKIE_NAME=rivin_lang`, `TRUST_COUNTRY_HEADER`, `LOCALE_PATHS`, `CACHES=LocMem`, WhiteNoise optional, dj-database-url Postgres-ready, security `W001` as deploy-only.
- `core/geo.py` — pure functions: `ARABIC_COUNTRIES(24)`, `BENGALI_COUNTRIES={BD}`, `normalize_country`, `language_for_country`, `language_from_accept_language` (q-value sorted), `country_from_request` (CF-IPCountry, X-Vercel-IP-Country, X-Country-Code, X-Geo-Country).
- `core/middleware.py` — `LanguageDetectionMiddleware` chain: `?lang=` > `rivin_lang` cookie (LocaleMiddleware) > (if TRUST) country > Accept-Language > `bn` default. Sets `request.language_source` + `Content-Language`, sticky cookie 1y Lax.
- `core/checks.py` — `E001` locale path, `W001` deploy-only.
- `core/views.py` — `GET /api/v1/geo/language/` debug, `POST /api/v1/geo/language/set/` cookie setter.
- `shop/models.py` — 12 models, `TrilingualNameMixin`, `Category`, `Product` (sku, stock, image 2MB validator, is_bestseller), `Customer`, `Order` (ORD-YYYY-###### collision-safe, state machine PLACED→...→DELIVERED, `transition_to`), `OrderItem` (JSON name snapshot), `OrderStatusHistory`, `StockMovement`, `AuditLog`, `Review`, `DeliveryZone`, `Coupon` (percent/fixed, validity), `SiteSetting.get_solo()`. Money validation, `DecimalField(10,2)`.
- `shop/api.py` — plain Django `JsonResponse` API 8 endpoints, language-aware `?lang`/`Accept-Language`, `dir` rtl/ltr, rate-limit 5/10min via cache.
- `shop/permissions.py` — `ensure_default_groups` on post_migrate (ShopAdmin, Catalog, OrderDesk, Accounts, Delivery).
- `shop/admin.py`, `rivin/urls.py` (serves `index.html` at `/` + manifest same-origin), `locale/*/django.po` (35 strings each bn/en/ar).
- `shop/management/commands/seed_rivin.py` — 6 categories + 24 products idempotent, bestsellers, delivery ৳60 min ৳300, coupon WELCOME10.
- `requirements.txt`, `.env.example`, `.gitignore`, `manage.py`, `README.md`.

### 3. Frontend PWA `index.html` + `manifest.webmanifest`
- Rebrand RIAZ → RIVIN (title, manifest name, apple title), 3-language switcher (?lang → cookie → backend), `dir=rtl` for Arabic, cart → `POST /api/v1/orders/`, track dialog, geoNotice from `/api/v1/geo/language/`, fallback catalog 24 items, live loader `GET /api/v1/products/?lang=`.

### 4. CI `.github/workflows/backend.yml` — sqlite + postgres:16 matrix, `check` + `makemigrations --check` + `compilemessages` + `test core shop`.

## Verification (all run, not guessed)

```bash
pip install -r backend/requirements.txt  # Django 5.2.17 OK
python backend/manage.py check           # 0 issues
python backend/manage.py check --deploy  # 6 security warnings (expected, DEBUG=True etc.)
python backend/manage.py makemigrations  # 0001_initial 17KB OK
python backend/manage.py migrate         # all OK, shop.0001
python backend/manage.py seed_rivin      # 6 cats, 24 prods
python backend/manage.py test core shop --verbosity=2  # 20 tests OK (was 1 failure fixed: Order.total before order_no)
```

Live server `http://127.0.0.1:8000` (preview `https://8000-*.e2b.app`):
- `GET /` → 200 HTML 21840 bytes, Content-Language bn
- `GET /api/v1/products/?lang=bn` → 200, `dir ltr`, name খাতা ✓
- `GET /api/v1/products/?lang=ar` → 200, `dir rtl`, name صمغ ✓
- `GET /api/v1/geo/language/` (no header) → bn default ✓
- `GET /api/v1/geo/language/` with `Accept-Language: ar-EG` → ar via accept-language ✓
- With `TRUST_COUNTRY_HEADER=False` + `CF-IPCountry: SA` → still bn (spoof ignored) ✓ — after restart `TRUST=True`:
  - `CF-IPCountry: SA` → ar country:SA ✓
  - `CF-IPCountry: BD` → bn ✓
  - `CF-IPCountry: US` → en ✓
  - `CF-IPCountry: SA` + `?lang=bn` → bn (override wins) ✓
- `POST /api/v1/orders/` subtotal 235 → 400 min order error ✓
- `POST /api/v1/orders/` 2 items 1300 → 201 ORD-2026-000001 total 1360, stock rivin-0008 15→14 ✓
- `POST /api/v1/orders/` with coupon WELCOME10 950 → discount 95 total 915 ✓
- Single item qty1 price15 → 400 min order error ✓
- `?lang=ar` vs `Accept-Language: ar` both return دفتر A4 rtl ✓
- `Order.transition_to` PLACED→CONFIRMED→PACKED OK, PLACED→DELIVERED blocked, history 2 rows ✓
```

## Repo name question

No rename needed now. Product brand = RIVIN. Keep repo `riaz-shop-app` until merge, then GitHub Settings → Rename to `rivin-shop` (redirects stay). Django package is already `rivin`. Frontend manifest and title already RIVIN. If you rename, update deploy hooks (Netlify/Render) but git remotes auto-redirect.

## Remaining P0/P1 (not in this scaffold)

- Excel import `import_products` command (template)
- Image upload pipeline to S3 (USE_S3=true) — currently `Product.image` field ready
- bKash tokenized / SSLCommerz + SMS (SSL Wireless/Alpha SMS)
- Server-rendered SEO pages + sitemap.xml
- Backup drills (reuse school's `backup_data`)
- Generate `rivin.lang` cookie banner for first visit

## How to run

```bash
cp backend/.env.example backend/.env  # edit SECRET_KEY!
python backend/manage.py migrate
python backend/manage.py seed_rivin
python backend/manage.py runserver 0.0.0.0:8000  # frontend at /, API at /api/v1/, admin at /admin/
# prod behind Cloudflare: TRUST_COUNTRY_HEADER=True
```

## Files

See PROMPT_RIVIN.md, README.md, backend/README.md, index.html, manifest.webmanifest, backend/shop/models.py, core/geo.py, core/middleware.py

## Phase 6 Verification (2026-09-17 13:58 UTC)
- `pip install` OK, `check` 0, `check --deploy` 6 warnings, `makemigrations --check` No changes, `test core shop` 20 passed
- Seed idempotent 6/24, sitemap.xml added (Product URLs), README patched with Demo Curls + Render+Cloudflare deploy docs + Tests
- No Paid deps: requirements only Django, dotenv, dj-database-url, whitenoise, gunicorn, Pillow, psycopg — S3 optional local media only, no Redis/Celery
- Final tree + server HTTP 200 verified, tag suggestion v0.1.0-rivin
