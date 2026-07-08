<script setup>
import { ref, reactive } from 'vue'

const props = defineProps({
  currentPage: {
    type: String,
    default: '大厅'
  }
})

const emit = defineEmits(['navigate'])

const showCreateModal = ref(false)
const roomCode = ref('')
const activeNav = ref(props.currentPage)

const createRoomForm = reactive({
  roomName: '',
  scriptTemplate: '',
  maxPlayers: 4,
  roomType: 'public',
  aiStyle: 'classic',
  difficulty: 'normal'
})

const navItems = [
  { name: '大厅' },
  { name: '世界观' },
  { name: '档案' }
]

const friendsList = [
  { name: '说书人', level: 'Lv.8', status: 'online' },
  { name: '云中君', level: 'Lv.15', status: 'online' },
  { name: '潇湘客', level: 'Lv.6', status: 'online' },
  { name: '墨染', level: 'Lv.10', status: 'offline' }
]

const quickRooms = [
  {
    name: '云泽佣兵团',
    players: '2/4',
    owner: '夜行者'
  },
  {
    name: '洛水断镖小组',
    players: '3/4',
    owner: '说书人'
  }
]

const lastAdventure = {
  title: '山海志怪 · 雾泽铜铃',
  chapter: '第3章 · 铜神回响',
  progress: 68
}

const scriptTemplates = ['山海志怪：雾泽铜铃', '江湖秘案：洛水断镖', '县衙诡案：黑雨纸铺']
const aiStyles = [
  { value: 'classic', label: '经典说书' },
  { value: 'immersive', label: '沉浸叙事' },
  { value: 'humorous', label: '轻松诙谐' },
  { value: 'mysterious', label: '神秘悬疑' }
]
const difficulties = [
  { value: 'easy', label: '简单' },
  { value: 'normal', label: '普通' },
  { value: 'hard', label: '困难' },
  { value: 'nightmare', label: '噩梦' }
]

const handleCreateRoom = () => {
  console.log('创建房间数据:', { ...createRoomForm })
  showCreateModal.value = false
}

const handleJoinRoom = () => {
  console.log('加入房间:', { roomCode: roomCode.value })
}

const handleContinue = () => {
  console.log('继续上次冒险:', lastAdventure)
}

const handleQuickJoin = (room) => {
  console.log('快速加入:', room)
}

const handleHistory = () => {
  console.log('查看历史档案')
}

const handleNavigate = (page) => {
  activeNav.value = page
  emit('navigate', page)
}
</script>

