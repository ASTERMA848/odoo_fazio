# Proyecto Odoo 19: Gestión de Carpinteros & Conciliación Contable Cruzada (Fazio)

Este repositorio contiene la personalización contable y de facturación desarrollada a medida para **Odoo 19 (compatible con entornos Enterprise y Community)**. El proyecto resuelve de manera elegante, nativa y transparente el flujo de facturación independiente para contactos Hijo (Clientes Finales) y su pago a través de saldos a favor de contactos Padre (Carpinteros).

---

## 🚀 Características Clave del Proyecto

### 1. Independencia Fiscal Total (Desacoplamiento Comercial)
*   **Decoupling Fiscal:** Permite que los contactos de tipo **Hijo** (Clientes Finales/Empresas) posean su propio **CUIT**, tipo de identificación y **Responsabilidad ante AFIP/ARCA** de forma 100% independiente de su contacto Padre (Carpintero).
*   **Sin Bloqueos:** Se eliminó la sincronización rígida y los bloqueos nativos en la interfaz XML, lo que permite modificar y facturar con total libertad.
*   **Impresión Limpia:** Se personalizó la función de visualización de nombres. Si el padre es un Carpintero, las facturas e informes muestran de forma limpia el nombre del Hijo (ej: `Constructora ABC SRL`), omitiendo el prefijo nativo de Odoo (`Carpintero, Constructora ABC SRL`).

### 2. Labeling Dinámico ("Contacto relacionado")
*   **UX Personalizada:** Si el contacto es configurado como **Empresa**, el campo nativo de relación (`parent_id`) muestra automáticamente la etiqueta **"Contacto relacionado"** en lugar del estándar "Compañía".
*   **Buscador Inteligente:** El buscador permite vincular como Padre tanto a contactos marcados explícitamente con el tilde **"Centralizador de Pagos"** como a cualquier otra cuenta principal.

### 3. Conciliación Cruzada Integrada en el Widget Nativo
*   **Centralización en Totales:** Se removieron pestañas redundantes para ofrecer una experiencia limpia e integrada.
*   **Inyección Dinámica:** Los saldos a favor (anticipos contables o notas de crédito abiertas) del contacto **Carpintero (Padre)** se muestran automáticamente en el widget de saldos pendientes de la factura del **Hijo (Cliente Final)** con el sufijo descriptivo `(Crédito de [Nombre del Carpintero])`.
*   **Conciliación Oficial:** El usuario solo debe hacer clic en el botón nativo **"Añadir" (Add)** y Odoo ejecutará una conciliación cruzada contable estándar a nivel de Ledger.

---

## 📁 Estructura del Repositorio

*   **`custom_addons/carpenter_invoicing`**: 📦 Módulo personalizado principal que contiene toda la lógica de negocio, overrides contables e interfaces XML adaptadas para Odoo 19.
*   **`documentacion_tecnica.md`**: 📑 Manual técnico detallado para desarrolladores. Incluye la arquitectura, diagramas de flujo, directrices específicas para **Odoo Enterprise**, y el protocolo de pruebas de calidad (UAT).
*   **`manual_uso_carpinteros.md`**: 📖 Guía ilustrativa paso a paso para el usuario final del sistema.
*   **`custom_addons/account-financial-reporting` (y dependencias OCA)**: ⚙️ Módulos de reporte financiero instalados únicamente para el entorno *Community* local (no requeridos en producción Enterprise).

---

## 🛠️ Requerimientos e Instalación Rápida

### Requerimientos
*   Odoo 19 (Community o Enterprise).
*   PostgreSQL 15+.
*   Librerías Python en el entorno virtual (`pip install pandas openpyxl xlsxwriter xlrd`).

### Instalación Rápida (Entorno Local / Community)
1.  Clona el repositorio en tu servidor.
2.  Agrega la ruta de `custom_addons` al parámetro `addons_path` de tu archivo `odoo.conf`.
3.  Inicia Odoo, activa el **Modo Desarrollador**, ve a Aplicaciones y haz clic en **Actualizar lista de aplicaciones**.
4.  Instala el módulo de localización argentina (`l10n_ar`) y configura el plan contable para Responsable Inscripto (`ar_ri`).
5.  Busca e instala el módulo **`carpenter_invoicing`**.

### ⚠️ Importante para Despliegues en Odoo Enterprise
Si vas a desplegar en **Odoo 19 Enterprise (producción o staging)**, por favor consulta la sección **3. Directrices de Despliegue en Odoo 19 Enterprise** del archivo [documentacion_tecnica.md](file:///c:/Users/Usuario/Desktop/Odoo%2019%20Fazio/documentacion_tecnica.md) para evitar la instalación de módulos innecesarios de la OCA y garantizar la compatibilidad total con la factura electrónica AFIP (`l10n_ar_edi`).

---
*Desarrollado con excelencia por Antigravity.*
