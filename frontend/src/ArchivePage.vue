<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { sessionsApi } from './api/client'
import AppNavbar from './components/AppNavbar.vue'
import hallBackground from '../背景/大厅界面.png'
import goblinCover from '../游戏种类/哥布林.jpg'
import dndCover from '../游戏种类/龙与地下城.jpg'
import dndCoverAlt from '../游戏种类/龙与地下城二.jpg'

const emit = defineEmits(['navigate', 'logout', 'enter-room', 'back-button-hidden', 'open-settings'])

const props = defineProps({
  currentUser: {
    type: Object,
    default: null
  },
  latestSession: {
    type: Object,
    default: null
  }
})

const searchKeyword = ref('')
const selectedArchiveId = ref(null)
const sessions = ref([])
const isLoading = ref(false)
const deletingArchiveId = ref(null)
const archiveStatus = ref('')

const statusLabels = {
  playing: '进行中',
  finished: '已结束',
  archived: '已归档'
}

const statusClasses = {
  playing: 'state-running',
  finished: 'state-finished',
  archived: 'state-paused'
}

const fallbackArchive = {
  id: 'module-krenko-preview',
  sessionId: null,
  roomId: null,
  worldName: '龙与地下城 DND',
  worldType: '世界观',
  moduleTitle: "追捕克伦可 / 追捕克仑可 / Krenko's Way",
  sessionTitle: '尚未开始的模组档案',
  chapter: '锯齿监狱的委托',
  lastRecord: '这是龙与地下城世界观下的冒险模组档案。创建或继续会话后，这里会展示真实跑团记录。',
  characterName: '待绑定角色',
  level: 1,
  hp: 100,
  maxHp: 100,
  date: '待开始',
  status: '待开始',
  statusClass: 'state-paused',
  cover: goblinCover,
  tags: ['D&D 5e', '冒险模组', '城市追捕']
}

const formatDate = (value) => {
  if (!value) return '未记录'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

const normalizeModuleTitle = (session) => {
  if (session.adventure_module_title) return session.adventure_module_title
  const source = `${session.title || ''} ${session.current_scene || ''}`.toLowerCase()
  if (source.includes('krenko') || source.includes('克伦可') || source.includes('克仑可')) {
    return "追捕克伦可 / 追捕克仑可 / Krenko's Way"
  }
  return '未绑定模组'
}

const normalizeWorldName = (session) => {
  if (session.world_name) return session.world_name
  const source = `${session.title || ''} ${session.current_scene || ''}`.toLowerCase()
  if (source.includes('dnd') || source.includes('龙与地下城') || source.includes('krenko')) {
    return '龙与地下城 DND'
  }
  return '未知世界观'
}

const coverForArchive = (worldName, moduleTitle, index) => {
  const source = `${worldName} ${moduleTitle}`.toLowerCase()
  if (source.includes('krenko') || source.includes('克伦可') || source.includes('克仑可')) return goblinCover
  if (source.includes('dnd') || source.includes('龙与地下城')) return index % 2 === 0 ? dndCover : dndCoverAlt
  return dndCoverAlt
}

const hpPercent = (hp, maxHp) => {
  const safeMax = Number(maxHp) || 100
  const safeHp = Number(hp) || safeMax
  return Math.max(0, Math.min(100, Math.round((safeHp / safeMax) * 100)))
}

const mapSessionToArchive = (session, index) => {
  const worldName = normalizeWorldName(session)
  const moduleTitle = normalizeModuleTitle(session)
  const status = statusLabels[session.status] || session.status || '已归档'
  const chapter = session.current_scene || session.adventure_module_scene || '开局场景'
  const lastRecord = session.current_task || session.summary || session.current_scene || '该会话暂无记录摘要。进入房间后继续行动，后端会继续写入数据库。'
  const characterHp = session.character_hp ?? 10
  const characterMaxHp = session.character_max_hp ?? 10

  return {
    id: `session-${session.id}`,
    sessionId: session.id,
    roomId: session.room_id,
    worldName,
    worldType: '世界观',
    moduleTitle,
    sessionTitle: session.title || `会话 #${session.id}`,
    chapter,
    lastRecord,
    characterName: session.character_name || '当前角色',
    level: session.character_level || 1,
    hp: characterHp,
    maxHp: characterMaxHp,
    hpPercent: hpPercent(characterHp, characterMaxHp),
    date: formatDate(session.started_at),
    status,
    statusClass: statusClasses[session.status] || 'state-paused',
    cover: coverForArchive(worldName, moduleTitle, index),
    tags: [
      worldName,
      moduleTitle === '未绑定模组' ? '未绑定模组' : '冒险模组',
      status
    ]
  }
}

const sourceArchives = computed(() => {
  const mapped = sessions.value.map(mapSessionToArchive)
  return mapped.length > 0 ? mapped : [fallbackArchive]
})

const filteredArchives = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  if (!keyword) return sourceArchives.value

  return sourceArchives.value.filter((archive) => {
    const haystack = [
      archive.worldName,
      archive.moduleTitle,
      archive.sessionTitle,
      archive.chapter,
      archive.lastRecord,
      archive.characterName,
      ...archive.tags
    ].join(' ').toLowerCase()
    return haystack.includes(keyword)
  })
})

