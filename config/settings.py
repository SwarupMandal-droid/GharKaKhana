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

# ─── Applications ─────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'cloudinary',
    'cloudinary_storage',

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
            'ENGINE': 'django.db.backends.mysql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            },
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

# ─── Media / Cloudinary ───────────────────────────────────────────────────────
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': config('CLOUDINARY_CLOUD_NAME', default=''),
    'API_KEY':    config('CLOUDINARY_API_KEY',    default=''),
    'API_SECRET': config('CLOUDINARY_API_SECRET', default=''),
}

# Use Cloudinary for media only when credentials are provided
if all([
    config('CLOUDINARY_CLOUD_NAME', default=''),
    config('CLOUDINARY_API_KEY',    default=''),
    config('CLOUDINARY_API_SECRET', default=''),
]):
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    MEDIA_URL = '/media/'  # Cloudinary rewrites this automatically
else:
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    MEDIA_URL = '/media/'
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
    SECURE_SSL_REDIRECT          = True
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
