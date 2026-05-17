from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from applications.tpv.models import Comanda  # Asumiendo que tienes un modelo Comanda


class Factura(models.Model):
    TIPOS_FACTURA = [
        ('ordinaria', 'Factura ordinaria'),
        ('rectificativa', 'Factura rectificativa'),
        ('proforma', 'Factura proforma'),
        ('simplificada', 'Factura simplificada (Ticket)'),
    ]

    ESTADOS_FACTURA = [
        ('borrador', 'Borrador'),
        ('emitida', 'Emitida'),
        ('enviada', 'Enviada al cliente'),
        ('pagada', 'Pagada'),
        ('vencida', 'Vencida'),
        ('anulada', 'Anulada'),
    ]

    METODOS_PAGO = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia'),
        ('domiciliacion', 'Domiciliación'),
        ('contrareembolso', 'Contrareembolso'),
        ('bitcoin', 'Bitcoin/Cripto'),
    ]

    # Identificación única
    numero = models.CharField("Número de factura", max_length=50, unique=True, editable=False)
    serie = models.CharField("Serie", max_length=10, default='FAC', help_text="Serie para agrupar facturas")
    tipo = models.CharField("Tipo de factura", max_length=20, choices=TIPOS_FACTURA, default='ordinaria')
    estado = models.CharField("Estado", max_length=20, choices=ESTADOS_FACTURA, default='borrador')
    
    # Fechas importantes
    fecha_emision = models.DateField("Fecha de emisión", default=timezone.now)
    fecha_vencimiento = models.DateField("Fecha de vencimiento", null=True, blank=True)
    fecha_pago = models.DateField("Fecha de pago", null=True, blank=True)
    
    # Relación con comanda/origen (para TPV)
    comanda = models.ForeignKey(
        Comanda, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='facturas',
        verbose_name="Comanda asociada"
    )
    
    # Datos del emisor (tu empresa)
    emisor_nombre = models.CharField("Nombre emisor", max_length=255, default="KUDEA TPV")
    emisor_nif = models.CharField("NIF/CIF emisor", max_length=20, default="")
    emisor_direccion = models.TextField("Dirección emisor", default="")
    emisor_codigo_postal = models.CharField("CP emisor", max_length=10, default="")
    emisor_ciudad = models.CharField("Ciudad emisor", max_length=100, default="")
    emisor_provincia = models.CharField("Provincia emisor", max_length=100, default="")
    emisor_pais = models.CharField("País emisor", max_length=100, default="España")
    emisor_email = models.EmailField("Email emisor", blank=True)
    emisor_telefono = models.CharField("Teléfono emisor", max_length=20, blank=True)
    emisor_registro_mercantil = models.TextField("Registro mercantil", blank=True)
    
    # Datos del cliente
    cliente_nombre = models.CharField("Nombre", max_length=100)
    cliente_apellidos = models.CharField("Apellidos", max_length=100, blank=True)
    cliente_empresa = models.CharField("Nombre de empresa", max_length=255, blank=True)
    cliente_nif = models.CharField("NIF/CIF", max_length=20, blank=True)
    cliente_direccion = models.TextField("Dirección")
    cliente_ciudad = models.CharField("Ciudad", max_length=100)
    cliente_provincia = models.CharField("Provincia", max_length=100, blank=True)
    cliente_pais = models.CharField("País", max_length=100, default="España")
    cliente_codigo_postal = models.CharField("Código Postal", max_length=10)
    cliente_telefono = models.CharField("Teléfono", max_length=20, blank=True)
    cliente_email = models.EmailField("Correo electrónico", blank=True)
    cliente_tipo = models.CharField("Tipo cliente", max_length=20, choices=[
        ('particular', 'Particular'), 
        ('empresa', 'Empresa'),
        ('autonomo', 'Autónomo'),
        ('extranjero', 'Extranjero')
    ], default='particular')
    
    # Totales y cálculos
    subtotal = models.DecimalField("Subtotal", max_digits=12, decimal_places=2, default=0.00)
    descuento_global = models.DecimalField("Descuento global", max_digits=12, decimal_places=2, default=0.00)
    base_imponible = models.DecimalField("Base imponible", max_digits=12, decimal_places=2, default=0.00)
    iva = models.DecimalField("IVA (%)", max_digits=5, decimal_places=2, default=21.00)
    total_iva = models.DecimalField("Total IVA", max_digits=12, decimal_places=2, default=0.00)
    recargo_equivalencia = models.DecimalField("RE (%)", max_digits=5, decimal_places=2, default=0.00)
    total_recargo = models.DecimalField("Total RE", max_digits=12, decimal_places=2, default=0.00)
    irpf = models.DecimalField("IRPF (%)", max_digits=5, decimal_places=2, default=0.00)
    total_irpf = models.DecimalField("Total IRPF", max_digits=12, decimal_places=2, default=0.00)
    total = models.DecimalField("Total", max_digits=12, decimal_places=2, default=0.00)
    
    # Pago y envío
    metodo_pago = models.CharField("Método de pago", max_length=20, choices=METODOS_PAGO, default='efectivo')
    condiciones_pago = models.CharField("Condiciones de pago", max_length=255, blank=True)
    cuenta_bancaria = models.CharField("Cuenta bancaria (IBAN)", max_length=50, blank=True)
    referencia_pago = models.CharField("Referencia de pago", max_length=100, blank=True)
    enviada = models.BooleanField("¿Enviada al cliente?", default=False)
    forma_envio = models.CharField("Forma de envío", max_length=100, blank=True)
    tracking_envio = models.CharField("Nº seguimiento envío", max_length=100, blank=True)
    
    # Legal y contabilidad
    leyenda_factura = models.TextField("Leyenda legal", blank=True, default="Factura conforme a la normativa vigente")
    factura_rectificada = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rectificaciones',
        verbose_name="Factura rectificada"
    )
    motivo_rectificacion = models.TextField("Motivo rectificación", blank=True)
    exportacion = models.BooleanField("¿Exportación?", default=False)
    exenta_iva = models.BooleanField("¿Exenta de IVA?", default=False)
    motivo_exencion = models.CharField("Motivo exención", max_length=100, blank=True)
    
    # Metadatos y auditoría
    creada_por = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='facturas_creadas',
        verbose_name="Creada por"
    )
    modificada_por = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='facturas_modificadas',
        verbose_name="Modificada por"
    )
    creada_en = models.DateTimeField(auto_now_add=True)
    modificada_en = models.DateTimeField(auto_now=True)
    notas_internas = models.TextField("Notas internas", blank=True)
    
    # Campos para integración con otros sistemas
    id_externo = models.CharField("ID sistema externo", max_length=100, blank=True)
    sincronizado_con_contabilidad = models.BooleanField("Sincronizado con contabilidad", default=False)
    fecha_sincronizacion = models.DateTimeField("Fecha sincronización", null=True, blank=True)

    class Meta:
        ordering = ['-fecha_emision']
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['cliente_nif']),
            models.Index(fields=['fecha_emision']),
            models.Index(fields=['estado']),
        ]

    def __str__(self):
        return f"{self.numero} - {self.cliente_nombre_completo()} ({self.total}€)"

    def cliente_nombre_completo(self):
        return f"{self.cliente_nombre} {self.cliente_apellidos}".strip()

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self.generar_numero_factura()
        self.calcular_totales()
        super().save(*args, **kwargs)

    def generar_numero_factura(self):
        año = timezone.now().year
        cantidad = Factura.objects.filter(
            serie=self.serie,
            fecha_emision__year=año
        ).count() + 1
        return f"{self.serie}{año}{cantidad:04d}"

    def calcular_totales(self):
        items = self.items.all()
        self.subtotal = sum(item.total_bruto for item in items)
        self.base_imponible = self.subtotal - self.descuento_global
        
        if not self.exenta_iva:
            self.total_iva = self.base_imponible * (self.iva / 100)
            self.total_recargo = self.base_imponible * (self.recargo_equivalencia / 100)
        else:
            self.total_iva = 0
            self.total_recargo = 0
            
        self.total_irpf = self.base_imponible * (self.irpf / 100)
        self.total = self.base_imponible + self.total_iva + self.total_recargo - self.total_irpf


