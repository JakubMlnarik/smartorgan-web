#!/usr/bin/env python3
"""
Static site generator for smartorgan.cz.

Usage:  python3 build.py

Content lives in content/{lang}/ — just the <div class="text"> interior.
Metadata (title, h1, active page, keywords, description)
is defined in the PAGES list below.

Edit content or metadata, then run build.py to regenerate all HTML files.
"""

import html
import json
import os
import re
import shutil
from datetime import datetime, timezone

try:
    from PIL import Image, ImageOps  # type: ignore[import-not-found]
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

    class _MissingPillow:
        LANCZOS = None

        @staticmethod
        def open(*args, **kwargs):
            raise RuntimeError("Pillow is not installed")

        @staticmethod
        def new(*args, **kwargs):
            raise RuntimeError("Pillow is not installed")

        @staticmethod
        def contain(*args, **kwargs):
            raise RuntimeError("Pillow is not installed")

    Image = _MissingPillow
    ImageOps = _MissingPillow
    print("⚠  Pillow not installed — thumbnails will not be generated.")
    print("   Install with: pip install Pillow")

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


def generate_favicon_assets(img_dir, out_dir):
    """Generate favicon assets from the logo image."""
    if not HAS_PILLOW:
        return

    source_path = os.path.join(img_dir, "logo-transparent.png")
    png_path = os.path.join(out_dir, "favicon.png")
    ico_path = os.path.join(out_dir, "favicon.ico")

    if not os.path.exists(source_path):
        print(f"   ⚠  Favicon source not found: {source_path}")
        return

    source_mtime = os.path.getmtime(source_path)
    if (
        os.path.exists(png_path)
        and os.path.exists(ico_path)
        and os.path.getmtime(png_path) >= source_mtime
        and os.path.getmtime(ico_path) >= source_mtime
    ):
        return

    logo = Image.open(source_path).convert("RGBA")
    canvas_size = 512
    fitted = ImageOps.contain(logo, (canvas_size, canvas_size), Image.LANCZOS)
    canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    offset = ((canvas_size - fitted.width) // 2, (canvas_size - fitted.height) // 2)
    canvas.paste(fitted, offset, fitted)
    canvas.save(png_path, optimize=True)
    canvas.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"   🖼  Generated favicon assets: {png_path}, {ico_path}")


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

def generate_json_ld(page_id, lang, title, description, canonical_url, base_url, home_url):
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
        {"@type": "ListItem", "position": 1, "name": breadcrumb_home.get(lang, "Home"), "item": home_url}
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
    if page_id in page_names and page_id != "index":
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
            "url": home_url,
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
            "url": home_url,
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

    if page_id in product_names:
        product_name = product_names[page_id].get(lang, product_names[page_id]["en"])
        graph.append({
            "@context": "https://schema.org",
            "@type": "Product",
            "name": product_name,
            "description": description,
            "url": canonical_url,
        })

    return json.dumps(graph, indent=2, ensure_ascii=False)


# ── Pages ──────────────────────────────────────────────────────────────────

