import { createResource } from 'frappe-ui'
import { STATUSES } from './platforms'

export const assetsResource = createResource({
  url: 'marketing_calendar.api.list_assets',
  auto: false,
  transform: (data) =>
    (data || []).map((a) => ({
      ...a,
      postStatusMeta: a.post ? STATUSES[a.post.status] || STATUSES.Draft : null,
    })),
})

export function fetchAssets(params = {}) {
  return assetsResource.fetch(params)
}

export function fmtBytes(bytes) {
  if (!bytes) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
