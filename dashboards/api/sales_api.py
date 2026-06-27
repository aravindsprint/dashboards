import frappe
from frappe import _
from frappe.utils import nowdate, add_months, flt
import json


# ── shared helpers ────────────────────────────────────────────────────────────

def _date_args(from_date, to_date):
    if not from_date:
        from_date = add_months(nowdate(), -1)
    if not to_date:
        to_date = nowdate()
    return from_date, to_date


def _cf(company):
    return "AND si.company=%s" if company else ""


# ── existing endpoints (unchanged) ───────────────────────────────────────────

@frappe.whitelist()
def get_dashboard_summary(from_date=None, to_date=None, company=None):
    from_date, to_date = _date_args(from_date, to_date)
    fb = {"docstatus": 1}
    if company:
        fb["company"] = company

    si_data = frappe.db.get_list(
        "Sales Invoice",
        filters={**fb, "posting_date": ["between", [from_date, to_date]]},
        fields=["grand_total", "outstanding_amount", "status", "name"],
        limit=10000,
    )
    total_invoiced   = sum(flt(r["grand_total"]) for r in si_data)
    total_outstanding = sum(flt(r["outstanding_amount"]) for r in si_data)
    total_collected  = total_invoiced - total_outstanding
    invoice_count    = len(si_data)
    status_counts_si = {}
    for r in si_data:
        s = r.get("status", "Draft")
        status_counts_si[s] = status_counts_si.get(s, 0) + 1

    so_data = frappe.db.get_list(
        "Sales Order",
        filters={**fb, "transaction_date": ["between", [from_date, to_date]]},
        fields=["grand_total", "advance_paid", "status", "delivery_status", "name"],
        limit=10000,
    )
    total_ordered   = sum(flt(r["grand_total"]) for r in so_data)
    order_count     = len(so_data)
    status_counts_so = {}
    delivery_counts  = {}
    for r in so_data:
        s = r.get("status", "Draft")
        status_counts_so[s] = status_counts_so.get(s, 0) + 1
        d = r.get("delivery_status", "Not Delivered")
        delivery_counts[d] = delivery_counts.get(d, 0) + 1

    collection_rate = round((total_collected / total_invoiced * 100), 2) if total_invoiced else 0

    return {
        "from_date": from_date, "to_date": to_date,
        "invoice": {
            "total_invoiced": total_invoiced,
            "total_collected": total_collected,
            "total_outstanding": total_outstanding,
            "collection_rate": collection_rate,
            "count": invoice_count,
            "status_breakdown": status_counts_si,
        },
        "order": {
            "total_ordered": total_ordered,
            "count": order_count,
            "status_breakdown": status_counts_so,
            "delivery_breakdown": delivery_counts,
        },
    }


@frappe.whitelist()
def get_monthly_trend(months=6, company=None):
    from_date = add_months(nowdate(), -int(months))
    cf = "AND company=%s" if company else ""
    p  = (from_date, company) if company else (from_date,)

    si_rows = frappe.db.sql(
        f"""SELECT DATE_FORMAT(posting_date,'%%Y-%%m') AS month,
                   SUM(grand_total) AS total, COUNT(name) AS cnt
            FROM `tabSales Invoice`
            WHERE docstatus=1 AND posting_date>=%s {cf}
            GROUP BY month ORDER BY month""",
        p, as_dict=True,
    )
    so_rows = frappe.db.sql(
        f"""SELECT DATE_FORMAT(transaction_date,'%%Y-%%m') AS month,
                   SUM(grand_total) AS total, COUNT(name) AS cnt
            FROM `tabSales Order`
            WHERE docstatus=1 AND transaction_date>=%s {cf}
            GROUP BY month ORDER BY month""",
        p, as_dict=True,
    )
    return {"invoices": si_rows, "orders": so_rows}


