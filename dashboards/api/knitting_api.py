import frappe
from frappe.utils import nowdate, add_months, flt


# ── shared helpers ────────────────────────────────────────────────────────────
# Same conventions as sales_api.py / inventory_api.py: Item.custom_item_type
# buckets stock movements into 'Fabric' (Kgs) vs 'Collar' / 'Cuff' (Pcs) — see
# inventory_api.get_mars200_stock for the same field used against live stock.
#
# ASSUMPTION (flag this if it doesn't match what you expect): "produced" here
# means positive Stock Ledger Entries (actual_qty > 0, i.e. stock receipts —
# Manufacture / Material Receipt entries) posted in the selected date range,
# landing in one of the two knitting-floor warehouses below. If you want this
# scoped to a specific stock entry type or a different definition of
# "produced", tell us and we'll adjust the WHERE clause below.

ROLL_WAREHOUSES = ("NAP_E1/FF/A01 - PSS", "NAP_E1/FF/A02 - PSS")


def _date_args(from_date, to_date):
    if not from_date:
        from_date = add_months(nowdate(), -1)
    if not to_date:
        to_date = nowdate()
    return from_date, to_date


@frappe.whitelist()
def get_summary(from_date=None, to_date=None, company=None):
    """
    Total quantity produced/received in the date range, split by
    Item.custom_item_type:
      - Fabric          -> qty in Kgs (or whatever stock_uom is on the item)
      - Collar + Cuff   -> qty in Pcs (or whatever stock_uom is on the item)
    Returns one row per (item_type, stock_uom) so the frontend can show the
    real UOM rather than assuming Kgs/Pcs.
    """
    from_date, to_date = _date_args(from_date, to_date)
    cf = "AND wh.company = %(company)s" if company else ""

    rows = frappe.db.sql(
        f"""
        SELECT
            item.custom_item_type   AS item_type,
            sle.stock_uom            AS uom,
            ROUND(SUM(sle.actual_qty), 3) AS qty,
            COUNT(DISTINCT sle.voucher_no) AS entries
        FROM `tabStock Ledger Entry` sle
        INNER JOIN `tabItem` item      ON item.item_code = sle.item_code
        INNER JOIN `tabWarehouse` wh   ON wh.name = sle.warehouse
        WHERE sle.is_cancelled = 0
          AND sle.actual_qty > 0
          AND sle.warehouse IN %(warehouses)s
          AND sle.posting_date BETWEEN %(from_date)s AND %(to_date)s
          AND item.custom_item_type IN ('Fabric', 'Collar', 'Cuff')
          {cf}
        GROUP BY item.custom_item_type, sle.stock_uom
        """,
        {"from_date": from_date, "to_date": to_date, "company": company, "warehouses": ROLL_WAREHOUSES},
        as_dict=True,
    )

    summary = {
        "fabric":  {"qty": 0, "uom": "Kgs", "entries": 0},
        "collar":  {"qty": 0, "uom": "Pcs", "entries": 0},
        "cuff":    {"qty": 0, "uom": "Pcs", "entries": 0},
    }
    for r in rows:
        key = (r["item_type"] or "").lower()
        if key not in summary:
            continue
        summary[key]["qty"] = flt(r["qty"])
        summary[key]["uom"] = r["uom"] or summary[key]["uom"]
        summary[key]["entries"] += int(r["entries"] or 0)

    return summary


@frappe.whitelist()
def get_daily_breakdown(from_date=None, to_date=None, company=None):
    """
    Day-wise Fabric / Collar / Cuff quantities, oldest to newest, plus a
    grand-total row — the same Fabric/Collar/Cuff stock data as get_summary,
    just grouped by day instead of totalled across the whole range.
    """
    from_date, to_date = _date_args(from_date, to_date)
    cf = "AND wh.company = %(company)s" if company else ""

    rows = frappe.db.sql(
        f"""
        SELECT
            sle.posting_date          AS date,
            item.custom_item_type      AS item_type,
            ROUND(SUM(sle.actual_qty), 3) AS qty
        FROM `tabStock Ledger Entry` sle
        INNER JOIN `tabItem` item      ON item.item_code = sle.item_code
        INNER JOIN `tabWarehouse` wh   ON wh.name = sle.warehouse
        WHERE sle.is_cancelled = 0
          AND sle.actual_qty > 0
          AND sle.warehouse IN %(warehouses)s
          AND sle.posting_date BETWEEN %(from_date)s AND %(to_date)s
          AND item.custom_item_type IN ('Fabric', 'Collar', 'Cuff')
          {cf}
        GROUP BY sle.posting_date, item.custom_item_type
        ORDER BY sle.posting_date ASC
        """,
        {"from_date": from_date, "to_date": to_date, "company": company, "warehouses": ROLL_WAREHOUSES},
        as_dict=True,
    )

    by_date = {}
    totals = {"fabric_qty": 0, "collar_qty": 0, "cuff_qty": 0}
    for r in rows:
        d = str(r["date"])
        day = by_date.setdefault(d, {"date": d, "fabric_qty": 0, "collar_qty": 0, "cuff_qty": 0})
        key = (r["item_type"] or "").lower() + "_qty"
        if key not in day:
            continue
        day[key] += flt(r["qty"])
        totals[key] += flt(r["qty"])

    days = sorted(by_date.values(), key=lambda x: x["date"])
    return {"days": days, "totals": totals}


