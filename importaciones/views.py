from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from .models import Importacion, Cotizacion, CotizacionItem, Empresa, TipoCosto
from .forms import ImportacionForm, CotizacionForm, CotizacionItemForm, EmpresaForm, TipoCostoForm
from decimal import Decimal


# -----------------------
# Importaciones
# -----------------------
def importaciones_list(request):
    importaciones = Importacion.objects.order_by("-fecha", "-id")
    for imp in importaciones:
        imp.kilos_utiles = (imp.kilos_estimados or 0) - (imp.kilos_merma or 0)

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

    items = cot.items.select_related(
        "tipo_costo", "empresa"
    ).order_by(
        "tipo_costo__categoria",
        "tipo_costo__nombre",
        "id"
    )

    imp = cot.importacion

    kilos_estimados = imp.kilos_estimados or Decimal("0")
    kilos_merma = getattr(imp, "kilos_merma", Decimal("0")) or Decimal("0")

    kilos_utiles = kilos_estimados - kilos_merma
    if kilos_utiles < 0:
        kilos_utiles = Decimal("0")

    costo_por_kg = None
    if kilos_utiles > 0:
        costo_por_kg = cot.total_sin_iva() / kilos_utiles

    costo_saco_8 = None
    costo_saco_20 = None

    if costo_por_kg is not None:
        costo_saco_8 = costo_por_kg * Decimal("8")
        costo_saco_20 = costo_por_kg * Decimal("20")

    totales_categoria = {}
    for it in items:
        cat = it.tipo_costo.categoria
        totales_categoria.setdefault(cat, Decimal("0"))
        totales_categoria[cat] += it.total_en_moneda_base()

    context = {
        "cot": cot,
        "imp": imp,
        "items": items,
        "total": cot.total(),
        "total_sin_iva": cot.total_sin_iva(),
        "total_iva": cot.total_iva(),
        "costo_por_kg": costo_por_kg,
        "kilos_estimados": kilos_estimados,
        "kilos_merma": kilos_merma,
        "kilos_utiles": kilos_utiles,
        "totales_categoria": totales_categoria,
        "costo_por_kg": costo_por_kg,
        "costo_saco_8": costo_saco_8,
        "costo_saco_20": costo_saco_20,
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


def tipo_costo_create(request):
    if request.method == "POST":
        form = TipoCostoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Tipo de costo creado.")
            return redirect("importaciones:tipos_costo_list")
    else:
        form = TipoCostoForm()
    return render(request, "importaciones/form.html", {"form": form, "titulo": "Nuevo tipo de costo"})


# -----------------------
# Dashboard / Reporting
# -----------------------
# Dashboard / Reporting
# -----------------------
def dashboard(request):
    # ----- Filter: importaciones seleccionadas via GET -----
    # Parámetro: ?importacion_ids=1&importacion_ids=3  (lista múltiple)
    selected_ids = request.GET.getlist("importacion_ids")
    # Convertir a enteros para comparar con los IDs de la BD
    selected_ids = [int(id) for id in selected_ids] if selected_ids else []
    # Filtro por estado
    selected_estado = request.GET.get("estado", "")

    # 1. Crear queryset base con todas las importaciones
    importaciones_seleccionadas = Importacion.objects.all()

    # 2. Filtrar por estado (si viene parámetro)
    if selected_estado:
        importaciones_seleccionadas = importaciones_seleccionadas.filter(
            estado=selected_estado
        )

    # 3. Filtrar por IDs seleccionados (si vienen parámetros)
    if selected_ids:
        importaciones_seleccionadas = importaciones_seleccionadas.filter(
            id__in=selected_ids
        )

    # 4. Ordenar por fecha descendente
    importaciones_seleccionadas = importaciones_seleccionadas.order_by("-fecha", "-id")

    # Derivadas de la selección
    cotizaciones_seleccionadas = Cotizacion.objects.filter(
        importacion__in=importaciones_seleccionadas
    )
    # FILTRAR: sólo items con empresa asociada, para los cálculos por empresa
    cotizacionitems_seleccionados = CotizacionItem.objects.filter(
        cotizacion__in=cotizaciones_seleccionadas,
        empresa__isnull=False
    )

    # Métricas exclusivamente sobre importaciones seleccionadas
    cantidad_importaciones_seleccionadas = importaciones_seleccionadas.count()
    cantidad_cotizaciones_seleccionadas = cotizaciones_seleccionadas.count()
    valor_total_cotizado = Decimal("0")
    for cot in cotizaciones_seleccionadas:
        valor_total_cotizado += cot.total()

    # Número de empresas que participan en esas importaciones
    empresas_participan = set()
    for item in cotizacionitems_seleccionados:
        if item.empresa:
            empresas_participan.add(item.empresa)
    numero_empresas_seleccionadas = len(empresas_participan)

    # Top 5 empresas exclusivamente con los CotizacionItem de las importaciones seleccionadas
    # empresa_costos: acumula valor_total por empresa
    # empresa_importas: set de IDs de importacion distintas donde la empresa tiene al menos un item
    empresa_costos = {}
    empresa_importaciones = {}  # nombre -> set de IDs de importacion distintas
    for item in cotizacionitems_seleccionados:
        emp_nombre = item.empresa.nombre
        empresa_costos.setdefault(emp_nombre, Decimal("0"))
        empresa_costos[emp_nombre] += item.total_en_moneda_base()

        # Track importaciones distintas por empresa (mismo item->c->imp, set auto-deduplica)
        imp_id = item.cotizacion.importacion.id
        empresa_importaciones.setdefault(emp_nombre, set())
        empresa_importaciones[emp_nombre].add(imp_id)

    # Construir lista Top 5 ordenada por valor total descendente
    top_empresas = []
    for nombre, costo_total in sorted(
        empresa_costos.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]:
        importaciones_distintas = len(empresa_importaciones.get(nombre, set()))
        valor_promedio = costo_total / importaciones_distintas if importaciones_distintas > 0 else Decimal("0")
        top_empresas.append({
            "nombre": nombre,
            "costo_total": costo_total,
            "numero_importaciones": importaciones_distintas,
            "valor_promedio": valor_promedio,
        })

    context = {
        "importaciones": importaciones_seleccionadas,
        "selected_ids": selected_ids,
        "selected_estado": selected_estado,
        "estados": Importacion.Estado.choices,
        "cantidad_importaciones_seleccionadas": cantidad_importaciones_seleccionadas,
        "cantidad_cotizaciones_seleccionadas": cantidad_cotizaciones_seleccionadas,
        "valor_total_cotizado": valor_total_cotizado,
        "numero_empresas_seleccionadas": numero_empresas_seleccionadas,
        "top_empresas": top_empresas,
    }
    return render(request, "importaciones/dashboard.html", context)