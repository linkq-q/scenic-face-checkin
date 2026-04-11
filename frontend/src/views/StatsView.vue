<script setup>
import { ref, onMounted, computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart } from 'echarts/charts'
import {
  GridComponent, TooltipComponent, TitleComponent,
  LegendComponent, DataZoomComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import { ElMessage } from 'element-plus'
import { getDailyStats, getRangeStats, getRealtimeStats } from '../api/index.js'

use([
  CanvasRenderer, LineChart, BarChart,
  GridComponent, TooltipComponent, TitleComponent,
  LegendComponent, DataZoomComponent,
])

// ── realtime cards ──────────────────────────────────────────────────────────
const realtime = ref({ today_total: 0, last_hour_count: 0, last_checkin_at: null })
async function loadRealtime() {
  try {
    const { data } = await getRealtimeStats()
    realtime.value = data
  } catch { /* silent */ }
}

// ── daily hourly chart ──────────────────────────────────────────────────────
const dailyDate = ref(new Date().toISOString().slice(0, 10))
const hourlyData = ref([])

async function loadDaily() {
  try {
    const { data } = await getDailyStats(dailyDate.value)
    hourlyData.value = data.by_hour || []
  } catch {
    ElMessage.error('日统计加载失败')
  }
}

const hourlyOption = computed(() => {
  const hours = Array.from({ length: 24 }, (_, i) => i)
  const countMap = Object.fromEntries(hourlyData.value.map(r => [r.hour, r.count]))
  const values = hours.map(h => countMap[h] ?? 0)
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 20, top: 30, bottom: 40 },
    xAxis: {
      type: 'category',
      data: hours.map(h => `${String(h).padStart(2, '0')}:00`),
      axisLabel: { rotate: 45, fontSize: 11 },
    },
    yAxis: { type: 'value', minInterval: 1, name: '核销人次' },
    series: [{
      name: '核销人次',
      type: 'bar',
      data: values,
      itemStyle: { color: '#409eff' },
      barMaxWidth: 32,
    }],
  }
})

// ── range trend chart ───────────────────────────────────────────────────────
const rangeValue = ref([
  new Date(Date.now() - 6 * 86400000).toISOString().slice(0, 10),
  new Date().toISOString().slice(0, 10),
])
const rangeData = ref([])

async function loadRange() {
  if (!rangeValue.value?.length) return
  try {
    const [start, end] = rangeValue.value
    const { data } = await getRangeStats(start, end)
    rangeData.value = data.records || []
  } catch {
    ElMessage.error('区间统计加载失败')
  }
}

const rangeOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 50, right: 20, top: 30, bottom: 50 },
  xAxis: {
    type: 'category',
    data: rangeData.value.map(r => r.date),
    axisLabel: { rotate: 30, fontSize: 11 },
  },
  yAxis: { type: 'value', minInterval: 1, name: '核销人次' },
  series: [{
    name: '每日核销',
    type: 'line',
    data: rangeData.value.map(r => r.count),
    smooth: true,
    symbol: 'circle',
    symbolSize: 6,
    itemStyle: { color: '#67c23a' },
    areaStyle: { color: 'rgba(103,194,58,0.15)' },
  }],
}))

function formatTime(t) {
  if (!t) return '暂无'
  return t.replace('T', ' ').slice(0, 19)
}

onMounted(() => {
  loadRealtime()
  loadDaily()
  loadRange()
})
</script>

<template>
  <!-- 实时数据卡片 -->
  <el-row :gutter="16" style="margin-bottom: 20px">
    <el-col :span="8">
      <el-card shadow="hover">
        <el-statistic title="今日核销总量" :value="realtime.today_total">
          <template #suffix>人次</template>
        </el-statistic>
      </el-card>
    </el-col>
    <el-col :span="8">
      <el-card shadow="hover">
        <el-statistic title="最近 1 小时" :value="realtime.last_hour_count">
          <template #suffix>人次</template>
        </el-statistic>
      </el-card>
    </el-col>
    <el-col :span="8">
      <el-card shadow="hover">
        <div style="font-size: 14px; color: #909399; margin-bottom: 8px">最后核销时间</div>
        <div style="font-size: 22px; font-weight: 600; color: #303133">
          {{ formatTime(realtime.last_checkin_at) }}
        </div>
      </el-card>
    </el-col>
  </el-row>

  <!-- 今日按小时分布 -->
  <el-card style="margin-bottom: 20px">
    <template #header>
      <div style="display: flex; align-items: center; gap: 12px">
        <span>今日核销分布（按小时）</span>
        <el-date-picker
          v-model="dailyDate"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="选择日期"
          style="width: 160px"
          @change="loadDaily"
        />
        <el-button type="primary" plain size="small" @click="loadDaily">刷新</el-button>
      </div>
    </template>
    <v-chart :option="hourlyOption" style="height: 260px" autoresize />
  </el-card>

  <!-- 多日趋势 -->
  <el-card>
    <template #header>
      <div style="display: flex; align-items: center; gap: 12px">
        <span>客流趋势（按日）</span>
        <el-date-picker
          v-model="rangeValue"
          type="daterange"
          value-format="YYYY-MM-DD"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="width: 260px"
          @change="loadRange"
        />
        <el-button type="primary" plain size="small" @click="loadRange">查询</el-button>
      </div>
    </template>
    <v-chart :option="rangeOption" style="height: 280px" autoresize />
  </el-card>
</template>
