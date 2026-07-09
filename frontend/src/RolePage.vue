<script setup>
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { charactersApi, roomsApi, sessionsApi, worldsApi } from './api/client'
import systemBackground from '../背景/系统主界面.png'
import productIcon from '../图标/产品图标.png'

const emit = defineEmits(['navigate', 'session-created', 'logout', 'back-button-hidden'])

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

const createStatus = ref('')
const isSubmitting = ref(false)
const currentStep = ref(1)
const selectedOccupation = ref('')
const selectedSkills = ref([])
const luckValue = ref(0)
const isRolling = ref(false)
const isEditingName = ref(false)
const nameInputRef = ref(null)

const worldviewTitle = computed(() => props.worldview?.title || props.worldview?.name || '')
const roomSettings = computed(() => props.worldview?.roomSettings || {})
const moduleTitle = computed(() => props.worldview?.selectedModule?.name || props.worldview?.recommendedModule || '追捕克伦可 Krenko\'s Way')
const isCocSystem = computed(() => worldviewTitle.value.includes('COC'))

const steps = [
  { id: 1, name: '基础设定', en: 'BASIC SETUP' },
  { id: 2, name: '分配属性', en: 'ABILITY SCORES' },
  { id: 3, name: '选择技能', en: 'SKILLS' }
]

const investigator = reactive({
  name: '',
  gender: '',
  age: '',
  era: 'faerun',
  birthplace: '',
  occupation: '',
  description: '',
  raceId: 'high-elf',
  backgroundId: 'acolyte'
})

const ancestryOptions = computed(() => {
  if (isCocSystem.value) {
    return [
      { id: 'human', name: '普通人类', en: 'Human', detail: '现实世界调查员', icon: 'user' },
      { id: 'scholar', name: '学者出身', en: 'Scholar', detail: '知识与调查优势', icon: 'book' },
      { id: 'wanderer', name: '旅行者', en: 'Wanderer', detail: '见多识广', icon: 'footprints' }
    ]
  }

  return [
    { id: 'human', name: '人类', en: 'Human', detail: '均衡可靠', icon: 'user' },
    { id: 'high-elf', name: '高等精灵', en: 'High Elf', detail: '+2 敏捷，奥术感知', icon: 'leaf', skillIds: ['prc'] },
    { id: 'hill-dwarf', name: '矮人', en: 'Dwarf', detail: '坚韧与体魄', icon: 'hammer' },
    { id: 'lightfoot-halfling', name: '半身人', en: 'Halfling', detail: '幸运与敏捷', icon: 'footprints' }
  ]
})

const classOptions = computed(() => {
  if (isCocSystem.value) {
    return [
      { id: 'investigator', name: '文物研究者', en: 'Antiquarian', detail: '历史、图书馆、鉴定' },
      { id: 'detective', name: '私家侦探', en: 'Detective', detail: '侦查、话术、追踪' },
      { id: 'doctor', name: '医生', en: 'Doctor', detail: '医学、急救、心理学' },
      { id: 'journalist', name: '记者', en: 'Journalist', detail: '采访、摄影、社交' }
    ]
  }

  return [
    { id: 'fighter', name: '战士', en: 'Fighter', detail: '武器、防具、战术', icon: 'shield', skillChoose: 2, skillFrom: ['acr', 'ani', 'ath', 'his', 'ins', 'itm', 'prc', 'sur'] },
    { id: 'rogue', name: '游荡者', en: 'Rogue', detail: '潜行、技巧、突袭', icon: 'rogue', skillChoose: 4, skillFrom: ['acr', 'ath', 'dec', 'ins', 'itm', 'inv', 'prc', 'prf', 'per', 'slt', 'ste'] },
    { id: 'wizard', name: '法师', en: 'Wizard', detail: '奥术、学识、法术', icon: 'wizard', skillChoose: 2, skillFrom: ['arc', 'his', 'ins', 'inv', 'med', 'rel'] },
    { id: 'cleric', name: '牧师', en: 'Cleric', detail: '神术、治疗、信仰', icon: 'cleric', skillChoose: 2, skillFrom: ['his', 'ins', 'med', 'per', 'rel'] }
  ]
})

const backgroundOptions = computed(() => {
  if (isCocSystem.value) {
    return [
      { id: 'professor', name: '教授', en: 'Professor', detail: '学术圈关系' },
      { id: 'police', name: '警方顾问', en: 'Police Aid', detail: '执法与询问' },
      { id: 'occultist', name: '神秘学者', en: 'Occultist', detail: '隐秘知识' }
    ]
  }

  return [
    { id: 'acolyte', name: '侍僧', en: 'Acolyte', detail: '洞悉、宗教', icon: 'prayer', skillIds: ['ins', 'rel'] },
    { id: 'criminal', name: '犯罪者', en: 'Criminal', detail: '欺瞒、隐匿', icon: 'coins', skillIds: ['dec', 'ste'] },
    { id: 'folk-hero', name: '民间英雄', en: 'Folk Hero', detail: '驯兽、生存', icon: 'mask', skillIds: ['ani', 'sur'] },
    { id: 'sage', name: '学者', en: 'Sage', detail: '奥秘、历史', icon: 'book', skillIds: ['arc', 'his'] }
  ]
})

const choiceIcons = {
  user: [
    'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z',
    'M4 21a8 8 0 0 1 16 0'
  ],
  leaf: [
    'M5 19c8-1 13-7 14-15C11 4 5 7 5 15c0 2 0 3 0 4Z',
    'M5 19c3-5 7-8 13-11'
  ],
  hammer: [
    'M14 4l6 6-2 2-6-6 2-2Z',
    'M5 21l7-7',
    'M9 9l6 6'
  ],
  footprints: [
    'M8 7c1.8 0 3 1.2 3 3 0 2.2-1.7 4-3.2 4S5 12.3 5 10c0-1.8 1.2-3 3-3Z',
    'M16 10c1.8 0 3 1.2 3 3 0 2.2-1.7 4-3.2 4S13 15.3 13 13c0-1.8 1.2-3 3-3Z'
  ],
  shield: [
    'M12 3l7 3v5c0 5-3 8-7 10-4-2-7-5-7-10V6l7-3Z'
  ],
  rogue: [
    'M12 3l3 5 5 1-4 4 1 6-5-3-5 3 1-6-4-4 5-1 3-5Z',
    'M12 8v8'
  ],
  wizard: [
    'M6 20h12l-3-13-3-4-3 4-3 13Z',
    'M8 15h8'
  ],
  cleric: [
    'M7 4h10v16H7z',
    'M12 7v7',
    'M9 10h6'
  ],
  prayer: [
    'M9 21l3-8',
    'M15 21l-3-8',
    'M8 4l4 9 4-9'
  ],
  coins: [
    'M12 4c3 0 5 1 5 2s-2 2-5 2-5-1-5-2 2-2 5-2Z',
    'M7 6v8c0 1 2 2 5 2s5-1 5-2V6',
    'M9 11c1 .7 5 .7 6 0'
  ],
  mask: [
    'M4 9c5-3 11-3 16 0l-2 7c-1 3-4 4-6 1-2 3-5 2-6-1L4 9Z',
    'M8 12h2',
    'M14 12h2'
  ],
  book: [
    'M5 5h6a3 3 0 0 1 3 3v11a3 3 0 0 0-3-3H5V5Z',
    'M19 5h-5a3 3 0 0 0-3 3v11a3 3 0 0 1 3-3h5V5Z'
  ]
}

