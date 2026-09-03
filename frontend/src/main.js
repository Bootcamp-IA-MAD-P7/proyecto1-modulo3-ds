import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './assets/main.css'
import { initThemeAndLanguage } from './store.js'

// Apply persisted theme + language to <html> before the app mounts.
initThemeAndLanguage()

const app = createApp(App)
app.use(router)
app.mount('#app')