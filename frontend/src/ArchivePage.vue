<script setup>
import { ref } from 'vue'

const emit = defineEmits(['navigate'])

const props = defineProps({
  currentPage: {
    type: String,
    default: '档案'
  }
})

const searchKeyword = ref('')
const activeNav = ref(props.currentPage)
const selectedArchive = ref(0)

const archives = [
  {
    id: 1,
    title: '龙与地下城 DND',
    tags: ['奇幻', '冒险', '高自由度'],
    character: '夜行者',
    level: 12,
    date: '2026.07.07',
    status: '进行中',
    statusColor: '#4ade80',
    actionBtn: '继续冒险',
    icon: '🐉',
    chapter: '第三章 · 黑龙苏醒',
    lastRecord: '你们进入废弃矿洞，发现古老龙族遗迹。',
    hp: 78,
    timeline: [
      { event: '发现黑龙遗迹', date: '2026.07.07' },
      { event: '获得龙鳞护符', date: '2026.07.06' },
      { event: '完成地下城探索', date: '2026.07.05' }
    ]
  },
  {
    id: 2,
    title: 'COC 7th',
    tags: ['推理', '恐怖'],
    character: '调查员',
    level: 8,
    date: '2026.06.20',
    status: '已结束',
    statusColor: '#f87171',
    actionBtn: '查看总结',
    icon: '🔱',
    chapter: '终章 · 真相大白',
    lastRecord: '真相浮出水面，一切归于寂静。',
    hp: 100,
    timeline: [
      { event: '揭开神秘面纱', date: '2026.06.20' },
      { event: '发现邪教据点', date: '2026.06.18' },
      { event: '开始调查', date: '2026.06.15' }
    ]
  },
  {
    id: 3,
    title: '赛博朋克2077',
    tags: ['科幻', '都市'],
    character: 'V',
    level: 15,
    date: '2026.06.10',
    status: '暂停',
    statusColor: '#fbbf24',
    actionBtn: '继续探索',
    icon: '🤖',
    chapter: '第二章 · 夜之城',
    lastRecord: '霓虹灯闪烁，夜之城的暗流涌动。',
    hp: 65,
    timeline: [
      { event: '遭遇银手', date: '2026.06.10' },
      { event: '获得义体升级', date: '2026.06.08' },
      { event: '进入夜之城', date: '2026.06.05' }
    ]
  }
]

const handleNavigate = (page) => {
  activeNav.value = page
  emit('navigate', page)
}

const handleSearch = () => {
  console.log('搜索档案:', searchKeyword.value)
}

const selectArchive = (index) => {
  selectedArchive.value = index
}

const handleAction = (archive) => {
  console.log(archive.actionBtn, archive.title)
}
</script>

