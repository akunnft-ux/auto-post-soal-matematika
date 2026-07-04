import os
import json
import random
import re
import requests
from datetime import datetime, date
from PIL import Image, ImageDraw, ImageFont
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HISTORY_PATH = "data/history.json"
FONT_BOLD = "fonts/DejaVuSans-Bold.ttf"
FONT_REGULAR = "fonts/DejaVuSans.ttf"
MAX_HISTORY_ITEMS = 180
IMG_WIDTH = 1080
IMG_HEIGHT = 1080

COLOR_BG = (255, 248, 231)          # warm cream #FFF8E7
COLOR_NAVY = (27, 42, 74)            # navy #1B2A4A
COLOR_ORANGE = (255, 140, 66)        # bright orange #FF8C42
COLOR_WHITE = (255, 255, 255)
COLOR_TEXT = (44, 62, 80)            # dark slate #2C3E50
COLOR_FOOTER = (149, 165, 166)       # gray #95A5A6
COLOR_STICKY = (255, 243, 176)       # sticky note yellow #FFF3B0

TOPIC_COLORS = {
    "deret_angka":         ((46, 134, 222), (214, 234, 248)),    # blue
    "aritmatika_aljabar":  ((39, 174, 96), (213, 245, 227)),     # green
    "peluang_statistika":  ((142, 68, 173), (232, 218, 239)),    # purple
    "geometri":            ((231, 76, 60), (250, 219, 216)),     # red/pink
    "fungsi_grafik":       ((243, 156, 18), (253, 235, 208)),    # orange/gold
}

DODDLE_ICONS = ["★", "◆", "●", "✓", "➤"]

TOPICS = [
    "deret_angka",
    "aritmatika_aljabar",
    "peluang_statistika",
    "geometri",
    "fungsi_grafik",
]

CONTENT_TYPES = ["soal", "materi", "fakta"]

CONTENT_TYPE_LABELS = {
    "soal": "SOAL MATEMATIKA",
    "materi": "MATERI MATEMATIKA",
    "fakta": "FAKTA MATEMATIKA",
}

CONTENT_TYPE_HEADER_SUB = {
    "soal": "CPNS  •  TKA  •  SNBT",
    "materi": "Belajar Konsep & Rumus",
    "fakta": "Fakta Menarik",
}

CONTENT_TYPE_WEIGHTS = [3, 3, 2]  # soal : materi : fakta

TOPIC_LABELS = {
    "deret_angka": "Deret Angka & Pola Bilangan",
    "aritmatika_aljabar": "Aritmatika & Aljabar",
    "peluang_statistika": "Peluang & Statistika",
    "geometri": "Geometri",
    "fungsi_grafik": "Fungsi & Grafik",
}

HASHTAG_POOL = [
    "#SoalMatematika", "#CPNS2026", "#BelajarMatematika",
    "#MatematikaDasar", "#CPNS", "#TIUCPNS", "#SKDCPNS",
    "#TryoutCPNS", "#RuangBelajar", "#Matematika",
    "#LatihanCPNS", "#StudiCPNS",
]

EMOJI_POOL = ["🧮", "📐", "📝", "✏️", "📊", "➗", "➕", "❌"]

FOOTER_POOL = [
    "",
    "Simak pembahasan di akhir video",
    "Semoga membantu",
    "Selamat belajar",
]

_topic_image_cache = {}


def get_topic_image(topic, size=200, opacity=0.15):
    key = (topic, size)
    if key not in _topic_image_cache:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        accent, _ = TOPIC_COLORS.get(topic, ((100, 100, 100), (220, 220, 220)))
        accent_rgba = (*accent, 255)
        light_rgba = (*accent, 60)
        cx, cy = size // 2, size // 2
        r = size // 2 - 12

        if topic == "geometri":
            pts = [(cx - r, cy + r), (cx + r, cy + r), (cx - r, cy - r)]
            draw.polygon(pts, fill=light_rgba, outline=accent_rgba, width=3)
            draw.text((cx - r - 10, cy + r - 8), "a", fill=accent_rgba, anchor="rb")
            draw.text((cx + r + 10, cy + r - 8), "b", fill=accent_rgba, anchor="lb")
            draw.text((cx - r - 10, cy - r + 8), "c", fill=accent_rgba, anchor="rt")

        elif topic == "fungsi_grafik":
            draw.line([(12, cy), (size - 12, cy)], fill=accent_rgba, width=2)
            draw.line([(cx, 12), (cx, size - 12)], fill=accent_rgba, width=2)
            arr = [(cx + int(x / r * r * 0.85), cy - int((x / r) ** 2 * r * 0.75)) for x in range(-r, r + 1)]
            draw.line(arr, fill=accent_rgba, width=3)

        elif topic == "peluang_statistika":
            bw = r // 4
            gap = 8
            heights = [int(r * 0.75), int(r * 0.95), int(r * 0.55)]
            colors = [(*accent, 200), (*accent, 220), (*accent, 150)]
            for i in range(3):
                x1 = cx - r + i * (bw + gap)
                y1 = cy + r
                y2 = y1 - heights[i]
                draw.rectangle([x1, y2, x1 + bw, y1], fill=colors[i], outline=accent_rgba, width=2)

        elif topic == "deret_angka":
            draw.line([(15, cy), (size - 15, cy)], fill=accent_rgba, width=3)
            spacing = 2 * r // 5
            dot_rad = 5
            for i in range(5):
                px = cx - 2 * spacing + i * spacing
                dr = dot_rad + i
                draw.ellipse([px - dr, cy - dr, px + dr, cy + dr], fill=accent_rgba)

        elif topic == "aritmatika_aljabar":
            draw.line([(cx - r, cy + 10), (cx + r, cy + 10)], fill=accent_rgba, width=3)
            draw.line([(cx - r, cy + 10), (cx - r, cy - 30)], fill=accent_rgba, width=2)
            draw.line([(cx + r, cy + 10), (cx + r, cy - 30)], fill=accent_rgba, width=2)
            draw.polygon([(cx - 7, cy + 10), (cx + 7, cy + 10), (cx, cy + 22)], fill=accent_rgba)
            draw.text((cx - r, cy - 40), "x+5=10", fill=accent_rgba, anchor="mt", font=ImageFont.truetype(FONT_BOLD, 16))

        _topic_image_cache[key] = img
    else:
        img = _topic_image_cache[key].copy()

    if opacity < 1.0:
        alpha = img.split()[3]
        alpha = alpha.point(lambda p: int(p * opacity))
        img.putalpha(alpha)
    return img

