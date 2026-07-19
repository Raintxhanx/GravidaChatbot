# GravidaChatbot 🤱

> PENGEMBANGAN CHATBOT VIRTUAL PENDAMPING KEHAMILAN MENGGUNAKAN RETRIEVAL-AUGMENTED GENERATION DAN FINE-TUNING PADA MODEL QWEN2.5-7B-INSTRUCT

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Backend-Flask%203.1-red.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Penelitian%20Skripsi-orange.svg)](.)

---

## 📋 Deskripsi Singkat

**GravidaChatbot** adalah sistem tanya-jawab medis berbasis *Large Language Model* (LLM) yang dirancang khusus untuk mendampingi ibu hamil melalui edukasi preventif dan pencegahan stunting. Sistem ini beroperasi sepenuhnya dalam Bahasa Indonesia dan menargetkan domain kesehatan maternal (kehamilan, prenatal care, persalinan, hingga postpartum).

Masalah utama yang diangkat adalah rendahnya akses informasi kesehatan maternal yang terpercaya dan terpersonalisasi, serta risiko *hallucination* pada LLM umum ketika menjawab pertanyaan medis. Pendekatan yang digunakan memadukan dua teknik:

1. **Retrieval-Augmented Generation (RAG)** — mengambil konteks faktual dari *vector database* (Qdrant) menggunakan *embedder* BGE-M3 agar jawaban berakar pada dokumen medis (Alodokter & hasil wawancara tenaga kesehatan).
2. **Fine-tuning parameter-efficient (LoRA)** — memadaptasi pengetahuan dan gaya bahasa medis model `Qwen2.5-7B-Instruct` terhadap korpus maternal berbahasa Indonesia melalui Unsloth (4-bit quantization) di Google Colab.

**Kebaruan (novelty) penelitian:**
- Dataset primer baru hasil wawancara terstruktur dengan tenaga kesehatan maternal (18 pasang Q&A).
- Evaluasi kuantitatif menggunakan metrik BLEU, ROUGE-1/2/L, dan BERTScore F1.
- Perbandingan eksperimental atas **tiga konfigurasi arsitektur**: LLM *fine-tuned* tanpa RAG, LLM *fine-tuned* + RAG, dan LLM *base* + RAG.
- Konteks bahasa Indonesia dengan *guardrail* medis (filter topik di luar kehamilan → respon "abort").

---

## 🎯 Tujuan Penelitian

- Membangun sistem chatbot edukasi kesehatan maternal berbahasa Indonesia yang aman, empatik, dan berakar pada fakta medis.
- Mengimplementasikan arsitektur RAG hibrida (dense + sparse) untuk mengurangi *hallucination* LLM.
- Melakukan *fine-tuning* model `Qwen2.5-7B-Instruct` dengan metode LoRA (4-bit) guna menyesuaikan gaya bahasa konsultasi medis Indonesia.
- Mengevaluasi dan membandingkan tiga konfigurasi (LLM only, RAG only, Fine-tuned + RAG) menggunakan metrik BLEU, ROUGE, dan BERTScore.
- Menyediakan *guardrail* agar model hanya menjawab topik kehamilan & kesehatan maternal, serta merangkum riwayat percakapan otomatis.

---

## 🖼️ Tampilan Antarmuka

Berikut tangkapan layar antarmuka frontend GravidaChatbot:

| Halaman | Pratinjau |
|---|---|
| Landing Page | ![Landing Page](docs/HalamanLandingPage.png) |
| Login | ![Login](docs/HalamanLogin.png) |
| Pendaftaran | ![Pendaftaran](docs/HalamanPendaftaran.png) |
| Dashboard | ![Dashboard](docs/HalamanDashboard.png) |
| Sesi Percakapan | ![Sesi Percakapan](docs/HalamanSesiPercakapan.png) |
| Riwayat Percakapan | ![Riwayat Percakapan](docs/HalamanRiwayatPercakapan.png) |

---

## 🏗️ Arsitektur Sistem

Sistem mengikuti pola arsitektur bersih (*clean architecture*) dengan pemisahan layer: `api` (Blueprint Flask) → `domain` (use case) → `data/repo` (repository). Alur RAG pada saat inferensi:

