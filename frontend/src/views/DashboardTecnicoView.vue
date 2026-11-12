<template>
  <div class="flex h-screen overflow-hidden">
    <SidebarTecnico />
    <SinoNotificacoes />
    <main class="flex-1 bg-gray-100 overflow-y-auto">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import SidebarTecnico from '@/components/SidebarTecnico.vue'
import SinoNotificacoes from '@/components/SinoNotificacoes.vue'
</script>