<script setup>
import { computed, onMounted, ref } from 'vue'
import { sessionsApi } from './api/client'
import endingBackground from '../背景/结局结算.png'
import goblinCover from '../游戏种类/哥布林.jpg'

const props = defineProps({
  endingPayload: {
    type: Object,
    default: null
  },
  latestSession: {
    type: Object,
    default: null
  },
  currentUser: {
    type: Object,
    default: null
  },
  worldview: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['navigate'])

const report = ref(null)
const statusText = ref('')
const isSaving = ref(false)

const payload = computed(() => props.endingPayload || {})
const room = computed(() => payload.value.room || props.latestSession?.room || null)
const ending = computed(() => payload.value.ending || payload.value.report || {})
const character = computed(() => payload.value.character || props.latestSession?.character || null)
const messages = computed(() => payload.value.messages || [])
const sessionId = computed(() =>
  payload.value.sessionId ||
  room.value?.current_session_id ||
  props.latestSession?.session?.id ||
  null
)

const lastNarration = computed(() => [...messages.value].reverse().find((item) =>
  item.message_type === 'narration' || item.sender_role === 'ai_dm'
)?.content || '')
const actionMessages = computed(() => messages.value.filter((item) => item.message_type === 'action'))

const endingTitle = computed(() =>
  report.value?.title ||
  ending.value.title ||
  room.value?.title ||
  '本局总结'
)
const conclusionTitle = computed(() => {
  const status = ending.value.status || endingTypeLabel.value
  return status.startsWith('结局') ? status : `结局：${status}`
})
const endingType = computed(() => report.value?.ending_type || ending.value.ending_type || 'normal')
const endingTypeLabel = computed(() => {
  const map = {
    good: '围捕成功',
    normal: '勉强生还',
    bad: '任务失败',
    open: '开放结局'
  }
  return map[endingType.value] || '本局结束'
})
const rating = computed(() => ending.value.rating || (endingType.value === 'good' ? 'A' : endingType.value === 'bad' ? 'C' : 'B'))
const statusLabel = computed(() => ending.value.status || endingTypeLabel.value)
const archiveCode = computed(() => {
  const raw = room.value?.room_code || sessionId.value || Date.now()
  return `CASE-${String(raw).toUpperCase()}`
})
const worldLabel = computed(() =>
  props.worldview?.title ||
  props.worldview?.name ||
  props.latestSession?.session?.world_name ||
  'StoryForge'
)
const moduleLabel = computed(() =>
  props.worldview?.selectedModule?.name ||
  props.worldview?.recommendedModule ||
  props.latestSession?.session?.adventure_module_title ||
  room.value?.title ||
  '本局冒险'
)
const teamLabel = computed(() => {
  const names = (payload.value.members || [])
    .map((member) => member.character_name || member.display_name)
    .filter(Boolean)
  return names.length ? names.join('、') : (props.currentUser?.nickname || props.currentUser?.username || '冒险小队')
})
const storySummary = computed(() =>
  report.value?.story_summary ||
  ending.value.summary ||
  lastNarration.value ||
  '本局已经抵达终点，AI DM 已完成终局判定。'
)
const keyNodes = computed(() => {
  const fromEnding = ending.value.key_nodes || ending.value.keyNodes
  if (Array.isArray(fromEnding) && fromEnding.length) return fromEnding.slice(0, 5)
  if (Array.isArray(report.value?.key_choices) && report.value.key_choices.length) {
    return report.value.key_choices.slice(0, 5)
  }
  const actions = actionMessages.value.map((item) => item.content).filter(Boolean).slice(-5)
  return actions.length ? actions : ['接取委托', '追查线索', '关键抉择', '终局判定', statusLabel.value]
})
const rewardItems = computed(() => {
  const rewards = ending.value.rewards || []
  if (Array.isArray(rewards) && rewards.length) {
    return rewards.slice(0, 4).map((item) => ({ title: item, desc: '已记录进本局档案。' }))
  }
  return [
    { title: '关键线索', desc: '已整理本局发现的重要情报。' },
    { title: '行动记录', desc: '保留玩家行动与 AI DM 叙事。' },
    { title: '角色成长', desc: report.value?.character_growth || '本局经历将影响后续冒险。' },
    { title: '后续建议', desc: report.value?.ai_suggestion || '可从档案馆继续查看。' }
  ]
})
const tags = computed(() => {
  const fromEnding = ending.value.tags
  if (Array.isArray(fromEnding) && fromEnding.length) return fromEnding
  const map = {
    good: ['幸存', '主目标达成'],
    normal: ['幸存', '代价未清'],
    bad: ['任务失败', '危机升级'],
    open: ['开放结局', '真相未尽']
  }
  return map[endingType.value] || ['本局结束']
})
const finalStats = computed(() => [
  ['目标状态', statusLabel.value],
  ['队伍状态', tags.value.includes('幸存') ? '仍可行动' : '待确认'],
  ['行动次数', `${actionMessages.value.length} 次`],
  ['关键节点', `${keyNodes.value.length} 项`],
  ['档案评级', rating.value],
  ['后续威胁', endingType.value === 'good' ? '余波未平' : '仍需追查']
])

const generateReport = async ({ silent = false } = {}) => {
  if (!sessionId.value) {
    if (!silent) statusText.value = '暂无可保存的会话档案。'
    return null
  }

  isSaving.value = true
  try {
    const data = await sessionsApi.generateReport(sessionId.value)
    report.value = data
    if (!silent) statusText.value = '档案已保存。'
    return data
  } catch (error) {
    if (!silent) statusText.value = error?.message || '保存档案失败。'
    return null
  } finally {
    isSaving.value = false
  }
}

const returnHome = () => {
  emit('navigate', 'home')
}

onMounted(() => {
  generateReport({ silent: true })
})
</script>

<template>
  <div class="ending-page" :style="{ backgroundImage: `url(${endingBackground})` }">
    <div class="main-wrapper">
      <aside class="left-title-area">
        <h2>本局总结</h2>
        <div class="title-divider"><span>◇</span></div>
        <p>{{ statusLabel }}，<br>但故事的余波仍在回响。</p>
      </aside>

      <main class="content-area">
        <section class="card banner-card">
          <div class="paperclip" aria-hidden="true"></div>
          <div class="banner-img" :style="{ backgroundImage: `linear-gradient(90deg, rgba(0,0,0,.12), rgba(0,0,0,.42)), url(${goblinCover})` }"></div>
          <div class="banner-content">
            <h3>{{ endingTitle }}</h3>
            <h2>{{ conclusionTitle }}</h2>

            <div class="meta-grid">
              <div class="meta-item"><span class="label">世界观：</span><span class="val">{{ worldLabel }}</span></div>
              <div class="meta-item"><span class="label">模组：</span><span class="val">{{ moduleLabel }}</span></div>
              <div class="meta-item"><span class="label">游玩时长：</span><span class="val">已结算</span></div>
              <div class="meta-item"><span class="label">行动队伍：</span><span class="val">{{ teamLabel }}</span></div>
              <div class="meta-item"><span class="label">当前状态：</span><span class="val survive">{{ statusLabel }}</span></div>
              <div class="meta-item"><span class="label">结局评级：</span><span class="val rating">{{ rating }}</span></div>
              <div class="meta-item wide"><span class="label">档案编号：</span><span class="val">{{ archiveCode }}</span></div>
            </div>

            <div class="seal-gold">
              <span>{{ statusLabel }}</span>
            </div>
            <div class="wax-seal"></div>
            <div class="stamp-red">{{ tags[tags.length - 1] || '真相未尽' }}</div>
          </div>
        </section>

        <section class="bottom-row">
          <article class="card event-card">
            <div class="paperclip" aria-hidden="true"></div>
            <div class="section-title">事件回顾</div>
            <p>{{ storySummary }}</p>

            <div class="node-wrap">
              <div class="section-title small">关键节点</div>
              <div class="timeline">
                <div
                  v-for="(node, index) in keyNodes"
                  :key="`${node}_${index}`"
                  class="node active"
                >
                  <div class="node-icon">{{ index + 1 }}</div>
                  <div class="node-text">{{ node }}</div>
                </div>
              </div>
            </div>
          </article>

          <article class="card status-card">
            <div class="section-title">战役最终状态</div>

            <div class="summary-grid">
              <section class="summary-box">
                <h4>结局摘要</h4>
                <div class="summary-list">
                  <div v-for="[label, value] in finalStats" :key="label">{{ label }}：<strong>{{ value }}</strong></div>
                </div>
              </section>

              <section class="summary-box">
                <h4>关键收获</h4>
                <div class="reward-grid">
                  <div v-for="item in rewardItems" :key="item.title" class="reward-item">
                    <strong>{{ item.title }}</strong>
                    <span>{{ item.desc }}</span>
                  </div>
                </div>
              </section>

              <section class="summary-box">
                <h4>结局标签</h4>
                <div class="tags-row">
                  <span
                    v-for="tag in tags"
                    :key="tag"
                    class="tag"
                    :class="tag.includes('失败') || tag.includes('危机') ? 'danger' : tag.includes('未') || tag.includes('代价') ? 'warn' : 'safe'"
                  >
                    {{ tag }}
                  </span>
                </div>
              </section>
            </div>
          </article>
        </section>

        <div class="actions-row">
          <button class="btn" type="button" @click="returnHome">返回大厅</button>
          <button class="btn btn-primary" type="button" :disabled="isSaving" @click="generateReport()">
            {{ isSaving ? '保存中...' : '保存档案' }}
          </button>
        </div>
        <p v-if="statusText" class="status-text">{{ statusText }}</p>
      </main>
    </div>
  </div>
</template>

<style scoped>
.ending-page {
  --bg-deep: #0a0807;
  --card-dark: rgba(20, 16, 13, 0.92);
  --text-gold: #c3a677;
  --text-gold-bright: #e3cca0;
  --text-light: #d6cfc5;
  --text-dim: #908475;
  --text-dark: #2a231d;
  --color-survive: #5c8a5a;
  --color-danger: #a73333;
  --color-warning: #b9893f;
  --border-gold: #5a4b35;
  --border-light: #8a7b66;
  min-height: 100vh;
  background-color: var(--bg-deep);
  background-position: center;
  background-repeat: no-repeat;
  background-size: cover;
  color: var(--text-light);
  font-family: 'Noto Serif SC', 'Source Han Serif SC', 'SimSun', serif;
  overflow: hidden;
}

.main-wrapper {
  display: flex;
  gap: 32px;
  width: 100%;
  max-width: 1560px;
  height: 100vh;
  min-height: 0;
  margin: 0 auto;
  padding: 18px 34px 28px;
}

.left-title-area {
  width: 360px;
  flex-shrink: 0;
  padding-top: 50px;
  border-right: 1px solid rgba(195, 166, 119, 0.16);
}

.left-title-area h2 {
  margin-bottom: 18px;
  color: var(--text-gold-bright);
  font-size: 78px;
  line-height: 1.1;
  letter-spacing: 6px;
  text-shadow: 0 0 15px rgba(195, 166, 119, 0.2);
  white-space: nowrap;
}

.title-divider {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 18px;
}

.title-divider::before,
.title-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(195, 166, 119, 0.56), transparent);
}

