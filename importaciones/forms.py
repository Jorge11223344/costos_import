from django import forms
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
        fields = ["fecha", "referencia", "incoterm", "pol", "pod", "kilos_estimados", "moneda_base"]


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
