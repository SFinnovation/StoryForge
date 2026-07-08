<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { charactersApi, sessionsApi, worldsApi } from './api/client'
import systemBackground from '../背景/系统主界面.png'

const emit = defineEmits(['navigate', 'session-created'])

const props = defineProps({
  currentPage: {
    type: String,
    default: '角色'
  },
  worldview: {
    type: Object,
    default: null
  },
  currentUser: {
    type: Object,
    default: null
  }
})

const activeNav = ref(props.currentPage)
const createStatus = ref('')
const isSubmitting = ref(false)
const worldviewTitle = computed(() => props.worldview?.title || props.worldview?.name || '')

const handleNavigate = (page) => {
  activeNav.value = page
  emit('navigate', page)
}

const currentStep = ref(1)

const steps = [
  { id: 1, name: '身份档案', completed: false },
  { id: 2, name: '特征分配', completed: false },
  { id: 3, name: '职业技能', completed: false },
  { id: 4, name: '背景确认', completed: false }
]

const investigator = reactive({
  name: '',
  gender: '',
  age: '',
  era: '1920s',
  birthplace: '',
  occupation: '',
  description: ''
})

const availableValues = ref([40, 50, 50, 50, 60, 60, 70, 80])
const usedValues = ref([])

const cocAttributes = [
  { name: '力量', abbr: 'STR', value: null, description: '肌肉力量和体力' },
  { name: '体质', abbr: 'CON', value: null, description: '健康状况和耐力' },
  { name: '意志', abbr: 'POW', value: null, description: '意志力和魔法抗性' },
  { name: '敏捷', abbr: 'DEX', value: null, description: '手眼协调和速度' },
  { name: '外貌', abbr: 'APP', value: null, description: '个人魅力和吸引力' },
  { name: '体型', abbr: 'SIZ', value: null, description: '身材大小和体重' },
  { name: '智力', abbr: 'INT', value: null, description: '推理和学习能力' },
  { name: '教育', abbr: 'EDU', value: null, description: '知识和教育程度' }
]

const dndAttributes = [
  { name: '力量', abbr: 'STR', value: null, description: '肌肉力量和近战能力' },
  { name: '体质', abbr: 'CON', value: null, description: '生命值和耐力' },
  { name: '敏捷', abbr: 'DEX', value: null, description: '速度和闪避' },
  { name: '智力', abbr: 'INT', value: null, description: '知识和法术' },
  { name: '感知', abbr: 'WIS', value: null, description: '洞察力和意志' },
  { name: '魅力', abbr: 'CHA', value: null, description: '社交和领导力' }
]

const attributes = reactive([])

const isCocSystem = computed(() => {
  if (!props.worldview) return true
  return worldviewTitle.value.includes('COC')
})

const pageTitle = computed(() => {
  if (!props.worldview) return '调查员创建室'
  if (worldviewTitle.value.includes('COC')) return '调查员创建室'
  if (worldviewTitle.value.includes('DND')) return '冒险者创建室'
  return '角色创建室'
})

const pageSubtitle = computed(() => {
  if (!props.worldview) return '按照 COC 7th 快速开始规则，建立你的调查员档案'
  if (worldviewTitle.value.includes('COC')) return '按照 COC 7th 快速开始规则，建立你的调查员档案'
  if (worldviewTitle.value.includes('DND')) return '按照 DND 5e 规则，创建你的冒险者角色'
  return '创建你的角色档案'
})

const initAttributes = () => {
  attributes.length = 0
  usedValues.value = []
  if (isCocSystem.value) {
    availableValues.value = [40, 50, 50, 50, 60, 60, 70, 80]
    cocAttributes.forEach(attr => {
      attributes.push({ ...attr, value: null })
    })
  } else {
    availableValues.value = [8, 10, 12, 13, 14, 15]
    dndAttributes.forEach(attr => {
      attributes.push({ ...attr, value: null })
    })
  }
}

watch(() => props.worldview, () => {
  initAttributes()
}, { immediate: true })

const assignValue = (attrIndex, value) => {
  const attr = attributes[attrIndex]
  if (attr.value === value) return
  
  if (attr.value !== null) {
    const idx = usedValues.value.indexOf(attr.value)
    if (idx > -1) usedValues.value.splice(idx, 1)
  }
  
  attr.value = value
  usedValues.value.push(value)
}

const canAssign = (value) => {
  const count = usedValues.value.filter(v => v === value).length
  const availableCount = availableValues.value.filter(v => v === value).length
  return count < availableCount
}

