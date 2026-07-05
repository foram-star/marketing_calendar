# Copyright (c) 2026, Foram Shah and contributors
# For license information, please see license.txt

import base64
import hashlib
import hmac
import importlib
import secrets
from urllib.parse import urlencode

import frappe
import requests
from frappe import _
from frappe.model.workflow import apply_workflow
from werkzeug.wrappers import Response

from marketing_calendar.notifications import notify_duplicate_publish_blocked

INTEGRATIONS = {
	"Blog": "marketing_calendar.integrations.blog",
	"Instagram": "marketing_calendar.integrations.instagram",
	"LinkedIn": "marketing_calendar.integrations.linkedin",
	"X": "marketing_calendar.integrations.x",
}


@frappe.whitelist()
def get_team_members():
	"""Users who can be assigned/reviewed on a Feed Post (for avatars/pickers)."""
	user_names = frappe.get_all(
		"Has Role",
		filters={"role": ["in", ["Marketing Manager", "Marketing User"]], "parenttype": "User"},
		pluck="parent",
		distinct=True,
	)
	if not user_names:
		return []
	return frappe.get_all(
		"User",
		filters={"name": ["in", user_names], "enabled": 1},
		fields=["name", "full_name", "user_image"],
		order_by="full_name asc",
	)


POST_LIST_FIELDS = [
	"name",
	"title",
	"status",
	"scheduled_on",
	"assigned_to",
	"reviewer",
	"marketing_project",
	"modified",
]


@frappe.whitelist()
def list_posts(status=None, search=None, start=None, end=None, platform=None, assigned_to=None):
	"""Posts plus their platform rows in two queries — `frappe.client.get_list`
	can't see child tables, and fetching each post's full doc one-by-one for a
	calendar month or the posts table would be an N+1 query per render.

	`platform`/`assigned_to` back the Calendar view's filter bar — the same
	`{fieldname: [operator, value]}` shape frappe-ui's `ListFilter` emits, so
	the SPA can reuse Desk's own filter-builder component as-is."""
	filters = {}
	if status and status != "All":
		filters["status"] = status
	if start and end:
		filters["scheduled_on"] = ["between", [start, end]]
	if assigned_to:
		operator, value = assigned_to if isinstance(assigned_to, list) else ["=", assigned_to]
		filters["assigned_to"] = [operator, value]

	if platform:
		operator, value = platform if isinstance(platform, list) else ["=", platform]
		matching_parents = frappe.get_all(
			"Feed Post Platform", filters={"platform": value}, pluck="parent", distinct=True
		)
		filters["name"] = ["not in", matching_parents] if operator == "!=" else ["in", matching_parents or [""]]

	posts = frappe.get_all(
		"Feed Post",
		filters=filters,
		or_filters={"title": ["like", f"%{search}%"]} if search else None,
		fields=POST_LIST_FIELDS,
		order_by="scheduled_on asc",
	)
	if not posts:
		return []

	names = [p.name for p in posts]
	platform_rows = frappe.get_all(
		"Feed Post Platform",
		filters={"parent": ["in", names]},
		fields=["parent", "platform", "status", "external_url", "caption"],
		order_by="idx asc",
	)
	by_parent = {}
	for row in platform_rows:
		by_parent.setdefault(row.parent, []).append(row)
	for post in posts:
		post["platforms"] = by_parent.get(post.name, [])

	return posts


@frappe.whitelist()
def list_assets(file_type=None, search=None):
	"""Every uploaded creative across all posts, with enough of the parent post
	to give context — `Feed Post Asset` is a child table so a plain
	`get_list` can't see it; this is the gallery's only query."""
	filters = {}
	if file_type and file_type != "All":
		filters["file_type"] = file_type
	if search:
		filters["alt_text"] = ["like", f"%{search}%"]

	assets = frappe.get_all(
		"Feed Post Asset",
		filters=filters,
		fields=["name", "parent", "file", "file_type", "alt_text", "width", "height", "file_size"],
		order_by="creation desc",
	)
	if not assets:
		return []

	parent_names = list({a.parent for a in assets})
	posts = frappe.get_all(
		"Feed Post",
		filters={"name": ["in", parent_names]},
		fields=["name", "title", "status", "scheduled_on"],
	)
	posts_by_name = {p.name: p for p in posts}
	for asset in assets:
		asset["post"] = posts_by_name.get(asset.parent)
	return assets


