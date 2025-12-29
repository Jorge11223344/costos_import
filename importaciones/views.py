from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from .models import Importacion, Cotizacion, CotizacionItem, Empresa, TipoCosto
from .forms import ImportacionForm, CotizacionForm, CotizacionItemForm, EmpresaForm, TipoCostoForm


# -----------------------
# Importaciones
# -----------------------
def importaciones_list(request):
    importaciones = Importacion.objects.order_by("-fecha", "-id")
    return render(request, "importaciones/importaciones_list.html", {"importaciones": importaciones})


def importacion_create(request):
    if request.method == "POST":
        form = ImportacionForm(request.POST)
        if form.is_valid():
            imp = form.save()
            messages.success(request, "Importación creada.")
            return redirect("importaciones:importacion_detail", importacion_id=imp.id)
    else:
        form = ImportacionForm()
    return render(request, "importaciones/form.html", {"form": form, "titulo": "Nueva importación"})


def importacion_detail(request, importacion_id):
    imp = get_object_or_404(Importacion, id=importacion_id)
    cotizaciones = imp.cotizaciones.order_by("-activa", "-id")
    return render(request, "importaciones/importacion_detail.html", {"imp": imp, "cotizaciones": cotizaciones})


def importacion_edit(request, importacion_id):
    imp = get_object_or_404(Importacion, id=importacion_id)
    if request.method == "POST":
        form = ImportacionForm(request.POST, instance=imp)
        if form.is_valid():
            form.save()
            messages.success(request, "Importación actualizada.")
            return redirect("importaciones:importacion_detail", importacion_id=imp.id)
    else:
        form = ImportacionForm(instance=imp)
    return render(request, "importaciones/form.html", {"form": form, "titulo": "Editar importación"})


# -----------------------
# Cotizaciones
# -----------------------
def cotizacion_create(request, importacion_id):
    imp = get_object_or_404(Importacion, id=importacion_id)
    if request.method == "POST":
        form = CotizacionForm(request.POST)
        if form.is_valid():
            cot = form.save(commit=False)
            cot.importacion = imp
            cot.save()
            messages.success(request, "Cotización creada.")
            return redirect("importaciones:cotizacion_detail", cotizacion_id=cot.id)
    else:
        form = CotizacionForm(initial={"importacion": imp})
        form.fields["importacion"].disabled = True
    return render(request, "importaciones/form.html", {"form": form, "titulo": "Nueva cotización"})


def cotizacion_detail(request, cotizacion_id):
    cot = get_object_or_404(Cotizacion, id=cotizacion_id)
    items = cot.items.select_related("tipo_costo", "empresa").order_by("tipo_costo__categoria", "tipo_costo__nombre", "id")

    # Totales por categoría (opcional, pero útil)
    totales_categoria = {}
    for it in items:
        cat = it.tipo_costo.categoria
        totales_categoria.setdefault(cat, 0)
        totales_categoria[cat] += float(it.total_en_moneda_base())

    context = {
        "cot": cot,
        "imp": cot.importacion,
        "items": items,
        "total": cot.total(),
        "total_sin_iva": cot.total_sin_iva(),
        "total_iva": cot.total_iva(),
        "totales_categoria": totales_categoria,
    }
    return render(request, "importaciones/cotizacion_detail.html", context)


def cotizacion_edit(request, cotizacion_id):
    cot = get_object_or_404(Cotizacion, id=cotizacion_id)
    if request.method == "POST":
        form = CotizacionForm(request.POST, instance=cot)
        if form.is_valid():
            form.save()
            messages.success(request, "Cotización actualizada.")
            return redirect("importaciones:cotizacion_detail", cotizacion_id=cot.id)
    else:
        form = CotizacionForm(instance=cot)
    return render(request, "importaciones/form.html", {"form": form, "titulo": "Editar cotización"})


# -----------------------
# Items de costo
# -----------------------
def item_create(request, cotizacion_id):
    cot = get_object_or_404(Cotizacion, id=cotizacion_id)
    if request.method == "POST":
        form = CotizacionItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.cotizacion = cot
            item.save()
            messages.success(request, "Ítem agregado.")
            return redirect("importaciones:cotizacion_detail", cotizacion_id=cot.id)
    else:
        form = CotizacionItemForm()
    return render(request, "importaciones/form.html", {"form": form, "titulo": "Agregar ítem de costo"})


def item_edit(request, item_id):
    item = get_object_or_404(CotizacionItem, id=item_id)
    cot = item.cotizacion
    if request.method == "POST":
        form = CotizacionItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Ítem actualizado.")
            return redirect("importaciones:cotizacion_detail", cotizacion_id=cot.id)
    else:
        form = CotizacionItemForm(instance=item)
    return render(request, "importaciones/form.html", {"form": form, "titulo": "Editar ítem de costo"})


def item_delete(request, item_id):
    item = get_object_or_404(CotizacionItem, id=item_id)
    cot_id = item.cotizacion.id
    if request.method == "POST":
        item.delete()
        messages.success(request, "Ítem eliminado.")
        return redirect("importaciones:cotizacion_detail", cotizacion_id=cot_id)
    return render(request, "importaciones/confirm_delete.html", {"obj": item, "volver_url": ("importaciones:cotizacion_detail", [cot_id])})


# -----------------------
# Catálogos básicos (opcional)
# -----------------------
def empresas_list(request):
    empresas = Empresa.objects.order_by("tipo", "nombre")
    return render(request, "importaciones/empresas_list.html", {"empresas": empresas})


def empresa_create(request):
    if request.method == "POST":
        form = EmpresaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Empresa creada.")
            return redirect("importaciones:empresas_list")
    else:
        form = EmpresaForm()
    return render(request, "importaciones/form.html", {"form": form, "titulo": "Nueva empresa"})


def tipos_costo_list(request):
    tipos = TipoCosto.objects.order_by("categoria", "nombre")
    return render(request, "importaciones/tipos_costo_list.html", {"tipos": tipos})
