<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { Button, FormControl } from 'frappe-ui'
import { Popover, PopoverButton, PopoverPanel } from '@headlessui/vue'
import LucideChevronDown from '~icons/lucide/chevron-down'
import LucideX from '~icons/lucide/x'
import PostPill from '@/components/PostPill.vue'
import DayPanel from '@/components/DayPanel.vue'
import ComposePanel from '@/components/ComposePanel.vue'
import PlatformBadge from '@/components/PlatformBadge.vue'
import { useTeam } from '@/data/team'
import { fetchCalendarRange, calendarPosts, usePostDocument } from '@/data/posts'
import { PLATFORM_LIST } from '@/data/platforms'
import {
  MONTH_NAMES,
  WEEKDAYS,
  isoDate,
  fmtTime,
  groupPostsByDay,
  buildMonth,
  buildWeek,
  weekRangeLabel,
} from '@/utils/date'
import { pillColors } from '@/utils/colors'
import { memberById } from '@/data/team'

const team = useTeam()
const today = new Date()
const cursor = reactive({ y: today.getFullYear(), m: today.getMonth(), d: today.getDate() })
const view = ref('month')
const colorBy = ref('platform')
const selectedDayKey = ref(null)
const hover = ref(null) // { x, y, post }

const composeState = reactive({ open: false, date: null, post: null })

// frappe-ui's ListFilter looked the part but its value-selector has a real
// reactivity bug (mutating a value pulled from inside a computed getter,
// which never reaches the underlying v-model) — picking anything other than
// the first option silently reverted. Only two fields ever need filtering
// here, so a small always-visible "field = value" pair beats fighting that.
const filterValue = reactive({ platform: '', assigned_to: '' })
const activeFilterCount = computed(() => Object.values(filterValue).filter(Boolean).length)
function clearFilters() {
  filterValue.platform = ''
  filterValue.assigned_to = ''
}
function togglePlatformFilter(platformName) {
  filterValue.platform = filterValue.platform === platformName ? '' : platformName
}

const postsByDay = computed(() => groupPostsByDay(calendarPosts.data || []))

const weeks = computed(() => (view.value === 'month' ? buildMonth(cursor.y, cursor.m, postsByDay.value) : []))
const weekDays = computed(() => (view.value === 'week' ? buildWeek(cursor, postsByDay.value) : []))

const rangeLabel = computed(() => {
  if (view.value === 'month') return `${MONTH_NAMES[cursor.m]} ${cursor.y}`
  return weekRangeLabel(buildWeek(cursor, postsByDay.value))
})

const selectedDay = computed(() => {
  if (!selectedDayKey.value) return null
  const [y, m, d] = selectedDayKey.value.split('-').map(Number)
  return { y, m: m - 1, d, posts: postsByDay.value.get(selectedDayKey.value) || [] }
})

const legend = computed(() =>
  colorBy.value === 'platform'
    ? PLATFORM_LIST.map((p) => ({ label: p.name, color: p.color }))
    : (team.data || []).map((m) => ({ label: m.name.split(' ')[0], color: m.color })),
)

function refresh() {
  let startY = cursor.y, startM = cursor.m, startD = 1, endY = cursor.y, endM = cursor.m, endD = 28
  if (view.value === 'month') {
    const first = new Date(cursor.y, cursor.m, 1)
    const dow = (first.getDay() + 6) % 7
    const start = new Date(cursor.y, cursor.m, 1 - dow)
    const end = new Date(start)
    end.setDate(start.getDate() + 41)
    startY = start.getFullYear(); startM = start.getMonth(); startD = start.getDate()
    endY = end.getFullYear(); endM = end.getMonth(); endD = end.getDate()
  } else {
    const base = new Date(cursor.y, cursor.m, cursor.d)
    const dow = (base.getDay() + 6) % 7
    const start = new Date(base)
    start.setDate(base.getDate() - dow)
    const end = new Date(start)
    end.setDate(start.getDate() + 6)
    startY = start.getFullYear(); startM = start.getMonth(); startD = start.getDate()
    endY = end.getFullYear(); endM = end.getMonth(); endD = end.getDate()
  }
  fetchCalendarRange(`${isoDate(startY, startM, startD)} 00:00:00`, `${isoDate(endY, endM, endD)} 23:59:59`, {
    platform: filterValue.platform || undefined,
    assigned_to: filterValue.assigned_to || undefined,
  })
}