@frappe.whitelist()
def get_top_customers(from_date=None, to_date=None, limit=10, company=None):
    from_date, to_date = _date_args(from_date, to_date)
    cf = "AND company=%s" if company else ""
    p_si = [from_date, to_date] + ([company] if company else [])
    p_so = [from_date, to_date] + ([company] if company else [])

    top_si = frappe.db.sql(
        f"""SELECT customer, SUM(grand_total) AS revenue, COUNT(name) AS invoices
            FROM `tabSales Invoice`
            WHERE docstatus=1 AND posting_date BETWEEN %s AND %s {cf}
            GROUP BY customer ORDER BY revenue DESC LIMIT {int(limit)}""",
        p_si, as_dict=True,
    )
    top_so = frappe.db.sql(
        f"""SELECT customer, SUM(grand_total) AS order_value, COUNT(name) AS orders
            FROM `tabSales Order`
            WHERE docstatus=1 AND transaction_date BETWEEN %s AND %s {cf}
            GROUP BY customer ORDER BY order_value DESC LIMIT {int(limit)}""",
        p_so, as_dict=True,
    )
    return {"by_invoice": top_si, "by_order": top_so}


@frappe.whitelist()
def get_recent_transactions(limit=20, company=None):
    cf = {"company": company} if company else {}

    si = frappe.db.get_list(
        "Sales Invoice",
        filters={"docstatus": 1, **cf},
        fields=["name", "customer", "posting_date as date", "grand_total", "outstanding_amount", "status"],
        order_by="posting_date desc", limit=int(limit),
    )
    for r in si: r["type"] = "Invoice"

    so = frappe.db.get_list(
        "Sales Order",
        filters={"docstatus": 1, **cf},
        fields=["name", "customer", "transaction_date as date", "grand_total", "delivery_status", "status"],
        order_by="transaction_date desc", limit=int(limit),
    )
    for r in so: r["type"] = "Order"

    combined = sorted(si + so, key=lambda x: x.get("date") or "", reverse=True)
    return combined[:int(limit)]


@frappe.whitelist()
def get_filter_options():
    companies = frappe.db.get_list("Company", fields=["name"], order_by="name asc")
    return {"companies": [c["name"] for c in companies]}


# ── helpers: detect custom vs standard field names ───────────────────────────

def _col_exists(table, column):
    """Check if a column exists in a MariaDB table."""
    result = frappe.db.sql(
        "SELECT COUNT(*) FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s",
        (table, column)
    )
    return result[0][0] > 0


def _commercial_name_col(item_table):
    """
    Returns the actual column name for commercial_name in the given item table.
    Supports both 'commercial_name' (server) and 'custom_commercial_name' (local dev).
    """
    if _col_exists(item_table, "commercial_name"):
        return "commercial_name"
    if _col_exists(item_table, "custom_commercial_name"):
        return "custom_commercial_name"
    return None


# ── NEW: Commercial Name wise ─────────────────────────────────────────────────

@frappe.whitelist()
def get_commercial_name_wise(from_date=None, to_date=None, company=None, limit=15):
    from_date, to_date = _date_args(from_date, to_date)
    cf = _cf(company)
    p  = [from_date, to_date] + ([company] if company else [])

    # Detect actual column name for this installation
    si_col = _commercial_name_col("tabSales Invoice Item")
    so_col = _commercial_name_col("tabSales Order Item")

    if not si_col:
        return {"by_invoice": [], "by_order": []}

    rows = frappe.db.sql(
        f"""SELECT
                sii.{si_col} AS commercial_name,
                SUM(sii.amount)   AS revenue,
                SUM(sii.qty)      AS qty,
                COUNT(DISTINCT si.name) AS invoices
            FROM `tabSales Invoice Item` sii
            INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
            WHERE si.docstatus = 1
              AND si.posting_date BETWEEN %s AND %s
              AND (sii.{si_col} IS NOT NULL AND sii.{si_col} != '')
              {cf}
            GROUP BY sii.{si_col}
            ORDER BY revenue DESC
            LIMIT {int(limit)}""",
        p, as_dict=True,
    )

    # SO level — only if column exists
    if not so_col:
        return {"by_invoice": rows, "by_order": []}

    so_rows = frappe.db.sql(
        f"""SELECT
                soi.{so_col} AS commercial_name,
                SUM(soi.amount)   AS order_value,
                SUM(soi.qty)      AS qty
            FROM `tabSales Order Item` soi
            INNER JOIN `tabSales Order` so ON so.name = soi.parent
            WHERE so.docstatus = 1
              AND so.transaction_date BETWEEN %s AND %s
              AND (soi.{so_col} IS NOT NULL AND soi.{so_col} != '')
              {cf.replace('si.company', 'so.company')}
            GROUP BY soi.{so_col}
            ORDER BY order_value DESC
            LIMIT {int(limit)}""",
        p, as_dict=True,
    )

    return {"by_invoice": rows, "by_order": so_rows}