```
User Query
   │
   ▼
[Guardrail / RAG Query Optimizer] ──LLM (Ollama)──▶ query bahasa Indonesia
   │                                           (atau "abort" jika di luar topik)
   ▼
BGE-M3 Embedder (dense 1024-dim + sparse lexical)
   │
   ▼
Qdrant Vector Search ── Hybrid (Dense + Sparse) + RRF Fusion
   │
   ▼
Top-K Context Retrieval (score tertinggi dipilih antara query user / query model)
   │
   ▼
Prompt Builder (System + User Query + Medical Context + Chat History)
   │
   ▼
LLM (Qwen / Ollama) ── Streaming (SSE) ──▶ Response ke Frontend
```

![Kerangka Kerja Arsitektur Model](docs/DiagramKerangkaKerjaArsitekturModel.png)

**Penjelasan komponen (terverifikasi dari `src/`):**
- **Embedder** — `BGEM3Embedder` (`src/data/repo/bgem.py`) membungkus `FlagEmbedding.BGEM3FlagModel` (`BAAI/bge-m3`, dimensi 1024), menghasilkan vektor *dense* dan *sparse* (lexical weights). Mendukung mode *offline* (cache di `model_data/`).
- **Vector DB** — `QdrantRepository` (`src/data/repo/qdrant.py`) membuat *collection* hibrida (named vector `dense` + `sparse`) dan melakukan *hybrid search* via `Prefetch` + `FusionQuery(fusion=Fusion.RRF)` (Reciprocal Rank Fusion).
- **Retrieval service** — `DocumentUseCases` (`src/domain/document/use_cases.py`) melakukan *chunking* (semantic, `percentile` threshold 85, ukuran 100–2000) lalu *embed* & simpan ke Qdrant; serta `retrieve()` untuk pencarian.
- **LLM service** — `ChatGeneration` (`src/data/repo/chat_generation.py`) memanggil Ollama (streaming) untuk: optimasi query RAG, generasi jawaban, ringkasan percakapan, dan pembuatan judul.
- **Orkestrasi chat** — `ChatUseCase` (`src/domain/chat/use_cases.py`) menggabungkan guardrail, retrieval, dan streaming LLM, menyimpan hasil ke PostgreSQL.

**Desain 3 Konfigurasi (dibandingkan pada evaluasi):**

1. **LLM Fine-tuned tanpa RAG** — model Qwen2.5-7B yang sudah di-fine-tune, menjawab dari *parametric knowledge*.
2. **LLM Fine-tuned + RAG** — fine-tuned model + retrieval dari Qdrant (BGE-M3).
3. **LLM Base + RAG** — model dasar (tanpa fine-tune) + retrieval.

![Visualisasi Perbandingan Arsitektur LLM](docs/VisualisasiPerbandinganArsitekturLLM.png)

---

## 🔬 Metode Penelitian

![Metode Penelitian](docs/MetodePenelitian.png)

