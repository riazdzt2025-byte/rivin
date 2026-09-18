# RIVIN — Trilingual E-commerce Platform — Master Prompt

> **Source:** Derived from analysis of `school-management-system` (205 commits, Django 6.1, 550 tests) — applying same production-grade discipline to e-commerce.
> **Previous name:** RIAZ Shop → **New brand:** RIVIN (রিভিন)
> **Date:** 2026-09-17

---

## 1. Brand & Identity

- **Product name:** RIVIN (not repo name). Repo may stay `riaz-shop-app` until merge, then rename to `rivin-shop` on GitHub (Settings → Rename). GitHub keeps redirects.
- **Rebrand checklist (frontend):**
  - `<title>RIVIN — রিভিন</title>`
  - `manifest.webmanifest` name/short_name = RIVIN
  - `apple-mobile-web-app-title` = RIVIN
  - Share URLs: replace `https://yoursite.com/riyaz_app_v9.html` / `https://example.com/riyaz_app_v9.html` → canonical domain (e.g. `https://rivin.example.com`)
  - WhatsApp `8801710091015` keep (verify)
  - Theme colors / favicon (generate new RIVIN icon)
- **Tone:** Bangla-first, mobile-first PWA (existing 311 products baseline), but now trilingual.

## 2. Languages — bn / en / ar

- **Supported:** `bn` (বাংলা, default), `en` (English), `ar` (العربية, RTL)
- **Storage:** Explicit fields `name_bn / name_en / name_ar` on Category/Product (+ `display_name(lang)` helper). Simple, no `django-modeltranslation` dep. Snapshotted into `OrderItem` at order time.
- **Django i18n:**
  ```py
  LANGUAGE_CODE = "bn"
  LANGUAGES = [("bn","বাংলা"), ("en","English"), ("ar","العربية")]
  LOCALE_PATHS = [BASE_DIR / "locale"]
  LANGUAGE_COOKIE_NAME = "rivin_lang"  # explicit choice only
  USE_I18N = True
  MIDDLEWARE = [..., "django.middleware.locale.LocaleMiddleware",
                 "core.middleware.LanguageDetectionMiddleware", ...]
  TEMPLATES context_processors includes `django.template.context_processors.i18n`
  <html dir="{% if LANGUAGE_BIDI %}rtl{% else %}ltr{% endif %}" lang="{{ LANGUAGE_CODE }}">
  ```
- **`.po` files:** `backend/locale/{bn,en,ar}/LC_MESSAGES/django.po` with ~35 shop strings + `compilemessages` → `.mo` (git-ignored).
- **Frontend switcher:** Calls `POST /api/v1/language/` or `?lang=ar`; respects `dir` field in API responses.

## 3. Geo-based Auto Language Detection

