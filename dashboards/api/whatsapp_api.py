# apps/dashboards/dashboards/api/whatsapp_api.py

import frappe
import json
import requests
from datetime import datetime
from frappe.utils import today, add_days, flt

CACHE_KEY_CONFIG = "wa_dashboard_config"
CACHE_KEY_LOG    = "wa_dashboard_log"


# ── Storage (Redis cache) ─────────────────────────────────────────────────────

def _config_path():
    import os
    return os.path.join(frappe.get_site_path(), "wa_config.json")

def _get_cache(key, default=None):
    # Primary: persistent JSON file (survives bench restart & deploys)
    try:
        import os
        path = _config_path()
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
            if key in data:
                return data[key]
    except Exception:
        pass
    # Fallback: Redis
    try:
        val = frappe.cache().get_value(key)
        if val:
            return json.loads(val) if isinstance(val, str) else val
    except Exception:
        pass
    return default

def _set_cache(key, value):
    # Primary: write to persistent JSON file
    try:
        import os
        path = _config_path()
        data = {}
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
        data[key] = value
        with open(path, "w") as f:
            json.dump(data, f, default=str, indent=2)
    except Exception as e:
        frappe.log_error(f"wa_config write: {e}")
    # Also update Redis for fast access
    try:
        frappe.cache().set_value(key, json.dumps(value, default=str))
    except Exception:
        pass


# ── Config endpoints ──────────────────────────────────────────────────────────

@frappe.whitelist()
def get_config():
    return _get_cache(CACHE_KEY_CONFIG, {})


@frappe.whitelist()
def save_config(config=None):
    try:
        if isinstance(config, str):
            config = json.loads(config)
    except Exception as e:
        frappe.throw(f"Invalid config JSON: {e}")
    _set_cache(CACHE_KEY_CONFIG, config or {})
    return {"success": True}


# ── Send log ──────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_send_log():
    logs = _get_cache(CACHE_KEY_LOG, [])
    return sorted(logs, key=lambda x: x.get("time", ""), reverse=True)[:50]


def _append_log(entry):
    logs = _get_cache(CACHE_KEY_LOG, [])
    logs.append(entry)
    _set_cache(CACHE_KEY_LOG, logs[-200:])


# ── Formatter ─────────────────────────────────────────────────────────────────

def _fmt(v):
    v = flt(v)
    if v >= 1e7: return f"Rs.{v/1e7:.2f} Cr"
    if v >= 1e5: return f"Rs.{v/1e5:.2f} L"
    if v < 0:    return f"Rs.{v:,.0f}"
    return f"Rs.{v:,.0f}"


# ── Dashboard summary (mirrors Overview tab) ──────────────────────────────────

