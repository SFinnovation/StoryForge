<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { charactersApi, roomsApi, sessionsApi, worldsApi } from './api/client'
import JoinRoomModal from './JoinRoomModal.vue'
import AppNavbar from './components/AppNavbar.vue'
import lobbyBackground from '../背景/大厅界面.png'
import productIcon from '../图标/产品图标.png'
import cubeIcon from '../图标/魔方.png'
import gateIcon from '../图标/魔法门.png'
import orbIcon from '../图标/魔法球.png'
import archiveIcon from '../图标/档案.png'
import goblinCover from '../游戏种类/哥布林.jpg'

const props = defineProps({
  currentPage: {
    type: String,
    default: '大厅'
  },
  currentUser: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['navigate', 'enter-room', 'session-created', 'logout', 'back-button-hidden', 'open-settings'])

const showCreateModal = ref(false)
const showJoinModal = ref(false)
const roomCode = ref('')
const worlds = ref([])
const characters = ref([])
const sessions = ref([])
const rooms = ref([])
const publicRooms = ref([])
const apiStatus = ref('')
const joinRoomError = ref('')
const isSubmitting = ref(false)

watch([showCreateModal, showJoinModal], ([isCreateOpen, isJoinOpen]) => {
  emit('back-button-hidden', isCreateOpen || isJoinOpen)
}, { immediate: true })

const createRoomForm = reactive({
  roomName: '',
  maxPlayers: 4,
  roomType: 'public',
  difficulty: 'normal'
})

const actionCards = [
  {
    key: 'create',
    title: '创建房间',
    subtitle: '启封新卷',
    icon: cubeIcon,
    tone: 'gold'
  },
  {
    key: 'join',
    title: '加入房间',
    subtitle: '输入卷宗编号',
    icon: gateIcon,
    tone: 'cyan'
  },
  {
    key: 'continue',
    title: '继续冒险',
    subtitle: '续写旧卷',
    icon: orbIcon,
    tone: 'ember'
  },
  {
    key: 'archive',
    title: '历史档案',
    subtitle: '查阅灵境卷宗',
    icon: archiveIcon,
    tone: 'steel'
  }
]

const fallbackQuickRooms = [
  {
    name: '追捕克伦可团',
    players: '2/4',
    owner: '夜行者'
  },
  {
    name: '迷雾矿井先遣队',
    players: '3/4',
    owner: '说书人'
  }
]

const fallbackLastAdventure = {
  title: '追捕克伦可',
  chapter: '第 1 章 · 地下线索',
  progress: 0,
  teamSync: 0,
  groupName: '等待新的冒险'
}

const fallbackScriptTemplates = [
  '追捕克伦可',
  '龙息之城的阴影',
  '失落矿洞的秘密'
]

const scriptTemplates = computed(() => {
  if (worlds.value.length > 0) {
    return worlds.value.map((world) => world.name)
  }

  return fallbackScriptTemplates
})

const statusLabel = (status) => {
  const map = { waiting: '招募中', playing: '进行中', paused: '暂停', finished: '已结束', archived: '已归档' }
  return map[status] || status
}

const worldName = (worldId) => worlds.value.find((w) => w.id === worldId)?.name || '未知世界'

const clampPercent = (value) => {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return 0
  return Math.max(0, Math.min(100, Math.round(numeric)))
}

const progressFromStats = (record = {}) => {
  if (record.progress_percent != null) return clampPercent(record.progress_percent)
  if (record.status === 'finished' || record.status === 'archived') return 100
  const actionProgress = Math.min(85, Number(record.action_count || 0) * 10)
  const clueProgress = Math.min(90, Number(record.clue_count || 0) * 7 + Number(record.key_clue_count || 0) * 11)
  const taskTotal = Number(record.task_total_count || 0)
  const taskProgress = taskTotal > 0 ? (Number(record.task_done_count || 0) / taskTotal) * 100 : 0
  return clampPercent(Math.max(actionProgress, clueProgress, taskProgress))
}

const teamSyncPercent = (record = {}) => {
  if (record.team_sync_percent != null) return clampPercent(record.team_sync_percent)
  const memberCount = Number(record.member_count || 0)
  const maxPlayers = Number(record.max_players || 0)
  if (maxPlayers > 0) return clampPercent((memberCount / maxPlayers) * 100)
  return 0
}

const quickRooms = computed(() => {
  if (rooms.value.length === 0) return fallbackQuickRooms

  return rooms.value.slice(0, 3).map((room) => ({
    name: room.title || `房间 #${room.id}`,
    players: room.max_players ? `${room.member_count || 0}/${room.max_players} 人` : statusLabel(room.status),
    owner: props.currentUser?.nickname || props.currentUser?.username || '当前用户',
    roomId: room.id
  }))
})

const joinableRooms = computed(() => {
  const merged = [...rooms.value]
  for (const r of publicRooms.value) {
    if (!merged.some((m) => m.id === r.id)) merged.push(r)
  }
  return merged.map((room) => ({
    id: room.id,
    roomId: room.id,
    roomCode: room.room_code,
    name: room.title || `房间 #${room.id}`,
    worldview: worldName(room.world_id),
    players: `${room.member_count || 0}/${room.max_players} 人`,
    status: statusLabel(room.status)
  }))
})

const lastAdventure = computed(() => {
  const playingRoom = rooms.value.find((r) => r.status === 'playing')
  if (playingRoom) {
    return {
      title: playingRoom.title || `房间 #${playingRoom.id}`,
      chapter: `${statusLabel(playingRoom.status)} · 房间码 ${playingRoom.room_code}`,
      progress: progressFromStats(playingRoom),
      teamSync: teamSyncPercent(playingRoom),
      groupName: `当前团：${playingRoom.title || '冒险小队'}`,
      roomId: playingRoom.id
    }
  }

  const session = sessions.value[0]
  if (!session) return fallbackLastAdventure

  return {
    title: session.title || `会话 #${session.id}`,
    chapter: session.current_scene || '等待继续',
    progress: progressFromStats(session),
    teamSync: teamSyncPercent(session),
    groupName: session.adventure_module_title ? `当前团：${session.adventure_module_title}` : '单人冒险',
    sessionId: session.id
  }
})

const difficulties = [
  { value: 'easy', label: '轻松' },
  { value: 'normal', label: '标准' },
  { value: 'hard', label: '困难' },
  { value: 'nightmare', label: '噩梦' }
]

const refreshLobbyData = async () => {
  try {
    const [worldList, characterList, sessionList, roomList, publicRoomList] = await Promise.all([
      worldsApi.list(),
      charactersApi.list(),
      sessionsApi.list(),
      roomsApi.list().catch(() => []),
      roomsApi.list({ scope: 'public' }).catch(() => [])
    ])
    worlds.value = worldList
    characters.value = characterList
    sessions.value = sessionList
    rooms.value = roomList || []
    publicRooms.value = publicRoomList || []
  } catch (error) {
    apiStatus.value = error?.message || '大厅数据同步失败，请稍后重试。'
  }
}

const selectedWorld = () => worlds.value[0] || null

const buildRoomJoinWorldview = (detail) => {
  const roomInfo = detail?.room
  const world = worlds.value.find((item) => item.id === roomInfo?.world_id)
  return {
    id: world?.id || roomInfo?.world_id,
    backendId: world?.id || roomInfo?.world_id,
    source: 'room-join',
    title: world?.name || roomInfo?.title || '房间角色',
    name: world?.name || roomInfo?.title || '房间角色',
    rule_style: world?.rule_style,
    description: world?.description,
    selectedModule: {
      worldId: world?.id || roomInfo?.world_id,
      name: roomInfo?.title || world?.name || '房间冒险'
    },
    roomJoin: {
      roomId: roomInfo?.id,
      roomCode: roomInfo?.room_code,
      title: roomInfo?.title
    }
  }
}

const routeToRoomCharacterCreation = (detail) => {
  showJoinModal.value = false
  apiStatus.value = '请先为这个房间创建你的角色。'
  emit('navigate', 'role', buildRoomJoinWorldview(detail))
}

const enterExistingPlayingSession = async () => {
  await refreshLobbyData()
  const playingSession = sessions.value.find((session) => session.status === 'playing') || sessions.value[0]
  if (playingSession) {
    showCreateModal.value = false
    apiStatus.value = ''
    emit('session-created', { session: playingSession })
    return true
  }
  return false
}

const handleCreateRoom = async () => {
  apiStatus.value = ''

  if (characters.value.length === 0) {
    showCreateModal.value = false
    emit('navigate', '世界观')
    return
  }

  const world = selectedWorld()
  if (!world) {
    apiStatus.value = '暂时没有可用世界观。'
    return
  }
  const roomName = createRoomForm.roomName.trim()
  if (!roomName) {
    apiStatus.value = '需要输入自定义房间名。'
    return
  }

  isSubmitting.value = true
  try {
    const detail = await roomsApi.create({
      title: roomName,
      world_id: world.id,
      visibility: createRoomForm.roomType === 'public' ? 'public' : 'private',
      max_players: Number(createRoomForm.maxPlayers) || 4
    })
    const charId = characters.value[0]?.id
    if (charId) {
      await roomsApi.setCharacter(detail.room.id, charId)
    }
    await refreshLobbyData()
    showCreateModal.value = false
    apiStatus.value = `房间已创建，房间码：${detail.room.room_code}`
    emit('enter-room', { roomId: detail.room.id })
  } catch (error) {
    apiStatus.value = error?.message || '创建房间失败。'
  } finally {
    isSubmitting.value = false
  }
}

const openJoinModal = () => {
  joinRoomError.value = ''
  showJoinModal.value = true
}

const closeJoinModal = () => {
  joinRoomError.value = ''
  showJoinModal.value = false
}

const handleJoinRoom = async ({ code = '', room = null } = {}) => {
  joinRoomError.value = ''

  const charId = characters.value[0]?.id ?? null
  isSubmitting.value = true
  try {
    if (room?.roomId) {
      const detail = await roomsApi.join({
        room_code: room.roomCode || String(room.roomId)
      })
      if (!charId) {
        routeToRoomCharacterCreation(detail)
        return
      }
      await roomsApi.setCharacter(detail.room.id, charId)
      closeJoinModal()
      emit('enter-room', { roomId: detail.room.id })
      return
    }

    const trimmedCode = code.trim().toUpperCase()
    if (trimmedCode) {
      const detail = await roomsApi.join({
        room_code: trimmedCode
      })
      if (!charId) {
        routeToRoomCharacterCreation(detail)
        return
      }
      await roomsApi.setCharacter(detail.room.id, charId)
      closeJoinModal()
      emit('enter-room', { roomId: detail.room.id })
      return
    }

    joinRoomError.value = '请输入房间码，或从列表中选择一个房间。'
  } catch (error) {
    joinRoomError.value = error?.message || '加入房间失败。'
  } finally {
    isSubmitting.value = false
  }
}

const handleContinue = () => {
  const playingRoom = rooms.value.find((r) => r.status === 'playing')
  if (playingRoom) {
    emit('enter-room', { roomId: playingRoom.id })
    return
  }
  if (lastAdventure.value.sessionId) {
    emit('session-created', { session: lastAdventure.value })
    return
  }
  emit('navigate', '档案')
}

const handleQuickJoin = (room) => {
  if (room.roomId) {
    emit('enter-room', { roomId: room.roomId })
    return
  }
  openJoinModal()
}

const handleHistory = () => {
  emit('navigate', '档案')
}

const handleAction = (action) => {
  if (action.key === 'create') {
    emit('navigate', '世界观')
    return
  }

  if (action.key === 'join') {
    openJoinModal()
    return
  }

  if (action.key === 'continue') {
    handleContinue()
    return
  }

  handleHistory()
}

onMounted(refreshLobbyData)
</script>

<template>
  <div class="home-page">
    <div class="scene-backdrop">
      <img class="scene-image" :src="lobbyBackground" alt="大厅背景" />
      <div class="scene-vignette"></div>
      <div class="scene-lantern"></div>
      <div class="scene-grid"></div>
    </div>

    <AppNavbar
      :current-user="props.currentUser"
      @open-settings="emit('open-settings')"
      @logout="emit('logout')"
    />

    <main class="lobby-shell">
      <section class="hero-grid">
        <div class="hero-copy">
          <div class="hero-mark">
            <img class="hero-mark-icon" :src="productIcon" alt="" />
            <span>灵境档案大厅</span>
          </div>
          <h1 class="hero-title">StoryForge</h1>
          <div class="hero-subtitle">
            <span></span>
            <p>灵境档案</p>
            <span></span>
          </div>
          <p class="hero-text">
            AI 掌卷人已启封卷宗，等待新的冒险者入局。
            创建房间，邀请同伴，选择模组，在同一张桌上继续属于你们的传奇。
          </p>

          <section class="action-row">
            <button
              v-for="card in actionCards"
              :key="card.key"
              class="action-card"
              :class="[card.tone, { active: card.key === 'create' }]"
              @click="handleAction(card)"
            >
              <div class="action-border"></div>
              <div class="action-icon" :class="card.tone">
                <img :src="card.icon" :alt="card.title" />
              </div>
              <strong>{{ card.title }}</strong>
              <span>{{ card.subtitle }}</span>
            </button>
          </section>
          <p v-if="apiStatus" class="lobby-status">{{ apiStatus }}</p>
        </div>

        <aside class="side-panels">
          <section class="panel continue-panel">
            <div class="panel-header">
              <div class="panel-heading">
                <img class="panel-icon orb" :src="orbIcon" alt="" />
                <span>继续上次冒险</span>
              </div>
            </div>

            <div class="continue-card">
              <div class="adventure-cover">
                <img :src="goblinCover" alt="追捕克伦可" />
                <div class="cover-glow"></div>
              </div>

              <div class="adventure-detail">
                <h3>{{ lastAdventure.title }}</h3>
                <p class="chapter">{{ lastAdventure.chapter }}</p>
                <p class="group-name">{{ lastAdventure.groupName }}</p>
                <div class="progress-meta">
                  <span>进度：{{ lastAdventure.progress }}%</span>
                  <span>同步：{{ lastAdventure.teamSync }}%</span>
                </div>
                <div class="progress-bar">
                  <div class="progress-fill" :style="{ width: `${lastAdventure.progress}%` }"></div>
                </div>
              </div>
            </div>

            <button class="panel-button primary" @click="handleContinue">继续冒险</button>
          </section>

          <section class="panel quick-panel">
            <div class="panel-header">
              <div class="panel-heading">
                <img class="panel-icon orb" :src="orbIcon" alt="" />
                <span>快捷进入</span>
              </div>
              <button class="panel-link">最近房间</button>
            </div>

            <div class="quick-list">
              <article
                v-for="room in quickRooms"
                :key="room.name"
                class="quick-item"
              >
                <div class="quick-badge">
                  <img :src="productIcon" alt="" />
                </div>
                <div class="quick-info">
                  <h4>{{ room.name }}</h4>
                  <p>房主：{{ room.owner }}</p>
                </div>
                <div class="quick-actions">
                  <span class="quick-players">{{ room.players }} 人</span>
                  <button class="panel-button small" @click="handleQuickJoin(room)">快速加入</button>
                </div>
              </article>
            </div>
          </section>
        </aside>
      </section>
    </main>

    <JoinRoomModal
      v-if="showJoinModal"
      :rooms="joinableRooms"
      :error-message="joinRoomError"
      @close="closeJoinModal"
      @join="handleJoinRoom"
      @clear-error="joinRoomError = ''"
    />

    <div class="modal-overlay" v-if="showCreateModal" @click="showCreateModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">创建房间</h3>
          <button class="modal-close" @click="showCreateModal = false">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M6 18 18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form class="modal-form" @submit.prevent="handleCreateRoom">
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">房间名称</label>
              <input
                v-model="createRoomForm.roomName"
                type="text"
                class="form-input"
                placeholder="请输入房间名称"
              />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label">房间邀请码</label>
              <input
                v-model="roomCode"
                type="text"
                class="form-input"
                placeholder="可选，留空则自动生成"
              />
            </div>

            <div class="form-group">
              <label class="form-label">人数上限</label>
              <select v-model="createRoomForm.maxPlayers" class="form-select">
                <option :value="1">1 人</option>
                <option :value="2">2 人</option>
                <option :value="3">3 人</option>
                <option :value="4">4 人</option>
                <option :value="5">5 人</option>
                <option :value="6">6 人</option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">挑战难度</label>
            <select v-model="createRoomForm.difficulty" class="form-select">
              <option v-for="diff in difficulties" :key="diff.value" :value="diff.value">{{ diff.label }}</option>
            </select>
          </div>

          <div class="form-group">
            <label class="form-label">房间类型</label>
            <div class="radio-group">
              <label class="radio-item">
                <input type="radio" v-model="createRoomForm.roomType" value="public" />
                <span>公开房间</span>
              </label>
              <label class="radio-item">
                <input type="radio" v-model="createRoomForm.roomType" value="private" />
                <span>私密房间</span>
              </label>
            </div>
          </div>

          <div class="modal-footer">
            <button type="button" class="panel-button secondary" @click="showCreateModal = false">取消</button>
            <button type="submit" class="panel-button primary solid" :disabled="isSubmitting">
              {{ isSubmitting ? '创建中...' : '创建房间' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background: #050607;
  color: #f5dfb2;
}

.scene-backdrop,
.scene-vignette,
.scene-lantern,
.scene-grid {
  position: absolute;
  inset: 0;
}

.scene-backdrop {
  z-index: 0;
}

.scene-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
  filter: brightness(0.82) saturate(0.95);
  transform: scale(1.02);
}

.scene-vignette {
  background:
    linear-gradient(90deg, rgba(3, 6, 12, 0.96) 0%, rgba(4, 7, 13, 0.92) 31%, rgba(5, 7, 12, 0.3) 58%, rgba(22, 11, 4, 0.7) 100%),
    linear-gradient(180deg, rgba(0, 0, 0, 0.54) 0%, transparent 18%, transparent 82%, rgba(0, 0, 0, 0.56) 100%);
}

.scene-lantern {
  background:
    radial-gradient(circle at 84% 28%, rgba(255, 170, 61, 0.16), transparent 11%),
    radial-gradient(circle at 64% 26%, rgba(89, 206, 255, 0.18), transparent 13%),
    radial-gradient(circle at 63% 68%, rgba(255, 183, 72, 0.18), transparent 16%);
  mix-blend-mode: screen;
}

.scene-grid {
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
  background-size: 120px 120px;
  opacity: 0.08;
}

.navbar {
  position: relative;
  z-index: 5;
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 20px;
  padding: 18px 34px 10px;
  border-bottom: 1px solid rgba(221, 174, 94, 0.14);
  background: linear-gradient(180deg, rgba(4, 4, 6, 0.88), rgba(4, 4, 6, 0.44));
  backdrop-filter: blur(10px);
}

.navbar::after {
  content: '';
  position: absolute;
  left: 50%;
  bottom: -1px;
  width: 92px;
  height: 2px;
  transform: translateX(-50%);
  background: linear-gradient(90deg, transparent, rgba(248, 199, 99, 0.96), transparent);
  box-shadow: 0 0 15px rgba(248, 199, 99, 0.45);
}

.nav-logo {
  grid-column: 2;
  grid-row: 1;
  justify-self: center;
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.logo-icon {
  width: 52px;
  height: 52px;
  object-fit: contain;
  filter: drop-shadow(0 0 12px rgba(240, 190, 90, 0.18));
}

.logo-text {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 0;
  line-height: 1.04;
}

.logo-en {
  font-size: 1.05rem;
  letter-spacing: 0.05em;
  color: #efc26a;
}

.logo-cn {
  margin-top: 2px;
  font-size: 0.88rem;
  letter-spacing: 0.26em;
  color: rgba(241, 198, 108, 0.86);
}

.nav-menu {
  grid-column: 1;
  grid-row: 1;
  justify-self: start;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 26px;
}

.nav-item {
  position: relative;
  padding: 8px 4px 14px;
  border: 0;
  background: transparent;
  color: rgba(250, 226, 179, 0.8);
  font-size: 1rem;
  letter-spacing: 0.16em;
  cursor: pointer;
  transition: color 0.25s ease, transform 0.25s ease;
}

.nav-item:hover,
.nav-item.active {
  color: #f6c56e;
  transform: translateY(-1px);
}

.nav-item.active::after {
  content: '';
  position: absolute;
  left: 50%;
  bottom: 0;
  width: 72px;
  height: 2px;
  transform: translateX(-50%);
  background: linear-gradient(90deg, transparent, rgba(247, 192, 88, 0.96), transparent);
  box-shadow: 0 0 14px rgba(247, 192, 88, 0.5);
}

.nav-user {
  grid-column: 3;
  grid-row: 1;
  justify-self: end;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 7px 14px 7px 7px;
  border: 1px solid rgba(237, 187, 93, 0.2);
  border-radius: 999px;
  background: linear-gradient(180deg, rgba(54, 34, 10, 0.45), rgba(11, 11, 14, 0.45));
}

.user-avatar {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  border: 1px solid rgba(248, 196, 94, 0.34);
  background:
    radial-gradient(circle at 35% 30%, rgba(255, 222, 170, 0.28), transparent 26%),
    linear-gradient(180deg, #3f2c12, #17100a);
  color: #f7cc7d;
  font-weight: 700;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-name {
  color: #f7d389;
  font-weight: 600;
}

.user-level {
  color: rgba(240, 222, 185, 0.76);
  font-size: 0.84rem;
}

.nav-icon {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  border: 1px solid rgba(241, 191, 94, 0.22);
  background: rgba(10, 11, 14, 0.55);
  color: rgba(247, 205, 122, 0.88);
  cursor: pointer;
}

.nav-icon svg {
  width: 19px;
  height: 19px;
}

.lobby-shell {
  position: relative;
  z-index: 2;
  max-width: 1620px;
  margin: 0 auto;
  padding: 18px 34px 24px;
  display: grid;
  gap: 18px;
}

.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.42fr) minmax(340px, 498px);
  gap: 24px;
  align-items: flex-start;
}

.hero-copy {
  max-width: 700px;
  padding-top: 8px;
}

.hero-mark {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 7px 14px;
  border: 1px solid rgba(242, 194, 103, 0.2);
  border-radius: 999px;
  background: rgba(7, 9, 14, 0.28);
  color: rgba(247, 213, 143, 0.88);
  letter-spacing: 0.18em;
  font-size: 0.8rem;
}

.hero-mark-icon {
  width: 16px;
  height: 16px;
}

.hero-title {
  margin-top: 18px;
  font-size: clamp(4.2rem, 7vw, 7rem);
  line-height: 0.9;
  letter-spacing: -0.05em;
  color: #f4d08c;
  text-shadow: 0 0 25px rgba(231, 175, 72, 0.18);
}

.hero-subtitle {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 14px;
}

.hero-subtitle span {
  width: 112px;
  max-width: 18vw;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(246, 196, 96, 0.6), transparent);
}

.hero-subtitle p {
  color: #f5c86f;
  font-size: clamp(1.3rem, 2.8vw, 2.2rem);
  letter-spacing: 0.56em;
  white-space: nowrap;
}

.hero-text {
  max-width: 540px;
  margin-top: 16px;
  color: rgba(248, 233, 204, 0.86);
  font-size: 1.08rem;
  line-height: 1.88;
  text-shadow: 0 2px 16px rgba(0, 0, 0, 0.5);
}

.side-panels {
  display: grid;
  gap: 16px;
}

.panel {
  border: 1px solid rgba(68, 146, 191, 0.24);
  border-radius: 20px;
  background:
    linear-gradient(180deg, rgba(7, 19, 26, 0.76), rgba(8, 10, 14, 0.86)),
    rgba(5, 8, 14, 0.72);
  box-shadow:
    0 22px 42px rgba(0, 0, 0, 0.3),
    inset 0 0 0 1px rgba(111, 183, 224, 0.06);
  backdrop-filter: blur(12px);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 18px 20px 14px;
}

.panel-heading {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #efc66f;
  font-size: 1.16rem;
  font-weight: 600;
}

.panel-icon {
  width: 16px;
  height: 16px;
}

.panel-icon.orb {
  filter: brightness(1.2) sepia(1) saturate(0.1) hue-rotate(160deg);
}

.panel-link {
  border: 0;
  background: transparent;
  color: rgba(111, 192, 230, 0.9);
  font-size: 0.95rem;
  cursor: pointer;
}

.continue-card {
  display: grid;
  grid-template-columns: 132px minmax(0, 1fr);
  gap: 16px;
  padding: 0 20px 16px;
}

.adventure-cover {
  position: relative;
  min-height: 118px;
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid rgba(111, 183, 224, 0.14);
}

.adventure-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-glow {
  position: absolute;
  inset: auto 10% 7% 10%;
  height: 24px;
  border-radius: 999px;
  background: radial-gradient(circle, rgba(255, 186, 74, 0.76), transparent 72%);
  filter: blur(6px);
}

.adventure-detail h3 {
  font-size: 1.72rem;
  line-height: 1.08;
  color: #f7ead2;
}

.adventure-detail .chapter,
.group-name {
  margin-top: 8px;
  color: rgba(243, 230, 201, 0.78);
  font-size: 0.95rem;
}

.group-name {
  color: rgba(245, 211, 145, 0.82);
}

.progress-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 14px;
  margin-top: 16px;
  color: rgba(246, 229, 191, 0.88);
  font-size: 0.95rem;
}

