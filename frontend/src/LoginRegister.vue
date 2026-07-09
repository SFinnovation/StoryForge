<script setup>
import { computed, reactive, ref } from 'vue'
import { authApi } from './api/client'
import productIcon from '../图标/产品图标.png'
import loginBackground from '../背景/login界面.png'

const emit = defineEmits(['enter', 'open-settings'])

const SESSION_KEY = 'storyforge_auth_session'
const USERNAME_MIN_LENGTH = 3
const USERNAME_MAX_LENGTH = 50
const PASSWORD_MIN_LENGTH = 6
const PASSWORD_MAX_LENGTH = 128
const NICKNAME_MAX_LENGTH = 50

const mode = ref('login')
const showLoginPassword = ref(false)
const showRegisterPassword = ref(false)
const showRegisterConfirmPassword = ref(false)
const authError = ref('')
const authMessage = ref('')
const isSubmitting = ref(false)

const loginForm = reactive({
  username: localStorage.getItem(SESSION_KEY) || '',
  password: '',
  remember: true
})

const registerForm = reactive({
  nickname: '',
  username: '',
  password: '',
  confirmPassword: ''
})

const isLogin = computed(() => mode.value === 'login')
const headerDesc = computed(() =>
  isLogin.value
    ? 'AI 掌卷人已启用灵境卷算，与你共赴冒险。'
    : '签下这份灵境契约，开启你的专属史诗。'
)

const knownErrorMessages = {
  'invalid username or password': '账号或密码不正确。',
  'username already exists': '该用户名已存在。',
  'email already exists': '该邮箱已存在。',
  'account is banned': '账号已被禁用。'
}

const getErrorMessage = (error, fallback) => {
  const message = typeof error?.message === 'string' ? error.message.trim() : ''
  return knownErrorMessages[message] || message || fallback
}

const switchTab = (nextMode) => {
  mode.value = nextMode
  authError.value = ''
  authMessage.value = ''
}

const showShellMessage = (name) => {
  authError.value = ''
  authMessage.value = `${name}暂未接入，当前仅保留入口。`
}

const handleGuestEnter = async () => {
  authError.value = ''
  authMessage.value = ''
  if (isSubmitting.value) return
  isSubmitting.value = true
  try {
    const result = await authApi.guest()
    authMessage.value = '已以游客身份进入。'
    emit('enter', { user: result.user })
  } catch (error) {
    authError.value = getErrorMessage(error, '游客账号创建失败，请稍后再试。')
  } finally {
    isSubmitting.value = false
  }
}

const handleLogin = async () => {
  authError.value = ''
  authMessage.value = ''

  const username = loginForm.username.trim()
  if (!username || !loginForm.password) {
    authError.value = '请填写用户名和密码。'
    return
  }

  if (isSubmitting.value) return
  isSubmitting.value = true

  try {
    const result = await authApi.login({
      username,
      password: loginForm.password
    })

    if (loginForm.remember) {
      localStorage.setItem(SESSION_KEY, username)
    } else {
      localStorage.removeItem(SESSION_KEY)
    }

    authMessage.value = `欢迎回来，${result.user?.nickname || result.user?.username || username}。`
    emit('enter', { user: result.user })
  } catch (error) {
    authError.value = getErrorMessage(error, '账号或密码不正确。')
  } finally {
    isSubmitting.value = false
  }
}

