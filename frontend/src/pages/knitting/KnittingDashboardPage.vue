<template>
<div id="knitting-dashboard-app">

  <!-- Header (same layout as the Sales Dashboard) -->
  <div class="kd-header">
    <div class="kd-header__left">
      <router-link to="/dashboard-app" class="kd-back" title="All Dashboards">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M10 3L5 8l5 5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </router-link>
      <svg width="26" height="26" viewBox="0 0 28 28" fill="none"><rect width="28" height="28" rx="6" fill="#F57C00"/><path d="M6 20 L10 13 L14 16 L18 8 L22 12" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/></svg>
      <div class="kd-title-group">
        <span class="kd-breadcrumb"><router-link to="/dashboard-app">Dashboards</router-link> /</span>
        <span class="kd-title">Knitting Dashboard</span>
      </div>
    </div>
    <div class="kd-header__right">
      <div class="kd-fg"><label class="kd-lbl">From</label><input type="date" v-model="filters.from_date" class="kd-input" @change="loadAll"/></div>
      <div class="kd-fg"><label class="kd-lbl">To</label><input type="date" v-model="filters.to_date" class="kd-input" @change="loadAll"/></div>
      <div class="kd-fg"><label class="kd-lbl">Company</label>
        <div class="kd-company-fixed">{{ COMPANY }}</div>
      </div>
      <div class="kd-ranges">
        <button v-for="r in quickRanges" :key="r.label" :class="['kd-range',{active:activeRange===r.label}]" @click="applyRange(r)">{{ r.label }}</button>
      </div>
    </div>
  </div>

  <!-- Tabs (add more entries to `tabs` below as the sections are defined) -->
  <div class="kd-tabs">
    <button v-for="t in tabs" :key="t.key" :class="['kd-tab',{active:activeTab===t.key}]" @click="activeTab=t.key">
      <span class="kd-tab-icon">{{ t.icon }}</span>{{ t.label }}
    </button>
  </div>

  <!-- Body -->
  <div v-show="activeTab==='overview'" class="kd-body">

    <div class="kd-section-title">Production summary</div>
    <div class="kd-cards">
      <div class="kd-card">
        <div class="kd-card-label">Fabric</div>
        <div class="kd-card-value">{{ fmtQty(summary.fabric.qty) }} <span class="kd-card-uom">{{ summary.fabric.uom }}</span></div>
        <div class="kd-card-sub">{{ summary.fabric.entries }} entries</div>
      </div>
      <div class="kd-card">
        <div class="kd-card-label">Collar</div>
        <div class="kd-card-value">{{ fmtQty(summary.collar.qty) }} <span class="kd-card-uom">{{ summary.collar.uom }}</span></div>
        <div class="kd-card-sub">{{ summary.collar.entries }} entries</div>
      </div>
      <div class="kd-card">
        <div class="kd-card-label">Cuff</div>
        <div class="kd-card-value">{{ fmtQty(summary.cuff.qty) }} <span class="kd-card-uom">{{ summary.cuff.uom }}</span></div>
        <div class="kd-card-sub">{{ summary.cuff.entries }} entries</div>
      </div>
    </div>

    <div class="kd-section-title">Item-wise breakdown</div>
    <KdTable :columns="itemColumns" :rows="itemRows" :empty-text="loaded ? 'No fabric, collar or cuff movement in this date range.' : 'Loading…'" />

  </div>

  <!-- Fabrics: production volume of all fabrics knitted (Roll doctype) -->
  <div v-show="activeTab==='fabrics'" class="kd-body">
    <div class="kd-section-title">Fabric production volume</div>
    <KdTable :columns="fabricColumns" :rows="fabricRows" :empty-text="loaded ? 'No rolls in this date range.' : 'Loading…'" />
  </div>

  <!-- Operators: skill level based on correct vs mistake qty (Roll doctype) -->
  <div v-show="activeTab==='operators'" class="kd-body">
    <div class="kd-section-title">Operator skill assessment</div>
    <KdTable :columns="operatorColumns" :rows="operatorRows" :empty-text="loaded ? 'No operator-logged rolls in this date range.' : 'Loading…'">
      <template #cell-skill_level="{ value }">
        <span :class="['kd-skill', skillClass(value)]">{{ value }}</span>
      </template>
    </KdTable>
  </div>

  <!-- Machines: output per knitting machine (Roll doctype) -->
  <div v-show="activeTab==='machines'" class="kd-body">
    <div class="kd-section-title">Machine output</div>
    <KdTable :columns="machineColumns" :rows="machineRows" :empty-text="loaded ? 'No machine-logged rolls in this date range.' : 'Loading…'" />
  </div>

  <!-- Monthly: total production by month (Roll doctype) -->
  <div v-show="activeTab==='monthly'" class="kd-body">
    <div class="kd-section-title">Monthly total production</div>
    <KdTable :columns="monthlyColumns" :rows="monthlyRows" :totals="monthlyTotals" :empty-text="loaded ? 'No rolls in this date range.' : 'Loading…'" />
  </div>

  <!-- Daily: Fabric (Kgs) / Collar / Cuffs (Pcs) per date, with grand totals -->
  <div v-show="activeTab==='daily'" class="kd-body">
    <div class="kd-section-title">Daily production — Body Fabric / Collar / Cuffs</div>
    <KdTable :columns="dailyColumns" :rows="dailyRows" :totals="dailyTotalsRow" :empty-text="loaded ? 'No fabric, collar or cuff movement in this date range.' : 'Loading…'" />
  </div>

