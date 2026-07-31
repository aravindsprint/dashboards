<template>
<div id="sales-dashboard-app">

  <!-- Header -->
  <div class="sd-header">
    <div class="sd-header__left">
      <a href="/dashboard-app" class="sd-back" title="All Dashboards">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M10 3L5 8l5 5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </a>
      <svg width="26" height="26" viewBox="0 0 28 28" fill="none"><rect width="28" height="28" rx="6" fill="#1565C0"/><path d="M6 20 L10 13 L14 16 L18 8 L22 12" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/></svg>
      <div class="sd-title-group">
        <span class="sd-breadcrumb"><a href="/dashboard-app">Dashboards</a> /</span>
        <span class="sd-title">Sales Dashboard</span>
      </div>
    </div>
    <div class="sd-header__right">
      <div class="sd-fg"><label class="sd-lbl">From</label><input type="date" v-model="filters.from_date" class="sd-input" @change="loadAll"/></div>
      <div class="sd-fg"><label class="sd-lbl">To</label><input type="date" v-model="filters.to_date" class="sd-input" @change="loadAll"/></div>
      <div class="sd-fg"><label class="sd-lbl">Company</label>
        <select v-model="filters.company" class="sd-select" @change="loadAll">
          <option value="">All companies</option>
          <option v-for="c in companies" :key="c" :value="c">{{ c }}</option>
        </select>
      </div>
      <div class="sd-ranges">
        <button v-for="r in quickRanges" :key="r.label" :class="['sd-range',{active:activeRange===r.label}]" @click="applyRange(r)">{{ r.label }}</button>
      </div>
      <a v-if="isSystemManager" href="/whatsapp-config" title="WhatsApp Configuration" style="display:inline-flex;align-items:center;gap:6px;padding:5px 12px;background:#25D366;color:#fff;border-radius:6px;font-size:12px;font-weight:600;text-decoration:none;flex-shrink:0;transition:.15s" onmouseover="this.style.background='#128C7E'" onmouseout="this.style.background='#25D366'">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M12 0C5.373 0 0 5.373 0 12c0 2.123.554 4.118 1.528 5.845L.057 23.428a.5.5 0 0 0 .609.61l5.676-1.484A11.95 11.95 0 0 0 12 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 22c-1.907 0-3.686-.528-5.2-1.44l-.373-.22-3.865 1.01 1.027-3.75-.242-.386A9.937 9.937 0 0 1 2 12C2 6.477 6.477 2 12 2s10 4.477 10 10-4.477 10-10 10z"/></svg>
        WhatsApp
      </a>
    </div>
  </div>

  <!-- Loading -->
  <div v-if="loading" class="sd-loading"><div class="sd-spinner"></div><span>Loading…</span></div>

  <template v-else>
    <!-- Tabs -->
    <div class="sd-tabs">
      <button v-for="t in tabs" :key="t.key" :class="['sd-tab',{active:activeTab===t.key}]" @click="activeTab=t.key">
        <span class="sd-tab-icon">{{ t.icon }}</span>{{ t.label }}
      </button>
    </div>

    <!-- ═══════════════ OVERVIEW ═══════════════ -->
    <div v-show="activeTab==='overview'" class="sd-body">
      <div class="sd-slbl">Sales Invoices</div>
      <div class="sd-kpis">
        <div class="sd-kpi"><div class="sd-kpi-l">Total Invoiced</div><div class="sd-kpi-v">{{ fmt(summary.invoice.total_invoiced) }}</div><div class="sd-kpi-s">{{ summary.invoice.count }} invoices</div></div>
        <div class="sd-kpi g"><div class="sd-kpi-l">Collected</div><div class="sd-kpi-v">{{ fmt(summary.invoice.total_collected) }}</div><div class="sd-kpi-s">{{ summary.invoice.collection_rate }}% rate</div></div>
        <div class="sd-kpi a"><div class="sd-kpi-l">Outstanding</div><div class="sd-kpi-v">{{ fmt(summary.invoice.total_outstanding) }}</div><div class="sd-kpi-s">Pending collection</div></div>
        <div class="sd-kpi"><div class="sd-kpi-l">Collection Rate</div><div class="sd-kpi-v">{{ summary.invoice.collection_rate }}%</div>
          <div class="sd-kpi-s"><div class="sd-prog"><div class="sd-progb" :class="summary.invoice.collection_rate>=80?'g':'a'" :style="{width:summary.invoice.collection_rate+'%'}"></div></div></div>
        </div>
      </div>
      <div class="sd-slbl mt">Top Customers — Cost Center Summary</div>
      <div class="sd-card" style="margin-bottom:0">
        <div class="sd-toolbar">
          <input v-model="filterText['ov_cc']" class="sd-search" placeholder="Filter cost centers…"/>
        </div>
        <div class="sd-twrap">
          <table class="sd-table">
            <thead>
              <tr>
                <th>#</th>
                <th @click="toggleSort('ov_cc','cost_center')">Cost Center <span :class="['sd-sort',{on:sortIconActive('ov_cc','cost_center')}]">{{ sortIcon('ov_cc','cost_center') }}</span></th>
                <th class="sd-th-r" @click="toggleSort('ov_cc','revenue')">Revenue (SI) <span :class="['sd-sort',{on:sortIconActive('ov_cc','revenue')}]">{{ sortIcon('ov_cc','revenue') }}</span></th>
                <th class="sd-th-r" @click="toggleSort('ov_cc','collected')">Collected <span :class="['sd-sort',{on:sortIconActive('ov_cc','collected')}]">{{ sortIcon('ov_cc','collected') }}</span></th>
                <th>Collection %</th>
                <th class="sd-th-r" @click="toggleSort('ov_cc','invoices')">Invoices <span :class="['sd-sort',{on:sortIconActive('ov_cc','invoices')}]">{{ sortIcon('ov_cc','invoices') }}</span></th>
                <th class="sd-th-r">Order Value (SO)</th>
                <th class="sd-th-r">Orders</th>
              </tr>
            </thead>
            <tbody>
              <template v-for="(row,i) in paged('ov_cc', sortedRows('ov_cc', ccData.by_invoice, ['revenue','collected','invoices']))" :key="row.cost_center">
                <tr class="clickable" :class="{'drill-open':isDrillOpen('ov_cc',row.cost_center)}"
                    @click="toggleDrill('ov_cc', row.cost_center, 'cost_center_customers', {cost_center: row.cost_center})">
                  <td style="color:#9E9E9E;font-size:12px">{{ i+1 }}</td>
                  <td><strong>{{ row.cost_center }}</strong> <span class="sd-chevron" :class="{open:isDrillOpen('ov_cc',row.cost_center)}">▾</span></td>
                  <td class="sd-amt">{{ fmt(row.revenue) }}</td>
                  <td class="sd-amt">{{ fmt(row.collected) }}</td>
                  <td>
                    <div style="display:flex;align-items:center;gap:6px">
                      <div class="sd-sbw" style="width:60px"><div class="sd-sbar" :style="{width:pct(row.collected,row.revenue)+'%',background:'#2E7D32'}"></div></div>
                      <span style="font-size:11px;color:#757575">{{ pct(row.collected,row.revenue) }}%</span>
                    </div>
                  </td>
                  <td class="sd-amt">{{ row.invoices }}</td>
                  <td class="sd-amt">{{ fmt((ccData.by_order.find(r=>r.cost_center===row.cost_center)||{}).order_value) }}</td>
                  <td class="sd-amt">{{ (ccData.by_order.find(r=>r.cost_center===row.cost_center)||{}).orders || '—' }}</td>
                </tr>
                <tr v-if="isDrillOpen('ov_cc', row.cost_center)" class="sd-drill">
                  <td colspan="8" style="padding:0">
                    <div class="sd-drill-inner">
                      <div class="sd-drill-title">▸ {{ row.cost_center }} — customers &amp; sales persons</div>
                      <div v-if="isDrillLoading('ov_cc', row.cost_center)" class="sd-drill-loading"><span class="sd-mini-spin"></span> Loading…</div>
                      <template v-else-if="getDrillRows('ov_cc', row.cost_center).length">
                        <table>
                          <thead><tr>
                            <th>Customer</th>
                            <th class="sd-th-r">Revenue (SI)</th>
                            <th class="sd-th-r">Invoices</th>
                            <th>Sales Person</th>
                            <th class="sd-th-r">Order Value (SO)</th>
                            <th class="sd-th-r">Orders</th>
                          </tr></thead>
                          <tbody>
                            <tr v-for="d in getDrillRows('ov_cc', row.cost_center)" :key="d.customer">
                              <td>{{ d.customer }}</td>
                              <td class="sd-amt">{{ fmt(d.revenue) }}</td>
                              <td class="sd-amt">{{ d.invoices }}</td>
                              <td>{{ d.sales_person || '—' }}</td>
                              <td class="sd-amt">{{ fmt(d.order_value) }}</td>
                              <td class="sd-amt">{{ d.orders || '—' }}</td>
                            </tr>
                          </tbody>
                        </table>
                      </template>
                      <div v-else class="sd-drill-empty">No drill-down data available.</div>
                    </div>
                  </td>
                </tr>
              </template>
              <tr v-if="!ccData.by_invoice.length"><td colspan="8" class="sd-empty">No data available.</td></tr>
            </tbody>
          </table>
        </div>
        <div v-if="remainingCount('ov_cc', sortedRows('ov_cc', ccData.by_invoice, ['revenue','collected','invoices'])) > 0" style="text-align:center;padding:14px 0 4px">
          <button class="sd-xbtn" @click="loadMore('ov_cc')">Load More — {{ remainingCount('ov_cc', sortedRows('ov_cc', ccData.by_invoice, ['revenue','collected','invoices'])) }} more rows</button>
        </div>
      </div>
      <div class="sd-slbl mt">Sales Orders</div>
      <div class="sd-kpis">
        <div class="sd-kpi"><div class="sd-kpi-l">Total Ordered</div><div class="sd-kpi-v">{{ fmt(summary.order.total_ordered) }}</div><div class="sd-kpi-s">{{ summary.order.count }} orders</div></div>
        <div class="sd-kpi t"><div class="sd-kpi-l">To Deliver</div><div class="sd-kpi-v">{{ (summary.order.delivery_breakdown['Not Delivered']||0)+(summary.order.delivery_breakdown['Partly Delivered']||0) }}</div><div class="sd-kpi-s">orders pending</div></div>
        <div class="sd-kpi g"><div class="sd-kpi-l">Fully Delivered</div><div class="sd-kpi-v">{{ summary.order.delivery_breakdown['Fully Delivered']||0 }}</div><div class="sd-kpi-s">completed</div></div>
        <div class="sd-kpi"><div class="sd-kpi-l">Completed Orders</div><div class="sd-kpi-v">{{ summary.order.status_breakdown['Completed']||0 }}</div><div class="sd-kpi-s">billed &amp; delivered</div></div>
      </div>
      <div class="sd-chart-row">
        <div class="sd-card wide">
          <div class="sd-ch"><span class="sd-ct">Monthly Revenue Trend</span>
            <div class="sd-leg"><span class="sd-dot" style="background:#1565C0"></span>Invoices <span class="sd-dot" style="background:#0097A7;margin-left:10px"></span>Orders</div>
          </div>
          <div style="position:relative;height:220px"><canvas id="trendChart" role="img" aria-label="Monthly revenue trend"></canvas></div>
        </div>
        <div class="sd-card">
          <div class="sd-ch"><span class="sd-ct">Invoice Status</span></div>
          <div style="position:relative;height:160px"><canvas id="invoiceStatusChart" role="img" aria-label="Invoice status"></canvas></div>
          <div class="sd-leg-list">
            <div v-for="(v,k) in summary.invoice.status_breakdown" :key="k" class="sd-li">
              <span class="sd-dot" :style="{background:siColor(k)}"></span><span class="sd-li-k">{{ k }}</span><span class="sd-li-v">{{ v }}</span>
            </div>
          </div>
        </div>
        <div class="sd-card">
          <div class="sd-ch"><span class="sd-ct">Delivery Status</span></div>
          <div style="position:relative;height:160px"><canvas id="deliveryStatusChart" role="img" aria-label="Delivery status"></canvas></div>
          <div class="sd-leg-list">
            <div v-for="(v,k) in summary.order.delivery_breakdown" :key="k" class="sd-li">
              <span class="sd-dot" :style="{background:delColor(k)}"></span><span class="sd-li-k">{{ k }}</span><span class="sd-li-v">{{ v }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════ SALES INVOICES ═══════════════ -->
    <div v-show="activeTab==='invoices'" class="sd-body">
      <div class="sd-2col">
        <div class="sd-card full">
          <div class="sd-ch"><span class="sd-ct">Top Customers — Revenue</span></div>
          <div :style="{position:'relative',height:Math.max(220,topCustomers.by_invoice.length*34+60)+'px'}"><canvas id="topCustSIChart" role="img" aria-label="Top customers by invoice revenue"></canvas></div>
        </div>
        <div class="sd-card full">
          <div class="sd-ch"><span class="sd-ct">Invoice Status Breakdown</span></div>
          <div class="sd-sbars">
            <div v-for="(v,k) in summary.invoice.status_breakdown" :key="k" class="sd-srow">
              <span class="sd-sbadge" :style="{background:siColor(k)+'22',color:siColor(k)}">{{ k }}</span>
              <div class="sd-sbw"><div class="sd-sbar" :style="{width:pct(v,summary.invoice.count)+'%',background:siColor(k)}"></div></div>
              <span class="sd-scnt">{{ v }}</span>
            </div>
          </div>
        </div>
      </div>
      <!-- Top customers table with drill → item lines -->
      <div class="sd-card" style="margin-top:16px">
        <div class="sd-ch"><span class="sd-ct">Customer Details</span><span class="sd-badge inv">Invoices</span><div style="display:flex;gap:6px"><button class="sd-xbtn" @click="expandAll('si_cust', topCustomers.by_invoice, 'customer_items', 'customer', r=>({customer:r.customer}))">⊞ Expand All</button><button class="sd-xbtn" @click="collapseAll('si_cust')">⊟ Collapse All</button></div></div>
        <div class="sd-toolbar">
          <input v-model="filterText['si_cust']" class="sd-search" placeholder="Filter customers…"/>
        </div>
        <div class="sd-twrap">
          <table class="sd-table">
            <thead><tr>
              <th @click="toggleSort('si_cust','customer')">Customer <span :class="['sd-sort',{on:sortIconActive('si_cust','customer')}]">{{ sortIcon('si_cust','customer') }}</span></th>
              <th class="sd-th-r" @click="toggleSort('si_cust','revenue')">Revenue <span :class="['sd-sort',{on:sortIconActive('si_cust','revenue')}]">{{ sortIcon('si_cust','revenue') }}</span></th>
              <th class="sd-th-r" @click="toggleSort('si_cust','invoices')">Invoices <span :class="['sd-sort',{on:sortIconActive('si_cust','invoices')}]">{{ sortIcon('si_cust','invoices') }}</span></th>
            </tr></thead>
            <tbody>
              <template v-for="row in paged('si_cust', sortedRows('si_cust', topCustomers.by_invoice, ['revenue','invoices']))" :key="row.customer">
                <tr class="clickable" :class="{'drill-open':isDrillOpen('si_cust',row.customer)}"
                    @click="toggleDrill('si_cust', row.customer, 'customer_items', {customer: row.customer})">
                  <td><strong>{{ row.customer }}</strong> <span class="sd-chevron" :class="{open:isDrillOpen('si_cust',row.customer)}">▾</span></td>
                  <td class="sd-amt">{{ fmt(row.revenue) }}</td>
                  <td class="sd-amt">{{ row.invoices }}</td>
                </tr>
                <tr v-if="isDrillOpen('si_cust', row.customer)" class="sd-drill">
                  <td colspan="3" style="padding:0">
                    <div class="sd-drill-inner">
                      <div class="sd-drill-title">▸ {{ row.customer }} — item codes &amp; commercial names</div>
                      <div v-if="isDrillLoading('si_cust', row.customer)" class="sd-drill-loading"><span class="sd-mini-spin"></span> Loading…</div>
                      <template v-else-if="getDrillRows('si_cust', row.customer).length">
                        <table>
                          <thead><tr>
                            <th>Item Code</th>
                            <th>Commercial Name</th>
                            <th>UOM</th>
                            <th class="sd-th-r">Qty</th>
                            <th class="sd-th-r">Revenue</th>
                            <th>Sales Person</th>
                          </tr></thead>
                          <tbody>
                            <tr v-for="d in getDrillRows('si_cust', row.customer)" :key="d.item_code">
                              <td><span class="sd-mono">{{ d.item_code }}</span></td>
                              <td>{{ cleanName(d.commercial_name || d.item_name) }}</td>
                              <td>{{ d.uom }}</td>
                              <td class="sd-amt">{{ fmtQty(d.qty) }}</td>
                              <td class="sd-amt">{{ fmt(d.revenue) }}</td>
                              <td>{{ d.sales_person || '—' }}</td>
                            </tr>
                          </tbody>
                        </table>
                      </template>
                      <div v-else class="sd-drill-empty">No item details found.</div>
                    </div>
                  </td>
                </tr>
              </template>
              <tr v-if="!topCustomers.by_invoice.length"><td colspan="3" class="sd-empty">No data.</td></tr>
            </tbody>
          </table>
        </div>
        <div v-if="remainingCount('si_cust', sortedRows('si_cust', topCustomers.by_invoice, ['revenue','invoices'])) > 0" style="text-align:center;padding:14px 0 4px">
          <button class="sd-xbtn" @click="loadMore('si_cust')">Load More — {{ remainingCount('si_cust', sortedRows('si_cust', topCustomers.by_invoice, ['revenue','invoices'])) }} more rows</button>
        </div>
      </div>
    </div>

    <!-- ═══════════════ SALES ORDERS ═══════════════ -->
    <div v-show="activeTab==='orders'" class="sd-body">
      <div class="sd-2col">
        <div class="sd-card full">
          <div class="sd-ch"><span class="sd-ct">Top Customers — Order Value</span></div>
          <div :style="{position:'relative',height:Math.max(220,topCustomers.by_order.length*34+60)+'px'}"><canvas id="topCustSOChart" role="img" aria-label="Top customers by order value"></canvas></div>
        </div>
        <div class="sd-card full">
          <div class="sd-ch"><span class="sd-ct">Order Status Breakdown</span></div>
          <div class="sd-sbars">
            <div v-for="(v,k) in summary.order.status_breakdown" :key="k" class="sd-srow">
              <span class="sd-sbadge" :style="{background:soColor(k)+'22',color:soColor(k)}">{{ k }}</span>
              <div class="sd-sbw"><div class="sd-sbar" :style="{width:pct(v,summary.order.count)+'%',background:soColor(k)}"></div></div>
              <span class="sd-scnt">{{ v }}</span>
            </div>
          </div>
        </div>
      </div>
      <!-- Customer table with drill → item lines -->
      <div class="sd-card" style="margin-top:16px">
        <div class="sd-ch"><span class="sd-ct">Customer Details</span><span class="sd-badge ord">Orders</span><div style="display:flex;gap:6px"><button class="sd-xbtn" @click="expandAll('so_cust', topCustomers.by_order, 'customer_order_items', 'customer', r=>({customer:r.customer}))">⊞ Expand All</button><button class="sd-xbtn" @click="collapseAll('so_cust')">⊟ Collapse All</button></div></div>
        <div class="sd-toolbar">
          <input v-model="filterText['so_cust']" class="sd-search" placeholder="Filter customers…"/>
        </div>
        <div class="sd-twrap">
          <table class="sd-table">
            <thead><tr>
              <th @click="toggleSort('so_cust','customer')">Customer <span :class="['sd-sort',{on:sortIconActive('so_cust','customer')}]">{{ sortIcon('so_cust','customer') }}</span></th>
              <th class="sd-th-r" @click="toggleSort('so_cust','order_value')">Order Value <span :class="['sd-sort',{on:sortIconActive('so_cust','order_value')}]">{{ sortIcon('so_cust','order_value') }}</span></th>
              <th class="sd-th-r" @click="toggleSort('so_cust','orders')">Orders <span :class="['sd-sort',{on:sortIconActive('so_cust','orders')}]">{{ sortIcon('so_cust','orders') }}</span></th>
            </tr></thead>
            <tbody>
              <template v-for="row in paged('so_cust', sortedRows('so_cust', topCustomers.by_order, ['order_value','orders']))" :key="row.customer">
                <tr class="clickable" :class="{'drill-open':isDrillOpen('so_cust',row.customer)}"
                    @click="toggleDrill('so_cust', row.customer, 'customer_order_items', {customer: row.customer})">
                  <td><strong>{{ row.customer }}</strong> <span class="sd-chevron" :class="{open:isDrillOpen('so_cust',row.customer)}">▾</span></td>
                  <td class="sd-amt">{{ fmt(row.order_value) }}</td>
                  <td class="sd-amt">{{ row.orders }}</td>
                </tr>
                <tr v-if="isDrillOpen('so_cust', row.customer)" class="sd-drill">
                  <td colspan="3" style="padding:0">
                    <div class="sd-drill-inner">
                      <div class="sd-drill-title">▸ {{ row.customer }} — item codes &amp; commercial names (orders)</div>
                      <div v-if="isDrillLoading('so_cust', row.customer)" class="sd-drill-loading"><span class="sd-mini-spin"></span> Loading…</div>
                      <template v-else-if="getDrillRows('so_cust', row.customer).length">
                        <table>
                          <thead><tr>
                            <th>Item Code</th>
                            <th>Commercial Name</th>
                            <th>UOM</th>
                            <th class="sd-th-r">Qty</th>
                            <th class="sd-th-r">Order Value</th>
                            <th>Sales Person</th>
                          </tr></thead>
                          <tbody>
                            <tr v-for="d in getDrillRows('so_cust', row.customer)" :key="d.item_code">
                              <td><span class="sd-mono">{{ d.item_code }}</span></td>
                              <td>{{ cleanName(d.commercial_name || d.item_name) }}</td>
                              <td>{{ d.uom }}</td>
                              <td class="sd-amt">{{ fmtQty(d.qty) }}</td>
                              <td class="sd-amt">{{ fmt(d.order_value) }}</td>
                              <td>{{ d.sales_person || '—' }}</td>
                            </tr>
                          </tbody>
                        </table>
                      </template>
                      <div v-else class="sd-drill-empty">No item details found.</div>
                    </div>
                  </td>
                </tr>
              </template>
              <tr v-if="!topCustomers.by_order.length"><td colspan="3" class="sd-empty">No data.</td></tr>
            </tbody>
          </table>
        </div>
        <div v-if="remainingCount('so_cust', sortedRows('so_cust', topCustomers.by_order, ['order_value','orders'])) > 0" style="text-align:center;padding:14px 0 4px">
          <button class="sd-xbtn" @click="loadMore('so_cust')">Load More — {{ remainingCount('so_cust', sortedRows('so_cust', topCustomers.by_order, ['order_value','orders'])) }} more rows</button>
        </div>
      </div>
    </div>

    <!-- ═══════════════ COMMERCIAL NAME ═══════════════ -->
    <div v-show="activeTab==='commercial_name'" class="sd-body">
      <div class="sd-2col">
        <div class="sd-card full">
          <div class="sd-ch"><span class="sd-ct">Revenue by Commercial Name</span><span class="sd-badge inv">Invoices</span></div>
          <div :style="{position:'relative',height:Math.max(240,commercialName.by_invoice.length*36+60)+'px'}"><canvas id="cnSIChart" role="img" aria-label="Commercial name revenue from invoices"></canvas></div>
        </div>
        <div class="sd-card full">
          <div class="sd-ch"><span class="sd-ct">Order Value by Commercial Name</span><span class="sd-badge ord">Orders</span></div>
          <div :style="{position:'relative',height:Math.max(240,commercialName.by_order.length*36+60)+'px'}"><canvas id="cnSOChart" role="img" aria-label="Commercial name order value"></canvas></div>
        </div>
      </div>
      <!-- Commercial name table → drill to item codes + customers -->
      <div class="sd-card" style="margin-top:16px">
        <div class="sd-ch"><span class="sd-ct">Commercial Name Details</span><div style="display:flex;gap:6px"><button class="sd-xbtn" @click="expandAll('cn', commercialName.by_invoice, 'commercial_name_detail', 'commercial_name', r=>({commercial_name:r.commercial_name}))">⊞ Expand All</button><button class="sd-xbtn" @click="collapseAll('cn')">⊟ Collapse All</button></div></div>
        <div class="sd-toolbar">
          <input v-model="filterText['cn']" class="sd-search" placeholder="Filter commercial names…"/>
        </div>
        <div class="sd-twrap">
          <table class="sd-table">
            <thead><tr>
              <th @click="toggleSort('cn','commercial_name')">Commercial Name <span :class="['sd-sort',{on:sortIconActive('cn','commercial_name')}]">{{ sortIcon('cn','commercial_name') }}</span></th>
              <th class="sd-th-r" @click="toggleSort('cn','revenue')">Revenue (SI) <span :class="['sd-sort',{on:sortIconActive('cn','revenue')}]">{{ sortIcon('cn','revenue') }}</span></th>
              <th class="sd-th-r" @click="toggleSort('cn','qty')">Qty (SI) <span :class="['sd-sort',{on:sortIconActive('cn','qty')}]">{{ sortIcon('cn','qty') }}</span></th>
              <th class="sd-th-r" @click="toggleSort('cn','invoices')">Invoices <span :class="['sd-sort',{on:sortIconActive('cn','invoices')}]">{{ sortIcon('cn','invoices') }}</span></th>
              <th class="sd-th-r">Order Value (SO)</th>
              <th class="sd-th-r">Qty (SO)</th>
            </tr></thead>
            <tbody>
              <template v-for="row in paged('cn', sortedRows('cn', commercialName.by_invoice, ['revenue','qty','invoices']))" :key="row.commercial_name">
                <tr class="clickable" :class="{'drill-open':isDrillOpen('cn',row.commercial_name)}"
                    @click="toggleDrill('cn', row.commercial_name, 'commercial_name_detail', {commercial_name: row.commercial_name})">
                  <td><strong>{{ cleanName(row.commercial_name) }}</strong> <span class="sd-chevron" :class="{open:isDrillOpen('cn',row.commercial_name)}">▾</span></td>
                  <td class="sd-amt">{{ fmt(row.revenue) }}</td>
                  <td class="sd-amt">{{ fmtQty(row.qty) }}</td>
                  <td class="sd-amt">{{ row.invoices }}</td>
                  <td class="sd-amt">{{ fmt((commercialName.by_order.find(r=>r.commercial_name===row.commercial_name)||{}).order_value) }}</td>
                  <td class="sd-amt">{{ fmtQty((commercialName.by_order.find(r=>r.commercial_name===row.commercial_name)||{}).qty) }}</td>
                </tr>
                <tr v-if="isDrillOpen('cn', row.commercial_name)" class="sd-drill">
                  <td colspan="6" style="padding:0">
                    <div class="sd-drill-inner">
                      <div class="sd-drill-title">▸ {{ cleanName(row.commercial_name) }} — item codes &amp; top customers</div>
                      <div v-if="isDrillLoading('cn', row.commercial_name)" class="sd-drill-loading"><span class="sd-mini-spin"></span> Loading…</div>
                      <template v-else-if="getDrillRows('cn', row.commercial_name).length">
                        <table>
                          <thead><tr>
                            <th>Color</th>
                            <th>UOM</th>
                            <th class="sd-th-r">Qty</th>
                            <th class="sd-th-r">Revenue</th>
                            <th>Sales Person</th>
                          </tr></thead>
                          <tbody>
                            <tr v-for="d in getDrillRows('cn', row.commercial_name)" :key="d.item_code+d.customer">
                              <td>{{ d.color || d.item_name || '—' }}</td>
                              <td>{{ d.uom }}</td>
                              <td class="sd-amt">{{ fmtQty(d.qty) }}</td>
                              <td class="sd-amt">{{ fmt(d.revenue) }}</td>
                              <td>{{ d.sales_person || '—' }}</td>
                            </tr>
                          </tbody>
                        </table>
                      </template>
                      <div v-else class="sd-drill-empty">No detail data found.</div>
                    </div>
                  </td>
                </tr>
              </template>
              <tr v-if="!commercialName.by_invoice.length"><td colspan="6" class="sd-empty">No data available.</td></tr>
            </tbody>
          </table>
        </div>
        <div v-if="remainingCount('cn', sortedRows('cn', commercialName.by_invoice, ['revenue','qty','invoices'])) > 0" style="text-align:center;padding:14px 0 4px">
          <button class="sd-xbtn" @click="loadMore('cn')">Load More — {{ remainingCount('cn', sortedRows('cn', commercialName.by_invoice, ['revenue','qty','invoices'])) }} more rows</button>
        </div>
      </div>
    </div>

    <!-- ═══════════════ UOM ═══════════════ -->
    <div v-show="activeTab==='uom'" class="sd-body">
      <div class="sd-2col">
        <div class="sd-card full">
          <div class="sd-ch"><span class="sd-ct">Revenue by UOM</span><span class="sd-badge inv">Invoices</span></div>
          <div style="position:relative;height:260px"><canvas id="uomSIChart" role="img" aria-label="UOM revenue invoices"></canvas></div>
        </div>
        <div class="sd-card full">
          <div class="sd-ch"><span class="sd-ct">Order Value by UOM</span><span class="sd-badge ord">Orders</span></div>
          <div style="position:relative;height:260px"><canvas id="uomSOChart" role="img" aria-label="UOM order value"></canvas></div>
        </div>
      </div>
      <div class="sd-card" style="margin-top:16px">
        <div class="sd-ch"><span class="sd-ct">UOM Details</span><div style="display:flex;gap:6px"><button class="sd-xbtn" @click="expandAll('uom', uomData.by_invoice, 'uom_items', 'uom', r=>({uom:r.uom}))">⊞ Expand All</button><button class="sd-xbtn" @click="collapseAll('uom')">⊟ Collapse All</button></div></div>
        <div class="sd-toolbar">
          <input v-model="filterText['uom']" class="sd-search" placeholder="Filter UOM…"/>
        </div>
        <div class="sd-twrap">
          <table class="sd-table">
            <thead><tr>
              <th @click="toggleSort('uom','uom')">UOM <span :class="['sd-sort',{on:sortIconActive('uom','uom')}]">{{ sortIcon('uom','uom') }}</span></th>
              <th class="sd-th-r" @click="toggleSort('uom','revenue')">Revenue (SI) <span :class="['sd-sort',{on:sortIconActive('uom','revenue')}]">{{ sortIcon('uom','revenue') }}</span></th>
              <th class="sd-th-r">Total Qty (SI)</th>
              <th class="sd-th-r">Invoices</th>
              <th class="sd-th-r">Order Value (SO)</th>
              <th class="sd-th-r">Total Qty (SO)</th>
              <th class="sd-th-r">Orders</th>
            </tr></thead>
            <tbody>
              <template v-for="row in paged('uom', sortedRows('uom', uomData.by_invoice, ['revenue','total_qty','invoices']))" :key="row.uom">
                <tr class="clickable" :class="{'drill-open':isDrillOpen('uom',row.uom)}"
                    @click="toggleDrill('uom', row.uom, 'uom_items', {uom: row.uom})">
                  <td><strong>{{ row.uom || '—' }}</strong> <span class="sd-chevron" :class="{open:isDrillOpen('uom',row.uom)}">▾</span></td>
                  <td class="sd-amt">{{ fmt(row.revenue) }}</td>
                  <td class="sd-amt">{{ fmtQty(row.total_qty) }}</td>
                  <td class="sd-amt">{{ row.invoices }}</td>
                  <td class="sd-amt">{{ fmt((uomData.by_order.find(r=>r.uom===row.uom)||{}).order_value) }}</td>
                  <td class="sd-amt">{{ fmtQty((uomData.by_order.find(r=>r.uom===row.uom)||{}).total_qty) }}</td>
                  <td class="sd-amt">{{ (uomData.by_order.find(r=>r.uom===row.uom)||{}).orders || '—' }}</td>
                </tr>
                <tr v-if="isDrillOpen('uom', row.uom)" class="sd-drill">
                  <td colspan="7" style="padding:0">
                    <div class="sd-drill-inner">
                      <div class="sd-drill-title">▸ {{ row.uom }} — item codes &amp; commercial names</div>
                      <div v-if="isDrillLoading('uom', row.uom)" class="sd-drill-loading"><span class="sd-mini-spin"></span> Loading…</div>
                      <template v-else-if="getDrillRows('uom', row.uom).length">
                        <table>
                          <thead><tr>
                            <th>Item Code</th>
                            <th>Commercial Name</th>
                            <th class="sd-th-r">Qty</th>
                            <th class="sd-th-r">Revenue</th>
                          </tr></thead>
                          <tbody>
                            <tr v-for="d in getDrillRows('uom', row.uom)" :key="d.item_code">
                              <td><span class="sd-mono">{{ d.item_code }}</span></td>
                              <td>{{ cleanName(d.commercial_name || d.item_name) }}</td>
                              <td class="sd-amt">{{ fmtQty(d.qty) }}</td>
                              <td class="sd-amt">{{ fmt(d.revenue) }}</td>
                            </tr>
                          </tbody>
                        </table>
                      </template>
                      <div v-else class="sd-drill-empty">No item data found.</div>
                    </div>
                  </td>
                </tr>
              </template>
              <tr v-if="!uomData.by_invoice.length"><td colspan="7" class="sd-empty">No data available.</td></tr>
            </tbody>
          </table>
        </div>
        <div v-if="remainingCount('uom', sortedRows('uom', uomData.by_invoice, ['revenue','total_qty','invoices'])) > 0" style="text-align:center;padding:14px 0 4px">
          <button class="sd-xbtn" @click="loadMore('uom')">Load More — {{ remainingCount('uom', sortedRows('uom', uomData.by_invoice, ['revenue','total_qty','invoices'])) }} more rows</button>
        </div>
      </div>
    </div>

    <!-- ═══════════════ STATE ═══════════════ -->
    <div v-show="activeTab==='state'" class="sd-body">
      <div class="sd-2col">
        <div class="sd-card full">
          <div class="sd-ch"><span class="sd-ct">Revenue by State</span><span class="sd-badge inv">Invoices</span></div>
          <div :style="{position:'relative',height:Math.max(240,stateData.by_invoice.length*36+60)+'px'}"><canvas id="stateSIChart" role="img" aria-label="Revenue by state invoices"></canvas></div>
        </div>
        <div class="sd-card full">
          <div class="sd-ch"><span class="sd-ct">Order Value by State</span><span class="sd-badge ord">Orders</span></div>
          <div :style="{position:'relative',height:Math.max(240,stateData.by_order.length*36+60)+'px'}"><canvas id="stateSOChart" role="img" aria-label="Order value by state"></canvas></div>
        </div>
      </div>
      <div class="sd-card" style="margin-top:16px">
        <div class="sd-ch"><span class="sd-ct">State Details</span><div style="display:flex;gap:6px"><button class="sd-xbtn" @click="expandAll('state', stateData.by_invoice, 'state_customers', 'state', r=>({state:r.state}))">⊞ Expand All</button><button class="sd-xbtn" @click="collapseAll('state')">⊟ Collapse All</button></div></div>
        <div class="sd-toolbar">
          <input v-model="filterText['state']" class="sd-search" placeholder="Filter states…"/>
        </div>
        <div class="sd-twrap">
          <table class="sd-table">
            <thead><tr>
              <th @click="toggleSort('state','state')">State <span :class="['sd-sort',{on:sortIconActive('state','state')}]">{{ sortIcon('state','state') }}</span></th>
              <th class="sd-th-r" @click="toggleSort('state','revenue')">Revenue (SI) <span :class="['sd-sort',{on:sortIconActive('state','revenue')}]">{{ sortIcon('state','revenue') }}</span></th>
              <th class="sd-th-r">Collected (SI)</th>
              <th class="sd-th-r" @click="toggleSort('state','invoices')">Invoices <span :class="['sd-sort',{on:sortIconActive('state','invoices')}]">{{ sortIcon('state','invoices') }}</span></th>
              <th class="sd-th-r">Order Value (SO)</th>
              <th class="sd-th-r">Orders</th>
            </tr></thead>
            <tbody>
              <template v-for="row in paged('state', sortedRows('state', stateData.by_invoice, ['revenue','collected','invoices']))" :key="row.state">
                <tr class="clickable" :class="{'drill-open':isDrillOpen('state',row.state)}"
                    @click="toggleDrill('state', row.state, 'state_customers', {state: row.state})">
                  <td><strong>{{ row.state || '—' }}</strong> <span class="sd-chevron" :class="{open:isDrillOpen('state',row.state)}">▾</span></td>
                  <td class="sd-amt">{{ fmt(row.revenue) }}</td>
                  <td class="sd-amt">{{ fmt(row.collected) }}</td>
                  <td class="sd-amt">{{ row.invoices }}</td>
                  <td class="sd-amt">{{ fmt((stateData.by_order.find(r=>r.state===row.state)||{}).order_value) }}</td>
                  <td class="sd-amt">{{ (stateData.by_order.find(r=>r.state===row.state)||{}).orders || '—' }}</td>
                </tr>
                <tr v-if="isDrillOpen('state', row.state)" class="sd-drill">
                  <td colspan="6" style="padding:0">
                    <div class="sd-drill-inner">
                      <div class="sd-drill-title">▸ {{ row.state }} — customers</div>
                      <div v-if="isDrillLoading('state', row.state)" class="sd-drill-loading"><span class="sd-mini-spin"></span> Loading…</div>
                      <template v-else-if="getDrillRows('state', row.state).length">
                        <table>
                          <thead><tr>
                            <th>City</th>
                            <th class="sd-th-r">Revenue</th>
                            <th class="sd-th-r">Invoices</th>
                            <th class="sd-th-r">Order Value</th>
                            <th class="sd-th-r">Orders</th>
                          </tr></thead>
                          <tbody>
                            <tr v-for="d in getDrillRows('state', row.state)" :key="d.city || d.customer">
                              <td>{{ d.city || d.customer || '—' }}</td>
                              <td class="sd-amt">{{ fmt(d.revenue) }}</td>
                              <td class="sd-amt">{{ d.invoices }}</td>
                              <td class="sd-amt">{{ fmt(d.order_value) }}</td>
                              <td class="sd-amt">{{ d.orders || '—' }}</td>
                            </tr>
                          </tbody>
                        </table>
                      </template>
                      <div v-else class="sd-drill-empty">No customers found for this state.</div>
                    </div>
                  </td>
                </tr>
              </template>
              <tr v-if="!stateData.by_invoice.length"><td colspan="6" class="sd-empty">No data available.</td></tr>
            </tbody>
          </table>
        </div>
        <div v-if="remainingCount('state', sortedRows('state', stateData.by_invoice, ['revenue','collected','invoices'])) > 0" style="text-align:center;padding:14px 0 4px">
          <button class="sd-xbtn" @click="loadMore('state')">Load More — {{ remainingCount('state', sortedRows('state', stateData.by_invoice, ['revenue','collected','invoices'])) }} more rows</button>
        </div>
      </div>
    </div>

    <!-- ═══════════════ SALES PERSON ═══════════════ -->
    <div v-show="activeTab==='salesperson'" class="sd-body">
      <div class="sd-2col">
        <div class="sd-card full">
          <div class="sd-ch"><span class="sd-ct">Revenue by Sales Person</span><span class="sd-badge inv">Invoices</span></div>
          <div :style="{position:'relative',height:Math.max(240,spData.by_invoice.length*36+60)+'px'}"><canvas id="spSIChart" role="img" aria-label="Revenue by sales person invoices"></canvas></div>
        </div>
        <div class="sd-card full">
          <div class="sd-ch"><span class="sd-ct">Order Value by Sales Person</span><span class="sd-badge ord">Orders</span></div>
          <div :style="{position:'relative',height:Math.max(240,spData.by_order.length*36+60)+'px'}"><canvas id="spSOChart" role="img" aria-label="Order value by sales person"></canvas></div>
        </div>
      </div>
      <div class="sd-card" style="margin-top:16px">
        <div class="sd-ch"><span class="sd-ct">Sales Person Performance</span><div style="display:flex;gap:6px"><button class="sd-xbtn" @click="expandAll('sp', spData.by_invoice, 'salesperson_items', 'sales_person', r=>({sales_person:r.sales_person}))">⊞ Expand All</button><button class="sd-xbtn" @click="collapseAll('sp')">⊟ Collapse All</button></div></div>
        <div class="sd-toolbar">
          <input v-model="filterText['sp']" class="sd-search" placeholder="Filter sales persons…"/>
        </div>
        <div class="sd-twrap">
          <table class="sd-table">
            <thead><tr>
              <th>#</th>
              <th @click="toggleSort('sp','sales_person')">Sales Person <span :class="['sd-sort',{on:sortIconActive('sp','sales_person')}]">{{ sortIcon('sp','sales_person') }}</span></th>
              <th class="sd-th-r" @click="toggleSort('sp','revenue')">Revenue (SI) <span :class="['sd-sort',{on:sortIconActive('sp','revenue')}]">{{ sortIcon('sp','revenue') }}</span></th>
              <th class="sd-th-r">Collected (SI)</th>
              <th class="sd-th-r" @click="toggleSort('sp','invoices')">Invoices <span :class="['sd-sort',{on:sortIconActive('sp','invoices')}]">{{ sortIcon('sp','invoices') }}</span></th>
              <th class="sd-th-r">Order Value (SO)</th>
              <th class="sd-th-r">Orders</th>
            </tr></thead>
            <tbody>
              <template v-for="(row,i) in paged('sp', sortedRows('sp', spData.by_invoice, ['revenue','collected','invoices']))" :key="row.sales_person">
                <tr class="clickable" :class="{'drill-open':isDrillOpen('sp',row.sales_person)}"
                    @click="toggleDrill('sp', row.sales_person, 'salesperson_items', {sales_person: row.sales_person})">
                  <td style="color:#9E9E9E;font-size:12px">{{ i+1 }}</td>
                  <td><strong>{{ row.sales_person || '—' }}</strong> <span class="sd-chevron" :class="{open:isDrillOpen('sp',row.sales_person)}">▾</span></td>
                  <td class="sd-amt">{{ fmt(row.revenue) }}</td>
                  <td class="sd-amt">{{ fmt(row.collected) }}</td>
                  <td class="sd-amt">{{ row.invoices }}</td>
                  <td class="sd-amt">{{ fmt((spData.by_order.find(r=>r.sales_person===row.sales_person)||{}).order_value) }}</td>
                  <td class="sd-amt">{{ (spData.by_order.find(r=>r.sales_person===row.sales_person)||{}).orders || '—' }}</td>
                </tr>
                <tr v-if="isDrillOpen('sp', row.sales_person)" class="sd-drill">
                  <td colspan="7" style="padding:0">
                    <div class="sd-drill-inner">
                      <div class="sd-drill-title">▸ {{ row.sales_person }} — item codes &amp; customers</div>
                      <div v-if="isDrillLoading('sp', row.sales_person)" class="sd-drill-loading"><span class="sd-mini-spin"></span> Loading…</div>
                      <template v-else-if="getDrillRows('sp', row.sales_person).length">
                        <table>
                          <thead><tr>
                            <th>Item Code</th>
                            <th>Commercial Name</th>
                            <th>Customer</th>
                            <th>UOM</th>
                            <th class="sd-th-r">Qty</th>
                            <th class="sd-th-r">Revenue</th>
                          </tr></thead>
                          <tbody>
                            <tr v-for="d in getDrillRows('sp', row.sales_person)" :key="d.item_code+d.customer">
                              <td><span class="sd-mono">{{ d.item_code }}</span></td>
                              <td>{{ cleanName(d.commercial_name || d.item_name) }}</td>
                              <td>{{ d.customer }}</td>
                              <td>{{ d.uom }}</td>
                              <td class="sd-amt">{{ fmtQty(d.qty) }}</td>
                              <td class="sd-amt">{{ fmt(d.revenue) }}</td>
                            </tr>
                          </tbody>
                        </table>
                      </template>
                      <div v-else class="sd-drill-empty">No item data found.</div>
                    </div>
                  </td>
                </tr>
              </template>
              <tr v-if="!spData.by_invoice.length"><td colspan="7" class="sd-empty">No data available.</td></tr>
            </tbody>
          </table>
        </div>
        <div v-if="remainingCount('sp', sortedRows('sp', spData.by_invoice, ['revenue','collected','invoices'])) > 0" style="text-align:center;padding:14px 0 4px">
          <button class="sd-xbtn" @click="loadMore('sp')">Load More — {{ remainingCount('sp', sortedRows('sp', spData.by_invoice, ['revenue','collected','invoices'])) }} more rows</button>
        </div>
      </div>
    </div>

    <!-- ═══════════════ TEAM (DEPARTMENT) ═══════════════ -->
    <div v-show="activeTab==='team'" class="sd-body">
      <div class="sd-2col">
        <div class="sd-card full">
          <div class="sd-ch"><span class="sd-ct">Revenue by Team</span><span class="sd-badge inv">Invoices</span></div>
          <div :style="{position:'relative',height:Math.max(240,teamData.by_invoice.length*36+60)+'px'}"><canvas id="teamSIChart" role="img" aria-label="Revenue by team invoices"></canvas></div>
        </div>
        <div class="sd-card full">
          <div class="sd-ch"><span class="sd-ct">Order Value by Team</span><span class="sd-badge ord">Orders</span></div>
          <div :style="{position:'relative',height:Math.max(240,teamData.by_order.length*36+60)+'px'}"><canvas id="teamSOChart" role="img" aria-label="Order value by team"></canvas></div>
        </div>
      </div>
      <div class="sd-card" style="margin-top:16px">
        <div class="sd-ch"><span class="sd-ct">Team Performance</span><div style="display:flex;gap:6px"><button class="sd-xbtn" @click="expandAll('team', teamData.by_invoice, 'team_customers', 'department', r=>({department:r.department}))">⊞ Expand All</button><button class="sd-xbtn" @click="collapseAll('team')">⊟ Collapse All</button></div></div>
        <div class="sd-toolbar">
          <input v-model="filterText['team']" class="sd-search" placeholder="Filter teams…"/>
        </div>
        <div class="sd-twrap">
          <table class="sd-table">
            <thead><tr>
              <th>#</th>
              <th @click="toggleSort('team','department')">Team <span :class="['sd-sort',{on:sortIconActive('team','department')}]">{{ sortIcon('team','department') }}</span></th>
              <th class="sd-th-r" @click="toggleSort('team','revenue')">Revenue (SI) <span :class="['sd-sort',{on:sortIconActive('team','revenue')}]">{{ sortIcon('team','revenue') }}</span></th>
              <th class="sd-th-r">Collected (SI)</th>
              <th>Collection %</th>
              <th class="sd-th-r" @click="toggleSort('team','invoices')">Invoices <span :class="['sd-sort',{on:sortIconActive('team','invoices')}]">{{ sortIcon('team','invoices') }}</span></th>
              <th class="sd-th-r">Order Value (SO)</th>
              <th class="sd-th-r">Orders</th>
            </tr></thead>
            <tbody>
              <template v-for="(row,i) in paged('team', sortedRows('team', teamData.by_invoice, ['revenue','collected','invoices']))" :key="row.department">
                <tr class="clickable" :class="{'drill-open':isDrillOpen('team',row.department)}"
                    @click="toggleDrill('team', row.department, 'team_customers', {department: row.department})">
                  <td style="color:#9E9E9E;font-size:12px">{{ i+1 }}</td>
                  <td><strong>{{ row.department || 'No Department' }}</strong> <span class="sd-chevron" :class="{open:isDrillOpen('team',row.department)}">▾</span></td>
                  <td class="sd-amt">{{ fmt(row.revenue) }}</td>
                  <td class="sd-amt">{{ fmt(row.collected) }}</td>
                  <td>
                    <div style="display:flex;align-items:center;gap:6px">
                      <div class="sd-sbw" style="width:60px"><div class="sd-sbar" :style="{width:pct(row.collected,row.revenue)+'%',background:'#2E7D32'}"></div></div>
                      <span style="font-size:11px;color:#757575">{{ pct(row.collected,row.revenue) }}%</span>
                    </div>
                  </td>
                  <td class="sd-amt">{{ row.invoices }}</td>
                  <td class="sd-amt">{{ fmt((teamData.by_order.find(r=>r.department===row.department)||{}).order_value) }}</td>
                  <td class="sd-amt">{{ (teamData.by_order.find(r=>r.department===row.department)||{}).orders || '—' }}</td>
                </tr>
                <tr v-if="isDrillOpen('team', row.department)" class="sd-drill">
                  <td colspan="8" style="padding:0">
                    <div class="sd-drill-inner">
                      <div class="sd-drill-title">▸ {{ row.department || 'No Department' }} — customers &amp; sales persons</div>
                      <div v-if="isDrillLoading('team', row.department)" class="sd-drill-loading"><span class="sd-mini-spin"></span> Loading…</div>
                      <template v-else-if="getDrillRows('team', row.department).length">
                        <table>
                          <thead><tr>
                            <th>Customer</th>
                            <th class="sd-th-r">Revenue</th>
                            <th class="sd-th-r">Invoices</th>
                            <th>Sales Person</th>
                            <th class="sd-th-r">Order Value</th>
                            <th class="sd-th-r">Orders</th>
                          </tr></thead>
                          <tbody>
                            <tr v-for="d in getDrillRows('team', row.department)" :key="d.customer">
                              <td>{{ d.customer }}</td>
                              <td class="sd-amt">{{ fmt(d.revenue) }}</td>
                              <td class="sd-amt">{{ d.invoices }}</td>
                              <td>{{ d.sales_person || '—' }}</td>
                              <td class="sd-amt">{{ fmt(d.order_value) }}</td>
                              <td class="sd-amt">{{ d.orders || '—' }}</td>
                            </tr>
                          </tbody>
                        </table>
                      </template>
                      <div v-else class="sd-drill-empty">No data found.</div>
                    </div>
                  </td>
                </tr>
              </template>
              <tr v-if="!teamData.by_invoice.length"><td colspan="8" class="sd-empty">No data available.</td></tr>
            </tbody>
          </table>
        </div>
        <div v-if="remainingCount('team', sortedRows('team', teamData.by_invoice, ['revenue','collected','invoices'])) > 0" style="text-align:center;padding:14px 0 4px">
          <button class="sd-xbtn" @click="loadMore('team')">Load More — {{ remainingCount('team', sortedRows('team', teamData.by_invoice, ['revenue','collected','invoices'])) }} more rows</button>
        </div>
      </div>
    </div>

    <!-- ═══════════════ COST CENTER ═══════════════ -->
    <div v-show="activeTab==='cost_center'" class="sd-body">
      <div class="sd-2col">
        <div class="sd-card full">
          <div class="sd-ch"><span class="sd-ct">Revenue by Cost Center</span><span class="sd-badge inv">Invoices</span></div>
          <div :style="{position:'relative',height:Math.max(240,ccData.by_invoice.length*36+60)+'px'}"><canvas id="ccSIChart" role="img" aria-label="Revenue by cost center invoices"></canvas></div>
        </div>
        <div class="sd-card full">
          <div class="sd-ch"><span class="sd-ct">Order Value by Cost Center</span><span class="sd-badge ord">Orders</span></div>
          <div :style="{position:'relative',height:Math.max(240,ccData.by_order.length*36+60)+'px'}"><canvas id="ccSOChart" role="img" aria-label="Order value by cost center"></canvas></div>
        </div>
      </div>
      <div class="sd-card" style="margin-top:16px">
        <div class="sd-ch"><span class="sd-ct">Cost Center Details</span><div style="display:flex;gap:6px"><button class="sd-xbtn" @click="expandAll('cc', ccData.by_invoice, 'cost_center_customers', 'cost_center', r=>({cost_center:r.cost_center}))">⊞ Expand All</button><button class="sd-xbtn" @click="collapseAll('cc')">⊟ Collapse All</button></div></div>
        <div class="sd-toolbar">
          <input v-model="filterText['cc']" class="sd-search" placeholder="Filter cost centers…"/>
        </div>
        <div class="sd-twrap">
          <table class="sd-table">
            <thead><tr>
              <th>#</th>
              <th @click="toggleSort('cc','cost_center')">Cost Center <span :class="['sd-sort',{on:sortIconActive('cc','cost_center')}]">{{ sortIcon('cc','cost_center') }}</span></th>
              <th class="sd-th-r" @click="toggleSort('cc','revenue')">Revenue (SI) <span :class="['sd-sort',{on:sortIconActive('cc','revenue')}]">{{ sortIcon('cc','revenue') }}</span></th>
              <th class="sd-th-r">Collected (SI)</th>
              <th>Collection %</th>
              <th class="sd-th-r" @click="toggleSort('cc','invoices')">Invoices <span :class="['sd-sort',{on:sortIconActive('cc','invoices')}]">{{ sortIcon('cc','invoices') }}</span></th>
              <th class="sd-th-r">Order Value (SO)</th>
              <th class="sd-th-r">Orders</th>
            </tr></thead>
            <tbody>
              <template v-for="(row,i) in paged('cc', sortedRows('cc', ccData.by_invoice, ['revenue','collected','invoices']))" :key="row.cost_center">
                <tr class="clickable" :class="{'drill-open':isDrillOpen('cc',row.cost_center)}"
                    @click="toggleDrill('cc', row.cost_center, 'cost_center_customers', {cost_center: row.cost_center})">
                  <td style="color:#9E9E9E;font-size:12px">{{ i+1 }}</td>
                  <td><strong>{{ row.cost_center }}</strong> <span class="sd-chevron" :class="{open:isDrillOpen('cc',row.cost_center)}">▾</span></td>
                  <td class="sd-amt">{{ fmt(row.revenue) }}</td>
                  <td class="sd-amt">{{ fmt(row.collected) }}</td>
                  <td>
                    <div style="display:flex;align-items:center;gap:6px">
                      <div class="sd-sbw" style="width:60px"><div class="sd-sbar" :style="{width:pct(row.collected,row.revenue)+'%',background:'#2E7D32'}"></div></div>
                      <span style="font-size:11px;color:#757575">{{ pct(row.collected,row.revenue) }}%</span>
                    </div>
                  </td>
                  <td class="sd-amt">{{ row.invoices }}</td>
                  <td class="sd-amt">{{ fmt((ccData.by_order.find(r=>r.cost_center===row.cost_center)||{}).order_value) }}</td>
                  <td class="sd-amt">{{ (ccData.by_order.find(r=>r.cost_center===row.cost_center)||{}).orders || '—' }}</td>
                </tr>
                <tr v-if="isDrillOpen('cc', row.cost_center)" class="sd-drill">
                  <td colspan="8" style="padding:0">
                    <div class="sd-drill-inner">
                      <div class="sd-drill-title">▸ {{ row.cost_center }} — customers &amp; sales persons</div>
                      <div v-if="isDrillLoading('cc', row.cost_center)" class="sd-drill-loading"><span class="sd-mini-spin"></span> Loading…</div>
                      <template v-else-if="getDrillRows('cc', row.cost_center).length">
                        <table>
                          <thead><tr>
                            <th>Customer</th>
                            <th class="sd-th-r">Revenue</th>
                            <th class="sd-th-r">Invoices</th>
                            <th>Sales Person</th>
                            <th class="sd-th-r">Order Value</th>
                            <th class="sd-th-r">Orders</th>
                          </tr></thead>
                          <tbody>
                            <tr v-for="d in getDrillRows('cc', row.cost_center)" :key="d.customer">
                              <td>{{ d.customer }}</td>
                              <td class="sd-amt">{{ fmt(d.revenue) }}</td>
                              <td class="sd-amt">{{ d.invoices }}</td>
                              <td>{{ d.sales_person || '—' }}</td>
                              <td class="sd-amt">{{ fmt(d.order_value) }}</td>
                              <td class="sd-amt">{{ d.orders || '—' }}</td>
                            </tr>
                          </tbody>
                        </table>
                      </template>
                      <div v-else class="sd-drill-empty">No data found.</div>
                    </div>
                  </td>
                </tr>
              </template>
              <tr v-if="!ccData.by_invoice.length"><td colspan="8" class="sd-empty">No data available.</td></tr>
            </tbody>
          </table>
        </div>
        <div v-if="remainingCount('cc', sortedRows('cc', ccData.by_invoice, ['revenue','collected','invoices'])) > 0" style="text-align:center;padding:14px 0 4px">
          <button class="sd-xbtn" @click="loadMore('cc')">Load More — {{ remainingCount('cc', sortedRows('cc', ccData.by_invoice, ['revenue','collected','invoices'])) }} more rows</button>
        </div>
      </div>
    </div>

    <!-- ═══════════════ NAMING SERIES ═══════════════ -->
    <div v-show="activeTab==='naming_series'" class="sd-body">
      <div class="sd-info-bar">
        <span>📋</span>
        <span>Naming series encodes your <strong>branch / location / year</strong> — e.g. <code>PTGB26</code> = Pranera Tirupur Garments B2B FY2026, <code>PFGB26</code> = Pranera Fashions Garments B2B.</span>
      </div>
      <div class="sd-2col" style="margin-top:14px">
        <div class="sd-card full">
          <div class="sd-ch"><span class="sd-ct">Revenue by Naming Series</span><span class="sd-badge inv">Invoices</span></div>
          <div :style="{position:'relative',height:Math.max(280,nsData.by_invoice.length*34+60)+'px'}"><canvas id="nsSIChart" role="img" aria-label="Revenue by naming series invoices"></canvas></div>
        </div>
        <div class="sd-card full">
          <div class="sd-ch"><span class="sd-ct">Order Value by Naming Series</span><span class="sd-badge ord">Orders</span></div>
          <div :style="{position:'relative',height:Math.max(280,nsData.by_order.length*34+60)+'px'}"><canvas id="nsSOChart" role="img" aria-label="Order value by naming series"></canvas></div>
        </div>
      </div>
      <div class="sd-card" style="margin-top:16px">
        <div class="sd-ch"><span class="sd-ct">Naming Series Details</span><div style="display:flex;gap:6px"><button class="sd-xbtn" @click="expandAll('ns', nsData.by_invoice, 'naming_series_docs', 'naming_series', r=>({naming_series:r.naming_series}))">⊞ Expand All</button><button class="sd-xbtn" @click="collapseAll('ns')">⊟ Collapse All</button></div></div>
        <div class="sd-toolbar">
          <input v-model="filterText['ns']" class="sd-search" placeholder="Filter series…"/>
        </div>
        <div class="sd-twrap">
          <table class="sd-table">
            <thead><tr>
              <th>#</th>
              <th @click="toggleSort('ns','naming_series')">Naming Series <span :class="['sd-sort',{on:sortIconActive('ns','naming_series')}]">{{ sortIcon('ns','naming_series') }}</span></th>
              <th>Prefix</th>
              <th class="sd-th-r" @click="toggleSort('ns','revenue')">Revenue (SI) <span :class="['sd-sort',{on:sortIconActive('ns','revenue')}]">{{ sortIcon('ns','revenue') }}</span></th>
              <th class="sd-th-r">Collected (SI)</th>
              <th class="sd-th-r" @click="toggleSort('ns','invoices')">Invoices <span :class="['sd-sort',{on:sortIconActive('ns','invoices')}]">{{ sortIcon('ns','invoices') }}</span></th>
              <th class="sd-th-r">Order Value (SO)</th>
              <th class="sd-th-r">Orders</th>
            </tr></thead>
            <tbody>
              <template v-for="(row,i) in paged('ns', sortedRows('ns', nsData.by_invoice, ['revenue','collected','invoices']))" :key="row.naming_series">
                <tr class="clickable" :class="{'drill-open':isDrillOpen('ns',row.naming_series)}"
                    @click="toggleDrill('ns', row.naming_series, 'naming_series_docs', {naming_series: row.naming_series})">
                  <td style="color:#9E9E9E;font-size:12px">{{ i+1 }}</td>
                  <td><code style="font-size:11px;background:#F5F5F5;padding:2px 6px;border-radius:4px">{{ row.naming_series }}</code> <span class="sd-chevron" :class="{open:isDrillOpen('ns',row.naming_series)}">▾</span></td>
                  <td><span class="sd-pill" style="background:#E3F2FD;color:#1565C0">{{ row.series_prefix }}</span></td>
                  <td class="sd-amt">{{ fmt(row.revenue) }}</td>
                  <td class="sd-amt">{{ fmt(row.collected) }}</td>
                  <td class="sd-amt">{{ row.invoices }}</td>
                  <td class="sd-amt">{{ fmt((nsData.by_order.find(r=>r.naming_series===row.naming_series)||{}).order_value) }}</td>
                  <td class="sd-amt">{{ (nsData.by_order.find(r=>r.naming_series===row.naming_series)||{}).orders || '—' }}</td>
                </tr>
                <tr v-if="isDrillOpen('ns', row.naming_series)" class="sd-drill">
                  <td colspan="8" style="padding:0">
                    <div class="sd-drill-inner">
                      <div class="sd-drill-title">▸ {{ row.naming_series }} — recent documents</div>
                      <div v-if="isDrillLoading('ns', row.naming_series)" class="sd-drill-loading"><span class="sd-mini-spin"></span> Loading…</div>
                      <template v-else-if="getDrillRows('ns', row.naming_series).length">
                        <table>
                          <thead><tr>
                            <th>Document ID</th>
                            <th>Customer</th>
                            <th>Date</th>
                            <th class="sd-th-r">Amount</th>
                            <th>Status</th>
                          </tr></thead>
                          <tbody>
                            <tr v-for="d in getDrillRows('ns', row.naming_series)" :key="d.name">
                              <td><a :href="'/app/sales-invoice/'+d.name" target="_blank" class="sd-link"><span class="sd-mono">{{ d.name }}</span></a></td>
                              <td>{{ d.customer }}</td>
                              <td>{{ fmtDate(d.date) }}</td>
                              <td class="sd-amt">{{ fmt(d.grand_total) }}</td>
                              <td><span class="sd-pill" :style="{background:siColor(d.status)+'22',color:siColor(d.status)}">{{ d.status }}</span></td>
                            </tr>
                          </tbody>
                        </table>
                      </template>
                      <div v-else class="sd-drill-empty">No documents found.</div>
                    </div>
                  </td>
                </tr>
              </template>
              <tr v-if="!nsData.by_invoice.length"><td colspan="8" class="sd-empty">No data available.</td></tr>
            </tbody>
          </table>
        </div>
        <div v-if="remainingCount('ns', sortedRows('ns', nsData.by_invoice, ['revenue','collected','invoices'])) > 0" style="text-align:center;padding:14px 0 4px">
          <button class="sd-xbtn" @click="loadMore('ns')">Load More — {{ remainingCount('ns', sortedRows('ns', nsData.by_invoice, ['revenue','collected','invoices'])) }} more rows</button>
        </div>
      </div>
    </div>

    <!-- ═══════════════ TRANSACTIONS ═══════════════ -->
    <div v-show="activeTab==='transactions'" class="sd-body">
      <div class="sd-card">
        <div class="sd-ch">
          <span class="sd-ct">Recent Transactions</span>
          <div style="display:flex;gap:6px;align-items:center"><button class="sd-xbtn" @click="expandAll('txn', filteredTransactions, 'transaction_items', 'name', r=>({doc_name:r.name, doc_type:r.type}))">⊞ Expand All</button><button class="sd-xbtn" @click="collapseAll('txn')">⊟ Collapse All</button></div>
          <input v-model="txSearch" class="sd-input" placeholder="Search customer or ID…" style="width:220px"/>
        </div>
        <div class="sd-twrap">
          <table class="sd-table">
            <thead><tr>
              <th @click="toggleSort('transactions','name')">ID <span :class="['sd-sort',{on:sortIconActive('transactions','name')}]">{{ sortIcon('transactions','name') }}</span></th>
              <th @click="toggleSort('transactions','type')">Type <span :class="['sd-sort',{on:sortIconActive('transactions','type')}]">{{ sortIcon('transactions','type') }}</span></th>
              <th @click="toggleSort('transactions','customer')">Customer <span :class="['sd-sort',{on:sortIconActive('transactions','customer')}]">{{ sortIcon('transactions','customer') }}</span></th>
              <th @click="toggleSort('transactions','date')">Date <span :class="['sd-sort',{on:sortIconActive('transactions','date')}]">{{ sortIcon('transactions','date') }}</span></th>
              <th class="sd-th-r" @click="toggleSort('transactions','grand_total')">Amount <span :class="['sd-sort',{on:sortIconActive('transactions','grand_total')}]">{{ sortIcon('transactions','grand_total') }}</span></th>
              <th @click="toggleSort('transactions','status')">Status <span :class="['sd-sort',{on:sortIconActive('transactions','status')}]">{{ sortIcon('transactions','status') }}</span></th>
            </tr></thead>
            <tbody>
              <template v-for="tx in filteredTransactions" :key="tx.name">
                <tr class="clickable" :class="{'drill-open':isDrillOpen('txn',tx.name)}"
                    @click="toggleDrill('txn', tx.name, 'transaction_items', {doc_name: tx.name, doc_type: tx.type})">
                  <td><a :href="txLink(tx)" target="_blank" class="sd-link" @click.stop>{{ tx.name }}</a> <span class="sd-chevron" :class="{open:isDrillOpen('txn',tx.name)}">▾</span></td>
                  <td><span :class="['sd-tbadge',tx.type==='Invoice'?'inv':'ord']">{{ tx.type }}</span></td>
                  <td>{{ tx.customer }}</td>
                  <td>{{ fmtDate(tx.date) }}</td>
                  <td class="sd-amt">{{ fmt(tx.grand_total) }}</td>
                  <td><span class="sd-pill" :style="{background:(tx.type==='Invoice'?siColor(tx.status):soColor(tx.status))+'22',color:tx.type==='Invoice'?siColor(tx.status):soColor(tx.status)}">{{ tx.status }}</span></td>
                </tr>
                <tr v-if="isDrillOpen('txn', tx.name)" class="sd-drill">
                  <td colspan="6" style="padding:0">
                    <div class="sd-drill-inner">
                      <div class="sd-drill-title">▸ {{ tx.name }} — line items</div>
                      <div v-if="isDrillLoading('txn', tx.name)" class="sd-drill-loading"><span class="sd-mini-spin"></span> Loading…</div>
                      <template v-else-if="getDrillRows('txn', tx.name).length">
                        <table>
                          <thead><tr>
                            <th>Item Code</th>
                            <th>Commercial Name</th>
                            <th>UOM</th>
                            <th class="sd-th-r">Qty</th>
                            <th class="sd-th-r">Rate</th>
                            <th class="sd-th-r">Amount</th>
                          </tr></thead>
                          <tbody>
                            <tr v-for="d in getDrillRows('txn', tx.name)" :key="d.item_code+d.idx">
                              <td><span class="sd-mono">{{ d.item_code }}</span></td>
                              <td>{{ cleanName(d.commercial_name || d.item_name) }}</td>
                              <td>{{ d.uom }}</td>
                              <td class="sd-amt">{{ fmtQty(d.qty) }}</td>
                              <td class="sd-amt">{{ fmt(d.rate) }}</td>
                              <td class="sd-amt">{{ fmt(d.amount) }}</td>
                            </tr>
                          </tbody>
                        </table>
                      </template>
                      <div v-else class="sd-drill-empty">No line items found.</div>
                    </div>
                  </td>
                </tr>
              </template>
              <tr v-if="!filteredTransactions.length"><td colspan="6" class="sd-empty">No transactions found.</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

  </template>
</div>
</template>

<script>
/* ──────────────────────────────────────────────────────────────
   Sales Dashboard — Vue 3 + Chart.js
   Ported from the original self-contained www/dashboards-sales.html
   into an SFC. Chart.js + the datalabels plugin are still loaded as
   CDN globals from frontend/index.html (this page's charting code
   references the global `Chart`, unchanged).
────────────────────────────────────────────────────────────── */
import { ref, computed, onMounted, nextTick } from 'vue'

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

export default {
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
      const isSystemManager = ref(false);

      const tabs = [
        { key: "overview",        icon: "📊", label: "Overview" },
        { key: "invoices",        icon: "🧾", label: "Sales Invoices" },
        { key: "orders",          icon: "📦", label: "Sales Orders" },
        { key: "commercial_name", icon: "🏷️",  label: "Commercial Name" },
        { key: "uom",             icon: "📐", label: "UOM" },
        { key: "state",           icon: "🗺️",  label: "State" },
        { key: "salesperson",     icon: "👤", label: "Sales Person" },
        { key: "team",            icon: "👥", label: "Team" },
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
      const teamData       = ref({ by_invoice: [], by_order: [] });
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
          const [s, t, tc, cn, uom, st, sp, team, cc, ns, tx] = await Promise.all([
            call("get_dashboard_summary",    a),
            call("get_monthly_trend",        { months: 6, company: a.company }),
            call("get_top_customers",        { ...a, limit: 300 }),
            call("get_commercial_name_wise", { ...a, limit: 300 }),
            call("get_uom_wise",             a),
            call("get_state_wise",           { ...a, limit: 300 }),
            call("get_salesperson_wise",     { ...a, limit: 300 }),
            call("get_team_wise",            { ...a, limit: 100 }),
            call("get_cost_center_wise",     { ...a, limit: 100 }),
            call("get_naming_series_wise",   { ...a, limit: 100 }),
            call("get_recent_transactions",  { limit: 300, company: a.company }),
          ]);
          const EMPTY_BI = { by_invoice: [], by_order: [] };
          summary.value        = s   || { invoice: { total_invoiced:0, total_collected:0, total_outstanding:0, collection_rate:0, count:0, status_breakdown:{} }, order: { total_ordered:0, count:0, status_breakdown:{}, delivery_breakdown:{} } };
          trend.value          = t   || { invoices: [], orders: [] };
          topCustomers.value   = tc  || { ...EMPTY_BI };
          commercialName.value = cn  || { ...EMPTY_BI };
          uomData.value        = uom || { ...EMPTY_BI };
          stateData.value      = st  || { ...EMPTY_BI };
          spData.value         = sp  || { ...EMPTY_BI };
          const safeTeam = team || { ...EMPTY_BI };
          if (safeTeam.by_invoice) safeTeam.by_invoice.forEach(r => { r.department = (r.department || '').replace(/ - PSS$/i, '').trim(); });
          if (safeTeam.by_order)   safeTeam.by_order.forEach(r =>   { r.department = (r.department || '').replace(/ - PSS$/i, '').trim(); });
          teamData.value        = safeTeam;
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
        buildHBar("teamSIChart", teamData.value.by_invoice, "revenue",     "#1565C0", "department");
        buildHBar("teamSOChart", teamData.value.by_order,   "order_value", "#0097A7", "department");
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
        call("check_app_permission", {}).then(v => { isSystemManager.value = !!v; }).catch(() => {});
      });



      /* ── table sort & filter ─────────────────────────────────── */
      const tableSort  = ref({});
      const filterText = ref({});

      /* ── "Load More" pagination (client-side, over already-fetched rows) */
      const PAGE_SIZE = 15;
      const PAGE_STEP = 25;
      const pageSize  = ref({});

      function paged(tableKey, rows) {
        const n = pageSize.value[tableKey] || PAGE_SIZE;
        return rows.slice(0, n);
      }
      function loadMore(tableKey) {
        pageSize.value[tableKey] = (pageSize.value[tableKey] || PAGE_SIZE) + PAGE_STEP;
      }
      function remainingCount(tableKey, rows) {
        const shown = pageSize.value[tableKey] || PAGE_SIZE;
        return Math.max(0, rows.length - shown);
      }

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
        activeTab, tabs, txSearch, isSystemManager,
        summary, trend, topCustomers,
        drill, drillCache, isDrillOpen, getDrillRows, isDrillLoading, toggleDrill, expandAll, collapseAll,
        tableSort, filterText, getSort, toggleSort, sortedRows, sortIcon, sortIconActive,
        paged, loadMore, remainingCount,
        commercialName, uomData, stateData, spData, teamData, ccData, nsData, transactions,
        filteredTransactions,
        fmt, fmtQty, fmtDate, pct, txLink, cleanName,
        applyRange, loadAll,
        siColor, soColor, delColor,
      };
    },
}

