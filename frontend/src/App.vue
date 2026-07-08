<script setup>
import { ref } from 'vue'
import HomePage from './HomePage.vue'
import ScriptPage from './ScriptPage.vue'
import ArchivePage from './ArchivePage.vue'
import RolePage from './RolePage.vue'

const currentPage = ref('大厅')
const selectedWorldview = ref(null)

const handleNavigate = (page, worldview = null) => {
  currentPage.value = page
  selectedWorldview.value = worldview
}
</script>

<template>
  <HomePage v-if="currentPage === '大厅'" :current-page="currentPage" @navigate="handleNavigate" />
  <ScriptPage v-else-if="currentPage === '世界观'" :current-page="currentPage" @navigate="handleNavigate" />
  <ArchivePage v-else-if="currentPage === '档案'" :current-page="currentPage" @navigate="handleNavigate" />
  <RolePage v-else-if="currentPage === '角色'" :current-page="currentPage" :worldview="selectedWorldview" @navigate="handleNavigate" />
</template>

