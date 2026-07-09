<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, watch } from 'vue'

const props = defineProps({
  open: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'logout'])

const STORAGE_KEY = 'storyforge:settings'
const settings = reactive({
  master: 80,
  music: 50,
  sfx: 75
})

let audioContext = null
let lastFocusedElement = null
let mediaObserver = null

const masterRatio = computed(() => settings.master / 100)
const sfxRatio = computed(() => (settings.master / 100) * (settings.sfx / 100))

const clampVolume = (value, fallback) => {
  const number = Number(value)
  if (Number.isNaN(number)) return fallback
  return Math.max(0, Math.min(100, Math.round(number)))
}

const readStoredSettings = () => {
  if (typeof window === 'undefined') return

  try {
    const stored = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || '{}')
    settings.master = clampVolume(stored.master, settings.master)
    settings.music = clampVolume(stored.music, settings.music)
    settings.sfx = clampVolume(stored.sfx, settings.sfx)
  } catch {
    window.localStorage.removeItem(STORAGE_KEY)
  }
}

const persistSettings = () => {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...settings }))
}

const applyMediaVolume = () => {
  if (typeof document === 'undefined') return

  document.querySelectorAll('audio, video').forEach((media) => {
    if (media.dataset.storyforgeVolumeManaged === 'false') return
    media.volume = masterRatio.value
    media.muted = settings.master === 0
  })
}

const watchMediaElements = () => {
  if (typeof document === 'undefined' || typeof MutationObserver === 'undefined') return

  mediaObserver = new MutationObserver((mutations) => {
    const hasNewMedia = mutations.some((mutation) =>
      Array.from(mutation.addedNodes).some((node) =>
        node.nodeType === Node.ELEMENT_NODE &&
        (node.matches?.('audio, video') || node.querySelector?.('audio, video'))
      )
    )
    if (hasNewMedia) applyMediaVolume()
  })

  mediaObserver.observe(document.body, { childList: true, subtree: true })
  document.addEventListener('play', applyMediaVolume, true)
}

const emitSettingsChange = () => {
  if (typeof window === 'undefined') return

  window.dispatchEvent(new CustomEvent('storyforge:settings-change', {
    detail: {
      ...settings,
      masterRatio: masterRatio.value,
      musicRatio: settings.music / 100,
      sfxRatio: sfxRatio.value
    }
  }))
}

const applySettings = () => {
  persistSettings()
  applyMediaVolume()
  emitSettingsChange()
}

const getAudioContext = () => {
  if (typeof window === 'undefined') return null
  const AudioContextCtor = window.AudioContext || window.webkitAudioContext
  if (!AudioContextCtor) return null
  if (!audioContext) audioContext = new AudioContextCtor()
  if (audioContext.state === 'suspended') audioContext.resume()
  return audioContext
}

const playSfxPreview = (frequency = 620) => {
  const volume = Math.min(0.12, sfxRatio.value * 0.12)
  if (volume <= 0) return

  const context = getAudioContext()
  if (!context) return

  const now = context.currentTime
  const oscillator = context.createOscillator()
  const gain = context.createGain()

  oscillator.type = 'triangle'
  oscillator.frequency.setValueAtTime(frequency, now)
  gain.gain.setValueAtTime(volume, now)
  gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.08)

  oscillator.connect(gain)
  gain.connect(context.destination)
  oscillator.start(now)
  oscillator.stop(now + 0.09)
}

const close = () => {
  playSfxPreview(420)
  emit('close')
}

const handleLogout = () => {
  playSfxPreview(320)
  emit('logout')
}

const handleSliderCommit = (key) => {
  if (key !== 'music') playSfxPreview(key === 'master' ? 520 : 760)
}

const handleKeydown = (event) => {
  if (event.key === 'Escape' && props.open) close()
}

watch(settings, applySettings, { deep: true })

watch(() => props.open, async (isOpen) => {
  if (typeof document === 'undefined') return

  if (isOpen) {
    lastFocusedElement = document.activeElement
    document.body.classList.add('settings-modal-open')
    await nextTick()
    document.querySelector('.settings-close-btn')?.focus()
    return
  }

  document.body.classList.remove('settings-modal-open')
  lastFocusedElement?.focus?.()
})

onMounted(() => {
  readStoredSettings()
  applySettings()
  watchMediaElements()
  window.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown)
  document.removeEventListener('play', applyMediaVolume, true)
  mediaObserver?.disconnect?.()
  document.body.classList.remove('settings-modal-open')
  audioContext?.close?.()
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="settings-modal-overlay"
      role="presentation"
      @click.self="close"
    >
      <section
        class="settings-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="settings-title"
      >
        <button
          class="settings-close-btn"
          type="button"
          aria-label="关闭设置"
          title="关闭"
          @click="close"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M6 6l12 12M18 6 6 18" />
          </svg>
        </button>

        <h2 id="settings-title" class="settings-title">系统设置</h2>

        <div class="settings-group">
          <label class="setting-item">
            <span class="setting-label">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M4 10v4h4l5 4V6l-5 4H4Z" />
                <path d="M16 8a5 5 0 0 1 0 8" />
                <path d="M18.5 5.5a9 9 0 0 1 0 13" />
              </svg>
              主音量
            </span>
            <span class="slider-row">
              <input
                v-model.number="settings.master"
                class="settings-slider"
                type="range"
                min="0"
                max="100"
                @change="handleSliderCommit('master')"
              />
              <span class="volume-value">{{ settings.master }}%</span>
            </span>
          </label>

          <label class="setting-item">
            <span class="setting-label">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M9 18V5l11-2v13" />
                <circle cx="6" cy="18" r="3" />
                <circle cx="17" cy="16" r="3" />
              </svg>
              音乐
            </span>
            <span class="slider-row">
              <input
                v-model.number="settings.music"
                class="settings-slider"
                type="range"
                min="0"
                max="100"
                title="音乐通道"
                @change="handleSliderCommit('music')"
              />
              <span class="volume-value">{{ settings.music }}%</span>
            </span>
          </label>

          <label class="setting-item">
            <span class="setting-label">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M13 2 4 14h7l-1 8 10-13h-7l1-7Z" />
              </svg>
              音效
            </span>
            <span class="slider-row">
              <input
                v-model.number="settings.sfx"
                class="settings-slider"
                type="range"
                min="0"
                max="100"
                @change="handleSliderCommit('sfx')"
              />
              <span class="volume-value">{{ settings.sfx }}%</span>
            </span>
          </label>
        </div>

        <button class="settings-logout-btn" type="button" @click="handleLogout">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M10 17l5-5-5-5" />
            <path d="M15 12H3" />
            <path d="M21 3v18h-8" />
          </svg>
          退出登录
        </button>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.settings-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 12000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(5px);
}

