<script setup>
import lobbyBackground from '../背景/大厅界面.png'

const props = defineProps({
  worlds: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['back', 'next'])

const selectedWorldId = defineModel('selectedWorldId', { default: 'dnd' })
const selectedModuleId = defineModel('selectedModuleId', { default: 'krenko' })

const chooseWorld = (world) => {
  selectedWorldId.value = world.id
  selectedModuleId.value = world.modules[0]?.id || ''
}

const chooseModule = (module) => {
  selectedModuleId.value = module.id
}

const goNext = () => {
  const world =
    (selectedWorldId.value && (props.worlds.find((item) => item.id === selectedWorldId.value) || props.worlds[0])) ||
    props.worlds[0]
  const module = world.modules.find((item) => item.id === selectedModuleId.value) || world.modules[0]
  emit('next', { world, module })
}
</script>

<template>
  <div class="worldview">
    <img class="bg" :src="lobbyBackground" alt="世界观背景" />
    <div class="overlay"></div>

    <main class="shell">
      <section class="worlds">
        <button v-for="world in props.worlds" :key="world.id" class="world-card" :class="{ active: selectedWorldId === world.id }" @click="chooseWorld(world)">
          <img :src="world.cover" :alt="world.title" />
          <strong>{{ world.title }}</strong>
        </button>
      </section>

      <aside class="modules">
        <h2>模组</h2>
        <button v-for="module in (props.worlds.find((w) => w.id === selectedWorldId)?.modules || [])" :key="module.id" class="module-card" :class="{ active: selectedModuleId === module.id }" @click="chooseModule(module)">
          <img :src="module.cover" :alt="module.name" />
          <div>
            <strong>{{ module.name }}</strong>
            <p>{{ module.group }}</p>
          </div>
        </button>
        <button class="next" @click="goNext">进入基础设定</button>
        <button class="back" @click="emit('back')">返回大厅</button>
      </aside>
    </main>
  </div>
</template>

<style scoped>
.worldview{min-height:100vh;position:relative;overflow:hidden;color:#f5efe2}
.bg,.overlay{position:absolute;inset:0}
.bg{width:100%;height:100%;object-fit:cover}
.overlay{background:linear-gradient(90deg,rgba(3,5,10,.95),rgba(3,5,10,.55))}
.shell{position:relative;z-index:1;padding:24px 28px;display:grid;grid-template-columns:minmax(0,1fr) 360px;gap:18px}
.worlds{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}
.world-card,.module-card{border:1px solid rgba(176,136,65,.18);border-radius:18px;background:rgba(7,11,17,.62);color:#f7e3bc}
.world-card img,.module-card img{width:100%;height:180px;object-fit:cover;border-radius:18px 18px 0 0}
.world-card strong,.module-card strong{display:block;padding:12px 14px 0}
.module-card{display:grid;grid-template-columns:84px 1fr;gap:12px;align-items:center;padding:0 0 0 0}
.module-card img{width:84px;height:84px;border-radius:14px;margin:12px}
.module-card p{padding:4px 14px 12px;color:rgba(237,228,211,.7)}
.active{border-color:rgba(243,180,92,.5)}
.modules{padding:18px;border:1px solid rgba(176,136,65,.18);border-radius:18px;background:rgba(7,11,17,.62);display:grid;gap:10px;align-content:start}
.modules h2{color:#f3d49b}
.next,.back{padding:14px 16px;border:0;border-radius:12px;font-weight:700}
.next{background:linear-gradient(90deg,#f3b45c,#ef9b37);color:#1c140d}
.back{background:rgba(255,255,255,.06);color:#f5efe2}
@media (max-width:1100px){.shell{grid-template-columns:1fr}.worlds{grid-template-columns:1fr}}
</style>
