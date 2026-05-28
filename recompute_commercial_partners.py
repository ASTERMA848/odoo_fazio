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
    partners = env['res.partner'].search([])
    print(f"Total partners to recompute: {len(partners)}")
    for partner in partners:
        partner._compute_commercial_partner()
    env.flush_all()
    cr.commit()
    print("Recomputation of commercial_partner_id completed successfully.")