const subAttributes = computed(() => {
  if (isCocSystem.value) {
    const con = attributes.find(a => a.abbr === 'CON')?.value || 50
    const siz = attributes.find(a => a.abbr === 'SIZ')?.value || 50
    const pow = attributes.find(a => a.abbr === 'POW')?.value || 50
    const edu = attributes.find(a => a.abbr === 'EDU')?.value || 50
    
    const hp = Math.floor((con + siz) / 10)
    const mp = Math.floor(pow / 5)
    const san = pow
    const db = siz >= 80 ? '+1d6' : siz >= 60 ? '+1d4' : siz <= 40 ? '-1d4' : '+0'
    const build = siz >= 80 ? 2 : siz >= 60 ? 1 : siz <= 40 ? -1 : 0
    
    return {
      hp,
      mp,
      san,
      luck: 0,
      db,
      build,
      system: 'coc'
    }
  } else {
    const con = attributes.find(a => a.abbr === 'CON')?.value || 10
    const dex = attributes.find(a => a.abbr === 'DEX')?.value || 10
    const wis = attributes.find(a => a.abbr === 'WIS')?.value || 10
    
    const conMod = Math.floor((con - 10) / 2)
    const dexMod = Math.floor((dex - 10) / 2)
    const wisMod = Math.floor((wis - 10) / 2)
    
    const hp = 8 + conMod
    const ac = 10 + dexMod
    const initiative = dexMod
    const speed = 30
    
    return {
      hp,
      ac,
      initiative,
      speed,
      conMod: conMod > 0 ? '+' + conMod : conMod,
      dexMod: dexMod > 0 ? '+' + dexMod : dexMod,
      wisMod: wisMod > 0 ? '+' + wisMod : wisMod,
      system: 'dnd'
    }
  }
})

const luckValue = ref(0)
const isRolling = ref(false)

const rollLuck = () => {
  isRolling.value = true
  let total = 0
  for (let i = 0; i < 3; i++) {
    total += Math.floor(Math.random() * 6) + 1
  }
  luckValue.value = total * 5
  setTimeout(() => {
    isRolling.value = false
  }, 500)
}



const occupations = [
  '文物研究者', '作家', '业余爱好者', '医生', '记者',
  '警方侦探', '私家侦探', '教授', '士兵', '自定义职业'
]

const selectedOccupation = ref('')

const classIdMap = {
  战士: 'fighter',
  法师: 'wizard',
  牧师: 'cleric',
  盗贼: 'rogue',
  游侠: 'ranger',
  吟游诗人: 'bard',
  圣骑士: 'paladin',
  德鲁伊: 'druid',
  武僧: 'monk',
  术士: 'warlock'
}

const getAttributeValue = (abbr, fallback) => attributes.find((attr) => attr.abbr === abbr)?.value || fallback

const dndAttributesPayload = () => ({
  strength: getAttributeValue('STR', 8),
  dexterity: getAttributeValue('DEX', 15),
  constitution: getAttributeValue('CON', 12),
  intelligence: getAttributeValue('INT', 14),
  wisdom: getAttributeValue('WIS', 13),
  charisma: getAttributeValue('CHA', 10)
})

const cocAttributesPayload = () => ({
  strength: Math.round(getAttributeValue('STR', 50) / 5),
  dexterity: Math.round(getAttributeValue('DEX', 50) / 5),
  constitution: Math.round(getAttributeValue('CON', 50) / 5),
  intelligence: Math.round(getAttributeValue('INT', 50) / 5),
  wisdom: Math.round(getAttributeValue('POW', 50) / 5),
  charisma: Math.round(getAttributeValue('APP', 50) / 5)
})

const validateRequiredFields = () => {
  if (!investigator.name.trim()) {
    createStatus.value = '请先填写角色姓名。'
    return false
  }

  if (attributes.some((attr) => attr.value === null)) {
    createStatus.value = '请先完成全部属性分配。'
    return false
  }

  return true
}

const resolveWorldId = async () => {
  if (props.worldview?.backendId) return props.worldview.backendId
  if (props.worldview?.source === 'backend' && props.worldview?.id) return props.worldview.id

  const worlds = await worldsApi.list()
  const dndWorld = worlds.find((world) => /krenko|克伦可|dnd|dragon|龙/i.test(world.name))
  return dndWorld?.id || worlds[0]?.id || 1
}

const createCharacterPayload = () => {
  if (isCocSystem.value) {
    return {
      name: investigator.name,
      profession: selectedOccupation.value || investigator.occupation || 'investigator',
      race_id: 'human',
      background_id: null,
      motivation: investigator.description || '追寻未知真相',
      hp: Math.max(1, subAttributes.value.hp),
      max_hp: Math.max(1, subAttributes.value.hp),
      attributes: cocAttributesPayload()
    }
  }

  return {
    name: investigator.name,
    race_id: 'high-elf',
    class_id: classIdMap[selectedOccupation.value] || 'rogue',
    background_id: 'acolyte',
    motivation: investigator.description || '踏上新的冒险',
    ability_assignment: 'standard_array',
    base_attributes: dndAttributesPayload(),
    selected_skills: []
  }
}

