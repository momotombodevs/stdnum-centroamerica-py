"""Single-file Django project: a form with DocumentFormField and a model validator.

Run:  uv run python examples/django_app.py runserver
In a real project the form goes in forms.py and the model in models.py (see docs/django.md).
"""

from __future__ import annotations

import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY="example-only",  # noqa: S106 - in production, read it from the environment
        ROOT_URLCONF=__name__,
        ALLOWED_HOSTS=["localhost", "127.0.0.1", "testserver"],
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        USE_I18N=True,
    )
    django.setup()

from django import forms
from django.http import HttpRequest, JsonResponse
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from stdnum_centroamerica.contrib.django import DocumentFormField, DocumentValidator

# In models.py:
#
#     class Customer(models.Model):
#         dpi = models.CharField(
#             max_length=13, unique=True, validators=[DocumentValidator("gt.dpi")]
#         )
#
# and in a DRF serializer:
#
#     dpi = serializers.CharField(validators=[DocumentValidator("gt.dpi")])
DPI_VALIDATOR = DocumentValidator("gt.dpi")


class CustomerForm(forms.Form):
    name = forms.CharField(max_length=100)
    dpi = DocumentFormField("gt.dpi")  # cleaned_data["dpi"] is compact
    cedula_ni = DocumentFormField(
        "ni.cedula", normalize="format", document_options={"strict_letter": True}, required=False
    )


@csrf_exempt  # example only: use the CSRF token in a real app
@require_POST
def create_customer(request: HttpRequest) -> JsonResponse:
    form = CustomerForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"errors": form.errors.get_json_data()}, status=422)
    return JsonResponse(form.cleaned_data, status=201)


urlpatterns = [path("customers", create_customer)]


if __name__ == "__main__":
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