# ── NEW: UOM wise ─────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_uom_wise(from_date=None, to_date=None, company=None):
    from_date, to_date = _date_args(from_date, to_date)
    cf = _cf(company)
    p  = [from_date, to_date] + ([company] if company else [])

    si_rows = frappe.db.sql(
        f"""SELECT
                sii.uom,
                SUM(sii.amount)   AS revenue,
                SUM(sii.qty)      AS total_qty,
                COUNT(DISTINCT si.name) AS invoices
            FROM `tabSales Invoice Item` sii
            INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
            WHERE si.docstatus = 1
              AND si.posting_date BETWEEN %s AND %s
              AND (sii.uom IS NOT NULL AND sii.uom != '')
              {cf}
            GROUP BY sii.uom
            ORDER BY revenue DESC""",
        p, as_dict=True,
    )

    so_rows = frappe.db.sql(
        f"""SELECT
                soi.uom,
                SUM(soi.amount)   AS order_value,
                SUM(soi.qty)      AS total_qty,
                COUNT(DISTINCT so.name) AS orders
            FROM `tabSales Order Item` soi
            INNER JOIN `tabSales Order` so ON so.name = soi.parent
            WHERE so.docstatus = 1
              AND so.transaction_date BETWEEN %s AND %s
              AND (soi.uom IS NOT NULL AND soi.uom != '')
              {cf.replace('si.company', 'so.company')}
            GROUP BY soi.uom
            ORDER BY order_value DESC""",
        p, as_dict=True,
    )

    return {"by_invoice": si_rows, "by_order": so_rows}


# ── NEW: State wise ───────────────────────────────────────────────────────────

@frappe.whitelist()
def get_state_wise(from_date=None, to_date=None, company=None, limit=15):
    from_date, to_date = _date_args(from_date, to_date)
    cf = _cf(company)
    p  = [from_date, to_date] + ([company] if company else [])

    # State comes from `place_of_supply` on SI header (e.g. "33-Tamil Nadu")
    # We strip the code prefix to get clean state name
    si_rows = frappe.db.sql(
        f"""SELECT
                TRIM(SUBSTRING_INDEX(si.place_of_supply, '-', -1)) AS state,
                SUM(si.grand_total)   AS revenue,
                COUNT(si.name)        AS invoices,
                SUM(si.grand_total - si.outstanding_amount) AS collected
            FROM `tabSales Invoice` si
            WHERE si.docstatus = 1
              AND si.posting_date BETWEEN %s AND %s
              AND si.place_of_supply IS NOT NULL
              AND si.place_of_supply != ''
              {cf}
            GROUP BY state
            ORDER BY revenue DESC
            LIMIT {int(limit)}""",
        p, as_dict=True,
    )

    so_rows = frappe.db.sql(
        f"""SELECT
                TRIM(SUBSTRING_INDEX(so.territory, '/', -1)) AS state,
                SUM(so.grand_total)   AS order_value,
                COUNT(so.name)        AS orders
            FROM `tabSales Order` so
            WHERE so.docstatus = 1
              AND so.transaction_date BETWEEN %s AND %s
              AND so.territory IS NOT NULL
              {cf.replace('si.company', 'so.company')}
            GROUP BY state
            ORDER BY order_value DESC
            LIMIT {int(limit)}""",
        p, as_dict=True,
    )

    return {"by_invoice": si_rows, "by_order": so_rows}