const handleCreateCharacter = async () => {
  createStatus.value = ''
  if (!validateRequiredFields() || isSubmitting.value) return

  isSubmitting.value = true
  try {
    const character = await charactersApi.create(createCharacterPayload())
    const worldId = await resolveWorldId()
    const sessionData = await sessionsApi.start({
      world_id: worldId,
      character_id: character.id
    })

    createStatus.value = '角色已创建，冒险会话已开启。'
    emit('session-created', {
      ...sessionData,
      character
    })
  } catch (error) {
    createStatus.value = error?.message || '角色创建失败，请检查属性与职业选择。'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="role-page">
    <div class="page-bg" :style="{ backgroundImage: `url(${systemBackground})` }">
      <div class="bg-overlay"></div>
      <div class="texture"></div>
      <div class="candles"></div>
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
      <header class="page-header">
        <div class="header-bg">
          <div class="header-overlay"></div>
        </div>
        <div class="header-content">
          <div class="title-wrap">
            <span class="decor-line"></span>
            <h1 class="page-title">{{ pageTitle }}</h1>
            <span class="decor-line"></span>
          </div>
          <p class="page-subtitle">{{ pageSubtitle }}</p>
        </div>
      </header>

      <div class="content-wrapper">
        <div class="progress-bar">
          <div
            v-for="step in steps"
            :key="step.id"
            class="progress-item"
            :class="{
              active: currentStep === step.id,
              completed: step.id < currentStep
            }"
          >
            <div class="step-number">{{ String(step.id).padStart(2, '0') }}</div>
            <span class="step-name">{{ step.name }}</span>
            <div v-if="step.id < currentStep" class="check-mark">✓</div>
          </div>
        </div>

        <div class="game-layout">
          <div class="character-display">
            <div class="character-visual">
              <div class="character-frame">
                <svg viewBox="0 0 200 200" class="character-silhouette">
                  <rect x="30" y="50" width="140" height="140" fill="rgba(10, 12, 18, 0.8)" stroke="#f5b95b" stroke-width="2" rx="8"/>
                  <circle cx="100" cy="80" r="35" fill="rgba(10, 12, 18, 0.9)" stroke="#f5b95b" stroke-width="1.5"/>
                  <path d="M75 75 Q100 95 125 75" stroke="#f5b95b" stroke-width="1.5" fill="none"/>
                  <path d="M80 105 Q100 125 120 105" stroke="#f5b95b" stroke-width="1.5" fill="none"/>
                  <rect x="50" y="120" width="100" height="60" fill="rgba(10, 12, 18, 0.9)" stroke="#f5b95b" stroke-width="1"/>
                </svg>
                <div class="character-glow"></div>
              </div>
              <div class="character-name-plate">
                <div class="name-title">
                  <span class="name-prefix">{{ isCocSystem ? '调查员' : '冒险者' }}</span>
                  <span class="name-text">{{ investigator.name || '未命名' }}</span>
                </div>
                <div class="name-info">
                  <span>{{ investigator.occupation || '未选择职业' }}</span>
                  <span class="dot">·</span>
                  <span>{{ investigator.age || '--' }}岁</span>
                </div>
              </div>
            </div>

            <div class="identity-panel">
              <h3 class="panel-title">身份档案</h3>
              <div class="form-group">
                <label class="form-label">姓名</label>
                <input
                  v-model="investigator.name"
                  type="text"
                  class="form-input"
                  placeholder="输入角色姓名"
                />
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label class="form-label">性别</label>
                  <select v-model="investigator.gender" class="form-select">
                    <option value="">请选择</option>
                    <option value="male">男</option>
                    <option value="female">女</option>
                    <option value="other">其他</option>
                  </select>
                </div>
                <div class="form-group">
                  <label class="form-label">年龄</label>
                  <input
                    v-model="investigator.age"
                    type="number"
                    class="form-input"
                    placeholder="年龄"
                  />
                </div>
              </div>
              <div class="form-group">
                <label class="form-label">{{ isCocSystem ? '所属年代' : '背景设定' }}</label>
                <div class="radio-group">
                  <template v-if="isCocSystem">
                    <label class="radio-item">
                      <input type="radio" v-model="investigator.era" value="1920s" />
                      <span>1920s</span>
                    </label>
                    <label class="radio-item">
                      <input type="radio" v-model="investigator.era" value="modern" />
                      <span>现代</span>
                    </label>
                    <label class="radio-item">
                      <input type="radio" v-model="investigator.era" value="custom" />
                      <span>自定义</span>
                    </label>
                  </template>
                  <template v-else>
                    <label class="radio-item">
                      <input type="radio" v-model="investigator.era" value="faerun" />
                      <span>费伦大陆</span>
                    </label>
                    <label class="radio-item">
                      <input type="radio" v-model="investigator.era" value="ebberon" />
                      <span>艾伯伦</span>
                    </label>
                    <label class="radio-item">
                      <input type="radio" v-model="investigator.era" value="homebrew" />
                      <span>自定义世界</span>
                    </label>
                  </template>
                </div>
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label class="form-label">出生地</label>
                  <input
                    v-model="investigator.birthplace"
                    type="text"
                    class="form-input"
                    placeholder="出生地"
                  />
                </div>
                <div class="form-group">
                  <label class="form-label">职业</label>
                  <select v-model="investigator.occupation" class="form-select">
                    <option value="">请选择职业</option>
                    <option v-for="occ in occupations" :key="occ" :value="occ">{{ occ }}</option>
                  </select>
                </div>
              </div>
              <div class="form-group">
                <label class="form-label">简短简介</label>
                <textarea
                  v-model="investigator.description"
                  class="form-textarea"
                  rows="3"
                  placeholder="简述你的角色背景故事..."
                ></textarea>
              </div>
            </div>
          </div>

          <div class="stats-panel">
            <div class="stats-header">
              <h3 class="panel-title">{{ isCocSystem ? '八大特征' : '六项属性' }}</h3>
              <span class="stats-hint">{{ isCocSystem ? '分配数值: 40、50、50、50、60、60、70、80' : '分配数值: 8、10、12、13、14、15' }}</span>
            </div>
            <div class="attributes-list">
              <div
                v-for="(attr, index) in attributes"
                :key="attr.abbr"
                class="attribute-row"
              >
                <div class="attr-left">
                  <span class="attr-abbr">{{ attr.abbr }}</span>
                  <span class="attr-name">{{ attr.name }}</span>
                </div>
                <div class="attr-right">
                  <select
                    :value="attr.value"
                    @change="assignValue(index, parseInt($event.target.value))"
                    class="attr-select"
                  >
                    <option :value="null" disabled>选择</option>
                    <option
                      v-for="val in availableValues"
                      :key="val"
                      :value="val"
                      :disabled="!canAssign(val) && attr.value !== val"
                    >
                      {{ val }}
                    </option>
                  </select>
                  <span class="attr-value-display" :class="{ assigned: attr.value }">
                    {{ attr.value || '--' }}
                  </span>
                </div>
              </div>
            </div>

            <div class="sub-stats">
              <h3 class="panel-title">副属性</h3>
              <div class="sub-stats-grid">
                <template v-if="isCocSystem">
                  <div class="sub-stat-item">
                    <span class="sub-stat-label">HP</span>
                    <span class="sub-stat-value">{{ subAttributes.hp }}</span>
                  </div>
                  <div class="sub-stat-item">
                    <span class="sub-stat-label">MP</span>
                    <span class="sub-stat-value">{{ subAttributes.mp }}</span>
                  </div>
                  <div class="sub-stat-item">
                    <span class="sub-stat-label">SAN</span>
                    <span class="sub-stat-value">{{ subAttributes.san }}</span>
                  </div>
                  <div class="sub-stat-item luck">
                    <span class="sub-stat-label">LUCK</span>
                    <div class="luck-area">
                      <span class="sub-stat-value" :class="{ rolling: isRolling }">{{ luckValue || '--' }}</span>
                      <button class="luck-btn" @click="rollLuck">🎲</button>
                    </div>
                  </div>
                  <div class="sub-stat-item">
                    <span class="sub-stat-label">DB</span>
                    <span class="sub-stat-value">{{ subAttributes.db }}</span>
                  </div>
                  <div class="sub-stat-item">
                    <span class="sub-stat-label">BUILD</span>
                    <span class="sub-stat-value">{{ subAttributes.build > 0 ? '+' : '' }}{{ subAttributes.build }}</span>
                  </div>
                </template>
                <template v-else>
                  <div class="sub-stat-item">
                    <span class="sub-stat-label">HP</span>
                    <span class="sub-stat-value">{{ subAttributes.hp }}</span>
                  </div>
                  <div class="sub-stat-item">
                    <span class="sub-stat-label">AC</span>
                    <span class="sub-stat-value">{{ subAttributes.ac }}</span>
                  </div>
                  <div class="sub-stat-item">
                    <span class="sub-stat-label">速度</span>
                    <span class="sub-stat-value">{{ subAttributes.speed }}ft</span>
                  </div>
                  <div class="sub-stat-item">
                    <span class="sub-stat-label">CON</span>
                    <span class="sub-stat-value">{{ subAttributes.conMod }}</span>
                  </div>
                  <div class="sub-stat-item">
                    <span class="sub-stat-label">DEX</span>
                    <span class="sub-stat-value">{{ subAttributes.dexMod }}</span>
                  </div>
                  <div class="sub-stat-item">
                    <span class="sub-stat-label">WIS</span>
                    <span class="sub-stat-value">{{ subAttributes.wisMod }}</span>
                  </div>
                </template>
              </div>
            </div>

            <div class="value-pool-section">
              <span class="pool-label">可分配数值</span>
              <div class="value-pool-items">
                <span
                  v-for="(val, idx) in availableValues"
                  :key="idx"
                  class="pool-item"
                  :class="{ used: usedValues.includes(val) }"
                >
                  {{ val }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="bottom-panel">
          <div class="panel-card wide-card">
            <h3 class="panel-title">{{ isCocSystem ? '职业与技能' : '职业与专长' }}</h3>
            <div class="occupation-grid">
              <template v-if="isCocSystem">
                <button
                  v-for="occ in occupations"
                  :key="occ"
                  class="occ-btn"
                  :class="{ active: selectedOccupation === occ }"
                  @click="selectedOccupation = occ"
                >
                  {{ occ }}
                </button>
              </template>
              <template v-else>
                <button
                  v-for="occ in ['战士', '法师', '牧师', '盗贼', '游侠', '吟游诗人', '圣骑士', '德鲁伊', '武僧', '术士']"
                  :key="occ"
                  class="occ-btn"
                  :class="{ active: selectedOccupation === occ }"
                  @click="selectedOccupation = occ"
                >
                  {{ occ }}
                </button>
              </template>
            </div>
            <div class="skills-info">
              <template v-if="isCocSystem">
                <div class="skill-info-item">
                  <span class="skill-label">职业技能分配：</span>
                  <span class="skill-value">1 个 70%，2 个 60%，3 个 50%，3 个 40%</span>
                </div>
                <div class="skill-info-item">
                  <span class="skill-label">兴趣技能：</span>
                  <span class="skill-value">选择 4 个非职业技能，每项在基础值上 +20%</span>
                </div>
                <div class="skill-info-item locked">
                  <span class="skill-label">🔒 克苏鲁神话：</span>
                  <span class="skill-value">创建时不可加点</span>
                </div>
              </template>
              <template v-else>
                <div class="skill-info-item">
                  <span class="skill-label">技能点数：</span>
                  <span class="skill-value">等级1获得 [(智力-10)/2 + 2] × 职业技能倍数 点技能</span>
                </div>
                <div class="skill-info-item">
                  <span class="skill-label">专长：</span>
                  <span class="skill-value">等级1获得 1 个专长，等级3、5、7...每2级获得 1 个专长</span>
                </div>
                <div class="skill-info-item locked">
                  <span class="skill-label">🔒 法术：</span>
                  <span class="skill-value">施法职业在等级选择后自动获得法术位</span>
                </div>
              </template>
            </div>
          </div>

          <div class="action-buttons">
            <button class="btn-secondary" @click="handleNavigate('世界观')">
              返回世界观
            </button>
            <button class="btn-secondary" @click="console.log('保存草稿')">
              保存草稿
            </button>
            <button class="btn-primary" :disabled="isSubmitting" @click="handleCreateCharacter">
              <span class="btn-icon">🎲</span>
              {{ isSubmitting ? '正在创建...' : (isCocSystem ? '完成调查员创建' : '完成冒险者创建') }}
            </button>
          </div>
          <p v-if="createStatus" class="create-status">{{ createStatus }}</p>
        </div>
      </div>
    </main>
  </div>
</template>


<style scoped>
.role-page {
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
  background-size: cover;
  background-position: center;
  z-index: 0;
  opacity: 0.15;
}

.bg-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(180deg, rgba(9, 8, 6, 0.95) 0%, rgba(12, 10, 8, 0.98) 50%, rgba(9, 8, 6, 0.95) 100%);
}

.texture {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  opacity: 0.03;
  background-image: url("data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
}

.candles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  background: 
    radial-gradient(ellipse at 10% 20%, rgba(245, 185, 91, 0.05) 0%, transparent 50%),
    radial-gradient(ellipse at 90% 30%, rgba(245, 185, 91, 0.03) 0%, transparent 40%),
    radial-gradient(ellipse at 50% 80%, rgba(111, 232, 255, 0.02) 0%, transparent 30%);
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

.page-header {
  position: relative;
  height: 180px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 32px;
}

.header-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #090806 0%, #1a1510 50%, #090806 100%);
}

.header-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: 
    radial-gradient(ellipse at center, rgba(245, 185, 91, 0.08) 0%, transparent 70%),
    radial-gradient(ellipse at 10% 50%, rgba(111, 232, 255, 0.03) 0%, transparent 50%);
}

