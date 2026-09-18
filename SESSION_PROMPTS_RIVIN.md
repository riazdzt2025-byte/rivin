# RIVIN — ৬টি সেশন-কমফোর্ট প্রম্পট (Fresh Start)

> **Goal:** এক্সপেরিমেন্টাল E-commerce, কোনো Paid সার্ভিস নয়, Cloudflare Free + Render Free
> **Brand:** RIVIN (রিভিন) — trilingual `bn` (ডিফল্ট) / `en` / `ar` (RTL), দেশ অনুযায়ী অটো ভাষা
> **How to use:** প্রতিটি প্রম্পট **কপি-পেস্ট** করে Arena Agent Mode-এ নতুন সেশন খোলো। আগের সেশন merge না হওয়া পর্যন্ত পরেরটি শুরু করো না। প্রতিটি সেশন ২০–৪০ মিনিট, ১ PR, ২০ টেস্টের বেশি নয়।
> **Repo:** নতুন `rivin-shop` (GitHub → Create repository → Private). এই প্রম্পটগুলো `rivin-shop`-এর `main` ব্রাঞ্চে কাজ করবে।
> **Stack:** Django 5.2+, Python 3.13, SQLite (dev) → Render Postgres Free (prod), WhiteNoise, Gunicorn, `Pillow`, `python-dotenv`, `dj-database-url`

---

## SESSION 1 — Foundation + Free Deploy (ভিত)

**Copy this prompt:**

```
You are Agent Mode for repo `rivin-shop`. SESSION 1/6 — Foundation.

Context:
- Fresh repo, no code yet. Experimental, NO paid services. Deploy = Render (Free) + Cloudflare Free (DNS/CDN).
- Brand RIVIN (রিভিন), but this session is ONLY foundation — no shop models yet.
- Mirror discipline from school-management-system: single commit PR, meaningful commit msg.

Goal:
- Init Django project `rivin` in `backend/`, app `core` (empty).
- Create `backend/requirements.txt`: Django>=5.2,<6, python-dotenv, dj-database-url, whitenoise, gunicorn, Pillow.
- `rivin/settings.py`: SECRET_KEY from env, DEBUG from env, ALLOWED_HOSTS from env, DATABASES sqlite fallback + DATABASE_URL → Postgres, TIME_ZONE=Asia/Dhaka, USE_I18N=True, LANGUAGE_CODE=bn, LANGUAGES=[bn,en,ar], LOCALE_PATHS=[BASE_DIR/locale], LANGUAGE_COOKIE_NAME=rivin_lang, CACHES=LocMem, MIDDLEWARE includes LocaleMiddleware + (placeholder) core.middleware.LanguageDetectionMiddleware (create stub that just passes), TEMPLATES i18n context, STATIC/MEDIA with WhiteNoise, STORAGES filesystem.
- `core/geo.py` + `core/middleware.py` stub (return get_response), `core/checks.py` (E001 locale path, W001 deploy-only), `core/apps.py`, `core/tests_geo.py` with 2 smoke tests (normalize_country, language_for_country).
- `rivin/urls.py`: admin + i18n, root redirects to /admin/.
- `backend/manage.py`, `backend/.env.example` (SECRET_KEY, DEBUG, ALLOWED_HOSTS, DATABASE_URL, TRUST_COUNTRY_HEADER=False), `backend/.gitignore`, `README.md` (RIVIN banner + quick start), `PROMPT_RIVIN.md` (copy from workspace if exists), `.github/workflows/backend.yml` (check + makemigrations --check).
- `locale/` empty with `bn/en/ar/LC_MESSAGES/.gitkeep`.

Constraints:
- NO shop models yet. NO frontend. Keep files < 10.
- Do NOT add S3, DRF, Redis, Celery.

Acceptance:
- `pip install -r backend/requirements.txt` OK
- `python backend/manage.py check` → 0 issues
- `python backend/manage.py test core --verbosity=2` → 2 passed
- `python backend/manage.py makemigrations --check --dry-run` → no changes
- README has Render + Cloudflare Free deploy steps.

Deliverable: single commit `feat(session1): foundation — Django + i18n skeleton`.
```

**After merge:** Render → New Web Service → connect `rivin-shop`, Build `pip install -r backend/requirements.txt`, Start `gunicorn rivin.wsgi:application --chdir backend`, env `SECRET_KEY, DEBUG=False, ALLOWED_HOSTS=rivin-shop.onrender.com`, add `DATABASE_URL` from Render Postgres Free. Cloudflare → add CNAME to `*.onrender.com` (Free).