.progress-bar {
  height: 8px;
  margin-top: 8px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(86, 104, 118, 0.42);
}

.progress-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #3ab3ef, #7ce2ff);
  box-shadow: 0 0 18px rgba(84, 205, 255, 0.35);
}

.quick-list {
  display: grid;
  gap: 12px;
  padding: 0 20px 20px;
}

.quick-item {
  display: grid;
  grid-template-columns: 52px minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  padding: 14px;
  border-radius: 16px;
  background: rgba(8, 15, 20, 0.5);
  border: 1px solid rgba(90, 154, 192, 0.12);
}

.quick-badge {
  width: 52px;
  height: 52px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  border: 1px solid rgba(241, 191, 94, 0.28);
  background: radial-gradient(circle, rgba(61, 45, 18, 0.76), rgba(7, 9, 13, 0.95));
}

.quick-badge img {
  width: 20px;
  height: 20px;
}

.quick-info h4 {
  color: #f2d28b;
  font-size: 1.02rem;
}

.quick-info p {
  margin-top: 4px;
  color: rgba(238, 225, 197, 0.72);
}

.quick-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}

.quick-players {
  color: #7fd7ff;
}

.action-row {
  margin-top: 28px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.lobby-status {
  margin-top: 14px;
  color: #7fd7ff;
  font-size: 0.95rem;
}

.action-card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 150px;
  padding: 18px 12px;
  border: 1px solid rgba(176, 136, 65, 0.25);
  border-radius: 14px;
  background:
    linear-gradient(180deg, rgba(8, 11, 17, 0.65), rgba(8, 10, 14, 0.82)),
    rgba(0, 0, 0, 0.4);
  color: #f7e3bc;
  text-align: center;
  cursor: pointer;
  transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
  backdrop-filter: blur(8px);
  overflow: hidden;
}