@frappe.whitelist()
def get_analytics():
	"""Operational analytics from what we actually have on-site — post/platform
	outcomes we recorded ourselves. No engagement metrics (likes/comments/reach):
	those would have to come back from each platform's own API, which isn't
	wired up yet (Phase 3, blocked on LinkedIn/X/Instagram credentials)."""
	status_counts = {
		row.status: row.count
		for row in frappe.get_all(
			"Feed Post", group_by="status", fields=["status", {"COUNT": "name", "as": "count"}]
		)
	}
	platform_counts = {
		row.platform: row.count
		for row in frappe.get_all(
			"Feed Post Platform",
			group_by="platform",
			fields=["platform", {"COUNT": "name", "as": "count"}],
		)
	}
	platform_outcome_counts = frappe.get_all(
		"Feed Post Platform",
		group_by="platform, status",
		fields=["platform", "status", {"COUNT": "name", "as": "count"}],
	)

	today = frappe.utils.today()
	week_end = frappe.utils.add_days(today, 7)
	month_start = frappe.utils.get_first_day(today)

	upcoming_count = frappe.db.count(
		"Feed Post", {"status": "Scheduled", "scheduled_on": ["between", [today, week_end]]}
	)
	published_this_month = frappe.db.count(
		"Feed Post Platform",
		{"status": "Published", "published_at": [">=", month_start]},
	)

	recent_failures = frappe.get_all(
		"Feed Post Platform",
		filters={"status": "Failed"},
		fields=["parent", "platform", "error_message", "last_attempted_at"],
		order_by="last_attempted_at desc",
		limit_page_length=10,
	)
	if recent_failures:
		titles = frappe.get_all(
			"Feed Post",
			filters={"name": ["in", [r.parent for r in recent_failures]]},
			fields=["name", "title"],
		)
		title_by_name = {t.name: t.title for t in titles}
		for r in recent_failures:
			r["post_title"] = title_by_name.get(r.parent)

	return {
		"total_posts": sum(status_counts.values()),
		"status_counts": status_counts,
		"platform_counts": platform_counts,
		"platform_outcome_counts": platform_outcome_counts,
		"upcoming_count": upcoming_count,
		"published_this_month": published_this_month,
		"recent_failures": recent_failures,
	}


def run_publish(doc):
	"""Core Scheduled -> Published/Partially Published/Failed step, shared by
	the manual "Publish now" button and the scheduler job. Claims each platform
	row before attempting it so a concurrent retry can't double-publish — a row
	already `Publishing`/`Published` is skipped and reported instead.
	"""
	any_success = False
	any_failure = False

	for row in doc.platforms:
		if row.status == "Published":
			any_success = True
			continue
		if row.status == "Publishing":
			notify_duplicate_publish_blocked(doc, row)
			continue

		row.status = "Publishing"
		row.last_attempted_at = frappe.utils.now_datetime()
		row.attempt_count = (row.attempt_count or 0) + 1
		doc.save(ignore_permissions=True)
		frappe.db.commit()

		try:
			module_path = INTEGRATIONS.get(row.platform)
			if not module_path:
				frappe.throw(_("{0} isn't connected yet — add credentials in Settings.").format(row.platform))
			importlib.import_module(module_path).publish(doc, row)
			row.status = "Published"
			row.published_at = frappe.utils.now_datetime()
			row.error_message = None
			any_success = True
		except Exception as e:
			frappe.db.rollback()
			row.status = "Failed"
			row.error_message = str(e)
			any_failure = True
		doc.save(ignore_permissions=True)
		frappe.db.commit()

	if any_success and any_failure:
		action = "Mark Partially Published"
	elif any_success:
		action = "Mark Published"
	else:
		action = "Mark Failed"

	apply_workflow({"doctype": "Feed Post", "name": doc.name}, action)
	return frappe.get_doc("Feed Post", doc.name)


