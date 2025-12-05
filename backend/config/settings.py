from pathlib import Path
import os
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
SECRET_KEY = config('SECRET_KEY', default='django-insecure-sgm7j#v5qz3_qj*lv995dzry3gul+dqpxz*a6g2e1pdgp5mnps')
DEBUG = config('DEBUG', default=False, cast=bool)

# Allow localhost and testserver for development and automated tests
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'testserver',
    '*.onrender.com',
    'rcrs.onrender.com',
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'apps.users.apps.UsersConfig',
    'apps.reports.apps.ReportsConfig',
    'apps.blockchain.apps.BlockchainConfig',
    'apps.dashboard.apps.DashboardConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # For static file serving in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Audit logging middleware
    'apps.reports.signals.AuditLogSignalMiddleware',
    'apps.reports.middleware.AuditLogMiddleware',
]

ROOT_URLCONF = 'config.urls'

# FIX: Add templates directory
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # ADD THIS LINE
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# FIX: Static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Include static files directory
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS Settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
]

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
}

# Email Configuration (for development)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# IPFS Configuration
IPFS_API_URL = 'http://127.0.0.1:5001'

# Cardano Configuration
CARDANO_NETWORK = 'preview'  # 'preview', 'preprod', or 'mainnet'
BLOCKFROST_PROJECT_ID = os.environ.get('BLOCKFROST_PROJECT_ID', 'previewIezrehG4AVtXRPP0dVMha1DHXrGNsfp8')

# Blockchain anchoring behavior
# When False, anchors are simulated (no real transaction broadcast)
# Switch to True only after configuring wallet and Blockfrost API key
ANCHOR_BROADCAST = os.environ.get('ANCHOR_BROADCAST', 'True').lower() == 'true'

# Cardano Wallet Configuration (for real transaction broadcasting)
# OPTION 1: Get test ADA from Preview testnet faucet (FREE)
#   - Visit: https://docs.cardano.org/cardano-testnet/tools/faucet/
#   - Request funds for your addr_test1... address
#   - Export keys from your wallet (Eternl, Nami, etc.) or use cardano-cli
#   - Set CARDANO_PAYMENT_ADDRESS to your funded address
#   - Set CARDANO_SIGNING_KEY_PATH to your payment.skey JSON file
#
# OPTION 2: Use cardano-cli to generate keys:
#   cardano-cli address key-gen --verification-key-file payment.vkey --signing-key-file payment.skey
#   cardano-cli address build --payment-verification-key-file payment.vkey --testnet-magic 2 --out-file payment.addr
#   # Then fund the address from faucet: https://docs.cardano.org/cardano-testnet/tools/faucet/
#
# Return unused test ADA when done to: addr_test1vqeux7xwusdju9dvsj8h7mca9aup2k439kfmwy773xxc2hcu7zy99
CARDANO_SIGNING_KEY_PATH = os.environ.get('CARDANO_SIGNING_KEY_PATH', str(BASE_DIR.parent / 'backend' / 'keys' / 'payment.skey'))
CARDANO_PAYMENT_ADDRESS = os.environ.get('CARDANO_PAYMENT_ADDRESS', 'addr_test1vza7nn8c7p7rgcqsdjxvmwyqdztq9tgp8q89p2xugxc8djqmphalu')