const selectedArchive = computed(() => {
  const archives = filteredArchives.value
  return archives.find((item) => item.id === selectedArchiveId.value) || archives[0] || fallbackArchive
})

const worldCount = computed(() => new Set(sourceArchives.value.map((archive) => archive.worldName)).size)
const moduleCount = computed(() => new Set(sourceArchives.value.map((archive) => `${archive.worldName}:${archive.moduleTitle}`)).size)
const sessionCount = computed(() => sourceArchives.value.filter((archive) => archive.sessionId).length)

const selectArchive = (archive) => {
  selectedArchiveId.value = archive.id
}

const handleSearch = () => {
  selectedArchiveId.value = filteredArchives.value[0]?.id || null
}

const handleNavigate = (page) => {
  emit('navigate', page)
}

const handleContinue = (archive) => {
  selectArchive(archive)
  if (archive.roomId) {
    emit('enter-room', { roomId: archive.roomId })
    return
  }
  archiveStatus.value = archive.sessionId
    ? `已选中会话 #${archive.sessionId}：${archive.worldName} / ${archive.moduleTitle}`
    : `已选中模组：${archive.worldName} / ${archive.moduleTitle}`
}

const handleDeleteArchive = async (archive) => {
  selectArchive(archive)
  if (!archive.sessionId) {
    archiveStatus.value = '这是本地模组预览，没有可删除的会话记录。'
    return
  }

  const confirmed = window.confirm(`确定删除「${archive.sessionTitle}」吗？删除后该房间名称可再次使用。`)
  if (!confirmed) return

  deletingArchiveId.value = archive.id
  archiveStatus.value = ''
  try {
    await sessionsApi.delete(archive.sessionId)
    sessions.value = sessions.value.filter((session) => session.id !== archive.sessionId)
    selectedArchiveId.value = filteredArchives.value[0]?.id || null
    archiveStatus.value = `已删除「${archive.sessionTitle}」，房间名已释放。`
  } catch (error) {
    archiveStatus.value = error?.message || '删除档案失败。'
  } finally {
    deletingArchiveId.value = null
  }
}

const loadSessions = async () => {
  isLoading.value = true
  archiveStatus.value = ''
  try {
    sessions.value = await sessionsApi.list()
    selectedArchiveId.value = filteredArchives.value[0]?.id || null
  } catch (error) {
    sessions.value = []
    archiveStatus.value = error?.message || '档案同步失败，已显示本地模组预览。'
  } finally {
    isLoading.value = false
  }
}

watch(searchKeyword, handleSearch)
watch(() => props.latestSession, loadSessions)

onMounted(() => {
  emit('back-button-hidden', false)
  loadSessions()
})
</script>

