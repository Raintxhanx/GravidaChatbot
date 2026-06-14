import { navigateTo } from '../main.js';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

// Utilitas untuk format tanggal
const formatDateTime = (dateString) => {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleDateString('id-ID', { 
    day: 'numeric', month: 'short', year: 'numeric', 
    hour: '2-digit', minute: '2-digit' 
  });
};

export const HistoryPage = {
  render: () => {
    return `
      <div class="w-full flex flex-col items-center mt-4 md:mt-[80px] pb-32 gap-6 relative">
        
        <div class="w-full md:w-[994px] md:h-[166px] bg-white/70 backdrop-blur-xl rounded-[24px] shadow-sm border border-white p-6 relative flex flex-col md:flex-row items-center justify-center gap-4 z-20">
          
          <div class="relative w-full md:w-[615px] h-[40px] md:h-[31px]">
            <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input type="text" id="search-input" placeholder="Cari sesi percakapan..." 
              class="w-full h-full pl-9 pr-4 rounded-[9px] border border-gray-200 bg-white/80 focus:outline-none focus:border-[#FE81D4] text-sm shadow-sm transition-all text-gray-700">
          </div>

          <div class="relative w-full md:w-[210px] h-[40px] md:h-[31px]">
            <button id="date-filter-btn" class="w-full h-full px-3 bg-white border border-gray-200 rounded-[9px] shadow-sm flex items-center justify-between hover:bg-gray-50 transition-colors text-sm text-gray-600">
              <span id="date-btn-text" class="truncate">Filter Tanggal</span>
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </button>
            
            <div id="date-popup" class="absolute top-[40px] right-0 w-[260px] bg-white p-4 rounded-xl shadow-lg shadow-pink-100 border border-gray-100 hidden flex-col gap-3 z-50">
              <div>
                <label class="text-[11px] font-bold text-gray-400 uppercase">Mulai Tanggal</label>
                <input type="date" id="start-date" class="w-full mt-1 border border-gray-200 rounded-lg p-2 text-sm text-gray-700 focus:outline-[#FE81D4]">
              </div>
              <div>
                <label class="text-[11px] font-bold text-gray-400 uppercase">Sampai Tanggal</label>
                <input type="date" id="end-date" class="w-full mt-1 border border-gray-200 rounded-lg p-2 text-sm text-gray-700 focus:outline-[#FE81D4]">
              </div>
              <div class="flex gap-2 mt-2">
                <button id="clear-date-btn" class="flex-1 py-1.5 text-xs text-gray-500 bg-gray-100 hover:bg-gray-200 rounded-lg transition">Reset</button>
                <button id="apply-date-btn" class="flex-1 py-1.5 text-xs text-white bg-[#FE81D4] hover:bg-pink-500 rounded-lg transition font-semibold">Terapkan</button>
              </div>
            </div>
          </div>

        </div>

        <div id="chat-list" class="w-full max-w-[994px] flex flex-col gap-4 relative z-10">
          <div class="text-center py-10 text-gray-500 text-sm">Memuat data riwayat...</div>
        </div>

        <div class="w-full max-w-[994px] flex justify-between items-center px-2 mt-2">
          <button id="prev-btn" class="px-5 py-2 bg-white border border-gray-200 shadow-sm rounded-xl text-sm font-semibold text-gray-600 hover:text-[#FE81D4] hover:border-pink-200 disabled:opacity-50 disabled:pointer-events-none transition-all">
            &laquo; Sebelumnya
          </button>
          <span id="page-indicator" class="text-xs font-bold text-gray-400 uppercase tracking-wider">Halaman 1</span>
          <button id="next-btn" class="px-5 py-2 bg-white border border-gray-200 shadow-sm rounded-xl text-sm font-semibold text-gray-600 hover:text-[#FE81D4] hover:border-pink-200 disabled:opacity-50 disabled:pointer-events-none transition-all">
            Selanjutnya &raquo;
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

    // Elemen DOM
    const chatListEl = document.getElementById('chat-list');
    const searchInput = document.getElementById('search-input');
    const dateFilterBtn = document.getElementById('date-filter-btn');
    const datePopup = document.getElementById('date-popup');
    const startDateInput = document.getElementById('start-date');
    const endDateInput = document.getElementById('end-date');
    const applyDateBtn = document.getElementById('apply-date-btn');
    const clearDateBtn = document.getElementById('clear-date-btn');
    const dateBtnText = document.getElementById('date-btn-text');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const pageIndicator = document.getElementById('page-indicator');

    // State Pagination & Filter
    let skip = 0;
    const limit = 10;
    let searchQuery = '';
    let startDate = '';
    let endDate = '';
    let isFetching = false;

    // Toggle Date Popup
    dateFilterBtn.addEventListener('click', () => {
      datePopup.classList.toggle('hidden');
      datePopup.classList.toggle('flex');
    });

    // Close popup outside click
    document.addEventListener('click', (e) => {
      if (!dateFilterBtn.contains(e.target) && !datePopup.contains(e.target)) {
        datePopup.classList.add('hidden');
        datePopup.classList.remove('flex');
      }
    });

    // Apply & Clear Date Filters
    applyDateBtn.addEventListener('click', () => {
      startDate = startDateInput.value;
      endDate = endDateInput.value;
      if (startDate || endDate) {
        dateBtnText.innerHTML = `<span class="text-[#FE81D4] font-bold">Terfilter</span>`;
      }
      datePopup.classList.add('hidden');
      datePopup.classList.remove('flex');
      skip = 0;
      fetchChats();
    });

    clearDateBtn.addEventListener('click', () => {
      startDateInput.value = '';
      endDateInput.value = '';
      startDate = '';
      endDate = '';
      dateBtnText.textContent = 'Filter Tanggal';
      datePopup.classList.add('hidden');
      datePopup.classList.remove('flex');
      skip = 0;
      fetchChats();
    });

    // Search (Debounce logic)
    let searchTimeout;
    searchInput.addEventListener('input', (e) => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
        searchQuery = e.target.value.trim();
        skip = 0;
        fetchChats();
      }, 500); // Tunggu 500ms setelah mengetik untuk hit API
    });

    // Pagination
    prevBtn.addEventListener('click', () => {
      if (skip >= limit) {
        skip -= limit;
        fetchChats();
      }
    });

    nextBtn.addEventListener('click', () => {
      skip += limit;
      fetchChats();
    });

    // Fungsi fetch data ke API
    const fetchChats = async () => {
      if (isFetching) return;
      isFetching = true;
      chatListEl.innerHTML = `<div class="text-center py-10 text-gray-500 text-sm">Memuat data...</div>`;

      try {
        const queryParams = new URLSearchParams({ limit, skip });
        if (searchQuery) queryParams.append('search', searchQuery);
        if (startDate) queryParams.append('start_date', startDate);
        if (endDate) queryParams.append('end_date', endDate);

        const response = await fetch(`${API_URL}/api/v1/chats?${queryParams.toString()}`, {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        });

        const result = await response.json();
        
        if (response.ok && result.success) {
          renderChatList(result.data);
          
          // Update pagination controls
          pageIndicator.textContent = `Halaman ${(skip / limit) + 1}`;
          prevBtn.disabled = skip === 0;
          // Asumsi jika data yang dikembalikan kurang dari limit, berarti tidak ada data lagi (next di-disable)
          nextBtn.disabled = result.data.length < limit;
        } else {
          chatListEl.innerHTML = `<div class="text-center py-10 text-red-500 text-sm font-medium">Gagal memuat riwayat.</div>`;
        }
      } catch (error) {
        console.error('Error fetching chats:', error);
        chatListEl.innerHTML = `<div class="text-center py-10 text-red-500 text-sm font-medium">Terjadi kesalahan jaringan.</div>`;
      } finally {
        isFetching = false;
      }
    };

    // Render HTML untuk List
    const renderChatList = (chats) => {
    if (!chats || chats.length === 0) {
        chatListEl.innerHTML = `
        <div class="w-full flex flex-col items-center justify-center bg-white rounded-2xl p-12 text-center shadow-sm border border-gray-100">
            <div class="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mb-4">
            <svg class="w-8 h-8 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path></svg>
            </div>
            <p class="text-gray-500 font-semibold">Belum ada riwayat percakapan.</p>
            <p class="text-sm text-gray-400 mt-1">Sesi konsultasi baru Anda akan muncul di sini.</p>
        </div>
        `;
        return;
    }

    // Gunakan 'mb-4' pada setiap card jika container utamanya (chatListEl) tidak menggunakan 'flex flex-col gap-4'
    chatListEl.innerHTML = chats.map(chat => `
        <div class="group w-full bg-white rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 border border-pink-50 hover:border-pink-100 p-5 md:p-6 flex flex-col gap-4 mb-4">
        
        <div class="flex flex-col md:flex-row md:items-center gap-3 md:gap-5 w-full">
            <span class="shrink-0 inline-flex items-center px-3 py-1.5 bg-gray-50 text-gray-500 text-xs font-semibold rounded-lg border border-gray-100">
            <svg class="w-3.5 h-3.5 mr-1.5 opacity-70" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
            ${formatDateTime(chat.created_at)}
            </span>
            
            <div class="flex items-center gap-2 flex-1 min-w-0">
            <input type="text" data-chat-id="${chat.id}" value="${chat.title}" 
                class="title-input w-full bg-transparent font-bold text-base md:text-lg text-gray-800 border-b-2 border-transparent focus:border-[#FE81D4] focus:bg-pink-50/50 hover:bg-gray-50 px-2 py-1 rounded-t transition-all outline-none truncate"
                placeholder="Judul Percakapan">
            <button data-chat-id="${chat.id}" class="save-title-btn hidden shrink-0 text-xs font-bold bg-[#FE81D4] text-white px-4 py-1.5 rounded-lg shadow-sm hover:bg-pink-500 hover:-translate-y-0.5 active:translate-y-0 transition-all">
                Simpan
            </button>
            </div>
        </div>

        <div class="flex flex-col md:flex-row items-start md:items-end justify-between gap-4 w-full">
            <p class="text-sm text-gray-600 leading-relaxed line-clamp-2 md:line-clamp-3 flex-1 md:pr-8">
            ${chat.description || 'Sesi konsultasi ini belum memiliki deskripsi yang dihasilkan.'}
            </p>
            
            <button data-target="${chat.id}" class="chat-lagi-btn shrink-0 w-full md:w-auto px-6 py-2.5 rounded-xl bg-gradient-to-r from-[#FAACBF] to-[#FE81D4] text-white text-sm font-bold shadow-sm shadow-pink-200 hover:shadow-md hover:shadow-pink-300 hover:-translate-y-0.5 active:translate-y-0 transition-all flex items-center justify-center gap-2">
            <span>Chat Lagi</span>
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
            </button>
        </div>

        </div>
    `).join('');

    attachChatEvents();
    };

    // Pasang Event Listener untuk setiap elemen dalam list hasil render
    const attachChatEvents = () => {
      
      // 1. Tombol Chat Lagi (Redirect)
        document.querySelectorAll('.chat-lagi-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const chatId = e.currentTarget.getAttribute('data-target');

                if (chatId) {
                navigateTo(`/session/${chatId}`);
                }
            });
        });

      // 2. Logic Update Judul (Tampilkan box edit dan request ke API)
      const titleInputs = document.querySelectorAll('.title-input');
      const saveBtns = document.querySelectorAll('.save-title-btn');

      titleInputs.forEach(input => {
        const id = input.getAttribute('data-chat-id');
        const saveBtn = Array.from(saveBtns).find(b => b.getAttribute('data-chat-id') === id);

        // Munculkan tombol simpan jika teks berubah
        input.addEventListener('input', () => {
          saveBtn.classList.remove('hidden');
        });

        // Request update saat menekan enter pada keyboard
        input.addEventListener('keypress', (e) => {
          if (e.key === 'Enter') {
            saveBtn.click();
            input.blur();
          }
        });

        // Fungsi Simpan (PUT/PATCH API)
        saveBtn.addEventListener('click', async () => {
          const newTitle = input.value.trim();
          if (!newTitle) return;

          saveBtn.textContent = '...';
          saveBtn.disabled = true;

          try {
            // Asumsi API endpoint Anda menerima method PATCH/PUT untuk update judul
            const response = await fetch(`${API_URL}/api/v1/chats/${id}`, {
              method: 'PATCH', // Ganti ke PUT jika server Anda mewajibkan PUT
              headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': `Bearer ${token}`
              },
              body: JSON.stringify({ title: newTitle })
            });

            const result = await response.json();

            if (response.ok && result.success) {
              // Berhasil, sembunyikan kembali tombol
              saveBtn.classList.add('hidden');
              saveBtn.textContent = 'Simpan';
              saveBtn.disabled = false;
            } else {
              alert('Gagal memperbarui judul: ' + (result.message || 'Error tidak diketahui'));
              saveBtn.textContent = 'Simpan';
              saveBtn.disabled = false;
            }
          } catch (error) {
            console.error('Update title error:', error);
            alert('Terjadi kesalahan jaringan.');
            saveBtn.textContent = 'Simpan';
            saveBtn.disabled = false;
          }
        });
      });
    };

    // Initial Fetch saat halaman dimuat
    fetchChats();
  }
};