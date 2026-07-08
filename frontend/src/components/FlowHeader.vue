<script setup>
import productIcon from '../../图标/产品图标.png'

defineProps({
  context: { type: String, default: '' },
  level: { type: String, default: 'Lv.12' },
  userName: { type: String, default: '夜行者' }
})
</script>

<template>
  <header class="flow-header">
    <div class="brand">
      <img class="brand-icon" :src="productIcon" alt="StoryForge" />
      <div class="brand-text">
        <span class="brand-en">StoryForge</span>
        <span class="brand-cn">灵境档案</span>
      </div>
    </div>
    <div class="context" v-if="context">{{ context }}</div>
    <div class="user-area">
      <div class="user-chip">
        <div class="user-avatar">夜</div>
        <div class="user-info">
          <span class="user-name">{{ userName }}</span>
          <span class="user-level">{{ level }}</span>
        </div>
      </div>
    </div>
  </header>
</template>

<style scoped>
.flow-header{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:18px;padding:12px 24px;border-bottom:1px solid rgba(221,174,94,.14);background:linear-gradient(180deg,rgba(4,4,6,.88),rgba(4,4,6,.44));backdrop-filter:blur(10px)}
.brand,.user-area{display:flex;align-items:center}
.brand{gap:10px}.brand-icon{width:44px;height:44px;object-fit:contain}
.brand-text{display:flex;flex-direction:column;gap:2px;line-height:1}.brand-en{color:#efc26a}.brand-cn{color:rgba(241,198,108,.86);letter-spacing:.26em;font-size:.88rem}
.context{color:#f0d59d;font-size:.92rem;letter-spacing:.16em;white-space:nowrap}
.user-area{justify-content:flex-end}.user-chip{display:flex;align-items:center;gap:10px;padding:7px 14px 7px 7px;border:1px solid rgba(237,187,93,.2);border-radius:999px;background:linear-gradient(180deg,rgba(54,34,10,.45),rgba(11,11,14,.45))}
.user-avatar{width:40px;height:40px;display:grid;place-items:center;border-radius:50%;background:linear-gradient(180deg,#3f2c12,#17100a);color:#f7cc7d;font-weight:700}
.user-info{display:flex;flex-direction:column;gap:2px}.user-name{color:#f7d389;font-weight:600}.user-level{color:rgba(240,222,185,.76);font-size:.84rem}
@media (max-width:900px){.flow-header{grid-template-columns:1fr;justify-items:start}.context{white-space:normal}.user-area{width:100%;justify-content:flex-start}}
</style>
