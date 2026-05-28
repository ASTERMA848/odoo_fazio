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
    
    # 1. Buscar o crear el idioma es_AR
    lang_code = 'es_AR'
    lang = env['res.lang'].with_context(active_test=False).search([('code', '=', lang_code)], limit=1)
    
    if not lang:
        print(f"Creating language {lang_code}...")
        lang = env['res.lang']._create_lang(lang_code, 'Español (AR)')
    else:
        print(f"Language {lang_code} found. Activating...")
        if not lang.active:
            lang.write({'active': True})
            
    # 2. Cargar traducciones para los módulos instalados
    print("Loading translations for installed modules... This might take a few seconds.")
    installed_modules = env['ir.module.module'].search([('state', '=', 'installed')])
    installed_modules._update_translations([lang_code])
    
    # 3. Establecer es_AR como idioma por defecto para nuevos contactos
    print("Setting es_AR as default language for partners...")
    env['ir.default'].set('res.partner', 'lang', lang_code)
    
    # 4. Cambiar idioma del usuario administrador
    admin_user = env.ref('base.user_admin')
    if admin_user:
        print(f"Updating administrator's language to {lang_code}...")
        admin_user.write({'lang': lang_code})
        # También actualizar el partner del administrador
        if admin_user.partner_id:
            admin_user.partner_id.write({'lang': lang_code})
            
    env.flush_all()
    cr.commit()
    print("Spanish language installed and configured successfully!")