@frappe.whitelist()
def publish_now(post):
	"""Manual "Publish now" — works from Approved (publishes immediately,
	skipping the wait) or from Scheduled/Failed (the normal due-time/retry path).
	Approved posts are walked through the Schedule transition first (defaulting
	scheduled_on to right now if it's still empty) so every published post has
	gone through the same Scheduled state on its way out, keeping the workflow
	graph and any reporting built on it consistent.
	"""
	doc = frappe.get_doc("Feed Post", post)
	doc.check_permission("write")

	if doc.status == "Approved":
		if not doc.scheduled_on:
			doc.scheduled_on = frappe.utils.now_datetime()
			doc.save(ignore_permissions=True)
			frappe.db.commit()
		apply_workflow({"doctype": "Feed Post", "name": doc.name}, "Schedule")
		doc.reload()
	elif doc.status == "Failed":
		# The only transition out of Failed is Retry -> Scheduled — run_publish's
		# own closing "Mark Published/Partially Published/Failed" transitions only
		# exist *from* Scheduled, so a retry has to walk back through it first.
		apply_workflow({"doctype": "Feed Post", "name": doc.name}, "Retry")
		doc.reload()
	elif doc.status != "Scheduled":
		frappe.throw(_("Only an Approved, Scheduled, or Failed post can be published."))

	return run_publish(doc)


# --- Instagram OAuth -------------------------------------------------------
# Meta's newer "Business Login for Instagram" — direct Instagram auth, no
# Facebook Page required. https://api.instagram.com/oauth/authorize, then a
# short-lived -> long-lived (~60 day) token exchange against graph.instagram.com.
INSTAGRAM_AUTHORIZE_URL = "https://api.instagram.com/oauth/authorize"
INSTAGRAM_TOKEN_URL = "https://api.instagram.com/oauth/access_token"
INSTAGRAM_LONG_LIVED_URL = "https://graph.instagram.com/access_token"
INSTAGRAM_SCOPES = "instagram_business_basic,instagram_business_content_publish"


def _redirect(url):
	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = url


@frappe.whitelist()
def connect_instagram():
	"""Kicks off the OAuth dance — the browser leaves our site entirely here
	and comes back via `oauth_callback_instagram` once the user approves.
	The `state` token (not the session cookie) is what ties that eventual
	callback back to whoever clicked Connect, since cross-site top-level
	redirects don't reliably carry session cookies the same way same-site
	navigation does.
	"""
	settings = frappe.get_single("Feed Settings")
	if not settings.meta_app_id:
		frappe.throw(_("Add a Meta App ID in Feed Settings first."))

	state = frappe.generate_hash(length=20)
	frappe.cache().set_value(f"mc_oauth_state:{state}", frappe.session.user, expires_in_sec=600)

	params = {
		"client_id": settings.meta_app_id,
		"redirect_uri": settings.meta_redirect_uri,
		"response_type": "code",
		"scope": INSTAGRAM_SCOPES,
		"state": state,
	}
	_redirect(f"{INSTAGRAM_AUTHORIZE_URL}?{urlencode(params)}")


@frappe.whitelist(allow_guest=True)
def oauth_callback_instagram(code=None, state=None, error=None, error_description=None):
	settings = frappe.get_single("Feed Settings")
	print(f"Instagram OAuth callback: code={code}, state={state}, error={error}, error_description={error_description}")

	def fail(message):
		frappe.log_error(title="Instagram OAuth failed", message=message)
		_redirect("/marketing/settings?connect_error=instagram")

	if error or not code or not state:
		return fail(error_description or error or "Missing code/state in callback")

	cache_key = f"mc_oauth_state:{state}"
	connecting_user = frappe.cache().get_value(cache_key)
	if not connecting_user:
		return fail("OAuth state expired, missing, or already used")
	frappe.cache().delete_value(cache_key)

	try:
		token_resp = requests.post(
			INSTAGRAM_TOKEN_URL,
			data={
				"client_id": settings.meta_app_id,
				"client_secret": settings.get_password("meta_app_secret"),
				"grant_type": "authorization_code",
				"redirect_uri": settings.meta_redirect_uri,
				"code": code,
			},
			timeout=15,
		)
		token_resp.raise_for_status()
		short_lived_token = token_resp.json()["access_token"]

		long_resp = requests.get(
			INSTAGRAM_LONG_LIVED_URL,
			params={
				"grant_type": "ig_exchange_token",
				"client_secret": settings.get_password("meta_app_secret"),
				"access_token": short_lived_token,
			},
			timeout=15,
		)
		long_resp.raise_for_status()
		long_data = long_resp.json()
		access_token = long_data["access_token"]
		expires_in = long_data.get("expires_in", 60 * 24 * 60 * 60)

		identity_resp = requests.get(
			"https://graph.instagram.com/v21.0/me",
			params={"fields": "id,username", "access_token": access_token},
			timeout=15,
		)
		identity_resp.raise_for_status()
		identity = identity_resp.json()
	except requests.RequestException as e:
		return fail(str(e))

	# `frappe.set_user` alone only changes the in-memory user for the rest of
	# *this* request — it doesn't issue a session cookie, so the very next
	# request (the redirect below, landing on the tunnel's own origin, which
	# has no cookie of its own yet even if you're separately logged in on
	# site1.localhost) would still look logged-out. `login_as` actually
	# establishes a real session and sets the cookie on this response.
	frappe.local.login_manager.login_as(connecting_user)
	_save_connected_account("Instagram", identity["id"], identity.get("username"), access_token, expires_in)

	_redirect("/marketing/settings?connected=instagram")