<template>
  <div class="home-page">
    <div class="page-bg">
      <div class="bg-overlay"></div>
    </div>

    <nav class="navbar">
      <div class="nav-logo">
        <svg viewBox="0 0 32 32" fill="none" class="logo-icon">
          <polygon points="16,2 28,10 28,22 16,30 4,22 4,10" fill="#f5b95b"/>
          <polygon points="16,4 26,10 26,22 16,28 6,22 6,10" fill="#d49a3f"/>
          <circle cx="16" cy="16" r="4" fill="#1a1a2e"/>
          <text x="16" y="19" text-anchor="middle" fill="#f5b95b" font-size="8" font-weight="bold">SF</text>
        </svg>
        <div class="logo-text">
          <span class="logo-en">StoryForge</span>
          <span class="logo-cn">灵境档案</span>
        </div>
      </div>
      <div class="nav-menu">
        <button
          v-for="item in navItems"
          :key="item.name"
          class="nav-item"
          :class="{ active: activeNav === item.name }"
          @click="handleNavigate(item.name)"
        >
          {{ item.name }}
        </button>
      </div>
      <div class="nav-user">
        <div class="user-avatar">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
            <circle cx="12" cy="7" r="4"/>
          </svg>
        </div>
        <div class="user-info">
          <span class="user-name">夜行者</span>
          <span class="user-level">Lv.12</span>
        </div>
        <button class="nav-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 0 01-3.46 0"/>
          </svg>
        </button>
        <button class="nav-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/>
          </svg>
        </button>
      </div>
    </nav>

    <main class="main-content">
      <div class="content-wrapper">
        <section class="friends-section">
          <div class="friends-header">
            <div class="friends-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 00-3-3.87"/>
                <path d="M16 3.13a4 4 0 010 7.75"/>
              </svg>
              <span>好友在线</span>
              <span class="online-count">{{ friendsList.filter(f => f.status === 'online').length }}</span>
            </div>
            <div class="friends-list">
              <div
                v-for="(friend, index) in friendsList"
                :key="index"
                class="friend-item"
              >
                <div class="friend-avatar">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
                    <circle cx="12" cy="7" r="4"/>
                  </svg>
                  <span class="status-dot" :class="friend.status"></span>
                </div>
                <span class="friend-name">{{ friend.name }}</span>
              </div>
            </div>
            <button class="view-all-friends">查看全部 ></button>
          </div>
        </section>

        <section class="hero-section">
          <div class="hero-main">
            <div class="hero-bg"></div>
            <div class="hero-content">
              <h1 class="hero-title">你的故事，</h1>
              <h1 class="hero-title">由你塑造</h1>
              <p class="hero-desc">与伙伴共创史诗，探索无限可能</p>
              <p class="hero-desc">与伙伴共创史诗，探索无限可能</p>
              <button class="hero-btn" @click="showCreateModal = true">开启新的冒险</button>
            </div>
          </div>

          <div class="hero-right">
            <div class="continue-panel">
              <div class="panel-header">
                <span class="panel-title">继续上次冒险</span>
              </div>
              <div class="adventure-info">
                <div class="adventure-cover"></div>
                <div class="adventure-detail">
                  <h4 class="adventure-title">{{ lastAdventure.title }}</h4>
                  <p class="adventure-chapter">{{ lastAdventure.chapter }}</p>
                  <div class="progress-wrap">
                    <div class="progress-bar">
                      <div class="progress-fill" :style="{ width: lastAdventure.progress + '%' }"></div>
                    </div>
                    <span class="progress-text">进度: {{ lastAdventure.progress }}%</span>
                  </div>
                </div>
              </div>
              <button class="continue-btn" @click="handleContinue">继续冒险</button>
            </div>

            <div class="quick-panel">
              <div class="panel-header">
                <span class="panel-title">快速加入</span>
                <button class="panel-more">更多 ></button>
              </div>
              <div class="quick-list">
                <div
                  v-for="(room, index) in quickRooms"
                  :key="index"
                  class="quick-item"
                >
                  <div class="quick-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                      <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                      <path d="M2 17l10 5 10-5"/>
                      <path d="M2 12l10 5 10-5"/>
                    </svg>
                  </div>
                  <div class="quick-info">
                    <span class="quick-name">{{ room.name }}</span>
                    <span class="quick-meta">房主: {{ room.owner }}</span>
                  </div>
                  <div class="quick-status">
                    <span class="player-count">{{ room.players }}</span>
                    <button class="quick-join" @click="handleQuickJoin(room)">加入</button>
                  </div>
                </div>
              </div>
              <button class="view-more-rooms">查看更多房间</button>
            </div>
          </div>
        </section>

        <section class="feature-section">
          <div class="feature-cards">
            <button class="feature-card gold-card" @click="showCreateModal = true">
              <div class="card-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"/>
                </svg>
              </div>
              <span class="card-title">创建房间</span>
              <span class="card-subtitle">开启新的故事</span>
            </button>
            <button class="feature-card blue-card" @click="handleJoinRoom">
              <div class="card-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
                </svg>
              </div>
              <span class="card-title">加入房间</span>
              <span class="card-subtitle">输入房号加入</span>
            </button>
            <button class="feature-card dark-card" @click="handleContinue">
              <div class="card-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/>
                  <path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
              </div>
              <span class="card-title">继续冒险</span>
              <span class="card-subtitle">续写未完的篇章</span>
            </button>
            <button class="feature-card dark-card" @click="handleHistory">
              <div class="card-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
                </svg>
              </div>
              <span class="card-title">查看档案</span>
              <span class="card-subtitle">探索你的故事世界</span>
            </button>
          </div>
        </section>

      </div>
    </main>

    <div class="modal-overlay" v-if="showCreateModal" @click="showCreateModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">创建房间</h3>
          <button class="modal-close" @click="showCreateModal = false">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M6 18L18 6M6 6l12 12"/>
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
                required
              />
            </div>
            <div class="form-group">
              <label class="form-label">剧本模板</label>
              <select v-model="createRoomForm.scriptTemplate" class="form-select" required>
                <option value="">请选择剧本</option>
                <option v-for="template in scriptTemplates" :key="template" :value="template">{{ template }}</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">人数上限</label>
              <select v-model="createRoomForm.maxPlayers" class="form-select">
                <option :value="2">2 人</option>
                <option :value="3">3 人</option>
                <option :value="4">4 人</option>
                <option :value="5">5 人</option>
                <option :value="6">6 人</option>
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
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">AI 主持风格</label>
              <select v-model="createRoomForm.aiStyle" class="form-select">
                <option v-for="style in aiStyles" :key="style.value" :value="style.value">{{ style.label }}</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">难度设置</label>
              <select v-model="createRoomForm.difficulty" class="form-select">
                <option v-for="diff in difficulties" :key="diff.value" :value="diff.value">{{ diff.label }}</option>
              </select>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn-cancel" @click="showCreateModal = false">取消</button>
            <button type="submit" class="btn-confirm">创建房间</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home-page {
  min-height: 100vh;
  position: relative;
  background: #1a1510;
}

