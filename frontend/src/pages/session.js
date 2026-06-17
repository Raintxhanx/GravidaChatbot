import { navigateTo } from '../main.js';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export const SessionPage = {
  render: () => {
    return `
      <div class="w-full flex flex-col items-center justify-between h-[calc(100vh-80px)] mt-4 md:mt-[80px] pb-4 relative max-w-[994px] mx-auto">
        
        <div class="w-full bg-white/80 backdrop-blur-xl rounded-t-[24px] shadow-sm border border-white p-4 flex flex-col z-30 shrink-0 transition-all">
          
          <div class="flex items-center justify-between w-full">
            <div class="flex items-center gap-3">
              <button id="back-btn" class="w-8 h-8 flex items-center justify-center rounded-full bg-gray-50 hover:bg-pink-50 text-gray-600 hover:text-[#FE81D4] transition-colors border border-gray-100">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7" /></svg>
              </button>
              <div>
                <h2 id="chat-title" class="text-[16px] font-bold text-gray-800 leading-tight">Sesi Konsultasi Baru</h2>
                <p class="text-[11px] text-gray-400 font-medium" id="chat-status">Ketik pesan untuk memulai obrolan</p>
              </div>
            </div>
            
            <button id="detail-toggle-btn" class="flex items-center gap-1.5 px-3 py-1.5 bg-gray-50 hover:bg-pink-50 text-gray-600 hover:text-[#FE81D4] rounded-lg text-[11px] font-bold transition-all border border-gray-200 shadow-sm">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              <span>Detail Chat</span>
            </button>
          </div>

          <div id="detail-section" class="hidden w-full border-t border-gray-100 mt-4 pt-4 flex-col md:flex-row gap-6 animate-fade-in origin-top">
            
            <div class="flex-1 flex flex-col gap-3">
              <div>
                <p class="text-[10px] text-[#FE81D4] font-bold uppercase tracking-wider mb-0.5">Judul Sesi</p>
                <p id="detail-title" class="text-sm font-bold text-gray-800 leading-snug">-</p>
              </div>
              <div>
                <p class="text-[10px] text-[#FE81D4] font-bold uppercase tracking-wider mb-0.5">Rangkuman / Deskripsi</p>
                <p id="detail-desc" class="text-xs text-gray-600 leading-relaxed text-justify">-</p>
              </div>
              <button id="btn-create-summary" class="self-start mt-1 px-3 py-1.5 bg-pink-50 hover:bg-[#FE81D4] text-[#FE81D4] hover:text-white rounded-lg text-[11px] font-bold transition-colors border border-pink-100 shadow-sm flex items-center gap-1.5">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                Buat Ringkasan
              </button>
            </div>

            <div class="flex-1 flex flex-col gap-2 border-l-0 md:border-l md:border-gray-100 md:pl-6">
              <p class="text-[10px] text-[#FE81D4] font-bold uppercase tracking-wider mb-0.5">Cari Pesan Sebelumnya</p>
              <div class="flex gap-2">
                <input type="text" id="search-msg-input" placeholder="Ketik kata kunci (misal: Dokter)..." class="flex-1 bg-gray-50 border border-gray-200 rounded-lg px-3 py-1.5 text-xs focus:border-[#FE81D4] focus:outline-none transition-colors">
                <button id="btn-search-msg" class="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-600 rounded-lg text-xs font-bold transition-colors border border-gray-200">Cari</button>
              </div>
              <div id="search-results-container" class="max-h-[140px] overflow-y-auto flex flex-col gap-2 pr-1 mt-1 scroll-smooth hidden">
                </div>
            </div>

          </div>
        </div>

        <div id="chat-box" class="flex-1 w-full bg-white/40 backdrop-blur-sm overflow-y-auto p-4 md:p-6 flex flex-col gap-4 border-l border-r border-white/50 relative scroll-smooth">
          <div id="load-more-container" class="w-full text-center hidden mb-2">
            <button id="load-more-btn" class="text-[11px] font-bold bg-white px-3 py-1.5 rounded-full text-gray-500 shadow-sm border border-gray-100 hover:text-[#FE81D4]">Muat pesan sebelumnya</button>
          </div>
          
          <div id="messages-container" class="flex flex-col gap-4 w-full pb-4"></div>
          
          <div id="typing-indicator" class="hidden self-start bg-white border border-gray-100 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm flex items-center gap-1.5 mt-2">
            <div class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"></div>
            <div class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.15s"></div>
            <div class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.3s"></div>
          </div>
        </div>

        <div class="w-full bg-white/80 backdrop-blur-xl rounded-b-[24px] shadow-md border border-white p-3 md:p-4 shrink-0 flex items-end gap-2 z-20">
          <textarea id="message-input" rows="1" placeholder="Tanyakan keluhan Anda di sini..." class="w-full bg-gray-50 border border-gray-200 rounded-[16px] px-4 py-3 text-sm text-gray-700 focus:outline-none focus:border-[#FE81D4] focus:ring-1 focus:ring-[#FE81D4] resize-none overflow-hidden min-h-[46px] max-h-[120px] transition-all"></textarea>
          
          <button id="send-btn" disabled class="w-[46px] h-[46px] shrink-0 bg-gradient-to-r from-[#FAACBF] to-[#FE81D4] hover:scale-105 active:scale-95 text-white rounded-[14px] flex items-center justify-center shadow-md shadow-pink-200 transition-all disabled:opacity-50 disabled:pointer-events-none disabled:scale-100">
            <svg class="w-5 h-5 ml-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
          </button>
        </div>

      </div>
    `;
  },

    afterrender: async () => {
        const token = localStorage.getItem('access_token');
        if (!token) {
            navigateTo('/login');
            return;
        }

        const pathParts = window.location.pathname.split('/');
        let chatId = pathParts[pathParts.length - 1];
        
        // Elemen DOM
        const chatStatus = document.getElementById('chat-status');
        const chatTitle = document.getElementById('chat-title');
        const messagesContainer = document.getElementById('messages-container');
        const chatBox = document.getElementById('chat-box');
        const messageInput = document.getElementById('message-input');
        const sendBtn = document.getElementById('send-btn');
        const typingIndicator = document.getElementById('typing-indicator');
        const backBtn = document.getElementById('back-btn');
        const loadMoreContainer = document.getElementById('load-more-container');
        const loadMoreBtn = document.getElementById('load-more-btn');
        
        // Header & Expandable Detail
        const detailToggleBtn = document.getElementById('detail-toggle-btn');
        const detailSection = document.getElementById('detail-section');
        const detailTitleEl = document.getElementById('detail-title');
        const detailDescEl = document.getElementById('detail-desc');
        const btnCreateSummary = document.getElementById('btn-create-summary');
        
        // Search elements
        const searchInput = document.getElementById('search-msg-input');
        const btnSearch = document.getElementById('btn-search-msg');

         // State
         let isProcessing = false;
        let nextCursor = null;
        let originalChatHTML = ''; // Simpan history chat asli sebelum difilter oleh pencarian
        let searchBeforeMessageId = null; // Menyimpan cursor ID pesan tertua dari batch saat ini
        let accumulatedSearchMessages = []; // Menampung semua hasil pesan yang berhasil di-load
        let hasMoreSearch = true; // Menandai apakah masih ada halaman pencarian berikutnya
        let currentSearchKeyword = '';// Menyimpan keyword pencarian yang aktif
        const SEARCH_LIMIT = 3;// Sesuaikan limit per page pencarian Anda

        // --- UTILITAS ---
        const formatText = (text) => text ? text.replace(/\n/g, '<br>') : '';
        const scrollToBottom = () => { chatBox.scrollTop = chatBox.scrollHeight; };

        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
            sendBtn.disabled = this.value.trim() === '';
        });

        backBtn.addEventListener('click', () => navigateTo('/history'));

        // Toggle Detail Section Expand
        detailToggleBtn.addEventListener('click', () => {
            detailSection.classList.toggle('hidden');
            detailSection.classList.toggle('flex');
        });

        // --- GELEMBUNG PESAN ---
        const appendMessage = (msg, prepend = false) => {
            if (msg.role === 'system') return;

            // Hapus tombol regenerasi dari pesan asisten sebelumnya jika kita menambah pesan baru ke bawah (bukan prepend/load history)
            if (!prepend && msg.role === 'user') {
                const lastRegenBtn = messagesContainer.querySelector('.regenerate-btn');
                if (lastRegenBtn) lastRegenBtn.remove();
            }

            const isUser = msg.role === 'user';
            const bubbleHtml = `
                <div class="max-w-[85%] md:max-w-[75%] flex flex-col ${isUser ? 'self-end items-end' : 'self-start items-start'} group mb-1" id="msg-${msg.id}">
                    <div class="px-4 py-3 rounded-2xl text-[14px] leading-relaxed shadow-sm 
                        ${isUser ? 'bg-[#FE81D4] text-white rounded-tr-sm user-bubble-content' : 'bg-white border border-gray-100 text-gray-700 rounded-tl-sm'}">
                        ${formatText(msg.content)}
                    </div>
                    
                    ${!isUser && !prepend ? `
                        <button class="regenerate-btn hidden group-hover:flex items-center gap-1 mt-1 text-[10px] font-bold text-gray-400 hover:text-[#FE81D4] transition-colors" data-msg-id="${msg.id}">
                            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
                            Edit & Regenerasi
                        </button>
                    ` : ''}
                </div>
            `;

            if (prepend) {
                messagesContainer.insertAdjacentHTML('afterbegin', bubbleHtml);
            } else {
                // Jika asisten merespon, pastikan hapus tombol regenerasi yang mungkin menggantung sebelum menaruh yang baru
                if (msg.role === 'assistant') {
                    const lastRegenBtn = messagesContainer.querySelector('.regenerate-btn');
                    if (lastRegenBtn) lastRegenBtn.remove();
                }

                messagesContainer.insertAdjacentHTML('beforeend', bubbleHtml);
                scrollToBottom();
            }
        };

        // --- EVENT DELEGATION UNTUK TOMBOL REGENERATE ---
        // (Menggantikan attachRegenerateEvent yang boros resource)
        messagesContainer.addEventListener('click', (e) => {
            const btn = e.target.closest('.regenerate-btn');
            if (btn) regenerateMessage(btn.dataset.msgId, btn.closest('.group'));
        });

        // --- API HANDLERS ---

        // 1. Ambil Detail Sesi Chat
        const fetchChatDetails = async () => {
            if (chatId === 'new') return;
            try {
                const res = await fetch(`${API_URL}/api/v1/chats/${chatId}`, {
                    method: 'GET',
                    headers: { 'Authorization': `Bearer ${token}`, 'Accept': 'application/json' }
                });
                const result = await res.json();
                
                if (res.ok && result.success) {
                    const detail = result.data;
                    chatTitle.textContent = detail.title || 'Sesi Konsultasi';
                    detailTitleEl.textContent = detail.title || '-';
                    detailDescEl.textContent = detail.description || 'Belum ada deskripsi untuk sesi ini.';
                }
            } catch (err) {
                console.error('Gagal mengambil detail obrolan', err);
            }
        };

        // 2. Ambil Riwayat Obrolan
        const fetchHistory = async (loadMore = false) => {
            if (chatId === 'new') return;
            
            try {
                let url = `${API_URL}/api/v1/chats/${chatId}/messages?limit=10`;
                if (loadMore && nextCursor) url += `&before_message_id=${nextCursor}`;

                const res = await fetch(url, {
                    method: 'GET',
                    headers: { 'Authorization': `Bearer ${token}`, 'Accept': 'application/json' }
                });
                const result = await res.json();

                if (res.ok && result.success) {
                    const items = result.data.items || [];
                    let sortedItems = items.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));

                    const oldScrollHeight = chatBox.scrollHeight;

                    if (!loadMore) {
                        messagesContainer.innerHTML = ''; 
                        sortedItems.forEach(msg => appendMessage(msg, false));
                    } else {
                        sortedItems.reverse().forEach(msg => appendMessage(msg, true));
                    }

                    if (loadMore) {
                        chatBox.scrollTop = chatBox.scrollHeight - oldScrollHeight;
                    } else {
                        scrollToBottom();
                    }

                    nextCursor = result.data.next_cursor;
                    if (result.data.has_more) {
                        loadMoreContainer.classList.remove('hidden');
                    } else {
                        loadMoreContainer.classList.add('hidden');
                    }

                    chatStatus.textContent = 'Aktif';
                }
            } catch (err) {
                chatStatus.textContent = 'Gagal memuat pesan';
            }
        };

        loadMoreBtn.addEventListener('click', () => fetchHistory(true));

        // 3. Kirim Pesan Baru
        const sendMessage = async () => {
            const text = messageInput.value.trim();
            if (!text || isProcessing) return;

            messageInput.value = '';
            messageInput.style.height = 'auto';
            sendBtn.disabled = true;

            const tempUserId = `temp_${Date.now()}`;
            appendMessage({ id: tempUserId, role: 'user', content: text });
            
            isProcessing = true;
            typingIndicator.classList.remove('hidden');
            scrollToBottom();

            try {
                if (chatId === 'new') {
                // === LOGIKA UNTUK CHAT BARU (STREAMING SSE) ===
                chatStatus.textContent = 'Sedang membuat sesi...';
                
                const res = await fetch(`${API_URL}/api/v1/chats`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                        'Accept': 'text/event-stream' // Sesuaikan dengan backend
                    },
                    body: JSON.stringify({ query: text })
                });
                
                typingIndicator.classList.add('hidden');

                if (res.ok) {
                    // Buat bubble assistant kosong di awal
                    const streamMsgId = `stream_${Date.now()}`;
                    appendMessage({ id: streamMsgId, role: 'assistant', content: '' });
                    const contentContainer = document.querySelector(`#msg-${streamMsgId} .bg-white`);
                    
                    // Mulai membaca stream
                    const reader = res.body.getReader();
                    const decoder = new TextDecoder("utf-8");
                    let fullText = "";
                    
                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;
                        
                        const chunk = decoder.decode(value, { stream: true });
                        const lines = chunk.split('\n');
                        
                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                const dataStr = line.substring(6).trim();
                                
                                if (dataStr === '[DONE]') break;
                                if (!dataStr) continue;
                                
                                try {
                                    const parsed = JSON.parse(dataStr);
                                    
                                    // 1. Tangkap metadata di awal stream untuk update URL & Info Sesi
                                    if (parsed.type === 'metadata') {
                                        chatId = parsed.chat_id;
                                        window.history.replaceState(null, '', `/session/${chatId}`);
                                        chatStatus.textContent = 'Aktif';
                                        fetchChatDetails(); // Refresh detail UI
                                    } 
                                    // 2. Tangkap token LLM dan render real-time
                                    else if (parsed.type === 'token') {
                                        fullText += parsed.content;
                                        contentContainer.innerHTML = formatText(fullText);
                                        scrollToBottom();
                                    }
                                    // 3. Tangani error jika terjadi kegagalan sistem
                                    else if (parsed.error || parsed.success === false) {
                                        fullText += `\n[Error: ${parsed.error || parsed.message}]`;
                                        contentContainer.innerHTML = formatText(fullText);
                                        scrollToBottom();
                                    }
                                } catch (e) {
                                    console.error("Gagal parsing token", e);
                                }
                            }
                        }
                    }
                } else {
                    // Jika status HTTP tidak OK (misal 422 Guardrail Abort)
                    const errData = await res.json().catch(() => ({}));
                    appendMessage({ 
                        id: 'err', 
                        role: 'assistant', 
                        content: errData.message || 'Maaf, gagal memulai obrolan.' 
                    });
                }

                } else {
                    // === LOGIKA UNTUK CHAT LANJUTAN (STREAMING SSE) ===
                    const res = await fetch(`${API_URL}/api/v1/chats/${chatId}/messages`, {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${token}`,
                            'Content-Type': 'application/json',
                            'Accept': 'text/event-stream' // Gunakan Stream
                        },
                        body: JSON.stringify({ query: text })
                    });
                    
                    typingIndicator.classList.add('hidden');

                    if (res.ok) {
                        // Buat bubble assistant kosong di awal
                        const streamMsgId = `stream_${Date.now()}`;
                        appendMessage({ id: streamMsgId, role: 'assistant', content: '' });
                        const contentContainer = document.querySelector(`#msg-${streamMsgId} .bg-white`);
                        
                        // Mulai membaca stream
                        const reader = res.body.getReader();
                        const decoder = new TextDecoder("utf-8");
                        let fullText = "";
                        
                        while (true) {
                            const { done, value } = await reader.read();
                            if (done) break;
                            
                            const chunk = decoder.decode(value, { stream: true });
                            const lines = chunk.split('\n');
                            
                            for (const line of lines) {
                                if (line.startsWith('data: ')) {
                                    const dataStr = line.substring(6).trim();
                                    
                                    if (dataStr === '[DONE]') break;
                                    if (!dataStr) continue;
                                    
                                    try {
                                        const parsed = JSON.parse(dataStr);
                                        if (parsed.error) {
                                            fullText += `\n[Error: ${parsed.error}]`;
                                        } else if (parsed.token) {
                                            fullText += parsed.token;
                                        }
                                        // Update UI secara realtime
                                        contentContainer.innerHTML = formatText(fullText);
                                        scrollToBottom();
                                    } catch (e) {
                                        console.error("Gagal parsing token", e);
                                    }
                                }
                            }
                        }
                    } else {
                        appendMessage({ id: 'err', role: 'assistant', content: 'Gagal mengirim pesan.' });
                    }
                }
            } catch (err) {
                console.error(err);
                typingIndicator.classList.add('hidden');
                appendMessage({ id: 'err', role: 'assistant', content: 'Koneksi terputus.' });
            } finally {
                isProcessing = false;
                messageInput.focus();
            }
        };

        // 4. Regenerasi (Edit Pesan Terakhir & Refresh Jawaban)
        const regenerateMessage = async (oldMsgId, assistantMsgElement) => {
            if (isProcessing || chatId === 'new') return;
            
            // Cari bubble user tepat di atas pesan assistant ini
            const userMsgElement = assistantMsgElement.previousElementSibling;
            let oldUserText = "";
            
            if (userMsgElement && userMsgElement.querySelector('.user-bubble-content')) {
                // Ambil teks asli untuk ditaruh di dalam prompt
                oldUserText = userMsgElement.querySelector('.user-bubble-content').innerText.trim();
            }

            const promptQuery = prompt(
                "Edit pesan terakhir Anda untuk menghasilkan jawaban baru:", 
                oldUserText
            );
            
            // Batal jika input kosong / di-cancel
            if (!promptQuery) return; 

            isProcessing = true;
            typingIndicator.classList.remove('hidden');
            scrollToBottom();

            try {
                const res = await fetch(`${API_URL}/api/v1/chats/${chatId}/messages/regenerate`, {
                    method: 'POST',
                    headers: { 
                        'Authorization': `Bearer ${token}`, 
                        'Content-Type': 'application/json',
                        'Accept': 'text/event-stream' // Ubah accept ke stream
                    },
                    body: JSON.stringify({ query: promptQuery })
                });

                typingIndicator.classList.add('hidden');
                
                if (res.ok) {
                    // 1. Update UI teks pesan user dengan teks hasil editan
                    if (userMsgElement && userMsgElement.querySelector('.user-bubble-content')) {
                        userMsgElement.querySelector('.user-bubble-content').innerHTML = formatText(promptQuery);
                    }
                    
                    // 2. Hapus bubble pesan assistant lama dari DOM
                    if (assistantMsgElement) assistantMsgElement.remove();
                    
                    // 3. Buat bubble assistant baru yang kosong
                    const regenMsgId = `regen_${Date.now()}`;
                    appendMessage({ id: regenMsgId, role: 'assistant', content: '' });
                    const contentContainer = document.querySelector(`#msg-${regenMsgId} .bg-white`);
                    
                    // 4. Mulai membaca stream
                    const reader = res.body.getReader();
                    const decoder = new TextDecoder("utf-8");
                    let fullText = "";
                    
                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;
                        
                        const chunk = decoder.decode(value, { stream: true });
                        const lines = chunk.split('\n');
                        
                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                const dataStr = line.substring(6).trim();
                                
                                if (dataStr === '[DONE]') break;
                                if (!dataStr) continue;
                                
                                try {
                                    const parsed = JSON.parse(dataStr);
                                    if (parsed.error) {
                                        fullText += `\n[Error: ${parsed.error}]`;
                                    } else if (parsed.token) {
                                        fullText += parsed.token;
                                    }
                                    // Update UI secara realtime
                                    contentContainer.innerHTML = formatText(fullText);
                                    scrollToBottom();
                                } catch (e) {
                                    console.error("Gagal parsing token regenerasi", e);
                                }
                            }
                        }
                    }
                } else {
                    alert('Gagal meregenerasi jawaban.');
                }
            } catch (err) {
                typingIndicator.classList.add('hidden');
                alert('Koneksi terputus saat regenerasi.');
            } finally {
                isProcessing = false;
            }
        };

        // 5. Trigger Summary Update Manual (Dari Tombol Detail Chat)
        btnCreateSummary.addEventListener('click', async () => {
            if (chatId === 'new') return alert('Sesi belum dimulai. Silakan kirim pesan pertama Anda.');
            
            const originalText = btnCreateSummary.innerHTML;
            btnCreateSummary.innerHTML = 'Sedang membuat...';
            btnCreateSummary.disabled = true;

            try {
                const res = await fetch(`${API_URL}/api/v1/chats/${chatId}/summary`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const result = await res.json();
                
                if (res.ok) {
                    await fetchChatDetails(); // Refresh detail untuk memuat ringkasan terbaru
                } else {
                    alert('Gagal membuat ringkasan.');
                }
            } catch (e) {
                console.error(e);
                alert('Koneksi terputus.');
            } finally {
                btnCreateSummary.innerHTML = originalText;
                btnCreateSummary.disabled = false;
            }
        });

        // 6. Pencarian Pesan Dalam Detail Expand
        const performSearch = async (isLoadMore = false) => {
            if (chatId === 'new') return;

            // Jika pencarian baru (bukan load more)
            if (!isLoadMore) {
                currentSearchKeyword = searchInput.value.trim();
                if (!currentSearchKeyword) return;

                // Reset state pencarian
                searchBeforeMessageId = null;
                accumulatedSearchMessages = [];
                hasMoreSearch = true;

                // KUNCI: Nonaktifkan input chat agar user tidak mengirim pesan saat mode search
                messageInput.disabled = true;
                sendBtn.disabled = true;

                // Sembunyikan tombol muat pesan chat asli
                loadMoreContainer.classList.add('hidden');
                
                // Simpan isi chatbox asli jika belum pernah disimpan
                if (!originalChatHTML) {
                    originalChatHTML = messagesContainer.innerHTML;
                }

                messagesContainer.innerHTML = '<p class="text-xs text-gray-400 italic text-center py-8 animate-pulse">Mencari pesan di database...</p>';
            } else {
                // State UI saat Load More
                const loadMoreBtn = document.getElementById('btn-load-more-search');
                if (loadMoreBtn) {
                    loadMoreBtn.innerText = 'Memuat...';
                    loadMoreBtn.disabled = true;
                }
            }

            try {
                // Konstruksi URL
                let url = `${API_URL}/api/v1/chats/${chatId}/messages?search=${encodeURIComponent(currentSearchKeyword)}&limit=${SEARCH_LIMIT}`;
                if (isLoadMore && searchBeforeMessageId) {
                    url += `&before_message_id=${searchBeforeMessageId}`;
                }

                const res = await fetch(url, {
                    method: 'GET',
                    headers: { 
                        'Authorization': `Bearer ${token}`, 
                        'Accept': 'application/json' 
                    }
                });
                const result = await res.json();

                if (res.ok && result.success) {
                    const items = result.data.items || [];

                    // Jika benar-benar tidak ada data
                    if (items.length === 0 && !isLoadMore) {
                        messagesContainer.innerHTML = `
                            <div class="text-center py-8 flex flex-col items-center">
                                <p class="text-sm text-gray-500 italic mb-4">Pesan dengan kata kunci "<strong>${currentSearchKeyword}</strong>" tidak ditemukan.</p>
                                <button id="btn-reset-search" class="px-4 py-2 bg-pink-50 hover:bg-pink-100 text-[#FE81D4] rounded-xl text-xs font-bold transition-colors border border-pink-200">Kembali ke Chat</button>
                            </div>
                        `;
                        document.getElementById('btn-reset-search').addEventListener('click', resetSearch);
                        return;
                    }

                    // Cek paginasi
                    searchBeforeMessageId = result.data.next_cursor || null;
                    hasMoreSearch = result.data.has_more ?? false;

                    // Gabungkan dan urutkan hasil
                    accumulatedSearchMessages = [...accumulatedSearchMessages, ...items];
                    const sortedItems = [...accumulatedSearchMessages].sort((a, b) => {
                        const numA = parseInt(a.id.split('_').pop());
                        const numB = parseInt(b.id.split('_').pop());
                        return numA - numB;
                    });

                    // REFAKTOR UI: Render Container Khusus Search agar rapi dan tidak melompat
                    messagesContainer.innerHTML = `
                        <div class="w-full text-center bg-pink-50 border border-pink-100 rounded-xl p-3 text-xs text-[#FE81D4] font-medium flex items-center justify-between shadow-sm">
                            <span>Ditemukan ${sortedItems.length} hasil untuk "<strong>${currentSearchKeyword}</strong>"</span>
                            <button id="btn-reset-search" class="bg-white hover:bg-pink-100 px-3 py-1.5 rounded-lg shadow-sm font-bold transition-colors border border-pink-100">Tampilkan Semua</button>
                        </div>
                        

                        ${hasMoreSearch ? `
                        <div class="text-center mb-4 mt-2">
                            <button id="btn-load-more-search" class="px-4 py-1.5 bg-gray-50 hover:bg-pink-50 text-gray-600 hover:text-[#FE81D4] rounded-full text-[11px] font-bold transition-colors border border-gray-200 shadow-sm">
                                Muat Pesan Lebih Lama
                            </button>
                        </div>
                        ` : ''}
                        
                        <div id="search-messages-wrapper" class="flex flex-col gap-4 w-full pb-4"></div>
                    `;

                    // REFAKTOR RENDER: Render manual tanpa memanggil appendMessage() agar tidak memicu scrollToBottom() berulang kali
                    const searchWrapper = document.getElementById('search-messages-wrapper');
                    sortedItems.forEach(msg => {
                        const isUser = msg.role === 'user';
                        const bubbleHtml = `
                            <div class="max-w-[85%] md:max-w-[75%] flex flex-col ${isUser ? 'self-end items-end' : 'self-start items-start'} mb-1">
                                <div class="px-4 py-3 rounded-2xl text-[14px] leading-relaxed shadow-sm ring-2 ring-[#FE81D4] ring-offset-2
                                    ${isUser ? 'bg-[#FE81D4] text-white rounded-tr-sm' : 'bg-white border border-gray-100 text-gray-700 rounded-tl-sm'}">
                                    ${formatText(msg.content)}
                                </div>
                            </div>
                        `;
                        searchWrapper.insertAdjacentHTML('beforeend', bubbleHtml);
                    });

                    // Bind Event Listeners yang baru di-render
                    document.getElementById('btn-reset-search').addEventListener('click', resetSearch);
                    if (hasMoreSearch) {
                        document.getElementById('btn-load-more-search').addEventListener('click', () => performSearch(true));
                    }

                    // Jika ini pencarian awal, scroll ke atas container agar user bisa membaca dari pesan terlama yang didapat
                    if (!isLoadMore) {
                        chatBox.scrollTop = 0;
                    }

                } else {
                    handleSearchError(isLoadMore);
                }
            } catch (err) {
                handleSearchError(isLoadMore);
            }
        };

        // Helper untuk menangani error UI pencarian
        const handleSearchError = (isLoadMore) => {
            if (!isLoadMore) {
                messagesContainer.innerHTML = '<p class="text-xs text-red-400 italic text-center py-4">Pencarian gagal atau terjadi kesalahan koneksi.</p>';
            } else {
                const loadMoreBtn = document.getElementById('btn-load-more-search');
                if (loadMoreBtn) {
                    loadMoreBtn.innerText = 'Gagal memuat. Coba lagi';
                    loadMoreBtn.disabled = false;
                }
            }
        };

        const resetSearch = () => {
            if (originalChatHTML) {
                messagesContainer.innerHTML = originalChatHTML;
                originalChatHTML = ''; // reset state
                searchInput.value = '';
                
                // Reset state pagination pencarian
                searchBeforeMessageId = null;
                accumulatedSearchMessages = [];
                hasMoreSearch = true;
                currentSearchKeyword = '';
                
                // REFAKTOR: Aktifkan kembali input chat
                messageInput.disabled = false;
                sendBtn.disabled = messageInput.value.trim() === '';
                
                if (nextCursor) {
                    loadMoreContainer.classList.remove('hidden');
                }
                scrollToBottom();
            }
        };

        btnSearch.addEventListener('click', () => performSearch(false));

        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') performSearch(false);
        });

        // Bind Event Input Pengiriman Utama
        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        sendBtn.addEventListener('click', sendMessage);

        // --- INISIALISASI HALAMAN ---
        if (chatId !== 'new') {
            chatStatus.textContent = 'Memuat sesi...';
            fetchChatDetails(); 
            fetchHistory();     
        }
    }
};