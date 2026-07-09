<script setup>
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { charactersApi, roomsApi, worldsApi } from './api/client'
import { RoomSocket, newClientMsgId } from './api/wsClient'

const DEMO_USER_ID = 1

const props = defineProps({
  currentUser: { type: Object, default: null },
  initialRoomId: { type: [Number, String], default: null }
})
const emit = defineEmits(['navigate'])

const view = ref('lobby') // 'lobby' | 'room'
const loading = ref(false)
const errorText = ref('')

// 大厅数据
const myRooms = ref([])
const publicRooms = ref([])
const worlds = ref([])
const myCharacters = ref([])
const createForm = reactive({ title: '', world_id: null, max_players: 4 })
const joinForm = reactive({ room_code: '', character_id: null })

// 房间数据
const room = ref(null)
const members = ref([])
const messages = ref([])
const messageIds = new Set()
const sessionMeta = ref(null)
const wsStatus = ref('offline')
const aiThinking = ref(null)
const chatInput = ref('')
const oocInput = ref('')
const actionInput = ref('')
const dmAskInput = ref('')
const typingUsers = ref({})
const socket = ref(null)
const isExitConfirmOpen = ref(false)

const myUserId = computed(() => props.currentUser?.id ?? DEMO_USER_ID)
const isHost = computed(() => room.value && room.value.owner_id === myUserId.value)
const isPlaying = computed(() => room.value?.status === 'playing')
const myMember = computed(() => members.value.find((m) => m.user_id === myUserId.value) || null)
const selectedCharacter = computed(() =>
  myCharacters.value.find((c) => c.id === myMember.value?.character_id) || null
)
const memberCountLabel = computed(() => `${members.value.length}/${room.value?.max_players || '-'}`)
const isRoomFull = computed(() => Boolean(room.value) && members.value.length >= room.value.max_players)
const allMembersHaveCharacters = computed(() =>
  members.value.length > 0 && members.value.every((m) => Boolean(m.character_id))
)
const allMembersReady = computed(() =>
  members.value.length > 0 && members.value.every((m) => Boolean(m.is_ready))
)
const readyDisabledReason = computed(() => {
  if (isPlaying.value) return ''
  if (!myMember.value?.character_id) return '请先选择出战角色'
  return ''
})
const startDisabledReason = computed(() => {
  if (!isHost.value || isPlaying.value || !room.value) return ''
  if (!isRoomFull.value) return `等待成员加入：${memberCountLabel.value}`
  if (!allMembersHaveCharacters.value) return '等待所有成员选择出战角色'
  if (!allMembersReady.value) return '等待所有成员准备就绪'
  return ''
})
const canStartGame = computed(() => isHost.value && !loading.value && !startDisabledReason.value)

const typingLabel = computed(() => {
  const names = Object.values(typingUsers.value).filter(Boolean)
  if (!names.length) return ''
  if (names.length === 1) return `${names[0]} 正在输入…`
  return `${names.slice(0, 2).join('、')}${names.length > 2 ? ' 等' : ''} 正在输入…`
})

const thinkingLabels = {
  parsing: 'AI DM 正在解析行动…',
  narrating: 'AI DM 正在撰写叙事…',
  reviewing: 'AI DM 正在审核叙事…',
  rolling: '正在掷骰判定…',
  guidance: 'AI DM 正在思考你的问题…'
}

const setError = (err) => {
  errorText.value = err?.message || String(err || '操作失败')
  setTimeout(() => { errorText.value = '' }, 4000)
}

// ---------------- 大厅 ----------------

const loadMyCharacters = async () => {
  const charList = await charactersApi.list().catch(() => [])
  myCharacters.value = charList || []
  if (!joinForm.character_id && myCharacters.value.length) {
    joinForm.character_id = myCharacters.value[0].id
  }
}

