from . import __version__ as app_version

app_name        = "dashboards"
app_title       = "Dashboards"
app_publisher   = "Pranera"
app_description = "Pranera ERP Dashboards"
app_email       = "admin@pranera.in"
app_license     = "MIT"
app_version     = "1.0.0"

add_to_apps_screen = [
    {
        "name": "dashboards",
        "logo": "/assets/dashboards/images/logo.svg",
        "title": "Dashboards",
        "route": "/dashboards",
        "has_permission": "dashboards.api.sales_api.check_app_permission",
    }
]

website_route_rules = [
    {"from_route": "/dashboards/<path:app_path>", "to_route": "dashboards"},
]

fixtures = [
    {"doctype": "Page",      "filters": [["module", "in", ["Dashboard Module"]]]},
    {"doctype": "Workspace", "filters": [["module", "in", ["Dashboard Module"]]]},
]
