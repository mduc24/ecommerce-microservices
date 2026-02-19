<template>
  <div class="min-h-screen bg-gray-50">
    <AppHeader />
    <router-view />
  </div>
</template>

<script setup>
import AppHeader from './components/AppHeader.vue'
</script>
