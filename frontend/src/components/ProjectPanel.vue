<script setup>
import { reactive, ref, computed, onMounted } from 'vue'
import { Button, TextInput, Textarea, FormControl } from 'frappe-ui'
import LucideX from '~icons/lucide/x'
import LucideTrash2 from '~icons/lucide/trash-2'
import { STAGES, createProject, updateProject, deleteProject } from '@/data/projects'
import { todosResource, fetchTodos, createTodo, updateTodo, deleteTodo } from '@/data/todos'
import { useTeam } from '@/data/team'

const props = defineProps({
  project: { type: Object, default: null },
})
const emit = defineEmits(['close', 'saved'])

const team = useTeam()

onMounted(() => {
  if (props.project) fetchTodos()
})

const projectTasks = computed(() =>
  (todosResource.data || []).filter((t) => t.marketing_project === props.project?.name)
)
const newTaskTitle = ref('')
const addingTask = ref(false)
async function addTask() {
  if (!newTaskTitle.value.trim() || addingTask.value || !props.project) return
  addingTask.value = true
  try {
    await createTodo({ title: newTaskTitle.value.trim(), marketing_project: props.project.name })
    newTaskTitle.value = ''
  } finally {
    addingTask.value = false
  }
}
function toggleTask(task) {
  task.done = task.done ? 0 : 1 // optimistic
  updateTodo(task.name, { done: task.done })
}
function removeTask(task) {
  todosResource.data = (todosResource.data || []).filter((t) => t.name !== task.name)
  deleteTodo(task.name)
}

function blankForm() {
  return {
    title: '',
    stage: 'Planning',
    priority: 'Medium',
    project_owner: window.user || '',
    due_date: '',
    description: '',
  }
}

function hydrate(project) {
  return {
    title: project.title || '',
    stage: project.stage || 'Planning',
    priority: project.priority || 'Medium',
    project_owner: project.project_owner || '',
    due_date: project.due_date || '',
    description: project.description || '',
  }
}

const form = reactive(props.project ? hydrate(props.project) : blankForm())
const saving = ref(false)
const deleting = ref(false)
const errorMessage = ref('')

const canSave = computed(() => !!form.title)

async function onSave() {
  if (!canSave.value || saving.value) return
  saving.value = true
  errorMessage.value = ''
  try {
    if (props.project?.name) {
      await updateProject(props.project.name, form)
    } else {
      await createProject(form)
    }
    emit('saved')
    emit('close')
  } catch (e) {
    errorMessage.value = e?.messages?.[0] || 'Could not save this project.'
  } finally {
    saving.value = false
  }
}

async function onDelete() {
  if (!props.project?.name || deleting.value) return
  deleting.value = true
  try {
    await deleteProject(props.project.name)
    emit('saved')
    emit('close')
  } catch (e) {
    errorMessage.value = e?.messages?.[0] || 'Could not delete this project.'
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div class="fixed inset-0 z-40" data-testid="project-panel">
    <div class="fixed inset-0 bg-black/30" @click="emit('close')" />
    <div class="absolute right-0 top-0 flex h-full w-[440px] flex-col bg-white shadow-2xl">
      <div class="flex items-center gap-3 border-b border-gray-100 px-5 py-4">
        <h2 class="m-0 text-[16.5px] font-semibold">{{ project ? 'Edit project' : 'New project' }}</h2>
        <LucideTrash2
          v-if="project"
          class="ml-auto h-4 w-4 cursor-pointer text-gray-400 hover:text-red-500"
          @click="onDelete"
        />
        <LucideX data-testid="close-project" class="h-4 w-4 cursor-pointer text-gray-400 hover:text-gray-600" :class="project ? '' : 'ml-auto'" @click="emit('close')" />
      </div>

      <div class="flex-1 overflow-y-auto px-5 py-4">
        <div class="flex flex-col gap-4">
          <div class="flex flex-col gap-1.5">
            <label class="text-[12px] font-medium text-gray-700">Title</label>
            <TextInput v-model="form.title" data-testid="project-title" placeholder="e.g. Q3 product launch campaign" />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div class="flex flex-col gap-1.5">
              <label class="text-[12px] font-medium text-gray-700">Stage</label>
              <FormControl type="select" v-model="form.stage" :options="STAGES" />
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="text-[12px] font-medium text-gray-700">Priority</label>
              <FormControl type="select" v-model="form.priority" :options="['High', 'Medium', 'Low']" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div class="flex flex-col gap-1.5">
              <label class="text-[12px] font-medium text-gray-700">Owner</label>
              <FormControl
                type="select"
                v-model="form.project_owner"
                :options="[{ label: 'Unassigned', value: '' }, ...(team.data || []).map((m) => ({ label: m.name, value: m.id }))]"
              />
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="text-[12px] font-medium text-gray-700">Due date</label>
              <input type="date" v-model="form.due_date" class="form-input w-full" />
            </div>
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-[12px] font-medium text-gray-700">Description</label>
            <Textarea v-model="form.description" :rows="4" placeholder="Notes, links, context…" />
          </div>

          <div v-if="project" class="flex flex-col gap-1.5 border-t border-gray-100 pt-4">
            <label class="text-[12px] font-medium text-gray-700">
              Tasks<template v-if="projectTasks.length"> <span class="text-ink-gray-5">· {{ projectTasks.filter((t) => t.done).length }}/{{ projectTasks.length }} done</span></template>
            </label>
            <div class="flex items-center gap-2">
              <TextInput
                v-model="newTaskTitle"
                placeholder="Add a task…"
                class="flex-1"
                @keydown.enter="addTask"
              />
            </div>
            <div class="flex flex-col gap-1">
              <div
                v-for="t in projectTasks"
                :key="t.name"
                class="group flex items-center gap-2 rounded-md border border-gray-100 px-2.5 py-1.5"
              >
                <button
                  class="flex h-3.5 w-3.5 shrink-0 items-center justify-center rounded-full border-[1.5px]"
                  :class="t.done ? 'border-gray-800 bg-gray-800 text-white' : 'border-gray-300'"
                  @click="toggleTask(t)"
                >
                  <svg v-if="t.done" viewBox="0 0 16 16" class="h-2 w-2" fill="none"><path d="M3 8.5L6 11.5L13 4.5" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" /></svg>
                </button>
                <span class="flex-1 text-[12.5px]" :class="t.done ? 'text-gray-400 line-through' : 'text-gray-800'">{{ t.title }}</span>
                <LucideTrash2 class="h-3 w-3 shrink-0 cursor-pointer text-gray-300 opacity-0 group-hover:opacity-100 hover:text-red-500" @click="removeTask(t)" />
              </div>
              <p v-if="!projectTasks.length" class="m-0 py-1 text-[11.5px] text-ink-gray-5">No tasks linked yet.</p>
            </div>
          </div>
        </div>
      </div>

      <div class="flex items-center gap-2.5 border-t border-gray-100 px-5 py-3.5">
        <span class="text-[11.5px]" :class="errorMessage ? 'font-semibold text-red-600' : 'text-ink-gray-5'">
          {{ errorMessage || (canSave ? 'Ready to save' : 'Title is required') }}
        </span>
        <div class="ml-auto flex gap-2">
          <Button variant="outline" @click="emit('close')">Close</Button>
          <Button variant="solid" :loading="saving" :disabled="!canSave" @click="onSave">{{ project ? 'Save changes' : 'Create project' }}</Button>
        </div>
      </div>
    </div>
  </div>
</template>
