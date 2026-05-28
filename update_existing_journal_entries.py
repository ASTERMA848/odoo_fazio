import sys
import os
sys.path.append(os.path.abspath('odoo'))
import odoo
import odoo.tools
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', 'odoo.conf', '-d', 'odoo19_fazio'])
registry = Registry('odoo19_fazio')

with registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    
    # Encontrar todos los partners que tengan un padre centralizador (Carpintero)
    # y por ende su commercial_partner_id sea diferente a ellos mismos.
    child_partners = env['res.partner'].search([
        ('parent_id', '!=', False),
        ('parent_id.is_carpenter', '=', True)
    ])
    
    print(f"Child partners found: {child_partners.mapped('name')}")
    
    for child in child_partners:
        new_commercial = child.commercial_partner_id
        print(f"Updating records for child: {child.name} -> new commercial partner: {new_commercial.name}")
        
        # 1. Actualizar las facturas (account.move)
        moves = env['account.move'].search([('partner_id', '=', child.id)])
        if moves:
            print(f"  Found {len(moves)} invoices to update commercial_partner_id...")
            moves.write({'commercial_partner_id': new_commercial.id})
            
        # 2. Actualizar los apuntes contables por cobrar/pagar (account.move.line)
        move_lines = env['account.move.line'].search([
            ('partner_id', '=', child.id),
            ('account_id.account_type', 'in', ('asset_receivable', 'liability_payable'))
        ])
        if move_lines:
            print(f"  Found {len(move_lines)} receivable/payable lines to update partner_id...")
            move_lines.write({'partner_id': new_commercial.id})
            
    env.flush_all()
    cr.commit()
    print("Alignment of existing accounting entries completed successfully.")
