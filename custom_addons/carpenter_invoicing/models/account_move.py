# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.fields import Domain

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

    is_paid_with_parent_credit = fields.Boolean(
        string="Pago Centralizado",
        store=True,
        default=False,
        readonly=True,
        help="Indica si esta factura fue saldada utilizando el saldo a favor de su contacto Padre (Carpintero)."
    )

    @api.depends('parent_partner_id', 'state', 'payment_state', 'partner_id')
    def _compute_parent_credit_line_ids(self):
        """
        Método computado defensivo que calcula las líneas de créditos pendientes del contacto Carpintero (Padre).
        Filtra únicamente apuntes contables asentados (state = posted), no conciliados (reconciled = False),
        con saldo pendiente real (balance != 0.0), y que pertenezcan al tipo 'receivable' o 'payable'.
        """
        for move in self:
            parent = move.partner_id.parent_id if move.partner_id and move.partner_id.parent_id.is_carpenter else move.parent_partner_id
            # Validación previa: solo facturas publicadas, impagas o parcialmente pagas, y que tengan un Carpintero asociado.
            if move.state == 'posted' and move.payment_state in ('not_paid', 'partial') and parent:
                # El dominio busca en las líneas de asiento (account.move.line):
                domain = [
                    ('partner_id', '=', parent.id),
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

    @api.depends('parent_partner_id', 'partner_id')
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
            parent = move.partner_id.parent_id if move.partner_id and move.partner_id.parent_id.is_carpenter else move.parent_partner_id
            # 2. Validación defensiva rápida: si no tiene Padre o no es factura válida para conciliar, ignoramos.
            if move.state not in {'draft', 'posted'} \
                    or move.payment_state not in ('not_paid', 'partial') \
                    or not move.is_invoice(include_receipts=True) \
                    or not parent:
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
                ('partner_id', '=', parent.id),
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
                    'journal_name': f"{line.ref or line.move_id.name} (Crédito de {parent.name})",
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

    def _get_l10n_latam_documents_domain(self):
        """
        [SOBREESCRITURA DE MÉTODO DE LOCALIZACIÓN ARGENTINA]
        Corrige la selección de letras de documentos (A, B, C, etc.) permitidas
        para la factura.
        Si la factura tiene un Carpintero como Padre, Odoo nativo usaría la responsabilidad
        del Padre (Consumidor Final -> Letra B) debido a commercial_partner_id.
        Forzamos a evaluar la responsabilidad real del contacto Hijo (ej: Responsable Inscripto -> Letra A)
        completamente en su lugar al reconstruir el dominio.
        """
        self.ensure_one()
        if self.company_id.account_fiscal_country_id.code == "AR" \
                and self.partner_id.parent_id \
                and self.partner_id.parent_id.is_carpenter:
            
            # Reconstruimos el dominio de forma exacta al módulo l10n_ar, pero usando
            # el partner_id real (el contacto hijo) en lugar de commercial_partner_id.
            
            # 1. Obtener los tipos internos base de l10n_latam_invoice_document
            internal_types = []
            invoice_type = self.move_type
            if invoice_type in ['out_refund', 'in_refund']:
                internal_types = ['credit_note']
            elif invoice_type in ['out_invoice', 'in_invoice']:
                internal_types = ['invoice', 'debit_note']
            if self.debit_origin_id:
                internal_types = ['debit_note']
            internal_types += ['all']
            
            domain = Domain([
                ('internal_type', 'in', internal_types),
                ('country_id', '=', self.company_id.account_fiscal_country_id.id)
            ])
            
            # 2. Calcular las letras permitidas usando el partner_id real de la factura
            letters = self.journal_id._get_journal_letter(counterpart_partner=self.partner_id)
            domain &= Domain('l10n_ar_letter', '=', False) | Domain('l10n_ar_letter', 'in', letters)
            
            # 3. Aplicar códigos y diarios específicos
            domain &= Domain(self.journal_id._get_journal_codes_domain())
            if self.move_type in ['out_refund', 'in_refund']:
                domain = Domain('code', 'in', self._get_l10n_ar_codes_used_for_inv_and_ref()) | domain
                
            return domain
            
        return super()._get_l10n_latam_documents_domain()

    def _set_afip_responsibility(self):
        """
        [SOBREESCRITURA DE MÉTODO DE LOCALIZACIÓN ARGENTINA]
        Guarda la responsabilidad ante AFIP del cliente al validar la factura.
        Si la factura tiene un Carpintero como Padre, forzamos a guardar la responsabilidad
        del Hijo (ej: Responsable Inscripto) en lugar de la del Padre (Consumidor Final).
        """
        super()._set_afip_responsibility()
        for rec in self:
            if rec.company_id.account_fiscal_country_id.code == "AR" \
                    and rec.partner_id.parent_id \
                    and rec.partner_id.parent_id.is_carpenter:
                rec.l10n_ar_afip_responsibility_type_id = rec.partner_id.l10n_ar_afip_responsibility_type_id.id

    @api.depends('line_ids.matched_debit_ids', 'line_ids.matched_credit_ids', 'matched_payment_ids')
    def _compute_reconciled_payment_ids(self):
        """
        [SOBREESCRITURA DE MÉTODO NATIVO DE ODOO]
        Este método calcula qué pagos están vinculados a la factura para mostrar el botón inteligente
        de 'Pagos' (smart button en la cabecera).
        
        Dado que el pago del Carpintero no se concilia directamente contra la factura de la Constructora,
        sino que pasa de forma transparente por un Asiento de Compensación/Traspaso, la consulta SQL estándar
        de Odoo no detecta el pago.
        
        Sobrescribimos este método para buscar de forma recursiva y segura el pago original del Carpintero
        siguiendo el flujo del traspaso, inyectándolo en reconciled_payment_ids.
        """
        super()._compute_reconciled_payment_ids()
        for move in self:
            if move.is_paid_with_parent_credit:
                # Obtenemos las líneas por cobrar/pagar de esta factura
                receivable_lines = move.line_ids.filtered(
                    lambda l: l.account_id.account_type in ('asset_receivable', 'liability_payable')
                )
                
                # Obtenemos las líneas con las que está conciliada (apuntando al Asiento de Compensación)
                directly_reconciled_lines = (
                    receivable_lines.matched_debit_ids.debit_move_id |
                    receivable_lines.matched_credit_ids.credit_move_id
                )
                
                # Filtramos para encontrar los asientos de compensación
                transfer_moves = directly_reconciled_lines.mapped('move_id').filtered(
                    lambda m: m.ref and "Compensación:" in m.ref
                )
                
                if transfer_moves:
                    # Obtenemos las otras líneas de esos asientos de compensación (la parte que asume el Padre)
                    transfer_parent_lines = transfer_moves.line_ids.filtered(
                        lambda l: l.partner_id != move.partner_id
                    )
                    
                    # Obtenemos las líneas con las que están conciliadas esas líneas del Padre (apuntando al pago original)
                    parent_reconciled_lines = (
                        transfer_parent_lines.matched_debit_ids.debit_move_id |
                        transfer_parent_lines.matched_credit_ids.credit_move_id
                    )
                    
                    # Buscamos el pago de Odoo asociado al asiento del pago original
                    parent_payments = self.env['account.payment'].search([
                        ('move_id', 'in', parent_reconciled_lines.mapped('move_id').ids)
                    ])
                    
                    if parent_payments:
                        # Unimos el pago al conjunto nativo para activar el botón inteligente 'Pagos'
                        move.reconciled_payment_ids = move.reconciled_payment_ids | parent_payments

    def js_assign_outstanding_line(self, line_id):
        """
        [SOBREESCRITURA DE MÉTODO NATIVO DE ODOO]
        Intercepta cuando el usuario hace clic en 'Añadir' en el widget de saldos pendientes
        para asociar un pago del Carpintero (Padre) a la factura de la Empresa Hija.
        
        Si los contactos son distintos pero tienen relación Carpintero-Hijo, en lugar de una
        conciliación directa entre distintos entes (que desajusta los saldos del Libro Mayor de cada uno),
        creamos un Asiento Diario de Traspaso (Compensación de Deuda) 100% estándar y transparente.
        
        Esto logra:
        1. Que la factura de la Empresa Hija quede marcada como PAGADA al conciliarse contra el traspaso.
        2. Que el saldo del Carpintero se descuente formalmente en su Libro Mayor (al conciliarse contra el traspaso).
        3. Que si la Empresa Hija paga con sus propios medios directos, todo quede en su propia cuenta y nombre.
        """
        self.ensure_one()
        payment_line = self.env['account.move.line'].browse(line_id)
        
        # Validamos si es una conciliación cruzada entre Padre (Carpintero) e Hijo
        if self.partner_id != payment_line.partner_id \
                and payment_line.partner_id.is_carpenter \
                and self.partner_id.parent_id == payment_line.partner_id:
            
            # Buscamos la línea contable por cobrar/pagar pendiente en esta factura
            invoice_receivable_line = self.line_ids.filtered(
                lambda l: l.account_id.account_type in ('asset_receivable', 'liability_payable') and not l.reconciled
            )
            if not invoice_receivable_line:
                return super().js_assign_outstanding_line(line_id)
            
            # El monto a compensar es el mínimo entre el saldo residual de la factura y el pago del Carpintero
            amount_to_transfer = min(abs(invoice_receivable_line.amount_residual), abs(payment_line.amount_residual))
            
            # Buscamos el diario de operaciones diversas (tipo 'general') para registrar la compensación
            journal = self.env['account.journal'].search([
                ('type', '=', 'general'),
                ('company_id', '=', self.company_id.id)
            ], limit=1)
            
            if not journal:
                raise UserError(_("No se encontró un diario de tipo 'General' para realizar la compensación de deudas."))
            
            # Creamos el Asiento Contable de Compensación / Traspaso
            move_vals = {
                'move_type': 'entry',
                'journal_id': journal.id,
                'date': self.invoice_date or fields.Date.context_today(self),
                'ref': f"Compensación: {self.name} - {payment_line.move_id.name}",
                'line_ids': [
                    # 1. Crédito a la Empresa Hija (cancela/disminuye su deuda en la factura)
                    (0, 0, {
                        'name': f"Compensación de deuda por pago de {payment_line.partner_id.name} en {self.name}",
                        'partner_id': self.partner_id.id,
                        'account_id': invoice_receivable_line.account_id.id,
                        'credit': amount_to_transfer if self.is_inbound() else 0.0,
                        'debit': 0.0 if self.is_inbound() else amount_to_transfer,
                    }),
                    # 2. Débito al Carpintero (asume la deuda del hijo para consumar su saldo a favor)
                    (0, 0, {
                        'name': f"Asunción de deuda de {self.partner_id.name} en {self.name}",
                        'partner_id': payment_line.partner_id.id,
                        'account_id': invoice_receivable_line.account_id.id,
                        'credit': 0.0 if self.is_inbound() else amount_to_transfer,
                        'debit': amount_to_transfer if self.is_inbound() else 0.0,
                    })
                ]
            }
            
            # Publicamos el asiento
            transfer_move = self.env['account.move'].create(move_vals)
            transfer_move.action_post()
            
            # Marcamos la factura indicando que fue compensada con el saldo del Carpintero
            self.is_paid_with_parent_credit = True
            
            # Conciliamos la línea de la factura de la constructora con la línea de crédito del traspaso
            constructora_transfer_line = transfer_move.line_ids.filtered(lambda l: l.partner_id == self.partner_id)
            (invoice_receivable_line | constructora_transfer_line).reconcile()
            
            # Conciliamos la línea de pago original del Carpintero con la línea de débito del traspaso
            carpenter_transfer_line = transfer_move.line_ids.filtered(lambda l: l.partner_id == payment_line.partner_id)
            (payment_line | carpenter_transfer_line).reconcile()
            
            return True
            
        return super().js_assign_outstanding_line(line_id)

    def js_remove_outstanding_partial(self, partial_id):
        """
        [SOBREESCRITURA DE MÉTODO NATIVO DE ODOO]
        Si el usuario rompe/elimina la conciliación en el widget de pagos (unreconcile),
        comprobamos si todavía queda alguna compensación de Carpintero vinculada a la factura.
        Si ya no queda ninguna, limpiamos la bandera 'is_paid_with_parent_credit'.
        """
        res = super().js_remove_outstanding_partial(partial_id)
        for rec in self:
            receivable_lines = rec.line_ids.filtered(
                lambda l: l.account_id.account_type in ('asset_receivable', 'liability_payable')
            )
            reconciled_lines = (
                receivable_lines.matched_debit_ids.debit_move_id |
                receivable_lines.matched_credit_ids.credit_move_id
            )
            # Buscamos si existe alguna línea de asiento de compensación aún activa
            parent_transfers = reconciled_lines.filtered(
                lambda l: l.move_id.ref and "Compensación:" in l.move_id.ref
            )
            if not parent_transfers:
                rec.is_paid_with_parent_credit = False
        return res





