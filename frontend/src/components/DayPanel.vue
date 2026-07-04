<script setup>
import { computed } from 'vue'
import { Button, Avatar } from 'frappe-ui'
import LucideCalendarX from '~icons/lucide/calendar-x'
import { MONTH_NAMES, fmtTime } from '@/utils/date'
import { memberById } from '@/data/team'
import PlatformBadge from './PlatformBadge.vue'

const props = defineProps({
  day: { type: Object, default: null }, // { y, m, d, posts }
})
const emit = defineEmits(['close', 'schedule', 'open-post'])

const weekdayLabel = computed(() => {
  if (!props.day) return ''
  return ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][
    new Date(props.day.y, props.day.m, props.day.d).getDay()
  ]
})
const dateLabel = computed(() => (props.day ? `${MONTH_NAMES[props.day.m]} ${props.day.d}` : ''))
const subtitle = computed(() => {
  const n = props.day?.posts?.length || 0
  if (!n) return 'No posts'
  return n === 1 ? '1 post scheduled' : `${n} posts scheduled`
})
</script>

<template>
  <div v-if="day" class="fixed inset-0 z-30" @click.self="emit('close')">
    <div class="fixed inset-0 bg-black/20" @click="emit('close')" />
    <div class="absolute right-0 top-0 flex h-full w-[392px] flex-col bg-white shadow-2xl">
      <div class="flex items-start gap-2.5 border-b border-gray-100 px-5 pb-3.5 pt-4.5">
        <div class="flex flex-col gap-0.5">
          <span class="text-[11.5px] font-semibold uppercase tracking-wide text-gray-500">{{ weekdayLabel }}</span>
          <h3 class="m-0 text-[19px] font-semibold">{{ dateLabel }}</h3>
          <span class="text-[12px] text-ink-gray-6">{{ subtitle }}</span>
        </div>
        <Button variant="ghost" class="ml-auto" icon="x" @click="emit('close')" />
      </div>

      <div class="flex flex-1 flex-col gap-2.5 overflow-auto p-5">
        <div
          v-for="post in day.posts"
          :key="post.name"
          :data-testid="`day-panel-post-${post.name}`"
          class="flex cursor-pointer flex-col gap-2 rounded-xl border border-gray-100 p-3.5 shadow-sm hover:border-gray-200"
          @click="emit('open-post', post)"
        >
          <div class="flex items-center gap-2">
            <span class="text-[12px] font-semibold">{{ fmtTime(post._dt?.time) }}</span>
            <span
              class="rounded-full px-2 py-0.5 text-[10.5px] font-semibold"
              :style="{ color: post.statusMeta.c, background: post.statusMeta.bg }"
              >{{ post.status }}</span
            >
            <div class="ml-auto flex gap-1">
              <PlatformBadge v-for="p in post.platforms" :key="p.platform" :platform="p.meta" />
            </div>
          </div>
          <span class="text-[13.5px] font-semibold leading-snug">{{ post.title }}</span>
          <span v-if="post.platforms?.[0]?.caption" class="truncate text-[12px] leading-relaxed text-ink-gray-6">{{ post.platforms[0].caption }}</span>
          <div class="flex items-center gap-1.5 border-t border-gray-100 pt-1.5">
            <Avatar :label="memberById(post.assigned_to).name" size="sm" />
            <span class="text-[11.5px] font-medium text-gray-600">{{ memberById(post.assigned_to).name }}</span>
          </div>
        </div>

        <div v-if="!day.posts.length" class="flex flex-1 flex-col items-center justify-center gap-3.5 px-4 py-10 text-center">
          <div class="flex h-[60px] w-[60px] items-center justify-center rounded-2xl bg-gray-100">
            <LucideCalendarX class="h-6 w-6 text-gray-400" />
          </div>
          <div class="flex flex-col gap-1">
            <span class="text-[14px] font-semibold text-gray-700">No posts scheduled</span>
            <span class="max-w-[220px] text-[12.5px] leading-relaxed text-ink-gray-6">
              Nothing scheduled.
            </span>
          </div>
        </div>
      </div>

      <div class="border-t border-gray-100 p-5">
        <Button variant="solid" class="w-full justify-center" @click="emit('schedule')">
          <template #prefix><LucidePlus class="h-3.5 w-3.5" /></template>
          Schedule new post
        </Button>
      </div>
    </div>
  </div>
</template>