.action-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.04), transparent 40%),
    linear-gradient(315deg, rgba(255, 255, 255, 0.02), transparent 45%);
  pointer-events: none;
}

.action-card:hover {
  transform: translateY(-3px);
  border-color: rgba(248, 196, 94, 0.4);
  box-shadow: 0 12px 22px rgba(0, 0, 0, 0.28);
}

.action-card.active {
  border-color: rgba(248, 196, 94, 0.55);
  box-shadow:
    0 0 0 1px rgba(250, 200, 95, 0.4),
    0 14px 26px rgba(0, 0, 0, 0.32),
    inset 0 0 24px rgba(248, 191, 77, 0.06);
}

.action-border {
  position: absolute;
  inset: 6px;
  border: 1px solid rgba(255, 220, 160, 0.12);
  border-radius: 12px;
  pointer-events: none;
}

.action-icon {
  width: 56px;
  height: 56px;
  display: grid;
  place-items: center;
  border-radius: 16px;
  border: 1px solid rgba(255, 216, 153, 0.2);
  background: rgba(255, 255, 255, 0.04);
}

.action-icon img {
  width: 28px;
  height: 28px;
  object-fit: contain;
}

.action-card strong {
  font-size: 1.2rem;
  font-weight: 600;
  letter-spacing: 0.06em;
}