PAGES = [
    # ── Czech pages (default language for .cz domain) ──
    ("cs/index.html", "cs",
     "Varhany Mlnařík | Digitální varhany, klaviatury a MIDI moduly pro Hauptwerk",
     "Domů",
     "index",
     "digitální varhany, varhany, cvičení, MIDI, pedálnice, hrací stoly, hauptwerk, grandorgue, opravy varhan, ladění, varhanní klaviatura",
     "Výroba digitálních varhan, MIDI modulů a unikátních kinetických klaviatur s Druckpunktem. Pedálnice, hrací stoly, cvičné varhany pro Hauptwerk a GrandOrgue."),

    ("cs/keyboards.html", "cs",
     "Varhanní klaviatury s kinetickým projevem | MIDI klaviatury pro Hauptwerk",
     "Varhanní klaviatury",
     "keyboards",
     "varhanní klaviatura, kinetická klaviatura, Druckpunkt, MIDI klaviatura, varhanní manuál, hall senzory, hauptwerk klaviatura",
     "Mechanické varhanní klaviatury s nastavitelným Druckpunktem a kinetickým projevem. 61 kláves, dřevěné klávesy, hliníkový rám, MIDI výstup. Ideální pro Hauptwerk a digitální varhany."),

    ("cs/cecilia.html", "cs",
     "Cecilia — zvukový systém pro digitální varhany | MIDI expandér",
     "Zvukový systém Cecilia",
     "cecilia",
     "cecilia, MIDI, expandér, varhanní modul, zvukový modul, digitální varhany",
     "Cecilia — výkonný zvukový systém a MIDI expandér pro stavbu digitálních varhan. Ideální doplněk k Hauptwerk a GrandOrgue."),

    ("cs/organ.html", "cs",
     "Digitální varhany na míru | Stavba, opravy, Hauptwerk konzole",
     "Varhany — díly i kompletní nástroje",
     "organ",
     "digitální varhany, varhany, cvičení, MIDI, pedálnice, hrací stoly, hauptwerk, grandorgue, opravy varhan, ladění, varhanní konzole",
     "Stavba digitálních varhan na míru, MIDI konzolí a pedálnic. Kompletní nástroje i jednotlivé díly. Specializace na Hauptwerk a samplové technologie."),

    ("cs/services.html", "cs",
     "Služby | Opravy digitálních varhan Viscount, Ahlborn, Johanus, Eminent",
     "Služby",
     "services",
     "digitální varhany, varhany, opravy digitálních varhan, opravy varhan, Viscount, Ahlborn, Johanus, Eminent, rekonstrukce varhan, MIDI, pedálnice, hrací stoly, hauptwerk, grandorgue, ladění, poradenství",
     "Opravy a rekonstrukce digitálních varhan Viscount, Ahlborn, Johanus, Eminent. Nabízíme ladění, poradenství při stavbě digitálních varhan a konzolí pro Hauptwerk. Servis MIDI modulů a klaviatur."),

    ("cs/contact.html", "cs",
     "Kontakt | Varhany Mlnařík — digitální varhany a MIDI",
     "Kontakt",
     "contact",
     "digitální varhany, varhany, MIDI, kontakt, jakub mlnařík, smartorgan",
     "Kontaktujte nás pro objednávky digitálních varhan, MIDI modulů, klaviatur nebo konzolí pro Hauptwerk."),

    ("cs/midi-modules.html", "cs",
     "MIDI moduly pro digitální varhany | Hall-Scanner64, Matrix-Scanner64 a další",
     "MIDI moduly",
     "midi",
     "MIDI moduly, Hall-Scanner64, Input-Module16, Matrix-Scanner64, Output-Module16, MIDI scanner, MIDI vstup, MIDI výstup, varhanní MIDI, hauptwerk MIDI",
     "MIDI moduly pro stavbu digitálních varhan: Hall-Scanner64, Input-Module16, Matrix-Scanner64, Output-Module16. Wi-Fi konfigurace, USB-MIDI, High-Speed Analog MIDI Bus. Ideální pro Hauptwerk projekty."),

    ("cs/about.html", "cs",
     "O mně | Jakub Mlnařík — digitální varhany a MIDI technologie",
     "O mně",
     "about",
     "varhany, digitální varhany, MIDI, jakub mlnařík, smartorgan, hauptwerk",
     "Příběh za projektem Smartorgan — od varhanáře k vývoji MIDI modulů a kinetických klaviatur pro digitální varhany a Hauptwerk."),

    # ── English pages ──
    ("en/index.html", "en",
     "Smartorgan | Digital Organs, Organ Keyboards & MIDI Modules for Hauptwerk",
     "Home",
     "index",
     "digital organ, MIDI, pedalboards, consoles, hauptwerk, organ keyboard, MIDI modules, grandorgue",
     "Digital organs, organ keyboards with kinetic touch, and MIDI modules for Hauptwerk. Custom consoles, pedalboards, and practice organs for organ builders."),

    ("en/keyboards.html", "en",
     "Organ MIDI Keyboards with Kinetic Touch & Druckpunkt | Hauptwerk Console Keyboards",
     "Organ Keyboards",
     "keyboards",
     "organ MIDI keyboard, kinetic keyboard Druckpunkt, organ keyboard touch, Hauptwerk keyboard, MIDI keyboard weighted, mechanical organ keyboard, organ console keyboard, organ manual MIDI",
     "Custom mechanical organ MIDI keyboards with authentic Druckpunkt touch and kinetic inertial response. 61 wooden keys, hall sensors, MIDI output. Perfect for Hauptwerk consoles, digital organs, and organ keyboard players seeking professional feel."),

    ("en/cecilia.html", "en",
     "Cecilia — Sound System for Digital Organs | MIDI Expander & Organ Module",
     "Organ sound system Cecilia",
     "cecilia",
     "cecilia, MIDI, expander, organ module, organ unit, sound engine, digital organ sound",
     "Cecilia — a powerful sound system and MIDI expander for building digital organs. A perfect companion for Hauptwerk and GrandOrgue setups."),

    ("en/organ.html", "en",
     "Digital Organs & MIDI Consoles for Hauptwerk | Custom Organ Building",
     "Organs — parts and complete instruments",
     "organ",
     "digital organ, MIDI, pedalboards, consoles, hauptwerk, grandorgue, organ console, custom organ",
     "Custom digital organs, MIDI consoles, and pedalboards for Hauptwerk. Complete instruments and individual components. Sampling technology for authentic pipe organ sound."),

    ("en/services.html", "en",
     "Services | Organ Repair, Maintenance & Consulting for Digital Organs",
     "Services",
     "services",
     "organ repair, organ maintenance, digital organ service, hauptwerk consulting, MIDI console service",
     "Organ repair, tuning, maintenance, and consulting for digital organ projects. Specialized in Hauptwerk consoles, MIDI modules, and organ keyboard installations."),

    ("en/contact.html", "en",
     "Contact | Mlnarik Organ — Digital Organs, Keyboards & MIDI Modules",
     "Contact",
     "contact",
     "digital organ, MIDI, pedalboards, consoles, hauptwerk, contact, organ builder",
     "Get in touch for custom digital organs, organ keyboards, MIDI modules, or Hauptwerk console projects. We provide material and technical support."),

    ("en/midi-modules.html", "en",
     "MIDI Modules for Organ Keyboards & Hauptwerk Consoles | Hall-Scanner64, Matrix-Scanner64",
     "MIDI Modules",
     "midi",
     "MIDI modules organ, MIDI scanner, Hall-Scanner64, Input-Module16, Matrix-Scanner64, Output-Module16, organ MIDI keyboard, Hauptwerk MIDI, organ console MIDI, organ keyboard controller",
     "Professional MIDI modules for digital organ consoles, keyboards, and Hauptwerk systems. Hall-Scanner64 for organ keyboards with sensors, Matrix-Scanner64 for MIDI key scanning, Input/Output modules. USB-MIDI, analog MIDI, Wi-Fi setup. Essential for custom organ console building."),

    ("en/about.html", "en",
     "About | Jakub Mlnarik — Digital Organs, MIDI Technology & Organ Building",
     "About — my story",
     "about",
     "organ building, MIDI, Cecilia, smartorgan, jakub mlnarik, digital organ, hauptwerk",
     "The story behind Smartorgan — from organ builder to MIDI module developer and kinetic keyboard designer for digital organs and Hauptwerk."),

    # ── German pages ──
    ("de/index.html", "de",
     "Smartorgan | Digitale Orgeln, Orgelkeyboards & MIDI-Module für Hauptwerk",
     "Startseite",
     "index",
     "digitale Orgel, MIDI, Pedalboards, Spieltische, Hauptwerk, Orgelkeyboard, MIDI-Module, GrandOrgue",
     "Digitale Orgeln, Orgelkeyboards mit kinetischer Ansprache und MIDI-Module für Hauptwerk. Kundenspezifische Spieltische, Pedalboards und Übungsorgeln für Orgelbauer."),

    ("de/keyboards.html", "de",
     "Orgelkeyboards mit kinetischer Ansprache | MIDI-Keyboards für Hauptwerk & digitale Orgeln",
     "Orgelkeyboards",
     "keyboards",
     "Orgelkeyboard, kinetisches Keyboard, Druckpunkt, MIDI-Keyboard, Orgelmanual, Hall-Sensoren, Hauptwerk-Keyboard, digitales Orgelkeyboard",
     "Mechanische Orgelkeyboards mit einstellbarem Druckpunkt und kinetischem Gefühl. 61 Tasten, Holztasten, Aluminiumrahmen, MIDI-Ausgang. Perfekt für Hauptwerk und digitale Orgelspieltische."),

    ("de/cecilia.html", "de",
     "Cecilia — Klangsystem für digitale Orgeln | MIDI-Expander & Orgelmodul",
     "Orgelklangsystem Cecilia",
     "cecilia",
     "Cecilia, MIDI, Expander, Orgelmodul, Orgeleinheit, Klangengine, digitaler Orgelklang",
     "Cecilia — ein leistungsstarkes Klangsystem und MIDI-Expander für den Bau digitaler Orgeln. Ein perfekter Begleiter für Hauptwerk- und GrandOrgue-Setups."),

    ("de/organ.html", "de",
     "Digitale Orgeln & MIDI-Spieltische für Hauptwerk | Kundenspezifischer Orgelbau",
     "Orgeln — Teile und komplette Instrumente",
     "organ",
     "digitale Orgel, MIDI, Pedalboards, Spieltische, Hauptwerk, GrandOrgue, Orgelspieltisch, kundenspezifische Orgel",
     "Kundenspezifische digitale Orgeln, MIDI-Spieltische und Pedalboards für Hauptwerk. Komplette Instrumente und Einzelkomponenten. Sampling-Technologie für authentischen Pfeifenorgelklang."),

    ("de/services.html", "de",
     "Dienstleistungen | Orgelreparatur, Wartung & Beratung für digitale Orgeln",
     "Dienstleistungen",
     "services",
     "Orgelreparatur, Orgelwartung, digitaler Orgelservice, Hauptwerk-Beratung, MIDI-Spieltisch-Service",
     "Orgelreparatur, Stimmung, Wartung und Beratung für digitale Orgelprojekte. Spezialisiert auf Hauptwerk-Spieltische, MIDI-Module und Orgelkeyboard-Installationen."),

    ("de/contact.html", "de",
     "Kontakt | Mlnarik Organ — Digitale Orgeln, Keyboards & MIDI-Module",
     "Kontakt",
     "contact",
     "digitale Orgel, MIDI, Pedalboards, Spieltische, Hauptwerk, Kontakt, Orgelbauer",
     "Nehmen Sie Kontakt auf für kundenspezifische digitale Orgeln, Orgelkeyboards, MIDI-Module oder Hauptwerk-Spieltischprojekte. Wir bieten materielle und technische Unterstützung."),

    ("de/midi-modules.html", "de",
     "MIDI-Module für digitale Orgeln | Hall-Scanner64, Matrix-Scanner64 & mehr",
     "MIDI-Module",
     "midi",
     "MIDI-Module, Hall-Scanner64, Input-Module16, Matrix-Scanner64, Output-Module16, MIDI-Scanner, MIDI-Eingang, MIDI-Ausgang, Orgel-MIDI, Hauptwerk-MIDI",
     "MIDI-Module für den Bau digitaler Orgeln: Hall-Scanner64, Input-Module16, Matrix-Scanner64, Output-Module16. Wi-Fi-Konfiguration, USB-MIDI, High-Speed Analog MIDI Bus. Ideal für Hauptwerk-Projekte."),

    ("de/about.html", "de",
     "Über mich | Jakub Mlnarik — Digitale Orgeln, MIDI-Technologie & Orgelbau",
     "Über mich — meine Geschichte",
     "about",
     "Orgelbau, MIDI, Cecilia, Smartorgan, Jakub Mlnarik, digitale Orgel, Hauptwerk",
     "Die Geschichte hinter Smartorgan — vom Orgelbauer zum MIDI-Modul-Entwickler und Designer kinetischer Keyboards für digitale Orgeln und Hauptwerk."),

    # ── Dutch pages ──
    ("nl/index.html", "nl",
     "Smartorgan | Digitale Orgels, Orgelkeyboards & MIDI-modules voor Hauptwerk",
     "Home",
     "index",
     "digitaal orgel, MIDI, pedaalborden, speeltafels, Hauptwerk, orgelkeyboard, MIDI-modules, GrandOrgue",
     "Digitale orgels, orgelkeyboards met kinetische aanslag en MIDI-modules voor Hauptwerk. Op maat gemaakte speeltafels, pedaalborden en oefenorgels voor orgelbouwers."),

    ("nl/keyboards.html", "nl",
     "Orgelkeyboards met kinetische aanslag | MIDI-keyboards voor Hauptwerk & digitale orgels",
     "Orgelkeyboards",
     "keyboards",
     "orgelkeyboard, kinetisch keyboard, Druckpunkt, MIDI-keyboard, orgelmanuaal, Hall-sensoren, Hauptwerk-keyboard, digitaal orgelkeyboard",
     "Mechanische orgelkeyboards met instelbare Druckpunkt en kinetisch gevoel. 61 toetsen, houten toetsen, aluminium frame, MIDI-uitgang. Perfect voor Hauptwerk en digitale orgelspeeltafels."),

    ("nl/cecilia.html", "nl",
     "Cecilia — Geluidssysteem voor digitale orgels | MIDI-expander & orgelmodule",
     "Orgelgeluidssysteem Cecilia",
     "cecilia",
     "Cecilia, MIDI, expander, orgelmodule, orgeleenheid, geluidsengine, digitale orgelgeluid",
     "Cecilia — een krachtig geluidssysteem en MIDI-expander voor het bouwen van digitale orgels. Een perfecte aanvulling voor Hauptwerk- en GrandOrgue-opstellingen."),

    ("nl/organ.html", "nl",
     "Digitale orgels & MIDI-speeltafels voor Hauptwerk | Op maat gemaakt orgelbouw",
     "Orgels — onderdelen en complete instrumenten",
     "organ",
     "digitaal orgel, MIDI, pedaalborden, speeltafels, Hauptwerk, GrandOrgue, orgelspeeltafel, op maat gemaakt orgel",
     "Op maat gemaakte digitale orgels, MIDI-speeltafels en pedaalborden voor Hauptwerk. Complete instrumenten en losse componenten. Sampling-technologie voor authentiek pijporgelgeluid."),

    ("nl/services.html", "nl",
     "Diensten | Orgelreparatie, onderhoud & advies voor digitale orgels",
     "Diensten",
     "services",
     "orgelreparatie, orgelonderhoud, digitale orgelservice, Hauptwerk-advies, MIDI-speeltafel-service",
     "Orgelreparatie, stemming, onderhoud en advies voor digitale orgelprojecten. Gespecialiseerd in Hauptwerk-speeltafels, MIDI-modules en orgelkeyboard-installaties."),

    ("nl/contact.html", "nl",
     "Contact | Mlnarik Organ — Digitale orgels, Keyboards & MIDI-modules",
     "Contact",
     "contact",
     "digitaal orgel, MIDI, pedaalborden, speeltafels, Hauptwerk, contact, orgelbouwer",
     "Neem contact op voor op maat gemaakte digitale orgels, orgelkeyboards, MIDI-modules of Hauptwerk-speeltafelprojecten. Wij bieden materiële en technische ondersteuning."),

    ("nl/midi-modules.html", "nl",
     "MIDI-modules voor digitale orgels | Hall-Scanner64, Matrix-Scanner64 & meer",
     "MIDI-modules",
     "midi",
     "MIDI-modules, Hall-Scanner64, Input-Module16, Matrix-Scanner64, Output-Module16, MIDI-scanner, MIDI-ingang, MIDI-uitgang, orgel-MIDI, Hauptwerk-MIDI",
     "MIDI-modules voor het bouwen van digitale orgels: Hall-Scanner64, Input-Module16, Matrix-Scanner64, Output-Module16. Wi-Fi-configuratie, USB-MIDI, High-Speed Analog MIDI Bus. Ideaal voor Hauptwerk-projecten."),

    ("nl/about.html", "nl",
     "Over mij | Jakub Mlnarik — Digitale orgels, MIDI-technologie & orgelbouw",
     "Over mij — mijn verhaal",
     "about",
     "orgelbouw, MIDI, Cecilia, Smartorgan, Jakub Mlnarik, digitale orgel, Hauptwerk",
     "Het verhaal achter Smartorgan — van orgelbouwer tot MIDI-module-ontwikkelaar en ontwerper van kinetische keyboards voor digitale orgels en Hauptwerk."),
]


