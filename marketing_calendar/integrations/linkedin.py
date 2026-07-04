# Copyright (c) 2026, Foram Shah and contributors
# For license information, please see license.txt

"""LinkedIn connector — the Posts API (the older UGC Posts API it replaced
is being sunset). One REST endpoint handles both plain-text and image posts,
but an image has to be uploaded through the separate Images API first and
referenced by URN — LinkedIn won't take inline image bytes on the post
itself the way some other platforms do.

@mentions are LinkedIn's own inline annotation syntax: `@[Name](urn:li:person:ID)`
embedded directly in the commentary text, where "Name" has to literally
appear in the text for LinkedIn to turn it into a real link. There's no way
for a personal-profile integration like this one to look someone up by name
— LinkedIn's People Typeahead API (the thing that *would* do that) is
restricted to organization-page-admin access, not available here — so the
caller has to already know the person's member URN; we just do the
find-and-wrap into the real annotation syntax.

Video isn't handled here yet — LinkedIn's video upload is a separate,
chunked multi-part flow (initializeUpload returns *multiple* upload URLs to
PUT consecutive byte ranges to), different enough in shape from the image
flow that it's a future addition rather than a quick extension here.
"""

import json

import frappe
import requests
from frappe import _

API_BASE = "https://api.linkedin.com"
LINKEDIN_VERSION = "202506"


def _connected_account():
	name = frappe.db.get_value(
		"Marketing Social Account",
		{"platform": "LinkedIn", "enabled": 1, "status": "Connected"},
		"name",
		order_by="modified desc",
	)
	if not name:
		frappe.throw(_("No connected LinkedIn account — connect one in Settings first."))
	return frappe.get_doc("Marketing Social Account", name)


def _headers(access_token):
	return {
		"Authorization": f"Bearer {access_token}",
		"Linkedin-Version": LINKEDIN_VERSION,
		"X-Restli-Protocol-Version": "2.0.0",
	}


def _api_call(method, path, access_token, **kwargs):
	resp = requests.request(method, f"{API_BASE}{path}", headers=_headers(access_token), timeout=30, **kwargs)
	if resp.status_code >= 400:
		try:
			detail = resp.json().get("message", resp.text)
		except ValueError:
			detail = resp.text
		raise frappe.ValidationError(f"LinkedIn API error ({resp.status_code}): {detail}")
	return resp


def _upload_video(asset, author_urn, access_token):
	"""Chunked video upload: initializeUpload → PUT chunk(s) → finalizeUpload."""
	init_resp = _api_call(
		"POST",
		"/rest/videos?action=initializeUpload",
		access_token,
		json={"initializeUploadRequest": {"owner": author_urn}},
	)
	init_data = init_resp.json()["value"]
	video_urn = init_data["video"]
	upload_token = init_data.get("uploadToken", "")
	instructions = init_data.get("uploadInstructions", [])

	file_url = frappe.utils.get_url(asset.file)
	video_bytes = requests.get(file_url, timeout=120).content

	etags = []
	for instruction in instructions:
		upload_url = instruction["uploadUrl"]
		first_byte = instruction.get("firstByte", 0)
		last_byte = instruction.get("lastByte", len(video_bytes) - 1)
		chunk = video_bytes[first_byte : last_byte + 1]
		put_resp = requests.put(
			upload_url,
			data=chunk,
			headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/octet-stream"},
			timeout=120,
		)
		put_resp.raise_for_status()
		etags.append(put_resp.headers.get("ETag", ""))

	_api_call(
		"POST",
		"/rest/videos?action=finalizeUpload",
		access_token,
		json={"finalizeUploadRequest": {"video": video_urn, "uploadToken": upload_token, "uploadedPartIds": etags}},
	)
	return video_urn


def _upload_image(asset, author_urn, access_token):
	init_resp = _api_call(
		"POST",
		"/rest/images?action=initializeUpload",
		access_token,
		json={"initializeUploadRequest": {"owner": author_urn}},
	)
	init_data = init_resp.json()["value"]
	upload_url = init_data["uploadUrl"]
	image_urn = init_data["image"]

	# Same "server fetches from our own URL" reality as Instagram's connector
	# would have hit too, except LinkedIn wants the bytes pushed to it
	# directly instead of fetching a URL itself — so we fetch our own file
	# and PUT it straight through.
	file_url = frappe.utils.get_url(asset.file)
	image_bytes = requests.get(file_url, timeout=30).content
	put_resp = requests.put(
		upload_url, data=image_bytes, headers={"Authorization": f"Bearer {access_token}"}, timeout=60
	)
	put_resp.raise_for_status()
	return image_urn


def _apply_mentions(text, mentions_json):
	if not mentions_json:
		return text
	try:
		mentions = json.loads(mentions_json)
	except (TypeError, ValueError):
		return text
	for m in mentions:
		name, urn = (m.get("name") or "").strip(), (m.get("urn") or "").strip()
		if not name or not urn or name not in text:
			continue
		text = text.replace(name, f"@[{name}]({urn})", 1)
	return text


def publish(post, platform_row):
	if not platform_row.caption:
		frappe.throw(_("Add a caption before publishing {0} to LinkedIn.").format(post.title))

	account = _connected_account()
	access_token = account.get_password("access_token")
	author_urn = f"urn:li:person:{account.external_account_id}"

	images = [a for a in post.assets if a.file_type == "Image"][:1]
	videos = [a for a in post.assets if a.file_type == "Video"][:1]

	body = {
		"author": author_urn,
		"commentary": _apply_mentions(platform_row.caption, platform_row.linkedin_mentions),
		"visibility": "PUBLIC",
		"distribution": {
			"feedDistribution": "MAIN_FEED",
			"targetEntities": [],
			"thirdPartyDistributionChannels": [],
		},
		"lifecycleState": "PUBLISHED",
		"isReshareDisabledByAuthor": False,
	}
	if videos:
		body["content"] = {"media": {"id": _upload_video(videos[0], author_urn, access_token)}}
	elif images:
		body["content"] = {"media": {"id": _upload_image(images[0], author_urn, access_token)}}
	elif platform_row.link_url:
		body["content"] = {"article": {"source": platform_row.link_url}}

	resp = _api_call("POST", "/rest/posts", access_token, json=body)
	post_urn = resp.headers.get("x-restli-id")
	if not post_urn:
		frappe.throw(_("LinkedIn accepted the post but returned no post id."))

	platform_row.external_post_id = post_urn
	platform_row.external_url = f"https://www.linkedin.com/feed/update/{post_urn}"
	return platform_row
