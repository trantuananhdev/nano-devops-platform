<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { Bot, Send, Paperclip, Mic, Image as ImageIcon, Plus, Settings, MessageSquare, MoreVertical, FileText, Database, Copy, GitPullRequest, ThumbsUp, ThumbsDown } from '@lucide/vue'
import { useChatStore } from '../stores/chat'
import { createAppraisalSocket } from '../services/ws'

const chatStore = useChatStore()
const inputText = ref('')
const isTyping = ref(false)
const chatBodyRef = ref(null)
let wsHandle = null

const chatHistory = computed(() => chatStore.sessions)
const messages = computed(() => chatStore.messages)
const activeSession = computed(() => chatStore.sessions.find((s) => s.active))

// T-41: rAF-based scroll — smooth, non-blocking, cancels any pending frame
let _rafId = null
const scrollToBottom = () => {
  if (_rafId) cancelAnimationFrame(_rafId)
  _rafId = requestAnimationFrame(() => {
    if (chatBodyRef.value) {
      chatBodyRef.value.scrollTop = chatBodyRef.value.scrollHeight
    }
    _rafId = null
  })
}

// T-40: Infinite scroll upward — load older messages when near top.
// Debounced so that a fast scroll doesn't fire multiple concurrent fetches.
let _scrollDebounce = null
const onChatScroll = (e) => {
  if (e.target.scrollTop >= 80) return          // not near top — skip
  if (chatStore.loadingHistory) return           // already fetching
  clearTimeout(_scrollDebounce)
  _scrollDebounce = setTimeout(async () => {
    const prevScrollHeight = chatBodyRef.value?.scrollHeight ?? 0
    await chatStore.loadMoreMessages()
    // Restore scroll anchor after prepend so view doesn't jump to top
    requestAnimationFrame(() => {
      if (chatBodyRef.value) {
        chatBodyRef.value.scrollTop =
          chatBodyRef.value.scrollHeight - prevScrollHeight
      }
    })
  }, 150)
}

onMounted(async () => {
  await chatStore.loadSessions()
  if (chatStore.activeDossierId) {
    wsHandle = createAppraisalSocket(chatStore.activeDossierId, {
      onMessage: async (evt) => {
        if (evt.type === 'tool_result' || evt.type === 'completed') {
          chatStore.invalidateSession(chatStore.activeDossierId)
          await chatStore.selectSession(chatStore.activeDossierId)
          scrollToBottom()
        }
      },
    })
  }
})

onUnmounted(() => {
  wsHandle?.close()
  if (_rafId) cancelAnimationFrame(_rafId)
  clearTimeout(_scrollDebounce)
})

const selectSession = async (session) => {
  wsHandle?.close()
  await chatStore.selectSession(session.id)
  wsHandle = createAppraisalSocket(session.id, {
    onMessage: async (evt) => {
      if (evt.type === 'tool_result' || evt.type === 'completed') {
        chatStore.invalidateSession(session.id)
        await chatStore.selectSession(session.id)
        scrollToBottom()
      }
    },
  })
  scrollToBottom()
}

const sendMessage = async () => {
  if (!inputText.value.trim()) return
  isTyping.value = true
  const query = inputText.value
  inputText.value = ''
  scrollToBottom()
  await chatStore.sendAndAppraise(query)
  isTyping.value = false
  scrollToBottom()
}

const copyText = (text) => {
  navigator.clipboard.writeText(text)
}
</script>

