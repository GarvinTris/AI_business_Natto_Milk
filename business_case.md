# Business Case — AI Smart Order Assistant UMKM

## 1. Business Context

Kedai Kopi sering mengalami kekosongan SDM (karyawan sakit/resign). Ketika orderan via WhatsApp/Instagram melonjak, pencatatan manual chat unformatted memperlambat pelayanan dan memperpanjang waiting time pelanggan.

## 2. Initial Problem

Owner harus membaca chat, mencari produk, jumlah, tanggal, jam, fulfillment, alamat, dan catatan,
lalu mencatat ulang order secara manual.

## 3. Target User

Manajer UMKM Kedai Kopi yang mengatur workflow manajemen SDM.

## 4. Pain Points

- Keterbatasan SDM membuat tim tersisa kelimpahan beban.
- Pemrosesan chat manual lambat dan tidak terstruktur.
- Waiting time pelanggan meningkat saat jam sibuk.

## 5. Problem Statement

Manajer mengalami kendala dalam menjaga kelancaran proses pelayanan ketika jumlah pesanan meningkat karena
keterbatasan SDM ini dapat disebabkan oleh ketidakhadiran karyawan, dan workflow yang terkadang tidak
berjalan sesuai prosedur.

## 6. How Might We

Bagaimana kita membantu manajer mengelola workflow karyawan agar proses pelayanan dapat berjalan lebih efektif.

## 7. AI Opportunity

Large Language Model digunakan untuk:

1. Memahami chat natural Bahasa Indonesia.
2. Mengekstrak entitas order.
3. Memahami tanggal relatif.
4. Mendeteksi ambiguity/missing information.
5. Membuat follow-up WhatsApp.

Kode biasa digunakan untuk:

1. Harga.
2. Perhitungan total.
3. Aturan wajib alamat untuk delivery.
4. Status order.

## 8. Success Metrics

Untuk demo kelas:

- AI tidak mengarang alamat/nama yang tidak diberikan.
- 100% total harga dihitung oleh business rule, bukan LLM.
- Waktu pencatatan order lebih singkat dibanding manual.

## 9. Ethical / Risk Notes

- Jangan gunakan chat customer sungguhan tanpa izin.
- Jangan memasukkan data sensitif ke demo kelas.
- API key tidak boleh dipublikasikan di GitHub.
- Output AI harus tetap dapat dikonfirmasi manusia.