const loadLobby = async () => {
  loading.value = true
  try {
    const [roomList, publicList, worldList, charList] = await Promise.all([
      roomsApi.list().catch(() => []),
      roomsApi.list({ scope: 'public' }).catch(() => []),
      worldsApi.list().catch(() => []),
      charactersApi.list().catch(() => [])
    ])
    myRooms.value = roomList || []
    publicRooms.value = (publicList || []).filter((r) => !(roomList || []).some((m) => m.id === r.id))
    worlds.value = worldList || []
    myCharacters.value = charList || []
    if (!createForm.world_id && worlds.value.length) createForm.world_id = worlds.value[0].id
    if (!joinForm.character_id && myCharacters.value.length) {
      joinForm.character_id = myCharacters.value[0].id
    }
  } catch (err) {
    setError(err)
  } finally {
    loading.value = false
  }
}

const handleCreate = async () => {
  if (!createForm.title.trim() || !createForm.world_id) {
    setError('请填写房间标题并选择世界')
    return
  }
  loading.value = true
  try {
    const detail = await roomsApi.create({
      title: createForm.title.trim(),
      world_id: createForm.world_id,
      max_players: Number(createForm.max_players) || 4
    })
    await enterRoom(detail.room.id)
  } catch (err) {
    setError(err)
  } finally {
    loading.value = false
  }
}

const handleJoin = async () => {
  if (!joinForm.room_code.trim()) {
    setError('请输入房间码')
    return
  }
  loading.value = true
  try {
    const detail = await roomsApi.join({
      room_code: joinForm.room_code.trim().toUpperCase(),
      character_id: joinForm.character_id
    })
    await enterRoom(detail.room.id)
  } catch (err) {
    setError(err)
  } finally {
    loading.value = false
  }
}

const joinPublicRoom = async (roomCode) => {
  joinForm.room_code = roomCode || ''
  await handleJoin()
}

// ---------------- 进入房间 ----------------

const pushMessage = (msg) => {
  if (msg == null) return
  const key = msg.id != null ? `id_${msg.id}` : `seq_${msg.seq}`
  if (messageIds.has(key)) return
  messageIds.add(key)
  messages.value.push(msg)
  messages.value.sort((a, b) => (a.seq || 0) - (b.seq || 0))
  if (msg.seq && socket.value) {
    socket.value.lastSeq = Math.max(socket.value.lastSeq || 0, msg.seq)
  }
}

const syncMissedMessages = async (afterSeq) => {
  if (!room.value?.id || !afterSeq) return
  try {
    const missed = await roomsApi.messages(room.value.id, { afterSeq, limit: 100 })
    missed.forEach(pushMessage)
  } catch (err) {
    setError(err)
  }
}

const applyDetail = (detail) => {
  if (!detail) return
  if (detail.room) room.value = detail.room
  if (detail.members) members.value = detail.members
}

const refreshRoomDetail = async () => {
  if (!room.value?.id) return
  applyDetail(await roomsApi.get(room.value.id))
}

const handleEvent = (event) => {
  const { type, data } = event
  switch (type) {
    case 'room.snapshot':
      room.value = data.room
      members.value = data.members || []
      messages.value = []
      messageIds.clear()
      ;(data.messages || []).forEach(pushMessage)
      break
    case 'room.updated':
    case 'game.started':
    case 'game.ended':
      applyDetail(data)
      break
    case 'member.joined':
      if (!members.value.some((m) => m.user_id === data.user_id)) members.value.push(data)
      break
    case 'member.left':
      members.value = members.value.filter((m) => m.user_id !== data.user_id)
      break
    case 'member.presence': {
      const m = members.value.find((x) => x.user_id === data.user_id)
      if (m) m.online_status = data.online_status
      if (data.online_status !== 'online') {
        const next = { ...typingUsers.value }
        delete next[data.user_id]
        typingUsers.value = next
      }
      break
    }
    case 'member.online': {
      const m = members.value.find((x) => x.user_id === data.user_id)
      if (m) m.online_status = 'online'
      break
    }
    case 'member.offline': {
      const m = members.value.find((x) => x.user_id === data.user_id)
      if (m) m.online_status = 'offline'
      const next = { ...typingUsers.value }
      delete next[data.user_id]
      typingUsers.value = next
      break
    }
    case 'typing.start':
      if (data.user_id !== myUserId.value) {
        typingUsers.value = {
          ...typingUsers.value,
          [data.user_id]: data.display_name || `玩家${data.user_id}`
        }
      }
      break
    case 'typing.stop':
      if (data.user_id !== myUserId.value) {
        const next = { ...typingUsers.value }
        delete next[data.user_id]
        typingUsers.value = next
      }
      break
    case 'chat.message':
    case 'ooc.message':
    case 'action.received':
    case 'ai.narration':
    case 'dice.result':
    case 'dice.rolled':
    case 'dm.narration':
    case 'dm.guidance':
      pushMessage(data)
      if (type === 'dm.narration' || type === 'dm.guidance') aiThinking.value = null
      break
    case 'ai.thinking':
      aiThinking.value = data
      break
    case 'state.updated':
      sessionMeta.value = data.session_meta
      aiThinking.value = null
      break
    case 'error':
      setError(data)
      break
    default:
      break
  }
}

