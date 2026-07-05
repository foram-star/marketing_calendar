<script setup>
import { ref, onMounted, computed } from 'vue'
import { Button, TextInput, call } from 'frappe-ui'
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

// LinkedIn org picker
const linkedinOrgs = ref(null)   // null = not loaded, [] = loaded but no orgs
const linkedinOrgsLoading = ref(false)
async function loadLinkedInOrgs() {
  linkedinOrgsLoading.value = true
  try {
    linkedinOrgs.value = await call('marketing_calendar.api.get_linkedin_organizations')
  } catch { linkedinOrgs.value = null }
  finally { linkedinOrgsLoading.value = false }
}
async function setLinkedInOrg(orgId) {
  if (!linkedinOrgs.value?.account) return
  await call('frappe.client.set_value', {
    doctype: 'Feed Social Account',
    name: linkedinOrgs.value.account,
    fieldname: 'organization_id',
    value: orgId,
  })
  linkedinOrgs.value.current_org_id = orgId
}
</script>

<template>
  <header class="flex items-center gap-3.5 border-b border-gray-100 bg-white px-6 pb-3.5 pt-4">
    <div class="flex flex-col gap-0.5">
      <h1 class="m-0 text-[17px] font-semibold">Settings</h1>
      <span class="text-[12px] text-ink-gray-6">App credentials and connected accounts</span>
    </div>
    <span v-if="savedNotice" class="text-[12px] font-medium text-green-600">Saved</span>
    <span v-if="saveError" class="text-[12px] font-medium text-red-600">{{ saveError }}</span>
    <Button class="ml-auto" variant="solid" :loading="saving" @click="saveCredentials">Save credentials</Button>
  </header>

  <!-- Loading -->
  <div v-if="settings.get.loading" class="flex flex-1 items-center justify-center">
    <span class="text-[13px] text-ink-gray-6">Loading settings…</span>
  </div>

  <!-- Error / not found -->
  <div v-else-if="settings.get.error" class="flex flex-1 flex-col items-center justify-center gap-2 text-center">
    <p class="m-0 text-[13px] font-medium text-gray-800">Could not load settings</p>
    <p class="m-0 text-[12px] text-ink-gray-6">{{ settings.get.error.message || 'Check that you have System Manager or Marketing Manager role.' }}</p>
    <button class="mt-2 text-[12px] font-medium text-gray-700 hover:underline" @click="settings.get.fetch()">Retry</button>
  </div>

  <div v-else-if="settings.doc" class="flex-1 overflow-auto p-6">
    <h3 class="mb-3 text-[13px] font-semibold text-gray-700">Connected accounts & credentials</h3>
    <div class="grid grid-cols-2 gap-4 xl:grid-cols-3">
      <!-- LinkedIn -->
      <div class="flex flex-col gap-3 rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
        <div class="flex items-center gap-2">
          <PlatformBadge :platform="PLATFORMS.linkedin" variant="badge" size="md" />
          <span
            v-if="!accountsForPlatform('LinkedIn').length"
            class="ml-auto rounded-full bg-gray-100 px-2 py-0.5 text-[10.5px] font-semibold text-gray-500"
            >Not connected</span
          >
        </div>

        <div class="flex flex-col gap-1">
          <label class="text-[11px] font-medium text-gray-600">Client ID</label>
          <TextInput v-model="settings.doc.linkedin_client_id" placeholder="86xxxxxxxxxxxx" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-[11px] font-medium text-gray-600">Client Secret</label>
          <PasswordField v-model="settings.doc.linkedin_client_secret" placeholder="•••••••••" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-[11px] font-medium text-gray-600">Redirect URI <span class="text-ink-gray-6">· register this in the LinkedIn app</span></label>
          <CopyableField :model-value="settings.doc.linkedin_redirect_uri" />
        </div>
        <p class="m-0 text-[11px] leading-relaxed text-ink-gray-6">
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
            <span v-else-if="acc.token_expires_on" class="text-[10.5px] text-ink-gray-6">Token expires {{ fmtDate(acc.token_expires_on) }}</span>

            <!-- Post-as selector -->
            <div class="mt-1.5 flex flex-col gap-1">
              <div class="flex items-center justify-between">
                <label class="text-[10.5px] font-medium text-gray-600">Post as</label>
                <button class="text-[10px] text-ink-gray-6 hover:underline" @click="loadLinkedInOrgs">
                  {{ linkedinOrgsLoading ? 'Loading…' : linkedinOrgs ? 'Refresh' : 'Load pages' }}
                </button>
              </div>
              <button v-if="!linkedinOrgs && !linkedinOrgsLoading"
                class="w-full rounded-md border border-dashed border-gray-200 bg-gray-50 px-2.5 py-2 text-left text-[11px] text-ink-gray-6 hover:bg-gray-100"
                @click="loadLinkedInOrgs">
                Click to load your company pages…
              </button>
              <div v-else-if="linkedinOrgsLoading" class="text-[11px] text-ink-gray-6">Fetching your company pages…</div>
              <select v-else
                class="form-select w-full text-[11.5px]"
                :value="linkedinOrgs.current_org_id"
                @change="setLinkedInOrg($event.target.value)">
                <option value="">{{ linkedinOrgs.personal_name }} — personal profile</option>
                <option v-for="org in linkedinOrgs.organizations" :key="org.id" :value="org.id">
                  {{ org.name }}
                </option>
              </select>
              <p v-if="linkedinOrgs && !linkedinOrgs.organizations.length" class="m-0 text-[10px] text-amber-600">
                No company pages found. Make sure you're an admin of the page, then reconnect LinkedIn to get the w_organization_social scope.
              </p>
            </div>
          </div>
        </div>
        <Button class="w-full justify-center" variant="outline" @click="onConnectClick('LinkedIn')">
          {{ accountsForPlatform('LinkedIn').length ? 'Connect another account' : 'Connect LinkedIn' }}
        </Button>
      </div>

      <!-- X -->
      <div class="flex flex-col gap-3 rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
        <div class="flex items-center gap-2">
          <PlatformBadge :platform="PLATFORMS.x" variant="badge" size="md" />
          <span
            v-if="!accountsForPlatform('X').length"
            class="ml-auto rounded-full bg-gray-100 px-2 py-0.5 text-[10.5px] font-semibold text-gray-500"
            >Not connected</span
          >
        </div>

        <div class="flex flex-col gap-1">
          <label class="text-[11px] font-medium text-gray-600">Client ID</label>
          <TextInput v-model="settings.doc.x_client_id" placeholder="VGhpcxxxxxxxxxxxx" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-[11px] font-medium text-gray-600">Client Secret</label>
          <PasswordField v-model="settings.doc.x_client_secret" placeholder="•••••••••" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-[11px] font-medium text-gray-600">Redirect URI <span class="text-ink-gray-6">· register this in the X app</span></label>
          <CopyableField :model-value="settings.doc.x_redirect_uri" />
        </div>
        <p class="m-0 text-[11px] leading-relaxed text-ink-gray-6">
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
            <span v-else-if="acc.token_expires_on" class="text-[10.5px] text-ink-gray-6">Token expires {{ fmtDate(acc.token_expires_on) }}</span>
          </div>
        </div>
        <Button class="w-full justify-center" variant="outline" @click="onConnectClick('X')">
          {{ accountsForPlatform('X').length ? 'Connect another account' : 'Connect X' }}
        </Button>
      </div>

      <!-- Instagram (Meta) -->
      <div class="flex flex-col gap-3 rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
        <div class="flex items-center gap-2">
          <PlatformBadge :platform="PLATFORMS.instagram" variant="badge" size="md" />
          <span
            v-if="!accountsForPlatform('Instagram').length"
            class="ml-auto rounded-full bg-gray-100 px-2 py-0.5 text-[10.5px] font-semibold text-gray-500"
            >Not connected</span
          >
        </div>

        <div class="flex flex-col gap-1">
          <label class="text-[11px] font-medium text-gray-600">Meta App ID</label>
          <TextInput v-model="settings.doc.meta_app_id" placeholder="1234567890123456" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-[11px] font-medium text-gray-600">Meta App Secret</label>
          <PasswordField v-model="settings.doc.meta_app_secret" placeholder="•••••••••" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-[11px] font-medium text-gray-600">Redirect URI <span class="text-ink-gray-6">· OAuth login step</span></label>
          <CopyableField :model-value="settings.doc.meta_redirect_uri" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-[11px] font-medium text-gray-600">Webhook Callback URL <span class="text-ink-gray-6">· separate "Configure webhooks" step</span></label>
          <CopyableField :model-value="settings.doc.meta_webhook_url" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-[11px] font-medium text-gray-600">Webhook Verify Token <span class="text-ink-gray-6">· must match Meta's "Verify token" field</span></label>
          <TextInput v-model="settings.doc.meta_webhook_verify_token" placeholder="any value, just match it on Meta's side" />
        </div>
        <p class="m-0 text-[11px] leading-relaxed text-ink-gray-6">
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
            <span v-else-if="acc.token_expires_on" class="text-[10.5px] text-ink-gray-6">Token expires {{ fmtDate(acc.token_expires_on) }}</span>
          </div>
        </div>
        <Button class="w-full justify-center" variant="outline" @click="onConnectClick('Instagram')">
          {{ accountsForPlatform('Instagram').length ? 'Connect another account' : 'Connect Instagram' }}
        </Button>
      </div>

      <!-- Blog -->
      <div class="flex flex-col gap-2 rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
        <div class="flex items-center gap-2">
          <PlatformBadge :platform="PLATFORMS.blog" variant="badge" size="md" />
          <span class="ml-auto rounded-full bg-green-100 px-2 py-0.5 text-[10.5px] font-semibold text-green-700">No setup needed</span>
        </div>
        <p class="m-0 text-[11.5px] text-ink-gray-6">
          Blog posts live in this same site's Blog app — there's nothing to connect. Write the post there, then pick it from the dropdown when composing.
        </p>
      </div>
    </div>

    <div v-if="connectNotice" class="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-3.5 py-2.5 text-[12px] text-amber-800">
      {{ connectNotice }}
    </div>
  </div>
</template>
