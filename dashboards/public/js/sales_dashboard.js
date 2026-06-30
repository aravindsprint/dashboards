/* ──────────────────────────────────────────────────────────────
   Sales Dashboard — Vue 3 + Chart.js
   Works in BOTH contexts:
     1. Frappe Desk page (/app/dashboards-sales) → uses frappe.call
     2. PWA www page (/dashboards-sales)          → uses fetch GET
────────────────────────────────────────────────────────────── */
(function () {
  const { createApp, ref, computed, onMounted, nextTick } = Vue;

  /* ── API: auto-detect desk vs www context ───────────────────── */
  function call(method, args) {
    const fullMethod = "dashboards.api.sales_api." + method;

    // Desk context: frappe object is available
    if (window.frappe && frappe.call) {
      return new Promise((res, rej) => {
        frappe.call({
          method: fullMethod,
          args: args || {},
          callback: (r) => (r && r.message !== undefined ? res(r.message) : rej(r)),
          error: rej,
        });
      });
    }

    // WWW / PWA context: plain fetch GET (no CSRF needed for whitelisted GET)
    const params = new URLSearchParams();
    for (const [k, v] of Object.entries(args || {})) {
      if (v !== null && v !== undefined && v !== "") params.set(k, String(v));
    }
    const url = "/api/method/" + fullMethod +
      (params.toString() ? "?" + params.toString() : "");
    return fetch(url, {
      method: "GET",
      credentials: "same-origin",
      headers: { "Accept": "application/json" },
    })
      .then(r => r.json())
      .then(r => {
        if (r.message !== undefined) return r.message;
        throw new Error(r.exc || r._server_messages || "API error");
      });
  }

  function todayStr() {
    if (window.frappe && frappe.datetime) return frappe.datetime.get_today();
    return new Date().toISOString().split("T")[0];
  }

  function subMonths(dateStr, n) {
    const d = new Date(dateStr);
    d.setMonth(d.getMonth() - n);
    return d.toISOString().split("T")[0];
  }

  function subDays(dateStr, n) {
    const d = new Date(dateStr);
    d.setDate(d.getDate() - n);
    return d.toISOString().split("T")[0];
  }

  function startOfWeek(dateStr) {
    const d = new Date(dateStr);
    const day = d.getDay(); // 0=Sun, 1=Mon
    d.setDate(d.getDate() - (day === 0 ? 6 : day - 1)); // Monday
    return d.toISOString().split("T")[0];
  }

  function startOfMonth(dateStr) {
    const d = new Date(dateStr);
    d.setDate(1);
    return d.toISOString().split("T")[0];
  }

  function startOfQuarter(dateStr) {
    const d = new Date(dateStr);
    const q = Math.floor(d.getMonth() / 3);
    d.setMonth(q * 3);
    d.setDate(1);
    return d.toISOString().split("T")[0];
  }

  function startOfYear(dateStr) {
    const d = new Date(dateStr);
    d.setMonth(0);
    d.setDate(1);
    return d.toISOString().split("T")[0];
  }

  function startOfFiscalYear(dateStr) {
    // India fiscal year: April 1 – March 31
    const d = new Date(dateStr);
    const month = d.getMonth(); // 0-indexed
    // If Jan–Mar, fiscal year started previous year April 1
    const fyYear = month < 3 ? d.getFullYear() - 1 : d.getFullYear();
    return `${fyYear}-04-01`;
  }

  /* ── chart registry ─────────────────────────────────────────── */
  const CH = {};
  const kill = (id) => { if (CH[id]) { CH[id].destroy(); delete CH[id]; } };

  /* ── colour maps ────────────────────────────────────────────── */
  const SI_COL = {
    Paid: "#2E7D32", Unpaid: "#1565C0", "Partly Paid": "#F57C00",
    Overdue: "#C62828", Return: "#6A1B9A", "Credit Note Issued": "#AD1457",
    Cancelled: "#78909C", Draft: "#90A4AE"
  };
  const SO_COL = {
    Completed: "#2E7D32", "To Deliver and Bill": "#1565C0",
    "To Bill": "#0097A7", "To Deliver": "#F57C00",
    Cancelled: "#78909C", Draft: "#90A4AE", Closed: "#546E7A"
  };
  const DEL_COL = {
    "Fully Delivered": "#2E7D32", "Partly Delivered": "#F57C00",
    "Not Delivered": "#C62828"
  };

  const siColor  = (s) => SI_COL[s]  || "#607D8B";
  const soColor  = (s) => SO_COL[s]  || "#607D8B";
  const delColor = (s) => DEL_COL[s] || "#90A4AE";

  /* ── Vue app ────────────────────────────────────────────────── */
  createApp({
    setup() {
      const today = todayStr();
      const DEFAULT_COMPANY = "Pranera Services and Solutions Pvt. Ltd.,";
      // Default: Today
      const filters = ref({ from_date: today, to_date: today, company: "" });
      const activeRange = ref("Today");
      const quickRanges = [
        { label: "Today",     fn: (t) => ({ from: t,                  to: t                  }) },
        { label: "Yesterday", fn: (t) => ({ from: subDays(t, 1),     to: subDays(t, 1)      }) },
        { label: "1W",        fn: (t) => ({ from: subDays(t, 7),     to: t                  }) },
        { label: "This Week", fn: (t) => ({ from: startOfWeek(t),    to: t                  }) },
        { label: "1M",        fn: (t) => ({ from: subMonths(t, 1),   to: t                  }) },
        { label: "This Month",fn: (t) => ({ from: startOfMonth(t),   to: t                  }) },
        { label: "3M",        fn: (t) => ({ from: subMonths(t, 3),   to: t                  }) },
        { label: "This Qtr",  fn: (t) => ({ from: startOfQuarter(t), to: t                  }) },
        { label: "6M",        fn: (t) => ({ from: subMonths(t, 6),   to: t                  }) },
        { label: "1Y",        fn: (t) => ({ from: subMonths(t, 12),  to: t                  }) },
        { label: "This Year", fn: (t) => ({ from: startOfYear(t),    to: t                  }) },
        { label: "Fiscal Yr",  fn: (t) => ({ from: startOfFiscalYear(t), to: t              }) },
      ];

      const loading   = ref(true);
      const companies = ref([]);
      const activeTab = ref("overview");
      const txSearch  = ref("");

      const tabs = [
        { key: "overview",        icon: "📊", label: "Overview" },
        { key: "invoices",        icon: "🧾", label: "Sales Invoices" },
        { key: "orders",          icon: "📦", label: "Sales Orders" },
        { key: "commercial_name", icon: "🏷️",  label: "Commercial Name" },
        { key: "uom",             icon: "📐", label: "UOM" },
        { key: "state",           icon: "🗺️",  label: "State" },
        { key: "salesperson",     icon: "👤", label: "Sales Person" },
        { key: "cost_center",     icon: "🏢", label: "Cost Center" },
        { key: "naming_series",   icon: "🔖", label: "Naming Series" },
        { key: "transactions",    icon: "🔄", label: "Transactions" },
      ];

      const empty = {
        invoice: { total_invoiced: 0, total_collected: 0, total_outstanding: 0, collection_rate: 0, count: 0, status_breakdown: {} },
        order:   { total_ordered: 0, count: 0, status_breakdown: {}, delivery_breakdown: {} },
      };
      const summary        = ref({ ...empty });
      const trend          = ref({ invoices: [], orders: [] });
      const topCustomers   = ref({ by_invoice: [], by_order: [] });
      const commercialName = ref({ by_invoice: [], by_order: [] });
      const uomData        = ref({ by_invoice: [], by_order: [] });
      const stateData      = ref({ by_invoice: [], by_order: [] });
      const spData         = ref({ by_invoice: [], by_order: [] });
      const ccData         = ref({ by_invoice: [], by_order: [] });
      const nsData         = ref({ by_invoice: [], by_order: [] });
      const transactions   = ref([]);

      const filteredTransactions = computed(() => {
        if (!txSearch.value) return transactions.value;
        const q = txSearch.value.toLowerCase();
        return transactions.value.filter(t =>
          (t.customer || "").toLowerCase().includes(q) || (t.name || "").toLowerCase().includes(q)
        );
      });

      /* ── formatters ─────────────────────────────────────────── */
      function fmt(val) {
        const n = parseFloat(val) || 0;
        if (n >= 1e7) return "₹" + (n / 1e7).toFixed(2) + " Cr";
        if (n >= 1e5) return "₹" + (n / 1e5).toFixed(2) + " L";
        return "₹" + n.toLocaleString("en-IN", { maximumFractionDigits: 0 });
      }
      function fmtQty(v) {
        const n = parseFloat(v) || 0;
        if (n >= 1e5) return (n / 1e5).toFixed(1) + "L";
        if (n >= 1e3) return (n / 1e3).toFixed(1) + "K";
        return Math.round(n).toLocaleString();
      }
      function fmtDate(d) {
        if (!d) return "—";
        try { return new Date(d).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" }); }
        catch { return d; }
      }
      function pct(val, total) { return total ? Math.round((val / total) * 100) : 0; }
      function txLink(tx) {
        const dt = tx.type === "Invoice" ? "sales-invoice" : "sales-order";
        return `/app/${dt}/${tx.name}`;
      }
      function cleanName(s) {
        if (!s) return "—";
        return s.replace(/_/g, " ").replace(/\//g, " / ");
      }

      /* ── quick range ────────────────────────────────────────── */
      function applyRange(r) {
        activeRange.value = r.label;
        const t = todayStr();
        const range = r.fn ? r.fn(t) : { from: subDays(t, r.days || 30), to: t };
        filters.value.from_date = range.from;
        filters.value.to_date   = range.to;
        loadAll();
      }

      /* ── load data ──────────────────────────────────────────── */
      async function loadAll() {
        loading.value = true;
        Object.keys(CH).forEach(kill);
        const a = {
          from_date: filters.value.from_date,
          to_date:   filters.value.to_date,
          company:   filters.value.company,
        };
        try {
          const [s, t, tc, cn, uom, st, sp, cc, ns, tx] = await Promise.all([
            call("get_dashboard_summary",    a),
            call("get_monthly_trend",        { months: 6, company: a.company }),
            call("get_top_customers",        { ...a, limit: 10 }),
            call("get_commercial_name_wise", { ...a, limit: 15 }),
            call("get_uom_wise",             a),
            call("get_state_wise",           { ...a, limit: 15 }),
            call("get_salesperson_wise",     { ...a, limit: 15 }),
            call("get_cost_center_wise",     { ...a, limit: 15 }),
            call("get_naming_series_wise",   { ...a, limit: 20 }),
            call("get_recent_transactions",  { limit: 50, company: a.company }),
          ]);
          const EMPTY_BI = { by_invoice: [], by_order: [] };
          summary.value        = s   || { invoice: { total_invoiced:0, total_collected:0, total_outstanding:0, collection_rate:0, count:0, status_breakdown:{} }, order: { total_ordered:0, count:0, status_breakdown:{}, delivery_breakdown:{} } };
          trend.value          = t   || { invoices: [], orders: [] };
          topCustomers.value   = tc  || { ...EMPTY_BI };
          commercialName.value = cn  || { ...EMPTY_BI };
          uomData.value        = uom || { ...EMPTY_BI };
          stateData.value      = st  || { ...EMPTY_BI };
          spData.value         = sp  || { ...EMPTY_BI };
          const safeCc = cc || { ...EMPTY_BI };
          if (safeCc.by_invoice) safeCc.by_invoice.forEach(r => { r.cost_center = (r.cost_center || '').replace(/ - PSS$/i, '').trim(); });
          if (safeCc.by_order)   safeCc.by_order.forEach(r =>   { r.cost_center = (r.cost_center || '').replace(/ - PSS$/i, '').trim(); });
          ccData.value         = safeCc;
          nsData.value         = ns  || { ...EMPTY_BI };
          transactions.value   = Array.isArray(tx) ? tx : [];
        } catch (e) {
          console.error("Dashboard load error:", e);
          if (window.frappe && frappe.msgprint) {
            frappe.msgprint("Dashboard load failed — check console.");
          } else {
            alert("Dashboard load failed: " + e.message);
          }
        } finally {
          loading.value = false;
          await nextTick();
          buildCharts();
        }
      }

      async function loadFilterOptions() {
        try {
          const o = await call("get_filter_options", {});
          companies.value = o.companies || [];
          if (companies.value.includes(DEFAULT_COMPANY)) {
            filters.value.company = DEFAULT_COMPANY;
          } else if (companies.value.length > 0) {
            // Default not found — pick the first available company
            filters.value.company = companies.value[0];
          }
          await loadAll();
        } catch (e) { console.warn("Filter options failed:", e); }
      }

      /* ── chart builders ─────────────────────────────────────── */
      function buildCharts() {
        buildTrend();
        buildDonut("invoiceStatusChart", summary.value.invoice.status_breakdown, siColor);
        buildDonut("deliveryStatusChart", summary.value.order.delivery_breakdown, delColor);
        buildHBar("topCustSIChart", topCustomers.value.by_invoice, "revenue",      "#1565C0", "customer");
        buildHBar("topCustSOChart", topCustomers.value.by_order,   "order_value",  "#0097A7", "customer");
        buildHBar("cnSIChart",  commercialName.value.by_invoice, "revenue",     "#1565C0", "commercial_name", true);
        buildHBar("cnSOChart",  commercialName.value.by_order,   "order_value", "#0097A7", "commercial_name", true);
        buildUOMCharts();
        buildHBar("stateSIChart", stateData.value.by_invoice, "revenue",     "#1565C0", "state");
        buildHBar("stateSOChart", stateData.value.by_order,   "order_value", "#0097A7", "state");
        buildHBar("spSIChart", spData.value.by_invoice, "revenue",     "#1565C0", "sales_person");
        buildHBar("spSOChart", spData.value.by_order,   "order_value", "#0097A7", "sales_person");
        buildHBar("ccSIChart", ccData.value.by_invoice, "revenue",     "#1565C0", "cost_center");
        buildHBar("ccSOChart", ccData.value.by_order,   "order_value", "#0097A7", "cost_center");
        buildHBar("nsSIChart", nsData.value.by_invoice, "revenue",     "#1565C0", "naming_series");
        buildHBar("nsSOChart", nsData.value.by_order,   "order_value", "#0097A7", "naming_series");
      }

      function buildTrend() {
        const el = document.getElementById("trendChart"); if (!el) return;
        const siMap = {}, soMap = {};
        (trend.value.invoices || []).forEach(r => siMap[r.month] = parseFloat(r.total) || 0);
        (trend.value.orders   || []).forEach(r => soMap[r.month] = parseFloat(r.total) || 0);
        const months = [...new Set([...Object.keys(siMap), ...Object.keys(soMap)])].sort();
        kill("trendChart");
        CH["trendChart"] = new Chart(el, {
          type: "bar",
          data: {
            labels: months.map(m => {
              const [y, mo] = m.split("-");
              return new Date(parseInt(y), parseInt(mo) - 1, 1)
                .toLocaleDateString("en-IN", { month: "short", year: "2-digit" });
            }),
            datasets: [
              { label: "Invoices", data: months.map(m => siMap[m] || 0), backgroundColor: "#1565C0cc", borderRadius: 4 },
              { label: "Orders",   data: months.map(m => soMap[m] || 0), backgroundColor: "#0097A7cc", borderRadius: 4 },
            ],
          },
          options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
              legend: { display: false },
              tooltip: { callbacks: { label: c => " ₹" + (c.parsed.y || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 }) } },
              datalabels: {
                anchor: "end", align: "top", offset: 6,
                font: { size: 10, weight: "700" }, color: "#111",
                backgroundColor: "rgba(255,255,255,0.9)",
                borderRadius: 4, padding: { top: 2, bottom: 2, left: 5, right: 5 },
                borderColor: "#ccc", borderWidth: 1,
                formatter: function(v) {
                  var n = parseFloat(v) || 0;
                  if (n === 0) return "";
                  if (n >= 1e7) return "Rs." + (n/1e7).toFixed(2) + "Cr";
                  if (n >= 1e5) return "Rs." + (n/1e5).toFixed(2) + "L";
                  return "Rs." + Math.round(n).toLocaleString("en-IN");
                },
              },
            },
            scales: {
              x: { grid: { display: false }, ticks: { font: { size: 11 } } },
              y: { grid: { color: "#f0f0f0" }, ticks: { font: { size: 11 }, callback: v => "₹" + (v >= 1e5 ? (v / 1e5).toFixed(1) + "L" : v.toLocaleString()) } },
            },
          },
        });
      }

      function buildDonut(id, breakdown, colorFn) {
        const el = document.getElementById(id); if (!el) return;
        const keys = Object.keys(breakdown || {}); if (!keys.length) return;
        kill(id);
        CH[id] = new Chart(el, {
          type: "doughnut",
          data: { labels: keys, datasets: [{ data: keys.map(k => breakdown[k]), backgroundColor: keys.map(colorFn), borderWidth: 2, borderColor: "#fff" }] },
          options: {
            responsive: true, maintainAspectRatio: false, cutout: "55%",
            plugins: {
              legend: { display: false },
              datalabels: {
                display: true,
                anchor: "center", align: "center",
                font: { size: 12, weight: "700" }, color: "#fff",
                textStrokeColor: "rgba(0,0,0,0.6)", textStrokeWidth: 3,
                formatter: function(value, ctx) {
                  var total = ctx.dataset.data.reduce(function(a,b){ return a+b; }, 0);
                  var pct = total ? Math.round(value / total * 100) : 0;
                  if (pct < 3) return "";
                  return value + " (" + pct + "%)";
                },
              },
            },
          },
        });
      }

      function buildHBar(id, data, valueKey, color, labelKey, cleanLabel = false) {
        const el = document.getElementById(id); if (!el || !data || !data.length) return;
        const top = data.slice(0, 10);
        const labels = top.map(r => {
          let n = r[labelKey] || "Unknown";
          if (cleanLabel) n = cleanName(n);
          return n.length > 22 ? n.substring(0, 22) + "…" : n;
        });
        kill(id);
        CH[id] = new Chart(el, {
          type: "bar",
          data: { labels, datasets: [{ label: "Value", data: top.map(r => parseFloat(r[valueKey]) || 0), backgroundColor: color + "cc", borderRadius: 4 }] },
          options: {
            indexAxis: "y", responsive: true, maintainAspectRatio: false,
            plugins: {
              legend: { display: false },
              tooltip: { callbacks: { label: c => " ₹" + (c.parsed.x || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 }) } },
              datalabels: {
                anchor: "end", align: "right", offset: 6,
                font: { size: 10, weight: "700" }, color: "#111",
                backgroundColor: "rgba(255,255,255,0.9)",
                borderRadius: 4, padding: { top: 2, bottom: 2, left: 5, right: 5 },
                borderColor: "#ccc", borderWidth: 1, clip: false,
                formatter: function(v) {
                  var n = parseFloat(v) || 0;
                  if (n === 0) return "";
                  if (n >= 1e7) return "Rs." + (n/1e7).toFixed(2) + "Cr";
                  if (n >= 1e5) return "Rs." + (n/1e5).toFixed(2) + "L";
                  return "Rs." + Math.round(n).toLocaleString("en-IN");
                },
              },
            },
            scales: {
              x: { grid: { color: "#f0f0f0" }, ticks: { font: { size: 10 }, callback: v => "₹" + (v >= 1e5 ? (v / 1e5).toFixed(1) + "L" : v.toLocaleString()) } },
              y: { grid: { display: false }, ticks: { font: { size: 11 } } },
            },
            layout: { padding: { right: 70 } },
          },
        });
      }

      function buildUOMCharts() {
        const build = (id, rows, valueKey, color) => {
          const el = document.getElementById(id); if (!el || !rows.length) return;
          kill(id);
          CH[id] = new Chart(el, {
            type: "bar",
            data: { labels: rows.map(r => r.uom || "N/A"), datasets: [{ label: "Value", data: rows.map(r => parseFloat(r[valueKey]) || 0), backgroundColor: color + "cc", borderRadius: 4 }] },
            options: {
              responsive: true, maintainAspectRatio: false,
              plugins: {
                legend: { display: false },
                datalabels: {
                  anchor: "end", align: "top", offset: 6,
                  font: { size: 10, weight: "700" }, color: "#111",
                  backgroundColor: "rgba(255,255,255,0.9)",
                  borderRadius: 4, padding: { top: 2, bottom: 2, left: 5, right: 5 },
                  borderColor: "#ccc", borderWidth: 1,
                  formatter: function(v) {
                    var n = parseFloat(v) || 0;
                    if (n === 0) return "";
                    if (n >= 1e7) return "Rs." + (n/1e7).toFixed(2) + "Cr";
                    if (n >= 1e5) return "Rs." + (n/1e5).toFixed(2) + "L";
                    return "Rs." + Math.round(n).toLocaleString("en-IN");
                  },
                },
              },
              scales: {
                x: { grid: { display: false }, ticks: { font: { size: 11 } } },
                y: { grid: { color: "#f0f0f0" }, ticks: { font: { size: 10 }, callback: v => "₹" + (v >= 1e5 ? (v / 1e5).toFixed(1) + "L" : v.toLocaleString()) } },
              },
              layout: { padding: { top: 20 } },
            },
          });
        };
        build("uomSIChart", (uomData.value.by_invoice || []).slice(0, 10), "revenue",     "#1565C0");
        build("uomSOChart", (uomData.value.by_order   || []).slice(0, 10), "order_value", "#0097A7");
      }

      onMounted(async () => {
        await loadFilterOptions();
      });



      /* ── table sort & filter ─────────────────────────────────── */
      const tableSort  = ref({});
      const filterText = ref({});

      function getSort(tableKey) {
        return tableSort.value[tableKey] || { col: null, dir: "asc" };
      }

      function toggleSort(tableKey, col) {
        const cur = getSort(tableKey);
        if (cur.col === col) {
          tableSort.value = { ...tableSort.value, [tableKey]: { col, dir: cur.dir === "asc" ? "desc" : "asc" } };
        } else {
          tableSort.value = { ...tableSort.value, [tableKey]: { col, dir: "asc" } };
        }
      }

      function sortedRows(tableKey, rows, numericCols) {
        if (!rows) return [];
        const { col, dir } = getSort(tableKey);
        const q = (filterText.value[tableKey] || "").toLowerCase();
        let out = rows;
        if (q) {
          out = rows.filter(r => Object.values(r).some(v => String(v || "").toLowerCase().includes(q)));
        }
        if (!col) return out;
        return [...out].sort((a, b) => {
          const av = a[col], bv = b[col];
          const isNum = numericCols && numericCols.includes(col);
          let cmp = isNum ? (parseFloat(av) || 0) - (parseFloat(bv) || 0)
                          : String(av || "").localeCompare(String(bv || ""));
          return dir === "asc" ? cmp : -cmp;
        });
      }

      function sortIcon(tableKey, col) {
        const { col: c, dir } = getSort(tableKey);
        if (c !== col) return "⇅";
        return dir === "asc" ? "↑" : "↓";
      }

      function sortIconActive(tableKey, col) {
        return getSort(tableKey).col === col;
      }

      /* ── drill-down state ───────────────────────────────────── */
      const drill = ref({ rowKey: null, tab: null, loading: false, rows: [], type: null });
      const drillCache = ref({});

      function isDrillOpen(tab, rowKey) {
        const k = tab + '::' + String(rowKey);
        if (drillCache.value[k] !== undefined) return true;
        return drill.value.tab === tab && drill.value.rowKey === rowKey;
      }

      function getDrillRows(tab, rowKey) {
        const k = tab + '::' + String(rowKey);
        if (drillCache.value[k] !== undefined) return drillCache.value[k];
        if (drill.value.tab === tab && drill.value.rowKey === rowKey) return drill.value.rows;
        return [];
      }

      function isDrillLoading(tab, rowKey) {
        const k = tab + '::' + String(rowKey);
        if (drillCache.value[k] !== undefined) return false;
        return drill.value.tab === tab && drill.value.rowKey === rowKey && drill.value.loading;
      }

      async function toggleDrill(tab, rowKey, drillType, args) {
        const k = tab + '::' + String(rowKey);
        if (drillCache.value[k] !== undefined) {
          const c = { ...drillCache.value }; delete c[k]; drillCache.value = c; return;
        }
        if (drill.value.rowKey === rowKey && drill.value.tab === tab) {
          drill.value = { rowKey: null, tab: null, loading: false, rows: [], type: null }; return;
        }
        drill.value = { rowKey, tab, loading: true, rows: [], type: drillType };
        try {
          const rows = await call("get_drill_down", {
            drill_type: drillType, ...args,
            from_date: filters.value.from_date,
            to_date:   filters.value.to_date,
            company:   filters.value.company,
          });
          drill.value = { rowKey, tab, loading: false, rows: rows || [], type: drillType };
        } catch(e) {
          drill.value = { rowKey, tab, loading: false, rows: [], type: drillType };
        }
      }

      async function expandAll(tabKey, rows, drillType, keyField, argsBuilder) {
        for (const row of rows) {
          const rk = row[keyField];
          const k  = tabKey + '::' + String(rk);
          if (!isDrillOpen(tabKey, rk)) {
            try {
              const res = await call("get_drill_down", {
                drill_type: drillType, ...argsBuilder(row),
                from_date: filters.value.from_date,
                to_date:   filters.value.to_date,
                company:   filters.value.company,
              });
              drillCache.value = { ...drillCache.value, [k]: res || [] };
            } catch(e) { drillCache.value = { ...drillCache.value, [k]: [] }; }
          }
        }
      }

      function collapseAll(tabKey) {
        const c = { ...drillCache.value };
        Object.keys(c).forEach(k => { if (k.startsWith(tabKey + '::')) delete c[k]; });
        drillCache.value = c;
        if (drill.value.tab === tabKey) drill.value = { rowKey: null, tab: null, loading: false, rows: [], type: null };
      }

      return {
        filters, activeRange, quickRanges, loading, companies,
        activeTab, tabs, txSearch,
        summary, trend, topCustomers,
        drill, drillCache, isDrillOpen, getDrillRows, isDrillLoading, toggleDrill, expandAll, collapseAll,
        tableSort, filterText, getSort, toggleSort, sortedRows, sortIcon, sortIconActive,
        commercialName, uomData, stateData, spData, ccData, nsData, transactions,
        filteredTransactions,
        fmt, fmtQty, fmtDate, pct, txLink, cleanName,
        applyRange, loadAll,
        siColor, soColor, delColor,
      };
    },
  }).mount("#sales-dashboard-app");
})();