</div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { call, todayStr } from '@/api/frappe'
import KdTable from '@/components/knitting/KdTable.vue'

/* ── date helpers (same as the Sales Dashboard) ───────────────── */
function fmtDate(d) {
  // local-date safe (toISOString would shift the day in +05:30)
  const y = d.getFullYear(), m = String(d.getMonth() + 1).padStart(2, '0'), day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}
function parse(s) { const [y, m, d] = s.split('-').map(Number); return new Date(y, m - 1, d) }
function subDays(s, n)   { const d = parse(s); d.setDate(d.getDate() - n); return fmtDate(d) }
function subMonths(s, n) { const d = parse(s); d.setMonth(d.getMonth() - n); return fmtDate(d) }
function startOfWeek(s)  { const d = parse(s); const day = d.getDay(); d.setDate(d.getDate() - (day === 0 ? 6 : day - 1)); return fmtDate(d) }
function startOfMonth(s) { const d = parse(s); d.setDate(1); return fmtDate(d) }
function startOfQuarter(s) { const d = parse(s); d.setMonth(Math.floor(d.getMonth() / 3) * 3); d.setDate(1); return fmtDate(d) }
function startOfYear(s)  { return `${parse(s).getFullYear()}-01-01` }
function startOfFiscalYear(s) {
  // India fiscal year: April 1 – March 31
  const d = parse(s)
  const fy = d.getMonth() < 3 ? d.getFullYear() - 1 : d.getFullYear()
  return `${fy}-04-01`
}

