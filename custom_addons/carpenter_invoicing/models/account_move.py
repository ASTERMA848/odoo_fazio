# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    """
    Este modelo extiende a 'account.move' (Facturas y Asientos Diarios) de Odoo
    para añadir la lógica contable y de relación requerida para el flujo
    de conciliación de créditos cruzados entre contactos Padre (Carpinteros) e Hijos (Clientes Finales).
    """
    _inherit = 'account.move'

    # Campo Relacionado (Many2one) almacenado en BD que apunta al contacto Padre del Cliente.
    # related='partner_id.parent_id' permite mapear en tiempo de guardado el Carpintero (Padre) del Cliente Final.
    # store=True es fundamental para optimizar búsquedas e indexación en base de datos.
    parent_partner_id = fields.Many2one(
        'res.partner',
        related='partner_id.parent_id',
        string="Parent Partner (Carpenter)",
        store=True,
        help="Muestra el contacto Padre (Carpintero) asociado al cliente de esta factura, permitiendo la búsqueda de sus saldos contables a favor."
    )

    # Campo Relación de Muchos a Muchos (Many2many) computado que busca las líneas contables disponibles.
    # Es de tipo 'account.move.line' y sirve para auditoría o visualización interna.
    parent_credit_line_ids = fields.Many2many(
        comodel_name='account.move.line',
        compute='_compute_parent_credit_line_ids',
        string="Available Parent Credits",
        help="Líneas contables no conciliadas de tipo cobro/pago pertenecientes al contacto Padre (Carpintero)."
    )

    @api.depends('parent_partner_id', 'state', 'payment_state', 'partner_id')
    def _compute_parent_credit_line_ids(self):
        """
        Método computado defensivo que calcula las líneas de créditos pendientes del contacto Carpintero (Padre).
        Filtra únicamente apuntes contables asentados (state = posted), no conciliados (reconciled = False),
        con saldo pendiente real (balance != 0.0), y que pertenezcan al tipo 'receivable' o 'payable'.
        """
        for move in self:
            # Validación previa: solo facturas publicadas, impagas o parcialmente pagas, y que tengan un Carpintero asociado.
            if move.state == 'posted' and move.payment_state in ('not_paid', 'partial') and move.parent_partner_id:
                # El dominio busca en las líneas de asiento (account.move.line):
                domain = [
                    ('partner_id', '=', move.parent_partner_id.id),
                    # account_type en 'asset_receivable' (por cobrar) o 'liability_payable' (por pagar) según Odoo 16/17/18/19.
                    ('account_id.account_type', 'in', ('asset_receivable', 'liability_payable')),
                    ('reconciled', '=', False),
                    ('move_id.state', '=', 'posted'),
                    ('balance', '!=', 0.0),
                ]
                
                lines = self.env['account.move.line'].search(domain)
                valid_lines = self.env['account.move.line']
                
                # Para facturas de clientes (inbound), necesitamos saldos con signo negativo (Créditos / Balance < 0).
                # Para facturas de proveedores (outbound), necesitamos saldos con signo positivo (Débitos / Balance > 0).
                if move.is_inbound():
                    valid_lines = lines.filtered(lambda l: l.balance < 0.0)
                elif move.is_outbound():
                    valid_lines = lines.filtered(lambda l: l.balance > 0.0)
                
                move.parent_credit_line_ids = valid_lines
            else:
                move.parent_credit_line_ids = False

    @api.depends('parent_partner_id')
    def _compute_payments_widget_to_reconcile_info(self):
        """
        [SOBREESCRITURA DE MÉTODO NATIVO DE ODOO]
        Este método intercepta el cálculo estándar del widget de Odoo 'Saldos Pendientes'
        (invoice_outstanding_credits_debits_widget) que se dibuja abajo a la derecha de la factura.
        
        Nativamente, Odoo solo busca pagos del mismo 'partner_id'. Nosotros hacemos un override para:
        1. Dejar que Odoo calcule primero todos los pagos nativos del Cliente usando super().
        2. Si la factura tiene un contacto Padre (Carpintero), buscar los saldos a favor de este Carpintero.
        3. Inyectar de manera segura los saldos a favor del Carpintero en el widget nativo con un sufijo aclaratorio,
           permitiendo que el botón oficial 'Añadir' (Add) de Odoo concilie cruzado de forma 100% nativa.
        """
        # 1. Ejecutar primero la lógica estándar de Odoo (Respeta el MRO contable y previene fallos)
        super()._compute_payments_widget_to_reconcile_info()
        
        for move in self:
            # 2. Validación defensiva rápida: si no tiene Padre o no es factura válida para conciliar, ignoramos.
            if move.state not in {'draft', 'posted'} \
                    or move.payment_state not in ('not_paid', 'partial') \
                    or not move.is_invoice(include_receipts=True) \
                    or not move.parent_partner_id:
                continue

            # Obtenemos las cuentas contables de cobro (receivable/payable) asociadas a esta factura.
            pay_term_lines = move.line_ids.filtered(
                lambda line: line.account_id.account_type in ('asset_receivable', 'liability_payable')
            )
            if not pay_term_lines:
                continue

            # 3. Consultamos los créditos disponibles del Carpintero (Padre) en esas mismas cuentas contables
            domain = [
                ('account_id', 'in', pay_term_lines.account_id.ids),
                ('parent_state', '=', 'posted'),
                ('partner_id', '=', move.parent_partner_id.id),
                ('reconciled', '=', False),
                ('balance', '<' if move.is_inbound() else '>', 0.0),
                '|', ('amount_residual', '!=', 0.0), ('amount_residual_currency', '!=', 0.0),
            ]

            parent_lines = self.env['account.move.line'].search(domain)
            if not parent_lines:
                continue

            # 4. Cargamos el widget nativo existente o lo inicializamos si estaba vacío
            widget = move.invoice_outstanding_credits_debits_widget or {
                'outstanding': True,
                'content': [],
                'move_id': move.id,
                'title': _('Outstanding credits') if move.is_inbound() else _('Outstanding debits')
            }

            # Conjunto de IDs ya cargados para evitar duplicidades accidentales en el widget
            existing_ids = {item['id'] for item in widget.get('content', [])}

            for line in parent_lines:
                if line.id in existing_ids:
                    continue

                # 5. Soporte Multimoneda: Convertimos el saldo residual del Carpintero a la moneda de la factura
                if line.currency_id == move.currency_id:
                    amount = abs(line.amount_residual_currency)
                else:
                    amount = line.company_currency_id._convert(
                        abs(line.amount_residual),
                        move.currency_id,
                        move.company_id,
                        line.date,
                    )

                if move.currency_id.is_zero(amount):
                    continue

                # 6. Añadimos el crédito al contenido del widget nativo de Odoo
                # Agregamos el texto '(Crédito de Carpintero)' para dar total claridad al usuario al presionar 'Añadir'
                widget['content'].append({
                    'journal_name': f"{line.ref or line.move_id.name} (Crédito de {move.parent_partner_id.name})",
                    'amount': amount,
                    'currency_id': move.currency_id.id,
                    'id': line.id,
                    'move_id': line.move_id.id,
                    'date': fields.Date.to_string(line.date),
                    'account_payment_id': line.payment_id.id,
                    'move_ref': line.ref or "",
                })

            # 7. Asignamos el widget modificado y marcamos que la factura sí posee créditos pendientes asociados
            if widget['content']:
                move.invoice_outstanding_credits_debits_widget = widget
                move.invoice_has_outstanding = True




