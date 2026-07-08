<script setup>
import { ref } from 'vue'

const emit = defineEmits(['navigate'])

const props = defineProps({
  currentPage: {
    type: String,
    default: '世界观'
  }
})

const searchKeyword = ref('')
const activeNav = ref(props.currentPage)
const selectedWorldview = ref(0)

const worldviews = [
  {
    id: 1,
    title: '龙与地下城 DND',
    tags: ['奇幻', '冒险'],
    description: '主值世界观，适合新手入门与多人长期跑团。',
    cover: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=fantasy%20dragon%20and%20knights%20medieval%20castle%20dungeons%20and%20dragons%20dark%20fantasy%20epic&image_size=landscape_16_9',
    icon: '🐉',
    recommendedModule: '追捕克仑可 Krenko\'s Way',
    modules: [
      { name: '追捕克仑可 Krenko\'s Way', players: '4-6人', time: '3-5小时', type: '冒险' },
      { name: '失落矿洞的秘密', players: '4-6人', time: '2-3小时', type: '冒险' },
      { name: '龙息之城的阴影', players: '4-6人', time: '3-5小时', type: '冒险' }
    ]
  },
  {
    id: 2,
    title: 'COC 7th',
    tags: ['调查', '悬疑', '恐怖'],
    description: '克苏鲁神话世界观，揭开不可名状的真相。',
    cover: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=cthulhu%20mythos%20dark%20horror%20investigation%20mysterious%20ancient%20ruins%20tentacles%20lovecraftian&image_size=landscape_16_9',
    icon: '🔱',
    recommendedModule: '捕梦 / 双盲 / 慢慢',
    modules: [
      { name: '捕梦者', players: '3-5人', time: '3-4小时', type: '悬疑' },
      { name: '双盲', players: '4-6人', time: '4-6小时', type: '恐怖' },
      { name: '慢慢', players: '4-6人', time: '3-5小时', type: '惊悚' }
    ]
  },
  {
    id: 3,
    title: '自定义世界观',
    tags: ['原创', '自由', '自定义规则'],
    description: '打造属于你的世界与规则体系，开启无限可能的冒险。',
    cover: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=custom%20fantasy%20world%20creation%20magic%20orb%20mystical%20library%20scrolls%20endless%20possibilities&image_size=landscape_16_9',
    icon: '✨',
    recommendedModule: '',
    modules: []
  }
]

const handleNavigate = (page) => {
  activeNav.value = page
  emit('navigate', page)
}

const handleSearch = () => {
  console.log('搜索世界观:', searchKeyword.value)
}

const selectWorldview = (index) => {
  selectedWorldview.value = index
}

const enterWorldview = (index) => {
  if (index !== undefined) {
    selectedWorldview.value = index
  }
  const worldview = worldviews[selectedWorldview.value]
  emit('navigate', '角色', worldview)
}

const enterModule = (module) => {
  console.log('进入模组:', module)
}

const handleCreateCustom = () => {
  console.log('开始创建自定义世界观')
}
</script>

