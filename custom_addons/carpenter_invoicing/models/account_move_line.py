# -*- coding: utf-8 -*-
from odoo import models, api

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def action_apply_to_invoice(self):
        """ Applie this credit line to the currently opened invoice in the context """
        self.ensure_one()
        invoice_id = self.env.context.get('active_id')
        if not invoice_id:
            return
            
        invoice = self.env['account.move'].browse(invoice_id)
        if not invoice or invoice.state != 'posted':
            return
            
        # Find the open receivable/payable line of the invoice
        receivable_lines = invoice.line_ids.filtered(
            lambda l: l.account_id.account_type in ('asset_receivable', 'liability_payable') and not l.reconciled
        )
        
        if receivable_lines:
            # Reconcile the invoice line with this parent's credit line
            (receivable_lines[0] | self).reconcile()