class ItemFactura(models.Model):
    TIPOS_IVA = [
        (21.0, '21% General'),
        (10.0, '10% Reducido'),
        (4.0, '4% Superreducido'),
        (0.0, '0% Exento'),
    ]

    factura = models.ForeignKey(Factura, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(
        'product.Producto',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Producto asociado"
    )
    descripcion = models.CharField("Descripción", max_length=255)
    referencia = models.CharField("Referencia", max_length=100, blank=True)
    cantidad = models.DecimalField("Cantidad", max_digits=10, decimal_places=3, default=1)
    unidad_medida = models.CharField("Unidad", max_length=20, default="ud.")
    precio_unitario = models.DecimalField("Precio unitario", max_digits=12, decimal_places=4)
    descuento = models.DecimalField(
        "Descuento (%)",
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    tipo_iva = models.DecimalField(
        "Tipo IVA",
        max_digits=4,
        decimal_places=2,
        choices=TIPOS_IVA,
        default=21.00
    )
    total_bruto = models.DecimalField("Total bruto", max_digits=12, decimal_places=2, editable=False)
    notas = models.TextField("Notas", blank=True)

    class Meta:
        verbose_name = "Línea de factura"
        verbose_name_plural = "Líneas de factura"

    def __str__(self):
        return f"{self.descripcion} x{self.cantidad}"

    def save(self, *args, **kwargs):
        self.calcular_totales()
        super().save(*args, **kwargs)

    def calcular_totales(self):
        bruto = self.precio_unitario * self.cantidad
        descuento = bruto * (self.descuento / 100)
        self.total_bruto = bruto - descuento