HOOK_TEMPLATES = [
    "Coba soal matematika ini! 🧐",
    "90% orang salah jawab. Kamu bisa? ⚡",
    "Kuis matematika untuk CPNS! 🎯",
    "Jangan terkecoh dengan soal ini! 💡",
    "Kebanyakan orang menjawab salah. Ayo coba! 🤔",
    "Tes kemampuan matematikamu! 📝",
    "Siap untuk soal hari ini? 🔥",
]

HOOK_MATERI = [
    "Pahami konsep matematika ini! 📖",
    "Materi penting buat CPNS! 🎯",
    "Kuasai rumus ini biar makin jago! 💡",
    "Yuk belajar matematika! 📚",
    "Rumus ini sering keluar di tes! 🔥",
]

HOOK_FAKTA = [
    "Tahukah kamu? 🤔",
    "Fakta matematika yang mengejutkan! ✨",
    "Matematika itu penuh kejutan! 🔍",
    "Unik banget! Cek fakta ini! 😮",
    "Whoa! Fakta matematika hari ini! ⚡",
]

CTA_POOL = [
    "Share ke temanmu biar ikut belajar! 📤",
    "Simpan postingan ini untuk latihan! 📌",
    "Coba kerjakan soal ini! 🧮",
    "Latihan rutin biar makin jago! 📚",
    "Ayo asah kemampuanmu! ⚡",
]

CTA_MATERI = [
    "Catat rumusnya buat belajar! 📝",
    "Share biar temanmu paham juga! 📤",
    "Simpan buat referensi belajar! 📌",
    "Latihan soal terkait materi ini! 📚",
]

CTA_FAKTA = [
    "Bagikan fakta ini ke temanmu! 📤",
    "Kaget juga ya? Simak terus! 😄",
    "Follow buat fakta lainnya! 🔔",
    "Share biar makin banyak yang tahu! 📤",
]

LEARNING_CONFIG_FILE = "self_learning/learning_config.json"

