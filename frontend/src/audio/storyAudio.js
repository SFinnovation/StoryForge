const SETTINGS_KEY = 'storyforge:settings'

const DEFAULT_SETTINGS = {
  master: 80,
  music: 50,
  sfx: 75
}

const MUSIC_TRACKS = {
  login: '/audio/登录页面.mp3',
  script: '/audio/世界观的选择.mp3',
  role: '/audio/角色选择.mp3',
  room: '/audio/房间页面.mp3'
}

const CLICK_SFX = '/audio/点击页面.mp3'
const CLICK_SFX_GAIN = 2.5
const INTERACTIVE_SELECTOR = [
  'button',
  'a',
  '[role="button"]',
  'summary',
  'select',
  'input[type="button"]',
  'input[type="submit"]',
  'input[type="checkbox"]',
  'input[type="radio"]',
  'input[type="range"]',
  '.worldview-card',
  '.module-card',
  '.archive-card',
  '.tree-item',
  '.room-card',
  '.member-row',
  '.skill-card',
  '.ability-card',
  '.option-card'
].join(',')

let settings = { ...DEFAULT_SETTINGS }
let musicAudio = null
let clickAudio = null
let currentScene = null
let userActivated = false
let initialized = false

const clampVolume = (value, fallback) => {
  const number = Number(value)
  if (Number.isNaN(number)) return fallback
  return Math.max(0, Math.min(100, Math.round(number)))
}

const readStoredSettings = () => {
  if (typeof window === 'undefined') return

  try {
    const stored = JSON.parse(window.localStorage.getItem(SETTINGS_KEY) || '{}')
    settings = {
      master: clampVolume(stored.master, DEFAULT_SETTINGS.master),
      music: clampVolume(stored.music, DEFAULT_SETTINGS.music),
      sfx: clampVolume(stored.sfx, DEFAULT_SETTINGS.sfx)
    }
  } catch {
    settings = { ...DEFAULT_SETTINGS }
  }
}

const musicVolume = () => (settings.master / 100) * (settings.music / 100)
const sfxVolume = () => (settings.master / 100) * (settings.sfx / 100)

const encodedPath = (path) => encodeURI(path)

const applyVolumes = () => {
  if (musicAudio) {
    musicAudio.volume = musicVolume()
    musicAudio.muted = musicVolume() <= 0
  }
  if (clickAudio) {
    clickAudio.volume = Math.min(1, sfxVolume() * CLICK_SFX_GAIN)
    clickAudio.muted = sfxVolume() <= 0
  }
}

const stopMusic = () => {
  if (!musicAudio) return
  musicAudio.pause()
  musicAudio.src = ''
  musicAudio = null
}

const tryPlayMusic = () => {
  if (!musicAudio || !userActivated || musicVolume() <= 0) return
  musicAudio.play().catch(() => {})
}

const createMusicAudio = (scene) => {
  const source = MUSIC_TRACKS[scene]
  if (!source) {
    stopMusic()
    return
  }

  stopMusic()
  musicAudio = new Audio(encodedPath(source))
  musicAudio.loop = true
  musicAudio.preload = 'auto'
  musicAudio.dataset.storyforgeVolumeManaged = 'false'
  applyVolumes()
  tryPlayMusic()
}

const createClickAudio = () => {
  if (clickAudio) return clickAudio

  clickAudio = new Audio(encodedPath(CLICK_SFX))
  clickAudio.preload = 'auto'
  clickAudio.dataset.storyforgeVolumeManaged = 'false'
  applyVolumes()
  return clickAudio
}

const playClickSfx = () => {
  if (sfxVolume() <= 0) return

  const audio = createClickAudio()
  audio.currentTime = 0
  audio.play().catch(() => {})
}

const isDisabledTarget = (element) =>
  Boolean(element?.closest?.('[disabled], [aria-disabled="true"], .disabled'))

const shouldPlayClick = (target) => {
  const element = target?.closest?.(INTERACTIVE_SELECTOR)
  if (!element || isDisabledTarget(element)) return false
  return !target.closest?.('input[type="text"], input[type="password"], textarea')
}

const handlePointerDown = (event) => {
  if (event.button !== 0) return
  userActivated = true
  if (shouldPlayClick(event.target)) playClickSfx()
  tryPlayMusic()
}

const handleKeydown = (event) => {
  if (event.key !== 'Enter' && event.key !== ' ') return
  userActivated = true
  if (shouldPlayClick(event.target)) playClickSfx()
  tryPlayMusic()
}

const handleSettingsChange = (event) => {
  const detail = event.detail || {}
  settings = {
    master: clampVolume(detail.master, settings.master),
    music: clampVolume(detail.music, settings.music),
    sfx: clampVolume(detail.sfx, settings.sfx)
  }
  applyVolumes()
  tryPlayMusic()
}

export const initStoryAudio = () => {
  if (typeof window === 'undefined' || initialized) return

  initialized = true
  readStoredSettings()
  createClickAudio()
  document.addEventListener('pointerdown', handlePointerDown, true)
  document.addEventListener('keydown', handleKeydown, true)
  window.addEventListener('storyforge:settings-change', handleSettingsChange)
}

export const setMusicScene = (scene) => {
  if (currentScene === scene) return
  currentScene = scene
  createMusicAudio(scene)
}

export const destroyStoryAudio = () => {
  if (typeof window === 'undefined' || !initialized) return

  initialized = false
  document.removeEventListener('pointerdown', handlePointerDown, true)
  document.removeEventListener('keydown', handleKeydown, true)
  window.removeEventListener('storyforge:settings-change', handleSettingsChange)
  stopMusic()
  clickAudio?.pause()
  clickAudio = null
}
