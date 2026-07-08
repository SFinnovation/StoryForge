<script setup>
import { computed, ref } from 'vue'
import lobbyBackground from '../背景/大厅界面.png'
import productIcon from '../图标/产品图标.png'
import goblinCover from '../游戏种类/哥布林.jpg'
import dndCover from '../游戏种类/龙与地下城.jpg'
import cocCover from '../游戏种类/克苏鲁.jpg'
import customCover from '../游戏种类/世界观.jpg'

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

const navItems = ['大厅', '世界观', '档案', '角色', '商城']

const worldviews = [
  {
    id: 1,
    title: '龙与地下城 DND',
    shortTitle: 'DND',
    subtitle: '主推世界观，适合新手入门与多人长期跑团。',
    tags: ['奇幻', '冒险', '高自由度'],
    description: '从城堡、地下城到巨龙阴影，适合长期剧情推进与团队成长。',
    cover: dndCover,
    recommendedModule: '追捕克伦可 Krenko’s Way',
    modules: [
      {
        name: '追捕克伦可 Krenko’s Way',
        players: '4-6 人',
        time: '8-12 小时',
        type: '冒险',
        summary: '地下帮派首领克伦可越狱逃亡，玩家受命追捕。',
        cover: goblinCover
      },
      {
        name: '失落矿洞的秘密',
        players: '3-5 人',
        time: '6-10 小时',
        type: '冒险',
        summary: '古老矿洞深处隐藏着矮人与龙的失落遗迹。',
        cover: lobbyBackground
      },
      {
        name: '龙息之城的阴影',
        players: '4-6 人',
        time: '8-12 小时',
        type: '史诗',
        summary: '王城在夜幕下动荡不安，旧誓与龙息一同苏醒。',
        cover: dndCover
      }
    ]
  },
  {
    id: 2,
    title: 'COC 7th',
    shortTitle: 'COC 7th',
    subtitle: '调查、悬疑与不可名状。',
    tags: ['调查', '悬疑', '恐怖'],
    description: '旧日阴影缓慢逼近，适合偏推理、心理压力和氛围感团本。',
    cover: cocCover,
    recommendedModule: '捕梦 / 双盲 / 慢慢',
    modules: [
      {
        name: '捕梦者',
        players: '3-5 人',
        time: '3-4 小时',
        type: '悬疑',
        summary: '梦境与现实边界逐渐瓦解，调查员开始怀疑自我。',
        cover: cocCover
      },
      {
        name: '双盲',
        players: '4-6 人',
        time: '4-6 小时',
        type: '恐怖',
        summary: '普通的学术委托背后，是组织与神话生物的双重骗局。',
        cover: cocCover
      }
    ]
  },
  {
    id: 3,
    title: '自定义世界观',
    shortTitle: '自定义',
    subtitle: '原创规则与世界自由搭建。',
    tags: ['原创', '自由', '自定义规则'],
    description: '你来定义地图、势力、规则和冲突，AI 按设定持续展开世界。',
    cover: customCover,
    recommendedModule: '从设定开始',
    modules: [
      {
        name: '从一页设定出发',
        players: '2-6 人',
        time: '自由',
        type: '原创',
        summary: '从地图、神秘学体系和势力关系开始构建你的世界。',
        cover: customCover
      }
    ]
  }
]

const selectedData = computed(() => worldviews[selectedWorldview.value])

const filteredWorldviews = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  if (!keyword) return worldviews

  return worldviews.filter((worldview) => {
    const haystack = [
      worldview.title,
      worldview.subtitle,
      worldview.description,
      worldview.tags.join(' '),
      worldview.modules.map((module) => module.name).join(' ')
    ]
      .join(' ')
      .toLowerCase()

    return haystack.includes(keyword)
  })
})

const selectedModules = computed(() => selectedData.value.modules || [])

const handleNavigate = (page) => {
  activeNav.value = page
  emit('navigate', page)
}

