from . import __version__ as app_version

app_name        = "dashboards"
app_title       = "Dashboards"
app_publisher   = "Pranera"
app_description = "Pranera ERP Dashboards"
app_email       = "admin@pranera.in"
app_license     = "MIT"
app_version     = "1.0.0"

setup_wizard_not_required = 1

add_to_apps_screen = [
    {
        "name": "dashboards",
        "logo": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='22' fill='%231565C0'/%3E%3Crect x='11' y='55' width='22' height='32' rx='4' fill='white'/%3E%3Crect x='39' y='33' width='22' height='54' rx='4' fill='white'/%3E%3Crect x='67' y='16' width='22' height='71' rx='4' fill='white'/%3E%3Cpolyline points='13,47 50,27 87,13' fill='none' stroke='white' stroke-width='4' stroke-linecap='round' stroke-linejoin='round' opacity='0.65'/%3E%3C/svg%3E",
        "title": "Dashboards",
        "route": "/dashboards",
    }
]

website_route_rules = [
    {"from_route": "/dashboards/<path:app_path>", "to_route": "dashboards"},
]

fixtures = [
    {"doctype": "Page",      "filters": [["module", "in", ["Dashboard Module"]]]},
    {"doctype": "Workspace", "filters": [["module", "in", ["Dashboard Module"]]]},
]
