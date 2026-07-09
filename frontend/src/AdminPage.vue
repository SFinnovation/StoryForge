<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { adminApi } from './api/client'
import adminBackground from '../背景/系统主界面.png'

const props = defineProps({
  currentUser: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['logout'])

const REFRESH_INTERVAL_MS = 10_000

const isLoading = ref(false)
const statusMessage = ref('')
const summary = ref({})
const worlds = ref([])
const users = ref([])
const sessions = ref([])
const selectedUser = ref(null)
const selectedUserSessions = ref([])
const openWorldIds = ref(new Set())
const openUserIds = ref(new Set())
let refreshTimer = null

const adminName = computed(() => props.currentUser?.nickname || props.currentUser?.username || 'Admin_Root')

const summaryCards = computed(() => [
  { label: '今日新增会话', value: summary.value.today_sessions ?? 0, note: '来自 game_sessions.started_at' },
  { label: '实时活跃房间', value: summary.value.active_rooms ?? 0, note: `${summary.value.rooms ?? 0} 个房间总数` },
  { label: '累计历史会话', value: summary.value.sessions ?? 0, note: `${summary.value.active_sessions ?? 0} 个进行中` },
  {
    label: '消息与行动',
    value: Number(summary.value.session_messages ?? 0) + Number(summary.value.room_messages ?? 0),
    note: `${summary.value.pending_actions ?? 0} 个待处理行动`
  },
  { label: '用户档案', value: summary.value.users ?? 0, note: `${summary.value.banned_users ?? 0} 个封禁账号` },
  { label: '世界观 / 模组', value: `${summary.value.worlds ?? 0}/${summary.value.modules ?? 0}`, note: '仅统计已启用内容' }
])

const chartItems = computed(() => summary.value.world_activity || [])
const chartMax = computed(() => Math.max(...chartItems.value.map((item) => Number(item.active_room_count || 0)), 1))
const hasChartData = computed(() => chartItems.value.some((item) => Number(item.active_room_count || 0) > 0))

const loadAdminData = async ({ silent = false } = {}) => {
  if (!silent) {
    isLoading.value = true
    statusMessage.value = ''
  }

  try {
    const [summaryData, worldsData, usersData, sessionsData] = await Promise.all([
      adminApi.summary(),
      adminApi.worlds({ includeDisabled: true }),
      adminApi.users({ limit: 100 }),
      adminApi.sessions({ limit: 100 })
    ])

    summary.value = summaryData || {}
    worlds.value = worldsData?.items || []
    users.value = usersData?.items || []
    sessions.value = sessionsData?.items || []

    if (openWorldIds.value.size === 0 && worlds.value.length > 0) {
      openWorldIds.value = new Set([worlds.value[0].id])
    }

    if (selectedUser.value) {
      await refreshSelectedUserSessions(selectedUser.value, { silent: true })
    }
  } catch (error) {
    statusMessage.value = error?.message || '管理员实时数据同步失败，请稍后重试。'
  } finally {
    if (!silent) isLoading.value = false
  }
}

const runAdminAction = async (action, successText) => {
  if (isLoading.value) return
  isLoading.value = true
  statusMessage.value = ''
  try {
    await action()
    await loadAdminData({ silent: true })
    statusMessage.value = successText
  } catch (error) {
    statusMessage.value = error?.message || '操作失败，请稍后重试。'
  } finally {
    isLoading.value = false
  }
}

const toggleWorld = (worldId) => {
  const next = new Set(openWorldIds.value)
  if (next.has(worldId)) {
    next.delete(worldId)
  } else {
    next.add(worldId)
  }
  openWorldIds.value = next
}

const toggleUser = (userId) => {
  const next = new Set(openUserIds.value)
  if (next.has(userId)) {
    next.delete(userId)
  } else {
    next.add(userId)
  }
  openUserIds.value = next
}

const createWorld = async () => {
  const name = window.prompt('请输入新世界观名称')
  if (!name?.trim()) return

  await runAdminAction(
    () =>
      adminApi.createWorld({
        name: name.trim(),
        type: 'custom',
        description: '',
        opening_prompt: '',
        rule_style: 'custom',
        difficulty: 'normal',
        is_public: true,
        modules: []
      }),
    `世界观「${name.trim()}」已上架。`
  )
}

const toggleWorldStatus = async (world) => {
  if (!world?.id) return
  const nextEnabled = !world.is_enabled
  await runAdminAction(
    () => (nextEnabled ? adminApi.enableWorld(world.id) : adminApi.deleteWorld(world.id)),
    `世界观「${world.name}」已${nextEnabled ? '启用' : '停用'}。`
  )
}

const createModule = async (world) => {
  if (!world?.id) return
  const name = window.prompt(`请输入「${world.name}」下的新模组名称`)
  if (!name?.trim()) return

  await runAdminAction(
    () => adminApi.createModule(world.id, { name: name.trim(), description: '' }),
    `模组「${name.trim()}」已加入「${world.name}」。`
  )
}

const toggleModuleStatus = async (module) => {
  if (!module?.id) return
  const nextEnabled = !module.is_enabled
  await runAdminAction(
    () => (nextEnabled ? adminApi.enableModule(module.id) : adminApi.deleteModule(module.id)),
    `模组「${module.name}」已${nextEnabled ? '启用' : '停用'}。`
  )
}

const toggleUserStatus = async (user) => {
  if (!user?.id || user.role === 'admin') return
  const nextActive = user.status === 'banned'
  await runAdminAction(
    () =>
      nextActive
        ? adminApi.unbanUser(user.id, { reason: '管理员后台解封' })
        : adminApi.banUser(user.id, { reason: '管理员后台封禁' }),
    `用户「${user.nickname || user.username}」已${nextActive ? '解封' : '封禁'}。`
  )
}

const refreshSelectedUserSessions = async (user, { silent = false } = {}) => {
  if (!user?.id) return
  if (!silent) statusMessage.value = ''
  selectedUser.value = user
  try {
    const result = await adminApi.sessions({ owner_id: user.id, limit: 100 })
    selectedUserSessions.value = result?.items || []
  } catch (error) {
    statusMessage.value = error?.message || '会话记录获取失败。'
  }
}

const dissolveSession = async (session) => {
  if (!session?.id) return
  await runAdminAction(
    () => adminApi.dissolveSession(session.id, { reason: '管理员后台强制归档' }),
    `会话 #${session.id} 已归档。`
  )
  if (selectedUser.value) {
    await refreshSelectedUserSessions(selectedUser.value, { silent: true })
  }
}

const formatDate = (value) => {
  if (!value) return '未知时间'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return date.toLocaleString('zh-CN', { hour12: false })
}

const statusLabel = (status) => {
  const labels = {
    active: '正常',
    banned: '封禁',
    waiting: '等待中',
    playing: '进行中',
    paused: '暂停',
    finished: '已结束',
    archived: '已归档'
  }
  return labels[status] || status || '未知'
}

onMounted(async () => {
  await loadAdminData()
  refreshTimer = window.setInterval(() => loadAdminData({ silent: true }), REFRESH_INTERVAL_MS)
})

onUnmounted(() => {
  if (refreshTimer) window.clearInterval(refreshTimer)
})
</script>

<template>
  <div class="admin-page">
    <img class="admin-backdrop" :src="adminBackground" alt="" />
    <div class="admin-shade" aria-hidden="true"></div>

    <header class="admin-navbar">
      <div class="logo-area">StoryForge <span>| 后台管理</span></div>
      <div class="admin-area">
        <div class="admin-info">管理员：{{ adminName }}</div>
        <button class="logout-btn" type="button" title="登出" aria-label="登出" @click="emit('logout')">⏻</button>
      </div>
    </header>

    <main class="admin-container">
      <p v-if="statusMessage" class="status-line">{{ statusMessage }}</p>

      <section class="status-grid">
        <div class="panel">
          <h2 class="section-title">热门世界观（活跃房间数）</h2>
          <div v-if="hasChartData" class="bar-chart-container">
            <div v-for="item in chartItems" :key="item.id" class="bar-col">
              <span class="bar-val">{{ item.active_room_count }}</span>
              <div class="bar-track">
                <div
                  class="bar-fill"
                  :style="{ height: `${Math.max(8, Math.round((Number(item.active_room_count || 0) / chartMax) * 100))}%` }"
                ></div>
              </div>
              <span class="bar-label">{{ item.name }}</span>
            </div>
          </div>
          <div v-else class="empty-panel">暂无活跃房间。</div>
        </div>

        <div class="panel">
          <h2 class="section-title">实时会话监控记录</h2>
          <div class="data-dashboard">
            <div v-for="card in summaryCards" :key="card.label" class="data-card">
              <div class="num">{{ card.value }}</div>
              <div class="desc">{{ card.label }}</div>
              <div class="sub-desc">{{ card.note }}</div>
            </div>
          </div>
        </div>
      </section>

      <section class="db-section">
        <div class="db-row">
          <div class="db-label-area">
            <div class="label-icon">※</div>
            <h3>世界观 / 模组库</h3>
          </div>
          <div class="db-content-area">
            <div class="toolbar">
              <button class="btn-outline-gold" type="button" @click="loadAdminData()" :disabled="isLoading">
                {{ isLoading ? '同步中' : '刷新数据' }}
              </button>
              <button class="btn-outline-gold" type="button" @click="createWorld" :disabled="isLoading">上架世界观</button>
            </div>

            <div class="tree-scroll">
              <ul class="tree-list">
                <li v-for="world in worlds" :key="world.id">
                  <div class="tree-item worldview-item" :class="{ disabled: !world.is_enabled }" @click="toggleWorld(world.id)">
                    <span class="toggle-icon" :class="{ open: openWorldIds.has(world.id) }">›</span>
                    <span class="folder-icon">◎</span>
                    <strong>{{ world.name }}</strong>
                    <span class="world-meta">
                      {{ world.type }} · 房间 {{ world.active_room_count }}/{{ world.room_count }} · 会话 {{ world.session_count }}
                    </span>
                    <div class="worldview-actions" @click.stop>
                      <button class="btn-micro-gold" type="button" @click="createModule(world)" :disabled="isLoading || !world.is_enabled">
                        新增模组
                      </button>
                      <button class="btn-micro-gold" type="button" @click="toggleWorldStatus(world)" :disabled="isLoading">
                        {{ world.is_enabled ? '停用世界观' : '启用世界观' }}
                      </button>
                    </div>
                  </div>

                  <ul v-if="openWorldIds.has(world.id)" class="nested-tree active">
                    <li>
                      <div class="tree-item">
                        <span class="sub-icon">▣</span>
                        规则风格：{{ world.rule_style || 'custom' }}
                      </div>
                    </li>
                    <li v-if="!world.modules?.length">
                      <div class="tree-item empty-item">暂无模组记录。</div>
                    </li>
                    <li v-for="module in world.modules" :key="module.id">
                      <div class="tree-item" :class="{ disabled: !module.is_enabled }">
                        <span class="sub-icon">▤</span>
                        模组：{{ module.name }}
                        <div class="module-status-group">
                          <span class="status-text" :class="module.is_enabled ? 'running' : 'stopped'">
                            {{ module.is_enabled ? '运行中' : '已停用' }}
                          </span>
                          <button class="btn-status-action" type="button" :disabled="isLoading" @click.stop="toggleModuleStatus(module)">
                            {{ module.is_enabled ? '停用' : '启用' }}
                          </button>
                        </div>
                      </div>
                    </li>
                  </ul>
                </li>
              </ul>
            </div>
          </div>
        </div>

        <div class="db-row compact-row">
          <div class="db-label-area">
            <div class="label-icon">◇</div>
            <h3>用户档案管理</h3>
          </div>
          <div class="db-content-area">
            <div class="hint-line">用户、状态与会话记录均来自后端管理员接口。</div>
            <div class="tree-scroll">
              <ul class="tree-list">
                <li v-for="user in users" :key="user.id">
                  <div class="tree-item" @click="toggleUser(user.id)">
                    <span class="folder-icon">●</span>
                    {{ user.nickname || user.username }}
                    <span class="user-meta">ID: {{ user.id }} · {{ user.role }} · {{ statusLabel(user.status) }}</span>
                  </div>
                  <div class="expand-actions" :class="{ active: openUserIds.has(user.id) }">
                    <button
                      class="btn-danger"
                      type="button"
                      :disabled="user.role === 'admin' || isLoading"
                      @click="toggleUserStatus(user)"
                    >
                      {{ user.status === 'banned' ? '账号解封' : '账号封禁' }}
                    </button>
                    <button class="btn-gold" type="button" @click="refreshSelectedUserSessions(user)">访问会话记录</button>
                  </div>
                </li>
              </ul>
            </div>

            <div v-if="selectedUser" class="session-strip">
              <h4>{{ selectedUser.nickname || selectedUser.username }} 的会话记录</h4>
              <p v-if="selectedUserSessions.length === 0">暂无会话记录。</p>
              <ul v-else>
                <li v-for="session in selectedUserSessions" :key="session.id">
                  <span>#{{ session.id }} {{ session.title || session.world_name || '未命名会话' }}</span>
                  <time>{{ formatDate(session.started_at) }}</time>
                  <strong>{{ statusLabel(session.status) }}</strong>
                  <button
                    class="btn-danger mini"
                    type="button"
                    :disabled="session.status === 'archived' || isLoading"
                    @click="dissolveSession(session)"
                  >
                    归档
                  </button>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.admin-page {
  --bg-dark: #0b0a09;
  --panel-bg: rgba(18, 14, 12, 0.78);
  --border-gold: #8b7355;
  --border-light: rgba(212, 184, 134, 0.4);
  --text-gold: #d4b886;
  --text-light: #e0d6c8;
  --text-dim: #8b7d6b;
  --success-green: #4ade80;
  --danger-red: #ff4d4f;
  position: relative;
  min-height: 100vh;
  overflow-x: hidden;
  background: var(--bg-dark);
  color: var(--text-light);
  font-family: "Noto Serif SC", "Songti SC", serif;
}

.admin-backdrop,
.admin-shade {
  position: fixed;
  inset: 0;
}

.admin-backdrop {
  width: 100%;
  height: 100%;
  object-fit: cover;
  filter: brightness(0.42) saturate(0.9);
}

.admin-shade {
  background:
    linear-gradient(180deg, rgba(0, 0, 0, 0.55), rgba(5, 4, 4, 0.9)),
    radial-gradient(circle at 78% 18%, rgba(103, 213, 245, 0.14), transparent 28%);
}

.admin-navbar {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 15px 30px;
  border-bottom: 1px solid rgba(139, 115, 85, 0.3);
  background: rgba(8, 6, 5, 0.95);
}

.logo-area {
  color: var(--text-gold);
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 2px;
}

.logo-area span {
  margin-left: 8px;
  color: var(--text-dim);
  font-size: 16px;
  font-weight: 400;
}

.admin-area {
  display: flex;
  align-items: center;
  gap: 15px;
}

.admin-info {
  padding: 8px 18px;
  border: 1px solid rgba(139, 115, 85, 0.6);
  border-radius: 4px;
  color: var(--text-light);
  font-size: 15px;
}

.logout-btn {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border: 1px solid rgba(255, 71, 71, 0.4);
  border-radius: 4px;
  background: transparent;
  color: var(--danger-red);
  cursor: pointer;
}

.admin-container {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 25px;
  padding: 30px;
}

.status-line,
.empty-panel {
  margin: 0;
  padding: 12px 16px;
  border: 1px solid rgba(103, 213, 245, 0.34);
  border-radius: 6px;
  background: rgba(8, 20, 24, 0.78);
  color: #bdefff;
}

.empty-panel {
  min-height: 170px;
  display: grid;
  place-items: center;
  color: var(--text-dim);
}

.status-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 25px;
}

