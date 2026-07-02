<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { Button, Avatar, TextInput } from 'frappe-ui'
import { Popover, PopoverButton, PopoverPanel } from '@headlessui/vue'
import LucideChevronsUpDown from '~icons/lucide/chevrons-up-down'
import LucideX from '~icons/lucide/x'
import LucideTrash2 from '~icons/lucide/trash-2'
import ComposePanel from '@/components/ComposePanel.vue'
import PlatformBadge from '@/components/PlatformBadge.vue'
import { postsTable, fetchPostsTable, usePostDocument, deletePost } from '@/data/posts'
import { POST_STATUS_OPTIONS, PLATFORM_LIST } from '@/data/platforms'
import { useTeam, memberById } from '@/data/team'
import { MONTH_NAMES, fmtTime } from '@/utils/date'

const team = useTeam()

const status = ref('All')
const search = ref('')
const platformFilter = ref('')
const assignedToFilter = ref('')
const composeState = reactive({ open: false, post: null })

// Bulk selection
const selected = ref(new Set())
const allChecked = computed(() => {
  const posts = postsTable.data || []
  return posts.length > 0 && posts.every((p) => selected.value.has(p.name))
})
function toggleAll() {
  const posts = postsTable.data || []
  if (allChecked.value) {
    selected.value = new Set()
  } else {
    selected.value = new Set(posts.map((p) => p.name))
  }
}
function toggleOne(name) {
  const s = new Set(selected.value)
  s.has(name) ? s.delete(name) : s.add(name)
  selected.value = s
}

const deleting = ref(false)
async function deleteSelected() {
  if (!selected.value.size || deleting.value) return
  deleting.value = true
  try {
    await Promise.all([...selected.value].map((name) => deletePost(name)))
    selected.value = new Set()
    refresh()
  } finally {
    deleting.value = false
  }
}

function refresh() {
  selected.value = new Set()
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
  refresh()
}
</script>