const getChoiceIcon = (icon) => choiceIcons[icon] || choiceIcons.user

const cocAttributes = [
  { name: '力量', abbr: 'STR', value: null, description: '肌肉力量和体力' },
  { name: '体质', abbr: 'CON', value: null, description: '健康状况和耐力' },
  { name: '意志', abbr: 'POW', value: null, description: '意志力和精神抗性' },
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
const availableValues = ref([])
const usedValues = ref([])

const skillGroups = computed(() => {
  if (isCocSystem.value) {
    return [
      {
        title: '调查',
        en: 'INVESTIGATION',
        skills: [
          { id: 'library_use', name: '图书馆使用', source: '职业' },
          { id: 'spot_hidden', name: '侦查' },
          { id: 'listen', name: '聆听' },
          { id: 'psychology', name: '心理学' }
        ]
      },
      {
        title: '社交',
        en: 'SOCIAL',
        skills: [
          { id: 'persuade', name: '说服' },
          { id: 'charm', name: '魅惑' },
          { id: 'intimidate', name: '恐吓' },
          { id: 'fast_talk', name: '话术' }
        ]
      },
      {
        title: '行动',
        en: 'ACTION',
        skills: [
          { id: 'stealth', name: '潜行' },
          { id: 'dodge', name: '闪避' },
          { id: 'first_aid', name: '急救' },
          { id: 'firearms', name: '射击' }
        ]
      }
    ]
  }

  return [
    {
      title: '体魄',
      en: 'BODY',
      skills: [
        { id: 'ath', name: '运动' },
        { id: 'acr', name: '杂技' },
        { id: 'slt', name: '巧手' },
        { id: 'ste', name: '隐匿' }
      ]
    },
    {
      title: '学识',
      en: 'LORE',
      skills: [
        { id: 'arc', name: '奥秘' },
        { id: 'his', name: '历史' },
        { id: 'inv', name: '调查' },
        { id: 'rel', name: '宗教' }
      ]
    },
    {
      title: '感知',
      en: 'SENSE',
      skills: [
        { id: 'ins', name: '洞悉' },
        { id: 'med', name: '医药' },
        { id: 'prc', name: '察觉' },
        { id: 'sur', name: '生存' }
      ]
    },
    {
      title: '魅力',
      en: 'CHARM',
      skills: [
        { id: 'dec', name: '欺瞒' },
        { id: 'itm', name: '威吓' },
        { id: 'prf', name: '表演' },
        { id: 'per', name: '说服' }
      ]
    }
  ]
})

const skillLimit = computed(() => (isCocSystem.value ? 4 : selectedClass.value?.skillChoose || 2))

const allSkillOptions = computed(() => skillGroups.value.flatMap((group) => group.skills))
const selectedSkillNames = computed(() => {
  const names = selectedSkills.value
    .map((id) => allSkillOptions.value.find((skill) => skill.id === id)?.name)
    .filter(Boolean)
  return names.length ? names.join('、') : '尚未选择'
})

const selectedRace = computed(() => ancestryOptions.value.find((item) => item.id === investigator.raceId) || ancestryOptions.value[0])
const selectedClass = computed(() => classOptions.value.find((item) => item.name === selectedOccupation.value || item.id === selectedOccupation.value) || classOptions.value[0])
const selectedBackground = computed(() => backgroundOptions.value.find((item) => item.id === investigator.backgroundId) || backgroundOptions.value[0])
const allowedClassSkillIds = computed(() => new Set(selectedClass.value?.skillFrom || []))
const grantedSkillIds = computed(() => new Set([
  ...(selectedRace.value?.skillIds || []),
  ...(selectedBackground.value?.skillIds || [])
]))

const DRAFT_VERSION = 1
const isRestoringDraft = ref(false)
const draftKey = computed(() => {
  const userKey = props.currentUser?.id || props.currentUser?.username || props.currentUser?.email || 'guest'
  const moduleKey = props.worldview?.selectedModule?.id || props.worldview?.selectedModule?.name || moduleTitle.value || worldviewTitle.value || 'default'
  return `storyforge:role-draft:${userKey}:${moduleKey}`
})

const draftStorage = () => {
  if (typeof window === 'undefined') return null
  return window.sessionStorage
}

const validStep = (value) => steps.some((step) => step.id === Number(value)) ? Number(value) : 1

const draftSnapshot = () => ({
  version: DRAFT_VERSION,
  system: isCocSystem.value ? 'coc' : 'dnd',
  currentStep: currentStep.value,
  investigator: { ...investigator },
  selectedOccupation: selectedOccupation.value,
  selectedSkills: [...selectedSkills.value],
  luckValue: luckValue.value,
  attributes: attributes.map((attr) => ({ abbr: attr.abbr, value: attr.value })),
  savedAt: new Date().toISOString()
})

const saveDraft = (showStatus = true) => {
  const storage = draftStorage()
  if (!storage) return

  try {
    storage.setItem(draftKey.value, JSON.stringify(draftSnapshot()))
    if (showStatus) createStatus.value = '草稿已保存。'
  } catch {
    if (showStatus) createStatus.value = '草稿保存失败，请检查浏览器存储权限。'
  }
}

const restoreDraft = () => {
  const storage = draftStorage()
  if (!storage) return false

  try {
    const rawDraft = storage.getItem(draftKey.value)
    if (!rawDraft) return false
    const draft = JSON.parse(rawDraft)
    if (draft?.version !== DRAFT_VERSION) return false
    if (draft.system && draft.system !== (isCocSystem.value ? 'coc' : 'dnd')) return false

    const savedInvestigator = draft.investigator || {}
    Object.keys(investigator).forEach((key) => {
      if (savedInvestigator[key] !== undefined) investigator[key] = savedInvestigator[key]
    })

    selectedOccupation.value = draft.selectedOccupation || selectedOccupation.value
    selectedSkills.value = Array.isArray(draft.selectedSkills) ? [...draft.selectedSkills] : []
    luckValue.value = Number(draft.luckValue) || 0

    const savedAttributes = new Map((draft.attributes || []).map((attr) => [attr.abbr, attr.value]))
    attributes.forEach((attr) => {
      if (!savedAttributes.has(attr.abbr)) return
      const value = savedAttributes.get(attr.abbr)
      attr.value = value === null || value === undefined || value === '' ? null : Number(value)
    })
    usedValues.value = attributes
      .map((attr) => attr.value)
      .filter((value) => value !== null && !Number.isNaN(value))

    currentStep.value = validStep(draft.currentStep)
    return true
  } catch {
    return false
  }
}

const clearDraft = () => {
  const storage = draftStorage()
  if (!storage) return
  storage.removeItem(draftKey.value)
}

const initAttributes = () => {
  isRestoringDraft.value = true
  attributes.length = 0
  usedValues.value = []
  selectedSkills.value = []
  if (isCocSystem.value) {
    availableValues.value = [40, 50, 50, 50, 60, 60, 70, 80]
    cocAttributes.forEach((attr) => attributes.push({ ...attr, value: null }))
    investigator.raceId = 'human'
    investigator.era = '1920s'
    investigator.backgroundId = 'professor'
    selectedOccupation.value = classOptions.value[0]?.id || 'investigator'
  } else {
    availableValues.value = [8, 10, 12, 13, 14, 15]
    dndAttributes.forEach((attr) => attributes.push({ ...attr, value: null }))
    investigator.raceId = 'high-elf'
    investigator.era = 'faerun'
    investigator.backgroundId = 'criminal'
    selectedOccupation.value = 'rogue'
  }

  if (!restoreDraft()) currentStep.value = 1
  createStatus.value = ''
  isRestoringDraft.value = false
}

watch(() => props.worldview, () => {
  initAttributes()
}, { immediate: true })

watch(selectedOccupation, (value, previousValue) => {
  investigator.occupation = value
  if (!isRestoringDraft.value && value !== previousValue) selectedSkills.value = []
})

watch(
  [currentStep, selectedOccupation, selectedSkills, luckValue, investigator, attributes],
  () => {
    if (!isRestoringDraft.value) saveDraft(false)
  },
  { deep: true }
)

const getAttributeValue = (abbr, fallback) => attributes.find((attr) => attr.abbr === abbr)?.value || fallback

const assignValue = (attrIndex, value) => {
  const attr = attributes[attrIndex]
  if (!attr || attr.value === value) return

  if (attr.value !== null) {
    const idx = usedValues.value.indexOf(attr.value)
    if (idx > -1) usedValues.value.splice(idx, 1)
  }

  attr.value = value
  usedValues.value.push(value)
}

const canAssign = (value) => {
  const count = usedValues.value.filter((item) => item === value).length
  const availableCount = availableValues.value.filter((item) => item === value).length
  return count < availableCount
}

const subAttributes = computed(() => {
  if (isCocSystem.value) {
    const con = getAttributeValue('CON', 50)
    const siz = getAttributeValue('SIZ', 50)
    const pow = getAttributeValue('POW', 50)
    const hp = Math.floor((con + siz) / 10)
    const mp = Math.floor(pow / 5)
    const san = pow
    const db = siz >= 80 ? '+1d6' : siz >= 60 ? '+1d4' : siz <= 40 ? '-1d4' : '+0'
    const build = siz >= 80 ? 2 : siz >= 60 ? 1 : siz <= 40 ? -1 : 0
    return { hp, mp, san, luck: luckValue.value || '--', db, build, system: 'coc' }
  }

  const con = getAttributeValue('CON', 10)
  const dex = getAttributeValue('DEX', 10)
  const wis = getAttributeValue('WIS', 10)
  const conMod = Math.floor((con - 10) / 2)
  const dexMod = Math.floor((dex - 10) / 2)
  const wisMod = Math.floor((wis - 10) / 2)
  return {
    hp: 8 + conMod,
    ac: 10 + dexMod,
    initiative: dexMod,
    speed: 30,
    conMod: conMod > 0 ? `+${conMod}` : conMod,
    dexMod: dexMod > 0 ? `+${dexMod}` : dexMod,
    wisMod: wisMod > 0 ? `+${wisMod}` : wisMod,
    system: 'dnd'
  }
})

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

const rollLuck = () => {
  isRolling.value = true
  let total = 0
  for (let i = 0; i < 3; i += 1) {
    total += Math.floor(Math.random() * 6) + 1
  }
  luckValue.value = total * 5
  window.setTimeout(() => {
    isRolling.value = false
  }, 500)
}

const stepOneReady = computed(() => Boolean(selectedRace.value && selectedClass.value && selectedBackground.value))
const stepTwoReady = computed(() => attributes.length > 0 && attributes.every((attr) => attr.value !== null))

const completedForStep = (stepId) => {
  if (stepId === 1) return stepOneReady.value && currentStep.value > 1
  if (stepId === 2) return stepTwoReady.value && currentStep.value > 2
  return false
}

const selectStep = (stepId) => {
  if (stepId < currentStep.value) {
    currentStep.value = stepId
    createStatus.value = ''
  }
}

const goPreviousStep = () => {
  if (currentStep.value > 1) {
    currentStep.value -= 1
    createStatus.value = ''
  }
}

const goNextStep = () => {
  createStatus.value = ''
  if (currentStep.value === 1 && !stepOneReady.value) {
    createStatus.value = '请先完成基础设定选择。'
    return
  }
  if (currentStep.value === 2 && !stepTwoReady.value) {
    createStatus.value = '请先完成全部属性分配。'
    return
  }
  if (currentStep.value < 3) currentStep.value += 1
}

const toggleSkill = (skill) => {
  if (!isSkillSelectable(skill)) return
  const idx = selectedSkills.value.indexOf(skill.id)
  if (idx > -1) {
    selectedSkills.value.splice(idx, 1)
    return
  }
  if (selectedSkills.value.length >= skillLimit.value) return
  selectedSkills.value.push(skill.id)
}

const isGrantedSkill = (skill) => !isCocSystem.value && grantedSkillIds.value.has(skill.id)

const isClassAllowedSkill = (skill) => {
  if (isCocSystem.value) return true
  return allowedClassSkillIds.value.has('*') || allowedClassSkillIds.value.has(skill.id)
}

const isSkillSelectable = (skill) => !isGrantedSkill(skill) && isClassAllowedSkill(skill)

const skillTag = (skill) => {
  if (isGrantedSkill(skill)) return '已获得'
  if (!isClassAllowedSkill(skill)) return '不可选'
  return ''
}

const selectedSkillsForPayload = () => {
  if (isCocSystem.value) return []
  return selectedSkills.value.filter((skillId) => {
    const allowedByClass = allowedClassSkillIds.value.has('*') || allowedClassSkillIds.value.has(skillId)
    return allowedByClass && !grantedSkillIds.value.has(skillId)
  })
}

const finishNameEdit = () => {
  investigator.name = investigator.name.trim()
  isEditingName.value = false
}

const startNameEdit = () => {
  isEditingName.value = true
  nextTick(() => {
    nameInputRef.value?.focus()
    nameInputRef.value?.select()
  })
}

const validateRequiredFields = () => {
  if (!stepOneReady.value) {
    currentStep.value = 1
    createStatus.value = '请先完成基础设定选择。'
    return false
  }

  if (!stepTwoReady.value) {
    currentStep.value = 2
    createStatus.value = '请先完成全部属性分配。'
    return false
  }

  if (!investigator.name.trim()) {
    createStatus.value = '请先输入角色名字。'
    startNameEdit()
    return false
  }

  return true
}

const resolveWorldId = async () => {
  if (props.worldview?.selectedModule?.worldId) return props.worldview.selectedModule.worldId
  if (props.worldview?.backendId) return props.worldview.backendId
  if (props.worldview?.source === 'backend' && props.worldview?.id) return props.worldview.id

  const worlds = await worldsApi.list()
  const dndWorld = worlds.find((world) => /krenko|克伦可|dnd|dragon|龙/i.test(world.name))
  return dndWorld?.id || worlds[0]?.id || 1
}

const createCharacterPayload = () => {
  const characterName = investigator.name.trim()

  if (isCocSystem.value) {
    return {
      name: characterName,
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
    name: characterName,
    race_id: investigator.raceId || 'high-elf',
    class_id: selectedClass.value?.id || 'rogue',
    background_id: investigator.backgroundId || 'acolyte',
    motivation: investigator.description || '踏上新的冒险',
    ability_assignment: 'standard_array',
    base_attributes: dndAttributesPayload(),
    selected_skills: selectedSkillsForPayload()
  }
}

const enterExistingPlayingSession = async (character = null) => {
  const sessions = await sessionsApi.list()
  const playingSession = sessions.find((session) => session.status === 'playing') || sessions[0]
  if (!playingSession) return false
  emit('session-created', {
    session: playingSession,
    character
  })
  return true
}

const handleCreateCharacter = async () => {
  createStatus.value = ''
  if (!validateRequiredFields() || isSubmitting.value) return

  isSubmitting.value = true
  try {
    const character = await charactersApi.create(createCharacterPayload())
    const worldId = await resolveWorldId()
    if (roomSettings.value.roomName) {
      const roomDetail = await roomsApi.create({
        title: roomSettings.value.roomName,
        world_id: worldId,
        visibility: roomSettings.value.roomType === 'public' ? 'public' : 'private',
        max_players: Number(roomSettings.value.maxPlayers) || 4
      })
      await roomsApi.setCharacter(roomDetail.room.id, character.id)

      createStatus.value = '角色已创建，房间已开启。'
      clearDraft()
      emit('session-created', {
        ...roomDetail,
        character,
        roomId: roomDetail.room.id
      })
      return
    }

    const sessionData = await sessionsApi.start({
      world_id: worldId,
      character_id: character.id,
      title: roomSettings.value.roomName,
      difficulty: roomSettings.value.difficulty || 'normal'
    })

    createStatus.value = '角色已创建，冒险会话已开启。'
    clearDraft()
    emit('session-created', {
      ...sessionData,
      character
    })
  } catch (error) {
    if (error?.message === 'already has a playing session') {
      const entered = await enterExistingPlayingSession()
      if (entered) return
    }
    createStatus.value = error?.message || '角色创建失败，请检查属性、职业与技能选择。'
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
    </div>

    <nav class="navbar">
      <div class="nav-placeholder"></div>
      <div class="nav-logo">
        <img class="logo-icon" :src="productIcon" alt="StoryForge 产品图标" />
        <div class="logo-text">
          <span class="logo-en">StoryForge</span>
          <span class="logo-cn">灵境档案</span>
        </div>
      </div>
      <div class="nav-user">
        <div class="user-chip">
          <div class="user-avatar">夜</div>
          <div class="user-info">
            <span class="user-name">{{ props.currentUser?.nickname || props.currentUser?.username || '游客' }}</span>
            <span class="user-level">Lv.12</span>
          </div>
        </div>
        <button class="nav-icon" aria-label="退出登录" @click="emit('logout')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">
            <path d="M10 17l5-5-5-5" />
            <path d="M15 12H3" />
            <path d="M21 3v18h-8" />
          </svg>
        </button>
      </div>
    </nav>

    <main class="creator-shell">
      <aside class="left-panel">
        <div class="page-title-block">
          <h1>角色创建</h1>
          <p>CHARACTER FORGE</p>
        </div>
        <p class="page-desc">为「{{ moduleTitle }}」创建 {{ isCocSystem ? '调查员' : 'D&D 5e 冒险者' }}</p>

        <div class="step-list">
          <button
            v-for="step in steps"
            :key="step.id"
            class="step-item"
            :class="{ active: currentStep === step.id, completed: completedForStep(step.id) }"
            type="button"
            @click="selectStep(step.id)"
          >
            <span class="num">{{ String(step.id).padStart(2, '0') }}</span>
            <span class="text">{{ step.name }}</span>
            <span class="mark">{{ completedForStep(step.id) ? '✓' : step.en }}</span>
          </button>
        </div>

        <div class="left-actions">
          <button class="btn-outline muted" type="button" @click="saveDraft()">保存草稿</button>
        </div>
      </aside>

      <section class="center-panel">
        <div class="char-summary-top">
          <span>{{ isCocSystem ? 'INVESTIGATOR' : 'ADVENTURER' }}</span>
          <span class="summary-dot"></span>
          <span class="summary-name">{{ investigator.name || '未命名角色' }}</span>
          <span class="summary-dot"></span>
          <span>{{ selectedClass?.name || '未选择职业' }}</span>
        </div>

        <div class="center-content">
          <section v-if="currentStep === 1" class="stage stage-basic">
            <div class="section-header centered">
              <span></span>
              <div>
                <h2>基础设定</h2>
                <p>选择你的种族、职业与背景，定义角色的出身与经历。</p>
              </div>
              <span></span>
            </div>

            <div class="identity-grid character-name-grid">
              <label class="field">
                <span>角色名称</span>
                <input
                  v-model.trim="investigator.name"
                  type="text"
                  maxlength="50"
                  placeholder="输入角色名字"
                />
              </label>
              <label class="field">
                <span>冒险动机</span>
                <input
                  v-model.trim="investigator.description"
                  type="text"
                  maxlength="120"
                  placeholder="追寻真相、偿还旧债、守护同伴..."
                />
              </label>
            </div>

            <div class="selection-grid">
              <article class="selection-col">
                <div class="col-header">
                  <strong>种族</strong>
                  <span>RACE</span>
                </div>
                <div class="current-selection">
                  <svg class="choice-icon" viewBox="0 0 24 24" aria-hidden="true">
                    <path
                      v-for="path in getChoiceIcon(selectedRace?.icon)"
                      :key="path"
                      :d="path"
                    />
                  </svg>
                  <strong>{{ selectedRace?.en }}</strong>
                  <span>{{ selectedRace?.name }}</span>
                </div>
                <div class="selection-options">
                  <button
                    v-for="option in ancestryOptions"
                    :key="option.id"
                    class="option-btn"
                    :class="{ active: investigator.raceId === option.id }"
                    type="button"
                    @click="investigator.raceId = option.id"
                  >
                    <svg class="option-icon" viewBox="0 0 24 24" aria-hidden="true">
                      <path
                        v-for="path in getChoiceIcon(option.icon)"
                        :key="path"
                        :d="path"
                      />
                    </svg>
                    <span class="option-copy">
                      <span>{{ option.en }}</span>
                      <small>{{ option.name }}</small>
                    </span>
                  </button>
                </div>
              </article>

              <article class="selection-col">
                <div class="col-header">
                  <strong>职业</strong>
                  <span>CLASS</span>
                </div>
                <div class="current-selection">
                  <svg class="choice-icon" viewBox="0 0 24 24" aria-hidden="true">
                    <path
                      v-for="path in getChoiceIcon(selectedClass?.icon)"
                      :key="path"
                      :d="path"
                    />
                  </svg>
                  <strong>{{ selectedClass?.en }}</strong>
                  <span>{{ selectedClass?.name }}</span>
                </div>
                <div class="selection-options">
                  <button
                    v-for="option in classOptions"
                    :key="option.id"
                    class="option-btn"
                    :class="{ active: selectedClass?.id === option.id }"
                    type="button"
                    @click="selectedOccupation = option.id"
                  >
                    <svg class="option-icon" viewBox="0 0 24 24" aria-hidden="true">
                      <path
                        v-for="path in getChoiceIcon(option.icon)"
                        :key="path"
                        :d="path"
                      />
                    </svg>
                    <span class="option-copy">
                      <span>{{ option.en }}</span>
                      <small>{{ option.name }}</small>
                    </span>
                  </button>
                </div>
              </article>

              <article class="selection-col">
                <div class="col-header">
                  <strong>背景</strong>
                  <span>BACKGROUND</span>
                </div>
                <div class="current-selection">
                  <svg class="choice-icon" viewBox="0 0 24 24" aria-hidden="true">
                    <path
                      v-for="path in getChoiceIcon(selectedBackground?.icon)"
                      :key="path"
                      :d="path"
                    />
                  </svg>
                  <strong>{{ selectedBackground?.en }}</strong>
                  <span>{{ selectedBackground?.name }}</span>
                </div>
                <div class="selection-options">
                  <button
                    v-for="option in backgroundOptions"
                    :key="option.id"
                    class="option-btn"
                    :class="{ active: investigator.backgroundId === option.id }"
                    type="button"
                    @click="investigator.backgroundId = option.id"
                  >
                    <svg class="option-icon" viewBox="0 0 24 24" aria-hidden="true">
                      <path
                        v-for="path in getChoiceIcon(option.icon)"
                        :key="path"
                        :d="path"
                      />
                    </svg>
                    <span class="option-copy">
                      <span>{{ option.en }}</span>
                      <small>{{ option.name }}</small>
                    </span>
                  </button>
                </div>
              </article>
            </div>
          </section>

          <section v-else-if="currentStep === 2" class="stage stage-attrs">
            <div class="section-header split">
              <div>
                <h2>分配属性</h2>
                <p>{{ isCocSystem ? '使用快速开始百分制数组完成调查员特征。' : '使用 D&D 5e 标准数组完成六项属性。' }}</p>
              </div>
              <div class="array-note">可用数组：{{ availableValues.join(' / ') }}</div>
            </div>

            <div class="attr-grid">
              <article v-for="(attr, index) in attributes" :key="attr.abbr" class="attr-card" :class="{ filled: attr.value }">
                <div class="attr-card-head">
                  <div>
                    <strong>{{ attr.name }}</strong>
                    <span>{{ attr.abbr }}</span>
                  </div>
                  <strong class="attr-value">{{ attr.value || '--' }}</strong>
                </div>
                <p>{{ attr.description }}</p>
                <select :value="attr.value || ''" @change="assignValue(index, Number($event.target.value))">
                  <option value="" disabled>选择数值</option>
                  <option
                    v-for="(value, valueIndex) in availableValues"
                    :key="`${value}-${valueIndex}`"
                    :value="value"
                    :disabled="!canAssign(value) && attr.value !== value"
                  >
                    {{ value }}
                  </option>
                </select>
              </article>
            </div>

            <div class="derived-grid">
              <template v-if="isCocSystem">
                <div><span>HP</span><strong>{{ subAttributes.hp }}</strong></div>
                <div><span>MP</span><strong>{{ subAttributes.mp }}</strong></div>
                <div><span>SAN</span><strong>{{ subAttributes.san }}</strong></div>
                <div><span>DB</span><strong>{{ subAttributes.db }}</strong></div>
                <div><span>BUILD</span><strong>{{ subAttributes.build > 0 ? '+' : '' }}{{ subAttributes.build }}</strong></div>
                <div>
                  <span>LUCK</span>
                  <button class="roll-btn" type="button" @click="rollLuck">{{ isRolling ? '...' : (luckValue || 'ROLL') }}</button>
                </div>
              </template>
              <template v-else>
                <div><span>HP</span><strong>{{ subAttributes.hp }}</strong></div>
                <div><span>AC</span><strong>{{ subAttributes.ac }}</strong></div>
                <div><span>速度</span><strong>{{ subAttributes.speed }}ft</strong></div>
                <div><span>CON</span><strong>{{ subAttributes.conMod }}</strong></div>
                <div><span>DEX</span><strong>{{ subAttributes.dexMod }}</strong></div>
                <div><span>WIS</span><strong>{{ subAttributes.wisMod }}</strong></div>
              </template>
            </div>
          </section>

          <section v-else class="stage stage-skills">
            <div class="section-header split">
              <div>
                <h2>选择技能</h2>
                <p>选择 {{ skillLimit }} 项技能熟练项；背景提供的技能已锁定展示。</p>
              </div>
              <div class="array-note">已选：{{ selectedSkills.length }} / {{ skillLimit }}</div>
            </div>

            <div class="skills-grid">
              <article v-for="group in skillGroups" :key="group.title" class="skill-group">
                <div class="group-header">
                  <strong>{{ group.title }}</strong>
                  <span>{{ group.en }}</span>
                </div>
                <button
                  v-for="skill in group.skills"
                  :key="skill.id"
                  class="skill-row"
                  :class="{ active: selectedSkills.includes(skill.id), locked: !isSkillSelectable(skill) }"
                  type="button"
                  @click="toggleSkill(skill)"
                >
                  <span class="skill-state">{{ !isSkillSelectable(skill) ? '锁' : selectedSkills.includes(skill.id) ? '✓' : '+' }}</span>
                  <span>{{ skill.name }}</span>
                  <small v-if="skillTag(skill)">{{ skillTag(skill) }}</small>
                </button>
              </article>
            </div>
          </section>
        </div>

        <div class="center-footer">
          <button v-if="currentStep > 1" class="footer-btn" type="button" @click="goPreviousStep">返回上一步</button>
          <span v-else></span>
          <button v-if="currentStep < 3" class="footer-btn primary" type="button" @click="goNextStep">
            下一步：{{ currentStep === 1 ? '分配属性' : '选择技能' }}
          </button>
          <button v-else class="footer-btn primary" type="button" :disabled="isSubmitting" @click="handleCreateCharacter">
            {{ isSubmitting ? '正在创建...' : '完成创建：保存角色' }}
          </button>
        </div>
        <p v-if="createStatus" class="create-status">{{ createStatus }}</p>
      </section>

      <aside class="right-panel">
        <section class="summary-card portrait-card">
          <div class="portrait-sigil">
            <img :src="productIcon" alt="" />
          </div>
          <div class="portrait-name">
            <input
              v-if="isEditingName"
              ref="nameInputRef"
              v-model="investigator.name"
              class="portrait-name-input"
              type="text"
              maxlength="50"
              placeholder="输入角色名字"
              @blur="finishNameEdit"
              @keydown.enter.prevent="finishNameEdit"
              @keydown.esc.prevent="isEditingName = false"
            />
            <button
              v-else
              class="portrait-name-button"
              type="button"
              title="点击修改角色名字"
              @click="startNameEdit"
            >
              {{ investigator.name || '未命名角色' }}
            </button>
          </div>
          <p>{{ selectedRace?.name }} / {{ selectedClass?.name }}</p>
          <span>{{ selectedBackground?.name }}</span>
        </section>

        <section class="summary-card">
          <h3>当前摘要</h3>
          <div class="summary-line"><span>世界观</span><strong>{{ worldviewTitle || '未指定' }}</strong></div>
          <div class="summary-line"><span>模组</span><strong>{{ moduleTitle }}</strong></div>
          <div class="summary-line"><span>房间</span><strong>{{ roomSettings.roomName || '待创建' }}</strong></div>
          <div class="summary-line"><span>难度</span><strong>{{ roomSettings.difficulty || 'normal' }}</strong></div>
        </section>

        <section class="summary-card">
          <h3>属性预览</h3>
          <div class="mini-attrs">
            <div v-for="attr in attributes" :key="attr.abbr">
              <span>{{ attr.abbr }}</span>
              <strong>{{ attr.value || '--' }}</strong>
            </div>
          </div>
        </section>

        <section class="summary-card">
          <h3>技能选择</h3>
          <p class="skill-summary">{{ selectedSkillNames }}</p>
        </section>
      </aside>
    </main>
  </div>
</template>

<style scoped>
.role-page {
  --bg-deep: #060504;
  --bg-panel: rgba(12, 10, 8, 0.86);
  --bg-card: rgba(18, 15, 12, 0.9);
  --border-dim: #2a2218;
  --border-normal: #4a3c2a;
  --border-gold: #8a7350;
  --border-glow: #d4b886;
  --text-title: #d4b886;
  --text-main: #e0d6c8;
  --text-dim: #8b7d6b;
  --highlight: #d4b886;
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background: var(--bg-deep);
  color: var(--text-main);
  font-family: 'Noto Serif SC', 'Source Han Serif SC', 'SimSun', serif;
}

.page-bg,
.bg-overlay,
.texture {
  position: absolute;
  inset: 0;
}

.page-bg {
  z-index: 0;
  background-size: cover;
  background-position: center;
}

.bg-overlay {
  background:
    radial-gradient(circle at center, rgba(26, 22, 20, 0.78) 0%, rgba(6, 5, 4, 0.96) 68%),
    linear-gradient(90deg, rgba(3, 4, 6, 0.92), rgba(6, 5, 4, 0.68), rgba(6, 5, 4, 0.96));
}

.texture {
  opacity: 0.05;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 120px 120px;
}

.navbar {
  position: relative;
  z-index: 20;
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  height: 70px;
  padding: 0 40px;
  border-bottom: 1px solid var(--border-normal);
  background: rgba(6, 5, 4, 0.95);
}

.nav-logo {
  grid-column: 2;
  display: flex;
  align-items: center;
  justify-self: center;
  gap: 12px;
}

.logo-icon {
  width: 46px;
  height: 46px;
  object-fit: contain;
}

.logo-text {
  display: grid;
  gap: 1px;
  line-height: 1;
}

.logo-en {
  color: var(--text-title);
  font-size: 22px;
  font-weight: 800;
}

.logo-cn {
  color: var(--text-dim);
  font-size: 12px;
  letter-spacing: 0.28em;
}

.nav-user {
  grid-column: 3;
  justify-self: end;
  display: flex;
  align-items: center;
  gap: 14px;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 7px 14px 7px 7px;
  border: 1px solid rgba(212, 184, 134, 0.24);
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.26);
}

.user-avatar {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border: 1px solid var(--border-gold);
  border-radius: 50%;
  color: var(--highlight);
}

.user-info {
  display: grid;
  gap: 2px;
  text-align: right;
}

.user-name {
  color: var(--text-main);
  font-size: 14px;
}

.user-level {
  color: var(--text-dim);
  font-size: 11px;
}

.nav-icon {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border: 1px solid var(--border-dim);
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.28);
  color: var(--text-title);
  cursor: pointer;
}

.nav-icon svg {
  width: 18px;
  height: 18px;
}

.creator-shell {
  position: relative;
  z-index: 2;
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr) 300px;
  gap: 25px;
  height: calc(100vh - 70px);
  padding: 25px 40px;
  overflow: hidden;
}

.left-panel,
.right-panel {
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.page-title-block {
  text-align: center;
}

.page-title-block h1 {
  color: var(--text-title);
  font-size: 24px;
  font-weight: 500;
  letter-spacing: 0.12em;
}

.page-title-block p,
.page-desc {
  color: var(--text-dim);
  font-size: 12px;
  line-height: 1.7;
}

.page-title-block p {
  margin-top: 4px;
  letter-spacing: 0.22em;
}

.page-desc {
  text-align: center;
}

.step-list {
  display: grid;
  gap: 15px;
}

.step-item {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 14px;
  min-height: 58px;
  padding: 0 18px;
  border: 1px solid transparent;
  border-radius: 3px;
  background: rgba(0, 0, 0, 0.22);
  color: var(--text-dim);
  text-align: left;
  cursor: pointer;
}

.step-item.active {
  border-color: var(--border-glow);
  background: linear-gradient(90deg, rgba(212, 184, 134, 0.12), transparent);
  color: var(--highlight);
  box-shadow: inset 0 0 15px rgba(212, 184, 134, 0.12);
}

.step-item.completed {
  border-color: var(--border-dim);
  color: var(--text-main);
}

.step-item .num {
  font-size: 18px;
  font-weight: 800;
}

.step-item .text {
  font-size: 15px;
}

.step-item .mark {
  max-width: 64px;
  overflow: hidden;
  color: inherit;
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.left-actions {
  margin-top: auto;
  display: grid;
  gap: 12px;
}

.btn-outline {
  min-height: 44px;
  border: 1px solid var(--border-normal);
  background: rgba(0, 0, 0, 0.48);
  color: var(--text-dim);
  cursor: pointer;
}

.btn-outline:hover {
  border-color: var(--highlight);
  color: var(--highlight);
}

.btn-outline.muted {
  opacity: 0.72;
}

.center-panel {
  min-height: 0;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border-normal);
  border-radius: 4px;
  background: var(--bg-panel);
  box-shadow: inset 0 0 50px rgba(0, 0, 0, 0.72);
}

.char-summary-top {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 15px;
  min-height: 52px;
  padding: 0 16px;
  border-bottom: 1px solid var(--border-dim);
  background: rgba(0, 0, 0, 0.34);
  color: var(--text-main);
  font-size: 13px;
}

.summary-name {
  color: var(--highlight);
}

.summary-dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--border-normal);
}