<template>
  <div class="worldview-page">
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
      <section class="hero-section">
        <div class="hero-header">
          <div class="hero-top-row">
            <div class="title-wrap">
              <span class="decor-line"></span>
              <h1 class="hero-title">世界观馆</h1>
              <span class="decor-line"></span>
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
                  placeholder="搜索世界观或模组..."
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
          </div>
          <p class="hero-desc">先选择世界观，再进入对应模组展开跑团冒险。</p>
          <p class="hero-hint">世界观不是剧本，模组属于世界观之下。</p>
        </div>

        <div class="worldview-grid">
          <div class="worldview-main">
            <div class="worldview-cards">
              <div
                v-for="(worldview, index) in worldviews"
                :key="worldview.id"
                class="worldview-card"
                :class="{ active: selectedWorldview === index }"
                @click="selectWorldview(index)"
              >
                <div class="card-cover">
                  <img :src="worldview.cover" :alt="worldview.title" class="cover-img" />
                  <div class="cover-overlay"></div>
                  <div v-if="index === 0" class="status-badge main">主推</div>
                </div>
                <div class="card-content">
                  <h3 class="worldview-title">{{ worldview.title }}</h3>
                  <div class="worldview-tags">
                    <span
                      v-for="(tag, tagIndex) in worldview.tags"
                      :key="tagIndex"
                      class="tag"
                    >
                      {{ tag }}
                    </span>
                  </div>
                  <p class="worldview-desc">{{ worldview.description }}</p>
                  <div v-if="worldview.recommendedModule" class="recommend-line">
                    <span class="recommend-label">推荐模组：</span>
                    <span class="recommend-value">{{ worldview.recommendedModule }}</span>
                  </div>
                  <button class="card-btn" @click.stop="index === 2 ? handleCreateCustom() : enterWorldview(index)">
                    {{ index === 2 ? '开始创建' : '进入世界观' }}
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                      <path d="M5 12h14M12 5l7 7-7 7"/>
                    </svg>
                  </button>
                </div>
              </div>
            </div>

            <div class="modules-preview">
              <div class="preview-header">
                <div class="title-wrap">
                  <span class="decor-line small"></span>
                  <h3 class="preview-title">模组预览 · {{ worldviews[selectedWorldview].title }}</h3>
                  <span class="decor-line small"></span>
                </div>
                <span class="preview-hint">以下模组均属于当前选中世界观，可点击查看详情或直接进入</span>
                <button class="view-all">查看全部</button>
              </div>
              <div class="modules-list">
                <div
                  v-for="(module, index) in worldviews[selectedWorldview].modules"
                  :key="index"
                  class="module-item"
                  @click="enterModule(module)"
                >
                  <div class="module-cover">
                    <img :src="worldviews[selectedWorldview].cover" :alt="module.name" class="module-img" />
                    <div class="cover-overlay"></div>
                    <span v-if="index === 0" class="recommend-badge">推荐</span>
                  </div>
                  <div class="module-info">
                    <h4 class="module-name">{{ module.name }}</h4>
                    <div class="module-meta">
                      <span class="meta-item">{{ module.players }}</span>
                      <span class="meta-item">{{ module.time }}</span>
                      <span class="meta-item">{{ module.type }}</span>
                    </div>
                  </div>
                  <button class="enter-btn">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                      <path d="M5 12h14M12 5l7 7-7 7"/>
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div class="worldview-sidebar">
            <div class="sidebar-card">
              <div class="card-header">
                <span class="header-icon">📜</span>
                <h4 class="header-title">当前选中世界观</h4>
              </div>
              <div class="selected-info">
                <div class="selected-detail">
                  <h3 class="selected-title">{{ worldviews[selectedWorldview].title }}</h3>
                  <p class="selected-desc">{{ worldviews[selectedWorldview].description }}</p>
                </div>
              </div>
              <div class="recommend-section">
                <h5 class="section-title">推荐模组</h5>
                <div class="recommend-list">
                  <div
                    v-for="(module, index) in worldviews[selectedWorldview].modules"
                    :key="index"
                    class="recommend-item"
                    @click="enterModule(module)"
                  >
                    <div class="item-cover">
                      <img :src="worldviews[selectedWorldview].cover" :alt="module.name" class="item-img" />
                      <div class="cover-overlay"></div>
                    </div>
                    <div class="item-info">
                      <span class="item-name">{{ module.name }}</span>
                      <span class="item-meta">{{ module.players }} · {{ module.time }}</span>
                    </div>
                    <button class="recommend-btn">推荐</button>
                  </div>
                </div>
              </div>
              <button class="enter-worldview-btn" @click="enterWorldview()">
                进入 {{ worldviews[selectedWorldview].title.replace(' DND', '') }} 世界观
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.worldview-page {
  min-height: 100vh;
  position: relative;
  background: #080a12;
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
  opacity: 0.2;
}

.bg-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: 
    radial-gradient(ellipse at 50% 0%, rgba(201, 169, 98, 0.02) 0%, transparent 60%),
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
  width: 18px;
  height: 18px;
}

.main-content {
  position: relative;
  z-index: 10;
  padding-top: 80px;
  padding-bottom: 60px;
}

.hero-section {
  padding: 48px;
  max-width: 1400px;
  margin: 0 auto;
}

.hero-header {
  margin-bottom: 48px;
}

.hero-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.title-wrap {
  display: flex;
  align-items: center;
  gap: 28px;
}

.decor-line {
  width: 120px;
  height: 3px;
  background: linear-gradient(90deg, transparent, #8b7355, transparent);
}

.decor-line.small {
  width: 60px;
  height: 2px;
}

.hero-title {
  font-size: 36px;
  font-weight: 700;
  color: #2d241a;
  letter-spacing: 16px;
  font-family: 'Georgia', 'Times New Roman', serif;
}

.hero-desc {
  font-size: 15px;
  color: #3d3024;
  font-weight: 500;
  margin-bottom: 8px;
  margin-top: 16px;
  font-family: 'Georgia', 'Times New Roman', serif;
}

.hero-hint {
  font-size: 13px;
  color: #6b5a45;
}

.search-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 320px;
  padding: 10px 18px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(139, 115, 85, 0.2);
  border-radius: 4px;
}

.search-icon {
  width: 20px;
  height: 20px;
  color: #8b7355;
}

