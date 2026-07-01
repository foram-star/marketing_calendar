<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { Button, TextInput, Textarea, FormControl, DateTimePicker, Dialog, createResource, useFileUpload, call } from 'frappe-ui'
import { PLATFORM_LIST, STATUSES } from '@/data/platforms'
import { useTeam, memberById } from '@/data/team'
import { MONTH_NAMES } from '@/utils/date'
import { createPost, updatePost, deletePost } from '@/data/posts'
import { useWorkflow } from '@/data/workflow'
import PlatformBadge from './PlatformBadge.vue'
import PostPreview from './PostPreview.vue'
import LucideEye from '~icons/lucide/eye'
import LucideImage from '~icons/lucide/image'

const props = defineProps({
  date: { type: String, default: null }, // 'YYYY-MM-DD' to prefill
  post: { type: Object, default: null }, // existing full doc (with child tables) to edit
})
const emit = defineEmits(['close', 'saved', 'workflow-changed'])

const team = useTeam()

const projectsResource = createResource({
  url: 'frappe.client.get_list',
  auto: true,
  params: { doctype: 'Marketing Project', fields: ['name', 'title'], limit_page_length: 100 },
})
const blogPostsResource = createResource({
  url: 'frappe.client.get_list',
  auto: true,
  params: { doctype: 'Blog Post', fields: ['name', 'title', 'published'], limit_page_length: 100, order_by: 'modified desc' },
})

function blankPlatformData() {
  return {
    selected: false,
    caption: '',
    link_url: '',
    showLink: false,
    x_reply_settings: 'Everyone',
    x_sensitive_media: false,
    instagram_first_comment: '',
    instagram_collaborators: '',
    linkedin_mentions: [], // [{ name, urn }] — serialized to JSON on save
    blog_post: '',
  }
}

function blankForm() {
  const today = new Date()
  const platforms = {}
  for (const p of PLATFORM_LIST) platforms[p.id] = blankPlatformData()
  return {
    platforms,
    assets: [],
    title: '',
    tags: ['marketing'],
    tagDraft: '',
    marketing_project: '',
    assigned_to: window.user || '',
    reviewer: '',
    scheduledOn: `${props.date || today.toISOString().slice(0, 10)} 09:00:00`,
  }
}

function hydrateFromPost(post) {
  const form = blankForm()
  form.title = post.title || ''
  form.tags = (post.tags || []).map((t) => t.tag)
  form.marketing_project = post.marketing_project || ''
  form.assigned_to = post.assigned_to || ''
  form.reviewer = post.reviewer || ''
  if (post.scheduled_on) {
    form.scheduledOn = post.scheduled_on
  }
  for (const row of post.platforms || []) {
    const key = row.platform?.toLowerCase()
    if (!(key in form.platforms)) continue
    form.platforms[key] = {
      selected: true,
      caption: row.caption || '',
      link_url: row.link_url || '',
      showLink: !!row.link_url,
      x_reply_settings: row.x_reply_settings || 'Everyone',
      x_sensitive_media: !!row.x_sensitive_media,
      instagram_first_comment: row.instagram_first_comment || '',
      instagram_collaborators: row.instagram_collaborators || '',
      linkedin_mentions: row.linkedin_mentions ? JSON.parse(row.linkedin_mentions) : [],
      blog_post: row.blog_post || '',
    }
  }
  form.assets = (post.assets || []).map((a) => ({
    id: a.name || `a${Math.random().toString(36).slice(2)}`,
    file_url: a.file,
    thumbnail_url: a.thumbnail || '',
    alt_text: a.alt_text || '',
    file_type: a.file_type || 'Image',
    width: a.width || 0,
    height: a.height || 0,
    size: a.file_size || 0,
    uploading: false,
  }))
  return form
}

const form = reactive(props.post ? hydrateFromPost(props.post) : blankForm())
const dragOver = ref(false)
const dragIdx = ref(null)
const saving = ref(false)
const errorMessage = ref('')

// Local snapshot of the persisted post's workflow status — kept separate from
// `form` since workflow actions operate on the saved doc, not in-progress edits.
const livePost = reactive({ name: props.post?.name || null, status: props.post?.status || 'Draft' })
const workflow = useWorkflow('Marketing Post', () => livePost.name)
const actionLoading = ref('')

// Real per-platform outcomes (status/error_message/attempt_count) — kept
// separate from `form` for the same reason `livePost` is: this reflects
// what actually happened on the saved doc, not in-progress edits. Refreshed
// from whatever the last workflow/publish call returned, since those always
// hand back the full post including its platform rows.
const platformRows = ref(props.post?.platforms || [])
const failedPlatformRows = computed(() => platformRows.value.filter((r) => r.status === 'Failed' && r.error_message))
// A row stuck on "Publishing" past this panel's own load means something
// else (the scheduler, or another tab) is mid-attempt right now — the exact
// "double scheduling" race `notify_duplicate_publish_blocked` exists for.
const publishingPlatformRows = computed(() => platformRows.value.filter((r) => r.status === 'Publishing'))
// Real Frappe Comments on the post — same timeline Desk shows, just rendered
// in our own Approval step so a reviewer can leave context without leaving
// the SPA. `frappe.desk.form.utils.add_comment` is the exact endpoint
// Desk's own comment box calls.
const commentsResource = createResource({
  url: 'frappe.client.get_list',
  auto: false,
  params: {
    doctype: 'Comment',
    filters: { reference_doctype: 'Marketing Post', reference_name: livePost.name, comment_type: 'Comment' },
    fields: ['name', 'content', 'comment_by', 'creation'],
    order_by: 'creation desc',
  },
})
const newComment = ref('')
const commentSubmitting = ref(false)
async function submitComment() {
  if (!newComment.value.trim() || !livePost.name || commentSubmitting.value) return
  commentSubmitting.value = true
  try {
    await call('frappe.desk.form.utils.add_comment', {
      reference_doctype: 'Marketing Post',
      reference_name: livePost.name,
      content: newComment.value.trim(),
      comment_email: window.user,
      comment_by: memberById(window.user).name,
    })
    newComment.value = ''
    commentsResource.fetch()
  } catch (e) {
    errorMessage.value = e?.messages?.[0] || 'Could not add comment.'
  } finally {
    commentSubmitting.value = false
  }
}

