# RIVIN E-commerce — কী কী লাগে (Full Map)

> **ব্র্যান্ড:** RIVIN (রিভিন) — এক্সপেরিমেন্টাল, কোনো Paid সার্ভিস নয়
> **ভাষা:** `bn` ডিফল্ট / `en` / `ar` (RTL) — দেশ অনুযায়ী অটো
> **Deploy:** Cloudflare (DNS + CDN, Free) + Render (App + Postgres Free)
> **DB:** Render Postgres Free (school system-এর মতো) — বিকল্প: SQLite (dev), পরে Cloudflare D1 নয় (Django-র সাথে ঝামেলা)
> **তারিখ:** 2026-09-17

এই ম্যাপ দেখে বুঝবে একটা ই-কমার্সে আসলে কত লেয়ার থাকে। নিচের প্রতিটা বক্স একে অপরের উপর দাঁড়ায় — নিচ থেকে উপরে বানালে ভিত শক্ত হয়।

```
┌─────────────────────────────────────────────────────────────────┐
│  7. OPERATIONS & GROWTH                                         │
│  Backup · SEO/sitemap · Analytics · SMS · Coupon · Review       │
├─────────────────────────────────────────────────────────────────┤
│  6. PAYMENT & TRUST                                             │
│  COD · bKash manual TrxID verify · Order state machine · Audit  │
├─────────────────────────────────────────────────────────────────┤
│  5. PEOPLE                                                      │
│  Customer (mobile) · Admin groups · Auth · Permission           │
├─────────────────────────────────────────────────────────────────┤
│  4. ORDER & FULFILLMENT                                         │
│  Cart (localStorage) · Checkout · OrderNo · Invoice · Tracking  │
├─────────────────────────────────────────────────────────────────┤
│  3. CATALOG                                                     │
│  Category · Product (bn/en/ar + stock + image) · Search · Bestseller │
├─────────────────────────────────────────────────────────────────┤
│  2. PLATFORM CORE                                               │
│  Django + i18n/RTL + Geo-middleware + API (JSON) + PWA shell   │
├─────────────────────────────────────────────────────────────────┤
│  1. FOUNDATION                                                  │
│  Repo rivin-shop · Render + Cloudflare · Env · CI · DB · Domain│
└─────────────────────────────────────────────────────────────────┘
```

---

## ১. FOUNDATION — ভিত (না হলে সব ভেঙে পড়বে)

| লাগবে | কী করবে | Paid? | Free বিকল্প |
|-------|---------|-------|-------------|
| **GitHub Repo** | `rivin-shop` (private, 1 commit = 1 PR) | Free | - |
| **Domain** | `rivin.yourdomain.com` বা `rivin.onrender.com` | Free (.onrender) | Cloudflare Free DNS |
| **App Host** | Render Web Service (Gunicorn + WhiteNoise) | Free (sleep) | - |
| **DB** | Render Postgres Free (1GB) | Free | SQLite (dev) — Render disk ephemeral তাই prod-এ Postgres |
| **CDN/DNS** | Cloudflare (Free) — `CF-IPCountry` header দেয় | Free | - |
| **Env** | `.env` → `SECRET_KEY, DEBUG, DATABASE_URL, TRUST_COUNTRY_HEADER, ALLOWED_HOSTS` | - | - |
| **CI** | GitHub Actions `check + makemigrations --check + test core shop` | Free | - |
| **Secrets** | Render Environment Variables | - | - |

**ডিসিশন:** School system যেমন Render-এ, RIVIN-ও Render + Cloudflare Free — নতুন Paid DB নয়।

---

## ২. PLATFORM CORE — ভাষা ও ফ্রেম

| লাগবে | বিবরণ |
|-------|--------|
| **Django 5.2+** | Python 3.13, `USE_I18N=True`, `LANGUAGE_CODE=bn`, `LANGUAGES=[bn,en,ar]`, `LOCALE_PATHS` |
| **LocaleMiddleware + Geo-middleware** | `?lang=` > `rivin_lang` cookie > (TRUST) `CF-IPCountry` > `Accept-Language` > `bn`. `ar` হলে `dir=rtl` |
| **API** | Plain Django `JsonResponse` (DRF নয়) — `/api/v1/...` same-origin, no CORS |
| **PWA Shell** | `index.html` (mobile-first, Bangla-first), `manifest.webmanifest`, offline fallback 24 products |
| **Cache** | `LocMemCache` (rate-limit), prod-এ চাইলে Redis নয় — Free রাখতে LocMem-ই |
| **Static** | WhiteNoise `staticfiles` |

---

## ৩. CATALOG — দোকানের আলমারি

| Model | ফিল্ড | নোট |
|-------|-------|-----|
| **Category** | `code, name_bn/en/ar, emoji, sort_order, is_active` | 6টা (stationery...) |
| **Product** | `sku, name_bn/en/ar, category, price, mrp, stock, emoji, image, link, is_active, is_bestseller` | `stock` 0 হলে Add to cart block, `image` local `media/` (S3 নয়, Free) |
| **Search** | `?q=` → `name_bn/en/ar, sku` icontains | Frontend `?category=` filter |
| **Bestseller** | `SiteSetting.bestsellers M2M` → `/api/v1/settings/` | হোমে ৪টা |
| **Seed** | `seed_rivin` command — ২৪ ডেমো, পরে ৩১১ Excel import | Idempotent |

