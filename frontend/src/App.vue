<script setup>
import { computed, onMounted, ref } from 'vue'
import { authApi, clearAuth, getStoredToken, getStoredUser } from './api/client'
import HomePage from './HomePage.vue'
import ScriptPage from './ScriptPage.vue'
import ArchivePage from './ArchivePage.vue'
import RolePage from './RolePage.vue'
import GameRoomPage from './GameRoomPage.vue'
import LoginRegister from './LoginRegister.vue'

const PAGE_HOME = 'home'
const PAGE_SCRIPT = 'script'
const PAGE_ARCHIVE = 'archive'
const PAGE_ROLE = 'role'
const PAGE_ROOM = 'room'

const currentPage = ref(PAGE_HOME)
const selectedWorldview = ref(null)
const isAuthenticated = ref(Boolean(getStoredToken()))
const isBootstrapping = ref(isAuthenticated.value)
const currentUser = ref(getStoredUser())
const latestSession = ref(null)
const currentRoomId = ref(null)
const pageHistory = ref([])
const isBackButtonHidden = ref(false)

const pageComponentMap = {
  [PAGE_HOME]: HomePage,
  [PAGE_SCRIPT]: ScriptPage,
  [PAGE_ARCHIVE]: ArchivePage,
  [PAGE_ROLE]: RolePage,
  [PAGE_ROOM]: GameRoomPage
}

const pageAliasMap = {
  home: PAGE_HOME,
  大厅: PAGE_HOME,
  script: PAGE_SCRIPT,
  世界观: PAGE_SCRIPT,
  archive: PAGE_ARCHIVE,
  档案: PAGE_ARCHIVE,
  role: PAGE_ROLE,
  角色: PAGE_ROLE,
  room: PAGE_ROOM,
  房间: PAGE_ROOM
}

const activeComponent = computed(() => pageComponentMap[currentPage.value] || HomePage)
const shouldShowBackButton = computed(() =>
  isAuthenticated.value &&
  currentPage.value !== PAGE_HOME &&
  currentPage.value !== PAGE_ROOM &&
  !isBackButtonHidden.value
)

const getCurrentViewState = () => ({
  page: currentPage.value,
  worldview: selectedWorldview.value,
  latestSession: latestSession.value,
  currentRoomId: currentRoomId.value
})

const applyViewState = (state) => {
  const nextPage = state?.page || PAGE_HOME
  if (nextPage === PAGE_SCRIPT) clearRoleDrafts()

  currentPage.value = nextPage
  selectedWorldview.value = state?.worldview || null
  latestSession.value = state?.latestSession || null
  currentRoomId.value = state?.currentRoomId ?? null
  isBackButtonHidden.value = false
}

const isSameViewState = (state) =>
  state.page === currentPage.value &&
  state.worldview === selectedWorldview.value &&
  state.latestSession === latestSession.value &&
  state.currentRoomId === currentRoomId.value

const pushCurrentViewState = (nextState) => {
  if (isSameViewState(nextState)) return
  pageHistory.value.push(getCurrentViewState())
}

const handleNavigate = (page, worldview = null) => {
  const nextPage = pageAliasMap[page] || PAGE_HOME
  const nextState = {
    page: nextPage,
    worldview,
    latestSession: latestSession.value,
    currentRoomId: nextPage === PAGE_ROOM ? currentRoomId.value : null
  }

  pushCurrentViewState(nextState)
  applyViewState(nextState)
}

const handleEnterRoom = (payload) => {
  const roomId = typeof payload === 'object' && payload !== null ? payload.roomId : payload
  const nextState = {
    page: PAGE_ROOM,
    worldview: selectedWorldview.value,
    latestSession: latestSession.value,
    currentRoomId: roomId != null ? Number(roomId) : null
  }

  pushCurrentViewState(nextState)
  applyViewState(nextState)
}

const handleEnterApp = (session = {}) => {
  currentUser.value = session.user || getStoredUser()
  isAuthenticated.value = true
  isBackButtonHidden.value = false
}

