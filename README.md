# smartorgan.eu — static site generator

A minimal Python script that eliminates HTML redundancy (header, footer, menu, boilerplate) across the site's 10 pages (5 pages × 2 languages).

## Prerequisites

- Python 3
- [Pillow](https://python-pillow.org/) (for automatic thumbnail generation)

### Setup (recommended: virtual environment)

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install Pillow
```

## Usage

```sh
python3 build.py
```

This regenerates all `.html` / `.htm` files in the project root and automatically generates thumbnail images (`-thumb.jpg`) for every gallery image that references one.

## File structure

| Path | Purpose |
|---|---|
| `build.py` | Generator script with templates + page metadata |
| `content/` | Page-specific content — just the `<div class="text">` interior |
| `*.html`, `*.htm`, `*-cz.html`, `*-cz.htm` | **Generated** output (16 files) |
| `styles.css` | Stylesheet (not generated) |

## Workflow

1. Edit content in `content/<filename>`.
2. Edit page metadata (title, h1, keywords, etc.) in the `PAGES` list inside `build.py` if needed.
3. Run `python3 build.py`.
4. Commit both `content/` and the generated HTML files.

## Regenerated files

### English (default — no suffix)
- `index.html`
- `cecilia.htm`
- `organ.htm`
- `services.htm`
- `contact.htm`
- `keyboards.htm`
- `midi-modules.htm`
- `about.htm`

### Czech (with `-cz` suffix)
- `index-cz.html`
- `cecilia-cz.htm`
- `organ-cz.htm`
- `services-cz.htm`
- `contact-cz.htm`
- `keyboards-cz.htm`
- `midi-modules-cz.htm`
- `about-cz.htm`