---

## SESSION 2 — Catalog Core (আলমারি)

**Copy this prompt:**

```
You are Agent Mode for `rivin-shop`, SESSION 2/6 — Catalog Core. SESSION 1 is merged (foundation exists).

Goal:
- Create Shop models: `Category(code, name_bn/en/ar, emoji, sort_order, is_active)` and `Product(sku, name_bn/en/ar, category FK, price, mrp, stock, emoji, image, link, is_active, is_bestseller, sort_order)` with `TrilingualNameMixin.display_name(lang)` fallback bn→en→ar, `money_field` Decimal(10,2) Min 0, image 2MB validator, stock Min 0.
- `shop/apps.py` with `ready` hook (no permissions yet), `shop/admin.py` (Category, Product), `shop/management/commands/seed_rivin.py` (6 cats + 24 products idempotent, list in previous ECOMMERCE_MAP_RIVIN.md), `shop/tests.py` (display_name fallback, money/stock validation).
- Update `rivin/settings.py` add `shop` to INSTALLED_APPS, `rivin/urls.py` add `path('api/v1/', include('shop.urls'))` + `core.urls` stub.
- `shop/urls.py` + `shop/api.py` (JSON only): `GET /api/v1/categories/?lang=`, `GET /api/v1/products/?category=&q=&lang=&is_bestseller=`, `GET /api/v1/products/<sku>/?lang=` — returns `name, name_bn/en/ar, dir (rtl/ltr), lang`.
- `backend/locale/{bn,en,ar}/LC_MESSAGES/django.po` with 12 strings (Add to cart, Cart, Price, Out of stock...), `shop/tests` include `ApiLanguageTests` (bn→ltr খাতা, ar→rtl صمغ).
- PWA stub `index.html` (339 lines or minimal) + `manifest.webmanifest` (RIVIN) at repo root, `rivin/urls.py` serve_frontend at `/` for DEBUG (FileResponse parent/index.html).

Constraints:
- NO Order, NO Customer, NO Cart checkout. Media local `media/products/` (no S3).
- Keep API plain JsonResponse, no DRF.

Acceptance:
- `python backend/manage.py makemigrations && migrate` OK
- `python backend/manage.py seed_rivin` → 6 cats 24 prods, bestsellers 4
- `python backend/manage.py test core shop --verbosity=2` → ~12 passed
- `curl /api/v1/products/?lang=bn` → খাতা ltr, `?lang=ar` → صمغ rtl
- Frontend at `/` shows 24 products, language switcher changes dir.

Deliverable: commit `feat(session2): catalog — trilingual product & API`.
```

---

## SESSION 3 — Cart & Checkout (ক্যাশ কাউন্টার)

**Copy this prompt:**