.search-input {
  flex: 1;
  background: none;
  border: none;
  outline: none;
  color: #2d241a;
  font-size: 14px;
}

.search-input::placeholder {
  color: #a6957a;
}

.filter-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  background: rgba(139, 115, 85, 0.1);
  border: 1px solid rgba(139, 115, 85, 0.3);
  border-radius: 4px;
  color: #6b5a45;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.filter-btn:hover {
  background: rgba(139, 115, 85, 0.2);
  border-color: #8b7355;
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
  border-radius: 12px;
  color: #f5b95b;
  cursor: pointer;
  transition: all 0.3s ease;
}

.layout-toggle:hover {
  background: rgba(245, 185, 91, 0.25);
}

.layout-toggle svg {
  width: 20px;
  height: 20px;
}

.worldview-grid {
  display: flex;
  gap: 32px;
}

.worldview-main {
  flex: 2;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.worldview-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 28px;
}

.worldview-card {
  background: #f5efe6;
  border: 1px solid rgba(139, 115, 85, 0.2);
  border-radius: 4px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.4s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.worldview-card:hover {
  transform: translateY(-3px);
  border-color: rgba(139, 115, 85, 0.4);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
}

.worldview-card.active {
  border-color: #8b7355;
  box-shadow: 0 4px 16px rgba(139, 115, 85, 0.15);
}

.card-cover {
  position: relative;
  height: 160px;
  overflow: hidden;
}

.cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(180deg, rgba(245, 239, 230, 0) 0%, rgba(245, 239, 230, 0.7) 100%);
  pointer-events: none;
}

.status-badge {
  position: absolute;
  top: 12px;
  left: 12px;
  padding: 4px 14px;
  border-radius: 2px;
  font-size: 12px;
  font-weight: 600;
  z-index: 3;
}

.status-badge.main {
  background: #2d241a;
  color: #f5efe6;
}

.card-content {
  padding: 18px;
}

.worldview-title {
  font-size: 20px;
  font-weight: 700;
  color: #2d241a;
  margin-bottom: 10px;
  font-family: 'Georgia', 'Times New Roman', serif;
}

.worldview-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.tag {
  padding: 3px 10px;
  background: rgba(139, 115, 85, 0.1);
  border: 1px solid rgba(139, 115, 85, 0.25);
  border-radius: 2px;
  font-size: 11px;
  color: #6b5a45;
}

.worldview-desc {
  font-size: 13px;
  color: #4a3d32;
  line-height: 1.6;
  margin-bottom: 14px;
}

.recommend-line {
  font-size: 13px;
  color: #6b5a45;
  margin-bottom: 16px;
}

.recommend-label {
  color: #6b5a45;
}

.recommend-value {
  color: #8b7355;
  font-weight: 600;
}

.card-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  background: #2d241a;
  border: 1px solid #4a3d32;
  border-radius: 2px;
  color: #f5efe6;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: 'Georgia', 'Times New Roman', serif;
}

.card-btn:hover {
  background: #3d3024;
  border-color: #6b5a45;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.card-btn svg {
  width: 18px;
  height: 18px;
}

.modules-preview {
  background: rgba(40, 45, 55, 0.95);
  border: 1px solid rgba(245, 185, 91, 0.35);
  border-radius: 16px;
  padding: 28px;
}

.preview-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.preview-title {
  font-size: 18px;
  font-weight: 800;
  color: #f5b95b;
  text-shadow: 0 0 20px rgba(245, 185, 91, 0.3);
}

.preview-hint {
  flex: 1;
  font-size: 13px;
  color: #b0b7c3;
  text-align: center;
}

.view-all {
  padding: 10px 24px;
  background: none;
  border: 1px solid rgba(139, 115, 85, 0.3);
  border-radius: 4px;
  color: #6b5a45;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.view-all:hover {
  background: rgba(139, 115, 85, 0.1);
}

.modules-list {
  display: flex;
  gap: 20px;
}

.module-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f5efe6;
  border: 1px solid rgba(139, 115, 85, 0.15);
  border-radius: 4px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
}