LANG_CONFIG = {
    "cs": {
        "html_lang": "cs",
        "site_name": "Smartorgan / Varhany Mlnařík",
        "logo_alt": "Smartorgan — digitální varhany, klaviatury a MIDI moduly",
        "og_locale": "cs_CZ",
    },
    "en": {
        "html_lang": "en",
        "site_name": "Smartorgan / Mlnarik Organ",
        "logo_alt": "Smartorgan — digital organs, organ keyboards and MIDI modules",
        "og_locale": "en_US",
    },
    "de": {
        "html_lang": "de",
        "site_name": "Smartorgan / Mlnarik Organ",
        "logo_alt": "Smartorgan — digitale Orgeln, Orgelkeyboards und MIDI-Module",
        "og_locale": "de_DE",
    },
    "nl": {
        "html_lang": "nl",
        "site_name": "Smartorgan / Mlnarik Organ",
        "logo_alt": "Smartorgan — digitale orgels, orgelkeyboards en MIDI-modules",
        "og_locale": "nl_NL",
    },
}

LANGS = ["cs", "en", "de", "nl"]

PAGE_LABELS = {
    "cs": {
        "index": "Domů",
        "midi": "MIDI",
        "keyboards": "Klaviatury",
        "organ": "Varhany",
        "services": "Služby",
        "cecilia": "Cecilia",
        "about": "O mně",
        "contact": "Kontakt",
    },
    "en": {
        "index": "Home",
        "midi": "MIDI",
        "keyboards": "Keyboards",
        "organ": "Organs",
        "services": "Services",
        "cecilia": "Cecilia",
        "about": "About",
        "contact": "Contact",
    },
    "de": {
        "index": "Startseite",
        "midi": "MIDI",
        "keyboards": "Keyboards",
        "organ": "Orgeln",
        "services": "Dienstleistungen",
        "cecilia": "Cecilia",
        "about": "Über mich",
        "contact": "Kontakt",
    },
    "nl": {
        "index": "Home",
        "midi": "MIDI",
        "keyboards": "Keyboards",
        "organ": "Orgels",
        "services": "Diensten",
        "cecilia": "Cecilia",
        "about": "Over mij",
        "contact": "Contact",
    },
}


