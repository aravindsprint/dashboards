no_cache = 1

def get_context(context):
    # Redirect to login if not authenticated
    import frappe
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/dashboards"
        raise frappe.Redirect
    context.no_cache = 1