.module-item:hover {
  border-color: rgba(139, 115, 85, 0.35);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.module-cover {
  position: relative;
  height: 130px;
  overflow: hidden;
}

.module-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.recommend-badge {
  position: absolute;
  top: 10px;
  left: 10px;
  padding: 3px 10px;
  background: #2d241a;
  border-radius: 2px;
  font-size: 11px;
  font-weight: 600;
  color: #f5efe6;
  z-index: 2;
}

.module-info {
  padding: 14px;
  flex: 1;
}

.module-name {
  font-size: 15px;
  font-weight: 600;
  color: #2d241a;
  margin-bottom: 10px;
  font-family: 'Georgia', 'Times New Roman', serif;
}

.module-meta {
  display: flex;
  gap: 14px;
}

.meta-item {
  font-size: 12px;
  color: #6b5a45;
}

.enter-btn {
  margin: 0 14px 14px;
  padding: 10px;
  background: rgba(139, 115, 85, 0.1);
  border: 1px solid rgba(139, 115, 85, 0.3);
  border-radius: 4px;
  color: #6b5a45;
  cursor: pointer;
  transition: all 0.3s ease;
}

.enter-btn:hover {
  background: rgba(139, 115, 85, 0.2);
}

.enter-btn svg {
  width: 16px;
  height: 16px;
}

.worldview-sidebar {
  flex: 1;
}

.sidebar-card {
  background: #f5efe6;
  border: 1px solid rgba(139, 115, 85, 0.2);
  border-radius: 4px;
  padding: 22px;
  height: fit-content;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 18px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(139, 115, 85, 0.15);
}

.header-icon {
  font-size: 16px;
  color: #8b7355;
}

.header-title {
  font-size: 15px;
  font-weight: 600;
  color: #2d241a;
  font-family: 'Georgia', 'Times New Roman', serif;
}

.selected-info {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 22px;
  padding: 14px;
  background: rgba(139, 115, 85, 0.06);
  border-radius: 4px;
  border: 1px solid rgba(139, 115, 85, 0.12);
}

.selected-detail {
  flex: 1;
}

.selected-title {
  font-size: 20px;
  font-weight: 600;
  color: #2d241a;
  margin-bottom: 8px;
  font-family: 'Georgia', 'Times New Roman', serif;
}

.selected-desc {
  font-size: 13px;
  color: #4a3d32;
  line-height: 1.6;
}

.recommend-section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #3d3024;
  margin-bottom: 14px;
  font-family: 'Georgia', 'Times New Roman', serif;
}

.recommend-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.recommend-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px;
  background: rgba(139, 115, 85, 0.05);
  border: 1px solid rgba(139, 115, 85, 0.12);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.recommend-item:hover {
  border-color: rgba(139, 115, 85, 0.3);
  background: rgba(139, 115, 85, 0.08);
}

.item-cover {
  width: 56px;
  height: 56px;
  border-radius: 2px;
  overflow: hidden;
}

.item-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.item-info {
  flex: 1;
}

.item-name {
  display: block;
  font-size: 14px;
  color: #2d241a;
  font-weight: 500;
  margin-bottom: 4px;
}

.item-meta {
  font-size: 12px;
  color: #6b5a45;
}

.recommend-btn {
  padding: 6px 16px;
  background: rgba(245, 185, 91, 0.2);
  border: 1px solid rgba(245, 185, 91, 0.5);
  border-radius: 8px;
  color: #f5b95b;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
}

.recommend-btn:hover {
  background: rgba(245, 185, 91, 0.35);
}

.enter-worldview-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 18px;
  background: linear-gradient(135deg, rgba(245, 185, 91, 0.35) 0%, rgba(212, 154, 63, 0.25) 100%);
  border: 2px solid #f5b95b;
  border-radius: 12px;
  color: #f5b95b;
  font-size: 16px;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.3s ease;
}

.enter-worldview-btn:hover {
  background: linear-gradient(135deg, rgba(245, 185, 91, 0.45) 0%, rgba(212, 154, 63, 0.35) 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(245, 185, 91, 0.35);
}

.enter-worldview-btn svg {
  width: 20px;
  height: 20px;
}

@media (max-width: 1200px) {
  .worldview-grid {
    flex-direction: column;
  }
  
  .worldview-main {
    flex: 1;
  }
  
  .worldview-sidebar {
    flex: 1;
  }
}

@media (max-width: 900px) {
  .worldview-cards {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .modules-list {
    flex-direction: column;
  }
}

@media (max-width: 768px) {
  .navbar {
    padding: 0 16px;
  }
  
  .nav-menu {
    display: none;
  }
  
  .hero-section {
    padding: 28px 16px;
  }
  
  .hero-title {
    font-size: 36px;
    letter-spacing: 16px;
  }
  
  .search-section {
    flex-direction: column;
    align-items: center;
  }
  
  .search-box {
    max-width: 100%;
  }
  
  .worldview-cards {
    grid-template-columns: 1fr;
    gap: 24px;
  }
  
  .preview-header {
    flex-wrap: wrap;
  }
  
  .preview-hint {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .hero-title {
    font-size: 32px;
    letter-spacing: 12px;
  }
  
  .card-cover {
    height: 180px;
  }
}
</style>
