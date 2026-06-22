# Architecture — Auto Post Soal Matematika CPNS/TKA/SNBT

## 1. Architecture Overview

**Project type:** Headless automation bot (no web UI)
**Runtime:** Python 3.12 on GitHub Actions (Ubuntu latest)
**Pattern:** Modular script — single entry point with separated concerns via functions

```
┌──────────────────────────────────────────────────┐
│              GitHub Actions (Cron)                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Sesi 1   │  │ Sesi 2   │  │ Sesi 3   │       │
│  │ 06:00 UTC │  │ 10:00 UTC│  │ 13:00 UTC│       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       └─────────────┼──────────────┘              │
│                     ▼                             │
│           ┌─────────────────┐                     │
│           │  main.py         │                     │
│           │  (single script) │                     │
│           └────────┬────────┘                     │
└────────────────────┼──────────────────────────────┘
                     │
     ┌───────────────┼───────────────┐
     ▼               ▼               ▼
┌─────────┐   ┌───────────┐   ┌──────────┐
│ Gemini  │   │   Pillow   │   │ Facebook │
│   AI    │   │  (Image)   │   │  Graph   │
└─────────┘   └───────────┘   └──────────┘
                     │
               ┌─────┴─────┐
               │  history   │
               │  .json     │
               └───────────┘
```

---

## 2. Context Diagram

```
┌───────────────────┐
│   GitHub Actions   │ ◄──── Cron trigger (3x/hari)
│   (Our System)     │
│                    │────► Gemini API ──► JSON soal
│                    │────► Pillow ──► PNG gambar
│                    │────► Facebook API ──► Post ID
│                    │────► Telegram API (if error)
│                    │◄──── history.json (read/write)
└───────────────────┘
```

---

## 3. Module Architecture

Since this is a single-script project, modules are **logical function groups** within one file:

| Module | Responsibilities | Dependencies | Owned Data |
|---|---|---|---|
| **Core** (`main`) | Orchestrasi: load config → pilih topik → generate → gambar → post → simpan | Semua module lain | Flow control |
| **Topic Randomizer** | Pilih topik acak dari pool, pastikan berbeda antar sesi | Pool topik (konstanta) | — |
| **Soal Generator** | Call Gemini API, parse response, validasi JSON | Gemini API, history module | Transient soal |
| **Image Renderer** | Render soal ke PNG dengan Pillow | Pillow, font files | File PNG sementara |
| **Facebook Publisher** | Upload gambar + caption ke Facebook Graph API | Facebook API | — |
| **History Manager** | Baca/tulis history.json, cek duplikat, maintain 60 item | File system | data/history.json |
| **Notifier** | Kirim notifikasi error via Telegram | Telegram API | — |

---

## 4. Layer Architecture

For a headless bot, a simplified 3-layer model applies:

```
┌─────────────────┐
│ Orchestration   │  main() — scheduling, flow control, error boundary
├─────────────────┤
│ Domain Logic    │  generate_soal(), buat_gambar(), post_to_facebook()
├─────────────────┤
│ Infrastructure  │  Gemini API client, Pillow, Facebook Graph HTTP,
│                 │  Telegram HTTP, file I/O for history.json
└─────────────────┘
```

---

## 5. Feature Architecture

### Feature: Generate + Post Soal

| Aspect | Detail |
|---|---|
| **Purpose** | Satu sesi lengkap: generate soal → gambar → post → simpan |
| **Inputs** | Topik (string), histori (array of string) |
| **Outputs** | Facebook post ID, updated history.json |
| **Dependencies** | Gemini API, Pillow, Facebook API |
| **Permissions** | GitHub secrets (API keys) |
| **Error Handling** | Retry Gemini 3x. Jika gagal total → skip sesi + notif Telegram. Facebook retry 1x. |

---

## 6. Data Flow

```
1. Load history.json ────────────────────────────► Cek duplikat
2. Pilih topik acak ──────────────────────────────► Pastikan berbeda dari sesi lain
3. Call Gemini API ─── prompt (topik + histori) ──► JSON response
4. Parse & validasi JSON ─────────────────────────► {soal, pilihan, jawaban, penjelasan}
5. Buat gambar ─────── Pillow ────────────────────► PNG file
6. Post ke Facebook ── Graph API ─────────────────► Post ID
7. Update history ──── append soal ───────────────► data/history.json
8. Commit ke repo ──── git add + commit + push ───► GitHub
```

---

## 7. Integration Design

| Integration | Direction | Trigger | Payload | Error Handling | Retry |
|---|---|---|---|---|---|
| Gemini API | Outbound | Setiap sesi | Prompt → JSON | Parse error → retry dgn topik lain | 3x |
| Facebook Graph | Outbound | Setelah gambar jadi | Multipart (PNG + caption) | HTTP error → retry | 1x |
| Telegram | Outbound | Error fatal | `{message}` | Log warning | 0x |

---

## 8. Authorization Architecture