const selectWorldview = (worldviewId) => {
  const index = worldviews.findIndex((item) => item.id === worldviewId)
  if (index >= 0) {
    selectedWorldview.value = index
  }
}

const enterWorldview = () => {
  emit('navigate', '角色', selectedData.value)
}

const enterModule = (module) => {
  console.log('进入模组:', module)
}
</script>

<template>
  <div class="worldview-page">
    <div class="page-background">
      <img class="page-image" :src="lobbyBackground" alt="世界观背景" />
      <div class="bg-shadow"></div>
      <div class="bg-focus"></div>
      <div class="bg-grid"></div>
    </div>

    <nav class="navbar">
      <div class="nav-logo">
        <img class="logo-icon" :src="productIcon" alt="StoryForge 产品图标" />
        <div class="logo-text">
          <span class="logo-en">StoryForge</span>
          <span class="logo-cn">灵境档案</span>
        </div>
      </div>

      <div class="nav-menu">
        <button
          v-for="item in navItems"
          :key="item"
          class="nav-item"
          :class="{ active: activeNav === item }"
          @click="handleNavigate(item)"
        >
          {{ item }}
        </button>
      </div>

      <div class="nav-user">
        <div class="user-chip">
          <div class="user-avatar">夜</div>
          <div class="user-info">
            <span class="user-name">夜行者</span>
            <span class="user-level">Lv.12</span>
          </div>
        </div>
        <button class="nav-icon" aria-label="消息">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">
            <path d="M4 6h16v12H4z" />
            <path d="m4 7 8 6 8-6" />
          </svg>
        </button>
        <button class="nav-icon" aria-label="设置">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.7 1.7 0 0 0 .34 1.82l.05.06a2 2 0 1 1-2.83 2.83l-.06-.05A1.7 1.7 0 0 0 15 19.4a1.7 1.7 0 0 0-1 1.53V21a2 2 0 1 1-4 0v-.08a1.7 1.7 0 0 0-1-1.52 1.7 1.7 0 0 0-1.9.36l-.06.05a2 2 0 1 1-2.83-2.83l.05-.06A1.7 1.7 0 0 0 4.6 15a1.7 1.7 0 0 0-1.52-1H3a2 2 0 1 1 0-4h.08A1.7 1.7 0 0 0 4.6 9a1.7 1.7 0 0 0-.34-1.82l-.05-.06a2 2 0 1 1 2.83-2.83l.06.05A1.7 1.7 0 0 0 9 4.6a1.7 1.7 0 0 0 1-1.52V3a2 2 0 1 1 4 0v.08a1.7 1.7 0 0 0 1 1.52 1.7 1.7 0 0 0 1.9-.36l.06-.05a2 2 0 1 1 2.83 2.83l-.05.06A1.7 1.7 0 0 0 19.4 9c.14.47.66.8 1.15.8H21a2 2 0 1 1 0 4h-.45c-.49 0-1.01.33-1.15.8Z" />
          </svg>
        </button>
      </div>
    </nav>

    <main class="worldview-shell">
      <section class="top-stage">
        <div class="hero-copy">
          <div class="title-row">
            <span></span>
            <p>WORLDVIEW GALLERY</p>
          </div>
          <h1>世界观馆</h1>
          <p class="hero-description">
            先选择世界观，再进入对应模组开启跑团冒险。
          </p>
          <p class="hero-note">世界观不是剧本，模组属于世界观之下。</p>
        </div>

        <div class="search-panel">
          <div class="search-box">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
              <path d="M21 21l-6-6m2-5a7 7 0 1 1-14 0 7 7 0 0 1 14 0Z" />
            </svg>
            <input
              v-model="searchKeyword"
              type="text"
              placeholder="搜索世界观或模组..."
            />
          </div>
          <button class="filter-btn">筛选</button>
          <button class="grid-btn" aria-label="切换布局">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
              <rect x="4" y="4" width="6" height="6" />
              <rect x="14" y="4" width="6" height="6" />
              <rect x="4" y="14" width="6" height="6" />
              <rect x="14" y="14" width="6" height="6" />
            </svg>
          </button>
        </div>
      </section>

      <section class="content-grid">
        <div class="left-column">
          <div class="worldview-cards">
            <article
              v-for="worldview in filteredWorldviews"
              :key="worldview.id"
              class="world-card"
              :class="{ active: selectedData.id === worldview.id }"
              @click="selectWorldview(worldview.id)"
            >
              <div class="card-image-wrap">
                <img :src="worldview.cover" :alt="worldview.title" class="card-image" />
                <div class="card-overlay"></div>
                <div v-if="worldview.id === 1" class="card-badge">主推</div>
              </div>
              <div class="card-body">
                <h3>{{ worldview.title }}</h3>
                <div class="tag-row">
                  <span v-for="tag in worldview.tags" :key="tag">{{ tag }}</span>
                </div>
                <p class="card-description">{{ worldview.subtitle }}</p>
                <p class="card-module">推荐模组：{{ worldview.recommendedModule }}</p>
                <button class="card-action" @click.stop="selectWorldview(worldview.id)">查看模组</button>
              </div>
            </article>
          </div>

          <section class="module-panel">
            <div class="module-panel-head">
              <div class="module-head-copy">
                <img :src="productIcon" alt="" />
                <h2>模组预览 · {{ selectedData.title }}</h2>
              </div>
              <button class="view-all-btn">查看全部</button>
            </div>

            <div class="module-list">
              <article
                v-for="(module, index) in selectedModules"
                :key="module.name"
                class="module-card"
                @click="enterModule(module)"
              >
                <div class="module-thumb">
                  <img :src="module.cover" :alt="module.name" />
                  <span v-if="index === 0" class="module-badge">推荐</span>
                </div>
                <div class="module-content">
                  <h3>{{ module.name }}</h3>
                  <div class="module-meta">
                    <span>{{ module.players }}</span>
                    <span>{{ module.time }}</span>
                    <span>{{ module.type }}</span>
                  </div>
                  <p>{{ module.summary }}</p>
                </div>
                <button class="module-enter">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
                    <path d="M5 12h14M12 5l7 7-7 7" />
                  </svg>
                </button>
              </article>
            </div>
          </section>
        </div>

        <aside class="right-column">
          <section class="intel-card">
            <p class="intel-kicker">当前选中世界观</p>
            <div class="selected-header">
              <img :src="productIcon" alt="" />
              <h2>{{ selectedData.title }}</h2>
            </div>
            <p class="intel-description">{{ selectedData.description }}</p>
            <div class="intel-tags">
              <span v-for="tag in selectedData.tags" :key="tag">{{ tag }}</span>
            </div>
            <div class="intel-divider"></div>
            <p class="intel-kicker">推荐模组</p>
            <div class="recommend-list">
              <button
                v-for="module in selectedModules"
                :key="module.name"
                class="recommend-item"
                @click="enterModule(module)"
              >
                <img :src="module.cover" :alt="module.name" />
                <div class="recommend-text">
                  <strong>{{ module.name }}</strong>
                  <span>{{ module.players }} · {{ module.time }}</span>
                </div>
              </button>
            </div>
            <button class="primary-enter" @click="enterWorldview">进入 {{ selectedData.shortTitle }} 世界观</button>
          </section>
        </aside>
      </section>
    </main>
  </div>
