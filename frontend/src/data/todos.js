import { createResource, createListResource } from 'frappe-ui'

export const todosResource = createResource({
  url: 'frappe.client.get_list',
  auto: false,
  params: {
    doctype: 'Feed Task',
    fields: ['name', 'title', 'done', 'marketing_project', 'assigned_to', 'description'],
    limit_page_length: 0,
    order_by: 'creation desc',
  },
})

export function fetchTodos() {
  return todosResource.fetch()
}

const mutator = createListResource({ doctype: 'Feed Task', auto: false })

export function createTodo(values) {
  return mutator.insert.submit(values).then((doc) => {
    todosResource.reload?.()
    return doc
  })
}

export function updateTodo(name, values) {
  return mutator.setValue.submit({ name, ...values }).then((doc) => {
    todosResource.reload?.()
    return doc
  })
}

export function deleteTodo(name) {
  return mutator.delete.submit(name).then(() => {
    todosResource.reload?.()
  })
}
