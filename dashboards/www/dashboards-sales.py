no_cache = 1

def get_context(context):
    import frappe
    # Redirect guests to login
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/dashboards-sales"
        raise frappe.Redirect
    # Inject CSRF token so the page can use it
    context.csrf_token = frappe.sessions.get_csrf_token()
    context.no_cache = 1
