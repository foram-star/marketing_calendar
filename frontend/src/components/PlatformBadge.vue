<script setup>
// "dot" — tight spaces like calendar cells or inline next to a printed name.
// "text" — compact badge showing the short-form platform name (IG / LI / X /
//   Blog). Sized and styled to match the status badges in the Posts list so
//   both columns look like they belong to the same design system.
defineProps({
  platform: { type: Object, default: null },
  variant: { type: String, default: 'text' }, // 'text' | 'dot'
})
</script>

<template>
  <span
    v-if="variant === 'dot'"
    class="inline-block h-2 w-2 shrink-0 rounded-full"
    :style="{ background: platform?.color || '#888' }"
  />
  <span
    v-else
    class="shrink-0 whitespace-nowrap rounded-full px-2 py-0.5 text-[11px] font-semibold leading-tight"
    :style="{ color: platform?.color || '#888', background: platform?.soft || '#f3f4f6' }"
    >{{ platform?.short || platform?.name || '?' }}</span
  >
</template>
