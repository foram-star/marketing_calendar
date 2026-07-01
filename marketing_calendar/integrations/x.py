# Copyright (c) 2026, Foram Shah and contributors
# For license information, please see license.txt

"""X (Twitter) connector — API v2 throughout, including the chunked media
upload endpoint (api.x.com/2/media/upload) that replaced the old OAuth-1.0a
upload.twitter.com one, which X retired for OAuth2 apps in March 2025.

Access tokens from the PKCE flow are short-lived (~2 hours), so unlike
LinkedIn/Instagram this connector refreshes its own token before every
publish using the refresh_token `offline.access` got us at connect time —
otherwise this would need a human to re-authorize every couple of hours.

`x_sensitive_media` is real on the doctype but deliberately unused here:
X's v2 create-post body has no per-Tweet sensitive-media field (only
`media.media_ids`/`media.tagged_user_ids`) — that flag is account-level
("mark media you Tweet as sensitive" in account settings), not something
this API call can set per post. `x_reply_settings` *is* a real per-post
field and is wired up below.
"""

import time

import frappe
import requests
from frappe import _

API_BASE = "https://api.x.com/2"
MEDIA_CATEGORY = {"Image": "tweet_image", "Video": "tweet_video"}
REPLY_SETTINGS = {"Following": "following", "Mentioned": "mentionedUsers"}  # "Everyone" = omit the field


def _connected_account():
	name = frappe.db.get_value(
		"Marketing Social Account",
		{"platform": "X", "enabled": 1, "status": "Connected"},
		"name",
		order_by="modified desc",
	)
	if not name:
		frappe.throw(_("No connected X account — connect one in Settings first."))
	return frappe.get_doc("Marketing Social Account", name)


def _refresh_if_needed(account):
	if account.token_expires_on and frappe.utils.now_datetime() < frappe.utils.get_datetime(account.token_expires_on):
		return account.get_password("access_token")

	refresh_token = account.get_password("refresh_token")
	if not refresh_token:
		frappe.throw(_("X access token expired and there's no refresh token saved — reconnect this account in Settings."))

	settings = frappe.get_single("Marketing Calendar Settings")
	resp = requests.post(
		f"{API_BASE}/oauth2/token",
		data={"grant_type": "refresh_token", "refresh_token": refresh_token, "client_id": settings.x_client_id},
		auth=(settings.x_client_id, settings.get_password("x_client_secret")),
		timeout=15,
	)
	resp.raise_for_status()
	data = resp.json()

	new_access_token = data["access_token"]
	account.access_token = new_access_token
	if data.get("refresh_token"):
		account.refresh_token = data["refresh_token"]
	account.token_expires_on = frappe.utils.add_to_date(frappe.utils.now_datetime(), seconds=data.get("expires_in", 7200))
	account.save(ignore_permissions=True)
	frappe.db.commit()
	return new_access_token


def _upload_media(asset, access_token):
	file_url = frappe.utils.get_url(asset.file)
	file_bytes = requests.get(file_url, timeout=30).content
	headers = {"Authorization": f"Bearer {access_token}"}

	init_resp = requests.post(
		f"{API_BASE}/media/upload",
		data={
			"command": "INIT",
			"media_type": "video/mp4" if asset.file_type == "Video" else "image/jpeg",
			"total_bytes": len(file_bytes),
			"media_category": MEDIA_CATEGORY.get(asset.file_type, "tweet_image"),
		},
		headers=headers,
		timeout=30,
	)
	init_resp.raise_for_status()
	media_id = init_resp.json()["data"]["id"]

	append_resp = requests.post(
		f"{API_BASE}/media/upload",
		data={"command": "APPEND", "media_id": media_id, "segment_index": 0},
		files={"media": file_bytes},
		headers=headers,
		timeout=60,
	)
	append_resp.raise_for_status()

	finalize_resp = requests.post(
		f"{API_BASE}/media/upload",
		data={"command": "FINALIZE", "media_id": media_id},
		headers=headers,
		timeout=30,
	)
	finalize_resp.raise_for_status()
	processing = finalize_resp.json()["data"].get("processing_info")

	while processing and processing.get("state") in ("pending", "in_progress"):
		time.sleep(processing.get("check_after_secs", 2))
		status_resp = requests.get(
			f"{API_BASE}/media/upload",
			params={"command": "STATUS", "media_id": media_id},
			headers=headers,
			timeout=30,
		)
		status_resp.raise_for_status()
		processing = status_resp.json()["data"].get("processing_info")
	if processing and processing.get("state") == "failed":
		message = processing.get("error", {}).get("message", "unknown error")
		frappe.throw(_("X couldn't process this media: {0}").format(message))

	return media_id


def publish(post, platform_row):
	if not platform_row.caption:
		frappe.throw(_("Add a caption before publishing {0} to X.").format(post.title))

	account = _connected_account()
	access_token = _refresh_if_needed(account)

	text = platform_row.caption
	if platform_row.link_url:
		text = f"{text}\n{platform_row.link_url}"

	body = {"text": text}
	reply_setting = REPLY_SETTINGS.get(platform_row.x_reply_settings)
	if reply_setting:
		body["reply_settings"] = reply_setting

	assets = post.assets[:4]  # X's own per-Tweet image cap
	if assets:
		body["media"] = {"media_ids": [_upload_media(a, access_token) for a in assets]}

	resp = requests.post(
		f"{API_BASE}/tweets",
		json=body,
		headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
		timeout=30,
	)
	if resp.status_code >= 400:
		try:
			detail = resp.json()
		except ValueError:
			detail = resp.text
		raise frappe.ValidationError(f"X API error ({resp.status_code}): {detail}")

	tweet_id = resp.json()["data"]["id"]
	username = account.external_username

	platform_row.external_post_id = tweet_id
	platform_row.external_url = f"https://x.com/{username}/status/{tweet_id}" if username else f"https://x.com/i/web/status/{tweet_id}"
	return platform_row