.header-content {
  position: relative;
  z-index: 2;
  text-align: center;
}

.title-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 32px;
  margin-bottom: 12px;
}

.decor-line {
  width: 120px;
  height: 2px;
  background: linear-gradient(90deg, transparent, #f5b95b, transparent);
}

.page-title {
  font-size: 42px;
  font-weight: 900;
  color: #eac77a;
  letter-spacing: 16px;
  font-family: 'KaiTi', 'STKaiti', 'SimSun', serif;
  text-shadow: 0 0 40px rgba(234, 199, 122, 0.3);
}

.page-subtitle {
  font-size: 15px;
  color: #b99a58;
  font-weight: 400;
}

.content-wrapper {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px;
}

.progress-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 40px;
  margin-bottom: 32px;
  padding: 20px;
  background: rgba(12, 10, 8, 0.9);
  border: 1px solid rgba(245, 185, 91, 0.2);
  border-radius: 12px;
}

.progress-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  position: relative;
}

.step-number {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(245, 185, 91, 0.1);
  border: 2px solid rgba(245, 185, 91, 0.3);
  border-radius: 50%;
  font-size: 16px;
  font-weight: 800;
  color: #6b7280;
  transition: all 0.3s ease;
}

.progress-item.active .step-number {
  background: rgba(245, 185, 91, 0.3);
  border-color: #f5b95b;
  color: #f5b95b;
  box-shadow: 0 0 20px rgba(245, 185, 91, 0.4);
}

