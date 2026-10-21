from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from .models import Importacion, Cotizacion, CotizacionItem, Empresa, TipoCosto
from .forms import ImportacionForm, CotizacionForm, CotizacionItemForm, EmpresaForm, TipoCostoForm
from decimal import Decimal
from collections import defaultdict


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
# Eliminar cotización
# -----------------------
def cotizacion_delete(request, cotizacion_id):
    cot = get_object_or_404(Cotizacion, id=cotizacion_id)
    imp = cot.importacion

    if request.method == "POST":
        # Borrar los items de costo asociados antes de borrar la cotización
        # (usamos filter + delete en lugar de on_delete=CASCADE para mantener integridad)
        cot.items.all().delete()

        cot.delete()
        messages.success(request, "Cotización eliminada.")
        return redirect("importaciones:importacion_detail", importacion_id=imp.id)

    # Mostrar página de confirmación para GET
    context = {
        "cot": cot,
        "imp": imp,
    }
    return render(request, "importaciones/cotizacion_delete_confirm.html", context)


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
# Comparador de cotizaciones
# -----------------------
def comparar(request, importacion_id):
    imp = get_object_or_404(Importacion, id=importacion_id)
    cotizaciones = imp.cotizaciones.order_by("-activa", "-id")
    tipo_costos = TipoCosto.objects.order_by("categoria", "nombre")
    kilos_utiles = (imp.kilos_estimados or 0) - (imp.kilos_merma or 0)
    if kilos_utiles < 0:
        kilos_utiles = 0

    # Construir filas: una por cada TipoCosto, con valores por cotización
    # Filtrar: sólo mostrar TipoCosto que aparezcan en al menos una cotización
    tipo_costos_con_datos = []
    for tc in tipo_costos:
        # Verificar si este TipoCosto aparece en alguna cotización
        tiene_datos = False
        for cot in cotizaciones:
            items = cot.items.select_related("tipo_costo").filter(tipo_costo=tc)
            if items.exists():
                tiene_datos = True
                break
        if tiene_datos:
            tipo_costos_con_datos.append(tc)

    # Construir filas: una por cada TipoCosto que tiene datos
    filas_comparacion = []
    for tc in tipo_costos_con_datos:
        valores = []
        for cot in cotizaciones:
            # Sumar items de este TipoCosto para esta cotización
            total = Decimal("0")
            for item in cot.items.select_related("tipo_costo").filter(tipo_costo=tc):
                total += item.total_en_moneda_base()
            valores.append(total if total > 0 else Decimal("0"))
        filas_comparacion.append({
            "tipo_costo": tc.nombre,
            "valores": valores,
        })

    # BLOQUE ADICIONAL: Matriz detallada Concepto × Empresa × Cotización
    all_items = CotizacionItem.objects.filter(
        cotizacion__in=cotizaciones
    ).select_related("tipo_costo", "empresa")

    grupos = defaultdict(lambda: defaultdict(lambda: Decimal("0")))

    for item in all_items:
        tc_nombre = item.tipo_costo.nombre
        emp_nombre = item.empresa.nombre if item.empresa else "Sin empresa"
        grupos[(tc_nombre, emp_nombre)][item.cotizacion_id] += item.total_en_moneda_base()

    filas_detalle = []
    for (tc_nombre, emp_nombre), cotizaciones_dict in grupos.items():
        valores = []
        for cot in cotizaciones:
            val = cotizaciones_dict.get(cot.id, None)
            if val == Decimal("0"):
                val = None
            valores.append(val)
        filas_detalle.append({
            "tipo_costo": tc_nombre,
            "empresa": emp_nombre,
            "valores": valores,
        })

    # Ordenar filas: primero los que tienen empresa "Sin empresa", luego alfabéticamente
    filas_detalle.sort(key=lambda f: (f["empresa"] == "Sin empresa", f["tipo_costo"].lower()))

    # Calcular costo por kg para cada cotización
    resumen_cotizaciones = []
    for cot in cotizaciones:
        total = cot.total()
        if kilos_utiles > 0:
            costo_por_kg = total / kilos_utiles
        else:
            costo_por_kg = None
        resumen_cotizaciones.append({
            "cotizacion": cot,
            "total": total,
            "costo_por_kg": costo_por_kg,
        })