</template>

<style scoped>
.worldview-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background: #050607;
  color: #f0e7d8;
}

.page-background,
.bg-shadow,
.bg-focus,
.bg-grid {
  position: absolute;
  inset: 0;
}

.page-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: 56% 21%;
  filter: brightness(0.72) saturate(0.94);
  transform: scale(1.03);
}

.bg-shadow {
  background:
    linear-gradient(90deg, rgba(4, 6, 11, 0.84) 0%, rgba(4, 7, 11, 0.74) 28%, rgba(4, 7, 11, 0.42) 56%, rgba(21, 11, 4, 0.76) 100%),
    linear-gradient(180deg, rgba(0, 0, 0, 0.56) 0%, transparent 22%, transparent 84%, rgba(0, 0, 0, 0.56) 100%);
}

.bg-focus {
  background:
    radial-gradient(circle at 59% 25%, rgba(95, 212, 255, 0.18), transparent 14%),
    radial-gradient(circle at 83% 26%, rgba(255, 183, 72, 0.18), transparent 12%);
  mix-blend-mode: screen;
}

.bg-grid {
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
  display: flex;
  align-items: center;
  gap: 10px;
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
}

.nav-item.active,
.nav-item:hover {
  color: #f6c56e;
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
}

.nav-icon svg {
  width: 19px;
  height: 19px;
}

