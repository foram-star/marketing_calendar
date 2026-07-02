<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, TextInput } from 'frappe-ui'
import { Popover, PopoverButton, PopoverPanel } from '@headlessui/vue'
import LucideChevronsUpDown from '~icons/lucide/chevrons-up-down'
import LucideX from '~icons/lucide/x'
import LucideTrash2 from '~icons/lucide/trash-2'
import { todosResource, fetchTodos, createTodo, updateTodo, deleteTodo } from '@/data/todos'
import { projectsResource, fetchProjects } from '@/data/projects'
import { memberById } from '@/data/team'

const route = useRoute()
const router = useRouter()

onMounted(() => {
  fetchTodos()
  fetchProjects()
})

const newTitle = ref('')
// Pre-fills from the project you're already filtered to (e.g. arriving via
// a project card's "2/4" badge), but stays a normal dropdown you can change
// before adding — the filter is just a sensible default, not a constraint.
const selectedProject = ref(route.query.project || '')
watch(() => route.query.project, (val) => { selectedProject.value = val || '' })

const adding = ref(false)
async function addTodo() {
  if (!newTitle.value.trim() || adding.value) return
  adding.value = true
  try {
    await createTodo({
      title: newTitle.value.trim(),
      marketing_project: selectedProject.value || null,
    })
    newTitle.value = ''
  } finally {
    adding.value = false
  }
}

function toggleDone(todo) {
  todo.done = todo.done ? 0 : 1 // optimistic
  updateTodo(todo.name, { done: todo.done })
}

function removeTodo(todo) {
  todosResource.data = (todosResource.data || []).filter((t) => t.name !== todo.name)
  deleteTodo(todo.name)
}

const projectFilter = computed(() => route.query.project || '')
const filteredProject = computed(() => (projectsResource.data || []).find((p) => p.name === projectFilter.value))
function clearProjectFilter() {
  router.push({ name: 'Todo' })
}

const visibleTodos = computed(() => {
  const list = todosResource.data || []
  return projectFilter.value ? list.filter((t) => t.marketing_project === projectFilter.value) : list
})
const pendingTodos = computed(() => visibleTodos.value.filter((t) => !t.done))
const doneTodos = computed(() => visibleTodos.value.filter((t) => t.done))

function projectTitle(name) {
  return (projectsResource.data || []).find((p) => p.name === name)?.title || name
}
</script>