</script>

<style scoped>
  <style>
:root{
  --b:#1565C0;--t:#0097A7;--g:#2E7D32;--a:#F57C00;--r:#C62828;--m:#757575;
  --br:#E0E0E0;--bg:#F8FAFB;--tx:#212121;--sh:0 1px 4px rgba(0,0,0,.07);--rd:10px;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;font-size:13px;color:var(--tx);background:var(--bg);min-height:100vh}

/* header */
.sd-header{background:#fff;border-bottom:1px solid var(--br);padding:12px 20px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;position:sticky;top:0;z-index:100}
.sd-header__left{display:flex;align-items:center;gap:8px}
.sd-title{font-size:16px;font-weight:700;color:#1A1A1A}
.sd-header__right{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.sd-fg{display:flex;flex-direction:column;gap:2px}
.sd-lbl{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;color:var(--m)}
.sd-input,.sd-select{font-size:12px;padding:5px 9px;border:1px solid var(--br);border-radius:6px;background:#fff;color:var(--tx);outline:none}
.sd-input:focus,.sd-select:focus{border-color:var(--b)}
.sd-ranges{display:flex;gap:3px;flex-wrap:wrap;align-items:center}
.sd-range{padding:4px 9px;font-size:11px;border:1px solid var(--br);border-radius:6px;background:#fff;cursor:pointer;color:var(--m);transition:.15s all}
.sd-range:hover,.sd-range.active{background:var(--b);border-color:var(--b);color:#fff}

/* loading */
.sd-loading{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;padding:80px;font-size:13px;color:var(--m)}
.sd-spinner{width:30px;height:30px;border:3px solid var(--br);border-top-color:var(--b);border-radius:50%;animation:spin .7s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}

/* tabs */
.sd-tabs{display:flex;background:#fff;border-bottom:1px solid var(--br);padding:0 20px;overflow-x:auto;gap:0}
.sd-tab{padding:12px 16px;font-size:12px;font-weight:500;border:none;border-bottom:2px solid transparent;background:none;cursor:pointer;color:var(--m);white-space:nowrap;display:flex;align-items:center;gap:5px;transition:.15s all}
.sd-tab:hover{color:var(--tx)}
.sd-tab.active{color:var(--b);border-bottom-color:var(--b)}
.sd-tab-icon{font-size:14px}

/* body */
.sd-body{padding:20px}
.sd-slbl{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.6px;color:var(--m);margin-bottom:10px}
.sd-slbl.mt{margin-top:20px}

/* kpis */
.sd-kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(175px,1fr));gap:12px}
.sd-kpi{background:#fff;border:1px solid var(--br);border-radius:var(--rd);padding:16px;box-shadow:var(--sh);border-left:4px solid var(--b)}
.sd-kpi.g{border-left-color:var(--g)}.sd-kpi.a{border-left-color:var(--a)}.sd-kpi.t{border-left-color:var(--t)}
.sd-kpi-l{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;color:var(--m);margin-bottom:6px}
.sd-kpi-v{font-size:20px;font-weight:700;margin-bottom:3px}
.sd-kpi-s{font-size:11px;color:var(--m)}
.sd-prog{height:5px;background:#EEE;border-radius:3px;overflow:hidden;margin-top:6px}
.sd-progb{height:100%;border-radius:3px}
.sd-progb.g{background:var(--g)}.sd-progb.a{background:var(--a)}

/* cards */
.sd-card{background:#fff;border:1px solid var(--br);border-radius:var(--rd);padding:16px;box-shadow:var(--sh)}
.sd-ch{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;flex-wrap:wrap;gap:6px}
.sd-ct{font-size:13px;font-weight:600}

/* chart row */
.sd-chart-row{display:grid;grid-template-columns:2fr 1fr 1fr;gap:14px;margin-top:20px}
@media(max-width:960px){.sd-chart-row{grid-template-columns:1fr 1fr}}
@media(max-width:600px){.sd-chart-row{grid-template-columns:1fr}}

/* 2col */
.sd-2col{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:768px){.sd-2col{grid-template-columns:1fr}}

/* legend */
.sd-leg{display:flex;align-items:center;font-size:11px;color:var(--m);gap:5px}
.sd-dot{display:inline-block;width:9px;height:9px;border-radius:2px;flex-shrink:0}
.sd-leg-list{margin-top:10px;display:flex;flex-direction:column;gap:5px}
.sd-li{display:flex;align-items:center;gap:6px;font-size:11px}
.sd-li-k{flex:1}
.sd-li-v{font-weight:600}

/* status bars */
.sd-sbars{display:flex;flex-direction:column;gap:9px}
.sd-srow{display:flex;align-items:center;gap:8px}
.sd-sbadge{font-size:11px;font-weight:600;padding:3px 8px;border-radius:4px;white-space:nowrap;min-width:140px}
.sd-sbw{flex:1;height:7px;background:#EEE;border-radius:4px;overflow:hidden}
.sd-sbar{height:100%;border-radius:4px;transition:width .4s ease}
.sd-scnt{font-weight:600;min-width:28px;text-align:right}

/* tab type badge */
.sd-badge{font-size:10px;font-weight:600;padding:2px 8px;border-radius:4px}
.sd-badge.inv{background:#E3F2FD;color:#1565C0}
.sd-badge.ord{background:#E0F7FA;color:#0097A7}

/* table toolbar */
.sd-toolbar{display:flex;align-items:center;gap:8px;margin-bottom:10px;flex-wrap:wrap}
.sd-search{font-size:12px;padding:5px 10px;border:1px solid var(--br);border-radius:6px;outline:none;min-width:180px}
.sd-search:focus{border-color:var(--b)}

/* table */
.sd-twrap{overflow-x:auto}
.sd-table{width:100%;border-collapse:collapse;font-size:13px}
.sd-table th{background:var(--bg);color:var(--m);font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;padding:9px 12px;text-align:left;border-bottom:1px solid var(--br);white-space:nowrap;cursor:pointer;user-select:none}
.sd-table th:hover{color:var(--b)}
.sd-table th.active{color:var(--b)}
.sd-sort{font-size:10px;margin-left:3px;opacity:.5}
.sd-sort.on{opacity:1;color:var(--b)}
.sd-table td{padding:9px 12px;border-bottom:1px solid #F5F5F5}
.sd-table tr.clickable{cursor:pointer}
.sd-table tr.clickable:hover td{background:#F0F7FF}
.sd-table tr.drill-open td{background:#EBF5FF;font-weight:500}
.sd-amt{font-variant-numeric:tabular-nums;font-weight:600;text-align:right}
.sd-th-r{text-align:right !important}
.sd-link{color:var(--b);text-decoration:none;font-weight:500}
.sd-link:hover{text-decoration:underline}
.sd-tbadge{font-size:11px;font-weight:600;padding:2px 8px;border-radius:4px}
.sd-tbadge.inv{background:#E3F2FD;color:#1565C0}
.sd-tbadge.ord{background:#E0F7FA;color:#0097A7}
.sd-pill{display:inline-block;font-size:11px;font-weight:600;padding:3px 8px;border-radius:20px;white-space:nowrap}
.sd-empty{text-align:center;color:var(--m);padding:28px;font-style:italic}
.sd-xbtn{padding:3px 10px;font-size:11px;font-weight:600;border:1px solid var(--br);border-radius:5px;background:#fff;cursor:pointer;color:var(--m);transition:.15s}
.sd-xbtn:hover{border-color:var(--b2);color:var(--b2)}
.sd-expand-btn{padding:4px 12px;font-size:11px;font-weight:600;border:1px solid var(--br);border-radius:6px;background:#fff;cursor:pointer;color:var(--m);transition:.15s;display:inline-flex;align-items:center;gap:4px}
.sd-expand-btn:hover{border-color:var(--b2);color:var(--b2)}

/* drill-down panel */
.sd-drill{background:#F0F7FF;border-top:2px solid #1565C020;padding:0}
.sd-drill-inner{padding:14px 16px}
.sd-drill-title{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.6px;color:var(--b);margin-bottom:10px;display:flex;align-items:center;gap:6px}
.sd-drill-loading{padding:16px;text-align:center;color:var(--m);font-size:12px;display:flex;align-items:center;justify-content:center;gap:6px}
.sd-mini-spin{width:14px;height:14px;border:2px solid #ccc;border-top-color:var(--b);border-radius:50%;animation:spin .6s linear infinite;display:inline-block}
.sd-drill table{width:100%;border-collapse:collapse;font-size:12px}
.sd-drill table th{background:#E3F2FD;color:#1565C0;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.4px;padding:6px 10px;text-align:left;white-space:nowrap;border-bottom:1px solid #BBDEFB}
.sd-drill table td{padding:7px 10px;border-bottom:1px solid #E3F2FD;color:var(--tx)}
.sd-drill table tr:last-child td{border-bottom:none}
.sd-drill table tr:hover td{background:#DDEEFF}
.sd-drill .sd-amt{text-align:right;font-weight:600}
.sd-drill .sd-th-r{text-align:right!important}
.sd-drill-empty{padding:12px;text-align:center;color:var(--m);font-style:italic;font-size:12px}
.sd-mono{font-family:monospace;font-size:11px;background:#E3F2FD;padding:1px 5px;border-radius:3px;color:#1565C0}
.sd-chevron{display:inline-block;transition:transform .2s;font-size:10px;margin-left:4px}
.sd-chevron.open{transform:rotate(180deg)}

/* cost center full cards */
.sd-cc-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:14px}
.sd-cc-card{background:#fff;border:1px solid var(--br);border-radius:var(--rd);padding:16px;box-shadow:var(--sh);border-top:3px solid var(--t)}
.sd-cc-title{font-size:13px;font-weight:700;color:var(--tx);margin-bottom:12px;text-transform:uppercase;letter-spacing:.4px}
.sd-cc-kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
@media(max-width:600px){.sd-cc-kpis{grid-template-columns:repeat(2,1fr)}}
.sd-cc-kpi{display:flex;flex-direction:column;gap:2px}
.sd-cc-kpi-l{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.4px;color:var(--m)}
.sd-cc-kpi-v{font-size:15px;font-weight:700;color:var(--tx);font-variant-numeric:tabular-nums}

/* breadcrumb & back */
.sd-back{display:flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:6px;border:1px solid var(--br);color:var(--m);text-decoration:none;flex-shrink:0;transition:.15s all}
.sd-back:hover{background:var(--bg);color:var(--tx)}
.sd-title-group{display:flex;flex-direction:column;gap:1px}
.sd-breadcrumb{font-size:11px;color:var(--m)}
.sd-breadcrumb a{color:var(--b);text-decoration:none}
.sd-breadcrumb a:hover{text-decoration:underline}

/* info bar */
.sd-info-bar{display:flex;align-items:flex-start;gap:8px;background:#E8F4FD;border:1px solid #BBDEFB;border-radius:8px;padding:10px 14px;font-size:12px;color:#1A237E;line-height:1.5}
.sd-info-bar code{background:#BBDEFB;padding:1px 5px;border-radius:3px;font-size:11px}
</style>
