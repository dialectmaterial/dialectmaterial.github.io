# actualspirit.com: notes for coding agents

A Jekyll site on GitHub Pages. Pushing `main` publishes it. The README maps every part of the site to its file.

## Before and after editing

- `git pull` first: the owner edits `_data/home.yml` on GitHub directly.
- Preview locally with `jekyll serve` (127.0.0.1:4000) or `jekyll build -d <dir>`; the gems are in the user gem directory (`GEM_PATH=~/.local/share/gem/ruby/3.4.0`). Live reload can serve a 0-byte copy of a file rewritten mid-copy; touch the file again.
- Publish only what the owner names. Don't stage `_site/` or anything in `private/`.

## Things that stay offline or untouched

- `private/` (gitignored) holds unpublished drafts (About pages). `about.md` and `glossary.md` stay `published: false` until the owner says otherwise.
- The local `insta` branch: don't rebase, push or change it unless asked. The `/insta/` page itself is live on `main`.

## Content conventions

- Substack import: `tools/import-substack.py` reads the publications in its `PUBLICATIONS` list (Actual Spirit and the Dutch Driftmatig). Dutch posts get `lang: nl`, poems are left out, and slug clashes get `-nl`. The daily scheduled import runs from a separate automation clone (see the README); never publish from this checkout as a routine check.
- Instagram page: `tools/import-instagram.py <export.zip>` writes `_data/insta_posts.json` and `assets/insta/`; `_data/insta.yml` is edited by hand.
- Talks: `_data/talks.yml`, thumbnails 640x360 in `assets/talks/`.
- Topic names are the owner's choice ("Modern philosophy", "Dialectical materialism"); don't rename them.
- `a-rose-is-a-rose/index.html` is a build product of an artwork project outside this repo; replace it whole rather than editing it.
- `local/index.html` ("Open-Source Must Win" in dot art) is likewise built by `~/Pictures/artwork/open-source-must-win/build.py` (run with the ascii-art venv); replace it whole.
