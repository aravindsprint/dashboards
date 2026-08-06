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
        "route": "/dashboard-app",
        "has_permission": "dashboards.api.sales_api.check_app_permission",
    }
]

website_route_rules = [
    # New Vue SPA (frontend/, built into dashboards/public/dashboard_app) —
    # single shell page, client-side routed. This is the pranera_knit-style
    # app going forward.
    {"from_route": "/dashboard-app/<path:app_path>", "to_route": "dashboard-app"},

    # Old standalone www pages — left in place so existing bookmarks/links
    # to /dashboards, /dashboards-sales, /dashboards-inventory keep working
    # until you're ready to retire them.
    {"from_route": "/dashboards/<path:app_path>", "to_route": "dashboards"},
]

fixtures = [
    {"doctype": "Page",      "filters": [["module", "in", ["Dashboard Module"]]]},
    {"doctype": "Workspace", "filters": [["module", "in", ["Dashboard Module"]]]},
]

scheduler_events = {
    "all": [
        "dashboards.api.whatsapp_api.run_scheduled_whatsapp",
    ],
}

# Bust the inventory dashboard's cache the moment stock actually changes,
# rather than letting it serve stale batch/warehouse quantities for up to
# CACHE_TTL. Stock Ledger Entry covers Stock Entry, Delivery Note, Purchase
# Receipt, Stock Reconciliation, Serial and Batch Bundle moves, etc. Repost
# Item Valuation is covered separately since it can rewrite qty_after_transaction
# via a background job without necessarily re-triggering SLE doc events.
doc_events = {
    "Stock Ledger Entry": {
        "on_update": "dashboards.api.inventory_api.clear_cache",
        "on_cancel": "dashboards.api.inventory_api.clear_cache",
        "on_trash": "dashboards.api.inventory_api.clear_cache",
    },
    "Repost Item Valuation": {
        "on_update": "dashboards.api.inventory_api.clear_cache",
    },
}