onMounted(() => {
  if (livePost.name) {
    workflow.refresh()
    commentsResource.fetch()
  }
})

const statusMeta = computed(() => STATUSES[livePost.status] || STATUSES.Draft)
// Approved -> publish immediately, skipping the wait. Scheduled/Failed -> the
// normal due-time/retry path. Either way it's the same backend call —
// `publish_now` walks an Approved post through Schedule first.
const canPublishNow = computed(() => ['Approved', 'Scheduled', 'Failed'].includes(livePost.status))
// "Schedule"/"Retry" are both "wait for the scheduler" — the passive half of
// the exact same timing choice "Publish now" is the immediate half of. Shown
// side by side as one decision instead of scattered buttons that all look
// equally weighted, so it's clear they're alternatives, not separate steps.
const TIMING_ACTIONS = new Set(['Schedule', 'Retry'])
const timingTransitions = computed(() => workflow.state.transitions.filter((t) => TIMING_ACTIONS.has(t.action)))
const otherTransitions = computed(() => workflow.state.transitions.filter((t) => !TIMING_ACTIONS.has(t.action)))
const scheduledOnLabel = computed(() => {
  if (!form.scheduledOn) return ''
  const [datePart, timePart] = form.scheduledOn.split(' ')
  const [y, m, d] = datePart.split('-').map(Number)
  return `${MONTH_NAMES[m - 1]} ${d}, ${(timePart || '00:00:00').slice(0, 5)}`
})

// Once a post has been through approval, silently letting "Save changes"
// rewrite its content with no new review is exactly the gap the approval
// step exists to close. So past that point the form opens read-only — "Edit
// post" is a deliberate, visible choice to go change something, not a
// default available everywhere.
const editMode = ref(false)
const isLocked = computed(() =>
  ['Approved', 'Scheduled', 'Published', 'Partially Published', 'Failed'].includes(livePost.status)
)
const isReadOnly = computed(() => isLocked.value && !editMode.value)

async function runWorkflowAction(action) {
  if (!livePost.name || actionLoading.value) return
  actionLoading.value = action
  errorMessage.value = ''
  try {
    const updated = await workflow.applyAction(action)
    if (updated?.status) livePost.status = updated.status
    if (updated?.platforms) platformRows.value = updated.platforms
    emit('workflow-changed')
  } catch (e) {
    errorMessage.value = e?.messages?.[0] || `Could not ${action.toLowerCase()}.`
  } finally {
    actionLoading.value = ''
  }
}

async function runPublishNow() {
  if (!livePost.name || actionLoading.value) return
  actionLoading.value = 'Publish now'
  errorMessage.value = ''
  try {
    const updated = await call('marketing_calendar.api.publish_now', { post: livePost.name })
    if (updated?.status) livePost.status = updated.status
    if (updated?.platforms) platformRows.value = updated.platforms
    emit('workflow-changed')
  } catch (e) {
    errorMessage.value = e?.messages?.[0] || 'Could not publish this post.'
  } finally {
    actionLoading.value = ''
  }
}

const selectedPlatforms = computed(() => PLATFORM_LIST.filter((p) => form.platforms[p.id].selected))
const showUpload = computed(() => selectedPlatforms.value.length > 0)

// Blog's content lives entirely in the Blog Post you picked, not in a
// caption — there's nothing useful to mock up for it.
const previewOpen = ref(false)
const previewPlatforms = computed(() =>
  selectedPlatforms.value
    .filter((p) => p.id !== 'blog')
    .map((p) => ({ id: p.id, name: p.name, caption: form.platforms[p.id].caption, link_url: form.platforms[p.id].link_url })),
)
const accountName = computed(() => memberById(form.assigned_to).name)
const canSave = computed(() => selectedPlatforms.value.length > 0)
function blogPostTitle(name) {
  return (blogPostsResource.data || []).find((b) => b.name === name)?.title || ''
}

// A real wizard, not a scroll-jump index — each step below is v-if gated so
// only the current one renders. Approval is its own final step: a read-only
// recap of everything entered so far, plus whatever's actually next
// (workflow transitions, or the timing/publish choice) — it only makes sense
// once the rest of the form is filled in.
const STEPS = [
  { key: 'platform', label: 'Platform' },
  { key: 'creative', label: 'Creative' },
  { key: 'content', label: 'Content' },
  { key: 'schedule', label: 'Schedule' },
  { key: 'approval', label: 'Approval' },
]
const currentStepKey = ref('platform')
const currentStepIndex = computed(() => STEPS.findIndex((s) => s.key === currentStepKey.value))
const scrollEl = ref(null)
function goToStep(step) {
  currentStepKey.value = step.key
  if (scrollEl.value) scrollEl.value.scrollTop = 0
}
function nextStep() {
  if (currentStepIndex.value < STEPS.length - 1) goToStep(STEPS[currentStepIndex.value + 1])
}
function prevStep() {
  if (currentStepIndex.value > 0) goToStep(STEPS[currentStepIndex.value - 1])
}

