<script setup>
import { ref, reactive } from 'vue'

const isLogin = ref(true)

const loginForm = reactive({
  username: '',
  password: '',
  remember: false
})

const registerForm = reactive({
  nickname: '',
  username: '',
  password: '',
  confirmPassword: ''
})

const handleLogin = () => {
  console.log('登录数据:', { ...loginForm })
}

const handleRegister = () => {
  if (registerForm.password !== registerForm.confirmPassword) {
    alert('两次输入的密码不一致')
    return
  }
  console.log('注册数据:', { ...registerForm })
}

const features = [
  { name: 'AI 主持', desc: '智能 DM 驱动叙事' },
  { name: '角色档案', desc: '完整角色成长记录' },
  { name: '行动判定', desc: 'D20 骰子精准裁决' },
  { name: '灵境卷宗', desc: '无限故事世界探索' }
]
</script>

<template>
  <div class="auth-page">
    <div class="auth-bg">
      <div class="bg-overlay"></div>
    </div>

    <div class="auth-content">
      <div class="brand-section">
        <div class="brand-inner">
          <div class="brand-logo">
            <div class="d20-icon">
              <span class="d20-number">20</span>
            </div>
          </div>
          <h1 class="brand-title">StoryForge</h1>
          <h2 class="brand-subtitle">灵境档案</h2>
          <p class="brand-slogan">
            AI 掌卷人已启封灵境卷宗，掷下命运之骰，开启你的跑团冒险。
          </p>
          <div class="features">
            <div
              v-for="(feature, index) in features"
              :key="index"
              class="feature-item"
            >
              <div class="feature-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path v-if="index === 0" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                  <path v-else-if="index === 1" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                  <path v-else-if="index === 2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                  <path v-else d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
                </svg>
              </div>
              <div class="feature-text">
                <span class="feature-name">{{ feature.name }}</span>
                <span class="feature-desc">{{ feature.desc }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="form-section">
        <div class="auth-card">
          <div class="card-glow"></div>
          <div class="card-border"></div>
          
          <div class="card-header">
            <div class="tabs">
              <button
                class="tab-btn"
                :class="{ active: isLogin }"
                @click="isLogin = true"
              >
                <span class="tab-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2"/>
                    <circle cx="9" cy="7" r="4"/>
                    <path d="M22 21v-2a4 4 0 00-3-3.87"/>
                    <path d="M16 3.13a4 4 0 010 7.75"/>
                  </svg>
                </span>
                <span>登录</span>
              </button>
              <button
                class="tab-btn"
                :class="{ active: !isLogin }"
                @click="isLogin = false"
              >
                <span class="tab-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0z"/>
                  </svg>
                </span>
                <span>注册</span>
              </button>
            </div>
          </div>

          <div class="card-body">
            <form v-if="isLogin" @submit.prevent="handleLogin" class="auth-form">
              <div class="form-group">
                <label class="form-label">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                  </svg>
                  <span>账号</span>
                </label>
                <input
                  v-model="loginForm.username"
                  type="text"
                  class="form-input"
                  placeholder="请输入账号"
                  required
                />
              </div>
              <div class="form-group">
                <label class="form-label">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                    <path d="M7 11V7a5 5 0 0110 0v4"/>
                  </svg>
                  <span>密码</span>
                </label>
                <input
                  v-model="loginForm.password"
                  type="password"
                  class="form-input"
                  placeholder="请输入密码"
                  required
                />
              </div>
              <div class="form-options">
                <label class="checkbox-label">
                  <input
                    v-model="loginForm.remember"
                    type="checkbox"
                    class="form-checkbox"
                  />
                  <span class="checkbox-custom"></span>
                  <span>记住我</span>
                </label>
                <button type="button" class="forgot-link">忘记密码？</button>
              </div>
              <button type="submit" class="submit-btn login-btn">
                <span>进入灵境</span>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M5 12h14"/>
                  <path d="M12 5l7 7-7 7"/>
                </svg>
              </button>
            </form>

            <form v-else @submit.prevent="handleRegister" class="auth-form">
              <div class="form-group">
                <label class="form-label">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                  </svg>
                  <span>昵称</span>
                </label>
                <input
                  v-model="registerForm.nickname"
                  type="text"
                  class="form-input"
                  placeholder="请输入昵称"
                  required
                />
              </div>
              <div class="form-group">
                <label class="form-label">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
                    <circle cx="12" cy="7" r="4"/>
                  </svg>
                  <span>账号</span>
                </label>
                <input
                  v-model="registerForm.username"
                  type="text"
                  class="form-input"
                  placeholder="请输入账号"
                  required
                />
              </div>
              <div class="form-group">
                <label class="form-label">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                    <path d="M7 11V7a5 5 0 0110 0v4"/>
                  </svg>
                  <span>密码</span>
                </label>
                <input
                  v-model="registerForm.password"
                  type="password"
                  class="form-input"
                  placeholder="请输入密码"
                  required
                />
              </div>
              <div class="form-group">
                <label class="form-label">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                    <path d="M7 11V7a5 5 0 0110 0v4"/>
                  </svg>
                  <span>确认密码</span>
                </label>
                <input
                  v-model="registerForm.confirmPassword"
                  type="password"
                  class="form-input"
                  placeholder="请再次输入密码"
                  required
                />
              </div>
              <button type="submit" class="submit-btn register-btn">
                <span>创建卷宗</span>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 4v16m8-8H4"/>
                </svg>
              </button>
            </form>
          </div>

          <div class="card-footer">
            <span v-if="isLogin">还没有灵境档案？</span>
            <span v-else>已有灵境档案？</span>
            <button type="button" class="switch-link" @click="isLogin = !isLogin">
              {{ isLogin ? '立即注册' : '返回登录' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="magic-particles">
      <div v-for="i in 20" :key="i" class="particle" :style="{ left: `${Math.random() * 100}%`, animationDelay: `${Math.random() * 5}s` }"></div>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  width: 100%;
  height: 100vh;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #05080e 0%, #080a10 50%, #0a0d14 100%);
}

.auth-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: url('/src/assets/auth-bg.png');
  background-size: cover;
  background-position: center;
  z-index: 0;
}

.bg-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, rgba(5, 8, 14, 0.9) 0%, rgba(8, 10, 16, 0.85) 50%, rgba(10, 13, 20, 0.9) 100%);
  backdrop-filter: blur(2px);
}

