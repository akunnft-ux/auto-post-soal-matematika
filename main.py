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
FONT_FREDOKA = "fonts/Fredoka-Variable.ttf"
FONT_KALAM = "fonts/Kalam-Regular.ttf"
FONT_EMOJI = "fonts/Symbola.ttf"
MAX_HISTORY_ITEMS = 180
IMG_WIDTH = 1080
IMG_HEIGHT = 1080

# ── Account strategy (per rekomendasi pemisahan format/tema) ──
ACCOUNT_TYPE = "personal"
CONTENT_FORMAT = "gambar"
PERSONAL_MAJOR_CT_WEIGHTS = {"soal": 1, "materi": 4, "fakta": 5}  # 80% light content
PERSONAL_MINOR_CT_WEIGHTS = {"soal": 8, "materi": 1, "fakta": 1}  # 20% quiz
STAGGER_FILE = "data/last_stagger.json"
STAGGER_MIN_HOURS = 3

COLOR_BG = (255, 248, 236)        # #FFF8EC cream
COLOR_INK = (43, 39, 48)          # #2B2730
COLOR_SUN = (255, 201, 74)        # #FFC94A
COLOR_CORAL = (255, 107, 87)      # #FF6B57
COLOR_HEADER_BG = (108, 79, 224)  # #6C4FE0 grape
COLOR_WHITE = (255, 255, 255)
COLOR_PAPER = (255, 255, 255)
COLOR_BORDER = (216, 207, 186)    # #d8cfba

CATEGORIES_FILE = "data/categories.json"

TOPICS = [
    "deret_angka",
    "aritmatika_aljabar",
    "peluang_statistika",
    "geometri",
    "fungsi_grafik",
    "teori_bilangan",
    "kombinatorika",
]

CONTENT_TYPES = ["soal", "materi", "fakta"]

CONTENT_TYPE_WEIGHTS = [3, 3, 2]  # soal : materi : fakta

TOPIC_LABELS = {
    "deret_angka": "Deret Angka & Pola Bilangan",
    "aritmatika_aljabar": "Aritmatika & Aljabar",
    "peluang_statistika": "Peluang & Statistika",
    "geometri": "Geometri",
    "fungsi_grafik": "Fungsi & Grafik",
    "teori_bilangan": "Teori Bilangan",
    "kombinatorika": "Kombinatorika",
}

HASHTAG_POOL = [
    "#SoalMatematika", "#CPNS2026", "#BelajarMatematika",
    "#MatematikaDasar", "#CPNS", "#TIUCPNS", "#SKDCPNS",
    "#TryoutCPNS", "#RuangBelajar", "#Matematika",
    "#LatihanCPNS", "#StudiCPNS",
]

EMOJI_POOL = ["🧮", "📐", "📝", "✏️", "📊", "➗", "➕", "❌"]

BADGE_MAP = {
    "soal": "\U0001f4dd Soal Kilat",
    "materi": "\U0001f4a1 Math Trik Harian",
    "fakta": "\U0001f92f Fun Fact",
}

TRICK_FLAG_MAP = {
    "soal": "\U0001f9e0 Trik Cepat",
    "materi": "\U0001f4d0 Rumus",
    "fakta": "\U0001f4a1 Triknya",
}