const handleRegister = async () => {
  authError.value = ''
  authMessage.value = ''

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
    authMessage.value = '注册成功，已自动进入大厅。'
    emit('enter', { user: result.user })
  } catch (error) {
    authError.value = getErrorMessage(error, '注册失败，请稍后再试。')
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="auth-stage">
    <img class="auth-backdrop" :src="loginBackground" alt="登录背景" />
    <div class="auth-shade" aria-hidden="true"></div>

    <section class="auth-modal" aria-label="登录注册">
      <header class="modal-header">
        <div class="d20-icon" aria-hidden="true">
          <img :src="productIcon" alt="" />
        </div>
        <p class="subtitle">StoryForge Archives</p>
        <h1 class="title">灵境档案</h1>
        <div class="divider">
          <span></span>
          <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
            <path d="M12 2l2 7 7 2-7 2-2 7-2-7-7-2 7-2 2-7Z" />
          </svg>
          <p>{{ headerDesc }}</p>
          <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
            <path d="M12 2l2 7 7 2-7 2-2 7-2-7-7-2 7-2 2-7Z" />
          </svg>
          <span></span>
        </div>
      </header>

      <nav class="tabs" aria-label="登录注册切换">
        <button type="button" :class="{ active: isLogin }" @click="switchTab('login')">登录</button>
        <button type="button" :class="{ active: !isLogin }" @click="switchTab('register')">注册</button>
      </nav>

      <form v-if="isLogin" class="auth-form" @submit.prevent="handleLogin">
        <button type="button" class="guest-btn" :disabled="isSubmitting" @click="handleGuestEnter">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
          以游客身份进入
        </button>

        <label class="field">
          <svg class="field-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
          <input v-model="loginForm.username" type="text" placeholder="用户名 / 邮箱" maxlength="50" required />
        </label>

        <label class="field">
          <svg class="field-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
            <rect x="3" y="11" width="18" height="11" rx="2" />
            <path d="M7 11V7a5 5 0 0 1 10 0v4" />
          </svg>
          <input
            v-model="loginForm.password"
            :type="showLoginPassword ? 'text' : 'password'"
            placeholder="密码"
            maxlength="128"
            required
          />
          <button type="button" class="eye-btn" @click="showLoginPassword = !showLoginPassword">
            {{ showLoginPassword ? '隐藏' : '显示' }}
          </button>
        </label>

        <div class="form-row">
          <label class="remember-box">
            <input v-model="loginForm.remember" type="checkbox" />
            <span>记住我</span>
          </label>
          <button type="button" class="text-link" @click="showShellMessage('忘记密码')">忘记密码?</button>
        </div>

        <button type="submit" class="submit-btn" :disabled="isSubmitting">
          {{ isSubmitting ? '连接中...' : '进入灵境' }}
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12 2l1.5 7.5L21 11l-7.5 1.5L12 20l-1.5-7.5L3 11l7.5-1.5L12 2Z" />
          </svg>
        </button>
      </form>

      <form v-else class="auth-form" @submit.prevent="handleRegister">
        <label class="field">
          <svg class="field-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
          <input v-model="registerForm.nickname" type="text" placeholder="昵称" :maxlength="NICKNAME_MAX_LENGTH" required />
        </label>

        <label class="field">
          <svg class="field-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
            <path d="M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0ZM12 14a7 7 0 0 0-7 7h14a7 7 0 0 0-7-7Z" />
          </svg>
          <input
            v-model="registerForm.username"
            type="text"
            placeholder="用户名"
            :minlength="USERNAME_MIN_LENGTH"
            :maxlength="USERNAME_MAX_LENGTH"
            required
          />
        </label>

        <label class="field">
          <svg class="field-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
            <rect x="3" y="11" width="18" height="11" rx="2" />
            <path d="M7 11V7a5 5 0 0 1 10 0v4" />
          </svg>
          <input
            v-model="registerForm.password"
            :type="showRegisterPassword ? 'text' : 'password'"
            placeholder="密码"
            :minlength="PASSWORD_MIN_LENGTH"
            :maxlength="PASSWORD_MAX_LENGTH"
            required
          />
          <button type="button" class="eye-btn" @click="showRegisterPassword = !showRegisterPassword">
            {{ showRegisterPassword ? '隐藏' : '显示' }}
          </button>
        </label>

        <label class="field">
          <svg class="field-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
            <rect x="3" y="11" width="18" height="11" rx="2" />
            <path d="M7 11V7a5 5 0 0 1 10 0v4" />
          </svg>
          <input
            v-model="registerForm.confirmPassword"
            :type="showRegisterConfirmPassword ? 'text' : 'password'"
            placeholder="确认密码"
            :minlength="PASSWORD_MIN_LENGTH"
            :maxlength="PASSWORD_MAX_LENGTH"
            required
          />
          <button type="button" class="eye-btn" @click="showRegisterConfirmPassword = !showRegisterConfirmPassword">
            {{ showRegisterConfirmPassword ? '隐藏' : '显示' }}
          </button>
        </label>

        <button type="submit" class="submit-btn" :disabled="isSubmitting">
          {{ isSubmitting ? '连接中...' : '缔结契约' }}
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12 2l1.5 7.5L21 11l-7.5 1.5L12 20l-1.5-7.5L3 11l7.5-1.5L12 2Z" />
          </svg>
        </button>
      </form>

      <p v-if="authError" class="auth-status error">{{ authError }}</p>
      <p v-else-if="authMessage" class="auth-status success">{{ authMessage }}</p>
      <p v-else class="auth-status"></p>

      <footer class="footer-links">
        <button type="button" class="footer-item" @click="emit('open-settings')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5v.2a2 2 0 1 1-4 0v-.2a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.2a1.7 1.7 0 0 0 1.5-1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3 1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.2a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8 1.7 1.7 0 0 0 1.5 1h.2a2 2 0 1 1 0 4h-.2a1.7 1.7 0 0 0-1.5 1Z" />
          </svg>
          <span>设置</span>
        </button>
        <button type="button" class="footer-item" @click="showShellMessage('公告')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
            <path d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
            <path d="M13.7 21a2 2 0 0 1-3.4 0" />
          </svg>
          <span>公告</span>
        </button>
        <button type="button" class="footer-item" @click="showShellMessage('客服')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
            <path d="M3 18v-6a9 9 0 0 1 18 0v6" />
            <path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3ZM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3Z" />
          </svg>
          <span>客服</span>
        </button>
      </footer>
    </section>
  </div>
</template>

<style scoped>
.auth-stage {
  position: relative;
  min-height: 100vh;
  display: grid;
  place-items: center;
  overflow: hidden;
  padding: 28px;
  background:
    radial-gradient(circle at 78% 24%, rgba(79, 151, 210, 0.18), transparent 32%),
    #070910;
  color: #d1d5db;
}

.auth-backdrop {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
  filter: brightness(0.68) saturate(0.92);
  transform: scale(1.02);
}

.auth-shade {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, rgba(5, 8, 14, 0.78), rgba(5, 8, 14, 0.36), rgba(5, 8, 14, 0.74)),
    radial-gradient(circle at center, transparent 0%, rgba(0, 0, 0, 0.42) 74%);
}