<template>
  <div class="archive-page">
    <div class="page-bg">
      <div class="bg-overlay"></div>
      <div class="particles"></div>
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
          class="nav-item"
          :class="{ active: activeNav === '大厅' }"
          @click="handleNavigate('大厅')"
        >
          大厅
        </button>
        <button
          class="nav-item"
          :class="{ active: activeNav === '世界观' }"
          @click="handleNavigate('世界观')"
        >
          世界观
        </button>
        <button
          class="nav-item"
          :class="{ active: activeNav === '档案' }"
          @click="handleNavigate('档案')"
        >
          档案
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
      <section class="banner-section">
        <div class="banner-bg">
          <div class="banner-overlay"></div>
          <div class="runes"></div>
        </div>
        <div class="banner-content">
          <div class="title-wrap">
            <span class="decor-line"></span>
            <h1 class="banner-title">档案馆</h1>
            <span class="decor-line"></span>
          </div>
          <p class="banner-subtitle">保存和回看过去的跑团记录。</p>
        </div>
        <div class="search-section">
          <div class="search-box">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="search-icon">
              <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
            </svg>
            <input
              v-model="searchKeyword"
              type="text"
              class="search-input"
              placeholder="搜索历史档案..."
              @keyup.enter="handleSearch"
            />
          </div>
          <button class="filter-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
              <polyline points="6 10 12 14 18 10"/>
              <line x1="12" y1="20" x2="12" y2="14"/>
            </svg>
            筛选
          </button>
          <button class="layout-toggle">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <rect x="3" y="3" width="7" height="7"/>
              <rect x="14" y="3" width="7" height="7"/>
              <rect x="14" y="14" width="7" height="7"/>
              <rect x="3" y="14" width="7" height="7"/>
            </svg>
          </button>
        </div>
      </section>

      <section class="archive-content">
        <div class="archive-list">
          <h2 class="list-title">历史档案</h2>
          <div class="cards-grid">
            <div
              v-for="(archive, index) in archives"
              :key="archive.id"
              class="archive-card"
              :class="{ active: selectedArchive === index }"
              @click="selectArchive(index)"
            >
              <div class="card-corner top-left"></div>
              <div class="card-corner top-right"></div>
              <div class="card-corner bottom-left"></div>
              <div class="card-corner bottom-right"></div>
              <div class="card-header">
                <h3 class="archive-title">{{ archive.title }}</h3>
              </div>
              <div class="card-body">
                <div class="archive-tags">
                  <span
                    v-for="(tag, tagIndex) in archive.tags"
                    :key="tagIndex"
                    class="tag"
                  >
                    {{ tag }}
                  </span>
                </div>
                <div class="archive-info">
                  <div class="info-item">
                    <div class="char-avatar">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
                        <circle cx="12" cy="7" r="4"/>
                      </svg>
                    </div>
                    <span class="char-name">{{ archive.character }} Lv.{{ archive.level }}</span>
                  </div>
                  <div class="info-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                      <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                      <line x1="16" y1="2" x2="16" y2="6"/>
                      <line x1="8" y1="2" x2="8" y2="6"/>
                      <line x1="3" y1="10" x2="21" y2="10"/>
                    </svg>
                    <span>{{ archive.date }}</span>
                  </div>
                </div>
                <div class="status-bar">
                  <span class="status-label">状态</span>
                  <span class="status-value" :style="{ color: archive.statusColor }">
                    {{ archive.status }}
                  </span>
                </div>
              </div>
              <button class="card-btn" @click.stop="handleAction(archive)">
                {{ archive.actionBtn }}
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
              </button>
            </div>
          </div>
        </div>

        <div class="archive-detail">
          <div class="detail-card">
            <div class="card-header">
              <span class="header-icon">📜</span>
              <h4 class="header-title">当前档案</h4>
            </div>
            <div class="detail-content">
              <div class="detail-title-row">
                <div class="detail-info">
                  <h3 class="detail-title">{{ archives[selectedArchive].title }}</h3>
                  <p class="detail-chapter">{{ archives[selectedArchive].chapter }}</p>
                </div>
              </div>
              <div class="record-section">
                <h5 class="section-title">最后记录</h5>
                <p class="record-text">{{ archives[selectedArchive].lastRecord }}</p>
              </div>
              <div class="status-section">
                <h5 class="section-title">角色状态</h5>
                <div class="status-grid">
                  <div class="status-item">
                    <span class="status-name">HP</span>
                    <div class="hp-bar">
                      <div class="hp-fill" :style="{ width: archives[selectedArchive].hp + '%' }"></div>
                    </div>
                    <span class="status-num">{{ archives[selectedArchive].hp }}%</span>
                  </div>
                  <div class="status-item">
                    <span class="status-name">等级</span>
                    <span class="status-value-lg">Lv.{{ archives[selectedArchive].level }}</span>
                  </div>
                </div>
              </div>
              <button class="enter-btn">
                继续进入冒险
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
              </button>
            </div>
          </div>

          <div class="timeline-card">
            <div class="card-header">
              <span class="header-icon">🕐</span>
              <h4 class="header-title">最近事件</h4>
            </div>
            <div class="timeline-content">
              <div
                v-for="(event, index) in archives[selectedArchive].timeline"
                :key="index"
                class="timeline-item"
              >
                <span class="timeline-dot"></span>
                <div class="timeline-line"></div>
                <div class="timeline-info">
                  <span class="timeline-event">{{ event.event }}</span>
                  <span class="timeline-date">{{ event.date }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.archive-page {
  min-height: 100vh;
  position: relative;
  background: #090806;
}

.page-bg {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: url('/src/assets/auth-bg.png');
  background-size: cover;
  background-position: center;
  z-index: 0;
  opacity: 0.1;
}

.bg-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(180deg, rgba(9, 8, 6, 0.95) 0%, rgba(9, 8, 6, 0.98) 100%);
}