@frappe.whitelist()
def get_summary_for_whatsapp(days=30, company=None):
    # Default to primary company if not specified
    if not company:
        company = frappe.defaults.get_global_default("company") or None
    days = int(days or 30)
    # Use IST timezone for today to match dashboard
    try:
        import pytz
        from datetime import datetime as dt
        ist = pytz.timezone("Asia/Kolkata")
        to_date   = dt.now(ist).strftime("%Y-%m-%d")
        from_date = to_date if days == 1 else add_days(to_date, -days)
    except Exception:
        to_date   = today()
        from_date = to_date if days == 1 else add_days(to_date, -days)

    cf    = "AND si.company=%s" if company else ""
    cf_so = "AND so.company=%s" if company else ""
    p     = [from_date, to_date] + ([company] if company else [])

    # Sales Invoice KPIs — same as dashboard (docstatus=1 only)
    si = frappe.db.sql(f"""
        SELECT
            COALESCE(SUM(grand_total), 0)        AS invoiced,
            COALESCE(SUM(outstanding_amount), 0) AS outstanding,
            COUNT(name)                           AS cnt
        FROM `tabSales Invoice` si
        WHERE si.docstatus=1
          AND si.posting_date BETWEEN %s AND %s {cf}
    """, p, as_dict=True)[0]

    total_invoiced    = flt(si.invoiced)
    total_outstanding = flt(si.outstanding)
    total_collected   = total_invoiced - total_outstanding
    invoice_count     = int(si.cnt or 0)
    collection_rate   = round(total_collected / total_invoiced * 100, 2) if total_invoiced else 0

    # Sales Order KPIs
    so = frappe.db.sql(f"""
        SELECT
            COALESCE(SUM(grand_total), 0)                                          AS ordered,
            COUNT(name)                                                            AS cnt,
            SUM(CASE WHEN delivery_status IN ('Not Delivered','Partly Delivered')
                     THEN 1 ELSE 0 END)                                           AS to_deliver,
            SUM(CASE WHEN delivery_status='Fully Delivered' THEN 1 ELSE 0 END)    AS full_del,
            SUM(CASE WHEN status='Completed' THEN 1 ELSE 0 END)                   AS completed
        FROM `tabSales Order` so
        WHERE so.docstatus=1
          AND so.transaction_date BETWEEN %s AND %s {cf_so}
    """, p, as_dict=True)[0]

    total_ordered    = flt(so.ordered)
    order_count      = int(so.cnt or 0)
    to_deliver       = int(so.to_deliver or 0)
    fully_delivered  = int(so.full_del or 0)
    completed_orders = int(so.completed or 0)

    # Cost Centers (item-level)
    cc_rows = frappe.db.sql(f"""
        SELECT
            sii.cost_center,
            COALESCE(SUM(sii.amount), 0)                                           AS revenue,
            COALESCE(
                SUM(si.grand_total - si.outstanding_amount)
                * SUM(sii.amount) / NULLIF(SUM(si.grand_total), 0), 0)            AS collected,
            COUNT(DISTINCT si.name)                                                AS invoices
        FROM `tabSales Invoice Item` sii
        JOIN `tabSales Invoice` si ON si.name = sii.parent
        WHERE si.docstatus=1
          AND si.posting_date BETWEEN %s AND %s {cf}
          AND sii.cost_center IS NOT NULL AND sii.cost_center != ''
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
        "total_invoiced":        total_invoiced,
    }


# ── Build {{1}}...{{12}} params for Meta template ─────────────────────────────
#
#  Meta template body (sales_summary):
#
#  📊 *Pranera Sales Report*
#  _{{1}}_
#  *Invoices*
#  - Total Invoiced: *{{2}}*
#  - Collected: *{{3}}*
#  - Outstanding: *{{4}}*
#  - Collection Rate: *{{5}}%*
#  - Count: {{6}} invoices
#  *Cost Centers*
#  {{7}}
#  *Orders*
#  - Total Ordered: *{{8}}*
#  - Count: {{9}} orders
#  - To Deliver: *{{10}}*
#  - Completed: *{{11}}*
#  _{{12}}_
#
#  RULES Meta enforces on parameter text:
#    - No newlines (\n) or tabs (\t)
#    - No more than 4 consecutive spaces
#    - ASCII only (no unicode arrows, bullets, dashes)

def _build_template_params(s, footer="Pranera ERP - Auto Report"):
    """
    Build parameters for sales_summary_v2 template (17 variables):
      {{1}}  date range
      {{2}}  total invoiced
      {{3}}  collected
      {{4}}  outstanding
      {{5}}  collection rate
      {{6}}  invoice count
      {{7}}–{{12}}  cost centers (one per line, up to 6)
      {{13}} total ordered
      {{14}} order count
      {{15}} to deliver
      {{16}} completed orders
      {{17}} footer
    """
    ccs = s.get("cost_centers", [])

    # Build up to 6 cost center lines — each as its own parameter
    def _cc_line(cc, i):
        name = cc["name"][:20] + ".." if len(cc["name"]) > 20 else cc["name"]
        return f"{i}. {name}: {cc['revenue']} | {cc['pct']}% ({cc['invoices']} inv)"

    cc_params = []
    for i in range(6):
        if i < len(ccs):
            cc_params.append(_cc_line(ccs[i], i + 1))
        else:
            cc_params.append("-")  # empty slot

    # Strip any non-ASCII characters from all values
    def _safe(v):
        if not v: return "-"
        return (str(v)
            .replace("→", "to")   # →
            .replace("·", "-")    # ·
            .replace("—", "-")    # —
            .replace("–", "-")    # –
            .replace("…", "...")) # …

    return [
        f"{s.get('from_date', '')} to {s.get('to_date', '')}",  # {{1}}
        _safe(s.get("total_invoiced_fmt")),                       # {{2}}
        _safe(s.get("total_collected_fmt")),                      # {{3}}
        _safe(s.get("total_outstanding_fmt")),                    # {{4}}
        str(s.get("collection_rate", 0)),                         # {{5}}
        str(s.get("invoice_count", 0)),                           # {{6}}
        cc_params[0],                                             # {{7}}  CC 1
        cc_params[1],                                             # {{8}}  CC 2
        cc_params[2],                                             # {{9}}  CC 3
        cc_params[3],                                             # {{10}} CC 4
        cc_params[4],                                             # {{11}} CC 5
        cc_params[5],                                             # {{12}} CC 6
        _safe(s.get("total_ordered_fmt")),                        # {{13}}
        str(s.get("order_count", 0)),                             # {{14}}
        str(s.get("to_deliver", 0)),                              # {{15}}
        str(s.get("completed_orders", 0)),                        # {{16}}
        _safe(footer),                                             # {{17}}
    ]


def _build_message(s, footer="Pranera ERP - Auto Report"):
    """Plain-text fallback used when no template name is configured."""
    ccs = s.get("cost_centers", [])
    cc_lines = []
    for i, cc in enumerate(ccs, 1):
        cc_lines.append(f"  {i}. {cc['name']}: {cc['revenue']} | {cc['pct']}%")
    cc_block = "\n".join(cc_lines) if cc_lines else "  -"

    return (
        f"Pranera Sales Report\n"
        f"{s.get('from_date','')} to {s.get('to_date','')}\n\n"
        f"Invoices\n"
        f"- Total Invoiced: {s.get('total_invoiced_fmt','-')}\n"
        f"- Collected: {s.get('total_collected_fmt','-')}\n"
        f"- Outstanding: {s.get('total_outstanding_fmt','-')}\n"
        f"- Collection Rate: {s.get('collection_rate',0)}%\n"
        f"- Count: {s.get('invoice_count',0)} invoices\n\n"
        f"Cost Centers\n{cc_block}\n\n"
        f"Orders\n"
        f"- Total Ordered: {s.get('total_ordered_fmt','-')}\n"
        f"- Count: {s.get('order_count',0)} orders\n"
        f"- To Deliver: {s.get('to_deliver',0)}\n"
        f"- Completed: {s.get('completed_orders',0)}\n\n"
        f"{footer}"
    )


# ── Send single message via Meta Graph API ────────────────────────────────────

def _send_single(phone, summary, cfg):
    token     = cfg.get("token", "")
    phone_id  = cfg.get("phoneId", "")
    version   = cfg.get("apiVersion", "v22.0")
    template  = cfg.get("templateName", "")
    lang      = cfg.get("languageCode", "en")
    footer    = cfg.get("messageFooter", "Pranera ERP - Auto Report")

    if not token or not phone_id:
        return {"status": "failed", "error": "Missing token or phoneId in config"}

    api_url = f"https://graph.facebook.com/{version}/{phone_id}/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    if template:
        params = _build_template_params(summary, footer)
        body = {
            "messaging_product": "whatsapp",
            "to": str(phone),
            "type": "template",
            "template": {
                "name": template,
                "language": {"code": lang},
                "components": [{
                    "type": "body",
                    "parameters": [{"type": "text", "text": p} for p in params],
                }],
            },
        }
    else:
        # Freeform text — only works within 24-hr customer service window
        body = {
            "messaging_product": "whatsapp",
            "to": str(phone),
            "type": "text",
            "text": {"body": _build_message(summary, footer)},
        }

    try:
        resp = requests.post(api_url, json=body, headers=headers, timeout=30)
        data = resp.json()
        if resp.ok and data.get("messages"):
            return {"status": "success", "messageId": data["messages"][0]["id"]}
        err = data.get("error", {})
        return {
            "status": "failed",
            "error": f"{err.get('message', str(data))} (code {err.get('code', '')})",
        }
    except Exception as e:
        return {"status": "failed", "error": str(e)}


# ── Main send endpoint ────────────────────────────────────────────────────────

@frappe.whitelist()
def send_whatsapp_report(recipients=None, summary=None, config=None, trigger="manual"):
    try:
        if isinstance(recipients, str): recipients = json.loads(recipients)
        if isinstance(summary, str):    summary    = json.loads(summary)
        if isinstance(config, str):     config     = json.loads(config)
    except Exception as e:
        frappe.throw(f"Invalid JSON parameter: {e}")

    recipients = recipients or []
    summary    = summary    or {}
    cfg        = config     or {}

    total, success, failed = 0, 0, 0
    details, errors = [], []

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
            errors.append(f"{phone}: {result.get('error', 'unknown')}")
        details.append({"phone": phone, "name": r.get("name", ""), **result})

    _append_log({
        "id":      str(int(datetime.now().timestamp())),
        "time":    datetime.now().isoformat(),
        "trigger": trigger,
        "total":   total,
        "success": success,
        "failed":  failed,
        "status":  "completed",
        "errors":  errors,
    })

    return {"total": total, "success": success, "failed": failed, "details": details}


# ── Frappe scheduled job (called every 5 min via hooks.py) ───────────────────

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

    # Check day
    day_map   = {0:"mon", 1:"tue", 2:"wed", 3:"thu", 4:"fri", 5:"sat", 6:"sun"}
    today_key = day_map[now.weekday()]
    if today_key not in (cfg.get("scheduleDays") or []):
        return

    # Check time (within 2-minute window)
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
            company=cfg.get("company") or None,
        )
    except Exception as e:
        frappe.log_error(f"WhatsApp scheduler: summary fetch failed - {e}")
        return

    active = [r for r in (cfg.get("recipients") or []) if r.get("active")]
    if not active:
        return

    try:
        send_whatsapp_report(
            recipients=active,
            summary=summary,
            config=cfg,
            trigger="scheduled",
        )
    except Exception as e:
        frappe.log_error(f"WhatsApp scheduler: send failed - {e}")


# ── Debug: test Meta API connection ──────────────────────────────────────────

@frappe.whitelist()
def test_whatsapp_connection():
    cfg      = _get_cache(CACHE_KEY_CONFIG, {})
    token    = cfg.get("token", "")
    phone_id = cfg.get("phoneId", "")
    version  = cfg.get("apiVersion", "v22.0")

    if not token or not phone_id:
        return {"error": "Missing token or phoneId in saved config"}

    try:
        resp = requests.get(
            f"https://graph.facebook.com/{version}/{phone_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        data = resp.json()
        return {
            "status_code":   resp.status_code,
            "ok":            resp.ok,
            "phone_id":      phone_id,
            "token_preview": token[:20] + "..." if token else "MISSING",
            "response":      data,
        }
    except Exception as e:
        return {"error": str(e)}


# ── Direct send: bypass saved config, pass params explicitly ─────────────────

@frappe.whitelist()
def direct_send(phone, token, phone_id, template_name, days=30,
                language_code="en", api_version="v22.0",
                message_footer="Pranera ERP - Auto Report", company=None):
    """Send directly without relying on saved config. Useful for testing."""
    cfg = {
        "token":         token,
        "phoneId":       phone_id,
        "templateName":  template_name,
        "languageCode":  language_code,
        "apiVersion":    api_version,
        "messageFooter": message_footer,
    }
    summary = get_summary_for_whatsapp(days=int(days), company=company or None)
    result  = _send_single(str(phone), summary, cfg)

    _append_log({
        "id":      str(int(datetime.now().timestamp())),
        "time":    datetime.now().isoformat(),
        "trigger": "direct_test",
        "total":   1,
        "success": 1 if result["status"] == "success" else 0,
        "failed":  0 if result["status"] == "success" else 1,
        "status":  "completed",
        "errors":  [] if result["status"] == "success" else [f"{phone}: {result.get('error', '')}"],
    })
    return result