.panel,
.db-row {
  border: 1px solid var(--border-light);
  border-radius: 8px;
  background: var(--panel-bg);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.52), inset 0 0 15px rgba(212, 184, 134, 0.05);
  backdrop-filter: blur(12px);
}

.panel {
  padding: 25px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0 0 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(139, 115, 85, 0.3);
  color: var(--text-gold);
  font-size: 16px;
}

.section-title::before {
  content: "";
  width: 4px;
  height: 16px;
  border-radius: 2px;
  background: var(--text-gold);
}

.bar-chart-container {
  display: flex;
  align-items: stretch;
  justify-content: space-around;
  min-height: 190px;
  gap: 15px;
  padding-top: 20px;
}

.bar-col {
  flex: 1;
  min-height: 190px;
  display: grid;
  grid-template-rows: auto minmax(96px, 1fr) minmax(28px, auto);
  align-items: center;
  justify-items: center;
  min-width: 0;
}

.bar-val {
  margin-bottom: 7px;
  color: var(--text-gold);
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.2;
}

.bar-track {
  width: 30px;
  height: 100%;
  display: flex;
  align-items: flex-end;
  border: 1px solid rgba(139, 115, 85, 0.2);
  border-bottom: 0;
  border-radius: 4px 4px 0 0;
  background: rgba(0, 0, 0, 0.4);
}

