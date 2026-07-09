<script setup>
import { computed, onBeforeUnmount, ref, reactive, watch } from 'vue'
import { charactersApi, roomsApi, worldsApi } from './api/client'
import { RoomSocket, newClientMsgId } from './api/wsClient'
import productIcon from '../图标/产品图标.png'

const DEMO_USER_ID = 1

const props = defineProps({
  currentUser: { type: Object, default: null },
  initialRoomId: { type: [Number, String], default: null },
  latestSession: { type: Object, default: null }
})

const emit = defineEmits(['navigate', 'open-settings', 'exit-room', 'game-ended'])

const view = ref('lobby')
const loading = ref(false)
const errorText = ref('')
const statusText = ref('')

const myRooms = ref([])
const publicRooms = ref([])
const worlds = ref([])
const myCharacters = ref([])
const createForm = reactive({ title: '', world_id: null, max_players: 4 })
const joinForm = reactive({ room_code: '' })

const room = ref(null)
const members = ref([])
const messages = ref([])
const messageIds = new Set()
const sessionMeta = ref(null)
const wsStatus = ref('offline')
const aiThinking = ref(null)
const typingUsers = ref({})
const socket = ref(null)
const isExitConfirmOpen = ref(false)
const selectedMemberUserId = ref(null)
const hasEmittedEnding = ref(false)

const activeComposer = ref('main')
const mainInputMode = ref('action')
const mainInput = ref('')
const groupInput = ref('')
const activeRightTab = ref('memo')
const memoContent = ref('')
const activeDiceRoll = ref(null)
let diceHideTimer = null

const myUserId = computed(() => props.currentUser?.id ?? DEMO_USER_ID)
const latestCharacter = computed(() => props.latestSession?.character || null)
const preferredCharacterId = computed(() => latestCharacter.value?.id || myCharacters.value[0]?.id || null)
const isHost = computed(() => Boolean(room.value) && room.value.owner_id === myUserId.value)
const isPlaying = computed(() => room.value?.status === 'playing')
const myMember = computed(() => members.value.find((m) => m.user_id === myUserId.value) || null)
const selectedCharacter = computed(() => {
  const boundId = myMember.value?.character_id
  return myCharacters.value.find((c) => c.id === boundId) || myMember.value?.character || null
})
const currentCharacter = computed(() => {
  if (selectedCharacter.value) return selectedCharacter.value
  if (myMember.value?.character_id && latestCharacter.value?.id === myMember.value.character_id) {
    return latestCharacter.value
  }
  if (myMember.value?.character_name) {
    return {
      id: myMember.value.character_id,
      name: myMember.value.character_name,
      level: 1,
      hp: 10,
      max_hp: 10
    }
  }
  return latestCharacter.value || myCharacters.value[0] || null
})
const selectedMember = computed(() => {
  const selected = members.value.find((m) => m.user_id === selectedMemberUserId.value)
  return selected || myMember.value || members.value[0] || null
})
const selectedCardCharacter = computed(() => {
  const member = selectedMember.value
  if (!member) return currentCharacter.value
  const character = member.character || myCharacters.value.find((c) => c.id === member.character_id)
  if (character) return character
  if (member.character_id && latestCharacter.value?.id === member.character_id) return latestCharacter.value
  if (member.character_name) {
    return {
      id: member.character_id,
      name: member.character_name,
      level: 1,
      hp: null,
      max_hp: null
    }
  }
  return null
})
const selectedCardOwnerName = computed(() => selectedMember.value ? memberDisplayName(selectedMember.value) : '')
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
  if (!myMember.value?.character_id) return '请先完成角色创建'
  return ''
})
const startDisabledReason = computed(() => {
  if (!isHost.value || isPlaying.value || !room.value) return ''
  if (!isRoomFull.value) return `等待成员加入：${memberCountLabel.value}`
  if (!allMembersHaveCharacters.value) return '等待所有成员完成角色创建'
  if (!allMembersReady.value) return '等待所有成员准备就绪'
  return ''
})
const canStartGame = computed(() => isHost.value && !loading.value && !startDisabledReason.value)
const roomTitle = computed(() => room.value?.title || '房间信息')
const roomCode = computed(() => room.value?.room_code || '------')
const currentWorld = computed(() => worlds.value.find((w) => w.id === room.value?.world_id) || null)
const accountName = computed(() => props.currentUser?.nickname || props.currentUser?.username || '游客')
const roomStatusLabel = computed(() => {
  const map = { waiting: '招募中', playing: '进行中', paused: '暂停', finished: '已结束', archived: '已归档' }
  return map[room.value?.status] || room.value?.status || '未知'
})

const typingLabel = computed(() => {
  const names = Object.values(typingUsers.value).filter(Boolean)
  if (!names.length) return ''
  if (names.length === 1) return `${names[0]} 正在输入...`
  return `${names.slice(0, 2).join('、')}${names.length > 2 ? ' 等' : ''} 正在输入...`
})

const thinkingLabels = {
  parsing: 'AI DM 正在解析行动...',
  narrating: 'AI DM 正在撰写叙事...',
  reviewing: 'AI DM 正在审核叙事...',
  rolling: '正在掷骰判定...',
  guidance: 'AI DM 正在思考你的问题...'
}

const memoStorageKey = computed(() => (
  room.value?.id ? `storyforge:room-memo:${myUserId.value}:${room.value.id}` : ''
))

const clearDiceAnimation = () => {
  if (diceHideTimer) {
    window.clearTimeout(diceHideTimer)
    diceHideTimer = null
  }
  activeDiceRoll.value = null
}

const diceRollNumber = (msg) => {
  const payload = msg?.payload || {}
  const candidates = [
    payload.dice_roll,
    payload.final_value,
    payload.roll,
    Number.parseInt(String(msg?.content || '').match(/\d+/)?.[0] || '', 10)
  ]

  for (const candidate of candidates) {
    const value = Number(candidate)
    if (Number.isInteger(value) && value >= 1 && value <= 20) return value
  }
  return null
}

const showDiceAnimation = (msg) => {
  const roll = diceRollNumber(msg)
  if (!roll) return
  clearDiceAnimation()
  activeDiceRoll.value = {
    key: `${msg?.id ?? msg?.seq ?? Date.now()}_${roll}`,
    roll,
    src: `/dice/${roll}.mp4`
  }
  diceHideTimer = window.setTimeout(clearDiceAnimation, 4200)
}

const setError = (err) => {
  errorText.value = err?.message || String(err || '操作失败')
  window.setTimeout(() => { errorText.value = '' }, 4000)
}