@frappe.whitelist()
def get_item_wise(from_date=None, to_date=None, company=None, limit=50):
    """
    Item-wise breakdown for the same date range — Item code, commercial
    name, color, item type, qty, uom — for a detail table under the
    summary cards.
    """
    from_date, to_date = _date_args(from_date, to_date)
    limit = frappe.utils.cint(limit) or 50
    cf = "AND wh.company = %(company)s" if company else ""

    rows = frappe.db.sql(
        f"""
        SELECT
            item.item_code           AS item_code,
            item.commercial_name     AS commercial_name,
            item.color                AS color,
            item.custom_item_type     AS item_type,
            sle.stock_uom              AS uom,
            ROUND(SUM(sle.actual_qty), 3) AS qty
        FROM `tabStock Ledger Entry` sle
        INNER JOIN `tabItem` item      ON item.item_code = sle.item_code
        INNER JOIN `tabWarehouse` wh   ON wh.name = sle.warehouse
        WHERE sle.is_cancelled = 0
          AND sle.actual_qty > 0
          AND sle.warehouse IN %(warehouses)s
          AND sle.posting_date BETWEEN %(from_date)s AND %(to_date)s
          AND item.custom_item_type IN ('Fabric', 'Collar', 'Cuff')
          {cf}
        GROUP BY item.item_code
        HAVING qty > 0
        ORDER BY item.custom_item_type, qty DESC
        LIMIT %(limit)s
        """,
        {"from_date": from_date, "to_date": to_date, "company": company, "limit": limit, "warehouses": ROLL_WAREHOUSES},
        as_dict=True,
    )
    for r in rows:
        r["qty"] = flt(r["qty"])
    return rows


@frappe.whitelist()
def get_filter_options():
    companies = frappe.db.get_list("Company", fields=["name"], order_by="name asc")
    return {"companies": [c["name"] for c in companies]}


# ── Roll-based production analytics ────────────────────────────────────────
# Source: the `Roll` doctype from the pranera_knit app (one row per knitted
# roll, logged operator-side via save_roll_data in pranera_knit/api/knit.py).
# Relevant fields used below: work_order, item_code, item_name,
# commercial_name, color, roll_weight (Kgs), total_qty (Pcs knitted),
# mistake_qty (Pcs), correct_qty (Pcs), knitting_machine_no,
# name_of_the_operator, start_time, end_time.
#
# A roll counts as "produced" once it's closed out: end_time is set OR
# roll_weight > 0 — same condition pranera_knit's own check_job_card_rolls
# uses. Date-ranged on end_time (falling back to start_time if end_time is
# blank), since that's when the roll is actually finished.
#
# Roll has no company field of its own, so the optional company filter goes
# through Work Order.company via roll.work_order.
#
# ASSUMPTION (flag this if it doesn't match what you expect): "skill level"
# below is a simple label derived from correct_qty / total_qty (the good-vs-
# mistake ratio already recorded on each roll) — Excellent >=95%, Good >=85%,
# Average >=70%, else Needs review. Tell us if you'd rather rank operators by
# something else (output volume, efficiency_percentage if that field is
# populated, etc.) and we'll change the ranking logic.

def _roll_date_filter():
    return "COALESCE(DATE(roll.end_time), DATE(roll.start_time)) BETWEEN %(from_date)s AND %(to_date)s"


def _roll_company_join(company):
    if not company:
        return "", {}
    return (
        "INNER JOIN `tabWork Order` wo ON wo.name = roll.work_order AND wo.company = %(company)s",
        {"company": company},
    )


def _skill_level(pct):
    if pct >= 95:
        return "Excellent"
    if pct >= 85:
        return "Good"
    if pct >= 70:
        return "Average"
    return "Needs review"