const clearRoleDrafts = () => {
  if (typeof window === 'undefined') return
  const prefix = 'storyforge:role-draft:'
  ;[window.sessionStorage, window.localStorage].forEach((storage) => {
    Object.keys(storage)
      .filter((key) => key.startsWith(prefix))
      .forEach((key) => storage.removeItem(key))
  })
}

const handleLogout = () => {
  clearRoleDrafts()
  clearAuth()
  currentUser.value = null
  selectedWorldview.value = null
  latestSession.value = null
  currentRoomId.value = null
  pageHistory.value = []
  isBackButtonHidden.value = false
  currentPage.value = PAGE_HOME
  isAuthenticated.value = false
}

const handleSessionCreated = (payload) => {
  clearRoleDrafts()
  const roomId = payload?.room?.id || payload?.session?.room_id || payload?.roomId || null
  const nextState = {
    page: PAGE_ROOM,
    worldview: selectedWorldview.value,
    latestSession: payload,
    currentRoomId: roomId != null ? Number(roomId) : null
  }

  pushCurrentViewState(nextState)
  applyViewState(nextState)
}

const handleExitRoom = () => {
  const nextState = {
    page: PAGE_HOME,
    worldview: null,
    latestSession: null,
    currentRoomId: null
  }

  pageHistory.value = []
  applyViewState(nextState)
}

const goBack = () => {
  const previousState = pageHistory.value.pop()
  if (previousState) {
    applyViewState(previousState)
    return
  }

  if (isAuthenticated.value && currentPage.value !== PAGE_HOME) {
    applyViewState({
      page: PAGE_HOME,
      worldview: null,
      latestSession: latestSession.value,
      currentRoomId: null
    })
    return
  }

  if (window.history.length > 1) {
    window.history.back()
  }
}

const handleBackButtonHidden = (hidden) => {
  isBackButtonHidden.value = Boolean(hidden)
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
  <template v-else>
    <button
      v-if="shouldShowBackButton"
      class="global-back-button"
      :class="{ 'global-back-button--with-navbar': isAuthenticated }"
      type="button"
      aria-label="返回上一个界面"
      title="返回上一个界面"
      @click="goBack"
    >
      <span class="global-back-button__icon" aria-hidden="true"></span>
    </button>

    <LoginRegister v-if="!isAuthenticated" @enter="handleEnterApp" />
    <component
      :is="activeComponent"
      v-else
      :current-page="currentPage"
      :worldview="selectedWorldview"
      :current-user="currentUser"
      :latest-session="latestSession"
      :initial-room-id="currentRoomId"
      @navigate="handleNavigate"
      @enter-room="handleEnterRoom"
      @session-created="handleSessionCreated"
      @exit-room="handleExitRoom"
      @back-button-hidden="handleBackButtonHidden"
      @logout="handleLogout"
    />
  </template>
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

.global-back-button {
  position: fixed;
  top: 18px;
  left: 18px;
  z-index: 10000;
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  border: 1px solid rgba(245, 185, 91, 0.62);
  border-radius: 50%;
  background:
    linear-gradient(180deg, rgba(44, 34, 21, 0.94), rgba(10, 8, 6, 0.92));
  color: #f5d08a;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.34), inset 0 0 14px rgba(245, 185, 91, 0.1);
  cursor: pointer;
  transition: transform 0.18s ease, border-color 0.18s ease, color 0.18s ease;
}

.global-back-button--with-navbar {
  top: 18px;
  left: 34px;
}

.global-back-button:hover {
  transform: translateX(-2px);
  border-color: rgba(245, 208, 138, 0.88);
  color: #ffe0a3;
}

.global-back-button:focus-visible {
  outline: 2px solid rgba(111, 232, 255, 0.86);
  outline-offset: 3px;
}

.global-back-button__icon {
  width: 11px;
  height: 11px;
  margin-left: 4px;
  border-left: 2px solid currentColor;
  border-bottom: 2px solid currentColor;
  transform: rotate(45deg);
}

@media (max-width: 640px) {
  .global-back-button {
    top: 14px;
    left: 14px;
    width: 38px;
    height: 38px;
  }

  .global-back-button--with-navbar {
    top: 14px;
    left: 18px;
  }
}
</style>
