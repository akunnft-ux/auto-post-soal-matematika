import os
import json
import random
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

COLOR_TOSCA = (13, 148, 136)
COLOR_TOSCA_LIGHT = (204, 251, 241)
COLOR_TOSCA_DARK = (15, 118, 110)
COLOR_BG = (240, 253, 250)
COLOR_TEXT = (15, 23, 42)
COLOR_TEXT_SECONDARY = (71, 85, 105)
COLOR_FOOTER = (148, 163, 184)
COLOR_WHITE = (255, 255, 255)

TOPICS = [
    "deret_angka",
    "aritmatika_aljabar",
    "peluang_statistika",
    "geometri",
    "fungsi_grafik",
]

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

TOPIC_PROMPTS = {
    "deret_angka": (
        "soal Deret Angka atau Pola Bilangan (barisan & deret). "
        "Contoh: deret Fibonacci, deret aritmatika, deret geometri, pola kuadrat, pola segitiga, dll."
    ),
    "aritmatika_aljabar": (
        "soal Aritmatika atau Aljabar. "
        "Contoh: perbandingan, kecepatan/jarak/waktu, persamaan linier, sistem persamaan, "
        "persamaan kuadrat, perbandingan senilai/berbalik nilai, bunga, diskon, skala, dll."
    ),
    "peluang_statistika": (
        "soal Peluang atau Statistika. "
        "Contoh: peluang kejadian, kombinasi, permutasi, mean/median/modus, "
        "rata-rata gabungan, diagram, frekuensi, dll."
    ),
    "geometri": (
        "soal Geometri. "
        "Contoh: luas & keliling bangun datar, volume bangun ruang, "
        "kesebangunan, teorema Pythagoras, sudut, garis singgung, dll."
    ),
    "fungsi_grafik": (
        "soal Fungsi atau Grafik. "
        "Contoh: fungsi linier, fungsi kuadrat, gradien, persamaan garis, "
        "domain/range, komposisi fungsi, invers fungsi, dll."
    ),
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
    for item in history:
        existing = item if isinstance(item, str) else item.get("soal", "")
        if existing == soal_text:
            return True
    return False


def pick_topic(history: list) -> str:
    used_today = get_used_topics_today(history)
    available = [t for t in TOPICS if t not in used_today]
    if not available:
        available = TOPICS
    return random.choice(available)


def generate_soal(topic, history, max_retry=3):
    history_text = "\n".join(
        f"- {(h['soal'] if isinstance(h, dict) else h)[:80]}"
        for h in history[-20:]
    ) or "(belum ada histori)"

    prompt = f"""
    Buat 1 {TOPIC_PROMPTS[topic]}
    Level: sedang hingga sulit (CPNS / TKA / SNBT).

    JANGAN membuat soal yang mirip dengan daftar berikut (histori):
    {history_text}

    Jawab HANYA dengan JSON valid, tanpa markdown, tanpa penjelasan tambahan.
    Format:
    {{
      "soal": "teks soal lengkap",
      "pilihan": ["pilihan A", "pilihan B", "pilihan C", "pilihan D"],
      "jawaban": "pilihan yang benar (sama persis dengan teks pilihan)",
      "penjelasan": "penjelasan cara menyelesaikan soal"
    }}
    """

    for attempt in range(1, max_retry + 1):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                ),
            )
            soal = json.loads(response.text.strip())

            required_keys = {"soal", "pilihan", "jawaban", "penjelasan"}
            if not required_keys.issubset(soal.keys()):
                raise ValueError("Field JSON tidak lengkap")
            if not isinstance(soal["pilihan"], list) or len(soal["pilihan"]) != 4:
                raise ValueError("Pilihan harus array 4 item")
            if soal["jawaban"] not in soal["pilihan"]:
                raise ValueError("Jawaban tidak ada di pilihan")
            if is_soal_duplicate(soal["soal"], history):
                raise ValueError("Soal duplikat dengan histori")

            return soal
        except Exception as e:
            print(f"[Percobaan {attempt}/{max_retry}] Gagal: {e}")

    return None


def wrap_text(text, font, draw, max_width):
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


