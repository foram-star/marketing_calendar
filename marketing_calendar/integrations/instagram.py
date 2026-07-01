# Copyright (c) 2026, Foram Shah and contributors
# For license information, please see license.txt

"""Instagram connector — Meta's Content Publishing API, using whichever
connected `Marketing Social Account` token the OAuth flow in api.py stored.
Two-step container flow per Meta's docs: create a media container, poll until
it's finished processing, then publish it. A second asset turns this into a
carousel container instead of a single-image one — Instagram has no other
way to do multi-image posts.

Host matters here: our OAuth flow uses the newer direct "Instagram Login"
(api.instagram.com), and tokens minted that way only validate against
graph.instagram.com — graph.facebook.com (the older Facebook-Login-based
flow's host) rejects them with "Cannot parse access token" even though the
endpoint shapes (/media, /media_publish) look identical on both hosts.

Real constraint worth knowing: Instagram's servers fetch the image/video
themselves from `image_url`/`video_url` (and `cover_url`) — our files have to
be reachable from the public internet for this to work at all, which is
exactly the same "local bench isn't internet-reachable" problem as the OAuth
redirect itself.
"""

import time

import frappe
import requests
from frappe import _

GRAPH_BASE = "https://graph.instagram.com/v21.0"
POLL_INTERVAL_SECONDS = 2
POLL_MAX_ATTEMPTS = 30
MAX_COLLABORATORS = 2  # Meta's own cap is 3 for images/Reels — ours is tighter, by request


def _connected_account():
	name = frappe.db.get_value(
		"Marketing Social Account",
		{"platform": "Instagram", "enabled": 1, "status": "Connected"},
		"name",
		order_by="modified desc",
	)
	if not name:
		frappe.throw(_("No connected Instagram account — connect one in Settings first."))
	return frappe.get_doc("Marketing Social Account", name)


def _graph_call(method, path, **kwargs):
	resp = requests.request(method, f"{GRAPH_BASE}/{path}", timeout=30, **kwargs)
	try:
		data = resp.json()
	except ValueError:
		resp.raise_for_status()
		raise
	if "error" in data:
		raise frappe.ValidationError(data["error"].get("message", str(data["error"])))
	resp.raise_for_status()
	return data


def _wait_until_finished(container_id, access_token):
	for _attempt in range(POLL_MAX_ATTEMPTS):
		data = _graph_call(
			"GET", container_id, params={"fields": "status_code", "access_token": access_token}
		)
		status = data.get("status_code")
		if status == "FINISHED":
			return
		if status in ("ERROR", "EXPIRED"):
			frappe.throw(_("Instagram couldn't process this media (status: {0}).").format(status))
		time.sleep(POLL_INTERVAL_SECONDS)
	frappe.throw(_("Instagram is still processing this media after {0}s — try publishing again shortly.").format(
		POLL_INTERVAL_SECONDS * POLL_MAX_ATTEMPTS
	))


def _collaborators(platform_row):
	raw = (platform_row.instagram_collaborators or "").strip()
	if not raw:
		return []
	usernames = [u.strip().lstrip("@") for u in raw.split(",") if u.strip()]
	return usernames[:MAX_COLLABORATORS]


def publish(post, platform_row):
	if not platform_row.caption:
		frappe.throw(_("Add a caption before publishing {0} to Instagram.").format(post.title))
	if not post.assets:
		frappe.throw(_("Instagram requires at least one image or video."))

	account = _connected_account()
	access_token = account.get_password("access_token")
	ig_user_id = account.external_account_id

	assets = post.assets[:4]  # Instagram's own carousel cap
	caption = platform_row.caption
	collaborators = _collaborators(platform_row)

	if len(assets) == 1:
		asset = assets[0]
		file_url = frappe.utils.get_url(asset.file)
		payload = {"caption": caption, "access_token": access_token}
		if collaborators:
			payload["collaborators"] = frappe.as_json(collaborators)
		if asset.file_type == "Video":
			payload["media_type"] = "REELS"
			payload["video_url"] = file_url
			if asset.thumbnail:
				payload["cover_url"] = frappe.utils.get_url(asset.thumbnail)
		else:
			payload["image_url"] = file_url
		container = _graph_call("POST", f"{ig_user_id}/media", data=payload)
		container_id = container["id"]
		_wait_until_finished(container_id, access_token)
	else:
		child_ids = []
		for asset in assets:
			file_url = frappe.utils.get_url(asset.file)
			item_payload = {"is_carousel_item": "true", "access_token": access_token}
			if asset.file_type == "Video":
				item_payload["media_type"] = "VIDEO"
				item_payload["video_url"] = file_url
				if asset.thumbnail:
					item_payload["cover_url"] = frappe.utils.get_url(asset.thumbnail)
			else:
				item_payload["image_url"] = file_url
			item = _graph_call("POST", f"{ig_user_id}/media", data=item_payload)
			_wait_until_finished(item["id"], access_token)
			child_ids.append(item["id"])

		carousel_payload = {
			"media_type": "CAROUSEL",
			"caption": caption,
			"children": ",".join(child_ids),
			"access_token": access_token,
		}
		if collaborators:
			carousel_payload["collaborators"] = frappe.as_json(collaborators)
		container = _graph_call("POST", f"{ig_user_id}/media", data=carousel_payload)
		container_id = container["id"]
		_wait_until_finished(container_id, access_token)

	published = _graph_call(
		"POST", f"{ig_user_id}/media_publish", data={"creation_id": container_id, "access_token": access_token}
	)
	media_id = published["id"]

	if platform_row.instagram_first_comment:
		try:
			_graph_call(
				"POST",
				f"{media_id}/comments",
				data={"message": platform_row.instagram_first_comment, "access_token": access_token},
			)
		except Exception:
			frappe.log_error(title="Instagram first-comment failed", message=frappe.get_traceback())

	permalink_data = _graph_call("GET", media_id, params={"fields": "permalink", "access_token": access_token})

	platform_row.external_post_id = media_id
	platform_row.external_url = permalink_data.get("permalink")
	return platform_row
