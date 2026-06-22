# PRD — Auto Post Soal Matematika CPNS/TKA/SNBT

## Document Control

### Document Version History

| Version | Date | Author | Summary of Changes |
|---|---|---|---|
| 0.1 | 2026-06-20 | Tech Lead | Initial draft |

### Approval / Sign-off

| Role | Name | Status | Date |
|---|---|---|---|
| Business Owner | [TBD] | Pending | |
| Technical Lead | [TBD] | Pending | |
| Security Reviewer | [TBD] | Pending | |

### Change Request Log

| CR ID | Date | Requester | Description | Status |
|---|---|---|---|---|

---

## 1. Executive Summary

**Project Name:** Auto Post Soal Matematika CPNS/TKA/SNBT

**Project Overview:** Bot otomatis yang menghasilkan soal matematika untuk CPNS, TKA, dan SNBT menggunakan Google Gemini AI, membuat gambar soal, dan memposting ke Facebook Page secara terjadwal 3x sehari dengan topik berbeda.

**Business Problem:** Pembuatan konten soal latihan matematika secara manual memakan waktu, tidak konsisten, dan sulit dilakukan setiap hari. Audiens membutuhkan soal latihan segar secara rutin untuk persiapan ujian.

**Target Users:** Followers Facebook Page yang sedang mempersiapkan CPNS, TKA, atau SNBT — terutama yang membutuhkan latihan soal matematika.

**Expected Outcomes:** Posting konsisten 3x/hari dengan soal berkualitas, variasi topik, dan tampilan visual profesional tanpa intervensi manual.

**Success Definition:** Bot berjalan otomatis setiap hari tanpa error, soal tidak pernah duplikat dalam 60 hari terakhir, dan setiap post mendapat engagement dari audiens.

---

## 2. Business Objectives

| ID | Objective | Type |
|---|---|---|
| BO-001 | Menghasilkan konten soal matematika secara otomatis setiap hari | Primary |
| BO-002 | Menyediakan variasi topik matematika (campuran) dalam setiap hari | Primary |
| BO-003 | Menjaga kualitas visual konten dengan tampilan branded profesional | Secondary |
| BO-004 | Memastikan tidak ada soal duplikat dalam periode 60 hari | Operational |
| BO-005 | Meminimalkan biaya operasional (zero-cost infra) | Operational |
| BO-006 | Mendeteksi dan melaporkan kegagalan eksekusi secara real-time | Operational |

---

## 3. Project Scope

### In Scope
- Generate soal matematika via Google Gemini AI (semua topik: deret angka, aritmatika, aljabar, peluang, geometri, fungsi/grafik)
- Generate gambar soal dengan Pillow — tema hijau tosca & putih
- Posting ke Facebook Page 3x/hari dengan topik berbeda
- Histori anti-duplikat (disimpan di JSON, di-commit ke repo)
- Notifikasi Telegram jika job gagal
- Berjalan di GitHub Actions via cron

### Out of Scope
- Web dashboard atau UI admin
- Multi-platform posting (Telegram, Twitter, dll)
- Auto-reply komentar di Facebook
- Multi-user / multi-page support
- Analytics dashboard

### Future Scope
- Penambahan tipe konten lain (quotes, tips belajar)
- Multi-platform posting
- Dashboard monitoring via Google Sheets
- Auto-reply jawaban di komentar

---

## 4. Stakeholders

| Stakeholder | Responsibilities | Expectations | Success Criteria |
|---|---|---|---|
| Pemilik Proyek | Konfigurasi API key & Page ID, pantau hasil, terima notifikasi error | Bot berjalan otomatis tanpa intervensi | 0 error dalam seminggu |
| Audiens (Followers) | Melihat dan mengerjakan soal di Facebook | Soal bervariasi, tidak monoton, tampilan menarik | Engagement mingguan konsisten |

---

## 5. User Roles