.progress-item.completed .step-number {
  background: rgba(245, 185, 91, 0.2);
  border-color: #f5b95b;
  color: #f5b95b;
}

.step-name {
  font-size: 13px;
  color: #6b7280;
  font-weight: 500;
}

.progress-item.active .step-name {
  color: #f5b95b;
}

.progress-item.completed .step-name {
  color: #9ca3af;
}

.check-mark {
  position: absolute;
  top: -4px;
  right: -4px;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5b95b;
  border-radius: 50%;
  font-size: 12px;
  color: #090806;
  font-weight: 800;
}

.game-layout {
  display: flex;
  gap: 24px;
  margin-bottom: 32px;
}

.character-display {
  flex: 0.4;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.character-visual {
  position: relative;
}

.character-frame {
  position: relative;
  width: 100%;
  aspect-ratio: 3/4;
  background: rgba(10, 12, 18, 0.9);
  border: 2px solid rgba(245, 185, 91, 0.3);
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.character-silhouette {
  width: 70%;
  height: 70%;
  opacity: 0.8;
}

.character-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(ellipse at 50% 30%, rgba(245, 185, 91, 0.1) 0%, transparent 60%);
  pointer-events: none;
}

.character-name-plate {
  position: absolute;
  bottom: 16px;
  left: 16px;
  right: 16px;
  background: rgba(9, 8, 6, 0.95);
  border: 1px solid rgba(245, 185, 91, 0.3);
  border-radius: 12px;
  padding: 12px 16px;
  backdrop-filter: blur(8px);
}

.name-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.name-prefix {
  font-size: 11px;
  color: #f5b95b;
  padding: 2px 8px;
  background: rgba(245, 185, 91, 0.15);
  border-radius: 4px;
  font-weight: 600;
}

.name-text {
  font-size: 20px;
  font-weight: 800;
  color: #ffffff;
  text-shadow: 0 0 10px rgba(245, 185, 91, 0.5);
}

.name-info {
  font-size: 13px;
  color: #9ca3af;
  display: flex;
  align-items: center;
  gap: 8px;
}

.name-info .dot {
  color: #f5b95b;
}

.identity-panel {
  background: rgba(12, 10, 8, 0.95);
  border: 1px solid rgba(245, 185, 91, 0.25);
  border-radius: 16px;
  padding: 20px;
}

.stats-panel {
  flex: 0.6;
  background: rgba(12, 10, 8, 0.95);
  border: 1px solid rgba(245, 185, 91, 0.25);
  border-radius: 16px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.stats-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(245, 185, 91, 0.2);
}

.stats-header .panel-title {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.stats-hint {
  font-size: 12px;
  color: #6b7280;
}

.attributes-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.attribute-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: rgba(5, 4, 3, 0.6);
  border-radius: 10px;
  border: 1px solid rgba(245, 185, 91, 0.15);
  transition: all 0.3s ease;
}

.attribute-row:hover {
  border-color: rgba(245, 185, 91, 0.3);
  background: rgba(5, 4, 3, 0.8);
}

.attr-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.attr-left .attr-abbr {
  font-size: 14px;
  font-weight: 800;
  color: #f5b95b;
  width: 36px;
  text-align: center;
}

.attr-left .attr-name {
  font-size: 14px;
  color: #e5e7eb;
  font-weight: 500;
}

.attr-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.attr-select {
  padding: 6px 10px;
  background: rgba(5, 4, 3, 0.8);
  border: 1px solid rgba(245, 185, 91, 0.3);
  border-radius: 6px;
  color: #ffffff;
  font-size: 13px;
  cursor: pointer;
  outline: none;
  min-width: 60px;
}

.attr-select:focus {
  border-color: #f5b95b;
}

.attr-value-display {
  font-size: 16px;
  font-weight: 800;
  color: #6b7280;
  min-width: 40px;
  text-align: right;
}

.attr-value-display.assigned {
  color: #f5b95b;
  text-shadow: 0 0 10px rgba(245, 185, 91, 0.5);
}

.sub-stats {
  padding-top: 12px;
  border-top: 1px solid rgba(245, 185, 91, 0.2);
}

.sub-stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.sub-stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px;
  background: rgba(5, 4, 3, 0.6);
  border-radius: 10px;
  border: 1px solid rgba(245, 185, 91, 0.15);
}

