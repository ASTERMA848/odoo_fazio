# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_carpenter = fields.Boolean(
        string='Is Carpenter (Parent Account)',
        help='Check this box if this contact acts as a parent account holding credits for child contacts.'
    )

    @api.model
    def _commercial_fields(self):
        """
        Remove fiscal fields from the commercial fields list
        so they do not sync from parent (Carpenter) to child (Final Customer).
        """
        commercial_fields = super(ResPartner, self)._commercial_fields()
        fields_to_remove = [
            'vat',
            'l10n_ar_afip_responsibility_type_id',
            'l10n_latam_identification_type_id',
        ]
        for f in fields_to_remove:
            if f in commercial_fields:
                commercial_fields.remove(f)
        return commercial_fields

    @api.depends('is_company', 'name', 'parent_id.is_company', 'type', 'company_name', 'parent_id.is_carpenter')
    def _compute_display_name(self):
        """ Override to prevent 'Carpenter, Final Customer' format in invoices print/UI """
        super()._compute_display_name()
        for partner in self:
            if partner.parent_id and partner.parent_id.is_carpenter:
                partner.display_name = partner.name
