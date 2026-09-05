#!/usr/bin/env python3
"""
Static site generator for smartorgan.eu.

Usage:  python3 build.py

Content lives in content/ — just the <div class="text"> interior.
Metadata (title, h1, active page, keywords, description, flag links)
is defined in the PAGES list below.

Edit content or metadata, then run build.py to regenerate all HTML files.
"""

import json
import os
import re
import shutil
from datetime import datetime

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

  <!-- Canonical URL -->
  <link rel="canonical" href="{canonical_url}">

  <!-- hreflang alternates -->
  <link rel="alternate" hreflang="cs" href="{base_url}/{cz_href}">
  <link rel="alternate" hreflang="en" href="{base_url}/{en_href}">
  <link rel="alternate" hreflang="de" href="{base_url}/{de_href}">
  <link rel="alternate" hreflang="nl" href="{base_url}/{nl_href}">
  <meta property="og:site_name" content="Smartorgan / Varhany Mlnařík">

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{og_title}">
  <meta name="twitter:description" content="{og_description}">

  <!-- JSON-LD Structured Data -->
  <script type="application/ld+json">
{json_ld}
  </script>
</head>

<body>
<div id="main-frame">
  <div id="header">
    <div id="lang-bar">
      <a href="{cz_href}" class="lang-switch" hreflang="cs">CS</a>
      <a href="{en_href}" class="lang-switch" hreflang="en">EN</a>
      <a href="{de_href}" class="lang-switch" hreflang="de">DE</a>
      <a href="{nl_href}" class="lang-switch" hreflang="nl">NL</a>
    </div>
    <div class="header-top">
      <div id="logo"><a href="index-cz.html"><img src="img/logo-transparent.png" alt="Smartorgan — digitální varhany, klaviatury a MIDI moduly" width="100"></a></div>
      <div id="top-menu">
        <a href="index-cz.html"{active_index}>Domů</a>
        <a href="midi-modules-cz.htm"{active_midi}>MIDI</a>
        <a href="keyboards-cz.htm"{active_keyboards}>Klaviatury</a>
        <a href="organ-cz.htm"{active_organ}>Varhany</a>
        <a href="services-cz.htm"{active_services}>Služby</a>
        <a href="cecilia-cz.htm"{active_cecilia}>Cecilia</a>
        <a href="about-cz.htm"{active_about}>O mně</a>
        <a href="contact-cz.htm"{active_contact}>Kontakt</a>
      </div>
    </div>
  </div>

  <div id="content">
    <div class="text">

{content}

    </div>
  </div>

  <div id="footer">
    <div class="footer-inner">
      <span class="footer-copy">&copy; 2026 smartorgan.eu</span>
      <span class="footer-sep">&middot;</span>
      <span class="footer-author">Created by Jakub Mlnarik</span>
    </div>
  </div>
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

  <!-- Canonical URL -->
  <link rel="canonical" href="{canonical_url}">

  <!-- hreflang alternates -->
  <link rel="alternate" hreflang="cs" href="{base_url}/{cz_href}">
  <link rel="alternate" hreflang="en" href="{base_url}/{en_href}">
  <link rel="alternate" hreflang="de" href="{base_url}/{de_href}">
  <link rel="alternate" hreflang="nl" href="{base_url}/{nl_href}">
  <meta property="og:site_name" content="Smartorgan / Mlnarik Organ">

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{og_title}">
  <meta name="twitter:description" content="{og_description}">

  <!-- JSON-LD Structured Data -->
  <script type="application/ld+json">
{json_ld}
  </script>
</head>

<body>
<div id="main-frame">
  <div id="header">
    <div id="lang-bar">
      <a href="{cz_href}" class="lang-switch" hreflang="cs">CS</a>
      <a href="{en_href}" class="lang-switch" hreflang="en">EN</a>
      <a href="{de_href}" class="lang-switch" hreflang="de">DE</a>
      <a href="{nl_href}" class="lang-switch" hreflang="nl">NL</a>
    </div>
    <div class="header-top">
      <div id="logo"><a href="index.html"><img src="img/logo-transparent.png" alt="Smartorgan — digital organs, organ keyboards and MIDI modules" width="100"></a></div>
      <div id="top-menu">
        <a href="index.html"{active_index}>Home</a>
        <a href="midi-modules.htm"{active_midi}>MIDI</a>
        <a href="keyboards.htm"{active_keyboards}>Keyboards</a>
        <a href="organ.htm"{active_organ}>Organs</a>
        <a href="services.htm"{active_services}>Services</a>
        <a href="cecilia.htm"{active_cecilia}>Cecilia</a>
        <a href="about.htm"{active_about}>About</a>
        <a href="contact.htm"{active_contact}>Contact</a>
      </div>
    </div>
  </div>

  <div id="content">
    <div class="text">

{content}

    </div>
  </div>

  <div id="footer">
    <div class="footer-inner">
      <span class="footer-copy">&copy; 2026 smartorgan.eu</span>
      <span class="footer-sep">&middot;</span>
      <span class="footer-author">Created by Jakub Mlnarik</span>
    </div>
  </div>