<template>
  <div class="archive-page">
    <div class="page-backdrop" :style="{ backgroundImage: `url(${hallBackground})` }"></div>

    <div class="page-shell">
      <AppNavbar
        :current-user="props.currentUser"
        :sub-label="`${sessionCount} 局记录`"
        @open-settings="emit('open-settings')"
        @logout="emit('logout')"
      />

      <section class="hero">
        <div class="hero-copy">
          <div class="hero-title-row">
            <span class="hero-line"></span>
            <h2>档案馆</h2>
            <span class="hero-line"></span>
          </div>
          <p>按世界观保存模组，再回看具体跑团记录。</p>
        </div>

        <div class="hero-tools">
          <label class="search-box">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
              <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              v-model="searchKeyword"
              type="search"
              placeholder="搜索世界观、模组或会话..."
              @keyup.enter="handleSearch"
            />
          </label>
          <div class="tool-btn">
            <span>{{ worldCount }}</span>
            世界观
          </div>
          <div class="tool-btn">
            <span>{{ moduleCount }}</span>
            模组
          </div>
        </div>
      </section>

      <p v-if="archiveStatus" class="archive-status">{{ archiveStatus }}</p>

      <section class="content-grid">
        <div>
          <h3 class="section-label">历史档案</h3>

          <div v-if="isLoading" class="loading-panel">正在同步档案...</div>
          <div v-else-if="filteredArchives.length" class="archive-grid">
            <article
              v-for="archive in filteredArchives"
              :key="archive.id"
              class="archive-card"
              :class="{ active: selectedArchive.id === archive.id }"
              @click="selectArchive(archive)"
            >
              <div class="archive-cover">
                <img :src="archive.cover" :alt="archive.moduleTitle" />
              </div>
              <div class="archive-body">
                <div class="path-line">
                  <span>{{ archive.worldType }}</span>
                  <strong>{{ archive.worldName }}</strong>
                </div>
                <h3>{{ archive.moduleTitle }}</h3>
                <div class="tag-row">
                  <span v-for="tag in archive.tags" :key="tag" class="tag">{{ tag }}</span>
                </div>
                <div class="archive-meta">
                  <div class="mini-avatar"></div>
                  <div>
                    <strong>{{ archive.characterName }}　Lv.{{ archive.level }}</strong>
                    <span>{{ archive.sessionTitle }} · {{ archive.date }}</span>
                  </div>
                </div>
                <div class="archive-state">
                  <span>当前状态</span>
                  <span class="state-value" :class="archive.statusClass">{{ archive.status }}</span>
                </div>
              </div>
              <button class="archive-action" type="button" @click.stop="handleContinue(archive)">
                {{ archive.roomId ? '继续进入房间' : '查看档案详情' }}
                <span aria-hidden="true">→</span>
              </button>
              <button
                class="archive-delete"
                type="button"
                :disabled="deletingArchiveId === archive.id || !archive.sessionId"
                @click.stop="handleDeleteArchive(archive)"
              >
                {{ deletingArchiveId === archive.id ? '删除中...' : '删除档案' }}
              </button>
            </article>
          </div>
          <div v-else class="loading-panel">没有匹配的档案。</div>

        </div>

        <aside class="detail-panel">
          <div class="detail-head">当前档案</div>
          <div class="detail-main">
            <div class="dragon-seal">D20</div>
            <h3>{{ selectedArchive.worldName }}</h3>
          </div>

          <section class="detail-block">
            <h4>层级</h4>
            <div class="detail-path">
              <div>
                <span>世界观</span>
                <strong>{{ selectedArchive.worldName }}</strong>
              </div>
              <div>
                <span>模组</span>
                <strong>{{ selectedArchive.moduleTitle }}</strong>
              </div>
              <div>
                <span>会话</span>
                <strong>{{ selectedArchive.sessionId ? `#${selectedArchive.sessionId}` : '尚未开始' }}</strong>
              </div>
            </div>
          </section>

          <section class="detail-block">
            <h4>章节</h4>
            <div class="detail-text">{{ selectedArchive.chapter }}</div>
          </section>

          <section class="detail-block">
            <h4>最后记录</h4>
            <div class="detail-text">{{ selectedArchive.lastRecord }}</div>
          </section>

          <section class="detail-block">
            <h4>角色状态</h4>
            <div class="status-row">
              <div>
                <div class="hp-head">
                  <span>HP</span>
                  <span>{{ selectedArchive.hpPercent || hpPercent(selectedArchive.hp, selectedArchive.maxHp) }}%</span>
                </div>
                <div class="hp-track">
                  <div
                    class="hp-fill"
                    :style="{ width: `${selectedArchive.hpPercent || hpPercent(selectedArchive.hp, selectedArchive.maxHp)}%` }"
                  ></div>
                </div>
              </div>
              <div class="level-row">
                <span>等级</span>
                <strong>Lv.{{ selectedArchive.level }}</strong>
              </div>
            </div>
          </section>

          <button class="enter-btn" type="button" @click="handleContinue(selectedArchive)">
            {{ selectedArchive.roomId ? '继续进入冒险' : '查看档案层级' }}
            <span aria-hidden="true">→</span>
          </button>
          <button
            class="detail-delete-btn"
            type="button"
            :disabled="deletingArchiveId === selectedArchive.id || !selectedArchive.sessionId"
            @click="handleDeleteArchive(selectedArchive)"
          >
            {{ deletingArchiveId === selectedArchive.id ? '删除中...' : '删除当前档案' }}
          </button>
        </aside>
      </section>
    </div>
  </div>
