<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Avatar, createResource, call } from 'frappe-ui'
import { Popover, PopoverButton, PopoverPanel } from '@headlessui/vue'
import LucideCalendarDays from '~icons/lucide/calendar-days'
import LucideFileText from '~icons/lucide/file-text'
import LucideFolderKanban from '~icons/lucide/folder-kanban'
import LucideImages from '~icons/lucide/images'
import LucideBarChart3 from '~icons/lucide/bar-chart-3'
import LucideSettings from '~icons/lucide/settings'
import LucideSend from '~icons/lucide/send'
import LucideBell from '~icons/lucide/bell'
import LucideLogOut from '~icons/lucide/log-out'
import LucideExternalLink from '~icons/lucide/external-link'
import { logout } from '@/composables/useAuth'

const route = useRoute()
const router = useRouter()

const navItems = [
  { to: '/marketing', name: 'Calendar', icon: LucideCalendarDays },
  { to: '/marketing/posts', name: 'Posts', icon: LucideFileText },
  { to: '/marketing/projects', name: 'Projects', icon: LucideFolderKanban },
  { to: '/marketing/assets', name: 'Assets', icon: LucideImages },
  { to: '/marketing/analytics', name: 'Analytics', icon: LucideBarChart3 },
]

function isActive(to) {
  if (to === '/marketing') return route.path === '/marketing'
  if (to === '/marketing/projects') return route.path.startsWith('/marketing/projects') || route.path.startsWith('/marketing/todo')
  return route.path.startsWith(to)
}

// Current user
const currentUser = computed(() => window.user || 'Administrator')

// User profile
const userResource = createResource({
  url: 'frappe.client.get',
  auto: true,
  params: { doctype: 'User', name: currentUser.value, fields: ['full_name', 'email', 'user_image'] },
})
const userInfo = computed(() => userResource.data || {
  full_name: currentUser.value,
  email: '',
  user_image: null,
})

// Notifications
const notificationsResource = createResource({
  url: 'frappe.client.get_list',
  auto: false,
  params: {
    doctype: 'Notification Log',
    filters: [['for_user', '=', currentUser.value], ['read', '=', 0]],
    fields: ['name', 'subject', 'creation', 'link', 'document_type', 'document_name'],
    limit_page_length: 15,
    order_by: 'creation desc',
  },
})

const unreadCount = computed(() => (notificationsResource.data || []).length)

onMounted(() => {
  notificationsResource.fetch()
})

async function openNotifications() {
  // Mark all as read after opening
  const names = (notificationsResource.data || []).map(n => n.name)
  if (names.length) {
    try {
      await call('frappe.client.set_value', {
        doctype: 'Notification Log',
        name: names[0],
        fieldname: 'read',
        value: 1,
      })
      // Bulk mark — call for each since set_value works per-doc
      for (const name of names) {
        await call('frappe.client.set_value', { doctype: 'Notification Log', name, fieldname: 'read', value: 1 })
      }
    } catch { /* non-critical */ }
    await notificationsResource.fetch()
  }
}

function fmtNotificationTime(creation) {
  if (!creation) return ''
  const d = new Date(creation)
  const now = new Date()
  const diffMin = Math.floor((now - d) / 60000)
  if (diffMin < 1) return 'just now'
  if (diffMin < 60) return `${diffMin}m ago`
  const diffH = Math.floor(diffMin / 60)
  if (diffH < 24) return `${diffH}h ago`
  return `${Math.floor(diffH / 24)}d ago`
}

async function handleLogout() {
  await logout()
  router.push('/marketing/login')
}
</script>

