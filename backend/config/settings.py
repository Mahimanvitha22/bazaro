import os
from pathlib import Path
from dotenv import load_dotenv
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR.parent / ".env")
DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or ("dev-only-key" if DEBUG else None)
if not SECRET_KEY: raise RuntimeError("Set DJANGO_SECRET_KEY")
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
INSTALLED_APPS = ["django.contrib.admin","django.contrib.auth","django.contrib.contenttypes","django.contrib.sessions",
 "django.contrib.messages","django.contrib.staticfiles","rest_framework","rest_framework.authtoken","corsheaders","shop"]
MIDDLEWARE = ["corsheaders.middleware.CorsMiddleware","django.middleware.security.SecurityMiddleware",
 "django.contrib.sessions.middleware.SessionMiddleware","django.middleware.common.CommonMiddleware",
 "django.middleware.csrf.CsrfViewMiddleware","django.contrib.auth.middleware.AuthenticationMiddleware",
 "django.contrib.messages.middleware.MessageMiddleware","django.middleware.clickjacking.XFrameOptionsMiddleware"]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{"BACKEND":"django.template.backends.django.DjangoTemplates","DIRS":[],"APP_DIRS":True,
 "OPTIONS":{"context_processors":["django.template.context_processors.request","django.contrib.auth.context_processors.auth","django.contrib.messages.context_processors.messages"]}}]
if os.environ.get("DB_NAME"):
    DATABASES = {"default":{"ENGINE":"django.db.backends.postgresql","NAME":os.environ["DB_NAME"],"USER":os.environ.get("DB_USER","postgres"),
     "PASSWORD":os.environ.get("DB_PASSWORD",""),"HOST":os.environ.get("DB_HOST","localhost"),"PORT":os.environ.get("DB_PORT","5432")}}
else:
    DATABASES = {"default":{"ENGINE":"django.db.backends.sqlite3","NAME":BASE_DIR/"db.sqlite3"}}
AUTH_PASSWORD_VALIDATORS = [{"NAME":"django.contrib.auth.password_validation.MinimumLengthValidator"},{"NAME":"django.contrib.auth.password_validation.CommonPasswordValidator"}]
STATIC_URL = "static/"; MEDIA_URL = "/media/"; MEDIA_ROOT = BASE_DIR/"media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
REST_FRAMEWORK = {"DEFAULT_AUTHENTICATION_CLASSES":["rest_framework.authentication.TokenAuthentication"],
 "DEFAULT_PERMISSION_CLASSES":["rest_framework.permissions.IsAuthenticated"],
 "DEFAULT_PAGINATION_CLASS":"rest_framework.pagination.PageNumberPagination","PAGE_SIZE":12}
CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ORIGINS","http://localhost:5173").split(",")
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID",""); RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET","")
DEMO_PAYMENTS = not (RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)
if not DEBUG:
    SECURE_SSL_REDIRECT = True; SESSION_COOKIE_SECURE = True; CSRF_COOKIE_SECURE = True
