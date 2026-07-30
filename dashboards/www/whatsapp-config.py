# dashboards/www/whatsapp-config.py

import frappe

no_cache = 1

def get_context(context):
    # Restrict access to System Manager role only
    if frappe.session.user == "Guest":
        frappe.throw("Please login to access this page.", frappe.PermissionError)
    
    if "System Manager" not in frappe.get_roles(frappe.session.user):
        frappe.throw("You do not have permission to access this page. System Manager role required.", frappe.PermissionError)
    
    context.no_cache = 1
    return context
