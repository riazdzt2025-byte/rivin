# RIVIN Backend

Django 5.2+ • Python 3.11+ • i18n bn/en/ar • Geo auto-language

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env   # edit SECRET_KEY
python backend/manage.py makemigrations core shop
python backend/manage.py migrate
python backend/manage.py createsuperuser
# optional: compile translations (needs gettext)
python backend/manage.py compilemessages
python backend/manage.py runserver 0.0.0.0:8000
```

API: http://localhost:8000/api/v1/products/?lang=bn

## i18n

- Default `bn`. Supported `bn, en, ar` (ar = RTL).
- Auto-detection chain: `?lang=` > cookie `rivin_lang` > (if `TRUST_COUNTRY_HEADER=True`) CDN country header > `Accept-Language` > default.
- Product/Category store `name_bn/en/ar`; `display_name(lang)` with fallback.
- `.po` in `backend/locale/*/LC_MESSAGES/django.po` → `compilemessages` → `.mo` git-ignored.
- Frontend: `<html dir="{% if LANGUAGE_BIDI %}rtl{% else %}ltr{% endif %}">`
- Debug: `GET /api/v1/geo/language/` shows `{detected, source, country}`.

Production behind Cloudflare: set `TRUST_COUNTRY_HEADER=True` to honor `CF-IPCountry`.

## Tests

```bash
python backend/manage.py test --verbosity=2
# geo: BD->bn, SA->ar, spoofing ignored when TRUST=False, q-value, cookie wins
# models: trilingual fallback, money/stock validation, order_no, state machine, coupon
# api: ?lang=ar => rtl
```
