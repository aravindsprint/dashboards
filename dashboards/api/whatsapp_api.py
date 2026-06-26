# apps/dashboards/dashboards/api/whatsapp_api.py

import frappe
import json
import requests
from datetime import datetime, timedelta
from frappe.utils import today, add_days, flt

CACHE_KEY_CONFIG = "wa_dashboard_config"
CACHE_KEY_LOG    = "wa_dashboard_log"

def _get_cache(key, default=None):
    try:
        val = frappe.cache().get_value(key)
        if val:
            return json.loads(val) if isinstance(val, str) else val
    except Exception:
        pass
    return default

def _set_cache(key, value):
    frappe.cache().set_value(key, json.dumps(value, default=str))


# ── Config ───────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_config():
    return _get_cache(CACHE_KEY_CONFIG, {})

@frappe.whitelist()
def save_config(config=None):
    if isinstance(config, str):
        config = json.loads(config)
    _set_cache(CACHE_KEY_CONFIG, config or {})
    return {"success": True}


# ── Send log ─────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_send_log():
    logs = _get_cache(CACHE_KEY_LOG, [])
    return sorted(logs, key=lambda x: x.get("time",""), reverse=True)[:50]

def _append_log(entry):
    logs = _get_cache(CACHE_KEY_LOG, [])
    logs.append(entry)
    _set_cache(CACHE_KEY_LOG, logs[-200:])


# ── Formatter ────────────────────────────────────────────────────────────────

def _fmt(v):
    v = flt(v)
    if v >= 1e7:  return f"Rs.{v/1e7:.2f} Cr"
    if v >= 1e5:  return f"Rs.{v/1e5:.2f} L"
    if v < 0:     return f"Rs.{v:,.0f}"
    return f"Rs.{v:,.0f}"


# ── Summary for WhatsApp (mirrors Overview tab) ───────────────────────────────

@frappe.whitelist()
def get_summary_for_whatsapp(days=30, company=None):
    days = int(days or 30)
    to_date   = today()
    from_date = add_days(to_date, -days)

    cf     = "AND si.company=%s"    if company else ""
    cf_so  = "AND so.company=%s"    if company else ""
    cf_sii = "AND si.company=%s"    if company else ""
    p      = [from_date, to_date]   + ([company] if company else [])

    # ── SI KPIs ──────────────────────────────────────────────────
    si_row = frappe.db.sql(f"""
        SELECT
            COALESCE(SUM(grand_total), 0)         AS invoiced,
            COALESCE(SUM(outstanding_amount), 0)  AS outstanding,
            COUNT(name)                            AS cnt
        FROM `tabSales Invoice` si
        WHERE si.docstatus=1
          AND si.posting_date BETWEEN %s AND %s
          {cf}
    """, p, as_dict=True)[0]

    total_invoiced    = flt(si_row.invoiced)
    total_outstanding = flt(si_row.outstanding)
    total_collected   = total_invoiced - total_outstanding
    invoice_count     = int(si_row.cnt or 0)
    collection_rate   = round(total_collected / total_invoiced * 100, 2) if total_invoiced else 0

    # ── SO KPIs ──────────────────────────────────────────────────
    so_row = frappe.db.sql(f"""
        SELECT
            COALESCE(SUM(grand_total), 0)                                              AS ordered,
            COUNT(name)                                                                AS cnt,
            SUM(CASE WHEN delivery_status IN ('Not Delivered','Partly Delivered')
                     THEN 1 ELSE 0 END)                                               AS to_deliver,
            SUM(CASE WHEN delivery_status='Fully Delivered' THEN 1 ELSE 0 END)        AS full_del,
            SUM(CASE WHEN status='Completed' THEN 1 ELSE 0 END)                       AS completed
        FROM `tabSales Order` so
        WHERE so.docstatus=1
          AND so.transaction_date BETWEEN %s AND %s
          {cf_so}
    """, p, as_dict=True)[0]

    total_ordered    = flt(so_row.ordered)
    order_count      = int(so_row.cnt or 0)
    to_deliver       = int(so_row.to_deliver or 0)
    fully_delivered  = int(so_row.full_del or 0)
    completed_orders = int(so_row.completed or 0)

    # ── Cost Centers (item-level, matches dashboard) ──────────────
    cc_rows = frappe.db.sql(f"""
        SELECT
            sii.cost_center,
            COALESCE(SUM(sii.amount), 0)                                              AS revenue,
            COALESCE(
                SUM(si.grand_total - si.outstanding_amount)
                * SUM(sii.amount) / NULLIF(SUM(si.grand_total), 0), 0)               AS collected,
            COUNT(DISTINCT si.name)                                                   AS invoices
        FROM `tabSales Invoice Item` sii
        JOIN `tabSales Invoice` si ON si.name = sii.parent
        WHERE si.docstatus=1
          AND si.posting_date BETWEEN %s AND %s
          {cf_sii}
          AND sii.cost_center IS NOT NULL
          AND sii.cost_center != ''
        GROUP BY sii.cost_center
        ORDER BY revenue DESC
        LIMIT 10
    """, p, as_dict=True)

    cost_centers = []
    for r in cc_rows:
        rev  = flt(r.revenue)
        col  = flt(r.collected)
        pct  = round(col / rev * 100) if rev else 0
        name = (r.cost_center or "").replace(" - PSS", "").strip()
        cost_centers.append({
            "name":      name,
            "revenue":   _fmt(rev),
            "collected": _fmt(col),
            "pct":       pct,
            "invoices":  int(r.invoices or 0),
        })

    return {
        "from_date":             from_date,
        "to_date":               to_date,
        "total_invoiced_fmt":    _fmt(total_invoiced),
        "total_collected_fmt":   _fmt(total_collected),
        "total_outstanding_fmt": _fmt(total_outstanding),
        "collection_rate":       collection_rate,
        "invoice_count":         invoice_count,
        "total_ordered_fmt":     _fmt(total_ordered),
        "order_count":           order_count,
        "to_deliver":            to_deliver,
        "fully_delivered":       fully_delivered,
        "completed_orders":      completed_orders,
        "cost_centers":          cost_centers,
        # alias kept for template compat
        "total_invoiced":        total_invoiced,
    }