def page_slug(source_filename):
    """Extract a clean page slug from a source path like 'cs/index.html'."""
    stem, _ext = os.path.splitext(source_filename)
    # Strip the language directory prefix to get the slug
    parts = stem.split(os.sep)
    return parts[-1]


def page_public_url(base_url, lang, filename, page_id):
    """Return the public URL for a page in a given language.
    
    Czech index is served at root '/' for .cz domain SEO.
    All other pages go under /{lang}/{slug}.html.
    """
    slug = page_slug(filename)
    if lang == "cs" and page_id == "index":
        return f"{base_url}/"
    return f"{base_url}/{lang}/{slug}.html"


def page_output_path(out_dir, lang, filename, page_id):
    """Return the output file path for a page in a given language.
    
    All pages go into {out_dir}/{lang}/{slug}.html (clean folder-based URLs).
    Czech index is additionally copied to root index.html for .cz domain SEO.
    """
    slug = page_slug(filename)
    return os.path.join(out_dir, lang, f"{slug}.html")


def relative_url(from_path, to_path):
    """Return a relative URL from one generated file to another."""
    from_dir = os.path.dirname(from_path) or "."
    rel = os.path.relpath(to_path, start=from_dir)
    return rel.replace(os.sep, "/")


def rewrite_content_links(content, current_out_path, source_output_paths):
    """Rewrite page links and asset URLs inside content snippets."""
    current_dir = os.path.dirname(current_out_path) or "."
    for source_filename, target_path in sorted(source_output_paths.items(), key=lambda item: len(item[0]), reverse=True):
        rel = os.path.relpath(target_path, start=current_dir).replace(os.sep, "/")
        content = content.replace(source_filename, rel)

    asset_prefix = "" if current_dir == "." else "../"
    content = content.replace('href="img/', f'href="{asset_prefix}img/')
    content = content.replace('src="img/', f'src="{asset_prefix}img/')
    content = content.replace('href="doc/', f'href="{asset_prefix}doc/')
    content = content.replace('src="doc/', f'src="{asset_prefix}doc/')
    return content


