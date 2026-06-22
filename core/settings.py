from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

_secret_key = os.environ.get('SECRET_KEY', '').strip()
if not _secret_key:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured(
        'SECRET_KEY muhit o\'zgaruvchisi o\'rnatilmagan. '
        'python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" '
        'bilan yangisini oling va .env ga yozing.'
    )
SECRET_KEY = _secret_key

# Production uchun DEBUG=False bo'lishi SHART. Lokal dev uchun .env da DEBUG=True qo'ying.
DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 'yes')

# Production uchun ALLOWED_HOSTS ni .env da ko'rsating (vergul bilan ajratilgan)
_hosts = os.environ.get('ALLOWED_HOSTS', '').strip()
if _hosts:
    ALLOWED_HOSTS = [h.strip() for h in _hosts.split(',') if h.strip()]
elif DEBUG:
    ALLOWED_HOSTS = ['*']  # Lokal dev va testlar uchun — production da DEBUG=False bo'lishi SHART
else:
    ALLOWED_HOSTS = []

# CSRF trusted origins — DEBUG holatidan qat'i nazar har doim qo'llanadi
# (HTTPS proksisi orqasidagi hosting uchun zarur, masalan Railway/Render)
_csrf_origins = os.environ.get('CSRF_TRUSTED_ORIGINS', '').strip()
if _csrf_origins:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_origins.split(',') if o.strip()]

# Security hardening — only enforced when DEBUG is off (production)
if not DEBUG:
    SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True').lower() in ('true', '1', 'yes')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    # Railway/Render kabi reverse-proxy orqali kelgan HTTPS ni Django tan olishi uchun
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

_CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME', '')

GOOGLE_ANALYTICS_ID = os.environ.get('GOOGLE_ANALYTICS_ID', '')

import sys as _sys
_TESTING = 'test' in _sys.argv or ('pytest' in _sys.argv[0] if _sys.argv else False)
TESTING = _TESTING  # Views uchun ochiq flag

CACHES = {
    'default': (
        # Test paytida DummyCache — rate limit testlar orasida saqlanmaydi
        {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}
        if _TESTING else
        {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'standardbridge'}
    )
}

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.sites',
    *(['cloudinary_storage', 'cloudinary'] if _CLOUDINARY_CLOUD_NAME else []),
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'accounts',
    'analysis',
    'experts',
    'blog',
    'qms',
    'expert_tools',
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.ContentSecurityPolicyMiddleware',
]

ROOT_URLCONF = 'core.urls'

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
                'core.context_processors.notifications_count',
                'core.context_processors.language_context',
                'core.context_processors.profile_completeness',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Baza: DATABASE_URL env bo'lsa (production, masalan Postgres) — o'shani ishlatadi,
# aks holda lokal SQLite. Hostingda DATABASE_URL ni o'rnating.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

_database_url = os.environ.get('DATABASE_URL', '').strip()
if _database_url:
    import dj_database_url
    DATABASES['default'] = dj_database_url.parse(_database_url, conn_max_age=600)

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTH_USER_MODEL = 'accounts.CustomUser'

LANGUAGE_CODE = 'uz-uz'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
# static/ papkasini faqat mavjud bo'lsa qo'shamiz (bo'sh papka git'da saqlanmaydi → W004 ogohlantirish)
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Cloudinary — production'da media fayllarni doimiy saqlash uchun
if _CLOUDINARY_CLOUD_NAME:
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': _CLOUDINARY_CLOUD_NAME,
        'API_KEY': os.environ.get('CLOUDINARY_API_KEY', ''),
        'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET', ''),
    }

# WhiteNoise — production'da statik fayllarni samarali uzatadi (siqilgan + keshlangan)
STORAGES = {
    'default': (
        {'BACKEND': 'cloudinary_storage.storage.RawMediaCloudinaryStorage'}
        if _CLOUDINARY_CLOUD_NAME else
        {'BACKEND': 'django.core.files.storage.FileSystemStorage'}
    ),
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Email — real credentials bo'lsa SMTP, aks holda console (dev/test uchun)
_email_user = os.environ.get('EMAIL_HOST_USER', '').strip()
_email_pass = os.environ.get('EMAIL_HOST_PASSWORD', '').strip()
_email_configured = (
    bool(_email_user) and bool(_email_pass)
    and _email_user not in ('your_email@gmail.com', 'noreply@standardbridge.uz')
    and _email_pass != 'your_app_password_here'
)
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = _email_user
EMAIL_HOST_PASSWORD = _email_pass
DEFAULT_FROM_EMAIL = f'StandardBridge <{_email_user or "noreply@standardbridge.uz"}>'
EMAIL_BACKEND = (
    'django.core.mail.backends.smtp.EmailBackend'
    if _email_configured else
    'django.core.mail.backends.console.EmailBackend'
)

# Sayt URL — email/Telegram linklari uchun (Railway da SITE_URL env ni o'rnating)
SITE_URL = os.environ.get('SITE_URL', 'https://standardbridge.uz')

# AI (Groq)
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
AI_TIMEOUT = int(os.environ.get('AI_TIMEOUT', '45'))

# Karta raqamlarini shifrlash uchun Fernet kalit
# Production: FERNET_KEY=<base64 32-bayt kalit> .env ga yozing
# Kalit generatsiya: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
_fernet_key = os.environ.get('FERNET_KEY', '').strip()
if _fernet_key:
    FERNET_KEY = _fernet_key
else:
    if not DEBUG:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured('FERNET_KEY muhit o\'zgaruvchisi o\'rnatilmagan. Production uchun majburiy.')
    # DEBUG: barqaror kalit .env ga yozilmagan bo'lsa — faylga keshlab saqla
    import base64
    _key_file = BASE_DIR / '.fernet_dev_key'
    if _key_file.exists():
        FERNET_KEY = _key_file.read_text().strip()
    else:
        from cryptography.fernet import Fernet as _Fernet
        FERNET_KEY = _Fernet.generate_key().decode()
        _key_file.write_text(FERNET_KEY)

# Telegram bot
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_BOT_USERNAME = os.environ.get('TELEGRAM_BOT_USERNAME', '')
TELEGRAM_WEBHOOK_SECRET = os.environ.get('TELEGRAM_WEBHOOK_SECRET', '')

# Click payment
CLICK_SERVICE_ID = os.environ.get('CLICK_SERVICE_ID', '')
CLICK_MERCHANT_ID = os.environ.get('CLICK_MERCHANT_ID', '')
CLICK_SECRET_KEY = os.environ.get('CLICK_SECRET_KEY', '')
CLICK_RETURN_URL = os.environ.get('CLICK_RETURN_URL', 'http://127.0.0.1:8000')

# Google OAuth (django-allauth)
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.environ.get('GOOGLE_CLIENT_ID', ''),
            'secret': os.environ.get('GOOGLE_CLIENT_SECRET', ''),
            'key': '',
        },
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
    }
}

# allauth settings
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_LOGIN_ON_GET = True
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_ADAPTER = 'accounts.adapters.AccountAdapter'
SOCIALACCOUNT_ADAPTER = 'accounts.adapters.SocialAccountAdapter'

# --- Logging ---
# Konsolga + fayllarga yozadi. Production'da AI/to'lov xatolarini kuzatish uchun.
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} [{levelname}] {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'app.log',
            'maxBytes': 5 * 1024 * 1024,  # 5 MB
            'backupCount': 3,
            'formatter': 'verbose',
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'error.log',
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 3,
            'level': 'ERROR',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        # Loyiha kodimiz uchun: logging.getLogger('standardbridge')
        'standardbridge': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}