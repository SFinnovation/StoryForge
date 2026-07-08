<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  rooms: {
    type: Array,
    default: () => []
  },
  errorMessage: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['close', 'join', 'clear-error'])

const inviteCode = ref('')
const selectedRoomId = ref(props.rooms[0]?.id || null)
const localError = ref('')

const selectedRoom = computed(() => props.rooms.find((room) => room.id === selectedRoomId.value) || null)

watch(inviteCode, (value) => {
  if (value.trim()) {
    selectedRoomId.value = null
    localError.value = ''
    emit('clear-error')
  }
})

watch(() => props.rooms, (rooms) => {
  if (!selectedRoomId.value && rooms.length > 0 && !inviteCode.value.trim()) {
    selectedRoomId.value = rooms[0].id
  }
})

const selectRoom = (room) => {
  selectedRoomId.value = room.id
  inviteCode.value = ''
  localError.value = ''
  emit('clear-error')
}

const submitJoin = () => {
  const code = inviteCode.value.trim()
  if (!code && !selectedRoom.value) {
    localError.value = '请输入房间号，或选择一个公开房间。'
    return
  }

  emit('join', {
    code,
    room: selectedRoom.value
  })
}
</script>

<template>
  <div class="join-room-overlay" @click.self="emit('close')">
    <section class="join-room-modal" role="dialog" aria-modal="true" aria-labelledby="join-room-title">
      <header class="join-room-header">
        <h2 id="join-room-title">加入房间</h2>
        <button class="close-btn" type="button" aria-label="关闭" @click="emit('close')">
          <span aria-hidden="true">×</span>
        </button>
      </header>

      <div class="form-group">
        <label class="form-label" for="invite-code">根据房间号加入房间</label>
        <div class="input-wrapper">
          <span class="input-icon">#</span>
          <input
            id="invite-code"
            v-model="inviteCode"
            class="form-input"
            type="text"
            placeholder="请输入 6 位房间码..."
            @keyup.enter="submitJoin"
          />
        </div>
      </div>

      <div class="divider">或选择公开房间加入</div>

      <div class="room-list-container">
        <button
          v-for="room in rooms"
          :key="room.id"
          type="button"
          class="room-item"
          :class="{ selected: selectedRoomId === room.id }"
          @click="selectRoom(room)"
        >
          <span class="room-info">
            <span class="radio-circle"></span>
            <span class="room-name">
              {{ room.name }}
              <span class="tag-worldview">{{ room.worldview }}</span>
            </span>
          </span>
          <span class="room-meta">
            <span class="player-count">{{ room.players }}</span>
            <span class="status">{{ room.status }}</span>
          </span>
        </button>

        <p v-if="rooms.length === 0" class="empty-state">暂无公开房间，可输入房间号加入。</p>
      </div>

      <p v-if="localError || errorMessage" class="join-error">{{ localError || errorMessage }}</p>

      <footer class="join-room-footer">
        <button class="btn btn-cancel" type="button" @click="emit('close')">取消</button>
        <button class="btn btn-primary" type="button" @click="submitJoin">加入房间</button>
      </footer>
    </section>
  </div>
</template>

<style scoped>
.join-room-overlay {
  position: fixed;
  inset: 0;
  z-index: 40;
  display: grid;
  place-items: center;
  background: rgba(0, 0, 0, 0.74);
  backdrop-filter: blur(8px);
}

.join-room-modal {
  width: min(540px, calc(100vw - 32px));
  max-height: calc(100vh - 48px);
  display: flex;
  flex-direction: column;
  padding: 30px;
  border: 1px solid #4a3c2a;
  border-radius: 12px;
  background: #110e0c;
  color: #e0d6c8;
  box-shadow:
    0 25px 50px rgba(0, 0, 0, 0.8),
    inset 0 0 20px rgba(0, 0, 0, 0.5);
}

.join-room-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 25px;
}

.join-room-header h2 {
  color: #e0d6c8;
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 0.08em;
}