def buat_gambar_soal(soal_data, topic, filename="soal/soal_hari_ini.png"):
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    img = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (IMG_WIDTH, IMG_HEIGHT)], fill=COLOR_BG)

    font_heading = ImageFont.truetype(FONT_BOLD, 42)
    font_subtitle = ImageFont.truetype(FONT_REGULAR, 26)
    font_badge = ImageFont.truetype(FONT_BOLD, 22)
    font_soal = ImageFont.truetype(FONT_REGULAR, 32)
    font_pilihan = ImageFont.truetype(FONT_REGULAR, 30)
    font_footer = ImageFont.truetype(FONT_REGULAR, 22)

    margin = 60
    usable_width = IMG_WIDTH - 2 * margin

    draw.rectangle([(0, 0), (IMG_WIDTH, 150)], fill=COLOR_TOSCA)
    draw.rectangle([(0, 150), (IMG_WIDTH, 155)], fill=COLOR_TOSCA_DARK)

    draw.text((IMG_WIDTH / 2, 58), "SOAL MATEMATIKA", fill=COLOR_WHITE, anchor="mm", font=font_heading)
    draw.text((IMG_WIDTH / 2, 110), "CPNS  •  TKA  •  SNBT", fill=COLOR_TOSCA_LIGHT, anchor="mm", font=font_subtitle)

    badge_label = TOPIC_LABELS.get(topic, topic)
    badge_w = draw.textlength(badge_label, font=font_badge) + 40
    badge_x = (IMG_WIDTH - badge_w) / 2
    draw_rounded_rect(draw, [badge_x, 190, badge_x + badge_w, 230], radius=20, fill=COLOR_TOSCA)
    draw.text((IMG_WIDTH / 2, 210), badge_label, fill=COLOR_WHITE, anchor="mm", font=font_badge)

    y = 270

    soal_lines = wrap_text(soal_data["soal"], font_soal, draw, usable_width)
    for line in soal_lines:
        draw.text((margin, y), line, fill=COLOR_TEXT, font=font_soal)
        y += 50

    y += 40

    for i, p in enumerate(soal_data["pilihan"]):
        letter = chr(65 + i)
        option_text = f"{letter}.  {p}"

        option_lines = wrap_text(option_text, font_pilihan, draw, usable_width - 50)

        bg_y = y - 8
        text_block_h = len(option_lines) * 44 + 16
        draw_rounded_rect(draw, [margin, bg_y, IMG_WIDTH - margin, bg_y + text_block_h], radius=12, fill=COLOR_WHITE)

        draw.rounded_rectangle(
            [margin, bg_y, margin + 6, bg_y + text_block_h],
            radius=3, fill=COLOR_TOSCA
        )

        for line in option_lines:
            draw.text((margin + 25, y), line, fill=COLOR_TEXT, font=font_pilihan)
            y += 44

        y += 16

    footer_y = IMG_HEIGHT - 90
    draw.rectangle([(0, footer_y - 10), (IMG_WIDTH, IMG_HEIGHT)], fill=COLOR_WHITE)
    draw.line([(margin, footer_y), (IMG_WIDTH - margin, footer_y)], fill=COLOR_TOSCA_LIGHT, width=2)
    footer = random.choice(FOOTER_POOL)
    if footer:
        draw.text(
            (IMG_WIDTH / 2, footer_y + 30),
            footer,
            fill=COLOR_FOOTER, anchor="mm", font=font_footer
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
    disallowed = [
        "comment", "tag", "share this", "subscri", "follow",
        "like", "komentar",
    ]
    caption_lower = caption.lower()
    for pattern in disallowed:
        if pattern in caption_lower:
            raise ValueError(f"Compliance: engagement bait pattern '{pattern}' detected in caption")
    return True


def format_caption(soal_data: dict, topic: str) -> str:
    label = TOPIC_LABELS.get(topic, topic)
    emoji = random.choice(EMOJI_POOL)
    tags = " ".join(random.sample(HASHTAG_POOL, k=random.randint(2, 3)))
    op = "\n".join(f"{chr(65 + i)}. {p}" for i, p in enumerate(soal_data["pilihan"]))

    templates = [
        f"{{emoji}} {{label}}\n\n{{soal}}\n\n{{pilihan}}\n\n{{tags}}",
        f"{{label}}\n\n{{soal}}\n\n{{emoji}} {{pilihan}}\n\n{{tags}}",
        f"{{emoji}} Latihan {{label}}\n\n{{soal}}\n\n{{pilihan}}\n\n{{tags}}",
        f"{{soal}}\n\n{{pilihan}}\n\n{{tags}}",
        f"{{emoji}} {{label}}\n\n{{soal}}\n\n{{emoji}} {{pilihan}}\n\n{{tags}}",
        f"Soal {{label}}:\n\n{{soal}}\n\n{{emoji}} {{pilihan}}\n\n{{tags}}",
    ]
    template = random.choice(templates)
    caption = template.format(
        emoji=emoji, label=label,
        soal=soal_data["soal"], pilihan=op, tags=tags,
    )
    return caption


def main():
    print("Memulai generate soal...")

    history = load_history()
    print(f"Histori: {len(history)} item")

    topic = pick_topic(history)
    print(f"Topik terpilih: {topic} ({TOPIC_LABELS.get(topic, topic)})")

    soal = generate_soal(topic, history)
    if not soal:
        raise RuntimeError("Gagal generate soal setelah beberapa percobaan")

    print(f"Soal: {soal['soal'][:60]}...")

    gambar = buat_gambar_soal(soal, topic)
    print(f"Gambar: {gambar}")

    caption = format_caption(soal, topic)
    compliance_check(caption)
    result = post_to_facebook(gambar, caption)
    print(f"Posting berhasil! Post ID: {result.get('id', 'unknown')}")

    history_item = {
        "soal": soal["soal"],
        "jawaban": soal["jawaban"],
        "topik": topic,
        "tanggal": date.today().isoformat(),
    }
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
