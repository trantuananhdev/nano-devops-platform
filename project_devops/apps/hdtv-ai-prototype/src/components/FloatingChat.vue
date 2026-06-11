<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { MessageSquareText, X, Send, Bot, Maximize2, Loader2, Sparkles, FileText } from '@lucide/vue'

const router = useRouter()
const route = useRoute()
const isOpen = ref(false)
const inputMsg = ref('')
const isTyping = ref(false)
const messages = ref([
  { id: 1, sender: 'AI', text: 'Xin chào! Tôi là Trợ lý AI HĐTV. Bạn cần tôi phân tích nhanh Tờ trình nào không?' }
])

const scrollToBottom = () => {
  nextTick(() => {
    const body = document.querySelector('.chat-body')
    if (body) body.scrollTop = body.scrollHeight
  })
}

const sendMsg = () => {
  if(!inputMsg.value) return
  messages.value.push({ id: Date.now(), sender: 'Me', text: inputMsg.value })
  inputMsg.value = ''
  isTyping.value = true
  scrollToBottom()
  
  // Simulate AI typing
  setTimeout(() => {
    messages.value.push({
      id: Date.now(),
      text: 'Đây là dữ liệu nội bộ bảo mật, vui lòng lưu ý quy định chia sẻ. Bạn cần xem chi tiết Quyết định không?',
      sender: 'AI'
    })
    isTyping.value = false
    scrollToBottom()
  }, 1500)
}

const openAdvancedChat = () => {
  isOpen.value = false
  router.push('/chat')
}
</script>

<template>
  <div class="floating-chat-container" v-if="route.path !== '/chat' && !route.path.startsWith('/workspace')">
    <!-- Chat Button -->
    <button class="chat-btn glass-panel" @click="isOpen = !isOpen" v-if="!isOpen">
      <MessageSquareText size="24" color="white" />
    </button>

    <!-- Chat Window -->
    <div class="chat-window glass-panel" v-if="isOpen">
      <div class="chat-header">
        <div class="header-title">
          <Bot size="18" />
          <span>Trợ lý AI EVN</span>
        </div>
        <div class="flex items-center gap-1">
          <button class="close-btn" @click="openAdvancedChat" title="Mở Chat Nâng cao">
            <Maximize2 size="16" />
          </button>
          <button class="close-btn" @click="isOpen = false"><X size="18"/></button>
        </div>
      </div>
      
      <div class="chat-body">
        <div v-for="msg in messages" :key="msg.id" class="chat-msg" :class="{ 'mine': msg.sender === 'Me' }">
          {{ msg.text }}
        </div>
        <div v-if="isTyping" class="chat-msg">
          <Loader2 class="animate-spin" size="16" />
        </div>
      </div>
      
      <div class="chat-footer">
        <input type="text" v-model="inputMsg" @keyup.enter="sendMsg" placeholder="Hỏi AI..." />
        <button @click="sendMsg"><Send size="16" /></button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.floating-chat-container {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  z-index: 100;
}
.chat-btn {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: var(--color-primary);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 15px rgba(0, 86, 179, 0.4);
  transition: transform 0.2s;
}
.chat-btn:hover { transform: scale(1.05); }

.chat-window {
  width: 350px;
  height: 500px;
  display: flex;
  flex-direction: column;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 10px 40px rgba(0,0,0,0.2);
}
.chat-header {
  background: var(--color-primary);
  color: white;
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header-title { display: flex; align-items: center; gap: 0.5rem; font-weight: 600; }
.close-btn { background: none; border: none; color: white; cursor: pointer; }

.chat-body {
  flex: 1;
  padding: 1rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  background: var(--color-bg-base);
}
.chat-msg {
  max-width: 80%;
  padding: 0.75rem 1rem;
  border-radius: 12px;
  font-size: 0.9rem;
  background: rgba(0, 86, 179, 0.1);
  color: var(--color-text-primary);
  align-self: flex-start;
  border-bottom-left-radius: 4px;
}
.chat-msg.mine {
  background: var(--color-primary);
  color: white;
  align-self: flex-end;
  border-bottom-left-radius: 12px;
  border-bottom-right-radius: 4px;
}

.chat-footer {
  padding: 1rem;
  background: var(--color-bg-panel);
  border-top: 1px solid var(--color-border);
  display: flex;
  gap: 0.5rem;
}
.chat-footer input {
  flex: 1;
  padding: 0.5rem 1rem;
  border: 1px solid var(--color-border);
  border-radius: 20px;
  outline: none;
  background: var(--color-bg-base);
  color: var(--color-text-primary);
}
.chat-footer button {
  background: var(--color-primary);
  color: white;
  border: none;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}
</style>