<template>
  <header class="flex items-center gap-3.5 border-b border-gray-100 bg-white px-6 pb-3.5 pt-4">
    <div class="flex flex-col gap-0.5">
      <h1 class="m-0 text-[17px] font-semibold">All Posts</h1>
      <span class="text-[12px] text-ink-gray-6">{{ postsTable.data?.length || 0 }} posts</span>
    </div>
    <Button variant="solid" class="ml-auto" @click="openNew">
      <template #prefix><LucidePlus class="h-3.5 w-3.5" /></template>
      Schedule post
    </Button>
  </header>

  <!-- Filter bar -->
  <div class="flex flex-wrap items-center gap-2 border-b border-gray-100 bg-white px-6 py-2.5">
    <Popover class="relative">
      <PopoverButton as="div">
        <div class="flex cursor-pointer items-center gap-1.5 rounded-lg border py-1 pl-2.5 pr-2 text-[12px]"
          :class="status !== 'All' ? 'border-gray-400 bg-white text-gray-800' : 'border-gray-200 bg-gray-50 text-gray-500'">
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
        <PopoverButton as="button" v-for="s in ['All', ...POST_STATUS_OPTIONS]" :key="s"
          class="flex w-full items-center px-3 py-1.5 text-left text-[12.5px] hover:bg-gray-50"
          :class="status === s ? 'font-semibold text-gray-900' : 'text-gray-600'"
          @click="status = s"
        >{{ s === 'All' ? 'Any status' : s }}</PopoverButton>
      </PopoverPanel>
    </Popover>

    <Popover class="relative">
      <PopoverButton as="div">
        <div class="flex cursor-pointer items-center gap-1.5 rounded-lg border py-1 pl-2.5 pr-2 text-[12px]"
          :class="platformFilter ? 'border-gray-400 bg-white text-gray-800' : 'border-gray-200 bg-gray-50 text-gray-500'">
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
        <PopoverButton as="button" v-for="p in PLATFORM_LIST" :key="p.name"
          class="flex w-full items-center gap-2 px-3 py-1.5 text-left text-[12.5px] hover:bg-gray-50"
          :class="platformFilter === p.name ? 'font-semibold text-gray-900' : 'text-gray-600'"
          @click="platformFilter = platformFilter === p.name ? '' : p.name"
        >
          <PlatformBadge :platform="p" variant="icon" class="text-gray-500" />
          {{ p.name }}
        </PopoverButton>
      </PopoverPanel>
    </Popover>

    <Popover class="relative">
      <PopoverButton as="div">
        <div class="flex cursor-pointer items-center gap-1.5 rounded-lg border py-1 pl-2.5 pr-2 text-[12px]"
          :class="assignedToFilter ? 'border-gray-400 bg-white text-gray-800' : 'border-gray-200 bg-gray-50 text-gray-500'">
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
        <PopoverButton as="button" v-for="m in team.data || []" :key="m.id"
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

  <!-- Bulk action bar — only visible when something is selected -->
  <div v-if="selected.size" class="flex items-center gap-3 border-b border-gray-100 bg-surface-gray-1 px-6 py-2">
    <span class="text-[12.5px] font-medium text-gray-700">{{ selected.size }} selected</span>
    <Button size="sm" variant="outline" :loading="deleting" @click="deleteSelected">
      <template #prefix><LucideTrash2 class="h-3.5 w-3.5" /></template>
      Delete
    </Button>
    <button class="ml-auto text-[12px] text-gray-500 hover:text-gray-700" @click="selected = new Set()">Clear selection</button>
  </div>

  <div class="flex-1 overflow-auto p-6">
    <div class="overflow-hidden rounded-xl border border-gray-100 bg-white shadow-sm">
      <!-- Header row -->
      <div class="grid grid-cols-[36px_1fr_140px_112px_156px_110px] items-center border-b border-gray-100 bg-surface-gray-1 px-4 py-2.5 text-[10.5px] font-semibold uppercase tracking-wide text-ink-gray-6">
        <label class="flex cursor-pointer items-center">
          <input
            type="checkbox"
            class="form-checkbox h-3.5 w-3.5"
            :checked="allChecked"
            :indeterminate="selected.size > 0 && !allChecked"
            @change="toggleAll"
          />
        </label>
        <span>Post</span><span>Channels</span><span>Status</span><span>Owner</span><span>Date</span>
      </div>

      <!-- Post rows -->
      <div
        v-for="post in postsTable.data || []"
        :key="post.name"
        class="grid grid-cols-[36px_1fr_140px_112px_156px_110px] items-center border-b border-gray-50 px-4 py-3 last:border-0 hover:bg-surface-gray-1"
        :class="selected.has(post.name) ? 'bg-surface-gray-1' : ''"
      >
        <label class="flex cursor-pointer items-center" @click.stop>
          <input
            type="checkbox"
            class="form-checkbox h-3.5 w-3.5"
            :checked="selected.has(post.name)"
            @change="toggleOne(post.name)"
          />
        </label>
        <div class="min-w-0 cursor-pointer pr-3.5" @click="openPost(post)">
          <div class="truncate text-[13px] font-semibold text-gray-900 hover:underline">{{ post.title }}</div>
          <div v-if="post.platforms?.[0]?.caption" class="truncate text-[11.5px] text-ink-gray-6">{{ post.platforms[0].caption }}</div>
        </div>
        <div class="flex flex-wrap gap-1.5">
          <button v-for="p in post.platforms" :key="p.platform" class="cursor-pointer text-gray-500 hover:text-gray-800" @click="filterByPlatform(p.platform)">
            <PlatformBadge :platform="p.meta" variant="icon" />
          </button>
        </div>
        <div>
          <button
            class="cursor-pointer rounded-full px-2 py-0.5 text-[11px] font-semibold"
            :style="{ color: post.statusMeta.c, background: post.statusMeta.bg }"
            @click="status = post.status"
          >{{ post.status }}</button>
        </div>
        <button class="flex min-w-0 cursor-pointer items-center gap-1.5" @click="filterByOwner(post.assigned_to)">
          <Avatar :label="memberById(post.assigned_to).name" :image="memberById(post.assigned_to).image" size="sm" />
          <span class="truncate text-[11.5px] text-gray-600">{{ memberById(post.assigned_to).name }}</span>
        </button>
        <div class="flex flex-col">
          <span class="text-[12px] font-medium text-gray-700">{{ dateLabel(post) }}</span>
          <span class="text-[10.5px] text-ink-gray-6">{{ fmtTime(post._dt?.time) }}</span>
        </div>
      </div>

      <div v-if="!(postsTable.data || []).length" class="p-11 text-center text-[13px] text-ink-gray-6">
        No posts match these filters.
      </div>
    </div>
  </div>

  <ComposePanel v-if="composeState.open" :post="composeState.post" @close="onClose" @saved="onSaved" @workflow-changed="refresh" />
</template>