.worldview-shell {
  position: relative;
  z-index: 2;
  max-width: 1620px;
  margin: 0 auto;
  padding: 18px 34px 22px;
  display: grid;
  gap: 16px;
}

.top-stage {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, 540px);
  gap: 18px;
  align-items: end;
}

.hero-copy {
  max-width: 620px;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}

.title-row span {
  width: 76px;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(245, 187, 88, 1), transparent);
}

.title-row p,
.intel-kicker {
  color: #f0d59d;
  font-size: 0.9rem;
  letter-spacing: 0.18em;
}

.hero-copy h1 {
  font-size: clamp(3.4rem, 6vw, 5.6rem);
  line-height: 0.94;
  color: #f1cb82;
}

.hero-description {
  margin-top: 12px;
  max-width: 36ch;
  color: rgba(242, 231, 216, 0.84);
  font-size: 1.18rem;
  line-height: 1.7;
}

.hero-note {
  margin-top: 10px;
  color: rgba(245, 208, 138, 0.82);
}

.search-panel {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: 12px;
  align-items: center;
}

.search-box,
.filter-btn,
.grid-btn,
.view-all-btn,
.card-action,
.primary-enter {
  border: 1px solid rgba(245, 187, 88, 0.18);
  border-radius: 14px;
  background: rgba(8, 12, 18, 0.62);
  backdrop-filter: blur(10px);
  color: #f3d49b;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
}

.search-box svg {
  width: 18px;
  height: 18px;
  color: rgba(240, 231, 216, 0.54);
}

.search-box input {
  width: 100%;
  background: transparent;
  border: none;
  outline: none;
  color: #f0e7d8;
}

.search-box input::placeholder {
  color: rgba(240, 231, 216, 0.36);
}

.filter-btn,
.grid-btn {
  min-height: 52px;
  padding: 0 18px;
  cursor: pointer;
}

.grid-btn {
  width: 56px;
  display: grid;
  place-items: center;
}

.grid-btn svg {
  width: 22px;
  height: 22px;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.55fr) 388px;
  gap: 18px;
  align-items: start;
}

.left-column {
  display: grid;
  gap: 16px;
}

.worldview-cards {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.world-card,
.module-panel,
.intel-card {
  border: 1px solid rgba(245, 187, 88, 0.14);
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(10, 14, 22, 0.82), rgba(8, 11, 18, 0.88));
  backdrop-filter: blur(10px);
  box-shadow: 0 18px 34px rgba(0, 0, 0, 0.24);
}

.world-card {
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.28s ease, border-color 0.28s ease, box-shadow 0.28s ease;
}

.world-card:hover,
.world-card.active {
  transform: translateY(-4px);
  border-color: rgba(245, 187, 88, 0.42);
}

.card-image-wrap {
  position: relative;
  height: 238px;
}

.card-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.card-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(4, 7, 12, 0.08), rgba(4, 7, 12, 0.76));
}

.card-badge,
.module-badge {
  position: absolute;
  top: 14px;
  left: 14px;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(245, 187, 88, 0.18);
  border: 1px solid rgba(245, 187, 88, 0.42);
  color: #f6d08a;
  font-size: 12px;
}