.auth-content {
  position: relative;
  z-index: 10;
  width: 100%;
  height: 100%;
  display: flex;
}

.brand-section {
  width: 55%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
  position: relative;
}

.brand-section::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 1px;
  height: 100%;
  background: linear-gradient(180deg, transparent 0%, rgba(245, 185, 91, 0.2) 20%, rgba(245, 185, 91, 0.3) 50%, rgba(245, 185, 91, 0.2) 80%, transparent 100%);
}

.brand-inner {
  max-width: 520px;
  animation: fadeInLeft 0.8s ease-out;
}

@keyframes fadeInLeft {
  from {
    opacity: 0;
    transform: translateX(-30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.brand-logo {
  margin-bottom: 32px;
}

.d20-icon {
  width: 80px;
  height: 80px;
  background: radial-gradient(130% 130% at 30% 30%, #f5b95b 0%, #d49a3f 40%, #8b6914 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 40px rgba(245, 185, 91, 0.4), inset 0 -10px 20px rgba(0, 0, 0, 0.3);
  position: relative;
}

.d20-icon::after {
  content: '';
  position: absolute;
  top: 5px;
  left: 5px;
  right: 5px;
  bottom: 5px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 50%;
}

.d20-number {
  font-size: 36px;
  font-weight: 700;
  color: #1a1a2e;
  text-shadow: 1px 1px 0 rgba(255, 255, 255, 0.3);
}

.brand-title {
  font-size: 56px;
  font-weight: 800;
  color: #f5b95b;
  letter-spacing: 8px;
  margin-bottom: 8px;
  text-shadow: 0 0 30px rgba(245, 185, 91, 0.5);
}

.brand-subtitle {
  font-size: 24px;
  font-weight: 400;
  color: #f5e6c8;
  letter-spacing: 12px;
  margin-bottom: 28px;
  opacity: 0.9;
}

.brand-slogan {
  font-size: 16px;
  line-height: 1.8;
  color: #c9b896;
  margin-bottom: 48px;
  font-weight: 300;
  letter-spacing: 0.5px;
}

.features {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.feature-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: rgba(245, 185, 91, 0.05);
  border-radius: 8px;
  border: 1px solid rgba(245, 185, 91, 0.1);
  transition: all 0.3s ease;
}

.feature-item:hover {
  background: rgba(245, 185, 91, 0.08);
  border-color: rgba(245, 185, 91, 0.2);
  transform: translateY(-2px);
}

.feature-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6fe8ff;
  flex-shrink: 0;
}

.feature-icon svg {
  width: 20px;
  height: 20px;
}

.feature-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.feature-name {
  font-size: 14px;
  font-weight: 600;
  color: #f5b95b;
}

.feature-desc {
  font-size: 12px;
  color: #9ca3af;
}

.form-section {
  width: 45%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.auth-card {
  width: 100%;
  max-width: 420px;
  background: rgba(10, 12, 18, 0.82);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 40px;
  position: relative;
  animation: fadeInRight 0.8s ease-out;
}

@keyframes fadeInRight {
  from {
    opacity: 0;
    transform: translateX(30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.card-glow {
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: linear-gradient(135deg, rgba(245, 185, 91, 0.15) 0%, rgba(111, 232, 255, 0.1) 50%, rgba(245, 185, 91, 0.15) 100%);
  border-radius: 18px;
  z-index: -1;
  filter: blur(20px);
}

.card-border {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border: 1px solid rgba(245, 185, 91, 0.2);
  border-radius: 16px;
  pointer-events: none;
}

.card-header {
  margin-bottom: 32px;
}

.tabs {
  display: flex;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  padding: 4px;
}

.tab-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: #9ca3af;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.tab-btn:hover {
  color: #f5e6c8;
}

.tab-btn.active {
  background: rgba(245, 185, 91, 0.15);
  color: #f5b95b;
}

.tab-icon svg {
  width: 16px;
  height: 16px;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #c9b896;
  font-weight: 500;
}

.form-label svg {
  width: 14px;
  height: 14px;
}

.form-input {
  width: 100%;
  padding: 14px 16px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  color: #f5e6c8;
  font-size: 14px;
  outline: none;
  transition: all 0.3s ease;
}

.form-input::placeholder {
  color: #4b5563;
}

.form-input:focus {
  border-color: #6fe8ff;
  box-shadow: 0 0 15px rgba(111, 232, 255, 0.3), inset 0 0 10px rgba(111, 232, 255, 0.1);
}

.form-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #9ca3af;
  cursor: pointer;
}

.form-checkbox {
  display: none;
}

.checkbox-custom {
  width: 16px;
  height: 16px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  position: relative;
  transition: all 0.3s ease;
}

.form-checkbox:checked + .checkbox-custom {
  background: #f5b95b;
  border-color: #f5b95b;
}

.form-checkbox:checked + .checkbox-custom::after {
  content: '';
  position: absolute;
  left: 5px;
  top: 2px;
  width: 5px;
  height: 10px;
  border: solid #1a1a2e;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.forgot-link {
  background: none;
  border: none;
  color: #6fe8ff;
  font-size: 13px;
  cursor: pointer;
  transition: color 0.3s ease;
}

.forgot-link:hover {
  color: #8ff0ff;
}

.submit-btn {
  margin-top: 8px;
  padding: 16px;
  background: linear-gradient(135deg, #f5b95b 0%, #d49a3f 50%, #f5b95b 100%);
  background-size: 200% 200%;
  border: none;
  border-radius: 8px;
  color: #1a1a2e;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.submit-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 30px rgba(245, 185, 91, 0.3);
  animation: shimmer 2s ease-in-out infinite;
}

@keyframes shimmer {
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
}

.submit-btn svg {
  width: 18px;
  height: 18px;
}

.card-footer {
  margin-top: 24px;
  text-align: center;
  font-size: 13px;
  color: #9ca3af;
}

.switch-link {
  background: none;
  border: none;
  color: #f5b95b;
  font-weight: 500;
  cursor: pointer;
  transition: color 0.3s ease;
}

.switch-link:hover {
  color: #ffe0a3;
}

.magic-particles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 5;
}

.particle {
  position: absolute;
  width: 4px;
  height: 4px;
  background: #f5b95b;
  border-radius: 50%;
  opacity: 0;
  animation: floatUp 5s ease-in-out infinite;
  box-shadow: 0 0 10px rgba(245, 185, 91, 0.5);
}

@keyframes floatUp {
  0% {
    opacity: 0;
    transform: translateY(100vh) scale(0);
  }
  10% {
    opacity: 1;
    transform: translateY(90vh) scale(1);
  }
  90% {
    opacity: 1;
    transform: translateY(10vh) scale(1);
  }
  100% {
    opacity: 0;
    transform: translateY(0) scale(0);
  }
}

@media (max-width: 992px) {
  .brand-section {
    display: none;
  }
  
  .form-section {
    width: 100%;
    padding: 20px;
  }
  
  .auth-card {
    padding: 30px 24px;
  }
  
  .brand-title {
    font-size: 40px;
  }
  
  .features {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .auth-card {
    padding: 24px 20px;
  }
  
  .tab-btn {
    padding: 10px 8px;
    font-size: 12px;
  }
  
  .form-input {
    padding: 12px 14px;
    font-size: 13px;
  }
  
  .submit-btn {
    padding: 14px;
    font-size: 14px;
  }
}
</style>