# ── NEW: Sales Person wise ────────────────────────────────────────────────────

@frappe.whitelist()
def get_salesperson_wise(from_date=None, to_date=None, company=None, limit=15):
    from_date, to_date = _date_args(from_date, to_date)
    cf = _cf(company)
    p  = [from_date, to_date] + ([company] if company else [])

    si_rows = frappe.db.sql(
        f"""SELECT
                st.sales_person,
                SUM(si.grand_total * st.allocated_percentage / 100) AS revenue,
                COUNT(DISTINCT si.name) AS invoices,
                SUM((si.grand_total - si.outstanding_amount) * st.allocated_percentage / 100) AS collected
            FROM `tabSales Team` st
            INNER JOIN `tabSales Invoice` si ON si.name = st.parent
            WHERE si.docstatus = 1
              AND st.parenttype = 'Sales Invoice'
              AND si.posting_date BETWEEN %s AND %s
              AND st.sales_person IS NOT NULL
              {cf}
            GROUP BY st.sales_person
            ORDER BY revenue DESC
            LIMIT {int(limit)}""",
        p, as_dict=True,
    )

    so_rows = frappe.db.sql(
        f"""SELECT
                st.sales_person,
                SUM(so.grand_total * st.allocated_percentage / 100) AS order_value,
                COUNT(DISTINCT so.name) AS orders
            FROM `tabSales Team` st
            INNER JOIN `tabSales Order` so ON so.name = st.parent
            WHERE so.docstatus = 1
              AND st.parenttype = 'Sales Order'
              AND so.transaction_date BETWEEN %s AND %s
              AND st.sales_person IS NOT NULL
              {cf.replace('si.company', 'so.company')}
            GROUP BY st.sales_person
            ORDER BY order_value DESC
            LIMIT {int(limit)}""",
        p, as_dict=True,
    )

    return {"by_invoice": si_rows, "by_order": so_rows}


# ── NEW: Cost Center wise ─────────────────────────────────────────────────────

@frappe.whitelist()
def get_cost_center_wise(from_date=None, to_date=None, company=None, limit=15):
    """
    Cost Center wise — aggregated from Sales Invoice Item.cost_center
    and Sales Order Item.cost_center (item-level field is fully populated;
    the header-level cost_center is mostly null in your data).
    """
    from_date, to_date = _date_args(from_date, to_date)
    cf  = _cf(company)
    p   = [from_date, to_date] + ([company] if company else [])
    cf_so = ("AND so.company=%s" if company else "")

    # SI — item-level cost_center aggregated to invoice level
    si_rows = frappe.db.sql(
        f"""SELECT
                sii.cost_center,
                SUM(sii.amount)         AS revenue,
                SUM(sii.qty)            AS total_qty,
                COUNT(DISTINCT si.name) AS invoices,
                SUM(si.grand_total - si.outstanding_amount)
                    * SUM(sii.amount) / NULLIF(SUM(si.grand_total), 0) AS collected
            FROM `tabSales Invoice Item` sii
            INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
            WHERE si.docstatus = 1
              AND si.posting_date BETWEEN %s AND %s
              AND sii.cost_center IS NOT NULL
              AND sii.cost_center != ''
              {cf}
            GROUP BY sii.cost_center
            ORDER BY revenue DESC
            LIMIT {int(limit)}""",
        p, as_dict=True,
    )

    # SO — item-level cost_center
    so_rows = frappe.db.sql(
        f"""SELECT
                soi.cost_center,
                SUM(soi.amount)         AS order_value,
                SUM(soi.qty)            AS total_qty,
                COUNT(DISTINCT so.name) AS orders
            FROM `tabSales Order Item` soi
            INNER JOIN `tabSales Order` so ON so.name = soi.parent
            WHERE so.docstatus = 1
              AND so.transaction_date BETWEEN %s AND %s
              AND soi.cost_center IS NOT NULL
              AND soi.cost_center != ''
              {cf_so}
            GROUP BY soi.cost_center
            ORDER BY order_value DESC
            LIMIT {int(limit)}""",
        p, as_dict=True,
    )

    return {"by_invoice": si_rows, "by_order": so_rows}