| Role | Responsibilities | Permissions | Restrictions | Approval Authority | Reporting Access | Data Access Scope |
|---|---|---|---|---|---|---|
| Admin (Pemilik) | Setup secrets, monitor logs, handle error | Full akses ke repo & secrets | — | — | GitHub Actions logs, Telegram notif | Semua data |

Hanya satu pengguna nyata (Admin). Tidak ada role lain.

---

## 6. Assumption Log

| ID | Description | Reason | Impact | Status | Linked Risk |
|---|---|---|---|---|---|
| ASM-001 | User sudah memiliki Facebook Page | Dikonfirmasi | Wajib untuk posting | Confirmed | — |
| ASM-002 | User dapat memperoleh Gemini API key | Asumsi standar | Blocker jika tidak | Inferred | RISK-001 |
| ASM-003 | Font DejaVu cukup untuk tampilan branded | Font default Ubuntu | Visual bisa ditingkatkan | Inferred | — |
| ASM-004 | Facebook System User Token lebih baik | Token biasa expire 60 hari | Perlu setup Business Manager | Inferred | RISK-002 |
| ASM-005 | GitHub Actions runner memiliki semua dependensi | Ubuntu latest | Perlu install Pillow, google-genai | Confirmed | — |

---

## 7. User Stories

| ID | As a | I want | So that | Realized by |
|---|---|---|---|---|
| US-001 | Admin | Menjadwalkan posting otomatis 3x/hari | Konten tetap terisi tanpa kerja manual | FR-001, FR-002 |
| US-002 | Admin | Soal berbeda tiap sesi posting | Audiens tidak bosan dengan topik itu-itu saja | FR-003 |
| US-003 | Admin | Gambar soal terlihat profesional | Meningkatkan kredibilitas halaman | FR-004 |
| US-004 | Admin | Tidak ada soal duplikat | Audiens mendapat soal baru setiap kali | FR-005 |
| US-005 | Admin | Dapat notifikasi jika gagal | Segera tahu dan bisa memperbaiki | FR-006 |

---

## 8. Functional Requirements

### FR-001 — Generate Soal via Gemini AI (Depth: Core)

| Sub-field | Value |
|---|---|
| **Feature Name** | Generate Soal Matematika |
| **Description** | Memanggil Gemini API untuk menghasilkan 1 soal matematika dari topik yang ditentukan, lengkap dengan pilihan jawaban, jawaban benar, dan penjelasan. Topik dipilih secara acak dari pool: deret angka, aritmatika/aljabar, peluang/statistika, geometri, fungsi/grafik. |
| **Business Purpose** | Otomatisasi pembuatan konten inti |
| **Traces to** | BO-001, BO-002 |
| **Inputs** | Topik terpilih (acak), histori soal (untuk anti-duplikat) |
| **Outputs** | JSON: `{soal, pilihan[], jawaban, penjelasan}` |
| **Validation Rules** | - Response harus JSON valid dengan 4 field wajib - Soal tidak boleh ada di histori 60 hari terakhir - Pilihan harus array of string (4 item) - Jawaban harus salah satu dari pilihan |
| **Permissions** | Hanya dieksekusi oleh GitHub Actions runner |
| **Error Handling** | Retry 3x dengan topik berbeda jika gagal. Jika seluruh retry gagal, kirim notifikasi Telegram dan abort sesi. |
| **Acceptance Criteria** | AC-001, AC-002 |
| **Dependencies** | Gemini API key (GEMINI_API_KEY) |

### FR-002 — 3x Posting Sehari dengan Topik Berbeda (Depth: Core)

| Sub-field | Value |
|---|---|
| **Feature Name** | Multi-sesi Harian |
| **Description** | GitHub Actions cron menjadwalkan 3 sesi per hari. Setiap sesi memilih topik yang berbeda dari 2 sesi lainnya pada hari yang sama. Sesi 1: topik_random_1, Sesi 2: topik_random_2 (≠ sesi 1), Sesi 3: topik_random_3 (≠ sesi 1 & 2). |
| **Business Purpose** | Variasi konten harian |
| **Traces to** | BO-001, BO-002 |
| **Inputs** | Daftar topik, jadwal cron |
| **Outputs** | 3 post Facebook per hari |
| **Validation Rules** | Topik tidak boleh sama dalam 1 hari. Jika pool topik < 3, error. |
| **Permissions** | — |
| **Error Handling** | Jika hanya 2 topik tersisa (karena anti-duplikat), gunakan yang tersedia tanpa error. |
| **Acceptance Criteria** | AC-003 |
| **Dependencies** | FR-001, FR-005 |

