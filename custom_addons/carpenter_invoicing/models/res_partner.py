# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResPartner(models.Model):
    """
    Este modelo extiende a 'res.partner' (Contactos/Terceros) de Odoo
    para proveer las bases de relación Padre e Hijo (Carpinteros y Clientes Finales),
    desacoplando sus campos fiscales e identidades fiscales nativas.
    """
    _inherit = 'res.partner'

    # Campo booleano de tilde manual para marcar si este contacto es un Centralizador de Pagos.
    is_carpenter = fields.Boolean(
        string='Centralizador de Pagos',
        help='Marque esta casilla si este contacto actúa como centralizador de pagos y créditos para sus contactos relacionados.'
    )

    @api.model
    def _commercial_fields(self):
        """
        [SOBREESCRITURA DE MÉTODO NATIVO DE ODOO]
        Determina qué campos son considerados 'comerciales' y por lo tanto
        se sincronizan y bloquean rígidamente desde el contacto Padre al Hijo.
        
        En Odoo estándar (y localización argentina), el CUIT y la Responsabilidad AFIP
        se copian y bloquean automáticamente en los subcontactos. Nosotros hacemos una
        exclusión de la lista nativa para permitir CUITs y Responsabilidades fiscales independientes.
        """
        # Obtenemos los campos comerciales estándar (incluye vat, l10n_ar_afip_responsibility_type_id, etc.)
        commercial_fields = super(ResPartner, self)._commercial_fields()
        
        # Campos fiscales específicos de AFIP/ARCA que deseamos desvincular
        fields_to_remove = [
            'vat',                                   # CUIT / DNI / Nro Identificación
            'l10n_ar_afip_responsibility_type_id',   # Responsabilidad ante el IVA (ex-AFIP / ARCA)
            'l10n_latam_identification_type_id',     # Tipo de Identificación (CUIT, DNI, etc.)
        ]
        
        # Removemos de forma segura de la lista de campos comerciales sincronizados
        for f in fields_to_remove:
            if f in commercial_fields:
                commercial_fields.remove(f)
                
        return commercial_fields

    @api.depends('is_company', 'name', 'parent_id.is_company', 'type', 'company_name', 'parent_id.is_carpenter')
    def _compute_display_name(self):
        """
        [SOBREESCRITURA DE MÉTODO NATIVO DE ODOO]
        Calcula el nombre visible del contacto en toda la plataforma (UIs, facturas, PDF).
        
        Nativamente, Odoo nombra a los subcontactos con el formato 'Compañía Padre, Subcontacto'.
        Si un cliente final ("Empresa 1") tiene como padre a "Carpintero", Odoo imprimiría "Carpintero, Empresa 1".
        Este override hace que si el padre es un Carpintero (is_carpenter = True), se imprima únicamente
        el nombre limpio de la empresa hija ("Empresa 1") en sus facturas y listados.
        """
        # 1. Ejecutar el cálculo nativo de Odoo primero
        super()._compute_display_name()
        
        # 2. Si tiene un Carpintero como padre, sobreescribir con su nombre limpio
        for partner in self:
            if partner.parent_id and partner.parent_id.is_carpenter:
                partner.display_name = partner.name

    # Campo monetario computado que suma todo lo facturado a los contactos relacionados (hijos) del Carpintero.
    total_invoiced_related = fields.Monetary(
        compute='_compute_total_invoiced_related',
        string="Facturado Relacionados",
        groups='account.group_account_invoice,account.group_account_readonly',
        help="Suma total facturada a los contactos relacionados (hijos) de este Carpintero."
    )

    def _compute_total_invoiced_related(self):
        """
        Calcula el total facturado (sin impuestos, igual que Odoo estándar)
        exclusivamente a los contactos relacionados (hijos) del partner actual.
        Esto alimenta nuestro nuevo botón inteligente.
        """
        if not self.ids:
            for partner in self:
                partner.total_invoiced_related = 0.0
            return
            
        all_partners_children = {}
        all_child_ids = []
        for partner in self:
            # Buscamos todos los hijos del partner actual (excluyéndose a sí mismo)
            children = self.with_context(active_test=False).search([('id', 'child_of', partner.id), ('id', '!=', partner.id)])
            all_partners_children[partner] = children.ids
            all_child_ids += children.ids
            
        if not all_child_ids:
            for partner in self:
                partner.total_invoiced_related = 0.0
            return
            
        # Consultamos el total facturado nativo (sin impuestos / subtotal) de todos los hijos en el reporte de facturas
        domain = [
            ('partner_id', 'in', all_child_ids),
            ('state', 'not in', ['draft', 'cancel']),
            ('move_type', 'in', ('out_invoice', 'out_refund')),
        ]
        price_totals = {
            p.id: price_subtotal_sum
            for p, price_subtotal_sum in self.env['account.invoice.report']._read_group(domain, ['partner_id'], ['price_subtotal:sum'])
        }
        for partner, child_ids in all_partners_children.items():
            partner.total_invoiced_related = sum(price_totals.get(cid, 0.0) for cid in child_ids)

    def action_view_related_partner_invoices(self):
        """
        Acción de clic para nuestro nuevo botón inteligente.
        Abre el listado de facturas emitidas a los contactos hijos/relacionados de este partner.
        """
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        children = self.with_context(active_test=False).search([('id', 'child_of', self.id), ('id', '!=', self.id)])
        action['domain'] = [
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('partner_id', 'in', children.ids)
        ]
        action['context'] = {
            'default_move_type': 'out_invoice',
            'move_type': 'out_invoice',
            'journal_type': 'sale',
            'search_default_unpaid': 1
        }
        if children:
            action['context']['default_partner_id'] = children[0].id
        return action