def render_html(
    *,
    lang,
    title,
    description,
    content,
    canonical_url,
    home_url,
    styles_href,
    favicon_ico,
    favicon_png,
    logo_src,
    cs_url,
    en_url,
    de_url,
    nl_url,
    x_default_url,
    cs_link,
    en_link,
    de_link,
    nl_link,
    midi_url,
    keyboards_url,
    organ_url,
    services_url,
    cecilia_url,
    about_url,
    contact_url,
    json_ld,
    og_image,
    active_index,
    active_midi,
    active_keyboards,
    active_organ,
    active_services,
    active_cecilia,
    active_about,
    active_contact,
):
    cfg = LANG_CONFIG[lang]
    labels = PAGE_LABELS[lang]

    template = """<!DOCTYPE html>
<html lang="{html_lang}">

<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <link rel="icon" href="{favicon_ico}" sizes="any">
  <link rel="icon" type="image/png" href="{favicon_png}" sizes="512x512">
  <link rel="stylesheet" href="{styles_href}">
  <meta name="description" content="{description}">

  <link rel="canonical" href="{canonical_url}">
  <link rel="alternate" hreflang="cs" href="{cs_url}">
  <link rel="alternate" hreflang="en" href="{en_url}">
  <link rel="alternate" hreflang="de" href="{de_url}">
  <link rel="alternate" hreflang="nl" href="{nl_url}">
  <link rel="alternate" hreflang="x-default" href="{x_default_url}">

  <meta property="og:type" content="website">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:url" content="{canonical_url}">
  <meta property="og:image" content="{og_image}">
  <meta property="og:locale" content="{og_locale}">
  <meta property="og:site_name" content="{site_name}">

  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{description}">
  <meta name="twitter:image" content="{og_image}">

  <script type="application/ld+json">
{json_ld}
  </script>
</head>

<body>
<div id="main-frame">
  <div id="header">
    <div id="lang-bar">
      <a href="{cs_link}" class="lang-switch" hreflang="cs">CS</a>
      <a href="{en_link}" class="lang-switch" hreflang="en">EN</a>
      <a href="{de_link}" class="lang-switch" hreflang="de">DE</a>
      <a href="{nl_link}" class="lang-switch" hreflang="nl">NL</a>
    </div>
    <div class="header-top">
      <div id="logo"><a href="{home_url}"><img src="{logo_src}" alt="{logo_alt}" width="100"></a></div>
      <div id="top-menu">
        <a href="{home_url}"{active_index}>{home_label}</a>
        <a href="{midi_url}"{active_midi}>{midi_label}</a>
        <a href="{keyboards_url}"{active_keyboards}>{keyboards_label}</a>
        <a href="{organ_url}"{active_organ}>{organ_label}</a>
        <a href="{services_url}"{active_services}>{services_label}</a>
        <a href="{cecilia_url}"{active_cecilia}>{cecilia_label}</a>
        <a href="{about_url}"{active_about}>{about_label}</a>
        <a href="{contact_url}"{active_contact}>{contact_label}</a>
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
      <span class="footer-copy">&copy; 2026 smartorgan.cz</span>
      <span class="footer-sep">&middot;</span>
      <span class="footer-author">Created by Jakub Mlnarik</span>
    </div>
  </div>
</div>

</body>
</html>
"""

    return template.format(
        html_lang=cfg["html_lang"],
        title=html.escape(title),
        description=html.escape(description),
        styles_href=styles_href,
        favicon_ico=favicon_ico,
        favicon_png=favicon_png,
        canonical_url=canonical_url,
        cs_url=cs_url,
        en_url=en_url,
        de_url=de_url,
        nl_url=nl_url,
        x_default_url=x_default_url,
        cs_link=cs_link,
        en_link=en_link,
        de_link=de_link,
        nl_link=nl_link,
        og_image=og_image,
        og_locale=cfg["og_locale"],
        site_name=html.escape(cfg["site_name"]),
        json_ld=json_ld,
        home_url=home_url,
        logo_src=logo_src,
        logo_alt=html.escape(cfg["logo_alt"]),
        home_label=html.escape(labels["index"]),
        midi_url=midi_url,
        midi_label=html.escape(labels["midi"]),
        keyboards_url=keyboards_url,
        keyboards_label=html.escape(labels["keyboards"]),
        organ_url=organ_url,
        organ_label=html.escape(labels["organ"]),
        services_url=services_url,
        services_label=html.escape(labels["services"]),
        cecilia_url=cecilia_url,
        cecilia_label=html.escape(labels["cecilia"]),
        about_url=about_url,
        about_label=html.escape(labels["about"]),
        contact_url=contact_url,
        contact_label=html.escape(labels["contact"]),
        active_index=active_index,
        active_midi=active_midi,
        active_keyboards=active_keyboards,
        active_organ=active_organ,
        active_services=active_services,
        active_cecilia=active_cecilia,
        active_about=active_about,
        active_contact=active_contact,
        content=content,
    )