<template>
  <header class="flex items-center gap-3.5 border-b border-gray-100 bg-white px-6 pb-3.5 pt-4">
    <div class="flex flex-col gap-0.5">
      <h1 class="m-0 text-[17px] font-semibold">Todo</h1>
      <span class="text-[12px] text-ink-gray-6">{{ pendingTodos.length }} open · {{ doneTodos.length }} done</span>
    </div>
    <button
      v-if="filteredProject"
      class="ml-3 flex items-center gap-1.5 rounded-full bg-gray-100 px-2.5 py-1 text-[11.5px] font-medium text-gray-600"
      @click="clearProjectFilter"
    >
      Project: {{ filteredProject.title }}
      <LucideX class="h-3 w-3" />
    </button>
  </header>

  <div class="flex-1 overflow-y-auto p-6">
    <div class="mx-auto flex max-w-[640px] flex-col gap-4">
      <div class="flex items-center gap-2 rounded-xl border border-gray-100 bg-white p-2 shadow-sm">
        <TextInput
          v-model="newTitle"
          placeholder="Add a task and press Enter…"
          class="flex-1"
          @keydown.enter="addTodo"
        />
        <Popover class="relative shrink-0">
          <PopoverButton as="div">
            <div class="flex h-7 w-[190px] cursor-pointer items-center gap-1.5 rounded-md border border-gray-200 bg-white px-2.5 text-[13px] text-gray-700">
              <span class="flex-1 truncate" :class="selectedProject ? 'text-gray-800' : 'text-ink-gray-6'">
                {{ selectedProject ? projectTitle(selectedProject) : 'No project' }}
              </span>
              <LucideChevronsUpDown class="h-3.5 w-3.5 shrink-0 text-gray-400" />
            </div>
          </PopoverButton>
          <PopoverPanel class="absolute left-0 top-full z-20 mt-1.5 max-h-52 w-[190px] overflow-y-auto rounded-lg border border-gray-100 bg-white py-1 shadow-lg">
            <PopoverButton as="button" class="flex w-full items-center px-3 py-1.5 text-left text-[12.5px] hover:bg-gray-50" :class="!selectedProject ? 'font-semibold text-gray-900' : 'text-gray-500'" @click="selectedProject = ''">No project</PopoverButton>
            <PopoverButton as="button" v-for="p in projectsResource.data || []" :key="p.name"
              class="flex w-full items-center gap-2 px-3 py-1.5 text-left text-[12.5px] hover:bg-gray-50"
              :class="selectedProject === p.name ? 'font-semibold text-gray-900' : 'text-gray-600'"
              @click="selectedProject = p.name"
            >{{ p.title }}</PopoverButton>
          </PopoverPanel>
        </Popover>
        <Button size="sm" variant="solid" :loading="adding" :disabled="!newTitle.trim()" @click="addTodo">Add</Button>
      </div>

      <div class="flex flex-col gap-1.5">
        <div
          v-for="todo in pendingTodos"
          :key="todo.name"
          :data-testid="`todo-${todo.name}`"
          class="group flex items-center gap-2.5 rounded-lg border border-gray-100 bg-white px-3 py-2.5 shadow-sm"
        >
          <button
            class="flex h-4.5 w-4.5 shrink-0 items-center justify-center rounded-full border-[1.5px] border-gray-300 hover:border-gray-800"
            @click="toggleDone(todo)"
          />
          <span class="flex-1 text-[13px] text-gray-900">{{ todo.title }}</span>
          <button
            v-if="todo.marketing_project"
            class="shrink-0 rounded-full bg-gray-100 px-2 py-0.5 text-[10.5px] font-medium text-gray-500 hover:bg-gray-200"
            @click="router.push({ name: 'Todo', query: { project: todo.marketing_project } })"
          >
            {{ projectTitle(todo.marketing_project) }}
          </button>
          <span v-if="todo.assigned_to" class="shrink-0 text-[10.5px] text-ink-gray-6">{{ memberById(todo.assigned_to).name }}</span>
          <LucideTrash2 class="h-3.5 w-3.5 shrink-0 cursor-pointer text-gray-300 opacity-0 group-hover:opacity-100 hover:text-red-500" @click="removeTodo(todo)" />
        </div>
        <div v-if="!pendingTodos.length" class="rounded-lg border border-dashed border-gray-200 p-5 text-center text-[12px] text-ink-gray-6">
          Nothing open{{ filteredProject ? ` for ${filteredProject.title}` : '' }} — add one above.
        </div>
      </div>

      <div v-if="doneTodos.length" class="flex flex-col gap-1.5">
        <span class="px-1 text-[11px] font-medium uppercase tracking-wide text-ink-gray-6">Done · {{ doneTodos.length }}</span>
        <div
          v-for="todo in doneTodos"
          :key="todo.name"
          :data-testid="`todo-${todo.name}`"
          class="group flex items-center gap-2.5 rounded-lg border border-gray-100 bg-surface-gray-1 px-3 py-2.5"
        >
          <button
            class="flex h-4.5 w-4.5 shrink-0 items-center justify-center rounded-full bg-gray-800 text-white"
            @click="toggleDone(todo)"
          >
            <svg viewBox="0 0 16 16" class="h-2.5 w-2.5" fill="none"><path d="M3 8.5L6 11.5L13 4.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" /></svg>
          </button>
          <span class="flex-1 text-[13px] text-ink-gray-6 line-through">{{ todo.title }}</span>
          <button
            v-if="todo.marketing_project"
            class="shrink-0 rounded-full bg-gray-100 px-2 py-0.5 text-[10.5px] font-medium text-ink-gray-6 hover:bg-gray-200"
            @click="router.push({ name: 'Todo', query: { project: todo.marketing_project } })"
          >
            {{ projectTitle(todo.marketing_project) }}
          </button>
          <LucideTrash2 class="h-3.5 w-3.5 shrink-0 cursor-pointer text-gray-300 opacity-0 group-hover:opacity-100 hover:text-red-500" @click="removeTodo(todo)" />
        </div>
      </div>
    </div>
  </div>
</template>
