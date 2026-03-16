# Proyecto Odoo 19 - Gestión de Carpinteros (Fazio)

Este repositorio contiene la configuración y el desarrollo a medida para Odoo 19 Community, enfocado en la resolución del flujo de pagos cruzados entre contactos Padre (Carpinteros) e Hijos (Clientes Finales).

## Estructura del Proyecto

*   **custom_addons/carpenter_invoicing**: Módulo principal con la lógica de independencia fiscal y conciliación de créditos.
*   **custom_addons/account-financial-reporting**: Reportes contables de la OCA (v19).
*   **manual_uso_carpinteros.md**: Guía paso a paso para el usuario final.
*   **documentacion_tecnica.md**: Detalles de arquitectura y guía para migración a Enterprise.

## Requerimientos
*   Odoo 19 Community.
*   PostgreSQL.
*   Dependencias de Python listadas en los módulos OCA (pandas, openpyxl).

## Instalación rápida
1. Clonar el repositorio.
2. Configurar el `odoo.conf` apuntando a las carpetas en `custom_addons`.
3. Instalar el módulo `carpenter_invoicing`.

Hecho con Antigravity 🚀
