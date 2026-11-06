"""Minimal Django settings for the tests and the mypy plugin."""

SECRET_KEY = "tests-only"
INSTALLED_APPS = ["django.contrib.contenttypes", "django.contrib.auth"]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
USE_I18N = True
LANGUAGE_CODE = "en"
USE_TZ = True
