import { navigateTo } from '../main.js';

const API_URL = import.meta.env.VITE_API_URL;

// Utilitas untuk format tanggal menjadi format lokal Indonesia (misal: 20 Nov 2026)
const formatDate = (dateString) => {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' });
};

export const DashboardPage = {
  render: () => {
    return `
      <div class="w-full max-w-[1000px] flex flex-col gap-6 relative mt-4 md:mt-32 pb-24">
        
        <div class="w-full bg-white/70 backdrop-blur-xl rounded-[32px] shadow-sm shadow-pink-100/50 border border-white p-6 md:p-8 flex flex-col md:flex-row gap-8 items-center md:items-stretch relative overflow-hidden">
          
          <div class="absolute -top-24 -right-24 w-64 h-64 bg-[#FE81D4]/10 rounded-full blur-3xl pointer-events-none"></div>

          <div class="relative w-48 h-48 md:w-56 md:h-56 rounded-3xl bg-gradient-to-tr from-[#FBC3C1]/40 to-[#FAACBF]/40 flex flex-col items-center justify-center shrink-0 border border-white shadow-inner overflow-hidden group">
            <div class="w-24 h-24 bg-[#FE81D4]/20 rounded-full blur-2xl absolute group-hover:scale-125 transition-transform duration-500"></div>
            <span class="text-[#FE81D4] font-bold text-center z-10 px-4 text-sm">
              Placeholder Avatar 3D<br><span class="text-xs font-medium text-gray-500 mt-1 block">(Maomao)</span>
            </span>
          </div>

          <div class="flex-1 flex flex-col w-full z-10 justify-center">
            
            <div class="mb-6 text-center md:text-left">
              <div class="flex flex-col sm:flex-row sm:items-center justify-center md:justify-start gap-3">
                <h2 id="user-name" class="text-2xl md:text-3xl font-bold text-gray-800 tracking-tight">Memuat data...</h2>
                    <button
                        id="logout-btn"
                            class="ml-auto px-3 py-1.5 rounded-xl bg-red-50 hover:bg-red-100 text-red-500 text-xs font-bold transition-all border border-red-100 flex items-center gap-1.5 cursor-pointer shadow-sm">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 0 013 3v1" />
                                </svg>
                        Keluar
                    </button>
              </div>
              <p id="user-email" class="text-gray-500 text-sm font-medium mt-1">Menyiapkan profil Anda</p>
            </div>

            <div class="grid grid-cols-2 md:grid-cols-3 gap-3 md:gap-4 w-full">
              <div class="bg-white/60 p-3.5 rounded-2xl border border-white shadow-sm">
                <p class="text-[11px] text-gray-400 uppercase font-bold tracking-wider mb-1">Usia</p>
                <p id="user-age" class="font-bold text-gray-700">-</p>
              </div>
              <div class="bg-white/60 p-3.5 rounded-2xl border border-white shadow-sm">
                <p class="text-[11px] text-gray-400 uppercase font-bold tracking-wider mb-1">Kehamilan Ke</p>
                <p id="user-pregnancy" class="font-bold text-gray-700">-</p>
              </div>
              <div class="bg-white/60 p-3.5 rounded-2xl border border-white shadow-sm">
                <p class="text-[11px] text-gray-400 uppercase font-bold tracking-wider mb-1">Perkiraan HPL</p>
                <p id="user-hpl" class="font-bold text-[#FE81D4]">-</p>
              </div>
              <div class="bg-white/60 p-3.5 rounded-2xl border border-white shadow-sm">
                <p class="text-[11px] text-gray-400 uppercase font-bold tracking-wider mb-1">Domisili</p>
                <p id="user-domicile" class="font-bold text-gray-700 truncate">-</p>
              </div>
              <div class="bg-[#FBC3C1]/20 p-3.5 rounded-2xl border border-[#FBC3C1]/50 shadow-sm md:col-span-2">
                <p class="text-[11px] text-red-400 uppercase font-bold tracking-wider mb-1">Riwayat Medis / Catatan</p>
                <p id="user-medical" class="font-semibold text-gray-800 line-clamp-2">-</p>
              </div>
            </div>

          </div>
        </div>

        <div class="w-full bg-[#FAACBF]/20 backdrop-blur-md p-5 rounded-2xl border border-[#FAACBF]/50 shadow-sm flex items-start gap-3 md:gap-4">
          <div class="bg-white rounded-full p-1.5 shrink-0 shadow-sm border border-red-100">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
            </svg>
          </div>
          <p class="text-gray-700 text-[13px] md:text-sm leading-relaxed text-justify mt-0.5">
            <span class="font-bold text-red-500">Peringatan Medis:</span> GravidaChatBot adalah AI dengan *knowledge* dasar. Harap diperhatikan bahwa informasi yang disampaikan tidak dijamin 100% akurat dan hanya digunakan sebagai referensi pendukung. <strong>Silakan hubungi dokter spesialis kandungan Anda jika terjadi keadaan darurat.</strong>
          </p>
        </div>

      </div>

      <div class="fixed bottom-8 right-6 md:right-10 z-[100] flex flex-col items-end gap-3 pointer-events-none">
        
        <div id="fab-menu" class="flex flex-col items-end gap-3 transition-all duration-300 transform translate-y-10 opacity-0 origin-bottom pointer-events-none">
          <a href="/history" data-link class="px-5 py-2.5 rounded-xl bg-white text-[#FE81D4] border border-white shadow-lg shadow-pink-100/50 hover:scale-105 hover:bg-gray-50 transition-all text-[13px] font-bold flex items-center gap-2">
            Riwayat Obrolan
          </a>
          <a href="/session/new" data-link class="px-5 py-2.5 rounded-xl bg-gradient-to-r from-[#FE81D4] to-[#f472b6] text-white shadow-lg shadow-pink-200 hover:scale-105 transition-all text-[13px] font-bold flex items-center gap-2">
            Mulai Obrolan Baru
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4" />
            </svg>
          </a>
        </div>

        <button id="fab-trigger" class="w-14 h-14 bg-gradient-to-tr from-[#FAACBF] to-[#FE81D4] rounded-[18px] shadow-lg shadow-pink-200 text-white flex items-center justify-center hover:scale-105 active:scale-95 transition-all duration-300 pointer-events-auto cursor-pointer border border-white/50">
          <svg id="fab-icon" xmlns="http://www.w3.org/2000/svg" class="h-7 w-7 transition-transform duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
        </button>
      </div>
    `;
  },

  afterrender: async () => {
    // 1. Cek Autentikasi
    const token = localStorage.getItem('access_token');
    if (!token) {
      navigateTo('/login');
      return;
    }

    // Identifikasi elemen DOM
    const nameEl = document.getElementById('user-name');
    const emailEl = document.getElementById('user-email');
    const ageEl = document.getElementById('user-age');
    const pregnancyEl = document.getElementById('user-pregnancy');
    const hplEl = document.getElementById('user-hpl');
    const domicileEl = document.getElementById('user-domicile');
    const medicalEl = document.getElementById('user-medical');
    
    const fabTrigger = document.getElementById('fab-trigger');
    const fabMenu = document.getElementById('fab-menu');
    const logoutBtn = document.getElementById('logout-btn');

    // LOGIKA TOMBOL LOGOUT
    if (logoutBtn) {
      logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('access_token');
        window.location.href = '/login'; // Bersihkan session dan tendang ke login
      });
    }

    // 3. Hit API Data User
    try {
      const response = await fetch(`${API_URL}/api/v1/user`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      const result = await response.json();

      if (!response.ok || !result.success) {
        throw new Error('Gagal mengambil data atau token tidak valid');
      }

      const userData = result.data;

      // Populate Data ke DOM
      nameEl.textContent = `Halo, ${userData.name}!`;
      emailEl.textContent = userData.email;
      ageEl.textContent = `${userData.age} Tahun`;
      pregnancyEl.textContent = `${userData.pregnancy_count}`;
      hplEl.textContent = formatDate(userData.estimated_delivery_date);
      domicileEl.textContent = userData.domicile || '-';
      medicalEl.textContent = userData.medical_history || 'Tidak ada catatan khusus';

    } catch (error) {
      console.error('Error fetching user data:', error);
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }

    // 4. Animasi FAB
    fabTrigger.addEventListener('click', () => {
        const isOpen = fabMenu.classList.contains('opacity-0');

        if (isOpen) {
            fabMenu.classList.remove(
            'opacity-0',
            'translate-y-10',
            'pointer-events-none'
            );

            fabMenu.classList.add('pointer-events-auto');
        } else {
            fabMenu.classList.add(
            'opacity-0',
            'translate-y-10',
            'pointer-events-none'
            );

            fabMenu.classList.remove('pointer-events-auto');
        }
    });


  }
};