### FR-003 — Pemilihan Topik Acak (Depth: Supporting)

| Sub-field | Value |
|---|---|
| **Feature Name** | Topik Randomizer |
| **Description** | Sebelum generate, pilih topik secara acak dari pool (deret angka, aritmatika/aljabar, peluang/statistika, geometri, fungsi/grafik) dengan memastikan tidak sama dengan sesi lain di hari yang sama. |
| **Business Purpose** | Variasi konten tanpa campur tangan manual |
| **Traces to** | BO-002 |
| **Inputs** | Pool topik, topik yang sudah dipakai hari ini |
| **Outputs** | Nama topik terpilih (string) |
| **Validation Rules** | Topik harus dari pool yang valid. Topik tidak boleh duplicate dalam 1 hari. |
| **Permissions** | — |
| **Error Handling** | Jika semua topik sudah dipakai, reset pool |
| **Acceptance Criteria** | AC-004 |
| **Dependencies** | FR-002 |

### FR-004 — Generate Gambar Soal (Depth: Core)

| Sub-field | Value |
|---|---|
| **Feature Name** | Image Renderer |
| **Description** | Membuat gambar soal 900x700px menggunakan Pillow dengan tema hijau tosca (#14b8a6) dan putih (#ffffff), header hijau tosca gradient, teks soal/pilihan dengan font profesional, footer dengan ajakan interaksi. Auto word-wrap untuk teks panjang. |
| **Business Purpose** | Konten visual yang siap diposting ke Facebook |
| **Traces to** | BO-003 |
| **Inputs** | Data soal (JSON dari FR-001) |
| **Outputs** | File PNG 900x700px |
| **Validation Rules** | - File PNG harus valid - Ukuran minimal 900x700 - Teks tidak boleh terpotong (overflow) |
| **Permissions** | — |
| **Error Handling** | Jika font tidak ditemukan, fallback ke ImageFont default. Jika gagal total, kirim notifikasi. |
| **Acceptance Criteria** | AC-005 |
| **Dependencies** | Pillow library, font files di repo |

### FR-005 — Histori Anti-Duplikat (Depth: Supporting)

| Sub-field | Value |
|---|---|
| **Feature Name** | Duplicate Prevention |
| **Description** | Simpan semua soal yang sudah pernah diposting ke `data/history.json`. Sebelum generate, cek apakah soal baru sudah ada di histori. Batasi histori maksimal 60 item (cukup untuk 20 hari pada 3x/hari). Setelah selesai posting, commit histori terbaru ke repo. |
| **Business Purpose** | Menjamin konten selalu fresh |
| **Traces to** | BO-004 |
| **Inputs** | Soal baru (string) |
| **Outputs** | Updated history.json |
| **Validation Rules** | - Histori tidak boleh duplikat - Maks 60 item (FIFO) - File harus valid JSON |
| **Permissions** | GitHub Actions need contents: write |
| **Error Handling** | Jika file corrupt, backup dulu lalu reset. Jika commit gagal, log warning saja (tidak blokir). |
| **Acceptance Criteria** | AC-006, AC-007 |
| **Dependencies** | Git push permission |

### FR-006 — Notifikasi Telegram (Depth: Supporting)

| Sub-field | Value |
|---|---|
| **Feature Name** | Error Notification |
| **Description** | Jika terjadi error fatal (gagal generate setelah retry, gagal post ke Facebook), kirim pesan ke Telegram via bot. Pesan berisi timestamp dan deskripsi error. Gunakan blocking call dengan timeout 10s. |
| **Business Purpose** | Admin tahu segera jika ada masalah |
| **Traces to** | BO-006 |
| **Inputs** | Error message (string) |
| **Outputs** | Pesan Telegram terkirim |
| **Validation Rules** | Hanya terkirim jika TELEGRAM_BOT_TOKEN dan TELEGRAM_CHAT_ID terisi |
| **Permissions** | — |
| **Error Handling** | Jika Telegram API gagal, log warning (jangan cascade error). |
| **Acceptance Criteria** | AC-008 |
| **Dependencies** | Telegram bot token & chat ID |

### FR-007 — Post ke Facebook Graph API (Depth: Core)

| Sub-field | Value |
|---|---|
| **Feature Name** | Facebook Publisher |
| **Description** | Upload gambar + caption ke Facebook Page via Graph API endpoint `/{page-id}/photos`. Menggunakan POST multipart dengan file gambar dan caption. |
| **Business Purpose** | Publikasi konten ke audiens |
| **Traces to** | BO-001 |
| **Inputs** | File PNG, caption string |
| **Outputs** | Facebook post ID |
| **Validation Rules** | Response dari API harus sukses (tidak ada `error` field). |
| **Permissions** | FB_ACCESS_TOKEN harus punya `pages_manage_posts` |
| **Error Handling** | Retry 1x jika timeout/rate-limit. Jika gagal total, kirim notifikasi Telegram. |
| **Acceptance Criteria** | AC-009 |
| **Dependencies** | FB_PAGE_ID, FB_ACCESS_TOKEN |

---

## 9. Non-Functional Requirements

| ID | Requirement | Target | Measurement | Traces to |
|---|---|---|---|---|
| NFR-001 | Waktu eksekusi per sesi | < 120 detik | GitHub Actions duration | BO-001 |
| NFR-002 | Anti-duplikat efektif | 0 duplikat dalam 60 hari | History audit | BO-004 |
| NFR-003 | Gambar readable di Facebook | Minimal 900px width | Visual inspection | BO-003 |
| NFR-004 | Zero biaya operasional | $0 per bulan | Cost tracking | BO-005 |

---

## 10. Data Requirements

### Entity: history.json

| Field | Type | Description | Validation |
|---|---|---|---|
| items | Array of string | Soal-soal yang sudah pernah diposting | Tidak boleh kosong string, max 60 item |

### Entity: Soal (transient, dari Gemini)

| Field | Type | Description |
|---|---|---|
| soal | string | Teks soal |
| pilihan | string[4] | Array of 4 pilihan jawaban |
| jawaban | string | Jawaban yang benar |
| penjelasan | string | Penjelasan jawaban |

---

## 11. Database Requirements

Tidak ada database server. Satu file JSON (`data/history.json`) sebagai penyimpanan state.

---

## 12. ERD

Tidak ada ERD karena tidak ada database relasional. Satu entity (`History`) dengan satu atribut (array of strings).

---

## 13. Business Rules

| ID | Rule | Category |
|---|---|---|
| BR-001 | Setiap sesi harus topik berbeda dari sesi lain di hari yang sama | Scheduling |
| BR-002 | Soal tidak boleh duplikat dengan 60 histori terakhir | Editing |
| BR-003 | Histori lama (item > 60) otomatis dihapus (FIFO) | Editing |
| BR-004 | Jika Gemini gagal 3x berturut-turut, skip sesi dan kirim notif | Scheduling |
| BR-005 | Jika Facebook API gagal setelah retry, kirim notif | Notification |

---

## 14. Workflows

### Main Workflow: Eksekusi Sesi Posting

```
Start (Cron Trigger)
  ↓
Load histori dari history.json
  ↓
Pilih topik acak (≠ sesi lain hari ini)
  ↓
Generate soal via Gemini (retry 3x jika gagal)
  ↓
Buat gambar PNG via Pillow
  ↓
Post ke Facebook Graph API
  ↓
Update histori → commit ke repo
  ↓
End
```

### Alternate Flow: Topik Hanya 2 Tersisa

```
...Pilih topik acak
  ↓
Hanya 2 topik tersedia (sisanya sudah dipakai)
  ↓
Gunakan yang tersedia tanpa error
  ↓
Generate soal...
```

### Failure Flow: Gemini Gagal

```
Generate soal via Gemini
  ↓
Gagal (parse error / duplikat / API error)
  ↓
Retry dengan topik berbeda (max 3x)
  ↓
Semua retry gagal
  ↓
Kirim notifikasi Telegram
  ↓
Abort sesi (jangan post)
```

### Failure Flow: Facebook Post Gagal

```
Post ke Facebook
  ↓
Gagal (rate limit / token invalid)
  ↓
Retry 1x
  ↓
Masih gagal
  ↓
Kirim notifikasi Telegram
  ↓
Histori tetap disimpan (soal sudah dibuat, hanya post-nya gagal)
```

---

## 15. API Requirements

Tidak ada API yang kita hosting. Kita mengonsumsi API eksternal:

| API | Method | Endpoint | Purpose |
|---|---|---|---|
| Gemini | POST | `https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent` | Generate soal |
| Facebook Graph | POST | `https://graph.facebook.com/{page-id}/photos` | Post gambar |
| Telegram | POST | `https://api.telegram.org/bot{token}/sendMessage` | Kirim notifikasi |

---

## 16. Integration Requirements

| Integration | Purpose | Trigger | Data Flow | Failure Handling |
|---|---|---|---|---|
| Google Gemini API | Generate konten soal | Setiap cron sesi | Prompt → API call → JSON response | Retry 3x, lalu notif Telegram |
| Facebook Graph API | Post ke Facebook | Setelah gambar selesai | Upload file + caption → Post ID | Retry 1x, lalu notif Telegram |
| Telegram Bot API | Notifikasi error | Setelah error fatal | Error message → POST ke Telegram | Log warning jika Telegram gagal |

---

## 17. UI Requirements

**N/A** — Project ini adalah headless bot tanpa user interface. Visual output berupa gambar soal yang diposting ke Facebook.

---

## 18. Reporting Requirements

Tidak ada dashboard atau laporan formal. Monitoring dilakukan via:
- GitHub Actions logs (real-time)
- Notifikasi Telegram (real-time error)
- Facebook Page Insights (eksternal, non-teknis)

---

## 19. Notification Requirements

| Notification | Trigger | Recipient | Content | Failure Handling |
|---|---|---|---|---|
| Job Failed | Error fatal di sesi mana pun | Admin via Telegram | `[Auto Post Soal] Job GAGAL pada {timestamp}: {error}` | Log warning jika Telegram gagal |

---

## 20. Audit Requirements

| Action | Audited Data | Retention |
|---|---|---|
| Setiap sesi posting | Timestamp, sukses/gagal, error message (via GitHub Actions logs) | 90 hari (GitHub Actions default) |
| Histori soal | Semua soal yang pernah diposting | Indefinite (histori JSON) |

---

## 21. Security Requirements

| Requirement | Implementation |
|---|---|
| API Key Management | GitHub Secrets (encrypted at rest, injected as env vars) |
| No secret in code | Semua secrets via env var, tidak hardcode |
| Minimal permissions | FB token hanya perlu `pages_manage_posts` |
| No user data | Tidak ada PII yang disimpan |

---

## 22. Performance Requirements

| Metric | Target |
|---|---|
| Sesi Gemini API | < 30 detik |
| Image generation | < 10 detik |
| Facebook upload | < 30 detik |
| Total per sesi | < 120 detik |

---

## 23. Scalability Requirements

Tidak ada scalability concern untuk proyek personal 3x/hari. Jika di masa depan perlu multi-page atau multi-user, arsitektur harus diubah menjadi service-based.

---

## 24. Multi-Tenancy Considerations

**N/A** — Proyek single-user, single-page.

---

## 25. Data Retention Policy

| Data | Retention | Archiving | Deletion |
|---|---|---|---|
| history.json | Maks 60 item terbaru | — | FIFO otomatis |
| Gambar soal (soal/*.png) | Hapus setelah posting | — | Cleanup setelah post sukses |
| GitHub Actions logs | 90 hari (default GitHub) | — | Otomatis |

---

## 26. Edge Cases

| ID | Edge Case | Related FR |
|---|---|---|
| EC-001 | Gemini mengembalikan JSON tidak valid | FR-001 |
| EC-002 | Soal baru sama persis dengan soal di histori (retry sampai beda) | FR-001, FR-005 |
| EC-003 | Pool topik hanya punya 2 item tersisa di hari itu | FR-003 |
| EC-004 | Facebook token expire saat runtime | FR-007 |
| EC-005 | File history.json corrupt (bukan JSON valid) | FR-005 |
| EC-006 | GitHub Actions commit conflict (push gagal karena concurrent) | FR-005 |
| EC-007 | Font file tidak ditemukan di runner | FR-004 |
| EC-008 | Gemini API rate limit tercapai | FR-001 |

---

## 27. Risk Assessment

| ID | Risk | Category | Likelihood | Impact | Mitigation | Linked Assumption |
|---|---|---|---|---|---|---|
| RISK-001 | Gemini API key tidak tersedia | Technical | Low | High | Dokumentasi cara dapat key | ASM-002 |
| RISK-002 | Facebook token expire | Operational | Medium | High | Gunakan System User Token | ASM-004 |
| RISK-003 | GitHub Actions runner perubahan | Operational | Low | Medium | Lock Python version, pin dependencies | — |
| RISK-004 | Gemini API response quality rendah | Technical | Low | Medium | Retry mechanism, prompt engineering | — |

---

## 28. Acceptance Criteria

| ID | Given | When | Then | FR |
|---|---|---|---|---|
| AC-001 | Gemini API key tersedia | Script dipanggil | Mengembalikan JSON valid dengan soal, pilihan, jawaban, penjelasan | FR-001 |
| AC-002 | Gemini mengembalikan soal duplikat | Script mendeteksi duplikat | Retry dengan topik berbeda, max 3x | FR-001 |
| AC-003 | Cron trigger 3x/hari | Setiap eksekusi | Setiap sesi menghasilkan topik yang berbeda dalam 1 hari | FR-002 |
| AC-004 | Pool topik 5 item | 3 sesi berjalan | Tidak ada 2 sesi dengan topik sama | FR-003 |
| AC-005 | Data soal tersedia | Gambar di-generate | PNG 900x700 dengan header tosca, teks terbaca, tidak overflow | FR-004 |
| AC-006 | Soal baru diposting | Histori diupdate | Soal baru muncul di history.json | FR-005 |
| AC-007 | Histori > 60 item | Histori disimpan | Hanya 60 item terbaru yang tersimpan | FR-005 |
| AC-008 | Error fatal terjadi | Notifikasi dikirim | Admin menerima pesan Telegram dalam < 30 detik | FR-006 |
| AC-009 | Gambar + caption siap | Post ke Facebook | Facebook mengembalikan post ID valid | FR-007 |

---

## 28a. Traceability Matrix

| BO | FR/NFR | AC | Risk |
|---|---|---|---|
| BO-001 | FR-001, FR-007 | AC-001, AC-009 | RISK-001, RISK-002 |
| BO-002 | FR-002, FR-003 | AC-003, AC-004 | — |
| BO-003 | FR-004 | AC-005 | — |
| BO-004 | FR-005 | AC-006, AC-007 | — |
| BO-005 | NFR-004 | — | — |
| BO-006 | FR-006 | AC-008 | — |
| BO-001 | NFR-001 | — | — |
| BO-004 | NFR-002 | — | — |
| BO-003 | NFR-003 | — | — |

---

## 29. Release Strategy

| Phase | Scope | Timeline |
|---|---|---|
| Phase 1 (MVP) | Generate soal deret angka + post FB + histori | Day 1 |
| Phase 2 | Semua topik matematika + multi-sesi + randomizer | Day 2 |
| Phase 3 | Tampilan branded (hijau tosca) + Telegram notif | Day 3 |

---

## 30. Future Enhancements

- Auto-reply jawaban & pembahasan di komentar Facebook
- Multi-platform posting (Telegram, Twitter)
- Dashboard monitoring via Google Sheets
- Tambah tipe konten lain (tips belajar, quotes)
- Logo halaman di gambar

---

## 31. Technical Recommendations

| Layer | Recommendation | Justification |
|---|---|---|
| Language | Python 3.12 | Sama dengan referensi, ekosistem matang untuk task automation |
| AI | Google Gemini 2.5 Flash | Cepat, murah (atau gratis), JSON mode built-in |
| Image | Pillow | Mature, no external dependency, available on Ubuntu |
| CI/CD | GitHub Actions | Zero cost, cron built-in, secrets management |
| Notification | Telegram Bot API | Simple, real-time, gratis |
| Font | DejaVu Sans (open source) | Default di Ubuntu, konsisten di runner |

---

## 32. Effort & Resource Estimation

| Feature Group | Estimated Effort | Roles | Dependencies |
|---|---|---|---|
| Generate + Post (deret angka) | 1 day | 1 developer | Gemini API, FB token |
| Multi-topik + randomizer | 0.5 day | 1 developer | — |
| Branded visual (tosca) | 0.5 day | 1 developer | Font files |
| Telegram notifikasi | 0.25 day | 1 developer | Telegram bot token |
| Anti-duplikat + histori | 0.25 day | 1 developer | — |
| GitHub Actions workflow | 0.25 day | 1 developer | — |

**Total estimasi:** ~3 hari kerja untuk 1 developer.
**Critical path:** Gemini API key + Facebook System User Token harus tersedia sebelum development dimulai.

---

## 33. Glossary

| Term | Definition |
|---|---|
| CPNS | Calon Pegawai Negeri Sipil — seleksi pegawai negeri Indonesia |
| TKA | Tes Kompetensi Akademik — bagian dari seleksi CPNS |
| SNBT | Seleksi Nasional Berdasarkan Tes — seleksi masuk PTN |
| TIU | Tes Intelegensi Umum — bagian dari SKD CPNS |
| Gemini | Model AI dari Google untuk generate teks |
| Pillow | Library Python untuk manipulasi gambar |
| GitHub Actions | Platform CI/CD dari GitHub untuk automation |
| System User Token | Token Facebook yang tidak expire dari Business Manager |

---

## 34. Final Validation Summary

| Checklist Item | Status | Notes |
|---|---|---|
| Stakeholders defined | ✓ | 2 stakeholder groups |
| User roles defined | ✓ | 1 role (Admin) — all 7 sub-fields populated |
| Workflows defined | ✓ | 1 main + 1 alternate + 2 failure flows |
| Permissions defined | ✓ | Admin — full access |
| Validations defined | ✓ | Per FR |
| Reports defined | ✓ | N/A — monitoring via GitHub logs + Telegram |
| Notifications defined | ✓ | Failure handling specified |
| Integrations defined | ✓ | Data flow + failure handling for all 3 integrations |
| Audit requirements defined | ✓ | Actions logged via GitHub |
| Security requirements defined | ✓ | Secrets management, no PII |
| Performance targets defined | ✓ | Per NFR |
| Retention policy defined | ✓ | FIFO 60 items |
| Risks documented | ✓ | 4 risks with mitigations |
| Assumptions documented | ✓ | 5 assumptions, unresolved ones linked to risks |
| Acceptance criteria defined | ✓ | 9 criteria, all mapped |
| Traceability matrix complete | ✓ | No orphan FR/NFR |

### Outstanding Gaps

- Detail visual branding (ukuran font, spacing, gradient) perlu ditentukan di implementasi
- Pool topik untuk randomizer final perlu diverifikasi relevansinya dengan CPNS/TKA/SNBT
