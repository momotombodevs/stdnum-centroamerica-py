# Django and Django REST Framework

```bash
uv add "stdnum-centroamerica[django]"     # or: pip install "stdnum-centroamerica[django]"
```

Nothing needs to be added to `INSTALLED_APPS`.

## In a model

```python
from django.db import models
from stdnum_centroamerica.contrib.django import DocumentValidator

class Customer(models.Model):
    dpi = models.CharField(max_length=13, unique=True, validators=[DocumentValidator("gt.dpi")])
    cedula = models.CharField(
        max_length=16, blank=True,
        validators=[DocumentValidator("ni.cedula", strict_letter=True)],
    )
```

`DocumentValidator` is *deconstructible*: `makemigrations` serializes it as `DocumentValidator('ni.cedula', strict_letter=True)`. For that reason, options must be plain values (`True`, `False`, strings), not class instances.

Remember that Django only runs model validators in `full_clean()` (which `ModelForm` and the admin call), not in `save()`.

## In a form

`DocumentFormField` validates the number and also returns it normalized in `cleaned_data`:

```python
from django import forms
from stdnum_centroamerica.contrib.django import DocumentFormField

class CustomerForm(forms.Form):
    dpi = DocumentFormField("gt.dpi")                                     # compact
    cedula_pa = DocumentFormField("pa.cedula", normalize="format", required=False)
    cedula_ni = DocumentFormField(
        "ni.cedula", normalize="format", document_options={"strict_letter": True}, required=False
    )
```

It accepts the `CharField` arguments (`label`, `required`, `help_text`, ...). Document options go in `document_options` so they do not clash with those.

In a `ModelForm`, use `DocumentValidator` on the model and normalize in `clean_<field>`:

```python
import stdnum_centroamerica as sca

class CustomerModelForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["dpi"]

    def clean_dpi(self) -> str:
        return sca.make("gt.dpi").compact(self.cleaned_data["dpi"])
```

## Django REST Framework

DRF accepts Django validators as they are:

```python
from rest_framework import serializers
import stdnum_centroamerica as sca
from stdnum_centroamerica.contrib.django import DocumentValidator

class CustomerSerializer(serializers.Serializer):
    dpi = serializers.CharField(max_length=32, validators=[DocumentValidator("gt.dpi")])

    def validate_dpi(self, value: str) -> str:
        return sca.make("gt.dpi").compact(value)    # store it normalized
```

For Panama, use `format()` instead of `compact()`, because the hyphens are part of the number.

## Messages and translation

Messages default to English and are marked with `gettext_lazy`, so your project can translate them (for example, to Spanish) in its own message catalogs. You can also pass a single custom message:

```python
DocumentValidator("gt.dpi", message=_("The DPI is not valid."))
```

The error `code` is `stdnum_format`, `stdnum_component` or `stdnum_checksum`, so you can tell the reason apart with `form.has_error("dpi", code="stdnum_checksum")`.

Complete, tested example: [examples/django_app.py](../examples/django_app.py).