const setStatus = (message) => {
  statusText.value = message
  window.setTimeout(() => { statusText.value = '' }, 2200)
}

const mergeLatestCharacter = () => {
  const character = latestCharacter.value
  if (!character?.id) return
  if (!myCharacters.value.some((item) => item.id === character.id)) {
    myCharacters.value = [character, ...myCharacters.value]
  }
}

const loadMyCharacters = async () => {
  const charList = await charactersApi.list().catch(() => [])
  myCharacters.value = charList || []
  mergeLatestCharacter()
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
    mergeLatestCharacter()
    if (!createForm.world_id && worlds.value.length) createForm.world_id = worlds.value[0].id
  } catch (err) {
    setError(err)
  } finally {
    loading.value = false
  }
}

const handleCreate = async () => {
  const title = createForm.title.trim()
  if (!title) {
    setError('需要输入自定义房间名。')
    return
  }
  if (!createForm.world_id) {
    setError('请选择世界观')
    return
  }
  if (!preferredCharacterId.value) {
    emit('navigate', '世界观')
    return
  }
  loading.value = true
  try {
    const detail = await roomsApi.create({
      title,
      world_id: createForm.world_id,
      max_players: Number(createForm.max_players) || 4
    })
    await roomsApi.setCharacter(detail.room.id, preferredCharacterId.value)
    await enterRoom(detail.room.id)
  } catch (err) {
    setError(err)
  } finally {
    loading.value = false
  }
}

const buildRoomJoinWorldview = async (detail) => {
  const roomInfo = detail?.room
  const world =
    worlds.value.find((item) => item.id === roomInfo?.world_id) ||
    (roomInfo?.world_id ? await worldsApi.get(roomInfo.world_id).catch(() => null) : null)
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

const routeToRoomCharacterCreation = async (detail) => {
  const worldview = await buildRoomJoinWorldview(detail)
  setStatus('请先为这个房间创建你的角色。')
  emit('navigate', 'role', worldview)
}

const handleJoin = async () => {
  if (!joinForm.room_code.trim()) {
    setError('请输入房间码')
    return
  }
  loading.value = true
  try {
    const detail = await roomsApi.join({
      room_code: joinForm.room_code.trim().toUpperCase()
    })
    if (!preferredCharacterId.value) {
      await routeToRoomCharacterCreation(detail)
      return
    }
    await roomsApi.setCharacter(detail.room.id, preferredCharacterId.value)
    await enterRoom(detail.room.id)
  } catch (err) {
    setError(err)
  } finally {
    loading.value = false
  }
}

const joinPublicRoom = async (roomCodeValue) => {
  joinForm.room_code = roomCodeValue || ''
  await handleJoin()
}

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
  if (detail.members) {
    members.value = detail.members
    if (!members.value.some((m) => m.user_id === selectedMemberUserId.value)) {
      selectedMemberUserId.value = myMember.value?.user_id || members.value[0]?.user_id || null
    }
  }
}

const refreshRoomDetail = async () => {
  if (!room.value?.id) return
  applyDetail(await roomsApi.get(room.value.id))
}

const emitGameEnded = (detail = null) => {
  if (hasEmittedEnding.value) return
  hasEmittedEnding.value = true
  const endedRoom = detail?.room || room.value || null
  emit('game-ended', {
    room: endedRoom,
    ending: detail?.ending || null,
    members: detail?.members || members.value,
    messages: [...messages.value],
    character: currentCharacter.value,
    sessionId: endedRoom?.current_session_id || room.value?.current_session_id || props.latestSession?.session?.id || null,
    endedAt: new Date().toISOString()
  })
}

const ensureCurrentMemberCharacter = async () => {
  if (!room.value?.id || !myMember.value || myMember.value.character_id || !preferredCharacterId.value) return
  try {
    await roomsApi.setCharacter(room.value.id, preferredCharacterId.value)
    await refreshRoomDetail()
  } catch {
    setError('角色未能自动绑定，请回到角色创建页确认角色已创建。')
  }
}