<template>
  <div class="advanced-chat-layout">
    <!-- Chat Sidebar -->
    <aside class="chat-sidebar glass-panel">
      <div class="sidebar-header">
        <button class="btn btn-primary w-full flex items-center justify-center gap-2">
          <Plus size="16"/> Phân tích mới
        </button>
      </div>
      
      <div class="history-list">
        <div class="section-title">Lịch sử Gần đây</div>
        <div 
          v-for="session in chatHistory" 
          :key="session.id"
          class="history-item"
          :class="{ active: session.active }"
          @click="selectSession(session)"
        >
          <MessageSquare size="16" class="item-icon"/>
          <div class="item-content">
            <div class="item-title">{{ session.title }}</div>
            <div class="item-date">{{ session.date }}</div>
          </div>
          <button class="btn-icon"><MoreVertical size="14"/></button>
        </div>
      </div>
    </aside>

    <!-- Chat Main Area -->
    <main class="chat-main">
      <!-- Header -->
      <header class="chat-header glass-panel">
        <div class="flex items-center gap-3">
          <div class="ai-avatar">
            <Bot size="24"/>
          </div>
          <div>
            <h2 class="chat-title">Phiên thẩm định: {{ activeSession?.docNo || '—' }}</h2>
            <div class="flex items-center gap-2 text-xs text-muted">
              <span class="status-dot"></span> Gemma 4 qua LLM_BASE_URL (HTTP)
            </div>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button class="btn-icon"><Settings size="18"/></button>
        </div>
      </header>

      <!-- Messages Body -->
      <div class="chat-body" ref="chatBodyRef" @scroll="onChatScroll">
        <!-- T-40: Load older history indicator -->
        <div v-if="chatStore.loadingHistory" class="loading-history">
          <span>⏳ Đang tải lịch sử cũ hơn...</span>
        </div>
        <div class="welcome-banner glass-panel text-center">
          <Bot size="48" class="text-primary mx-auto mb-3 opacity-80"/>
          <h3>Trợ lý Phân tích Chuyên sâu</h3>
          <p class="text-muted text-sm max-w-md mx-auto mt-2">Hỗ trợ đọc file PDF, chạy Python Scripts, truy vấn cơ sở dữ liệu và gọi API nội bộ.</p>
        </div>

        <div 
          v-for="msg in messages" 
          :key="msg.id" 
          class="message-wrapper"
          :class="msg.sender === 'user' ? 'message-user' : 'message-ai'"
        >
          <div class="avatar-box" v-if="msg.sender === 'ai'">
            <Bot size="18"/>
          </div>
          
          <div class="message-content-wrapper">
            <div class="sender-name">{{ msg.sender === 'user' ? 'Lãnh đạo HĐTV' : 'Trợ lý AI' }} <span class="msg-time">{{ msg.time }}</span></div>
            
            <div v-if="msg.isTool" class="tool-execution glass-panel">
              <div class="tool-header flex items-center gap-2">
                <Database size="14" class="text-primary"/>
                <span class="font-medium text-sm">Đã gọi công cụ: {{ msg.toolName }}</span>
                <span class="badge-success ml-auto">Hoàn tất</span>
              </div>
              <div class="tool-body code-font">
                {{ msg.toolResult }}
              </div>
            </div>
            
            <div v-if="msg.text" class="message-bubble" :class="{ 'user-bubble': msg.sender === 'user', 'ai-bubble glass-panel': msg.sender === 'ai' }">
              {{ msg.text }}
            </div>
            
            <!-- Message Actions (For AI Only) -->
            <div v-if="msg.sender === 'ai'" class="message-actions">
              <button class="action-btn" title="Sao chép" @click="copyText(msg.text)"><Copy size="14"/></button>
              <button class="action-btn" title="Phản hồi Tốt"><ThumbsUp size="14"/></button>
              <button class="action-btn" title="Phản hồi Tệ"><ThumbsDown size="14"/></button>
              
              <div class="action-divider"></div>
              
              <button v-if="msg.hasActions" class="btn btn-outline-primary btn-sm action-pill">
                <GitPullRequest size="14"/> Bổ sung Ý kiến vào Quy trình
              </button>
            </div>
          </div>
        </div>

        <div v-if="isTyping" class="message-wrapper message-ai">
          <div class="avatar-box"><Bot size="18"/></div>
          <div class="typing-indicator glass-panel">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>

      <!-- Input Area -->
      <div class="chat-footer glass-panel">
        <div class="context-tags flex gap-2 mb-2">
          <span class="context-tag"><FileText size="12"/> {{ activeSession?.docNo || 'Chưa chọn' }}</span>
          <span class="context-tag outline flex items-center gap-1"><Plus size="12"/> Gắn thẻ dữ liệu</span>
        </div>
        
        <div class="input-wrapper">
          <button class="btn-icon attach-btn" title="Đính kèm (PDF, Word, Excel)"><Paperclip size="18"/></button>
          <button class="btn-icon attach-btn" title="Chèn Ảnh"><ImageIcon size="18"/></button>
          
          <textarea 
            v-model="inputText" 
            class="chat-input" 
            placeholder="Nhập câu lệnh chuyên sâu, yêu cầu phân tích số liệu hoặc gõ @ để gọi Tool..."
            @keyup.enter.prevent="sendMessage"
            rows="1"
          ></textarea>
          
          <button class="btn-icon mic-btn"><Mic size="18"/></button>
          <button class="btn btn-primary send-btn" @click="sendMessage">
            <Send size="16"/> Gửi
          </button>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.advanced-chat-layout {
  display: flex;
  height: 100vh;
  width: 100%;
  overflow: hidden;
}

