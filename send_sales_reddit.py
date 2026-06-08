import html
import math
import os
import re
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageFont


WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK", "")

REDDIT_USER = "MuffinSundae"
SENT_POST_FILE = ".last_reddit_sale.txt"
LATEST_POST_URL = None
LATEST_POST_TEXT = None

HEADERS = {
    "User-Agent": "GPBot weekly sales by Marcos"
}


def normalize(text):
    return (
        text.lower()
        .replace("&", "and")
        .replace("'", "")
        .replace(".", "")
        .replace("-", " ")
        .replace(":", "")
        .strip()
    )


def font(size, bold=False):
    possible_paths = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]

    for path in possible_paths:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass

    return ImageFont.load_default()


def cover_resize(img, size):
    tw, th = size
    w, h = img.size
    scale = max(tw / w, th / h)
    nw, nh = int(w * scale), int(h * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - tw) // 2
    top = int((nh - th) * 0.25)
    return img.crop((left, top, left + tw, top + th))


def rounded_image(img, radius):
    img = img.convert("RGBA")
    mask = Image.new("L", img.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(
        (0, 0, img.size[0] - 1, img.size[1] - 1),
        radius=radius,
        fill=255,
    )
    img.putalpha(mask)
    return img


def current_week_text():
    today = date.today()
    days_since_monday = today.weekday()
    start = today - timedelta(days=days_since_monday)
    end = start + timedelta(days=7)
    months = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]
    return f"{start.day:02d} {months[start.month - 1]} - {end.day:02d} {months[end.month - 1]}"


def get_latest_reddit_post_url():
    post_url = get_latest_post_from_reddit_user()
    if post_url:
        return post_url

    raise RuntimeError(f"No se encontro ningun post Weekly Skin Sale en el perfil de {REDDIT_USER}")


def normalize_reddit_url(url):
    url = html.unescape(url).strip()
    if url.startswith("/r/"):
        url = "https://www.reddit.com" + url
    return url.split("?")[0].rstrip("/") + "/"


def get_latest_post_from_reddit_user_json():
    url = f"https://www.reddit.com/user/{REDDIT_USER}/submitted.json"
    response = requests.get(
        url,
        params={"limit": 25, "sort": "new"},
        headers=HEADERS,
        timeout=20,
    )
    response.raise_for_status()
    posts = response.json()["data"]["children"]

    for post in posts:
        data = post["data"]
        title = data.get("title", "")
        if "weekly skin sale" in title.lower():
            return "https://www.reddit.com" + data["permalink"]

    return None


def get_latest_post_from_reddit_user_rss():
    global LATEST_POST_TEXT

    rss_url = f"https://www.reddit.com/user/{REDDIT_USER}/submitted/.rss"
    response = requests.get(rss_url, headers=HEADERS, timeout=20)
    response.raise_for_status()

    root = ET.fromstring(response.text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}

    for entry in root.findall("atom:entry", ns):
        title = entry.findtext("atom:title", default="", namespaces=ns)
        if "weekly skin sale" not in title.lower():
            continue

        link = entry.find("atom:link", ns)
        if link is None:
            continue

        content = entry.findtext("atom:content", default="", namespaces=ns)
        summary = entry.findtext("atom:summary", default="", namespaces=ns)
        LATEST_POST_TEXT = html.unescape(content or summary)
        return link.attrib.get("href")

    return None


def get_latest_post_from_reddit_user():
    global LATEST_POST_TEXT

    LATEST_POST_TEXT = None

    try:
        post_url = get_latest_post_from_reddit_user_json()
        if post_url:
            return post_url
    except requests.HTTPError as exc:
        if exc.response is None or exc.response.status_code != 403:
            raise
        print("Reddit bloqueo submitted.json, probando RSS del perfil")

    return get_latest_post_from_reddit_user_rss()


