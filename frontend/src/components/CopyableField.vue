<script setup>
import { ref } from 'vue'
import LucideCopy from '~icons/lucide/copy'
import LucideCheck from '~icons/lucide/check'

const props = defineProps({
  modelValue: { type: String, default: '' },
})

const copied = ref(false)
async function copy() {
  if (!props.modelValue) return
  await navigator.clipboard.writeText(props.modelValue)
  copied.value = true
  setTimeout(() => (copied.value = false), 1500)
}
</script>

<template>
  <div class="flex items-center gap-1.5 rounded-md border border-gray-200 bg-gray-50 px-2.5 py-1.5">
    <span class="min-w-0 flex-1 truncate text-[12px] text-gray-600">{{ modelValue || '—' }}</span>
    <button class="shrink-0 text-gray-400 hover:text-gray-700" @click="copy">
      <LucideCheck v-if="copied" class="h-3.5 w-3.5 text-green-600" />
      <LucideCopy v-else class="h-3.5 w-3.5" />
    </button>
  </div>
</template>
