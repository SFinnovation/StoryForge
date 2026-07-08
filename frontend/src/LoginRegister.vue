<script setup>
import { computed, reactive, ref } from 'vue'
import { authApi, clearAuth } from './api/client'
import loginBackground from '../背景/login界面.png'
import productIcon from '../图标/产品图标.png'

const emit = defineEmits(['enter'])

const STORAGE_KEY = 'storyforge_auth_users'
const SESSION_KEY = 'storyforge_auth_session'
const USERNAME_MIN_LENGTH = 3
const USERNAME_MAX_LENGTH = 50
const PASSWORD_MIN_LENGTH = 6
const PASSWORD_MAX_LENGTH = 128
const NICKNAME_MAX_LENGTH = 50

const isLogin = ref(true)
const showPassword = ref(false)
const authError = ref('')
const authMessage = ref('')
const isSubmitting = ref(false)

const loginForm = reactive({
  username: '',
  password: '',
  remember: true
})

const registerForm = reactive({
  nickname: '',
  username: '',
  password: '',
  confirmPassword: ''
})

const rememberedUser = ref(localStorage.getItem(SESSION_KEY) || '')

const getErrorMessage = (error, fallback) =>
  typeof error?.message === 'string' && error.message.trim() ? error.message : fallback

const menuItems = computed(() => [
  {
    label: '登录',
    desc: '进入灵境档案',
    active: isLogin.value,
    action: () => switchMode(true)
  },
  {
    label: '注册',
    desc: '创建新账号',
    active: !isLogin.value,
    action: () => switchMode(false)
  },
  {
    label: '游客进入',
    desc: '先体验大厅',
    active: false,
    action: handleGuestEnter
  },
  {
    label: '继续上次冒险',
    desc: '读取最近会话',
    active: false,
    action: handleGuestEnter
  }
])

const getUsers = () => {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
  } catch {
    return []
  }
}

const saveUsers = (users) => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(users))
}

const switchMode = (loginMode) => {
  isLogin.value = loginMode
  authError.value = ''
  authMessage.value = ''
}

const handleGuestEnter = () => {
  authError.value = ''
  clearAuth()
  authMessage.value = '已以游客身份进入。'
  emit('enter', {
    user: {
      username: 'guest',
      nickname: '游客'
    }
  })
}

const handleLogin = async () => {
  authError.value = ''
  if (isSubmitting.value) return
  isSubmitting.value = true

  try {
    const result = await authApi.login({
      username: loginForm.username,
      password: loginForm.password
    })

    if (loginForm.remember) {
      localStorage.setItem(SESSION_KEY, loginForm.username)
    } else {
      localStorage.removeItem(SESSION_KEY)
    }

    rememberedUser.value = loginForm.username
    authMessage.value = `欢迎回来，${result.user?.nickname || result.user?.username || loginForm.username}。`
    emit('enter', { user: result.user })
    return
  } catch (error) {
    authError.value = getErrorMessage(error, '账号或密码不正确。')
    return
  } finally {
    isSubmitting.value = false
  }

  const users = getUsers()
  const matchedUser = users.find(
    (user) => user.username === loginForm.username && user.password === loginForm.password
  )

  if (!matchedUser) {
    authError.value = '账号或密码不正确。'
    return
  }

  if (loginForm.remember) {
    localStorage.setItem(SESSION_KEY, loginForm.username)
  } else {
    localStorage.removeItem(SESSION_KEY)
  }

  rememberedUser.value = loginForm.username
  authMessage.value = `欢迎回来，${matchedUser.nickname || matchedUser.username}。`
  emit('enter')
}

const handleRegister = async () => {
  authError.value = ''

  const nickname = registerForm.nickname.trim()
  const username = registerForm.username.trim()
  const password = registerForm.password
  const confirmPassword = registerForm.confirmPassword

  if (!nickname || !username || !password) {
    authError.value = '请完整填写注册信息。'
    return
  }

  if (username.length < USERNAME_MIN_LENGTH) {
    authError.value = `用户名至少需要 ${USERNAME_MIN_LENGTH} 个字符。`
    return
  }

  if (username.length > USERNAME_MAX_LENGTH) {
    authError.value = `用户名不能超过 ${USERNAME_MAX_LENGTH} 个字符。`
    return
  }

  if (nickname.length > NICKNAME_MAX_LENGTH) {
    authError.value = `昵称不能超过 ${NICKNAME_MAX_LENGTH} 个字符。`
    return
  }

  if (password.length < PASSWORD_MIN_LENGTH) {
    authError.value = `密码至少需要 ${PASSWORD_MIN_LENGTH} 个字符。`
    return
  }

  if (password.length > PASSWORD_MAX_LENGTH) {
    authError.value = `密码不能超过 ${PASSWORD_MAX_LENGTH} 个字符。`
    return
  }

  if (password !== confirmPassword) {
    authError.value = '两次输入的密码不一致。'
    return
  }

  if (isSubmitting.value) return
  isSubmitting.value = true

  try {
    const result = await authApi.register({
      nickname,
      username,
      password
    })

    localStorage.setItem(SESSION_KEY, username)
    rememberedUser.value = username
    authMessage.value = '注册成功，已自动进入大厅。'
    emit('enter', { user: result.user })
    return
  } catch (error) {
    authError.value = getErrorMessage(error, '注册失败，请稍后再试。')
    return
  } finally {
    isSubmitting.value = false
  }

  const users = getUsers()
  if (users.some((user) => user.username === registerForm.username)) {
    authError.value = '该账号已存在。'
    return
  }

  users.push({
    nickname: registerForm.nickname,
    username: registerForm.username,
    password: registerForm.password
  })
  saveUsers(users)

  localStorage.setItem(SESSION_KEY, registerForm.username)
  rememberedUser.value = registerForm.username
  authMessage.value = '注册成功，已自动进入大厅。'
  emit('enter')
}