TOPIC_PROMPTS = {
    "deret_angka": {
        "soal": "soal Deret Angka atau Pola Bilangan (barisan & deret). "
                "Contoh: deret Fibonacci, deret aritmatika, deret geometri, pola kuadrat, pola segitiga, dll.",
        "materi": "MATERI tentang Deret Angka atau Pola Bilangan. "
                  "Jelaskan konsep barisan & deret (aritmatika, geometri, Fibonacci, pola kuadrat). "
                  "Sertakan rumus utama dan contoh penerapan singkat.",
        "fakta": "FAKTA menarik tentang Deret Angka atau Pola Bilangan. "
                 "Misal: keunikan deret Fibonacci di alam, pola bilangan segitiga Pascal, dll. "
                 "Beri fakta yang mengejutkan dan edukatif.",
    },
    "aritmatika_aljabar": {
        "soal": "soal Aritmatika atau Aljabar. "
                "Contoh: perbandingan, kecepatan/jarak/waktu, persamaan linier, sistem persamaan, "
                "persamaan kuadrat, perbandingan senilai/berbalik nilai, bunga, diskon, skala, dll.",
        "materi": "MATERI tentang Aritmatika atau Aljabar. "
                  "Jelaskan konsep seperti persamaan kuadrat, sistem persamaan linier, atau perbandingan. "
                  "Sertakan rumus utama, langkah penyelesaian, dan contoh.",
        "fakta": "FAKTA menarik tentang Aritmatika atau Aljabar. "
                 "Misal: sejarah aljabar, keunikan angka nol, teka-teki matematika terkenal, dll. "
                 "Beri fakta yang mengejutkan dan edukatif.",
    },
    "peluang_statistika": {
        "soal": "soal Peluang atau Statistika. "
                "Contoh: peluang kejadian, kombinasi, permutasi, mean/median/modus, "
                "rata-rata gabungan, diagram, frekuensi, dll.",
        "materi": "MATERI tentang Peluang atau Statistika. "
                  "Jelaskan konsep seperti permutasi-kombinasi, peluang kejadian, atau ukuran pemusatan data. "
                  "Sertakan rumus utama, interpretasi, dan contoh.",
        "fakta": "FAKTA menarik tentang Peluang atau Statistika. "
                 "Misal: paradoks Monty Hall, birthday paradox, kesalahan statistik terkenal, dll. "
                 "Beri fakta yang mengejutkan dan edukatif.",
    },
    "geometri": {
        "soal": "soal Geometri. "
                "Contoh: luas & keliling bangun datar, volume bangun ruang, "
                "kesebangunan, teorema Pythagoras, sudut, garis singgung, dll.",
        "materi": "MATERI tentang Geometri. "
                  "Jelaskan konsep seperti teorema Pythagoras, kesebangunan, atau rumus volume bangun ruang. "
                  "Sertakan rumus utama, visualisasi konsep, dan contoh.",
        "fakta": "FAKTA menarik tentang Geometri. "
                 "Misal: bilangan phi (π) dan keunikannya, fraktal di alam, geometri non-Euclid, dll. "
                 "Beri fakta yang mengejutkan dan edukatif.",
    },
    "fungsi_grafik": {
        "soal": "soal Fungsi atau Grafik. "
                "Contoh: fungsi linier, fungsi kuadrat, gradien, persamaan garis, "
                "domain/range, komposisi fungsi, invers fungsi, dll.",
        "materi": "MATERI tentang Fungsi atau Grafik. "
                  "Jelaskan konsep seperti fungsi kuadrat, komposisi fungsi, atau transformasi grafik. "
                  "Sertakan rumus utama, sifat-sifat fungsi, dan contoh.",
        "fakta": "FAKTA menarik tentang Fungsi atau Grafik. "
                 "Misal: aplikasi fungsi dalam kehidupan nyata, grafik terkenal, keunikan fungsi trigonometri, dll. "
                 "Beri fakta yang mengejutkan dan edukatif.",
    },
}

client = genai.Client(api_key=GEMINI_API_KEY)


def notify_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=10)
    except Exception as e:
        print(f"Gagal kirim notifikasi Telegram: {e}")


def load_history():
    if not os.path.exists(HISTORY_PATH):
        return []
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_history(history):
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    history = history[-MAX_HISTORY_ITEMS:]
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def get_used_topics_today(history):
    today_str = date.today().isoformat()
    used = set()
    for item in history:
        if isinstance(item, dict) and item.get("tanggal") == today_str:
            used.add(item.get("topik"))
    return used


def is_soal_duplicate(soal_text, history):
    soal_lower = soal_text.lower()
    for item in history:
        existing = item if isinstance(item, str) else item.get("soal", "")
        existing_lower = existing.lower()
        if existing == soal_text:
            return True
        words_soal = set(soal_lower.split())
        words_existing = set(existing_lower.split())
        if len(words_soal) > 0 and len(words_existing) > 0:
            overlap = len(words_soal & words_existing) / max(len(words_soal), len(words_existing))
            if overlap > 0.70:
                return True
    return False


def pick_topic(history: list) -> str:
    used_today = get_used_topics_today(history)
    available = [t for t in TOPICS if t not in used_today]
    if not available:
        available = TOPICS
    return random.choice(available)


def pick_content_type() -> str:
    return random.choices(CONTENT_TYPES, weights=CONTENT_TYPE_WEIGHTS, k=1)[0]


