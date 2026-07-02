<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Button, TextInput } from 'frappe-ui'
import LucideMegaphone from '~icons/lucide/megaphone'
import { signup } from '@/composables/useAuth'

const router = useRouter()

const fullName = ref('')
const email = ref('')
const loading = ref(false)
const error = ref('')
const done = ref(false)

async function onSubmit() {
  if (!email.value || !fullName.value || loading.value) return
  loading.value = true
  error.value = ''
  try {
    await signup(email.value, fullName.value)
    done.value = true
  } catch (e) {
    error.value = e?.messages?.[0] || 'Could not create account. The email may already be registered.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex h-screen w-full items-center justify-center bg-surface-gray-1">
    <div class="w-full max-w-[360px]">
      <div class="mb-8 flex flex-col items-center gap-3">
        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-gray-800 text-white">
          <LucideMegaphone class="h-5 w-5" />
        </div>
        <div class="text-center">
          <h1 class="m-0 text-[20px] font-semibold text-gray-900">Marketing Calendar</h1>
          <p class="m-0 mt-1 text-[13px] text-ink-gray-6">Create your account</p>
        </div>
      </div>

      <!-- Success state -->
      <div v-if="done" class="rounded-xl border border-gray-200 bg-white p-6 text-center shadow-sm">
        <LucideCheckCircle2 class="mx-auto mb-3 h-8 w-8 text-green-600" />
        <p class="m-0 text-[13px] font-medium text-gray-800">Check your email</p>
        <p class="m-0 mt-1 text-[12px] text-ink-gray-6">We've sent a verification link to <b>{{ email }}</b>. Click it to activate your account.</p>
        <router-link to="/marketing/login" class="mt-4 block text-[12.5px] font-medium text-gray-800 hover:underline">Back to sign in</router-link>
      </div>

      <!-- Form card -->
      <div v-else class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <form class="flex flex-col gap-4" @submit.prevent="onSubmit">
          <div class="flex flex-col gap-1.5">
            <label class="text-[12px] font-medium text-gray-700">Full name</label>
            <TextInput v-model="fullName" placeholder="Your name" autocomplete="name" autofocus />
          </div>
          <div class="flex flex-col gap-1.5">
            <label class="text-[12px] font-medium text-gray-700">Email</label>
            <TextInput v-model="email" type="email" placeholder="you@example.com" autocomplete="email" />
          </div>
          <p v-if="error" class="m-0 text-[12px] font-medium text-red-600">{{ error }}</p>
          <Button type="submit" variant="solid" class="w-full justify-center" :loading="loading">
            Create account
          </Button>
        </form>
      </div>

      <p class="mt-4 text-center text-[12.5px] text-ink-gray-6">
        Already have an account?
        <router-link to="/marketing/login" class="font-medium text-gray-800 hover:underline">Sign in</router-link>
      </p>
    </div>
  </div>
</template>