.title-divider span {
  color: var(--text-gold);
  font-size: 12px;
}

.left-title-area p {
  color: var(--text-dim);
  font-size: 15px;
  line-height: 1.9;
  letter-spacing: 1px;
}

.content-area {
  min-width: 0;
  min-height: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.card {
  position: relative;
  border-radius: 8px;
  box-shadow: 5px 5px 20px rgba(0, 0, 0, 0.5);
}

.paperclip {
  position: absolute;
  top: -6px;
  left: 26px;
  z-index: 10;
  width: 16px;
  height: 34px;
  border: 3px solid rgba(124, 132, 145, 0.88);
  border-top: 0;
  border-radius: 0 0 10px 10px;
  transform: rotate(-14deg);
  box-shadow: 0 0 8px rgba(110, 130, 168, 0.35);
}

.paperclip::before {
  content: '';
  position: absolute;
  top: -10px;
  left: 2px;
  width: 8px;
  height: 24px;
  border: 2px solid rgba(190, 198, 208, 0.9);
  border-top: 0;
  border-radius: 0 0 8px 8px;
}

.banner-card {
  display: flex;
  flex-shrink: 0;
  height: 290px;
  overflow: hidden;
  border: 1px solid var(--border-gold);
  background: var(--card-dark);
}

.banner-img {
  position: relative;
  width: 360px;
  border-right: 1px solid var(--border-gold);
  background-size: cover;
  background-position: center;
}

.banner-img::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent 0%, rgba(20, 17, 14, 0.78) 100%);
}