.card-body {
  display: grid;
  gap: 10px;
  padding: 18px;
}

.card-body h3,
.module-content h3,
.selected-header h2 {
  color: #f2ead9;
  font-size: 1.86rem;
}

.tag-row,
.intel-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-row span,
.intel-tags span {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: rgba(240, 231, 216, 0.76);
  font-size: 12px;
}

.card-description,
.card-module,
.intel-description,
.module-content p,
.recommend-text span {
  color: rgba(240, 231, 216, 0.76);
  line-height: 1.65;
}

.card-module {
  color: rgba(245, 208, 138, 0.9);
}

.card-action,
.view-all-btn,
.primary-enter {
  min-height: 46px;
  padding: 0 18px;
  font-weight: 700;
  cursor: pointer;
}

.module-panel {
  padding: 18px;
}

.module-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.module-head-copy {
  display: flex;
  align-items: center;
  gap: 10px;
}

.module-head-copy img {
  width: 18px;
  height: 18px;
}

.module-head-copy h2 {
  color: #f3d49b;
  font-size: 1.36rem;
}

.module-list,
.recommend-list {
  display: grid;
  gap: 12px;
  margin-top: 16px;
}

.module-card {
  display: grid;
  grid-template-columns: 184px 1fr auto;
  gap: 14px;
  align-items: center;
  padding: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.03);
  cursor: pointer;
}

.module-thumb {
  position: relative;
  height: 106px;
  border-radius: 14px;
  overflow: hidden;
}

.module-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.module-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 8px 0 10px;
}

.module-meta span {
  color: rgba(240, 231, 216, 0.62);
  font-size: 12px;
}

.module-enter {
  width: 46px;
  height: 46px;
  border: 1px solid rgba(245, 187, 88, 0.24);
  border-radius: 50%;
  background: rgba(245, 187, 88, 0.08);
  color: #f6d08a;
  cursor: pointer;
}

.module-enter svg {
  width: 18px;
  height: 18px;
}

.intel-card {
  padding: 20px;
  position: sticky;
  top: 18px;
}

.selected-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 10px;
}

.selected-header img {
  width: 28px;
  height: 28px;
}

.intel-description {
  margin-top: 12px;
}

.intel-divider {
  height: 1px;
  margin: 18px 0;
  background: linear-gradient(90deg, transparent, rgba(245, 187, 88, 0.34), transparent);
}

.recommend-item {
  display: grid;
  grid-template-columns: 72px 1fr;
  gap: 12px;
  align-items: center;
  padding: 10px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.03);
  cursor: pointer;
}

.recommend-item img {
  width: 72px;
  height: 72px;
  border-radius: 12px;
  object-fit: cover;
}

.recommend-text {
  display: grid;
  gap: 4px;
  text-align: left;
}

.recommend-text strong {
  color: #f2ead9;
}

.primary-enter {
  width: 100%;
  margin-top: 16px;
}

@media (max-width: 1280px) {
  .content-grid {
    grid-template-columns: 1fr;
  }

  .intel-card {
    position: static;
  }
}

@media (max-width: 1100px) {
  .top-stage {
    grid-template-columns: 1fr;
  }

  .worldview-cards {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .navbar {
    grid-template-columns: 1fr;
    justify-items: start;
    gap: 16px;
    padding: 18px 18px 12px;
  }

  .nav-menu {
    width: 100%;
    justify-content: space-between;
    gap: 12px;
    overflow-x: auto;
  }

  .nav-user {
    width: 100%;
    justify-content: space-between;
  }

  .worldview-shell {
    padding: 18px 18px 22px;
  }

  .search-panel {
    grid-template-columns: 1fr;
  }

  .module-card {
    grid-template-columns: 1fr;
  }

  .module-thumb {
    height: 150px;
  }
}

@media (max-width: 640px) {
  .hero-copy h1 {
    font-size: 3rem;
  }

  .module-panel-head {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
