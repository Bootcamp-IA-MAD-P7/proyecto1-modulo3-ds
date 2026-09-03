<script setup>
/**
 * App shell used by the dashboard and all internal (sidebar) views.
 * Composes AppSidebar + Header + a routed content slot.
 */
import { ref } from 'vue'
import AppSidebar from '@/components/AppSidebar.vue'
import Header from '@/components/Header.vue'

const sidebarOpen = ref(false)
</script>

<template>
  <div class="shell">
    <AppSidebar :open="sidebarOpen" @close="sidebarOpen = false" />

    <div class="shell__main">
      <Header @toggle-sidebar="sidebarOpen = true" />
      <main class="shell__content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
.shell {
  position: relative;
  min-height: 100vh;
  background: var(--color-canvas);
}

.shell::before {
  /* Subtle navy/yellow decorative accents, very restrained. */
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background:
    radial-gradient(circle at 82% 4%, rgba(244, 201, 93, 0.1), transparent 34%),
    radial-gradient(circle at 14% 96%, rgba(7, 20, 38, 0.05), transparent 30%);
}

.shell__main {
  position: relative;
  z-index: 1;
  min-height: 100vh;
  margin-left: var(--sidebar-width);
  display: flex;
  flex-direction: column;
}

.shell__content {
  flex: 1;
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
  padding: 30px 32px 56px;
}

@media (max-width: 1080px) {
  .shell__main {
    margin-left: 0;
  }
}

@media (max-width: 640px) {
  .shell__content {
    padding: 22px 16px 44px;
  }
}
</style>