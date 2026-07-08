<script setup>
import lobbyBackground from '../背景/大厅界面.png'
import productIcon from '../图标/产品图标.png'
import cubeIcon from '../图标/魔方.png'
import gateIcon from '../图标/魔法门.png'
import orbIcon from '../图标/魔法球.png'
import goblinCover from '../游戏种类/哥布林.jpg'

const emit = defineEmits(['create-room', 'continue-adventure'])

const actions = [
  { key: 'create', title: '创建房间', subtitle: '直接进入世界观', icon: cubeIcon, tone: 'gold' },
  { key: 'join', title: '进入房间', subtitle: '输入房间信息', icon: gateIcon, tone: 'cyan' },
  { key: 'continue', title: '继续冒险', subtitle: '追捕克伦可', icon: orbIcon, tone: 'ember' },
  { key: 'quick', title: '快捷进入', subtitle: '快速开局', icon: orbIcon, tone: 'steel' }
]

const handleAction = (action) => {
  if (action.key === 'create') emit('create-room')
  if (action.key === 'continue') emit('continue-adventure')
}
</script>

<template>
  <div class="lobby">
    <img class="bg" :src="lobbyBackground" alt="大厅背景" />
    <div class="overlay"></div>
    <div class="top">
      <img class="logo" :src="productIcon" alt="StoryForge" />
      <div>
        <h1>StoryForge</h1>
        <p>大厅</p>
      </div>
    </div>

    <main class="shell">
      <section class="hero">
        <h2>先创建房间，再选择世界观。</h2>
        <p>顶部导航已删除，所有流程由页面内按钮驱动。</p>
      </section>

      <section class="cards">
        <button v-for="action in actions" :key="action.key" class="card" :class="action.tone" @click="handleAction(action)">
          <img :src="action.icon" alt="" />
          <strong>{{ action.title }}</strong>
          <span>{{ action.subtitle }}</span>
        </button>
      </section>

      <section class="adventure">
        <img :src="goblinCover" alt="追捕克伦可" />
        <div>
          <h3>追捕克伦可团</h3>
          <p>继续冒险会直接进入当前对局。</p>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.lobby{min-height:100vh;position:relative;overflow:hidden;color:#f5efe2}
.bg,.overlay{position:absolute;inset:0}
.bg{width:100%;height:100%;object-fit:cover}
.overlay{background:linear-gradient(90deg,rgba(3,5,10,.96),rgba(3,5,10,.45))}
.top{position:relative;z-index:1;display:flex;align-items:center;gap:10px;padding:18px 28px 10px}
.logo{width:48px;height:48px;object-fit:contain}
.top h1{color:#efc26a;font-size:1.1rem}
.top p{color:rgba(241,198,108,.86)}
.shell{position:relative;z-index:1;padding:8px 28px 24px;display:grid;gap:18px}
.hero h2{font-size:clamp(2.4rem,5vw,4.6rem);color:#f3d49b;line-height:1}
.hero p{margin-top:10px;color:rgba(237,228,211,.78)}
.cards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}
.card{min-height:180px;border:1px solid rgba(176,136,65,.18);border-radius:18px;background:rgba(7,11,17,.56);color:#f7e3bc;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px}
.card img{width:42px;height:42px;object-fit:contain}
.card.gold img{filter:brightness(0) saturate(100%) invert(78%) sepia(57%) saturate(557%) hue-rotate(356deg) brightness(101%) contrast(93%)}
.card.cyan img{filter:brightness(0) saturate(100%) invert(72%) sepia(47%) saturate(1714%) hue-rotate(165deg) brightness(101%) contrast(102%)}
.card.ember img{filter:brightness(0) saturate(100%) invert(81%) sepia(39%) saturate(626%) hue-rotate(353deg) brightness(100%) contrast(92%)}
.card.steel img{filter:brightness(0) saturate(100%) invert(91%) sepia(16%) saturate(274%) hue-rotate(170deg) brightness(89%) contrast(86%)}
.adventure{display:flex;align-items:center;gap:16px;max-width:760px;padding:14px;border:1px solid rgba(90,154,192,.12);border-radius:16px;background:rgba(8,15,20,.5)}
.adventure img{width:88px;height:88px;object-fit:cover;border-radius:12px}
@media (max-width:1100px){.cards{grid-template-columns:1fr 1fr}.adventure{flex-direction:column;align-items:flex-start}}
</style>
