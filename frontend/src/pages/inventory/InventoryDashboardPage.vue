<template>
<div id="app">

  <div class="sd-header">
    <div class="sd-header__left">
      <a class="sd-back" href="/dashboard-app">&larr; Dashboards</a>
      <div class="sd-title">📦 Inventory Dashboard</div>
    </div>
    <div class="sd-header__right">
      <button class="sd-btn" @click="expandAll">Expand All Rows</button>
      <button class="sd-btn" @click="collapseAll">Collapse All Rows</button>
      <button class="sd-btn primary" @click="loadActiveTab(true)">⟳ Refresh</button>
    </div>
  </div>

  <div class="sd-tabs">
    <button v-for="t in tabs" :key="t.key" class="sd-tab" :class="{active: activeTab===t.key}" @click="switchTab(t.key)">{{ t.label }}</button>
  </div>

  <div class="sd-body">
    <div class="sd-card">

      <div v-if="loading[activeTab]" class="sd-loading">
        <div class="sd-spinner"></div>
        <div>Loading stock details…</div>
      </div>

      <div v-else-if="error[activeTab]" class="sd-error">{{ error[activeTab] }}</div>

      <template v-else>
        <div class="sd-toolbar">
          <div class="sd-toolbar__left">
            <input class="sd-search" type="text" v-model="search" placeholder="Filter by commercial name, color, batch no, warehouse…"/>
            <span class="sd-meta">{{ filteredLeafCount }} batch rows · {{ groupCount }} commercial names</span>
          </div>
        </div>

        <div class="sd-twrap">
          <table class="sd-table">
            <thead>
              <tr>
                <th>Commercial Name / Color</th>
                <th>Width</th>
                <th v-if="activeTab!=='mars200'">Item Code</th>
                <th>{{ activeTab==='mars200' ? 'Batch No' : 'Warehouse' }}</th>
                <th v-if="activeTab==='mars200'">Warehouse</th>
                <th class="sd-th-r">Qty</th>
                <th v-if="activeTab!=='mars200'">Batch No</th>
                <th>Batch Status</th>
                <th v-if="activeTab==='mars200'" class="sd-th-r">Collar Qty</th>
                <th v-if="activeTab==='mars200'">Collar Status</th>
                <th v-if="activeTab==='mars200'" class="sd-th-r">Cuff Qty</th>
                <th v-if="activeTab==='mars200'">Cuff Status</th>
              </tr>
            </thead>
            <tbody>
              <template v-if="flatRows.length">
                <tr v-for="row in flatRows" :key="row.key"
                    :class="row.type==='g0' ? 'sd-row-g0' : row.type==='g1' ? 'sd-row-g1' : 'sd-row-leaf'"
                    @click="row.type!=='leaf' && toggle(row.key)">

                  <td :class="row.type==='g1' ? 'sd-indent1' : row.type==='leaf' ? 'sd-indent2' : ''">
                    <span class="sd-grouplabel">
                      <span v-if="row.type!=='leaf'" class="sd-chev" :class="{open: expanded.has(row.key)}">▶</span>
                      <span>{{ row.label }}</span>
                      <span v-if="row.type!=='leaf'" class="sd-count">({{ row.count }})</span>
                    </span>
                  </td>

                  <td>{{ row.type==='leaf' ? row.data.width : '' }}</td>

                  <td v-if="activeTab!=='mars200'">{{ row.type==='leaf' ? row.data.item_code : '' }}</td>

                  <td>{{ row.type==='leaf' ? (activeTab==='mars200' ? row.data.batch_no : row.data.warehouse) : '' }}</td>
                  <td v-if="activeTab==='mars200'">{{ row.type==='leaf' ? row.data.parentwarehouse : '' }}</td>

                  <td class="sd-amt">{{ fmt(row.qty) }}</td>

                  <td v-if="activeTab!=='mars200'">{{ row.type==='leaf' ? row.data.batch_no : '' }}</td>
                  <td>
                    <span v-if="row.type==='leaf'" class="sd-badge" :class="statusClass(row.data.batch_status)">{{ row.data.batch_status }}</span>
                  </td>

                  <td v-if="activeTab==='mars200'" class="sd-amt">{{ row.type!=='leaf' ? fmt(row.collarQty) : fmt(row.data.collar_qty) }}</td>
                  <td v-if="activeTab==='mars200'">
                    <span v-if="row.type==='leaf' && row.data.collar_status" class="sd-badge" :class="statusClass(row.data.collar_status)">{{ row.data.collar_status }}</span>
                  </td>
                  <td v-if="activeTab==='mars200'" class="sd-amt">{{ row.type!=='leaf' ? fmt(row.cuffQty) : fmt(row.data.cuff_qty) }}</td>
                  <td v-if="activeTab==='mars200'">
                    <span v-if="row.type==='leaf' && row.data.cuff_status" class="sd-badge" :class="statusClass(row.data.cuff_status)">{{ row.data.cuff_status }}</span>
                  </td>

                </tr>
              </template>
              <tr v-else>
                <td class="sd-empty" :colspan="activeTab==='mars200' ? 11 : 8">No stock found.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>

    </div>
  </div>

