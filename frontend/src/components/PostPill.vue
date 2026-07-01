<script setup>
import { computed } from 'vue'
import { fmtTime } from '@/utils/date'
import { pillColors } from '@/utils/colors'
import PlatformBadge from './PlatformBadge.vue'

const props = defineProps({
  post: { type: Object, required: true },
  colorBy: { type: String, default: 'platform' },
  dense: { type: Boolean, default: false },
})
const emit = defineEmits(['enter', 'leave'])

const colors = computed(() => pillColors(props.post, props.colorBy))
const time = computed(() => fmtTime(props.post._dt?.time))
</script>

<template>
  <div
    class="flex cursor-default items-center gap-1 overflow-hidden rounded px-1.5 py-0.5"
    :class="dense ? '' : 'gap-1.5'"
    :style="{ background: colors.bg, borderLeft: `2.5px solid ${colors.bar}` }"
    @mouseenter="emit('enter', $event, post)"
    @mouseleave="emit('leave')"
  >
    <span
      class="flex-1 truncate text-[11px] font-semibold"
      :style="{ color: colors.fg }"
      >{{ post.title }}</span
    >
    <span class="flex shrink-0 items-center gap-1">
      <PlatformBadge v-for="p in post.platforms" :key="p.platform" :platform="p.meta" variant="dot" />
    </span>
  </div>
</template>