def generate_content(topic, content_type, history, max_retry=3):
    history_text = "\n".join(
        f"- {(h.get('soal') or h.get('judul') or str(h))[:120]}"
        for h in history[-50:]
    ) or "(belum ada histori)"

    originality_rule = (
        "KONTEN HARUS ORISINIL DAN BELUM PERNAH ADA SEBELUMNYA.\n"
        "Buat konten yang SAMA SEKALI BARU, tidak mirip dengan konten di atas.\n"
        "Gunakan konteks/cerita/angka/sudut pandang yang BERBEDA dari histori.\n"
        "JANGAN menggunakan soal standar textbook — buat variasi unik.\n"
        "Hindari pola soal yang sama (misal: jangan selalu 'Dalam sebuah kotak terdapat...').\n"
        "Variasikan struktur kalimat, angka, dan konteks cerita.\n"
        "Angka-angka dalam soal harus BERBEDA dari histori di atas."
    )

    if content_type == "soal":
        prompt = f"""
    Buat 1 {TOPIC_PROMPTS[topic][content_type]}
    Level: sedang hingga sulit (CPNS / TKA / SNBT).

    {originality_rule}

    Histori konten sebelumnya (JANGAN buat yang mirip):
    {history_text}

    Jawab HANYA dengan JSON valid, tanpa markdown, tanpa penjelasan tambahan.
    Format:
    {{
      "tipe": "soal",
      "soal": "teks soal lengkap",
      "pilihan": ["pilihan A", "pilihan B", "pilihan C", "pilihan D"],
      "jawaban": "pilihan yang benar (sama persis dengan teks pilihan)",
      "penjelasan": "penjelasan cara menyelesaikan soal"
    }}
    """
    elif content_type == "materi":
        prompt = f"""
    Buat 1 {TOPIC_PROMPTS[topic][content_type]}

    {originality_rule}

    Histori konten sebelumnya (JANGAN buat yang mirip):
    {history_text}

    Jawab HANYA dengan JSON valid, tanpa markdown, tanpa penjelasan tambahan.
    Format:
    {{
      "tipe": "materi",
      "judul": "judul materi singkat dan menarik",
      "isi_materi": "penjelasan konsep lengkap, mudah dipahami, 2-3 paragraf pendek",
      "rumus": "rumus utama jika ada (dalam teks, misal: Rumus: a² + b² = c²)",
      "contoh": "contoh singkat penerapan materi"
    }}
    """
    else:  # fakta
        prompt = f"""
    Buat 1 {TOPIC_PROMPTS[topic][content_type]}

    {originality_rule}

    Histori konten sebelumnya (JANGAN buat yang mirip):
    {history_text}

    Jawab HANYA dengan JSON valid, tanpa markdown, tanpa penjelasan tambahan.
    Format:
    {{
      "tipe": "fakta",
      "judul": "judul fakta singkat dan menarik",
      "isi_fakta": "penjelasan fakta yang menarik dan edukatif, 1-2 paragraf",
      "sumber": "sumber atau konteks singkat (opsional)"
    }}
    """

    for attempt in range(1, max_retry + 1):
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.95,
                ),
            )
            data = json.loads(response.text.strip())

            if data.get("tipe") == "soal":
                required_keys = {"soal", "pilihan", "jawaban", "penjelasan"}
                if not required_keys.issubset(data.keys()):
                    raise ValueError("Field soal tidak lengkap")
                if not isinstance(data["pilihan"], list) or len(data["pilihan"]) != 4:
                    raise ValueError("Pilihan harus array 4 item")
                if data["jawaban"] not in data["pilihan"]:
                    raise ValueError("Jawaban tidak ada di pilihan")
                if is_soal_duplicate(data["soal"], history):
                    raise ValueError("Soal duplikat dengan histori")
            elif data.get("tipe") == "materi":
                required_keys = {"judul", "isi_materi", "rumus", "contoh"}
                if not required_keys.issubset(data.keys()):
                    raise ValueError("Field materi tidak lengkap")
            elif data.get("tipe") == "fakta":
                required_keys = {"judul", "isi_fakta"}
                if not required_keys.issubset(data.keys()):
                    raise ValueError("Field fakta tidak lengkap")
            else:
                raise ValueError(f"Tipe konten tidak dikenal: {data.get('tipe')}")

            return data
        except Exception as e:
            print(f"[Percobaan {attempt}/{max_retry}] Gagal: {e}")

    return None


def wrap_text(text, font, draw, max_width):
    text = text.replace("\n", " ")
    words = text.split(" ")
    lines, current = [], ""
    for word in words:
        test = f"{current} {word}".strip()
        if draw.textlength(test, font=font) <= max_width:
            current = test
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_rounded_rect(draw, xy, radius, fill):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill)


def render_soal(draw, data, topic, margin, usable_width, font_soal, font_pilihan, font_badge, topic_accent, topic_bg, badge_y, header_h):
    y = badge_y + 80
    soal_lines = wrap_text(data["soal"], font_soal, draw, usable_width)
    for line in soal_lines:
        draw.text((margin, y), line, fill=COLOR_TEXT, font=font_soal)
        y += 52
    y += 30
    for i, p in enumerate(data["pilihan"]):
        letter = chr(65 + i)
        option_text = f"{letter}.  {p}"
        option_lines = wrap_text(option_text, font_pilihan, draw, usable_width - 50)
        bg_y = y - 8
        text_block_h = len(option_lines) * 44 + 18
        draw_rounded_rect(draw, [margin, bg_y, IMG_WIDTH - margin, bg_y + text_block_h], radius=14, fill=COLOR_WHITE)
        draw.rounded_rectangle([margin + 2, bg_y + 2, IMG_WIDTH - margin - 2, bg_y + text_block_h - 2], radius=12, fill=None, outline=topic_bg, width=2)
        draw.rounded_rectangle([margin, bg_y, margin + 8, bg_y + text_block_h], radius=4, fill=topic_accent)
        for line in option_lines:
            draw.text((margin + 30, y), line, fill=COLOR_TEXT, font=font_pilihan)
            y += 44
        y += 14
    return y


