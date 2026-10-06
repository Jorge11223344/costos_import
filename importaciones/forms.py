from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Empresa, TipoCosto, Importacion, Cotizacion, CotizacionItem


class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ["nombre", "tipo", "contacto", "email", "telefono", "notas"]


class TipoCostoForm(forms.ModelForm):
    class Meta:
        model = TipoCosto
        fields = ["nombre", "categoria", "descripcion", "activo"]


class ImportacionForm(forms.ModelForm):
    class Meta:
        model = Importacion
        fields = ["fecha", "referencia", "incoterm", "pol", "pod", "kilos_estimados", "kilos_merma", "moneda_base", "estado"]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date", "class": "form-control"}, format="%Y-%m-%d"),
            "pol": forms.TextInput(attrs={"placeholder": "Ej: Callao", "class": "form-control"}),
            "pod": forms.TextInput(attrs={"placeholder": "Ej: Valparaíso", "class": "form-control"}),
            "referencia": forms.TextInput(attrs={"placeholder": "Ej: Contenedor Tianjin Sep-2025", "class": "form-control"}),
            "kilos_estimados": forms.NumberInput(attrs={"step": "0.1", "class": "form-control"}),
            "estado": forms.Select(attrs={"class": "form-control"}),
        }


class CotizacionForm(forms.ModelForm):
    class Meta:
        model = Cotizacion
        fields = ["importacion", "nombre", "activa", "notas"]


class CotizacionItemForm(forms.ModelForm):
    class Meta:
        model = CotizacionItem
        fields = [
            "tipo_costo", "empresa", "descripcion",
            "monto", "moneda", "tipo_cambio",
            "aplica_iva", "iva_pct",
        ]
        widgets = {
            "descripcion": forms.TextInput(attrs={"placeholder": "Ej: THC destino - terminal X"}),
        }