if (rememberedUser.value) {
  loginForm.username = rememberedUser.value
}
</script>

<template>
  <div class="login-stage">
    <div class="login-backdrop">
      <img class="backdrop-image" :src="loginBackground" alt="登录背景" />
      <div class="backdrop-vignette"></div>
      <div class="magic-overlay"></div>
      <div class="orb-container">
        <div class="orb-glow"></div>
        <div class="orb-ring orb-ring-1"></div>
        <div class="orb-ring orb-ring-2"></div>
        <div class="orb-ring orb-ring-3"></div>
        <div class="orb-core"></div>
      </div>
    </div>

    <div class="login-panel">
      <div class="brand-section">
        <img class="brand-icon" :src="productIcon" alt="StoryForge 产品图标" />
        <p class="brand-kicker">StoryForge Archives</p>
        <h1 class="brand-title">灵境档案</h1>
        <p class="brand-copy">
          AI 掌卷人已启封灵境卷宗，与你共赴冒险。
        </p>
      </div>

      <nav class="menu-section">
        <button
          v-for="item in menuItems"
          :key="item.label"
          type="button"
          class="menu-item"
          :class="{ active: item.active }"
          @click="item.action?.()"
        >
          <span class="menu-item-icon">
            <svg v-if="item.label === '登录'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"/>
            </svg>
            <svg v-else-if="item.label === '注册'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M18 9v3a3 3 0 006 0v-3M13 19h7a3 3 0 003-3v-8a3 3 0 00-3-3h-7a4 4 0 00-4 4v11a3 3 0 003 3z"/>
            </svg>
            <svg v-else-if="item.label === '游客进入'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
              <path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/>
              <path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
          </span>
          <span class="menu-item-label">{{ item.label }}</span>
          <span class="menu-item-desc">{{ item.desc }}</span>
        </button>
      </nav>

      <section class="form-section">
        <form v-if="isLogin" class="auth-form" @submit.prevent="handleLogin">
          <label class="field">
            <span class="field-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
              </svg>
            </span>
            <input v-model="loginForm.username" type="text" placeholder="用户名 / 邮箱" required />
          </label>
          <label class="field">
            <span class="field-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0110 0v4"/>
              </svg>
            </span>
            <div class="password-row">
              <input
                v-model="loginForm.password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="密码"
                required
              />
              <button type="button" class="eye-btn" @click="showPassword = !showPassword">
                {{ showPassword ? '隐藏' : '显示' }}
              </button>
            </div>
          </label>
          <div class="form-row">
            <label class="remember-box">
              <input v-model="loginForm.remember" type="checkbox" />
              <span>记住我</span>
            </label>
            <button type="button" class="ghost-link">忘记密码?</button>
          </div>
          <button type="submit" class="primary-action">进入灵境</button>
        </form>

        <form v-else class="auth-form" @submit.prevent="handleRegister">
          <label class="field">
            <span class="field-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
            </span>
            <input
              v-model="registerForm.nickname"
              type="text"
              placeholder="昵称"
              :maxlength="NICKNAME_MAX_LENGTH"
              required
            />
          </label>
          <label class="field">
            <span class="field-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
              </svg>
            </span>
            <input
              v-model="registerForm.username"
              type="text"
              placeholder="用户名 / 邮箱"
              :minlength="USERNAME_MIN_LENGTH"
              :maxlength="USERNAME_MAX_LENGTH"
              required
            />
          </label>
          <label class="field">
            <span class="field-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0110 0v4"/>
              </svg>
            </span>
            <input
              v-model="registerForm.password"
              type="password"
              placeholder="密码"
              :minlength="PASSWORD_MIN_LENGTH"
              :maxlength="PASSWORD_MAX_LENGTH"
              required
            />
          </label>
          <label class="field">
            <span class="field-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0110 0v4"/>
              </svg>
            </span>
            <input
              v-model="registerForm.confirmPassword"
              type="password"
              placeholder="确认密码"
              :minlength="PASSWORD_MIN_LENGTH"
              :maxlength="PASSWORD_MAX_LENGTH"
              required
            />
          </label>
          <button type="submit" class="primary-action">创建账号</button>
        </form>

        <p v-if="authError" class="auth-status error">{{ authError }}</p>
        <p v-else-if="authMessage" class="auth-status success">{{ authMessage }}</p>
      </section>

      <div class="footer-section">
        <button class="footer-btn">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.7 1.7 0 00.34 1.82l.05.06a2 2 0 11-2.83 2.83l-.06-.05A1.7 1.7 0 0015 19.4a1.7 1.7 0 00-1 1.53V21a2 2 0 11-4 0v-.08a1.7 1.7 0 00-1-1.52 1.7 1.7 0 00-1.9.36l-.06.05a2 2 0 11-2.83-2.83l.05-.06A1.7 1.7 0 004.6 15a1.7 1.7 0 00-1.52-1H3a2 2 0 110-4h.08A1.7 1.7 0 004.6 9a1.7 1.7 0 00-.34-1.82l-.05-.06a2 2 0 112.83-2.83l.06.05A1.7 1.7 0 009 4.6a1.7 1.7 0 001-1.52V3a2 2 0 114 0v.08a1.7 1.7 0 001 1.52 1.7 1.7 0 001.9-.36l.06-.05a2 2 0 112.83 2.83l-.05.06A1.7 1.7 0 0019.4 9c.14.47.66.8 1.15.8H21a2 2 0 110 4h-.45c-.49 0-1.01.33-1.15.8Z"/>
          </svg>
          <span>设置</span>
        </button>
        <button class="footer-btn">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M18 6h-3a5 5 0 00-5 5v2a3 3 0 00-3 3v7a2 2 0 002 2h10a2 2 0 002-2v-7a3 3 0 00-3-3V11a5 5 0 00-5-5z"/>
            <line x1="16" y1="11" x2="16" y2="17"/>
            <line x1="8" y1="11" x2="8" y2="17"/>
          </svg>
          <span>公告</span>
        </button>
        <button class="footer-btn">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
          <span>客服</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-stage {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background: #05070d;
  color: #f2ead9;
}

