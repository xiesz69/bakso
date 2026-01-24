# 🚀 App Monitor & RAM Cleaner Pro v2.3
**Monitor Sistem Android Interaktif & Pembersih RAM Cerdas lewat Termux!**

Skrip Python profesional untuk memantau aplikasi Android secara real-time. Jika aplikasi mati, Anda akan menerima notifikasi instan via Telegram. Dilengkapi dengan dashboard dinamis yang menampilkan penggunaan RAM, Beban CPU, dan status aplikasi secara otomatis.

---

## 🌟 Fitur Unggulan
- 🖥️ **Interactive CLI Menu**: Tampilan profesional dengan bingkai dan skema warna modern.
- 📊 **Dynamic Dashboard**: Update otomatis untuk:
    - Penggunaan RAM (Total, Used, Free) dengan progress bar.
    - **Beban CPU**: Tampilan persentase yang mudah dipahami.
    - **App Uptime**: Mengetahui berapa lama aplikasi target telah berjalan.
- ⚙️ **In-App Management**: Tambah atau hapus aplikasi yang dipantau & daftar whitelist langsung dari menu tanpa edit kode.
- 📩 **Smart Telegram Alert**: Notifikasi detail saat aplikasi mati (termasuk info RAM & Uptime Sistem saat kejadian).
- 🧹 **Pembersih RAM Cerdas**: Menghapus cache sistem dan menghentikan aplikasi latar belakang yang tidak penting (Optimal dengan akses Root).
- 🔄 **Multithreading**: Pemantauan tetap berjalan di latar belakang saat Anda menavigasi menu.

---

## 🛠️ Persiapan Telegram
Anda memerlukan API Token dan Chat ID:
1. **Bot Token**: Dapatkan dari [@BotFather](https://t.me/BotFather) dengan perintah `/newbot`.
2. **Chat ID**: Dapatkan dari [@userinfobot](https://t.me/userinfobot).

---

## 🚀 Instalasi Cepat
Salin dan tempel perintah ini di Termux untuk instalasi otomatis:
```bash
pkg install git -y && git clone https://github.com/xiesz69/bakso.git && cd bakso && chmod +x setup.sh && ./setup.sh
```

---

## 🎮 Cara Penggunaan
Setelah instalasi selesai, jalankan skrip:
```bash
python monitor.py
```
**Menu Utama:**
1. **Toggle Monitor**: Menghidupkan atau mematikan fungsi pemantauan.
2. **Manajemen Aplikasi**: Tambah/Hapus paket aplikasi yang ingin dipantau.
3. **Manajemen Whitelist**: Kelola aplikasi yang aman dari pembersihan RAM.
4. **Konfigurasi Telegram**: Update Token dan Chat ID langsung dari aplikasi.
5. **Lihat Status Detail**: Menampilkan daftar lengkap aplikasi yang sedang dipantau.

---

## 💡 Tips
- **Nama Paket**: Gunakan nama paket aplikasi Android (contoh: `com.termux`, `com.whatsapp`).
- **Akses Root**: Direkomendasikan agar fitur `drop_caches` dan `force-stop` bekerja maksimal.
- **Stay Alive**: Skrip otomatis menggunakan `termux-wake-lock` agar tetap berjalan saat layar padam.

---
**Created by [ME](https://t.me/xiesz) | [CHANNEL](https://t.me/xiechannel)**