function togglePlatform(id) {
  form.platforms[id].selected = !form.platforms[id].selected
}

function counterFor(p) {
  if (!p.limit) return null
  const used = form.platforms[p.id].caption.length
  return { label: `${used}/${p.limit}`, over: used > p.limit }
}

// Instagram needs no lookup at all — a plain @username in the caption is
// already a real, working tag once Instagram renders it. This is just a
// "yes, that'll work" confirmation as you type.
const instagramMentions = computed(() => [...(form.platforms.instagram.caption || '').matchAll(/@(\w+)/g)].map((m) => m[1]))

function onTagKey(e) {
  if (e.key === 'Enter' || e.key === ',') {
    e.preventDefault()
    const v = form.tagDraft.trim().replace(/^#/, '')
    if (v && !form.tags.includes(v)) form.tags.push(v)
    form.tagDraft = ''
  } else if (e.key === 'Backspace' && !form.tagDraft) {
    form.tags.pop()
  }
}
function removeTag(t) {
  form.tags = form.tags.filter((x) => x !== t)
}

function readImageDims(src) {
  return new Promise((resolve) => {
    const img = new Image()
    img.onload = () => resolve({ width: img.naturalWidth, height: img.naturalHeight })
    img.onerror = () => resolve({ width: 0, height: 0 })
    img.src = src
  })
}

async function handleFiles(fileList) {
  const files = [...fileList].filter((f) => /image|video/.test(f.type)).slice(0, 4 - form.assets.length)
  for (const file of files) {
    const isImage = /image/.test(file.type)
    const localPreview = URL.createObjectURL(file)
    const dims = isImage ? await readImageDims(localPreview) : { width: 1280, height: 720 }
    const asset = reactive({
      id: `a${Math.random().toString(36).slice(2)}`,
      file_url: localPreview,
      alt_text: '',
      file_type: isImage ? 'Image' : 'Video',
      width: dims.width,
      height: dims.height,
      size: file.size,
      uploading: true,
    })
    form.assets.push(asset)
    const { upload } = useFileUpload()
    try {
      const result = await upload(file, { private: 0 })
      asset.file_url = result.file_url
    } catch (e) {
      errorMessage.value = `Failed to upload ${file.name}.`
      form.assets = form.assets.filter((a) => a.id !== asset.id)
    } finally {
      asset.uploading = false
    }
  }
}

function onFileInputChange(e) {
  handleFiles(e.target.files)
  e.target.value = ''
}
async function onThumbnailChange(asset, e) {
  const file = e.target.files[0]
  e.target.value = ''
  if (!file) return
  asset.thumbnail_url = URL.createObjectURL(file)
  const { upload } = useFileUpload()
  try {
    const result = await upload(file, { private: 0 })
    asset.thumbnail_url = result.file_url
  } catch {
    errorMessage.value = `Failed to upload thumbnail for ${file.name}.`
    asset.thumbnail_url = ''
  }
}
function onDrop(e) {
  e.preventDefault()
  dragOver.value = false
  handleFiles(e.dataTransfer.files)
}
function removeAsset(id) {
  form.assets = form.assets.filter((a) => a.id !== id)
}
function onAssetDragStart(idx) {
  dragIdx.value = idx
}
function onAssetDrop(idx) {
  const from = dragIdx.value
  if (from == null || from === idx) return
  const arr = form.assets.slice()
  const [moved] = arr.splice(from, 1)
  arr.splice(idx, 0, moved)
  form.assets = arr
  dragIdx.value = null
}

function previewCards(asset) {
  const ar = asset.width / asset.height || 1
  return selectedPlatforms.value.map((p) => {
    const w = 120
    const h = Math.round(w / p.ratio)
    let warn = ''
    if (ar / p.ratio < 0.6) warn = `Tall image — top & bottom may be cropped on ${p.name}.`
    else if (ar / p.ratio > 1.75) warn = `Wide image — the sides may be cropped on ${p.name}.`
    return { platform: p.name, color: p.color, w, h, ratioLabel: p.ratioLabel, warn }
  })
}
function firstWarning(asset) {
  return previewCards(asset).find((c) => c.warn)?.warn || ''
}

async function onSave() {
  if (!canSave.value || saving.value) return
  saving.value = true
  errorMessage.value = ''
  try {
    const payload = {
      title: form.title || (selectedPlatforms.value[0] ? form.platforms[selectedPlatforms.value[0].id].caption.slice(0, 32) : 'Untitled post'),
      scheduled_on: form.scheduledOn,
      assigned_to: form.assigned_to || null,
      reviewer: form.reviewer || null,
      marketing_project: form.marketing_project || null,
      tags: form.tags.map((tag) => ({ tag })),
      platforms: selectedPlatforms.value.map((p) => {
        const data = form.platforms[p.id]
        return {
          platform: p.name,
          caption: p.id === 'blog' ? '' : data.caption,
          link_url: p.hasLink && data.showLink ? data.link_url : '',
          x_reply_settings: p.id === 'x' ? data.x_reply_settings : null,
          x_sensitive_media: p.id === 'x' ? data.x_sensitive_media : 0,
          instagram_first_comment: p.id === 'instagram' ? data.instagram_first_comment : '',
          instagram_collaborators: p.id === 'instagram' ? data.instagram_collaborators : '',
          linkedin_mentions: p.id === 'linkedin' && data.linkedin_mentions.length ? JSON.stringify(data.linkedin_mentions) : '',
          blog_post: p.id === 'blog' ? data.blog_post || null : null,
        }
      }),
      assets: form.assets
        .filter((a) => !a.uploading)
        .map((a) => ({
          file: a.file_url,
          thumbnail: a.thumbnail_url || null,
          alt_text: a.alt_text,
          file_type: a.file_type,
          width: a.width,
          height: a.height,
          file_size: a.size,
        })),
    }
    if (livePost.name) {
      await updatePost(livePost.name, payload)
    } else {
      const created = await createPost(payload)
      if (created?.name) {
        livePost.name = created.name
        livePost.status = created.status || 'Draft'
        await workflow.refresh()
      }
    }
    emit('saved')
  } catch (e) {
    errorMessage.value = e?.messages?.[0] || 'Could not save this post.'
  } finally {
    saving.value = false
  }
}

// Two-step confirm in place, instead of a second (nested-Dialog) popup —
// click once to arm it, click again within a few seconds to actually
// delete; arming reverts on its own otherwise so a stray click can't delete
// anything by itself.
const deleteArmed = ref(false)
const deleting = ref(false)
let deleteArmTimer = null
function onDeleteClick() {
  if (!deleteArmed.value) {
    deleteArmed.value = true
    deleteArmTimer = setTimeout(() => (deleteArmed.value = false), 4000)
    return
  }
  clearTimeout(deleteArmTimer)
  onDelete()
}
async function onDelete() {
  if (!livePost.name || deleting.value) return
  deleting.value = true
  errorMessage.value = ''
  try {
    await deletePost(livePost.name)
    emit('saved')
    emit('close')
  } catch (e) {
    errorMessage.value = e?.messages?.[0] || 'Could not delete this post.'
    deleteArmed.value = false
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <Dialog :model-value="true" :options="{ size: '3xl' }" @close="emit('close')">
    <template #body>
      <div class="flex max-h-[88vh] flex-col" data-testid="compose-panel">
        <div class="flex items-center gap-3 border-b border-gray-100 px-6 py-4">
          <h2 class="m-0 text-[16.5px] font-semibold">{{ livePost.name ? 'Edit post' : 'Schedule a post' }}</h2>
          <span
            v-if="livePost.name"
            class="rounded-full px-2.5 py-1 text-[11px] font-semibold"
            :style="{ color: statusMeta.c, background: statusMeta.bg }"
            >{{ livePost.status }}</span
          >
          <Button class="ml-auto" size="sm" variant="outline" :disabled="!previewPlatforms.length" @click="previewOpen = true">
            <template #prefix><LucideEye class="h-3.5 w-3.5" /></template>
            Preview
          </Button>
          <LucideX data-testid="close-compose" class="h-4 w-4 cursor-pointer text-gray-400 hover:text-gray-600" @click="emit('close')" />
        </div>

        <!-- FAILURE / IN-PROGRESS BANNERS — visible on every step, not just buried in Approval -->
        <div v-if="failedPlatformRows.length" class="flex flex-col gap-1.5 border-b border-red-100 bg-red-50 px-6 py-2.5">
          <div v-for="row in failedPlatformRows" :key="row.platform" class="flex items-start gap-2 text-[12px] text-red-700">
            <LucideTriangleAlert class="mt-0.5 h-3.5 w-3.5 shrink-0" />
            <span><b>{{ row.platform }}</b> failed to publish: {{ row.error_message }}</span>
          </div>
        </div>
        <div v-if="publishingPlatformRows.length" class="flex flex-col gap-1.5 border-b border-amber-100 bg-amber-50 px-6 py-2.5">
          <div v-for="row in publishingPlatformRows" :key="row.platform" class="flex items-start gap-2 text-[12px] text-amber-700">
            <LucideTriangleAlert class="mt-0.5 h-3.5 w-3.5 shrink-0" />
            <span><b>{{ row.platform }}</b> is already being published right now — wait for it to finish before retrying, to avoid a duplicate post.</span>
          </div>
        </div>

        <!-- STEPPER -->
        <div class="flex items-center gap-1.5 border-b border-gray-100 bg-gray-25 px-6 py-3.5">
          <template v-for="(step, idx) in STEPS" :key="step.key">
            <button class="flex items-center gap-2" @click="goToStep(step)">
              <span
                class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[11px] font-bold"
                :class="currentStepKey === step.key ? 'bg-gray-800 text-white' : 'border border-gray-300 text-gray-400'"
                >{{ idx + 1 }}</span
              >
              <span class="text-[12.5px] font-medium" :class="currentStepKey === step.key ? 'text-gray-900' : 'text-gray-400'">{{ step.label }}</span>
            </button>
            <div v-if="idx < STEPS.length - 1" class="mx-1 h-px w-8 shrink-0 bg-gray-200" />
          </template>
        </div>

        <div ref="scrollEl" class="flex-1 overflow-auto px-6 py-1">
        <!-- STEP 1: PLATFORM -->
        <section v-if="currentStepKey === 'platform'" class="py-4.5" :class="isReadOnly ? 'pointer-events-none opacity-50' : ''">
          <h3 class="m-0 mb-3 text-[14px] font-semibold">Platform</h3>
          <div class="ml-0 grid grid-cols-4 gap-2.5">
            <div
              v-for="p in PLATFORM_LIST"
              :key="p.id"
              :data-testid="`platform-card-${p.id}`"
              class="relative cursor-pointer rounded-xl border-[1.5px] p-3 transition-all"
              :class="form.platforms[p.id].selected ? 'border-gray-800 bg-gray-50' : 'border-gray-200 bg-white'"
              @click="togglePlatform(p.id)"
            >
              <div class="flex items-center gap-2">
                <PlatformBadge :platform="p" variant="dot" />
                <span class="text-[13px] font-semibold">{{ p.name }}</span>
                <LucideCheckCircle2 v-if="form.platforms[p.id].selected" class="ml-auto h-4.5 w-4.5 text-gray-800" />
              </div>
            </div>
          </div>
        </section>

        <!-- STEP 2: CREATIVE -->
        <section v-if="currentStepKey === 'creative'" class="py-4.5" :class="isReadOnly ? 'pointer-events-none opacity-50' : ''">
          <h3 class="m-0 mb-3 text-[14px] font-semibold">Creative</h3>
          <p v-if="!selectedPlatforms.length" class="m-0 ml-0 text-[12.5px] text-gray-400">Select platform(s) first.</p>
          <template v-else>
          <div v-if="showUpload" class="ml-0 mb-3 flex flex-col gap-1.5">
            <div v-for="p in selectedPlatforms" :key="p.id" class="flex items-center gap-2 rounded-lg border border-gray-100 px-2.5 py-2">
              <span class="h-1.5 w-1.5 rounded-sm" :style="{ background: p.color }" />
              <span class="min-w-[64px] text-[11px] font-bold text-gray-700">{{ p.name }}</span>
              <span class="text-[11.5px] text-gray-500">{{ p.guide }}</span>
            </div>
          </div>
          <div class="ml-0">
            <div
              class="flex flex-col items-center gap-2 rounded-xl border-[1.5px] border-dashed p-6 text-center transition-all"
              :class="dragOver ? 'border-gray-800 bg-gray-50' : 'border-gray-300 bg-gray-25'"
              @click="$refs.fileInput.click()"
              @dragover.prevent="dragOver = true"
              @dragleave.prevent="dragOver = false"
              @drop="onDrop"
            >
              <LucideUpload class="h-6 w-6 text-gray-400" />
              <span class="text-[13px] font-semibold text-gray-700">Drag & drop, or click to browse</span>
              <span class="text-[11.5px] text-gray-400">PNG, JPG, MP4 — up to 4 assets for a carousel</span>
              <input ref="fileInput" type="file" accept="image/*,video/*" multiple class="hidden" @change="onFileInputChange" @click.stop />
            </div>

            <div v-if="form.assets.length" class="mt-3 flex flex-col gap-3">
              <div
                v-for="(asset, idx) in form.assets"
                :key="asset.id"
                draggable="true"
                class="rounded-xl border border-gray-100 p-3 shadow-sm"
                @dragstart="onAssetDragStart(idx)"
                @dragover.prevent
                @drop="onAssetDrop(idx)"
              >
                <div class="flex items-start gap-2.5">
                  <LucideGripVertical class="mt-0.5 h-4 w-4 shrink-0 cursor-grab text-gray-300" />
                  <div class="h-13 w-13 shrink-0 overflow-hidden rounded-lg bg-gray-100">
                    <img v-if="asset.file_type === 'Image'" :src="asset.file_url" class="h-full w-full object-cover" />
                    <div v-else class="flex h-full w-full items-center justify-center text-gray-400"><LucidePlay class="h-4 w-4" /></div>
                  </div>
                  <div class="min-w-0 flex-1">
                    <div class="truncate text-[12.5px] font-semibold">
                      {{ asset.uploading ? 'Uploading…' : asset.file_type }}
                    </div>
                    <div class="text-[11px] text-gray-400">{{ asset.width }}×{{ asset.height }}px</div>
                  </div>
                  <button class="flex h-6.5 w-6.5 shrink-0 items-center justify-center rounded-md bg-gray-100 text-gray-400" @click="removeAsset(asset.id)">
                    <LucideX class="h-3.5 w-3.5" />
                  </button>
                </div>
                <div class="ml-7 mt-2.5 flex flex-wrap gap-2.5">
                  <div v-for="card in previewCards(asset)" :key="card.platform" class="flex flex-col gap-1">
                    <div
                      class="overflow-hidden rounded-md border border-gray-100 bg-black"
                      :style="{ width: card.w + 'px', height: card.h + 'px' }"
                    >
                      <img v-if="asset.file_type === 'Image'" :src="asset.file_url" class="h-full w-full object-cover" />
                    </div>
                    <div class="flex items-center gap-1">
                      <span class="h-1.5 w-1.5 rounded-sm" :style="{ background: card.color }" />
                      <span class="text-[10.5px] font-semibold text-gray-600">{{ card.platform }}</span>
                    </div>
                  </div>
                </div>
                <div v-if="firstWarning(asset)" class="ml-7 mt-2.5 flex items-center gap-2 rounded-lg border border-orange-200 bg-orange-50 px-2.5 py-1.5">
                  <LucideTriangleAlert class="h-3.5 w-3.5 text-orange-500" />
                  <span class="text-[11.5px] font-medium text-orange-700">{{ firstWarning(asset) }}</span>
                </div>
                <input
                  v-model="asset.alt_text"
                  placeholder="Alt text for accessibility (optional)"
                  class="ml-7 mt-2.5 w-[calc(100%-1.75rem)] rounded-md border border-gray-200 px-2.5 py-1.5 text-[11.5px] outline-none"
                />
                <div v-if="asset.file_type === 'Video'" class="ml-7 mt-2.5 flex items-center gap-2.5">
                  <div class="h-10 w-10 shrink-0 overflow-hidden rounded-md bg-gray-100">
                    <img v-if="asset.thumbnail_url" :src="asset.thumbnail_url" class="h-full w-full object-cover" />
                    <LucideImage v-else class="h-full w-full p-2 text-gray-300" />
                  </div>
                  <div class="flex flex-col gap-0.5">
                    <button class="self-start text-[11.5px] font-semibold text-gray-500" @click="$refs.thumbInput[idx].click()">
                      {{ asset.thumbnail_url ? 'Replace thumbnail' : '+ Add thumbnail' }}
                    </button>
                    <span class="text-[10.5px] text-gray-400">Custom cover image for this video (optional) — Instagram only for now</span>
                  </div>
                  <input ref="thumbInput" type="file" accept="image/*" class="hidden" @change="onThumbnailChange(asset, $event)" />
                </div>
              </div>
            </div>
          </div>
          </template>
        </section>

        <!-- STEP 3: CONTENT -->
        <section v-if="currentStepKey === 'content'" class="py-4.5" :class="isReadOnly ? 'pointer-events-none opacity-50' : ''">
          <h3 class="m-0 mb-3 text-[14px] font-semibold">Content</h3>
          <div class="ml-0 flex flex-col gap-3.5">
            <div class="flex flex-col gap-1.5">
              <label class="text-[12px] font-medium text-gray-700">Title <span class="text-gray-400">· internal reference</span></label>
              <TextInput v-model="form.title" placeholder="e.g. June product launch teaser" />
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="text-[12px] font-medium text-gray-700">Internal tags <span class="text-gray-400">· for organizing this calendar, not posted anywhere</span></label>
              <div class="flex flex-wrap items-center gap-1.5 rounded-md border border-gray-200 px-2.5 py-2">
                <span
                  v-for="t in form.tags"
                  :key="t"
                  class="inline-flex items-center gap-1 rounded-md bg-gray-100 py-1 pl-2.5 pr-1 text-[11.5px] font-medium text-gray-700"
                >
                  #{{ t }}
                  <button class="text-gray-400" @click="removeTag(t)">×</button>
                </span>
                <input
                  v-model="form.tagDraft"
                  @keydown="onTagKey"
                  placeholder="Type and press Enter…"
                  class="min-w-[130px] flex-1 border-none text-[12.5px] outline-none"
                />
              </div>
            </div>

            <!-- per-platform caption + options -->
            <div v-for="p in selectedPlatforms" :key="p.id" :data-testid="`platform-section-${p.id}`" class="rounded-xl border border-gray-100 p-3.5">
              <div class="mb-2.5 flex items-center gap-2">
                <PlatformBadge :platform="p" variant="dot" />
                <span class="text-[12.5px] font-semibold text-gray-800">{{ p.name }}</span>
                <span
                  v-if="counterFor(p)"
                  class="ml-auto rounded-full px-2 py-0.5 text-[10.5px] font-semibold"
                  :class="counterFor(p).over ? 'bg-red-100 text-red-600' : 'bg-gray-100 text-gray-500'"
                  >{{ counterFor(p).label }}</span
                >
              </div>

              <!-- Blog: schedule an existing Blog Post, never author one here -->
              <div v-if="p.id === 'blog'" class="flex flex-col gap-1">
                <FormControl
                  type="select"
                  data-testid="caption-blog"
                  v-model="form.platforms.blog.blog_post"
                  :options="[{ label: 'Select a blog post…', value: '' }, ...(blogPostsResource.data || []).map((b) => ({ label: b.title + (b.published ? ' (published)' : ' (draft)'), value: b.name }))]"
                />
                <p class="m-0 text-[11px] text-gray-400">
                  Only blog posts already written in the Blog app show up here — this schedules it, it doesn't write it.
                </p>
              </div>

              <Textarea
                v-else
                v-model="form.platforms[p.id].caption"
                :data-testid="`caption-${p.id}`"
                :rows="3"
                placeholder="Write your post copy…"
              />
              <p v-if="p.id === 'instagram' && instagramMentions.length" class="m-0 mt-1 text-[11px] text-gray-400">
                Will tag: <span v-for="(m, i) in instagramMentions" :key="m" class="font-medium text-gray-600">@{{ m }}<template v-if="i < instagramMentions.length - 1">, </template></span>
              </p>

              <!-- X-specific -->
              <div v-if="p.id === 'x'" class="mt-2.5 flex items-center gap-3">
                <div class="flex flex-col gap-1">
                  <label class="text-[11px] font-medium text-gray-600">Who can reply</label>
                  <FormControl type="select" v-model="form.platforms.x.x_reply_settings" :options="['Everyone', 'Following', 'Mentioned']" />
                </div>
                <label class="mt-4 flex items-center gap-1.5 text-[11.5px] text-gray-600">
                  <input type="checkbox" v-model="form.platforms.x.x_sensitive_media" />
                  Mark media as sensitive
                </label>
              </div>

              <!-- Instagram-specific -->
              <div v-if="p.id === 'instagram'" class="mt-2.5 flex flex-col gap-2.5">
                <div class="flex flex-col gap-1">
                  <label class="text-[11px] font-medium text-gray-600">First comment <span class="text-gray-400">(hide hashtags here instead)</span></label>
                  <TextInput v-model="form.platforms.instagram.instagram_first_comment" placeholder="#marketing #launch…" />
                </div>
                <div class="flex flex-col gap-1">
                  <label class="text-[11px] font-medium text-gray-600">Collaborators <span class="text-gray-400">· up to 2, comma-separated — they'll need to accept the invite</span></label>
                  <TextInput v-model="form.platforms.instagram.instagram_collaborators" placeholder="username1, username2" />
                </div>
              </div>

              <!-- LinkedIn-specific -->
              <div v-if="p.id === 'linkedin'" class="mt-2.5 flex flex-col gap-1.5">
                <label class="text-[11px] font-medium text-gray-600">
                  Tag people <span class="text-gray-400">· LinkedIn needs their exact member URN, not just a name — paste both, the name must appear in your caption above</span>
                </label>
                <div v-for="(m, i) in form.platforms.linkedin.linkedin_mentions" :key="i" class="flex items-center gap-1.5">
                  <TextInput v-model="m.name" placeholder="Name as it appears in the caption" class="flex-1" />
                  <TextInput v-model="m.urn" placeholder="urn:li:person:xxxxxxxx" class="flex-1" />
                  <button class="shrink-0 text-gray-400 hover:text-gray-700" @click="form.platforms.linkedin.linkedin_mentions.splice(i, 1)">
                    <LucideX class="h-3.5 w-3.5" />
                  </button>
                </div>
                <button
                  class="self-start text-[11.5px] font-semibold text-gray-500"
                  @click="form.platforms.linkedin.linkedin_mentions.push({ name: '', urn: '' })"
                >
                  + Tag someone
                </button>
              </div>

              <!-- shared link toggle (LinkedIn/X/Instagram) -->
              <div v-if="p.hasLink" class="mt-2.5">
                <div v-if="form.platforms[p.id].showLink" class="flex flex-col gap-1">
                  <label class="text-[11px] font-medium text-gray-600">Link / URL</label>
                  <TextInput v-model="form.platforms[p.id].link_url" placeholder="https://…" />
                </div>
                <button class="mt-1 text-[11.5px] font-semibold text-gray-500" @click="form.platforms[p.id].showLink = !form.platforms[p.id].showLink">
                  {{ form.platforms[p.id].showLink ? '− Remove link' : '+ Add a link / URL' }}
                </button>
              </div>
            </div>
          </div>
        </section>

        <!-- STEP 4: SCHEDULE -->
        <section v-if="currentStepKey === 'schedule'" class="py-4.5">
          <h3 class="m-0 mb-3 text-[14px] font-semibold">Schedule</h3>
          <div class="ml-0 grid grid-cols-2 gap-3" :class="isReadOnly ? 'pointer-events-none opacity-50' : ''">
            <div class="flex flex-col gap-1.5">
              <label class="text-[12px] font-medium text-gray-700">Publish date & time</label>
              <DateTimePicker v-model="form.scheduledOn" placeholder="Select date & time" />
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="text-[12px] font-medium text-gray-700">Linked project</label>
              <FormControl
                type="select"
                v-model="form.marketing_project"
                :options="[{ label: 'No project', value: '' }, ...(projectsResource.data || []).map((p) => ({ label: p.title, value: p.name }))]"
              />
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="text-[12px] font-medium text-gray-700">Assigned to</label>
              <FormControl
                type="select"
                v-model="form.assigned_to"
                :options="(team.data || []).map((m) => ({ label: m.name, value: m.id }))"
              />
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="text-[12px] font-medium text-gray-700">Reviewer <span class="text-gray-400">· optional</span></label>
              <FormControl
                type="select"
                v-model="form.reviewer"
                :options="[{ label: 'No reviewer', value: '' }, ...(team.data || []).map((m) => ({ label: m.name, value: m.id }))]"
              />
            </div>
          </div>
        </section>

        <!-- STEP 5: APPROVAL -->
        <section v-if="currentStepKey === 'approval'" class="py-4.5 pb-2">
          <h3 class="m-0 mb-3 text-[14px] font-semibold">Approval</h3>
          <div class="ml-0 flex flex-col gap-4">
            <!-- read-only recap of everything entered in steps 1-4 -->
            <div class="flex flex-col gap-3 rounded-xl border border-gray-100 p-3.5">
              <div class="flex flex-wrap gap-1.5">
                <PlatformBadge v-for="p in selectedPlatforms" :key="p.id" :platform="p" />
                <span v-if="!selectedPlatforms.length" class="text-[12px] text-gray-400">No platforms picked yet.</span>
              </div>
              <div>
                <span class="text-[11px] font-medium text-gray-500">Title</span>
                <p class="m-0 text-[13px] font-semibold text-gray-900">{{ form.title || '—' }}</p>
              </div>
              <div v-if="form.tags.length" class="flex flex-wrap gap-1">
                <span v-for="t in form.tags" :key="t" class="rounded bg-gray-100 px-1.5 py-0.5 text-[11px] text-gray-600">#{{ t }}</span>
              </div>
              <div v-for="p in selectedPlatforms" :key="p.id" class="border-t border-gray-100 pt-2.5">
                <div class="mb-1 flex items-center gap-1.5"><PlatformBadge :platform="p" /></div>
                <p class="m-0 whitespace-pre-line text-[12.5px] text-gray-600">
                  {{ p.id === 'blog' ? blogPostTitle(form.platforms.blog.blog_post) || 'No blog post selected' : form.platforms[p.id].caption || 'No caption written' }}
                </p>
              </div>
              <div v-if="form.assets.length" class="flex gap-2 border-t border-gray-100 pt-2.5">
                <div v-for="a in form.assets" :key="a.id" class="h-12 w-12 shrink-0 overflow-hidden rounded-lg bg-gray-100">
                  <img v-if="a.file_type === 'Image'" :src="a.file_url" class="h-full w-full object-cover" />
                </div>
              </div>
              <div class="border-t border-gray-100 pt-2.5 text-[12px] text-gray-500">
                Scheduled for {{ scheduledOnLabel || '—' }} · Assigned to {{ memberById(form.assigned_to).name }}
              </div>
            </div>

            <div v-if="!livePost.name" class="text-[12px] text-gray-400">Save this as a draft first — workflow and publish actions appear here once it exists.</div>
            <div v-else class="flex flex-col gap-2.5">
              <div v-if="otherTransitions.length" class="flex flex-wrap items-center gap-2">
                <Button
                  v-for="t in otherTransitions"
                  :key="t.action"
                  size="sm"
                  variant="outline"
                  :loading="actionLoading === t.action"
                  :disabled="!!actionLoading"
                  @click="runWorkflowAction(t.action)"
                  >{{ t.action }}</Button
                >
              </div>
              <div v-if="timingTransitions.length || canPublishNow" class="flex flex-col gap-1.5 rounded-lg border border-gray-100 bg-gray-25 p-3">
                <span class="text-[11px] font-medium text-gray-500">When should this go out?</span>
                <div class="flex flex-wrap gap-2">
                  <Button
                    v-for="t in timingTransitions"
                    :key="t.action"
                    size="sm"
                    variant="outline"
                    :loading="actionLoading === t.action"
                    :disabled="!!actionLoading"
                    @click="runWorkflowAction(t.action)"
                    >{{ t.action === 'Schedule' ? `Schedule for ${scheduledOnLabel}` : 'Retry later' }}</Button
                  >
                  <Button
                    v-if="canPublishNow"
                    size="sm"
                    variant="solid"
                    :loading="actionLoading === 'Publish now'"
                    :disabled="!!actionLoading"
                    @click="runPublishNow"
                    >Publish now</Button
                  >
                </div>
              </div>
              <p v-if="!otherTransitions.length && !timingTransitions.length && !canPublishNow" class="m-0 text-[12px] text-gray-400">
                Nothing pending — this post has no further workflow actions right now.
              </p>

              <div class="flex flex-col gap-2.5 border-t border-gray-100 pt-3">
                <span class="text-[11px] font-medium text-gray-500">Comments</span>
                <div v-if="(commentsResource.data || []).length" class="flex flex-col gap-2">
                  <div v-for="c in commentsResource.data" :key="c.name" class="rounded-lg bg-gray-25 px-2.5 py-2">
                    <div class="flex items-center gap-1.5">
                      <span class="text-[11.5px] font-semibold text-gray-700">{{ c.comment_by }}</span>
                      <span class="text-[10.5px] text-gray-400">{{ new Date(c.creation).toLocaleString() }}</span>
                    </div>
                    <p class="m-0 mt-0.5 whitespace-pre-line text-[12px] text-gray-600">{{ c.content }}</p>
                  </div>
                </div>
                <div class="flex items-start gap-2">
                  <Textarea v-model="newComment" :rows="2" class="flex-1" placeholder="Leave a note for whoever reads this next…" />
                  <Button size="sm" variant="outline" :loading="commentSubmitting" :disabled="!newComment.trim()" @click="submitComment">Comment</Button>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>

      <div class="flex items-center gap-2.5 border-t border-gray-100 px-6 py-3.5">
        <span class="text-[11.5px]" :class="errorMessage ? 'font-semibold text-red-600' : 'text-gray-400'">
          {{
            errorMessage ||
            (isReadOnly
              ? `${livePost.status} — click Edit post to make changes`
              : canSave
                ? 'Ready to save'
                : 'Pick at least one platform to continue')
          }}
        </span>
        <Button
          v-if="livePost.name"
          variant="outline"
          :loading="deleting"
          :class="deleteArmed ? 'border-red-300 !text-red-600' : '!text-red-500'"
          @click="onDeleteClick"
          >{{ deleteArmed ? 'Confirm delete?' : 'Delete post' }}</Button
        >
        <div class="ml-auto flex gap-2">
          <Button variant="outline" @click="emit('close')">Close</Button>
          <Button v-if="currentStepIndex > 0" variant="outline" @click="prevStep">Back</Button>
          <Button v-if="currentStepIndex < STEPS.length - 1" variant="solid" :disabled="currentStepIndex === 0 && !canSave" @click="nextStep">Next</Button>
          <template v-else>
            <Button v-if="isReadOnly" variant="solid" @click="editMode = true">Edit post</Button>
            <Button v-else variant="solid" :loading="saving" :disabled="!canSave" @click="onSave">{{ livePost.name ? 'Save changes' : 'Create draft' }}</Button>
          </template>
        </div>
      </div>
      </div>
    </template>
  </Dialog>

  <PostPreview v-model="previewOpen" :platforms="previewPlatforms" :assets="form.assets" :account-name="accountName" />
</template>
