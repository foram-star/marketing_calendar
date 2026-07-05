import { createResource } from 'frappe-ui'

export const socialAccountsResource = createResource({
  url: 'frappe.client.get_list',
  auto: false,
  params: {
    doctype: 'Feed Social Account',
    fields: ['name', 'platform', 'account_label', 'enabled', 'status', 'external_username', 'token_expires_on', 'last_synced_on', 'last_error'],
    limit_page_length: 0,
  },
})

export function fetchSocialAccounts() {
  return socialAccountsResource.fetch()
}

export function accountsForPlatform(platformName) {
  return (socialAccountsResource.data || []).filter((a) => a.platform === platformName)
}