const enterRoom = async (roomId) => {
  loading.value = true
  try {
    if (!myCharacters.value.length) {
      await loadMyCharacters()
    }
    const detail = await roomsApi.get(roomId)
    applyDetail(detail)
    messages.value = []
    messageIds.clear()
    const history = await roomsApi.messages(roomId, { limit: 100 }).catch(() => [])
    history.forEach(pushMessage)
    view.value = 'room'

    socket.value = new RoomSocket(roomId, {
      onEvent: handleEvent,
      onStatus: (s) => { wsStatus.value = s },
      onReconnect: syncMissedMessages
    })
    socket.value.connect()
  } catch (err) {
    setError(err)
  } finally {
    loading.value = false
  }
}

const disconnect = () => {
  if (socket.value) {
    socket.value.close()
    socket.value = null
  }
  wsStatus.value = 'offline'
}

const leaveToLobby = async () => {
  disconnect()
  room.value = null
  members.value = []
  messages.value = []
  messageIds.clear()
  sessionMeta.value = null
  aiThinking.value = null
  if (props.initialRoomId) {
    emit('navigate', 'home')
    return
  }
  view.value = 'lobby'
  await loadLobby()
}

const requestLeaveRoom = () => {
  if (view.value !== 'room') {
    leaveToLobby()
    return
  }
  isExitConfirmOpen.value = true
}

const cancelLeaveRoom = () => {
  isExitConfirmOpen.value = false
}

const confirmLeaveRoom = async () => {
  isExitConfirmOpen.value = false
  await leaveToLobby()
}

const toggleReady = async () => {
  if (!room.value || !myMember.value) return
  if (!myMember.value.character_id) {
    setError('请先选择出战角色')
    return
  }
  try {
    await roomsApi.setReady(room.value.id, !myMember.value.is_ready)
    await refreshRoomDetail()
  } catch (err) {
    setError(err)
  }
}

// ---------------- 房间内操作 ----------------

const chooseCharacter = async (characterId) => {
  if (!characterId) return
  try {
    await roomsApi.setCharacter(room.value.id, characterId)
    await refreshRoomDetail()
  } catch (err) {
    setError(err)
  }
}

const startGame = async () => {
  if (startDisabledReason.value) {
    setError(startDisabledReason.value)
    return
  }
  loading.value = true
  try {
    const result = await roomsApi.start(room.value.id, myMember.value?.character_id || null)
    applyDetail(result.detail)
    if (result.opening_message) pushMessage(result.opening_message)
  } catch (err) {
    setError(err)
  } finally {
    loading.value = false
  }
}

const endGame = async () => {
  try {
    await roomsApi.end(room.value.id)
  } catch (err) {
    setError(err)
  }
}

const sendChat = async () => {
  const content = chatInput.value.trim()
  if (!content) return
  socket.value?.notifyTyping(false)
  const cid = newClientMsgId()
  chatInput.value = ''
  if (!socket.value || !socket.value.sendChat(content, cid)) {
    try {
      pushMessage(await roomsApi.chat(room.value.id, content, cid))
    } catch (err) {
      setError(err)
    }
  }
}

const sendOoc = async () => {
  const content = oocInput.value.trim()
  if (!content) return
  socket.value?.notifyTyping(false)
  const cid = newClientMsgId()
  oocInput.value = ''
  if (!socket.value || !socket.value.sendOoc(content, cid)) {
    try {
      pushMessage(await roomsApi.ooc(room.value.id, content, cid))
    } catch (err) {
      setError(err)
    }
  }
}