.action-card span {
  color: rgba(245, 232, 205, 0.72);
  font-size: 0.98rem;
  letter-spacing: 0.12em;
}

.action-card.gold {
  border-color: rgba(241, 187, 88, 0.32);
}

.action-card.gold .action-icon {
  box-shadow: inset 0 0 20px rgba(247, 193, 92, 0.08);
}

.action-card.gold .action-icon img,
.action-card.gold.active .action-icon img {
  filter: brightness(0) saturate(100%) invert(78%) sepia(57%) saturate(557%) hue-rotate(356deg) brightness(101%) contrast(93%);
}

.action-card.cyan {
  border-color: rgba(86, 170, 207, 0.28);
}

.action-card.cyan .action-border,
.action-card.cyan .action-icon {
  border-color: rgba(115, 219, 255, 0.2);
}

.action-card.cyan .action-icon img {
  filter: brightness(0) saturate(100%) invert(72%) sepia(47%) saturate(1714%) hue-rotate(165deg) brightness(101%) contrast(102%);
}

.action-card.ember .action-icon img {
  filter: brightness(0) saturate(100%) invert(81%) sepia(39%) saturate(626%) hue-rotate(353deg) brightness(100%) contrast(92%);
}

.action-card.steel .action-icon img {
  filter: brightness(0) saturate(100%) invert(91%) sepia(16%) saturate(274%) hue-rotate(170deg) brightness(89%) contrast(86%);
}

