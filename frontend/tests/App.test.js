import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import router from '@/router'
import App from '@/App.vue'

// The default route renders the Dashboard (and its SummaryCards row), which
// fetches real statistics — mock the service so the shell test stays offline.
vi.mock('@/services/predictionService.js', () => ({
  predictStroke: vi.fn(),
  listPatients: vi.fn().mockResolvedValue([]),
  listAssessments: vi.fn().mockResolvedValue([]),
  checkHealth: vi.fn().mockResolvedValue(true),
}))

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