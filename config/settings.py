from pathlib import Path
from decouple import config, Csv
from decimal import Decimal
import mimetypes
import dj_database_url

mimetypes.add_type("text/css", ".css", True)
mimetypes.add_type("text/javascript", ".js", True)

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ─── Core ─────────────────────────────────────────────────────────────────────
SECRET_KEY = config('SECRET_KEY')

DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='127.0.0.1,localhost',
    cast=Csv(),
)

# Always allow local dev — prevents DisallowedHost when running runserver locally
for _local_host in ('127.0.0.1', 'localhost'):
    if _local_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_local_host)

# Auto-include Railway's public domain so healthchecks and traffic are accepted
_railway_public_domain = config('RAILWAY_PUBLIC_DOMAIN', default='')
if _railway_public_domain and _railway_public_domain not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_railway_public_domain)

# Railway also uses the private networking hostname
_railway_private_domain = config('RAILWAY_PRIVATE_DOMAIN', default='')
if _railway_private_domain and _railway_private_domain not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_railway_private_domain)

# Railway healthcheck probes use this hostname — must be explicitly allowed
if 'healthcheck.railway.app' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('healthcheck.railway.app')

# ─── Applications ─────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'storages',

    # Our apps
    'accounts',
    'cooks',
    'orders',
    'delivery',
    'reviews',
    'notifications',
    'billing',
    'admin_panel',
]

# ─── Middleware ────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # Serve static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ─── Database ─────────────────────────────────────────────────────────────────
# Prefer DATABASE_URL (Railway auto-injects this) over individual env vars.
_DATABASE_URL = config('DATABASE_URL', default='')

if _DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(
            _DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='postgres'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }

# ─── Password Validation ───────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─── Internationalisation ─────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# ─── Static files ─────────────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise — compressed + cached static files in production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ─── Media / Supabase Storage (S3-compatible) ────────────────────────────────
_SUPABASE_URL        = config('SUPABASE_URL', default='')          # https://<ref>.supabase.co
_SUPABASE_KEY        = config('SUPABASE_S3_ACCESS_KEY_ID', default='')
_SUPABASE_SECRET     = config('SUPABASE_S3_SECRET_ACCESS_KEY', default='')
_SUPABASE_BUCKET     = config('SUPABASE_STORAGE_BUCKET', default='media')
_SUPABASE_REGION     = config('SUPABASE_S3_REGION', default='ap-south-1')

if all([_SUPABASE_URL, _SUPABASE_KEY, _SUPABASE_SECRET]):
    # Use Supabase S3-compatible storage
    DEFAULT_FILE_STORAGE  = 'storages.backends.s3boto3.S3Boto3Storage'

    AWS_ACCESS_KEY_ID       = _SUPABASE_KEY
    AWS_SECRET_ACCESS_KEY   = _SUPABASE_SECRET
    AWS_STORAGE_BUCKET_NAME = _SUPABASE_BUCKET
    AWS_S3_REGION_NAME      = _SUPABASE_REGION
    AWS_S3_ENDPOINT_URL     = f'{_SUPABASE_URL}/storage/v1/s3'

    # Files are publicly readable via Supabase CDN URL
    AWS_S3_CUSTOM_DOMAIN    = f'{_SUPABASE_URL.replace("https://", "")}/storage/v1/object/public/{_SUPABASE_BUCKET}'
    MEDIA_URL               = f'https://{AWS_S3_CUSTOM_DOMAIN}/'

    AWS_DEFAULT_ACL         = 'public-read'
    AWS_QUERYSTRING_AUTH    = False   # Use public URLs, not signed URLs
    AWS_S3_FILE_OVERWRITE   = False   # Keep unique filenames
else:
    # Local fallback — store files on disk
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    MEDIA_URL  = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

# ─── Auth ─────────────────────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'accounts.User'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# ─── Sessions ─────────────────────────────────────────────────────────────────
SESSION_COOKIE_AGE = 1209600       # 2 weeks
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True

# ─── Email ────────────────────────────────────────────────────────────────────
EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = 'smtp.gmail.com'
EMAIL_PORT          = 587
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL  = config('EMAIL_HOST_USER')

# ─── Payments ─────────────────────────────────────────────────────────────────
RAZORPAY_KEY_ID     = config('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = config('RAZORPAY_KEY_SECRET')

# ─── Billing ──────────────────────────────────────────────────────────────────
PLATFORM_UPI_ID       = config('PLATFORM_UPI_ID', default='gharkhana@icici')
PLATFORM_FEE_RATE     = Decimal(config('PLATFORM_FEE_RATE',     default='0.20'))
COOK_COMMISSION_RATE  = Decimal(config('COOK_COMMISSION_RATE',  default='5.00'))

# ─── Security (production only) ───────────────────────────────────────────────
if not DEBUG:
    # HTTPS enforcement
    # SECURE_SSL_REDIRECT is intentionally False on Railway:
    # Railway terminates TLS at its load balancer and forwards requests
    # internally over plain HTTP, so enabling the redirect causes an
    # infinite redirect loop.  SECURE_PROXY_SSL_HEADER tells Django the
    # original connection was HTTPS, which is all we need.
    SECURE_SSL_REDIRECT          = False
    SECURE_PROXY_SSL_HEADER      = ('HTTP_X_FORWARDED_PROTO', 'https')

    # HSTS — tell browsers to always use HTTPS
    SECURE_HSTS_SECONDS          = 31536000   # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD          = True

    # Cookie security
    SESSION_COOKIE_SECURE        = True
    CSRF_COOKIE_SECURE           = True

    # Clickjacking / content-type protection
    X_FRAME_OPTIONS              = 'DENY'
    SECURE_CONTENT_TYPE_NOSNIFF  = True
    SECURE_BROWSER_XSS_FILTER    = True

    # CSRF trusted origins — Railway HTTPS domain (set RAILWAY_PUBLIC_DOMAIN in env)
    _railway_domain = config('RAILWAY_PUBLIC_DOMAIN', default='')
    _extra_origins  = config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())
    CSRF_TRUSTED_ORIGINS = (
        [f'https://{_railway_domain}'] if _railway_domain else []
    ) + list(_extra_origins)
