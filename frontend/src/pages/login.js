// pages/login.js
import { navigateTo } from '../main.js';

// Mengambil URL Backend dari environment variable (.env)
const API_URL = import.meta.env.VITE_API_URL;

export const LoginPage = {
  // 1. Bagian Render HTML
  render: () => {
    return `
    <section class="w-full max-w-md bg-white/80 backdrop-blur-md rounded-[30px] shadow-xl border border-white p-8 md:p-10 relative pt-14 mt-28 md:mt-36 mb-12">
      
      <a href="/" data-link class="absolute top-6 left-6 flex items-center gap-2 text-sm text-gray-700 hover:text-[#FE81D4] transition-colors font-medium bg-gray-50/50 hover:bg-white px-3 py-1.5 rounded-xl border border-gray-100 shadow-sm">
        <span>←</span> Kembali
      </a>

      <div class="flex justify-center mb-6">
        <div class="w-16 h-16 rounded-[17px] bg-[#FAACBF] flex items-center justify-center text-white text-xs font-semibold shadow-inner">
          IMG
        </div>
      </div>
      
      <div class="text-center mb-8">
        <h2 class="text-3xl font-bold text-gray-900 mb-2">Selamat Datang</h2>
        <p class="text-gray-600 text-sm">Silakan masuk ke akun Anda.</p>
      </div>

      <form id="login-form" class="flex flex-col gap-5">
        <div class="flex flex-col gap-1">
          <label class="text-sm font-semibold text-gray-700" for="email">Email</label>
          <input type="email" id="email" name="email" required placeholder="user@example.com" class="px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#FE81D4] transition-all">
        </div>

        <div class="flex flex-col gap-1">
          <label class="text-sm font-semibold text-gray-700" for="password">Password</label>
          <input type="password" id="password" name="password" required placeholder="••••••••" class="px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#FE81D4] transition-all">
        </div>

        <div id="error-message" class="hidden text-red-500 text-sm font-medium text-center"></div>

        <button type="submit" id="submit-btn" class="w-full py-4 mt-2 bg-[#FE81D4] hover:bg-pink-500 transition-colors text-white font-bold rounded-xl shadow-lg flex justify-center items-center">
          Masuk
        </button>
      </form>

      <p class="text-center text-sm text-gray-600 mt-8">
        Belum punya akun? <a href="/register" data-link class="text-[#FE81D4] font-semibold hover:underline">Daftar sekarang</a>
      </p>
    </section>
    `;
  },

  // 2. Bagian Logika Manipulasi DOM & API
  afterrender: () => {
    const form = document.getElementById('login-form');
    const errorMsg = document.getElementById('error-message');
    const submitBtn = document.getElementById('submit-btn');

    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      // Loading state
      submitBtn.disabled = true;
      submitBtn.innerText = 'Memproses...';
      errorMsg.classList.add('hidden');

      // Ambil data form
      const email = document.getElementById('email').value;
      const password = document.getElementById('password').value;

      try {
        // --- HIT API LOGIN ---
        const response = await fetch(`${API_URL}/api/v1/auth/login`, {
          method: 'POST',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ email, password })
        });

        const result = await response.json();

        // Validasi response API
        if (!response.ok || !result.success) {
          throw new Error(result.message || 'Login gagal, silakan periksa kembali email dan password Anda.');
        }

        // Simpan token ke localStorage (bisa dipanggil nanti sebagai Bearer Token)
        localStorage.setItem('access_token', result.data.access_token);

        // --- REDIRECT KE DASHBOARD ---
        navigateTo('/dashboard');

      } catch (error) {
        // Menampilkan pesan error ke user jika gagal
        errorMsg.textContent = error.message;
        errorMsg.classList.remove('hidden');
      } finally {
        // Kembalikan state tombol jika proses selesai/gagal
        submitBtn.disabled = false;
        submitBtn.innerText = 'Masuk';
      }
    });
  }
};