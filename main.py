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
                model="gemini-3.1-flash-lite",
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

    img = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), COLOR_BG)
    draw = ImageDraw.Draw(img)

    font_heading = ImageFont.truetype(FONT_BOLD, 48)
    font_subtitle = ImageFont.truetype(FONT_REGULAR, 26)
    font_badge = ImageFont.truetype(FONT_BOLD, 24)
    font_soal = ImageFont.truetype(FONT_REGULAR, 34)
    font_pilihan = ImageFont.truetype(FONT_REGULAR, 30)
    font_footer = ImageFont.truetype(FONT_REGULAR, 22)
    font_icon = ImageFont.truetype(FONT_BOLD, 28)

    margin = 60
    usable_width = IMG_WIDTH - 2 * margin
    header_h = 160

    topic_accent, topic_bg = TOPIC_COLORS.get(topic, (COLOR_NAVY, (220, 220, 220)))

    # ── Header ──
    draw.rounded_rectangle([(0, 0), (IMG_WIDTH, header_h)], radius=0, fill=COLOR_NAVY)
    draw.rounded_rectangle([(0, header_h - 8), (IMG_WIDTH, header_h + 4)], radius=0, fill=COLOR_ORANGE)

    draw.text((IMG_WIDTH / 2, 55), "SOAL MATEMATIKA", fill=COLOR_WHITE, anchor="mm", font=font_heading)
    draw.text((IMG_WIDTH / 2, 115), "CPNS  •  TKA  •  SNBT", fill=(255, 200, 150), anchor="mm", font=font_subtitle)

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

    # ── Soal text ──
    y = badge_y + 80

    soal_lines = wrap_text(soal_data["soal"], font_soal, draw, usable_width)
    for line in soal_lines:
        draw.text((margin, y), line, fill=COLOR_TEXT, font=font_soal)
        y += 52

    y += 30

    # ── Pilihan ──
    for i, p in enumerate(soal_data["pilihan"]):
        letter = chr(65 + i)
        option_text = f"{letter}.  {p}"

        option_lines = wrap_text(option_text, font_pilihan, draw, usable_width - 50)

        bg_y = y - 8
        text_block_h = len(option_lines) * 44 + 18
        draw_rounded_rect(draw, [margin, bg_y, IMG_WIDTH - margin, bg_y + text_block_h], radius=14, fill=COLOR_WHITE)
        draw.rounded_rectangle(
            [margin + 2, bg_y + 2, IMG_WIDTH - margin - 2, bg_y + text_block_h - 2],
            radius=12, fill=None, outline=topic_bg, width=2
        )
        draw.rounded_rectangle(
            [margin, bg_y, margin + 8, bg_y + text_block_h],
            radius=4, fill=topic_accent
        )

        for line in option_lines:
            draw.text((margin + 30, y), line, fill=COLOR_TEXT, font=font_pilihan)
            y += 44

        y += 14

    # ── Footer ──
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
    post_mode = check_telegram_mode()
    print(f"[INFO] Post mode: {post_mode.upper()}")
    if post_mode == "telegram":
        post_to_telegram(gambar, caption)
    else:
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
