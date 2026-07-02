<script setup>
import { ref, computed, watch } from 'vue'
import { Dialog } from 'frappe-ui'
import { initialsForUser, colorForUser } from '@/data/platforms'
import LucideHeart from '~icons/lucide/heart'
import LucideMessageCircle from '~icons/lucide/message-circle'
import LucideSend from '~icons/lucide/send'
import LucideBookmark from '~icons/lucide/bookmark'
import LucideMoreHorizontal from '~icons/lucide/more-horizontal'
import LucideThumbsUp from '~icons/lucide/thumbs-up'
import LucideRepeat2 from '~icons/lucide/repeat-2'
import LucideGlobe from '~icons/lucide/globe'
import LucideBarChart2 from '~icons/lucide/bar-chart-2'
import LucideShare from '~icons/lucide/share'
import LucideImage from '~icons/lucide/image'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  platforms: { type: Array, default: () => [] }, // [{ id, name, caption, link_url }]
  assets: { type: Array, default: () => [] }, // [{ file_url, file_type }]
  accountName: { type: String, default: 'Your Brand' },
})
const emit = defineEmits(['update:modelValue'])

const activeId = ref(props.platforms[0]?.id || '')
watch(
  () => props.platforms.map((p) => p.id).join(','),
  () => {
    if (!props.platforms.find((p) => p.id === activeId.value)) activeId.value = props.platforms[0]?.id || ''
  },
)

const active = computed(() => props.platforms.find((p) => p.id === activeId.value) || props.platforms[0] || null)
const heroAsset = computed(() => props.assets.find((a) => a.file_type !== 'Video') || props.assets[0] || null)
const initials = computed(() => initialsForUser(props.accountName))
const avatarColor = computed(() => colorForUser(props.accountName))
const handle = computed(() => '@' + (props.accountName || 'yourbrand').toLowerCase().replace(/[^a-z0-9]/g, ''))

function fmtCount(n) {
  if (n >= 1000) return (n / 1000).toFixed(1).replace(/\.0$/, '') + 'K'
  return String(n)
}
</script>

