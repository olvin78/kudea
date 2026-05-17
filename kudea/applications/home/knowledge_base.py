import difflib
import json
import os
import re

# ==============================================================================
# KUDEA BRAIN MEMORY - ENCICLOPEDIA VIVA DEL MENTOR (V4.0)
# ==============================================================================

KUDEA_KNOWLEDGE = {
    "gestion_personal": {
        "registro_horas": {
            "titulo": "⏱️ Control de Horario: Cómo Registrar la Jornada (Fichajes)",
            "keywords": ["fichaje", "horas", "fichar", "entrada", "salida", "registro", "jornada", "tiempo", "empleado", "control horario"],
            "paso_a_paso": [
                "**Opción 1: Registro Rápido**\n   - Ve a **'Personal'** -> **'Fichaje Rápido'**.\n   - Escanea tu **código QR** o introduce tu **código numérico** de empleado.\n   - El sistema detecta automáticamente si estás entrando o saliendo.",
                "**Opción 2: QR desde móvil**\n   - Muestra tu ficha de empleado con QR a la cámara de la pantalla de fichaje.\n   - Verás el mensaje de confirmación: **'Entrada registrada'** o **'Salida registrada'**.",
                "**Opción 3: Corrección Manual (Administrador)**\n   - Ve a **'Personal'** -> **'Listado de Empleados'**.\n   - Entra en la ficha del empleado -> pestaña **'Asistencia'** -> **'+ Añadir Fichaje Manual'**.",
                "**Consultar tus Horas:**\n   - En la pantalla de fichaje, pulsa **'Mi Historial'** e introduce tu código para ver las horas del mes."
            ],
            "deep_memory": [
                "⚡ **Modelo Técnico**: Cada registro es un `Punch`. Si `clock_out` está vacío, el empleado está 'Dentro'.",
                "⚡ **Seguridad**: Los tokens de QR son únicos por empleado para evitar suplantaciones.",
                "⚡ **Cálculo**: La jornada se calcula restando `clock_in` de `clock_out`."
            ]
        }
    },
    "inventario_y_logistica": {
        "impresion_etiquetas": {
            "titulo": "🏷️ Cómo Imprimir o Descargar Códigos de Barras",
            "keywords": ["barras", "etiqueta", "imprimir", "barcode", "sticker", "ean", "codigo", "descargar", "codigo de barras"],
            "paso_a_paso": [
                "**Paso 1:** Ve al menú lateral -> **'Productos'** o **'Inventario'**.",
                "**Paso 2:** Usa el buscador para encontrar el producto que quieres etiquetar.",
                "**Paso 3: Dos opciones desde la lista:**\n     1. **Icono de Impresora** 🖨️: Abre la ventana de impresión para una etiqueta individual.\n     2. **Icono de Descarga** ⬇️: Descarga el código como imagen PNG para pegarlo en documentos.",
                "**Paso 4: Imprimir todos los del pedido:**\n   - Filtra por **'Stock Bajo'** y pulsa **'Imprimir Pedido'** -> PDF con todos los artículos que necesitas."
            ],
            "deep_memory": [
                "⚡ **Tecnología**: Códigos generados con `JsBarcode` en tiempo real desde el navegador.",
                "⚡ **Formato**: CODE128 por defecto (el más compatible con lectores de mano).",
                "⚡ **Impresoras**: La vista de impresión está optimizada para impresoras térmicas tipo Zebra o Brother."
            ]
        },
        "stock_bajo": {
            "titulo": "🟠 Ver Productos con Stock Bajo o Agotados",
            "keywords": ["stock bajo", "stock minimo", "reposicion", "agotado", "faltan", "reponer", "poco stock", "quedan", "bajo", "minimo", "alerta stock", "productos agotados"],
            "paso_a_paso": [
                "**¿Dónde lo veo?**\nVe al menú **'Productos'**. Hay un filtro llamado **'Stock Bajo'**. Ábrelo y verás todos los productos que necesitan reposición.",
                "**Entender los colores:**\n   - 🟠 **Naranja**: El stock actual es inferior al mínimo que configuraste.\n   - 🔴 **Rojo**: El producto está completamente agotado (stock = 0).",
                "**Generar Pedido al Proveedor:**\n   1. Filtra por **'Stock Bajo'**.\n   2. Pulsa **'Imprimir Pedido'** arriba a la derecha.\n   3. Se genera un PDF listo para enviar al proveedor.",
                "**Reponer el stock:**\n   - Entra en la ficha del producto y usa **'+Entrada de Stock'** para añadir las unidades que han llegado."
            ],
            "deep_memory": [
                "⚡ **Lógica**: El producto aparece como 'Stock Bajo' cuando `stock < stock_minimo`.",
                "⚡ **Propiedad calculada**: El modelo `Producto` tiene la propiedad `necesita_reposicion` que devuelve `True` automáticamente."
            ]
        }
    },
    "gestion_tesoreria": {
        "apertura_caja": {
            "titulo": "🔓 Cómo Empezar el Día: Abriendo la Caja",
            "keywords": ["apertura", "abrir", "fondo", "inicio", "sesion", "inicial", "empezar", "abrir caja", "fondo inicial"],
            "paso_a_paso": [
                "**¿Por qué abrimos caja?**\nPara decirle al sistema con cuánto dinero físico empezamos el día, así al final las cuentas cuadran.",
                "**Los Pasos:**\n   1. Pulsa en **'Caja'**. Si es tu primera vez en el día, verás la pantalla de apertura.\n   2. Introduce el **Fondo Inicial** (el dinero en el cajón para dar cambios).\n   3. Dale a **'Confirmar Apertura'**. ¡Listo!",
                "**Consejo:** Si falta cambio, déjalo escrito en el campo de observaciones antes de confirmar."
            ],
            "deep_memory": [
                "⚡ **Bloqueo**: Sin apertura de caja activa no puedes hacer ventas. Es una medida de seguridad.",
                "⚡ **Modelo**: `cash_aperturacaja` guarda `fondo_inicial`, `usuario` y `hora_apertura`."
            ]
        },
        "cierre_arqueo": {
            "titulo": "🏷️ Cómo Cerrar la Caja y Hacer el Arqueo",
            "keywords": ["cerrar", "cierre", "arqueo", "cuadre", "balance", "fin", "contar", "efectivo", "diferencia", "cuadrar", "cerrar caja", "fin del dia", "arqueo diario"],
            "paso_a_paso": [
                "**¿Qué es un arqueo?**\nEs revisar al final del día si el dinero del cajón coincide con lo que el sistema dice que deberías tener. Si cuadra, perfecto.",
                "**Los Pasos:**\n   1. Ve a **'Caja'** -> **'Cierre del Día'** o **'Arqueo'**.\n   2. Cuenta el dinero físico del cajón y escríbelo en **'Efectivo Contado'**.\n   3. El sistema te muestra la **Diferencia** (si sobra o falta algo).\n   4. Escribe una nota si hubo algo especial ese día.",
                "**Guardar y PDF:**\n   - Pulsa **'Guardar Arqueo'**. La caja queda cerrada.\n   - Descarga el **PDF del Arqueo** para enviarlo a tu gestoría. Incluye efectivo, tarjeta y Bizum desglosados."
            ],
            "deep_memory": [
                "⚡ **Modelo**: Los cierres se guardan en `CierreCaja` con `efectivo_esperado`, `efectivo_retirado` y `total_ventas`.",
                "⚡ **PDF unificado**: Plantilla `arqueo_pdf.html` garantiza el mismo formato profesional en todos los reportes."
            ]
        }
    },
    "analisis_y_reportes": {
        "dashboard_informes": {
            "titulo": "📊 Informes y Análisis de Negocio",
            "keywords": ["informe", "reporte", "grafico", "estadistica", "analisis", "ventas mes", "margen", "beneficio", "ganancia", "perdida"],
            "paso_a_paso": [
                "**Acceder:** Menú lateral -> **'Informes'**. Se abrirá el centro de análisis de tu negocio.",
                "**Filtrar por periodo:** Botones rápidos: **Hoy, Ayer, 7 Días, Mes, Año** o un rango personalizado con el icono de calendario.",
                "**Margen del Periodo:** Es el dinero que te queda tras restar el coste de los productos y el IVA. Es el dato más importante.",
                "**Detectar problemas:**\n   - **'Fugas de Capital'**: Productos vendidos por debajo de su coste.\n   - **'Stock Muerto'**: Productos que no se han vendido en todo el mes.",
                "**Stock Estratégico:** 'Reposición Urgente' te dice qué productos se agotarán pronto según la velocidad de venta."
            ],
            "deep_memory": [
                "⚡ **Cálculo**: Se usa el `costo` de la ficha del producto vs el `precio` de venta de cada ticket.",
                "⚡ **Ticker Operativo**: Avisa en tiempo real de eventos importantes (venta grande, stock agotado).",
                "⚡ **Predicción**: El sistema proyecta cuántos días de inventario te quedan."
            ]
        }
    },
    "gestion_productos": {
        "crear_producto": {
            "titulo": "🚀 Cómo Crear un Producto desde Cero",
            "keywords": ["crear", "producto", "nuevo", "alta", "añadir", "meter", "subir", "articulo"],
            "paso_a_paso": [
                "**Paso 1:** Menú lateral -> **'Productos'** -> botón **'+ Nuevo Artículo'** (arriba a la derecha).",
                "**Paso 2: Datos básicos:**\n   - **Nombre**: El nombre comercial.\n   - **Categoría**: Para que aparezca filtrado en el TPV.\n   - **Código de Barras**: Escanea el producto. Si no tiene, el sistema crea uno tipo 'KUD-XXXXXXXX'.",
                "**Paso 3: Precio e IVA:**\n   - **Precio de Venta (PVP)**: El precio final que paga el cliente, ya con IVA incluido.\n   - **Tipo de IVA**: 21%, 10%, 4%... El sistema lo desglosará automáticamente en el ticket.",
                "**Paso 4: Stock:**\n   - **Stock Actual**: Cuántas unidades tienes ahora mismo.\n   - **Stock Mínimo**: ¡Importante! A partir de qué cantidad quieres que te avise el sistema.",
                "**Paso 5:** Pulsa **'Guardar Producto'**. Ya aparecerá en el TPV."
            ],
            "deep_memory": [
                "⚡ **Validación**: El código de barras no puede repetirse. El sistema lo comprueba al guardar.",
                "⚡ **TPV**: Solo los productos marcados como activos aparecen en la pantalla de cobros."
            ]
        }
    },
    "gestion_servicios": {
        "crear_servicio": {
            "titulo": "🛠️ Cómo Crear un Servicio (Corte de Pelo, Masaje, etc.)",
            "keywords": ["servicio", "crear servicio", "nuevo servicio", "alta servicio", "corte", "peluqueria", "masaje", "tratamiento", "cita", "turno"],
            "paso_a_paso": [
                "**¿Qué es un servicio?**\nSon servicios que ofreces sin ser un producto físico: cortes de pelo, masajes, consultas, etc.",
                "**Paso 1:** Ve al menú **'Tienda Online'** o **'Servicios'** -> **'Gestionar Servicios'**.",
                "**Paso 2:** Pulsa el botón **'+ Nuevo Servicio'**.",
                "**Paso 3: Datos del servicio:**",
                "   - **Nombre**: Ej: 'Corte de Pelo Caballero', 'Masaje 60 min'.",
                "   - **Descripción**: Qué incluye el servicio.",
                "   - **Precio**: Cuánto cuesta.",
                "   - **Duración**: Tiempo estimado (opcional).",
                "   - **Activo**: Marquealo para que aparezca en la tienda.",
                "**Paso 4:** Guarda y ¡listo! Los clientes podrán comprarlo desde la tienda online."
            ],
            "deep_memory": [
                "⚡ **Modelo**: El modelo `Service` en `tpv_shop` tiene campos: name, description, price, is_active, duration, slug.",
                "⚡ **Tienda Online**: Los servicios aparecen en la tienda virtual para que los clientes reserven/compren.",
                "⚡ **Carrito**: Los servicios se pueden añadir al carrito igual que los productos físicos."
            ]
        },
        "vender_servicio": {
            "titulo": "💇 Cómo Vender un Servicio en el TPV",
            "keywords": ["vender servicio", "cobrar servicio", "tpv servicio", "corte pelo", "servicio peluqueria"],
            "paso_a_paso": [
                "**En el TPV (pantalla principal):**",
                "1. Busca el servicio en el panel de productos/servicios.",
                "2. Haz clic para añadirlo al ticket.",
                "3. El servicio aparece con su precio.",
                "4. Continúa como con cualquier venta normal.",
                "**Desde la Tienda Online:**",
                "1. El cliente entra en la web de tu negocio.",
                "2. Selecciona el servicio desired.",
                "3. Añade al carrito y paga online.",
                "4. Te llega la notificación del pedido."
            ],
            "deep_memory": [
                "⚡ **Sin stock**: Los servicios no afectan al inventario (stock).",
                "⚡ **TPV Shop**: Módulo `tpv_shop` gestiona tanto productos como servicios en el carrito unificado."
            ]
        }
    },
    "operaciones_venta": {
        "vender_tpv": {
            "titulo": "💰 Cómo Vender Algo Rápido en el TPV",
            "keywords": ["vender", "cobrar", "pago", "ticket", "vender producto", "operacion", "tpv", "cobro", "venta", "ventas", "cobros"],
            "paso_a_paso": [
                "**1. Seleccionar productos:** Haz clic en ellos. Aparecen en el ticket de la derecha automáticamente.",
                "**2. Cantidades:** Usa los botones **'+'** y **'-'** del ticket para ajustar sin tener que clicar varias veces.",
                "**3. Cobrar:** Pulsa el botón verde **'Pagar'**.",
                "**4. El Pago:** Elige efectivo o tarjeta. Si es efectivo, indica cuánto te dan y yo te digo el cambio exacto.",
                "**5. Finalizar:** Confirma la venta. El ticket se imprime y el stock se descuenta automáticamente."
            ],
            "deep_memory": [
                "⚡ **Seguridad**: Si el dinero recibido es menor al total, el botón de completar se bloquea.",
                "⚡ **Stock**: Se crea un `Movement` negativo al instante para mantener el inventario actualizado."
            ]
        },
        "eliminar_item_ticket": {
            "titulo": "❌ Cómo Quitar un Producto del Ticket",
            "keywords": ["quitar", "borrar", "eliminar", "errata", "equivocacion", "sacar", "ticket", "mal", "quitar del ticket"],
            "paso_a_paso": [
                "**Paso 1:** Mira el ticket de la derecha en la pantalla del TPV.",
                "**Paso 2:** Al lado del precio de cada producto hay un icono de **Papelera Roja** 🗑️. Haz clic.",
                "**Paso 3:** Confirma en el mensaje que aparece pulsando **'Eliminar'**.",
                "**Paso 4:** El sistema recalcula automáticamente el total, el IVA y el cambio."
            ],
            "deep_memory": [
                "⚡ **Técnico**: Se usa `TPV.requestRemove(id)` para el modal y `TPV.confirmRemove()` para filtrar el array `ticket`.",
                "⚡ **Sin impacto en stock**: Hasta que no se complete la venta, no hay movimiento de inventario."
            ]
        },
        "aplicar_descuento_ticket": {
            "titulo": "🏷️ Cómo Aplicar un Descuento al Ticket",
            "keywords": ["descuento", "rebaja", "promocion", "oferta", "aplicar descuento", "descuento ticket", "porcentaje", "euro descuento"],
            "paso_a_paso": [
                "**Paso 1:** Añade los productos al ticket como haces normalmente.",
                "**Paso 2:** Antes de pagar, busca el botón **'Aplicar Descuento'** en la barra superior del ticket.",
                "**Paso 3:** Se abrirá una ventana donde puedes poner el descuento:",
                "   - **En euros (€)**: Escribe el monto directo a descontar.",
                "   - **En porcentaje (%)**: Escribe el % de descuento sobre el total.",
                "**Paso 4:** Pulsa **'Aplicar'** y verás el descuento reflejado en el ticket con color rojo.",
                "**Paso 5:** El descuento se aplica sobre el subtotal (antes de IVA). Listo para cobrar."
            ],
            "deep_memory": [
                "⚡ **Campo en BD**: El modelo `Venta` tiene un campo `descuento` que guarda el valor aplicado.",
                "⚡ **Lógica**: El descuento se resta del subtotal bruto antes de calcular el IVA.",
                "⚡ **Validación**: El sistema no permite aplicar un descuento mayor al subtotal del ticket."
            ]
        },
        "descuento_producto": {
            "titulo": "💸 Cómo Poner Descuentos en Productos (Ofertas Permanentes)",
            "keywords": ["descuento producto", "oferta producto", "rebaja producto", "descuento permanente", "promocion producto", "precio oferta"],
            "paso_a_paso": [
                "**¿Qué es?** Puedes configurar un descuento fijo (%) en un producto para que siempre se venda con oferta.",
                "**Cómo hacerlo:**",
                "1. Ve a **'Productos'** -> busca el producto.",
                "2. Entra en **'Editar'** el producto.",
                "3. Busca el campo **'Descuento'** (está al lado del precio).",
                "4. Escribe el porcentaje: por ejemplo **20** para 20% de descuento.",
                "5. Guarda los cambios.",
                "**Resultado:** El precio se muestra tachado con el nuevo precio reducido automáticamente en el TPV."
            ],
            "deep_memory": [
                "⚡ **Campo**: El modelo `Producto` tiene `descuento = models.DecimalField(...)`.",
                "⚡ **Cálculo**: `precio_final = precio * (1 - descuento / 100)`.",
                "⚡ **Visual**: En el TPV se muestra una etiqueta '-{descuento}%' en productos con oferta."
            ]
        }
    },
    "sistema_ia": {
        "status_cerebro": {
            "titulo": "🧠 ¿Qué ha aprendido la IA de Kudea?",
            "keywords": ["aprendizaje", "aprender", "saber", "conocer", "inteligencia", "cerebro", "datos", "sistema", "estatus", "estado"],
            "paso_a_paso": [
                "**¿Qué he aprendido?**\nHe analizado todo el código fuente de Kudea: modelos de datos, pantallas y lógica de negocio. Lo tengo guardado en `dynamic_brain.json`.",
                "**¿Cómo preguntarme?**\n   - Pregúntame por cualquier función: *'¿cómo creo un producto?'*, *'¿cómo hago el arqueo?'*, *'¿qué es el IVA?'*...\n   - También puedo responder preguntas técnicas sobre el código si me preguntas por un módulo específico.",
                "**¿Cómo se actualiza mi memoria?**\n   - Cada vez que se ejecuta `brain_sync.py`, mi cerebro escanea el proyecto y se actualiza automáticamente."
            ],
            "deep_memory": [
                "⚡ **Módulos conocidos**: TPV, Personal, Stock, Caja, Facturación, Clientes, Presupuestos e Informes.",
                "⚡ **Persistencia**: La memoria dinámica está en `applications/home/dynamic_brain.json`."
            ]
        }
    },
    "arquitectura_ingenieria": {
        "estructura_global": {
            "titulo": "🏗️ Cómo Está Construido Kudea por Dentro",
            "keywords": ["arquitectura", "estructura", "directorios", "tecnologia", "desarrollo", "carpetas", "como funciona", "diseno", "modulos", "creado", "construido"],
            "paso_a_paso": [
                "**1. Motor principal (Django + Python):**\n   - El proyecto usa el patrón **Modelo-Vista-Template (MVT)**.\n   - Los modelos son los datos, las vistas la lógica y los templates lo que ves en pantalla.",
                "**2. Módulos independientes:**\n   - Todo está en la carpeta `applications/`. Cada subcarpeta es un módulo: `product`, `cash`, `attendance`, etc.\n   - Si falla un módulo, los demás siguen funcionando.",
                "**3. Frontend (lo que ves):**\n   - **HTML5 + CSS** con diseño Glassmorphism (efecto cristal oscuro).\n   - El TPV usa **JavaScript puro** para ser lo más rápido posible.",
                "**4. El Mentor (yo):**\n   - Aprendo leyendo el código fuente con `brain_sync.py` y guardo el resultado en `dynamic_brain.json`."
            ],
            "deep_memory": [
                "⚡ **Backend**: Django 4.x / Python 3.x.",
                "⚡ **Base de Datos**: SQLite3 (desarrollo local, portable).",
                "⚡ **Seguridad**: `LoginRequiredMixin` en todas las vistas + `transaction.atomic` para stock.",
                "⚡ **Carpetas clave**: `kudea/` (config), `applications/` (lógica), `templates/` (HTML), `static/` (CSS/JS)."
            ]
        }
    },
    "fiscalidad_avanzada": {
        "configurar_iva": {
            "titulo": "⚖️ ¿Qué es el IVA y Cómo se Gestiona en Kudea?",
            "keywords": ["iva", "impuesto", "cambiar iva", "configuracion iva", "fiscal", "que es iva", "modificar iva"],
            "paso_a_paso": [
                "**¿Qué es el IVA?**\nEs el impuesto que se aplica a cada venta. En Kudea, metes el precio final (IVA incluido) y el sistema lo desglosa automáticamente sin que tú hagas nada.",
                "**¿Cómo cambio el IVA general?**\n   - Ve a **'Administración'** -> **'Configuración Fiscal'** para cambiar el IVA por defecto de toda la tienda.",
                "**¿Y si un producto tiene un IVA diferente?**\n   - Edita el producto directamente. Hay un campo **'Tipo de IVA'** donde puedes poner 21%, 10% o 4%.",
                "**En el ticket:** Kudea muestra siempre la base imponible y la cuota de IVA separadas, para que tu contabilidad esté perfecta."
            ],
            "deep_memory": [
                "⚡ **Fórmula**: `Base = PVP / (1 + tasa_iva)`. El sistema calcula solo, tú solo pones el PVP.",
                "⚡ **Modelo**: `ConfiguracionFiscal` guarda el IVA por defecto y el fondo de caja sugerido."
            ]
        }
    },
    "gestion_presupuestos": {
        "crear_presupuesto": {
            "titulo": "📄 Cómo Crear un Presupuesto",
            "keywords": ["crear presupuesto", "nuevo presupuesto", "presupuestar", "cotizacion", "presupuesto cliente", "hacer presupuesto", "elaborar presupuesto"],
            "paso_a_paso": [
                "**Paso 1:** Ve al menú **'Presupuestos'**.",
                "**Paso 2:** Pulsa **'+ Nuevo Presupuesto'**.",
                "**Paso 3: Datos del cliente:**",
                "   - Busca o crea un cliente (nombre, NIF, email, teléfono).",
                "**Paso 4: Añadir servicios/productos:**",
                "   - Escribe la descripción del trabajo.",
                "   - Indica cantidad y precio unitario.",
                "   - Opcional: aplica un % de descuento a cada línea.",
                "**Paso 5:** El sistema calcula automáticamente el subtotal, descuento, IVA y total.",
                "**Paso 6:** Pulsa **'Guardar Presupuesto'**. Se puede exportar a PDF para enviar al cliente."
            ],
            "deep_memory": [
                "⚡ **Modelo**: `Budget` y `BudgetItem` en el módulo `budget`.",
                "⚡ **Descuentos**: Cada línea de presupuesto puede tener su propio descuento (%) y el presupuesto global también.",
                "⚡ **Plantilla**: Se genera un PDF profesional con el logo de la empresa."
            ]
        },
        "presupuesto_a_factura": {
            "titulo": "🧾 Convertir Presupuesto en Factura",
            "keywords": ["presupuesto a factura", "facturar presupuesto", "aprobar presupuesto", "presupuesto aceptado"],
            "paso_a_paso": [
                "**Cuando el cliente acepta el presupuesto:**",
                "1. Ve al **'Presupuestos'** y abre el presupuesto aceptado.",
                "2. Pulsa el botón **'Convertir a Factura'**.",
                "3. Se creará automáticamente una factura con los mismos datos, precios y descuentos.",
                "4. Revisa la factura y márcala como **'Emitida'**."
            ],
            "deep_memory": [
                "⚡ **Flujo**: Budget -> Factura manteniendo todos los detalles.",
                "⚡ **Factura**: Se guarda en el módulo `invoice` con todos los campos fiscales."
            ]
        }
    },
    "gestion_facturas": {
        "crear_factura": {
            "titulo": "🧾 Cómo Crear una Factura",
            "keywords": ["factura", "crear factura", "nueva factura", "facturar", "emitir factura", "factura pdf"],
            "paso_a_paso": [
                "**Opción 1: Desde una venta del TPV:**",
                "1. Al cobrar, marca la opción **'Generar Factura'**.",
                "2. Rellena los datos del cliente (nombre, NIF, dirección).",
                "3. La factura se genera automáticamente con todos los detalles.",
                "**Opción 2: Manual (desde cero):**",
                "1. Ve a **'Facturación'** -> **'Nueva Factura'**.",
                "2. Selecciona el cliente o introduce sus datos.",
                "3. Añade los productos/servicios con sus precios.",
                "4. El sistema aplica IVA, descuentos, etc.",
                "5. Guarda y descarga el PDF."
            ],
            "deep_memory": [
                "⚡ **Modelo**: `Factura` en el módulo `invoice` tiene campos: serie, número, cliente, subtotal, descuento_global, base_imponible, iva, total, etc.",
                "⚡ **IVA**: Soporta diferentes tipos de IVA (21%, 10%, 4%) por línea.",
                "⚡ **IRPF**: Opcional, para profesionales autónomos."
            ]
        },
        "factura_rectificativa": {
            "titulo": "↩️ Cómo Hacer una Factura Rectificativa (Abono)",
            "keywords": ["factura rectificativa", "abono", "devolucion", "rectificar factura", "anular factura"],
            "paso_a_paso": [
                "**¿Cuándo se usa?** Para rectificar errores o devoluciones.",
                "**Paso 1:** Ve a **'Facturación'** y abre la factura a rectificar.",
                "2. Pulsa **'Crear Factura Rectificativa'** o **'Abono'**.",
                "**Paso 3:** El sistema crea una nueva factura con:",
                "   - Serie diferente (ej: R1).",
                "   - Mismos datos pero con signo negativo o con los importes correctos.",
                "   - Campo **'Motivo de rectificación'** (selecciona: error, devolución, etc.).",
                "**Paso 4:** Confirma y descarga el PDF."
            ],
            "deep_memory": [
                "⚡ **Código**: La factura rectificativa se vincula a la original mediante `factura_rectificada`.",
                "⚡ **Modelo**: Campo `motivo_rectificacion` en `Factura`."
            ]
        }
    },
    "gestion_clientes": {
        "crear_cliente": {
            "titulo": "👤 Cómo Dar de Alta un Cliente",
            "keywords": ["cliente", "crear cliente", "nuevo cliente", "alta cliente", "añadir cliente", "registrar cliente"],
            "paso_a_paso": [
                "**Paso 1:** Ve al menú **'Clientes'** o desde el TPV.",
                "**Paso 2:** Pulsa **'+ Nuevo Cliente'**.",
                "**Paso 3: Datos del cliente:**",
                "   - **Nombre**: Nombre completo o razón social.",
                "   - **NIF/CIF**: Documento de identificación fiscal.",
                "   - **Email**: Para enviarle facturas o presupuestos.",
                "   - **Teléfono**: Para contactar.",
                "   - **Dirección**: Para la factura (calle, ciudad, provincia, CP).",
                "**Paso 4:** Guarda el cliente.",
                "**Resultado:** El cliente aparecerá en las búsquedas rápidas del TPV y presupuestos."
            ],
            "deep_memory": [
                "⚡ **Modelo**: `Cliente` en el módulo `customer`.",
                "⚡ **Validación**: El NIF se valida para que no se repita.",
                "⚡ **Historial**: Al comprar, el cliente se associa a la venta para estadísticas."
            ]
        }
    },
    "metodos_pago": {
        "configurar_pago": {
            "titulo": "💳 Cómo Configurar Métodos de Pago",
            "keywords": ["pago", "metodo pago", "configurar pago", "bizum", "tarjeta", "efectivo", "transferencia", "nuevo metodo"],
            "paso_a_paso": [
                "**Paso 1:** Ve a **'Administración'** -> **'Métodos de Pago'**.",
                "**Paso 2:** Verás los métodos activos: Efectivo, Tarjeta, Bizum.",
                "**Paso 3: Añadir nuevo:**",
                "   - Pulsa **'+ Añadir Método'**.",
                "   - Nombre: ej 'Transferencia Bancaria'.",
                "   - Descripción: ej 'IBAN: ES12...'.",
                "   - **Activo**: Marquealo para que aparezca en el TPV.",
                "   - **Acepta cambio**: Para efectivo y Bizum, permite dar cambio.",
                "**Paso 4:** Guarda y listo."
            ],
            "deep_memory": [
                "⚡ **Modelo**: `MetodoPago` en el módulo `home` o `payments`.",
                "⚡ **TPV**: Los métodos activos aparecen como botones en la pantalla de cobro."
            ]
        }
    },
    "gestion_inventario": {
        "entrada_stock": {
            "titulo": "📥 Cómo Registrar Entrada de Mercancía (Reposición)",
            "keywords": ["entrada", "recibir", "reposicion", "proveedor", "pedido", "llegada", "mercancia", "incrementar stock", "anadir stock"],
            "paso_a_paso": [
                "**¿Para qué sirve?** Cuando te llega mercancía del proveedor, la registras para que el stock se actualice.",
                "**Paso 1:** Ve a **'Productos'** y busca el artículo.",
                "**Paso 2:** Entra en la ficha del producto.",
                "**Paso 3:** Busca el botón **'+ Entrada de Stock'** o **'Añadir Stock'**.",
                "**Paso 4:** Introduce la cantidad recibida.",
                "**Paso 5 (opcional):** Añade una nota (ej: 'Pedido #123 del proveedor X').",
                "**Paso 6:** Confirma. El stock se actualiza automáticamente."
            ],
            "deep_memory": [
                "⚡ **Modelo**: Se crea un `Movement` con tipo 'entrada' o 'entrada_stock'.",
                "⚡ **Historial**: Cada movimiento queda registrado para auditoría⚡ **Alertas**: Si el.",
                " stock supera el mínimo, la alerta de 'Stock Bajo' desaparece."
            ]
        },
        "salida_stock": {
            "titulo": "📤 Cómo Registrar Salida de Mercancía",
            "keywords": ["salida", "dar de baja", "perdida", "robo", "merma", "rotura", "ajuste negativo", "descontar stock"],
            "paso_a_paso": [
                "**¿Para qué sirve?** Para registrar productos que se pierden, se rompen, o se dan de baja.",
                "**Paso 1:** Ve a **'Productos'** y busca el artículo.",
                "**Paso 2:** Entra en la ficha del producto.",
                "**Paso 3:** Busca el botón **'- Salida de Stock'** o **'Dar de Baja'**.",
                "**Paso 4:** Introduce la cantidad y el **motivo** (pérdida, rotura, donación, etc.).",
                "**Paso 5:** Confirma. El stock disminuye."
            ],
            "deep_memory": [
                "⚡ **Modelo**: Se crea un `Movement` con tipo 'salida' o 'baja'.",
                "⚡ **Motivo**: El campo 'observaciones' guarda el motivo de la salida."
            ]
        },
        "ajuste_inventario": {
            "titulo": "⚖️ Cómo Hacer un Ajuste de Inventario",
            "keywords": ["ajuste", "inventario", "contar", "recontar", "cuadre", "diferencia stock", "inventario fisico"],
            "paso_a_paso": [
                "**¿Para qué sirve?** Cuando el stock real no coincide con el del sistema, haces un ajuste.",
                "**Opción 1 (producto específico):**",
                "1. Ve al producto.",
                "2. Edita directamente el campo 'Stock Actual'.",
                "3. Añade una nota explicando la diferencia.",
                "**Opción 2 (inventario completo):**",
                "1. Ve a **'Informes'** -> **'Inventario'**.",
                "2. Exporta la lista a Excel.",
                "3. Compara con tu inventario físico.",
                "4. Haz ajustes uno por uno o contacta al administrador."
            ],
            "deep_memory": [
                "⚡ **Auditoría**: Todos los ajustes quedan registrados con fecha y usuario.",
                "⚡ **Tabla**: El ajuste se guarda en `Movement` con tipo 'ajuste'."
            ]
        },
        "exportar_productos": {
            "titulo": "📊 Cómo Exportar Productos a Excel/CSV",
            "keywords": ["exportar", "excel", "csv", "descargar", "productos lista", "inventario exportar"],
            "paso_a_paso": [
                "**Paso 1:** Ve a **'Productos'**.",
                "**Paso 2:** Verás la lista de todos tus artículos.",
                "**Paso 3:** Busca el botón **'Exportar'** o **'Descargar'** (normalmente arriba a la derecha).",
                "**Paso 4:** Elige el formato: **Excel (.xlsx)** o **CSV**.",
                "**Paso 5:** Se descargará el archivo con todos los productos, precios, stocks, etc."
            ],
            "deep_memory": [
                "⚡ **Django**: Se usa `pandas` o `openpyxl` para generar Excel.",
                "⚡ **Campos**: Incluye nombre, código, precio, stock, categoría, proveedor."
            ]
        }
    },
    "gestion_tienda_online": {
        "tpv_shop_inicio": {
            "titulo": "🛒 Cómo Usar la Tienda Online (TPV Shop)",
            "keywords": ["tienda online", "tpv shop", "ecommerce", "carrito", "compra online", "web tienda"],
            "paso_a_paso": [
                "**¿Qué es?** Una tienda online donde tus clientes pueden comprar desde el móvil o ordenador.",
                "**Acceder:** Escribe la URL de tu tienda (normalmente /shop o /tienda).",
                "**Para el cliente:**",
                "1. Navega por las categorías.",
                "2. Añade productos al carrito.",
                "3. Elige método de pago.",
                "4. Confirma el pedido.",
                "**Para ti:**",
                "1. Ve a **'Pedidos'** o **'Órdenes'**.",
                "2. Verás los pedidos nuevos.",
                "3. Confirma el pago y prepara el pedido.",
                "4. Cambia el estado a 'Completado'."
            ],
            "deep_memory": [
                "⚡ **Módulo**: `tpv_shop` gestiona productos, servicios, carrito y pedidos.",
                "⚡ **Payment**: Integra con pasarelas de pago o contrareembolso.",
                "⚡ **Plantillas**: En `templates/tpv_shop/`."
            ]
        }
    },
    "configuracion_sistema": {
        "configuracion_general": {
            "titulo": "⚙️ Configuración General del Sistema",
            "keywords": ["configuracion", "ajustes", "opciones", "administracion", "parametros", "preferencias"],
            "paso_a_paso": [
                "**Paso 1:** Busca el menú **'Administración'** o **'Configuración'** en el lateral.",
                "**Opciones típicas:**",
                "   - **Datos de la tienda**: Nombre, dirección, teléfono, email.",
                "   - **Configuración Fiscal**: IVA por defecto, IRPF.",
                "   - **Caja**: Fondo inicial por defecto.",
                "   - **TPV**: Impimir tickets, mostrar stock, moneda.",
                "   - **Usuarios**: Crear empleados, permisos.",
                "   - **Copias de seguridad**: Descargar DB."
            ],
            "deep_memory": [
                "⚡ **Modelo**: `ConfiguracionTPV` guarda los ajustes principales.",
                "⚡ **Seguridad**: Solo administradores pueden cambiar configuración."
            ]
        },
        "usuarios_permisos": {
            "titulo": "👥 Gestión de Usuarios y Permisos",
            "keywords": ["usuario", "permiso", "empleado", "rol", "administrador", "acceso", "restrict", "autorizacion"],
            "paso_a_paso": [
                "**Crear empleado:**",
                "1. Ve a **'Personal'** o **'Empleados'**.",
                "2. Pulsa **'+ Nuevo Empleado'**.",
                "3. Rellena sus datos y genera un código de fichaje.",
                "**Permisos:**",
                "   - **Administrador**: Acceso total.",
                "   - **Caja**: Solo puede operar ventas.",
                "   - **Solo lectura**: Puede ver informes pero no tocar nada.",
                "**Fichaje QR:** Cada empleado tiene un QR único para registrar su jornada."
            ],
            "deep_memory": [
                "⚡ **Modelo**: `Empleado` con campos: nombre, código, qr_token, permisos.",
                "⚡ **Permisos Django**: Usa `is_staff`, `is_superuser` y permisos personalizados."
            ]
        }
    }
}


