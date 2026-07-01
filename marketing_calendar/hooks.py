app_name = "marketing_calendar"
app_title = "Marketing Calendar"
app_publisher = "Foram Shah"
app_description = "Real-time marketing content calendar with multi-platform scheduling and publishing"
app_email = "foram@frappe.io"
app_license = "mit"

# Apps
# ------------------

# The Blog connector links to Blog Post/Blog Category/Blogger from that app.
required_apps = ["blog"]

# Each item in the list will be shown as an app in the apps page
# Route points straight at the standalone SPA, not a Desk workspace — there's
# no Desk-based UI for this app to land in.
add_to_apps_screen = [
	{
		"name": "marketing_calendar",
		"logo": "/assets/marketing_calendar/frontend/favicon.svg",
		"title": "Marketing Calendar",
		"route": "/marketing",
	}
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/marketing_calendar/css/marketing_calendar.css"
# app_include_js = "/assets/marketing_calendar/js/marketing_calendar.js"

# include js, css files in header of web template
# web_include_css = "/assets/marketing_calendar/css/marketing_calendar.css"
# web_include_js = "/assets/marketing_calendar/js/marketing_calendar.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "marketing_calendar/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "marketing_calendar/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# Website route rules
# --------------------
# Lets the Vue Router inside the /marketing SPA own any sub-path
# (e.g. /marketing/posts) instead of Frappe's website router 404ing on it.
website_route_rules = [
	{"from_route": "/marketing/<path:app_path>", "to_route": "marketing"},
]

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "marketing_calendar.utils.jinja_methods",
# 	"filters": "marketing_calendar.utils.jinja_filters"
# }

# Installation
# ------------

after_install = "marketing_calendar.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "marketing_calendar.uninstall.before_uninstall"
# after_uninstall = "marketing_calendar.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "marketing_calendar.utils.before_app_install"
# after_app_install = "marketing_calendar.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "marketing_calendar.utils.before_app_uninstall"
# after_app_uninstall = "marketing_calendar.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "marketing_calendar.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "marketing_calendar.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# Without this, `scheduled_on` is just a label — nothing ever actually fires
# a Scheduled post on its own. Runs every 5 minutes rather than on "all"
# (every scheduler tick) since publishing is not so time-critical that it
# needs sub-minute precision, and this keeps the check cheap.
scheduler_events = {
	"cron": {
		"*/5 * * * *": [
			"marketing_calendar.tasks.publish_due_posts",
		],
	},
}

# Testing
# -------

# before_tests = "marketing_calendar.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "marketing_calendar.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "marketing_calendar.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "marketing_calendar.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["marketing_calendar.utils.before_request"]
# after_request = ["marketing_calendar.utils.after_request"]

# Job Events
# ----------
# before_job = ["marketing_calendar.utils.before_job"]
# after_job = ["marketing_calendar.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"marketing_calendar.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

