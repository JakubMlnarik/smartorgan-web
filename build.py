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
import re
import shutil

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False
    print("⚠  Pillow not installed — thumbnails will not be generated.")
    print("   Install with: pip install Pillow")

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
    <div id="lang-bar">
      <a href="{cz_href}" class="lang-switch">CS</a>
      <a href="{en_href}" class="lang-switch">EN</a>
    </div>
    <div class="header-top">
      <div id="logo"><img src="img/logo-transparent.png" alt="logo" width="100"></div>
      <div id="top-menu">
        <a href="index.html"{active_index}>Domů</a>
        <a href="midi-modules.htm"{active_midi}>MIDI</a>
        <a href="keyboards.htm"{active_keyboards}>Klaviatury</a>
        <a href="organ.htm"{active_organ}>Varhany</a>
        <a href="services.htm"{active_services}>Služby</a>
        <a href="cecilia.htm"{active_cecilia}>Cecilia</a>
        <a href="about.htm"{active_about}>O mně</a>
        <a href="contact.htm"{active_contact}>Kontakt</a>
      </div>
    </div>
  </div>

  <div id="content">
    <div class="text">

{content}

    </div>
  </div>

  <div id="footer">Copyright &copy; 2026 | www.smartorgan.eu | All rights reserved | Created by Jakub Mlnarik</div>
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
    <div id="lang-bar">
      <a href="{cz_href}" class="lang-switch">CS</a>
      <a href="{en_href}" class="lang-switch">EN</a>
    </div>
    <div class="header-top">
      <div id="logo"><img src="img/logo-transparent.png" alt="logo" width="100"></div>
      <div id="top-menu">
        <a href="index-en.html"{active_index}>Home</a>
        <a href="midi-modules-en.htm"{active_midi}>MIDI</a>
        <a href="keyboards-en.htm"{active_keyboards}>Keyboards</a>
        <a href="organ-en.htm"{active_organ}>Organs</a>
        <a href="services-en.htm"{active_services}>Services</a>
        <a href="cecilia-en.htm"{active_cecilia}>Cecilia</a>
        <a href="about-en.htm"{active_about}>About</a>
        <a href="contact-en.htm"{active_contact}>Contact</a>
      </div>
    </div>
  </div>

  <div id="content">
    <div class="text">

{content}

    </div>
  </div>

  <div id="footer">Copyright &copy; 2026 | www.smartorgan.eu | All rights reserved | Created by Jakub Mlnarik</div>
</div>

</body>
</html>
"""


# ── Helper ─────────────────────────────────────────────────────────────────

def active_class(page_id, current):
    """Return ' class=\"active\"' if page_id matches current, else empty string."""
    return ' class="active"' if page_id == current else ''


THUMB_HEIGHT = 180


def generate_thumb(full_path, thumb_path):
    """Generate a thumbnail from full_path if it doesn't exist or is outdated."""
    if not HAS_PILLOW:
        return
    if os.path.exists(thumb_path):
        full_mtime = os.path.getmtime(full_path)
        thumb_mtime = os.path.getmtime(thumb_path)
        if thumb_mtime >= full_mtime:
            return  # thumbnail is up-to-date
    img = Image.open(full_path)
    ratio = THUMB_HEIGHT / img.height
    new_width = int(img.width * ratio)
    thumb = img.resize((new_width, THUMB_HEIGHT), Image.LANCZOS)
    thumb.save(thumb_path, optimize=True, quality=85)
    print(f"   🖼  Generated thumbnail: {thumb_path}")


def process_content_images(content, img_dir):
    """Generate thumbnails for -thumb references and add loading='lazy' to all img tags."""

    def replace_img(match):
        tag = match.group(0)

        # Extract src attribute
        src_match = re.search(r'src="([^"]+)"', tag)
        if src_match:
            src = src_match.group(1)

            # Generate thumbnail if src points to a -thumb file
            if src.endswith('-thumb.jpg'):
                # Derive full image path: strip '-thumb' from the basename
                full_src = src[:-len('-thumb.jpg')] + '.jpg'
                full_path = os.path.join(img_dir, os.path.basename(full_src))
                thumb_path = os.path.join(img_dir, os.path.basename(src))
                if os.path.exists(full_path):
                    generate_thumb(full_path, thumb_path)
                else:
                    print(f"   ⚠  Full image not found: {full_path} (referenced from {src})")

        # Add loading="lazy" if not already present
        if 'loading=' not in tag:
            tag = tag.replace('<img', '<img loading="lazy"')

        return tag

    return re.sub(r'<img[^>]+>', replace_img, content)


# ── Page definitions ───────────────────────────────────────────────────────
# Each entry: (filename, lang, title, h1, active_page, keywords, description, cz_href, en_href)

