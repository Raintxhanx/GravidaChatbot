import { navigateTo } from '../main.js'

// Mengambil URL Backend dari environment variable (.env)
const API_URL = import.meta.env.VITE_API_URL;

export const RegisterPage = {
  // 1. Bagian Render HTML
  render: () => {
    return `
    <section class="w-full max-w-3xl bg-white/80 backdrop-blur-md rounded-[30px] shadow-xl border border-white p-8 md:p-10 pt-16 md:pt-16 relative mt-28 md:mt-36 mb-12">
      
      <a href="/" data-link class="absolute top-6 left-6 flex items-center gap-2 text-sm text-gray-700 hover:text-[#FE81D4] transition-colors font-medium bg-gray-50/50 hover:bg-white px-3 py-1.5 rounded-xl border border-gray-100 shadow-sm">
        <span>←</span> Kembali
      </a>

      <div class="text-center mb-8">
        <h2 class="text-3xl font-bold text-gray-900 mb-2">Buat Akun Gravida</h2>
        <p class="text-gray-600 text-sm">Lengkapi data diri Anda untuk memulai perjalanan cerdas ini.</p>
      </div>

      <form id="register-form" class="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div class="flex flex-col gap-1">
          <label class="text-sm font-semibold text-gray-700" for="name">Nama Lengkap</label>
          <input type="text" id="name" name="name" required class="px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#FE81D4] transition-all">
        </div>
        
        <div class="flex flex-col gap-1">
          <label class="text-sm font-semibold text-gray-700" for="email">Email</label>
          <input type="email" id="email" name="email" required class="px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#FE81D4] transition-all">
        </div>

        <div class="flex flex-col gap-1">
          <label class="text-sm font-semibold text-gray-700" for="password">Password</label>
          <input type="password" id="password" name="password" required class="px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#FE81D4] transition-all">
        </div>

        <div class="flex flex-col gap-1">
          <label class="text-sm font-semibold text-gray-700" for="phone_number">No. Telepon</label>
          <input type="tel" id="phone_number" name="phone_number" required class="px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#FE81D4] transition-all">
        </div>

        <div class="flex flex-col gap-1">
          <label class="text-sm font-semibold text-gray-700" for="age">Usia</label>
          <input type="number" id="age" name="age" required min="1" class="px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#FE81D4] transition-all">
        </div>

        <div class="flex flex-col gap-1">
          <label class="text-sm font-semibold text-gray-700" for="domicile">Domisili</label>
          <input type="text" id="domicile" name="domicile" required class="px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#FE81D4] transition-all">
        </div>

        <div class="flex flex-col gap-1">
          <label class="text-sm font-semibold text-gray-700" for="pregnancy_count">Kehamilan Ke-</label>
          <input type="number" id="pregnancy_count" name="pregnancy_count" required min="1" class="px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#FE81D4] transition-all">
        </div>

        <div class="flex flex-col gap-1">
          <label class="text-sm font-semibold text-gray-700" for="estimated_delivery_date">Perkiraan Lahir (HPL)</label>
          <input type="date" id="estimated_delivery_date" name="estimated_delivery_date" required class="px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#FE81D4] transition-all text-gray-700">
        </div>

        <div class="flex flex-col gap-1 md:col-span-2">
          <label class="text-sm font-semibold text-gray-700" for="medical_history">Riwayat Medis / Alergi</label>
          <textarea id="medical_history" name="medical_history" rows="2" class="px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#FE81D4] transition-all resize-none"></textarea>
        </div>

        <div id="error-message" class="hidden md:col-span-2 text-red-500 text-sm font-medium text-center"></div>

        <div class="md:col-span-2 mt-4">
          <button type="submit" id="submit-btn" class="w-full py-4 bg-[#FE81D4] hover:bg-pink-500 transition-colors text-white font-bold rounded-xl shadow-lg flex justify-center items-center">
            Daftar & Masuk
          </button>
        </div>
      </form>
      
      <p class="text-center text-sm text-gray-600 mt-6">
        Sudah punya akun? <a href="/login" data-link class="text-[#FE81D4] font-semibold hover:underline">Login di sini</a>
      </p>
    </section>
    `;
  },

  // 2. Bagian Logika Manipulasi DOM & API
  afterrender: () => {
    const form = document.getElementById('register-form');
    const errorMsg = document.getElementById('error-message');
    const submitBtn = document.getElementById('submit-btn');

    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      // Loading state sederhana
      submitBtn.disabled = true;
      submitBtn.innerText = 'Memproses...';
      errorMsg.classList.add('hidden');

      // Ambil data form
      const email = document.getElementById('email').value;
      const password = document.getElementById('password').value;

      // Susun payload register sesuai dengan tipe data integer untuk age & pregnancy_count
      const registerPayload = {
        name: document.getElementById('name').value,
        email: email,
        password: password,
        phone_number: document.getElementById('phone_number').value,
        age: parseInt(document.getElementById('age').value, 10),
        domicile: document.getElementById('domicile').value,
        pregnancy_count: parseInt(document.getElementById('pregnancy_count').value, 10),
        estimated_delivery_date: document.getElementById('estimated_delivery_date').value,
        medical_history: document.getElementById('medical_history').value || "",
      };

      try {
        // --- 1. HIT API REGISTER ---
        const registerResponse = await fetch(`${API_URL}/api/v1/auth/register`, {
          method: 'POST',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(registerPayload)
        });

        const registerResult = await registerResponse.json();

        if (!registerResponse.ok || !registerResult.success) {
          throw new Error(registerResult.message || 'Registrasi gagal, silakan coba lagi.');
        }

        // --- 2. HIT API LOGIN (Langsung setelah register sukses) ---
        const loginResponse = await fetch(`${API_URL}/api/v1/auth/login`, {
          method: 'POST',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ email, password })
        });

        const loginResult = await loginResponse.json();

        if (!loginResponse.ok || !loginResult.success) {
          throw new Error(loginResult.message || 'Registrasi sukses, tapi gagal login otomatis.');
        }

        // Simpan token ke localStorage
        localStorage.setItem('access_token', loginResult.data.access_token);

        // --- 3. REDIRECT KE DASHBOARD ---
        // Jika aplikasi kamu menggunakan router kustom (SPA), ganti bagian ini dengan fungsi router kamu, misal: router.navigate('/dashboard')
        navigateTo('/dashboard');

      } catch (error) {
        // Menampilkan pesan error ke user
        errorMsg.textContent = error.message;
        errorMsg.classList.remove('hidden');
      } finally {
        // Kembalikan state tombol
        submitBtn.disabled = false;
        submitBtn.innerText = 'Daftar & Masuk';
      }
    });
  }
};