from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import Movimiento, Cuenta


@transaction.atomic
def register_movement(
    *,
    concepto: str,
    tipo: str,
    origen: str,
    cuenta: Cuenta,
    cantidad: Decimal,
    metodo_pago: str | None = None,
    fecha=None,
    external_ref: str | None = None,
    created_by=None,
    canal_operacion: str | None = None,
) -> Movimiento:
    """
    Única puerta de entrada para registrar dinero en KUDEA.
    - cantidad SIEMPRE positiva
    - el signo lo da el campo 'tipo'
    - evita duplicados por (origen, external_ref)
    """

    if cantidad is None:
        raise ValueError("cantidad es obligatoria")

    cantidad = Decimal(cantidad)

    if cantidad <= 0:
        raise ValueError("cantidad debe ser > 0")

    if tipo not in [
        Movimiento.Tipo.INGRESO,
        Movimiento.Tipo.GASTO,
        Movimiento.Tipo.AJUSTE,
        Movimiento.Tipo.TRANSFERENCIA,
    ]:
        raise ValueError(f"Tipo inválido: {tipo}")

    fecha = fecha or timezone.now()
    canal_operacion = canal_operacion or Movimiento.CanalOperacion.DIRECTA
    metodo_pago = metodo_pago or Movimiento.MetodoPago.EFECTIVO

    # Evitar duplicados automáticos
    if external_ref:
        existing = Movimiento.objects.filter(
            origen=origen,
            external_ref=external_ref
        ).first()
        if existing:
            return existing

    movimiento = Movimiento.objects.create(
        concepto=concepto,
        tipo=tipo,
        origen=origen,
        cuenta=cuenta,
        cantidad=abs(cantidad),  # SIEMPRE positiva
        metodo_pago=metodo_pago,
        fecha=fecha,
        external_ref=external_ref,
        created_by=created_by,
        canal_operacion=canal_operacion,
    )

    return movimiento


@transaction.atomic
def transfer(
    *,
    concepto: str,
    cuenta_origen: Cuenta,
    cuenta_destino: Cuenta,
    cantidad: Decimal,
    fecha=None,
    external_ref: str | None = None,
    created_by=None,
):
    """
    Transferencia = 2 movimientos:
    - GASTO en cuenta_origen
    - INGRESO en cuenta_destino
    """

    cantidad = Decimal(cantidad)

    if cantidad <= 0:
        raise ValueError("cantidad debe ser > 0")

    fecha = fecha or timezone.now()

    ref_out = f"{external_ref}:out" if external_ref else None
    ref_in = f"{external_ref}:in" if external_ref else None

    m_out = register_movement(
        concepto=f"{concepto} (salida)",
        tipo=Movimiento.Tipo.GASTO,
        origen=Movimiento.Origen.SISTEMA,
        cuenta=cuenta_origen,
        cantidad=cantidad,
        fecha=fecha,
        external_ref=ref_out,
        created_by=created_by,
    )

    m_in = register_movement(
        concepto=f"{concepto} (entrada)",
        tipo=Movimiento.Tipo.INGRESO,
        origen=Movimiento.Origen.SISTEMA,
        cuenta=cuenta_destino,
        cantidad=cantidad,
        fecha=fecha,
        external_ref=ref_in,
        created_by=created_by,
    )

    return m_out, m_in