.panel-button {
  border: 1px solid rgba(243, 191, 92, 0.26);
  background: rgba(30, 20, 8, 0.48);
  color: #f4ce86;
  cursor: pointer;
  transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
}

.panel-button:hover {
  transform: translateY(-1px);
  border-color: rgba(243, 191, 92, 0.42);
  box-shadow: 0 10px 18px rgba(0, 0, 0, 0.22);
}

.panel-button:disabled {
  cursor: wait;
  opacity: 0.62;
  transform: none;
  box-shadow: none;
}

.panel-button.primary {
  width: calc(100% - 40px);
  margin: 0 20px 20px;
  padding: 14px 18px;
  border-radius: 14px;
  color: #fde7bf;
  font-size: 1.12rem;
  font-weight: 600;
}

.panel-button.primary:not(.solid) {
  background: linear-gradient(180deg, rgba(122, 78, 24, 0.86), rgba(77, 49, 16, 0.92));
}

.panel-button.primary.solid {
  margin: 0;
}

.panel-button.secondary {
  padding: 12px 22px;
  border-radius: 14px;
}

.panel-button.small {
  padding: 9px 16px;
  border-radius: 12px;
  color: #f7d497;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 20;
  display: grid;
  place-items: center;
  background: rgba(2, 4, 8, 0.72);
  backdrop-filter: blur(12px);
}

