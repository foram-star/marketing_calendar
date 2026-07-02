<script setup>
import IconInstagram from './icons/IconInstagram.vue'
import IconLinkedIn from './icons/IconLinkedIn.vue'
import IconX from './icons/IconX.vue'
import IconBlog from './icons/IconBlog.vue'

// 'dot'   — coloured dot, calendar pills and dense inline contexts
// 'icon'  — b/w SVG brand logo only (default)
// 'badge' — SVG icon + name, coloured pill, for filter chips and selectors
defineProps({
  platform: { type: Object, default: null },
  variant: { type: String, default: 'icon' },
  size: { type: String, default: 'sm' }, // 'sm' (14px) | 'md' (18px)
})

const ICON_MAP = {
  instagram: IconInstagram,
  linkedin: IconLinkedIn,
  x: IconX,
  blog: IconBlog,
}

function iconFor(platform) {
  if (!platform) return null
  const key = (platform.id || platform.name || '').toLowerCase()
  return ICON_MAP[key] || null
}
</script>

<template>
  <span
    v-if="variant === 'dot'"
    class="inline-block shrink-0 rounded-full"
    :class="size === 'md' ? 'h-2.5 w-2.5' : 'h-2 w-2'"
    :style="{ background: platform?.color || '#888' }"
  />

  <component
    v-else-if="variant === 'icon'"
    :is="iconFor(platform)"
    class="shrink-0"
    :class="size === 'md' ? 'h-[18px] w-[18px]' : 'h-3.5 w-3.5'"
  />

  <span
    v-else-if="variant === 'badge'"
    class="inline-flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-full px-2 py-0.5 text-[11px] font-semibold leading-tight"
    :style="{ color: platform?.color || '#555', background: platform?.soft || '#f3f4f6' }"
  >
    <component
      :is="iconFor(platform)"
      class="h-3 w-3 shrink-0"
      :style="{ color: platform?.color || '#555' }"
    />
    {{ platform?.name || '?' }}
  </span>
</template>