</template>

<style scoped>
:global(body) {
  margin: 0;
}

.archive-page {
  --sf-bg: #06080d;
  --sf-panel: rgba(12, 14, 20, 0.9);
  --sf-gold: #d8a84a;
  --sf-gold-bright: #ffd889;
  --sf-ink: #f5e9d0;
  --sf-ink-soft: #c9b99b;
  --sf-ink-muted: #8e836d;
  --sf-arcane: #6fdcff;
  --sf-border: rgba(216, 168, 74, 0.28);
  --sf-border-strong: rgba(255, 216, 137, 0.62);
  --sf-shadow: 0 24px 60px rgba(0, 0, 0, 0.58);
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
  background: var(--sf-bg);
  color: var(--sf-ink);
  font-family: "Noto Serif SC", "Microsoft YaHei", serif;
}

.page-backdrop {
  position: fixed;
  inset: 0;
  z-index: 0;
  background-position: center;
  background-size: cover;
}

.page-backdrop::before,
.page-backdrop::after {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.page-backdrop::before {
  background:
    linear-gradient(180deg, rgba(0, 0, 0, 0.66), rgba(0, 0, 0, 0.82)),
    linear-gradient(90deg, rgba(2, 5, 10, 0.92), rgba(2, 5, 10, 0.36) 48%, rgba(2, 5, 10, 0.88));
}

.page-backdrop::after {
  background:
    radial-gradient(circle at 58% 14%, rgba(255, 183, 72, 0.12), transparent 18%),
    radial-gradient(circle at 66% 12%, rgba(111, 220, 255, 0.18), transparent 16%),
    radial-gradient(circle at center, transparent 34%, rgba(0, 0, 0, 0.76) 100%);
}

.page-shell {
  position: relative;
  z-index: 1;
  max-width: 1540px;
  margin: 0 auto;
  padding: 18px 24px 28px;
}

.navbar {
  height: 70px;
  display: grid;
  grid-template-columns: 300px 1fr 300px;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid rgba(216, 168, 74, 0.2);
}

.brand,
.user-box,
.archive-meta,
.hero-title-row,
.hero-tools,
.section-label,
.detail-head,
.detail-main,
.hp-head,
.level-row {
  display: flex;
  align-items: center;
}

.brand {
  gap: 14px;
}

.brand-mark {
  width: 48px;
  height: 48px;
  border: 1px solid var(--sf-border-strong);
  border-radius: 12px;
  display: grid;
  place-items: center;
  color: var(--sf-gold);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.04);
}

.brand-mark svg {
  width: 30px;
  height: 30px;
}

.brand-copy h1 {
  margin: 0;
  font-size: 28px;
  color: var(--sf-gold-bright);
  font-family: Georgia, "Times New Roman", serif;
  font-weight: 600;
}

.brand-copy p {
  margin: 3px 0 0;
  color: var(--sf-ink-soft);
  font-size: 14px;
  letter-spacing: 0.18em;
}

.nav-links {
  display: flex;
  justify-content: center;
  gap: 44px;
}