- **No user authentication** — the system runs as a headless bot
- All secrets stored as **GitHub Actions Secrets** (encrypted at rest)
- No role system needed (single admin)
- Facebook token permission: `pages_manage_posts` minimum

---

## 9. Audit Architecture

| Action | Captured Data | Storage |
|---|---|---|
| Setiap eksekusi sesi | Timestamp, status (success/fail), error message | GitHub Actions logs (90 days) |
| Soal yang diposting | String soal di history.json | Indefinite (in repo) |

No before/after value tracking needed (no CRUD on entities).

---

## 10. Observability Architecture

| Type | Mechanism |
|---|---|
| Application logs | `print()` to stdout (captured by GitHub Actions) |
| Error logs | `print()` + Telegram notification |
| Success confirmation | Returned post ID + "Berhasil" message |
| Alerting | Telegram bot for fatal errors only |

---

## 11. Security Architecture

| Concern | Approach |
|---|---|
| API Key storage | GitHub Actions Secrets (never in code) |
| Facebook token | System User Token recommended (no expiry) |
| No PII | No personal data stored |
| Minimal attack surface | Single script, no open ports, no web server |

---

## 12. Performance Strategy

No performance concern for 3x/day execution. Each session:
- Gemini API: ~10-20s
- Image generation: ~2-5s
- Facebook upload: ~5-15s
- **Total per sesi: < 60s** (well under GitHub Actions 360m limit)

---

## 13. Scalability Strategy

**Current capacity:** 3 sesi/hari, 1 page. No scaling needed.

**If needed in future:** Extract to service-based architecture with:
- Queue (Redis/PubSub) for job scheduling
- Database (PostgreSQL) for history
- Multi-page support via config table

---

## 14. Deployment Architecture

```
┌──────────────────────────────────────────┐
│  Developer                               │
│  └─ push to GitHub ──────────────────┐   │
└──────────────────────────────────────┘   │
                                           ▼
┌──────────────────────────────────────────┐
│  GitHub Repository                        │
│  ├── main.py                             │
│  ├── requirements.txt                    │
│  ├── fonts/                              │
│  ├── data/history.json                   │
│  └── .github/workflows/auto-post.yml     │
└──────────────────┬───────────────────────┘
                   │ Cron trigger
                   ▼
┌──────────────────────────────────────────┐
│  GitHub Actions Runner (Ubuntu latest)   │
│  ├── pip install -r requirements.txt     │
│  ├── python main.py                      │
│  ├── git add data/history.json           │
│  ├── git commit                          │
│  └── git push                            │
└──────────────────────────────────────────┘
```

**Rollback:** Simple — revert or remove the problematic commit. The previous history.json remains intact.

---

## 15. ADRs

### ADR-001: Single script vs. multi-module

| Aspect | Value |
|---|---|
| **Decision** | Single Python file (`main.py`) with function-level modularity |
| **Reason** | Bot sederhana dengan < 10 function groups. Multi-file menambah kompleksitas tanpa manfaat. |
| **Alternatives** | Package dengan `src/` directory |
| **Tradeoffs** | Jika proyek tumbuh signifikan, refactor ke package. Saat ini over-engineering. |
| **Final Choice** | Single file |

### ADR-002: No database server

| Aspect | Value |
|---|---|
| **Decision** | JSON file (`data/history.json`) sebagai penyimpanan state |
| **Reason** | Tidak perlu query, tidak ada relasi, data < 100 item. Database server adalah overhead untuk proyek ini. |
| **Alternatives** | SQLite, PostgreSQL via Supabase |
| **Tradeoffs** | Tidak ada concurrency write — GitHub Actions menjalankan 1 sesi per run, aman. |
| **Final Choice** | JSON file |

### ADR-003: GitHub Actions sebagai scheduler

| Aspect | Value |
|---|---|
| **Decision** | Cron trigger di GitHub Actions |
| **Reason** | Zero cost, secrets management built-in, otomatis commit history.json |
| **Alternatives** | Vercel Cron, AWS Lambda, Railway |
| **Tradeoffs** | Tidak ada retry otomatis (jika cron gagal, harus manual re-run via workflow_dispatch) |
| **Final Choice** | GitHub Actions |

---

## 16. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Token Facebook expire | Posting gagal total | Gunakan System User Token; maintenance reminder di repo |
| Gemini API change | Format response berubah | Pin model version (gemini-3.1-flash-lite); error handling robust |
| GitHub Actions outage | Posting terlewat | workflow_dispatch untuk manual trigger |
| Font rendering issue | Gambar error | Fallback ke default Pillow font |

---

## 17. Recommendations

1. **Implementasi bertahap:** Mulai dengan 1 topik (deret angka) dulu, lalu tambah topik lain
2. **System User Token:** Setup Facebook Business Manager + System User agar token tidak expire
3. **Test lokal:** Jalankan `python main.py` lokal dengan env var sebelum push ke GitHub
4. **Branch protection:** Tidak kritis untuk proyek personal, tapi disarankan
