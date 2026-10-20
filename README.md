# dialectmaterial.github.io

Personal site of Dimitri Crooijmans: profile, links, and articles mirrored from
[Actual Spirit on Substack](https://actualspirit.substack.com). Hosted free on GitHub Pages,
which builds it with Jekyll on every push.

- Links and name: `_config.yml`
- Articles: `_posts/YYYY-MM-DD-slug.md` (plain Markdown; write new ones by hand or import them)
- Images: `assets/images/<slug>/`
- Look: `assets/style.css`, `_layouts/`

## Import new Substack posts

```sh
python3 -m venv /tmp/venv && /tmp/venv/bin/pip install markdownify beautifulsoup4
/tmp/venv/bin/python tools/import-substack.py   # only fetches posts not imported yet
git add -A && git commit -m "Import new articles" && git push
```