const submitAction = async () => {
  const text = actionInput.value.trim()
  if (!text) return
  const cid = newClientMsgId()
  actionInput.value = ''
  if (!socket.value || !socket.value.submitAction(text, cid)) {
    try {
      await roomsApi.action(room.value.id, text, cid)
    } catch (err) {
      setError(err)
    }
  }
}

const onComposerInput = () => {
  socket.value?.notifyTyping(true)
}

const submitDmAsk = async () => {
  const question = dmAskInput.value.trim()
  if (!question) return
  socket.value?.notifyTyping(false)
  const cid = newClientMsgId()
  dmAskInput.value = ''
  if (!socket.value || !socket.value.sendDmAsk(question, cid)) {
    try {
      await roomsApi.ask(room.value.id, question, { clientMsgId: cid })
    } catch (err) {
      setError(err)
    }
  }
}

const messageTypeLabel = (m) => {
  if (m.message_type === 'dm_ask') return '问 DM'
  if (m.message_type === 'chat') return '聊天'
  if (m.message_type === 'narration') return '旁白'
  if (m.message_type === 'guidance') return 'DM 建议'
  if (m.message_type === 'ooc') return '场外讨论'
  return m.message_type
}

const characterName = (id) => myCharacters.value.find((c) => c.id === id)?.name || null
const memberDisplayName = (m) => m.display_name || `玩家${m.user_id || ''}`
const memberCharacterName = (m) => m.character_name || characterName(m.character_id) || ''
const characterSummary = (c) => {
  if (!c) return ''
  const pieces = [c.name]
  if (c.level) pieces.push(`Lv.${c.level}`)
  if (c.class_id) pieces.push(c.class_id)
  return pieces.join(' · ')
}

const roleLabel = (m) => (m.sender_role === 'ai_dm' ? 'AI DM' : m.sender_name || `玩家${m.sender_user_id || ''}`)

onBeforeUnmount(disconnect)

// 从大厅（HomePage）带 roomId 直接进房；否则显示房间大厅
if (props.initialRoomId) {
  enterRoom(Number(props.initialRoomId))
} else {
  loadLobby()
}

watch(
  () => props.initialRoomId,
  (id) => {
    if (id && (!room.value || room.value.id !== Number(id))) {
      enterRoom(Number(id))
    }
  }
)
</script>

