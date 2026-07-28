import frappe
from frappe.utils import flt

# ── cache helpers ────────────────────────────────────────────────────────────
CACHE_TTL = 1800  # 30 minutes, mirrors the old node/redis cache window


def _cache_get(key):
    val = frappe.cache().get_value(key)
    return val


def _cache_set(key, val):
    frappe.cache().set_value(key, val, expires_in_sec=CACHE_TTL)


# ── shared row shaper ────────────────────────────────────────────────────────
def _rows_for_warehouse_group(wh_like):
    """
    Batch-wise available stock (qty > 0) for every fabric item sitting in
    warehouses matching wh_like, e.g. 'JV/%' or 'PT/SASTRI%'.
    Mirrors the old stockapp getStockDetailsForAllBatches(JV) queries, but
    reads live from ERPNext's own Stock Ledger Entry / Batch / Item tables
    instead of a mirrored sqlite cache.
    """
    return frappe.db.sql(
        """
        SELECT
            sle.item_code                      AS item_code,
            item.commercial_name                AS commercial_name,
            item.color                          AS color,
            item.width                          AS width,
            sle.warehouse                       AS warehouse,
            sle.batch_no                        AS batch_no,
            batch.batch_status                  AS batch_status,
            ROUND(SUM(sle.actual_qty), 3)       AS actual_qty,
            sle.stock_uom                       AS stock_uom
        FROM `tabStock Ledger Entry` sle
        INNER JOIN `tabItem` item  ON item.item_code = sle.item_code
        INNER JOIN `tabBatch` batch ON batch.name = sle.batch_no
        WHERE sle.is_cancelled = 0
          AND sle.warehouse LIKE %(wh_like)s
          AND sle.batch_no IS NOT NULL AND sle.batch_no != ''
          AND item.commercial_name IS NOT NULL AND item.commercial_name != ''
        GROUP BY sle.item_code, sle.warehouse, sle.batch_no
        HAVING actual_qty > 0
        ORDER BY item.commercial_name, item.color, item.width
        """,
        {"wh_like": wh_like},
        as_dict=True,
    )


@frappe.whitelist()
def get_stock_by_batch(group, refresh=0):
    """
    group: 'pt_sastri' | 'jv'
    Returns the flat batch-level rows used to build the
    Commercial Name > Color tree table (Width / Item code / Warehouse /
    Qty / BatchNo / BatchStatus) — same shape as the old
    getStockDetailsForAllBatches / getStockDetailsForAllBatchesJV endpoints.
    """
    group = (group or "").lower()
    if group not in ("pt_sastri", "jv"):
        frappe.throw("group must be 'pt_sastri' or 'jv'")

    key = f"inv_dash:stock_by_batch:{group}"
    if not frappe.utils.cint(refresh):
        cached = _cache_get(key)
        if cached is not None:
            return cached

    wh_like = "PT/SASTRI%" if group == "pt_sastri" else "JV/%"
    rows = _rows_for_warehouse_group(wh_like)
    for r in rows:
        r["actual_qty"] = flt(r["actual_qty"])

    _cache_set(key, rows)
    return rows


@frappe.whitelist()
def get_mars200_stock(commercial_name="MARS 200", refresh=0):
    """
    Fabric stock for a given commercial name (default 'MARS 200'), in the
    JV / PT-SASTRI warehouses, joined with the matching Collar and Cuff
    batch quantities via Batch.custom_parent_batch — mirrors
    getFabricCollarCuffStockDetails() in the old stockapp, computed live
    against ERPNext instead of the mirrored sqlite cache.

    NOTE: this is a best-effort rebuild of that join. If the collar/cuff
    figures look off once you see real data, flag it and we'll adjust the
    matching logic.
    """
    commercial_name = commercial_name or "MARS 200"
    key = f"inv_dash:mars200:{commercial_name.strip().lower()}"
    if not frappe.utils.cint(refresh):
        cached = _cache_get(key)
        if cached is not None:
            return cached

    fabric_rows = frappe.db.sql(
        """
        SELECT
            sle.batch_no                                            AS batch_no,
            item.commercial_name                                    AS commercial_name,
            item.color                                              AS color,
            item.width                                               AS width,
            batch.batch_status                                       AS batch_status,
            CASE WHEN sle.warehouse LIKE 'JV/%%' THEN 'JV' ELSE 'SASTRI' END AS parentwarehouse,
            ROUND(SUM(sle.actual_qty), 3)                            AS actual_qty,
            sle.stock_uom                                            AS stock_uom
        FROM `tabStock Ledger Entry` sle
        INNER JOIN `tabItem` item  ON item.item_code = sle.item_code
        INNER JOIN `tabBatch` batch ON batch.name = sle.batch_no
        WHERE sle.is_cancelled = 0
          AND item.custom_item_type = 'Fabric'
          AND item.commercial_name LIKE %(comm)s
          AND (sle.warehouse LIKE 'JV/%%' OR sle.warehouse LIKE 'PT/SASTRI%%')
          AND sle.batch_no IS NOT NULL AND sle.batch_no != ''
        GROUP BY sle.batch_no, parentwarehouse
        HAVING actual_qty > 0
        ORDER BY item.color, item.width
        """,
        {"comm": f"{commercial_name.strip()}%"},
        as_dict=True,
    )

    batch_nos = list({r["batch_no"] for r in fabric_rows})
    collar_cuff_by_batch = {}
    if batch_nos:
        cc_rows = frappe.db.sql(
            """
            SELECT
                batch.custom_parent_batch AS parent_batch,
                item.custom_item_type     AS item_type,
                batch.batch_status        AS batch_status,
                ROUND(SUM(sle.actual_qty), 3) AS qty
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabBatch` batch ON batch.name = sle.batch_no
            INNER JOIN `tabItem` item   ON item.item_code = sle.item_code
            WHERE sle.is_cancelled = 0
              AND item.custom_item_type IN ('Collar', 'Cuff')
              AND batch.custom_parent_batch IN %(batch_nos)s
            GROUP BY batch.custom_parent_batch, item.custom_item_type, batch.batch_status
            HAVING qty > 0
            """,
            {"batch_nos": batch_nos},
            as_dict=True,
        )
        for r in cc_rows:
            entry = collar_cuff_by_batch.setdefault(
                r["parent_batch"],
                {"collar_qty": 0, "collar_status": None, "cuff_qty": 0, "cuff_status": None},
            )
            if r["item_type"] == "Collar":
                entry["collar_qty"] = flt(entry["collar_qty"]) + flt(r["qty"])
                entry["collar_status"] = r["batch_status"]
            else:
                entry["cuff_qty"] = flt(entry["cuff_qty"]) + flt(r["qty"])
                entry["cuff_status"] = r["batch_status"]

    rows = []
    for r in fabric_rows:
        cc = collar_cuff_by_batch.get(r["batch_no"], {})
        rows.append({
            "commercial_name": r["commercial_name"],
            "color": r["color"],
            "width": r["width"],
            "batch_no": r["batch_no"],
            "batch_status": r["batch_status"],
            "parentwarehouse": r["parentwarehouse"],
            "actual_qty": flt(r["actual_qty"]),
            "stock_uom": r["stock_uom"],
            "collar_qty": flt(cc.get("collar_qty", 0)),
            "collar_status": cc.get("collar_status"),
            "cuff_qty": flt(cc.get("cuff_qty", 0)),
            "cuff_status": cc.get("cuff_status"),
        })

    _cache_set(key, rows)
    return rows


@frappe.whitelist()
def check_app_permission():
    return "System Manager" in frappe.get_roles()