.page-bg {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: 
    repeating-linear-gradient(
      0deg,
      transparent,
      transparent 40px,
      rgba(61, 48, 36, 0.05) 40px,
      rgba(61, 48, 36, 0.05) 41px
    ),
    radial-gradient(ellipse at 10% 20%, rgba(139, 115, 85, 0.1) 0%, transparent 50%),
    radial-gradient(ellipse at 90% 80%, rgba(92, 61, 61, 0.08) 0%, transparent 40%),
    linear-gradient(180deg, #1a1510 0%, #2d241a 50%, #1a1510 100%);
  z-index: 0;
}

.bg-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: 
    radial-gradient(ellipse at 50% 0%, rgba(201, 169, 98, 0.03) 0%, transparent 60%),
    radial-gradient(ellipse at 30% 50%, rgba(139, 115, 85, 0.02) 0%, transparent 40%);
}

.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 40px;
  background: rgba(26, 21, 16, 0.95);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid rgba(139, 115, 85, 0.2);
  z-index: 100;
}

.nav-logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-icon {
  width: 36px;
  height: 36px;
}

.logo-text {
  display: flex;
  flex-direction: column;
}

.logo-en {
  font-size: 16px;
  font-weight: 700;
  color: #c9a962;
  letter-spacing: 1px;
  font-family: 'Georgia', 'Times New Roman', serif;
}

.logo-cn {
  font-size: 10px;
  color: #a67c52;
  letter-spacing: 2px;
  font-family: 'KaiTi', 'STKaiti', serif;
}

.nav-menu {
  display: flex;
  gap: 4px;
}

.nav-item {
  padding: 10px 28px;
  background: none;
  border: none;
  color: #8b7355;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.3s ease;
  font-family: 'Georgia', 'Times New Roman', serif;
}

.nav-item:hover {
  color: #c9a962;
  background: rgba(139, 115, 85, 0.1);
}

.nav-item.active {
  color: #c9a962;
  background: rgba(201, 169, 98, 0.1);
  border-bottom: 2px solid #c9a962;
}

.nav-user {
  display: flex;
  align-items: center;
  gap: 14px;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(139, 115, 85, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid rgba(139, 115, 85, 0.6);
}

.user-avatar svg {
  width: 22px;
  height: 22px;
  color: #8b7355;
}

.user-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.user-name {
  font-size: 14px;
  color: #f5efe6;
  font-weight: 600;
}

.user-level {
  padding: 2px 10px;
  background: rgba(139, 115, 85, 0.2);
  border: 1px solid rgba(139, 115, 85, 0.5);
  border-radius: 12px;
  font-size: 12px;
  color: #8b7355;
  font-weight: 600;
}

.nav-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(139, 115, 85, 0.1);
  border: none;
  border-radius: 6px;
  color: #8b7355;
  cursor: pointer;
  transition: all 0.3s ease;
}

.nav-icon:hover {
  background: rgba(139, 115, 85, 0.2);
  color: #c9a962;
}

