import frappe

def after_install():
    # Create default Whitelabel Setting if it doesn't exist
    if not frappe.db.exists("Whitelabel Setting", "Whitelabel Setting"):
        doc = frappe.get_doc({
            "doctype": "Whitelabel Setting",
            "application_logo": "/assets/whitelabel/images/whitelabel_logo.jpg",
            "custom_navbar_title": "ZaynERP",
            "disable_new_update_popup": 1,
            "disable_standard_footer": 1
        })
        doc.insert(ignore_permissions=True)