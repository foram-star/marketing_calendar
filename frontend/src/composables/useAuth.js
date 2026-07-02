import { ref } from 'vue'
import { call } from 'frappe-ui'

export const currentUser = ref(window.frappe?.boot?.user || window.user || null)
export const isGuest = ref(currentUser.value === 'Guest' || !currentUser.value)

export async function checkAuth() {
  try {
    const user = await call('frappe.auth.get_logged_user')
    currentUser.value = user
    isGuest.value = user === 'Guest'
    return user
  } catch {
    currentUser.value = 'Guest'
    isGuest.value = true
    return 'Guest'
  }
}

export async function login(usr, pwd) {
  const result = await call('login', { usr, pwd })
  const user = result?.full_name || usr
  currentUser.value = user
  isGuest.value = false
  return result
}

export async function signup(email, fullName) {
  return call('frappe.core.doctype.user.user.sign_up', {
    email,
    full_name: fullName,
    redirect_to: '/marketing',
  })
}

export async function logout() {
  await call('logout')
  currentUser.value = 'Guest'
  isGuest.value = true
}