.nav-links button {
  position: relative;
  border: 0;
  background: transparent;
  color: var(--sf-ink);
  font: inherit;
  font-size: 18px;
  cursor: pointer;
}

.nav-links button.active {
  color: var(--sf-gold-bright);
}

.nav-links button.active::after {
  content: "";
  position: absolute;
  left: 50%;
  bottom: -18px;
  width: 90px;
  height: 14px;
  transform: translateX(-50%);
  background:
    radial-gradient(circle at center, rgba(255, 217, 137, 0.95) 0 16%, transparent 18%),
    linear-gradient(90deg, transparent, rgba(216, 168, 74, 0.8), transparent);
}

.user-box {
  justify-content: flex-end;
  gap: 18px;
}

.user-avatar,
.mini-avatar {
  border-radius: 50%;
  border: 1px solid var(--sf-border-strong);
  background:
    radial-gradient(circle at 40% 30%, rgba(255, 214, 143, 0.28), transparent 36%),
    linear-gradient(180deg, #332618, #110e0b);
  box-shadow: 0 0 18px rgba(216, 168, 74, 0.2);
}

.user-avatar {
  width: 58px;
  height: 58px;
}

.user-meta strong {
  display: block;
  color: var(--sf-ink);
  font-size: 20px;
  margin-bottom: 4px;
}

.user-meta span {
  color: var(--sf-ink-soft);
  font-size: 15px;
}

.icon-btn {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  border: 1px solid var(--sf-border);
  background: rgba(8, 10, 15, 0.5);
  color: var(--sf-gold-bright);
  display: grid;
  place-items: center;
  cursor: pointer;
}

.icon-btn svg {
  width: 20px;
  height: 20px;
}

.hero {
  display: grid;
  grid-template-columns: 1.3fr 0.9fr;
  gap: 24px;
  min-height: 280px;
  padding: 32px 8px 18px;
}

.hero-copy {
  padding: 22px 0 0 8px;
}

.hero-title-row {
  gap: 18px;
  margin-bottom: 20px;
}

.hero-line {
  width: 62px;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--sf-gold-bright), transparent);
}

.hero h2 {
  margin: 0;
  font-size: 86px;
  line-height: 1;
  color: var(--sf-gold-bright);
  letter-spacing: 0.08em;
  text-shadow: 0 0 30px rgba(216, 168, 74, 0.22);
}

.hero p {
  margin: 8px 0 0 96px;
  color: var(--sf-gold-bright);
  font-size: 22px;
}

.hero-tools {
  align-self: end;
  justify-content: flex-end;
  gap: 16px;
  padding-bottom: 18px;
}

.tool-btn,
.search-box {
  min-height: 62px;
  border: 1px solid var(--sf-border);
  background: rgba(10, 12, 18, 0.72);
  border-radius: 16px;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.03);
}

.search-box {
  width: 330px;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 0 20px;
  color: var(--sf-ink-muted);
}

.search-box svg {
  width: 20px;
  height: 20px;
  flex: 0 0 auto;
}

.search-box input {
  min-width: 0;
  width: 100%;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--sf-ink);
  font-size: 15px;
}

.search-box input::placeholder {
  color: var(--sf-ink-muted);
}

.tool-btn {
  min-width: 118px;
  padding: 0 22px;
  color: var(--sf-gold-bright);
  display: grid;
  place-items: center;
  gap: 2px;
  font-size: 15px;
}

.tool-btn span {
  font-size: 22px;
  font-weight: 800;
}

.archive-status {
  margin: 0 8px 18px;
  color: var(--sf-gold-bright);
  font-size: 14px;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 400px;
  gap: 28px;
}

.section-label {
  gap: 14px;
  justify-content: center;
  color: var(--sf-gold-bright);
  font-size: 20px;
  margin: 0 0 18px;
}

.section-label::before,
.section-label::after {
  content: "";
  width: 32px;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--sf-gold), transparent);
}

.archive-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.archive-card {
  position: relative;
  border-radius: 22px;
  overflow: hidden;
  border: 1px solid var(--sf-border);
  background: rgba(7, 9, 14, 0.82);
  box-shadow: var(--sf-shadow);
  min-height: 610px;
  cursor: pointer;
}

