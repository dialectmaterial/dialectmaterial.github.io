#!/usr/bin/env python3
"""Import an Instagram data export into the /insta/ page.

Usage:
    python3 tools/import-instagram.py PATH [--include-archived] [--dry-run]

PATH is the export .zip or its unpacked folder. Ask Instagram for the JSON
format (Accounts Centre > Your information and permissions > Download your
information > JSON, media quality High).

Writes:
    _data/insta_posts.json     every post and reel, newest first
    assets/insta/<id>/NN.jpg   the image, at most 1440 px on the long side
    assets/insta/<id>/NN-t.jpg a 480 px thumbnail for the grid
    assets/insta/<id>/NN.mp4   videos as they are, with an NN.jpg poster frame
    assets/insta/avatar.jpg    the profile photo

Profile text (name, bio) is printed, not written: edit _data/insta.yml by hand.
Uses only the standard library, plus ImageMagick (magick) and ffmpeg.
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DATA = ROOT / "_data" / "insta_posts.json"
OUT_MEDIA = ROOT / "assets" / "insta"
VIDEO = {".mp4", ".mov", ".m4v"}
IMAGE = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".gif"}


def fix(s):
    """Instagram writes UTF-8 text as if it were Latin-1 (é becomes Ã©). Undo that."""
    if not isinstance(s, str):
        return s
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


def safe_extract(zpath, dest):
    with zipfile.ZipFile(zpath) as z:
        for member in z.infolist():
            target = (dest / member.filename).resolve()
            if not str(target).startswith(str(dest.resolve())):
                sys.exit(f"Refusing unsafe path in zip: {member.filename}")
        z.extractall(dest)


def find_root(base):
    """The folder that holds your_instagram_activity/ (or the older content/)."""
    for p in [base, *sorted(base.iterdir())]:
        if p.is_dir() and ((p / "your_instagram_activity").exists() or (p / "content").exists() or (p / "media").exists()):
            return p
    return base


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def find(root, name):
    hits = sorted(root.rglob(name))
    return hits


def entries(root, include_archived):
    """Yield (kind, entry) for every post and reel in the export."""
    for f in find(root, "posts_*.json"):
        data = load(f)
        for e in data if isinstance(data, list) else data.get("ig_posts", []):
            yield "post", e
    for f in find(root, "reels.json"):
        for e in load(f).get("ig_reels_media", []):
            yield "reel", e
    if include_archived:
        for f in find(root, "archived_posts.json"):
            for e in load(f).get("ig_archived_post_media", []):
                yield "post", e


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def size(path):
    out = subprocess.check_output(["magick", "identify", "-format", "%w %h", f"{path}[0]"]).decode().split()
    return int(out[0]), int(out[1])


def make_image(src, dest_dir, n):
    full, thumb = dest_dir / f"{n:02d}.jpg", dest_dir / f"{n:02d}-t.jpg"
    run(["magick", f"{src}[0]", "-auto-orient", "-strip", "-resize", "1440x1440>", "-quality", "84", "-interlace", "Plane", str(full)])
    run(["magick", str(full), "-resize", "480x640^", "-quality", "78", "-interlace", "Plane", str(thumb)])
    w, h = size(full)
    return {"type": "image", "src": url(full), "thumb": url(thumb), "width": w, "height": h}


def make_video(src, dest_dir, n):
    vid, poster, thumb = dest_dir / f"{n:02d}.mp4", dest_dir / f"{n:02d}.jpg", dest_dir / f"{n:02d}-t.jpg"
    shutil.copyfile(src, vid)
    run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "0.5", "-i", str(src), "-frames:v", "1", "-q:v", "3", str(poster)])
    run(["magick", str(poster), "-resize", "480x640^", "-quality", "78", str(thumb)])
    w, h = size(poster)
    mb = vid.stat().st_size / 1e6
    if mb > 50:
        print(f"  warning: {vid.relative_to(ROOT)} is {mb:.0f} MB (GitHub refuses files over 100 MB)")
    return {"type": "video", "src": url(vid), "thumb": url(thumb), "poster": url(poster), "width": w, "height": h}


def url(p):
    return "/" + str(p.relative_to(ROOT))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", type=Path)
    ap.add_argument("--include-archived", action="store_true", help="also import posts you archived (hidden from the profile)")
    ap.add_argument("--dry-run", action="store_true", help="list what would be imported, write nothing")
    args = ap.parse_args()

    for tool in ("magick", "ffmpeg"):
        if not shutil.which(tool):
            sys.exit(f"{tool} is needed but not installed")

    with tempfile.TemporaryDirectory() as tmp:
        base = args.path
        if base.suffix == ".zip":
            base = Path(tmp)
            safe_extract(args.path, base)
        root = find_root(base)

        # Profile
        for f in find(root, "personal_information.json"):
            user = load(f).get("profile_user", [{}])[0]
            strings = {k: fix(v.get("value")) for k, v in user.get("string_map_data", {}).items()}
            print("Profile in the export (copy what you want into _data/insta.yml):")
            for key in ("Username", "Name", "Bio", "Website"):
                if strings.get(key):
                    print(f"  {key}: {strings[key]!r}")
            photo = user.get("media_map_data", {}).get("Profile Photo", {}).get("uri")
            if photo and (root / photo).exists() and not args.dry_run:
                OUT_MEDIA.mkdir(parents=True, exist_ok=True)
                run(["magick", str(root / photo), "-auto-orient", "-strip", "-resize", "600x600>", "-quality", "86", str(OUT_MEDIA / "avatar.jpg")])
                print("  profile photo saved as /assets/insta/avatar.jpg")
            break

        posts, seen = [], set()
        for kind, e in entries(root, args.include_archived):
            media = e.get("media") or [e]
            ts = e.get("creation_timestamp") or media[0].get("creation_timestamp")
            if not ts:
                continue
            date = datetime.fromtimestamp(ts, tz=timezone.utc)
            pid = date.strftime("%Y%m%d-%H%M%S")
            while pid in seen:
                pid += "b"
            seen.add(pid)
            caption = fix(e.get("title") or media[0].get("title") or "")
            files = [root / m["uri"] for m in media if m.get("uri")]
            files = [f for f in files if f.suffix.lower() in VIDEO | IMAGE and f.exists()]
            if not files:
                print(f"  skipped {pid}: no media files found")
                continue
            print(f"{pid}  {kind:4}  {len(files)} file(s)  {caption[:50]!r}")
            if args.dry_run:
                posts.append({"id": pid, "date": date.isoformat(), "kind": kind})
                continue
            dest = OUT_MEDIA / pid
            if dest.exists():
                shutil.rmtree(dest)
            dest.mkdir(parents=True)
            items = [(make_video if f.suffix.lower() in VIDEO else make_image)(f, dest, n) for n, f in enumerate(files, 1)]
            if kind == "post" and len(items) == 1 and items[0]["type"] == "video":
                kind = "reel"
            posts.append({"id": pid, "date": date.isoformat(), "kind": kind, "caption": caption, "media": items})

    posts.sort(key=lambda p: p["date"], reverse=True)
    print(f"\n{len(posts)} posts, {sum(p['kind'] == 'reel' for p in posts)} reels")
    if args.dry_run:
        return
    OUT_DATA.write_text(json.dumps(posts, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_DATA.relative_to(ROOT)}")
    # Folders from an earlier import that are no longer in the export
    keep = {p["id"] for p in posts}
    for d in OUT_MEDIA.iterdir():
        if d.is_dir() and d.name not in keep:
            print(f"  note: {d.relative_to(ROOT)} is not in this export (left in place)")


if __name__ == "__main__":
    main()
