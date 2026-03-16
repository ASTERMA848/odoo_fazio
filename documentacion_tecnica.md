# Documento Técnico: Personalización de Carpinteros y Guía de Migración Enterprise

**Fecha:** 2026-03-16
**Estado:** Implementado en Odoo 19 Community
**Módulo Personalizado:** `carpenter_invoicing`

---

## 1. Arquitectura de Módulos Instalados

Para lograr la funcionalidad contable en la versión Community, se instalaron y configuraron los siguientes repositorios de la OCA (Odoo Community Association):

### Repositorios OCA (Base Contable)
1.  **account-financial-reporting**: Provee el Libro Mayor, Balance de Comprobación y Reportes de Antigüedad de Deuda (Aged Partner Balance).
    *   *Nota Técnica:* Se aplicó un hotfix en `res_config_settings_views.xml` para evitar un error 500 en el frontend relacionado con intervalos de fechas.
2.  **server-tools**: Dependencia técnica (módulo `date_range`) para la gestión de periodos fiscales en reportes.
3.  **reporting-engine**: Motor base para generación de informes XLSX y PDF.
4.  **server-ux**: Mejoras de usabilidad requeridas por los widgets de reportes.

### Módulo Custom: `carpenter_invoicing`
Este módulo es el núcleo de la lógica de negocio solicitada. Interviene tres áreas críticas:
*   **res.partner**: Desvincula la herencia comercial mediante `_commercial_fields()` para permitir CUITs independientes en contactos hijos.
*   **account.move**: Agrega un campo Many2many computado (`parent_credit_line_ids`) que escanea en tiempo real los apuntes contables (de tipo activo/pasivo) del partner Padre.
*   **account.move.line**: Implementa el método `action_apply_to_invoice` que ejecuta la conciliación física entre la línea de la factura del hijo y la línea de pago del padre usando el método nativo `.reconcile()`.

---

## 2. Consideraciones para el Paso a Enterprise

Al migrar a **Odoo Enterprise**, el desarrollador debe tener en cuenta que Enterprise ya posee un motor de reportes nativo diferente al de la OCA.

### Conflictos de Módulos (OCA vs Enterprise)
> [!WARNING]
> **No instalar `account_financial_report` (OCA) en Enterprise sin revisión previa.**
> Odoo Enterprise ya incluye los informes financieros dinámicos. Si se desea mantener los de la OCA, se deben revisar posibles conflictos de menú. Se recomienda migrar los datos al reporte nativo de Enterprise.

### Adaptación de `carpenter_invoicing`
El módulo personalizado es compatible en un 95%, pero el desarrollador deberá:
1.  **Revisión de Vistas:** Enterprise utiliza variaciones en el formulario de `account.move`. Verificar que el XPath del tab "Créditos del Carpintero" no interfiera con los reportes de análisis visuales de Enterprise.
2.  **Reportes nativos de Enterprise:** Si se desea filtrar el Libro Mayor de Enterprise por "Hijo" pero ver resultados pagados por el "Padre", el desarrollador deberá revisar si los "Tags" analíticos de Enterprise proporcionan una solución más limpia sin requerir la conciliación cruzada (aunque la conciliación actual es la más sólida contablemente).
3.  **L10N Argentina:** En Enterprise, el módulo `l10n_ar` suele estar más integrado con el Webservice de AFIP. Nuestra modificación en `res.partner` para el CUIT independiente es fundamental para que la factura electrónica de Enterprise salga con los datos del Cliente Final y no del Carpintero.

---

## 3. Guía de Despliegue (Deploy Checklist)

Si vas a mover estos cambios a producción o a un entorno Enterprise:

- [ ] **Python context:** Asegurar que `pandas` y `openpyxl` estén instalados (requeridos por el motor de la OCA para reportes Excel).
- [ ] **Sequence Check:** Antes de subir el módulo `carpenter_invoicing`, instalar primero las dependencias de la OCA en el orden: `server-tools` -> `reporting-engine` -> `account-financial-reporting`.
- [ ] **Fiscal Overrides:** Verificar en el entorno Enterprise que el campo `commercial_partner_id` no esté siendo forzado por otros módulos de localización (esto podría romper nuestra independencia de CUIT si no se maneja correctamente).
- [ ] **Display Name:** El override de `_compute_display_name` en `res_partner.py` es intencional para evitar el formato "Padre, Hijo" en la impresión oficial de facturas. Mantenerlo.

---

## 4. Estructura de Archivos del Desarrollador
- `models/res_partner.py`: Gestión de independencia de datos fiscales.
- `models/account_move.py`: Lógica de detección de créditos de terceros (padres).
- `models/account_move_line.py`: Lógica de ejecución de conciliación cruzada.
- `views/account_move_views.xml`: Inyección de interfaz en el widget de facturación.
