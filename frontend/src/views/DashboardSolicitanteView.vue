<template>
  <div class="flex h-screen overflow-hidden">
    <SidebarSolicitante />
    <SinoNotificacoes />
    <main class="flex-1 bg-gray-100 overflow-y-auto">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import SidebarSolicitante from '@/components/SidebarSolicitante.vue'
import SinoNotificacoes from '@/components/SinoNotificacoes.vue'
</script>