.auth-modal {
  position: relative;
  z-index: 1;
  width: min(440px, 100%);
  padding: 38px 40px 30px;
  border: 1px solid #3a3429;
  border-radius: 12px;
  background: rgba(18, 22, 29, 0.88);
  box-shadow: 0 30px 70px rgba(0, 0, 0, 0.72);
  backdrop-filter: blur(14px);
}

.auth-modal::after {
  content: '';
  position: absolute;
  inset: 6px;
  border: 1px solid rgba(223, 180, 112, 0.16);
  border-radius: 8px;
  pointer-events: none;
}

.modal-header {
  text-align: center;
}

.d20-icon {
  width: 42px;
  height: 42px;
  margin: 0 auto 12px;
  display: grid;
  place-items: center;
}

.d20-icon img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  filter: drop-shadow(0 0 10px rgba(223, 180, 112, 0.18));
}

.subtitle {
  margin: 0;
  color: #9ca3af;
  font-size: 11px;
  letter-spacing: 0.36em;
  text-transform: uppercase;
}

.title {
  margin: 8px 0 16px;
  color: #f3f0ea;
  font-family: "Noto Serif SC", "Songti SC", serif;
  font-size: 30px;
  font-weight: 600;
  letter-spacing: 0.12em;
}

.divider {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 28px;
}

.divider span {
  height: 1px;
  flex: 1;
  background: linear-gradient(90deg, transparent, rgba(223, 180, 112, 0.34), transparent);
}

.divider svg {
  width: 12px;
  height: 12px;
  flex: 0 0 auto;
  color: rgba(223, 180, 112, 0.54);
}