.center-content {
  min-height: 0;
  flex: 1;
  overflow-y: auto;
  padding: 30px;
}

.center-content::-webkit-scrollbar {
  width: 4px;
}

.center-content::-webkit-scrollbar-thumb {
  border-radius: 4px;
  background: var(--border-normal);
}

.stage {
  display: grid;
  gap: 22px;
}

.section-header {
  display: flex;
  gap: 18px;
  color: var(--text-dim);
}

.section-header.centered {
  align-items: center;
  justify-content: center;
  text-align: center;
}

.section-header.centered > span {
  width: 88px;
  height: 1px;
  background: var(--border-normal);
}

.section-header.split {
  align-items: flex-end;
  justify-content: space-between;
}

.section-header h2 {
  margin-bottom: 5px;
  color: var(--text-title);
  font-size: 25px;
  font-weight: 500;
  letter-spacing: 0.14em;
}

.section-header p {
  font-size: 13px;
}

.array-note {
  padding: 8px 12px;
  border: 1px solid var(--border-dim);
  background: rgba(0, 0, 0, 0.28);
  color: var(--highlight);
  font-size: 12px;
}

.selection-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 26px;
}

.selection-col {
  display: grid;
  grid-template-rows: auto 1fr auto;
  gap: 22px;
  min-height: 590px;
  padding: 42px 28px 36px;
  border: 1px solid var(--border-normal);
  background: rgba(0, 0, 0, 0.34);
}