---

## ৪. ORDER & FULFILLMENT — বিক্রির প্রাণ

| লাগবে | বিবরণ |
|-------|--------|
| **Cart** | Frontend `localStorage` (`rivin_cart`), qty, price string |
| **Checkout** | `customer {name, mobile, address}` + `items [{sku,qty}]` + `coupon_code` |
| **Order** | `order_no=ORD-YYYY-######` collision-safe, `subtotal + delivery_fee(৳60) - discount = total`, `total = Decimal` |
| **OrderItem** | `product_name_snapshot {bn,en,ar} + unit_price_snapshot` — immutable |
| **Validation** | Min order ৳300, stock check, `MinValue(0)` money |
| **Tracking** | `GET /api/v1/orders/<no>/`, `GET /orders/mine/?mobile=`, `history[]` |
| **Media** | Order-এ কোনো Paid invoice PDF নয় — HTML receipt |

---

## ৫. PEOPLE — মানুষ

| Role | কী করবে |
|------|---------|
| **Customer** | `name, mobile (unique-ish), address, preferred_language, country_code` — OTP নয় (Free রাখতে), mobile-ই ID |
| **Admin Groups** | `ShopAdmin (all), Catalog, OrderDesk, Accounts, Delivery` — `post_migrate` এ auto |
| **Auth** | Django `auth` + `admin` — `ADMIN_PIN=1234` নয় |
| **Permission** | `Order.transition_to` শুধু allowed group পারবে (future) |

---

## ৬. PAYMENT & TRUST — টাকার জায়গায় ভরসা

| লাগবে | Paid? | Free উপায় |
|-------|-------|------------|
| **COD** | Free | Default `payment_method=cod`, `payment_status=unpaid→paid` manual |
| **bKash Manual** | Free | Customer `TrxID` লিখবে, Admin `paid` করবে — SSLCommerz নয় |
| **Coupon** | Free | `WELCOME10` percent/fixed, `is_valid_for` check |
| **State Machine** | Free | `PLACED→CONFIRMED→PACKED→OUT_FOR_DELIVERY→DELIVERED`, `CANCELLED/RETURNED`, `OrderStatusHistory` |
| **Audit** | Free | `AuditLog, StockMovement` — কে দাম/স্টক বদলালো |

---

## ৭. OPERATIONS & GROWTH — দোকান চলবে কীভাবে

| লাগবে | Paid? | Free |
|-------|-------|------|
| **Backup** | Free | `pg_dump` cron + Render backup (manual), docs |
| **Image Upload** | Free | `media/products/` local, 2MB validator (S3 নয়) |
| **Review** | Free | `rating 1-5 + emoji + comment` → `POST /orders/<no>/review/` |
| **DeliveryZone** | Free | `Dhaka ৳60` ভবিষ্যতে বাড়বে |
| **SMS** | Skip (Paid) | Status change এ Email/WhatsApp free link only |
| **SEO** | Free | `sitemap.xml`, `meta`, server-rendered product page (future) |
| **Analytics** | Free | Cloudflare Web Analytics (Free) বা Plausible self-host নয় |
| **.po Translation** | Free | `bn/en/ar` 35 string, `compilemessages` (gettext optional) |

---

## এক নজরে Data Model (12 Model)

```
Category ─┬─ Product ─┬─ OrderItem ─┬─ Order ─┬─ OrderStatusHistory
          │           │             │         ├─ Customer
          │           │             │         ├─ Coupon
          │           └─ StockMovement       ├─ Review
          │                                  └─ AuditLog
          └─ SiteSetting (singleton) ─┬─ DeliveryZone
                                      └─ bestsellers M2M Product
```

---

## কেন "শুরু থেকে" ভালো?

- আগের `backend/` স্ক্যাফোল্ডটি ভালো ছিল কিন্তু `PROMPT_RIVIN.md` একবারে ১১ সেকশন — এক সেশনে হজম হয় না, মডিফাই করতে গিয়ে `order_no`, `money_field` বাগ ধরতে হয়েছে
- ফ্রেশ `rivin-shop` রিপোতে প্রতি সেশনে ১টি clean PR, `git log` পড়া যায়, `school-management-system`-এর PR discipline (205 commit) ফলো করা যায়
- কোনো legacy Firebase `index.html` (3699 লাইন) টানতে হবে না — ৩৩৯ লাইনের clean PWA দিয়ে শুরু

**পরের পাতা:** `SESSION_PROMPTS_RIVIN.md` — ৬টি সেশন-কমফোর্ট প্রম্পট, কপি-পেস্ট করে Agent Mode-এ চালালেই প্রতিটি সেশন ২০-৪০ মিনিটে শেষ।