def render_materi(draw, data, topic, margin, usable_width, font_soal, font_materi_judul, font_materi_body, font_label, topic_accent, topic_bg, badge_y, header_h):
    y = badge_y + 60

    font_rumus = ImageFont.truetype(FONT_BOLD, 28)

    # ── Icon + Label ──
    label = "📖 MATERI"
    lw = draw.textlength(label, font=font_label)
    draw_rounded_rect(draw, [margin, y, margin + lw + 24, y + 34], radius=6, fill=topic_accent)
    draw.text((margin + 12, y + 17), label, fill=COLOR_WHITE, anchor="lm", font=font_label)
    y += 50

    # ── Judul ──
    judul_lines = wrap_text(data["judul"], font_materi_judul, draw, usable_width)
    for line in judul_lines:
        draw.text((margin, y), line, fill=COLOR_NAVY, font=font_materi_judul)
        y += 42
    y += 10

    # ── Isi Materi ──
    isi_lines = wrap_text(data["isi_materi"], font_materi_body, draw, usable_width)
    for line in isi_lines:
        draw.text((margin, y), line, fill=COLOR_TEXT, font=font_materi_body)
        y += 36
    y += 12

    # ── Rumus box ──
    rumus_text = data.get("rumus", "")
    if rumus_text:
        rumus_pad = 14
        rumus_lines = wrap_text(rumus_text, font_rumus, draw, usable_width - 2 * rumus_pad)
        rumus_h = len(rumus_lines) * 36 + 2 * rumus_pad
        draw_rounded_rect(draw, [margin, y, IMG_WIDTH - margin, y + rumus_h], radius=10, fill=tuple(min(c + 220, 255) for c in topic_accent))
        draw.rounded_rectangle([margin, y, IMG_WIDTH - margin, y + rumus_h], radius=10, fill=None, outline=topic_accent, width=2)
        draw.text((margin + 12, y + rumus_pad), "📐", fill=topic_accent, font=font_label)
        rumus_y = y + rumus_pad + 4
        for line in rumus_lines:
            draw.text((margin + 44, rumus_y), line, fill=COLOR_NAVY, font=font_rumus)
            rumus_y += 36
        y += rumus_h + 20

    # ── Contoh ──
    contoh_text = data.get("contoh", "")
    if contoh_text:
        c_label = "💡 Contoh"
        draw.text((margin, y), c_label, fill=topic_accent, font=font_materi_judul)
        y += 38
        contoh_lines = wrap_text(contoh_text, font_materi_body, draw, usable_width)
        for line in contoh_lines:
            draw.text((margin, y), line, fill=COLOR_TEXT, font=font_materi_body)
            y += 36

    return y


def render_fakta(draw, data, topic, margin, usable_width, font_soal, font_materi_judul, font_materi_body, font_label, topic_accent, topic_bg, badge_y, header_h):
    y = badge_y + 60

    # ── Icon + Label ──
    label = "✨ FAKTA"
    lw = draw.textlength(label, font=font_label)
    draw_rounded_rect(draw, [margin, y, margin + lw + 24, y + 34], radius=6, fill=topic_accent)
    draw.text((margin + 12, y + 17), label, fill=COLOR_WHITE, anchor="lm", font=font_label)
    y += 55

    # ── Judul ──
    judul_lines = wrap_text(data["judul"], font_materi_judul, draw, usable_width)
    for line in judul_lines:
        draw.text((margin, y), line, fill=COLOR_NAVY, font=font_materi_judul)
        y += 42
    y += 10

    # ── Decorative large quote mark ──
    draw.text((margin, y), "❝", fill=topic_accent, font=ImageFont.truetype(FONT_BOLD, 60))
    y += 10

    # ── Isi Fakta ──
    isi_lines = wrap_text(data["isi_fakta"], font_materi_body, draw, usable_width)
    for line in isi_lines:
        draw.text((margin + 20, y), line, fill=COLOR_TEXT, font=font_materi_body)
        y += 36
    y += 5

    # ── Closing quote ──
    draw.text((IMG_WIDTH - margin - 20, y), "❞", fill=topic_accent, font=ImageFont.truetype(FONT_BOLD, 60), anchor="rt")

    # ── Sumber ──
    sumber = data.get("sumber", "")
    if sumber:
        y += 50
        draw.text((margin, y), f"📌 {sumber}", fill=COLOR_FOOTER, font=ImageFont.truetype(FONT_REGULAR, 22))

    return y


