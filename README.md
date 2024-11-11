# Proxygrass Bot
Bot otomatis untuk menggunakan proxy dari Grass.

## Langkah Instalasi
1. **Clone repository**
   ```bash
   git clone https://github.com/fadhiljr7/okonomiyaki.git
   cd okonomiyaki
   ```

2. **Install dependencies**

   Install paket yang diperlukan dari file `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

4. **Ambil User ID Grass**
   - Buka [dashboard Grass](https://www.grass.com) Anda.
   - Buka *inspect element* dengan menekan `Ctrl + Shift + I`.
   - Buka tab "Console" dan ketik `localStorage.user` untuk mendapatkan User ID akun Grass Anda.
   - Simpan userid anda pada file `userid.txt`.

5. **Konfigurasi Proxy**

   Isi daftar proxy pada file `local_proxies.txt` dengan Connection type `IP Address` menggunakan format berikut:
   ```
   http://username:password@ip:port
   ```
   Tambahkan satu baris untuk setiap proxy yang ingin digunakan.

7. **Jalankan Bot**

   Untuk menjalankan bot, gunakan perintah berikut:
   ```bash
   python mufiiin.py
   ```

## Catatan
Pastikan proxy yang digunakan valid dan sesuai format agar bot dapat berjalan dengan lancar.
Python Version:3.10++
