<script setup>
import { computed, onMounted, ref } from 'vue'
import { authApi, clearAuth, getStoredToken, getStoredUser } from './api/client'
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
const isAuthenticated = ref(Boolean(getStoredToken()))
const isBootstrapping = ref(isAuthenticated.value)
const currentUser = ref(getStoredUser())
const latestSession = ref(null)

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

const handleEnterApp = (session = {}) => {
  currentUser.value = session.user || getStoredUser()
  isAuthenticated.value = true
}

const handleLogout = () => {
  clearAuth()
  currentUser.value = null
  selectedWorldview.value = null
  latestSession.value = null
  currentPage.value = PAGE_HOME
  isAuthenticated.value = false
}

const handleSessionCreated = (payload) => {
  latestSession.value = payload
  currentPage.value = PAGE_ARCHIVE
}

onMounted(async () => {
  if (!getStoredToken()) {
    isBootstrapping.value = false
    return
  }

  try {
    currentUser.value = await authApi.me()
    isAuthenticated.value = true
  } catch {
    handleLogout()
  } finally {
    isBootstrapping.value = false
  }
})
</script>

<template>
  <div v-if="isBootstrapping" class="app-loading">正在连接灵境档案...</div>
  <LoginRegister v-else-if="!isAuthenticated" @enter="handleEnterApp" />
  <component
    :is="activeComponent"
    v-else
    :current-page="currentPage"
    :worldview="selectedWorldview"
    :current-user="currentUser"
    :latest-session="latestSession"
    @navigate="handleNavigate"
    @session-created="handleSessionCreated"
    @logout="handleLogout"
  />
</template>

<style scoped>
.app-loading {
  min-height: 100vh;
  display: grid;
  place-items: center;
  background: #090806;
  color: #f5b95b;
  font-size: 16px;
}
</style>
