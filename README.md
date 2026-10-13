# 🤖 AI Smart Order Assistant UMKM

> **Hands-On Lab — Kecerdasan Artifisial untuk Bisnis**
> Pertemuan 3: Structured Output & Business Rules

Aplikasi ini mendemonstrasikan bagaimana **AI (Gemini)** dapat mengubah chat customer yang tidak terstruktur menjadi data order yang terstruktur, kemudian diproses oleh **business rules** deterministik.

---

## 🎯 Learning Goals

Setelah hands-on lab ini, mahasiswa diharapkan memahami:

1. Perbedaan antara **AI tasks** (memahami bahasa natural) dan **deterministic rules** (harga, total, validasi).
2. Konsep **Structured Output** — memaksa AI mengembalikan data dalam format JSON yang konsisten.
3. Bagaimana membangun pipeline: **Chat → AI → Structured Data → Business Rules → Action**.
4. Cara mendeteksi **missing information** dan membuat follow-up otomatis.

---

## 🔄 Alur Sistem

```
Customer Chat (WhatsApp/Instagram)
        ↓
Unstructured Text
        ↓
Gemini AI (Structured Output)
        ↓
Structured Order (JSON/Pydantic)
        ↓
Missing Information Detection
        ↓
Business Rules (harga, total, validasi)
        ↓
Order Confirmation / Follow-up WhatsApp
        ↓
Order Dashboard
```

---

## 🧠 AI vs Business Rules

| Task | AI (Gemini) | Business Rules (Code) |
|---|:---:|:---:|
| Memahami bahasa customer | ✅ | |
| Mengenali nama produk | ✅ | |
| Memahami "besok/lusa/Jumat" | ✅ | |
| Mengenali alamat pengiriman | ✅ | |
| Menemukan informasi ambigu | ✅ | ✅ |
| Membuat follow-up WhatsApp | ✅ | ✅ |
| Menentukan harga produk | | ✅ |
| Menghitung subtotal & total | | ✅ |
| Validasi delivery wajib alamat | | ✅ |
| Menentukan status READY | | ✅ |

**Prinsip utama:** AI digunakan untuk pekerjaan yang membutuhkan pemahaman bahasa dan konteks. Business rules digunakan untuk hal yang harus pasti dan deterministik.

---

## 🗂️ Struktur Project

```
├── app.py               ← Streamlit UI & main application
├── ai_service.py        ← Gemini API integration & prompt
├── schemas.py           ← Pydantic schema (Structured Output)
├── business_rules.py    ← Pricing, validation, order status
├── sample_messages.csv  ← Test cases untuk evaluasi
├── business_case.md     ← Konteks bisnis dan problem statement
├── requirements.txt     ← Python dependencies
├── .env.example         ← Template konfigurasi API key
└── README.md
```

---

## 🚀 Setup & Instalasi

### 1. Prasyarat

Pastikan sudah terinstall **Python 3.10+**:

```bash
python --version
```

### 2. Clone Repository

```bash
git clone https://github.com/triandessinaga/Ai-for-business-session-3.git
cd Ai-for-business-session-3
```

### 3. Buat Virtual Environment

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Konfigurasi API Key

Salin file `.env.example` menjadi `.env`:

**Windows:**
```bash
copy .env.example .env
```

**macOS / Linux:**
```bash
cp .env.example .env
```

Buka file `.env` dan isi dengan API key Anda:

```env
GEMINI_API_KEY=PASTE_API_KEY_KAMU_DI_SINI
GEMINI_MODEL=gemini-3.8-flash
```