.login-backdrop {
  position: absolute;
  inset: 0;
  z-index: 0;
}

.backdrop-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
  filter: brightness(0.85) saturate(0.95);
}

.backdrop-vignette {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, rgba(3, 5, 10, 0.96) 0%, rgba(3, 5, 10, 0.92) 25%, rgba(3, 5, 10, 0.7) 45%, rgba(3, 5, 10, 0.4) 70%, rgba(3, 5, 10, 0.2) 100%),
    linear-gradient(180deg, rgba(0, 0, 0, 0.3) 0%, transparent 20%, transparent 80%, rgba(0, 0, 0, 0.4) 100%);
}

.magic-overlay {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 70% 30%, rgba(89, 206, 255, 0.08), transparent 30%),
    radial-gradient(circle at 65% 45%, rgba(255, 183, 72, 0.05), transparent 25%);
}

.orb-container {
  position: absolute;
  right: 18%;
  top: 28%;
  width: 200px;
  height: 200px;
  pointer-events: none;
}

.orb-glow {
  position: absolute;
  inset: -40px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(89, 206, 255, 0.3), rgba(89, 206, 255, 0.1) 40%, transparent 70%);
  filter: blur(30px);
  animation: orbPulse 4s ease-in-out infinite;
}

.orb-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 1px solid rgba(89, 206, 255, 0.3);
}

.orb-ring-1 {
  animation: ringRotate 20s linear infinite;
}

.orb-ring-2 {
  inset: 15%;
  border-color: rgba(255, 183, 72, 0.25);
  animation: ringRotate 15s linear infinite reverse;
}

.orb-ring-3 {
  inset: 30%;
  border-color: rgba(89, 206, 255, 0.4);
  animation: ringRotate 10s linear infinite;
}

.orb-core {
  position: absolute;
  inset: 40%;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.8), rgba(89, 206, 255, 0.4) 50%, transparent);
  filter: blur(8px);
  animation: coreGlow 3s ease-in-out infinite;
}

@keyframes orbPulse {
  0%, 100% { transform: scale(0.95); opacity: 0.7; }
  50% { transform: scale(1.1); opacity: 1; }
}

@keyframes ringRotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes coreGlow {
  0%, 100% { opacity: 0.6; transform: scale(0.9); }
  50% { opacity: 1; transform: scale(1.1); }
}