# ── Build message text (matches the screenshot layout) ───────────────────────

def _build_message(s, footer="Pranera ERP · Auto Report"):
    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━",
        "📊 *Pranera Sales Report*",
        f"_{s.get('from_date','')} → {s.get('to_date','')}_",
        "━━━━━━━━━━━━━━━━━━━━━━",
        "",
        "🧾 *SALES INVOICES*",
        f"• Total Invoiced : *{s.get('total_invoiced_fmt','—')}*  ({s.get('invoice_count',0)} invoices)",
        f"• Collected      : *{s.get('total_collected_fmt','—')}*",
        f"• Outstanding    : *{s.get('total_outstanding_fmt','—')}*",
        f"• Collection Rate: *{s.get('collection_rate',0)}%*",
        "",
    ]

    # Cost Centers table
    ccs = s.get("cost_centers", [])
    if ccs:
        lines.append("🏢 *COST CENTERS*")
        for i, cc in enumerate(ccs, 1):
            bar_filled = round(cc['pct'] / 10)
            bar = "█" * bar_filled + "░" * (10 - bar_filled)
            lines.append(
                f"{i}. *{cc['name']}*\n"
                f"   Revenue: {cc['revenue']}  |  Collected: {cc['collected']}\n"
                f"   [{bar}] {cc['pct']}%  •  {cc['invoices']} invoices"
            )
        lines.append("")

    lines += [
        "📦 *SALES ORDERS*",
        f"• Total Ordered  : *{s.get('total_ordered_fmt','—')}*  ({s.get('order_count',0)} orders)",
        f"• To Deliver     : *{s.get('to_deliver',0)}*",
        f"• Fully Delivered: *{s.get('fully_delivered',0)}*",
        f"• Completed      : *{s.get('completed_orders',0)}*",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━",
        f"_{footer}_",
    ]
    return "\n".join(lines)


# ── Send single message via Meta Graph API ────────────────────────────────────