```
You are Agent Mode for `rivin-shop`, SESSION 3/6 — Cart & Checkout. SESSION 2 merged (Catalog API live).

Goal:
- Add `Customer(name, mobile, address, preferred_language, country_code)`, `Order(order_no ORD-YYYY-###### collision-safe, customer FK, status, subtotal, delivery_fee, discount, total, payment_method, payment_status, coupon_code, ordered_at, delivered_at)`, `OrderItem(order, product, product_name_snapshot JSON bn/en/ar, unit_price_snapshot, qty, line_total)`, `SiteSetting(singleton delivery 60 min 300 + bestsellers M2M)`.
- Implement `Order.save()` total = subtotal+delivery-discount, `OrderStatusHistory` model stub + `Order.ALLOWED_TRANSITIONS` dict (PLACED→CONFIRMED→PACKED→OUT→DELIVERED, CANCELLED, RETURNED), `transition_to` raises InvalidOrderTransition.
- `shop/api.py` add: `GET /api/v1/settings/` (delivery/min/bestsellers), `POST /api/v1/orders/` (csrf_exempt, rate-limit 5/10min via cache, validates mobile+address, items [{sku,qty}], stock check, min_order 300, creates Customer get_or_create, creates Order + OrderItem snapshots, decrements Product.stock, creates StockMovement, handles Coupon stub), `GET /api/v1/orders/<order_no>/` (track), `GET /api/v1/orders/mine/?mobile=`.
- Add `DeliveryZone`, `Coupon(code, type percent/fixed, value, valid_from/to, min_subtotal, usage_limit, used_count)` with `is_valid_for`, `discount_for`, `StockMovement`, `AuditLog` models (minimal).
- Update PWA `index.html` cart: localStorage `rivin_cart`, addToCart, cartbar total, checkout prompt (name/mobile/address) → POST /api/v1/orders/, track dialog.

Constraints:
- NO auth yet, NO image upload, manual COD only (payment_method=cod).
- Money as string in JSON, Decimal in DB.

Acceptance:
- `makemigrations && migrate` OK
- `POST /api/v1/orders/` with 2 items subtotal>300 → 201 ORD-..., total 1360, stock decreased
- `POST` with subtotal 15 → 400 min order error
- `POST` with coupon WELCOME10 → discount applied
- `GET /api/v1/orders/<no>/` shows snapshot names bn/en/ar
- `python backend/manage.py test core shop --verbosity=2` → ~18 passed

Deliverable: commit `feat(session3): cart & checkout — order lifecycle`.
```

---

## SESSION 4 — Order Lifecycle + Admin (অপারেশন)

**Copy this prompt:**

```
You are Agent Mode for `rivin-shop`, SESSION 4/6 — Order Ops. SESSION 3 merged.

Goal:
- Complete `Order.transition_to` + `OrderStatusHistory` creation, `shop/admin.py` add OrderAdmin with OrderItemInline + HistoryInline, list_display order_no/customer/status/total, filter status.
- `shop/permissions.py` ensure_default_groups (ShopAdmin, Catalog, OrderDesk, Accounts, Delivery) on post_migrate, connect in `shop/apps.py`.
- Add `Review(product/order, customer, rating 1-5, emoji, comment)` + `POST /api/v1/orders/<no>/review/`, `GET /api/v1/products/<sku>/?lang=` already done.
- Admin dashboard: extend `shop/admin.py` with simple changelist for DeliveryZone, Coupon (is_valid).
- Update `shop/api.py` to support `?lang` on order detail (display_name), add `dir` field.
- Add `shop/tests.py` tests: state machine valid/invalid, invalid transition blocked, history created, review creation, coupon min_subtotal.
- Document `TRUST_COUNTRY_HEADER` still False (next session).

Constraints:
- No payment gateway, no SMS.
- Keep tests < 25 total.

Acceptance:
- Admin at /admin/ shows Category, Product, Order, Customer, Coupon; groups created after `migrate`
- `Order.objects.first().transition_to(CONFIRMED)` OK, `PLACED→DELIVERED` raises InvalidOrderTransition
- `POST /api/v1/orders/<no>/review/` → 200, review saved
- `python backend/manage.py test core shop --verbosity=2` → ~20 passed

Deliverable: commit `feat(session4): admin & lifecycle — state machine + reviews`.
```

---

## SESSION 5 — Trilingual & Geo (ভাষা = বিক্রি)

**Copy this prompt:**

```
You are Agent Mode for `rivin-shop`, SESSION 5/6 — i18n & Geo. Prior sessions merged.

Goal:
- Finish `core/geo.py`: ARABIC_COUNTRIES 24, BENGALI_COUNTRIES={BD}, SUPPORTED=(bn,en,ar), DEFAULT=bn, functions `normalize_country`, `language_for_country`, `language_from_accept_language` (q-value), `country_from_request` (CF-IPCountry, X-Vercel-IP-Country, X-Country-Code, X-Geo-Country).
- `core/middleware.py`: `LanguageDetectionMiddleware` AFTER LocaleMiddleware, priority ?lang > cookie rivin_lang > (if TRUST_COUNTRY_HEADER) country > Accept-Language > bn, sets request.language_source, request.LANGUAGE_CODE, Content-Language, sticky cookie 1y Lax, request._rivin_country for debug.
- `core/views.py`: `GET /api/v1/geo/language/` debug {detected, source, country, accept_language, cookie}, `POST /api/v1/geo/language/set/` {lang} sets cookie.
- `rivin/settings.py`: LANGUAGE_COOKIE_NAME=rivin_lang (already), TRUST_COUNTRY_HEADER env, MIDDLEWARE order, TAGS security deploy, LOCALE_PATHS.
- `backend/locale/{bn,en,ar}/LC_MESSAGES/django.po` expand to 35 strings (Cart, Checkout, Track order, Bestsellers...), add `compilemessages` note (gettext optional, .mo gitignored).
- Update `shop/api.py` all endpoints to use `_lang(request)` helper (query > translation.get_language) and return `dir: rtl|ltr`.
- Update PWA `index.html` language switcher to set cookie rivin_lang + ?lang + dir=rtl toggle, geoNotice from /api/v1/geo/language/.
- `core/tests_geo.py` expand to 10 tests: BD→bn, SA→ar, US→en, q-order, spoofed ignored when TRUST=False, cookie wins, ?lang sets cookie, Accept-Language ar-EG → ar, default bn.

Constraints:
- NO new models. Keep TRUST default False, document to set True behind Cloudflare.
- RTL test: ?lang=ar → dir rtl, name صمغ.

Acceptance:
- `python backend/manage.py test core --verbosity=2` → 10 geo passed
- `curl -H "CF-IPCountry: SA" /api/v1/geo/language/` with TRUST=False → bn default (spoof ignored), with TRUST=True → ar country:SA
- `curl /api/v1/products/?lang=ar` → rtl, `Accept-Language: bn-BD` → bn ltr without ?lang
- Frontend switcher العربية → <html dir="rtl"> + cookie set

Deliverable: commit `feat(session5): i18n — trilingual + country-geo`.
```

---

## SESSION 6 — Hardening & Launch Ready (লঞ্চ)

**Copy this prompt:**

```
You are Agent Mode for `rivin-shop`, SESSION 6/6 — Hardening. Prior sessions merged.

Goal:
- Hardening: `Product.image` already exists, ensure validator 2MB, local media `media/products/%Y/%m/` (no S3), `shop/admin.py` low-stock list_filter, `shop/models.py` `StockMovement` auto on order, `AuditLog` helper.
- Add rate-limit already in api.py, ensure CACHES LocMem, add `shop/management/commands/import_products.py` (Excel openpyxl optional, fallback CSV) + downloadable template logic (read docs/DATA_SAFETY).
- SEO: `rivin/urls.py` add `sitemap.xml` (static view enumerating products), `robots.txt`, `index.html` meta OG (RIVIN), `manifest.webmanifest` icons.
- Backup docs: `docs/BACKUP.md` (pg_dump for Render Postgres Free, restore steps), `backend/.env.example` finalize (DATABASE_URL, TRUST_COUNTRY_HEADER, SECRET_KEY gen).
- Update `.github/workflows/backend.yml` matrix sqlite + postgres:16, `compilemessages --ignore`, frontend-smoke (index.html + manifest).
- `README.md` final: brand RIVIN, quick start, deploy steps (Render + Cloudflare Free), language demo curls, order demo, `python backend/manage.py test core shop` 20+ tests.

Constraints:
- NO paid gateways, NO paid SMS, NO S3 — manual bKash TrxID verify only.
- Keep experimental: note sleep on Render Free.

Acceptance:
- `python backend/manage.py check` → 0, `check --deploy` → expected security warnings
- `python backend/manage.py test core shop --verbosity=1` → >=20 passed
- `curl /api/v1/sitemap.xml` → 200, lists products
- `curl /media/` when image uploaded → 200
- README has one-line Render deploy + Cloudflare DNS note.

Deliverable: commit `feat(session6): launch ready — hardening + docs` and tag `v0.1.0-rivin`.
```

---

## How to Run Sequencially

1. Create GitHub repo `rivin-shop` (README off).
2. Clone, then for each session: `git checkout -b arena/session1`, run Agent Mode with that session prompt, review PR, merge to `main`.
3. After SESSION 1, connect Render + Cloudflare — keep deploy green.
4. Each session commit message must be `feat(sessionN): ...` for clean log like school system.
5. Experimental launch: Render Free will sleep — first request slow, acceptable. No paid DB/SMS.

## Tips to Keep Sessions Comfortable

- Each prompt < 1 file change set; if agent wants to add too much, stop and re-prompt "only session N scope".
- Run `python backend/manage.py test core shop` after each session — if fail, fix before next.
- Keep `PROMPT_RIVIN.md` + `ECOMMERCE_MAP_RIVIN.md` in repo root for reference; do not delete.
- Use `TRUST_COUNTRY_HEADER=False` until Cloudflare CNAME is live, then flip to True in Render env.

## File Reference

- `ECOMMERCE_MAP_RIVIN.md` — what is needed (this map)
- `PROMPT_RIVIN.md` — original single big prompt (now split)
- `SESSION_PROMPTS_RIVIN.md` — this file
- After SESSION 2+: `IMPLEMENTATION_NOTE.md` — verification log
