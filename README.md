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