.col-header {
  display: grid;
  gap: 2px;
  justify-items: center;
  text-align: center;
}

.col-header strong {
  color: var(--text-main);
  font-family: "STKaiti", "KaiTi", serif;
  font-size: 29px;
  font-weight: 500;
  line-height: 1.05;
  letter-spacing: 0.12em;
}

.col-header span {
  color: var(--text-dim);
  font-family: Georgia, "Times New Roman", serif;
  font-size: 16px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.col-header span::before,
.col-header span::after {
  content: "";
  display: inline-block;
  width: 42px;
  height: 1px;
  margin: 0 12px 5px;
  background: var(--border-dim);
}

.current-selection {
  display: grid;
  align-content: center;
  gap: 8px;
  justify-items: center;
  min-height: 220px;
  padding: 12px;
  color: var(--highlight);
  text-align: center;
}

.current-selection strong {
  font-family: Georgia, "Times New Roman", serif;
  font-size: 36px;
  font-variant: small-caps;
  line-height: 1;
  text-shadow: 0 0 22px rgba(212, 184, 134, 0.18);
}

.current-selection span {
  color: var(--text-main);
  font-size: 20px;
}

.choice-icon {
  width: 74px;
  height: 74px;
  margin-bottom: 14px;
  color: var(--highlight);
  filter: drop-shadow(0 0 18px rgba(212, 184, 134, 0.28));
}

.choice-icon path,
.option-icon path {
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.selection-options {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.option-btn {
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr);
  align-items: center;
  gap: 12px;
  min-height: 80px;
  padding: 13px 14px;
  border: 1px solid var(--border-dim);
  background: rgba(0, 0, 0, 0.42);
  color: var(--text-main);
  cursor: pointer;
  text-align: left;
}

.option-icon {
  width: 30px;
  height: 30px;
  color: var(--text-dim);
}

.option-copy {
  display: grid;
  gap: 3px;
  min-width: 0;
}

.option-copy span {
  overflow-wrap: anywhere;
  color: var(--text-main);
  font-family: Georgia, "Times New Roman", serif;
  font-size: 17px;
  font-variant: small-caps;
  line-height: 1.05;
}

.option-copy small {
  color: var(--text-dim);
  font-size: 14px;
  line-height: 1.2;
}

.option-btn.active,
.option-btn:hover {
  border-color: var(--highlight);
  background: rgba(212, 184, 134, 0.1);
  color: var(--highlight);
}

.option-btn.active .option-icon,
.option-btn:hover .option-icon,
.option-btn.active .option-copy span,
.option-btn:hover .option-copy span,
.option-btn.active .option-copy small,
.option-btn:hover .option-copy small {
  color: var(--highlight);
}

.identity-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  padding: 18px;
  border: 1px solid var(--border-normal);
  background: rgba(0, 0, 0, 0.22);
}

.character-name-grid {
  grid-template-columns: minmax(220px, 0.8fr) minmax(260px, 1.2fr);
}

.field {
  display: grid;
  gap: 8px;
}

.field span {
  color: var(--text-dim);
  font-size: 12px;
}

.field input,
.field select,
.attr-card select {
  width: 100%;
  min-height: 42px;
  border: 1px solid var(--border-dim);
  border-radius: 2px;
  background: rgba(0, 0, 0, 0.48);
  color: var(--text-main);
  outline: none;
  padding: 0 12px;
}

.field input:focus,
.field select:focus,
.attr-card select:focus {
  border-color: var(--highlight);
}

.attr-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 15px;
}

