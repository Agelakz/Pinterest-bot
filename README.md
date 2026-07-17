# Pinterest Affiliate Bot 📌🤖

Bot automasi E2E (End-to-End) untuk membangun aliran pasif *affiliate marketing* di Pinterest. Bot ini akan otomatis mencari produk dari Shopee, mencari video relevan (tanpa watermark) dari TikTok, men-generate copywriting SEO dengan Gemini AI, dan mem-publish-nya ke Pinterest Board yang sesuai.

## ✨ Fitur Utama
* **Shopee to TikTok Pipeline:** Otomatis mencari produk affiliate dan mencocokkan video viral di TikTok.
* **Smart Category Intelligence:** Auto-assign board (contoh: "Skintific Cushion" masuk ke board "Makeup"). Jika board belum ada, otomatis dibuatkan.
* **AI SEO Copywriting:** Prompt AI khusus bergaya "Kreator Konten" yang natural, soft-selling, dan teroptimasi untuk algoritma Pinterest.
* **Anti-Banned WAF Bypass:** Dilengkapi curl_cffi untuk melewati blokiran Akamai (403 Forbidden) di Pinterest.
* **Watermark Penalty:** Mengeliminasi video TikTok yang terindikasi *hard-selling* atau berisi teks tempelan berlebihan.

---

## 🚀 Persyaratan API Eksternal
Untuk menjalankan bot ini secara sempurna, Anda wajib mengatur beberapa API Eksternal (API ini diwajibkan karena script ini tidak menyediakan API rahasia developer di dalam repo publik).

1. **Google Gemini API (SEO Engine):**
   - Dapatkan API Key secara gratis di: [Google AI Studio](https://ai.google.dev/gemini-api/docs)
   - Masukkan ke variabel `GEMINI_API_KEY` di file `.env`.
   
2. **Cobalt API (Video Downloader Tanpa Watermark):**
   - Secara default, bot menggunakan instance publik (`https://co.wuk.sh/api/json`). 
   - ⚠️ **SANGAT DISARANKAN** untuk melakukan *Self-Host* Cobalt API (Cek repo: [Cobalt Github](https://github.com/imputnet/cobalt)) agar tidak terkena rate-limit atau blokir IP.
   - Masukkan URL Cobalt self-host Anda ke variabel `COBALT_API_URL` di file `.env`.

3. **TikTok Search API (Pencarian Video):**
   - Script ini didesain untuk terhubung dengan microservice pencarian TikTok internal (di port 3000). 
   - Karena microservice tersebut bersifat *private*, **Anda perlu membuat provider pencarian Anda sendiri**. Gunakan bantuan AI (ChatGPT/Claude) atau library seperti `tiktok-scraper` untuk membuat script pencarian TikTok, dan sesuaikan di dalam folder `providers/`.
   - Jika Anda membuat microservice sendiri, masukkan URL-nya ke `TIKTOK_SEARCH_API_URL` di file `.env`.

---

## 🛠️ Cara Instalasi & Setup

### 1. Clone & Setup Lingkungan
Pastikan menggunakan OS Linux/WSL dan Python 3.10+.

```bash
git clone https://github.com/Agelakz/Pinterest-bot.git
cd Pinterest-bot

# Buat virtual environment & aktifkan
python3 -m venv venv
source venv/bin/activate

# Install dependencies (akan menginstal library google-generativeai)
pip install -r requirements.txt
```

### 2. Kredensial & Cookies
Buat file `.env` di root folder dan isi sesuai kebutuhan API di atas:
```ini
GEMINI_API_KEY="AIzaSy_XXXXXXXXXXXXX"
COBALT_API_URL="http://IP_VPS_ANDA:9000/api/json"
TIKTOK_SEARCH_API_URL="http://IP_VPS_ANDA:3000/api/search"
```

### 3. Cookies Akun Pinterest
Bot ini tidak menggunakan password, melainkan Cookie Login untuk mengakses akun Pinterest Anda. 
1. Login ke akun Pinterest di browser PC Anda.
2. Gunakan ekstensi seperti **EditThisCookie** atau **Cookie-Editor**.
3. Export cookie Pinterest Anda dalam format JSON.
4. Buat file baru bernama `cookies.json` di root folder proyek ini dan *paste* cookie tersebut.

### 4. Data Produk
Taruh daftar produk affiliate dari Shopee kamu ke dalam file `data/shopee_products.json`.

---

## ⚙️ Cara Menjalankan (Auto-Upload)
Bot akan mem-publish 1 produk, lalu otomatis *sleep* selama 2 jam sebelum post berikutnya (menghindari shadowban). Sangat disarankan dijalankan di background menggunakan `screen` atau `tmux`.

```bash
python main.py
```

---
*Developed by Agelakz*
