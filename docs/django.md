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
    dpi = DocumentFormField("gt.dpi")                                     # canonical: compact
    cedula_pa = DocumentFormField("pa.cedula", required=False)            # canonical: keeps hyphens
    cedula_ni = DocumentFormField(
        "ni.cedula", normalize="format", document_options={"strict_letter": True}, required=False
    )
```

`normalize` is `"canonical"` by default: the form to store, which is the compact form except in Panama, whose hyphens are part of the number (`compact()` would turn `1-12-345` and `11-2-345` into the same `112345`). The other values are `"compact"`, `"format"` (for display) and `"none"`.

It accepts the `CharField` arguments (`label`, `required`, `help_text`, ...). Document options go in `document_options` so they do not clash with those. `max_length` defaults to 128, so formatted input with spaces or hyphens fits.

`DocumentValidator` only validates; it never changes the value. In a `ModelForm`, declare the field with `DocumentFormField` so it normalizes before saving:

```python
class CustomerModelForm(forms.ModelForm):
    dpi = DocumentFormField("gt.dpi")   # accepts "1234 56789 0101", saves "1234567890101"

    class Meta:
        model = Customer
        fields = ["dpi"]
```

Without that declaration, Django builds the form field from the model, with `max_length=13`, and rejects `"1234 56789 0101"` (15 characters) before any `clean_dpi()` can compact it.

## Django REST Framework

DRF accepts Django validators as they are:

```python
from rest_framework import serializers
import stdnum_centroamerica as sca
from stdnum_centroamerica.contrib.django import DocumentValidator

class CustomerSerializer(serializers.Serializer):
    dpi = serializers.CharField(max_length=32, validators=[DocumentValidator("gt.dpi")])

    def validate_dpi(self, value: str) -> str:
        return sca.canonical("gt.dpi", value)    # store it normalized
```

`sca.canonical()` is the form to store for every document: variants of the same number share it and different numbers never do. For Panama it keeps the hyphens, which `compact()` would remove.

## Messages and translation

Messages default to English and are marked with `gettext_lazy`, so your project can translate them (for example, to Spanish) in its own message catalogs. You can also pass a single custom message:

```python
DocumentValidator("gt.dpi", message=_("The DPI is not valid."))
```

The error `code` is `stdnum_format`, `stdnum_component` or `stdnum_checksum`, so you can tell the reason apart with `form.has_error("dpi", code="stdnum_checksum")`.

Complete, tested example: [examples/django_app.py](../examples/django_app.py).