export default {
  name: 'KnittingDashboardPage',
  components: { KdTable },
  setup() {
    const today = todayStr()
    // Locked to this one company — no dropdown, matches every other tile on
    // the Overview screenshot you sent ("Pranera Services and Solutions Pvt. Ltd.,").
    const COMPANY = 'Pranera Services and Solutions Pvt. Ltd.,'

    const filters = ref({ from_date: today, to_date: today, company: COMPANY })
    const activeRange = ref('Today')
    const quickRanges = [
      { label: 'Today',      fn: (t) => ({ from: t,                     to: t }) },
      { label: 'Yesterday',  fn: (t) => ({ from: subDays(t, 1),         to: subDays(t, 1) }) },
      { label: '1W',         fn: (t) => ({ from: subDays(t, 7),         to: t }) },
      { label: 'This Week',  fn: (t) => ({ from: startOfWeek(t),        to: t }) },
      { label: '1M',         fn: (t) => ({ from: subMonths(t, 1),       to: t }) },
      { label: 'This Month', fn: (t) => ({ from: startOfMonth(t),       to: t }) },
      { label: '3M',         fn: (t) => ({ from: subMonths(t, 3),       to: t }) },
      { label: 'This Qtr',   fn: (t) => ({ from: startOfQuarter(t),     to: t }) },
      { label: '6M',         fn: (t) => ({ from: subMonths(t, 6),       to: t }) },
      { label: '1Y',         fn: (t) => ({ from: subMonths(t, 12),      to: t }) },
      { label: 'This Year',  fn: (t) => ({ from: startOfYear(t),        to: t }) },
      { label: 'Fiscal Yr',  fn: (t) => ({ from: startOfFiscalYear(t),  to: t }) },
    ]

    const tabs = [
      { key: 'overview',  label: 'Overview',  icon: '📊' },
      { key: 'fabrics',   label: 'Fabrics',   icon: '🧵' },
      { key: 'operators', label: 'Operators', icon: '🧑‍🏭' },
      { key: 'machines',  label: 'Machines',  icon: '⚙️' },
      { key: 'monthly',   label: 'Monthly',   icon: '📅' },
      { key: 'daily',     label: 'Daily',     icon: '🗓️' },
    ]
    const activeTab = ref('overview')

    const summary = ref({
      fabric: { qty: 0, uom: 'Kgs', entries: 0 },
      collar: { qty: 0, uom: 'Pcs', entries: 0 },
      cuff:   { qty: 0, uom: 'Pcs', entries: 0 },
    })
    const itemRows = ref([])
    const fabricRows = ref([])
    const operatorRows = ref([])
    const machineRows = ref([])
    const monthlyRows = ref([])
    const dailyRows = ref([])
    const dailyTotals = ref({ fabric_qty: 0, collar_qty: 0, cuff_qty: 0 })
    const loaded = ref(false)

    function applyRange(r) {
      activeRange.value = r.label
      const range = r.fn(todayStr())
      filters.value.from_date = range.from
      filters.value.to_date = range.to
      loadAll()
    }

    function fmtQty(n) {
      return Number(n || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })
    }

    function skillClass(level) {
      if (level === 'Excellent') return 'kd-skill-excellent'
      if (level === 'Good') return 'kd-skill-good'
      if (level === 'Average') return 'kd-skill-average'
      return 'kd-skill-review'
    }

    function fmtDateLabel(d) {
      // 'YYYY-MM-DD' -> '01-Sep', matching the sheet you're matching against
      const dt = parse(d)
      const day = String(dt.getDate()).padStart(2, '0')
      const mon = dt.toLocaleDateString('en-GB', { month: 'short' })
      return `${day}-${mon}`
    }

    // ── column definitions for each table (KdTable handles sort + per-column filter) ──
    const itemColumns = [
      { key: 'item_code',       label: 'Item code' },
      { key: 'commercial_name', label: 'Commercial name' },
      { key: 'color',           label: 'Color' },
      { key: 'item_type',       label: 'Type' },
      { key: 'qty',             label: 'Qty', numeric: true, format: fmtQty },
      { key: 'uom',             label: 'UOM' },
    ]
    const fabricColumns = [
      { key: 'fabric',       label: 'Fabric' },
      { key: 'item_code',    label: 'Item code' },
      { key: 'rolls',        label: 'Rolls',        numeric: true },
      { key: 'total_weight', label: 'Weight (Kgs)', numeric: true, format: fmtQty },
      { key: 'total_qty',    label: 'Pieces',       numeric: true, format: fmtQty },
    ]
    const operatorColumns = [
      { key: 'operator',      label: 'Operator' },
      { key: 'rolls',         label: 'Rolls',        numeric: true },
      { key: 'total_weight',  label: 'Weight (Kgs)', numeric: true, format: fmtQty },
      { key: 'correct_qty',   label: 'Correct pcs',  numeric: true, format: fmtQty },
      { key: 'mistake_qty',   label: 'Mistake pcs',  numeric: true, format: fmtQty },
      { key: 'accuracy_pct',  label: 'Accuracy',     numeric: true, suffix: '%' },
      { key: 'skill_level',   label: 'Skill level' },
    ]
    const machineColumns = [
      { key: 'machine',        label: 'Machine' },
      { key: 'rolls',          label: 'Rolls',        numeric: true },
      { key: 'total_weight',   label: 'Weight (Kgs)', numeric: true, format: fmtQty },
      { key: 'total_qty',      label: 'Pieces',       numeric: true, format: fmtQty },
      { key: 'efficiency_pct', label: 'Efficiency',   numeric: true, suffix: '%' },
    ]
    const monthlyColumns = [
      { key: 'month',        label: 'Month' },
      { key: 'rolls',        label: 'Rolls',        numeric: true },
      { key: 'total_weight', label: 'Weight (Kgs)', numeric: true, format: fmtQty },
      { key: 'total_qty',    label: 'Pieces',       numeric: true, format: fmtQty },
    ]
    const dailyColumns = [
      { key: 'date',       label: 'Date',                numeric: false, format: fmtDateLabel },
      { key: 'fabric_qty', label: 'Body Fabric (Kgs)',    numeric: true,  format: fmtQty },
      { key: 'collar_qty', label: 'Collar (Pcs)',         numeric: true,  format: fmtQty },
      { key: 'cuff_qty',   label: 'Cuffs (Pcs)',          numeric: true,  format: fmtQty },
    ]

    // Totals rows — computed from the full dataset (unaffected by the
    // in-table column filters), matching how the Daily tab already worked.
    const monthlyTotals = computed(() => {
      if (!monthlyRows.value.length) return null
      const t = { label: 'Total prod', rolls: 0, total_weight: 0, total_qty: 0 }
      for (const r of monthlyRows.value) {
        t.rolls += Number(r.rolls) || 0
        t.total_weight += Number(r.total_weight) || 0
        t.total_qty += Number(r.total_qty) || 0
      }
      return t
    })
    const dailyTotalsRow = computed(() => ({
      label: 'Total prod',
      fabric_qty: dailyTotals.value.fabric_qty,
      collar_qty: dailyTotals.value.collar_qty,
      cuff_qty: dailyTotals.value.cuff_qty,
    }))

    async function loadAll() {
      loaded.value = false
      const args = {
        from_date: filters.value.from_date,
        to_date: filters.value.to_date,
        company: filters.value.company,
      }
      try {
        const [s, rows, fabrics, operators, machines, monthly, daily] = await Promise.all([
          call('dashboards.api.knitting_api.get_summary', args),
          call('dashboards.api.knitting_api.get_item_wise', args),
          call('dashboards.api.knitting_api.get_fabric_volume', args),
          call('dashboards.api.knitting_api.get_operator_summary', args),
          call('dashboards.api.knitting_api.get_machine_output', args),
          call('dashboards.api.knitting_api.get_monthly_production', args),
          call('dashboards.api.knitting_api.get_daily_breakdown', args),
        ])
        summary.value = { ...summary.value, ...s }
        itemRows.value = rows || []
        fabricRows.value = fabrics || []
        operatorRows.value = operators || []
        machineRows.value = machines || []
        monthlyRows.value = monthly || []
        dailyRows.value = (daily && daily.days) || []
        dailyTotals.value = (daily && daily.totals) || { fabric_qty: 0, collar_qty: 0, cuff_qty: 0 }
      } catch (e) {
        console.warn('Knitting dashboard load failed:', e)
      } finally {
        loaded.value = true
      }
    }

    onMounted(loadAll)

    return {
      filters, activeRange, quickRanges, COMPANY, tabs, activeTab,
      applyRange, loadAll, summary, itemRows, fabricRows, operatorRows,
      machineRows, monthlyRows, dailyRows, dailyTotals, loaded, fmtQty,
      fmtDateLabel, skillClass,
      itemColumns, fabricColumns, operatorColumns, machineColumns,
      monthlyColumns, dailyColumns, monthlyTotals, dailyTotalsRow,
    }
  },
}
</script>