<template>
  <div class="room-shell">
    <header class="topbar">
      <button class="ghost" @click="requestLeaveRoom">
        {{ view === 'room' ? '退出房间' : '← 返回大厅' }}
      </button>
      <h1>多人房间 · AI DM 跑团</h1>
      <span v-if="view === 'room'" class="ws-badge" :data-status="wsStatus">{{ wsStatus }}</span>
    </header>

    <p v-if="errorText" class="error-banner">{{ errorText }}</p>

    <!-- ============ 大厅 ============ -->
    <section v-if="view === 'lobby'" class="lobby">
      <div class="panel">
        <h2>创建房间</h2>
        <label>标题
          <input v-model="createForm.title" placeholder="例如：锻炉街突袭" />
        </label>
        <label>世界观
          <select v-model="createForm.world_id">
            <option v-for="w in worlds" :key="w.id" :value="w.id">{{ w.name }}</option>
          </select>
        </label>
        <label>人数上限
          <input v-model.number="createForm.max_players" type="number" min="1" max="12" />
        </label>
        <button class="primary" :disabled="loading" @click="handleCreate">创建并进入</button>
      </div>

      <div class="panel">
        <h2>加入房间</h2>
        <label>房间码
          <input v-model="joinForm.room_code" placeholder="6 位房间码" maxlength="12" />
        </label>
        <label>出战角色
          <select v-model="joinForm.character_id">
            <option :value="null">稍后选择</option>
            <option v-for="c in myCharacters" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </label>
        <button class="primary" :disabled="loading" @click="handleJoin">加入</button>
      </div>

      <div class="panel wide">
        <h2>我的房间</h2>
        <ul v-if="myRooms.length" class="room-list">
          <li v-for="r in myRooms" :key="r.id">
            <div>
              <strong>{{ r.title }}</strong>
              <span class="tag">{{ r.room_code }}</span>
              <span class="tag" :data-status="r.status">{{ r.status }}</span>
            </div>
            <button class="ghost" @click="enterRoom(r.id)">进入</button>
          </li>
        </ul>
        <p v-else class="muted">还没有房间，创建或加入一个吧。</p>
      </div>
      <div class="panel wide">
        <h2>公开房间</h2>
        <ul v-if="publicRooms.length" class="room-list">
          <li v-for="r in publicRooms" :key="`pub_${r.id}`">
            <div>
              <strong>{{ r.title }}</strong>
              <span class="tag">{{ r.room_code }}</span>
              <span class="tag" :data-status="r.status">{{ r.status }}</span>
            </div>
            <button class="ghost" @click="joinPublicRoom(r.room_code)">加入</button>
          </li>
        </ul>
        <p v-else class="muted">暂无可加入的公开房间。</p>
      </div>
    </section>

    <!-- ============ 房间内 ============ -->
    <section v-else class="room-view">
      <aside class="side">
        <div class="room-head">
          <h2>{{ room?.title }}</h2>
          <p class="muted">
            房间码 <strong>{{ room?.room_code }}</strong> · 状态 {{ room?.status }}
          </p>
          <p v-if="sessionMeta" class="muted">
            当前场景：{{ sessionMeta.current_scene }} · 线索压力
            {{ sessionMeta.clue_pressure?.toFixed?.(2) ?? sessionMeta.clue_pressure }}
          </p>
        </div>

        <h3>成员 ({{ memberCountLabel }})</h3>
        <ul class="members">
          <li v-for="m in members" :key="m.user_id">
            <span class="dot" :data-online="m.online_status" />
            <span class="member-main">
              <span class="mname">{{ memberDisplayName(m) }}</span>
              <span class="member-character">
                {{ memberCharacterName(m) ? `出战：${memberCharacterName(m)}` : '未选择出战角色' }}
              </span>
            </span>
            <span class="member-tags">
              <span v-if="m.role === 'host'" class="tag host">房主</span>
              <span v-if="m.is_ready" class="tag ready">已准备</span>
              <span v-else class="tag">未准备</span>
            </span>
          </li>
        </ul>

        <div v-if="!isPlaying" class="prep">
          <h3>选择出战角色</h3>
          <select
            :value="myMember?.character_id || ''"
            :disabled="!myCharacters.length"
            @change="chooseCharacter(Number($event.target.value))"
          >
            <option value="" disabled>{{ myCharacters.length ? '请选择' : '暂无可用角色' }}</option>
            <option v-for="c in myCharacters" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
          <p v-if="selectedCharacter" class="muted">当前出战：{{ characterSummary(selectedCharacter) }}</p>
          <p v-else class="muted">请选择一个角色后再准备。</p>
          <button class="ghost" :disabled="Boolean(readyDisabledReason)" @click="toggleReady">
            {{ myMember?.is_ready ? '取消准备' : '准备就绪' }}
          </button>
          <button v-if="isHost" class="primary" :disabled="!canStartGame" @click="startGame">开始游戏</button>
          <p v-if="isHost && startDisabledReason" class="muted">{{ startDisabledReason }}</p>
          <p v-if="!isHost" class="muted">等待房主开始游戏…</p>
        </div>
        <div v-else class="prep">
          <button v-if="isHost" class="danger" @click="endGame">结束本局</button>
        </div>

        <button class="ghost" @click="requestLeaveRoom">退出房间</button>
      </aside>

      <main class="stream">
        <p v-if="aiThinking" class="thinking-banner">
          {{ thinkingLabels[aiThinking.stage] || 'AI DM 正在思考…' }}
        </p>
        <p v-if="typingLabel" class="typing-banner">{{ typingLabel }}</p>
        <div class="messages">
          <div
            v-for="m in messages"
            :key="m.id ?? ('seq' + m.seq)"
            class="msg"
            :data-role="m.sender_role"
            :data-type="m.message_type"
          >
            <div class="msg-head">
              <span class="who">{{ roleLabel(m) }}</span>
              <span class="mtype">{{ messageTypeLabel(m) }}</span>
            </div>
            <div class="msg-body">{{ m.content }}</div>
            <div v-if="m.payload && m.payload.rule_hint" class="rule-hint">
              规则提示：{{ m.payload.rule_hint }}
            </div>
            <div v-if="m.payload && m.payload.suggested_options && m.payload.suggested_options.length" class="options">
              <span v-for="(opt, i) in m.payload.suggested_options" :key="i" class="opt">{{ opt }}</span>
            </div>
            <div v-if="m.payload && m.payload.next_options && m.payload.next_options.length" class="options">
              <span v-for="(opt, i) in m.payload.next_options" :key="i" class="opt">{{ opt }}</span>
            </div>
          </div>
          <p v-if="!messages.length" class="muted center">暂无消息，开始你们的冒险吧。</p>
        </div>

        <div class="composer">
          <div v-if="isPlaying" class="row">
            <input
              v-model="actionInput"
              placeholder="描述你的行动（AI DM 会解析并叙事）"
              @keyup.enter="submitAction"
            />
            <button class="primary" @click="submitAction">行动</button>
          </div>
          <div v-if="isPlaying" class="row">
            <input
              v-model="dmAskInput"
              placeholder="向 AI DM 提问（规则/策略建议，不推进剧情）"
              @keyup.enter="submitDmAsk"
            />
            <button class="ghost" @click="submitDmAsk">问 DM</button>
          </div>
          <div class="row">
            <input v-model="chatInput" placeholder="发送聊天…" @input="onComposerInput" @keyup.enter="sendChat" />
            <button class="ghost" @click="sendChat">聊天</button>
          </div>
          <div class="row">
            <input v-model="oocInput" placeholder="场外讨论（OOC）…" @input="onComposerInput" @keyup.enter="sendOoc" />
            <button class="ghost" @click="sendOoc">OOC</button>
          </div>
        </div>
      </main>
    </section>

    <div v-if="isExitConfirmOpen" class="exit-modal-backdrop" role="presentation">
      <section class="exit-modal" role="dialog" aria-modal="true" aria-labelledby="exit-room-title">
        <h2 id="exit-room-title">确认退出房间？</h2>
        <p>退出房间会导致角色死亡，本次冒险将结束。确定要退出吗？</p>
        <div class="exit-modal-actions">
          <button class="ghost" type="button" @click="cancelLeaveRoom">继续冒险</button>
          <button class="danger" type="button" @click="confirmLeaveRoom">确认退出</button>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.room-shell {
  min-height: 100vh;
  background: #090806;
  color: #e9dcc3;
  padding: 20px 28px;
  box-sizing: border-box;
}
.topbar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}
.topbar h1 { font-size: 20px; color: #f5b95b; margin: 0; flex: 1; }
.ws-badge {
  font-size: 12px; padding: 2px 10px; border-radius: 10px;
  border: 1px solid #6b5a33; text-transform: uppercase;
}
.ws-badge[data-status='online'] { color: #7ee081; border-color: #2f6b34; }
.ws-badge[data-status='reconnecting'], .ws-badge[data-status='connecting'] { color: #f5b95b; }
.error-banner {
  background: #3a1414; color: #ff9f9f; border: 1px solid #6b2323;
  padding: 8px 12px; border-radius: 6px; margin: 8px 0;
}
.lobby { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.panel {
  background: #14110c; border: 1px solid #2c2418; border-radius: 10px; padding: 16px;
  display: flex; flex-direction: column; gap: 10px;
}
.panel.wide { grid-column: 1 / -1; }
.panel h2 { color: #f5b95b; margin: 0 0 4px; font-size: 16px; }
label { display: flex; flex-direction: column; gap: 4px; font-size: 13px; color: #b7a888; }
input, select {
  background: #0c0a07; border: 1px solid #3a3021; color: #e9dcc3;
  padding: 8px 10px; border-radius: 6px; font-size: 14px;
}
button { cursor: pointer; border-radius: 6px; padding: 8px 14px; font-size: 14px; border: none; }
button:disabled { opacity: 0.5; cursor: not-allowed; }
.primary { background: #f5b95b; color: #1a1206; font-weight: 600; }
.primary:disabled { opacity: 0.5; cursor: not-allowed; }
.ghost { background: transparent; border: 1px solid #4a3d26; color: #e9dcc3; }
.danger { background: #6b2323; color: #ffdede; }
.muted { color: #8a7c60; font-size: 13px; }
.center { text-align: center; margin-top: 40px; }
.room-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
.room-list li {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 12px; background: #0c0a07; border: 1px solid #2c2418; border-radius: 8px;
}
.tag {
  font-size: 11px; padding: 1px 8px; border-radius: 8px; margin-left: 6px;
  background: #241d11; border: 1px solid #3a3021; color: #c9b78d;
}
.tag.host { color: #f5b95b; border-color: #6b5a33; }
.tag.ready { color: #7ee081; border-color: #2f6b34; }
.thinking-banner {
  margin: 0 16px; padding: 8px 12px; border-radius: 6px;
  background: rgba(245, 185, 91, 0.08); border: 1px solid #6b5a33;
  color: #f5b95b; font-size: 13px;
}
.typing-banner {
  margin: 0 16px 8px; padding: 4px 12px; font-size: 12px; color: #8a7c60;
}

.room-view { display: grid; grid-template-columns: 300px 1fr; gap: 16px; height: calc(100vh - 90px); }
.side {
  background: #14110c; border: 1px solid #2c2418; border-radius: 10px; padding: 16px;
  display: flex; flex-direction: column; gap: 12px; overflow: auto;
}
.side h2 { color: #f5b95b; margin: 0; font-size: 18px; }
.side h3 { margin: 8px 0 4px; font-size: 13px; color: #b7a888; text-transform: uppercase; }
.members { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
.members li { display: flex; align-items: flex-start; gap: 8px; font-size: 14px; }
.dot { width: 8px; height: 8px; flex: 0 0 8px; margin-top: 6px; border-radius: 50%; background: #555; }
.dot[data-online='online'] { background: #7ee081; }
.member-main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.mname { color: #e9dcc3; overflow-wrap: anywhere; }
.member-character { color: #8a7c60; font-size: 12px; overflow-wrap: anywhere; }
.member-tags { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 4px; max-width: 108px; }
.member-tags .tag { margin-left: 0; }
.prep { display: flex; flex-direction: column; gap: 8px; padding-top: 8px; border-top: 1px solid #2c2418; }

.stream { display: flex; flex-direction: column; background: #14110c; border: 1px solid #2c2418; border-radius: 10px; overflow: hidden; }
.messages { flex: 1; overflow: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; }
.msg { border-left: 3px solid #3a3021; padding: 4px 12px; }
.msg[data-role='ai_dm'] { border-color: #f5b95b; background: #191308; }
.msg[data-role='system'] { border-color: #4a6b8a; }
.msg[data-role='user'] { border-color: #6b5a33; }
.msg-head { display: flex; gap: 8px; align-items: baseline; margin-bottom: 2px; }
.who { font-weight: 600; color: #f5b95b; font-size: 13px; }
.mtype { font-size: 11px; color: #8a7c60; }
.msg-body { font-size: 14px; line-height: 1.6; white-space: pre-wrap; }
.msg[data-type='guidance'] { border-color: #8a7ee0; background: #12101a; }
.msg[data-type='dm_ask'] { border-color: #6b8a9a; }
.rule-hint { margin-top: 6px; font-size: 12px; color: #9a8fc9; font-style: italic; }
.options { margin-top: 6px; display: flex; flex-wrap: wrap; gap: 6px; }
.opt { font-size: 12px; padding: 2px 8px; border: 1px dashed #4a3d26; border-radius: 8px; color: #c9b78d; }
.composer { border-top: 1px solid #2c2418; padding: 12px; display: flex; flex-direction: column; gap: 8px; }
.row { display: flex; gap: 8px; }
.row input { flex: 1; }
.exit-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 30;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgba(0, 0, 0, 0.68);
}
.exit-modal {
  width: min(420px, 100%);
  border: 1px solid #6b5a33;
  border-radius: 10px;
  background: #14110c;
  color: #e9dcc3;
  padding: 24px;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.56);
}
.exit-modal h2 {
  margin: 0 0 12px;
  color: #f5b95b;
  font-size: 20px;
}
.exit-modal p {
  margin: 0;
  color: #b7a888;
  line-height: 1.8;
}
.exit-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 22px;
}
</style>
