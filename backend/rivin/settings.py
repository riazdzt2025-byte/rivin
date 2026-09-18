"""
RIVIN — Django settings. Mirrors school-management-system discipline.
- TRUST_COUNTRY_HEADER guards spoofable geo header
- i18n: bn (default) / en / ar (RTL)
"""
from pathlib import Path
import os

try:
    from dotenv import load_dotenv
    load_dotenv  # keep reference
    from dotenv import load_dotenv as _ld
    _ld(Path(__file__).resolve().parent.parent / '.env')
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-insecure-key-change-me-please-set-env')
DEBUG = os.environ.get('DEBUG', 'True').lower() in ('1', 'true', 'yes', 'on')
ALLOWED_HOSTS = [h.strip() for h in os.environ.get('ALLOWED_HOSTS', '*').split(',') if h.strip()]
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()]

# Language / i18n — PROMPT section 2 & 3
LANGUAGE_CODE = os.environ.get('LANGUAGE_CODE', 'bn')
LANGUAGES = [
    ('bn', 'বাংলা'),
    ('en', 'English'),
    ('ar', 'العربية'),
]
LOCALE_PATHS = [BASE_DIR / 'locale']
LANGUAGE_COOKIE_NAME = 'rivin_lang'
LANGUAGE_COOKIE_HTTPONLY = False  # JS needs to read for switcher
LANGUAGE_COOKIE_SAMESITE = 'Lax'
LANGUAGE_COOKIE_AGE = 365 * 24 * 3600
USE_I18N = True
USE_TZ = True
TIME_ZONE = os.environ.get('TIME_ZONE', 'Asia/Dhaka')

# Geo trust flag — section 3
TRUST_COUNTRY_HEADER = os.environ.get('TRUST_COUNTRY_HEADER', 'False').lower() in ('1','true','yes','on')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'core',
    'shop',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise optional — if installed, serves static
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',          # 1) cookie/session -> LANGUAGE_CODE
    'core.middleware.LanguageDetectionMiddleware',        # 2) geo + Accept-Language wins
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Insert WhiteNoise if available (do not hard-depend)
try:
    import whitenoise  # noqa
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
    WHITENOISE_AUTOREFRESH = DEBUG
except ImportError:
    pass

ROOT_URLCONF = 'rivin.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
            ],
        },
    },
]

WSGI_APPLICATION = 'rivin.wsgi.application'

# Database — DATABASE_URL -> Postgres, else SQLite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
if os.environ.get('DATABASE_URL'):
    try:
        import dj_database_url
        DATABASES['default'] = dj_database_url.config(
            conn_max_age=600,
            ssl_require=os.environ.get('PGSSLMODE') == 'require',
        )
    except ImportError:
        pass  # keep sqlite if dj-database-url not installed

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Static / Media
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Optional S3 (mirrors school system USE_S3)
if os.environ.get('USE_S3', 'False').lower() in ('1','true','yes','on'):
    try:
        INSTALLED_APPS  # already defined
        # django-storages[boto3] expected
        STORAGES = {
            "default": {"BACKEND": "storages.backends.s3.S3Storage"},
            "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage" if 'whitenoise.storage' in str(MIDDLEWARE) else "django.contrib.staticfiles.storage.StaticFilesStorage"},
        }
        AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', '')
        AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'ap-southeast-1')
        AWS_DEFAULT_ACL = None
        AWS_S3_FILE_OVERWRITE = False
    except Exception:
        pass
else:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
    # WhiteNoise compressed if available
    try:
        import whitenoise  # noqa
        STORAGES["staticfiles"] = {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"}
    except ImportError:
        pass

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Rate limit for order creation (mirrors school P1-9)
RIVIN_ORDER_RATE_LIMIT = int(os.environ.get('RIVIN_ORDER_RATE_LIMIT', '5'))  # 5 per window
RIVIN_ORDER_RATE_WINDOW = int(os.environ.get('RIVIN_ORDER_RATE_WINDOW', '600'))  # 10 min

# Logging minimal
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'INFO'},
}

# Cache — LocMem for dev (rate-limit). In prod use Redis if available.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'rivin-locmem',
    }
}
