# apps/dashboards/dashboards/www/whatsapp-config.py
no_cache = 1

def get_context(context):
    import frappe
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/whatsapp-config"
        raise frappe.Redirect
    context.csrf_token = frappe.sessions.get_csrf_token()
    context.no_cache = 1