</div>

</body>
</html>
"""

TEMPLATE_DE = """<!DOCTYPE html>
<html lang="de">

<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <link rel="stylesheet" href="styles.css">
  <meta name="keywords" content="{keywords}">
  <meta name="description" content="{description}">

  <!-- Canonical URL -->
  <link rel="canonical" href="{canonical_url}">

  <!-- hreflang alternates -->
  <link rel="alternate" hreflang="cs" href="{base_url}/{cz_href}">
  <link rel="alternate" hreflang="en" href="{base_url}/{en_href}">
  <link rel="alternate" hreflang="de" href="{base_url}/{de_href}">
  <link rel="alternate" hreflang="nl" href="{base_url}/{nl_href}">

  <!-- Open Graph -->
  <meta property="og:type" content="website">
  <meta property="og:title" content="{og_title}">
  <meta property="og:description" content="{og_description}">
  <meta property="og:url" content="{canonical_url}">
  <meta property="og:image" content="{og_image}">
  <meta property="og:locale" content="de_DE">
  <meta property="og:site_name" content="Smartorgan / Mlnarik Organ">

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{og_title}">
  <meta name="twitter:description" content="{og_description}">

  <!-- JSON-LD Structured Data -->
  <script type="application/ld+json">
{json_ld}
  </script>
</head>

<body>
<div id="main-frame">
  <div id="header">
    <div id="lang-bar">
      <a href="{cz_href}" class="lang-switch" hreflang="cs">CS</a>
      <a href="{en_href}" class="lang-switch" hreflang="en">EN</a>
      <a href="{de_href}" class="lang-switch" hreflang="de">DE</a>
      <a href="{nl_href}" class="lang-switch" hreflang="nl">NL</a>
    </div>
    <div class="header-top">
      <div id="logo"><a href="index-de.html"><img src="img/logo-transparent.png" alt="Smartorgan — digitale Orgeln, Orgelkeyboards und MIDI-Module" width="100"></a></div>
      <div id="top-menu">
        <a href="index-de.html"{active_index}>Startseite</a>
        <a href="midi-modules-de.htm"{active_midi}>MIDI</a>
        <a href="keyboards-de.htm"{active_keyboards}>Keyboards</a>
        <a href="organ-de.htm"{active_organ}>Orgeln</a>
        <a href="services-de.htm"{active_services}>Dienstleistungen</a>
        <a href="cecilia-de.htm"{active_cecilia}>Cecilia</a>
        <a href="about-de.htm"{active_about}>Über mich</a>
        <a href="contact-de.htm"{active_contact}>Kontakt</a>
      </div>
    </div>
  </div>

  <div id="content">
    <div class="text">

{content}

    </div>
  </div>

  <div id="footer">
    <div class="footer-inner">
      <span class="footer-copy">&copy; 2026 smartorgan.eu</span>
      <span class="footer-sep">&middot;</span>
      <span class="footer-author">Created by Jakub Mlnarik</span>
    </div>
  </div>
</div>

</body>
</html>
"""

TEMPLATE_NL = """<!DOCTYPE html>
<html lang="nl">

<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <link rel="stylesheet" href="styles.css">
  <meta name="keywords" content="{keywords}">
  <meta name="description" content="{description}">

  <!-- Canonical URL -->
  <link rel="canonical" href="{canonical_url}">

  <!-- hreflang alternates -->
  <link rel="alternate" hreflang="cs" href="{base_url}/{cz_href}">
  <link rel="alternate" hreflang="en" href="{base_url}/{en_href}">
  <link rel="alternate" hreflang="de" href="{base_url}/{de_href}">
  <link rel="alternate" hreflang="nl" href="{base_url}/{nl_href}">

  <!-- Open Graph -->
  <meta property="og:type" content="website">
  <meta property="og:title" content="{og_title}">
  <meta property="og:description" content="{og_description}">
  <meta property="og:url" content="{canonical_url}">
  <meta property="og:image" content="{og_image}">
  <meta property="og:locale" content="nl_NL">
  <meta property="og:site_name" content="Smartorgan / Mlnarik Organ">

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{og_title}">
  <meta name="twitter:description" content="{og_description}">

  <!-- JSON-LD Structured Data -->
  <script type="application/ld+json">
{json_ld}
  </script>
</head>

<body>
<div id="main-frame">
  <div id="header">
    <div id="lang-bar">
      <a href="{cz_href}" class="lang-switch" hreflang="cs">CS</a>
      <a href="{en_href}" class="lang-switch" hreflang="en">EN</a>
      <a href="{de_href}" class="lang-switch" hreflang="de">DE</a>
      <a href="{nl_href}" class="lang-switch" hreflang="nl">NL</a>
    </div>
    <div class="header-top">
      <div id="logo"><a href="index-nl.html"><img src="img/logo-transparent.png" alt="Smartorgan — digitale orgels, orgelkeyboards en MIDI-modules" width="100"></a></div>
      <div id="top-menu">
        <a href="index-nl.html"{active_index}>Home</a>
        <a href="midi-modules-nl.htm"{active_midi}>MIDI</a>
        <a href="keyboards-nl.htm"{active_keyboards}>Keyboards</a>
        <a href="organ-nl.htm"{active_organ}>Orgels</a>
        <a href="services-nl.htm"{active_services}>Diensten</a>
        <a href="cecilia-nl.htm"{active_cecilia}>Cecilia</a>
        <a href="about-nl.htm"{active_about}>Over mij</a>
        <a href="contact-nl.htm"{active_contact}>Contact</a>
      </div>
    </div>
  </div>

  <div id="content">
    <div class="text">