def get_reddit_post_text(post_url):
    if LATEST_POST_TEXT:
        return LATEST_POST_TEXT

    json_url = post_url.rstrip("/") + ".json"
    response = requests.get(json_url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    data = response.json()
    return data[0]["data"]["children"][0]["data"].get("selftext", "")


def parse_sales_table(text):
    sales = []
    html_row_pattern = re.compile(
        r"<tr>\s*"
        r"<td[^>]*>(?P<skin_cell>.*?)</td>\s*"
        r"<td[^>]*>(?P<price>\d+)\s*RP</td>\s*"
        r"<td[^>]*>(?P<original>\d+)\s*RP</td>\s*"
        r"<td[^>]*>(?P<discount>\d+)%</td>\s*"
        r"</tr>",
        re.IGNORECASE | re.DOTALL,
    )

    for match in html_row_pattern.finditer(text):
        skin_cell = match.group("skin_cell")
        skin = re.sub(r"<[^>]+>", "", skin_cell)
        skin = html.unescape(skin).strip(" -|")
        sales.append(
            {
                "skin": skin,
                "price": int(match.group("price")),
                "discount": int(match.group("discount")),
                "week": current_week_text(),
                "source": "reddit",
            }
        )

    if sales:
        return sales

    row_pattern = re.compile(
        r"(?:\[(?P<link_skin>[^\]]+)\]\([^)]+\)|(?P<plain_skin>[^\n\r|]+?))"
        r"\s+(?P<price>\d+)\s*RP\s+"
        r"(?P<original>\d+)\s*RP\s+"
        r"(?P<discount>\d+)%",
        re.IGNORECASE,
    )

    for match in row_pattern.finditer(text):
        skin = match.group("link_skin") or match.group("plain_skin")
        skin = html.unescape(skin).strip(" -|")
        if skin.lower() in {"skin", "cost", "original cost", "discount"}:
            continue
        sales.append(
            {
                "skin": skin,
                "price": int(match.group("price")),
                "discount": int(match.group("discount")),
                "week": current_week_text(),
                "source": "reddit",
            }
        )

    return sales


def fetch_reddit_sales():
    global LATEST_POST_URL
    post_url = get_latest_reddit_post_url()
    LATEST_POST_URL = normalize_reddit_url(post_url)
    print("Usando post de Reddit:", post_url)
    post_text = get_reddit_post_text(post_url)
    sales = parse_sales_table(post_text)
    if not sales:
        raise RuntimeError("No se encontraron ofertas en el post de Reddit")
    return sales


def read_sent_post_url():
    if not os.path.exists(SENT_POST_FILE):
        return ""
    with open(SENT_POST_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()


def write_sent_post_url(post_url):
    with open(SENT_POST_FILE, "w", encoding="utf-8") as f:
        f.write(post_url + "\n")


def resolve_skin_from_ddragon(sale, champion_data):
    target = normalize(sale["skin"])

    for champion_id, champion in champion_data.items():
        for skin in champion["skins"]:
            if normalize(skin["name"]) == target:
                return {
                    "skin": sale["skin"],
                    "champion": champion["name"],
                    "discount": sale["discount"],
                    "price": sale["price"],
                    "week": sale.get("week", current_week_text()),
                    "url": f"https://ddragon.leagueoflegends.com/cdn/img/champion/splash/{champion_id}_{skin['num']}.jpg",
                }

    return None


sales = fetch_reddit_sales()

if LATEST_POST_URL == read_sent_post_url():
    print("El ultimo post de Reddit ya fue enviado:", LATEST_POST_URL)
    raise SystemExit(0)

sales = sorted(sales, key=lambda x: int(x["discount"]), reverse=True)

version = requests.get("https://ddragon.leagueoflegends.com/api/versions.json", headers=HEADERS, timeout=20).json()[0]
champion_data = requests.get(
    f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/championFull.json",
    headers=HEADERS,
    timeout=20,
).json()["data"]

resolved = []

for sale in sales:
    resolved_skin = resolve_skin_from_ddragon(sale, champion_data)
    if resolved_skin:
        resolved.append(resolved_skin)
    else:
        print("No se encontro skin:", sale["skin"])


image_slots = [
    (70, 182, 410, 185), (524, 182, 410, 185), (980, 182, 410, 185),
    (70, 462, 410, 185), (524, 462, 410, 185), (980, 462, 410, 185),
    (70, 740, 410, 185), (524, 740, 410, 185), (980, 740, 410, 185),
]

text_slots = [
    (73, 395, 345, 412), (532, 395, 804, 412), (994, 395, 1265, 412),
    (73, 675, 345, 702), (532, 675, 804, 702), (994, 675, 1265, 702),
    (73, 950, 345, 992), (532, 950, 804, 992), (994, 950, 1265, 992),
]

discount_slots = [
    (398, 333), (857, 333), (1319, 333),
    (398, 623), (857, 623), (1319, 623),
    (398, 913), (857, 913), (1319, 913),
]

price_slots = [
    (412, 391), (871, 391), (1333, 391),
    (412, 672), (871, 672), (1333, 672),
    (412, 945), (871, 945), (1333, 945),
]

ROW_CROP_HEIGHTS = {
    1: 455,
    2: 735,
    3: 1087,
}


def crop_to_promos(canvas, promo_count):
    if promo_count <= 0:
        return canvas

    used_rows = math.ceil(promo_count / 3)
    crop_height = ROW_CROP_HEIGHTS.get(used_rows, canvas.height)
    crop_height = min(crop_height, canvas.height)
    return canvas.crop((0, 0, canvas.width, crop_height))


name_font = font(18, True)
discount_font = font(24, True)
price_font = font(27, True)
rp_font = font(15, True)
week_font = font(22, True)

PAGE_SIZE = 9
pages = math.ceil(len(resolved) / PAGE_SIZE)
sent_to_discord = False

for page in range(pages):
    canvas = Image.open("template.png").convert("RGB")
    draw = ImageDraw.Draw(canvas)

    draw.text(
        (1215, 72),
        current_week_text(),
        fill=(10, 16, 30),
        font=week_font,
    )

    page_items = resolved[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]

    for i, skin in enumerate(page_items):
        x, y, w, h = image_slots[i]

        try:
            img_data = requests.get(skin["url"], headers=HEADERS, timeout=20).content
            splash = Image.open(BytesIO(img_data)).convert("RGB")
            splash = cover_resize(splash, (w, h))
            splash = splash.resize((w - 8, h - 8), Image.LANCZOS)
            splash = rounded_image(splash, 20)
            canvas.paste(splash, (x - 7, y + 1), splash)
        except Exception as exc:
            print("Error imagen:", exc)

        name_x, name_y, _, _ = text_slots[i]
        draw.rectangle(
            (name_x - 2, name_y - 2, name_x + 280, name_y + 40),
            fill=(247, 250, 255),
        )
        draw.text(
            (name_x, name_y),
            skin["skin"][:28],
            fill=(10, 16, 30),
            font=name_font,
        )

        dx, dy = discount_slots[i]
        discount_text = f"-{skin['discount']}%"
        discount_bbox = draw.textbbox((0, 0), discount_text, font=discount_font)
        discount_w = discount_bbox[2] - discount_bbox[0] + 24
        discount_h = 34
        discount_x2 = dx + 82
        discount_x1 = discount_x2 - discount_w
        discount_y1 = dy - 4
        discount_y2 = discount_y1 + discount_h

        draw.rounded_rectangle(
            (discount_x1 + 2, discount_y1 + 3, discount_x2 + 2, discount_y2 + 3),
            radius=17,
            fill=(208, 221, 255),
        )
        draw.rounded_rectangle(
            (discount_x1, discount_y1, discount_x2, discount_y2),
            radius=17,
            fill=(45, 95, 255),
        )
        draw.text(
            (discount_x1 + 12, discount_y1 + 2),
            discount_text,
            fill=(255, 255, 255),
            font=discount_font,
        )

        px, py = price_slots[i]
        price_text = str(skin["price"])
        price_bbox = draw.textbbox((0, 0), price_text, font=price_font)
        price_w = price_bbox[2] - price_bbox[0]

        draw.rounded_rectangle(
            (px - 48, py - 4, px + 104, py + 37),
            radius=12,
            fill=(247, 250, 255),
        )
        draw.text(
            (px - 34, py),
            price_text,
            fill=(10, 16, 30),
            font=price_font,
        )
        draw.text(
            (px - 28 + price_w, py + 8),
            "RP",
            fill=(85, 103, 150),
            font=rp_font,
        )

    canvas = crop_to_promos(canvas, len(page_items))

    filename = f"sales_page_{page + 1}.png"
    canvas.save(filename)

    if WEBHOOK_URL:
        with open(filename, "rb") as f:
            response = requests.post(
                WEBHOOK_URL,
                data={
                    "content": f"GPBot Tienda Semanal | Pagina {page + 1}/{pages}"
                },
                files={
                    "file": (filename, f, "image/png")
                },
                timeout=20,
            )
            response.raise_for_status()
            sent_to_discord = True

if LATEST_POST_URL and sent_to_discord:
    write_sent_post_url(LATEST_POST_URL)

print("Finalizado")