def buat_gambar_konten(data, topic, content_type, filename="soal/konten_hari_ini.png"):
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    img = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), COLOR_BG)
    draw = ImageDraw.Draw(img)

    topic_img = get_topic_image(topic, size=240, opacity=0.12)
    wx = IMG_WIDTH - 240 - 40
    wy = IMG_HEIGHT - 240 - 60
    img.paste(topic_img, (wx, wy), topic_img)

    font_heading = ImageFont.truetype(FONT_BOLD, 48)
    font_subtitle = ImageFont.truetype(FONT_REGULAR, 26)
    font_badge = ImageFont.truetype(FONT_BOLD, 24)
    font_soal = ImageFont.truetype(FONT_REGULAR, 34)
    font_pilihan = ImageFont.truetype(FONT_REGULAR, 30)
    font_footer = ImageFont.truetype(FONT_REGULAR, 22)
    font_icon = ImageFont.truetype(FONT_BOLD, 28)
    font_materi_judul = ImageFont.truetype(FONT_BOLD, 30)
    font_materi_body = ImageFont.truetype(FONT_REGULAR, 26)
    font_label = ImageFont.truetype(FONT_BOLD, 22)

    margin = 60
    usable_width = IMG_WIDTH - 2 * margin
    header_h = 160

    topic_accent, topic_bg = TOPIC_COLORS.get(topic, (COLOR_NAVY, (220, 220, 220)))

    # ── Common Header ──
    draw.rounded_rectangle([(0, 0), (IMG_WIDTH, header_h)], radius=0, fill=COLOR_NAVY)
    draw.rounded_rectangle([(0, header_h - 8), (IMG_WIDTH, header_h + 4)], radius=0, fill=COLOR_ORANGE)

    header_title = CONTENT_TYPE_LABELS.get(content_type, "SOAL MATEMATIKA")
    header_sub = CONTENT_TYPE_HEADER_SUB.get(content_type, "CPNS  •  TKA  •  SNBT")
    draw.text((IMG_WIDTH / 2, 55), header_title, fill=COLOR_WHITE, anchor="mm", font=font_heading)
    draw.text((IMG_WIDTH / 2, 115), header_sub, fill=(255, 200, 150), anchor="mm", font=font_subtitle)

    # Sticky note corner
    sticky_x = IMG_WIDTH - 120
    sticky_y = 20
    draw.rounded_rectangle([(sticky_x, sticky_y), (sticky_x + 80, sticky_y + 70)], radius=6, fill=COLOR_STICKY, outline=(200, 180, 100), width=2)
    draw.text((sticky_x + 40, sticky_y + 35), "✏️", fill=(80, 60, 20), anchor="mm", font=font_icon)

    # Decorative star top-left
    draw.text((40, 25), "★", fill=(255, 200, 100), anchor="mm", font=font_icon)
    draw.text((100, 130), "✦", fill=(255, 200, 100), anchor="mm", font=font_icon)

    # ── Topic badge ──
    topic_label = TOPIC_LABELS.get(topic, topic)
    badge_label = f"★ {topic_label}"
    badge_w = draw.textlength(badge_label, font=font_badge) + 44
    badge_x = (IMG_WIDTH - badge_w) / 2
    badge_y = header_h + 28
    draw_rounded_rect(draw, [badge_x, badge_y, badge_x + badge_w, badge_y + 42], radius=21, fill=topic_accent)
    draw.rounded_rectangle([badge_x + 4, badge_y + 4, badge_x + badge_w - 4, badge_y + 38], radius=17, fill=None, outline=COLOR_WHITE, width=2)
    draw.text((IMG_WIDTH / 2, badge_y + 21), badge_label, fill=COLOR_WHITE, anchor="mm", font=font_badge)

    # ── Content body ──
    if content_type == "soal":
        y = render_soal(draw, data, topic, margin, usable_width, font_soal, font_pilihan, font_badge, topic_accent, topic_bg, badge_y, header_h)
    elif content_type == "materi":
        y = render_materi(draw, data, topic, margin, usable_width, font_soal, font_materi_judul, font_materi_body, font_label, topic_accent, topic_bg, badge_y, header_h)
    else:  # fakta
        y = render_fakta(draw, data, topic, margin, usable_width, font_soal, font_materi_judul, font_materi_body, font_label, topic_accent, topic_bg, badge_y, header_h)

    # ── Footer ──
    footer_y = min(IMG_HEIGHT - 80, y + 60)
    if footer_y > IMG_HEIGHT - 80:
        footer_y = IMG_HEIGHT - 80
    draw.line([(margin, footer_y), (IMG_WIDTH - margin, footer_y)], fill=topic_bg, width=3)

    deco_icon = random.choice(DODDLE_ICONS)
    footer = random.choice(FOOTER_POOL)
    if footer:
        draw.text(
            (IMG_WIDTH / 2 - 20, footer_y + 32),
            footer,
            fill=COLOR_FOOTER, anchor="mm", font=font_footer
        )
        fw = draw.textlength(footer, font=font_footer)
        draw.text(
            (IMG_WIDTH / 2 + fw / 2 + 20, footer_y + 32),
            f" {deco_icon}",
            fill=COLOR_ORANGE, anchor="mm", font=font_footer
        )
    else:
        draw.text(
            (IMG_WIDTH / 2, footer_y + 32),
            deco_icon,
            fill=COLOR_ORANGE, anchor="mm", font=font_icon
        )

    img.save(filename)
    return filename


def post_to_facebook(image_path, caption):
    url = f"https://graph.facebook.com/{FB_PAGE_ID}/photos"
    with open(image_path, "rb") as img:
        payload = {"caption": caption, "access_token": FB_ACCESS_TOKEN}
        files = {"source": img}
        response = requests.post(url, data=payload, files=files, timeout=30)

    result = response.json()

    if not response.ok or "error" in result:
        raise RuntimeError(f"Gagal posting: {result}")

    return result


def compliance_check(caption):
    disallowed_bait_patterns = [
        "comment.*if you", "comment.*if agree", "tag.*friends",
        "tag 5", "share this.*see", "share.*to win",
    ]
    caption_lower = caption.lower()
    for pattern in disallowed_bait_patterns:
        if re.search(pattern, caption_lower):
            raise ValueError(f"Compliance: engagement bait pattern '{pattern}' detected in caption")
    return True


