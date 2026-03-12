# 🚀 Heartbeat Monitor

Tools minimalis untuk menjaga **koneksi pipeline tetap mesra**  dan mencegah error menyebelin kayak `packet_write_wait: Connection to IP: Broken pipe` atau timeout saat SSH.

##  Fungsi Utama
* **Anti-Broken Pipeline**: Mengirim detak jantung (*heartbeat*) konsisten agar sesi SSH dan tunnel Tailscale lo dianggap aktif oleh firewall atau NAT.
* **Connection Warming**: Memastikan jalur transmisi data nggak "dingin" atau diputus paksa oleh *idle-timer* di sisi server.
* **Service Dashboard**: Pantau kesehatan Tailscale dan SSH lo dalam satu layar TUI (Text User Interface) yang rapi.
* **Dynamic Target**: Ubah target IP/Domain ping secara *real-time* tanpa perlu mematikan dashboard.

## Struktur File
* `daemon.py`: Tukang pukul ping yang bekerja secara mandiri di balik layar.
* `cli.py`: Dashboard interaktif berbasis library `Rich` untuk kontrol layanan.
* `config.json`: Tempat menyimpan konfigurasi target IP.
* `logs/`: Direktori penyimpanan log metrik koneksi (`status.json`).

## 🛠️ Usage

### Cara Menjalankan
Pastikan lo udah install library yang dibutuhin (`pip install rich`), terus sikat:
```bash
python3 cli.py
```

Dashboard Keys
| Tombol | Aksi |
|---|---|
| 1 | Restart Tailscale (Userspace networking) |
| 2 | Restart SSH Service (Port 2288) |
| 3 | Toggle Heartbeat (Mulai/Hentikan daemon.py) |
| T | Change Target (Ubah IP target ping dinamis) |
| Q | Quit (Keluar dashboard) |

💡 Tips Biar Hubungan Makin "Abadi"
1. Sisi Client (Sangat Disarankan)
Biar makin mantap, konfigurasi SSH client lo agar mengirim paket keep-alive juga. Edit file ~/.ssh/config di mesin lokal lo:
Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3
    TCPKeepAlive yes

2. Buat Bocil Termux (Wajib!) ⚠️
Kalo lo jalanin tools ini di Termux, Android bakal otomatis "nyuntik mati" prosesnya pas HP masuk kantong (CPU mode tidur). Biar lari maraton terus, lo WAJIB aktifin WakeLock:
 * Tarik bar notifikasi, cari notifikasi Termux, klik "Acquire WakeLock".
 * Atau ketik perintah ini di terminal:
   ```bash
   termux-wake-lock
   ```

🔄 Auto-start
Masukin baris ini ke .zshrc atau .bashrc biar otomatis jalan tiap buka terminal:

```bash
# Otomatis deteksi path repo
HB_PATH="$HOME/heartbeat-monitor"

# Start daemon kalo belum jalan
if ! pgrep -f "$HB_PATH/daemon.py" > /dev/null; then
    nohup python3 "$HB_PATH/daemon.py" > /dev/null 2>&1 &
fi

# Shortcut login dashboard
alias hb="python3 $HB_PATH/cli.py"
```

jangan tanya saya kalo eror, coba tanya github copilot