> 💡 **Cara mendapatkan API Key:** Daftar di [Google AI Studio](https://aistudio.google.com/) → klik **Get API Key** → buat API key baru → copy ke `.env`

> ⚠️ **Jangan pernah upload file `.env` ke GitHub!** File ini sudah ada di `.gitignore`.

### 6. Jalankan Aplikasi

```bash
streamlit run app.py
```

Browser akan terbuka otomatis di `http://localhost:8501`.

---

## 🧪 Cara Menggunakan Aplikasi

### Tab 1 — Analyze Order

1. Pilih **sample message** atau paste chat customer sendiri.
2. Klik **✨ Analyze with Gemini AI**.
3. Lihat hasil ekstraksi: customer info, produk, tanggal, metode pengiriman.
4. Perhatikan bagian **Missing / Need Confirmation** — ini ditentukan oleh business rules, bukan AI.
5. Preview dan kirim pesan follow-up ke WhatsApp customer.
6. Klik **💾 Save to Order Dashboard** untuk menyimpan order.

### Tab 2 — Order Dashboard

- Lihat semua order yang tersimpan dalam session.
- Lihat metrics: total order, order ready, potensi revenue.
- Download data sebagai CSV.

### Tab 3 — AI vs Business Rules

- Tabel perbandingan tugas AI dan business rules.
- Visualisasi alur proses bisnis.
- Katalog produk beserta harga.

---

## 🧾 Contoh Chat Customer

Berikut beberapa contoh chat yang bisa dicoba:

**Contoh 1 — Data Lengkap:**
```
Halo kak, saya Michelle. Mau Red Velvet 2 dan Brownies 1 untuk 
12 September 2026 jam 3 sore. Tolong antar ke Komplek Cemara Asri 
Blok A12 Medan. Red velvet satunya tulis Happy Birthday Mama ya.
```

**Contoh 2 — Data Kurang:**
```
Kak besok mau cheesecake satu, ambil sendiri sekitar jam 5.
```

**Contoh 3 — Delivery Ambigu:**
```
Brownies 3 box untuk Jumat ya kak, kirim ke kantor saya di Multatuli.
```

---

## 📋 Demo Script (15–20 Menit)

### Scene 1 — Manual Chaos
Berikan chat: *"Kak besok mau cheesecake satu, ambil sendiri sekitar jam 5."*

Tanya mahasiswa:
- Produk apa? Berapa?
- Tanggal berapa "besok"?
- Jam 5 pagi atau sore?
- Pickup atau delivery?
- Apa yang belum diketahui seller?

### Scene 2 — AI Extraction
Klik **Analyze with AI** dan tunjukkan bahwa AI mengubah teks bebas menjadi data terstruktur.

### Scene 3 — Missing Data Detection
Perhatikan bagian **Missing / Need Confirmation** dan **suggested follow-up** yang dibuat otomatis.

### Scene 4 — AI vs Rules
Tunjukkan bahwa **harga tidak ditentukan AI**. Harga diambil dari katalog dan dihitung oleh business rules.

### Scene 5 — Business Value
Simpan order ke dashboard. Diskusikan:
- Pekerjaan manual apa yang berkurang?
- Risiko apa yang masih ada?
- Di mana human confirmation tetap diperlukan?

---

## 💡 Challenge Kelompok

Ubah domain aplikasi ini ke bisnis lain. Setiap kelompok memilih satu domain:

| No | Domain |
|---|---|
| 1 | Restaurant Reservation Assistant |
| 2 | Salon Booking Assistant |
| 3 | Laundry Order Assistant |
| 4 | Catering Order Assistant |
| 5 | Event Registration Assistant |
| 6 | Online Shop Inquiry Assistant |

**Syarat deliverable:**
- ✅ Problem statement yang jelas
- ✅ Minimal 10 test chat yang bervariasi
- ✅ Pemisahan yang jelas antara AI task dan deterministic rule
- ✅ Minimal 1 metric evaluasi (akurasi ekstraksi, dll.)

---

## 📊 Test Plan & Evaluasi

Gunakan `sample_messages.csv` sebagai bahan evaluasi.

Untuk setiap chat, cek:
- Nama produk benar?
- Quantity benar?
- Tanggal benar? (terutama untuk kata relatif "besok", "lusa")
- Fulfillment (pickup/delivery) benar?
- Alamat tidak di-hallucinate?
- Missing fields terdeteksi dengan benar?
- Follow-up message relevan dan natural?

**Template tabel evaluasi:**

| ID | Chat | Product ✓ | Qty ✓ | Date ✓ | Fulfillment ✓ | Missing Field ✓ | Hallucination? | Pass? |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|

---

## 🔧 Konfigurasi Lanjutan

### Mengubah Produk Katalog
Edit variabel `PRODUCT_CATALOG` di `app.py`:

```python
PRODUCT_CATALOG = {
    "Nama Produk": harga_dalam_rupiah,
    ...
}
```

### Mengubah Model Gemini
Ubah di file `.env`:
```env
GEMINI_MODEL=gemini-2.0-flash
```

Atau langsung dari sidebar aplikasi saat runtime.

### Mengubah Nomor WhatsApp
Edit konstanta di bagian atas `app.py`:
```python
SELLER_WHATSAPP = "62XXXXXXXXXX"
```

---

## ❓ Troubleshooting

**Error: `GEMINI_API_KEY belum tersedia`**
→ Pastikan file `.env` sudah dibuat dan API key sudah diisi dengan benar.

**Error: `ModuleNotFoundError`**
→ Pastikan virtual environment sudah aktif dan `pip install -r requirements.txt` sudah dijalankan.

**Aplikasi tidak terbuka di browser**
→ Buka manual di browser: `http://localhost:8501`

**AI mengembalikan hasil tidak akurat**
→ Coba ganti model di sidebar (contoh: `gemini-2.0-flash`) atau perbaiki teks chat agar lebih jelas.

---

## 📚 Referensi

- [Google AI Studio](https://aistudio.google.com/) — untuk mendapatkan API key
- [Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

---

*Dibuat untuk mata kuliah Kecerdasan Artifisial untuk Bisnis — 2026/2027*
