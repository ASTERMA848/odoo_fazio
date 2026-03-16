# Manual de Usuario: Pagos y Facturación Intermediarios (Carpinteros)

## Prerrequisitos y Configuración Inicial

1. **El Contacto Carpintero (Padre)**
   - Ve a **Contactos** y crea o selecciona el contacto del Carpintero.
   - Marca la nueva casilla de verificación **"Is Carpenter (Parent Account)"** que aparece bajo la categoría de las etiquetas (tags).
   - Esto le indicará al sistema que este contacto funciona como "Billetera" o intermediario.

2. **Los Clientes Finales (Hijos)**
   - Dentro del contacto del Carpintero, ve a la pestaña **Contactos y Direcciones**.
   - Haz clic en **Añadir**.
   - Define el Tipo como "Contacto" y pon el nombre del Cliente Final.
   - **¡Novedad!**: Podrás ver que Odoo ahora te permite colocarle a este Cliente Final su propio **CUIT**, tipo de factura y **Responsabilidad frente a ARCA** de forma 100% independiente del Padre.

## Flujo de Trabajo

### Paso 1: Pago Anticipado del Carpintero

1. Dirígete a **Contabilidad / Facturación > Clientes > Pagos**.
2. Dale a **Nuevo** y crea un pago a nombre del **Carpintero** (Ej: Juan Pérez).
3. Ingresa el monto (Ej: $50.000) y valida. Este pago queda registrado en estado *Abierto* porque es un saldo a favor en su cuenta corriente (sin cruzarlo con una factura).

### Paso 2: Facturando la Mercadería Retirada

1. Dirígete a **Contabilidad / Facturación > Clientes > Facturas**.
2. Dale a **Nuevo**. En el campo Cliente elige al **Cliente Final (Hijo)** (Ej: Constructora ABC SRL, hijo de Juan Pérez).
3. Agrega los productos como siempre.
4. Fíjate que al imprimir y validar la factura, los datos salen exepcionalmente a nombre de *Constructora ABC SRL*, usando su propio CUIT independiente.

### Paso 3: Pagar la Factura usando Crédito del Padre

1. En la misma pantalla de la factura recién validada, en la parte de abajo de la pestaña principal notarás un **nuevo panel**: "Créditos del Carpintero (Padre)".
2. Aparecerá una alerta azul informándote que su contacto principal tiene dinero a cuenta.
3. El sistema te mostrará automáticamente todos los saldos anticipados (y Notas de Crédito abiertas) que posea el Carpintero *Padre* y que sirvan para pagar.
4. A la derecha de la fila del pago de los `$50.000` del Paso 1, verás el botón azul **"Aplicar Crédito"**. Hazle clic.
5. El sistema reducirá la deuda de la Factura y rebajará el saldo a favor del Carpintero. Si es pago total, marcará la factura como *Pagada*. ¡Ya está conciliada de forma cruzada!
