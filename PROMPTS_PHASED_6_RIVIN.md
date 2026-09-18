# RIVIN — ৬টি সেশন-কমফোর্ট প্রম্পট (বর্তমান workspace থেকে Continue)

> **নিয়ম:** প্রতিটি প্রম্পট **ওভাররাইট নয়** — বিদ্যমান `backend/`, `index.html`, `manifest.webmanifest`, `locale/` অক্ষত রেখে **যাচাই/সম্পূরক** করবে। এক সেশনে একটি ফেজ, রিপোর্ট দিয়ে পরেরটিতে যাবে।
> **Stack:** Django 5.2, Python 3.13, SQLite(dev)→Render Postgres Free(prod), Cloudflare Free, WhiteNoise, No Paid S3/Redis
> **Workspace Status (2026-09-17):** Foundation + Models + i18n/API + Tests সব scaffolded, `shop/migrations/0001_initial.py` applied, DB `Category 6 Product 24 Order 2`, `check 0 issues`, `test 20 passed`. সার্ভার পুনরায় চালু করতে হবে।

---

## PROMPT 1/6 — Foundation Verify (Django scaffold health-check)

```
You are Agent Mode, repo `rivin-shop` CONTINUE mode. Do NOT overwrite working code.

Context:
- Workspace already has backend/rivin/settings.py, backend/manage.py, backend/requirements.txt, backend/core/*, index.html, manifest.webmanifest.
- Previous phase seeded DB and passed 20 tests, but env was reset (Django not installed, server down).

Goal — Verify only, no new scaffold:
- Run `pip install -q -r backend/requirements.txt`, `python backend/manage.py check` → 0 issues, `python backend/manage.py check --deploy` → document warnings, `ls backend/locale/*/LC_MESSAGES/django.po` exists.
- Confirm `rivin/settings.py` has: SECRET_KEY from env, DEBUG from env, ALLOWED_HOSTS from env, DATABASES fallback sqlite + DATABASE_URL, LANGUAGE_CODE=bn, LANGUAGES bn/en/ar, LOCALE_PATHS, LANGUAGE_COOKIE_NAME=rivin_lang, CACHES LocMem, MIDDLEWARE order Session→Locale→core.middleware.LanguageDetectionMiddleware→Common, TEMPLATES i18n context, STATIC/MEDIA WhiteNoise.
- Report file tree `find backend -type f | sort`, env `TRUST_COUNTRY_HEADER` value, and `index.html` title contains RIVIN.

Constraints: Do NOT run makemigrations/migrate, do NOT edit settings except to fix missing import.

Acceptance: check 0, locale 3 .po files present, README mentions Render+Cloudflare. Report after.
```

---

## PROMPT 2/6 — Models & Migrations Verify (Catalog foundation)

```
You are Agent Mode, CONTINUE. Do NOT recreate models.

Context: backend/shop/models.py already has 12 models with TrilingualNameMixin.

Goal — Verify models & migrations without overwrite:
- Read backend/shop/models.py: confirm Category(Product), Product(sku, name_bn/en/ar, category, price, stock, emoji, image 2MB validator), TrilingualNameMixin.display_name fallback, money_field Decimal(10,2).
- Verify `backend/shop/migrations/0001_initial.py` exists and `python backend/manage.py showmigrations shop` → [X] 0001_initial.
- Via shell: `Category.objects.count()==6`, `Product.objects.count()==24`, bestsellers 4, print 2 products display_name bn/en/ar.
- If counts mismatch, run `python backend/manage.py seed_rivin` idempotently (do NOT recreate file).
- Run `python backend/manage.py test shop --verbosity=1` catalog subset → pass.

Constraints: Do NOT edit models.py unless validation missing.

Acceptance: 6 cats 24 prods verified, migration applied, 2 products print bn/en/ar correctly. Report.
```

---

## PROMPT 3/6 — Models & Migrations Verify (Order & Fulfillment)

```
You are Agent Mode, CONTINUE. Do NOT overwrite.

Context: Order lifecycle already scaffolded.

Goal — Verify Order stack:
- Read shop/models.py: confirm Customer, Order(order_no ORD-YYYY-######, subtotal/delivery/discount/total, status choices, ALLOWED_TRANSITIONS, transition_to raises InvalidOrderTransition, total computed before order_no), OrderItem(snapshot JSON), OrderStatusHistory, StockMovement, AuditLog, Coupon, DeliveryZone, SiteSetting singleton.
- Verify via shell: `Order.objects.count()>=2`, `ORD-2026-000001` exists, try `transition_to(CONFIRMED)` then invalid `PLACED` blocked, history length.
- Test stock decrement: `Product SKU rivin-0008 stock` after order.
- Coupon WELCOME10 percent 10 valid.

Constraints: No new models.

Acceptance: Order state machine valid/invalid both verified, history created, coupon discount 95 on 950. Report.
```

---

## PROMPT 4/6 — i18n/API Verify (Trilingual + Geo)

```
You are Agent Mode, CONTINUE.

Goal — Verify i18n/API without overwriting core/geo.py, middleware, api.py:
- Read core/geo.py: ARABIC 24, BENGALI {BD}, SUPPORTED, functions country/language parsers.
- Read core/middleware.py: priority ?lang > cookie rivin_lang > (TRUST) country > Accept-Language > bn, sets request.language_source, Content-Language, sticky cookie.
- Check rivin/settings.py TRUST_COUNTRY_HEADER env, MIDDLEWARE order, LOCALE_PATHS, 3 .po files 35 strings each.
- Restart server `TRUST_COUNTRY_HEADER=True python backend/manage.py runserver 0.0.0.0:8000 --noreload` in background, then curl:
  - `GET /api/v1/products/?lang=bn` → ltr খাতা, `?lang=ar` → rtl صمغ
  - `GET /api/v1/geo/language/` → default bn, with `Accept-Language: ar-EG` → ar, with `CF-IPCountry: SA` (TRUST True) → ar country:SA, (TRUST False) → bn
  - `GET /api/v1/products/rivin-0001/?lang=ar` vs `Accept-Language: ar` → both rtl
  - `GET /` → 200 HTML 21840, Content-Language bn, `dir` toggles.

Constraints: Do NOT regenerate .po, only verify.

Acceptance: All 6 curls pass with expected dir/lang. Report.
```

---

## PROMPT 5/6 — Tests & Final Checks (Core suite)

```
You are Agent Mode, CONTINUE.

Goal — Full test suite, no overwrite:
- Run `python backend/manage.py test core shop --verbosity=2` → 20 passed (10 geo + 10 shop). If any fail, fix bug without overwriting whole file (patch Order.save total before order_no etc.).
- Verify 2 added shims: backend/core/tests.py and backend/shop/tests.py import correctly so `test core shop` discovers.
- Document `makemigrations --check --dry-run` → no changes.
- Keep W001 as deploy-only (Tags.security, deploy=True) so `check` 0, `check --deploy` shows security warnings.

Constraints: Do NOT add new test files unless missing case.

Acceptance: 20 tests OK, check 0, check --deploy documented. Report.
```

---

## PROMPT 6/6 — Seed, Docs & CI Final (Launch ready without Paid)

```
You are Agent Mode, CONTINUE — Final phase before experimental launch.

Goal — Docs & seed, no new code overwrite:
- Ensure `seed_rivin` idempotent, bestsellers 4, SiteSetting delivery 60 min 300.
- Verify `index.html` 339 lines RIVIN, `manifest.webmanifest` name RIVIN, `PROMPT_RIVIN.md` + `ECOMMERCE_MAP_RIVIN.md` present.
- Verify `.github/workflows/backend.yml` matrix sqlite+postgres, `compilemessages --ignore`.
- Create/verify `IMPLEMENTATION_NOTE.md` with honest execution log (pip, check, makemigrations, migrate, seed, test 20, live curls).
- Update `README.md` quick start: `cp .env.example .env`, `migrate`, `seed_rivin`, `runserver 0.0.0.0:8000`, TRUST flag note for Cloudflare.
- Ensure no Paid deps: grep S3/Redis/Celery should be optional/local only.

Constraints: No paid gateway/SMS, local media only.

Acceptance: seed counts verified, sitemap stub check, README has Render+Cloudflare Free steps, CI file present. Report and tag v0.1.0-rivin suggestion.

Deliverable: Final report with file tree + test log.
```

---

## Memory (Not shown now, kept for next batch)

- **PROMPT 7/9 — Excel Import** (`import_products` openpyxl/CSV, template download)
- **PROMPT 8/9 — Media Hardening** (local `media/products` 2MB, admin low-stock, StockMovement audit)
- **PROMPT 9/9 — Deploy** (Render Postgres Free + Cloudflare DNS, env, sleep note, domain)

These 3 will be given after 1-6 are merged phase-by-phase.
