from django.urls import path
from . import views

app_name = "importaciones"

urlpatterns = [
    path("", views.importaciones_list, name="importaciones_list"),
    path("nueva/", views.importacion_create, name="importacion_create"),
    path("<int:importacion_id>/", views.importacion_detail, name="importacion_detail"),
    path("<int:importacion_id>/editar/", views.importacion_edit, name="importacion_edit"),

    path("<int:importacion_id>/cotizacion/nueva/", views.cotizacion_create, name="cotizacion_create"),
    path("cotizacion/<int:cotizacion_id>/", views.cotizacion_detail, name="cotizacion_detail"),
    path("cotizacion/<int:cotizacion_id>/editar/", views.cotizacion_edit, name="cotizacion_edit"),

    path("cotizacion/<int:cotizacion_id>/item/nuevo/", views.item_create, name="item_create"),
    path("item/<int:item_id>/editar/", views.item_edit, name="item_edit"),
    path("item/<int:item_id>/eliminar/", views.item_delete, name="item_delete"),

    path("empresas/", views.empresas_list, name="empresas_list"),
    path("empresas/nueva/", views.empresa_create, name="empresa_create"),

    path("tipos-costo/", views.tipos_costo_list, name="tipos_costo_list"),
    path("tipos-costo/nuevo/", views.tipo_costo_create, name="tipo_costo_create"),
]