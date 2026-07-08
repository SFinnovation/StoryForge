<script setup>
import { computed, ref } from 'vue'
import HomePage from './HomePage.vue'
import ScriptPage from './ScriptPage.vue'
import ArchivePage from './ArchivePage.vue'
import RolePage from './RolePage.vue'
import LoginRegister from './LoginRegister.vue'

const PAGE_HOME = 'home'
const PAGE_SCRIPT = 'script'
const PAGE_ARCHIVE = 'archive'
const PAGE_ROLE = 'role'

const currentPage = ref(PAGE_HOME)
const selectedWorldview = ref(null)
const isAuthenticated = ref(false)

const pageComponentMap = {
  [PAGE_HOME]: HomePage,
  [PAGE_SCRIPT]: ScriptPage,
  [PAGE_ARCHIVE]: ArchivePage,
  [PAGE_ROLE]: RolePage
}

const pageAliasMap = {
  home: PAGE_HOME,
  大厅: PAGE_HOME,
  script: PAGE_SCRIPT,
  世界观: PAGE_SCRIPT,
  archive: PAGE_ARCHIVE,
  档案: PAGE_ARCHIVE,
  role: PAGE_ROLE,
  角色: PAGE_ROLE
}

const activeComponent = computed(() => pageComponentMap[currentPage.value] || HomePage)

const handleNavigate = (page, worldview = null) => {
  currentPage.value = pageAliasMap[page] || PAGE_HOME
  selectedWorldview.value = worldview
}

const handleEnterApp = () => {
  isAuthenticated.value = true
}
</script>

<template>
  <LoginRegister v-if="!isAuthenticated" @enter="handleEnterApp" />
  <component
    :is="activeComponent"
    v-else
    :current-page="currentPage"
    :worldview="selectedWorldview"
    @navigate="handleNavigate"
  />
</template>