const handleEvent = (event) => {
  const { type, data } = event
  switch (type) {
    case 'room.snapshot':
      room.value = data.room
      members.value = data.members || []
      if (!members.value.some((m) => m.user_id === selectedMemberUserId.value)) {
        selectedMemberUserId.value = myMember.value?.user_id || members.value[0]?.user_id || null
      }
      messages.value = []
      messageIds.clear()
      ;(data.messages || []).forEach(pushMessage)
      break
    case 'room.updated':
    case 'game.started':
      applyDetail(data)
      break
    case 'game.ended':
      applyDetail(data)
      emitGameEnded(data)
      break
    case 'member.joined':
      if (!members.value.some((m) => m.user_id === data.user_id)) members.value.push(data)
      if (!selectedMemberUserId.value) selectedMemberUserId.value = data.user_id
      break
    case 'member.left':
      members.value = members.value.filter((m) => m.user_id !== data.user_id)
      if (selectedMemberUserId.value === data.user_id) {
        selectedMemberUserId.value = myMember.value?.user_id || members.value[0]?.user_id || null
      }
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
    case 'typing.stop': {
      if (data.user_id === myUserId.value) break
      const next = { ...typingUsers.value }
      delete next[data.user_id]
      typingUsers.value = next
      break
    }
    case 'chat.message':
    case 'ooc.message':
    case 'action.received':
    case 'ai.narration':
    case 'dice.result':
    case 'dice.rolled':
    case 'dm.narration':
    case 'dm.guidance':
      pushMessage(data)
      if (type === 'dice.result') showDiceAnimation(data)
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
    hasEmittedEnding.value = false
    disconnect()
    await loadMyCharacters()
    const detail = await roomsApi.get(roomId)
    applyDetail(detail)
    if (detail.room?.world_id && !worlds.value.some((w) => w.id === detail.room.world_id)) {
      const world = await worldsApi.get(detail.room.world_id).catch(() => null)
      if (world) worlds.value = [...worlds.value, world]
    }
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

function disconnect() {
  if (socket.value) {
    socket.value.close()
    socket.value = null
  }
  clearDiceAnimation()
  wsStatus.value = 'offline'
}

const leaveToLobby = async () => {
  disconnect()
  room.value = null
  members.value = []
  selectedMemberUserId.value = null
  messages.value = []
  messageIds.clear()
  sessionMeta.value = null
  aiThinking.value = null
  if (props.initialRoomId) {
    emit('exit-room')
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
    setError('请先完成角色创建')
    return
  }
  try {
    await roomsApi.setReady(room.value.id, !myMember.value.is_ready)
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
    const result = await roomsApi.start(room.value.id, myMember.value?.character_id || preferredCharacterId.value || null)
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
    const detail = await roomsApi.end(room.value.id)
    applyDetail(detail)
    emitGameEnded(detail)
  } catch (err) {
    setError(err)
  }
}

const sendChatText = async (content) => {
  socket.value?.notifyTyping(false)
  const cid = newClientMsgId()
  if (!socket.value || !socket.value.sendChat(content, cid)) {
    pushMessage(await roomsApi.chat(room.value.id, content, cid))
  }
}

const submitActionText = async (text) => {
  const cid = newClientMsgId()
  if (!socket.value || !socket.value.submitAction(text, cid)) {
    await roomsApi.action(room.value.id, text, cid)
  }
}

const submitDmAskText = async (question) => {
  socket.value?.notifyTyping(false)
  const cid = newClientMsgId()
  if (!socket.value || !socket.value.sendDmAsk(question, cid)) {
    await roomsApi.ask(room.value.id, question, { clientMsgId: cid })
  }
}

const sendComposer = async () => {
  if (!room.value) return
  if (activeComposer.value === 'group') {
    const content = groupInput.value.trim()
    if (!content) return
    groupInput.value = ''
    try {
      await sendChatText(content)
    } catch (err) {
      setError(err)
    }
    return
  }

  const content = mainInput.value.trim()
  if (!content) return
  if (!isPlaying.value) {
    setError('游戏开始后才能提交行动或询问 DM')
    return
  }
  mainInput.value = ''
  try {
    if (mainInputMode.value === 'ask-dm') {
      await submitDmAskText(content)
    } else {
      await submitActionText(content)
    }
  } catch (err) {
    setError(err)
  }
}

const onComposerInput = () => {
  if (activeComposer.value === 'group') socket.value?.notifyTyping(true)
}

const copyRoomCode = async () => {
  if (!room.value?.room_code) return
  try {
    await navigator.clipboard.writeText(room.value.room_code)
    setStatus('邀请码已复制')
  } catch {
    setStatus(`邀请码：${room.value.room_code}`)
  }
}

const messageTypeLabel = (m) => {
  if (m.message_type === 'dm_ask') return '问 DM'
  if (m.message_type === 'chat') return '群聊'
  if (m.message_type === 'narration') return '旁白'
  if (m.message_type === 'guidance') return 'DM 建议'
  if (m.message_type === 'ooc') return '场外'
  if (m.message_type === 'action') return '行动'
  if (m.message_type === 'dice') return '骰点'
  return m.message_type
}

const characterName = (id) => myCharacters.value.find((c) => c.id === id)?.name || null
const memberDisplayName = (m) => m.display_name || `玩家${m.user_id || ''}`
const memberCharacterName = (m) => m.character_name || characterName(m.character_id) || ''
const roleLabel = (m) => (m.sender_role === 'ai_dm' ? 'AI DM' : m.sender_name || `玩家${m.sender_user_id || ''}`)

const classLabel = (id) => {
  const map = {
    fighter: '战士',
    rogue: '游荡者',
    wizard: '法师',
    cleric: '牧师',
    investigator: '调查员',
    detective: '侦探',
    doctor: '医生',
    journalist: '记者'
  }
  return map[id] || id || '冒险者'
}

const raceLabel = (id) => {
  const map = {
    human: '人类',
    elf: '精灵',
    'high-elf': '高等精灵',
    dwarf: '矮人',
    'hill-dwarf': '矮人',
    'lightfoot-halfling': '半身人'
  }
  return map[id] || id || '未知种族'
}

const backgroundLabel = (id) => {
  const map = {
    acolyte: '侍僧',
    criminal: '犯罪者',
    'folk-hero': '民间英雄',
    sage: '学者',
    detective: '侦探',
    soldier: '士兵'
  }
  return map[id] || id || '无背景'
}

const abilityLabels = {
  strength: '力量',
  dexterity: '敏捷',
  constitution: '体质',
  intelligence: '智力',
  wisdom: '感知',
  charisma: '魅力'
}

const skillLabels = {
  acr: '杂技',
  ani: '驯兽',
  arc: '奥秘',
  ath: '运动',
  dec: '欺瞒',
  his: '历史',
  ins: '洞悉',
  itm: '威吓',
  inv: '调查',
  med: '医药',
  nat: '自然',
  prc: '察觉',
  prf: '表演',
  per: '说服',
  rel: '宗教',
  slt: '巧手',
  ste: '隐匿',
  sur: '生存'
}

const worldRuleLabel = computed(() => {
  const style = currentWorld.value?.rule_style
  if (style === 'lite_dnd') return 'DND 5e'
  return currentWorld.value?.name || '世界观'
})

const isDndCharacter = (character) => {
  const style = currentWorld.value?.rule_style || ''
  const worldName = `${currentWorld.value?.name || ''} ${currentWorld.value?.description || ''}`.toLowerCase()
  return style.includes('dnd') || worldName.includes('dnd') || worldName.includes('龙与地下城') || Boolean(character?.attributes)
}

const formatModifier = (score) => {
  const value = Number(score)
  if (!Number.isFinite(value)) return '--'
  const modifier = Math.floor((value - 10) / 2)
  return modifier >= 0 ? `+${modifier}` : String(modifier)
}

const attributeRows = (character) => {
  const attrs = character?.attributes || {}
  return Object.entries(abilityLabels).map(([key, label]) => ({
    key,
    label,
    value: attrs[key] ?? '--',
    modifier: formatModifier(attrs[key])
  }))
}

const savingThrowLabels = (character) => (character?.saving_throws || [])
  .map((key) => abilityLabels[key] || key)

const proficientSkillLabels = (character) => Object.entries(character?.skills || {})
  .filter(([, value]) => value?.proficient)
  .map(([key]) => skillLabels[key] || key)

const selectedCardAttributes = computed(() => attributeRows(selectedCardCharacter.value))
const selectedCardSavingThrows = computed(() => savingThrowLabels(selectedCardCharacter.value))
const selectedCardSkills = computed(() => proficientSkillLabels(selectedCardCharacter.value))
const selectedCardIsDnd = computed(() => isDndCharacter(selectedCardCharacter.value))

const characterSummary = (character) => {
  if (!character) return '角色待创建'
  const pieces = [`Lv.${character.level || 1}`, classLabel(character.class_id || character.profession)]
  if (character.race_id) pieces.unshift(raceLabel(character.race_id))
  return pieces.join(' · ')
}

const hpPercent = (character) => {
  const hp = Number(character?.hp)
  const maxHp = Number(character?.max_hp)
  if (!Number.isFinite(hp) || !Number.isFinite(maxHp) || maxHp <= 0) return 100
  return Math.max(0, Math.min(100, Math.round((hp / maxHp) * 100)))
}

const teammateRows = computed(() => members.value.map((member, index) => {
  const character = member.character || myCharacters.value.find((item) => item.id === member.character_id)
  const hasHp = Number.isFinite(Number(character?.hp)) && Number.isFinite(Number(character?.max_hp))
  return {
    member,
    character,
    name: memberCharacterName(member) || '角色创建中',
    playerName: memberDisplayName(member),
    level: character?.level || 1,
    hpLabel: hasHp ? `${character.hp}/${character.max_hp}` : (member.character_id ? '已绑定' : '待创建'),
    hpWidth: hasHp ? hpPercent(character) : (member.character_id ? 100 : 0),
    avatarText: memberCharacterName(member)?.slice(0, 1) || String(index + 1),
    summary: characterSummary(character),
    selected: selectedMember.value?.user_id === member.user_id
  }
}))

const visibleMessages = computed(() => {
  if (activeComposer.value === 'group') {
    return messages.value.filter((msg) => msg.message_type === 'chat' || msg.message_type === 'ooc')
  }
  return messages.value.filter((msg) => msg.message_type !== 'chat' && msg.message_type !== 'ooc')
})

const actionLogRows = computed(() => messages.value
  .filter((msg) => ['action', 'dice', 'narration', 'guidance', 'dm_ask'].includes(msg.message_type))
  .slice(-12)
  .reverse()
)

const composerPlaceholder = computed(() => {
  if (activeComposer.value === 'group') return '发送房间内自由聊天...'
  if (!isPlaying.value) return '游戏开始后可提交行动或询问 DM...'
  return mainInputMode.value === 'ask-dm' ? '向 AI DM 提问...' : '描述你的动作...'
})

watch(memoStorageKey, (key) => {
  memoContent.value = key ? window.localStorage.getItem(key) || '' : ''
}, { immediate: true })

watch(memoContent, (value) => {
  if (!memoStorageKey.value) return
  window.localStorage.setItem(memoStorageKey.value, value)
})

watch(latestCharacter, mergeLatestCharacter, { immediate: true })

watch(
  () => props.initialRoomId,
  (id) => {
    if (id && (!room.value || room.value.id !== Number(id))) {
      enterRoom(Number(id))
    }
  },
  { immediate: true }
)

if (!props.initialRoomId) {
  loadLobby()
}

onBeforeUnmount(disconnect)
</script>

<template>
  <div class="room-shell">
    <p v-if="errorText" class="toast error-toast">{{ errorText }}</p>
    <p v-if="statusText" class="toast status-toast">{{ statusText }}</p>

    <section v-if="view === 'lobby'" class="room-lobby">
      <header class="lobby-topbar">
        <button class="ghost-btn" type="button" @click="emit('navigate', 'home')">返回大厅</button>
        <h1>多人房间</h1>
        <button class="icon-btn" type="button" aria-label="设置" title="设置" @click="emit('open-settings')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5v.2a2 2 0 1 1-4 0v-.2a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.2a1.7 1.7 0 0 0 1.5-1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3 1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.2a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8 1.7 1.7 0 0 0 1.5 1h.2a2 2 0 1 1 0 4h-.2a1.7 1.7 0 0 0-1.5 1Z" />
          </svg>
        </button>
      </header>

      <main class="lobby-grid">
        <form class="lobby-panel" @submit.prevent="handleCreate">
          <h2>创建房间</h2>
          <label>房间名称
            <input v-model="createForm.title" placeholder="请输入自定义房间名" />
          </label>
          <label>世界观
            <select v-model="createForm.world_id">
              <option v-for="w in worlds" :key="w.id" :value="w.id">{{ w.name }}</option>
            </select>
          </label>
          <label>人数上限
            <input v-model.number="createForm.max_players" type="number" min="1" max="12" />
          </label>
          <button class="primary-btn" type="submit" :disabled="loading">创建并进入</button>
        </form>

        <form class="lobby-panel" @submit.prevent="handleJoin">
          <h2>加入房间</h2>
          <label>房间码
            <input v-model="joinForm.room_code" placeholder="6 位房间码" maxlength="12" />
          </label>
          <p class="muted-line">当前角色：{{ currentCharacter?.name || '角色待创建' }}</p>
          <button class="primary-btn" type="submit" :disabled="loading">加入</button>
        </form>

        <section class="lobby-panel wide">
          <h2>我的房间</h2>
          <ul v-if="myRooms.length" class="room-list">
            <li v-for="r in myRooms" :key="r.id">
              <div>
                <strong>{{ r.title }}</strong>
                <span>{{ r.room_code }}</span>
                <span>{{ r.status }}</span>
              </div>
              <button class="ghost-btn" type="button" @click="enterRoom(r.id)">进入</button>
            </li>
          </ul>
          <p v-else class="muted-line">还没有房间。</p>
        </section>

        <section class="lobby-panel wide">
          <h2>公开房间</h2>
          <ul v-if="publicRooms.length" class="room-list">
            <li v-for="r in publicRooms" :key="`pub_${r.id}`">
              <div>
                <strong>{{ r.title }}</strong>
                <span>{{ r.room_code }}</span>
                <span>{{ r.status }}</span>
              </div>
              <button class="ghost-btn" type="button" @click="joinPublicRoom(r.room_code)">加入</button>
            </li>
          </ul>
          <p v-else class="muted-line">暂无可加入的公开房间。</p>
        </section>
      </main>
    </section>

    <template v-else>
      <header class="navbar">
        <div class="logo-area">
          <img :src="productIcon" alt="StoryForge Icon" />
          <span>StoryForge</span>
        </div>

        <button class="room-header-info" type="button" @click="copyRoomCode">
          <span>{{ roomTitle }}</span>
          <small>邀请码 {{ roomCode }}</small>
        </button>

        <div class="user-area">
          <span class="ws-badge" :data-status="wsStatus">{{ wsStatus }}</span>
          <span class="user-label">{{ accountName }}</span>
          <button class="icon-btn icon-btn--pending" type="button" aria-label="待开发" title="待开发" disabled>
            待开发
          </button>
          <button class="icon-btn" type="button" aria-label="设置" title="设置" @click="emit('open-settings')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5v.2a2 2 0 1 1-4 0v-.2a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.2a1.7 1.7 0 0 0 1.5-1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3 1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.2a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8 1.7 1.7 0 0 0 1.5 1h.2a2 2 0 1 1 0 4h-.2a1.7 1.7 0 0 0-1.5 1Z" />
            </svg>
          </button>
        </div>
      </header>

      <main class="main-container">
        <aside class="left-panel-wrapper">
          <section class="panel char-selected-box">
            <div class="character-card-main">
              <div class="character-avatar large">
                {{ selectedCardCharacter?.name?.slice(0, 1) || '?' }}
              </div>
              <div class="character-copy">
                <p>选中角色 · {{ selectedCardOwnerName || '未入席' }}</p>
                <h2>{{ selectedCardCharacter?.name || '角色待创建' }}</h2>
                <span>{{ characterSummary(selectedCardCharacter) }}</span>
                <div class="hp-row">
                  <small>HP {{ selectedCardCharacter?.hp ?? '--' }}/{{ selectedCardCharacter?.max_hp ?? '--' }}</small>
                  <div class="mini-bar-bg">
                    <div class="mini-bar-fill" :style="{ width: `${hpPercent(selectedCardCharacter)}%` }"></div>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="selectedCardCharacter" class="character-sheet">
              <div class="sheet-meta-grid">
                <span>
                  <small>规则</small>
                  <strong>{{ worldRuleLabel }}</strong>
                </span>
                <span>
                  <small>种族</small>
                  <strong>{{ raceLabel(selectedCardCharacter.race_id) }}</strong>
                </span>
                <span>
                  <small>职业</small>
                  <strong>{{ classLabel(selectedCardCharacter.class_id || selectedCardCharacter.profession) }}</strong>
                </span>
                <span>
                  <small>背景</small>
                  <strong>{{ backgroundLabel(selectedCardCharacter.background_id) }}</strong>
                </span>
                <span>
                  <small>等级</small>
                  <strong>Lv.{{ selectedCardCharacter.level || 1 }}</strong>
                </span>
                <span>
                  <small>熟练</small>
                  <strong>+{{ selectedCardCharacter.proficiency_bonus || 2 }}</strong>
                </span>
              </div>

              <div v-if="selectedCardIsDnd" class="ability-grid">
                <span v-for="attr in selectedCardAttributes" :key="attr.key">
                  <small>{{ attr.label }}</small>
                  <strong>{{ attr.value }}</strong>
                  <em>{{ attr.modifier }}</em>
                </span>
              </div>

              <div v-if="selectedCardIsDnd" class="sheet-tags">
                <div>
                  <small>豁免</small>
                  <p>{{ selectedCardSavingThrows.length ? selectedCardSavingThrows.join('、') : '暂无' }}</p>
                </div>
                <div>
                  <small>技能熟练</small>
                  <p>{{ selectedCardSkills.length ? selectedCardSkills.join('、') : '暂无' }}</p>
                </div>
              </div>
            </div>

          </section>

          <section class="panel room-control-panel">
            <p class="room-state">状态 {{ roomStatusLabel }} · 成员 {{ memberCountLabel }}</p>
            <button
              v-if="!isPlaying"
              class="ghost-btn fill"
              type="button"
              :disabled="Boolean(readyDisabledReason)"
              @click="toggleReady"
            >
              {{ myMember?.is_ready ? '取消准备' : '准备就绪' }}
            </button>
            <button
              v-if="!isPlaying && myMember && !myMember.character_id"
              class="primary-btn fill"
              type="button"
              @click="routeToRoomCharacterCreation({ room })"
            >
              创建我的角色
            </button>
            <button
              v-if="isHost && !isPlaying"
              class="primary-btn fill"
              type="button"
              :disabled="!canStartGame"
              @click="startGame"
            >
              开始游戏
            </button>
            <button v-if="isHost && isPlaying" class="danger-btn fill" type="button" @click="endGame">结束本局</button>
            <p v-if="!isPlaying && (startDisabledReason || readyDisabledReason)" class="muted-line">
              {{ startDisabledReason || readyDisabledReason }}
            </p>
          </section>

          <section class="panel char-list-box">
            <div class="list-header">房间内角色列表</div>
            <div class="teammates-container">
              <button
                v-for="row in teammateRows"
                :key="row.member.user_id"
                class="teammate"
                :class="{ selected: row.selected }"
                type="button"
                @click="selectedMemberUserId = row.member.user_id"
              >
                <div class="character-avatar">{{ row.avatarText }}</div>
                <div class="teammate-info">
                  <h3>
                    {{ row.name }}
                    <span>Lv.{{ row.level }}</span>
                  </h3>
                  <p>{{ row.summary }}</p>
                  <p>{{ row.playerName }} · HP {{ row.hpLabel }}</p>
                  <div class="mini-bar-bg">
                    <div class="mini-bar-fill" :style="{ width: `${row.hpWidth}%` }"></div>
                  </div>
                </div>
                <span class="ready-dot" :class="{ active: row.member.is_ready || isPlaying }"></span>
              </button>
            </div>
          </section>

          <button class="ghost-btn fill" type="button" @click="requestLeaveRoom">退出房间</button>
        </aside>

        <section class="panel center-panel">
          <p v-if="aiThinking" class="thinking-banner">
            {{ thinkingLabels[aiThinking.stage] || 'AI DM 正在思考...' }}
          </p>
          <p v-if="typingLabel" class="typing-banner">{{ typingLabel }}</p>

          <div class="chat-area">
            <article
              v-for="m in visibleMessages"
              :key="m.id ?? ('seq' + m.seq)"
              class="msg"
              :data-role="m.sender_role"
              :data-type="m.message_type"
            >
              <div class="msg-head">
                <strong>{{ roleLabel(m) }}</strong>
                <span>{{ messageTypeLabel(m) }}</span>
              </div>
              <p>{{ m.content }}</p>
              <div v-if="m.payload?.rule_hint" class="rule-hint">规则提示：{{ m.payload.rule_hint }}</div>
              <div v-if="m.payload?.suggested_options?.length" class="options">
                <span v-for="(opt, i) in m.payload.suggested_options" :key="i">{{ opt }}</span>
              </div>
              <div v-if="m.payload?.next_options?.length" class="options">
                <span v-for="(opt, i) in m.payload.next_options" :key="i">{{ opt }}</span>
              </div>
            </article>
            <div v-if="!visibleMessages.length" class="placeholder-text">实时对话</div>
          </div>

          <div class="input-section">
            <div class="input-tabs">
              <button
                type="button"
                :class="{ active: activeComposer === 'main' }"
                @click="activeComposer = 'main'"
              >
                主页
              </button>
              <button
                type="button"
                :class="{ active: activeComposer === 'group' }"
                @click="activeComposer = 'group'"
              >
                群聊
              </button>
            </div>
            <div class="input-box">
              <select
                v-if="activeComposer === 'main'"
                v-model="mainInputMode"
                class="action-selector"
                title="选择输入模式"
              >
                <option value="action">行动</option>
                <option value="ask-dm">询问 DM</option>
              </select>

              <input
                :value="activeComposer === 'group' ? groupInput : mainInput"
                :placeholder="composerPlaceholder"
                :disabled="activeComposer === 'main' && !isPlaying"
                @input="activeComposer === 'group' ? (groupInput = $event.target.value) : (mainInput = $event.target.value); onComposerInput()"
                @keyup.enter="sendComposer"
              />
              <button class="send-btn" type="button" :disabled="activeComposer === 'main' && !isPlaying" @click="sendComposer">
                发送
              </button>
            </div>
          </div>
        </section>

        <aside class="panel right-panel">
          <h2>功能面板</h2>
          <transition name="dice-pop">
            <div v-if="activeDiceRoll" class="dice-stage" aria-live="polite">
              <video
                :key="activeDiceRoll.key"
                class="dice-video"
                :src="activeDiceRoll.src"
                autoplay
                muted
                playsinline
                preload="auto"
                @ended="clearDiceAnimation"
                @error="clearDiceAnimation"
              ></video>
              <div class="dice-stage-meta">
                <strong>{{ activeDiceRoll.roll }}</strong>
                <span>骰点结果</span>
              </div>
            </div>
          </transition>
          <div class="right-tabs">
            <button
              type="button"
              :class="{ active: activeRightTab === 'memo' }"
              @click="activeRightTab = 'memo'"
            >
              备忘录
            </button>
            <button
              type="button"
              :class="{ active: activeRightTab === 'log' }"
              @click="activeRightTab = 'log'"
            >
              行动日志
            </button>
          </div>

          <div class="right-content">
            <textarea
              v-if="activeRightTab === 'memo'"
              v-model="memoContent"
              class="memo-textarea"
              placeholder="记录线索、NPC 名字或个人日志..."
            ></textarea>

            <div v-else class="action-log">
              <article v-for="m in actionLogRows" :key="m.id ?? ('log' + m.seq)" class="log-item">
                <span>{{ messageTypeLabel(m) }}</span>
                <p>{{ m.content }}</p>
              </article>
              <p v-if="!actionLogRows.length" class="muted-line">暂无行动日志。</p>
            </div>
          </div>
        </aside>
      </main>

      <div v-if="isExitConfirmOpen" class="exit-modal-backdrop" role="presentation">
        <section class="exit-modal" role="dialog" aria-modal="true" aria-labelledby="exit-room-title">
          <h2 id="exit-room-title">确认退出房间？</h2>
          <p>退出房间会导致角色死亡，本次冒险将结束。确定要退出吗？</p>
          <div class="exit-modal-actions">
            <button class="ghost-btn" type="button" @click="cancelLeaveRoom">继续冒险</button>
            <button class="danger-btn" type="button" @click="confirmLeaveRoom">确认退出</button>
          </div>
        </section>
      </div>
    </template>
  </div>
</template>

<style scoped>
.room-shell {
  --bg-dark: #0b0a09;
  --panel-bg: rgba(22, 19, 17, 0.85);
  --border-gold: #4a3c2a;
  --border-soft: #332a1f;
  --text-gold: #d4b886;
  --text-light: #e0d6c8;
  --text-dim: #8b7d6b;
  --hp-red: #8b2621;
  min-height: 100vh;
  background:
    radial-gradient(circle at center, #1a1614 0%, #0b0a09 100%);
  color: var(--text-light);
  font-family: 'Noto Serif SC', 'Source Han Serif SC', 'SimSun', serif;
  overflow: hidden;
}

button,
input,
select,
textarea {
  font: inherit;
}

button {
  cursor: pointer;
}

button:disabled,
input:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.toast {
  position: fixed;
  top: 72px;
  left: 50%;
  z-index: 80;
  transform: translateX(-50%);
  max-width: min(720px, calc(100vw - 32px));
  padding: 10px 16px;
  border-radius: 6px;
  font-size: 13px;
}

.error-toast {
  border: 1px solid #6b2323;
  background: #3a1414;
  color: #ffb6b6;
}

.status-toast {
  border: 1px solid #4a3c2a;
  background: #17120c;
  color: var(--text-gold);
}

.navbar {
  display: grid;
  grid-template-columns: 220px 1fr 260px;
  align-items: center;
  height: 60px;
  padding: 10px 20px;
  border-bottom: 1px solid var(--border-gold);
  background: rgba(10, 8, 7, 0.92);
}

.logo-area,
.user-area {
  display: flex;
  align-items: center;
}

.logo-area {
  gap: 10px;
  color: var(--text-gold);
  font-size: 18px;
  font-weight: 700;
}

.logo-area img {
  width: 30px;
  height: 30px;
  object-fit: contain;
}

.room-header-info {
  display: grid;
  gap: 2px;
  justify-items: center;
  border: 0;
  background: transparent;
  color: var(--text-light);
  text-align: center;
}

.room-header-info span {
  max-width: min(620px, 52vw);
  overflow: hidden;
  font-size: 16px;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.room-header-info small {
  color: var(--text-dim);
  font-size: 12px;
  transition: color 0.2s ease;
}

.room-header-info:hover small {
  color: var(--text-gold);
}

.user-area {
  justify-content: flex-end;
  gap: 12px;
}

.user-label {
  max-width: 92px;
  overflow: hidden;
  color: var(--text-light);
  font-size: 14px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.icon-btn {
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  border: 1px solid var(--border-gold);
  border-radius: 4px;
  background: transparent;
  color: var(--text-gold);
  transition: background 0.2s ease, color 0.2s ease;
}

.icon-btn--pending {
  width: auto;
  min-width: 68px;
  padding: 0 12px;
  border-radius: 999px;
  font-size: 12px;
  letter-spacing: 0;
}

.icon-btn svg {
  width: 17px;
  height: 17px;
}

.icon-btn:hover {
  background: var(--border-gold);
  color: var(--bg-dark);
}

.ws-badge {
  padding: 2px 8px;
  border: 1px solid var(--border-gold);
  border-radius: 999px;
  color: var(--text-dim);
  font-size: 11px;
  text-transform: uppercase;
}

.ws-badge[data-status='online'] {
  border-color: #2f6b34;
  color: #8ee08f;
}

.main-container {
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr) 280px;
  gap: 15px;
  height: calc(100vh - 60px);
  padding: 15px;
  overflow: hidden;
}

.panel {
  min-height: 0;
  border: 1px solid var(--border-gold);
  border-radius: 12px;
  background: var(--panel-bg);
  overflow: hidden;
}

.left-panel-wrapper {
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 15px;
  overflow-y: auto;
  padding-right: 5px;
}

.char-selected-box {
  flex: 0 1 auto;
  max-height: min(620px, calc(100vh - 315px));
  display: grid;
  gap: 14px;
  align-content: start;
  padding: 15px;
  overflow-y: auto;
}

.character-card-main {
  display: flex;
  align-items: center;
  gap: 15px;
}

.character-avatar {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  border: 1px solid var(--border-gold);
  border-radius: 4px;
  background:
    radial-gradient(circle at 30% 30%, rgba(212, 184, 134, 0.22), transparent 34%),
    #3a2e24;
  color: var(--text-gold);
  font-weight: 700;
}

.character-avatar.large {
  width: 64px;
  height: 64px;
  font-size: 24px;
}

.character-copy {
  min-width: 0;
  flex: 1;
}

.character-copy p,
.teammate-info p,
.room-state,
.muted-line {
  color: var(--text-dim);
  font-size: 12px;
  line-height: 1.5;
}

.character-copy h2 {
  overflow-wrap: anywhere;
  color: var(--text-gold);
  font-size: 17px;
  line-height: 1.25;
}

.character-copy span {
  color: var(--text-dim);
  font-size: 12px;
}

.hp-row {
  display: grid;
  gap: 5px;
  margin-top: 8px;
}

.hp-row small {
  color: var(--text-light);
  font-size: 12px;
}

.character-sheet {
  display: grid;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border-soft);
}

.sheet-meta-grid,
.ability-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.sheet-meta-grid span,
.ability-grid span {
  min-width: 0;
  display: grid;
  gap: 2px;
  padding: 7px 8px;
  border: 1px solid var(--border-soft);
  border-radius: 6px;
  background: rgba(10, 8, 7, 0.32);
}

.sheet-meta-grid small,
.ability-grid small,
.sheet-tags small {
  color: var(--text-dim);
  font-size: 11px;
  line-height: 1.2;
}

.sheet-meta-grid strong,
.ability-grid strong {
  min-width: 0;
  overflow: hidden;
  color: var(--text-light);
  font-size: 13px;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ability-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.ability-grid span {
  place-items: center;
  text-align: center;
}

.ability-grid strong {
  color: var(--text-gold);
  font-size: 16px;
}

.ability-grid em {
  color: var(--text-dim);
  font-size: 11px;
  font-style: normal;
}

.sheet-tags {
  display: grid;
  gap: 8px;
}

.sheet-tags div {
  display: grid;
  gap: 3px;
}

.sheet-tags p {
  color: var(--text-light);
  font-size: 12px;
  line-height: 1.5;
}

.prep-actions {
  display: grid;
  gap: 8px;
}

.room-control-panel {
  flex: 0 0 auto;
  display: grid;
  gap: 8px;
  padding: 14px;
}

.char-list-box {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.list-header {
  flex: 0 0 auto;
  padding: 12px;
  border-bottom: 1px solid var(--border-gold);
  background: rgba(10, 8, 7, 0.5);
  color: var(--text-gold);
  font-size: 15px;
  font-weight: 700;
  text-align: center;
}

.teammates-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 15px;
  overflow-y: auto;
}

.teammate {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 10px;
  border: 1px solid var(--border-soft);
  border-radius: 8px;
  background: rgba(10, 8, 7, 0.6);
  color: inherit;
  text-align: left;
  transition: border-color 0.2s ease, background 0.2s ease;
}

.teammate:hover,
.teammate:focus-visible,
.teammate.selected {
  border-color: var(--text-gold);
  background: rgba(32, 24, 14, 0.74);
}

.teammate:focus-visible {
  outline: 1px solid var(--text-gold);
  outline-offset: 2px;
}

.teammate-info {
  min-width: 0;
  flex: 1;
}

.teammate-info h3 {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  color: var(--text-light);
  font-size: 14px;
}

.teammate-info h3 span {
  color: var(--text-dim);
  font-size: 12px;
  font-weight: 400;
}

.ready-dot {
  width: 8px;
  height: 8px;
  flex: 0 0 auto;
  border-radius: 50%;
  background: #554d42;
}

.ready-dot.active {
  background: #7ee081;
}

.mini-bar-bg {
  width: 100%;
  height: 4px;
  margin-top: 5px;
  border-radius: 2px;
  background: #222;
  overflow: hidden;
}

.mini-bar-fill {
  height: 100%;
  border-radius: inherit;
  background: var(--hp-red);
}

.center-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 15px;
}

.thinking-banner,
.typing-banner {
  flex: 0 0 auto;
  margin: 0;
  padding: 8px 12px;
  border: 1px solid var(--border-gold);
  border-radius: 6px;
  background: rgba(10, 8, 7, 0.5);
  color: var(--text-gold);
  font-size: 13px;
}

.typing-banner {
  margin-top: -4px;
  color: var(--text-dim);
}

.chat-area {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: stretch;
  border: 1px dashed var(--border-soft);
  border-radius: 8px;
  padding: 15px;
  overflow-y: auto;
}

.placeholder-text {
  margin: auto;
  color: var(--text-dim);
  font-size: 20px;
  letter-spacing: 2px;
}

.msg {
  border-left: 3px solid var(--border-soft);
  padding: 8px 12px;
  background: rgba(10, 8, 7, 0.34);
}

.msg[data-role='ai_dm'] {
  border-color: var(--text-gold);
  background: rgba(32, 24, 14, 0.58);
}

.msg[data-type='guidance'],
.msg[data-type='dm_ask'] {
  border-color: #6b8a9a;
}

.msg-head {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 4px;
}

.msg-head strong {
  color: var(--text-gold);
  font-size: 13px;
}

.msg-head span {
  color: var(--text-dim);
  font-size: 11px;
}

.msg p {
  color: var(--text-light);
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
}

.rule-hint,
.options span {
  color: #a99fd4;
  font-size: 12px;
}

.options {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.options span {
  padding: 2px 8px;
  border: 1px dashed var(--border-gold);
  border-radius: 999px;
  color: var(--text-gold);
}

.input-section {
  flex: 0 0 auto;
  border: 1px solid var(--border-gold);
  border-radius: 8px;
  overflow: hidden;
}

.input-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-soft);
  background: rgba(10, 8, 7, 0.8);
}

.input-tabs button {
  flex: 1;
  border: 0;
  background: transparent;
  color: var(--text-dim);
  padding: 10px;
  transition: color 0.2s ease, background 0.2s ease;
}

.input-tabs button.active {
  background: rgba(30, 25, 22, 0.9);
  color: var(--text-gold);
  font-weight: 700;
}

.input-box {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: rgba(20, 17, 15, 0.9);
}

.action-selector,
.input-box input {
  min-height: 38px;
  border: 1px solid var(--border-gold);
  border-radius: 4px;
  outline: none;
  background: rgba(10, 8, 7, 0.9);
  color: var(--text-light);
}

.action-selector {
  width: 112px;
  padding: 0 10px;
  color: var(--text-gold);
}

.input-box input {
  flex: 1;
  min-width: 0;
  padding: 0 10px;
}

.input-box input::placeholder,
.memo-textarea::placeholder {
  color: #554d42;
}

.send-btn,
.primary-btn,
.ghost-btn,
.danger-btn {
  min-height: 38px;
  border-radius: 4px;
  padding: 0 16px;
}

.send-btn,
.primary-btn {
  border: 0;
  background: var(--text-gold);
  color: #090806;
  font-weight: 700;
}

.ghost-btn {
  border: 1px solid var(--border-gold);
  background: transparent;
  color: var(--text-light);
}

.danger-btn {
  border: 1px solid #7a302b;
  background: #6b2323;
  color: #ffdede;
}

.fill {
  width: 100%;
}

.right-panel {
  display: flex;
  flex-direction: column;
}

.right-panel h2 {
  flex: 0 0 auto;
  padding: 12px;
  border-bottom: 1px solid var(--border-gold);
  background: rgba(10, 8, 7, 0.5);
  color: var(--text-gold);
  font-size: 16px;
  text-align: center;
}

.dice-stage {
  display: grid;
  gap: 10px;
  flex: 0 0 auto;
  padding: 12px;
  border-bottom: 1px solid var(--border-soft);
  background: rgba(10, 8, 7, 0.72);
}

.dice-video {
  width: 100%;
  aspect-ratio: 1 / 1;
  object-fit: contain;
  border: 1px solid var(--border-soft);
  border-radius: 8px;
  background: #090806;
}

.dice-stage-meta {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
  color: var(--text-gold);
}

.dice-stage-meta strong {
  font-size: 26px;
  line-height: 1;
}

.dice-stage-meta span {
  color: var(--text-dim);
  font-size: 12px;
}

.right-tabs {
  display: flex;
  flex: 0 0 auto;
  border-bottom: 1px solid var(--border-soft);
}

.right-tabs button {
  flex: 1;
  border: 0;
  border-bottom: 2px solid transparent;
  background: transparent;
  color: var(--text-dim);
  padding: 10px;
}

.right-tabs button.active {
  border-bottom-color: var(--text-gold);
  color: var(--text-gold);
}

.right-content {
  flex: 1;
  min-height: 0;
  display: flex;
  padding: 15px;
}

.memo-textarea {
  flex: 1;
  width: 100%;
  resize: none;
  outline: none;
  border: 1px dashed var(--border-soft);
  border-radius: 8px;
  background: rgba(10, 8, 7, 0.3);
  color: var(--text-light);
  padding: 12px;
  line-height: 1.6;
}

.memo-textarea:focus {
  border-color: var(--border-gold);
  background: rgba(10, 8, 7, 0.6);
}

.action-log {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
}

.log-item {
  display: grid;
  gap: 5px;
  padding: 10px;
  border: 1px solid var(--border-soft);
  border-radius: 6px;
  background: rgba(10, 8, 7, 0.4);
}

.log-item span {
  color: var(--text-gold);
  font-size: 12px;
}

.log-item p {
  display: -webkit-box;
  overflow: hidden;
  color: var(--text-light);
  font-size: 13px;
  line-height: 1.55;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 4;
}

.room-lobby {
  min-height: 100vh;
  padding: 20px 28px;
  background: #090806;
}

.lobby-topbar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.lobby-topbar h1 {
  flex: 1;
  color: var(--text-gold);
  font-size: 20px;
}

.lobby-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.lobby-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  border: 1px solid var(--border-soft);
  border-radius: 10px;
  background: #14110c;
}

.lobby-panel.wide {
  grid-column: 1 / -1;
}

.lobby-panel h2 {
  color: var(--text-gold);
  font-size: 16px;
}

.lobby-panel label {
  display: grid;
  gap: 5px;
  color: #b7a888;
  font-size: 13px;
}

.lobby-panel input,
.lobby-panel select {
  min-height: 38px;
  border: 1px solid #3a3021;
  border-radius: 6px;
  background: #0c0a07;
  color: var(--text-light);
  padding: 0 10px;
}

.room-list {
  display: grid;
  gap: 8px;
  list-style: none;
}

.room-list li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  border: 1px solid var(--border-soft);
  border-radius: 8px;
  background: #0c0a07;
}

