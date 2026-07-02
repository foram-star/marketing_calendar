<script setup>
import { computed, onMounted } from 'vue'
import { DonutChart } from 'frappe-ui'
import LucideTriangleAlert from '~icons/lucide/triangle-alert'
import PlatformBadge from '@/components/PlatformBadge.vue'
import { analyticsResource, fetchAnalytics } from '@/data/analytics'
import { STATUSES, PLATFORMS } from '@/data/platforms'

onMounted(fetchAnalytics)

const kpis = computed(() => {
  const d = analyticsResource.data
  if (!d) return []
  return [
    { label: 'Total posts', value: d.total_posts },
    { label: 'Scheduled, next 7 days', value: d.upcoming_count },
    { label: 'Published this month', value: d.published_this_month },
    { label: 'Needs attention (failed)', value: d.status_counts?.Failed || 0, warn: (d.status_counts?.Failed || 0) > 0 },
  ]
})

const statusChartData = computed(() => {
  const counts = analyticsResource.data?.status_counts || {}
  return Object.keys(STATUSES)
    .filter((s) => counts[s])
    .map((s) => ({ status: s, count: counts[s] }))
})
const statusColors = computed(() => statusChartData.value.map((row) => STATUSES[row.status]?.c || '#888'))

const platformChartData = computed(() => {
  const counts = analyticsResource.data?.platform_counts || {}
  return Object.values(PLATFORMS)
    .filter((p) => counts[p.name])
    .map((p) => ({ platform: p.name, count: counts[p.name] }))
})
const platformColors = computed(() => platformChartData.value.map((row) => PLATFORMS[row.platform.toLowerCase()]?.color || '#888'))

function fmtFailedAt(dt) {
  if (!dt) return ''
  return dt.replace(' ', ' · ').slice(0, 16)
}
</script>

<template>
  <header class="flex items-center gap-3.5 border-b border-gray-100 bg-white px-6 pb-3.5 pt-4">
    <div class="flex flex-col gap-0.5">
      <h1 class="m-0 text-[17px] font-semibold">Analytics</h1>
      <span class="text-[12px] text-ink-gray-5">Operational overview — publish outcomes we've recorded ourselves</span>
    </div>
  </header>

  <div class="flex-1 overflow-auto p-6">
    <div class="mb-5 grid grid-cols-4 gap-4">
      <div v-for="k in kpis" :key="k.label" class="rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
        <span class="text-[11.5px] font-medium text-ink-gray-5">{{ k.label }}</span>
        <div class="mt-1 text-[26px] font-semibold" :class="k.warn ? 'text-red-600' : 'text-gray-900'">{{ k.value }}</div>
      </div>
    </div>

    <div class="grid grid-cols-2 gap-4">
      <div class="rounded-xl border border-gray-100 bg-white p-2 shadow-sm">
        <DonutChart
          v-if="statusChartData.length"
          :config="{
            title: 'Posts by status',
            data: statusChartData,
            categoryColumn: 'status',
            valueColumn: 'count',
            colors: statusColors,
          }"
        />
        <div v-else class="flex h-[220px] items-center justify-center text-[12.5px] text-ink-gray-5">No posts yet</div>
      </div>
      <div class="rounded-xl border border-gray-100 bg-white p-2 shadow-sm">
        <DonutChart
          v-if="platformChartData.length"
          :config="{
            title: 'Platform mix',
            data: platformChartData,
            categoryColumn: 'platform',
            valueColumn: 'count',
            colors: platformColors,
          }"
        />
        <div v-else class="flex h-[220px] items-center justify-center text-[12.5px] text-ink-gray-5">No platforms selected yet</div>
      </div>
    </div>

    <!-- Platform analytics: engagement data pulled from each connected platform's API -->
    <div class="rounded-xl border border-gray-100 bg-white shadow-sm">
      <div class="border-b border-gray-100 px-4 py-3">
        <h3 class="m-0 text-[13.5px] font-semibold">Platform analytics</h3>
        <p class="m-0 mt-0.5 text-[11.5px] text-ink-gray-5">Likes, reach, comments and saves pulled from each connected platform</p>
      </div>
      <div class="flex flex-col items-center gap-2 px-4 py-10 text-center">
        <span class="rounded-full bg-gray-100 px-3 py-1 text-[11px] font-semibold uppercase tracking-wide text-ink-gray-5">Coming soon</span>
        <p class="m-0 max-w-[380px] text-[12.5px] text-ink-gray-5">
          Once LinkedIn and X are connected, per-platform engagement metrics (impressions, reach, reactions) will appear here alongside Instagram's existing data.
        </p>
      </div>
    </div>

    <div class="rounded-xl border border-gray-100 bg-white shadow-sm">
      <div class="flex items-center gap-2 border-b border-gray-100 px-4 py-3">
        <LucideTriangleAlert class="h-4 w-4 text-red-500" />
        <h3 class="m-0 text-[13.5px] font-semibold">Recent failures</h3>
      </div>
      <div v-if="(analyticsResource.data?.recent_failures || []).length">
        <div
          v-for="f in analyticsResource.data.recent_failures"
          :key="f.parent + f.platform"
          class="flex items-center gap-3 border-b border-gray-50 px-4 py-2.5 last:border-0"
        >
          <PlatformBadge :platform="PLATFORMS[f.platform.toLowerCase()]" />
          <span class="min-w-0 flex-1 truncate text-[12.5px] font-medium text-gray-800">{{ f.post_title }}</span>
          <span class="max-w-[320px] truncate text-[11.5px] text-ink-gray-5">{{ f.error_message }}</span>
          <span class="text-[10.5px] text-ink-gray-5">{{ fmtFailedAt(f.last_attempted_at) }}</span>
        </div>
      </div>
      <div v-else class="px-4 py-8 text-center text-[12.5px] text-ink-gray-5">Nothing's failed — clean record.</div>
    </div>
  </div>
</template>
