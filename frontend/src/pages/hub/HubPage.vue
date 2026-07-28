<template>
  <div class="hub">
    <div class="hub-header">
      <div class="hub-logo">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <rect x="2" y="13" width="4" height="8" rx="1" fill="white"/>
          <rect x="9" y="8" width="4" height="13" rx="1" fill="white"/>
          <rect x="16" y="3" width="4" height="18" rx="1" fill="white"/>
        </svg>
      </div>
      <div class="hub-titles">
        <h1>Dashboards</h1>
        <p>Pranera ERP Analytics</p>
      </div>
    </div>
    <p class="hub-sub">All analytical views — click any dashboard to open it.</p>
    <div class="grid">

      <router-link to="/dashboard-app/sales" class="card">
        <div class="accent" style="background:#1565C0"></div>
        <div class="icon">📊</div>
        <div class="card-title">Sales Dashboard</div>
        <div class="card-desc">Sales Invoices &amp; Sales Orders — revenue, customers, commercial name, UOM, state, sales person, cost center, naming series.</div>
        <span class="tag tag-live">● Live</span>
      </router-link>

      <div class="card coming">
        <div class="accent" style="background:#F57C00"></div>
        <div class="icon">🛒</div>
        <div class="card-title">Purchase Dashboard</div>
        <div class="card-desc">Purchase Orders &amp; Purchase Invoices — supplier-wise spend, pending GRNs, payment aging.</div>
        <span class="tag tag-soon">Coming soon</span>
      </div>

      <div class="card coming">
        <div class="accent" style="background:#2E7D32"></div>
        <div class="icon">🏭</div>
        <div class="card-title">Work Order Dashboard</div>
        <div class="card-desc">Work Orders — production vs target, WIP, finished goods, operation-wise efficiency.</div>
        <span class="tag tag-soon">Coming soon</span>
      </div>

      <router-link to="/dashboard-app/inventory" class="card">
        <div class="accent" style="background:#0097A7"></div>
        <div class="icon">📦</div>
        <div class="card-title">Inventory Dashboard</div>
        <div class="card-desc">Stock by batch — Commercial Name &amp; Color, MARS 200 fabric/collar/cuff, BWBH PT/SASTRI, BWBH JV.</div>
        <span class="tag tag-live">● Live</span>
      </router-link>

      <div class="card coming">
        <div class="accent" style="background:#6A1B9A"></div>
        <div class="icon">💰</div>
        <div class="card-title">Finance Dashboard</div>
        <div class="card-desc">Accounts Receivable &amp; Payable — aging buckets, cash flow, P&amp;L summary.</div>
        <span class="tag tag-plan">Planned</span>
      </div>

      <div class="card coming">
        <div class="accent" style="background:#C62828"></div>
        <div class="icon">🔧</div>
        <div class="card-title">Quality Dashboard</div>
        <div class="card-desc">Quality Inspections — rejection rate, defect category, supplier quality trends.</div>
        <span class="tag tag-plan">Planned</span>
      </div>

    </div>
  </div>
</template>

<script>
export default {
  name: 'HubPage',
}
</script>

<style scoped>
.hub{max-width:1000px;margin:0 auto;padding:40px 24px}
.hub-header{margin-bottom:8px;display:flex;align-items:center;gap:12px}
.hub-logo{width:40px;height:40px;border-radius:10px;background:#1565C0;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.hub-titles h1{font-size:22px;font-weight:700;color:#1A1A1A;margin-bottom:2px}
.hub-titles p{font-size:13px;color:#757575}
.hub-sub{font-size:13px;color:#757575;margin-bottom:32px;margin-top:8px;padding-left:52px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:20px}
.card{background:#fff;border:1px solid #E0E0E0;border-radius:12px;padding:24px;text-decoration:none;color:inherit;display:flex;flex-direction:column;gap:10px;position:relative;overflow:hidden;transition:box-shadow .2s,transform .15s}
.card:hover{box-shadow:0 4px 16px rgba(0,0,0,.12);transform:translateY(-2px);text-decoration:none}
.card.coming{opacity:.55;pointer-events:none}
.accent{position:absolute;top:0;left:0;right:0;height:4px}
.icon{font-size:28px;line-height:1;margin-top:4px}
.card-title{font-size:15px;font-weight:700;color:#1A1A1A}
.card-desc{font-size:12px;color:#757575;line-height:1.6;flex:1}
.tag{display:inline-block;font-size:10px;font-weight:600;padding:3px 10px;border-radius:20px;margin-top:4px;width:fit-content}
.tag-live{background:#E8F5E9;color:#2E7D32}
.tag-soon{background:#FFF3E0;color:#E65100}
.tag-plan{background:#F3E5F5;color:#6A1B9A}
</style>
