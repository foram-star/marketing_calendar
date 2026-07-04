import { createDocumentResource } from 'frappe-ui'

// Single doctype — its own name is the document name. `.save` round-trips
// the whole `doc` object back through `frappe.client.set_value`, which is
// what makes editing Password fields safe here: a field we never touched
// still holds whatever masked "*****" placeholder the GET returned, and
// Frappe's own dummy-password check skips re-encrypting an unchanged mask —
// it only overwrites the real secret if we hand it back something else.
export function useCalendarSettings() {
  return createDocumentResource({
    doctype: 'Feed Settings',
    name: 'Feed Settings',
    auto: true,
  })
}
