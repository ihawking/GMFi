"""
Django settings for GMFi project.

Generated by 'django-admin startproject' using Django 4.2.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""
import os
import sys
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# Custom

sys.path.insert(0, os.path.join(BASE_DIR, "apps"))
AUTH_USER_MODEL = "users.Manager"
GMFIPRO = (Path.cwd().parent.parent / "apps" / "projects" / "__init__.py").exists()

# Celery Configuration
CELERY_BROKER_URL = "redis://redis:6379/8"
CELERY_RESULT_BACKEND = "django-db"
CELERY_TASK_TIME_LIMIT = 300
CELERY_WORKER_MAX_TASKS_PER_CHILD = 32
CELERY_TASK_STORE_ERRORS_EVEN_IF_IGNORED = True
CELERY_RESULT_EXTENDED = True
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-1rs%sf5v3hlkq+tq1ci#rc41x_wl&q)7n!#+ki8+cltvcete*w"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS: list = []

# Application definition

INSTALLED_APPS = [
    "unfold",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_extensions",
    "django_celery_results",
    "rest_framework",
    "users",
    "chains",
    "tokens",
    "globals",
    "invoices",
    "notifications",
]
if GMFIPRO:
    INSTALLED_APPS += ["projects", "deposits", "withdrawals"]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "common.middlewares.CheckHeadersMiddleware",
    "common.middlewares.IPWhiteListMiddleware",
    "common.middlewares.HMACMiddleware",
]

ROOT_URLCONF = "GMFi.urls"

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
            ],
        },
    },
]

WSGI_APPLICATION = "GMFi.wsgi.application"


REST_FRAMEWORK = {"DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"]}

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "zh-hans"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"
# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

UNFOLD = {
    "SITE_TITLE": "GMFi",
    "SITE_HEADER": "GMFi",
    "SITE_URL": "https://GMFi.org/",
    "SITE_SYMBOL": "radar",  # symbol from icon set
    "ENVIRONMENT": "common.admin.environment_callback",
    "DASHBOARD_CALLBACK": "common.admin.dashboard_callback",
    "SIDEBAR": {
        "navigation": [
            {
                "title": _("系统"),
                "separator": False,  # Top border
                "items": [
                    {
                        "title": _("控制台"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                    {
                        "title": _("管理员"),
                        "icon": "manage_accounts",
                        "link": reverse_lazy("admin:users_manager_changelist"),
                    },
                    {
                        "title": _("项目配置"),
                        "icon": "settings",
                        "link": reverse_lazy("admin:globals_project_changelist"),
                        "badge": "globals.models.status",
                    },
                    {
                        "title": _("任务日志"),
                        "icon": "task",
                        "link": reverse_lazy("admin:django_celery_results_taskresult_changelist"),
                    },
                ],
            },
            {
                "title": _("区块链"),
                "separator": True,
                "items": [
                    {
                        "title": _("主网"),
                        "icon": "lan",
                        "link": reverse_lazy("admin:chains_network_changelist"),
                    },
                    {
                        "title": _("区块"),
                        "icon": "grid_view",
                        "link": reverse_lazy("admin:chains_block_changelist"),
                    },
                    {
                        "title": _("交易"),
                        "icon": "deployed_code",
                        "link": reverse_lazy("admin:chains_transaction_changelist"),
                    },
                    {
                        "title": _("发送交易"),
                        "icon": "deployed_code_history",
                        "link": reverse_lazy("admin:chains_platformtransaction_changelist"),
                    },
                ],
            },
            {
                "title": _("代币"),
                "separator": True,
                "items": [
                    {
                        "title": _("代币"),
                        "icon": "database",
                        "link": reverse_lazy("admin:tokens_token_changelist"),
                    },
                    {
                        "title": _("转移"),
                        "icon": "change_circle",
                        "link": reverse_lazy("admin:tokens_tokentransfer_changelist"),
                    },
                    {
                        "title": _("余额"),
                        "icon": "price_change",
                        "link": reverse_lazy("admin:tokens_accounttokenbalance_changelist"),
                    },
                ],
            },
            {
                "title": _("账单"),
                "separator": True,
                "items": [
                    {
                        "title": _("账单"),
                        "icon": "receipt_long",
                        "link": reverse_lazy("admin:invoices_invoice_changelist"),
                    },
                    {
                        "title": _("支付"),
                        "icon": "payments",
                        "link": reverse_lazy("admin:invoices_payment_changelist"),
                    },
                ],
            },
            {
                "title": _("通知"),
                "separator": True,
                "items": [
                    {
                        "title": _("通知"),
                        "icon": "notifications_active",
                        "link": reverse_lazy("admin:notifications_notification_changelist"),
                    },
                ],
            },
        ],
    },
}

if GMFIPRO:
    UNFOLD["SIDEBAR"]["navigation"].append(  # type: ignore
        {
            "title": _("充提币"),
            "separator": True,
            "items": [
                {
                    "title": _("充币"),
                    "icon": "download",
                    "link": reverse_lazy("admin:deposits_deposit_changelist"),
                },
                {
                    "title": _("提币"),
                    "icon": "upload",
                    "link": reverse_lazy("admin:withdrawals_withdrawal_changelist"),
                },
            ],
        }
    )
