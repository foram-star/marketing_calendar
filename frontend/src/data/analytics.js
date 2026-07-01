import { createResource } from 'frappe-ui'

export const analyticsResource = createResource({
  url: 'marketing_calendar.api.get_analytics',
  auto: false,
})

export function fetchAnalytics() {
  return analyticsResource.fetch()
}
