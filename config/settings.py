import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
env_path = BASE_DIR / '.env'
if env_path.exists():
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                os.environ[key.strip()] = val.strip()

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-electroplastic-production-logging-key')
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'producao.apps.ProducaoConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
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

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Database
# Using a simple SQLite database for Django session and metadata persistence
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = []

# Internationalization
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = []

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Google Sheets Configuration
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID', '1hbXN9-LmP-rrNG0Iv5a-TEa09q0vdJzcGgn40P9M720')
CREDENTIALS_FILE = BASE_DIR / 'credentials.json'
TOKEN_FILE = BASE_DIR / 'token.json'

# Recursos (Machines) configuration
RECURSOS = [
    'HS1000.2',
    'MS1000.1',
    'HS1000.3',
    'HS1200.1',
    'MS1200.2',
    'F750 02',
    'SCW700.3',
    'MS1000.4',
    'HS1000.1',
    'HSC1100',
    'MS1000.3',
    'CS600 L',
    'MAQ.1',
    'MAQ.2',
    'P140.1',
    'P140.3',
    'P140.4',
    'P130.1',
    'P130.2',
    'P130.3',
    'P130.4',
    'P130.5',
    'P130.6',
    'P130.7',
    'P130.8',
    'POLIROLL'
]

# Motivos (Occurrence reasons) configuration
MOTIVOS = [
    'Ajuste Operacional',
    'Banheiro',
    'Elétrica',
    'Falta de Material',
    'Manutenção',
    'Parada Programada',
    'Refeição',
    'Remanejamento',
    'Setup',
    'Troca de Bobina'
]
