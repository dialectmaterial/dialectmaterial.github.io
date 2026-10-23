#!/usr/bin/env python3
"""Import posts from a Substack publication into Jekyll Markdown posts.

Usage:
    pip install markdownify beautifulsoup4
    python3 tools/import-substack.py                 # import every post not yet imported
    python3 tools/import-substack.py --force         # re-import everything
    python3 tools/import-substack.py some-post-slug  # (re)import specific posts

Writes _posts/YYYY-MM-DD-<slug>.md and downloads images to assets/images/<slug>/.
"""

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup
from markdownify import markdownify

PUBLICATION = "actualspirit"
BASE = f"https://{PUBLICATION}.substack.com"
SKIP_SLUGS = {"coming-soon"}  # placeholder posts with no content

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "_posts"
IMAGES = ROOT / "assets" / "images"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def fetch_json(url):
    return json.loads(fetch(url))


def archive():
    posts, offset = [], 0
    while True:
        page = fetch_json(f"{BASE}/api/v1/archive?sort=new&limit=50&offset={offset}")
        if not page:
            return posts
        posts += page
        offset += len(page)


def attrs(tag):
    try:
        return json.loads(tag.get("data-attrs") or "{}")
    except json.JSONDecodeError:
        return {}


def download_image(url, slug, n):
    ext = re.search(r"\.(jpe?g|png|gif|webp)$", url.split("?")[0], re.I)
    ext = ext.group(1).lower().replace("jpeg", "jpg") if ext else "jpg"
    folder = IMAGES / slug
    folder.mkdir(parents=True, exist_ok=True)
    existing = sorted(folder.glob(f"{n:02d}.*"))  # may have been recompressed to another format
    if existing:
        return f"/assets/images/{slug}/{existing[0].name}"
    path = folder / f"{n:02d}.{ext}"
    if not path.exists():
        path.write_bytes(fetch(url))
    return f"/assets/images/{slug}/{path.name}"


def local_link(href, known_slugs):
    """Point links to other imported posts at this site instead of Substack."""
    m = re.match(rf"https?://(?:(?:{PUBLICATION}|dimitricrooijmans)\.substack\.com|open\.substack\.com/pub/{PUBLICATION})/p/([\w-]+)", href or "")
    if m and m.group(1) in known_slugs:
        return f"/articles/{m.group(1)}/"
    return href


def convert(post, known_slugs):
    slug = post["slug"]
    soup = BeautifulSoup(post["body_html"], "html.parser")
    raw = {}  # placeholder -> raw HTML kept as-is in the Markdown

    def keep_raw(tag, html):
        key = f"RAWHTML{len(raw)}X"
        raw[key] = html
        p = soup.new_tag("p")
        p.string = key
        tag.replace_with(p)

    # Substack chrome that makes no sense off Substack
    for sel in [".subscription-widget-wrap-editor", ".embedded-publication-wrap", "form", ".image-link-expand", "label.hide-text"]:
        for t in soup.select(sel):
            t.decompose()
    for t in soup.select("p.button-wrapper"):
        a = t.find("a")
        href = a.get("href", "") if a else ""
        if "/subscribe" in href or "action=share" in href:
            t.decompose()

    # Images: download the original and keep the caption
    n = 0
    figures = soup.select(".captioned-image-container")
    figures += [f for f in soup.select("figure") if not f.find_parent(class_="captioned-image-container")]
    for fig in figures:
        img = fig.find("img")
        if not img:
            continue
        a = attrs(img)
        n += 1
        try:
            local = download_image(a.get("src") or img["src"], slug, n)
        except OSError:  # original sometimes 403s; the CDN copy still works
            local = download_image(img["src"], slug, n)
        alt = (a.get("alt") or img.get("alt") or "").replace('"', "&quot;")
        cap = fig.find("figcaption")
        html = f'<figure><img src="{local}" alt="{alt}" loading="lazy">'
        if cap and cap.get_text(strip=True):
            html += f"<figcaption>{cap.decode_contents()}</figcaption>"
        keep_raw(fig, html + "</figure>")

    # Embeds
    for t in soup.select(".youtube-wrap"):
        vid = attrs(t).get("videoId")
        keep_raw(t, f'<div class="embed"><iframe src="https://www.youtube-nocookie.com/embed/{vid}" '
                    f'loading="lazy" allowfullscreen title="YouTube video"></iframe></div>')
    for t in soup.select("iframe.spotify-wrap"):
        keep_raw(t, f'<iframe class="spotify" src="{t["src"]}" height="152" loading="lazy" '
                    f'allow="encrypted-media" title="Spotify"></iframe>')
    for t in soup.select(".embedded-post-wrap"):
        a = attrs(t)
        title = a.get("title") or t.get_text(" ", strip=True)[:80]
        href = local_link(a.get("url") or (t.find("a") or {}).get("href"), known_slugs)
        p = soup.new_tag("p")
        link = soup.new_tag("a", href=href)
        link.string = f"→ {title}"
        p.append(link)
        t.replace_with(p)
    for t in soup.select(".mention-wrap"):
        a = attrs(t)
        if a.get("url"):
            link = soup.new_tag("a", href=a["url"])
            link.string = a.get("name", "")
            t.replace_with(link)
        else:
            t.replace_with(a.get("name", ""))

    # Footnotes -> kramdown footnotes
    notes = []
    for fn in soup.select("div.footnote"):
        num = fn.select_one(".footnote-number").get_text(strip=True)
        body = fn.select_one(".footnote-content")
        notes.append((num, body.extract()))
        fn.decompose()
    for a in soup.select("a.footnote-anchor"):
        a.replace_with(f"FNREF{a.get_text(strip=True)}X")

    for a in soup.find_all("a", href=True):
        a["href"] = local_link(a["href"], known_slugs)

    def md(html):
        out = markdownify(str(html), heading_style="ATX", bullets="-", escape_underscores=False)
        return re.sub(r"\n{3,}", "\n\n", out).strip()

    text = md(soup)
    if notes:
        text += "\n\n"
        for num, body in notes:
            note = md(body).replace("\n\n", "\n\n    ")
            text += f"\n[^{num}]: {note}\n"
    text = re.sub(r"FNREF(\d+)X", r"[^\1]", text)
    for key, html in raw.items():
        text = text.replace(key, html)
    return normalize_headings(text) + "\n"


