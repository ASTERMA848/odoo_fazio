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
    users = env['res.users'].search([])
    print("Database Users:")
    for user in users:
        print(f"ID: {user.id}, Name: {user.name}, Login: {user.login}, Active: {user.active}")
