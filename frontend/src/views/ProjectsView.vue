<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, Avatar } from 'frappe-ui'
import ProjectPanel from '@/components/ProjectPanel.vue'
import { projectsResource, fetchProjects, updateProject, STAGES, PRIORITY_META } from '@/data/projects'
import { todosResource, fetchTodos, createTodo, updateTodo, deleteTodo } from '@/data/todos'
import { memberById } from '@/data/team'
import { MONTH_NAMES } from '@/utils/date'
import LucideX from '~icons/lucide/x'
import LucideTrash2 from '~icons/lucide/trash-2'

const route = useRoute()
const router = useRouter()

onMounted(() => {
  fetchProjects()
  fetchTodos()
})

// ─── View toggle ───────────────────────────────────────────────────────────
const currentView = computed(() => route.query.view === 'todo' ? 'todo' : 'kanban')
function setView(v) {
  router.push({ name: 'Projects', query: { ...route.query, view: v } })
}

// ─── Kanban ────────────────────────────────────────────────────────────────
const panelState = ref({ open: false, project: null })
const dragTask = ref(null)
const dragOverStage = ref(null)

const byStage = computed(() => {
  const map = {}
  for (const s of STAGES) map[s] = []
  for (const t of projectsResource.data || []) {
    if (map[t.stage]) map[t.stage].push(t)
    else map.Planning.push(t)
  }
  return map
})

const completionByProject = computed(() => {
  const map = {}
  for (const t of todosResource.data || []) {
    if (!t.marketing_project) continue
    if (!map[t.marketing_project]) map[t.marketing_project] = { done: 0, total: 0 }
    map[t.marketing_project].total += 1
    if (t.done) map[t.marketing_project].done += 1
  }
  return map
})

function goToProjectTodo(projectName) {
  router.push({ name: 'Projects', query: { view: 'todo', project: projectName } })
}

function dueLabel(due_date) {
  if (!due_date) return ''
  const [y, m, d] = due_date.split('-').map(Number)
  return `${MONTH_NAMES[m - 1].slice(0, 3)} ${d}`
}
const isOverdue = (t) => t.due_date && t.stage !== 'Done' && new Date(t.due_date) < new Date(new Date().toDateString())

function openProject(project) { panelState.value = { open: true, project } }
function openNewProject() { panelState.value = { open: true, project: null } }
function onClose() { panelState.value = { open: false, project: null } }

function onDragStart(task) { dragTask.value = task }
function onDropOnStage(stage) {
  dragOverStage.value = null
  const task = dragTask.value
  dragTask.value = null
  if (!task || task.stage === stage) return
  task.stage = stage
  updateProject(task.name, { stage })
}

