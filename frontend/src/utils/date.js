// Date-grid helpers ported from the validated prototype (Feed.dc.html) —
// the month/week building logic was already correct there, just re-targeted to
// read from real `Marketing Post.scheduled_on` values instead of a static array.

export const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
]
export const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

function pad(n) {
  return String(n).padStart(2, '0')
}

export function isoDate(y, m, d) {
  return `${y}-${pad(m + 1)}-${pad(d)}`
}

export function isoDateTime(y, m, d, time) {
  return `${isoDate(y, m, d)} ${time}:00`
}

/** Splits a Frappe Datetime string ("2026-06-18 09:00:00") into {y, m, d, time}. */
export function splitScheduled(scheduledOn) {
  if (!scheduledOn) return null
  const [datePart, timePart] = scheduledOn.split(' ')
  const [y, m, d] = datePart.split('-').map(Number)
  const time = (timePart || '00:00:00').slice(0, 5)
  return { y, m: m - 1, d, time }
}

export function fmtTime(time) {
  if (!time) return ''
  const [H, M] = time.split(':').map(Number)
  const ap = H >= 12 ? 'PM' : 'AM'
  const h = ((H + 11) % 12) + 1
  return `${h}:${pad(M)} ${ap}`
}

export function isToday(y, m, d, today = new Date()) {
  return y === today.getFullYear() && m === today.getMonth() && d === today.getDate()
}

/** Groups posts (each carrying a parsed {y,m,d,time}) by "y-m-d" for fast lookups. */
export function groupPostsByDay(posts) {
  const map = new Map()
  for (const post of posts) {
    if (!post._dt) continue
    const key = isoDate(post._dt.y, post._dt.m, post._dt.d)
    if (!map.has(key)) map.set(key, [])
    map.get(key).push(post)
  }
  for (const list of map.values()) list.sort((a, b) => a._dt.time.localeCompare(b._dt.time))
  return map
}

function dayObj(date, curMonth, postsByDay, opts = {}) {
  const y = date.getFullYear()
  const m = date.getMonth()
  const d = date.getDate()
  const iso = isoDate(y, m, d)
  const all = postsByDay.get(iso) || []
  const limit = opts.limit || all.length
  return {
    y, m, d, iso,
    inMonth: m === curMonth,
    today: isToday(y, m, d),
    weekday: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][date.getDay()],
    posts: all.slice(0, limit),
    hasMore: all.length > limit,
    more: all.length - limit,
    count: all.length,
  }
}

export function buildMonth(y, m, postsByDay, limit = 3) {
  const first = new Date(y, m, 1)
  const dow = (first.getDay() + 6) % 7 // Monday-first
  const start = new Date(y, m, 1 - dow)
  const totalDays = new Date(y, m + 1, 0).getDate()
  const numWeeks = Math.ceil((dow + totalDays) / 7)
  const weeks = []
  for (let w = 0; w < numWeeks; w++) {
    const days = []
    for (let i = 0; i < 7; i++) {
      const dt = new Date(start)
      dt.setDate(start.getDate() + w * 7 + i)
      days.push(dayObj(dt, m, postsByDay, { limit }))
    }
    weeks.push({ days })
  }
  return weeks
}

export function buildWeek(ref, postsByDay) {
  const base = new Date(ref.y, ref.m, ref.d)
  const dow = (base.getDay() + 6) % 7
  const start = new Date(base)
  start.setDate(base.getDate() - dow)
  const days = []
  for (let i = 0; i < 7; i++) {
    const dt = new Date(start)
    dt.setDate(start.getDate() + i)
    days.push(dayObj(dt, ref.m, postsByDay))
  }
  return days
}

export function weekRangeLabel(week) {
  const a = week[0]
  const b = week[6]
  if (a.m === b.m) return `${MONTH_NAMES[a.m]} ${a.d} – ${b.d}, ${b.y}`
  return `${MONTH_NAMES[a.m].slice(0, 3)} ${a.d} – ${MONTH_NAMES[b.m].slice(0, 3)} ${b.d}`
}
