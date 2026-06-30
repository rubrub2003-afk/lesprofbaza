"""
Настройки Django-проекта ЛЕСПРОФБАЗА.

Все «секретные» и средо-зависимые параметры читаются из переменных окружения
(файл .env). Для разработки достаточно значений по умолчанию.
"""
from pathlib import Path
import os

# dotenv — необязателен; если установлен, подхватит .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent


def env(key, default=None):
    return os.environ.get(key, default)


def env_bool(key, default=False):
    val = os.environ.get(key)
    if val is None:
        return default
    return val.lower() in ("1", "true", "yes", "on")


# --- Безопасность ---
SECRET_KEY = env("SECRET_KEY", "dev-insecure-key-change-me-on-deploy")
DEBUG = env_bool("DEBUG", True)
ALLOWED_HOSTS = [h for h in env("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if h]

# --- Приложения ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",  # форматирование чисел (цены, объёмы)
    # Наши приложения:
    "catalog",
    "orders",
    "content",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "content.context_processors.site_settings",  # настройки сайта во всех шаблонах
                "catalog.context_processors.catalog_menu",    # меню категорий + счётчик корзины
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --- База данных ---
# По умолчанию — SQLite (просто файл, ничего ставить не нужно).
# Для боевого сервера задайте переменные DB_* и поставьте PostgreSQL.
if env("DATABASE_URL"):
    import dj_database_url
    DATABASES = {"default": dj_database_url.parse(env("DATABASE_URL"), conn_max_age=600)}
elif env("DB_ENGINE") == "postgres":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_NAME", "lesprofbaza"),
            "USER": env("DB_USER", "lesprofbaza"),
            "PASSWORD": env("DB_PASSWORD", ""),
            "HOST": env("DB_HOST", "127.0.0.1"),
            "PORT": env("DB_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            # путь к файлу БД можно переопределить переменной SQLITE_PATH
            "NAME": env("SQLITE_PATH", str(BASE_DIR / "db.sqlite3")),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Локализация ---
LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True

# --- Статика и медиа ---
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Уведомления о заказах (почта + Telegram) ---
# Значения-заглушки; реальные подставим на деплое.
EMAIL_BACKEND = env("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", "")
EMAIL_PORT = int(env("EMAIL_PORT", "587"))
EMAIL_HOST_USER = env("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
ORDER_NOTIFY_EMAIL = env("ORDER_NOTIFY_EMAIL", "")           # куда слать заявки
TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN", "")    

# --- Статика на проде (WhiteNoise) ---
if not DEBUG:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    CSRF_TRUSTED_ORIGINS = [o for o in env("CSRF_TRUSTED_ORIGINS", "").split(",") if o]
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