.attr-card {
  display: grid;
  gap: 12px;
  padding: 16px;
  border: 1px solid var(--border-normal);
  background: var(--bg-card);
}

.attr-card.filled {
  border-color: rgba(212, 184, 134, 0.62);
  box-shadow: inset 0 0 16px rgba(212, 184, 134, 0.08);
}

.attr-card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.attr-card-head div {
  display: grid;
  gap: 3px;
}

.attr-card-head strong {
  color: var(--text-main);
  font-size: 15px;
}

.attr-card-head span,
.attr-card p {
  color: var(--text-dim);
  font-size: 12px;
}

.attr-value {
  color: var(--highlight) !important;
  font-size: 28px !important;
  line-height: 1;
}

.derived-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 10px;
  padding: 16px;
  border: 1px dashed var(--border-normal);
  background: rgba(0, 0, 0, 0.2);
}

.derived-grid div {
  display: grid;
  gap: 6px;
  justify-items: center;
  border-right: 1px solid var(--border-dim);
}

.derived-grid div:last-child {
  border-right: 0;
}

.derived-grid span {
  color: var(--text-dim);
  font-size: 11px;
}

.derived-grid strong,
.roll-btn {
  color: var(--highlight);
  font-size: 20px;
}

.roll-btn {
  border: 0;
  background: transparent;
  cursor: pointer;
}