.nav-icon svg {
  width: 16px;
  height: 16px;
}

.main-content {
  position: relative;
  z-index: 10;
  padding-top: 80px;
  padding-bottom: 40px;
}

.content-wrapper {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 20px;
}

.hero-section {
  display: flex;
  gap: 24px;
  margin-bottom: 32px;
}

.hero-main {
  flex: 2;
  position: relative;
  border-radius: 4px;
  overflow: hidden;
  height: 380px;
  background: #f5efe6;
  box-shadow: 
    0 4px 20px rgba(0, 0, 0, 0.3),
    inset 0 0 60px rgba(139, 115, 85, 0.05);
}

.hero-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: 
    linear-gradient(180deg, rgba(245, 239, 230, 0.98) 0%, rgba(232, 224, 213, 0.95) 100%),
    repeating-linear-gradient(
      0deg,
      transparent,
      transparent 30px,
      rgba(139, 115, 85, 0.03) 30px,
      rgba(139, 115, 85, 0.03) 31px
    );
}

.hero-bg::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: 1px solid rgba(139, 115, 85, 0.15);
  pointer-events: none;
}

.hero-content {
  position: relative;
  z-index: 2;
  padding: 48px;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.hero-title {
  font-size: 48px;
  font-weight: 700;
  color: #2d241a;
  line-height: 1.2;
  margin: 0;
  font-family: 'Georgia', 'Times New Roman', serif;
}

.hero-desc {
  font-size: 16px;
  color: #4a3d32;
  margin-top: 16px;
  font-weight: 400;
  font-family: 'Georgia', 'Times New Roman', serif;
  line-height: 1.6;
}

.hero-btn {
  margin-top: 28px;
  padding: 12px 32px;
  background: #2d241a;
  border: 1px solid #4a3d32;
  border-radius: 2px;
  color: #f5efe6;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  align-self: flex-start;
  font-family: 'Georgia', 'Times New Roman', serif;
}

.hero-btn:hover {
  background: #3d3024;
  border-color: #6b5a4a;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.hero-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.continue-panel,
.quick-panel {
  background: #f5efe6;
  border: 1px solid rgba(139, 115, 85, 0.2);
  border-radius: 4px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  background: rgba(139, 115, 85, 0.08);
  border-bottom: 1px solid rgba(139, 115, 85, 0.15);
}

.panel-title {
  font-size: 13px;
  font-weight: 600;
  color: #3d3024;
  font-family: 'Georgia', 'Times New Roman', serif;
}

.panel-more {
  background: none;
  border: none;
  color: #8b7355;
  font-size: 12px;
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 2px;
  transition: color 0.3s ease;
}

.panel-more:hover {
  color: #c9a962;
}

.adventure-info {
  display: flex;
  gap: 14px;
  padding: 18px;
}

.adventure-cover {
  width: 80px;
  height: 80px;
  background: #3d3024;
  border-radius: 2px;
  flex-shrink: 0;
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(139, 115, 85, 0.3);
}

.adventure-cover::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url("data:image/svg+xml,%3Csvg viewBox='0 0 80 80' xmlns='http://www.w3.org/2000/svg'%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' dy='.3em' fill='%238b7355' font-size='18' font-weight='bold'%3E%E6%9C%A8%E7%BB%84%E7%AD%89%E7%9B%AE%E6%A0%87%3C/text%3E%3C/svg%3E") no-repeat center;
  opacity: 0.2;
}

.adventure-detail {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.adventure-title {
  font-size: 14px;
  font-weight: 600;
  color: #2d241a;
  margin-bottom: 4px;
  font-family: 'Georgia', 'Times New Roman', serif;
}

.adventure-chapter {
  font-size: 12px;
  color: #6b5a45;
  margin-bottom: 10px;
}

.progress-wrap {
  margin-top: auto;
}

.progress-bar {
  height: 4px;
  background: rgba(139, 115, 85, 0.15);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 4px;
}

.progress-fill {
  height: 100%;
  background: #8b7355;
  border-radius: 2px;
  transition: width 0.5s ease;
}

.progress-text {
  font-size: 11px;
  color: #6b5a45;
}

.continue-btn {
  width: calc(100% - 36px);
  margin: 0 18px 18px;
  padding: 10px;
  background: #2d241a;
  border: 1px solid #4a3d32;
  border-radius: 2px;
  color: #f5efe6;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: 'Georgia', 'Times New Roman', serif;
}

.continue-btn:hover {
  background: #3d3024;
  border-color: #6b5a45;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
}

.quick-list {
  padding: 8px;
}

.quick-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 4px;
  transition: background 0.3s ease;
  cursor: pointer;
}

.quick-item:hover {
  background: rgba(139, 115, 85, 0.08);
}

.quick-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8b7355;
  background: rgba(139, 115, 85, 0.1);
  border-radius: 4px;
}