{content}

    </div>
  </div>

  <div id="footer">
    <div class="footer-inner">
      <span class="footer-copy">&copy; 2026 smartorgan.eu</span>
      <span class="footer-sep">&middot;</span>
      <span class="footer-author">Created by Jakub Mlnarik</span>
    </div>
  </div>
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


# ── JSON-LD Structured Data ────────────────────────────────────────────────

def generate_json_ld(page_id, lang, title, description, canonical_url, base_url, filename):
    """Generate JSON-LD structured data block for the page."""
    org_names = {
        "cs": "Varhany Mlnařík / Smartorgan",
        "en": "Mlnarik Organ / Smartorgan",
        "de": "Mlnarik Organ / Smartorgan",
        "nl": "Mlnarik Organ / Smartorgan",
    }
    org_name = org_names.get(lang, "Smartorgan")

    breadcrumb_home = {
        "cs": "Domů",
        "en": "Home",
        "de": "Startseite",
        "nl": "Home",
    }
    breadcrumb_items = [
        {"@type": "ListItem", "position": 1, "name": breadcrumb_home.get(lang, "Home"), "item": base_url}
    ]

    page_names = {
        "index":     ("Domů", "Home", "Startseite", "Home"),
        "keyboards": ("Klaviatury", "Keyboards", "Keyboards", "Keyboards"),
        "midi":      ("MIDI moduly", "MIDI Modules", "MIDI-Module", "MIDI-modules"),
        "organ":     ("Varhany", "Organs", "Orgeln", "Orgels"),
        "cecilia":   ("Cecilia", "Cecilia", "Cecilia", "Cecilia"),
        "services":  ("Služby", "Services", "Dienstleistungen", "Diensten"),
        "about":     ("O mně", "About", "Über mich", "Over mij"),
        "contact":   ("Kontakt", "Contact", "Kontakt", "Contact"),
    }

    lang_idx = {"cs": 0, "en": 1, "de": 2, "nl": 3}
    idx = lang_idx.get(lang, 1)
    if page_id in page_names:
        breadcrumb_items.append({
            "@type": "ListItem", "position": 2,
            "name": page_names[page_id][idx],
            "item": canonical_url
        })

    graph = [
        {
            "@context": "https://schema.org",
            "@type": "Organization",
            "@id": f"{base_url}/#organization",
            "name": org_name,
            "url": base_url,
            "description": description,
            "contactPoint": {
                "@type": "ContactPoint",
                "contactType": "customer service",
                "availableLanguage": ["Czech", "English", "German", "Dutch"]
            }
        },
        {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "@id": f"{base_url}/#website",
            "url": base_url,
            "name": org_name,
            "description": description,
            "publisher": {"@id": f"{base_url}/#organization"}
        },
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "@id": f"{canonical_url}#breadcrumb",
            "itemListElement": breadcrumb_items
        }
    ]

    # Add Product schema for product pages
    product_names = {
        "keyboards": {
            "cs": "Kinetická varhanní klaviatura",
            "en": "Kinetic Organ Keyboard",
            "de": "Kinetisches Orgelkeyboard",
            "nl": "Kinetisch orgelkeyboard",
        },
        "midi": {
            "cs": "MIDI moduly pro digitální varhany",
            "en": "MIDI Modules for Digital Organs",
            "de": "MIDI-Module für digitale Orgeln",
            "nl": "MIDI-modules voor digitale orgels",
        },
    }

    if page_id == "keyboards":
        graph.append({
            "@context": "https://schema.org",
            "@type": "Product",
            "name": product_names["keyboards"].get(lang, product_names["keyboards"]["en"]),
            "description": description,
            "brand": {"@type": "Brand", "name": "Mlnarik Organ"},
            "offers": {
                "@type": "Offer",
                "price": "1820",
                "priceCurrency": "EUR",
                "availability": "https://schema.org/InStock"
            }
        })
    elif page_id == "midi":
        graph.append({
            "@context": "https://schema.org",
            "@type": "Product",
            "name": product_names["midi"].get(lang, product_names["midi"]["en"]),
            "description": description,
            "brand": {"@type": "Brand", "name": "Mlnarik Organ"},
            "offers": {
                "@type": "AggregateOffer",
                "priceCurrency": "EUR",
                "lowPrice": "70",
                "highPrice": "95",
                "availability": "https://schema.org/InStock"
            }
        })

    return json.dumps(graph, ensure_ascii=False, indent=2)


# ── Page definitions ───────────────────────────────────────────────────────
# Each entry: (filename, lang, title, h1, active_page, keywords, description, cz_href, en_href, de_href, nl_href)