Pendekatan penelitian terdiri dari tiga tahap utama: pengumpulan & augmentasi data, fine-tuning model (LoRA), dan evaluasi komparatif tiga konfigurasi arsitektur. Detail setiap tahap dijelaskan pada bagian [Notebook Pipeline](#-notebook-pipeline) dan [Dataset](#-dataset).

---

## 🛠️ Tech Stack

| Komponen | Teknologi (terverifikasi) | Keterangan |
|---|---|---|
| Backend Framework | **Flask 3.1** + Flasgger 0.9.7 | API REST + dokumentasi Swagger (`/apidocs/`) |
| LLM Runtime | **Ollama** (`ollama` 0.6.2) | Inferensi streaming; model bawaan `qwen2.5:0.5b` (`OLLAMA_MODEL`) |
| LLM Base / Fine-tune | **Qwen2.5-7B-Instruct** (`unsloth/Qwen2.5-7B-Instruct-bnb-4bit`) | Fine-tune via Unsloth (Colab T4) |
| Fine-tuning Method | **LoRA** via **Unsloth** + 4-bit quantization | `r=16`, `alpha=16`, `adamw_8bit` |
| Embedder | **BGE-M3** (`FlagEmbedding` 1.4, `BAAI/bge-m3`) | Hybrid dense (1024) + sparse |
| Vector Database | **Qdrant** (`qdrant-client` 1.17.1) | Hybrid search + RRF |
| Relational DB | **PostgreSQL** + SQLAlchemy 2.0 + Flask-SQLAlchemy | Chat history, user, collection |
| Auth | **PyJWT** (Bearer) + ApiKey | `JWT_SECRET_KEY`, `API_KEY` |
| Orchestration | LangChain 1.3 (`langchain-text-splitters`) | Chunking & embedding wrapper |
| Containerization | **Docker** + **Docker Compose** | Multi-stage (Node frontend + Python 3.11 slim) |
| Training Platform | Google Colab (NVIDIA Tesla T4, 16 GB VRAM) | `notebook/TrainingQwenModel_v2.ipynb` |
| Frontend | React (Node 22) — *ada namun bukan fokus dokumentasi* | Build di-copy ke `dist/` |

> Dependensi lengkap & versi terkunci ada di `requirements.txt` (torch 2.11, transformers 5.8, peft 0.19, datasets 5.0, scikit-learn, dll.).

---

## 📁 Struktur Direktori

```
.
├── main.py                     # Entry point Flask; wiring repository → use case → blueprint
├── requirements.txt            # Dependency backend (Python)
├── Dockerfile                  # Multi-stage: build frontend (node) + backend (python:3.11-slim)
├── docker-compose.yaml         # Service "app" (port 8021:5000) + volume model_data
├── .env.example                # Template environment variable
├── src/
│   ├── api/v1/                 # Blueprint Flask: auth, user, chat, message, document, collection
│   ├── data/
│   │   ├── models/             # SQLAlchemy models: chats, messages, users, collections, settings
│   │   └── repo/               # Repository: bgem (embedder), qdrant, chat_generation, database
│   ├── domain/                 # Use cases & interface tiap fitur (auth, chat, document, ...)
│   └── util/                   # Middleware decorator (token/api key) & password hasher
├── notebook/
│   ├── KnowledgeIngest.ipynb   # Ingestion 300 Alodokter + 18 primer + augmentasi back-translation
│   └── TrainingQwenModel_v2.ipynb  # LoRA fine-tuning Qwen2.5-7B (Unsloth, Colab T4)
├── data_collection/
│   ├── main.py                 # Scraper daftar topik Alodokter (topic-tag/kehamilan)
│   ├── scrape.py               # Scraper isi (pertanyaan + jawaban dokter) per URL
│   ├── *.csv                   # Hasil scraping & dataset (lihat bawah)
│   └── TranscriptWawancaraCleaned.txt  # Transkrip wawancara tenaga kesehatan (primer)
├── inference_model_result/     # CSV hasil evaluasi 3 konfigurasi + PerbandinganModel.png
├── model_data/                 # Cache model BGE-M3 (offline)
├── merge_model/                # hasil merge model
└── frontend/                   # Aplikasi web
```

---

## 📓 Notebook Pipeline

Urutan eksekusi notebook yang benar (untuk replikasi):

**1. `notebook/KnowledgeIngest.ipynb`** — *Data Preparation & Ingestion*
- Memuat `hasil_scraping_alodokter.csv` (300 data) dan `dataset_primer_parafase.csv` (18 data).
- Melakukan **back-translation / parafrase** via `deep_translator` (Google Translate) ke 4 bahasa pivot: Inggris (`ID-EN-ID`), Jerman (`ID-DE-ID`), Jepang (`ID-JA-ID`), Melayu (`ID-MS-ID`), menghasilkan `hasil_scraping_alodokter_testset.csv` (100 sampel acak, `random_state=42`, masing-masing 25 per bahasa).
- Mengirim dokumen ke endpoint `POST /api/v1/documents/ingest` (Alodokter → 300 dokumen berhasil, 4 gagal lalu di-*retry*; primer → 18 dokumen).

**2. `notebook/TrainingQwenModel_v2.ipynb`** — *Fine-tuning LLM*
- Environment: Google Colab, GPU Tesla T4 (±14.5 GB), Unsloth 2026.6.9, CUDA 12.8.
- Load `unsloth/Qwen2.5-7B-Instruct-bnb-4bit` (4-bit), setup LoRA, training dengan `SFTTrainer`/`SFTConfig` (TRL), lalu `FastLanguageModel.for_inference` + `save_pretrained`.
- Menghasilkan model LoRA siap *merge*/deploy ke Ollama untuk konfigurasi "Fine-tuned + RAG".
- Visualisasi *training loss* tersimpan di `docs/GrafLossFunctionFineTuningModel.png`:

![Graf Loss Function Fine-Tuning](docs/GrafLossFunctionFineTuningModel.png)

**3. Inferensi & Evaluasi** (output di `inference_model_result/`)
- Menjalankan 3 konfigurasi terhadap ~50 data uji, membandingkan jawaban model vs "Jawaban Dokter" (ground truth).
- Hasil per konfigurasi: `hasil_evaluasi_llm_50_data.csv`, `hasil_evaluasi_llm_base.csv`, `hasil_evaluasi_llm_dan_rag_50_data.csv`.

---

## 📊 Dataset

| Sumber | Jumlah | Keterangan |
|---|---|---|
| **Primer** — wawancara terstruktur (20 menit) dengan tenaga kesehatan maternal | **18 pasang Q&A** | `data_collection/dataset_primer_parafase.csv` & `TranscriptWawancaraCleaned.txt` |
| **Sekunder** — web scraping Alodokter (`komunitas/topic-tag/kehamilan`) | **300 pasang Q&A** | Diambil **16 Mei 2026**; `hasil_scraping_alodokter.csv` (bersih: `..._merged_cleaned.csv`) |
| **Augmentasi** — back-translation | 4 bahasa pivot | ID→EN/DE/JA/MS→ID (parafrase) |
| **Data uji** | **50 data** | Dari gabungan dataset ter-augmentasi (`hasil_scraping_alodokter_testset.csv` = 100 sampel; subset 50 untuk evaluasi) |

**Format data** (CSV): `Topik`, `Pertanyaan`, `Jawaban Dokter`, `URL`, `Metode_Augmentasi`.

**Alur pengumpulan** (`data_collection/`):
- `main.py` — mengambil daftar topik (title + href + full_url) dari halaman paginasi Alodokter dengan jeda *rate-limit* 2 detik.
- `scrape.py` — mengekstrak `<detail-topic>` (pertanyaan) dan `<doctor-topic>` (jawaban dokter) per URL, decode HTML → teks bersih, jeda 5 detik.

---

## ⚙️ Konfigurasi & Environment Variables

Salin `.env.example` → `.env` dan isi nilainya. Variabel wajib (dari `.env.example`):

| Variabel | Default / Contoh | Keterangan |
|---|---|---|
| `QDRANT_URL` | `https://...` | URL instance Qdrant |
| `QDRANT_API_KEY` | `secret` | API key Qdrant |
| `QDRANT_PORT` | `443` | Port Qdrant |
| `DATABASE_URL` | `postgresql://user:pass@host:5432/db` | Koneksi PostgreSQL |
| `API_KEY` | `secret` | ApiKey untuk endpoint admin (`ApiKey <key>`) |
| `ADMIN_PASSWORD` | `secretadmin` | Password admin awal (auto-populate) |
| `OFFLINE_MODE` | `False` | Mode offline (model BGE-M3 dari cache lokal) |

Variabel tambahan yang digunakan di kode (`main.py` / `chat_generation.py`) — wajib ditambahkan ke `.env`:

| Variabel | Default | Keterangan |
|---|---|---|
| `JWT_SECRET_KEY` | `super-secret-key-change-me` | Secret penandatanganan JWT |
| `OLLAMA_BASE_URL` | `localhost:11434` | Base URL server Ollama |
| `OLLAMA_MODEL` | `qwen2.5:0.5b` | Nama model LLM (bisa diganti `qwen_gravida:latest`, dll.) |
| `CF_CLIENT_ID` | `none` | Cloudflare Access Client Id (jika Ollama di-*tunnel*) |
| `CF_CLIENT_SECRET` | `none` | Cloudflare Access Client Secret |

---

## 🚀 Cara Menjalankan

### Prasyarat
- Python **3.11**
- PostgreSQL (eksternal) — `docker-compose` mengharapkan network `postgres-docker_pg_network`
- Ollama (untuk inferensi LLM) + model (`ollama pull qwen2.5:0.5b`)
- Qdrant (instance/cloud)
- Docker & Docker Compose (opsional, untuk deployment)

### Instalasi (Local)

```bash
# 1. Buat virtual environment
python -m venv venv
source venv/Scripts/activate        # Windows
# source venv/bin/activate          # Linux/Mac

# 2. Install dependency
pip install -r requirements.txt

# 3. Siapkan environment
cp .env.example .env
# edit .env sesuai konfigurasi Qdrant, PostgreSQL, Ollama

# 4. Jalankan server (Flask, port 5000)
python main.py
```

Server berjalan di `http://localhost:5000`. Dokumentasi API (Swagger) di `http://localhost:5000/apidocs/`, health check di `/health`.

### Menjalankan dengan Docker

```bash
# Pastikan file .env sudah ada, lalu:
docker compose up --build
```

- Container `pregnancy_app` mengekspos port **8021** → 5000.
- Folder `model_data` di-mount sebagai volume (cache BGE-M3).
- Frontend (React) di-build pada stage pertama dan disajikan dari `dist/`.

### Menjalankan Notebook (Google Colab)

1. Buka `notebook/TrainingQwenModel_v2.ipynb` di Colab, pilih GPU **T4**.
2. Jalankan sel berurutan: install Unsloth → load model 4-bit → setup LoRA → tokenize (ChatML) → `SFTTrainer` (150 steps) → simpan adapter.
3. (Opsional) `notebook/KnowledgeIngest.ipynb` untuk ingest & augmentasi data ke backend lokal/cloud.

---

## 📈 Hasil Evaluasi Model

Sistem dievaluasi dengan membandingkan jawaban model terhadap *ground truth* ("Jawaban Dokter") untuk **~50 data uji** menggunakan metrik BLEU, ROUGE-1/2/L, dan BERTScore F1. Tiga konfigurasi dibandingkan:

| Konfigurasi | BLEU | ROUGE-1 | ROUGE-2 | ROUGE-L | BERTScore F1 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| LLM Base + RAG | 0.2288 | 0.5237 | 0.2850 | 0.3705 | 0.7573 |
| LLM Fine-tuned (LoRA) tanpa RAG | 0.1264 | 0.4522 | 0.1422 | 0.2384 | 0.7460 |
| **LLM Fine-tuned + RAG** | **0.3279** | **0.6175** | **0.3651** | **0.4437** | **0.8122** |

## Kesimpulan
Berdasarkan data di atas, konfigurasi **LLM Fine-tuned + RAG** memberikan performa paling optimal dan unggul mutlak di seluruh metrik evaluasi. Kombinasi antara penyesuaian gaya/format lewat *Fine-Tuning* serta penyediaan basis pengetahuan eksternal lewat *RAG* menghasilkan jawaban dengan tingkat akurasi leksikal dan semantik tertinggi.

**Parameter training (konfigurasi terbaik Fine-tuned + RAG):**

| Parameter | Nilai |
|---|---|
| `max_steps` | 150 |
| `learning_rate` | 2e-4 |
| `per_device_train_batch_size` | 1 |
| `gradient_accumulation_steps` | 8 |
| `warmup_steps` | 5 |
| `optim` | `adamw_8bit` |
| LoRA `r` / `alpha` / `dropout` | 16 / 16 / 0 |
| `max_seq_length` | 1024 |
| `seed` | 3407 |

---

## 🔌 Dokumentasi API

Base URL: `/api/v1`. Semua endpoint (kecuali `/health`, `/`, `/documents/health`) memerlukan autentikasi **Bearer JWT** (`Authorization: Bearer <token>`) atau **ApiKey** (`Authorization: ApiKey <key>`). Dokumentasi interaktif tersedia di `/apidocs/` (Flasgger).

### Auth (`/auth`)

| Method | Path | Deskripsi | Body |
|---|---|---|---|
| POST | `/auth/register` | Registrasi user baru | `{ username, email, password, ... }` |
| POST | `/auth/login` | Login → JWT token | `{ email/username, password }` |
| GET | `/auth/me` | Profil user dari token | — |

### Chat (`/chats`)

| Method | Path | Deskripsi | Body / Response |
|---|---|---|---|
| POST | `/chats` | Buat sesi chat baru (**streaming SSE**). Jalur: guardrail → RAG optimizer → retrieve → LLM streaming. | Body: `{ "query": "..." }` → stream `metadata` + `token` |
| GET | `/chats` | Daftar sesi chat user (paginasi, search, filter tanggal) | Query: `search, limit, skip, start_date, end_date` |
| GET | `/chats/<chat_id>` | Detail sesi chat | — |
| PATCH | `/chats/<chat_id>` | Ubah judul chat | `{ "title": "..." }` |
| POST | `/chats/<chat_id>/summary` | Buat ringkasan otomatis percakapan (LLM) | — |

### Message (`/chats/<chat_id>/messages`)

| Method | Path | Deskripsi |
|---|---|---|
| POST | `.../messages` | Kirim pesan lanjutan (streaming + RAG) |
| POST | `.../messages/regenerate` | Regenerasi jawaban asisten |
| GET | `.../messages` | Ambil riwayat pesan dalam sesi |

### Document (Admin)

| Method | Path | Deskripsi | Auth |
|---|---|---|---|
| POST | `/documents/ingest` | Ingest 1 dokumen ke Qdrant (embed + chunk + store) | Admin |
| POST | `/documents/retrieve` | Hybrid search konteks (`query`, `limit`) | Admin |
| GET | `/documents/health` | Health check layanan dokumen | Publik |

### Collection (Admin)

| Method | Path | Deskripsi |
|---|---|---|
| POST | `/collections` | Buat collection Qdrant baru |
| GET | `/collections` | Daftar collection |
| GET | `/collections/active` | Collection aktif |
| POST | `/collections/<id>/active` | Set collection aktif |
| DELETE | `/collections/<id>` | Hapus collection |

### User (Admin)

| Method | Path | Deskripsi |
|---|---|---|
| GET | `/user` | Profil user terautentikasi |
| GET | `/users` | Daftar seluruh user (admin) |

### Root

| Method | Path | Deskripsi |
|---|---|---|
| GET | `/health` | Health check server (`{"success": true, ...}`) |
| GET | `/` | Menyajikan frontend (SPA) |

---

## ⚠️ Keterbatasan & Catatan Penelitian

- **Kapasitas kontekstual riwayat**: Ringkasan percakapan hanya mengambil **20 pesan** (1 pesan user pertama + 19 pesan terbaru); bukan seluruh histori tanpa batas.
- **Training steps terbatas**: Fine-tuning hanya **150 steps** dengan dataset relatif kecil (~314 baris hasil augmentasi) — bukan pelatihan penuh; karenanya kemampuan generalisasi terbatas.
- **Dataset terbatas & domain spesifik**: 18 data primer + 300 data sekunder (Alodokter); topik di luar kehamilan sengaja diblokir (*guardrail* "abort").
- **Model produksi vs riset**: Backend menggunakan Ollama (bawaan `qwen2.5:0.5b`); model `Qwen2.5-7B` hasil fine-tune dievaluasi di luar deployment harian.
- **Hallucination risk**: Meski ada RAG + instruksi "hanya jawab dari konteks", sistem tetap memerlukan verifikasi tenaga medis profesional — **bukan pengganti konsultasi dokter**.
- **Dependensi eksternal**: Membutuhkan instance Qdrant, PostgreSQL, dan Ollama yang terpisah (tidak dibundel dalam satu container).
- **Fitur belum selesai** (lihat `todo.txt`): penanganan pesan tanpa query RAG (regenerate + new message), dan logika "abort" saat asisten tidak membutuhkan RAG (mis. "halo!").

---

## 🗂️ Referensi & Sitasi

- **Qwen2.5** — QwenLM, *Qwen2.5 Technical Report* (LLM base & instruct).
- **Unsloth** — *Unsloth: Efficient LLM Fine-tuning* (LoRA 4-bit, GitHub `unslothai/unsloth`).
- **BGE-M3** — Chen et al., *BGE M3-Embedding: Multi-Lingual, Multi-Functionality, Multi-Granularity* (FlagEmbedding / BAAI).
- **Qdrant** — *Qdrant Vector Database* (hybrid search & RRF).
- **RAG** — Lewis et al., *Retrieval-Augmented Generation for Knowledge-Intensive NLP*.
- **LoRA** — Hu et al., *LoRA: Low-Rank Adaptation of Large Language Models*.
- **Metrik** — BLEU (Papineni et al.), ROUGE (Lin), BERTScore (Zhang et al.).
- **Dataset sekunder** — Alodokter (`https://www.alodokter.com`, komunitas topik kehamilan), diakses 16 Mei 2026.
- **Framework** — Flask, Flasgger, SQLAlchemy, LangChain, PyTorch, Transformers (HuggingFace), TRL.

---

## 👤 Informasi Penelitian

| Item | Keterangan |
|---|---|
| Nama Sistem | GravidaChatbot |
| Jenis | Penelitian Ilmiah (Penulisan Ilmiah / Skripsi) |
| Domain | Kesehatan maternal — pendampingan ibu hamil & pencegahan stunting |
| Bahasa | Indonesia |
| Platform Training | Google Colab (NVIDIA Tesla T4) |
| Tahun | 2026 |

---