<template>
  <Dialog :model-value="modelValue" :options="{ size: 'sm' }" @update:model-value="(v) => emit('update:modelValue', v)" @close="emit('update:modelValue', false)">
    <template #body>
      <div class="flex max-h-[88vh] flex-col">
        <div class="flex items-center gap-3 border-b border-gray-100 px-5 py-4">
          <h2 class="m-0 text-[15px] font-semibold">Preview</h2>
          <span class="text-[11.5px] text-ink-gray-5">Mock layout — nothing is fetched from the real platform</span>
        </div>

        <div v-if="platforms.length > 1" class="flex flex-wrap gap-1.5 border-b border-gray-100 px-5 py-3">
          <button
            v-for="p in platforms"
            :key="p.id"
            class="rounded-full px-3 py-1 text-[12px] font-medium"
            :class="active?.id === p.id ? 'bg-gray-800 text-white' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'"
            @click="activeId = p.id"
          >
            {{ p.name }}
          </button>
        </div>

        <div class="flex-1 overflow-auto bg-gray-50 px-5 py-5">
          <p v-if="!active" class="m-0 text-center text-[12.5px] text-ink-gray-5">Pick a platform first.</p>

          <!-- ================= INSTAGRAM ================= -->
          <div v-else-if="active.id === 'instagram'" class="mx-auto w-[320px] overflow-hidden rounded-lg border border-gray-200 bg-white">
            <div class="flex items-center gap-2 px-3 py-2.5">
              <div
                class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[10px] font-bold text-white ring-2 ring-offset-1"
                :style="{ background: `linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888)` }"
              >
                {{ initials }}
              </div>
              <span class="text-[13px] font-semibold text-gray-900">{{ handle.slice(1) }}</span>
              <LucideMoreHorizontal class="ml-auto h-4 w-4 text-gray-700" />
            </div>
            <div class="flex aspect-square w-full items-center justify-center bg-gray-100">
              <img v-if="heroAsset" :src="heroAsset.file_url" class="h-full w-full object-cover" />
              <LucideImage v-else class="h-10 w-10 text-gray-300" />
            </div>
            <div class="flex items-center gap-3 px-3 pt-2.5">
              <LucideHeart class="h-5.5 w-5.5 text-gray-900" />
              <LucideMessageCircle class="h-5.5 w-5.5 -scale-x-100 text-gray-900" />
              <LucideSend class="h-5 w-5 text-gray-900" />
              <LucideBookmark class="ml-auto h-5.5 w-5.5 text-gray-900" />
            </div>
            <div class="px-3 pt-1.5 text-[13px] font-semibold text-gray-900">128 likes</div>
            <div class="px-3 pt-1 text-[13px] leading-snug text-gray-900">
              <span class="font-semibold">{{ handle.slice(1) }}</span> {{ active.caption || 'Your caption will show up here…' }}
            </div>
            <div class="px-3 pt-1 text-[12px] text-gray-400">View all 12 comments</div>
            <div class="px-3 pb-2.5 pt-1 text-[10px] uppercase tracking-wide text-gray-400">2 hours ago</div>
          </div>

          <!-- ================= LINKEDIN ================= -->
          <div v-else-if="active.id === 'linkedin'" class="mx-auto w-[340px] overflow-hidden rounded-lg border border-gray-200 bg-white">
            <div class="flex items-start gap-2 px-3.5 py-3">
              <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-full text-[13px] font-bold text-white" :style="{ background: avatarColor }">{{ initials }}</div>
              <div class="min-w-0 flex-1">
                <div class="truncate text-[13.5px] font-semibold text-gray-900">{{ accountName }}</div>
                <div class="truncate text-[11.5px] text-gray-500">Marketing • Posting via Marketing Calendar</div>
                <div class="flex items-center gap-1 text-[11px] text-gray-400">
                  <span>2h</span>
                  <span>•</span>
                  <LucideGlobe class="h-3 w-3" />
                </div>
              </div>
              <LucideMoreHorizontal class="h-4 w-4 shrink-0 text-gray-500" />
            </div>
            <div class="px-3.5 pb-2 text-[13.5px] leading-snug text-gray-800">{{ active.caption || 'Your caption will show up here…' }}</div>
            <div v-if="active.link_url" class="mx-3.5 mb-2.5 rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-[11.5px] text-gray-500">{{ active.link_url }}</div>
            <div v-if="heroAsset" class="w-full bg-gray-100">
              <img :src="heroAsset.file_url" class="w-full object-cover" style="max-height: 280px" />
            </div>
            <div class="flex items-center gap-1.5 px-3.5 pt-2.5 text-[11px] text-gray-400">
              <span class="flex h-3.5 w-3.5 items-center justify-center rounded-full bg-blue-600 text-white"><LucideThumbsUp class="h-2 w-2" /></span>
              <span>42</span>
              <span class="ml-auto">8 comments</span>
            </div>
            <div class="mx-3.5 mt-2 flex items-center justify-between border-t border-gray-100 pt-1.5 pb-2 text-[11.5px] font-medium text-gray-500">
              <span class="flex items-center gap-1.5 rounded px-2 py-1.5 hover:bg-gray-50"><LucideThumbsUp class="h-4 w-4" /> Like</span>
              <span class="flex items-center gap-1.5 rounded px-2 py-1.5 hover:bg-gray-50"><LucideMessageCircle class="h-4 w-4" /> Comment</span>
              <span class="flex items-center gap-1.5 rounded px-2 py-1.5 hover:bg-gray-50"><LucideRepeat2 class="h-4 w-4" /> Repost</span>
              <span class="flex items-center gap-1.5 rounded px-2 py-1.5 hover:bg-gray-50"><LucideSend class="h-4 w-4" /> Send</span>
            </div>
          </div>

          <!-- ================= X ================= -->
          <div v-else-if="active.id === 'x'" class="mx-auto w-[340px] rounded-lg border border-gray-200 bg-white px-3.5 py-3">
            <div class="flex gap-2.5">
              <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-[12px] font-bold text-white" :style="{ background: avatarColor }">{{ initials }}</div>
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-1 text-[13.5px]">
                  <span class="truncate font-bold text-gray-900">{{ accountName }}</span>
                  <span class="truncate text-gray-500">{{ handle }}</span>
                  <span class="text-gray-400">·</span>
                  <span class="shrink-0 text-gray-500">2h</span>
                  <LucideMoreHorizontal class="ml-auto h-4 w-4 shrink-0 text-gray-400" />
                </div>
                <div class="mt-0.5 whitespace-pre-line text-[13.5px] leading-snug text-gray-900">{{ active.caption || 'Your post text will show up here…' }}</div>
                <div v-if="heroAsset" class="mt-2 overflow-hidden rounded-2xl border border-gray-200 bg-gray-100">
                  <img :src="heroAsset.file_url" class="w-full object-cover" style="max-height: 220px" />
                </div>
                <div v-if="active.link_url" class="mt-2 overflow-hidden rounded-2xl border border-gray-200">
                  <div class="bg-gray-50 px-3 py-2 text-[11.5px] text-gray-500">{{ active.link_url }}</div>
                </div>
                <div class="mt-2.5 flex items-center justify-between text-gray-500">
                  <span class="flex items-center gap-1 text-[11.5px]"><LucideMessageCircle class="h-4 w-4" /> 6</span>
                  <span class="flex items-center gap-1 text-[11.5px]"><LucideRepeat2 class="h-4 w-4" /> 3</span>
                  <span class="flex items-center gap-1 text-[11.5px]"><LucideHeart class="h-4 w-4" /> 28</span>
                  <span class="flex items-center gap-1 text-[11.5px]"><LucideBarChart2 class="h-4 w-4" /> {{ fmtCount(1240) }}</span>
                  <span class="flex items-center gap-1 text-[11.5px]"><LucideShare class="h-4 w-4" /></span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>
