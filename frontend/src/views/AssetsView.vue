<script setup>
import { ref, reactive, watch, onMounted } from 'vue'
import { TextInput } from 'frappe-ui'
import LucideVideo from '~icons/lucide/video'
import LucideImages from '~icons/lucide/images'
import ComposePanel from '@/components/ComposePanel.vue'
import { assetsResource, fetchAssets, fmtBytes } from '@/data/assets'
import { usePostDocument } from '@/data/posts'

const fileType = ref('All')
const search = ref('')
const composeState = reactive({ open: false, post: null })

function refresh() {
  fetchAssets({ file_type: fileType.value, search: search.value })
}
let debounceHandle
watch(search, () => {
  clearTimeout(debounceHandle)
  debounceHandle = setTimeout(refresh, 300)
})
watch(fileType, refresh)
onMounted(refresh)

async function openAsset(asset) {
  if (!asset.post) return
  const doc = usePostDocument(asset.post.name)
  await doc.reload()
  composeState.open = true
  composeState.post = doc.doc
}
function onClose() {
  composeState.open = false
}
</script>

<template>
  <header class="flex items-center gap-3.5 border-b border-gray-100 bg-white px-6 pb-3.5 pt-4">
    <div class="flex flex-col gap-0.5">
      <h1 class="m-0 text-[17px] font-semibold">Assets</h1>
      <span class="text-[12px] text-ink-gray-5">{{ assetsResource.data?.length || 0 }} files across all posts</span>
    </div>
  </header>

  <div class="flex flex-wrap items-center gap-3 border-b border-gray-100 bg-white px-6 py-3">
    <div class="flex flex-wrap gap-1.5">
      <button
        v-for="t in ['All', 'Image', 'Video']"
        :key="t"
        class="rounded-full px-3 py-1 text-[12px] font-semibold"
        :class="fileType === t ? 'bg-gray-800 text-white' : 'bg-gray-100 text-gray-500'"
        @click="fileType = t"
      >
        {{ t }}
      </button>
    </div>
    <TextInput v-model="search" placeholder="Search by alt text…" class="ml-auto w-[240px]" />
  </div>

  <div class="flex-1 overflow-auto p-6">
    <div v-if="(assetsResource.data || []).length" class="grid grid-cols-[repeat(auto-fill,minmax(190px,1fr))] gap-4">
      <div
        v-for="asset in assetsResource.data"
        :key="asset.name"
        class="cursor-pointer overflow-hidden rounded-xl border border-gray-100 bg-white shadow-sm hover:border-gray-200"
        @click="openAsset(asset)"
      >
        <div class="flex h-[120px] items-center justify-center bg-gray-50">
          <img v-if="asset.file_type === 'Image'" :src="asset.file" :alt="asset.alt_text" class="h-full w-full object-cover" />
          <LucideVideo v-else class="h-8 w-8 text-ink-gray-5" />
        </div>
        <div class="flex flex-col gap-1 p-2.5">
          <span class="truncate text-[12px] font-semibold text-gray-800">{{ asset.alt_text || asset.file?.split('/').pop() }}</span>
          <span v-if="asset.post" class="truncate text-[11px] text-ink-gray-5">{{ asset.post.title }}</span>
          <div class="flex items-center gap-1.5">
            <span
              v-if="asset.post"
              class="rounded-full px-1.5 py-0.5 text-[9.5px] font-semibold"
              :style="{ color: asset.postStatusMeta?.c, background: asset.postStatusMeta?.bg }"
              >{{ asset.post.status }}</span
            >
            <span class="ml-auto text-[10px] text-ink-gray-5">{{ fmtBytes(asset.file_size) }}</span>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="flex flex-1 flex-col items-center justify-center gap-3 py-20 text-center">
      <div class="flex h-14 w-14 items-center justify-center rounded-2xl bg-gray-100">
        <LucideImages class="h-6 w-6 text-ink-gray-5" />
      </div>
      <p class="m-0 text-[13px] font-medium text-gray-500">No assets yet — upload images or video from a post's Compose panel.</p>
    </div>
  </div>

  <ComposePanel v-if="composeState.open" :post="composeState.post" @close="onClose" @saved="refresh" />
</template>