<template>
  <div class="flex h-screen w-full overflow-hidden bg-gray-50 text-[13px] text-gray-900">
    <!-- SIDEBAR -->
    <aside class="flex w-[236px] shrink-0 flex-col border-r border-gray-100 bg-white p-3">

      <!-- App logo -->
      <div class="flex items-center gap-2.5 px-2 pb-3.5 pt-1.5">
        <div class="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-white" style="background:#8B7CF8">
          <LucideSend class="h-4 w-4" />
        </div>
        <span class="text-[13.5px] font-semibold">Feed</span>
      </div>

      <!-- Nav -->
      <nav class="mt-1.5 flex flex-col gap-0.5">
        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-[13px] font-medium"
          :class="isActive(item.to) ? 'bg-gray-100 text-gray-900' : 'text-gray-600 hover:bg-gray-50'"
        >
          <component :is="item.icon" class="h-4 w-4" />
          <span>{{ item.name }}</span>
        </router-link>
        <router-link
          to="/marketing/settings"
          class="mt-3 flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-[13px] font-medium"
          :class="isActive('/marketing/settings') ? 'bg-gray-100 text-gray-900' : 'text-gray-600 hover:bg-gray-50'"
        >
          <LucideSettings class="h-4 w-4" />
          <span>Settings</span>
        </router-link>
      </nav>

      <!-- Bottom: Bell + Profile -->
      <div class="mt-auto flex items-center gap-1.5 border-t border-gray-100 pt-3">

        <!-- Bell notifications -->
        <Popover class="relative">
          <PopoverButton as="button"
            class="relative flex h-7 w-7 items-center justify-center rounded-md text-gray-500 hover:bg-gray-100 hover:text-gray-800"
            @click="openNotifications"
          >
            <LucideBell class="h-4 w-4" />
            <span
              v-if="unreadCount"
              class="absolute right-0.5 top-0.5 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-red-500 text-[8px] font-bold text-white"
            >{{ unreadCount > 9 ? '9+' : unreadCount }}</span>
          </PopoverButton>
          <PopoverPanel class="absolute bottom-full left-0 z-50 mb-2 w-[280px] rounded-xl border border-gray-100 bg-white shadow-xl">
            <div class="flex items-center justify-between border-b border-gray-100 px-3.5 py-2.5">
              <span class="text-[12.5px] font-semibold text-gray-800">Notifications</span>
              <span class="text-[11px] text-ink-gray-6">{{ unreadCount }} unread</span>
            </div>
            <div class="max-h-[320px] overflow-y-auto">
              <div
                v-for="n in notificationsResource.data || []"
                :key="n.name"
                class="flex flex-col gap-0.5 px-3.5 py-2.5 hover:bg-gray-50"
              >
                <span class="text-[12px] font-medium leading-snug text-gray-800">{{ n.subject }}</span>
                <span class="text-[10.5px] text-ink-gray-6">{{ fmtNotificationTime(n.creation) }}</span>
              </div>
              <div v-if="!(notificationsResource.data || []).length" class="px-3.5 py-5 text-center text-[12px] text-ink-gray-6">
                No new notifications
              </div>
            </div>
          </PopoverPanel>
        </Popover>

        <!-- Profile dropdown -->
        <Popover class="relative flex-1">
          <PopoverButton as="button" class="flex w-full min-w-0 items-center gap-2 rounded-md px-1.5 py-1 hover:bg-gray-50">
            <Avatar :label="userInfo.full_name || currentUser" :image="userInfo.user_image" size="sm" />
            <span class="min-w-0 flex-1 truncate text-left text-[12px] font-medium text-gray-700">
              {{ userInfo.full_name || currentUser }}
            </span>
          </PopoverButton>
          <PopoverPanel class="absolute bottom-full left-0 z-50 mb-2 w-[220px] rounded-xl border border-gray-100 bg-white shadow-xl">
            <!-- User info -->
            <div class="border-b border-gray-100 px-3.5 py-3">
              <div class="flex items-center gap-2.5">
                <Avatar :label="userInfo.full_name || currentUser" :image="userInfo.user_image" size="md" />
                <div class="min-w-0">
                  <div class="truncate text-[12.5px] font-semibold text-gray-900">{{ userInfo.full_name || currentUser }}</div>
                  <div class="truncate text-[11px] text-ink-gray-6">{{ userInfo.email || currentUser }}</div>
                </div>
              </div>
            </div>

            <!-- Actions -->
            <div class="py-1">
              <a
                href="/app"
                target="_blank"
                class="flex items-center gap-2.5 px-3.5 py-2 text-[12.5px] text-gray-700 hover:bg-gray-50"
              >
                <LucideExternalLink class="h-3.5 w-3.5 shrink-0 text-gray-400" />
                Back to Desk
              </a>
              <button
                class="flex w-full items-center gap-2.5 px-3.5 py-2 text-left text-[12.5px] text-gray-700 hover:bg-gray-50"
                @click="handleLogout"
              >
                <LucideLogOut class="h-3.5 w-3.5 shrink-0 text-gray-400" />
                Log out
              </button>
            </div>
          </PopoverPanel>
        </Popover>
      </div>
    </aside>

    <!-- MAIN -->
    <main class="relative flex min-w-0 flex-1 flex-col">
      <router-view />
    </main>
  </div>
</template>