.settings-modal {
  position: relative;
  width: min(420px, 100%);
  display: flex;
  flex-direction: column;
  padding: 40px;
  border: 1px solid #8b7355;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(30, 25, 22, 0.98), rgba(15, 12, 10, 0.98));
  color: #e0d6c8;
  box-shadow:
    0 15px 40px rgba(0, 0, 0, 0.8),
    inset 0 0 20px rgba(139, 115, 85, 0.15);
  font-family: "Noto Serif SC", "Microsoft YaHei", serif;
  animation: settingsFadeIn 0.25s ease-out;
}

@keyframes settingsFadeIn {
  from {
    opacity: 0;
    transform: scale(0.96) translateY(10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.settings-close-btn {
  position: absolute;
  top: 18px;
  right: 22px;
  width: 30px;
  height: 30px;
  display: grid;
  place-items: center;
  border: 0;
  background: transparent;
  color: #8b7d6b;
  cursor: pointer;
  transition: color 0.2s ease, transform 0.2s ease;
}

.settings-close-btn:hover {
  color: #ff6b6b;
  transform: scale(1.1);
}

.settings-close-btn svg,
.settings-logout-btn svg {
  width: 20px;
  height: 20px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.settings-title {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin: 0 0 30px;
  color: #d4b886;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 4px;
  text-align: center;
}

.settings-title::before,
.settings-title::after {
  content: "";
  width: 6px;
  height: 6px;
  border: 1px solid rgba(139, 115, 85, 0.65);
  transform: rotate(45deg);
}

.settings-group {
  display: flex;
  flex-direction: column;
  gap: 25px;
  margin-bottom: 40px;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  color: #e0d6c8;
  font-size: 15px;
}

.setting-label {
  width: 100px;
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 0 0 auto;
}

.setting-label svg {
  width: 16px;
  height: 16px;
  flex: 0 0 auto;
  fill: none;
  stroke: #d4b886;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.slider-row {
  min-width: 0;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  flex: 1;
}

.settings-slider {
  width: min(150px, 100%);
  height: 4px;
  border-radius: 2px;
  outline: none;
  background: rgba(139, 115, 85, 0.4);
  appearance: none;
  cursor: pointer;
  transition: background 0.2s ease;
}

.settings-slider:hover {
  background: rgba(139, 115, 85, 0.8);
}

.settings-slider::-webkit-slider-thumb {
  width: 14px;
  height: 14px;
  border: 2px solid #1a1614;
  border-radius: 50%;
  background: #d4b886;
  box-shadow: 0 0 5px rgba(0, 0, 0, 0.8);
  appearance: none;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.settings-slider::-webkit-slider-thumb:hover {
  transform: scale(1.2);
  box-shadow: 0 0 8px #d4b886;
}

.settings-slider::-moz-range-thumb {
  width: 14px;
  height: 14px;
  border: 2px solid #1a1614;
  border-radius: 50%;
  background: #d4b886;
  box-shadow: 0 0 5px rgba(0, 0, 0, 0.8);
  cursor: pointer;
}

.volume-value {
  width: 34px;
  color: #8b7d6b;
  font-family: Consolas, "Courier New", monospace;
  font-size: 12px;
  text-align: right;
}

.settings-logout-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 48px;
  padding: 14px;
  border: 1px solid #8b2621;
  border-radius: 6px;
  background: rgba(139, 38, 33, 0.1);
  color: #ff6b6b;
  font: inherit;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 2px;
  cursor: pointer;
  transition:
    background 0.3s ease,
    border-color 0.3s ease,
    box-shadow 0.3s ease,
    color 0.3s ease,
    transform 0.3s ease;
}

.settings-logout-btn:hover {
  border-color: #8b2621;
  background: #8b2621;
  color: #e0d6c8;
  box-shadow: 0 0 15px rgba(139, 38, 33, 0.6);
  transform: translateY(-2px);
}

@media (max-width: 480px) {
  .settings-modal {
    padding: 34px 22px 24px;
  }

  .setting-item {
    align-items: flex-start;
    flex-direction: column;
    gap: 12px;
  }

  .setting-label {
    width: auto;
  }

  .slider-row {
    width: 100%;
  }

  .settings-slider {
    width: 100%;
  }
}
</style>