def analyze_code_for_query(query, normalized_words):
    """Analiza TODO el código fuente para responder preguntas automáticamente."""
    # Usar __file__ para obtener la ruta correcta
    current_file = os.path.abspath(__file__)
    base_dir = os.path.dirname(current_file)
    project_dir = os.path.dirname(os.path.dirname(base_dir))
    
    search_terms = normalized_words if normalized_words else query.lower().split()
    results = {
        'models': [],
        'views': [],
        'templates': [],
        'forms': [],
        'urls': [],
        'actions': []
    }
    
    apps_dir = os.path.join(project_dir, 'applications')
    if not os.path.exists(apps_dir):
        return results
    
    # Analizar cada aplicación
    for app_name in os.listdir(apps_dir):
        app_path = os.path.join(apps_dir, app_name)
        if not os.path.isdir(app_path):
            continue
        
        # Skip non-app directories
        if app_name.startswith('__'):
            continue
        
        # 1. Analizar models.py
        models_file = os.path.join(app_path, 'models.py')
        if os.path.exists(models_file):
            with open(models_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                models_info = extract_models_info(content, app_name, search_terms)
                results['models'].extend(models_info)
        
        # 2. Analizar views.py
        views_file = os.path.join(app_path, 'views.py')
        if os.path.exists(views_file):
            with open(views_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                views_info = extract_views_info(content, app_name, search_terms)
                results['views'].extend(views_info)
        
        # 3. Analizar forms.py
        forms_file = os.path.join(app_path, 'forms.py')
        if os.path.exists(forms_file):
            with open(forms_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                forms_info = extract_forms_info(content, app_name, search_terms)
                results['forms'].extend(forms_info)
        
        # 4. Analizar urls.py
        urls_file = os.path.join(app_path, 'urls.py')
        if os.path.exists(urls_file):
            with open(urls_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                urls_info = extract_urls_info(content, app_name, search_terms)
                results['urls'].extend(urls_info)
    
    # 5. Analizar templates
    templates_dir = os.path.join(project_dir, 'templates')
    if os.path.exists(templates_dir):
        for root, dirs, files in os.walk(templates_dir):
            for file in files:
                if file.endswith('.html'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        templates_info = extract_template_info(content, file_path, project_dir, search_terms)
                        results['templates'].extend(templates_info)
    
    # 6. Generar acciones basadas en lo encontrado
    results['actions'] = generate_actions_from_analysis(results, search_terms)
    
    return results


def extract_models_info(content, app_name, search_terms):
    """Extrae información de los modelos."""
    models = []
    
    # Encontrar todas las clases de modelos
    pattern = r'class\s+(\w+)\(.*?Model.*?\):'
    matches = re.finditer(pattern, content)
    
    for match in matches:
        model_name = match.group(1)
        
        # Verificar si este modelo es relevante para la búsqueda
        relevance = calculate_relevance(model_name, search_terms)
        
        # Si no hay términos de búsqueda, devolver todos los modelos
        if not search_terms or len(search_terms) == 0:
            relevance = 10
        
        # Si no es relevante, buscar en el contenido
        if relevance == 0 and search_terms:
            if not any_term_in_text(search_terms, content[match.start():match.start()+2000]):
                continue
            relevance = 20  # Encontrado en contenido
        
        # Extraer campos
        model_content = content[match.end():]
        next_class = re.search(r'\nclass\s+\w+', model_content)
        if next_class:
            model_content = model_content[:next_class.start()]
        
        fields = re.findall(r'(\w+)\s*=\s*models\.\w+', model_content)
        
        # Extraer métodos importantes
        methods = re.findall(r'def\s+(\w+)\s*\(', model_content)
        
        models.append({
            'app': app_name,
            'name': model_name,
            'fields': fields[:15],
            'methods': methods[:10],
            'relevance': relevance
        })
    
    return models


def extract_views_info(content, app_name, search_terms):
    """Extrae información de las vistas."""
    views = []
    
    # Encontrar clases de vistas
    class_pattern = r'class\s+(\w+)\((.*?View|View\)):'
    class_matches = re.finditer(class_pattern, content)
    
    for match in class_matches:
        view_name = match.group(1)
        parent = match.group(2)
        
        relevance = calculate_relevance(view_name, search_terms)
        
        # Si no hay términos de búsqueda, devolver todas las vistas
        if not search_terms or len(search_terms) == 0:
            relevance = 10
        elif relevance == 0:
            if not any_term_in_text(search_terms, content[match.start():match.start()+1000]):
                continue
            relevance = 20
        
        # Extraer métodos de la vista
        view_content = content[match.end():]
        next_class = re.search(r'\nclass\s+\w+', view_content)
        if next_class:
            view_content = view_content[:next_class.start()]
        
        methods = re.findall(r'def\s+(\w+)\s*\(', view_content)
        
        views.append({
            'app': app_name,
            'name': view_name,
            'parent': parent,
            'methods': methods[:15],
            'relevance': relevance
        })
    
    # También buscar funciones de vistas
    func_pattern = r'def\s+(\w+)\s*\('
    func_matches = re.finditer(func_pattern, content)
    
    for match in func_matches:
        func_name = match.group(1)
        if func_name in ['__init__', '__str__', '__unicode__', 'get_context_data']:
            continue
        
        relevance = calculate_relevance(func_name, search_terms)
        if relevance > 0 or not search_terms:
            views.append({
                'app': app_name,
                'name': func_name,
                'type': 'function',
                'relevance': max(relevance, 5)
            })
    
    return views


def extract_forms_info(content, app_name, search_terms):
    """Extrae información de los formularios."""
    forms = []
    
    pattern = r'class\s+(\w+)\(.*?Form.*?\):'
    matches = re.finditer(pattern, content)
    
    for match in matches:
        form_name = match.group(1)
        
        relevance = calculate_relevance(form_name, search_terms)
        if relevance == 0 and not any_term_in_text(search_terms, content[match.start():match.start()+1000]):
            continue
        
        form_content = content[match.end():]
        next_class = re.search(r'\nclass\s+\w+', form_content)
        if next_class:
            form_content = form_content[:next_class.start()]
        
        fields = re.findall(r"['\"](\w+)['\"]\s*:", form_content)
        
        forms.append({
            'app': app_name,
            'name': form_name,
            'fields': fields[:10],
            'relevance': relevance
        })
    
    return forms


def extract_urls_info(content, app_name, search_terms):
    """Extrae información de las URLs."""
    urls = []
    
    # Buscar patrones path
    path_pattern = r"path\(['\"]([^'\"]+)['\"]"
    matches = re.finditer(path_pattern, content)
    
    for match in matches:
        url_path = match.group(1)
        
        # Buscar la vista asociada
        line_start = content.rfind('\n', 0, match.start())
        line_end = content.find('\n', match.end())
        line = content[line_start:line_end] if line_end > 0 else content[line_start:]
        
        view_match = re.search(r',\s*(\w+)', line)
        view_name = view_match.group(1) if view_match else ''
        
        if view_name:
            relevance = calculate_relevance(view_name, search_terms) + calculate_relevance(url_path, search_terms)
            if relevance > 0:
                urls.append({
                    'app': app_name,
                    'path': url_path,
                    'view': view_name,
                    'relevance': relevance
                })
    
    return urls


def extract_template_info(content, file_path, project_dir, search_terms):
    """Extrae información de las plantillas."""
    templates = []
    
    rel_path = os.path.relpath(file_path, project_dir)
    
    # Buscar menciones a los términos de búsqueda
    for term in search_terms:
        if len(term) < 3:
            continue
        
        # Buscar botones, formularios, enlaces
        if term.lower() in content.lower():
            # Encontrar botones relacionados
            buttons = re.findall(r'<button[^>]*>([^<]+)</button>', content, re.IGNORECASE)
            button_matches = [b for b in buttons if term.lower() in b.lower()]
            
            # Encontrar enlaces
            links = re.findall(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>', content, re.IGNORECASE)
            link_matches = [(h, t) for h, t in links if term.lower() in t.lower()]
            
            # Encontrar formularios
            forms = re.findall(r'<form[^>]*>', content, re.IGNORECASE)
            
            templates.append({
                'file': rel_path,
                'term': term,
                'buttons': button_matches[:5],
                'links': link_matches[:5],
                'forms_count': len(forms),
                'relevance': calculate_relevance(term, search_terms)
            })
    
    return templates


def generate_actions_from_analysis(results, search_terms):
    """Genera acciones posibles basándose en el análisis."""
    actions = []
    
    # Generar acciones basadas en modelos
    for model in results.get('models', []):
        if model['relevance'] > 0:
            model_name = model['name'].lower()
            
            # Determinar tipo de entidad
            entity_type = identify_entity_type(model_name, model.get('fields', []))
            
            # Generar acciones típicas para este modelo
            for action in ['crear', 'ver', 'editar', 'eliminar', 'listar']:
                if action in ['crear', 'ver', 'editar', 'eliminar']:
                    actions.append({
                        'action': action,
                        'entity': model['name'],
                        'entity_type': entity_type,
                        'app': model['app'],
                        'score': model['relevance']
                    })
    
    return actions


def identify_entity_type(model_name, fields):
    """Identifica el tipo de entidad basándose en el nombre y campos."""
    name_lower = model_name.lower()
    
    # Palabras clave para identificar tipo
    types = {
        'producto': ['product', 'articulo', 'item', 'producto'],
        'servicio': ['service', 'servicio', 'tratamiento'],
        'cliente': ['client', 'cliente', 'customer'],
        'factura': ['invoice', 'factura', 'bill'],
        'presupuesto': ['budget', 'presupuesto', 'quote'],
        'pago': ['payment', 'pago'],
        'caja': ['cash', 'caja', 'arqueo'],
        'empleado': ['employee', 'empleado', 'trabajador', 'staff'],
        'asistencia': ['attendance', 'asistencia', 'punch', 'fichaje'],
        'movimiento': ['movement', 'movimiento', 'stock'],
        'categoria': ['category', 'categoria'],
    }
    
    for entity_type, keywords in types.items():
        if any(kw in name_lower for kw in keywords):
            return entity_type
    
    return 'entidad'


def calculate_relevance(text, search_terms):
    """Calcula la relevancia de un texto para los términos de búsqueda."""
    if not search_terms:
        return 0
    
    text_lower = text.lower()
    score = 0
    
    for term in search_terms:
        if len(term) < 3:
            continue
        
        # Coincidencia exacta
        if term.lower() == text_lower:
            score += 100
        # El término está contenido
        elif term.lower() in text_lower:
            score += 50
        # Similitud
        elif difflib.SequenceMatcher(None, term.lower(), text_lower).ratio() > 0.6:
            score += 30
    
    return score


def any_term_in_text(terms, text):
    """Verifica si algún término está en el texto."""
    text_lower = text.lower()
    return any(t.lower() in text_lower for t in terms if len(t) >= 3)


def generate_auto_response(query, normalized_words, analysis_results):
    """Genera una respuesta automática basada en el análisis COMPLETO del código."""
    
    # Si no hay resultados relevantes, intentar búsqueda más amplia
    has_relevant_data = (
        len(analysis_results.get('models', [])) > 0 or
        len(analysis_results.get('views', [])) > 0 or
        len(analysis_results.get('actions', [])) > 0
    )
    
    if not has_relevant_data:
        return None
    
    response = f"## 🔍 Análisis Automático: '{query}'\n\n"
    response += "He analizado el código fuente de Kudea y esto es lo que encontré:\n\n"
    
    # 1. Entidades relacionadas (Modelos)
    models = analysis_results.get('models', [])
    if models:
        response += "### 🗃️ **Entidades/Datos relacionados:**\n"
        for model in models[:5]:
            fields_str = ', '.join(model.get('fields', [])[:5])
            if fields_str:
                response += f"- **{model['name']}** ({model['app']}): {fields_str}...\n"
            else:
                response += f"- **{model['name']}** ({model['app']})\n"
        response += "\n"
    
    # 2. Acciones posibles
    actions = analysis_results.get('actions', [])
    if actions:
        response += "### ⚙️ **Qué puedes hacer:**\n"
        
        # Agrupar por tipo de acción
        grouped = {}
        for a in actions[:8]:
            action = a['action']
            if action not in grouped:
                grouped[action] = []
            grouped[action].append(a['entity'])
        
        for action, entities in grouped.items():
            response += f"- **{action.upper()}** {', '.join(set(entities))}\n"
        response += "\n"
    
    # 3. Dónde está en la interfaz (Templates)
    templates = analysis_results.get('templates', [])
    if templates:
        response += "### 🖥️ **Dónde encontrarlo en la interfaz:**\n"
        seen = set()
        for t in templates[:5]:
            file = t.get('file', '')
            if file not in seen:
                seen.add(file)
                buttons = t.get('buttons', [])
                if buttons:
                    response += f"- `{file}` - Botones: {', '.join(buttons[:3])}\n"
                else:
                    response += f"- `{file}`\n"
        response += "\n"
    
    # 4. Rutas/URLs
    urls = analysis_results.get('urls', [])
    if urls:
        response += "🌐 **Rutas del sistema:**\n"
        for url in urls[:5]:
            response += f"- `/`{url.get('path', '')}` → {url.get('view', '')}\n"
        response += "\n"
    
    # 5. Formularios relacionados
    forms = analysis_results.get('forms', [])
    if forms:
        response += "📝 **Formularios relacionados:**\n"
        for form in forms[:3]:
            fields = form.get('fields', [])
            if fields:
                response += f"- **{form['name']}** ({form['app']}): {', '.join(fields[:5])}\n"
        response += "\n"
    
    response += "---\n"
    response += "💡 *Esta respuesta fue generada automáticamente analizando el código fuente. "
    response += "Puedes pedirme más detalles sobre cualquier aspecto específico.*"
    
    return response


def clean_accents(text):
    text = text.lower().strip()
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ü': 'u'
    }
    for accent, clean in replacements.items():
        text = text.replace(accent, clean)
    return text


def search_knowledge(query):
    # 1. Normalización robusta con eliminación de acentos
    query_raw = query
    query_clean = clean_accents(query)
    for char in "¿?¡!,.;:()":
        query_clean = query_clean.replace(char, "")

    words = query_clean.split()
    # Detener palabras de parada en español con acentos normalizados
    stopwords = {
        "que", "es", "el", "la", "de", "en", "para", "un", "con", "por", 
        "los", "las", "como", "hacer", "hago", "puedo", "quiero", 
        "ayuda", "sobre", "del", "al"
    }
    filtered_words = [w for w in words if w not in stopwords and len(w) > 1]

    best_matches = []

    # Sinónimos para ampliar la búsqueda
    synonyms = {
        "creo": "crear", "crea": "crear", "hago": "crear", "nuevo": "crear",
        "pago": "cobrar", "pagar": "cobrar", "cobro": "cobrar",
        "existencias": "stock", "unidades": "stock", "cantidad": "stock",
        "impuestos": "iva", "tasas": "iva",
        "informacion": "informe", "estadisticas": "informe", "graficos": "informe",
        "horas": "fichaje", "tiempo": "fichaje", "horario": "fichaje", "fichar": "fichaje",
        "barras": "etiqueta", "barcode": "etiqueta", "ean": "etiqueta", "imprimir": "etiqueta",
        "abrir": "apertura", "inicio": "apertura",
        "cerrar": "cierre", "fin": "cierre", "cuadrar": "cierre", "cuadre": "cierre",
        "quitar": "eliminar", "borrar": "eliminar", "sacar": "eliminar",
        "aprender": "aprendizaje", "cerebro": "aprendizaje", "inteligencia": "aprendizaje",
        "creado": "arquitectura", "construido": "arquitectura", "estructura": "arquitectura",
        "poco": "bajo", "agotado": "bajo", "reponer": "bajo", "reposicion": "bajo",
        "rebaja": "descuento", "promocion": "descuento", "oferta": "descuento",
        "servicios": "servicio", "tratamiento": "servicio", "corte": "servicio",
        "presupuesto": "presupuesto", "cotizacion": "presupuesto",
        "factura": "factura", "facturar": "factura", "facturacion": "factura",
        "rectificativa": "factura", "abono": "factura", "devolucion": "factura",
        "cliente": "cliente", "clientes": "cliente", "nombre": "cliente",
        "metodo": "pago", "transferencia": "pago"
    }

    normalized_words = [synonyms.get(w, w) for w in filtered_words]

    # 2. Búsqueda en Manuales (base de conocimiento estática)
    for cat_name, secciones in KUDEA_KNOWLEDGE.items():
        for sub_key, data in secciones.items():
            score = 0
            
            # Limpiar palabras clave y título para matching robusto
            clean_keywords = [clean_accents(kw) for kw in data["keywords"]]
            clean_title = clean_accents(data["titulo"])
            
            if normalized_words:
                for word in normalized_words:
                    word_clean = clean_accents(word)
                    
                    # 1. Coincidencia exacta de palabra clave
                    if word_clean in clean_keywords:
                        score += 60
                    else:
                        # 2. Coincidencia difusa de palabra clave (evita falsos positivos como venta en inventario)
                        for kw in clean_keywords:
                            # Permitir plurales simples o variaciones (ej. venta -> ventas)
                            if len(word_clean) > 3 and len(kw) > 3:
                                if word_clean == kw + 's' or kw == word_clean + 's':
                                    score += 45
                                    break
                                elif difflib.SequenceMatcher(None, word_clean, kw).ratio() > 0.8:
                                    score += 30
                                    break

                # 3. Coincidencia en el título (sin stopwords de por medio)
                title_words = clean_title.split()
                for w in normalized_words:
                    if clean_accents(w) in title_words:
                        score += 40

                # 4. Similitud global del título con la consulta limpia
                ratio = difflib.SequenceMatcher(None, query_clean, clean_title).ratio()
                if ratio > 0.6:
                    score += 50

            if score > 20:
                res = f"## {data['titulo']}\n\n"
                res += "📜 **Te explico paso a paso:**\n\n"
                for paso in data["paso_a_paso"]:
                    res += f"{paso}\n\n"
                res += "---\n"
                res += "🧠 **Para los más técnicos:**\n"
                for tech in data["deep_memory"]:
                    res += f"{tech}\n"

                best_matches.append({
                    "score": score,
                    "titulo": data["titulo"],
                    "respuesta_completa": res,
                    "tipo": "manual_paso_a_paso"
                })

    # 3. Si no hay manuales, buscar en código fuente dinámicamente
    if not best_matches:
        code_results = analyze_code_for_query(query_clean, normalized_words)
        if code_results:
            auto_response = generate_auto_response(query_clean, normalized_words, code_results)
            if auto_response:
                best_matches.append({
                    "score": 100,
                    "titulo": f"Análisis automático: {query}",
                    "respuesta_completa": auto_response,
                    "tipo": "auto_discovery"
                })
        else:
            # 4. Fallback a dynamic_brain.json
            try:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                dynamic_path = os.path.join(base_dir, 'dynamic_brain.json')
                if os.path.exists(dynamic_path):
                    with open(dynamic_path, 'r', encoding='utf-8') as f:
                        dynamic_data = json.load(f)

                    for app, info in dynamic_data.items():
                        if app == "support" and ("eliminar" in normalized_words or "quitar" in normalized_words):
                            continue

                        app_score = 0
                        tech_details = []

                        for model in info.get("modelos", []):
                            if normalized_words and any(w == model["nombre"].lower() for w in normalized_words):
                                app_score += 40
                                tech_details.append(f"🔹 **Modelo `{model['nombre']}`**: Núcleo de `{app}`.")
                            if query_clean in model["nombre"].lower():
                                app_score += 20
                                campos = model.get("campos", [])
                                if campos:
                                    tech_details.append(f"🔹 **`{model['nombre']}`**: Campos: {', '.join(campos[:5])}...")

                        for view in info.get("vistas", []):
                            if query_clean in view.lower() or any(w in view.lower() for w in normalized_words):
                                app_score += 15
                                tech_details.append(f"🖥️ **Vista `{view}`**: Detectada.")

                        if app_score >= 60 and tech_details:
                            res = f"## 🔍 Análisis Técnico: Módulo `{app.upper()}`\n\n"
                            for d in tech_details[:5]:
                                res += f"- {d}\n"
                            res += "\n---\n💡 *Análisis del código fuente.*"

                            best_matches.append({
                                "score": app_score,
                                "titulo": f"Módulo: {app}",
                                "respuesta_completa": res,
                                "tipo": "dynamic_discovery"
                            })
            except Exception:
                pass

    if best_matches:
        best_matches.sort(key=lambda x: x["score"], reverse=True)
        return [best_matches[0]]

    return []
