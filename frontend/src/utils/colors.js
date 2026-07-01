import { memberById } from '@/data/team'

/** Background/foreground/bar colors for a calendar pill — ported from the prototype's mapPill(). */
export function pillColors(post, colorBy) {
  const plats = post.platforms.map((p) => p.meta).filter(Boolean)
  if (colorBy === 'member') {
    const mem = memberById(post.assigned_to)
    return { bg: mem.color + '1f', fg: '#3a3f46', bar: mem.color }
  }
  if (plats.length > 1) {
    return { bg: '#f4f5f7', fg: '#3a3f46', bar: '#71717a' }
  }
  if (plats.length === 1) {
    return { bg: plats[0].soft, fg: '#2b3138', bar: plats[0].color }
  }
  return { bg: '#f4f5f7', fg: '#3a3f46', bar: '#cbd5e1' }
}