CTA_TAGLINES = [
    "Coba sendiri, ya! \U0001f440",
    "Kamu pasti bisa! \U0001f4aa",
    "Yuk, latihan lagi! \U0001f525",
    "Share ke temanmu! \U0001f4e4",
    "Follow buat belajar tiap hari! \U0001f514",
]

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
    "teori_bilangan": {
        "soal": "soal Teori Bilangan. "
                "Contoh: bilangan prima, faktorisasi prima, KPK/FPB, modulo, "
                "sisa pembagian, bilangan bulat, sistem bilangan, dll.",
        "materi": "MATERI tentang Teori Bilangan. "
                  "Jelaskan konsep seperti bilangan prima, faktorisasi, KPK/FPB, atau modulo. "
                  "Sertakan rumus utama, sifat-sifat bilangan, dan contoh.",
        "fakta": "FAKTA menarik tentang Teori Bilangan. "
                 "Misal: keunikan bilangan prima, teorema Fermat, bilangan sempurna, dll. "
                 "Beri fakta yang mengejutkan dan edukatif.",
    },
    "kombinatorika": {
        "soal": "soal Kombinatorika. "
                "Contoh: aturan perkalian/penjumlahan, permutasi, kombinasi, "
                "prinsip inklusi-eksklusi, pigeonhole principle, dll.",
        "materi": "MATERI tentang Kombinatorika. "
                  "Jelaskan konsep seperti permutasi, kombinasi, atau prinsip pencacahan. "
                  "Sertakan rumus utama dan contoh penerapan.",
        "fakta": "FAKTA menarik tentang Kombinatorika. "
                 "Misal: angka ajaib 7, permutasi dalam kehidupan, teka-teki kombinatorika terkenal, dll. "
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


def load_categories():
    if not os.path.exists(CATEGORIES_FILE):
        print("[WARN] categories.json not found, using legacy mode")
        return None
    try:
        with open(CATEGORIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] Failed to load categories: {e}")
        return None


def get_category_keys(categories):
    return list(categories.keys()) if categories else []


def get_category_weights(categories):
    return [categories[k]["weight"] for k in categories] if categories else []


def pick_category(categories, history):
    if not categories:
        return None
    keys = get_category_keys(categories)
    weights = get_category_weights(categories)
    used_today = set()
    today_str = date.today().isoformat()
    for item in history:
        if isinstance(item, dict) and item.get("tanggal") == today_str:
            used_today.add(item.get("kategori"))
    available = [(k, w) for k, w in zip(keys, weights) if k not in used_today]
    if not available:
        available = list(zip(keys, weights))
    chosen = random.choices([k for k, w in available], weights=[w for k, w in available], k=1)[0]
    return chosen


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


def get_used_combos_today(history):
    today_str = date.today().isoformat()
    used = set()
    for item in history:
        if isinstance(item, dict) and item.get("tanggal") == today_str:
            used.add((item.get("kategori"), item.get("topik")))
    return used


def is_soal_duplicate(soal_text, history, kategori=None):
    soal_lower = soal_text.lower()
    for item in history:
        if kategori and item.get("kategori") != kategori:
            continue
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


def pick_topic(history, kategori=None, categories=None):
    used_today = get_used_combos_today(history)
    if categories and kategori:
        cat_config = categories.get(kategori, {})
        valid_topics = cat_config.get("valid_topics", TOPICS)
    else:
        valid_topics = TOPICS
    available = [t for t in valid_topics if (kategori, t) not in used_today]
    if not available:
        available = valid_topics
    return random.choice(available)


def pick_content_type() -> str:
    return random.choices(CONTENT_TYPES, weights=CONTENT_TYPE_WEIGHTS, k=1)[0]


def generate_content(topic, content_type, history, kategori=None, categories=None, max_retry=3):
    history_text = "\n".join(
        f"- {(h.get('soal') or h.get('judul') or str(h))[:120]}"
        for h in history[-50:]
    ) or "(belum ada histori)"

    if categories and kategori:
        cat = categories.get(kategori, {})
        audience = cat.get("audience", "")
        level = cat.get("level", "sedang hingga sulit")
        category_context = f"Target: {audience}\nLevel kesulitan: {level}"
    else:
        category_context = "Level: sedang hingga sulit (CPNS / TKA / SNBT)"

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
    {category_context}

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
    {category_context}

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
    {category_context}

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
                if is_soal_duplicate(data["soal"], history, kategori):
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


def _draw_header(draw, content_type, title, margin, usable_width):
    """Draw grape header with badge pill and centered title."""
    header_h = 210
    draw.rounded_rectangle([(0, 0), (IMG_WIDTH, header_h)], radius=0, fill=COLOR_HEADER_BG)

    font_badge = ImageFont.truetype(FONT_EMOJI, 26)
    font_title = ImageFont.truetype(FONT_FREDOKA, 50)

    badge_text = BADGE_MAP.get(content_type, "\U0001f4dd Soal Kilat")
    badge_w = draw.textlength(badge_text, font=font_badge) + 36
    badge_h = 36
    badge_x = (IMG_WIDTH - badge_w) / 2
    badge_y = 44
    draw_rounded_rect(draw, [badge_x, badge_y, badge_x + badge_w, badge_y + badge_h], radius=18, fill=COLOR_SUN)
    draw.text((IMG_WIDTH / 2, badge_y + badge_h / 2), badge_text, fill=COLOR_INK, anchor="mm", font=font_badge)

    title_y = badge_y + badge_h + 24
    title_lines = wrap_text(title, font_title, draw, usable_width)
    if len(title_lines) == 1:
        draw.text((IMG_WIDTH / 2, title_y + 5), title_lines[0], fill=COLOR_WHITE, anchor="mm", font=font_title)
    else:
        for line in title_lines:
            draw.text((IMG_WIDTH / 2, title_y), line, fill=COLOR_WHITE, anchor="mt", font=font_title)
            title_y += 56

    return header_h


def _draw_trick_box(draw, x, y, w, flag_text, elements):
    """Draw trick-box with flag pill and content.
    elements: list of (text, font, color) tuples
    Returns y position after the box.
    """
    pad = 24
    line_h = 36

    total_h = 0
    for text, font, _ in elements:
        lines = wrap_text(text, font, draw, w - 2 * pad)
        total_h += len(lines) * line_h + 4

    box_h = total_h + 2 * pad + 16

    # Shadow
    draw_rounded_rect(draw, [x + 8, y + 8, x + w + 8, y + box_h + 8], radius=14, fill=COLOR_SUN)
    # Main box
    draw.rounded_rectangle([x, y, x + w, y + box_h], radius=14, fill=COLOR_PAPER, outline=COLOR_INK, width=3)

    # Flag pill
    font_flag = ImageFont.truetype(FONT_EMOJI, 24)
    flag_w = draw.textlength(flag_text, font=font_flag) + 36
    flag_h = 34
    flag_x = x + 24
    flag_y = y - 17
    draw_rounded_rect(draw, [flag_x, flag_y, flag_x + flag_w, flag_y + flag_h], radius=17, fill=COLOR_CORAL)
    draw.text((flag_x + flag_w / 2, flag_y + flag_h / 2), flag_text, fill=COLOR_WHITE, anchor="mm", font=font_flag)

    # Content
    cy = y + 22
    for text, font, color in elements:
        lines = wrap_text(text, font, draw, w - 2 * pad)
        for line in lines:
            draw.text((x + pad, cy), line, fill=color, font=font)
            cy += line_h
        cy += 4

    return y + box_h + 16


def _draw_footer(draw, y):
    """Draw footer with dashed line, tagline and CTA pill."""
    margin = 64
    font_tagline = ImageFont.truetype(FONT_EMOJI, 28)
    font_cta = ImageFont.truetype(FONT_EMOJI, 24)

    # Dashed line
    dash_len = 16
    gap_len = 8
    dx = margin
    while dx < IMG_WIDTH - margin:
        draw.line([(dx, y), (min(dx + dash_len, IMG_WIDTH - margin), y)], fill=COLOR_BORDER, width=3)
        dx += dash_len + gap_len

    # Tagline (left)
    tagline = random.choice(CTA_TAGLINES)
    draw.text((margin, y + 24), tagline, fill=COLOR_INK, font=font_tagline)

    # CTA pill (right)
    cta_text = "Follow \u2192"
    cta_w = draw.textlength(cta_text, font=font_cta) + 44
    cta_h = 40
    cta_x = IMG_WIDTH - margin - cta_w
    cta_y = y + 14
    draw_rounded_rect(draw, [cta_x, cta_y, cta_x + cta_w, cta_y + cta_h], radius=20, fill=COLOR_CORAL)
    draw.text((cta_x + cta_w / 2, cta_y + cta_h / 2), cta_text, fill=COLOR_WHITE, anchor="mm", font=font_cta)

    return y + 80


def _render_body_soal(draw, data, margin, usable_width, y_start):
    """Render body for soal type: question + options + trick-box."""
    font_body = ImageFont.truetype(FONT_REGULAR, 30)
    font_option = ImageFont.truetype(FONT_REGULAR, 28)
    font_jawaban = ImageFont.truetype(FONT_FREDOKA, 30)
    font_penjelasan = ImageFont.truetype(FONT_REGULAR, 26)

    y = y_start
    # Question
    soal_lines = wrap_text(data["soal"], font_body, draw, usable_width)
    for line in soal_lines:
        draw.text((margin, y), line, fill=COLOR_INK, font=font_body)
        y += 42
    y += 20

    # Options A-D
    for i, p in enumerate(data["pilihan"]):
        letter = chr(65 + i)
        opt_text = f"{letter}. {p}"
        opt_lines = wrap_text(opt_text, font_option, draw, usable_width - 40)
        opt_h = len(opt_lines) * 36 + 16
        draw_rounded_rect(draw, [margin, y, margin + usable_width, y + opt_h], radius=10, fill=COLOR_PAPER)
        draw.rounded_rectangle([margin, y, margin + usable_width, y + opt_h], radius=10, fill=None, outline=COLOR_BORDER, width=2)
        for line in opt_lines:
            draw.text((margin + 20, y + 8), line, fill=COLOR_INK, font=font_option)
            y += 36
        y += 10
    y += 10

    # Trick-box: Trik Cepat
    jawaban_text = f"Jawaban: {data['jawaban']}"
    elements = [
        (jawaban_text, font_jawaban, COLOR_HEADER_BG),
        (data["penjelasan"], font_penjelasan, COLOR_INK),
    ]
    y = _draw_trick_box(draw, margin, y, usable_width, TRICK_FLAG_MAP["soal"], elements)

    return y


def _render_body_materi(draw, data, margin, usable_width, y_start):
    """Render body for materi type: content + trick-box with rumus+contoh."""
    font_body = ImageFont.truetype(FONT_REGULAR, 32)
    font_rumus = ImageFont.truetype(FONT_FREDOKA, 30)
    font_contoh = ImageFont.truetype(FONT_REGULAR, 26)

    y = y_start
    isi_lines = wrap_text(data["isi_materi"], font_body, draw, usable_width)
    for line in isi_lines:
        draw.text((margin, y), line, fill=COLOR_INK, font=font_body)
        y += 40
    y += 20

    elements = []
    rumus = data.get("rumus", "")
    if rumus:
        elements.append((rumus, font_rumus, COLOR_HEADER_BG))
    contoh = data.get("contoh", "")
    if contoh:
        elements.append((f"Contoh: {contoh}", font_contoh, COLOR_INK))

    if elements:
        y = _draw_trick_box(draw, margin, y, usable_width, TRICK_FLAG_MAP["materi"], elements)
    else:
        y += 10

    return y


def _render_body_fakta(draw, data, margin, usable_width, y_start):
    """Render body for fakta type: content + trick-box with sumber/CTA."""
    font_body = ImageFont.truetype(FONT_REGULAR, 32)
    font_sumber = ImageFont.truetype(FONT_EMOJI, 26)

    y = y_start
    isi_lines = wrap_text(data["isi_fakta"], font_body, draw, usable_width)
    for line in isi_lines:
        draw.text((margin, y), line, fill=COLOR_INK, font=font_body)
        y += 40
    y += 20

    sumber = data.get("sumber", "")
    if sumber:
        elements = [(f"\U0001f4cc {sumber}", font_sumber, COLOR_INK)]
    else:
        elements = [("Simpan postingan ini buat referensi belajar! \U0001f4cc", font_sumber, COLOR_INK)]

    y = _draw_trick_box(draw, margin, y, usable_width, TRICK_FLAG_MAP["fakta"], elements)

    return y


def render_card(data, content_type, kategori=None, categories=None, filename="soal/konten_hari_ini.png"):
    """Main rendering function — replaces buat_gambar_konten."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    img = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), COLOR_BG)
    draw = ImageDraw.Draw(img)

    margin = 64
    usable_width = IMG_WIDTH - 2 * margin

    if content_type == "soal":
        title = data.get("judul", "Ayo Coba Soal Ini!")
    else:
        title = data.get("judul", "Materi Matematika")

    header_h = _draw_header(draw, content_type, title, margin, usable_width)

    y = header_h + 24
    if content_type == "soal":
        y = _render_body_soal(draw, data, margin, usable_width, y)
    elif content_type == "materi":
        y = _render_body_materi(draw, data, margin, usable_width, y)
    else:
        y = _render_body_fakta(draw, data, margin, usable_width, y)

    footer_y = max(y, IMG_HEIGHT - 140)
    _draw_footer(draw, footer_y)

    img.save(filename)
    return filename


# --- Legacy alias ---
buat_gambar_konten = render_card



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


# NOTE: post_to_facebook_profile() — disabled until FB_USER_TOKEN/FB_USER_ID are ready

def check_stagger():
    if not os.path.exists(STAGGER_FILE):
        return True
    try:
        with open(STAGGER_FILE) as f:
            data = json.load(f)
        last_time = datetime.fromisoformat(data.get("last_post_time", ""))
        hours_since = (datetime.now() - last_time).total_seconds() / 3600
        if hours_since < STAGGER_MIN_HOURS:
            print(f"[STAGGER] Only {hours_since:.1f}h since last post to other account — skipping (min {STAGGER_MIN_HOURS}h)")
            return False
        return True
    except (ValueError, KeyError, FileNotFoundError):
        return True


def record_stagger():
    os.makedirs("data", exist_ok=True)
    with open(STAGGER_FILE, "w") as f:
        json.dump({"last_post_time": datetime.now().isoformat()}, f)


def pick_content_type_for_account():
    roll = random.random()
    if roll < 0.8:
        weights = PERSONAL_MAJOR_CT_WEIGHTS
    else:
        weights = PERSONAL_MINOR_CT_WEIGHTS
    types = list(CONTENT_TYPES)
    w = [weights.get(t, 1) for t in types]
    return random.choices(types, weights=w, k=1)[0]


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


def format_caption(data: dict, topic: str, kategori=None, categories=None) -> str:
    label = TOPIC_LABELS.get(topic, topic)
    emoji = random.choice(EMOJI_POOL)
    content_type = data.get("tipe", "soal")

    if categories and kategori:
        cat = categories.get(kategori, {})
        hashtag_pool = cat.get("hashtag_pool", HASHTAG_POOL)
        hooks_soal = cat.get("hooks_soal", HOOK_TEMPLATES)
        hooks_materi = cat.get("hooks_materi", HOOK_MATERI)
        hooks_fakta = cat.get("hooks_fakta", HOOK_FAKTA)
        cta_soal = cat.get("cta_soal", CTA_POOL)
        cta_materi = cat.get("cta_materi", CTA_MATERI)
        cta_fakta = cat.get("cta_fakta", CTA_FAKTA)
    else:
        hashtag_pool = HASHTAG_POOL
        hooks_soal = HOOK_TEMPLATES
        hooks_materi = HOOK_MATERI
        hooks_fakta = HOOK_FAKTA
        cta_soal = CTA_POOL
        cta_materi = CTA_MATERI
        cta_fakta = CTA_FAKTA

    tags = " ".join(random.sample(hashtag_pool, k=min(random.randint(2, 3), len(hashtag_pool))))

    if content_type == "soal":
        hook = random.choice(hooks_soal)
        cta = random.choice(cta_soal)
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
        hook = random.choice(hooks_materi)
        cta = random.choice(cta_materi)
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
        hook = random.choice(hooks_fakta)
        cta = random.choice(cta_fakta)
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
    return cfg


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


def make_history_item(data: dict, topic: str, content_type: str, kategori=None) -> dict:
    item = {
        "kategori": kategori or "cpns",
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

    if not check_stagger():
        print("[STAGGER] Skip — too soon since other account post")
        return

    categories = load_categories()
    history = load_history()
    print(f"Histori: {len(history)} item")

    kategori = pick_category(categories, history)
    if kategori and categories:
        cat_label = categories[kategori]["label"]
        print(f"Kategori: {kategori} ({cat_label})")
    else:
        print("Kategori: (legacy mode)")

    topic = pick_topic(history, kategori, categories)
    print(f"Topik terpilih: {topic} ({TOPIC_LABELS.get(topic, topic)})")

    content_type = pick_content_type_for_account()
    print(f"Tipe konten: {content_type.upper()}")

    data = generate_content(topic, content_type, history, kategori, categories)
    if not data:
        raise RuntimeError("Gagal generate konten setelah beberapa percobaan")

    if content_type == "soal":
        print(f"Soal: {data['soal'][:60]}...")
    elif content_type == "materi":
        print(f"Materi: {data['judul']}")
    else:
        print(f"Fakta: {data['judul']}")

    gambar = buat_gambar_konten(data, topic, content_type, kategori, categories)
    print(f"Gambar: {gambar}")

    caption = format_caption(data, topic, kategori, categories)
    compliance_check(caption)
    post_mode = check_telegram_mode()
    print(f"[INFO] Post mode: {post_mode.upper()}")
    if post_mode == "telegram":
        post_to_telegram(gambar, caption)
    else:
        result = post_to_facebook(gambar, caption)
        print(f"Posting berhasil! Post ID: {result.get('id', 'unknown')}")

    history_item = make_history_item(data, topic, content_type, kategori)
    history_item["account_type"] = ACCOUNT_TYPE
    history_item["format"] = CONTENT_FORMAT
    history_item["theme"] = kategori or "cpns"
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