// ─── Todo ──────────────────────────────────────────────────────────────────
const newTitle = ref('')
const taskInputEl = ref(null)
function focusTaskInput() {
  taskInputEl.value?.focus()
  taskInputEl.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
const selectedProject = ref(route.query.project || '')
watch(() => route.query.project, (val) => { selectedProject.value = val || '' })

const adding = ref(false)
async function addTodo() {
  if (!newTitle.value.trim() || adding.value) return
  adding.value = true
  try {
    await createTodo({ title: newTitle.value.trim(), marketing_project: selectedProject.value || null })
    newTitle.value = ''
  } finally {
    adding.value = false
  }
}

function toggleDone(todo) {
  todo.done = todo.done ? 0 : 1
  updateTodo(todo.name, { done: todo.done })
}
function removeTodo(todo) {
  todosResource.data = (todosResource.data || []).filter((t) => t.name !== todo.name)
  deleteTodo(todo.name)
}

const projectFilter = computed(() => route.query.project || '')
const filteredProject = computed(() => (projectsResource.data || []).find((p) => p.name === projectFilter.value))
function clearProjectFilter() {
  router.push({ name: 'Projects', query: { view: 'todo' } })
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
function goToProjectFilter(projectName) {
  router.push({ name: 'Projects', query: { view: 'todo', project: projectName } })
}
</script>

<template>
  <header class="flex items-center gap-3.5 border-b border-gray-100 bg-white px-6 pb-3.5 pt-4">
    <!-- LEFT: title + subtitle -->
    <div class="flex flex-col gap-0.5">
      <h1 class="m-0 text-[17px] font-semibold">Projects</h1>
      <div class="flex items-center gap-2">
        <span class="text-[12px] text-ink-gray-6">
          <template v-if="currentView === 'kanban'">{{ projectsResource.data?.length || 0 }} projects</template>
          <template v-else>{{ pendingTodos.length }} open · {{ doneTodos.length }} done</template>
        </span>
        <button
          v-if="currentView === 'todo' && filteredProject"
          class="flex items-center gap-1 rounded-full bg-gray-100 px-2 py-0.5 text-[11px] font-medium text-gray-600 hover:bg-gray-200"
          @click="clearProjectFilter"
        >
          {{ filteredProject.title }}
          <LucideX class="h-2.5 w-2.5" />
        </button>
      </div>
    </div>

    <!-- RIGHT: toggle + fixed-width button side by side — button is min-w of
         the longer label ("New project") so the toggle never shifts -->
    <div class="ml-auto flex items-center gap-3">
      <div class="flex items-center rounded-lg bg-gray-100 p-0.5">
        <button
          class="rounded-md px-3 py-1 text-[12px] font-semibold transition-colors"
          :class="currentView === 'kanban' ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500'"
          @click="setView('kanban')"
        >Kanban</button>
        <button
          class="rounded-md px-3 py-1 text-[12px] font-semibold transition-colors"
          :class="currentView === 'todo' ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500'"
          @click="setView('todo')"
        >Todo</button>
      </div>
      <Button variant="solid" class="min-w-[120px] justify-center"
        @click="currentView === 'kanban' ? openNewProject() : focusTaskInput()">
        <template #prefix><LucidePlus class="h-3.5 w-3.5" /></template>
        {{ currentView === 'kanban' ? 'New project' : 'New task' }}
      </Button>
    </div>
  </header>

  <!-- KANBAN VIEW -->
  <div v-if="currentView === 'kanban'" class="flex-1 overflow-x-auto p-6">
    <div class="grid h-full grid-cols-4 gap-4" style="min-width: 900px">
      <div
        v-for="stage in STAGES"
        :key="stage"
        class="flex flex-col rounded-xl bg-gray-50 p-3"
        :class="dragOverStage === stage ? 'ring-2 ring-gray-300' : ''"
        @dragover.prevent="dragOverStage = stage"
        @dragleave.prevent="dragOverStage = null"
        @drop="onDropOnStage(stage)"
      >
        <div class="mb-2.5 flex items-center gap-2 px-1">
          <span class="text-[12.5px] font-semibold text-gray-700">{{ stage }}</span>
          <span class="rounded-full bg-gray-200 px-1.5 text-[10.5px] font-semibold text-gray-500">{{ byStage[stage].length }}</span>
        </div>
        <div class="flex flex-1 flex-col gap-2 overflow-y-auto">
          <div
            v-for="project in byStage[stage]"
            :key="project.name"
            draggable="true"
            class="cursor-pointer rounded-lg border border-gray-100 bg-white p-3 shadow-sm hover:border-gray-200"
            @dragstart="onDragStart(project)"
            @click="openProject(project)"
          >
            <div class="mb-1.5 flex items-center gap-1.5">
              <span
                class="rounded-full px-2 py-0.5 text-[10px] font-semibold"
                :style="{ color: PRIORITY_META[project.priority]?.c, background: PRIORITY_META[project.priority]?.bg }"
                >{{ project.priority }}</span
              >
              <span v-if="isOverdue(project)" class="rounded-full bg-red-100 px-2 py-0.5 text-[10px] font-semibold text-red-600">Overdue</span>
              <button
                v-if="completionByProject[project.name]?.total"
                class="ml-auto rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-semibold text-gray-600 hover:bg-gray-200"
                @click.stop="goToProjectTodo(project.name)"
              >
                {{ completionByProject[project.name].done }}/{{ completionByProject[project.name].total }}
              </button>
              <button
                v-else
                class="ml-auto flex items-center gap-0.5 rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-medium text-ink-gray-6 hover:bg-gray-200"
                @click.stop="goToProjectTodo(project.name)"
              ><LucidePlus class="h-2.5 w-2.5" /> tasks</button>
            </div>
            <div class="mb-2 text-[13px] font-semibold leading-snug text-gray-900">{{ project.title }}</div>
            <div class="flex items-center gap-1.5">
              <Avatar :label="memberById(project.project_owner).name" :image="memberById(project.project_owner).image" size="sm" />
              <span class="truncate text-[11px] text-gray-500">{{ memberById(project.project_owner).name }}</span>
              <span v-if="project.due_date" class="ml-auto text-[10.5px] text-ink-gray-6">{{ dueLabel(project.due_date) }}</span>
            </div>
          </div>
          <div v-if="!byStage[stage].length" class="py-4 text-center text-[11.5px] text-ink-gray-6">
            Nothing here
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- TODO VIEW -->
  <div v-else class="flex-1 overflow-y-auto p-6">
    <div class="mx-auto flex max-w-[640px] flex-col gap-4">
      <div class="flex items-center gap-2 rounded-xl border border-gray-100 bg-white p-2 shadow-sm">
        <input
          ref="taskInputEl"
          v-model="newTitle"
          placeholder="Add a task and press Enter…"
          class="flex-1 border-none px-2 text-[13px] outline-none"
          @keydown.enter="addTodo"
        />
        <Popover class="relative shrink-0">
          <PopoverButton as="div">
            <div class="flex h-10 w-[190px] cursor-pointer items-center gap-1.5 rounded-md border border-gray-200 bg-white px-2.5 text-[13px] text-gray-700">
              <span class="flex-1 truncate" :class="selectedProject ? 'text-gray-800' : 'text-gray-400'">
                {{ selectedProject ? projectTitle(selectedProject) : 'No project' }}
              </span>
              <LucideChevronsUpDown class="h-3.5 w-3.5 shrink-0 text-gray-400" />
            </div>
          </PopoverButton>
          <PopoverPanel v-slot="{ close }" class="absolute left-0 top-full z-20 mt-1.5 max-h-52 w-[190px] overflow-y-auto rounded-lg border border-gray-100 bg-white py-1 shadow-lg">
            <button class="flex w-full items-center px-3 py-1.5 text-left text-[12.5px] hover:bg-gray-50" :class="!selectedProject ? 'font-semibold text-gray-900' : 'text-gray-500'" @click="() => { selectedProject = ''; close() }">No project</button>
            <button v-for="p in projectsResource.data || []" :key="p.name"
              class="flex w-full items-center gap-2 px-3 py-1.5 text-left text-[12.5px] hover:bg-gray-50"
              :class="selectedProject === p.name ? 'font-semibold text-gray-900' : 'text-gray-600'"
              @click="() => { selectedProject = p.name; close() }"
            >{{ p.title }}</button>
          </PopoverPanel>
        </Popover>
        <Button size="sm" variant="solid" :loading="adding" :disabled="!newTitle.trim()" @click="addTodo">Add</Button>
      </div>

      <div class="flex flex-col gap-1.5">
        <div
          v-for="todo in pendingTodos"
          :key="todo.name"
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
            @click="goToProjectFilter(todo.marketing_project)"
          >{{ projectTitle(todo.marketing_project) }}</button>
          <span v-if="todo.assigned_to" class="shrink-0 text-[10.5px] text-ink-gray-6">{{ memberById(todo.assigned_to).name }}</span>
          <LucideTrash2 class="h-3.5 w-3.5 shrink-0 cursor-pointer text-gray-300 opacity-0 group-hover:opacity-100 hover:text-red-500" @click="removeTodo(todo)" />
        </div>
        <div v-if="!pendingTodos.length" class="py-5 text-center text-[12px] text-ink-gray-6">
          No open tasks{{ filteredProject ? ` for "${filteredProject.title}"` : '' }}.
        </div>
      </div>

      <div v-if="doneTodos.length" class="flex flex-col gap-1.5">
        <span class="px-1 text-[11px] font-medium uppercase tracking-wide text-ink-gray-6">Done · {{ doneTodos.length }}</span>
        <div
          v-for="todo in doneTodos"
          :key="todo.name"
          class="group flex items-center gap-2.5 rounded-lg border border-gray-100 bg-surface-gray-1 px-3 py-2.5"
        >
          <button
            class="flex h-4.5 w-4.5 shrink-0 items-center justify-center rounded-full bg-gray-800 text-white"
            @click="toggleDone(todo)"
          >
            <svg viewBox="0 0 16 16" class="h-2.5 w-2.5" fill="none"><path d="M3 8.5L6 11.5L13 4.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" /></svg>
          </button>
          <span class="flex-1 text-[13px] text-gray-400 line-through">{{ todo.title }}</span>
          <button
            v-if="todo.marketing_project"
            class="shrink-0 rounded-full bg-gray-100 px-2 py-0.5 text-[10.5px] font-medium text-gray-400 hover:bg-gray-200"
            @click="goToProjectFilter(todo.marketing_project)"
          >{{ projectTitle(todo.marketing_project) }}</button>
          <LucideTrash2 class="h-3.5 w-3.5 shrink-0 cursor-pointer text-gray-300 opacity-0 group-hover:opacity-100 hover:text-red-500" @click="removeTodo(todo)" />
        </div>
      </div>
    </div>
  </div>

  <ProjectPanel v-if="panelState.open" :project="panelState.project" @close="onClose" />
</template>