PAGES = [
    # ── Czech pages (with -cz suffix) ──
    ("index-cz.html", "cs",
     "Varhany Mlnařík | Digitální varhany, klaviatury a MIDI moduly pro Hauptwerk",
     "Domů",
     "index",
     "digitální varhany, varhany, cvičení, MIDI, pedálnice, hrací stoly, hauptwerk, grandorgue, opravy varhan, ladění, varhanní klaviatura",
     "Výroba digitálních varhan, MIDI modulů a unikátních kinetických klaviatur s Druckpunktem. Pedálnice, hrací stoly, cvičné varhany pro Hauptwerk a GrandOrgue.",
     "index-cz.html", "index.html", "index-de.html", "index-nl.html"),

    ("keyboards-cz.htm", "cs",
     "Varhanní klaviatury s kinetickým projevem | MIDI klaviatury pro Hauptwerk",
     "Varhanní klaviatury",
     "keyboards",
     "varhanní klaviatura, kinetická klaviatura, Druckpunkt, MIDI klaviatura, varhanní manuál, hall senzory, hauptwerk klaviatura",
     "Mechanické varhanní klaviatury s nastavitelným Druckpunktem a kinetickým projevem. 61 kláves, dřevěné klávesy, hliníkový rám, MIDI výstup. Ideální pro Hauptwerk a digitální varhany.",
     "keyboards-cz.htm", "keyboards.htm", "keyboards-de.htm", "keyboards-nl.htm"),

    ("cecilia-cz.htm", "cs",
     "Cecilia — zvukový systém pro digitální varhany | MIDI expandér",
     "Zvukový systém Cecilia",
     "cecilia",
     "cecilia, MIDI, expandér, varhanní modul, zvukový modul, digitální varhany",
     "Cecilia — výkonný zvukový systém a MIDI expandér pro stavbu digitálních varhan. Ideální doplněk k Hauptwerk a GrandOrgue.",
     "cecilia-cz.htm", "cecilia.htm", "cecilia-de.htm", "cecilia-nl.htm"),

    ("organ-cz.htm", "cs",
     "Digitální varhany na míru | Stavba, opravy, Hauptwerk konzole",
     "Varhany — díly i kompletní nástroje",
     "organ",
     "digitální varhany, varhany, cvičení, MIDI, pedálnice, hrací stoly, hauptwerk, grandorgue, opravy varhan, ladění, varhanní konzole",
     "Stavba digitálních varhan na míru, MIDI konzolí a pedálnic. Kompletní nástroje i jednotlivé díly. Specializace na Hauptwerk a samplové technologie.",
     "organ-cz.htm", "organ.htm", "organ-de.htm", "organ-nl.htm"),

    ("services-cz.htm", "cs",
     "Služby | Opravy varhan, ladění, poradenství",
     "Služby",
     "services",
     "digitální varhany, varhany, cvičení, MIDI, pedálnice, hrací stoly, hauptwerk, grandorgue, opravy varhan, ladění, poradenství",
     "Nabízíme opravy varhan, ladění, poradenství při stavbě digitálních varhan a konzolí pro Hauptwerk. Servis MIDI modulů a klaviatur.",
     "services-cz.htm", "services.htm", "services-de.htm", "services-nl.htm"),

    ("contact-cz.htm", "cs",
     "Kontakt | Varhany Mlnařík — digitální varhany a MIDI",
     "Kontakt",
     "contact",
     "digitální varhany, varhany, MIDI, kontakt, jakub mlnařík, smartorgan",
     "Kontaktujte nás pro objednávky digitálních varhan, MIDI modulů, klaviatur nebo konzolí pro Hauptwerk.",
     "contact-cz.htm", "contact.htm", "contact-de.htm", "contact-nl.htm"),

    ("midi-modules-cz.htm", "cs",
     "MIDI moduly pro digitální varhany | Hall-Scanner64, Matrix-Scanner64 a další",
     "MIDI moduly",
     "midi",
     "MIDI moduly, Hall-Scanner64, Input-Module16, Matrix-Scanner64, Output-Module16, MIDI scanner, MIDI vstup, MIDI výstup, varhanní MIDI, hauptwerk MIDI",
     "MIDI moduly pro stavbu digitálních varhan: Hall-Scanner64, Input-Module16, Matrix-Scanner64, Output-Module16. Wi-Fi konfigurace, USB-MIDI, High-Speed Analog MIDI Bus. Ideální pro Hauptwerk projekty.",
     "midi-modules-cz.htm", "midi-modules.htm", "midi-modules-de.htm", "midi-modules-nl.htm"),

    ("about-cz.htm", "cs",
     "O mně | Jakub Mlnařík — digitální varhany a MIDI technologie",
     "O mně",
     "about",
     "varhany, digitální varhany, MIDI, jakub mlnařík, smartorgan, hauptwerk",
     "Příběh za projektem Smartorgan — od varhanáře k vývoji MIDI modulů a kinetických klaviatur pro digitální varhany a Hauptwerk.",
     "about-cz.htm", "about.htm", "about-de.htm", "about-nl.htm"),

    # ── English pages (default, no suffix) ──
    ("index.html", "en",
     "Smartorgan | Digital Organs, Organ Keyboards & MIDI Modules for Hauptwerk",
     "Home",
     "index",
     "digital organ, MIDI, pedalboards, consoles, hauptwerk, organ keyboard, MIDI modules, grandorgue",
     "Digital organs, organ keyboards with kinetic touch, and MIDI modules for Hauptwerk. Custom consoles, pedalboards, and practice organs for organ builders.",
     "index-cz.html", "index.html", "index-de.html", "index-nl.html"),

    ("keyboards.htm", "en",
     "Organ Keyboards with Kinetic Touch | MIDI Keyboards for Hauptwerk & Digital Organs",
     "Organ Keyboards",
     "keyboards",
     "organ keyboard, kinetic keyboard, Druckpunkt, MIDI keyboard, organ manual, hall sensors, hauptwerk keyboard, digital organ keyboard",
     "Mechanical organ keyboards with adjustable Druckpunkt and kinetic feel. 61 keys, wooden keys, aluminium frame, MIDI output. Perfect for Hauptwerk and digital organ consoles.",
     "keyboards-cz.htm", "keyboards.htm", "keyboards-de.htm", "keyboards-nl.htm"),

    ("cecilia.htm", "en",
     "Cecilia — Sound System for Digital Organs | MIDI Expander & Organ Module",
     "Organ sound system Cecilia",
     "cecilia",
     "cecilia, MIDI, expander, organ module, organ unit, sound engine, digital organ sound",
     "Cecilia — a powerful sound system and MIDI expander for building digital organs. A perfect companion for Hauptwerk and GrandOrgue setups.",
     "cecilia-cz.htm", "cecilia.htm", "cecilia-de.htm", "cecilia-nl.htm"),

    ("organ.htm", "en",
     "Digital Organs & MIDI Consoles for Hauptwerk | Custom Organ Building",
     "Organs — parts and complete instruments",
     "organ",
     "digital organ, MIDI, pedalboards, consoles, hauptwerk, grandorgue, organ console, custom organ",
     "Custom digital organs, MIDI consoles, and pedalboards for Hauptwerk. Complete instruments and individual components. Sampling technology for authentic pipe organ sound.",
     "organ-cz.htm", "organ.htm", "organ-de.htm", "organ-nl.htm"),

    ("services.htm", "en",
     "Services | Organ Repair, Maintenance & Consulting for Digital Organs",
     "Services",
     "services",
     "organ repair, organ maintenance, digital organ service, hauptwerk consulting, MIDI console service",
     "Organ repair, tuning, maintenance, and consulting for digital organ projects. Specialized in Hauptwerk consoles, MIDI modules, and organ keyboard installations.",
     "services-cz.htm", "services.htm", "services-de.htm", "services-nl.htm"),

    ("contact.htm", "en",
     "Contact | Mlnarik Organ — Digital Organs, Keyboards & MIDI Modules",
     "Contact",
     "contact",
     "digital organ, MIDI, pedalboards, consoles, hauptwerk, contact, organ builder",
     "Get in touch for custom digital organs, organ keyboards, MIDI modules, or Hauptwerk console projects. We provide material and technical support.",
     "contact-cz.htm", "contact.htm", "contact-de.htm", "contact-nl.htm"),

    ("midi-modules.htm", "en",
     "MIDI Modules for Digital Organs | Hall-Scanner64, Matrix-Scanner64 & More",
     "MIDI Modules",
     "midi",
     "MIDI modules, Hall-Scanner64, Input-Module16, Matrix-Scanner64, Output-Module16, MIDI scanner, MIDI input, MIDI output, organ MIDI, hauptwerk MIDI",
     "MIDI modules for building digital organs: Hall-Scanner64, Input-Module16, Matrix-Scanner64, Output-Module16. Wi-Fi configuration, USB-MIDI, High-Speed Analog MIDI Bus. Ideal for Hauptwerk projects.",
     "midi-modules-cz.htm", "midi-modules.htm", "midi-modules-de.htm", "midi-modules-nl.htm"),

    ("about.htm", "en",
     "About | Jakub Mlnarik — Digital Organs, MIDI Technology & Organ Building",
     "About — my story",
     "about",
     "organ building, MIDI, Cecilia, smartorgan, jakub mlnarik, digital organ, hauptwerk",
     "The story behind Smartorgan — from organ builder to MIDI module developer and kinetic keyboard designer for digital organs and Hauptwerk.",
     "about-cz.htm", "about.htm", "about-de.htm", "about-nl.htm"),

    # ── German pages (with -de suffix) ──
    ("index-de.html", "de",
     "Smartorgan | Digitale Orgeln, Orgelkeyboards & MIDI-Module für Hauptwerk",
     "Startseite",
     "index",
     "digitale Orgel, MIDI, Pedalboards, Spieltische, Hauptwerk, Orgelkeyboard, MIDI-Module, GrandOrgue",
     "Digitale Orgeln, Orgelkeyboards mit kinetischer Ansprache und MIDI-Module für Hauptwerk. Kundenspezifische Spieltische, Pedalboards und Übungsorgeln für Orgelbauer.",
     "index-cz.html", "index.html", "index-de.html", "index-nl.html"),

    ("keyboards-de.htm", "de",
     "Orgelkeyboards mit kinetischer Ansprache | MIDI-Keyboards für Hauptwerk & digitale Orgeln",
     "Orgelkeyboards",
     "keyboards",
     "Orgelkeyboard, kinetisches Keyboard, Druckpunkt, MIDI-Keyboard, Orgelmanual, Hall-Sensoren, Hauptwerk-Keyboard, digitales Orgelkeyboard",
     "Mechanische Orgelkeyboards mit einstellbarem Druckpunkt und kinetischem Gefühl. 61 Tasten, Holztasten, Aluminiumrahmen, MIDI-Ausgang. Perfekt für Hauptwerk und digitale Orgelspieltische.",
     "keyboards-cz.htm", "keyboards.htm", "keyboards-de.htm", "keyboards-nl.htm"),

    ("cecilia-de.htm", "de",
     "Cecilia — Klangsystem für digitale Orgeln | MIDI-Expander & Orgelmodul",
     "Orgelklangsystem Cecilia",
     "cecilia",
     "Cecilia, MIDI, Expander, Orgelmodul, Orgeleinheit, Klangengine, digitaler Orgelklang",
     "Cecilia — ein leistungsstarkes Klangsystem und MIDI-Expander für den Bau digitaler Orgeln. Ein perfekter Begleiter für Hauptwerk- und GrandOrgue-Setups.",
     "cecilia-cz.htm", "cecilia.htm", "cecilia-de.htm", "cecilia-nl.htm"),

    ("organ-de.htm", "de",
     "Digitale Orgeln & MIDI-Spieltische für Hauptwerk | Kundenspezifischer Orgelbau",
     "Orgeln — Teile und komplette Instrumente",
     "organ",
     "digitale Orgel, MIDI, Pedalboards, Spieltische, Hauptwerk, GrandOrgue, Orgelspieltisch, kundenspezifische Orgel",
     "Kundenspezifische digitale Orgeln, MIDI-Spieltische und Pedalboards für Hauptwerk. Komplette Instrumente und Einzelkomponenten. Sampling-Technologie für authentischen Pfeifenorgelklang.",
     "organ-cz.htm", "organ.htm", "organ-de.htm", "organ-nl.htm"),

    ("services-de.htm", "de",
     "Dienstleistungen | Orgelreparatur, Wartung & Beratung für digitale Orgeln",
     "Dienstleistungen",
     "services",
     "Orgelreparatur, Orgelwartung, digitaler Orgelservice, Hauptwerk-Beratung, MIDI-Spieltisch-Service",
     "Orgelreparatur, Stimmung, Wartung und Beratung für digitale Orgelprojekte. Spezialisiert auf Hauptwerk-Spieltische, MIDI-Module und Orgelkeyboard-Installationen.",
     "services-cz.htm", "services.htm", "services-de.htm", "services-nl.htm"),

    ("contact-de.htm", "de",
     "Kontakt | Mlnarik Organ — Digitale Orgeln, Keyboards & MIDI-Module",
     "Kontakt",
     "contact",
     "digitale Orgel, MIDI, Pedalboards, Spieltische, Hauptwerk, Kontakt, Orgelbauer",
     "Nehmen Sie Kontakt auf für kundenspezifische digitale Orgeln, Orgelkeyboards, MIDI-Module oder Hauptwerk-Spieltischprojekte. Wir bieten materielle und technische Unterstützung.",
     "contact-cz.htm", "contact.htm", "contact-de.htm", "contact-nl.htm"),

    ("midi-modules-de.htm", "de",
     "MIDI-Module für digitale Orgeln | Hall-Scanner64, Matrix-Scanner64 & mehr",
     "MIDI-Module",
     "midi",
     "MIDI-Module, Hall-Scanner64, Input-Module16, Matrix-Scanner64, Output-Module16, MIDI-Scanner, MIDI-Eingang, MIDI-Ausgang, Orgel-MIDI, Hauptwerk-MIDI",
     "MIDI-Module für den Bau digitaler Orgeln: Hall-Scanner64, Input-Module16, Matrix-Scanner64, Output-Module16. Wi-Fi-Konfiguration, USB-MIDI, High-Speed Analog MIDI Bus. Ideal für Hauptwerk-Projekte.",
     "midi-modules-cz.htm", "midi-modules.htm", "midi-modules-de.htm", "midi-modules-nl.htm"),

    ("about-de.htm", "de",
     "Über mich | Jakub Mlnarik — Digitale Orgeln, MIDI-Technologie & Orgelbau",
     "Über mich — meine Geschichte",
     "about",
     "Orgelbau, MIDI, Cecilia, Smartorgan, Jakub Mlnarik, digitale Orgel, Hauptwerk",
     "Die Geschichte hinter Smartorgan — vom Orgelbauer zum MIDI-Modul-Entwickler und Designer kinetischer Keyboards für digitale Orgeln und Hauptwerk.",
     "about-cz.htm", "about.htm", "about-de.htm", "about-nl.htm"),

    # ── Dutch pages (with -nl suffix) ──
    ("index-nl.html", "nl",
     "Smartorgan | Digitale Orgels, Orgelkeyboards & MIDI-modules voor Hauptwerk",
     "Home",
     "index",
     "digitaal orgel, MIDI, pedaalborden, speeltafels, Hauptwerk, orgelkeyboard, MIDI-modules, GrandOrgue",
     "Digitale orgels, orgelkeyboards met kinetische aanslag en MIDI-modules voor Hauptwerk. Op maat gemaakte speeltafels, pedaalborden en oefenorgels voor orgelbouwers.",
     "index-cz.html", "index.html", "index-de.html", "index-nl.html"),

    ("keyboards-nl.htm", "nl",
     "Orgelkeyboards met kinetische aanslag | MIDI-keyboards voor Hauptwerk & digitale orgels",
     "Orgelkeyboards",
     "keyboards",
     "orgelkeyboard, kinetisch keyboard, Druckpunkt, MIDI-keyboard, orgelmanuaal, Hall-sensoren, Hauptwerk-keyboard, digitaal orgelkeyboard",
     "Mechanische orgelkeyboards met instelbare Druckpunkt en kinetisch gevoel. 61 toetsen, houten toetsen, aluminium frame, MIDI-uitgang. Perfect voor Hauptwerk en digitale orgelspeeltafels.",
     "keyboards-cz.htm", "keyboards.htm", "keyboards-de.htm", "keyboards-nl.htm"),

    ("cecilia-nl.htm", "nl",
     "Cecilia — Geluidssysteem voor digitale orgels | MIDI-expander & orgelmodule",
     "Orgelgeluidssysteem Cecilia",
     "cecilia",
     "Cecilia, MIDI, expander, orgelmodule, orgeleenheid, geluidsengine, digitale orgelgeluid",
     "Cecilia — een krachtig geluidssysteem en MIDI-expander voor het bouwen van digitale orgels. Een perfecte aanvulling voor Hauptwerk- en GrandOrgue-opstellingen.",
     "cecilia-cz.htm", "cecilia.htm", "cecilia-de.htm", "cecilia-nl.htm"),

    ("organ-nl.htm", "nl",
     "Digitale orgels & MIDI-speeltafels voor Hauptwerk | Op maat gemaakt orgelbouw",
     "Orgels — onderdelen en complete instrumenten",
     "organ",
     "digitaal orgel, MIDI, pedaalborden, speeltafels, Hauptwerk, GrandOrgue, orgelspeeltafel, op maat gemaakt orgel",
     "Op maat gemaakte digitale orgels, MIDI-speeltafels en pedaalborden voor Hauptwerk. Complete instrumenten en losse componenten. Sampling-technologie voor authentiek pijporgelgeluid.",
     "organ-cz.htm", "organ.htm", "organ-de.htm", "organ-nl.htm"),

    ("services-nl.htm", "nl",
     "Diensten | Orgelreparatie, onderhoud & advies voor digitale orgels",
     "Diensten",
     "services",
     "orgelreparatie, orgelonderhoud, digitale orgelservice, Hauptwerk-advies, MIDI-speeltafel-service",
     "Orgelreparatie, stemming, onderhoud en advies voor digitale orgelprojecten. Gespecialiseerd in Hauptwerk-speeltafels, MIDI-modules en orgelkeyboard-installaties.",
     "services-cz.htm", "services.htm", "services-de.htm", "services-nl.htm"),

    ("contact-nl.htm", "nl",
     "Contact | Mlnarik Organ — Digitale orgels, Keyboards & MIDI-modules",
     "Contact",
     "contact",
     "digitaal orgel, MIDI, pedaalborden, speeltafels, Hauptwerk, contact, orgelbouwer",
     "Neem contact op voor op maat gemaakte digitale orgels, orgelkeyboards, MIDI-modules of Hauptwerk-speeltafelprojecten. Wij bieden materiële en technische ondersteuning.",
     "contact-cz.htm", "contact.htm", "contact-de.htm", "contact-nl.htm"),

    ("midi-modules-nl.htm", "nl",
     "MIDI-modules voor digitale orgels | Hall-Scanner64, Matrix-Scanner64 & meer",
     "MIDI-modules",
     "midi",
     "MIDI-modules, Hall-Scanner64, Input-Module16, Matrix-Scanner64, Output-Module16, MIDI-scanner, MIDI-ingang, MIDI-uitgang, orgel-MIDI, Hauptwerk-MIDI",
     "MIDI-modules voor het bouwen van digitale orgels: Hall-Scanner64, Input-Module16, Matrix-Scanner64, Output-Module16. Wi-Fi-configuratie, USB-MIDI, High-Speed Analog MIDI Bus. Ideaal voor Hauptwerk-projecten.",
     "midi-modules-cz.htm", "midi-modules.htm", "midi-modules-de.htm", "midi-modules-nl.htm"),

    ("about-nl.htm", "nl",
     "Over mij | Jakub Mlnarik — Digitale orgels, MIDI-technologie & orgelbouw",
     "Over mij — mijn verhaal",
     "about",
     "orgelbouw, MIDI, Cecilia, Smartorgan, Jakub Mlnarik, digitale orgel, Hauptwerk",
     "Het verhaal achter Smartorgan — van orgelbouwer tot MIDI-module-ontwikkelaar en ontwerper van kinetische keyboards voor digitale orgels en Hauptwerk.",
     "about-cz.htm", "about.htm", "about-de.htm", "about-nl.htm"),
]


