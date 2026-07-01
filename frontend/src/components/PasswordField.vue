<script setup>
import { ref } from 'vue'
import LucideEye from '~icons/lucide/eye'
import LucideEyeOff from '~icons/lucide/eye-off'

defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: '' },
})
defineEmits(['update:modelValue'])

const revealed = ref(false)
</script>

<template>
  <div class="flex items-center gap-1.5 rounded-md border border-gray-200 px-2.5 py-1.5">
    <input
      :type="revealed ? 'text' : 'password'"
      :value="modelValue"
      :placeholder="placeholder"
      class="min-w-0 flex-1 border-none p-0 text-[12.5px] outline-none"
      @input="$emit('update:modelValue', $event.target.value)"
    />
    <button type="button" class="shrink-0 text-gray-400 hover:text-gray-700" @click="revealed = !revealed">
      <LucideEyeOff v-if="revealed" class="h-3.5 w-3.5" />
      <LucideEye v-else class="h-3.5 w-3.5" />
    </button>
  </div>
</template>
