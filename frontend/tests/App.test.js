import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import router from '@/router'
import App from '@/App.vue'

describe('App', () => {
  it('mounts successfully with the router', async () => {
    await router.push('/')
    await router.isReady()
    const wrapper = mount(App, { global: { plugins: [router] } })
    expect(wrapper.exists()).toBe(true)
  })

  it('renders the dashboard shell (sidebar + content) on the default route', async () => {
    await router.push('/')
    await router.isReady()
    const wrapper = mount(App, { global: { plugins: [router] } })
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('Patient Assessment')
    expect(wrapper.text()).toContain('F5 RiskAI')
  })
})