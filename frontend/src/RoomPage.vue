<script setup>
import { onBeforeUnmount, onMounted } from 'vue'
import roomPageUrl from './房间主页面.html?url'

defineProps({
  latestSession: {
    type: Object,
    default: null
  },
  currentUser: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['navigate', 'logout', 'back-button-hidden', 'exit-room'])

const handleRoomMessage = (event) => {
  if (event.origin !== window.location.origin) return
  if (event.data?.type === 'storyforge:exit-room') emit('exit-room')
}

onMounted(() => {
  window.addEventListener('message', handleRoomMessage)
})

onBeforeUnmount(() => {
  window.removeEventListener('message', handleRoomMessage)
})
</script>

<template>
  <div class="room-page">
    <iframe
      class="room-frame"
      :src="roomPageUrl"
      title="StoryForge 房间主页面"
    ></iframe>
  </div>
</template>

<style scoped>
.room-page {
  min-height: 100vh;
  background: #0b0a09;
  overflow: hidden;
}

.room-frame {
  display: block;
  width: 100%;
  height: 100vh;
  border: 0;
  background: #0b0a09;
}
</style>