watch([() => cursor.y, () => cursor.m, () => cursor.d, view, filterValue], refresh, { deep: true })
onMounted(refresh)

function goPrev() {
  if (view.value === 'week') {
    const dt = new Date(cursor.y, cursor.m, cursor.d - 7)
    Object.assign(cursor, { y: dt.getFullYear(), m: dt.getMonth(), d: dt.getDate() })
  } else {
    const dt = new Date(cursor.y, cursor.m - 1, 1)
    Object.assign(cursor, { y: dt.getFullYear(), m: dt.getMonth(), d: 1 })
  }
}
function goNext() {
  if (view.value === 'week') {
    const dt = new Date(cursor.y, cursor.m, cursor.d + 7)
    Object.assign(cursor, { y: dt.getFullYear(), m: dt.getMonth(), d: dt.getDate() })
  } else {
    const dt = new Date(cursor.y, cursor.m + 1, 1)
    Object.assign(cursor, { y: dt.getFullYear(), m: dt.getMonth(), d: 1 })
  }
}
function goToday() {
  Object.assign(cursor, { y: today.getFullYear(), m: today.getMonth(), d: today.getDate() })
}

function openDay(day) {
  selectedDayKey.value = day.iso
}
function closeDay() {
  selectedDayKey.value = null
}
function openCompose(dateIso) {
  composeState.open = true
  composeState.date = dateIso
  composeState.post = null
}
function openComposeFromPanel() {
  openCompose(selectedDayKey.value)
  selectedDayKey.value = null
}
async function openPostDetail(post) {
  const doc = usePostDocument(post.name)
  await doc.reload()
  composeState.open = true
  composeState.date = null
  composeState.post = doc.doc
  selectedDayKey.value = null
}
function onComposeClose() {
  composeState.open = false
}
function onComposeSaved() {
  // Keep the panel open after a save — the workflow action buttons (Submit
  // for Review, etc.) only appear once the post exists, so closing here would
  // mean reopening it just to click the next action. "Close" dismisses explicitly.
  refresh()
}

function onPillEnter(e, post) {
  const r = e.currentTarget.getBoundingClientRect()
  hover.value = { x: r.left + r.width / 2, y: r.top - 6, post }
}
function onPillLeave() {
  hover.value = null
}
</script>