@frappe.whitelist(allow_guest=True)
def webhook_instagram():
	"""Meta's Webhooks product — a *different* callback from the OAuth login
	one above, with its own verification handshake. We don't act on any
	event content (publishing here is one-way; we don't need comments/
	mentions/etc.), but Meta's Instagram product setup wants this endpoint
	to exist and pass verification regardless, and a real POST receiver
	should always check the signature before trusting a payload — anyone
	who finds this URL could otherwise POST forged events at it.
	"""
	request = frappe.request
	print(f"Instagram webhook event: method={request.method}, args={request.args}, headers={dict(request.headers)}")

	if request.method == "GET":
		return _verify_webhook_subscription(request)

	_verify_webhook_signature(request)
	frappe.log_error(title="Instagram webhook event", message=frappe.as_json(request.get_json(silent=True) or {}))
	return Response("OK", status=200)


def _verify_webhook_subscription(request):
	mode = request.args.get("hub.mode")
	challenge = request.args.get("hub.challenge")
	token = request.args.get("hub.verify_token")

	expected = frappe.db.get_single_value("Feed Settings", "meta_webhook_verify_token")
	if mode == "subscribe" and expected and token == expected and challenge:
		return Response(challenge, status=200, mimetype="text/plain")

	frappe.log_error(title="Instagram webhook verification failed", message=f"mode={mode} token_match={token == expected}")
	return Response("Verification failed", status=403)


def _verify_webhook_signature(request):
	signature = request.headers.get("X-Hub-Signature-256", "")
	secret = frappe.get_single("Feed Settings").get_password("meta_app_secret")
	if not secret:
		frappe.throw(_("No Meta App Secret configured"), frappe.AuthenticationError)

	expected = "sha256=" + hmac.new(secret.encode(), request.get_data(), hashlib.sha256).hexdigest()
	if not hmac.compare_digest(signature, expected):
		frappe.throw(_("Invalid webhook signature"), frappe.AuthenticationError)


def _save_connected_account(platform, external_id, label, access_token, expires_in, refresh_token=None):
	"""Shared by every platform's callback below — same upsert-by-external-id
	shape Instagram's callback already proved out."""
	existing_name = frappe.db.get_value(
		"Feed Social Account", {"platform": platform, "external_account_id": external_id}
	)
	doc = (
		frappe.get_doc("Feed Social Account", existing_name)
		if existing_name
		else frappe.new_doc("Feed Social Account")
	)
	doc.platform = platform
	doc.account_label = label
	doc.external_account_id = external_id
	doc.external_username = label
	doc.access_token = access_token
	if refresh_token:
		doc.refresh_token = refresh_token
	doc.token_expires_on = frappe.utils.add_to_date(frappe.utils.now_datetime(), seconds=expires_in)
	doc.status = "Connected"
	doc.enabled = 1
	doc.last_synced_on = frappe.utils.now_datetime()
	doc.last_error = None
	doc.save(ignore_permissions=True)
	frappe.db.commit()


