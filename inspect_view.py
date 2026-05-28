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
    move_obj = env['account.move']
    
    # In Odoo 16/17/18/19, get_view is the standard method
    try:
        view_info = move_obj.get_view(view_id=None, view_type='form')
        arch = view_info['arch']
        print("Successfully retrieved view via get_view!")
    except Exception as e:
        print(f"get_view failed: {e}")
        try:
            view_info = move_obj.fields_view_get(view_id=None, view_type='form')
            arch = view_info['arch']
            print("Successfully retrieved view via fields_view_get!")
        except Exception as e2:
            print(f"fields_view_get failed: {e2}")
            arch = ""

    if arch:
        # Check if button_box is present in the architecture
        import xml.etree.ElementTree as ET
        root = ET.fromstring(arch)
        button_box = root.find(".//div[@name='button_box']")
        if button_box is not None:
            print("\nFound button_box in view arch!")
            buttons = button_box.findall(".//button")
            print(f"Total buttons in button_box: {len(buttons)}")
            for btn in buttons:
                name = btn.attrib.get('name')
                string = btn.attrib.get('string')
                invisible = btn.attrib.get('invisible')
                groups = btn.attrib.get('groups')
                print(f"  Button: name='{name}', string='{string}', invisible='{invisible}', groups='{groups}'")
                for child in btn:
                    print(f"    Child tag: {child.tag}, attrib: {child.attrib}")
        else:
            print("\nbutton_box NOT found in view arch!")