def cleanup_generated_outputs(out_dir):
    """Remove previously generated site files before rebuilding."""
    for directory in ("cs", "en", "de", "nl"):
        path = os.path.join(out_dir, directory)
        if os.path.isdir(path):
            shutil.rmtree(path)

    for entry in os.listdir(out_dir):
        path = os.path.join(out_dir, entry)
        if not os.path.isfile(path):
            continue
        if entry == "index.html" or entry == "sitemap.xml":
            os.remove(path)
            continue
        if entry.endswith((".html", ".htm")):
            os.remove(path)


# ── Sitemap ────────────────────────────────────────────────────────────────

SITEMAP_PRIORITIES = {
    "index": "1.0",
    "organ": "0.9",
    "keyboards": "0.8",
    "midi": "0.8",
    "cecilia": "0.3",
    "services": "0.6",
    "about": "0.5",
    "contact": "0.5",
}

SITEMAP_FREQUENCIES = {
    "index": "monthly",
    "organ": "monthly",
    "keyboards": "monthly",
    "midi": "monthly",
    "cecilia": "yearly",
    "services": "yearly",
    "about": "yearly",
    "contact": "yearly",
}


def generate_sitemap(pages, base_url, out_dir):
    """Generate sitemap.xml with hreflang annotations for CS/EN/DE/NL pages."""
    by_id: dict[str, list] = {}
    for entry in pages:
        filename, lang, _title, _h1, active, _keywords, _description = entry
        by_id.setdefault(active, []).append((filename, lang))

    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>\n')
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n')
    lines.append('        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n')

    for page_id, versions in by_id.items():
        for filename, lang in versions:
            content_file = os.path.join("content", filename)

            lastmod = ""
            if os.path.exists(content_file):
                mtime = os.path.getmtime(content_file)
                lastmod = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%d")

            priority = SITEMAP_PRIORITIES.get(page_id, "0.5")
            changefreq = SITEMAP_FREQUENCIES.get(page_id, "monthly")

            url = page_public_url(base_url, lang, filename, page_id)
            cs_version = next(item for item in versions if item[1] == "cs")
            cs_url = page_public_url(base_url, "cs", cs_version[0], page_id)
            en_version = next(item for item in versions if item[1] == "en")
            en_url = page_public_url(base_url, "en", en_version[0], page_id)
            de_version = next(item for item in versions if item[1] == "de")
            de_url = page_public_url(base_url, "de", de_version[0], page_id)
            nl_version = next(item for item in versions if item[1] == "nl")
            nl_url = page_public_url(base_url, "nl", nl_version[0], page_id)

            lines.append("  <url>\n")
            lines.append(f"    <loc>{url}</loc>\n")
            if lastmod:
                lines.append(f"    <lastmod>{lastmod}</lastmod>\n")
            lines.append(f"    <changefreq>{changefreq}</changefreq>\n")
            lines.append(f"    <priority>{priority}</priority>\n")
            lines.append(f'    <xhtml:link rel="alternate" hreflang="cs" href="{cs_url}" />\n')
            lines.append(f'    <xhtml:link rel="alternate" hreflang="en" href="{en_url}" />\n')
            lines.append(f'    <xhtml:link rel="alternate" hreflang="de" href="{de_url}" />\n')
            lines.append(f'    <xhtml:link rel="alternate" hreflang="nl" href="{nl_url}" />\n')
            lines.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{cs_url}" />\n')
            lines.append("  </url>\n")

    lines.append('</urlset>\n')

    out_path = os.path.join(out_dir, "sitemap.xml")
    with open(out_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"✓  Generated {out_path}")