.quick-icon svg {
  width: 16px;
  height: 16px;
}

.quick-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.quick-name {
  font-size: 13px;
  font-weight: 500;
  color: #3d3024;
}

.quick-meta {
  font-size: 11px;
  color: #6b5a45;
}

.quick-status {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}

.player-count {
  font-size: 11px;
  color: #8b7355;
}

.quick-join {
  padding: 6px 14px;
  background: rgba(139, 115, 85, 0.1);
  border: 1px solid rgba(139, 115, 85, 0.3);
  border-radius: 2px;
  color: #6b5a45;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.quick-join:hover {
  background: rgba(139, 115, 85, 0.2);
  border-color: rgba(139, 115, 85, 0.5);
}

.view-more-rooms {
  width: calc(100% - 36px);
  margin: 0 18px 18px;
  padding: 10px;
  background: rgba(139, 115, 85, 0.08);
  border: 1px solid rgba(139, 115, 85, 0.15);
  border-radius: 2px;
  color: #6b5a45;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.view-more-rooms:hover {
  background: rgba(139, 115, 85, 0.15);
}

.feature-section {
  margin-bottom: 24px;
}

.feature-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.feature-card {
  padding: 24px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
  border: 1px solid transparent;
  background: #f5efe6;
}

.feature-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.gold-card {
  background: linear-gradient(145deg, rgba(139, 115, 85, 0.08) 0%, rgba(201, 169, 98, 0.05) 100%);
  border-color: rgba(139, 115, 85, 0.2);
}

.gold-card:hover {
  border-color: rgba(139, 115, 85, 0.35);
  box-shadow: 0 4px 16px rgba(139, 115, 85, 0.1);
}

.gold-card .card-icon {
  color: #8b7355;
  background: rgba(139, 115, 85, 0.15);
}

.gold-card .card-title {
  color: #3d3024;
}

.blue-card {
  background: linear-gradient(145deg, rgba(139, 115, 85, 0.06) 0%, rgba(92, 61, 61, 0.04) 100%);
  border-color: rgba(139, 115, 85, 0.15);
}