.skills-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 15px;
  align-items: start;
}

.skill-group {
  border: 1px solid var(--border-normal);
  background: var(--bg-card);
}

.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 44px;
  padding: 0 14px;
  border-bottom: 1px solid var(--border-dim);
  background: rgba(0, 0, 0, 0.38);
}

.group-header strong {
  color: var(--text-main);
  font-size: 13px;
}

.group-header span {
  color: var(--text-dim);
  font-size: 10px;
}

.skill-row {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 10px;
  width: 100%;
  min-height: 44px;
  padding: 0 14px;
  border: 0;
  border-bottom: 1px solid var(--border-dim);
  background: transparent;
  color: var(--text-dim);
  text-align: left;
  cursor: pointer;
}

.skill-row:last-child {
  border-bottom: 0;
}

.skill-row:hover:not(.locked),
.skill-row.active {
  background: linear-gradient(90deg, rgba(212, 184, 134, 0.12), transparent);
  color: var(--text-main);
}

.skill-row.active {
  border-left: 2px solid var(--highlight);
}

.skill-row.locked {
  cursor: not-allowed;
  opacity: 0.72;
}

.skill-state {
  color: var(--highlight);
}

.skill-row small {
  padding: 2px 6px;
  border: 1px solid var(--border-normal);
  color: var(--highlight);
  font-size: 10px;
}