# ── Redirect stubs for old URL structure ──────────────────────────────────
# GitHub Pages does not support server-side redirects, so we generate small
# HTML stub files at the old URLs that redirect via <meta refresh> (0-second
# delay). Google treats 0-second meta refresh as equivalent to a 301 redirect.

OLD_URL_MAP = {
    # (old_filename, lang, page_id) -> new URL path
    # Czech
    ("index-cz.html", "cs", "index"): "/",
    ("keyboards-cz.htm", "cs", "keyboards"): "/cs/keyboards.html",
    ("midi-modules-cz.htm", "cs", "midi"): "/cs/midi-modules.html",
    ("organ-cz.htm", "cs", "organ"): "/cs/organ.html",
    ("services-cz.htm", "cs", "services"): "/cs/services.html",
    ("cecilia-cz.htm", "cs", "cecilia"): "/cs/cecilia.html",
    ("about-cz.htm", "cs", "about"): "/cs/about.html",
    ("contact-cz.htm", "cs", "contact"): "/cs/contact.html",
    # English — note: index.html at root is now the Czech homepage copy,
    # so no redirect stub is generated for it (it would overwrite the homepage).
    # The old English index at /index.html is gone; visitors get the Czech homepage.
    ("keyboards.htm", "en", "keyboards"): "/en/keyboards.html",
    ("midi-modules.htm", "en", "midi"): "/en/midi-modules.html",
    ("organ.htm", "en", "organ"): "/en/organ.html",
    ("services.htm", "en", "services"): "/en/services.html",
    ("cecilia.htm", "en", "cecilia"): "/en/cecilia.html",
    ("about.htm", "en", "about"): "/en/about.html",
    ("contact.htm", "en", "contact"): "/en/contact.html",
    # German
    ("index-de.html", "de", "index"): "/de/index.html",
    ("keyboards-de.htm", "de", "keyboards"): "/de/keyboards.html",
    ("midi-modules-de.htm", "de", "midi"): "/de/midi-modules.html",
    ("organ-de.htm", "de", "organ"): "/de/organ.html",
    ("services-de.htm", "de", "services"): "/de/services.html",
    ("cecilia-de.htm", "de", "cecilia"): "/de/cecilia.html",
    ("about-de.htm", "de", "about"): "/de/about.html",
    ("contact-de.htm", "de", "contact"): "/de/contact.html",
    # Dutch
    ("index-nl.html", "nl", "index"): "/nl/index.html",
    ("keyboards-nl.htm", "nl", "keyboards"): "/nl/keyboards.html",
    ("midi-modules-nl.htm", "nl", "midi"): "/nl/midi-modules.html",
    ("organ-nl.htm", "nl", "organ"): "/nl/organ.html",
    ("services-nl.htm", "nl", "services"): "/nl/services.html",
    ("cecilia-nl.htm", "nl", "cecilia"): "/nl/cecilia.html",
    ("about-nl.htm", "nl", "about"): "/nl/about.html",
    ("contact-nl.htm", "nl", "contact"): "/nl/contact.html",
}


def generate_redirect_stubs(base_url, out_dir):
    """Generate small HTML stub files at old URLs that redirect to new URLs.
    
    GitHub Pages does not support server-side 301 redirects, so we create
    stub files with a 0-second meta refresh. Google treats this as a
    permanent redirect and transfers ranking signals to the new URL.
    """
    for (old_filename, _lang, _page_id), new_path in OLD_URL_MAP.items():
        new_url = f"{base_url}{new_path}"
        html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta http-equiv="refresh" content="0; url={new_url}">
  <link rel="canonical" href="{new_url}">
  <script>location.replace("{new_url}")</script>
  <title>Redirecting&hellip;</title>
</head>
<body>
  <a href="{new_url}">Redirecting to {new_url}</a>