.particles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  background-image: radial-gradient(circle, rgba(245, 185, 91, 0.1) 1px, transparent 1px);
  background-size: 40px 40px;
  animation: float 20s infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50% { transform: translateY(-20px) rotate(1deg); }
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
  background: rgba(9, 8, 6, 0.98);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(245, 185, 91, 0.2);
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
  font-weight: 800;
  color: #f5b95b;
  letter-spacing: 1px;
}

.logo-cn {
  font-size: 10px;
  color: #ffe0a3;
  letter-spacing: 2px;
}

.nav-menu {
  display: flex;
  gap: 4px;
}

.nav-item {
  padding: 10px 28px;
  background: none;
  border: none;
  color: #b0b7c3;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.nav-item:hover {
  color: #ffffff;
}

.nav-item.active {
  color: #f5b95b;
  background: rgba(245, 185, 91, 0.2);
  border-bottom: 2px solid #f5b95b;
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
  background: rgba(245, 185, 91, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid rgba(245, 185, 91, 0.5);
}

.user-avatar svg {
  width: 22px;
  height: 22px;
  color: #f5b95b;
}

.user-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.user-name {
  font-size: 14px;
  color: #ffffff;
  font-weight: 600;
}

.user-level {
  padding: 2px 10px;
  background: rgba(245, 185, 91, 0.2);
  border: 1px solid rgba(245, 185, 91, 0.5);
  border-radius: 12px;
  font-size: 12px;
  color: #f5b95b;
  font-weight: 600;
}

.nav-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 8px;
  color: #b0b7c3;
  cursor: pointer;
  transition: all 0.3s ease;
}

.nav-icon:hover {
  background: rgba(255, 255, 255, 0.18);
  color: #ffffff;
}

.nav-icon svg {
  width: 18px;
  height: 18px;
}

.main-content {
  position: relative;
  z-index: 10;
  padding-top: 80px;
}

.banner-section {
  position: relative;
  height: 220px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.banner-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #090806 0%, #1a1510 50%, #090806 100%);
}

.banner-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: 
    radial-gradient(ellipse at center top, rgba(245, 185, 91, 0.1) 0%, transparent 50%),
    radial-gradient(ellipse at center bottom, rgba(111, 232, 255, 0.05) 0%, transparent 50%);
}

.runes {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0.1;
  background-image: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M30 5L35 20L50 25L38 38L42 55L30 45L18 55L22 38L10 25L25 20Z' fill='%23f5b95b'/%3E%3C/svg%3E");
  background-size: 60px 60px;
}

.banner-content {
  position: relative;
  z-index: 2;
  text-align: center;
}

.title-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 32px;
  margin-bottom: 16px;
}

.decor-line {
  width: 150px;
  height: 2px;
  background: linear-gradient(90deg, transparent, #f5b95b, transparent);
}

.banner-title {
  font-size: 48px;
  font-weight: 900;
  color: #eac77a;
  letter-spacing: 24px;
  font-family: 'KaiTi', 'STKaiti', 'SimSun', serif;
  text-shadow: 0 0 60px rgba(234, 199, 122, 0.4);
}

.banner-subtitle {
  font-size: 16px;
  color: #b99a58;
  font-weight: 400;
}

.search-section {
  position: absolute;
  bottom: -26px;
  right: 40px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 320px;
  padding: 12px 20px;
  background: rgba(9, 8, 6, 0.9);
  border: 1px solid rgba(245, 185, 91, 0.4);
  border-radius: 10px;
  backdrop-filter: blur(10px);
  box-shadow: 0 0 20px rgba(245, 185, 91, 0.1);
}

.search-icon {
  width: 20px;
  height: 20px;
  color: #9ca3af;
}

.search-input {
  flex: 1;
  background: none;
  border: none;
  outline: none;
  color: #ffffff;
  font-size: 14px;
}

.search-input::placeholder {
  color: #6b7280;
}

.filter-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: rgba(245, 185, 91, 0.2);
  border: 1px solid rgba(245, 185, 91, 0.5);
  border-radius: 10px;
  color: #f5b95b;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.filter-btn:hover {
  background: rgba(245, 185, 91, 0.3);
  border-color: #f5b95b;
}