<template>
  <header class="flex items-center gap-3.5 border-b border-gray-100 bg-white px-6 pb-3.5 pt-4">
    <div class="flex flex-col gap-0.5">
      <h1 class="m-0 text-[17px] font-semibold">Content Calendar</h1>
      <span class="text-[12px] text-ink-gray-5">Plan & schedule posts across platforms</span>
    </div>
    <Button variant="solid" class="ml-auto" @click="openCompose(null)">
      <template #prefix><LucidePlus class="h-3.5 w-3.5" /></template>
      Schedule post
    </Button>
  </header>

  <div class="flex flex-wrap items-center gap-3.5 border-b border-gray-100 bg-white px-6 py-3">
    <div class="flex items-center gap-1">
      <Button variant="outline" icon="chevron-left" @click="goPrev" />
      <Button variant="outline" label="Today" @click="goToday" />
      <Button variant="outline" icon="chevron-right" @click="goNext" />
    </div>
    <h2 class="m-0 min-w-[190px] text-[16px] font-semibold">{{ rangeLabel }}</h2>

    <div class="ml-auto flex items-center gap-4">
      <Popover class="relative">
        <PopoverButton as="div">
          <button class="flex items-center gap-1.5 rounded-full bg-gray-100 px-3 py-1.5 text-[12.5px] font-medium text-gray-600 hover:bg-gray-200">
            <LucideChevronDown class="h-3.5 w-3.5" />
            Filter
            <LucideX v-if="activeFilterCount" class="h-3 w-3 text-gray-500 hover:text-gray-800" @click.stop="clearFilters" />
          </button>
        </PopoverButton>
        <PopoverPanel class="absolute right-0 top-full z-20 mt-2 w-[360px] rounded-lg border border-gray-100 bg-white p-3.5 shadow-xl">
          <div class="flex flex-col gap-3">
            <div class="flex items-center gap-2.5">
              <span class="w-[78px] shrink-0 text-[11.5px] text-gray-500">Platform</span>
              <span class="shrink-0 text-[11.5px] text-gray-400">=</span>
              <FormControl
                type="select"
                class="flex-1"
                v-model="filterValue.platform"
                :options="[{ label: 'Any', value: '' }, ...PLATFORM_LIST.map((p) => ({ label: p.name, value: p.name }))]"
              />
            </div>
            <div class="flex items-center gap-2.5">
              <span class="w-[78px] shrink-0 text-[11.5px] text-gray-500">Assigned to</span>
              <span class="shrink-0 text-[11.5px] text-gray-400">=</span>
              <FormControl
                type="select"
                class="flex-1"
                v-model="filterValue.assigned_to"
                :options="[{ label: 'Anyone', value: '' }, ...(team.data || []).map((m) => ({ label: m.name, value: m.id }))]"
              />
            </div>
            <button
              v-if="activeFilterCount"
              class="self-start text-[11.5px] font-medium text-gray-400 hover:text-gray-600"
              @click="clearFilters"
            >
              Clear filters
            </button>
          </div>
        </PopoverPanel>
      </Popover>

      <div class="flex items-center gap-2">
        <span class="text-[11.5px] font-medium text-ink-gray-5">Color by</span>
        <div class="flex rounded-lg bg-gray-100 p-0.5">
          <button
            class="rounded-md px-2.5 py-1 text-[12px] font-semibold"
            :class="colorBy === 'platform' ? 'bg-white shadow-sm' : 'text-ink-gray-5'"
            @click="colorBy = 'platform'"
          >
            Platform
          </button>
          <button
            class="rounded-md px-2.5 py-1 text-[12px] font-semibold"
            :class="colorBy === 'member' ? 'bg-white shadow-sm' : 'text-ink-gray-5'"
            @click="colorBy = 'member'"
          >
            Member
          </button>
        </div>
      </div>
      <div class="flex rounded-lg bg-gray-100 p-0.5">
        <button
          class="rounded-md px-3 py-1 text-[12px] font-semibold"
          :class="view === 'month' ? 'bg-white shadow-sm' : 'text-ink-gray-5'"
          @click="view = 'month'"
        >
          Month
        </button>
        <button
          class="rounded-md px-3 py-1 text-[12px] font-semibold"
          :class="view === 'week' ? 'bg-white shadow-sm' : 'text-ink-gray-5'"
          @click="view = 'week'"
        >
          Week
        </button>
      </div>
    </div>
  </div>

  <div class="flex items-center gap-4.5 border-b border-gray-100 bg-surface-gray-1 px-6 py-2.5">
    <span class="text-[11px] font-medium uppercase tracking-wide text-ink-gray-5">
      {{ colorBy === 'platform' ? 'Platforms' : 'Team' }}
    </span>
    <div class="flex flex-wrap items-center gap-4">
      <button
        v-for="l in legend"
        :key="l.label"
        class="flex items-center gap-1.5"
        :class="colorBy === 'platform' ? 'cursor-pointer' : 'cursor-default'"
        @click="colorBy === 'platform' && togglePlatformFilter(l.label)"
      >
        <span class="h-2 w-2 rounded-sm" :style="{ background: l.color }" />
        <span
          class="text-[12px] font-medium"
          :class="colorBy === 'platform' && filterValue.platform === l.label ? 'text-gray-900' : 'text-gray-600'"
          >{{ l.label }}</span
        >
      </button>
    </div>
  </div>

  <div class="flex-1 overflow-auto bg-gray-50">
    <!-- MONTH VIEW -->
    <div v-if="view === 'month'">
      <div class="sticky top-0 z-[5] grid grid-cols-7 border-b border-gray-100 bg-white">
        <div v-for="wd in WEEKDAYS" :key="wd" class="px-3 py-2 text-[11px] font-semibold uppercase tracking-wide text-ink-gray-5">
          {{ wd }}
        </div>
      </div>
      <div v-for="(week, wi) in weeks" :key="wi" class="grid grid-cols-7">
        <div
          v-for="day in week.days"
          :key="day.iso"
          class="flex min-h-[124px] cursor-pointer flex-col gap-1.5 border-b border-r border-gray-100 p-2"
          :class="day.today ? 'bg-gray-50' : day.inMonth ? 'bg-white' : 'bg-surface-gray-1'"
          @click="openDay(day)"
        >
          <div class="flex items-center justify-between">
            <span
              class="flex h-5.5 w-5.5 items-center justify-center rounded-full text-[12.5px]"
              :class="day.today ? 'bg-gray-800 font-bold text-white' : day.inMonth ? 'text-gray-700' : 'text-gray-300'"
              >{{ day.d }}</span
            >
            <span v-if="day.count" class="text-[10px] font-medium text-gray-300">{{ day.count }}</span>
          </div>
          <div class="flex flex-col gap-0.5">
            <PostPill
              v-for="post in day.posts"
              :key="post.name"
              :post="post"
              :color-by="colorBy"
              dense
              @enter="onPillEnter"
              @leave="onPillLeave"
            />
            <span v-if="day.hasMore" class="pl-1 text-[10.5px] font-semibold text-ink-gray-5">+{{ day.more }} more</span>
          </div>
        </div>
      </div>
    </div>

    <!-- WEEK VIEW -->
    <div v-else class="grid min-h-full grid-cols-7">
      <div
        v-for="day in weekDays"
        :key="day.iso"
        class="flex cursor-pointer flex-col border-r border-gray-100"
        :class="day.today ? 'bg-gray-50' : 'bg-white'"
        @click="openDay(day)"
      >
        <div class="sticky top-0 flex flex-col gap-0.5 border-b border-gray-100 bg-inherit px-3 py-2.5">
          <span class="text-[10.5px] font-semibold uppercase tracking-wide text-ink-gray-5">{{ day.weekday }}</span>
          <span class="text-[18px] font-semibold" :class="day.today ? 'text-gray-900' : ''">{{ day.d }}</span>
        </div>
        <div class="flex flex-1 flex-col gap-1.5 p-2">
          <div
            v-for="post in day.posts"
            :key="post.name"
            class="flex flex-col gap-1 rounded-lg p-1.5"
            :style="{ background: pillColors(post, colorBy).bg, borderLeft: `3px solid ${pillColors(post, colorBy).bar}` }"
            @mouseenter="onPillEnter($event, post)"
            @mouseleave="onPillLeave"
          >
            <div class="flex items-center gap-1">
              <span class="text-[10.5px] font-semibold">{{ fmtTime(post._dt?.time) }}</span>
              <PlatformBadge v-for="p in post.platforms" :key="p.platform" :platform="p.meta" variant="dot" />
            </div>
            <span class="text-[12px] font-semibold leading-snug text-gray-800">{{ post.title }}</span>
            <span
              class="self-start rounded-full px-2 py-0.5 text-[10.5px] font-semibold"
              :style="{ color: post.statusMeta.c, background: post.statusMeta.bg }"
              >{{ post.status }}</span
            >
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- HOVER TOOLTIP -->
  <div
    v-if="hover"
    class="pointer-events-none fixed z-[90] w-[208px] -translate-x-1/2 -translate-y-full rounded-lg bg-gray-900 p-2.5 text-white shadow-xl"
    :style="{ left: hover.x + 'px', top: hover.y + 'px' }"
  >
    <div class="mb-1 text-[12.5px] font-semibold leading-snug">{{ hover.post.title }}</div>
    <div class="mb-1 flex items-center gap-1.5">
      <span
        class="rounded-full px-1.5 py-0.5 text-[10.5px] font-semibold"
        :style="{ color: hover.post.statusMeta.c, background: hover.post.statusMeta.bg }"
        >{{ hover.post.status }}</span
      >
      <span class="text-[11px] text-gray-300">{{ fmtTime(hover.post._dt?.time) }}</span>
    </div>
    <div class="flex items-center gap-1.5 text-[11px] text-gray-300">
      <span
        class="flex h-3.5 w-3.5 items-center justify-center rounded-full text-[7px] font-bold"
        :style="{ background: memberById(hover.post.assigned_to).color }"
        >{{ memberById(hover.post.assigned_to).initials }}</span
      >
      {{ memberById(hover.post.assigned_to).name }} · {{ hover.post.platforms.map((p) => p.platform).join(' · ') }}
    </div>
  </div>

  <DayPanel :day="selectedDay" @close="closeDay" @schedule="openComposeFromPanel" @open-post="openPostDetail" />

  <ComposePanel
    v-if="composeState.open"
    :date="composeState.date"
    :post="composeState.post"
    @close="onComposeClose"
    @saved="onComposeSaved"
    @workflow-changed="refresh"
  />
</template>
