<script setup>
import { ref, onMounted, computed } from 'vue'
import { Button } from 'frappe-ui'
import PlatformBadge from '@/components/PlatformBadge.vue'
import CopyableField from '@/components/CopyableField.vue'
import PasswordField from '@/components/PasswordField.vue'
import { PLATFORMS } from '@/data/platforms'
import { socialAccountsResource, fetchSocialAccounts, accountsForPlatform } from '@/data/socialAccounts'
import { useCalendarSettings } from '@/data/settings'

const settings = useCalendarSettings()

onMounted(() => {
  fetchSocialAccounts()
  const params = new URLSearchParams(window.location.search)
  if (params.get('connected')) connectNotice.value = `${params.get('connected')} connected.`
  if (params.get('connect_error')) connectNotice.value = `Connecting ${params.get('connect_error')} failed — check the Error Log in Desk for details.`
})

const CONNECTABLE = [PLATFORMS.linkedin, PLATFORMS.x, PLATFORMS.instagram]

const REAL_CONNECT_URL = {
  Instagram: '/api/method/marketing_calendar.api.connect_instagram',
  LinkedIn: '/api/method/marketing_calendar.api.connect_linkedin',
  X: '/api/method/marketing_calendar.api.connect_x',
}

const connectNotice = ref('')
function onConnectClick(platformName) {
  const url = REAL_CONNECT_URL[platformName]
  if (url) {
    window.location.href = url
    return
  }
  connectNotice.value = `${platformName} isn't wired up yet — OAuth connect comes next, once app credentials are in place below.`
  setTimeout(() => {
    if (connectNotice.value.startsWith(platformName)) connectNotice.value = ''
  }, 4000)
}

function fmtDate(dt) {
  if (!dt) return ''
  return dt.split(' ')[0]
}

const saveError = ref('')
const savedNotice = ref(false)
async function saveCredentials() {
  saveError.value = ''
  try {
    await settings.save.submit()
    savedNotice.value = true
    setTimeout(() => (savedNotice.value = false), 2500)
  } catch (e) {
    saveError.value = e?.messages?.[0] || 'Could not save credentials.'
  }
}
const saving = computed(() => settings.save.loading)
</script>

