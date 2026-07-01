<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { Button, Avatar, TextInput } from 'frappe-ui'
import { Popover, PopoverButton, PopoverPanel } from '@headlessui/vue'
import LucideChevronsUpDown from '~icons/lucide/chevrons-up-down'
import LucideX from '~icons/lucide/x'
import ComposePanel from '@/components/ComposePanel.vue'
import PlatformBadge from '@/components/PlatformBadge.vue'
import { postsTable, fetchPostsTable, usePostDocument } from '@/data/posts'
import { POST_STATUS_OPTIONS, PLATFORM_LIST } from '@/data/platforms'
import { useTeam, memberById } from '@/data/team'
import { MONTH_NAMES, fmtTime } from '@/utils/date'

const team = useTeam()

const status = ref('All')
const search = ref('')
// Same idea as Desk's own list view: clicking a status/owner/channel badge in
// a row filters by that value instead of opening the record — only the title
// opens it. These two live separately from the status tabs above since a row
// click can set them to something not reflected by the tabs (e.g. "assigned
// to Foram" has no tab of its own).
const platformFilter = ref('')
const assignedToFilter = ref('')
const composeState = reactive({ open: false, post: null })

const hasRowFilters = computed(() => !!(platformFilter.value || assignedToFilter.value))

function refresh() {
  fetchPostsTable({
    status: status.value,
    search: search.value,
    platform: platformFilter.value || undefined,
    assigned_to: assignedToFilter.value || undefined,
  })
}
let debounceHandle
watch(search, () => {
  clearTimeout(debounceHandle)
  debounceHandle = setTimeout(refresh, 300)
})
watch([status, platformFilter, assignedToFilter], refresh)
onMounted(refresh)

function dateLabel(post) {
  if (!post._dt) return ''
  return `${MONTH_NAMES[post._dt.m].slice(0, 3)} ${post._dt.d}`
}

function filterByPlatform(platformName) {
  platformFilter.value = platformFilter.value === platformName ? '' : platformName
}
function filterByOwner(userId) {
  assignedToFilter.value = assignedToFilter.value === userId ? '' : userId
}
function clearRowFilters() {
  platformFilter.value = ''
  assignedToFilter.value = ''
}

async function openPost(post) {
  const doc = usePostDocument(post.name)
  await doc.reload()
  composeState.open = true
  composeState.post = doc.doc
}
function openNew() {
  composeState.open = true
  composeState.post = null
}
function onClose() {
  composeState.open = false
}
function onSaved() {
  // Keep the panel open — workflow action buttons only appear once the post
  // exists, so closing here would mean reopening it for the next action.
  refresh()
}
</script>