.banner-content {
  position: relative;
  flex: 1;
  min-width: 0;
  padding: 26px 32px;
}

.banner-content h3 {
  margin-bottom: 6px;
  color: var(--text-light);
  font-size: 24px;
  font-weight: 400;
}

.banner-content h2 {
  max-width: calc(100% - 168px);
  margin-bottom: 20px;
  color: var(--text-gold-bright);
  font-size: 58px;
  line-height: 1.08;
  letter-spacing: 2px;
  text-shadow: 0 0 10px rgba(195, 166, 119, 0.3);
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  column-gap: 32px;
  row-gap: 10px;
  width: 74%;
  padding-top: 14px;
  border-top: 1px solid rgba(195, 166, 119, 0.12);
  font-size: 15px;
}

.meta-item {
  display: flex;
  align-items: baseline;
  gap: 12px;
  min-width: 0;
}

.meta-item.wide {
  grid-column: 1 / 3;
}

.meta-item .label {
  width: 88px;
  flex: 0 0 auto;
  color: var(--text-dim);
  text-align: right;
}

.meta-item .val {
  min-width: 0;
  overflow: hidden;
  color: var(--text-light);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.meta-item .val.survive {
  color: var(--color-survive);
  font-weight: 700;
}

.meta-item .val.rating {
  color: var(--text-gold-bright);
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 32px;
  line-height: 0.9;
}

.seal-gold {
  position: absolute;
  right: 38px;
  top: 16px;
  z-index: 2;
  width: 142px;
  height: 142px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px dashed #ffe6b3;
  border-radius: 50%;
  background: radial-gradient(circle, #d4b886 0%, #8a6c3c 70%, #4a381c 100%);
  box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.8), 5px 5px 15px rgba(0, 0, 0, 0.6);
  transform: rotate(14deg);
}

.seal-gold::before {
  content: '';
  position: absolute;
  width: 112px;
  height: 112px;
  border: 1px solid rgba(255, 230, 179, 0.5);
  border-radius: 50%;
}

.seal-gold span {
  z-index: 3;
  max-width: 96px;
  color: #30200e;
  font-size: 24px;
  font-weight: 900;
  letter-spacing: 2px;
  line-height: 1.1;
  text-align: center;
}

.stamp-red {
  position: absolute;
  right: 26px;
  bottom: 20px;
  z-index: 1;
  max-width: 230px;
  border: 3px solid var(--color-danger);
  border-radius: 4px;
  background: rgba(167, 51, 51, 0.05);
  color: var(--color-danger);
  padding: 5px 14px;
  font-size: 21px;
  font-weight: 900;
  letter-spacing: 3px;
  transform: rotate(-9deg);
}

.wax-seal {
  position: absolute;
  right: -18px;
  top: 96px;
  z-index: 4;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: radial-gradient(circle, #b73229 0%, #70110a 100%);
  box-shadow: inset 0 0 5px #000, 2px 2px 5px rgba(0, 0, 0, 0.5);
}

.wax-seal::after {
  content: '';
  position: absolute;
  top: 34px;
  left: 5px;
  z-index: -1;
  width: 40px;
  height: 58px;
  background: #8b2621;
  transform: rotate(-20deg);
}

.bottom-row {
  min-height: 0;
  flex: 1;
  display: flex;
  gap: 18px;
}

.event-card {
  flex: 1.2;
  overflow: hidden;
  border: 1px solid #a39581;
  background:
    linear-gradient(135deg, rgba(214, 200, 179, 0.96), rgba(191, 174, 148, 0.98));
  color: var(--text-dark);
  padding: 26px 28px;
  box-shadow: inset 0 0 50px rgba(100, 80, 60, 0.2), 5px 5px 15px rgba(0, 0, 0, 0.4);
}

.section-title {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
  margin-bottom: 16px;
  color: #4a3e32;
  font-size: 20px;
  font-weight: 700;
  text-align: center;
}

.section-title.small {
  margin-bottom: 0;
  font-size: 16px;
}

.section-title::before,
.section-title::after {
  content: '';
  width: 40px;
  height: 1px;
  background: #8a7b66;
}

.event-card p {
  margin-bottom: 18px;
  color: #3a3025;
  font-size: 15px;
  line-height: 1.9;
  text-indent: 2em;
}

.node-wrap {
  padding-top: 14px;
  border-top: 1px solid rgba(74, 62, 50, 0.18);
}

.timeline {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 6px;
  margin-top: 16px;
  padding: 0 8px;
}

.timeline::before {
  content: '';
  position: absolute;
  top: 22px;
  left: 34px;
  right: 34px;
  z-index: 1;
  height: 2px;
  background: #a39581;
}

.node {
  position: relative;
  z-index: 2;
  width: 74px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  text-align: center;
}

.node-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #6b5c49;
  border-radius: 50%;
  background: #d6c8b3;
  box-shadow: 0 0 0 3px rgba(214, 200, 179, 0.84);
  color: #4a3e32;
  font-size: 14px;
  font-weight: 700;
}

.node.active .node-icon {
  background: #4a3e32;
  color: #d6c8b3;
}

.node-text {
  color: #4a3e32;
  font-size: 11px;
  font-weight: 700;
  line-height: 1.45;
}

.status-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  overflow-x: hidden;
  border: 1px solid var(--border-gold);
  background: var(--card-dark);
  padding: 24px 24px 18px;
}