# --- LinkedIn OAuth ---------------------------------------------------------
# Standard 3-legged OAuth2 + "Sign In with LinkedIn using OpenID Connect" for
# identity (the /userinfo call), "Share on LinkedIn" (w_member_social) for
# posting. Unlike Instagram/X, LinkedIn's standard user-auth flow doesn't
# hand back a refresh_token at all (that needs separate "Programmatic
# Refresh Token" partner access) — the 60-day access token just has to be
# reconnected manually once it expires.
LINKEDIN_AUTHORIZE_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
LINKEDIN_SCOPES = "openid profile w_member_social"


@frappe.whitelist()
def connect_linkedin():
	settings = frappe.get_single("Feed Settings")
	if not settings.linkedin_client_id:
		frappe.throw(_("Add a LinkedIn Client ID in Feed Settings first."))

	state = frappe.generate_hash(length=20)
	frappe.cache().set_value(f"mc_oauth_state:{state}", frappe.session.user, expires_in_sec=600)

	params = {
		"client_id": settings.linkedin_client_id,
		"redirect_uri": settings.linkedin_redirect_uri,
		"response_type": "code",
		"scope": LINKEDIN_SCOPES,
		"state": state,
	}
	_redirect(f"{LINKEDIN_AUTHORIZE_URL}?{urlencode(params)}")


@frappe.whitelist(allow_guest=True)
def oauth_callback_linkedin(code=None, state=None, error=None, error_description=None):
	settings = frappe.get_single("Feed Settings")

	def fail(message):
		frappe.log_error(title="LinkedIn OAuth failed", message=message)
		_redirect("/marketing/settings?connect_error=linkedin")

	if error or not code or not state:
		return fail(error_description or error or "Missing code/state in callback")

	cache_key = f"mc_oauth_state:{state}"
	connecting_user = frappe.cache().get_value(cache_key)
	if not connecting_user:
		return fail("OAuth state expired, missing, or already used")
	frappe.cache().delete_value(cache_key)

	try:
		token_resp = requests.post(
			LINKEDIN_TOKEN_URL,
			data={
				"grant_type": "authorization_code",
				"code": code,
				"redirect_uri": settings.linkedin_redirect_uri,
				"client_id": settings.linkedin_client_id,
				"client_secret": settings.get_password("linkedin_client_secret"),
			},
			timeout=15,
		)
		token_resp.raise_for_status()
		token_data = token_resp.json()
		access_token = token_data["access_token"]
		expires_in = token_data.get("expires_in", 60 * 24 * 60 * 60)

		identity_resp = requests.get(
			LINKEDIN_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}, timeout=15
		)
		identity_resp.raise_for_status()
		identity = identity_resp.json()
	except requests.RequestException as e:
		return fail(str(e))

	frappe.local.login_manager.login_as(connecting_user)
	_save_connected_account("LinkedIn", identity["sub"], identity.get("name"), access_token, expires_in)
	_redirect("/marketing/settings?connected=linkedin")


# --- X (Twitter) OAuth -------------------------------------------------------
# OAuth2 with PKCE — X requires it even for confidential (server-side)
# clients, unlike LinkedIn/Meta. The code_verifier has to survive between
# `connect_x` (where it's generated) and `oauth_callback_x` (where it's
# needed for the token exchange); it rides in cache next to the state token
# rather than in any cookie, for the same cross-site-redirect reason the
# state token itself doesn't ride in the session.
X_AUTHORIZE_URL = "https://x.com/i/oauth2/authorize"
X_TOKEN_URL = "https://api.x.com/2/oauth2/token"
X_USERINFO_URL = "https://api.x.com/2/users/me"
X_SCOPES = "tweet.read tweet.write users.read offline.access media.write"


def _pkce_pair():
	verifier = base64.urlsafe_b64encode(secrets.token_bytes(40)).rstrip(b"=").decode()
	challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
	return verifier, challenge