<template>
  <header class="flex items-center gap-3.5 border-b border-gray-100 bg-white px-6 pb-3.5 pt-4">
    <div class="flex flex-col gap-0.5">
      <h1 class="m-0 text-[17px] font-semibold">Settings</h1>
      <span class="text-[12px] text-gray-400">App credentials and connected accounts</span>
    </div>
    <span v-if="savedNotice" class="text-[12px] font-medium text-green-600">Saved</span>
    <span v-if="saveError" class="text-[12px] font-medium text-red-600">{{ saveError }}</span>
    <Button class="ml-auto" variant="solid" :loading="saving" @click="saveCredentials">Save credentials</Button>
  </header>

  <div v-if="settings.doc" class="flex-1 overflow-auto p-6">
    <h3 class="mb-3 text-[13px] font-semibold text-gray-700">Connected accounts & credentials</h3>
    <div class="grid grid-cols-2 gap-4 xl:grid-cols-3">
      <!-- LinkedIn -->
      <div class="flex flex-col gap-3 rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
        <div class="flex items-center gap-2">
          <PlatformBadge :platform="PLATFORMS.linkedin" />
          <span
            v-if="!accountsForPlatform('LinkedIn').length"
            class="ml-auto rounded-full bg-gray-100 px-2 py-0.5 text-[10.5px] font-semibold text-gray-500"
            >Not connected</span
          >
        </div>

        <div class="flex flex-col gap-1">
          <label class="text-[11px] font-medium text-gray-600">Client ID</label>
          <input v-model="settings.doc.linkedin_client_id" placeholder="86xxxxxxxxxxxx" class="rounded-md border border-gray-200 px-2.5 py-1.5 text-[12.5px] outline-none" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-[11px] font-medium text-gray-600">Client Secret</label>
          <PasswordField v-model="settings.doc.linkedin_client_secret" placeholder="•••••••••" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-[11px] font-medium text-gray-600">Redirect URI <span class="text-gray-400">· register this in the LinkedIn app</span></label>
          <CopyableField :model-value="settings.doc.linkedin_redirect_uri" />
        </div>
        <p class="m-0 text-[11px] leading-relaxed text-gray-400">
          Create a LinkedIn app with <b>Share on LinkedIn</b> + <b>Sign In with LinkedIn using OpenID Connect</b>, add the Redirect URI above under OAuth 2.0 settings, request
          <code>openid</code>, <code>profile</code>, <code>w_member_social</code>.
        </p>

        <div v-if="accountsForPlatform('LinkedIn').length" class="flex flex-col gap-2">
          <div v-for="acc in accountsForPlatform('LinkedIn')" :key="acc.name" class="flex flex-col gap-1 rounded-lg border border-gray-100 p-2.5">
            <div class="flex items-center gap-1.5">
              <span class="truncate text-[12px] font-semibold text-gray-800">{{ acc.account_label || acc.external_username || acc.name }}</span>
              <span class="ml-auto rounded-full px-1.5 py-0.5 text-[9.5px] font-semibold" :class="acc.status === 'Connected' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'">{{ acc.status || 'Unknown' }}</span>
            </div>
            <span v-if="acc.last_error" class="truncate text-[10.5px] text-red-500">{{ acc.last_error }}</span>
            <span v-else-if="acc.token_expires_on" class="text-[10.5px] text-gray-400">Token expires {{ fmtDate(acc.token_expires_on) }}</span>
          </div>
        </div>
        <Button class="w-full justify-center" variant="outline" @click="onConnectClick('LinkedIn')">
          {{ accountsForPlatform('LinkedIn').length ? 'Connect another account' : 'Connect LinkedIn' }}
        </Button>
      </div>

      <!-- X -->
      <div class="flex flex-col gap-3 rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
        <div class="flex items-center gap-2">
          <PlatformBadge :platform="PLATFORMS.x" />
          <span
            v-if="!accountsForPlatform('X').length"
            class="ml-auto rounded-full bg-gray-100 px-2 py-0.5 text-[10.5px] font-semibold text-gray-500"
            >Not connected</span
          >
        </div>

        <div class="flex flex-col gap-1">
          <label class="text-[11px] font-medium text-gray-600">Client ID</label>
          <input v-model="settings.doc.x_client_id" placeholder="VGhpcxxxxxxxxxxxx" class="rounded-md border border-gray-200 px-2.5 py-1.5 text-[12.5px] outline-none" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-[11px] font-medium text-gray-600">Client Secret</label>
          <PasswordField v-model="settings.doc.x_client_secret" placeholder="•••••••••" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-[11px] font-medium text-gray-600">Redirect URI <span class="text-gray-400">· register this in the X app</span></label>
          <CopyableField :model-value="settings.doc.x_redirect_uri" />
        </div>
        <p class="m-0 text-[11px] leading-relaxed text-gray-400">
          Create an X app with OAuth 2.0 (PKCE) enabled, add the Redirect URI above, request <code>tweet.read</code>, <code>tweet.write</code>, <code>users.read</code>,
          <code>offline.access</code>. Posting needs at least the Free API tier with write access.
        </p>

        <div v-if="accountsForPlatform('X').length" class="flex flex-col gap-2">
          <div v-for="acc in accountsForPlatform('X')" :key="acc.name" class="flex flex-col gap-1 rounded-lg border border-gray-100 p-2.5">
            <div class="flex items-center gap-1.5">
              <span class="truncate text-[12px] font-semibold text-gray-800">{{ acc.account_label || acc.external_username || acc.name }}</span>
              <span class="ml-auto rounded-full px-1.5 py-0.5 text-[9.5px] font-semibold" :class="acc.status === 'Connected' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'">{{ acc.status || 'Unknown' }}</span>
            </div>
            <span v-if="acc.last_error" class="truncate text-[10.5px] text-red-500">{{ acc.last_error }}</span>
            <span v-else-if="acc.token_expires_on" class="text-[10.5px] text-gray-400">Token expires {{ fmtDate(acc.token_expires_on) }}</span>
          </div>
        </div>
        <Button class="w-full justify-center" variant="outline" @click="onConnectClick('X')">
          {{ accountsForPlatform('X').length ? 'Connect another account' : 'Connect X' }}
        </Button>
      </div>

      <!-- Instagram (Meta) -->
      <div class="flex flex-col gap-3 rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
        <div class="flex items-center gap-2">
          <PlatformBadge :platform="PLATFORMS.instagram" />
          <span
            v-if="!accountsForPlatform('Instagram').length"
            class="ml-auto rounded-full bg-gray-100 px-2 py-0.5 text-[10.5px] font-semibold text-gray-500"
            >Not connected</span
          >
        </div>

        <div class="flex flex-col gap-1">
          <label class="text-[11px] font-medium text-gray-600">Meta App ID</label>
          <input v-model="settings.doc.meta_app_id" placeholder="1234567890123456" class="rounded-md border border-gray-200 px-2.5 py-1.5 text-[12.5px] outline-none" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-[11px] font-medium text-gray-600">Meta App Secret</label>
          <PasswordField v-model="settings.doc.meta_app_secret" placeholder="•••••••••" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-[11px] font-medium text-gray-600">Redirect URI <span class="text-gray-400">· OAuth login step</span></label>
          <CopyableField :model-value="settings.doc.meta_redirect_uri" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-[11px] font-medium text-gray-600">Webhook Callback URL <span class="text-gray-400">· separate "Configure webhooks" step</span></label>
          <CopyableField :model-value="settings.doc.meta_webhook_url" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-[11px] font-medium text-gray-600">Webhook Verify Token <span class="text-gray-400">· must match Meta's "Verify token" field</span></label>
          <input v-model="settings.doc.meta_webhook_verify_token" placeholder="any value, just match it on Meta's side" class="rounded-md border border-gray-200 px-2.5 py-1.5 text-[12.5px] outline-none" />
        </div>
        <p class="m-0 text-[11px] leading-relaxed text-gray-400">
          Create a Meta App with the <b>Instagram</b> product (direct Instagram Login, no Facebook Page needed), add the Redirect URI above, request
          <code>instagram_business_basic</code>, <code>instagram_business_content_publish</code>. The account must be an Instagram Business/Creator account.
        </p>

        <div v-if="accountsForPlatform('Instagram').length" class="flex flex-col gap-2">
          <div v-for="acc in accountsForPlatform('Instagram')" :key="acc.name" class="flex flex-col gap-1 rounded-lg border border-gray-100 p-2.5">
            <div class="flex items-center gap-1.5">
              <span class="truncate text-[12px] font-semibold text-gray-800">{{ acc.account_label || acc.external_username || acc.name }}</span>
              <span class="ml-auto rounded-full px-1.5 py-0.5 text-[9.5px] font-semibold" :class="acc.status === 'Connected' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'">{{ acc.status || 'Unknown' }}</span>
            </div>
            <span v-if="acc.last_error" class="truncate text-[10.5px] text-red-500">{{ acc.last_error }}</span>
            <span v-else-if="acc.token_expires_on" class="text-[10.5px] text-gray-400">Token expires {{ fmtDate(acc.token_expires_on) }}</span>
          </div>
        </div>
        <Button class="w-full justify-center" variant="outline" @click="onConnectClick('Instagram')">
          {{ accountsForPlatform('Instagram').length ? 'Connect another account' : 'Connect Instagram' }}
        </Button>
      </div>

      <!-- Blog -->
      <div class="flex flex-col gap-2 rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
        <div class="flex items-center gap-2">
          <PlatformBadge :platform="PLATFORMS.blog" />
          <span class="ml-auto rounded-full bg-green-100 px-2 py-0.5 text-[10.5px] font-semibold text-green-700">No setup needed</span>
        </div>
        <p class="m-0 text-[11.5px] text-gray-400">
          Blog posts live in this same site's Blog app — there's nothing to connect. Write the post there, then pick it from the dropdown when composing.
        </p>
      </div>
    </div>

    <div v-if="connectNotice" class="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-3.5 py-2.5 text-[12px] text-amber-800">
      {{ connectNotice }}
    </div>
  </div>
</template>
