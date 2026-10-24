from dotenv import load_dotenv
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env', override=True)

SECRET_KEY = os.getenv('SECRET_KEY')

DEBUG = True

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    '192.168.0.144',
    '.ngrok-free.dev',
    '.ngrok-free.app'
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'corsheaders',       
    'rest_framework',
    'rest_framework_simplejwt',

    'usuario',
    'perfil',
    'predio',
    'localizacao',
    'ordem_servico',
    'historico',
    'authentication',
    'ativo',
    'os_participante',
    'validacao',
    'auditoria_usuario',
    'notificacao',
    'evidencia_os',
    'preventiva_grupo',
    'inteligencia',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware', 
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = True

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

EXECUTANDO_TESTES = 'pytest' in sys.modules or (len(sys.argv) > 1 and sys.argv[1] == 'test')

if os.getenv('DB_NAME') and not EXECUTANDO_TESTES:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME'),
            'USER': os.getenv('DB_USER'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'HOST': os.getenv('DB_HOST'),
            'PORT': os.getenv('DB_PORT'),
            'DISABLE_SERVER_SIDE_CURSORS': True,
            'OPTIONS': {
                'sslmode': 'require',
            },
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
BASE_URL = os.getenv('BASE_URL')

FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173').rstrip('/')

HORAS_VALIDADE_TOKEN_CONFIRMACAO = int(os.getenv('HORAS_VALIDADE_TOKEN_CONFIRMACAO', 24))

DOMINIOS_EMAIL_PERMITIDOS = tuple(
    dominio.strip().lower()
    for dominio in os.getenv(
        'DOMINIOS_EMAIL_PERMITIDOS',
        '@gmail.com,@fho.edu.br'
    ).split(',')
)

def _lista_env(nome, padrao):
    return tuple(item.strip().lower() for item in os.getenv(nome, padrao).split(',') if item.strip())


EVIDENCIA_FORMATOS_IMAGEM = _lista_env('EVIDENCIA_FORMATOS_IMAGEM', 'jpg,jpeg,png,webp')
EVIDENCIA_FORMATOS_VIDEO = _lista_env('EVIDENCIA_FORMATOS_VIDEO', 'mp4,webm,mov')
EVIDENCIA_IMAGEM_TAMANHO_MAX_MB = int(os.getenv('EVIDENCIA_IMAGEM_TAMANHO_MAX_MB', 5))
EVIDENCIA_VIDEO_TAMANHO_MAX_MB = int(os.getenv('EVIDENCIA_VIDEO_TAMANHO_MAX_MB', 30))
EVIDENCIA_MAX_POR_ENVIO = int(os.getenv('EVIDENCIA_MAX_POR_ENVIO', 5))
EVIDENCIA_MAX_POR_ORDEM = int(os.getenv('EVIDENCIA_MAX_POR_ORDEM', 10))

INTERVALO_PREVENTIVA_DIAS = {
    'AR_CONDICIONADO': int(os.getenv('INTERVALO_PREVENTIVA_AR_CONDICIONADO_DIAS', 30)),
    'BEBEDOURO': int(os.getenv('INTERVALO_PREVENTIVA_BEBEDOURO_DIAS', 180)),
}
INTERVALO_PREVENTIVA_PADRAO_DIAS = int(os.getenv('INTERVALO_PREVENTIVA_PADRAO_DIAS', 90))
DIAS_ALERTA_PREVENTIVA_PROXIMA = int(os.getenv('DIAS_ALERTA_PREVENTIVA_PROXIMA', 7))

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL', 'claude-opus-5-5')
ANTHROPIC_TIMEOUT_SEGUNDOS = float(os.getenv('ANTHROPIC_TIMEOUT_SEGUNDOS', 60))
ANTHROPIC_MAX_RETRIES = int(os.getenv('ANTHROPIC_MAX_RETRIES', 2))
ANTHROPIC_MAX_TOKENS = int(os.getenv('ANTHROPIC_MAX_TOKENS', 4000))

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

if EXECUTANDO_TESTES:
    PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = Path(os.getenv('MEDIA_ROOT', BASE_DIR / 'media'))

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'USER_ID_FIELD': 'id_usuario',
    'USER_ID_CLAIM': 'id_usuario',
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'authentication.authentication.CustomJWTAuthentication',
    ),
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'reenvio_confirmacao': os.getenv('THROTTLE_REENVIO_CONFIRMACAO', '5/hour'),
        'cadastro_publico': os.getenv('THROTTLE_CADASTRO_PUBLICO', '20/hour'),
    },
}
