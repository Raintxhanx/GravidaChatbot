export function LandingPage() {
    return `
      <!-- SECTION 1: HERO / INTRODUCTION -->
      <section id="hero" class="w-full max-w-6xl px-6 pt-[160px] pb-24 flex flex-col items-center text-center">
        <div class="inline-block px-4 py-1.5 rounded-full bg-[#FAACBF]/30 text-[#FE81D4] font-semibold text-sm mb-6 border border-[#FAACBF]/50">
          Era Baru Interaksi Digital
        </div>
        <h2 class="text-4xl md:text-6xl font-bold mb-6 text-gray-900 tracking-tight">
          Temui <span class="text-[#FE81D4]">Avatar Virtual</span> Anda.
        </h2>
        <p class="text-lg text-gray-700 max-w-2xl mb-10 leading-relaxed">
          GravidaChatbot adalah proyek asisten virtual interaktif yang dirancang untuk menghadirkan pengalaman percakapan yang cerdas, responsif, dan personal. Integrasi teknologi terkini untuk membantu kebutuhan digital Anda.
        </p>
        <!-- Redirect ke /register -->
        <a href="/register" class="px-8 py-4 bg-[#FE81D4] hover:bg-pink-500 transition-all text-white font-semibold rounded-2xl shadow-lg hover:shadow-xl hover:-translate-y-1 text-lg">
          Gabung Sekarang
        </a>
      </section>

      <!-- SECTION 2: INTRODUCTION SLIDE (Yang Indah-indah) -->
      <section id="intro" class="w-full bg-white/60 backdrop-blur-sm py-24 rounded-t-[50px] md:rounded-t-[100px] border-t border-white shadow-[0_-10px_40px_rgba(254,129,212,0.1)]">
        <div class="max-w-6xl mx-auto px-6 flex flex-col md:flex-row items-center gap-12">
          
          <!-- Kiri: Placeholder Gambar -->
          <div class="w-full md:w-1/2 flex justify-center">
            <div class="w-full aspect-[4/5] max-w-[400px] rounded-[40px] bg-gradient-to-tr from-[#FBC3C1] to-[#FAACBF] shadow-2xl relative flex items-center justify-center overflow-hidden border-8 border-white">
              <span class="text-white/80 font-semibold text-xl tracking-widest">3D / IMAGE PLACEHOLDER</span>
              <!-- Dekorasi floating di atas placeholder -->
              <div class="absolute -bottom-6 -right-6 w-32 h-32 bg-[#FE81D4] rounded-full blur-3xl opacity-40"></div>
              <div class="absolute -top-6 -left-6 w-32 h-32 bg-[#FFEABB] rounded-full blur-3xl opacity-60"></div>
            </div>
          </div>

          <!-- Kanan: Teks & Lorem Ipsum -->
          <div class="w-full md:w-1/2 text-left">
            <h3 class="text-3xl font-bold mb-4 text-gray-900">Membawa Karakter Menjadi Hidup.</h3>
            <p class="text-gray-600 mb-6 leading-relaxed">
              Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
            </p>
            <ul class="space-y-4 mb-8">
              <li class="flex items-start gap-3">
                <div class="w-6 h-6 rounded-full bg-[#FE81D4] text-white flex items-center justify-center shrink-0 text-sm">✓</div>
                <span class="text-gray-700">Duis aute irure dolor in reprehenderit in voluptate.</span>
              </li>
              <li class="flex items-start gap-3">
                <div class="w-6 h-6 rounded-full bg-[#FAACBF] text-white flex items-center justify-center shrink-0 text-sm">✓</div>
                <span class="text-gray-700">Velit esse cillum dolore eu fugiat nulla pariatur.</span>
              </li>
              <li class="flex items-start gap-3">
                <div class="w-6 h-6 rounded-full bg-[#FBC3C1] text-white flex items-center justify-center shrink-0 text-sm">✓</div>
                <span class="text-gray-700">Excepteur sint occaecat cupidatat non proident.</span>
              </li>
            </ul>
          </div>
        </div>
      </section>

      <!-- SECTION 3: FAQ -->
      <section id="faq" class="w-full py-24 bg-white">
        <div class="max-w-4xl mx-auto px-6 text-center">
          <h3 class="text-3xl font-bold mb-12 text-gray-900">Frequently Asked Questions</h3>
          
          <div class="space-y-4 text-left">
            <!-- FAQ Item 1 -->
            <details class="group bg-[#FFEABB]/30 rounded-2xl border border-[#FFEABB] overflow-hidden cursor-pointer">
              <summary class="px-6 py-5 font-semibold text-gray-800 flex justify-between items-center bg-white hover:bg-gray-50 transition-colors">
                Apa itu GravidaChatbot?
                <span class="text-[#FE81D4] text-2xl group-open:rotate-45 transition-transform duration-300">+</span>
              </summary>
              <div class="px-6 pb-5 pt-2 text-gray-600 leading-relaxed border-t border-gray-100">
                Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer nec odio. Praesent libero. Sed cursus ante dapibus diam. Sed nisi. Nulla quis sem at nibh elementum imperdiet.
              </div>
            </details>

            <!-- FAQ Item 2 -->
            <details class="group bg-[#FFEABB]/30 rounded-2xl border border-[#FFEABB] overflow-hidden cursor-pointer">
              <summary class="px-6 py-5 font-semibold text-gray-800 flex justify-between items-center bg-white hover:bg-gray-50 transition-colors">
                Bagaimana cara kerjanya?
                <span class="text-[#FE81D4] text-2xl group-open:rotate-45 transition-transform duration-300">+</span>
              </summary>
              <div class="px-6 pb-5 pt-2 text-gray-600 leading-relaxed border-t border-gray-100">
                Duis sagittis ipsum. Praesent mauris. Fusce nec tellus sed augue semper porta. Mauris massa. Vestibulum lacinia arcu eget nulla.
              </div>
            </details>

            <!-- FAQ Item 3 -->
            <details class="group bg-[#FFEABB]/30 rounded-2xl border border-[#FFEABB] overflow-hidden cursor-pointer">
              <summary class="px-6 py-5 font-semibold text-gray-800 flex justify-between items-center bg-white hover:bg-gray-50 transition-colors">
                Apakah data saya aman?
                <span class="text-[#FE81D4] text-2xl group-open:rotate-45 transition-transform duration-300">+</span>
              </summary>
              <div class="px-6 pb-5 pt-2 text-gray-600 leading-relaxed border-t border-gray-100">
                Curabitur sodales ligula in libero. Sed dignissim lacinia nunc. Curabitur tortor. Pellentesque nibh. Aenean quam.
              </div>
            </details>
          </div>
        </div>
      </section>

      <!-- SECTION 4: CONTACT -->
      <section id="contact" class="w-full py-24 bg-[#FAACBF]/10">
        <div class="max-w-6xl mx-auto px-6 text-center">
          <h3 class="text-3xl font-bold mb-4 text-gray-900">Kontak Pengembang</h3>
          <p class="text-gray-600 mb-12 max-w-xl mx-auto">
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Hubungi kami jika Anda memiliki pertanyaan atau tertarik untuk berkolaborasi.
          </p>

          <div class="bg-white rounded-[30px] p-8 md:p-12 shadow-xl border border-[#FBC3C1]/50 max-w-3xl mx-auto flex flex-col md:flex-row gap-8 items-center text-left">
            <!-- Profil Placeholder -->
            <div class="w-32 h-32 rounded-full bg-[#FBC3C1] border-4 border-[#FE81D4]/20 flex-shrink-0 flex items-center justify-center text-white text-sm font-semibold shadow-inner">
              FOTO
            </div>
            
            <div class="flex-1">
              <h4 class="text-2xl font-bold text-gray-900 mb-2">Pembuat Web</h4>
              <p class="text-[#FE81D4] font-medium mb-4">Lead Developer & Designer</p>
              <p class="text-gray-600 mb-6 text-sm leading-relaxed">
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam."
              </p>
              <div class="flex gap-4">
                <button class="px-6 py-2 bg-[#FBC3C1] hover:bg-[#FAACBF] text-gray-800 rounded-lg font-medium transition-colors">Email Me</button>
                <button class="px-6 py-2 border-2 border-[#FAACBF] text-[#FAACBF] hover:bg-[#FAACBF] hover:text-white rounded-lg font-medium transition-colors">GitHub</button>
              </div>
            </div>
          </div>
        </div>
      </section>
    `;
}