**Priority (highest → lowest):**
1. `?lang=bn|en|ar` query param → set `rivin_lang` cookie (sticky, 1 year, SameSite=Lax)
2. `rivin_lang` cookie (user's explicit past choice) → `LocaleMiddleware` already activated
3. CDN country header → `language_for_country(country)` — **only if `TRUST_COUNTRY_HEADER=True`** (prevents spoofing when not behind Cloudflare)
   - `BD` → `bn`
   - `ARABIC_COUNTRIES = SA,AE,EG,KW,QA,BH,OM,YE,JO,LB,SY,IQ,LY,SD,MA,DZ,TN,PS,MR,SO,DJ,KM,TD,ER` → `ar`
   - `US,GB,CA,AU,IE,NZ,SG,PH,ZA,MY` → `en` (fallback)
   - `IN` intentionally **not** mapped → falls through to Accept-Language (West Bengal vs other states)
4. `Accept-Language` header parsed with q-values (`bn-BD,bn;q=0.9,ar;q=0.8`)
5. Default `bn`

**Headers checked:** `CF-IPCountry` (Cloudflare), `X-Vercel-IP-Country`, `X-Country-Code`, `X-Geo-Country` (generic Nginx GeoIP). Netlify free has no country header — document that Cloudflare in front is recommended.

**Middleware:** `core/middleware.py::LanguageDetectionMiddleware` (after `LocaleMiddleware` so it wins), sets `request.language_source` for debug endpoint `GET /api/v1/geo/language/`.

**Security:** `TRUST_COUNTRY_HEADER` env (default False in dev, True in prod behind CDN). Tests cover spoofing.

## 4. Architecture — Hybrid (Recommended)

```
[Bangla-first PWA (index.html)]  <──JSON──>  [Django API (rivin)]
                                          └──> Postgres (prod) / SQLite (dev)
                                          └──> S3-compatible media (reuse USE_S3)
                                          └──> Django Admin (templates) for ops
```

- **Why hybrid:** Keep the existing mobile PWA UX users know, but move data/auth/reports to your own Django (same patterns as school system).
- **Fallback:** Single-file Firebase SPA had `ADMIN_PIN='1234'` client-side + loose Firestore rules. New backend fixes both.

## 5. Django Stack (mirror school-management-system)

- Python 3.11+ / 3.13, Django 5.2 (or 6.1 if Python 3.12+), Bootstrap 5 templates for admin, Gunicorn, WhiteNoise, `dj-database-url` optional, `python-dotenv`, `Pillow` for images, `psycopg[binary]` for Postgres.
- DB: `DATABASE_URL` if set → Postgres, else SQLite (`db.sqlite3`). `CONN_MAX_AGE=600`.
- Security: `SECRET_KEY` from env, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, rate-limit on order creation (5/10min/IP), `SECURE_*` flags documented.
- Checks: `rivin.W001` (ALLOWED_HOSTS=* in prod), `rivin.E001` (locale dir missing).

## 6. Data Model — 12 Models (same discipline as school system)

| Model | Key fields | Pattern reused |
|---|---|---|
| **Category** | `code, name_bn/en/ar, emoji, sort_order, is_active` | — |
| **Product** | `sku unique, name_bn/en/ar, category FK, price, mrp, stock, emoji, image, link, is_active, is_bestseller, sort_order` | Image 2MB validator (like `clean_photo`) |
| **Customer** | `name, mobile, email, address, preferred_language, country_code` | Mobile normalisation |
| **Order** | `order_no unique ORD-YYYY-###### collision-safe, customer FK, status state-machine, subtotal, delivery_fee, discount, total, payment_method, payment_status, ordered_at` | `MoneyReceipt.receipt_no` generation |
| **OrderItem** | `order FK, product FK, product_name_snapshot (JSON bn/en/ar), unit_price_snapshot, qty, line_total` | Snapshot = immutability |
| **OrderStatusHistory** | `order FK, from_status, to_status, changed_by, note, at` | Employee status history |
| **StockMovement** | `product FK, delta, reason, at, by` | Audit trail |
| **AuditLog** | `actor, action, object_type, object_id, changed_fields JSON, at, ip` | `record_audit` |
| **Review** | `product/order FK, customer FK, rating 1-5, emoji, comment, at` | — |
| **DeliveryZone** | `name, charge, min_order, is_active` | Fee schedule |
| **Coupon** | `code, type percent/fixed, value, valid_from/to, min_subtotal, usage_limit, used_count, is_active` | — |
| **SiteSetting** | singleton: `theme, bg, bestsellers M2M, delivery defaults` | Replaces Firestore settings doc |

**Money validation:** `DecimalField(max_digits=10, decimal_places=2)` + `MinValueValidator(0)`, `MaxValueValidator(99999999.99)`.

**Order state machine:**
```
PLACED → CONFIRMED → PACKED → OUT_FOR_DELIVERY → DELIVERED
  ↓         ↓           ↓           ↓
CANCELLED CANCELLED  CANCELLED  CANCELLED
DELIVERED → RETURNED (only)
```
- `transition_to(new_status, actor, note)` raises `InvalidOrderTransition` if illegal; creates `OrderStatusHistory` atomically.

**Permissions (post_migrate → ensure_default_groups):** `ShopAdmin, Catalog, OrderDesk, Accounts, Delivery`

## 7. JSON API (no DRF dep, plain Django JsonResponse)

```
GET  /api/v1/categories/?lang=ar
GET  /api/v1/products/?category=&q=&lang=ar&is_bestseller=1
GET  /api/v1/products/<sku>/?lang=
GET  /api/v1/settings/
POST /api/v1/orders/                 {customer:{name,mobile,address}, items:[{sku,qty}], coupon_code}
GET  /api/v1/orders/<order_no>/
GET  /api/v1/orders/mine/?mobile=   (device-scoped fallback)
POST /api/v1/orders/<order_no>/review/ {rating, emoji, comment}
POST /api/v1/language/              {lang} → sets cookie
GET  /api/v1/geo/language/          → {detected:"ar", source:"country:SA", country:"SA"}
```

- Language-aware: `?lang=` or Accept-Language, response includes `name`, `name_bn/en/ar`, `dir: "rtl"|"ltr"`.
- `POST /api/v1/orders/` is `csrf_exempt` + rate-limited (like school admission form). Document token-auth upgrade path.
- All money in `Decimal` strings to avoid float.

## 8. Operations (reuse school ops)

- **Excel import:** `manage.py import_products template.xlsx` (like `import_exam_marks`) + downloadable template.
- **Backup:** `backup_data / restore_backup / check_backups --check-remote` with encrypted off-box S3 copy + drills (orders = money, so same rigor).
- **CI:** `.github/workflows/backend.yml` — `check + makemigrations --check + test` matrix `sqlite + postgres:16` + node job (mirror `tests.yml`).
- **Migrations:** `python manage.py makemigrations && python manage.py migrate` (hand-written `0001` avoided on purpose; generate verified).

## 9. Immediate P0/P1 Roadmap

**P0 (live risk):**
- [ ] Firestore rules audit (if keeping Firebase temporarily)
- [ ] Replace `ADMIN_PIN=1234` with Django auth
- [ ] Fix share placeholder domains → canonical
- [ ] Fix README 3× duplication → RIVIN branding

**P1 (revenue):**
- [ ] Enable product image upload (was `handleProductImageUpload` disabled) → S3
- [ ] Stock field + low-stock admin alert
- [ ] bKash/Nagad manual TrxID verification → later SSLCommerz tokenized
- [ ] SMS/WhatsApp on status change (SSL Wireless / Alpha SMS)

**P2 (scale):**
- [ ] Django API scaffold (this prompt)
- [ ] Excel bulk import for 311 products
- [ ] Server-rendered SEO product pages + sitemap.xml
- [ ] Daily sales Excel export

## 10. Environment

```env
SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOSTS=*
DATABASE_URL=           # sqlite fallback if empty; postgres: postgres://user:pass@host:5432/rivin
TRUST_COUNTRY_HEADER=False  # True behind Cloudflare
LANGUAGE_CODE=bn
TIME_ZONE=Asia/Dhaka
USE_S3=False
AWS_STORAGE_BUCKET_NAME=
```

## 11. Acceptance Criteria

- [ ] `python manage.py check` passes (no E001/W001 in prod config)
- [ ] `python manage.py makemigrations --check` clean
- [ ] `python manage.py test` — geo tests (6 cases), state-machine tests, trilingual fallback tests, API language negotiation tests — all green
- [ ] `curl -H "CF-IPCountry: SA" /api/v1/geo/language/` → `{"detected":"ar","source":"country:SA"}`
- [ ] `curl -H "Accept-Language: bn-BD" /api/v1/products/?q=খাতা` → localized names
- [ ] Arabic page renders `dir="rtl"` and `lang="ar"`
- [ ] Order `ORD-2026-000001` collision-safe under concurrent POSTs
- [ ] Admin groups created on `migrate`

---

**Execution instruction:** Scaffold exactly this spec under `backend/` (Django project `rivin`), keep existing PWA frontend but make it i18n-aware, ship locale `.po` with 35 strings, and document `compilemessages` + `makemigrations` steps with honest "not-yet-verified until you run" note per PROJECT_STATUS rule 7.
