#!/usr/bin/env python3
"""
Static site generator for smartorgan.eu.

Usage:  python3 build.py

Content lives in content/ — just the <div class="text"> interior.
Metadata (title, h1, active page, keywords, description, flag links)
is defined in the PAGES list below.

Edit content or metadata, then run build.py to regenerate all HTML files.
"""

import os
import shutil

# ── Templates ──────────────────────────────────────────────────────────────

TEMPLATE_CS = """<!DOCTYPE html>
<html lang="cs">

<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <link rel="stylesheet" href="styles.css">
  <meta name="keywords" content="{keywords}">
  <meta name="description" content="{description}">
</head>

<body>
<div id="main-frame">
  <div id="header">
    <div class="header-top">
      <div id="logo"><img src="img/logo-transparent.png" alt="logo" width="100"></div>
      <div id="top-menu">
        <a href="index.html"{active_index}>Úvod</a>
        <a href="cecilia.htm"{active_cecilia}>Cecilia</a>
        <a href="organ.htm"{active_organ}>Varhany</a>
        <a href="services.htm"{active_services}>Služby</a>
        <a href="contact.htm"{active_contact}>Kontakt / partneři</a>
        <a href="{cz_href}"><img src="img/flag_cz.gif" alt="Čeština"></a>
        <a href="{en_href}"><img src="img/flag_en.gif" alt="English"></a>
      </div>
    </div>
  </div>

  <div id="content">
    <div class="text">

{content}

    </div>
  </div>

  <div id="footer">Copyright &copy; 2011 | www.smartorgan.eu | All rights reserved | Created by Jakub Mlnařík</div>
</div>

</body>
</html>
"""

TEMPLATE_EN = """<!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <link rel="stylesheet" href="styles.css">
  <meta name="keywords" content="{keywords}">
  <meta name="description" content="{description}">
</head>

<body>
<div id="main-frame">
  <div id="header">
    <div class="header-top">
      <div id="logo"><img src="img/logo-transparent.png" alt="logo" width="100"></div>
      <div id="top-menu">
        <a href="index-en.html"{active_index}>Introduction</a>
        <a href="cecilia-en.htm"{active_cecilia}>Cecilia</a>
        <a href="organ-en.htm"{active_organ}>Organs</a>
        <a href="services-en.htm"{active_services}>Services</a>
        <a href="contact-en.htm"{active_contact}>Contact / partners</a>
        <a href="{cz_href}"><img src="img/flag_cz.gif" alt="Čeština"></a>
        <a href="{en_href}"><img src="img/flag_en.gif" alt="English"></a>
      </div>
    </div>
  </div>

  <div id="content">
    <div class="text">

{content}

    </div>
  </div>

  <div id="footer">Copyright &copy; 2011 | www.smartorgan.eu | All rights reserved | Created by Jakub Mlnařík</div>
</div>

</body>
</html>
"""


# ── Helper ─────────────────────────────────────────────────────────────────

def active_class(page_id, current):
    """Return ' class=\"active\"' if page_id matches current, else empty string."""
    return ' class="active"' if page_id == current else ''


# ── Page definitions ───────────────────────────────────────────────────────
# Each entry: (filename, lang, title, h1, active_page, keywords, description, cz_href, en_href)

