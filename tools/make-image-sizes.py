#!/usr/bin/env python3
"""Make a smaller copy of every large article image, so phones and the small
picture tiles load less, and point the articles' <img> tags at both sizes.

Usage:
    pip install pillow
    python3 tools/make-image-sizes.py

For each image in assets/images/ wider than 900 px it writes <name>-800.jpg
(skipped when it already exists), then adds srcset/sizes to the <img> tags in
_posts/ that use it. Safe to run again; the daily Substack sync runs it.
"""

import re
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
IMAGES = ROOT / "assets" / "images"
SMALL = 800
SIZES = "(max-width: 900px) 100vw, 860px"   # the text column plus the wide-figure overhang


def small_name(path):
    return path.with_name(f"{path.stem}-{SMALL}.jpg")


def make_small(path):
    """Write the smaller copy if the image is big enough to need one. Returns the original width or None."""
    if re.search(rf"-{SMALL}$", path.stem):
        return None
    with Image.open(path) as img:
        width = img.width
        if width <= 900:
            return None
        dest = small_name(path)
        if not dest.exists():
            copy = img.convert("RGBA") if img.mode in ("P", "LA") else img
            if copy.mode == "RGBA":
                background = Image.new("RGB", copy.size, (243, 240, 230))
                background.paste(copy, mask=copy.split()[3])
                copy = background
            copy = copy.convert("RGB")
            copy.thumbnail((SMALL, SMALL * 4), Image.LANCZOS)
            copy.save(dest, quality=78, optimize=True, progressive=True)
            print("wrote", dest.relative_to(ROOT))
    return width


def main():
    widths = {}
    for path in sorted(IMAGES.rglob("*")):
        if path.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
            w = make_small(path)
            if w:
                widths["/" + str(path.relative_to(ROOT))] = w

    def add_srcset(m):
        tag, src = m.group(0), m.group(1)
        if "srcset=" in tag or src not in widths:
            return tag
        small = "/" + str(small_name(ROOT / src.lstrip("/")).relative_to(ROOT))
        return tag.replace(f'src="{src}"', f'src="{src}" srcset="{small} {SMALL}w, {src} {widths[src]}w" sizes="{SIZES}"', 1)

    for post in sorted((ROOT / "_posts").glob("*.md")):
        text = post.read_text()
        new = re.sub(r'<img src="([^"]+)"[^>]*>', add_srcset, text)
        if new != text:
            post.write_text(new)
            print("updated", post.relative_to(ROOT))


if __name__ == "__main__":
    main()
