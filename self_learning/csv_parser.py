import csv
import io
import json
import os
import re
from datetime import datetime

try:
    from google import genai
except ImportError:
    genai = None


def parse_csv(csv_path: str) -> list:
    if not os.path.exists(csv_path):
        return []

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        raw = f.read()

    if not raw.strip():
        return []

    records = _parse_csv_direct(raw)
    if records:
        return records

    records = _parse_csv_via_gemini(raw)
    return records


def _parse_csv_direct(raw: str) -> list:
    reader = csv.DictReader(io.StringIO(raw))
    if not reader.fieldnames:
        return []

    original_headers = [h.strip() for h in reader.fieldnames]
    lowered_headers = [h.lower() for h in original_headers]
    col_map = _map_columns(lowered_headers, original_headers)
    if not col_map:
        return []

    records = []
    for row in reader:
        record = _extract_record(row, col_map)
        if record:
            records.append(record)
    return records


def _map_columns(lowered: list, original: list) -> dict:
    mapping = {}
    for i, hl in enumerate(lowered):
        if any(t in hl for t in ["post id", "post_id", "id posting"]):
            mapping["post_id"] = original[i]
        elif any(t in hl for t in ["post date", "post_date", "date", "tanggal"]):
            mapping["post_date"] = original[i]
        elif any(t in hl for t in ["impressions", "views", "reach", "tayangan"]):
            if "organic" not in hl and "paid" not in hl:
                mapping["views"] = original[i]
        elif any(t in hl for t in ["likes", "reactions", "suka"]):
            mapping["likes"] = original[i]
        elif any(t in hl for t in ["comments", "komentar", "comment"]):
            mapping["comments"] = original[i]
        elif any(t in hl for t in ["shares", "bagikan", "share"]):
            mapping["shares"] = original[i]

    if "views" in mapping and ("likes" in mapping or "comments" in mapping or "shares" in mapping):
        return mapping
    return {}


def _extract_record(row: dict, col_map: dict) -> dict:
    try:
        post_id = str(row.get(col_map.get("post_id", ""), "")).strip()
        views = _parse_int(row.get(col_map.get("views", "")))
        likes = _parse_int(row.get(col_map.get("likes", "")))
        comments = _parse_int(row.get(col_map.get("comments", "")))
        shares = _parse_int(row.get(col_map.get("shares", "")))

        if not post_id or views is None:
            return None

        engagement = (likes or 0) + (comments or 0) + (shares or 0)
        engagement_rate = round(engagement / views, 4) if views and views > 0 else 0.0

        return {
            "post_id": post_id,
            "platform": "facebook",
            "views": views or 0,
            "likes": likes or 0,
            "comments": comments or 0,
            "shares": shares or 0,
            "engagement_rate": engagement_rate,
            "source": "manual",
            "fetched_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    except Exception:
        return None


def _parse_csv_via_gemini(raw: str) -> list:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or genai is None:
        return []

    client = genai.Client(api_key=api_key)
    model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

    prompt = (
        "Parse CSV Facebook Insights. "
        "Ekstrak: post_id, post_date, views, likes, comments, shares. "
        "Kembalikan JSON array: [{\"post_id\":\"...\",\"views\":100,\"likes\":5,\"comments\":1,\"shares\":0}]\n\n"
        f"CSV:\n{raw[:50000]}"
    )

    try:
        response = client.models.generate_content(model=model, contents=prompt)
        text = response.text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        parsed = json.loads(text)
        if isinstance(parsed, list):
            now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            for r in parsed:
                r["platform"] = "facebook"
                r["engagement_rate"] = 0.0
                r["source"] = "manual"
                r["fetched_at"] = now
                views = r.get("views", 0) or 0
                eng = (r.get("likes", 0) or 0) + (r.get("comments", 0) or 0) + (r.get("shares", 0) or 0)
                r["engagement_rate"] = round(eng / views, 4) if views > 0 else 0.0
            return parsed
    except Exception:
        pass

    return []


def _parse_int(val) -> int:
    if val is None:
        return 0
    try:
        cleaned = re.sub(r"[^\d\-]", "", str(val))
        return int(cleaned) if cleaned else 0
    except (ValueError, TypeError):
        return 0


import json