PAGES = [
    # ── Czech pages ──
    ("index.html", "cs",
     "Varhany Mlnařík",
     "Domů",
     "index",
     "digitální varhany, varhany, cvičení, MIDI, pedálnice, hrací stoly, hauptwerk, grandorgue, opravy varhan, ladění",
     "Výroba: digitální varhany, MIDI, pedálnice, hrací stoly, cvičné varhany, hauptwerk, grandorgue, opravy varhan, ladění",
     "index.html", "index-en.html"),

    ("keyboards.htm", "cs",
     "Varhanní klaviatury | Kinetické klaviatury s Druckpunktem",
     "Varhanní klaviatury",
     "keyboards",
     "varhanní klaviatura, kinetická klaviatura, Druckpunkt, MIDI klaviatura, varhanní manuál, hall senzory",
     "Mechanické varhanní klaviatury s nastavitelným Druckpunktem a kinetickým projevem. 64 kláves, dřevěné klávesy, hliníkový rám, MIDI výstup.",
     "keyboards.htm", "keyboards-en.htm"),

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

    ("midi-modules.htm", "cs",
     "MIDI moduly pro digitální varhany | Hall-Scanner64, Input-Module16, Matrix-Scanner64, Output-Module16",
     "MIDI moduly",
     "midi",
     "MIDI moduly, Hall-Scanner64, Input-Module16, Matrix-Scanner64, Output-Module16, MIDI scanner, MIDI vstup, MIDI výstup, varhanní MIDI",
     "MIDI moduly pro stavbu digitálních varhan: Hall-Scanner64, Input-Module16, Matrix-Scanner64, Output-Module16. Wi-Fi konfigurace, USB-MIDI, High-Speed Analog MIDI Bus.",
     "midi-modules.htm", "midi-modules-en.htm"),

    ("about.htm", "cs",
     "O mně | Varhany Mlnařík",
     "O mně",
     "about",
     "varhany, digitální varhany, MIDI, jakub mlnařík, smartorgan",
     "Příběh za projektem Smartorgan",
     "about.htm", "about-en.htm"),

    # ── English pages ──
    ("index-en.html", "en",
     "Organ Mlnarik",
     "Home",
     "index",
     "digital organ, MIDI, pedalboards, consoles, hauptwerk",
     "digital organ, MIDI, pedalboards, consoles, hauptwerk",
     "index.html", "index-en.html"),

    ("keyboards-en.htm", "en",
     "Organ Keyboards | Kinetic Keyboards with Druckpunkt",
     "Organ Keyboards",
     "keyboards",
     "organ keyboard, kinetic keyboard, Druckpunkt, MIDI keyboard, organ manual, hall sensors",
     "Mechanical organ keyboards with adjustable Druckpunkt and kinetic feel. 64 keys, wooden keys, aluminium frame, MIDI output.",
     "keyboards.htm", "keyboards-en.htm"),

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

    ("midi-modules-en.htm", "en",
     "MIDI Modules for Digital Organs | Hall-Scanner64, Input-Module16, Matrix-Scanner64, Output-Module16",
     "MIDI Modules",
     "midi",
     "MIDI modules, Hall-Scanner64, Input-Module16, Matrix-Scanner64, Output-Module16, MIDI scanner, MIDI input, MIDI output, organ MIDI",
     "MIDI modules for building digital organs: Hall-Scanner64, Input-Module16, Matrix-Scanner64, Output-Module16. Wi-Fi configuration, USB-MIDI, High-Speed Analog MIDI Bus.",
     "midi-modules.htm", "midi-modules-en.htm"),

    ("about-en.htm", "en",
     "About | Organ Mlnarik",
     "About — my story",
     "about",
     "organ building, MIDI, Cecilia, smartorgan, jakub mlnarik, digital organ",
     "The story behind Smartorgan — from organ builder to software developer and back",
     "about.htm", "about-en.htm"),
]


# ── Build ──────────────────────────────────────────────────────────────────

def build():
    # Ensure output directory (current dir)
    out_dir = "."
    img_dir = os.path.join(out_dir, "img")

    for filename, lang, title, h1, active, keywords, description, cz_href, en_href in PAGES:
        # Read content snippet
        content_file = os.path.join("content", filename)
        if not os.path.exists(content_file):
            print(f"⚠  Missing content file: {content_file}")
            continue

        with open(content_file, "r", encoding="utf-8") as f:
            content = f.read().rstrip()

        # Process images: generate thumbnails, add loading="lazy"
        content = process_content_images(content, img_dir)

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
            active_keyboards=active_class("keyboards", active),
            active_cecilia=active_class("cecilia", active),
            active_midi=active_class("midi", active),
            active_organ=active_class("organ", active),
            active_services=active_class("services", active),
            active_about=active_class("about", active),
            active_contact=active_class("contact", active),
        )

        out_path = os.path.join(out_dir, filename)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
            f.write("\n")

        print(f"✓  Generated {out_path}")


if __name__ == "__main__":
    build()