@frappe.whitelist()
def get_operator_summary(from_date=None, to_date=None, company=None, limit=50):
    """Per-operator output and a skill-level label, for the date range."""
    from_date, to_date = _date_args(from_date, to_date)
    limit = frappe.utils.cint(limit) or 50
    join, extra = _roll_company_join(company)

    rows = frappe.db.sql(
        f"""
        SELECT
            roll.name_of_the_operator AS operator,
            COUNT(*)                   AS rolls,
            ROUND(SUM(roll.roll_weight), 3) AS total_weight,
            ROUND(SUM(roll.total_qty), 3)   AS total_qty,
            ROUND(SUM(roll.correct_qty), 3) AS correct_qty,
            ROUND(SUM(roll.mistake_qty), 3) AS mistake_qty
        FROM `tabRoll` roll
        {join}
        WHERE (roll.end_time IS NOT NULL OR roll.roll_weight > 0)
          AND roll.name_of_the_operator IS NOT NULL AND roll.name_of_the_operator != ''
          AND {_roll_date_filter()}
        GROUP BY roll.name_of_the_operator
        ORDER BY total_weight DESC
        LIMIT %(limit)s
        """,
        {"from_date": from_date, "to_date": to_date, "limit": limit, **extra},
        as_dict=True,
    )
    for r in rows:
        total_qty = flt(r["total_qty"])
        correct_qty = flt(r["correct_qty"])
        pct = (correct_qty / total_qty * 100) if total_qty else 0
        r["total_weight"] = flt(r["total_weight"])
        r["total_qty"] = total_qty
        r["correct_qty"] = correct_qty
        r["mistake_qty"] = flt(r["mistake_qty"])
        r["accuracy_pct"] = round(pct, 1)
        r["skill_level"] = _skill_level(pct)
    return rows


@frappe.whitelist()
def get_fabric_volume(from_date=None, to_date=None, company=None, limit=50):
    """Production volume (Kgs) for every fabric knitted in the date range."""
    from_date, to_date = _date_args(from_date, to_date)
    limit = frappe.utils.cint(limit) or 50
    join, extra = _roll_company_join(company)

    rows = frappe.db.sql(
        f"""
        SELECT
            COALESCE(NULLIF(roll.commercial_name, ''), roll.item_name, roll.item_code) AS fabric,
            roll.item_code              AS item_code,
            COUNT(*)                     AS rolls,
            ROUND(SUM(roll.roll_weight), 3) AS total_weight,
            ROUND(SUM(roll.total_qty), 3)   AS total_qty
        FROM `tabRoll` roll
        {join}
        WHERE (roll.end_time IS NOT NULL OR roll.roll_weight > 0)
          AND {_roll_date_filter()}
        GROUP BY fabric, roll.item_code
        HAVING total_weight > 0
        ORDER BY total_weight DESC
        LIMIT %(limit)s
        """,
        {"from_date": from_date, "to_date": to_date, "limit": limit, **extra},
        as_dict=True,
    )
    for r in rows:
        r["total_weight"] = flt(r["total_weight"])
        r["total_qty"] = flt(r["total_qty"])
    return rows


@frappe.whitelist()
def get_machine_output(from_date=None, to_date=None, company=None, limit=50):
    """Per-machine output for the date range."""
    from_date, to_date = _date_args(from_date, to_date)
    limit = frappe.utils.cint(limit) or 50
    join, extra = _roll_company_join(company)

    rows = frappe.db.sql(
        f"""
        SELECT
            NULLIF(roll.knitting_machine_no, '') AS machine,
            COUNT(*)                     AS rolls,
            ROUND(SUM(roll.roll_weight), 3) AS total_weight,
            ROUND(SUM(roll.total_qty), 3)   AS total_qty,
            ROUND(SUM(roll.correct_qty), 3) AS correct_qty
        FROM `tabRoll` roll
        {join}
        WHERE (roll.end_time IS NOT NULL OR roll.roll_weight > 0)
          AND roll.knitting_machine_no IS NOT NULL AND roll.knitting_machine_no != ''
          AND {_roll_date_filter()}
        GROUP BY roll.knitting_machine_no
        ORDER BY total_weight DESC
        LIMIT %(limit)s
        """,
        {"from_date": from_date, "to_date": to_date, "limit": limit, **extra},
        as_dict=True,
    )
    for r in rows:
        total_qty = flt(r["total_qty"])
        correct_qty = flt(r["correct_qty"])
        r["total_weight"] = flt(r["total_weight"])
        r["total_qty"] = total_qty
        r["correct_qty"] = correct_qty
        r["efficiency_pct"] = round((correct_qty / total_qty * 100) if total_qty else 0, 1)
    return rows


@frappe.whitelist()
def get_monthly_production(from_date=None, to_date=None, company=None):
    """Monthly totals (Kgs and Pcs) across the date range, oldest first."""
    from_date, to_date = _date_args(from_date, to_date)
    join, extra = _roll_company_join(company)

    rows = frappe.db.sql(
        f"""
        SELECT
            DATE_FORMAT(COALESCE(roll.end_time, roll.start_time), '%%Y-%%m') AS month,
            COUNT(*)                     AS rolls,
            ROUND(SUM(roll.roll_weight), 3) AS total_weight,
            ROUND(SUM(roll.total_qty), 3)   AS total_qty
        FROM `tabRoll` roll
        {join}
        WHERE (roll.end_time IS NOT NULL OR roll.roll_weight > 0)
          AND {_roll_date_filter()}
        GROUP BY month
        ORDER BY month ASC
        """,
        {"from_date": from_date, "to_date": to_date, **extra},
        as_dict=True,
    )
    for r in rows:
        r["total_weight"] = flt(r["total_weight"])
        r["total_qty"] = flt(r["total_qty"])
    return rows