/* Sidebar */
.chat-sidebar {
  width: 280px;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--color-border);
  border-radius: 0;
  border-top: none; border-bottom: none; border-left: none;
}
.sidebar-header { padding: 1.5rem 1rem; border-bottom: 1px solid var(--color-border); }
.w-full { width: 100%; }

.history-list { flex: 1; overflow-y: auto; padding: 1rem 0; }
.section-title { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; color: var(--color-text-secondary); padding: 0 1rem; margin-bottom: 0.5rem; font-weight: 600; }
.history-item { display: flex; align-items: center; gap: 0.75rem; padding: 0.75rem 1rem; cursor: pointer; transition: all 0.2s; border-left: 3px solid transparent; }
.history-item:hover { background: rgba(0,0,0,0.03); }
[data-theme='dark'] .history-item:hover { background: rgba(255,255,255,0.05); }
.history-item.active { background: rgba(0, 86, 179, 0.05); border-left-color: var(--color-primary); }
[data-theme='dark'] .history-item.active { background: rgba(59, 130, 246, 0.1); }
.item-icon { color: var(--color-text-secondary); flex-shrink: 0; }
.history-item.active .item-icon { color: var(--color-primary); }
.item-content { flex: 1; overflow: hidden; }
.item-title { font-size: 0.9rem; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.item-date { font-size: 0.75rem; color: var(--color-text-secondary); }

/* Main Area */
.chat-main { flex: 1; display: flex; flex-direction: column; background: var(--color-bg-base); position: relative; }

.chat-header {
  padding: 1rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-radius: 0; border-top: none; border-left: none; border-right: none;
  z-index: 10;
}
.ai-avatar { width: 40px; height: 40px; background: linear-gradient(135deg, var(--color-primary), #2563eb); color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
.chat-title { font-size: 1.1rem; font-weight: 600; margin: 0; }
.status-dot { width: 8px; height: 8px; background: var(--color-success); border-radius: 50%; box-shadow: 0 0 5px var(--color-success); }
.text-muted { color: var(--color-text-secondary); }

/* Chat Body */
.chat-body { flex: 1; overflow-y: auto; padding: 2rem; display: flex; flex-direction: column; gap: 1.5rem; }
.loading-history {
  text-align: center;
  font-size: 0.82rem;
  color: var(--color-text-secondary);
  padding: 0.5rem;
  animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
.welcome-banner { margin: 2rem auto; padding: 2rem; max-width: 500px; border-radius: 16px; border: 1px dashed var(--color-border); }
.mx-auto { margin-left: auto; margin-right: auto; }
.mb-3 { margin-bottom: 0.75rem; }
.mt-2 { margin-top: 0.5rem; }
.max-w-md { max-width: 28rem; }

.message-wrapper { display: flex; gap: 1rem; max-width: 85%; }
.message-user { align-self: flex-end; flex-direction: row-reverse; }
.message-ai { align-self: flex-start; }

.avatar-box { width: 32px; height: 32px; background: var(--color-primary); color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 1.25rem; }
.message-content-wrapper { display: flex; flex-direction: column; gap: 0.25rem; }
.message-user .message-content-wrapper { align-items: flex-end; }

.sender-name { font-size: 0.8rem; font-weight: 600; color: var(--color-text-secondary); margin-left: 0.25rem; }
.message-user .sender-name { margin-left: 0; margin-right: 0.25rem; }
.msg-time { font-weight: 400; font-size: 0.7rem; opacity: 0.7; margin-left: 0.5rem; }

.message-bubble { padding: 1rem 1.25rem; border-radius: 16px; font-size: 0.95rem; line-height: 1.5; }
.user-bubble { background: var(--color-primary); color: white; border-bottom-right-radius: 4px; box-shadow: 0 4px 10px rgba(0, 86, 179, 0.2); }
.ai-bubble { border-bottom-left-radius: 4px; border: 1px solid var(--color-border); }

/* Message Actions */
.message-actions { display: flex; align-items: center; gap: 0.5rem; margin-top: 0.25rem; margin-left: 0.5rem; opacity: 0.7; transition: opacity 0.2s; }
.message-wrapper:hover .message-actions { opacity: 1; }
.action-btn { background: none; border: none; color: var(--color-text-secondary); cursor: pointer; padding: 0.25rem; border-radius: 4px; display: flex; align-items: center; justify-content: center; transition: all 0.2s; }
.action-btn:hover { background: rgba(0,0,0,0.05); color: var(--color-primary); }
[data-theme='dark'] .action-btn:hover { background: rgba(255,255,255,0.1); }
.action-divider { width: 1px; height: 14px; background: var(--color-border); margin: 0 0.25rem; }
.action-pill { border-radius: 20px; padding: 0.2rem 0.75rem; font-size: 0.75rem; display: flex; align-items: center; gap: 0.25rem; background: transparent; border: 1px solid var(--color-primary); color: var(--color-primary); cursor: pointer; font-weight: 500; transition: all 0.2s; }
.action-pill:hover { background: rgba(0, 86, 179, 0.1); }
[data-theme='dark'] .action-pill { border-color: var(--color-primary-light); color: var(--color-primary-light); }
[data-theme='dark'] .action-pill:hover { background: rgba(59, 130, 246, 0.15); }

/* Tool Execution */
.tool-execution { border-radius: 12px; border: 1px solid var(--color-primary); overflow: hidden; margin-bottom: 0.5rem; max-width: 600px; }
.tool-header { background: rgba(0, 86, 179, 0.05); padding: 0.5rem 1rem; border-bottom: 1px solid var(--color-border); }
[data-theme='dark'] .tool-header { background: rgba(59, 130, 246, 0.1); }
.badge-success { background: rgba(16, 185, 129, 0.15); color: var(--color-success); padding: 0.1rem 0.5rem; border-radius: 12px; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; }
.tool-body { padding: 1rem; font-size: 0.85rem; color: var(--color-text-primary); white-space: pre-wrap; }
.code-font { font-family: 'Consolas', 'Courier New', Courier, monospace; }

/* Typing Indicator */
.typing-indicator { padding: 1rem; border-radius: 16px; border-bottom-left-radius: 4px; display: flex; gap: 0.4rem; align-items: center; border: 1px solid var(--color-border); }
.typing-indicator span { width: 6px; height: 6px; background: var(--color-primary); border-radius: 50%; animation: typing 1.4s infinite ease-in-out both; }
.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
@keyframes typing { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }

/* Footer */
.chat-footer { padding: 1rem 1.5rem; border-radius: 0; border-bottom: none; border-left: none; border-right: none; }
.context-tags { margin-bottom: 0.75rem; }
.context-tag { font-size: 0.75rem; font-weight: 500; padding: 0.3rem 0.6rem; border-radius: 12px; background: rgba(0, 86, 179, 0.1); color: var(--color-primary); display: flex; align-items: center; gap: 0.4rem; cursor: pointer; }
.context-tag.outline { background: transparent; border: 1px dashed var(--color-border); color: var(--color-text-secondary); }
.context-tag.outline:hover { border-color: var(--color-primary); color: var(--color-primary); }

.input-wrapper { display: flex; align-items: center; gap: 0.5rem; background: var(--color-bg-base); border: 1px solid var(--color-border); border-radius: 24px; padding: 0.5rem 0.5rem 0.5rem 1rem; transition: border-color 0.2s; box-shadow: 0 2px 10px rgba(0,0,0,0.02); }
.input-wrapper:focus-within { border-color: var(--color-primary); box-shadow: 0 4px 15px rgba(0, 86, 179, 0.1); }
.attach-btn { color: var(--color-text-secondary); margin-right: 0.25rem; }
.attach-btn:hover { color: var(--color-primary); }
.chat-input { flex: 1; border: none; background: transparent; outline: none; resize: none; font-family: inherit; color: var(--color-text-primary); font-size: 0.95rem; max-height: 120px; overflow-y: auto; padding-top: 0.3rem; }
.mic-btn { color: var(--color-text-secondary); margin-right: 0.5rem; }
.mic-btn:hover { color: var(--color-danger); }
.send-btn { border-radius: 20px; padding: 0.5rem 1rem; display: flex; gap: 0.5rem; }
</style>