.login-panel {
  position: relative;
  z-index: 1;
  width: 400px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 32px 28px;
  background: linear-gradient(180deg, rgba(4, 5, 10, 0.92), rgba(4, 5, 10, 0.85));
  backdrop-filter: blur(12px);
  border-right: 1px solid rgba(255, 255, 255, 0.05);
}

.brand-section {
  margin-bottom: 32px;
}

.brand-icon {
  width: 56px;
  height: 56px;
  object-fit: contain;
  filter: drop-shadow(0 0 12px rgba(240, 190, 90, 0.2));
}

.brand-kicker {
  margin-top: 8px;
  color: #5fcfff;
  font-size: 11px;
  letter-spacing: 0.45em;
  text-transform: uppercase;
}

.brand-title {
  margin-top: 4px;
  font-size: 38px;
  line-height: 1;
  letter-spacing: 0.08em;
  color: #f3f0e8;
}

.brand-copy {
  margin-top: 12px;
  max-width: 22ch;
  color: rgba(237, 228, 211, 0.65);
  line-height: 1.7;
  font-size: 13px;
}

.menu-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 28px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 14px;
  width: 100%;
  padding: 12px 16px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.02);
  color: #d7d0c1;
  text-align: left;
  cursor: pointer;
  transition: all 0.25s ease;
  border-radius: 8px;
}

.menu-item:hover {
  border-color: rgba(243, 180, 92, 0.3);
  background: rgba(243, 180, 92, 0.05);
}

.menu-item.active {
  border-color: rgba(243, 180, 92, 0.5);
  background: linear-gradient(90deg, rgba(243, 180, 92, 0.12), rgba(255, 255, 255, 0.02));
}

.menu-item-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(243, 180, 92, 0.6);
}

.menu-item-icon svg {
  width: 18px;
  height: 18px;
}

.menu-item.active .menu-item-icon {
  color: #f3b45c;
}

.menu-item-label {
  flex: 1;
  font-size: 16px;
  letter-spacing: 0.06em;
}

.menu-item-desc {
  font-size: 11px;
  color: rgba(215, 208, 193, 0.5);
}

.form-section {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.field {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
}

.field-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(243, 180, 92, 0.5);
  flex-shrink: 0;
}

.field-icon svg {
  width: 16px;
  height: 16px;
}

.field input {
  flex: 1;
  padding: 14px 0;
  border: none;
  background: transparent;
  color: #f5efe2;
  outline: none;
  font-size: 14px;
}

.field input::placeholder {
  color: rgba(215, 208, 193, 0.35);
}

.field:focus-within {
  border-color: rgba(98, 218, 255, 0.4);
  box-shadow: 0 0 0 3px rgba(98, 218, 255, 0.08);
}

.password-row {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
}

.password-row input {
  flex: 1;
  padding: 14px 0;
}

.eye-btn {
  padding: 8px 12px;
  border: none;
  background: rgba(255, 255, 255, 0.05);
  color: #68ddff;
  font-size: 12px;
  cursor: pointer;
  border-radius: 6px;
}

.form-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 4px;
}

.remember-box {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: rgba(237, 228, 211, 0.65);
  font-size: 12px;
}

.remember-box input {
  accent-color: #f3b45c;
}

.ghost-link {
  border: none;
  background: none;
  color: #68ddff;
  font-size: 12px;
  cursor: pointer;
}

.primary-action {
  margin-top: 12px;
  padding: 14px 18px;
  border: none;
  border-radius: 10px;
  background: linear-gradient(90deg, #f3b45c, #f7d28f 50%, #ef9b37 100%);
  color: #1c140d;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 8px 20px rgba(239, 155, 55, 0.25);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.primary-action:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 24px rgba(239, 155, 55, 0.3);
}

.auth-status {
  margin-top: 10px;
  font-size: 12px;
  text-align: center;
}

.auth-status.error {
  color: #ff8e8e;
}

.auth-status.success {
  color: #86e0b5;
}

.footer-section {
  display: flex;
  justify-content: space-around;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.footer-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 10px 16px;
  border: none;
  background: transparent;
  color: rgba(215, 208, 193, 0.5);
  cursor: pointer;
  transition: color 0.2s ease;
}

.footer-btn:hover {
  color: #f3b45c;
}

.footer-btn svg {
  width: 18px;
  height: 18px;
}

.footer-btn span {
  font-size: 11px;
}

@media (max-width: 768px) {
  .login-panel {
    width: 100%;
    border-right: none;
    padding: 24px 20px;
  }

  .orb-container {
    display: none;
  }

  .brand-title {
    font-size: 32px;
  }

  .menu-item {
    padding: 10px 14px;
  }
}
</style>