.center-footer {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  padding: 16px 30px 24px;
}

.footer-btn {
  min-width: 148px;
  min-height: 48px;
  border: 1px solid var(--border-normal);
  border-radius: 2px;
  background: rgba(0, 0, 0, 0.42);
  color: var(--text-main);
  cursor: pointer;
}

.footer-btn.primary {
  min-width: 220px;
  border-color: var(--highlight);
  background: linear-gradient(90deg, rgba(138, 115, 80, 0.55), rgba(40, 28, 12, 0.88));
  color: #f8ddb0;
  font-weight: 800;
}

.footer-btn:disabled {
  cursor: wait;
  opacity: 0.64;
}

.create-status {
  margin: -10px 30px 20px;
  color: #7fd7ff;
  text-align: right;
  font-size: 13px;
}

.summary-card {
  padding: 18px;
  border: 1px solid var(--border-normal);
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.34);
}

.portrait-card {
  display: grid;
  justify-items: center;
  gap: 8px;
  text-align: center;
}

.portrait-sigil {
  width: 112px;
  height: 112px;
  display: grid;
  place-items: center;
  border: 1px solid var(--border-gold);
  background: radial-gradient(circle, rgba(212, 184, 134, 0.14), rgba(0, 0, 0, 0.2));
}

.portrait-sigil img {
  width: 74px;
  height: 74px;
  object-fit: contain;
}

