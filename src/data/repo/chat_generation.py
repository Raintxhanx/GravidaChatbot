import json
import logging
import ollama
from typing import List, Any
from pydantic import BaseModel, Field

# ==========================================
# DTO (Sesuai dengan blueprint sebelumnya)
# ==========================================
class MessageContextDTO(BaseModel):
    """Digunakan khusus untuk menyusun history payload ke LLM"""
    role: str = Field(..., description="'system', 'user', atau 'assistant'")
    content: Any = Field(..., description="Teks pesan atau struktur JSON content")


# ==========================================
# Concrete Chat Generation Service (Simulation)
# ==========================================
class ChatGeneration:
    """Concrete Object untuk simulasi interaksi dengan Ollama & RAG Engine"""
    def __init__(self, ollama_url: str, cf_id: str, cf_secret: str, model_name: str = "qwen2.5:0.5b"):
        self.model_name = model_name
        
        # Setup custom headers untuk menembus Cloudflare Tunnel
        headers = {
            "CF-Access-Client-Id": cf_id,
            "CF-Access-Client-Secret": cf_secret
        }
        
        # Inisialisasi official Ollama client dengan base_url dan headers khusus
        self.client = ollama.Client(
            host=ollama_url,
            headers=headers
        )

    def _validate_and_log_payload(self, method_name: str, history: List[MessageContextDTO]) -> None:
        """
        Helper untuk memastikan input dari service lain (Chat/Message Service) 
        sudah masuk dengan struktur, tipe data, dan role yang valid.
        """        
        if not history:
            raise ValueError(f"❌ [{method_name}] Error: History payload tidak boleh kosong!")

        logging.info(f"🔍 [{method_name}] Memvalidasi {len(history)} pesan dalam history...")
        
        for index, message in enumerate(history):
            # 1. STRICT CHECK: Hentikan sistem jika tipe data salah!
            if not isinstance(message, MessageContextDTO):
                error_msg = f"❌ [INDEX {index}] Gagal validasi: Objek bukan instance dari MessageContextDTO! Terdeteksi tipe: {type(message)}"
                logging.error(error_msg)
                raise TypeError(error_msg) # Menghindari AttributeError di fungsi utama
                
            # 2. VALIDASI ROLE: Memastikan role sesuai standard LLM
            allowed_roles = ["system", "user", "assistant"]
            if message.role not in allowed_roles:
                error_msg = f"❌ [INDEX {index}] Gagal validasi: Role '{message.role}' tidak dikenali oleh Ollama!"
                logging.error(error_msg)
                raise ValueError(error_msg)
                
            # 3. LOGGING VISUAL: Menggunakan logger agar rapi di konsol server
            content_snippet = str(message.content)[:50] + "..." if len(str(message.content)) > 50 else message.content
            logging.info(f"   [{index}] Role: {message.role:<10} | Content: {content_snippet}")
            
        logging.info(f"{'='*65}\n")

    # def chat_completion(self, history: List[MessageContextDTO]) -> str:
    #     """Mengirimkan seluruh history konteks terpilih ke API Ollama Riil"""
    #     # 1. Jalankan fungsi helper validasi bawaan Anda
    #     self._validate_and_log_payload("chat_completion", history)
        
    #     # 2. Konversi DTO menjadi format array of dict yang dipahami oleh Ollama SDK
    #     #    Format: [{"role": "user", "content": "..."}, ...]
    #     formatted_messages = [
    #         {"role": msg.role, "content": msg.content}
    #         for msg in history
    #     ]
        
    #     try:
    #         print(f"🔮 [Ollama Engine] Mengirim permintaan ke model: '{self.model_name}' via Cloudflare Tunnel...")
            
    #         # 3. Panggil Official Ollama Client dengan parameter inferensi sesuai blueprint
    #         response = self.client.chat(
    #             model=self.model_name,
    #             messages=formatted_messages,
    #             options={
    #                 "temperature": 0.3,
    #                 "top_p": 0.8,
    #                 "repeat_penalty": 1.1,
    #                 "stop": ["<|im_end|>", "<|im_start|>"]
    #             }
    #         )
            
    #         # 4. Ekstraksi konten teks dari response objek Ollama
    #         ai_response = response.get("message", {}).get("content", "")
            
    #         if not ai_response:
    #             print("⚠️ [Ollama Engine] Peringatan: Respon dari model kosong.")
                
    #         return ai_response

    #     except Exception as e:
    #         # Handle error jika Cloudflare Tunnel putus atau Ollama server mati
    #         print(f"❌ [Ollama Engine] Error Terjadi saat Chat Completion: {str(e)}")
    #         raise e

    def chat_completion_stream(self, history: List[MessageContextDTO]):
        """Mengirimkan seluruh history konteks ke API Ollama secara Streaming"""
        # 1. Jalankan fungsi helper validasi bawaan Anda
        self._validate_and_log_payload("chat_completion_stream", history)
        
        # 2. Konversi DTO menjadi format array of dict
        formatted_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in history
        ]
        
        try:
            print(f"🔮 [Ollama Engine] Membuka stream ke model: '{self.model_name}'...")
            
            # 3. Panggil Official Ollama Client dengan opsi stream=True
            response_stream = self.client.chat(
                model=self.model_name,
                messages=formatted_messages,
                options={
                    "temperature": 0.3,
                    "top_p": 0.8,
                    "repeat_penalty": 1.1                },
                stream=True  # 🔥 AKTIFKAN STREAMING
            )
            
            # 4. Iterasi setiap chunk token yang dikirim oleh Ollama
            for chunk in response_stream:
                token = chunk.message.content if chunk.message else ""
                if token:
                    yield token

        except Exception as e:
            print(f"❌ [Ollama Engine] Error Terjadi saat Stream Completion: {str(e)}")
            raise e

    # def query_retrieval_generator(self, history: List[MessageContextDTO]) -> str:
    #     """Menghasilkan keyword pencarian ke Qdrant dengan Guardrail Medis & Kehamilan Ketat"""
    #     # 1. Jalankan helper validasi bawaan Anda
    #     self._validate_and_log_payload("query_retrieval_generator", history)
        
    #     # 2. System Prompt khusus Inggris untuk Guardrail + Keyword Extraction
    #     system_prompt_extractor = (
    #         "You are an expert medical search query optimizer for a RAG system specializing strictly in maternal health and pregnancy.\n"
    #         "Your task is to analyze the user's request and transform it into a clear, highly specific natural language question in Indonesian. "
    #         "Because the target vector database contains detailed medical consultations (Patient Questions and Doctor Answers), structuring the query as a complete question ensures the highest semantic retrieval accuracy.\n\n"
    #         "CRITICAL SECURITY GUARDRAILS:\n"
    #         "1. You MUST ONLY service queries related to medical health, specifically focusing on pregnant women (ibu hamil), pregnancy symptoms, prenatal care, or fetal development.\n"
    #         "2. If the user's prompt is OUTSIDE of medical health or pregnancy context (e.g., casual chit-chat, IT/coding, general cooking, math, generic jokes), you MUST reply with exactly one word: \"abort\". Do not include any other words, punctuation, or explanations.\n"
    #         "3. If the query is valid, output ONLY the optimized medical question in Indonesian (e.g., \"Berapa kenaikan berat badan yang ideal untuk ibu hamil di trimester ketiga?\"). Do not wrap it in quotes, and do not include any introductory text, separate keywords, or explanations."
    #     )
        
    #     # 3. Susun array percakapan khusus untuk Ollama
    #     #    Kita tempatkan system_prompt_extractor di paling atas
    #     formatted_messages = [{"role": "system", "content": system_prompt_extractor}]
        
    #     # Masukkan riwayat pesan user/assistant (abaikan system prompt asli DB agar tidak bentrok)
    #     for msg in history:
    #         if msg.role != "system":
    #             formatted_messages.append({"role": msg.role, "content": msg.content})
        
    #     try:
    #         print(f"🔮 [Ollama Engine] Mengevaluasi konteks & mengekstrak RAG Query...")
            
    #         response = self.client.chat(
    #             model=self.model_name,
    #             messages=formatted_messages,
    #             options={
    #                 "temperature": 0.0,   
    #                 "top_p": 0.1,
    #             }
    #         )
            
    #         # 💡 SINKRONISASI: Menggunakan dot notation Pydantic
    #         raw_output = response.message.content.strip() if response.message else ""
    #         cleaned_query = raw_output.strip("'\"")
            
    #         print(f"🔮 [Ollama Engine] Hasil Evaluasi Generator: \"{cleaned_query}\"")
    #         return cleaned_query

    #     except Exception as e:
    #         print(f"❌ [Ollama Engine] Error pada query_retrieval_generator: {str(e)}")
    #         raise e

    # def summarize(self, history: List[MessageContextDTO]) -> str:
    #     """Simulasi merangkum chat untuk kolom deskripsi room - FIXED VERSION"""
    #     self._validate_and_log_payload("summarize", history)
        
    #     system_prompt_summarizer = (
    #         "You are an expert AI summarizer. Your task is to analyze the chat history and generate a highly concise room description in Indonesian.\n\n"
    #         "CRITICAL RULES:\n"
    #         "1. MAX LENGTH: Your summary MUST be a maximum of 3 sentences and STRICTLY UNDER 50 words.\n"
    #         "2. You MUST generate a response. Do not leave it empty.\n"
    #         "3. Write in Indonesian language only."
    #     )

    #     formatted_messages = [{"role": "system", "content": system_prompt_summarizer}]

    #     for msg in history:
    #         if msg.role != "system":
    #             formatted_messages.append({"role": msg.role, "content": msg.content})

    #     formatted_messages.append({
    #         "role": "user", 
    #         "content": "Buatkan rangkuman maksimal 3 kalimat dari seluruh percakapan kita di atas."
    #     })

    #     try:            
    #         print(f"🔮 [Ollama Engine] Mengirim request summarize ke model: {self.model_name}...")
            
    #         response = self.client.chat(
    #             model=self.model_name,
    #             messages=formatted_messages,
    #             options={
    #                 "temperature": 0.3,      
    #                 "top_p": 0.5,            
    #                 "num_ctx": 4096,
    #                 "num_predict": 100,      
    #                 "repeat_penalty": 1.1    
    #             }
    #         )
            
    #         logging.debug(f"[OLLAMA RAW RESPONSE] {response.model_dump_json(indent=2)}")
            
    #         # 💡 PERBAIKAN 1: Mengakses content dengan Dot Notation khas Pydantic
    #         raw_output = response.message.content.strip() if response.message else ""
    #         cleaned_query = raw_output.strip("'\"")
            
    #         if not cleaned_query:
    #             # 💡 PERBAIKAN 2: Gunakan model_dump().keys() agar tidak error AttributeError
    #             response_keys = list(response.model_dump().keys())
    #             logging.warning(
    #                 f"[Ollama Engine] ⚠️ Empty response from model. "
    #                 f"Raw output: '{raw_output}' | Response keys: {response_keys}"
    #             )
    #             # Fallback: Generate basic summary dari pesan pertama & terakhir
    #             if len(history) >= 2:
    #                 first_user_msg = next((h.content for h in history if h.role == "user"), "Chat")
    #                 return f"Konsultasi tentang: {str(first_user_msg)[:50]}..."
    #             else:
    #                 return "Sesi chat dengan dokter Gravida"
            
    #         print(f"✅ [Ollama Engine] Summary Dibuat : \"{cleaned_query}\"")
    #         return cleaned_query

    #     except Exception as e:
    #         logging.error(f"❌ [Ollama Engine] Error pada summarize: {str(e)}", exc_info=True)
    #         # ✅ ADDED: Fallback instead of raising exception
    #         if len(history) >= 2:
    #             first_user_msg = next((h.content for h in history if h.role == "user"), "Chat")
    #             return f"Konsultasi tentang: {str(first_user_msg)[:50]}..."
    #         return "Sesi chat dengan dokter Gravida"

    def title_generation(self, query: str) -> str:
        """Generasi otomatis judul chat berdasarkan query pertama user"""        

        words = query.split()
        short_title = " ".join(words[:20]) if len(words) >= 20 else query
        
        print(f"🔮 [Ollama Engine] Chat baru tergenerate dengan judul: \"{short_title}\"")
        return short_title

    def query_retrieval_generator(self, history: List[MessageContextDTO]):
        """Menghasilkan keyword/pertanyaan optimasi untuk pencarian RAG (Streaming)"""
        self._validate_and_log_payload("query_retrieval_generator", history)

        try:
            print(f"🔮 [Ollama Engine] Membuka stream ke model untuk RAG Optimizer: '{self.model_name}'...")

            # System prompt dipertahankan persis (tidak diubah)
            system_prompt = """
                Anda adalah spesialis optimasi kueri pencarian medis untuk sistem Retrieval-Augmented Generation (RAG) yang berfokus pada kesehatan ibu dan kehamilan.
                Tugas Anda adalah menganalisis permintaan pengguna dan mengubahnya menjadi satu pertanyaan bahasa Indonesia yang jelas, lengkap, spesifik, dan mudah dipahami. Basis data yang digunakan berisi konsultasi medis mendalam dalam format Pertanyaan Pasien dan Jawaban Dokter. Oleh karena itu, kueri harus dirumuskan sebagai pertanyaan alami yang utuh agar menghasilkan akurasi pencarian semantik yang optimal.
                Ketentuan keamanan:
                1. Anda hanya boleh memproses permintaan yang berkaitan dengan kesehatan, terutama yang berhubungan dengan kehamilan, kesehatan ibu, gejala kehamilan, perawatan prenatal, persalinan, atau perkembangan janin.
                2. Jika permintaan pengguna tidak berkaitan dengan konteks kesehatan atau kehamilan (misalnya teknologi, pemrograman, hiburan, matematika, memasak, percakapan umum, atau topik lainnya), Anda wajib menjawab dengan tepat satu kata berikut:
                abort
                3. Untuk permintaan yang valid, keluarkan hanya satu pertanyaan medis yang telah dioptimalkan dalam bahasa Indonesia.
                4. Jangan menambahkan penjelasan, salam, komentar, daftar kata kunci, tanda kutip, atau teks lain di luar pertanyaan yang dihasilkan.
                Contoh keluaran yang benar:
                Berapa kenaikan berat badan yang ideal pada ibu hamil trimester ketiga?
                Contoh keluaran yang salah:
                Pertanyaan yang dioptimalkan:
                "Berapa kenaikan berat badan yang ideal pada ibu hamil trimester ketiga?"
                Kata kunci: berat badan, trimester ketiga
            """

            # --- PERBAIKAN STRUKTUR MESSAGES ---
            messages = [{"role": "system", "content": system_prompt}]

            # Masukkan riwayat pesan lama (kecuali pesan paling terakhir) secara natural
            for msg in history:
                if msg.role != "system":
                    messages.append(
                        {
                            "role": msg.role,
                            "content": str(msg.content).strip(),
                        }
                    )

            isolated_content = (
                "Tugas Anda adalah membuat satu pertanyaan yang paling relevan dan diperlukan "
                "untuk memperoleh informasi tambahan yang dibutuhkan agar dapat menjawab pertanyaan "
                "berdasarkan konteks percakapan sebelumnya. "
                "Balas hanya dalam bentuk pertanyaan, tanpa penjelasan tambahan, "
                "dan tetap perhatikan serta terapkan ketentuan keamanan yang telah ditetapkan sebelumnya."
            )
            messages.append(
                {
                    "role": "user",
                    "content": isolated_content,
                }
            )
            # ------------------------------------

            response_stream = self.client.chat(
                model=self.model_name,
                messages=messages,
                options={
                    "temperature": 0.0,
                    "top_p": 0.1,
                    "stop": ["<|im_end|>", "<|im_start|>", "\n"],
                },
                stream=True
            )

            for chunk in response_stream:
                token = chunk.message.content if chunk.message else ""
                if token:
                    yield token
        except Exception as e:
            print(f"❌ [Ollama Engine] Error Terjadi saat Stream RAG Query: {str(e)}")
            raise e

    def summarize(self, history: List[MessageContextDTO]):
        """Membuat ringkasan riwayat percakapan secara streaming untuk deskripsi room"""
        # 1. Validasi input payload menggunakan helper bawaan
        self._validate_and_log_payload("summarize", history)
        
        try:
            print(f"🔮 [Ollama Engine] Membuka stream ke model untuk Summarizer: '{self.model_name}'...")

            system_prompt_summarizer = """
                Anda adalah AI yang ahli dalam membuat ringkasan percakapan.

                Tugas Anda adalah menganalisis seluruh riwayat percakapan dan menghasilkan deskripsi singkat yang mewakili topik utama pembahasan dalam bahasa Indonesia.

                Ketentuan:
                1. Ringkasan wajib dibuat dan tidak boleh kosong.
                2. Ringkasan harus sangat singkat, padat, dan informatif.
                3. Panjang ringkasan maksimal 3 kalimat dan tidak boleh melebihi 50 kata.
                4. Fokus hanya pada inti pembahasan yang paling penting.
                5. Jangan menambahkan informasi yang tidak terdapat dalam percakapan.
                6. Hasil akhir harus ditulis sepenuhnya dalam bahasa Indonesia.
                7. Keluarkan hanya ringkasan tanpa judul, penjelasan, atau teks tambahan lainnya.
            """

            # --- PERBAIKAN STRUKTUR MESSAGES ---
            messages = [{"role": "system", "content": system_prompt_summarizer}]

            # Masukkan seluruh riwayat pesan secara natural sebagai konteks
            for msg in history:
                if msg.role != "system":
                    messages.append(
                        {
                            "role": msg.role,
                            "content": str(msg.content).strip(),
                        }
                    )

            # ISOLASI INSTRUKSI TERAKHIR: Berikan perintah eksplisit di akhir percakapan 
            # agar LLM tahu tugas akhirnya setelah membaca riwayat di atas.
            isolated_content = """
                Berdasarkan seluruh percakapan sebelumnya di atas, buatkan ringkasan, deskripsi singkat, ataupun rangkuman maksimal 3 kalimat. 
                Pastikan Anda hanya membalas dengan teks ringkasan tanpa penjelasan atau teks tambahan.

                Contoh keluaran yang diharapkan:
                Tekanan darah tinggi (hipertensi) pada ibu hamil bisa berbahaya jika tidak terkontrol, namun banyak jenisnya seperti hipertensi gestasional dan preeklamsia. Kondisi ini memerlukan pemantauan rutin ke dokter kandungan agar dapat ditangani dengan baik untuk menjaga kesehatan ibu dan janin.
            """
            messages.append(
                {
                    "role": "user",
                    "content": isolated_content,
                }
            )
            # ------------------------------------

            # 3. Panggil API Chat Ollama dengan konfigurasi Streaming
            response_stream = self.client.chat(
                model=self.model_name,
                messages=messages,
                options={
                    "temperature": 0.3,
                    "top_p": 0.5,
                    "num_ctx": 4096,
                    "num_predict": 100,
                    "repeat_penalty": 1.1
                },
                stream=True  # 🔥 AKTIFKAN STREAMING
            )

            # 4. Yield token secara beruntun (Streaming)
            for chunk in response_stream:
                token = chunk.message.content if chunk.message else ""
                if token:
                    yield token

        except Exception as e:
            print(f"❌ [Ollama Engine] Error Terjadi saat Stream Summarizer: {str(e)}")
            raise e

        except Exception as e:
            print(f"❌ [Ollama Engine] Error Terjadi saat Stream Summarize: {str(e)}")
            raise e