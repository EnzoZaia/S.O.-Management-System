<template>
  <div class="flex h-screen overflow-hidden">
    <SidebarGestor />
    <SinoNotificacoes />
    <main class="flex-1 bg-gray-100 overflow-y-auto">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import SidebarGestor from '@/components/SidebarGestor.vue'
import SinoNotificacoes from '@/components/SinoNotificacoes.vue'
</script>