.archive-card.active {
  border-color: var(--sf-border-strong);
  box-shadow: 0 0 28px rgba(216, 168, 74, 0.28), var(--sf-shadow);
}

.archive-card::before {
  content: "";
  position: absolute;
  inset: 10px;
  border: 1px solid rgba(216, 168, 74, 0.22);
  border-radius: 16px;
  pointer-events: none;
  z-index: 2;
}

.archive-cover {
  position: relative;
  height: 380px;
  overflow: hidden;
  background: #0d1117;
}

.archive-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.archive-cover::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(4, 6, 10, 0.08), rgba(4, 6, 10, 0.64));
}

.archive-body {
  padding: 18px 22px 0;
}

.path-line {
  display: grid;
  gap: 4px;
  margin-bottom: 12px;
}

.path-line span {
  color: var(--sf-arcane);
  font-size: 12px;
}

.path-line strong {
  color: var(--sf-ink-soft);
  font-size: 14px;
}

.archive-body h3 {
  margin: 0 0 12px;
  min-height: 70px;
  font-size: 27px;
  line-height: 1.28;
  color: var(--sf-gold-bright);
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 18px;
}

.tag {
  padding: 5px 10px;
  border-radius: 999px;
  border: 1px solid rgba(216, 168, 74, 0.34);
  background: rgba(216, 168, 74, 0.08);
  color: var(--sf-ink-soft);
  font-size: 13px;
}

.archive-meta {
  gap: 14px;
  margin-bottom: 12px;
}

.mini-avatar {
  width: 64px;
  height: 64px;
  flex: 0 0 auto;
}

.archive-meta strong {
  display: block;
  font-size: 16px;
  color: var(--sf-ink);
  margin-bottom: 4px;
}

.archive-meta span,
.archive-date {
  color: var(--sf-ink-soft);
  font-size: 14px;
}

.archive-state {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  color: var(--sf-ink-soft);
  font-size: 14px;
}

.state-value {
  font-size: 15px;
  font-weight: 600;
}

.state-running {
  color: #9ad66f;
}

.state-paused {
  color: #ffc65b;
}

.state-finished {
  color: #9fb0c4;
}

.archive-action {
  width: calc(100% - 44px);
  margin: 18px 22px 10px;
  min-height: 56px;
  border-radius: 14px;
  border: 1px solid var(--sf-border-strong);
  background:
    linear-gradient(180deg, rgba(255, 214, 143, 0.18), rgba(145, 95, 28, 0.22)),
    rgba(11, 10, 7, 0.92);
  color: var(--sf-gold-bright);
  font-size: 18px;
  letter-spacing: 0.04em;
  cursor: pointer;
}

.archive-delete,
.detail-delete-btn {
  width: calc(100% - 44px);
  min-height: 44px;
  margin: 0 22px 22px;
  border-radius: 12px;
  border: 1px solid rgba(248, 113, 113, 0.42);
  background: rgba(75, 20, 20, 0.34);
  color: #ffc3c3;
  font-size: 15px;
  cursor: pointer;
}

.archive-delete:hover:not(:disabled),
.detail-delete-btn:hover:not(:disabled) {
  border-color: rgba(248, 113, 113, 0.78);
  background: rgba(116, 30, 30, 0.42);
}

.archive-delete:disabled,
.detail-delete-btn:disabled {
  cursor: not-allowed;
  opacity: 0.52;
}

.detail-panel,
.loading-panel {
  border: 1px solid var(--sf-border);
  border-radius: 24px;
  background: rgba(10, 12, 18, 0.78);
  box-shadow: var(--sf-shadow);
}

.loading-panel {
  padding: 42px;
  color: var(--sf-ink-soft);
  text-align: center;
}

.detail-panel {
  background:
    linear-gradient(180deg, rgba(10, 11, 16, 0.94), rgba(8, 9, 14, 0.96)),
    rgba(10, 11, 16, 0.92);
  padding: 18px 22px 22px;
  min-height: 610px;
}