.portrait-name {
  width: 100%;
  min-height: 38px;
  display: grid;
  place-items: center;
}

.portrait-name-button {
  max-width: 100%;
  border: 0;
  background: transparent;
  color: var(--text-title);
  cursor: pointer;
  font-family: inherit;
  font-size: 22px;
  font-weight: 800;
  line-height: 1.25;
  overflow-wrap: anywhere;
  text-align: center;
}

.portrait-name-button:hover,
.portrait-name-button:focus-visible {
  color: #f8ddb0;
  outline: none;
  text-decoration: underline;
  text-underline-offset: 6px;
}

.portrait-name-input {
  width: min(100%, 220px);
  min-height: 38px;
  border: 1px solid var(--highlight);
  border-radius: 2px;
  background: rgba(0, 0, 0, 0.58);
  color: var(--text-title);
  font-size: 18px;
  font-weight: 700;
  outline: none;
  padding: 0 10px;
  text-align: center;
}

.portrait-card p,
.portrait-card span,
.skill-summary {
  color: var(--text-dim);
  line-height: 1.7;
}

.summary-card h3 {
  margin-bottom: 14px;
  color: var(--text-title);
  font-size: 16px;
  font-weight: 500;
}

.summary-line {
  display: grid;
  grid-template-columns: 64px 1fr;
  gap: 10px;
  padding: 9px 0;
  border-bottom: 1px solid var(--border-dim);
}

.summary-line:last-child {
  border-bottom: 0;
}

.summary-line span {
  color: var(--text-dim);
  font-size: 12px;
}

.summary-line strong {
  color: var(--text-main);
  font-size: 13px;
  text-align: right;
}

.mini-attrs {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.mini-attrs div {
  display: grid;
  justify-items: center;
  gap: 3px;
  padding: 8px;
  border: 1px solid var(--border-dim);
  background: rgba(0, 0, 0, 0.24);
}

.mini-attrs span {
  color: var(--text-dim);
  font-size: 10px;
}

.mini-attrs strong {
  color: var(--highlight);
}

@media (max-width: 1280px) {
  .creator-shell {
    grid-template-columns: 220px minmax(0, 1fr);
  }

  .right-panel {
    display: none;
  }

  .selection-grid,
  .skills-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .navbar {
    padding: 0 18px;
  }

  .nav-user .user-chip {
    display: none;
  }

  .creator-shell {
    grid-template-columns: 1fr;
    height: auto;
    min-height: calc(100vh - 70px);
    overflow-y: auto;
    padding: 18px;
  }

  .left-panel {
    min-height: auto;
  }

  .step-list {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .step-item {
    grid-template-columns: 1fr;
    justify-items: center;
    text-align: center;
  }

  .step-item .mark {
    display: none;
  }

  .center-panel {
    min-height: 620px;
  }

  .identity-grid,
  .attr-grid,
  .selection-grid,
  .skills-grid,
  .derived-grid {
    grid-template-columns: 1fr;
  }

  .derived-grid div {
    border-right: 0;
    border-bottom: 1px solid var(--border-dim);
    padding-bottom: 8px;
  }

  .center-footer {
    flex-direction: column;
  }

  .footer-btn {
    width: 100%;
  }
}
</style>