# ── NEW: Naming Series wise ───────────────────────────────────────────────────

@frappe.whitelist()
def get_naming_series_wise(from_date=None, to_date=None, company=None, limit=20):
    """
    Naming Series wise breakdown — groups by the full naming_series value
    and also extracts a human-readable prefix (everything before the first dot).
    e.g. 'PTGB26/.#####' → prefix 'PTGB26', label 'PTGB26 (Tirupur Garments B2B)'
    """
    from_date, to_date = _date_args(from_date, to_date)
    cf = _cf(company)
    p  = [from_date, to_date] + ([company] if company else [])

    si_rows = frappe.db.sql(
        f"""SELECT
                si.naming_series,
                TRIM(SUBSTRING_INDEX(si.naming_series, '/', 1)) AS series_prefix,
                SUM(si.grand_total)   AS revenue,
                COUNT(si.name)        AS invoices,
                SUM(si.grand_total - si.outstanding_amount) AS collected
            FROM `tabSales Invoice` si
            WHERE si.docstatus = 1
              AND si.posting_date BETWEEN %s AND %s
              AND si.naming_series IS NOT NULL
              AND si.naming_series != ''
              {cf}
            GROUP BY si.naming_series
            ORDER BY revenue DESC
            LIMIT {int(limit)}""",
        p, as_dict=True,
    )

    so_rows = frappe.db.sql(
        f"""SELECT
                so.naming_series,
                TRIM(SUBSTRING_INDEX(so.naming_series, '/', 1)) AS series_prefix,
                SUM(so.grand_total)   AS order_value,
                COUNT(so.name)        AS orders
            FROM `tabSales Order` so
            WHERE so.docstatus = 1
              AND so.transaction_date BETWEEN %s AND %s
              AND so.naming_series IS NOT NULL
              AND so.naming_series != ''
              {cf.replace('si.company', 'so.company')}
            GROUP BY so.naming_series
            ORDER BY order_value DESC
            LIMIT {int(limit)}""",
        p, as_dict=True,
    )

    return {"by_invoice": si_rows, "by_order": so_rows}


# ── App screen permission check ───────────────────────────────────────────────

def has_app_permission():
    """Allow any logged-in user with Sales/Purchase/System Manager role."""
    allowed_roles = {"Sales User", "Sales Manager", "Purchase User",
                     "Purchase Manager", "Stock User", "Manufacturing User",
                     "System Manager"}
    user_roles = set(frappe.get_roles(frappe.session.user))
    return bool(allowed_roles & user_roles)


@frappe.whitelist()
def check_app_permission():
    return "System Manager" in frappe.get_roles()
# ── ADD THIS BLOCK TO THE BOTTOM OF sales_api.py ──────────────────────────
# Paste everything below this line into:
#   apps/dashboards/dashboards/api/sales_api.py

@frappe.whitelist()
# ── APPEND THIS ENTIRE BLOCK TO THE END OF sales_api.py ──────────────────────


@frappe.whitelist()
# ── APPEND THIS ENTIRE BLOCK TO THE END OF sales_api.py ──────────────────────


@frappe.whitelist()
# ── APPEND THIS ENTIRE BLOCK TO THE END OF sales_api.py ──────────────────────


@frappe.whitelist()
# ── APPEND THIS ENTIRE BLOCK TO THE END OF sales_api.py ──────────────────────