# ── Sitemap ────────────────────────────────────────────────────────────────

SITEMAP_PRIORITIES = {
    "index": "1.0",
    "organ": "0.9",
    "keyboards": "0.8",
    "midi": "0.8",
    "cecilia": "0.8",
    "services": "0.6",
    "about": "0.5",
    "contact": "0.5",
}

SITEMAP_FREQUENCIES = {
    "index": "monthly",
    "organ": "monthly",
    "keyboards": "monthly",
    "midi": "monthly",
    "cecilia": "monthly",
    "services": "yearly",
    "about": "yearly",
    "contact": "yearly",
}


def generate_sitemap(pages, base_url, out_dir):
    """Generate sitemap.xml with hreflang annotations for CS/EN/DE/NL pages."""
    # Group pages by their active ID to pair language versions
    by_id: dict[str, list] = {}
    for entry in pages:
        filename, lang, title, h1, active, keywords, description, cz_href, en_href, de_href, nl_href = entry
        by_id.setdefault(active, []).append((filename, lang, cz_href, en_href, de_href, nl_href))

    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>\n')
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n')
    lines.append('        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n')

    for page_id, versions in by_id.items():
        for filename, lang, cz_href, en_href, de_href, nl_href in versions:
            content_file = os.path.join("content", filename)

            # lastmod from content file modification time
            lastmod = ""
            if os.path.exists(content_file):
                mtime = os.path.getmtime(content_file)
                lastmod = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")

            priority = SITEMAP_PRIORITIES.get(page_id, "0.5")
            changefreq = SITEMAP_FREQUENCIES.get(page_id, "monthly")
            url = f"{base_url}/{filename}"

            lines.append("  <url>\n")
            lines.append(f"    <loc>{url}</loc>\n")
            if lastmod:
                lines.append(f"    <lastmod>{lastmod}</lastmod>\n")
            lines.append(f"    <changefreq>{changefreq}</changefreq>\n")
            lines.append(f"    <priority>{priority}</priority>\n")
            lines.append(f'    <xhtml:link rel="alternate" hreflang="cs" href="{base_url}/{cz_href}" />\n')
            lines.append(f'    <xhtml:link rel="alternate" hreflang="en" href="{base_url}/{en_href}" />\n')
            lines.append(f'    <xhtml:link rel="alternate" hreflang="de" href="{base_url}/{de_href}" />\n')
            lines.append(f'    <xhtml:link rel="alternate" hreflang="nl" href="{base_url}/{nl_href}" />\n')
            lines.append("  </url>\n")

    lines.append('</urlset>\n')

    out_path = os.path.join(out_dir, "sitemap.xml")
    with open(out_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"✓  Generated {out_path}")