def format_caption(data: dict, topic: str) -> str:
    label = TOPIC_LABELS.get(topic, topic)
    emoji = random.choice(EMOJI_POOL)
    tags = " ".join(random.sample(HASHTAG_POOL, k=random.randint(2, 3)))
    content_type = data.get("tipe", "soal")

    if content_type == "soal":
        hook = random.choice(HOOK_TEMPLATES)
        cta = random.choice(CTA_POOL)
        op = "\n".join(f"{chr(65 + i)}. {p}" for i, p in enumerate(data["pilihan"]))
        templates = [
            f"{{hook}}\n\n{{emoji}} {{label}}\n\n{{soal}}\n\n{{pilihan}}\n\n{{cta}}\n\n{{tags}}",
            f"{{hook}}\n\n{{label}}\n\n{{soal}}\n\n{{emoji}} {{pilihan}}\n\n{{cta}}\n\n{{tags}}",
            f"{{hook}}\n\n{{emoji}} Latihan {{label}}\n\n{{soal}}\n\n{{pilihan}}\n\n{{cta}}\n\n{{tags}}",
            f"{{hook}}\n\n{{soal}}\n\n{{pilihan}}\n\n{{cta}}\n\n{{tags}}",
        ]
        template = random.choice(templates)
        caption = template.format(
            hook=hook, emoji=emoji, label=label,
            soal=data["soal"], pilihan=op, cta=cta, tags=tags,
        )
    elif content_type == "materi":
        hook = random.choice(HOOK_MATERI)
        cta = random.choice(CTA_MATERI)
        templates = [
            f"{{hook}}\n\n{{emoji}} {{label}}\n\n**{{judul}}**\n\n{{isi}}\n\n📐 {{rumus}}\n\n💡 {{contoh}}\n\n{{cta}}\n\n{{tags}}",
            f"{{hook}}\n\n{{emoji}} {{label}}\n\n{{isi}}\n\n📐 Rumus: {{rumus}}\n\n{{cta}}\n\n{{tags}}",
            f"📚 {{label}}\n\n**{{judul}}**\n\n{{isi}}\n\n{{cta}}\n\n{{tags}}",
        ]
        template = random.choice(templates)
        caption = template.format(
            hook=hook, emoji=emoji, label=label,
            judul=data["judul"], isi=data["isi_materi"],
            rumus=data.get("rumus", ""), contoh=data.get("contoh", ""),
            cta=cta, tags=tags,
        )
    else:  # fakta
        hook = random.choice(HOOK_FAKTA)
        cta = random.choice(CTA_FAKTA)
        templates = [
            f"{{hook}}\n\n{{emoji}} {{label}}\n\n**{{judul}}**\n\n{{isi}}\n\n{{cta}}\n\n{{tags}}",
            f"{{hook}}\n\n{{isi}}\n\n{{emoji}} {{label}}\n\n{{cta}}\n\n{{tags}}",
            f"✨ {{label}}\n\n**{{judul}}**\n\n{{isi}}\n\n{{cta}}\n\n{{tags}}",
        ]
        template = random.choice(templates)
        caption = template.format(
            hook=hook, emoji=emoji, label=label,
            judul=data["judul"], isi=data["isi_fakta"],
            cta=cta, tags=tags,
        )

    return caption


MODE_FILE = "data/mode.json"


def check_telegram_mode():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return "telegram"

    current_mode = "telegram"
    last_id = 0
    if os.path.exists(MODE_FILE):
        with open(MODE_FILE) as f:
            d = json.load(f)
            current_mode = d.get("mode", "telegram")
            last_id = d.get("last_update_id", 0)

    try:
        resp = requests.get(
            f"https://api.telegram.org/bot{token}/getUpdates",
            params={"offset": last_id + 1, "timeout": 5},
        )
        if resp.ok:
            for upd in resp.json().get("result", []):
                uid = upd["update_id"]
                if uid > last_id:
                    last_id = uid
                    text = (upd.get("message") or {}).get("text", "").strip().lower()
                    if text == "/mode facebook":
                        current_mode = "telegram"
                        requests.post(
                            f"https://api.telegram.org/bot{token}/sendMessage",
                            json={"chat_id": chat_id, "text": "✅ Mode berubah ke FACEBOOK"},
                            timeout=10,
                        )
                    elif text == "/mode telegram":
                        current_mode = "telegram"
                        requests.post(
                            f"https://api.telegram.org/bot{token}/sendMessage",
                            json={"chat_id": chat_id, "text": "✅ Mode berubah ke TELEGRAM"},
                            timeout=10,
                        )
    except Exception as e:
        print(f"[WARN] Telegram mode check failed: {e}")

    os.makedirs("data", exist_ok=True)
    with open(MODE_FILE, "w") as f:
        json.dump({"mode": current_mode, "last_update_id": last_id}, f)
    return current_mode


def load_and_apply_learning_config():
    if not os.path.exists(LEARNING_CONFIG_FILE):
        return
    try:
        with open(LEARNING_CONFIG_FILE) as f:
            cfg = json.load(f)
    except Exception as e:
        print(f"[WARN] Failed to load learning config: {e}")
        return

    global HOOK_TEMPLATES, CTA_POOL, HASHTAG_POOL
    changed = []
    if "hook_templates" in cfg and cfg["hook_templates"]:
        HOOK_TEMPLATES = cfg["hook_templates"]
        changed.append("hooks")
    if "cta_pool" in cfg and cfg["cta_pool"]:
        CTA_POOL = cfg["cta_pool"]
        changed.append("CTA")
    if "hashtag_pool" in cfg and cfg["hashtag_pool"]:
        HASHTAG_POOL = cfg["hashtag_pool"]
        changed.append("hashtags")
    if changed:
        print(f"[SL] Applied learning config: {', '.join(changed)}")