def _send_single(phone, summary, cfg):
    token    = cfg.get("token", "")
    phone_id = cfg.get("phoneId", "")
    version  = cfg.get("apiVersion", "v22.0")
    template = cfg.get("templateName", "")
    lang     = cfg.get("languageCode", "en")
    footer   = cfg.get("messageFooter", "Pranera ERP · Auto Report")

    if not token or not phone_id:
        return {"status": "failed", "error": "Missing token or phoneId in config"}

    api_url = f"https://graph.facebook.com/{version}/{phone_id}/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    s = summary

    # Build cost-center block as a single text param
    cc_text = ""
    for i, cc in enumerate(s.get("cost_centers", []), 1):
        cc_text += f"\n{i}. {cc['name']}: {cc['revenue']} | {cc['pct']}% collected"

    if template:
        # Meta template with variables — template body must use {{1}}…{{n}}
        # Single-param approach: pass the full pre-built message as {{1}}
        full_msg = _build_message(s, footer)
        body = {
            "messaging_product": "whatsapp",
            "to": str(phone),
            "type": "template",
            "template": {
                "name": template,
                "language": {"code": lang},
                "components": [{
                    "type": "body",
                    "parameters": [{"type": "text", "text": full_msg}],
                }],
            },
        }
    else:
        # Freeform text — only works within 24-hr window
        body = {
            "messaging_product": "whatsapp",
            "to": str(phone),
            "type": "text",
            "text": {"body": _build_message(s, footer)},
        }

    try:
        resp = requests.post(api_url, json=body, headers=headers, timeout=30)
        data = resp.json()
        if resp.ok and data.get("messages"):
            return {"status": "success", "messageId": data["messages"][0]["id"]}
        err = data.get("error", {})
        return {"status": "failed", "error": f"{err.get('message', str(data))} (code {err.get('code','')})"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


# ── Main send endpoint ────────────────────────────────────────────────────────

@frappe.whitelist()
def send_whatsapp_report(recipients=None, summary=None, config=None, trigger="manual"):
    if isinstance(recipients, str): recipients = json.loads(recipients)
    if isinstance(summary, str):    summary    = json.loads(summary)
    if isinstance(config, str):     config     = json.loads(config)

    recipients = recipients or []
    summary    = summary    or {}
    cfg        = config     or {}

    total, success, failed = 0, 0, 0
    details = []

    for r in recipients:
        phone = str(r.get("phone", "")).strip()
        if not phone:
            continue
        total += 1
        result = _send_single(phone, summary, cfg)
        if result["status"] == "success":
            success += 1
        else:
            failed += 1
        details.append({"phone": phone, "name": r.get("name", ""), **result})

    _append_log({
        "id":      str(int(datetime.now().timestamp())),
        "time":    datetime.now().isoformat(),
        "trigger": trigger,
        "total":   total,
        "success": success,
        "failed":  failed,
        "status":  "completed",
    })

    return {"total": total, "success": success, "failed": failed, "details": details}


# ── Frappe scheduled job ──────────────────────────────────────────────────────

def run_scheduled_whatsapp():
    cfg = _get_cache(CACHE_KEY_CONFIG, {})
    if not cfg or not cfg.get("enabled"):
        return

    try:
        import pytz
        tz  = pytz.timezone(cfg.get("timezone", "Asia/Kolkata"))
        now = datetime.now(tz)
    except Exception:
        now = datetime.now()

    day_map   = {0:"mon",1:"tue",2:"wed",3:"thu",4:"fri",5:"sat",6:"sun"}
    today_key = day_map[now.weekday()]
    if today_key not in (cfg.get("scheduleDays") or []):
        return

    current_hm = now.strftime("%H:%M")
    matched = False
    for t in (cfg.get("scheduleTimes") or []):
        try:
            sh, sm = map(int, t.split(":"))
            ch, cm = map(int, current_hm.split(":"))
            if abs((ch * 60 + cm) - (sh * 60 + sm)) <= 2:
                matched = True
                break
        except Exception:
            pass

    if not matched:
        return

    try:
        summary = get_summary_for_whatsapp(
            days=int(cfg.get("dateRangeDays", 30)),
            company=cfg.get("company") or None
        )
    except Exception as e:
        frappe.log_error(f"WhatsApp scheduler: summary fetch failed — {e}")
        return

    active = [r for r in (cfg.get("recipients") or []) if r.get("active")]
    if not active:
        return

    try:
        send_whatsapp_report(
            recipients=active,
            summary=summary,
            config=cfg,
            trigger="scheduled"
        )
    except Exception as e:
        frappe.log_error(f"WhatsApp scheduler: send failed — {e}")