# ── Build ──────────────────────────────────────────────────────────────────

def build():
    # Ensure output directory (current dir)
    out_dir = "."
    img_dir = os.path.join(out_dir, "img")

    # Determine base URL from CNAME
    cname_file = os.path.join(out_dir, "CNAME")
    if os.path.exists(cname_file):
        with open(cname_file) as f:
            domain = f.read().strip()
    else:
        domain = "smartorgan.cz"
    base_url = f"https://{domain}"

    for filename, lang, title, h1, active, keywords, description, cz_href, en_href, de_href, nl_href in PAGES:
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
        templates = {"cs": TEMPLATE_CS, "en": TEMPLATE_EN, "de": TEMPLATE_DE, "nl": TEMPLATE_NL}
        template = templates.get(lang, TEMPLATE_EN)

        # Canonical URL for this page
        canonical_url = f"{base_url}/{filename}"

        # OG image (use the same for all pages — the logo)
        og_image = f"{base_url}/img/logo-transparent.png"

        # JSON-LD structured data
        json_ld_raw = generate_json_ld(active, lang, title, description, canonical_url, base_url, filename)
        # Indent each line with 2 extra spaces so it fits inside the <head>
        json_ld_indented = "\n".join("  " + line for line in json_ld_raw.split("\n"))

        # Build the HTML
        html = template.format(
            title=title,
            h1=h1,
            keywords=keywords,
            description=description,
            content=content,
            cz_href=cz_href,
            en_href=en_href,
            de_href=de_href,
            nl_href=nl_href,
            canonical_url=canonical_url,
            base_url=base_url,
            og_title=title,
            og_description=description,
            og_image=og_image,
            json_ld=json_ld_indented,
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

    # Generate sitemap.xml
    generate_sitemap(PAGES, base_url, out_dir)


if __name__ == "__main__":
    build()
