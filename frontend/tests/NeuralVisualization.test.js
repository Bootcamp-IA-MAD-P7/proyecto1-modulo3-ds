import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import NeuralVisualization from '@/components/NeuralVisualization.vue'

describe('NeuralVisualization (Issue #037)', () => {
  it('renders the placeholder', () => {
    const wrapper = mount(NeuralVisualization)
    expect(wrapper.text()).toContain('Neural Visualization')
    expect(wrapper.text()).toContain('coming soon')
  })

  it('does NOT mount a real 3D model or external canvas/three container', () => {
    const wrapper = mount(NeuralVisualization)
    // No <canvas>, no three.js-style container, just abstract SVG/CSS art.
    expect(wrapper.find('canvas').exists()).toBe(false)
    expect(wrapper.html()).not.toContain('three.js')
    expect(wrapper.html()).not.toContain('webgl')
  })

  it('includes an abstract SVG placeholder (future integration point to swap)', () => {
    const wrapper = mount(NeuralVisualization)
    expect(wrapper.find('svg').exists()).toBe(true)
  })
})