</body>
</html>
"""
        out_path = os.path.join(out_dir, old_filename)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✓  Redirect stub: {old_filename} → {new_url}")


# ── Build ──────────────────────────────────────────────────────────────────

def build():
    # Ensure output directory (current dir)
    out_dir = "."
    cleanup_generated_outputs(out_dir)
    img_dir = os.path.join(out_dir, "img")
    generate_favicon_assets(img_dir, out_dir)

    # Determine base URL from CNAME
    cname_file = os.path.join(out_dir, "CNAME")
    if os.path.exists(cname_file):
        with open(cname_file) as f:
            domain = f.read().strip()
    else:
        domain = "smartorgan.cz"
    base_url = f"https://{domain}"

    source_output_paths = {}
    filename_by_active_lang = {}
    for filename, lang, title, h1, active, keywords, description in PAGES:
        source_output_paths[filename] = page_output_path(out_dir, lang, filename, active)
        filename_by_active_lang.setdefault(active, {})[lang] = filename

    page_ids = ["index", "keyboards", "midi", "organ", "services", "cecilia", "about", "contact"]

    for filename, lang, title, h1, active, keywords, description in PAGES:
        # Read content snippet
        content_file = os.path.join("content", filename)
        if not os.path.exists(content_file):
            print(f"⚠  Missing content file: {content_file}")
            continue

        with open(content_file, "r", encoding="utf-8") as f:
            content = f.read().rstrip()

        current_out_path = page_output_path(out_dir, lang, filename, active)
        styles_href = relative_url(current_out_path, os.path.join(out_dir, "styles.css"))
        favicon_ico = relative_url(current_out_path, os.path.join(out_dir, "favicon.ico"))
        favicon_png = relative_url(current_out_path, os.path.join(out_dir, "favicon.png"))
        logo_src = relative_url(current_out_path, os.path.join(out_dir, "img", "logo-transparent.png"))
        og_image = f"{base_url}/img/logo-transparent.png"

        content = process_content_images(content, img_dir)
        content = rewrite_content_links(content, current_out_path, source_output_paths)

        home_filename = filename_by_active_lang["index"][lang]
        home_target_path = page_output_path(out_dir, lang, home_filename, "index")
        home_url = relative_url(current_out_path, home_target_path)
        home_url_abs = page_public_url(base_url, lang, home_filename, "index")
        canonical_url = page_public_url(base_url, lang, filename, active)

        alternate_urls = {
            "cs": page_public_url(base_url, "cs", filename_by_active_lang[active]["cs"], active),
            "en": page_public_url(base_url, "en", filename_by_active_lang[active]["en"], active),
            "de": page_public_url(base_url, "de", filename_by_active_lang[active]["de"], active),
            "nl": page_public_url(base_url, "nl", filename_by_active_lang[active]["nl"], active),
        }
        alternate_urls["x-default"] = alternate_urls["cs"]

        lang_switch_links = {
            target_lang: relative_url(
                current_out_path,
                page_output_path(out_dir, target_lang, filename_by_active_lang[active][target_lang], active),
            )
            for target_lang in LANGS
        }

        nav_urls = {
            page_id: relative_url(current_out_path, page_output_path(out_dir, lang, filename_by_active_lang[page_id][lang], page_id))
            for page_id in page_ids
        }

        json_ld_raw = generate_json_ld(active, lang, title, description, canonical_url, base_url, home_url_abs)
        json_ld_indented = "\n".join("  " + line for line in json_ld_raw.split("\n"))

        html_out = render_html(
            lang=lang,
            title=title,
            description=description,
            content=content,
            canonical_url=canonical_url,
            home_url=home_url,
            styles_href=styles_href,
            favicon_ico=favicon_ico,
            favicon_png=favicon_png,
            logo_src=logo_src,
            cs_url=alternate_urls["cs"],
            en_url=alternate_urls["en"],
            de_url=alternate_urls["de"],
            nl_url=alternate_urls["nl"],
            x_default_url=alternate_urls["x-default"],
            cs_link=lang_switch_links["cs"],
            en_link=lang_switch_links["en"],
            de_link=lang_switch_links["de"],
            nl_link=lang_switch_links["nl"],
            midi_url=nav_urls["midi"],
            keyboards_url=nav_urls["keyboards"],
            organ_url=nav_urls["organ"],
            services_url=nav_urls["services"],
            cecilia_url=nav_urls["cecilia"],
            about_url=nav_urls["about"],
            contact_url=nav_urls["contact"],
            json_ld=json_ld_indented,
            og_image=og_image,
            active_index=active_class("index", active),
            active_midi=active_class("midi", active),
            active_keyboards=active_class("keyboards", active),
            active_organ=active_class("organ", active),
            active_services=active_class("services", active),
            active_cecilia=active_class("cecilia", active),
            active_about=active_class("about", active),
            active_contact=active_class("contact", active),
        )

        out_path = page_output_path(out_dir, lang, filename, active)
        out_dirname = os.path.dirname(out_path)
        if out_dirname:
            os.makedirs(out_dirname, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_out)
            f.write("\n")

        print(f"✓  Generated {out_path}")

    # Also generate root index.html as a copy of cs/index.html for .cz domain SEO.
    # We read the cs/ version and re-root relative paths to root level.
    root_index_src = os.path.join(out_dir, "cs", "index.html")
    root_index_out = os.path.join(out_dir, "index.html")
    if os.path.exists(root_index_src):
        with open(root_index_src, "r", encoding="utf-8") as f:
            root_html = f.read()
        # Re-root asset paths from cs/ level to root level
        root_html = root_html.replace('href="../favicon.', 'href="favicon.')
        root_html = root_html.replace('href="../styles.css"', 'href="styles.css"')
        root_html = root_html.replace('href="../img/', 'href="img/')
        root_html = root_html.replace('src="../img/', 'src="img/')
        root_html = root_html.replace('href="../doc/', 'href="doc/')
        root_html = root_html.replace('src="../doc/', 'src="doc/')
        # Fix lang-switch links (were ../en, ../de, ../nl from cs/ context)
        root_html = root_html.replace('href="../en/', 'href="en/')
        root_html = root_html.replace('href="../de/', 'href="de/')
        root_html = root_html.replace('href="../nl/', 'href="nl/')
        # Fix page links: in cs/ folder they point to same-folder, but at root they
        # need the cs/ prefix for non-index pages
        for page_id in ["keyboards", "midi-modules", "organ", "services", "cecilia", "about", "contact", "index"]:
            slug = page_id
            root_html = root_html.replace(f'href="{slug}.html"', f'href="cs/{slug}.html"' if page_id != "index" else 'href="index.html"')
        with open(root_index_out, "w", encoding="utf-8") as f:
            f.write(root_html)
            f.write("\n")
        print(f"✓  Generated {root_index_out}")

    generate_sitemap(PAGES, base_url, out_dir)
    generate_redirect_stubs(base_url, out_dir)


if __name__ == "__main__":
    build()