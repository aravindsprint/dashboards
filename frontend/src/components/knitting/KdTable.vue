<template>
<div class="kdt-wrap">
  <table class="kdt-table" v-if="rows && rows.length">
    <thead>
      <tr v-if="totals" class="kdt-total-row">
        <td v-for="(col, i) in columns" :key="'t-' + col.key" :class="col.numeric ? 'num' : ''">
          {{ i === 0 ? (totals.label || 'Total') : formatCell(col, totals[col.key]) }}
        </td>
      </tr>
      <tr>
        <th v-for="col in columns" :key="col.key" :class="['kdt-sortable', col.numeric ? 'num' : '']" @click="toggleSort(col.key)">
          {{ col.label }}
          <span class="kdt-arrow" v-if="sortKey === col.key">{{ sortDir === 'asc' ? '▲' : '▼' }}</span>
        </th>
      </tr>
      <tr class="kdt-filter-row">
        <th v-for="col in columns" :key="'f-' + col.key" :class="col.numeric ? 'num' : ''">
          <input type="text" v-model="filters[col.key]" class="kdt-filter-input" placeholder="Filter…" />
        </th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="(row, ridx) in sortedRows" :key="row.__key ?? ridx">
        <td v-for="col in columns" :key="col.key" :class="col.numeric ? 'num' : ''">
          <slot :name="'cell-' + col.key" :row="row" :value="row[col.key]">{{ formatCell(col, row[col.key]) }}</slot>
        </td>
      </tr>
      <tr v-if="sortedRows.length === 0">
        <td :colspan="columns.length" class="kdt-empty">No rows match the filters.</td>
      </tr>
    </tbody>
  </table>
  <div v-else class="kdt-placeholder">{{ emptyText }}</div>
</div>
</template>

<script>
import { reactive, ref, computed } from 'vue'

export default {
  name: 'KdTable',
  props: {
    // [{ key, label, numeric?: bool, format?: (value) => string, suffix?: string }]
    columns: { type: Array, required: true },
    rows: { type: Array, default: () => [] },
    // Optional highlighted totals row shown above the header, e.g. { label: 'Total prod', qty: 123 }.
    // Reflects the full dataset, not the current filters (matches how the Daily tab's totals worked before).
    totals: { type: Object, default: null },
    emptyText: { type: String, default: 'No data.' },
  },
  setup(props) {
    const filters = reactive({})
    const sortKey = ref('')
    const sortDir = ref('asc')

    function toggleSort(key) {
      if (sortKey.value === key) {
        sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
      } else {
        sortKey.value = key
        sortDir.value = 'asc'
      }
    }

    function formatCell(col, value) {
      if (value === null || value === undefined || value === '') return '—'
      let v = col.format ? col.format(value) : value
      if (col.suffix) v = `${v}${col.suffix}`
      return v
    }

    // Simple substring match on the same text shown in the cell — works for
    // both text and number columns. Range/greater-than filters aren't
    // supported; say so if you'd rather have those on numeric columns.
    const filteredRows = computed(() =>
      (props.rows || []).filter((row) =>
        props.columns.every((col) => {
          const f = (filters[col.key] || '').trim().toLowerCase()
          if (!f) return true
          const display = String(formatCell(col, row[col.key]) ?? '').toLowerCase()
          return display.includes(f)
        })
      )
    )

    const sortedRows = computed(() => {
      const rows = [...filteredRows.value]
      if (!sortKey.value) return rows
      const col = props.columns.find((c) => c.key === sortKey.value)
      rows.sort((a, b) => {
        let av = a[sortKey.value]
        let bv = b[sortKey.value]
        if (col && col.numeric) {
          av = Number(av) || 0
          bv = Number(bv) || 0
          return sortDir.value === 'asc' ? av - bv : bv - av
        }
        av = String(av ?? '').toLowerCase()
        bv = String(bv ?? '').toLowerCase()
        if (av < bv) return sortDir.value === 'asc' ? -1 : 1
        if (av > bv) return sortDir.value === 'asc' ? 1 : -1
        return 0
      })
      return rows
    })

    return { filters, sortKey, sortDir, toggleSort, formatCell, sortedRows }
  },
}
</script>

<style scoped>
.kdt-wrap{--b:#1565C0;--m:#757575;--br:#E0E0E0;--tx:#212121;background:#fff;border:1px solid var(--br);border-radius:10px;overflow-x:auto}
.kdt-table{width:100%;border-collapse:collapse;font-size:12.5px}
.kdt-table th,.kdt-table td{padding:9px 14px;border-bottom:1px solid #F0F0F0;color:var(--tx);white-space:nowrap;text-align:left}
.kdt-table th{font-size:10.5px;font-weight:700;text-transform:uppercase;letter-spacing:.4px;color:var(--m);border-bottom:1px solid var(--br)}
.kdt-table tbody tr:last-child td{border-bottom:none}
.kdt-table .num{text-align:right}

.kdt-sortable{cursor:pointer;user-select:none}
.kdt-sortable:hover{color:var(--tx)}
.kdt-arrow{margin-left:4px;font-size:9px;color:var(--b)}

.kdt-filter-row th{padding:6px 10px;border-bottom:1px solid var(--br)}
.kdt-filter-input{width:100%;min-width:70px;font-size:11.5px;padding:4px 7px;border:1px solid var(--br);border-radius:5px;background:#F8FAFB;color:var(--tx);outline:none;text-transform:none;letter-spacing:normal;font-weight:400}
.kdt-filter-input:focus{border-color:var(--b);background:#fff}

.kdt-total-row td{background:#FFF7E0;font-weight:700;color:#1A1A1A;border-bottom:1px solid var(--br)}
.kdt-empty{text-align:center;color:var(--m);padding:24px 14px}
.kdt-placeholder{padding:48px 24px;text-align:center;color:var(--m);font-size:14px;border:1px dashed #BDBDBD;border-radius:10px}
</style>
