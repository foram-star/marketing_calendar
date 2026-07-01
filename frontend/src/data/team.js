import { createResource } from 'frappe-ui'
import { colorForUser, initialsForUser } from './platforms'

export const teamResource = createResource({
  url: 'marketing_calendar.api.get_team_members',
  auto: true,
  cache: 'marketing-calendar-team',
  transform(data) {
    return (data || []).map((m) => ({
      id: m.name,
      name: m.full_name || m.name,
      image: m.user_image,
      color: colorForUser(m.name),
      initials: initialsForUser(m.full_name, m.name),
    }))
  },
})

export function useTeam() {
  return teamResource
}

export function memberById(id) {
  const list = teamResource.data || []
  return (
    list.find((m) => m.id === id) || {
      id,
      name: id || 'Unassigned',
      color: colorForUser(id || '?'),
      initials: initialsForUser(null, id || '?'),
    }
  )
}