.blue-card:hover {
  border-color: rgba(139, 115, 85, 0.3);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.blue-card .card-icon {
  color: #8b7355;
  background: rgba(139, 115, 85, 0.12);
}

.blue-card .card-title {
  color: #3d3024;
}

.dark-card {
  background: #f5efe6;
  border-color: rgba(139, 115, 85, 0.15);
}

.dark-card:hover {
  border-color: rgba(139, 115, 85, 0.3);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.dark-card .card-icon {
  color: #8b7355;
  background: rgba(139, 115, 85, 0.12);
}

.dark-card .card-title {
  color: #3d3024;
}

.card-icon {
  width: 56px;
  height: 56px;
  margin: 0 auto 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

.card-icon svg {
  width: 24px;
  height: 24px;
}

.card-title {
  display: block;
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 4px;
  color: #2d241a;
  font-family: 'Georgia', 'Times New Roman', serif;
}

.card-subtitle {
  display: block;
  font-size: 12px;
  color: #6b5a45;
}

.friends-section {
  background: #f5efe6;
  border: 1px solid rgba(139, 115, 85, 0.15);
  border-radius: 4px;
  padding: 16px 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.friends-header {
  display: flex;
  align-items: center;
  gap: 20px;
}

.friends-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #3d3024;
  font-family: 'Georgia', 'Times New Roman', serif;
}

.friends-title svg {
  width: 16px;
  height: 16px;
  color: #8b7355;
}

.online-count {
  padding: 2px 8px;
  background: rgba(139, 115, 85, 0.15);
  border: 1px solid rgba(139, 115, 85, 0.3);
  border-radius: 8px;
  font-size: 11px;
  color: #6b5a45;
}

.friends-list {
  flex: 1;
  display: flex;
  gap: 16px;
}

.friend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.friend-avatar {
  position: relative;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(139, 115, 85, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
}

.friend-avatar svg {
  width: 18px;
  height: 18px;
  color: #6b5a45;
}

.status-dot {
  position: absolute;
  bottom: 1px;
  right: 1px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid #f5efe6;
}

.status-dot.online {
  background: #8b7355;
}

.status-dot.offline {
  background: #a6957a;
}

.friend-name {
  font-size: 12px;
  color: #4a3d32;
}

.view-all-friends {
  background: none;
  border: none;
  color: #6b5a45;
  font-size: 12px;
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 2px;
  transition: color 0.3s ease;
}

.view-all-friends:hover {
  color: #8b7355;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(26, 21, 16, 0.8);
  backdrop-filter: blur(4px);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-content {
  width: 100%;
  max-width: 560px;
  background: #f5efe6;
  border: 1px solid rgba(139, 115, 85, 0.2);
  border-radius: 4px;
  padding: 28px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.modal-title {
  font-size: 18px;
  font-weight: 600;
  color: #2d241a;
  font-family: 'Georgia', 'Times New Roman', serif;
}

.modal-close {
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(139, 115, 85, 0.1);
  border: none;
  border-radius: 4px;
  color: #6b5a45;
  cursor: pointer;
}

.modal-close:hover {
  background: rgba(139, 115, 85, 0.2);
  color: #3d3024;
}

.modal-close svg {
  width: 16px;
  height: 16px;
}

.modal-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 12px;
  color: #6b5a45;
  font-weight: 500;
}

.form-input,
.form-select {
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(139, 115, 85, 0.2);
  border-radius: 2px;
  color: #2d241a;
  font-size: 13px;
  outline: none;
  transition: all 0.3s ease;
}

.form-input::placeholder {
  color: #a6957a;
}

.form-input:focus,
.form-select:focus {
  border-color: #8b7355;
  box-shadow: 0 0 6px rgba(139, 115, 85, 0.15);
}

.form-select option {
  background: #f5efe6;
  color: #2d241a;
}

.radio-group {
  display: flex;
  gap: 12px;
}

.radio-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #4a3d32;
  cursor: pointer;
}

.radio-item input[type="radio"] {
  width: 14px;
  height: 14px;
  accent-color: #8b7355;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 8px;
}

.btn-cancel {
  padding: 10px 20px;
  background: rgba(139, 115, 85, 0.08);
  border: 1px solid rgba(139, 115, 85, 0.2);
  border-radius: 2px;
  color: #6b5a45;
  font-size: 13px;
  cursor: pointer;
}

.btn-cancel:hover {
  background: rgba(139, 115, 85, 0.15);
  color: #3d3024;
}

.btn-confirm {
  padding: 10px 20px;
  background: #2d241a;
  border: 1px solid #4a3d32;
  border-radius: 2px;
  color: #f5efe6;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
}

.btn-confirm:hover {
  background: #3d3024;
  border-color: #6b5a45;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

@media (max-width: 1200px) {
  .hero-section {
    flex-direction: column;
  }
  
  .hero-right {
    width: 100%;
    max-width: 600px;
    margin: 0 auto;
  }
  
  .feature-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .navbar {
    padding: 0 16px;
  }
  
  .nav-menu {
    display: none;
  }
  
  .content-wrapper {
    padding: 0 16px;
  }
  
  .hero-content {
    padding: 32px;
  }
  
  .hero-title {
    font-size: 32px;
  }
  
  .feature-cards {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  
  .friends-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .friends-list {
    flex-wrap: wrap;
  }
  
  .form-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .feature-cards {
    grid-template-columns: 1fr;
  }
  
  .adventure-info {
    flex-direction: column;
  }
  
  .adventure-cover {
    width: 100%;
    height: 100px;
  }
  
  .modal-content {
    margin: 0 12px;
    padding: 20px;
  }
}
</style>