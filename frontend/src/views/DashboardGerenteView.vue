<template>
  <div class="flex h-screen overflow-hidden">
    <SidebarGerente />
    <SinoNotificacoes />
    <main class="flex-1 bg-gray-100 overflow-y-auto">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import SidebarGerente from '@/components/SidebarGerente.vue'
import SinoNotificacoes from '@/components/SinoNotificacoes.vue'
</script>