def process_telegram_csv():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return

    last_id = 0
    if os.path.exists(MODE_FILE):
        with open(MODE_FILE) as f:
            last_id = json.load(f).get("last_update_id", 0)

    try:
        resp = requests.get(
            f"https://api.telegram.org/bot{token}/getUpdates",
            params={"offset": last_id + 1, "timeout": 5},
        )
        if not resp.ok:
            return

        for upd in resp.json().get("result", []):
            uid = upd["update_id"]
            if uid <= last_id:
                continue
            msg = upd.get("message") or {}
            doc = msg.get("document")
            if doc and doc.get("file_name", "").lower().endswith(".csv"):
                print(f"[SL] CSV detected: {doc['file_name']}")
                tmp_path = f"/tmp/sl_csv_{doc['file_id']}.csv"
                if _download_telegram_file(doc["file_id"], tmp_path, token):
                    try:
                        from self_learning import run_self_learning
                        result = run_self_learning(tmp_path)
                        notify_telegram(_format_sl_summary(result))
                    except Exception as e:
                        notify_telegram(f"[SL] Self-learning FAILED: {e}")
                    finally:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
    except Exception as e:
        print(f"[WARN] process_telegram_csv failed: {e}")


def _download_telegram_file(file_id, dest_path, token):
    resp = requests.get(
        f"https://api.telegram.org/bot{token}/getFile?file_id={file_id}", timeout=15
    )
    if not resp.ok:
        return False
    file_path = resp.json()["result"]["file_path"]
    dl = requests.get(
        f"https://api.telegram.org/file/bot{token}/{file_path}", timeout=30
    )
    if not dl.ok:
        return False
    with open(dest_path, "wb") as f:
        f.write(dl.content)
    print(f"[SL] CSV downloaded ({len(dl.content)} bytes)")
    return True


def _format_sl_summary(result: dict) -> str:
    if result.get("status") == "skipped":
        return f"[SL] Self-learning skipped: {result.get('reason', 'unknown')}"
    lines = ["[SL] Self-learning selesai!"]
    lines.append(f"Records diproses: {result.get('records_parsed', 0)}")
    cls = result.get("classifications", {})
    if cls:
        lines.append(f"Viral: {cls.get('viral', 0)} | Good: {cls.get('good', 0)} | Bad: {cls.get('bad', 0)}")
    changes = result.get("changes_made", [])
    if changes:
        lines.append(f"Perubahan: {', '.join(changes)}")
    return "\n".join(lines)


def post_to_telegram(image_path, caption):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID required")
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    with open(image_path, "rb") as f:
        files = {"photo": f}
        data = {"chat_id": chat_id, "caption": caption[:1024]}
        resp = requests.post(url, files=files, data=data, timeout=60)
    if not resp.ok:
        raise RuntimeError(f"Telegram sendPhoto failed: {resp.status_code} {resp.text}")
    msg_id = resp.json()["result"]["message_id"]
    print(f"[OK] Sent to Telegram. Message ID: {msg_id}")


def make_history_item(data: dict, topic: str, content_type: str) -> dict:
    item = {
        "tipe": content_type,
        "topik": topic,
        "tanggal": date.today().isoformat(),
    }
    if content_type == "soal":
        item["soal"] = data["soal"]
        item["jawaban"] = data["jawaban"]
    elif content_type == "materi":
        item["judul"] = data["judul"]
        item["isi_materi"] = data["isi_materi"][:80]
    else:
        item["judul"] = data["judul"]
        item["isi_fakta"] = data["isi_fakta"][:80]
    return item


def main():
    print("Memulai generate konten...")

    load_and_apply_learning_config()
    process_telegram_csv()

    history = load_history()
    print(f"Histori: {len(history)} item")

    topic = pick_topic(history)
    print(f"Topik terpilih: {topic} ({TOPIC_LABELS.get(topic, topic)})")

    content_type = pick_content_type()
    print(f"Tipe konten: {content_type.upper()}")

    data = generate_content(topic, content_type, history)
    if not data:
        raise RuntimeError("Gagal generate konten setelah beberapa percobaan")

    if content_type == "soal":
        print(f"Soal: {data['soal'][:60]}...")
    elif content_type == "materi":
        print(f"Materi: {data['judul']}")
    else:
        print(f"Fakta: {data['judul']}")

    gambar = buat_gambar_konten(data, topic, content_type)
    print(f"Gambar: {gambar}")

    caption = format_caption(data, topic)
    compliance_check(caption)
    post_mode = check_telegram_mode()
    print(f"[INFO] Post mode: {post_mode.upper()}")
    if post_mode == "telegram":
        post_to_telegram(gambar, caption)
    else:
        result = post_to_facebook(gambar, caption)
        print(f"Posting berhasil! Post ID: {result.get('id', 'unknown')}")

    history_item = make_history_item(data, topic, content_type)
    history.append(history_item)
    save_history(history)

    print("Selesai. Histori diperbarui.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error_msg = f"[Auto Post Soal] Job GAGAL pada {datetime.now()}:\n{e}"
        print(error_msg)
        notify_telegram(error_msg)
        raise
