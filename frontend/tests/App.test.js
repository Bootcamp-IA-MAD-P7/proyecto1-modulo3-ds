import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import App from '@/App.vue'
import Dashboard from '@/views/Dashboard.vue'

function makeRouter() {
  return createRouter({
    history: createWebHistory('/'),
    routes: [{ path: '/', name: 'dashboard', component: Dashboard }],
  })
}

describe('App', () => {
  it('mounts successfully with the router', async () => {
    const router = makeRouter()
    router.push('/')
    await router.isReady()
    const wrapper = mount(App, { global: { plugins: [router] } })
    expect(wrapper.exists()).toBe(true)
  })

  it('renders the dashboard on the default route', async () => {
    const router = makeRouter()
    router.push('/')
    await router.isReady()
    const wrapper = mount(App, { global: { plugins: [router] } })
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('Patient Assessment')
    expect(wrapper.text()).toContain('F5 RiskAI')
  })
})