@frappe.whitelist()
def get_drill_down(drill_type, from_date=None, to_date=None, company=None,
                   customer=None, state=None, cost_center=None,
                   sales_person=None, commercial_name=None, uom=None,
                   naming_series=None, doc_name=None, doc_type=None):
    """
    Single drill-down endpoint for all dashboard tables.

    drill_type values:
      customer_items          → SI line items (item_code, commercial_name, uom, qty, revenue, sales_person)
      customer_order_items    → SO line items for a customer
      commercial_name_detail  → SI: item codes + customers for a commercial name
      uom_items               → SI: item codes for a UOM
      state_customers         → SI+SO: customers in a state
      salesperson_items       → SI: items sold by a sales person
      cost_center_customers   → SI+SO: customers under a cost center
      naming_series_docs      → SI: recent docs for a naming series
      transaction_items       → line items for a specific SI or SO document
    """
    from_date, to_date = _date_args(from_date, to_date)
    cf    = _cf(company)
    cf_so = cf.replace("si.company", "so.company")
    p     = [from_date, to_date] + ([company] if company else [])
    # p_base excludes company so customer/filter goes BEFORE company in params
    p_base = [from_date, to_date]
    p_co   = ([company] if company else [])

    # Detect commercial_name column for this installation
    si_cn = _commercial_name_col("tabSales Invoice Item") or "item_name"
    so_cn = _commercial_name_col("tabSales Order Item")   or "item_name"

    # ── 1. Customer → SI line items (item code, commercial name, sales person) ─
    if drill_type == "customer_items":
        return frappe.db.sql(f"""
            SELECT
                sii.item_code,
                sii.item_name,
                sii.{si_cn}               AS commercial_name,
                sii.uom,
                SUM(sii.qty)              AS qty,
                SUM(sii.amount)           AS revenue,
                MAX(st.sales_person) AS sales_person
            FROM `tabSales Invoice Item` sii
            JOIN `tabSales Invoice` si ON si.name = sii.parent
            LEFT JOIN `tabSales Team` st
                ON st.parent = si.name AND st.parenttype = 'Sales Invoice'
            WHERE si.docstatus = 1
              AND si.posting_date BETWEEN %s AND %s
              AND si.customer = %s
              {cf}
            GROUP BY sii.item_code, sii.uom
            ORDER BY revenue DESC
            LIMIT 20
        """, p_base + [customer] + p_co, as_dict=True)

    # ── 2. Customer → SO line items ────────────────────────────────────────────
    if drill_type == "customer_order_items":
        return frappe.db.sql(f"""
            SELECT
                soi.item_code,
                soi.item_name,
                soi.{so_cn}               AS commercial_name,
                soi.uom,
                SUM(soi.qty)              AS qty,
                SUM(soi.amount)           AS order_value,
                MAX(st.sales_person) AS sales_person
            FROM `tabSales Order Item` soi
            JOIN `tabSales Order` so ON so.name = soi.parent
            LEFT JOIN `tabSales Team` st
                ON st.parent = so.name AND st.parenttype = 'Sales Order'
            WHERE so.docstatus = 1
              AND so.transaction_date BETWEEN %s AND %s
              AND so.customer = %s
              {cf_so}
            GROUP BY soi.item_code, soi.uom
            ORDER BY order_value DESC
            LIMIT 20
        """, p_base + [customer] + p_co, as_dict=True)

    # ── 3. Commercial name → item codes + customers ────────────────────────────
    if drill_type == "commercial_name_detail":
        # Try to get color from item master
        try:
            has_color = frappe.db.sql(
                "SELECT 1 FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='tabItem' AND COLUMN_NAME='color' LIMIT 1"
            )
            color_col = "i.color" if has_color else "sii.item_name"
        except Exception:
            color_col = "sii.item_name"

        return frappe.db.sql(f"""
            SELECT
                {color_col}               AS color,
                sii.{si_cn}               AS commercial_name,
                sii.uom,
                si.customer,
                SUM(sii.qty)              AS qty,
                SUM(sii.amount)           AS revenue,
                MAX(st.sales_person)      AS sales_person
            FROM `tabSales Invoice Item` sii
            JOIN `tabSales Invoice` si ON si.name = sii.parent
            LEFT JOIN `tabItem` i ON i.name = sii.item_code
            LEFT JOIN `tabSales Team` st
                ON st.parent = si.name AND st.parenttype = 'Sales Invoice'
            WHERE si.docstatus = 1
              AND si.posting_date BETWEEN %s AND %s
              AND sii.{si_cn} = %s
              {{'AND si.company=%s' if company else ''}}
            GROUP BY {color_col}, sii.uom
            ORDER BY revenue DESC
            LIMIT 30
        """, p_base + [commercial_name] + p_co, as_dict=True)

    # ── 4. UOM → item codes ────────────────────────────────────────────────────
    if drill_type == "uom_items":
        return frappe.db.sql(f"""
            SELECT
                sii.item_code,
                sii.item_name,
                sii.{si_cn}  AS commercial_name,
                SUM(sii.qty) AS qty,
                SUM(sii.amount) AS revenue
            FROM `tabSales Invoice Item` sii
            JOIN `tabSales Invoice` si ON si.name = sii.parent
            WHERE si.docstatus = 1
              AND si.posting_date BETWEEN %s AND %s
              AND sii.uom = %s
              {cf}
            GROUP BY sii.item_code
            ORDER BY revenue DESC
            LIMIT 20
        """, p_base + [uom] + p_co, as_dict=True)

    # ── 5. State → cities ───────────────────────────────────────────────────────
    if drill_type == "state_customers":
        si_rows = frappe.db.sql(f"""
            SELECT
                COALESCE(addr.city, 'Unknown') AS city,
                SUM(si.grand_total)             AS revenue,
                COUNT(si.name)                  AS invoices,
                SUM(si.outstanding_amount)      AS outstanding
            FROM `tabSales Invoice` si
            JOIN `tabCustomer` c ON c.name = si.customer
            LEFT JOIN `tabDynamic Link` dl
                ON dl.link_doctype = 'Customer'
                AND dl.link_name = c.name
                AND dl.parenttype = 'Address'
            LEFT JOIN `tabAddress` addr ON addr.name = dl.parent AND addr.is_primary_address = 1
            WHERE si.docstatus = 1
              AND si.posting_date BETWEEN %s AND %s
              AND COALESCE(addr.state, '') = %s
              {cf}
            GROUP BY addr.city
            ORDER BY revenue DESC
            LIMIT 20
        """, p_base + [state] + p_co, as_dict=True)

        so_rows = frappe.db.sql(f"""
            SELECT
                COALESCE(addr.city, 'Unknown') AS city,
                SUM(so.grand_total)             AS order_value,
                COUNT(so.name)                  AS orders
            FROM `tabSales Order` so
            JOIN `tabCustomer` c ON c.name = so.customer
            LEFT JOIN `tabDynamic Link` dl
                ON dl.link_doctype = 'Customer'
                AND dl.link_name = c.name
                AND dl.parenttype = 'Address'
            LEFT JOIN `tabAddress` addr ON addr.name = dl.parent AND addr.is_primary_address = 1
            WHERE so.docstatus = 1
              AND so.transaction_date BETWEEN %s AND %s
              AND COALESCE(addr.state, '') = %s
              {cf_so}
            GROUP BY addr.city
            ORDER BY order_value DESC
            LIMIT 20
        """, p_base + [state] + p_co, as_dict=True)

        so_map = {r.city: r for r in so_rows}
        for r in si_rows:
            so = so_map.get(r.city, {})
            r["order_value"] = so.get("order_value", 0)
            r["orders"]      = so.get("orders", 0)
        return si_rows

    # ── 6. Sales person → items sold ──────────────────────────────────────────
    if drill_type == "salesperson_items":
        return frappe.db.sql(f"""
            SELECT
                sii.item_code,
                sii.item_name,
                sii.{si_cn}    AS commercial_name,
                si.customer,
                sii.uom,
                SUM(sii.qty)   AS qty,
                SUM(sii.amount) AS revenue
            FROM `tabSales Invoice Item` sii
            JOIN `tabSales Invoice` si ON si.name = sii.parent
            JOIN `tabSales Team` st
                ON st.parent = si.name AND st.parenttype = 'Sales Invoice'
            WHERE si.docstatus = 1
              AND si.posting_date BETWEEN %s AND %s
              AND st.sales_person = %s
              {'AND si.company=%s' if company else ''}
            GROUP BY sii.item_code, si.customer
            ORDER BY revenue DESC
            LIMIT 20
        """, p_base + [sales_person] + p_co, as_dict=True)

    # ── 7. Cost center → customers + sales persons ─────────────────────────────
    if drill_type == "cost_center_customers":
        cc_val  = (cost_center or "").strip()
        cc_like = f"%{cc_val}%"
        cf_si   = ("AND si.company=%s" if company else "")
        cf_so2  = ("AND so.company=%s" if company else "")

        # Cost center is stored at item level (tabSales Invoice Item), not header
        si_rows = frappe.db.sql(f"""
            SELECT
                si.customer,
                SUM(sii.amount)           AS revenue,
                COUNT(DISTINCT si.name)   AS invoices,
                MAX(st.sales_person)      AS sales_person
            FROM `tabSales Invoice Item` sii
            JOIN `tabSales Invoice` si ON si.name = sii.parent
            LEFT JOIN `tabSales Team` st
                ON st.parent = si.name AND st.parenttype = 'Sales Invoice'
            WHERE si.docstatus = 1
              AND si.posting_date BETWEEN %s AND %s
              AND sii.cost_center LIKE %s
              {cf_si}
            GROUP BY si.customer
            ORDER BY revenue DESC
            LIMIT 20
        """, p_base + [cc_like] + p_co, as_dict=True)

        so_rows = frappe.db.sql(f"""
            SELECT
                so.customer,
                SUM(soi.amount) AS order_value,
                COUNT(DISTINCT so.name) AS orders
            FROM `tabSales Order Item` soi
            JOIN `tabSales Order` so ON so.name = soi.parent
            WHERE so.docstatus = 1
              AND so.transaction_date BETWEEN %s AND %s
              AND soi.cost_center LIKE %s
              {cf_so2}
            GROUP BY so.customer
            ORDER BY order_value DESC
            LIMIT 20
        """, p_base + [cc_like] + p_co, as_dict=True)

        so_map = {r.customer: r for r in so_rows}
        for r in si_rows:
            so = so_map.get(r.customer, {})
            r["order_value"] = so.get("order_value", 0)
            r["orders"]      = so.get("orders", 0)
        return si_rows

    # ── 8. Naming series → recent documents ───────────────────────────────────
    if drill_type == "naming_series_docs":
        cf_plain = ("AND company=%s" if company else "")
        return frappe.db.sql(f"""
            SELECT
                name,
                customer,
                posting_date AS date,
                grand_total,
                status
            FROM `tabSales Invoice`
            WHERE docstatus = 1
              AND posting_date BETWEEN %s AND %s
              AND naming_series = %s
              {cf_plain}
            ORDER BY posting_date DESC
            LIMIT 20
        """, p_base + [naming_series] + p_co, as_dict=True)

    # ── 9. Transaction → line items (SI or SO) ─────────────────────────────────
    if drill_type == "transaction_items":
        if doc_type == "Invoice":
            return frappe.db.sql(f"""
                SELECT
                    sii.idx,
                    sii.item_code,
                    sii.item_name,
                    sii.{si_cn} AS commercial_name,
                    sii.uom,
                    sii.qty,
                    sii.rate,
                    sii.amount
                FROM `tabSales Invoice Item` sii
                WHERE sii.parent = %s
                ORDER BY sii.idx
            """, [doc_name], as_dict=True)
        else:
            return frappe.db.sql(f"""
                SELECT
                    soi.idx,
                    soi.item_code,
                    soi.item_name,
                    soi.{so_cn} AS commercial_name,
                    soi.uom,
                    soi.qty,
                    soi.rate,
                    soi.amount
                FROM `tabSales Order Item` soi
                WHERE soi.parent = %s
                ORDER BY soi.idx
            """, [doc_name], as_dict=True)

    return []
