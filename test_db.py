import psycopg2
import json

try:
    conn = psycopg2.connect(dbname="odoo19_fazio", user="odoo", password="odoo", host="localhost", port="5432")
    conn.autocommit = True
    cur = conn.cursor()
    
    # Get admin user ID
    cur.execute("SELECT id, login FROM res_users WHERE login IN ('admin', 'admin@example.com') ORDER BY id;")
    users = cur.fetchall()
    print("Users found:", users)
    if not users:
        print("No admin user found")
        exit(1)
    admin_id = users[0][0]
    
    # Get all groups
    cur.execute("SELECT id, name FROM res_groups;")
    all_groups = cur.fetchall()
    
    target_groups = []
    print("Matching groups for accounting / invoicing:")
    for gid, name_json in all_groups:
        # name_json is a dict
        name_str = name_json.get('en_US', '') if isinstance(name_json, dict) else str(name_json)
        lower_name = name_str.lower()
        if any(term in lower_name for term in ['accounting', 'invoice', 'billing', 'accountant', 'facturacion', 'contabilidad']):
            print(f"ID: {gid}, Name: {name_str}")
            target_groups.append(gid)
            
    # Assign these groups to the admin user
    for gid in target_groups:
        cur.execute("SELECT 1 FROM res_groups_users_rel WHERE uid=%s AND gid=%s", (admin_id, gid))
        if not cur.fetchone():
            cur.execute("INSERT INTO res_groups_users_rel (uid, gid) VALUES (%s, %s)", (admin_id, gid))
            print(f"Assigned group ID {gid} to admin user.")
        else:
            print(f"Group ID {gid} already assigned to admin user.")
            
    print("Finished enabling permissions successfully.")
    
    cur.close()
    conn.close()
except Exception as e:
    print("Error:", e)