.close-btn {
  width: 30px;
  height: 30px;
  display: grid;
  place-items: center;
  border: 1px solid #4a3c2a;
  border-radius: 50%;
  background: transparent;
  color: #d4b886;
  cursor: pointer;
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.close-btn:hover {
  border-color: #d4b886;
  box-shadow: 0 0 10px rgba(212, 184, 134, 0.2);
  transform: scale(1.05);
}

.form-group {
  display: grid;
  gap: 10px;
  margin-bottom: 25px;
}

.form-label {
  color: #8b7d6b;
  font-size: 13px;
}

.input-wrapper {
  position: relative;
}

.input-icon {
  position: absolute;
  left: 15px;
  top: 50%;
  transform: translateY(-50%);
  color: #5c4e3c;
  font-weight: 700;
}

.form-input {
  width: 100%;
  padding: 12px 15px 12px 40px;
  border: 1px solid #4a3c2a;
  border-radius: 6px;
  background: #0d0a08;
  color: #e0d6c8;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.form-input::placeholder {
  color: #5c4e3c;
}

.form-input:focus {
  border-color: #d4b886;
  box-shadow: inset 0 0 8px rgba(212, 184, 134, 0.1);
}

.divider {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 25px;
  color: #5c4e3c;
  font-size: 12px;
  text-align: center;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  border-bottom: 1px solid #2a2218;
}

.room-list-container {
  max-height: 220px;
  display: grid;
  gap: 12px;
  overflow-y: auto;
  padding-right: 5px;
  margin-bottom: 16px;
}

.room-list-container::-webkit-scrollbar {
  width: 4px;
}

.room-list-container::-webkit-scrollbar-thumb {
  border-radius: 2px;
  background: #4a3c2a;
}

.room-item {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 15px;
  border: 1px solid #4a3c2a;
  border-radius: 6px;
  background: #0d0a08;
  color: #e0d6c8;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.2s ease, background-color 0.2s ease, box-shadow 0.2s ease;
}

.room-item:hover {
  border-color: #6b573d;
  background: rgba(212, 184, 134, 0.03);
}

.room-item.selected {
  border-color: #d4b886;
  background: rgba(212, 184, 134, 0.08);
  box-shadow: inset 0 0 15px rgba(212, 184, 134, 0.1);
}

.room-info {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.radio-circle {
  width: 16px;
  height: 16px;
  flex: 0 0 16px;
  display: grid;
  place-items: center;
  border: 1px solid #5c4e3c;
  border-radius: 50%;
}

.room-item.selected .radio-circle {
  border-color: #d4b886;
}

.room-item.selected .radio-circle::after {
  content: '';
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #d4b886;
}

.room-name {
  min-width: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  font-size: 14px;
}

.tag-worldview {
  padding: 2px 8px;
  border: 1px solid #2a2218;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.5);
  color: #8b7d6b;
  font-size: 11px;
}

.room-item.selected .tag-worldview {
  border-color: #6b573d;
  color: #d4b886;
}

.room-meta {
  flex: 0 0 auto;
  display: grid;
  justify-items: end;
  gap: 4px;
}

.player-count {
  color: #8b7d6b;
  font-size: 12px;
}

.status {
  color: #4ade80;
  font-size: 11px;
}

.empty-state,
.join-error {
  color: #8b7d6b;
  font-size: 13px;
  text-align: center;
}

.join-error {
  margin-bottom: 14px;
  color: #ff9f7a;
}

.join-room-footer {
  display: flex;
  gap: 15px;
  margin-top: auto;
}

.btn {
  height: 48px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #4a3c2a;
  border-radius: 6px;
  background: transparent;
  color: #8b7d6b;
  cursor: pointer;
  transition: background-color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease, color 0.2s ease;
}

.btn-cancel {
  width: 72px;
}

.btn-cancel:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #e0d6c8;
}

.btn-primary {
  flex: 1;
  border-color: #6b573d;
  background: linear-gradient(180deg, rgba(212, 184, 134, 0.05), rgba(0, 0, 0, 0));
  color: #d4b886;
  letter-spacing: 0.08em;
}

.btn-primary:hover {
  border-color: #d4b886;
  background: rgba(212, 184, 134, 0.1);
  box-shadow: 0 0 15px rgba(212, 184, 134, 0.15);
}
</style>