@frappe.whitelist()
def connect_x():
	settings = frappe.get_single("Feed Settings")
	if not settings.x_client_id:
		frappe.throw(_("Add an X Client ID in Feed Settings first."))

	state = frappe.generate_hash(length=20)
	verifier, challenge = _pkce_pair()
	frappe.cache().set_value(f"mc_oauth_state:{state}", frappe.session.user, expires_in_sec=600)
	frappe.cache().set_value(f"mc_oauth_pkce:{state}", verifier, expires_in_sec=600)

	params = {
		"client_id": settings.x_client_id,
		"redirect_uri": settings.x_redirect_uri,
		"response_type": "code",
		"scope": X_SCOPES,
		"state": state,
		"code_challenge": challenge,
		"code_challenge_method": "S256",
	}
	_redirect(f"{X_AUTHORIZE_URL}?{urlencode(params)}")


@frappe.whitelist(allow_guest=True)
def oauth_callback_x(code=None, state=None, error=None, error_description=None):
	settings = frappe.get_single("Feed Settings")

	def fail(message):
		frappe.log_error(title="X OAuth failed", message=message)
		_redirect("/marketing/settings?connect_error=x")

	if error or not code or not state:
		return fail(error_description or error or "Missing code/state in callback")

	connecting_user = frappe.cache().get_value(f"mc_oauth_state:{state}")
	verifier = frappe.cache().get_value(f"mc_oauth_pkce:{state}")
	if not connecting_user or not verifier:
		return fail("OAuth state expired, missing, or already used")
	frappe.cache().delete_value(f"mc_oauth_state:{state}")
	frappe.cache().delete_value(f"mc_oauth_pkce:{state}")

	try:
		token_resp = requests.post(
			X_TOKEN_URL,
			data={
				"grant_type": "authorization_code",
				"code": code,
				"redirect_uri": settings.x_redirect_uri,
				"client_id": settings.x_client_id,
				"code_verifier": verifier,
			},
			auth=(settings.x_client_id, settings.get_password("x_client_secret")),
			timeout=15,
		)
		token_resp.raise_for_status()
		token_data = token_resp.json()
		access_token = token_data["access_token"]
		refresh_token = token_data.get("refresh_token")
		expires_in = token_data.get("expires_in", 7200)

		identity_resp = requests.get(
			X_USERINFO_URL,
			headers={"Authorization": f"Bearer {access_token}"},
			params={"user.fields": "username"},
			timeout=15,
		)
		identity_resp.raise_for_status()
		identity = identity_resp.json()["data"]
	except requests.RequestException as e:
		return fail(str(e))

	frappe.local.login_manager.login_as(connecting_user)
	_save_connected_account(
		"X", identity["id"], identity.get("username"), access_token, expires_in, refresh_token=refresh_token
	)
	_redirect("/marketing/settings?connected=x")


@frappe.whitelist(allow_guest=True)
def diagnostic():
	"""Returns what code version is actually running on the server."""
	import os
	app_path = frappe.get_app_path("marketing_calendar")
	www_path = os.path.join(app_path, "www", "marketing.html")
	assets_path = os.path.join(app_path, "public", "frontend", "assets")

	html_ref = ""
	if os.path.exists(www_path):
		with open(www_path) as f:
			for line in f:
				if "index" in line and ".js" in line:
					html_ref = line.strip()
					break

	index_files = []
	if os.path.exists(assets_path):
		index_files = [f for f in os.listdir(assets_path) if "index" in f and f.endswith(".js") and not f.endswith(".map")]

	return {
		"app_path": app_path,
		"www_html_js_ref": html_ref,
		"index_js_files_in_app": index_files,
		"commit_indicator": "39dc6ce-fixed-filenames",
	}


@frappe.whitelist()
def debug_instagram_url():
	"""Returns the Instagram authorization URL without redirecting — for debugging."""
	settings = frappe.get_single("Marketing Calendar Settings")
	from urllib.parse import urlencode
	params = {
		"client_id": settings.meta_app_id,
		"redirect_uri": settings.meta_redirect_uri,
		"response_type": "code",
		"scope": INSTAGRAM_SCOPES,
		"state": "debug_test",
	}
	return {
		"auth_url": f"{INSTAGRAM_AUTHORIZE_URL}?{urlencode(params)}",
		"app_id": settings.meta_app_id,
		"redirect_uri": settings.meta_redirect_uri,
		"scope": INSTAGRAM_SCOPES,
	}