.filter-btn svg {
  width: 16px;
  height: 16px;
}

.layout-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  background: rgba(245, 185, 91, 0.15);
  border: 1px solid rgba(245, 185, 91, 0.3);
  border-radius: 10px;
  color: #f5b95b;
  cursor: pointer;
  transition: all 0.3s ease;
}

.layout-toggle:hover {
  background: rgba(245, 185, 91, 0.25);
}

.layout-toggle svg {
  width: 18px;
  height: 18px;
}

.archive-content {
  display: flex;
  gap: 32px;
  padding: 48px;
  max-width: 1400px;
  margin: 0 auto;
}

.archive-list {
  flex: 0.7;
}

.list-title {
  font-size: 20px;
  font-weight: 800;
  color: #f5b95b;
  margin-bottom: 24px;
  letter-spacing: 4px;
}

.cards-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
}

.archive-card {
  position: relative;
  width: 420px;
  background: #090806;
  border: 1px solid rgba(245, 185, 91, 0.4);
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.4s ease;
  overflow: hidden;
}

.archive-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border: 1px solid transparent;
  border-radius: 12px;
  background: linear-gradient(#090806, #090806) padding-box,
              linear-gradient(135deg, rgba(245, 185, 91, 0.3), rgba(245, 185, 91, 0.1), rgba(245, 185, 91, 0.3)) border-box;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.4s ease;
}

.archive-card:hover,
.archive-card.active {
  border-color: rgba(245, 185, 91, 0.8);
  box-shadow: 0 0 30px rgba(245, 185, 91, 0.2),
              inset 0 0 30px rgba(245, 185, 91, 0.05);
}

.archive-card:hover::before,
.archive-card.active::before {
  opacity: 1;
}

.card-corner {
  position: absolute;
  width: 20px;
  height: 20px;
  border-color: #f5b95b;
  border-style: solid;
  border-width: 0;
  opacity: 0.6;
}

.card-corner.top-left {
  top: 8px;
  left: 8px;
  border-top-width: 2px;
  border-left-width: 2px;
}

.card-corner.top-right {
  top: 8px;
  right: 8px;
  border-top-width: 2px;
  border-right-width: 2px;
}

.card-corner.bottom-left {
  bottom: 8px;
  left: 8px;
  border-bottom-width: 2px;
  border-left-width: 2px;
}

.card-corner.bottom-right {
  bottom: 8px;
  right: 8px;
  border-bottom-width: 2px;
  border-right-width: 2px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 16px;
}

.archive-title {
  font-size: 22px;
  font-weight: 800;
  color: #eac77a;
  letter-spacing: 2px;
}

.card-body {
  margin-bottom: 16px;
}

.archive-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 14px;
}

.tag {
  padding: 4px 12px;
  background: rgba(245, 185, 91, 0.15);
  border: 1px solid rgba(245, 185, 91, 0.3);
  border-radius: 6px;
  font-size: 12px;
  color: #ffe0a3;
}

.archive-info {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: #b0b7c3;
}

.info-item svg {
  width: 16px;
  height: 16px;
  color: #9ca3af;
}

.char-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(245, 185, 91, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(245, 185, 91, 0.4);
}

.char-avatar svg {
  width: 14px;
  height: 14px;
  color: #f5b95b;
}

.char-name {
  font-weight: 600;
  color: #ffffff;
}

.status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid rgba(245, 185, 91, 0.2);
}

.status-label {
  font-size: 12px;
  color: #9ca3af;
}

.status-value {
  font-size: 14px;
  font-weight: 700;
}

.card-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 12px;
  background: linear-gradient(135deg, #5a4a1d 0%, #7b6425 50%, #5a4a1d 100%);
  border: 1px solid #f5b95b;
  border-radius: 8px;
  color: #ffffff;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
}

