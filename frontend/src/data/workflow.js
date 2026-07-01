import { reactive } from 'vue'
import { call } from 'frappe-ui'

// Wraps Frappe's own workflow engine endpoints (frappe/model/workflow.py) —
// the same ones Desk's form toolbar uses for its workflow action buttons,
// just rendered by our own SPA instead of Desk's form JS.
export function useWorkflow(doctype, getName) {
  const state = reactive({ transitions: [], loading: false })

  async function refresh() {
    const name = getName()
    if (!name) {
      state.transitions = []
      return
    }
    state.loading = true
    try {
      const transitions = (await call('frappe.model.workflow.get_transitions', {
        doc: { doctype, name },
      })) || []
      // Multiple roles can be allowed the same (state, action, next_state) —
      // each gets its own Workflow Transition row, but the UI only needs one button.
      const seen = new Set()
      state.transitions = transitions.filter((t) => {
        if (seen.has(t.action)) return false
        seen.add(t.action)
        return true
      })
    } finally {
      state.loading = false
    }
  }

  async function applyAction(action) {
    const name = getName()
    const updated = await call('frappe.model.workflow.apply_workflow', { doc: { doctype, name }, action })
    await refresh()
    return updated
  }

  return { state, refresh, applyAction }
}