</div>
</template>

<script>
/* Inventory Dashboard — Vue 3, ported from www/dashboards-inventory.html */

/* API: works in both Desk (/app/...) and www/PWA contexts, same approach
   used in dashboards-sales.html */
function callApi(method, args) {
  const fullMethod = "dashboards.api.inventory_api." + method;

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

  const params = new URLSearchParams();
  for (const [k, v] of Object.entries(args || {})) {
    if (v !== null && v !== undefined && v !== "") params.set(k, String(v));
  }
  const url = "/api/method/" + fullMethod + (params.toString() ? "?" + params.toString() : "");
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


export default {
  data(){
    return {
      tabs: [
        { key: 'mars200',   label: 'MARS 200' },
        { key: 'pt_sastri', label: 'BWBH PT/SASTRI' },
        { key: 'jv',        label: 'BWBH JV' },
      ],
      activeTab: 'pt_sastri',
      rows: { mars200: [], pt_sastri: [], jv: [] },
      loaded: { mars200: false, pt_sastri: false, jv: false },
      loading: { mars200: false, pt_sastri: false, jv: false },
      error: { mars200: '', pt_sastri: '', jv: '' },
      expanded: new Set(),
      search: '',
    }
  },
  computed: {
    currentRows(){ return this.rows[this.activeTab] || []; },
    filteredRows(){
      const q = this.search.trim().toLowerCase();
      if(!q) return this.currentRows;
      return this.currentRows.filter(r => {
        return ['commercial_name','color','width','item_code','warehouse','parentwarehouse','batch_no','batch_status']
          .some(f => (r[f] || '').toString().toLowerCase().includes(q));
      });
    },
    tree(){
      // group by commercial_name -> color
      const byComm = new Map();
      for(const r of this.filteredRows){
        const commKey = 'g0:' + (r.commercial_name || '—');
        if(!byComm.has(commKey)) byComm.set(commKey, { key: commKey, label: r.commercial_name || '—', qty:0, collarQty:0, cuffQty:0, count:0, colors: new Map() });
        const commNode = byComm.get(commKey);

        const colorKey = commKey + '|g1:' + (r.color || '—');
        if(!commNode.colors.has(colorKey)) commNode.colors.set(colorKey, { key: colorKey, label: r.color || '—', qty:0, collarQty:0, cuffQty:0, count:0, leaves: [] });
        const colorNode = commNode.colors.get(colorKey);

        colorNode.leaves.push(r);
        colorNode.qty += (+r.actual_qty || 0);
        colorNode.collarQty += (+r.collar_qty || 0);
        colorNode.cuffQty += (+r.cuff_qty || 0);
        colorNode.count += 1;

        commNode.qty += (+r.actual_qty || 0);
        commNode.collarQty += (+r.collar_qty || 0);
        commNode.cuffQty += (+r.cuff_qty || 0);
        commNode.count += 1;
      }
      return [...byComm.values()].sort((a,b)=>a.label.localeCompare(b.label));
    },
    flatRows(){
      const out = [];
      for(const comm of this.tree){
        out.push({ type:'g0', key: comm.key, label: comm.label, count: comm.count, qty: comm.qty, collarQty: comm.collarQty, cuffQty: comm.cuffQty });
        if(!this.expanded.has(comm.key)) continue;
        const colors = [...comm.colors.values()].sort((a,b)=>a.label.localeCompare(b.label));
        for(const color of colors){
          out.push({ type:'g1', key: color.key, label: color.label, count: color.count, qty: color.qty, collarQty: color.collarQty, cuffQty: color.cuffQty });
          if(!this.expanded.has(color.key)) continue;
          for(const leaf of color.leaves){
            out.push({ type:'leaf', key: color.key + '|' + leaf.batch_no + leaf.warehouse, data: leaf, qty: +leaf.actual_qty || 0 });
          }
        }
      }
      return out;
    },
    filteredLeafCount(){ return this.filteredRows.length; },
    groupCount(){ return this.tree.length; },
  },
  methods: {
    fmt(v){
      const n = +v || 0;
      return n.toFixed(3).replace(/\B(?=(\d{3})+(?!\d)\.)/g, ',');
    },
    statusClass(status){
      if(!status) return 'other';
      const s = status.toUpperCase();
      if(s.includes('QC OK')) return 'ok';
      if(s.includes('PENDING') || s.includes('HOLD') || s.includes('UNDER')) return 'pending';
      if(s.includes('REJECT') || s.includes('SCRAP')) return 'reject';
      return 'other';
    },
    toggle(key){
      if(this.expanded.has(key)) this.expanded.delete(key);
      else this.expanded.add(key);
    },
    expandAll(){
      for(const comm of this.tree){
        this.expanded.add(comm.key);
        for(const color of comm.colors.values()) this.expanded.add(color.key);
      }
    },
    collapseAll(){
      this.expanded.clear();
    },
    switchTab(key){
      this.activeTab = key;
      this.search = '';
      this.expanded.clear();
      if(!this.loaded[key]) this.loadActiveTab(false);
    },
    async loadActiveTab(forceRefresh){
      const tab = this.activeTab;
      this.loading[tab] = true;
      this.error[tab] = '';
      try {
        let method, args = { refresh: forceRefresh ? 1 : 0 };
        if(tab === 'mars200'){
          method = 'get_mars200_stock';
        } else {
          method = 'get_stock_by_batch';
          args.group = tab;
        }
        const message = await callApi(method, args);
        this.rows[tab] = message || [];
        this.loaded[tab] = true;
      } catch(e){
        console.error(e);
        this.error[tab] = 'Could not load stock details. Please try again.';
      } finally {
        this.loading[tab] = false;
      }
    },
  },
  mounted(){
    this.loadActiveTab(false);
  }
}

</script>

<style scoped>
:root{
  --b:#1565C0;--t:#0097A7;--g:#2E7D32;--a:#F57C00;--r:#C62828;--m:#757575;
  --br:#E0E0E0;--bg:#F8FAFB;--tx:#212121;--sh:0 1px 4px rgba(0,0,0,.07);--rd:10px;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;font-size:13px;color:var(--tx);background:var(--bg);min-height:100vh}

/* header */
.sd-header{background:#fff;border-bottom:1px solid var(--br);padding:12px 20px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;position:sticky;top:0;z-index:100}
.sd-header__left{display:flex;align-items:center;gap:10px}
.sd-back{color:var(--m);text-decoration:none;font-size:13px}
.sd-back:hover{color:var(--t)}
.sd-title{font-size:16px;font-weight:700;color:#1A1A1A}
.sd-header__right{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.sd-btn{font-size:12px;padding:6px 12px;border:1px solid var(--br);border-radius:6px;background:#fff;cursor:pointer;color:var(--tx);transition:.15s all}
.sd-btn:hover{border-color:var(--t);color:var(--t)}
.sd-btn.primary{background:var(--t);border-color:var(--t);color:#fff}
.sd-btn.primary:hover{opacity:.9;color:#fff}

/* loading / error */
.sd-loading{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;padding:80px;font-size:13px;color:var(--m)}
.sd-spinner{width:30px;height:30px;border:3px solid var(--br);border-top-color:var(--t);border-radius:50%;animation:spin .7s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.sd-error{padding:40px;text-align:center;color:var(--r);font-size:13px}

/* tabs */
.sd-tabs{display:flex;background:#fff;border-bottom:1px solid var(--br);padding:0 20px;overflow-x:auto;gap:0}
.sd-tab{padding:12px 16px;font-size:12px;font-weight:600;border:none;border-bottom:2px solid transparent;background:none;cursor:pointer;color:var(--m);white-space:nowrap;transition:.15s all}
.sd-tab:hover{color:var(--tx)}
.sd-tab.active{color:var(--t);border-bottom-color:var(--t)}

/* body */
.sd-body{padding:20px}
.sd-card{background:#fff;border:1px solid var(--br);border-radius:var(--rd);padding:16px;box-shadow:var(--sh)}

/* toolbar */
.sd-toolbar{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:12px;flex-wrap:wrap}
.sd-toolbar__left{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.sd-search{font-size:12px;padding:6px 10px;border:1px solid var(--br);border-radius:6px;outline:none;min-width:220px}
.sd-search:focus{border-color:var(--t)}
.sd-meta{font-size:11px;color:var(--m)}

/* tree table */
.sd-twrap{overflow-x:auto;border:1px solid var(--br);border-radius:8px}
.sd-table{width:100%;border-collapse:collapse;font-size:12.5px;min-width:900px}
.sd-table thead th{background:var(--bg);color:var(--m);font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;padding:9px 10px;text-align:left;border-bottom:1px solid var(--br);white-space:nowrap;position:sticky;top:0}
.sd-th-r{text-align:right !important}
.sd-table td{padding:6px 10px;border-bottom:1px solid #F2F2F2;white-space:nowrap}
.sd-amt{text-align:right;font-variant-numeric:tabular-nums}
.sd-row-g0{background:#F5FAFB;cursor:pointer;font-weight:700}
.sd-row-g0:hover{background:#ECF6F7}
.sd-row-g1{background:#FBFDFE;cursor:pointer;font-weight:600}
.sd-row-g1:hover{background:#F1F8F9}
.sd-row-leaf td{color:var(--tx)}
.sd-row-leaf:hover{background:#FAFAFA}
.sd-chev{display:inline-block;width:14px;font-size:10px;color:var(--m);transition:transform .15s}
.sd-chev.open{transform:rotate(90deg)}
.sd-indent1{padding-left:26px}
.sd-indent2{padding-left:46px}
.sd-grouplabel{display:flex;align-items:center;gap:6px}
.sd-count{color:var(--m);font-weight:500}
.sd-badge{display:inline-block;font-size:10px;font-weight:700;padding:2px 8px;border-radius:4px;white-space:nowrap}
.sd-badge.ok{background:#E8F5E9;color:#2E7D32}
.sd-badge.pending{background:#FFF3E0;color:#E65100}
.sd-badge.reject{background:#FFEBEE;color:#C62828}
.sd-badge.other{background:#F3E5F5;color:#6A1B9A}
.sd-empty{padding:40px;text-align:center;color:var(--m)}
</style>
