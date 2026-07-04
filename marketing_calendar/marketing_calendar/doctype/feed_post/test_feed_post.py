# Copyright (c) 2026, Foram Shah and Contributors
# See license.txt

# import frappe
from frappe.tests import IntegrationTestCase


# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]



class IntegrationTestMarketingPost(IntegrationTestCase):
	"""
	Integration tests for MarketingPost.
	Use this class for testing interactions between multiple components.
	"""

	pass
