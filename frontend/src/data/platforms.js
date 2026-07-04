// Platform metadata: colors, caption limits, and upload guidance.
// "name" must match the DocType's Select options exactly.
// "short" is used in compact badge contexts (Posts list columns etc.)
// where fitting multiple badges in a narrow column matters.
export const PLATFORMS = {
  linkedin: {
    id: 'linkedin',
    name: 'LinkedIn',
    short: 'LI',
    color: '#0A66C2',
    soft: '#eaf2fb',
    limit: 3000,
    guide: '1200×1200px square · or 1200×627px landscape',
    ratio: 1,
    ratioLabel: 'Square 1:1',
    videoGuide: '1920×1080px (16:9) or 1080×1920px (9:16) · MP4 · up to 10 min',
    videoRatio: 16 / 9,
    videoRatioLabel: '16:9',
    videoMinSec: 3,
    videoMaxSec: 600,
    hasLink: true,
  },
  x: {
    id: 'x',
    name: 'X',
    short: 'X',
    color: '#18181b',
    soft: '#f1f1f2',
    limit: 280,
    guide: '1600×900px (16:9) · or 1200×1200px square',
    ratio: 16 / 9,
    ratioLabel: '16:9',
    videoGuide: '1920×1080px (16:9) · MP4 or MOV · up to 140 sec',
    videoRatio: 16 / 9,
    videoRatioLabel: '16:9',
    videoMinSec: 0,
    videoMaxSec: 140,
    hasLink: true,
  },
  instagram: {
    id: 'instagram',
    name: 'Instagram',
    short: 'IG',
    color: '#c13584',
    soft: '#fbe9f3',
    limit: 2200,
    guide: '1080×1350px (4:5) · or 1080×1080px square',
    ratio: 4 / 5,
    ratioLabel: '4:5',
    videoGuide: '1080×1920px (9:16) · MP4 · 3–90 sec · Published as Reel',
    videoRatio: 9 / 16,
    videoRatioLabel: '9:16 Reel',
    videoMinSec: 3,
    videoMaxSec: 90,
    hasLink: true,
  },
  blog: {
    id: 'blog',
    name: 'Blog',
    short: 'Blog',
    color: '#b45309',
    soft: '#fef3c7',
    limit: null,
    guide: 'No image required · content goes straight to the blog post body',
    ratio: 16 / 9,
    ratioLabel: '16:9',
    hasLink: false,
  },
}

export const PLATFORM_LIST = Object.values(PLATFORMS)

export const STATUSES = {
  Draft: { c: '#6b7280', bg: '#f1f3f5' },
  'In Review': { c: '#b45309', bg: '#fef3c7' },
  Approved: { c: '#1d4ed8', bg: '#dbeafe' },
  Rejected: { c: '#dc2626', bg: '#fee2e2' },
  Scheduled: { c: '#0f766e', bg: '#cdf3ec' },
  Published: { c: '#15803d', bg: '#dcfce7' },
  'Partially Published': { c: '#9333ea', bg: '#f3e8ff' },
  Failed: { c: '#dc2626', bg: '#fee2e2' },
}

export const POST_STATUS_OPTIONS = Object.keys(STATUSES)

export const MEMBER_COLORS = [
  '#e0588f',
  '#5b8def',
  '#e8a33d',
  '#9b6dde',
  '#10b981',
  '#0ea5a4',
]

export function colorForUser(userId) {
  let hash = 0
  for (let i = 0; i < userId.length; i++) hash = (hash * 31 + userId.charCodeAt(i)) >>> 0
  return MEMBER_COLORS[hash % MEMBER_COLORS.length]
}

export function initialsForUser(fullName, userId) {
  const source = (fullName || userId || '?').trim()
  const parts = source.split(/\s+/).filter(Boolean)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return source.slice(0, 2).toUpperCase()
}