def normalize_headings(markdown):
    """Make the post's top heading level ## (the title is the page's only #),
    shift the others along, and drop bold that Substack wraps headings in."""
    pattern = re.compile(r"^(#{1,6}) +(.*)$", re.M)
    levels = [len(m.group(1)) for m in pattern.finditer(markdown)]
    if not levels:
        return markdown
    shift = 2 - min(levels)

    def fix(m):
        title = re.sub(r"^\*\*(.*)\*\*$", r"\1", m.group(2).strip())
        return "#" * min(len(m.group(1)) + shift, 6) + " " + title

    return pattern.sub(fix, markdown)


def describe(markdown, words=40):
    """The opening of the first real paragraph, for previews and link cards."""
    for para in markdown.split("\n\n"):
        para = para.strip()
        if not para or para[0] in "<*>#![-|`" or len(para.split()) < 15:
            continue
        para = re.sub(r"\[\^\d+\]", "", para)
        para = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", para)
        para = re.sub(r"[*_]", "", para)
        cut = para.split()
        return " ".join(cut[:words]) + ("…" if len(cut) > words else "")
    return ""


def yaml_str(s):
    return json.dumps(s or "", ensure_ascii=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slugs", nargs="*")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    entries = [p for p in archive() if p["slug"] not in SKIP_SLUGS and p.get("audience") == "everyone"]
    known = {p["slug"] for p in entries}
    POSTS.mkdir(exist_ok=True)
    # Posts renamed on the site still point at their Substack original
    imported = {m.group(1) for f in POSTS.glob("*.md")
                for m in [re.search(r"^substack: .*/p/([\w-]+)", f.read_text(), re.M)] if m}
    for entry in entries:
        slug = entry["slug"]
        date = entry["post_date"][:10]
        out = POSTS / f"{date}-{slug}.md"
        if args.slugs and slug not in args.slugs:
            continue
        if (out.exists() or slug in imported) and not (args.force or args.slugs):
            continue
        post = fetch_json(f"{BASE}/api/v1/posts/{slug}")
        body = convert(post, known)
        front = [
            "---",
            f"title: {yaml_str(post['title'].strip())}",
            f"subtitle: {yaml_str(post.get('subtitle'))}",
            f"description: {yaml_str(describe(body))}",
            f"date: {date}",
            f"permalink: /articles/{slug}/",
            f"substack: {post['canonical_url']}",
        ]
        cover = sorted((IMAGES / slug).glob("01.*"))
        if cover:
            front.append(f"image: /assets/images/{slug}/{cover[0].name}")
        front += [
            "---",
            "",
        ]
        out.write_text("\n".join(front) + body)
        print("wrote", out.relative_to(ROOT))


if __name__ == "__main__":
    sys.exit(main())