PAGES = [
    # ── Czech pages ──
    ("index.html", "cs",
     "Varhany Mlnařík",
     "Úvod",
     "index",
     "digitální varhany, varhany, cvičení, MIDI, pedálnice, hrací stoly, hauptwerk, grandorgue, opravy varhan, ladění",
     "Výroba: digitální varhany, MIDI, pedálnice, hrací stoly, cvičné varhany, hauptwerk, grandorgue, opravy varhan, ladění",
     "index.html", "index-en.html"),

    ("cecilia.htm", "cs",
     "Varhanní systém Cecilia",
     "Zvukový systém Cecilia",
     "cecilia",
     "cecilia, MIDI, expandér, varhanní modul",
     "cecilia, MIDI, expandér, varhanní modul",
     "cecilia.htm", "cecilia-en.htm"),

    ("organ.htm", "cs",
     "Digitální varhany, pedálnice, MIDI, traktura, zvukové moduly",
     "Varhany - díly i kompletní nástroje",
     "organ",
     "digitální varhany, varhany, cvičení, MIDI, pedálnice, hrací stoly, hauptwerk, grandorgue, opravy varhan, ladění",
     "Výroba: digitální varhany, MIDI, pedálnice, hrací stoly, cvičné varhany, hauptwerk, grandorgue, opravy varhan, ladění",
     "organ.htm", "organ-en.htm"),

    ("services.htm", "cs",
     "Varhany Mlnařík | služby",
     "Služby",
     "services",
     "digitální varhany, varhany, cvičení, MIDI, pedálnice, hrací stoly, hauptwerk, grandorgue, opravy varhan, ladění",
     "Výroba: digitální varhany, MIDI, pedálnice, hrací stoly, cvičné varhany, hauptwerk, grandorgue, opravy varhan, ladění",
     "services.htm", "services-en.htm"),

    ("contact.htm", "cs",
     "Kontakty | Varhany Mlnařík",
     "Kontakt",
     "contact",
     "digitální varhany, varhany, cvičení, MIDI, pedálnice, hrací stoly, hauptwerk, grandorgue, opravy varhan, ladění",
     "Výroba: digitální varhany, MIDI, pedálnice, hrací stoly, cvičné varhany, hauptwerk, grandorgue, opravy varhan, ladění",
     "contact.htm", "contact-en.htm"),

    # ── English pages ──
    ("index-en.html", "en",
     "Organ Mlnarik",
     "Introduction",
     "index",
     "digital organ, MIDI, pedalboards, consoles, hauptwerk",
     "digital organ, MIDI, pedalboards, consoles, hauptwerk",
     "index.html", "index-en.html"),

    ("cecilia-en.htm", "en",
     "Organ system Cecilia",
     "Organ sound system Cecilia",
     "cecilia",
     "cecilia, MIDI, expander, organ module, organ unit, sound engine",
     "cecilia, MIDI, expander, organ module, organ unit, sound engine",
     "cecilia.htm", "cecilia-en.htm"),

    ("organ-en.htm", "en",
     "Digital organs, MIDI consoles",
     "Organs - parts and complete instruments",
     "organ",
     "digital organ, MIDI, pedalboards, consoles, hauptwerk, grandorgue",
     "digital organ, MIDI, pedalboards, consoles, hauptwerk, grandorgue",
     "organ.htm", "organ-en.htm"),

    ("services-en.htm", "en",
     "Mlnarik organ | services",
     "Services",
     "services",
     "cecilia, MIDI, expander, organ module, organ unit, sound engine",
     "cecilia, MIDI, expander, organ module, organ unit, sound engine",
     "services.htm", "services-en.htm"),

    ("contact-en.htm", "en",
     "Contact | Organ Mlnarik",
     "Contact",
     "contact",
     "digital organ, MIDI, pedalboards, consoles, hauptwerk",
     "digital organ, MIDI, pedalboards, consoles, hauptwerk",
     "contact.htm", "contact-en.htm"),
]


# ── Build ──────────────────────────────────────────────────────────────────

def build():
    # Ensure output directory (current dir)
    out_dir = "."

    for filename, lang, title, h1, active, keywords, description, cz_href, en_href in PAGES:
        # Read content snippet
        content_file = os.path.join("content", filename)
        if not os.path.exists(content_file):
            print(f"⚠  Missing content file: {content_file}")
            continue

        with open(content_file, "r", encoding="utf-8") as f:
            content = f.read().rstrip()

        # Pick template
        template = TEMPLATE_CS if lang == "cs" else TEMPLATE_EN

        # Build the HTML
        html = template.format(
            title=title,
            h1=h1,
            keywords=keywords,
            description=description,
            content=content,
            cz_href=cz_href,
            en_href=en_href,
            active_index=active_class("index", active),
            active_cecilia=active_class("cecilia", active),
            active_organ=active_class("organ", active),
            active_services=active_class("services", active),
            active_contact=active_class("contact", active),
        )

        out_path = os.path.join(out_dir, filename)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
            f.write("\n")

        print(f"✓  Generated {out_path}")


if __name__ == "__main__":
    build()
