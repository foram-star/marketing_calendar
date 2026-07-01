import { createResource, createListResource } from 'frappe-ui'

export const STAGES = ['Planning', 'In Progress', 'Review', 'Done']

export const PRIORITY_META = {
  High: { c: '#dc2626', bg: '#fee2e2' },
  Medium: { c: '#b45309', bg: '#fef3c7' },
  Low: { c: '#6b7280', bg: '#f3f4f6' },
}

export const projectsResource = createResource({
  url: 'frappe.client.get_list',
  auto: false,
  params: {
    doctype: 'Marketing Project',
    fields: ['name', 'title', 'stage', 'priority', 'project_owner', 'due_date', 'description'],
    limit_page_length: 0,
    order_by: 'due_date asc',
  },
})

export function fetchProjects() {
  return projectsResource.fetch()
}

const mutator = createListResource({ doctype: 'Marketing Project', auto: false })

export function createProject(values) {
  return mutator.insert.submit(values).then((doc) => {
    projectsResource.reload?.()
    return doc
  })
}

export function updateProject(name, values) {
  return mutator.setValue.submit({ name, ...values }).then((doc) => {
    projectsResource.reload?.()
    return doc
  })
}

export function deleteProject(name) {
  return mutator.delete.submit(name).then(() => {
    projectsResource.reload?.()
  })
}
