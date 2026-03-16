# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = 'account.move'

    parent_partner_id = fields.Many2one(
        'res.partner',
        related='partner_id.parent_id',
        string="Parent Partner (Carpenter)",
        store=True
    )

    parent_credit_line_ids = fields.Many2many(
        comodel_name='account.move.line',
        compute='_compute_parent_credit_line_ids',
        string="Available Parent Credits"
    )

    @api.depends('parent_partner_id', 'state', 'payment_state', 'partner_id')
    def _compute_parent_credit_line_ids(self):
        for move in self:
            if move.state == 'posted' and move.payment_state in ('not_paid', 'partial') and move.parent_partner_id:
                # In Odoo 16+, Account Types have changed
                # Instead of user_type_id, we use account_type
                domain = [
                    ('partner_id', '=', move.parent_partner_id.id),
                    ('account_id.account_type', 'in', ('asset_receivable', 'liability_payable')),
                    ('reconciled', '=', False),
                    ('move_id.state', '=', 'posted'),
                    ('balance', '!=', 0.0),
                ]
                
                lines = self.env['account.move.line'].search(domain)
                
                # Filter by those that can actually offset this move
                valid_lines = self.env['account.move.line']
                
                # For a customer invoice (out_invoice), we need negative balance (credit)
                # For supplier bill (in_invoice), we need positive balance (debit)
                if move.is_inbound():
                    valid_lines = lines.filtered(lambda l: l.balance < 0.0)
                elif move.is_outbound():
                    valid_lines = lines.filtered(lambda l: l.balance > 0.0)
                
                move.parent_credit_line_ids = valid_lines
            else:
                move.parent_credit_line_ids = False


