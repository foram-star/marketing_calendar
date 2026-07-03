<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Button, TextInput } from 'frappe-ui'
import LucideSend from '~icons/lucide/send'
import { login, isGuest } from '@/composables/useAuth'

const router = useRouter()
const route = useRoute()

const usr = ref('')
const pwd = ref('')
const loading = ref(false)
const error = ref('')
const showPwd = ref(false)

async function onSubmit() {
  if (!usr.value || !pwd.value || loading.value) return
  loading.value = true
  error.value = ''
  try {
    await login(usr.value, pwd.value)
    const next = route.query.next && route.query.next !== '/marketing/login' ? route.query.next : '/marketing'
    router.replace(next)
  } catch (e) {
    error.value = e?.messages?.[0] || 'Invalid email or password.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex h-screen w-full items-center justify-center bg-surface-gray-1">
    <div class="w-full max-w-[360px]">
      <!-- Logo -->
      <div class="mb-8 flex flex-col items-center gap-3">
        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-gray-800 text-white">
          <LucideSend class="h-5 w-5" />
        </div>
        <div class="text-center">
          <h1 class="m-0 text-[20px] font-semibold text-gray-900">Feed</h1>
          <p class="m-0 mt-1 text-[13px] text-ink-gray-6">Sign in to your account</p>
        </div>
      </div>

      <!-- Form card -->
      <div class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <form class="flex flex-col gap-4" @submit.prevent="onSubmit">
          <div class="flex flex-col gap-1.5">
            <label class="text-[12px] font-medium text-gray-700">Email</label>
            <TextInput
              v-model="usr"
              type="email"
              placeholder="you@example.com"
              autocomplete="email"
              autofocus
            />
          </div>
          <div class="flex flex-col gap-1.5">
            <label class="text-[12px] font-medium text-gray-700">Password</label>
            <div class="relative">
              <TextInput
                v-model="pwd"
                :type="showPwd ? 'text' : 'password'"
                placeholder="••••••••"
                autocomplete="current-password"
              />
              <button
                type="button"
                class="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-700"
                @click="showPwd = !showPwd"
              >
                <LucideEyeOff v-if="showPwd" class="h-3.5 w-3.5" />
                <LucideEye v-else class="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
          <p v-if="error" class="m-0 text-[12px] font-medium text-red-600">{{ error }}</p>
          <Button type="submit" variant="solid" class="w-full justify-center" :loading="loading">
            Sign in
          </Button>
        </form>
      </div>

      <p class="mt-4 text-center text-[12.5px] text-ink-gray-6">
        Don't have an account?
        <router-link to="/marketing/signup" class="font-medium text-gray-800 hover:underline">Sign up</router-link>
      </p>
    </div>
  </div>
</template>