.status-card .section-title {
  margin-bottom: 20px;
  color: var(--text-gold);
}

.status-card .section-title::before,
.status-card .section-title::after {
  background: var(--border-gold);
}

.summary-grid {
  display: grid;
  gap: 14px;
}

.summary-box {
  border: 1px solid rgba(90, 75, 53, 0.56);
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.22);
  padding: 14px 14px 12px;
}

.summary-box h4 {
  margin-bottom: 12px;
  color: var(--text-gold-bright);
  font-size: 17px;
  font-weight: 600;
}

.summary-list {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px 18px;
  color: var(--text-dim);
  font-size: 14px;
}

.summary-list strong {
  margin-left: 6px;
  color: var(--text-light);
  font-weight: 400;
}

.reward-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.reward-item {
  border: 1px solid rgba(90, 75, 53, 0.48);
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.24);
  padding: 10px 12px;
}

.reward-item strong {
  display: block;
  margin-bottom: 4px;
  color: var(--text-gold-bright);
  font-size: 14px;
}

.reward-item span {
  color: var(--text-dim);
  font-size: 12px;
  line-height: 1.6;
}

.tags-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.tag {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  border: 1px solid;
  border-radius: 12px;
  padding: 4px 12px;
  font-size: 12px;
}

.tag.safe {
  border-color: var(--color-survive);
  background: rgba(92, 138, 90, 0.1);
  color: var(--color-survive);
}

