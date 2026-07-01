import './style.css'
import 'frappe-ui/style.css'

import { createApp } from 'vue'
import { resourcesPlugin, setConfig, frappeRequest, Button } from 'frappe-ui'

import App from './App.vue'
import router from './router'

setConfig('resourceFetcher', frappeRequest)

const app = createApp(App)
app.use(router)
app.use(resourcesPlugin)
// frappe-ui ships some internal components (e.g. ListFilter) whose own
// templates reference <Button> without importing it locally — within
// frappe-ui's own desk build that resolves via global auto-import, but a
// plain Vite consumer needs it registered explicitly or it silently renders
// an empty native <button>.
app.component('Button', Button)
app.mount('#app')
