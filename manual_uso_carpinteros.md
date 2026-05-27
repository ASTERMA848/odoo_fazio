# Manual de Usuario: Pagos y Facturación Intermediaria (Carpinteros)
## Flujo de Trabajo para el Usuario Final

Este manual describe el funcionamiento diario y el flujo de pasos a seguir para facturar a un Cliente Final (Hijo) utilizando los saldos a favor o anticipos de su Carpintero asociado (Padre).

---

## ⚙️ Configuración Inicial (Solo una vez)

### 1. El Contacto Carpintero (Padre / Cuenta Principal)
1. Ve a la aplicación de **Contactos** y selecciona o crea al Carpintero (ej: *Juan Pérez*).
2. Marca la casilla **"Centralizador de Pagos"** ubicada debajo del bloque de etiquetas de categorías.
3. Completa sus datos de contacto y datos fiscales habituales. Esta cuenta funcionará como la "billetera" o intermediario financiero de los fondos.

### 2. El Cliente Final (Hijo / Cuenta de Facturación)
1. Dentro de la ficha del Carpintero anterior, dirígete a la pestaña **Contactos y Direcciones** y haz clic en **Añadir**.
2. Selecciona el tipo **"Contacto"** y escribe el nombre del Cliente Final (ej: *Constructora ABC SRL*).
3. **¡Independencia Fiscal Activa!** Completa el **CUIT**, el tipo de documento y la **Responsabilidad ante AFIP / ARCA** (ej: *Responsable Inscripto*) propios de este cliente. Verás que Odoo te permite rellenar estos datos de forma 100% independiente sin copiar ni bloquear los datos del Padre.
4. Notarás que el campo superior de relación se etiqueta dinámicamente como **"Contacto relacionado"** en lugar de "Compañía" si el contacto es una Empresa, facilitando la lectura del operador.
5. Guarda el registro.

---

## 📈 Flujo de Trabajo Diario

### Paso 1: Registro de un Pago Anticipado (Cobro al Carpintero)
Cuando el Carpintero entrega dinero a cuenta o realiza un pago anticipado para compras futuras:
1. Dirígete a **Contabilidad / Facturación > Clientes > Pagos**.
2. Haz clic en **Nuevo**.
3. En el campo **Cliente**, selecciona al **Carpintero (Padre)** (ej: *Juan Pérez*).
4. Escribe el importe entregado (ej: `$50.000`) y completa los datos de diario y método de pago habituales.
5. Haz clic en **Confirmar / Validar**.
6. El pago queda registrado en estado **"Publicado" (Posted)**. Al no estar asociado a ninguna factura, este importe queda automáticamente disponible como un saldo abierto a su favor en su cuenta corriente contable.

### Paso 2: Emisión y Validación de la Factura al Cliente Final
Cuando se retira mercadería y corresponde facturar al cliente real de la obra:
1. Dirígete a **Contabilidad / Facturación > Clientes > Facturas**.
2. Haz clic en **Nuevo**.
3. En el campo **Cliente**, selecciona al **Cliente Final (Hijo)** (ej: *Constructora ABC SRL*).
4. El sistema detectará automáticamente su relación con el Carpintero asociado de forma interna.
5. Carga los productos y cantidades correspondientes en las líneas de factura.
6. Haz clic en **Confirmar**.
7. La factura queda validada. Verás que la factura física y su impresión PDF salen de forma impecable a nombre de *Constructora ABC SRL* con su CUIT propio, cumpliendo de forma estricta con todas las normativas legales de facturación.

### Paso 3: Aplicación del Crédito del Padre (Conciliación Cruzada)
Para cancelar la deuda de la factura del Cliente Final usando el dinero que entregó previamente su Carpintero:
1. Permanece en la pantalla de la factura recién confirmada del **Hijo** (ej: *Constructora ABC SRL*).
2. Dirígete a la parte inferior derecha, justo **debajo de las líneas de totales de la factura**.
3. Verás el widget oficial de Odoo de **Saldos Pendientes (Outstanding Credits)**.
4. Notarás que aparece el pago anticipado registrado en el *Paso 1* bajo el formato claro:
   `[Nro Pago] (Crédito de Juan Pérez)` por valor de `$50.000`.
5. Simplemente haz clic en el botón azul **"Añadir" (Add)** que figura junto al importe.
6. **¡Listo!** Odoo conciliará de forma cruzada la factura del Cliente Final con el pago de su Carpintero. La factura cambiará su estado inmediatamente a una cinta verde que dice **"Pagada"** de forma 100% limpia y oficial.

---
*Manual de usuario optimizado para la experiencia interactiva de Odoo 19.*
