export function LandingPage() {
  return `
      <!-- SECTION 1: HERO -->
      <section id="hero" class="w-full max-w-6xl px-6 pt-[160px] pb-24 flex flex-col items-center text-center">
        <div class="inline-block px-4 py-1.5 rounded-full bg-[#FAACBF]/30 text-[#FE81D4] font-semibold text-sm mb-6 border border-[#FAACBF]/50">
          Ditenagai RAG &amp; LLM Fine-Tuned Khusus Kehamilan
        </div>
        <h1 class="text-4xl md:text-6xl font-bold mb-6 text-gray-900 tracking-tight">
          Kenalan dengan <span class="text-[#FE81D4]">Gravida</span>, Sahabat Kehamilan Anda.
        </h1>
        <p class="text-lg text-gray-700 max-w-2xl mb-10 leading-relaxed">
          Gravida adalah asisten virtual pendamping kehamilan berbasis chatbot yang memadukan
          teknologi <em>Retrieval-Augmented Generation</em> (RAG) dan model bahasa Qwen2.5-7B-Instruct
          hasil fine-tuning, untuk memberikan jawaban yang empatik, relevan, dan berbasis referensi
          medis tepercaya bagi ibu hamil.
        </p>
        <a
          href="/register"
          data-link
          class="px-8 py-4 bg-[#FE81D4] hover:bg-pink-500 transition-all text-white font-semibold rounded-2xl shadow-lg hover:shadow-xl hover:-translate-y-1 text-lg"
        >
          Gabung Sekarang
        </a>
      </section>

      <!-- SECTION 2: TENTANG GRAVIDA -->
      <section id="intro" class="w-full bg-white/60 backdrop-blur-sm py-24 rounded-t-[50px] md:rounded-t-[100px] border-t border-white shadow-[0_-10px_40px_rgba(254,129,212,0.1)]">
        <div class="max-w-6xl mx-auto px-6 flex flex-col md:flex-row items-center gap-12">

          <!-- Kiri: Placeholder Ilustrasi -->
          <div class="w-full md:w-1/2 flex justify-center">
            <div class="w-full aspect-[4/5] max-w-[400px] rounded-[40px] bg-gradient-to-tr from-[#FBC3C1] to-[#FAACBF] shadow-2xl relative flex items-center justify-center overflow-hidden border-8 border-white">
              <span class="text-white/80 font-semibold text-xl tracking-widest text-center px-6">
                ILUSTRASI GRAVIDA
              </span>
              <div class="absolute -bottom-6 -right-6 w-32 h-32 bg-[#FE81D4] rounded-full blur-3xl opacity-40"></div>
              <div class="absolute -top-6 -left-6 w-32 h-32 bg-[#FFEABB] rounded-full blur-3xl opacity-60"></div>
            </div>
          </div>

          <!-- Kanan: Penjelasan -->
          <div class="w-full md:w-1/2 text-left">
            <h2 class="text-3xl font-bold mb-4 text-gray-900">Menemani Setiap Trimester dengan Jawaban yang Tepat.</h2>
            <p class="text-gray-600 mb-6 leading-relaxed">
              Berbeda dari chatbot kesehatan pada umumnya yang mengandalkan jawaban statis, Gravida
              menggabungkan fine-tuning LoRA dan sistem RAG agar setiap respons tetap faktual, mengurangi
              risiko halusinasi, dan relevan dengan konteks kehamilan Anda secara personal.
            </p>
            <ul class="space-y-4 mb-8">
              <li class="flex items-start gap-3">
                <div class="w-6 h-6 rounded-full bg-[#FE81D4] text-white flex items-center justify-center shrink-0 text-sm">✓</div>
                <span class="text-gray-700">Dilatih dari transkrip wawancara bersama bidan dan tenaga kesehatan agar gaya komunikasinya empatik.</span>
              </li>
              <li class="flex items-start gap-3">
                <div class="w-6 h-6 rounded-full bg-[#FAACBF] text-white flex items-center justify-center shrink-0 text-sm">✓</div>
                <span class="text-gray-700">Setiap jawaban ditarik dari basis pengetahuan medis terkurasi melalui teknologi RAG, bukan sekadar tebakan model.</span>
              </li>
              <li class="flex items-start gap-3">
                <div class="w-6 h-6 rounded-full bg-[#FBC3C1] text-white flex items-center justify-center shrink-0 text-sm">✓</div>
                <span class="text-gray-700">Seluruh percakapan diproses melalui inferensi lokal untuk menjaga privasi data kesehatan Anda.</span>
              </li>
            </ul>
          </div>
        </div>
      </section>

      <!-- SECTION 3: FAQ -->
      <section id="faq" class="w-full py-24 bg-white">
        <div class="max-w-4xl mx-auto px-6 text-center">
          <h2 class="text-3xl font-bold mb-12 text-gray-900">Pertanyaan yang Sering Diajukan</h2>

          <div class="space-y-4 text-left">
            <!-- FAQ Item 1 -->
            <details class="group bg-[#FFEABB]/30 rounded-2xl border border-[#FFEABB] overflow-hidden cursor-pointer">
              <summary class="px-6 py-5 font-semibold text-gray-800 flex justify-between items-center bg-white hover:bg-gray-50 transition-colors">
                Apa itu Gravida?
                <span class="text-[#FE81D4] text-2xl group-open:rotate-45 transition-transform duration-300">+</span>
              </summary>
              <div class="px-6 pb-5 pt-2 text-gray-600 leading-relaxed border-t border-gray-100">
                Gravida adalah chatbot pendamping kehamilan berbasis web yang dikembangkan dengan
                model LLM Qwen2.5-7B-Instruct, dipadukan dengan fine-tuning LoRA dan Retrieval-Augmented
                Generation (RAG) agar mampu menjawab keluhan seputar kehamilan secara empatik dan akurat.
              </div>
            </details>

            <!-- FAQ Item 2 -->
            <details class="group bg-[#FFEABB]/30 rounded-2xl border border-[#FFEABB] overflow-hidden cursor-pointer">
              <summary class="px-6 py-5 font-semibold text-gray-800 flex justify-between items-center bg-white hover:bg-gray-50 transition-colors">
                Bagaimana cara Gravida menjawab pertanyaan saya?
                <span class="text-[#FE81D4] text-2xl group-open:rotate-45 transition-transform duration-300">+</span>
              </summary>
              <div class="px-6 pb-5 pt-2 text-gray-600 leading-relaxed border-t border-gray-100">
                Saat Anda mengirim pertanyaan, sistem RAG akan menelusuri basis data vektor berisi
                referensi medis kehamilan yang relevan, kemudian menyusun jawaban bersama model LLM
                yang telah di-fine-tune. Pendekatan ini menekan risiko jawaban yang mengada-ada dan
                menjaga agar respons tetap berdasarkan konteks yang valid.
              </div>
            </details>

            <!-- FAQ Item 3 -->
            <details class="group bg-[#FFEABB]/30 rounded-2xl border border-[#FFEABB] overflow-hidden cursor-pointer">
              <summary class="px-6 py-5 font-semibold text-gray-800 flex justify-between items-center bg-white hover:bg-gray-50 transition-colors">
                Apakah Gravida bisa menggantikan dokter kandungan?
                <span class="text-[#FE81D4] text-2xl group-open:rotate-45 transition-transform duration-300">+</span>
              </summary>
              <div class="px-6 pb-5 pt-2 text-gray-600 leading-relaxed border-t border-gray-100">
                Tidak. Gravida dirancang sebagai media edukasi dan pendamping harian, bukan pengganti
                diagnosis medis. Untuk keluhan serius atau kondisi darurat, tetap disarankan untuk
                segera menghubungi dokter spesialis kandungan atau bidan Anda.
              </div>
            </details>

            <!-- FAQ Item 4 -->
            <details class="group bg-[#FFEABB]/30 rounded-2xl border border-[#FFEABB] overflow-hidden cursor-pointer">
              <summary class="px-6 py-5 font-semibold text-gray-800 flex justify-between items-center bg-white hover:bg-gray-50 transition-colors">
                Apakah data percakapan saya aman?
                <span class="text-[#FE81D4] text-2xl group-open:rotate-45 transition-transform duration-300">+</span>
              </summary>
              <div class="px-6 pb-5 pt-2 text-gray-600 leading-relaxed border-t border-gray-100">
                Ya. Proses inferensi model dijalankan secara lokal tanpa bergantung pada layanan pihak
                ketiga, sehingga seluruh percakapan dan data kesehatan Anda tetap berada dalam kendali
                infrastruktur sistem.
              </div>
            </details>
          </div>
        </div>
      </section>

      <!-- SECTION 4: KONTAK -->
      <section id="contact" class="w-full py-24 bg-[#FAACBF]/10">
        <div class="max-w-6xl mx-auto px-6 text-center">
          <h2 class="text-3xl font-bold mb-4 text-gray-900">Kontak Pengembang</h2>
          <p class="text-gray-600 mb-12 max-w-xl mx-auto">
            Gravida dikembangkan sebagai bagian dari Penulisan Ilmiah di Program Studi Informatika,
            Universitas Gunadarma. Ada pertanyaan atau ingin berdiskusi lebih lanjut? Silakan hubungi
            pengembang melalui kanal di bawah ini.
          </p>

          <div class="bg-white rounded-[30px] p-8 md:p-12 shadow-xl border border-[#FBC3C1]/50 max-w-3xl mx-auto flex flex-col md:flex-row gap-8 items-center text-left">
            <!-- Foto Placeholder -->
            <div class="w-32 h-32 rounded-full bg-[#FBC3C1] border-4 border-[#FE81D4]/20 flex-shrink-0 flex items-center justify-center text-white text-sm font-semibold shadow-inner">
              FOTO
            </div>

            <div class="flex-1">
              <h3 class="text-2xl font-bold text-gray-900 mb-2">Raihan Ahmad Fathoni</h3>
              <p class="text-[#FE81D4] font-medium mb-4">Pengembang Gravida &middot; S1 Informatika, Universitas Gunadarma</p>
              <p class="text-gray-600 mb-6 text-sm leading-relaxed">
                "Gravida dibangun dengan harapan dapat menjadi teman bicara yang tenang dan tepercaya
                bagi ibu hamil, sekaligus menjadi kontribusi kecil untuk mendukung literasi kesehatan
                maternal dan pencegahan stunting di Indonesia."
              </p>
              <div class="flex gap-4">
                <a
                  href="mailto:raihan.ahmad@example.com"
                  class="px-6 py-2 bg-[#FBC3C1] hover:bg-[#FAACBF] text-gray-800 rounded-lg font-medium transition-colors"
                >
                  Kirim Email
                </a>
                <a
                  href="https://github.com/"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="px-6 py-2 border-2 border-[#FAACBF] text-[#FAACBF] hover:bg-[#FAACBF] hover:text-white rounded-lg font-medium transition-colors"
                >
                  GitHub
                </a>
              </div>
            </div>
          </div>
        </div>
      </section>
    `;
}