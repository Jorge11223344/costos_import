

# Create your models here.
from django.db import models
from django.utils import timezone
from decimal import Decimal


class Empresa(models.Model):
    class Tipo(models.TextChoices):
        PRODUCTOR = "productor", "Productor"
        AGENTE_CARGA = "agente_carga", "Agente de carga / Forwarder"
        NAVIERA = "naviera", "Naviera"
        PUERTO = "puerto", "Puerto / Terminal"
        ADUANA = "aduana", "Agencia de aduana"
        TRANSP_LOCAL = "transporte_local", "Transportista local"
        BODEGA = "bodega", "Bodega / Depósito"
        OTRO = "otro", "Otro"

    nombre = models.CharField(max_length=150, unique=True)
    tipo = models.CharField(max_length=30, choices=Tipo.choices, default=Tipo.OTRO)
    contacto = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=50, blank=True)
    notas = models.TextField(blank=True)

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"


class TipoCosto(models.Model):
    class Categoria(models.TextChoices):
        ORIGEN = "origen", "Origen"
        INTERNACIONAL = "internacional", "Internacional"
        DESTINO = "destino", "Destino / Puerto"
        ADUANA = "aduana", "Aduana"
        LOCAL = "local", "Local (Chile)"
        FINANCIERO = "financiero", "Financiero"
        OTRO = "otro", "Otro"

    nombre = models.CharField(max_length=120, unique=True)
    categoria = models.CharField(max_length=20, choices=Categoria.choices, default=Categoria.OTRO)
    descripcion = models.CharField(max_length=250, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Importacion(models.Model):
    class Incoterm(models.TextChoices):
        EXW = "EXW", "EXW"
        FOB = "FOB", "FOB"
        CIF = "CIF", "CIF"
        CFR = "CFR", "CFR"
        DDP = "DDP", "DDP"

    fecha = models.DateField(default=timezone.localdate)
    referencia = models.CharField(max_length=120, blank=True, help_text="Ej: Contenedor Tianjin Sep-2025")
    incoterm = models.CharField(max_length=10, choices=Incoterm.choices, default=Incoterm.FOB)
    pol = models.CharField(max_length=80, blank=True, help_text="Puerto origen (POL)")
    pod = models.CharField(max_length=80, blank=True, help_text="Puerto destino (POD)")

    kilos_estimados = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    kilos_merma = models.DecimalField(
    max_digits=12,
    decimal_places=2,
    default=0,
    help_text="Kilos perdidos por rotura, humedad, polvo, etc."
)
    moneda_base = models.CharField(max_length=10, default="CLP", help_text="CLP / USD / CNY")

    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.fecha} - {self.referencia or 'Importación'}"


class Cotizacion(models.Model):
    importacion = models.ForeignKey(Importacion, on_delete=models.CASCADE, related_name="cotizaciones")
    nombre = models.CharField(max_length=120, help_text="Ej: Forwarder A + Puerto Lirquén + Transp X")
    activa = models.BooleanField(default=True)
    notas = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    def total(self):
        return sum((item.total_en_moneda_base() for item in self.items.all()), Decimal("0"))

    def total_sin_iva(self):
        return sum((item.subtotal_en_moneda_base() for item in self.items.all()), Decimal("0"))

    def total_iva(self):
        return sum((item.iva_en_moneda_base() for item in self.items.all()), Decimal("0"))

    def __str__(self):
        return f"{self.importacion} / {self.nombre}"


class CotizacionItem(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name="items")
    tipo_costo = models.ForeignKey(TipoCosto, on_delete=models.PROTECT)
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, null=True, blank=True)

    descripcion = models.CharField(max_length=200, blank=True)

    monto = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    moneda = models.CharField(max_length=10, default="CLP")  # CLP/USD/CNY

    # Convierte desde "moneda" a "moneda_base" de la importación. Por ahora lo ingresas tú.
    tipo_cambio = models.DecimalField(max_digits=14, decimal_places=4, default=1)

    aplica_iva = models.BooleanField(default=True)
    iva_pct = models.DecimalField(max_digits=5, decimal_places=2, default=19)

    def subtotal_en_moneda_base(self):
        return (self.monto or Decimal("0")) * (self.tipo_cambio or Decimal("1"))

    def iva_en_moneda_base(self):
        if not self.aplica_iva:
            return Decimal("0")
        return self.subtotal_en_moneda_base() * (self.iva_pct / Decimal("100"))

    def total_en_moneda_base(self):
        return self.subtotal_en_moneda_base() + self.iva_en_moneda_base()

    def __str__(self):
        return f"{self.tipo_costo} - {self.monto} {self.moneda}"
