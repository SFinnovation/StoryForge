<script setup>
import { computed } from 'vue'
import productIcon from '../../图标/产品图标.png'

const props = defineProps({
  currentUser: {
    type: Object,
    default: null
  },
  subLabel: {
    type: String,
    default: 'Lv.12'
  }
})

const emit = defineEmits(['open-settings', 'logout'])

const displayName = computed(() => (
  props.currentUser?.nickname || props.currentUser?.username || '游客'
))

const avatarText = computed(() => {
  const source = props.currentUser?.username || props.currentUser?.nickname || displayName.value || '游'
  return String(source).trim().slice(0, 1).toUpperCase() || '游'
})
</script>

<template>
  <nav class="sf-navbar" aria-label="主导航">
    <div class="sf-navbar-side" aria-hidden="true"></div>

    <div class="sf-nav-logo" aria-label="StoryForge 灵境档案">
      <img class="sf-logo-icon" :src="productIcon" alt="StoryForge 产品图标" />
      <div class="sf-logo-text">
        <span class="sf-logo-en">StoryForge</span>
        <span class="sf-logo-cn">灵境档案</span>
      </div>
    </div>

    <div class="sf-nav-user">
      <div class="sf-user-chip">
        <div class="sf-user-avatar" aria-hidden="true">{{ avatarText }}</div>
        <div class="sf-user-info">
          <span class="sf-user-name">{{ displayName }}</span>
          <span class="sf-user-level">{{ subLabel }}</span>
        </div>
      </div>

      <button class="sf-nav-icon sf-nav-icon--pending" type="button" aria-label="邮箱功能待开发" title="邮箱功能待开发">
        待开发
      </button>

      <button class="sf-nav-icon" type="button" aria-label="设置" title="设置" @click="emit('open-settings')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
          <circle cx="12" cy="12" r="3" />
          <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5v.2a2 2 0 1 1-4 0v-.2a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.2a1.7 1.7 0 0 0 1.5-1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3 1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.2a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8 1.7 1.7 0 0 0 1.5 1h.2a2 2 0 1 1 0 4h-.2a1.7 1.7 0 0 0-1.5 1Z" />
        </svg>
      </button>

      <button class="sf-nav-icon" type="button" aria-label="退出登录" title="退出登录" @click="emit('logout')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
          <path d="M10 17l5-5-5-5" />
          <path d="M15 12H3" />
          <path d="M21 3v18h-8" />
        </svg>
      </button>
    </div>
  </nav>
</template>

<style scoped>
.sf-navbar {
  position: relative;
  z-index: 20;
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 20px;
  min-height: 76px;
  padding: 14px 34px 10px;
  border-bottom: 1px solid rgba(221, 174, 94, 0.14);
  background: linear-gradient(180deg, rgba(4, 4, 6, 0.88), rgba(4, 4, 6, 0.44));
  backdrop-filter: blur(10px);
}

.sf-navbar::after {
  content: '';
  position: absolute;
  left: 50%;
  bottom: -1px;
  width: 92px;
  height: 2px;
  transform: translateX(-50%);
  background: linear-gradient(90deg, transparent, rgba(248, 199, 99, 0.96), transparent);
  box-shadow: 0 0 15px rgba(248, 199, 99, 0.45);
}

.sf-navbar-side {
  min-width: 0;
}

.sf-nav-logo {
  grid-column: 2;
  grid-row: 1;
  justify-self: center;
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.sf-logo-icon {
  width: 52px;
  height: 52px;
  object-fit: contain;
  filter: drop-shadow(0 0 12px rgba(240, 190, 90, 0.18));
}

.sf-logo-text {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 0;
  line-height: 1.04;
}

.sf-logo-en {
  color: #efc26a;
  font-size: 1.05rem;
  letter-spacing: 0.05em;
}

.sf-logo-cn {
  margin-top: 2px;
  color: rgba(241, 198, 108, 0.86);
  font-size: 0.88rem;
  letter-spacing: 0.26em;
}

.sf-nav-user {
  grid-column: 3;
  grid-row: 1;
  justify-self: end;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  min-width: 0;
}

.sf-user-chip {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  max-width: 270px;
  padding: 7px 14px 7px 7px;
  border: 1px solid rgba(237, 187, 93, 0.2);
  border-radius: 999px;
  background: linear-gradient(180deg, rgba(54, 34, 10, 0.45), rgba(11, 11, 14, 0.45));
}

.sf-user-avatar {
  width: 42px;
  height: 42px;
  flex: 0 0 auto;
  display: grid;
  place-items: center;
  border: 1px solid rgba(248, 196, 94, 0.34);
  border-radius: 50%;
  background:
    radial-gradient(circle at 35% 30%, rgba(255, 222, 170, 0.28), transparent 26%),
    linear-gradient(180deg, #3f2c12, #17100a);
  color: #f7cc7d;
  font-weight: 700;
  line-height: 1;
}

.sf-user-info {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sf-user-name {
  max-width: 160px;
  overflow: hidden;
  color: #f7d389;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sf-user-level {
  color: rgba(240, 222, 185, 0.76);
  font-size: 0.84rem;
}

.sf-nav-icon {
  width: 44px;
  height: 44px;
  flex: 0 0 auto;
  display: grid;
  place-items: center;
  border: 1px solid rgba(241, 191, 94, 0.22);
  border-radius: 50%;
  background: rgba(10, 11, 14, 0.55);
  color: rgba(247, 205, 122, 0.88);
  cursor: pointer;
  transition: border-color 0.2s ease, color 0.2s ease, background 0.2s ease;
}

.sf-nav-icon:hover {
  border-color: rgba(241, 191, 94, 0.5);
  color: #ffd889;
  background: rgba(54, 34, 10, 0.5);
}

.sf-nav-icon svg {
  width: 19px;
  height: 19px;
}

.sf-nav-icon--pending {
  width: 58px;
  border-radius: 999px;
  color: rgba(240, 222, 185, 0.72);
  font-size: 12px;
  letter-spacing: 0;
}

@media (max-width: 900px) {
  .sf-navbar {
    grid-template-columns: auto 1fr auto;
    gap: 12px;
    padding: 14px 18px 10px;
  }

  .sf-nav-logo {
    grid-column: 1;
    justify-self: start;
  }

  .sf-navbar-side {
    display: none;
  }

  .sf-nav-user {
    grid-column: 3;
  }

  .sf-user-chip {
    display: none;
  }
}

@media (max-width: 560px) {
  .sf-logo-icon {
    width: 42px;
    height: 42px;
  }

  .sf-logo-en {
    font-size: 0.95rem;
  }

  .sf-logo-cn {
    font-size: 0.76rem;
  }

  .sf-nav-icon {
    width: 38px;
    height: 38px;
  }

  .sf-nav-icon--pending {
    width: 50px;
    font-size: 11px;
  }
}
</style>