.detail-head {
  gap: 12px;
  margin-bottom: 18px;
  color: var(--sf-gold-bright);
  font-size: 18px;
}

.detail-main {
  gap: 18px;
  margin-bottom: 22px;
}

.dragon-seal {
  width: 86px;
  height: 86px;
  border-radius: 50%;
  border: 1px solid rgba(216, 168, 74, 0.24);
  display: grid;
  place-items: center;
  color: var(--sf-gold);
  font-size: 28px;
  font-family: Georgia, "Times New Roman", serif;
  background: radial-gradient(circle, rgba(216, 168, 74, 0.14), transparent 72%);
}

.detail-main h3 {
  margin: 0;
  font-size: 34px;
  line-height: 1.2;
  color: var(--sf-gold-bright);
}

.detail-block {
  margin-top: 18px;
  padding-top: 18px;
  border-top: 1px solid rgba(216, 168, 74, 0.18);
}

.detail-block h4 {
  margin: 0 0 12px;
  font-size: 18px;
  color: var(--sf-gold-bright);
  display: flex;
  align-items: center;
  gap: 12px;
}

.detail-block h4::before,
.detail-block h4::after {
  content: "";
  height: 1px;
  flex: 1;
  background: linear-gradient(90deg, rgba(216, 168, 74, 0.28), transparent);
}

.detail-block h4::after {
  background: linear-gradient(90deg, transparent, rgba(216, 168, 74, 0.28));
}

.detail-text {
  color: var(--sf-ink-soft);
  font-size: 15px;
  line-height: 1.9;
}

.detail-path {
  display: grid;
  gap: 12px;
}

.detail-path div {
  padding: 12px 14px;
  border: 1px solid rgba(216, 168, 74, 0.18);
  border-radius: 12px;
  background: rgba(15, 18, 24, 0.64);
}

.detail-path span {
  display: block;
  margin-bottom: 5px;
  color: var(--sf-arcane);
  font-size: 12px;
}

.detail-path strong {
  color: var(--sf-ink);
  font-size: 15px;
  line-height: 1.4;
}

.status-row {
  display: grid;
  gap: 18px;
}

.hp-head,
.level-row {
  justify-content: space-between;
  color: var(--sf-gold-bright);
  font-size: 18px;
}

.hp-head span:last-child,
.level-row strong {
  color: var(--sf-arcane);
}

.hp-track {
  height: 10px;
  border-radius: 999px;
  background: rgba(111, 220, 255, 0.14);
  overflow: hidden;
  border: 1px solid rgba(111, 220, 255, 0.24);
}

.hp-fill {
  height: 100%;
  background: linear-gradient(90deg, #168db1, #4ed8ff);
  box-shadow: 0 0 16px rgba(111, 220, 255, 0.32);
}

.enter-btn {
  width: 100%;
  min-height: 72px;
  margin-top: 28px;
  border-radius: 18px;
  border: 1px solid var(--sf-border-strong);
  background:
    linear-gradient(180deg, rgba(255, 214, 143, 0.16), rgba(145, 95, 28, 0.26)),
    rgba(12, 11, 8, 0.96);
  color: var(--sf-gold-bright);
  font-size: 22px;
  letter-spacing: 0.04em;
  box-shadow: 0 0 24px rgba(216, 168, 74, 0.18);
  cursor: pointer;
}

.detail-delete-btn {
  width: 100%;
  margin: 12px 0 0;
}

@media (max-width: 1320px) {
  .content-grid {
    grid-template-columns: 1fr;
  }

  .archive-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 980px) {
  .page-shell {
    padding: 14px 16px 24px;
  }

  .navbar {
    grid-template-columns: 1fr;
    height: auto;
    padding-bottom: 18px;
  }

  .nav-links,
  .user-box {
    justify-content: flex-start;
    flex-wrap: wrap;
    gap: 18px;
  }

  .hero {
    grid-template-columns: 1fr;
  }

  .hero h2 {
    font-size: 58px;
  }

  .hero p {
    margin-left: 0;
  }

  .hero-tools {
    justify-content: flex-start;
    flex-wrap: wrap;
  }

  .search-box {
    width: 100%;
  }
}
</style>
