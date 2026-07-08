<script setup>
import FlowHeader from './components/FlowHeader.vue'

defineProps({
  context: { type: String, default: '' },
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  steps: { type: Array, default: () => [] },
  activeStep: { type: Number, default: 1 }
})
</script>

<template>
  <div class="character-flow">
    <FlowHeader :context="context" />
    <main class="flow-body">
      <aside class="left-panel">
        <div class="title-block">
          <p class="eyebrow">CHARACTER FLOW</p>
          <h1>{{ title }}</h1>
          <p>{{ subtitle }}</p>
        </div>
        <div class="step-list">
          <div v-for="step in steps" :key="step.id" class="step-item" :class="{ active: step.id === activeStep, done: step.id < activeStep }">
            <span class="step-num">{{ String(step.id).padStart(2, '0') }}</span>
            <div class="step-copy">
              <strong>{{ step.name }}</strong>
              <span>{{ step.desc }}</span>
            </div>
          </div>
        </div>
        <div class="left-slot"><slot name="left" /></div>
      </aside>

      <section class="center-panel"><slot /></section>

      <aside class="right-panel"><slot name="right" /></aside>
    </main>
  </div>
</template>

<style scoped>
.character-flow{min-height:100vh;background:linear-gradient(180deg,#050607 0%,#08080a 38%,#0f0b08 100%);color:#f5efe2}
.flow-body{display:grid;grid-template-columns:290px minmax(0,1fr) 360px;gap:18px;padding:18px 22px 22px}
.left-panel,.center-panel,.right-panel{min-width:0}
.left-panel{display:flex;flex-direction:column;gap:18px}
.title-block{padding:10px 6px 0}.eyebrow{color:#5fcfff;font-size:11px;letter-spacing:.45em;margin-bottom:10px}
.title-block h1{color:#f3f0e8;font-size:40px;line-height:1.02;letter-spacing:.08em}.title-block p{margin-top:10px;color:rgba(237,228,211,.68);line-height:1.7;font-size:13px}
.step-list{display:grid;gap:10px}.step-item{display:flex;align-items:center;gap:12px;padding:14px 16px;border-radius:12px;border:1px solid rgba(255,255,255,.06);background:rgba(255,255,255,.03)}.step-item.active{border-color:rgba(243,180,92,.45);background:linear-gradient(90deg,rgba(243,180,92,.12),rgba(255,255,255,.02))}.step-item.done{border-color:rgba(243,180,92,.22)}
.step-num{width:36px;height:36px;display:grid;place-items:center;border-radius:50%;border:1px solid rgba(243,180,92,.28);color:#f3b45c;font-weight:700}.step-copy{display:flex;flex-direction:column;gap:4px}.step-copy strong{font-size:15px;color:#f5efe2}.step-copy span{font-size:11px;color:rgba(237,228,211,.56)}
.left-slot{margin-top:auto}
.center-panel{min-height:calc(100vh - 110px)}
.right-panel{position:sticky;top:18px;height:fit-content}
.flow-rail{display:grid;gap:10px}
.flow-btn{padding:14px 16px;border:0;border-radius:12px;background:linear-gradient(90deg,#f3b45c,#ef9b37);color:#1c140d;font-weight:700}
.flow-btn.ghost{background:rgba(255,255,255,.06);color:#f5efe2}
.flow-card,.right-stack,.room-panel,.summary-panel{border:1px solid rgba(176,136,65,.18);border-radius:18px;background:rgba(7,11,17,.62);padding:18px}
.flow-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.flow-col{display:grid;gap:10px}.flow-col h3{color:#f3d49b}.field{display:grid;gap:6px}.field span{font-size:12px;color:rgba(237,228,211,.72)}.field input{padding:12px 12px;border:1px solid rgba(255,255,255,.08);border-radius:10px;background:rgba(255,255,255,.03);color:#f5efe2}
.attr-line{display:flex;justify-content:space-between;padding:10px 12px;border:1px solid rgba(255,255,255,.06);border-radius:10px;background:rgba(255,255,255,.02)}
.right-stack{display:grid;gap:12px}.mini-card{padding:14px;border-radius:12px;background:rgba(255,255,255,.03)}.mini-card p{font-size:12px;color:rgba(237,228,211,.65)}.mini-card strong{color:#f3d49b}
.room-panel img,.summary-panel img{width:100%;height:280px;object-fit:cover;border-radius:14px}.room-copy{margin-top:14px;display:grid;gap:10px}.room-copy h2{color:#f3d49b;font-size:2rem}
@media (max-width:1280px){.flow-body{grid-template-columns:260px minmax(0,1fr)}.right-panel{grid-column:2;position:static}}
@media (max-width:900px){.flow-body{grid-template-columns:1fr;padding:16px 16px 20px}.center-panel,.right-panel{grid-column:1;min-height:auto}.flow-grid{grid-template-columns:1fr}}
</style>
