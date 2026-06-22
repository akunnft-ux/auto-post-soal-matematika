# Discovery Report — Auto Post Soal Matematika CPNS/TKA/SNBT

## 1. Executive Summary

Proyek ini adalah bot otomatis yang **menghasilkan soal matematika** untuk CPNS, TKA, dan SNBT menggunakan **Google Gemini AI**, membuat gambar soal secara otomatis, lalu **memposting ke Facebook Page** secara terjadwal 3x sehari dengan topik berbeda. Bot berjalan di **GitHub Actions** secara gratis.

## 2. Problem Statement

- Referensi hanya mencakup Deret Angka CPNS — pengguna ingin cakupan lebih luas (semua topik matematika CPNS/TKA/SNBT)
- Ingin jadwal lebih sering (3x/hari) dengan variasi topik
- Ingin tampilan visual yang lebih branded/profesional
- Tidak ingin repot generate & posting manual setiap hari

## 3. Project Type Classification

**Bot / Automation / Headless Integration**

Tidak ada web UI. Default Stack (Next.js/Supabase/Vercel) **tidak berlaku**.

Stack yang digunakan:
- **Runtime**: Python 3.12
- **AI**: Google Gemini API (gemini-3.1-flash-lite)
- **Image Processing**: Pillow
- **Platform**: Facebook Graph API
- **Scheduler**: GitHub Actions (cron)
- **Notifikasi**: Telegram Bot API

## 4. Stakeholders

| Stakeholder | Role |
|---|---|
| Pemilik Proyek | Pembuat konten & admin halaman Facebook |
| Audiens | Followers Facebook Page (peserta CPNS/TKA/SNBT) |

## 5. User Roles

| Role | Responsibilities | Permissions |
|---|---|---|
| Admin (Pemilik) | Konfigurasi API key, jadwal, style visual; monitor hasil posting | Akses penuh ke repo & secrets |

## 6. Core Workflows

```
[GitHub Actions Cron] → Generate Soal (Gemini AI)
                      → Buat Gambar (Pillow)
                      → Post ke Facebook Page
                      → Simpan Histori (anti-duplikat)
                      → Notifikasi Telegram (jika gagal)
                      → Commit histori ke repo
```

Setiap hari 3x eksekusi (pagi, siang, sore) — topik berbeda tiap sesi.

## 7. Functional Requirements

### MUST HAVE

| ID | Requirement |
|---|---|
| F-01 | Generate soal matematika CPNS/TKA/SNBT via Gemini AI (campuran semua topik) |
| F-02 | 3x posting per hari dengan topik berbeda |
| F-03 | Buat gambar soal otomatis dengan Pillow — style hijau tosca & putih, branded profesional |
| F-04 | Post gambar + caption ke Facebook Page via Graph API |
| F-05 | Histori soal anti-duplikat (disimpan di GitHub, di-commit tiap selesai) |
| F-06 | Notifikasi Telegram jika job gagal |
| F-07 | Menjalankan semua operasi di GitHub Actions (zero-cost) |

### SHOULD HAVE

| ID | Requirement |
|---|---|
| F-08 | Caption otomatis dengan ajakan interaksi |
| F-09 | Pembatasan histori (max item) agar file tidak membengkak |

## 8. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NF-01 | Waktu eksekusi < 2 menit per sesi (GitHub Actions limit) |
| NF-02 | Anti-duplikat ketat: tidak ada soal yang sama dalam 60 hari terakhir |
| NF-03 | Gambar harus terbaca jelas di Facebook (minimal 900px width) |
| NF-04 | Font yang digunakan harus tersedia di environment GitHub Actions (tidak bergantung font sistem) |

## 9. Reporting Requirements

Tidak ada dashboard atau laporan formal. Monitoring via:
- GitHub Actions logs
- Notifikasi Telegram jika gagal
- Facebook Page insights (eksternal)

## 10. Integration Requirements

| Integration | Purpose |
|---|---|
| Google Gemini API | Generate konten soal |
| Facebook Graph API | Post gambar ke Facebook Page |
| Telegram Bot API | Notifikasi error |

## 11. Data Requirements

### history.json
| Field | Type | Description |
|---|---|---|
| Array of strings | JSON | Daftar soal yang sudah pernah diposting (digunakan untuk anti-duplikat) |

### Environment Variables / Secrets
| Secret | Source |
|---|---|
| GEMINI_API_KEY | Google AI Studio |
| FB_PAGE_ID | Facebook Page settings |
| FB_ACCESS_TOKEN | Facebook Business Manager (System User Token) |
| TELEGRAM_BOT_TOKEN | @BotFather |
| TELEGRAM_CHAT_ID | @userinfobot |

## 12. Assumption Log

| Assumption | Reason | Impact | Status |
|---|---|---|---|
| Facebook Page sudah ada | Dikonfirmasi user | Harus pakai Page ID yang sudah ada | Confirmed |
| Gemini API key bisa didapatkan | Asumsi standar | Blocker jika belum punya | Inferred |
| Font DejaVu cukup untuk tampilan branded | Font open-source tersedia di Ubuntu | Visual bisa ditingkatkan nanti | Inferred |
| Facebook System User Token lebih baik | Token biasa expire 60 hari | Perlu setup Business Manager | Inferred |

## 13. Gap Analysis

| Gap | Severity | Note |
|---|---|---|
| Detail branding (logo, font spesifik) | Low | Bisa ditentukan di fase implementasi |
| Topik per sesi (jadwal tetap atau acak) | Low | Bisa random dari pool topik |
| Caption spesifik per topik | Low | Caption umum bisa dipakai untuk semua |

## 14. Open Questions

| Question | Status |
|---|---|
| Apakah user sudah punya Gemini API key? | Belum dikonfirmasi |
| Apakah mau pakai logo di gambar? | Belum ditanyakan |
| Font spesifik untuk tampilan branded? | Belum ditanyakan |

## 15. Risks

| Risk | Mitigation |
|---|---|
| Gemini API rate limit | Pakai model flash, request kecil |
| Facebook Token expire | Sarankan System User Token (tidak expire) |
| GitHub Actions 6h limit per run | Setiap sesi < 2 menit, aman |
| Font tidak tersedia | Gunakan DejaVu (default Ubuntu) |

## 16. Feature Prioritization

| Priority | Features |
|---|---|
| P0 (Must) | Generate soal, buat gambar, post FB, anti-duplikat, notif error |
| P1 (Should) | Caption otomatis, histori terbatas |
| P2 (Could) | Logo di gambar, variasi layout per topik |
| P3 (Future) | Multiple platform, dashboard monitoring |

## 17. Recommendation

Lanjut ke PRD dan arsitektur. Proyek ini straightforward — cukup 1 script Python utama (modifikasi dari referensi) dengan penambahan:
- Pemilihan topik acak dari pool
- 3x jadwal cron dengan topik berbeda
- Tampilan visual branded (hijau tosca/putih)
- Penyesuaian prompt Gemini agar menghasilkan berbagai tipe soal
