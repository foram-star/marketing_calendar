import { createResource, createListResource, createDocumentResource } from 'frappe-ui'
import { PLATFORMS, STATUSES } from './platforms'
import { splitScheduled } from '@/utils/date'

function decoratePost(raw) {
  const platforms = (raw.platforms || []).map((row) => ({
    ...row,
    meta: PLATFORMS[row.platform.toLowerCase()] || null,
  }))
  return {
    ...raw,
    _dt: splitScheduled(raw.scheduled_on),
    platforms,
    statusMeta: STATUSES[raw.status] || STATUSES.Draft,
  }
}

// Separate resource instances per view so the calendar's date-bounded fetch
// and the posts table's status/search fetch never clobber each other's state.
export const calendarPosts = createResource({
  url: 'marketing_calendar.api.list_posts',
  auto: false,
  transform: (data) => (data || []).map(decoratePost),
})

export const postsTable = createResource({
  url: 'marketing_calendar.api.list_posts',
  auto: false,
  transform: (data) => (data || []).map(decoratePost),
})

export function fetchCalendarRange(startIso, endIso, filters = {}) {
  return calendarPosts.fetch({ start: startIso, end: endIso, ...filters })
}

export function fetchPostsTable({ status, search, platform, assigned_to } = {}) {
  return postsTable.fetch({ status, search, platform, assigned_to })
}

// Plain mutator — `createListResource` gives us `frappe.client.insert` /
// `frappe.client.set_value`, both of which accept nested child-table rows
// (platforms/assets/tags) in a single round trip.
const mutator = createListResource({ doctype: 'Feed Post', auto: false })

export function createPost(values) {
  return mutator.insert.submit(values).then((doc) => {
    calendarPosts.reload?.()
    return doc
  })
}

export function updatePost(name, values) {
  return mutator.setValue.submit({ name, ...values })
}

export function deletePost(name) {
  return mutator.delete.submit(name).then(() => {
    calendarPosts.reload?.()
    postsTable.reload?.()
  })
}

/** Full document (incl. child tables) for editing an existing post in Compose. */
export function usePostDocument(name) {
  return createDocumentResource({ doctype: 'Feed Post', name, auto: !!name })
}
