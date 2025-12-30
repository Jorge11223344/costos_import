from django.core.management.base import BaseCommand
from importaciones.models import TipoCosto

TIPOS = [
    ("Booking fee", "origen"),
    ("Documentación origen", "origen"),
    ("Transporte interno origen", "origen"),
    ("THC origen", "origen"),
    ("Costo del producto (FOB)", "origen"),

    ("Flete marítimo", "internacional"),
    ("Seguro", "internacional"),
    ("BL fee / Document fee", "internacional"),
    ("Recargos naviera (BAF/CAF)", "internacional"),

    ("THC destino", "destino"),
    ("Servicios terminal / TATC", "destino"),
    ("Servicios portuarios", "destino"), 
    ("Almacenaje puerto", "destino"),
    ("Aforo / inspección", "destino"),
    ("Demurrage / Detention", "destino"),

    ("Agencia de aduana (honorarios)", "aduana"),
    ("Gastos aduaneros varios", "aduana"),
    ("Servicios aduaneros (SAG / inspecciones)", "aduana"),

    ("Transporte puerto → bodega", "local"),
    ("Descarga / grúa / estiba", "local"),
    ("Bodegaje local", "local"),
    ("Peajes", "local"),

    ("Comisiones bancarias", "financiero"),
    ("Costos de pago internacional", "financiero"),

    ("Otros gastos", "otro"),
]

class Command(BaseCommand):
    help = "Crea un catálogo inicial de Tipos de Costo"

    def handle(self, *args, **options):
        creados = 0
        for nombre, categoria in TIPOS:
            obj, created = TipoCosto.objects.get_or_create(
                nombre=nombre,
                defaults={"categoria": categoria, "activo": True},
            )
            if created:
                creados += 1
        self.stdout.write(self.style.SUCCESS(f"Tipos de costo creados: {creados}"))