.card-btn:hover {
  background: linear-gradient(135deg, #6a5a2d 0%, #8b7435 50%, #6a5a2d 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(245, 185, 91, 0.4);
}

.card-btn svg {
  width: 16px;
  height: 16px;
}

.archive-detail {
  flex: 0.3;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.detail-card,
.timeline-card {
  background: rgba(40, 45, 55, 0.95);
  border: 1px solid rgba(245, 185, 91, 0.35);
  border-radius: 16px;
  padding: 24px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(245, 185, 91, 0.35);
}

.header-icon {
  font-size: 18px;
}

.header-title {
  font-size: 15px;
  font-weight: 700;
  color: #f5b95b;
  text-shadow: 0 0 20px rgba(245, 185, 91, 0.3);
}

.detail-title-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.detail-info {
  flex: 1;
}

.detail-title {
  font-size: 20px;
  font-weight: 800;
  color: #eac77a;
  margin-bottom: 4px;
}

.detail-chapter {
  font-size: 13px;
  color: #b99a58;
}

.record-section {
  margin-bottom: 20px;
}

.section-title {
  font-size: 14px;
  font-weight: 700;
  color: #ffe0a3;
  margin-bottom: 12px;
}

.record-text {
  font-size: 13px;
  color: #d1d5db;
  line-height: 1.7;
  padding: 12px;
  background: rgba(9, 8, 6, 0.6);
  border-radius: 8px;
  border: 1px solid rgba(245, 185, 91, 0.2);
}

.status-section {
  margin-bottom: 20px;
}

.status-grid {
  display: flex;
  gap: 16px;
}

.status-item {
  flex: 1;
}

.status-name {
  display: block;
  font-size: 12px;
  color: #9ca3af;
  margin-bottom: 8px;
}

.hp-bar {
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 6px;
}

.hp-fill {
  height: 100%;
  background: linear-gradient(90deg, #4ade80, #22c55e);
  border-radius: 4px;
  transition: width 0.5s ease;
}

.status-num {
  font-size: 14px;
  font-weight: 700;
  color: #4ade80;
}

.status-value-lg {
  font-size: 24px;
  font-weight: 800;
  color: #f5b95b;
}

.enter-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 16px;
  background: linear-gradient(135deg, rgba(245, 185, 91, 0.35) 0%, rgba(212, 154, 63, 0.25) 100%);
  border: 2px solid #f5b95b;
  border-radius: 12px;
  color: #f5b95b;
  font-size: 15px;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.3s ease;
}

.enter-btn:hover {
  background: linear-gradient(135deg, rgba(245, 185, 91, 0.45) 0%, rgba(212, 154, 63, 0.35) 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(245, 185, 91, 0.35);
}

.enter-btn svg {
  width: 18px;
  height: 18px;
}

.timeline-content {
  position: relative;
}

.timeline-item {
  display: flex;
  gap: 12px;
  padding-bottom: 20px;
  position: relative;
}

.timeline-item:last-child {
  padding-bottom: 0;
}

.timeline-item:last-child .timeline-line {
  display: none;
}

.timeline-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #f5b95b;
  flex-shrink: 0;
  box-shadow: 0 0 10px rgba(245, 185, 91, 0.5);
}

.timeline-line {
  position: absolute;
  left: 5px;
  top: 14px;
  width: 2px;
  height: calc(100% - 14px);
  background: linear-gradient(180deg, rgba(245, 185, 91, 0.5) 0%, rgba(245, 185, 91, 0.1) 100%);
}

.timeline-info {
  flex: 1;
}

.timeline-event {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 4px;
}

.timeline-date {
  font-size: 12px;
  color: #9ca3af;
}

@media (max-width: 1200px) {
  .archive-content {
    flex-direction: column;
  }
  
  .archive-list {
    flex: 1;
  }
  
  .archive-detail {
    flex: 1;
  }
  
  .cards-grid {
    justify-content: center;
  }
}

@media (max-width: 768px) {
  .navbar {
    padding: 0 16px;
  }
  
  .nav-menu {
    display: none;
  }
  
  .banner-title {
    font-size: 32px;
    letter-spacing: 16px;
  }
  
  .search-section {
    position: static;
    justify-content: center;
    margin-top: 20px;
  }
  
  .archive-content {
    padding: 24px 16px;
  }
  
  .archive-card {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .banner-title {
    font-size: 28px;
    letter-spacing: 12px;
  }
}
</style>