# Determinar la mejor cotización (menor total y menor costo/kg)
    mejor_total = min(cotizaciones, key=lambda c: c.total()) if cotizaciones else None
    # Calcular mejor_kg usando la lógica especificada
    resumen_con_costo = [r for r in resumen_cotizaciones if r["costo_por_kg"] is not None]
    mejor_kg = min(resumen_con_costo, key=lambda r: r["costo_por_kg"])["cotizacion"] if resumen_con_costo else None
    # Costo por kg de la mejor cotización
    if kilos_utiles > 0 and mejor_total:
        mejor_costo_kg = mejor_total.total() / kilos_utiles
    else:
        mejor_costo_kg = None

    context = {
        "imp": imp,
        "cotizaciones": cotizaciones,
        "tipo_costos": tipo_costos,
        "filas_comparacion": filas_comparacion,
        "tipo_costos_con_datos": tipo_costos_con_datos,
        "filas_detalle": filas_detalle,
        "resumen_cotizaciones": resumen_cotizaciones,
        "kilos_utiles": kilos_utiles,
        "mejor_total": mejor_total,
        "mejor_kg": mejor_kg,
        "mejor_costo_kg": mejor_costo_kg,
    }
    return render(request, "importaciones/comparar.html", context)


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
    
    # VALOR TOTAL SOLAMENTE IMPORTACIONES FINALIZADAS
    # Considerar somente Importacion con estado="finalizada"
    # Tomar las Cotizacion asociadas a esas importaciones finalizadas
    # Sumar Cotizacion.total()
    # Si el usuario aplica el selector manual de importaciones:
    # - el valor debe considerar solo las importaciones seleccionadas que además tengan estado="finalizada"
    importaciones_finalizadas = importaciones_seleccionadas.filter(estado="finalizada")
    cotizaciones_finalizadas = Cotizacion.objects.filter(
        importacion__in=importaciones_finalizadas
    )
    valor_total_importaciones_finalizadas = Decimal("0")
    for cot in cotizaciones_finalizadas:
        valor_total_importaciones_finalizadas += cot.total()

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
        "valor_total_importaciones_finalizadas": valor_total_importaciones_finalizadas,
        "numero_empresas_seleccionadas": numero_empresas_seleccionadas,
        "top_empresas": top_empresas,
    }
    return render(request, "importaciones/dashboard.html", context)

# -----------------------
# Análisis de evolución de importaciones
# -----------------------
def evolucion(request):
    # Filtro: importaciones seleccionadas via GET
    selected_ids = request.GET.getlist("importacion_ids")
    selected_ids = [int(id) for id in selected_ids] if selected_ids else []
    # Filtro por estado en la lista
    selected_estado_lista = request.GET.get("estado", "")

    # 1. Crear queryset base con todas las importaciones (excluyendo simulacion y cancelada)
    importaciones_base = Importacion.objects.exclude(
        estado__in=["simulacion", "cancelada"]
    ).order_by("-fecha", "-id")

    # Aplicar filtro manual de importacion_ids si viene
    if selected_ids:
        importaciones_base = importaciones_base.filter(id__in=selected_ids)

    # Determinar el estado activo para el filtro de la tabla
    # "Todas" = mostrar tanto finalizadas como en_curso
    # "Finalizadas" = solo finalizadas
    # "En curso" = solo en_curso
    if selected_estado_lista == "finalizadas":
        importaciones_queryset = importaciones_base.filter(estado=Importacion.Estado.FINALIZADA)
    elif selected_estado_lista == "en_curso":
        importaciones_queryset = importaciones_base.filter(estado=Importacion.Estado.EN_CURSO)
    else:
        importaciones_queryset = importaciones_base

    # 2. Calcular métricas por importación
    filas = []
    importaciones_finalizadas_list = []
    importaciones_en_curso_list = []

    # Primer pasada: obtener datos y clasificar
    for imp in importaciones_queryset:
        kilos_utiles = (imp.kilos_estimados or 0) - (imp.kilos_merma or 0)
        if kilos_utiles < 0:
            kilos_utiles = 0

        # Costo total: sumar todas las cotizaciones de esta importación
        cotizaciones_imp = imp.cotizaciones.all()
        costo_total = Decimal("0")
        for cot in cotizaciones_imp:
            costo_total += cot.total()

        # Costo por kg
        costo_por_kg = None
        if kilos_utiles > 0:
            # Buscar costo por kg entre las cotizaciones
            # Usar el costo total / kilos utiles como criterio
            costo_por_kg = costo_total / kilos_utiles

        # Porcentaje de merma
        porcentaje_merma = None
        if imp.kilos_estimados and imp.kilos_estimados > 0:
            porcentaje_merma = (imp.kilos_merma or 0) / imp.kilos_estimados * 100

        # Clasificar por estado
        if imp.estado == Importacion.Estado.FINALIZADA:
            importaciones_finalizadas_list.append(imp)
        elif imp.estado == Importacion.Estado.EN_CURSO:
            importaciones_en_curso_list.append(imp)

        filas.append({
            "importacion": imp,
            "estado": imp.estado,
            "fecha": imp.fecha,
            "referencia": imp.referencia,
            "kilos_estimados": imp.kilos_estimados or 0,
            "kilos_merma": imp.kilos_merma or 0,
            "kilos_utiles": kilos_utiles,
            "porcentaje_merma": porcentaje_merma,
            "costo_total": costo_total,
            "costo_por_kg": costo_por_kg,
        })

