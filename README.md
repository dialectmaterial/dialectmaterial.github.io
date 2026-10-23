# actualspirit.com

Personal site of Dimitri Crooijmans: profile, links, and articles mirrored from
[Actual Spirit on Substack](https://actualspirit.substack.com). Hosted free on GitHub Pages (repo dialectmaterial/dialectmaterial.github.io) at actualspirit.com,
which builds it with Jekyll on every push.

- Home page text, featured essays and project cards: `_data/home.yml`
- How the site shows up in Google (title, description, your other profiles): the `search:` block in `_data/home.yml`
- Site icon and share preview: `assets/icons/`, `favicon.ico`, `assets/share.jpg`
- "Read next" under each article: the `related:` line in the post's front matter (two slugs). Posts without one show the "Start here" essays.
- Name and footer links: `_config.yml`
- Articles: `_posts/YYYY-MM-DD-slug.md` (plain Markdown; write new ones by hand or import them)
- Images: `assets/images/<slug>/`
- Look: `assets/style.css`, `_layouts/`

## Import new Substack posts

```sh
python3 -m venv /tmp/venv && /tmp/venv/bin/pip install markdownify beautifulsoup4
/tmp/venv/bin/python tools/import-substack.py   # only fetches posts not imported yet
git add -A && git commit -m "Import new articles" && git push
```

## Topics, share images, citations, About

- **Topics:** each essay has a `topics: [Hegel, Politics]` line. The names and their page texts are in `_data/topics.yml`; each has a page at `/topics/<slug>/`. A new topic also needs a file in `topics/` (copy one).
- **Share images:** `python3 tools/make-share-images.py` makes `assets/share/<slug>.jpg` for articles that have none; `--force` remakes them all (after a title or cover change).
- **Daily import:** `tools/sync-substack.sh` imports new Substack posts, makes their share images and publishes them. It runs every day at 08:00 on Dimitri's computer (systemd user timer `actualspirit-sync`; run now with `systemctl --user start actualspirit-sync`, see the log with `journalctl --user -u actualspirit-sync`). Substack blocks GitHub's servers, so it can't be a GitHub Action. Always `git pull` before editing locally.
- **Citations:** essays (not stories) end with "Cite this essay"; the name format is `author_cite` in `_config.yml`.
- **Visitor counts:** Cloudflare Web Analytics, token `cloudflare_analytics` in `_config.yml`.
- **About page:** `about.md` is a draft, offline while it has `published: false`.