.tag.warn {
  border-color: var(--color-warning);
  background: rgba(185, 137, 63, 0.1);
  color: var(--color-warning);
}

.tag.danger {
  border-color: var(--color-danger);
  background: rgba(167, 51, 51, 0.1);
  color: var(--color-danger);
}

.actions-row {
  display: flex;
  justify-content: center;
  gap: 38px;
  flex-shrink: 0;
  margin-top: 8px;
  padding-bottom: 6px;
}

.btn {
  width: 290px;
  height: 72px;
  border: 1px solid var(--border-gold);
  border-radius: 4px;
  background: rgba(10, 8, 7, 0.5);
  color: var(--text-light);
  font-size: 18px;
  cursor: pointer;
  transition: background 0.3s ease, color 0.3s ease, box-shadow 0.3s ease;
}

.btn:hover {
  background: rgba(195, 166, 119, 0.1);
  color: var(--text-gold-bright);
}

.btn:disabled {
  cursor: wait;
  opacity: 0.62;
}

.btn-primary {
  border-color: var(--text-gold);
  color: var(--text-gold-bright);
  box-shadow: 0 0 15px rgba(195, 166, 119, 0.2), inset 0 0 10px rgba(195, 166, 119, 0.1);
}

.status-text {
  margin-top: -8px;
  color: var(--text-gold-bright);
  font-size: 13px;
  text-align: center;
}

@media (max-width: 1440px) {
  .left-title-area {
    width: 300px;
  }

  .left-title-area h2 {
    font-size: 64px;
  }

  .banner-content h2 {
    font-size: 46px;
  }

  .meta-grid {
    width: 78%;
  }
}

@media (max-width: 980px) {
  .ending-page {
    overflow: auto;
  }

  .main-wrapper {
    height: auto;
    min-height: 100vh;
    flex-direction: column;
    padding: 22px;
  }

  .left-title-area {
    width: auto;
    padding-top: 0;
    border-right: 0;
  }

  .left-title-area h2 {
    font-size: 44px;
  }

  .banner-card,
  .bottom-row {
    flex-direction: column;
  }

  .banner-card {
    height: auto;
  }

  .banner-img {
    width: 100%;
    min-height: 220px;
  }

  .banner-content h2 {
    max-width: none;
  }

  .seal-gold,
  .wax-seal,
  .stamp-red {
    display: none;
  }

  .meta-grid,
  .summary-list,
  .reward-grid {
    width: 100%;
    grid-template-columns: 1fr;
  }

  .meta-item.wide {
    grid-column: auto;
  }

  .actions-row {
    flex-direction: column;
    gap: 12px;
  }

  .btn {
    width: 100%;
  }
}
</style>
