from pathlib import Path
from datetime import timedelta
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-change-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'accounts',
    'applications',
    'documents',
    'payments',
    'workflow',
    'notifications',
    'audit',
    'config',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'snrms.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'snrms.wsgi.application'

# If DATABASE_URL is present (e.g. Fly.io Postgres attach), use it; otherwise
# fall back to the discrete DB_* variables used by local dev and docker-compose.
DATABASE_URL = config('DATABASE_URL', default='')
if DATABASE_URL:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600),
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='snrms'),
            'USER': config('DB_USER', default='snrms'),
            'PASSWORD': config('DB_PASSWORD', default='snrms'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }

AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Lagos'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

KOBO_API_TOKEN = config('KOBO_API_TOKEN', default='')

CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://localhost:3000',
    'http://127.0.0.1:5173',
]
CORS_ALLOW_CREDENTIALS = True

# Allow the committee second-tier token header through CORS (browsers strip
# non-default custom request headers otherwise, which silently breaks the
# committee console when the frontend and API are on different origins).
from corsheaders.defaults import default_headers as _default_cors_headers  # noqa: E402
CORS_ALLOW_HEADERS = list(_default_cors_headers) + ['x-committee-member']

FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# --- Payment gateway (Ibeju Pay) ---
# Leave IBEJUPAY_SECRET_KEY blank for demo mode (applicants can simulate payment).
# Add your Ibeju Pay keys to enable real checkout:
#   IBEJUPAY_SECRET_KEY   -> sk_test_... / sk_live_...  (server-to-server API auth)
#   IBEJUPAY_PUBLIC_KEY   -> pk_test_... / pk_live_...  (optional, client-side)
#   IBEJUPAY_WEBHOOK_SECRET -> whsec_...  (verifies webhook signatures)
IBEJUPAY_SECRET_KEY = config('IBEJUPAY_SECRET_KEY', default='')
IBEJUPAY_PUBLIC_KEY = config('IBEJUPAY_PUBLIC_KEY', default='')
IBEJUPAY_WEBHOOK_SECRET = config('IBEJUPAY_WEBHOOK_SECRET', default='')
IBEJUPAY_BASE_URL = config('IBEJUPAY_BASE_URL', default='https://ibejupay.com/api/v1')
PAYMENT_CALLBACK_URL = config('PAYMENT_CALLBACK_URL', default='http://localhost:5173/payment-callback')


# --- Static files (WhiteNoise, for production) ---
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

# --- Production hardening (driven by env; safe defaults for local dev) ---
CSRF_TRUSTED_ORIGINS = [o for o in config('CSRF_TRUSTED_ORIGINS', default='').split(',') if o]
_extra_cors = [o for o in config('CORS_ALLOWED_ORIGINS', default='').split(',') if o]
if _extra_cors:
    CORS_ALLOWED_ORIGINS = CORS_ALLOWED_ORIGINS + _extra_cors

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)

# --- Email (renewal & application notifications) ---
# Console backend by default: emails print to the server log, so the flow works
# with no mail account. Set EMAIL_HOST etc. in .env to send real email via SMTP.
EMAIL_HOST = config('EMAIL_HOST', default='')
if EMAIL_HOST:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
    EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
    EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
    EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = config(
    'DEFAULT_FROM_EMAIL', default='SNRMS Ibeju-Lekki <no-reply@ibeju-lekki.gov.ng>')

# Public base URL that receipt QR codes point to (a verification page).
RECEIPT_VERIFY_URL = config('RECEIPT_VERIFY_URL', default='http://localhost:5173/verify-receipt')

# Google Maps / Street View (for street pictures on the map & applicant picker).
GOOGLE_MAPS_API_KEY = config('GOOGLE_MAPS_API_KEY', default='')
