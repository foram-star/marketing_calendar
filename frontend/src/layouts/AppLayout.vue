<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Avatar } from 'frappe-ui'
import LucideCalendarDays from '~icons/lucide/calendar-days'
import LucideFileText from '~icons/lucide/file-text'
import LucideFolderKanban from '~icons/lucide/folder-kanban'
import LucideImages from '~icons/lucide/images'
import LucideBarChart3 from '~icons/lucide/bar-chart-3'
import LucideSettings from '~icons/lucide/settings'
import LucideSend from '~icons/lucide/send'

const route = useRoute()

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

const currentUser = computed(() => window.user || 'Administrator')
</script>

<template>
  <div class="flex h-screen w-full overflow-hidden bg-gray-50 text-[13px] text-gray-900">
    <!-- SIDEBAR -->
    <aside class="flex w-[236px] shrink-0 flex-col border-r border-gray-100 bg-white p-3">
      <div class="flex items-center gap-2.5 px-2 pb-3.5 pt-1.5">
        <div class="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-gray-800 text-white">
          <LucideSend class="h-4 w-4" />
        </div>
        <div class="flex flex-col leading-tight">
          <span class="text-[13.5px] font-semibold">Feed</span>
        </div>
      </div>

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

      <div class="mt-auto flex items-center gap-2 border-t border-gray-100 pt-3">
        <Avatar :label="currentUser" size="md" />
        <span class="text-[12.5px] font-medium text-gray-700">{{ currentUser }}</span>
      </div>
    </aside>

    <!-- MAIN -->
    <main class="relative flex min-w-0 flex-1 flex-col">
      <router-view />
    </main>
  </div>
</template>