# 3. Calcular variación respecto de la última importación finalizada anterior
    # Para cada importación, encontrar la última finalizada cronológicamente anterior
    filas_con_variacion = []
    for fila in filas:
        imp = fila["importacion"]
        # Buscar la última importación finalizada con fecha anterior a esta (usando fecha + id para desempate)
        costo_kg_referencia = None
        variacion_porcentaje = None

        anteriores = Importacion.objects.filter(
            estado=Importacion.Estado.FINALIZADA,
            fecha__lt=imp.fecha
        ).order_by("-fecha", "-id")  # más reciente primera para el desempate

        if anteriores.exists():
            ant = anteriores[0]
            k_u_ant = (ant.kilos_estimados or 0) - (ant.kilos_merma or 0)
            if k_u_ant > 0:
                cots_ant = ant.cotizaciones.all()
                ct_ant = Decimal("0")
                for cot in cots_ant:
                    ct_ant += cot.total()
                costo_kg_referencia = ct_ant / k_u_ant
                # Calcular variación
                if fila["costo_por_kg"] is not None and costo_kg_referencia is not None and costo_kg_referencia != 0:
                    variacion_porcentaje = (
                        (fila["costo_por_kg"] - costo_kg_referencia) / costo_kg_referencia * 100
                    )
                else:
                    variacion_porcentaje = None
            else:
                costo_kg_referencia = None

        fila["costo_kg_referencia"] = costo_kg_referencia
        fila["variacion_porcentaje"] = variacion_porcentaje
        filas_con_variacion.append(fila)

    # Conjunto de todas las finalizadas (para métricas resumidas)
    todas_finalizadas_asc = Importacion.objects.filter(
        estado=Importacion.Estado.FINALIZADA
    ).order_by("fecha")

    # Datos para el gráfico: lista cronológica de costo por kg
    # Orden ascendente (más antigua a más reciente) según el filtro actual
    # Las filas ya vienen filtradas por importaciones_queryset, entonces el gráfico
    # muestra exactamente el mismo conjunto que la tabla
    chart_data = []
    filas_ordenadas = sorted(filas_con_variacion, key=lambda f: (f["fecha"], f["importacion"].id))
    for fila in filas_ordenadas:
        costo_kg = fila["costo_por_kg"]
        chart_data.append({
            "x": fila["fecha"],
            "referencia": fila["referencia"] or "—",
            "estado": fila["importacion"].get_estado_display(),
            "costo_kg": float(costo_kg) if costo_kg is not None else None,
        })

    # 4. Calcular resumen superior usando el MISMO CONJUNTO filtrado
    # que muestra la tabla y el gráfico (importaciones_queryset)
    
    # Cantidad de importaciones finalizadas en el conjunto filtrado
    cantidad_finalizadas = importaciones_queryset.filter(
        estado=Importacion.Estado.FINALIZADA
    ).count()

    # Cantidad de importaciones en curso en el conjunto filtrado
    cantidad_en_curso = importaciones_queryset.filter(
        estado=Importacion.Estado.EN_CURSO
    ).count()

    # Costo/kg promedio de importaciones finalizadas en el conjunto filtrado
    costo_kg_promedio_finalizadas = Decimal("0")
    finalizadas_filtradas = importaciones_queryset.filter(
        estado=Importacion.Estado.FINALIZADA
    )
    costos_kg_finalizadas = []
    for imp in finalizadas_filtradas:
        k_u = (imp.kilos_estimados or 0) - (imp.kilos_merma or 0)
        if k_u > 0:
            cots = imp.cotizaciones.all()
            ct = Decimal("0")
            for cot in cots:
                ct += cot.total()
            costos_kg_finalizadas.append(ct / k_u)

    if costos_kg_finalizadas:
        costo_kg_promedio_finalizadas = sum(costos_kg_finalizadas) / len(costos_kg_finalizadas)

    # Último costo/kg real (la última finalizada cronológicamente en el conjunto filtrado)
    ultimo_costo_kg_real = None
    finalizadas_ordenadas = importaciones_queryset.filter(
        estado=Importacion.Estado.FINALIZADA
    ).order_by("fecha", "id")
    if finalizadas_ordenadas.exists():
        imp_ult = finalizadas_ordenadas.last()
        k_u = (imp_ult.kilos_estimados or 0) - (imp_ult.kilos_merma or 0)
        if k_u > 0:
            cots_ult = imp_ult.cotizaciones.all()
            ct_ult = Decimal("0")
            for cot in cots_ult:
                ct_ult += cot.total()
            ultimo_costo_kg_real = ct_ult / k_u

    # Costo/kg de la importación en curso más reciente en el conjunto filtrado
    ultima_en_curso = None
    importaciones_en_curso_filtradas = importaciones_queryset.filter(
        estado=Importacion.Estado.EN_CURSO
    ).order_by("-fecha", "-id")
    if importaciones_en_curso_filtradas.exists():
        ultima_en_curso = importaciones_en_curso_filtradas[0]
    costo_kg_ultima_en_curso = None
    if ultima_en_curso:
        k_u = (ultima_en_curso.kilos_estimados or 0) - (ultima_en_curso.kilos_merma or 0)
        if k_u > 0:
            cots_uc = ultima_en_curso.cotizaciones.all()
            ct_uc = Decimal("0")
            for cot in cots_uc:
                ct_uc += cot.total()
            costo_kg_ultima_en_curso = ct_uc / k_u

    # Variación de la importación en curso más reciente respecto de la última finalizada
    variacion_ultima_en_curso = None
    if ultima_en_curso and ultimo_costo_kg_real is not None:
        if costo_kg_ultima_en_curso is not None and ultimo_costo_kg_real != 0:
            variacion_ultima_en_curso = (
                (costo_kg_ultima_en_curso - ultimo_costo_kg_real) / ultimo_costo_kg_real * 100
            )

    # 5. Context
    context = {
        "importaciones": importaciones_queryset,
        "filas": filas_con_variacion,
        "selected_ids": selected_ids,
        "selected_estado_lista": selected_estado_lista,
        "estados_choices": Importacion.Estado.choices,
        "cantidad_finalizadas": cantidad_finalizadas,
        "cantidad_en_curso": cantidad_en_curso,
        "costo_kg_promedio_finalizadas": costo_kg_promedio_finalizadas,
        "ultimo_costo_kg_real": ultimo_costo_kg_real,
        "costo_kg_ultima_en_curso": costo_kg_ultima_en_curso,
        "variacion_ultima_en_curso": variacion_ultima_en_curso,
        "importaciones_finalizadas_list": importaciones_finalizadas_list,
        "importaciones_en_curso_list": importaciones_en_curso_list,
        "chart_data": chart_data,
        "ultima_en_curso": ultima_en_curso,
    }
    return render(request, "importaciones/evolucion.html", context)