<template>
  <header class="flex items-center gap-3.5 border-b border-gray-100 bg-white px-6 pb-3.5 pt-4">
    <div class="flex flex-col gap-0.5">
      <h1 class="m-0 text-[17px] font-semibold">All Posts</h1>
      <span class="text-[12px] text-gray-400">{{ postsTable.data?.length || 0 }} posts</span>
    </div>
    <Button variant="solid" class="ml-auto" @click="openNew">+ Schedule post</Button>
  </header>

  <!-- Inline filter bar — [Field] [≈] [Value ▾] chip pattern -->
  <div class="flex flex-wrap items-center gap-2 border-b border-gray-100 bg-white px-6 py-2.5">

    <!-- Status chip -->
    <Popover class="relative">
      <PopoverButton as="div">
        <div
          class="flex cursor-pointer items-center gap-1.5 rounded-lg border py-1 pl-2.5 pr-2 text-[12px]"
          :class="status !== 'All' ? 'border-gray-400 bg-white text-gray-800' : 'border-gray-200 bg-gray-50 text-gray-500'"
        >
          <span class="font-medium">Status</span>
          <span v-if="status !== 'All'" class="text-gray-400">≈</span>
          <span v-if="status !== 'All'" class="font-semibold">{{ status }}</span>
          <LucideChevronsUpDown class="h-3 w-3 text-gray-400" />
          <button v-if="status !== 'All'" class="ml-0.5 rounded text-gray-400 hover:text-gray-700" @click.stop="status = 'All'">
            <LucideX class="h-3 w-3" />
          </button>
        </div>
      </PopoverButton>
      <PopoverPanel class="absolute left-0 top-full z-20 mt-1.5 w-44 rounded-lg border border-gray-100 bg-white py-1 shadow-lg">
        <PopoverButton as="button"
          v-for="s in ['All', ...POST_STATUS_OPTIONS]"
          :key="s"
          class="flex w-full items-center px-3 py-1.5 text-left text-[12.5px] hover:bg-gray-50"
          :class="status === s ? 'font-semibold text-gray-900' : 'text-gray-600'"
          @click="status = s"
        >{{ s === 'All' ? 'Any status' : s }}</PopoverButton>
      </PopoverPanel>
    </Popover>

    <!-- Channel chip -->
    <Popover class="relative">
      <PopoverButton as="div">
        <div
          class="flex cursor-pointer items-center gap-1.5 rounded-lg border py-1 pl-2.5 pr-2 text-[12px]"
          :class="platformFilter ? 'border-gray-400 bg-white text-gray-800' : 'border-gray-200 bg-gray-50 text-gray-500'"
        >
          <span class="font-medium">Channel</span>
          <span v-if="platformFilter" class="text-gray-400">≈</span>
          <span v-if="platformFilter" class="font-semibold">{{ platformFilter }}</span>
          <LucideChevronsUpDown class="h-3 w-3 text-gray-400" />
          <button v-if="platformFilter" class="ml-0.5 rounded text-gray-400 hover:text-gray-700" @click.stop="platformFilter = ''">
            <LucideX class="h-3 w-3" />
          </button>
        </div>
      </PopoverButton>
      <PopoverPanel class="absolute left-0 top-full z-20 mt-1.5 w-40 rounded-lg border border-gray-100 bg-white py-1 shadow-lg">
        <PopoverButton as="button"
          v-for="p in PLATFORM_LIST"
          :key="p.name"
          class="flex w-full items-center gap-2 px-3 py-1.5 text-left text-[12.5px] hover:bg-gray-50"
          :class="platformFilter === p.name ? 'font-semibold text-gray-900' : 'text-gray-600'"
          @click="platformFilter = platformFilter === p.name ? '' : p.name"
        >
          <span class="h-1.5 w-1.5 shrink-0 rounded-full" :style="{ background: p.color }" />
          {{ p.name }}
        </PopoverButton>
      </PopoverPanel>
    </Popover>

    <!-- Owner chip -->
    <Popover class="relative">
      <PopoverButton as="div">
        <div
          class="flex cursor-pointer items-center gap-1.5 rounded-lg border py-1 pl-2.5 pr-2 text-[12px]"
          :class="assignedToFilter ? 'border-gray-400 bg-white text-gray-800' : 'border-gray-200 bg-gray-50 text-gray-500'"
        >
          <span class="font-medium">Owner</span>
          <span v-if="assignedToFilter" class="text-gray-400">≈</span>
          <span v-if="assignedToFilter" class="font-semibold">{{ memberById(assignedToFilter).name }}</span>
          <LucideChevronsUpDown class="h-3 w-3 text-gray-400" />
          <button v-if="assignedToFilter" class="ml-0.5 rounded text-gray-400 hover:text-gray-700" @click.stop="assignedToFilter = ''">
            <LucideX class="h-3 w-3" />
          </button>
        </div>
      </PopoverButton>
      <PopoverPanel class="absolute left-0 top-full z-20 mt-1.5 w-44 rounded-lg border border-gray-100 bg-white py-1 shadow-lg">
        <PopoverButton as="button"
          v-for="m in team.data || []"
          :key="m.id"
          class="flex w-full items-center gap-2 px-3 py-1.5 text-left text-[12.5px] hover:bg-gray-50"
          :class="assignedToFilter === m.id ? 'font-semibold text-gray-900' : 'text-gray-600'"
          @click="assignedToFilter = assignedToFilter === m.id ? '' : m.id"
        >
          <Avatar :label="m.name" :image="m.image" size="sm" />
          {{ m.name }}
        </PopoverButton>
      </PopoverPanel>
    </Popover>

    <TextInput v-model="search" placeholder="Search posts…" class="ml-auto w-[220px]" />
  </div>

  <div class="flex-1 overflow-auto p-6">
    <div class="overflow-hidden rounded-xl border border-gray-100 bg-white shadow-sm">
      <div class="grid grid-cols-[1fr_150px_112px_156px_110px] border-b border-gray-100 bg-gray-25 px-4 py-2.5 text-[10.5px] font-semibold uppercase tracking-wide text-gray-400">
        <span>Post</span><span>Channels</span><span>Status</span><span>Owner</span><span>Date</span>
      </div>
      <div
        v-for="post in postsTable.data || []"
        :key="post.name"
        class="grid grid-cols-[1fr_150px_112px_156px_110px] items-center border-b border-gray-50 px-4 py-3 last:border-0 hover:bg-gray-25"
      >
        <div class="min-w-0 cursor-pointer pr-3.5" @click="openPost(post)">
          <div class="truncate text-[13px] font-semibold text-gray-900 hover:underline">{{ post.title }}</div>
          <div v-if="post.platforms?.[0]?.caption" class="truncate text-[11.5px] text-gray-400">{{ post.platforms[0].caption }}</div>
        </div>
        <div class="flex flex-wrap gap-1">
          <button v-for="p in post.platforms" :key="p.platform" class="cursor-pointer" @click="filterByPlatform(p.platform)">
            <PlatformBadge :platform="p.meta" />
          </button>
        </div>
        <div>
          <button
            class="cursor-pointer rounded-full px-2 py-0.5 text-[11px] font-semibold"
            :style="{ color: post.statusMeta.c, background: post.statusMeta.bg }"
            @click="status = post.status"
          >
            {{ post.status }}
          </button>
        </div>
        <button class="flex min-w-0 cursor-pointer items-center gap-1.5" @click="filterByOwner(post.assigned_to)">
          <Avatar :label="memberById(post.assigned_to).name" :image="memberById(post.assigned_to).image" size="sm" />
          <span class="truncate text-[11.5px] text-gray-600">{{ memberById(post.assigned_to).name }}</span>
        </button>
        <div class="flex flex-col">
          <span class="text-[12px] font-medium text-gray-700">{{ dateLabel(post) }}</span>
          <span class="text-[10.5px] text-gray-400">{{ fmtTime(post._dt?.time) }}</span>
        </div>
      </div>
      <div v-if="!(postsTable.data || []).length" class="p-11 text-center text-[13px] text-gray-400">
        No posts match these filters.
      </div>
    </div>
  </div>

  <ComposePanel v-if="composeState.open" :post="composeState.post" @close="onClose" @saved="onSaved" @workflow-changed="refresh" />
</template>