.modal-content {
  width: min(720px, calc(100vw - 32px));
  padding: 28px;
  border-radius: 22px;
  border: 1px solid rgba(241, 191, 94, 0.24);
  background:
    linear-gradient(180deg, rgba(14, 17, 23, 0.96), rgba(8, 10, 14, 0.98)),
    #090b10;
  box-shadow: 0 34px 52px rgba(0, 0, 0, 0.42);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.modal-title {
  color: #f5d18b;
  font-size: 1.56rem;
}

.modal-close {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  border: 1px solid rgba(241, 191, 94, 0.18);
  border-radius: 50%;
  background: rgba(16, 17, 22, 0.9);
  color: #f2cb7a;
  cursor: pointer;
}

.modal-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.form-row > .form-group:only-child {
  grid-column: 1 / -1;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  color: rgba(245, 226, 192, 0.84);
  font-size: 0.95rem;
}

.form-input,
.form-select {
  width: 100%;
  padding: 14px 16px;
  border: 1px solid rgba(105, 147, 173, 0.24);
  border-radius: 14px;
  background: rgba(10, 16, 22, 0.88);
  color: #f6ead1;
  outline: none;
}

.form-input::placeholder {
  color: rgba(181, 190, 201, 0.52);
}

.form-input:focus,
.form-select:focus {
  border-color: rgba(104, 197, 240, 0.5);
  box-shadow: 0 0 0 4px rgba(52, 149, 192, 0.12);
}

.radio-group {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.radio-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: rgba(245, 229, 194, 0.9);
}

.radio-item input {
  accent-color: #f1bb5e;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 4px;
}

@media (max-width: 1280px) {
  .hero-grid {
    grid-template-columns: 1fr;
    min-height: auto;
  }

  .side-panels {
    max-width: 620px;
  }

  .action-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .navbar {
    grid-template-columns: 1fr auto 1fr;
    justify-items: stretch;
    gap: 12px;
    padding: 14px 18px 10px;
  }

  .nav-menu {
    display: none;
  }

  .nav-user {
    width: auto;
    justify-content: flex-end;
  }

  .lobby-shell {
    padding: 18px 18px 24px;
  }

  .continue-card {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .action-row,
  .form-row {
    grid-template-columns: 1fr;
  }

  .quick-item {
    grid-template-columns: 1fr;
    align-items: start;
  }

  .quick-actions {
    align-items: stretch;
  }

  .hero-title {
    font-size: clamp(3.2rem, 15vw, 5.2rem);
  }

  .hero-subtitle p {
    letter-spacing: 0.32em;
    font-size: 1.28rem;
  }

  .hero-text {
    font-size: 1rem;
  }
}
</style>
