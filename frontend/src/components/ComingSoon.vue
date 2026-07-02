<script setup>
import LucideConstruction from '~icons/lucide/construction'

defineProps({
  title: { type: String, required: true },
  description: { type: String, required: true },
})
</script>

<template>
  <header class="flex items-center gap-3.5 border-b border-gray-100 bg-white px-6 pb-3.5 pt-4">
    <div class="flex flex-col gap-0.5">
      <h1 class="m-0 text-[17px] font-semibold">{{ title }}</h1>
      <span class="text-[12px] text-ink-gray-6">{{ description }}</span>
    </div>
  </header>
  <div class="flex flex-1 items-center justify-center text-ink-gray-6">
    <div class="flex flex-col items-center gap-2 text-center">
      <div class="flex h-14 w-14 items-center justify-center rounded-2xl bg-gray-100">
        <LucideConstruction class="h-6 w-6 text-gray-400" />
      </div>
      <p class="m-0 text-[13px] font-medium text-gray-500">Coming up in a later build phase</p>
    </div>
  </div>
</template>