.room-list div {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.room-list strong {
  color: var(--text-light);
}

.room-list span {
  color: var(--text-dim);
}

.exit-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 70;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgba(0, 0, 0, 0.68);
}

.exit-modal {
  width: min(420px, 100%);
  border: 1px solid var(--border-gold);
  border-radius: 10px;
  background: #14110c;
  color: var(--text-light);
  padding: 24px;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.56);
}

.exit-modal h2 {
  margin-bottom: 12px;
  color: var(--text-gold);
  font-size: 20px;
}

.exit-modal p {
  color: #b7a888;
  line-height: 1.8;
}

.exit-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 22px;
}

::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  border-radius: 3px;
  background: #3a2e24;
}

.dice-pop-enter-active,
.dice-pop-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.dice-pop-enter-from,
.dice-pop-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

@media (max-width: 1120px) {
  .navbar {
    grid-template-columns: auto 1fr auto;
  }

  .user-label,
  .ws-badge {
    display: none;
  }

  .main-container {
    grid-template-columns: 260px minmax(0, 1fr);
  }

  .right-panel {
    display: none;
  }
}

@media (max-width: 820px) {
  .room-shell {
    overflow: auto;
  }

  .navbar {
    grid-template-columns: 1fr auto;
    height: auto;
    gap: 10px;
  }

  .room-header-info {
    grid-column: 1 / -1;
    order: 3;
  }

  .main-container {
    grid-template-columns: 1fr;
    height: auto;
    min-height: calc(100vh - 84px);
    overflow: visible;
  }

  .center-panel {
    min-height: 620px;
  }

  .char-selected-box {
    max-height: none;
  }

  .lobby-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 560px) {
  .input-box {
    align-items: stretch;
    flex-direction: column;
  }

  .action-selector,
  .send-btn {
    width: 100%;
  }

  .character-card-main {
    align-items: flex-start;
  }
}
</style>
