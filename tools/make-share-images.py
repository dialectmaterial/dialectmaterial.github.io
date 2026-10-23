#!/usr/bin/env python3
"""Make the preview image shown when an article is shared (Instagram, Telegram,
WhatsApp, X...): the title beside the article's cover, 1200x630.

Usage:
    pip install pillow
    python3 tools/make-share-images.py            # make images for articles that have none yet
    python3 tools/make-share-images.py --force    # remake all of them (after changing a title or cover)

Writes assets/share/<slug>.jpg. The site uses it automatically when it exists.
"""

import argparse
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = Path(__file__).resolve().parent / "fonts"
OUT = ROOT / "assets" / "share"

W, H = 1200, 630
PAPER = (243, 240, 230)
INK = (23, 21, 28)
MUTED = (106, 102, 89)
ACCENT = (85, 48, 138)


def front_matter(path):
    text = path.read_text()
    m = re.match(r"---\n(.*?)\n---", text, re.S)
    data = {}
    for line in (m.group(1) if m else "").splitlines():
        k, _, v = line.partition(":")
        v = v.split("  #")[0].strip()
        if v.startswith('"') and v.endswith('"'):
            v = v[1:-1].replace('\\"', '"')
        data[k.strip()] = v
    return data


def font(name, size, weight=None):
    f = ImageFont.truetype(str(FONTS / name), size)
    if weight:
        f.set_variation_by_axes([14, weight]) if len(f.get_variation_axes()) == 2 else f.set_variation_by_axes([weight])
    return f


def wrap(draw, text, f, width):
    lines, line = [], ""
    for word in text.split():
        test = (line + " " + word).strip()
        if draw.textlength(test, font=f) <= width or not line:
            line = test
        else:
            lines.append(line)
            line = word
    return lines + [line]


def cover(path, box_w, box_h):
    img = Image.open(path).convert("RGB")
    scale = max(box_w / img.width, box_h / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    left, top = (img.width - box_w) // 2, (img.height - box_h) // 2
    return img.crop((left, top, left + box_w, top + box_h))


def make(post, dest):
    canvas = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(canvas)
    image = post.get("image")
    pic_w = 470
    if image and (ROOT / image.lstrip("/")).exists():
        canvas.paste(cover(ROOT / image.lstrip("/"), pic_w, H), (W - pic_w, 0))
    else:
        draw.rectangle((W - pic_w, 0, W, H), fill=ACCENT)
        a = font("InstrumentSerif-Italic.ttf", 360)
        draw.text((W - pic_w / 2, H / 2 - 20), "a", font=a, fill=PAPER, anchor="mm")

    x, text_w = 72, W - pic_w - 72 * 2
    kicker = font("Inter.ttf", 20, 600)
    draw.text((x, 70), "ACTUAL SPIRIT", font=kicker, fill=ACCENT)

    # The largest title size that fits in four lines
    for size in (84, 76, 68, 60, 54, 48, 42):
        title_font = font("InstrumentSerif-Regular.ttf", size)
        lines = wrap(draw, post["title"], title_font, text_w)
        if len(lines) <= 4:
            break
    y = 120
    for line in lines:
        draw.text((x, y), line, font=title_font, fill=INK)
        y += round(size * 1.05)

    subtitle = post.get("subtitle", "")
    if subtitle and len(subtitle) <= 90 and len(lines) <= 3:
        dek = font("InstrumentSerif-Italic.ttf", 34)
        for line in wrap(draw, subtitle, dek, text_w)[:2]:
            y += 6
            draw.text((x, y + 12), line, font=dek, fill=MUTED)
            y += 38

    byline = font("Inter.ttf", 22, 500)
    draw.text((x, H - 70), "Dimitri F. Crooijmans · actualspirit.com", font=byline, fill=MUTED, anchor="ls")
    dest.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(dest, quality=86, optimize=True, progressive=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    for path in sorted((ROOT / "_posts").glob("*.md")):
        post = front_matter(path)
        slug = post.get("permalink", "").strip("/").split("/")[-1]
        if not slug or post.get("published") == "false":
            continue
        dest = OUT / f"{slug}.jpg"
        if dest.exists() and not args.force:
            continue
        make(post, dest)
        print("wrote", dest.relative_to(ROOT))


if __name__ == "__main__":
    main()