.divider p {
  max-width: 18em;
  margin: 0;
  color: #888d96;
  font-size: 13px;
  line-height: 1.5;
}

.tabs {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  margin-bottom: 24px;
  border-bottom: 1px solid #333;
}

.tabs button {
  position: relative;
  padding: 0 0 12px;
  border: 0;
  background: transparent;
  color: #6b7280;
  font-size: 15px;
  cursor: pointer;
}

.tabs button.active {
  color: #dfb470;
}

.tabs button.active::after {
  content: '';
  position: absolute;
  right: 0;
  bottom: -1px;
  left: 0;
  height: 2px;
  background: #dfb470;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  animation: fadeIn 0.24s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.guest-btn,
.field {
  min-height: 48px;
  border: 1px solid rgba(223, 180, 112, 0.2);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.025);
}

.guest-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
  color: #d1d5db;
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease;
}

.guest-btn:hover {
  border-color: rgba(223, 180, 112, 0.36);
  background: rgba(255, 255, 255, 0.06);
}

.guest-btn svg {
  width: 20px;
  height: 20px;
  color: #dfb470;
}

.field {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 14px;
  border-color: #333;
  background: #12141a;
}

.field:focus-within {
  border-color: #dfb470;
}

.field-icon {
  width: 18px;
  height: 18px;
  flex: 0 0 auto;
  color: #6b7280;
}

.field input {
  width: 100%;
  min-width: 0;
  padding: 14px 0;
  border: 0;
  outline: 0;
  background: transparent;
  color: #f3f0ea;
  font-size: 14px;
}

.field input::placeholder {
  color: #6b7280;
}

.eye-btn,
.text-link {
  border: 0;
  background: transparent;
  color: #9ca3af;
  cursor: pointer;
  transition: color 0.2s ease;
}

.eye-btn {
  flex: 0 0 auto;
  padding: 6px 0 6px 8px;
  font-size: 12px;
}

.eye-btn:hover,
.text-link:hover {
  color: #dfb470;
}

.form-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #888d96;
  font-size: 13px;
}

.remember-box {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #9ca3af;
  cursor: pointer;
}

.remember-box input {
  width: 16px;
  height: 16px;
  accent-color: #dfb470;
}

.submit-btn {
  position: relative;
  min-height: 52px;
  margin-top: 8px;
  padding: 15px 48px 15px 18px;
  border: 0;
  border-radius: 6px;
  background: linear-gradient(90deg, #f3d49b, #dfb470, #c89a54);
  color: #1a1a1a;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(223, 180, 112, 0.22);
  transition: filter 0.2s ease, opacity 0.2s ease;
}

.submit-btn:hover {
  filter: brightness(1.08);
}

.submit-btn:disabled {
  cursor: wait;
  opacity: 0.72;
}

.submit-btn svg {
  position: absolute;
  top: 50%;
  right: 16px;
  width: 20px;
  height: 20px;
  transform: translateY(-50%);
  fill: #1a1a1a;
}

.auth-status {
  min-height: 20px;
  margin: 12px 0 0;
  color: #888d96;
  font-size: 13px;
  line-height: 1.5;
  text-align: center;
}

.auth-status.error {
  color: #ff9d9d;
}

.auth-status.success {
  color: #91e4bd;
}

.footer-links {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
  margin-top: 10px;
  padding-top: 18px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.footer-item {
  min-height: 58px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 7px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: #6b7280;
  cursor: pointer;
  transition: color 0.2s ease, background 0.2s ease;
}

.footer-item:hover {
  background: rgba(255, 255, 255, 0.03);
  color: #dfb470;
}

.footer-item svg {
  width: 20px;
  height: 20px;
}

.footer-item span {
  font-size: 13px;
}

@media (max-width: 560px) {
  .auth-stage {
    place-items: stretch;
    padding: 16px;
  }

  .auth-modal {
    width: 100%;
    margin: auto 0;
    padding: 30px 22px 24px;
  }

  .title {
    font-size: 27px;
  }

  .divider p {
    font-size: 12px;
  }
}
</style>
