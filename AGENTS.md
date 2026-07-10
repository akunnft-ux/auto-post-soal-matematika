# Agent Memory — auto-post-soal-matematika

## Template Gambar (1080×1080)

### Layout
- **Header**: grape #6C4FE0, 210px tinggi, badge pill kuning (Kalam/Symbola) + judul Fredoka 50px putih
- **Body**: cream #FFF8EC, margin 64px kiri/kanan
- **Trick-box**: white bg, border ink 3px, shadow kuning 8px, flag coral pill
- **Footer**: dashed line #d8cfba, tagline kiri (Symbola), CTA pill coral kanan "Follow →"

### Font
- FONT_FREDOKA = `fonts/Fredoka-Variable.ttf`
- FONT_KALAM = `fonts/Kalam-Regular.ttf`
- FONT_EMOJI = `fonts/Symbola.ttf`
- DejaVu Sans untuk body text fallback

### Warna
- COLOR_BG = (255, 248, 236) #FFF8EC
- COLOR_INK = (43, 39, 48) #2B2730
- COLOR_SUN = (255, 201, 74) #FFC94A
- COLOR_CORAL = (255, 107, 87) #FF6B57
- COLOR_HEADER_BG = (108, 79, 224) #6C4FE0

### Badge per Content Type
- soal: "📝 Soal Kilat"
- materi: "💡 Math Trik Harian"
- fakta: "🤯 Fun Fact"

### Trick-box Flag per Content Type
- soal: "🧠 Trik Cepat" — jawaban + penjelasan (cara cepat)
- materi: "📐 Rumus" — rumus + contoh
- fakta: "💡 Triknya" — sumber atau fallback ajakan

### Font sizes (agar muat konten panjang)
- Body soal: 26px, line_h 34px
- Opsi: 24px, line_h 30px
- Body materi/fakta: 28px, line_h 34px
- Trick-box: pad 16, line_h 30

### Fungsi Utama
- `render_card(data, topic, content_type, ...)` — entry point rendering
- `_draw_header()` — header ungu
- `_draw_trick_box()` — trick-box dengan flag + content
- `_draw_footer()` — footer dengan CTA
- `_render_body_soal/materi/fakta()` — body per tipe

### Konvensi
- `buat_gambar_konten` adalah alias dari `render_card` (kompatibilitas main.py)
- Semua fungsi Gemini/posting/history tidak disentuh

### Fixes Applied
- CSV parser `_extract_record()` baca `account_type`/`format`/`theme` dari kolom CSV (bukan hardcoded None)
- Tambah `topic` parameter ke `render_card` agar call dari main() kompatibel
- Perkecil font & spacing body agar konten panjang tidak overflow
