# Final-Assignment-Project

Sistem Absensi RFID + Webcam
Sistem absensi karyawan berbasis RFID USB dan Webcam dengan website manajemen data real-time. Dibangun menggunakan Python (Flask) dan MySQL.

Fitur

1. Scan RFID otomatis — tap kartu = check-in, tap lagi = check-out
2. Foto otomatis — webcam mengambil foto karyawan setiap scan
3. ashboard harian — statistik kehadiran real-time
4. CRUD Karyawan — tambah, edit, hapus data karyawan
5. Laporan Absensi — filter berdasarkan tanggal & nama karyawan
6. Live Monitor — log scan terbaru dengan auto-refresh tiap 4 detik

Cara Pakai Sehari-hari
1. Buka Laragon → Start All
2. CMD 1 → cd backend → python app.py
3. CMD 2 → cd client → python attendance_client.py --preview
4. Buka http://localhost:5000 di browser
5. Karyawan tap kartu saat masuk & pulang

Catatan

Sistem hanya berjalan secara lokal (localhost)
Data tersimpan permanen di MySQL selama Laragon tidak di-uninstall
Backup database secara berkala via phpMyAdmin → Export
Pastikan hanya satu aplikasi yang mengakses webcam dalam satu waktu


Lisensi
Project ini dibuat untuk keperluan Tugas Akhir SMK. Bebas digunakan dan dikembangkan.
