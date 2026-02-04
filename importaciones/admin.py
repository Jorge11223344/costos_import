from django.contrib import admin
from .models import Empresa, TipoCosto, Importacion, Cotizacion, CotizacionItem


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'contacto', 'email', 'telefono']
    list_filter = ['tipo']
    search_fields = ['nombre', 'contacto', 'email']


@admin.register(TipoCosto)
class TipoCostoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria', 'activo']
    list_filter = ['categoria', 'activo']
    search_fields = ['nombre', 'descripcion']


@admin.register(Importacion)
class ImportacionAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'referencia', 'incoterm', 'pol', 'pod', 'kilos_estimados']
    list_filter = ['incoterm', 'fecha']
    search_fields = ['referencia', 'pol', 'pod']
    date_hierarchy = 'fecha'


class CotizacionItemInline(admin.TabularInline):
    model = CotizacionItem
    extra = 1
    fields = ['tipo_costo', 'empresa', 'descripcion', 'monto', 'moneda', 'tipo_cambio', 'aplica_iva', 'iva_pct']


@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = ['importacion', 'nombre', 'activa', 'creado_en']
    list_filter = ['activa', 'creado_en']
    search_fields = ['nombre', 'notas']
    inlines = [CotizacionItemInline]


@admin.register(CotizacionItem)
class CotizacionItemAdmin(admin.ModelAdmin):
    list_display = ['cotizacion', 'tipo_costo', 'empresa', 'monto', 'moneda', 'aplica_iva']
    list_filter = ['moneda', 'aplica_iva']