.bar-fill {
  width: 100%;
  border-radius: 3px 3px 0 0;
  background: linear-gradient(to top, rgba(139, 115, 85, 0.42), var(--text-gold));
  box-shadow: 0 -2px 10px rgba(212, 184, 134, 0.32);
}

.bar-label {
  width: 100%;
  min-height: 28px;
  margin-top: 10px;
  overflow: hidden;
  color: var(--text-light);
  font-size: 12px;
  line-height: 1.45;
  padding-bottom: 2px;
  text-align: center;
  text-overflow: ellipsis;
  overflow-wrap: anywhere;
  white-space: normal;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.data-dashboard {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.data-card {
  min-height: 78px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(139, 115, 85, 0.2);
  border-radius: 6px;
  background: rgba(10, 8, 7, 0.62);
  padding: 14px;
}

.num {
  color: var(--text-gold);
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 27px;
  font-weight: 700;
}

.desc {
  margin-top: 7px;
  color: var(--text-dim);
  font-size: 13px;
}

.sub-desc {
  margin-top: 4px;
  color: var(--success-green);
  font-size: 11px;
}

.db-section {
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.db-row {
  display: flex;
  min-height: 380px;
  overflow: hidden;
}

.compact-row {
  min-height: 280px;
}

.db-label-area {
  width: 200px;
  flex: 0 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 15px;
  border-right: 1px solid rgba(139, 115, 85, 0.3);
  background: rgba(15, 12, 10, 0.82);
  padding: 20px;
  text-align: center;
}

.label-icon {
  color: var(--text-gold);
  font-size: 32px;
}

.db-label-area h3 {
  margin: 0;
  color: var(--text-light);
  font-size: 15px;
}

.db-content-area {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 20px;
}

.toolbar,
.worldview-actions,
.module-status-group,
.expand-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toolbar {
  flex-wrap: wrap;
  margin-bottom: 20px;
}

button {
  font: inherit;
}

button:disabled {
  cursor: not-allowed;
  opacity: 0.52;
}

.btn-outline-gold,
.btn-micro-gold,
.btn-status-action,
.btn-danger,
.btn-gold {
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease, color 0.2s ease;
}

.btn-outline-gold {
  padding: 8px 18px;
  border: 1px solid rgba(212, 184, 134, 0.5);
  background: transparent;
  color: var(--text-gold);
}

.btn-micro-gold,
.btn-status-action,
.btn-gold {
  border: 1px solid rgba(139, 115, 85, 0.4);
  background: rgba(139, 115, 85, 0.1);
  color: var(--text-gold);
}

.btn-outline-gold:hover:not(:disabled),
.btn-micro-gold:hover:not(:disabled),
.btn-status-action:hover:not(:disabled),
.btn-gold:hover:not(:disabled) {
  border-color: var(--text-gold);
  background: rgba(212, 184, 134, 0.12);
}

.tree-scroll {
  flex: 1;
  overflow-y: auto;
  padding-right: 10px;
}

.tree-list {
  margin: 0;
  padding: 0;
  list-style: none;
  color: var(--text-light);
  font-size: 14px;
}

.tree-item {
  width: 100%;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 38px;
  padding: 8px 10px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s ease;
}

.tree-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.tree-item.disabled {
  opacity: 0.58;
}

.worldview-item {
  margin-bottom: 5px;
  border: 1px solid rgba(139, 115, 85, 0.1);
  background: rgba(255, 255, 255, 0.03);
  font-weight: 700;
}

.toggle-icon {
  width: 12px;
  color: var(--text-dim);
  font-size: 20px;
  line-height: 1;
  transition: transform 0.2s ease;
}

.toggle-icon.open {
  transform: rotate(90deg);
}

.folder-icon {
  color: var(--text-gold);
}

.sub-icon {
  color: var(--text-dim);
  font-size: 13px;
}

.world-meta,
.user-meta {
  margin-left: auto;
  color: var(--text-dim);
  font-size: 12px;
  font-weight: 400;
}

.worldview-actions,
.module-status-group {
  margin-left: auto;
}

.btn-micro-gold,
.btn-status-action,
.btn-danger,
.btn-gold {
  padding: 5px 10px;
  font-size: 12px;
}

.nested-tree {
  display: none;
  margin: 5px 0 15px 15px;
  padding-left: 28px;
  border-left: 1px dashed rgba(139, 115, 85, 0.4);
  list-style: none;
}

.nested-tree.active {
  display: block;
}

.empty-item {
  color: var(--text-dim);
  cursor: default;
}

.status-text {
  font-size: 14px;
}

.status-text.running {
  color: var(--success-green);
}

.status-text.stopped {
  color: var(--text-dim);
}

.hint-line {
  margin-bottom: 15px;
  color: var(--text-dim);
  font-size: 13px;
}

.expand-actions {
  display: none;
  margin: 5px 0 8px 25px;
  padding: 10px;
  border: 1px solid rgba(139, 115, 85, 0.2);
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.3);
}

.expand-actions.active {
  display: flex;
}

.btn-danger {
  border: 1px solid var(--danger-red);
  background: rgba(255, 71, 71, 0.1);
  color: var(--danger-red);
}

.btn-danger:hover:not(:disabled) {
  background: rgba(255, 77, 79, 0.12);
}

.btn-danger.mini {
  padding: 4px 8px;
}

.session-strip {
  margin-top: 14px;
  border-top: 1px solid rgba(139, 115, 85, 0.22);
  padding-top: 12px;
}

.session-strip h4,
.session-strip p {
  margin: 0 0 8px;
}

.session-strip ul {
  margin: 0;
  padding: 0;
  list-style: none;
}

.session-strip li {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto auto;
  align-items: center;
  gap: 12px;
  padding: 6px 0;
  color: var(--text-dim);
  font-size: 13px;
}

.session-strip span {
  min-width: 0;
  overflow: hidden;
  color: var(--text-light);
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 900px) {
  .admin-navbar,
  .admin-area,
  .db-row {
    align-items: stretch;
    flex-direction: column;
  }

  .status-grid,
  .data-dashboard {
    grid-template-columns: 1fr;
  }

  .db-label-area {
    width: 100%;
    border-right: 0;
    border-bottom: 1px solid rgba(139, 115, 85, 0.3);
  }

  .worldview-actions,
  .module-status-group {
    width: 100%;
    margin-left: 0;
    justify-content: flex-start;
  }

  .tree-item {
    flex-wrap: wrap;
  }

  .session-strip li {
    grid-template-columns: 1fr;
  }
}
</style>
