# Feed

A [Frappe](https://github.com/frappe/frappe) app for planning, scheduling, and publishing marketing content across multiple platforms from a single calendar view.

## Features

- **Visual calendar** — drag-and-drop content planning across weeks and months
- **Multi-platform publishing** — publish to Instagram, LinkedIn, X (Twitter), and Frappe Blog in one click
- **Approval workflow** — Draft → In Review → Approved → Scheduled → Published with role-based gates
- **Asset gallery** — manage images and creatives attached to posts
- **Projects & tasks** — group posts under campaigns and track to-dos
- **Analytics** — post status breakdown, per-platform counts, and recent failure log
- **OAuth integrations** — connect Instagram (Meta Business Login), LinkedIn, and X via standard OAuth2/PKCE flows

## Requirements

- Frappe v16+
- The [`blog`](https://github.com/frappe/frappe) app (for Blog Post integration)
- Python 3.11+, Node 18+

## Installation

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/foram-star/marketing_calendar.git --branch version-16
bench install-app marketing_calendar
```

After installation, navigate to `/marketing` on your Frappe site.

## Configuration

Go to **Marketing Calendar Settings** (or `/marketing/settings`) and add credentials for each platform you want to use:

| Platform  | Credentials needed |
|-----------|--------------------|
| Instagram | Meta App ID, App Secret, Redirect URI, Webhook Verify Token |
| LinkedIn  | Client ID, Client Secret, Redirect URI |
| X         | Client ID, Client Secret, Redirect URI |
| Blog      | No credentials — uses the built-in Frappe Blog app |

## Roles

`after_install` creates two roles:

- **Marketing User** — create and submit posts for review
- **Marketing Manager** — approve, schedule, and manage all posts

## Development

```bash
# Python
cd apps/marketing_calendar
pre-commit install   # ruff, pyupgrade, eslint, prettier

# Frontend (Vue 3 + Vite + frappe-ui)
cd frontend
npm install
npm run dev
```

Built assets are committed under `marketing_calendar/public/frontend/` so the app works out-of-the-box on a fresh install without a separate build step.

## License

MIT — see [license.txt](license.txt)