<style scoped>
#knitting-dashboard-app{
  --b:#1565C0;--m:#757575;--br:#E0E0E0;--bg:#F8FAFB;--tx:#212121;
  font-size:13px;color:var(--tx);background:var(--bg);min-height:100vh
}

/* header */
.kd-header{background:#fff;border-bottom:1px solid var(--br);padding:12px 20px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;position:sticky;top:0;z-index:100}
.kd-header__left{display:flex;align-items:center;gap:8px}
.kd-back{display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:6px;color:#1A1A1A;text-decoration:none}
.kd-back:hover{background:#F0F0F0}
.kd-title-group{display:flex;flex-direction:column;line-height:1.25}
.kd-breadcrumb{font-size:12px;color:var(--tx)}
.kd-breadcrumb a{color:inherit;text-decoration:none}
.kd-breadcrumb a:hover{text-decoration:underline}
.kd-title{font-size:16px;font-weight:700;color:#1A1A1A}
.kd-header__right{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.kd-fg{display:flex;flex-direction:column;gap:2px}
.kd-lbl{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;color:var(--m)}
.kd-input,.kd-select{font-size:12px;padding:5px 9px;border:1px solid var(--br);border-radius:6px;background:#fff;color:var(--tx);outline:none}
.kd-input:focus,.kd-select:focus{border-color:var(--b)}
.kd-company-fixed{font-size:12px;padding:5px 9px;border:1px solid var(--br);border-radius:6px;background:#F8FAFB;color:var(--tx);white-space:nowrap}
.kd-ranges{display:flex;gap:3px;flex-wrap:wrap;align-items:center}
.kd-range{padding:4px 9px;font-size:11px;border:1px solid var(--br);border-radius:6px;background:#fff;cursor:pointer;color:var(--m);transition:.15s all}
.kd-range:hover,.kd-range.active{background:var(--b);border-color:var(--b);color:#fff}

/* tabs */
.kd-tabs{display:flex;background:#fff;border-bottom:1px solid var(--br);padding:0 20px;overflow-x:auto;gap:0}
.kd-tab{padding:12px 16px;font-size:12px;font-weight:500;border:none;border-bottom:2px solid transparent;background:none;cursor:pointer;color:var(--m);white-space:nowrap;display:flex;align-items:center;gap:5px;transition:.15s all}
.kd-tab:hover{color:var(--tx)}
.kd-tab.active{color:var(--b);border-bottom-color:var(--b)}
.kd-tab-icon{font-size:14px}

/* body */
.kd-body{padding:20px}
.kd-placeholder{background:#fff;border:1px dashed #BDBDBD;border-radius:10px;padding:48px 24px;text-align:center;color:var(--m);font-size:14px}

.kd-section-title{font-size:11px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;color:var(--m);margin:0 0 10px}
.kd-section-title:not(:first-child){margin-top:24px}

.kd-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin-bottom:8px}
.kd-card{background:#fff;border:1px solid var(--br);border-radius:10px;padding:16px 18px}
.kd-card-label{font-size:11px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;color:var(--m);margin-bottom:6px}
.kd-card-value{font-size:24px;font-weight:700;color:#1A1A1A}
.kd-card-uom{font-size:13px;font-weight:500;color:var(--m)}
.kd-card-sub{font-size:12px;color:var(--m);margin-top:4px}

.kd-skill{display:inline-block;padding:2px 9px;border-radius:12px;font-size:11px;font-weight:700}
.kd-skill-excellent{background:#E1F5EE;color:#085041}
.kd-skill-good{background:#EAF3DE;color:#27500A}
.kd-skill-average{background:#FAEEDA;color:#854F0B}
.kd-skill-review{background:#FCEBEB;color:#791F1F}
</style>