.sub-stat-label {
  font-size: 11px;
  color: #6b7280;
  margin-bottom: 4px;
}

.sub-stat-value {
  font-size: 18px;
  font-weight: 800;
  color: #f5b95b;
}

.sub-stat-item.luck .luck-area {
  display: flex;
  align-items: center;
  gap: 8px;
}

.luck-btn {
  width: 28px;
  height: 28px;
  font-size: 14px;
  background: rgba(245, 185, 91, 0.2);
  border: 1px solid rgba(245, 185, 91, 0.4);
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s ease;
}

.luck-btn:hover {
  background: rgba(245, 185, 91, 0.4);
  transform: scale(1.1);
}

.value-pool-section {
  padding-top: 12px;
  border-top: 1px solid rgba(245, 185, 91, 0.2);
}

.value-pool-section .pool-label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 10px;
  display: block;
}

.value-pool-items {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.pool-item {
  padding: 6px 14px;
  background: rgba(245, 185, 91, 0.15);
  border: 1px solid rgba(245, 185, 91, 0.3);
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  color: #f5b95b;
  transition: all 0.3s ease;
}

.pool-item.used {
  opacity: 0.3;
  color: #6b7280;
  border-color: rgba(245, 185, 91, 0.1);
}

.panel-card {
  background: rgba(12, 10, 8, 0.95);
  border: 1px solid rgba(245, 185, 91, 0.25);
  border-radius: 16px;
  padding: 24px;
  position: relative;
}

.card-corner {
  position: absolute;
  width: 16px;
  height: 16px;
  border-color: #f5b95b;
  border-style: solid;
  border-width: 0;
  opacity: 0.5;
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

.panel-title {
  font-size: 18px;
  font-weight: 800;
  color: #f5b95b;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(245, 185, 91, 0.2);
  text-shadow: 0 0 20px rgba(245, 185, 91, 0.3);
}

.form-group {
  margin-bottom: 16px;
}

.form-label {
  display: block;
  font-size: 13px;
  color: #9ca3af;
  margin-bottom: 8px;
  font-weight: 500;
}

.form-input {
  width: 100%;
  padding: 10px 14px;
  background: rgba(5, 4, 3, 0.8);
  border: 1px solid rgba(245, 185, 91, 0.3);
  border-radius: 8px;
  color: #ffffff;
  font-size: 14px;
  outline: none;
  transition: all 0.3s ease;
}

.form-input:focus {
  border-color: #f5b95b;
  box-shadow: 0 0 15px rgba(245, 185, 91, 0.2);
}

.form-input::placeholder {
  color: #4b5563;
}

.form-select {
  width: 100%;
  padding: 10px 14px;
  background: rgba(5, 4, 3, 0.8);
  border: 1px solid rgba(245, 185, 91, 0.3);
  border-radius: 8px;
  color: #ffffff;
  font-size: 14px;
  outline: none;
  cursor: pointer;
  transition: all 0.3s ease;
}

.form-select:focus {
  border-color: #f5b95b;
  box-shadow: 0 0 15px rgba(245, 185, 91, 0.2);
}

.form-textarea {
  width: 100%;
  padding: 10px 14px;
  background: rgba(5, 4, 3, 0.8);
  border: 1px solid rgba(245, 185, 91, 0.3);
  border-radius: 8px;
  color: #ffffff;
  font-size: 14px;
  outline: none;
  resize: vertical;
  transition: all 0.3s ease;
}

.form-textarea:focus {
  border-color: #f5b95b;
  box-shadow: 0 0 15px rgba(245, 185, 91, 0.2);
}

.form-textarea::placeholder {
  color: #4b5563;
}

.form-row {
  display: flex;
  gap: 16px;
}

.form-row .form-group {
  flex: 1;
}

.radio-group {
  display: flex;
  gap: 12px;
}

.radio-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: rgba(5, 4, 3, 0.8);
  border: 1px solid rgba(245, 185, 91, 0.3);
  border-radius: 8px;
  cursor: pointer;
  color: #9ca3af;
  font-size: 13px;
  transition: all 0.3s ease;
}

.radio-item:hover {
  border-color: rgba(245, 185, 91, 0.5);
}

.radio-item input {
  display: none;
}

.radio-item input:checked + span {
  color: #f5b95b;
}

.radio-item input:checked {
  border-color: #f5b95b;
}

.feature-hint {
  font-size: 13px;
  color: #b99a58;
  margin-bottom: 20px;
  text-align: center;
}

.attributes-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.attr-card {
  background: rgba(5, 4, 3, 0.8);
  border: 1px solid rgba(245, 185, 91, 0.25);
  border-radius: 12px;
  padding: 16px;
  transition: all 0.3s ease;
}

.attr-card:hover {
  border-color: rgba(245, 185, 91, 0.5);
}

.attr-card.filled {
  border-color: rgba(245, 185, 91, 0.4);
  background: rgba(20, 18, 15, 0.9);
}

.attr-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.attr-name {
  font-size: 15px;
  font-weight: 700;
  color: #f5b95b;
}

.attr-abbr {
  font-size: 14px;
  font-weight: 800;
  color: #9ca3af;
  font-family: monospace;
}

.attr-value-wrap {
  text-align: center;
  margin-bottom: 12px;
}

.attr-empty {
  font-size: 24px;
  color: #4b5563;
}

.attr-value {
  font-size: 36px;
  font-weight: 900;
  color: #eac77a;
  text-shadow: 0 0 20px rgba(234, 199, 122, 0.4);
}

.attr-success {
  display: flex;
  justify-content: space-around;
  margin-bottom: 10px;
}

.success-item {
  font-size: 12px;
  color: #9ca3af;
}

.success-item strong {
  color: #6fe8ff;
}

.attr-desc {
  font-size: 12px;
  color: #6b7280;
  text-align: center;
  margin-bottom: 12px;
}

.attr-select {
  text-align: center;
}

.attr-dropdown {
  padding: 6px 12px;
  background: rgba(9, 8, 6, 0.9);
  border: 1px solid rgba(245, 185, 91, 0.4);
  border-radius: 6px;
  color: #f5b95b;
  font-size: 14px;
  cursor: pointer;
}

.attr-dropdown option[disabled]:not([value=""]) {
  color: #4b5563;
}

.value-pool {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid rgba(245, 185, 91, 0.15);
}

.pool-label {
  font-size: 13px;
  color: #9ca3af;
}

.pool-values {
  display: flex;
  gap: 8px;
}

.pool-value {
  padding: 6px 12px;
  background: rgba(245, 185, 91, 0.2);
  border: 1px solid rgba(245, 185, 91, 0.4);
  border-radius: 6px;
  font-size: 14px;
  font-weight: 700;
  color: #f5b95b;
}

.pool-value.used {
  background: rgba(245, 185, 91, 0.05);
  border-color: rgba(245, 185, 91, 0.15);
  color: #4b5563;
}

.radar-card {
  padding: 24px;
}

.radar-chart {
  position: relative;
  width: 100%;
  padding-bottom: 100%;
}

.radar-svg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.radar-labels {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.radar-label {
  position: absolute;
  font-size: 12px;
  font-weight: 700;
  color: #9ca3af;
  font-family: monospace;
}

.preview-card {
  text-align: center;
}

.avatar-placeholder {
  width: 120px;
  height: 120px;
  margin: 0 auto 20px;
  border-radius: 8px;
  border: 2px solid rgba(245, 185, 91, 0.3);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(5, 4, 3, 0.8);
}

.avatar-placeholder svg {
  width: 50px;
  height: 50px;
  color: #f5b95b;
  opacity: 0.6;
}

.avatar-text {
  font-size: 11px;
  color: #6b7280;
  margin-top: 8px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.info-item {
  text-align: left;
}

.info-label {
  display: block;
  font-size: 11px;
  color: #6b7280;
  margin-bottom: 4px;
}

.info-value {
  font-size: 13px;
  color: #e5e7eb;
  font-weight: 500;
}

.stats-card {
  padding: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.stat-item {
  text-align: center;
  padding: 12px;
  background: rgba(5, 4, 3, 0.6);
  border-radius: 8px;
  border: 1px solid rgba(245, 185, 91, 0.15);
}

.stat-label {
  display: block;
  font-size: 11px;
  color: #6b7280;
  margin-bottom: 6px;
  font-family: monospace;
}

.stat-value {
  font-size: 20px;
  font-weight: 800;
  color: #f5b95b;
}

.stat-value.rolling {
  animation: pulse 0.3s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.luck-item {
  grid-column: span 3;
}

.luck-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.roll-btn {
  padding: 6px 12px;
  background: rgba(245, 185, 91, 0.2);
  border: 1px solid rgba(245, 185, 91, 0.5);
  border-radius: 6px;
  color: #f5b95b;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.roll-btn:hover {
  background: rgba(245, 185, 91, 0.3);
  transform: translateY(-1px);
}

.bottom-panel {
  margin-top: 32px;
}

.wide-card {
  margin-bottom: 24px;
}

.occupation-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 20px;
}

.occ-btn {
  padding: 8px 20px;
  background: rgba(5, 4, 3, 0.8);
  border: 1px solid rgba(245, 185, 91, 0.25);
  border-radius: 8px;
  color: #9ca3af;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.occ-btn:hover {
  border-color: rgba(245, 185, 91, 0.5);
  color: #f5b95b;
}

.occ-btn.active {
  background: rgba(245, 185, 91, 0.15);
  border-color: #f5b95b;
  color: #f5b95b;
}

.skills-info {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
  background: rgba(5, 4, 3, 0.6);
  border-radius: 8px;
}

.skill-info-item {
  display: flex;
  gap: 8px;
}

.skill-label {
  font-size: 13px;
  color: #6b7280;
  font-weight: 500;
}

.skill-value {
  font-size: 13px;
  color: #e5e7eb;
}

.skill-info-item.locked {
  opacity: 0.6;
}

.action-buttons {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.btn-secondary {
  padding: 12px 28px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(245, 185, 91, 0.3);
  border-radius: 10px;
  color: #9ca3af;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
  border-color: rgba(245, 185, 91, 0.5);
}

.btn-primary {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 40px;
  background: linear-gradient(135deg, rgba(245, 185, 91, 0.4) 0%, rgba(212, 154, 63, 0.3) 100%);
  border: 2px solid #f5b95b;
  border-radius: 12px;
  color: #f5b95b;
  font-size: 15px;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 0 30px rgba(245, 185, 91, 0.3);
}

.btn-primary:hover {
  background: linear-gradient(135deg, rgba(245, 185, 91, 0.5) 0%, rgba(212, 154, 63, 0.4) 100%);
  transform: translateY(-2px);
  box-shadow: 0 0 50px rgba(245, 185, 91, 0.5);
}

.btn-primary:disabled {
  cursor: wait;
  opacity: 0.72;
  transform: none;
}

.btn-icon {
  font-size: 18px;
}

.create-status {
  margin-top: 14px;
  color: #f5b95b;
  text-align: right;
  font-size: 13px;
}

@media (max-width: 1200px) {
  .main-layout {
    flex-direction: column;
  }
  
  .left-panel, .center-panel, .right-panel {
    flex: 1;
  }
  
  .center-panel {
    order: 1;
  }
  
  .left-panel {
    order: 2;
  }
  
  .right-panel {
    order: 3;
  }
}

@media (max-width: 768px) {
  .navbar {
    padding: 0 16px;
  }
  
  .page-title {
    font-size: 28px;
    letter-spacing: 10px;
  }
  
  .progress-bar {
    flex-wrap: wrap;
    gap: 16px;
  }
  
  .attributes-grid {
    grid-template-columns: 1fr;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .luck-item {
    grid-column: span 2;
  }
  
  .action-buttons {
    flex-direction: column;
    gap: 12px;
  }
  
  .btn-primary {
    width: 100%;
    justify-content: center;
  }
}
</style>
