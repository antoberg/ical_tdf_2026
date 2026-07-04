#!/usr/bin/env python3
"""
Génère le fichier tdf2026.ics à partir de stages.json.

Usage :
    python3 generate.py                     # Génère dans ./public/tdf2026.ics
    python3 generate.py --output autre.ics  # Chemin custom
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────
#  Configuration
# ──────────────────────────────────────────────────────────────────────

STAGE_URL_TEMPLATE = "https://www.letour.fr/fr/etape-{num}"

TYPE_CONFIG = {
    "clm_equipe":    {"emoji": "⏱️", "label": "Contre-la-montre par équipes"},
    "clm_individuel":{"emoji": "⏱️", "label": "Contre-la-montre individuel"},
    "montagne":      {"emoji": "🏔️", "label": "Étape de montagne"},
    "etape_reine":   {"emoji": "🔥", "label": "Étape reine"},
    "accidentee":    {"emoji": "⛰️",  "label": "Étape accidentée"},
    "plaine":        {"emoji": "🚀", "label": "Étape de plaine"},
    "repos":         {"emoji": "🟡", "label": "Journée de repos"},
}

# ──────────────────────────────────────────────────────────────────────
#  iCal helpers
# ──────────────────────────────────────────────────────────────────────

def fold_line(line: str) -> str:
    """RFC 5545 : repli des lignes > 75 octets."""
    parts = []
    while len(line.encode("utf-8")) > 75:
        cut = 75
        while len(line[:cut].encode("utf-8")) > 75:
            cut -= 1
        parts.append(line[:cut])
        line = " " + line[cut:]
    parts.append(line)
    return "\r\n".join(parts)


def ical_escape(text: str) -> str:
    """Échappe les caractères spéciaux iCal."""
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def make_uid(stage: dict) -> str:
    """UID unique et stable par étape."""
    raw = f"tdf2026-stage-{stage['num']}-{stage['date']}"
    return hashlib.md5(raw.encode()).hexdigest() + "@tdf2026.ical"


# ──────────────────────────────────────────────────────────────────────
#  Génération d'un VEVENT
# ──────────────────────────────────────────────────────────────────────

def stage_to_vevent(stage: dict) -> str:
    date_obj = datetime.strptime(stage["date"], "%Y-%m-%d")
    now = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    is_rest = str(stage["num"]).startswith("R")
    cfg = TYPE_CONFIG.get(stage["type"], {"emoji": "🚴", "label": stage["type"]})

    # ── SUMMARY ──
    if is_rest:
        summary = f"{cfg['emoji']} Tour de France 2026 — Repos ({stage['end']})"
    else:
        summary = (
            f"{cfg['emoji']} TDF 2026 — Ét. {stage['num']} : "
            f"{stage['start']} → {stage['end']} ({stage['km']} km)"
        )

    # ── DESCRIPTION ──
    desc_lines = []
    if not is_rest:
        desc_lines.append(f"📍 {stage['start']} → {stage['end']}")
        desc_lines.append(f"📏 Distance : {stage['km']} km")
        if stage.get("deniv"):
            desc_lines.append(f"📐 Dénivelé : {stage['deniv']} m D+")
        desc_lines.append(f"🏷️ Type : {cfg['label']}")

        if stage.get("cols"):
            desc_lines.append("")
            desc_lines.append("⛰️ Difficultés :")
            for col in stage["cols"].split(", "):
                desc_lines.append(f"  • {col.strip()}")

        desc_lines.append("")
        desc_lines.append(stage["description"])

        if stage.get("favoris"):
            desc_lines.append("")
            desc_lines.append(f"⭐ Favoris : {stage['favoris']}")

        desc_lines.append("")
        stage_num = stage["num"]
        desc_lines.append(f"🔗 Profil et carte : {STAGE_URL_TEMPLATE.format(num=stage_num)}")
    else:
        desc_lines.append(stage["description"])

    # Escape each line individually, THEN join with iCal newline literal
    description = "\\n".join(ical_escape(line) for line in desc_lines)

    # ── LOCATION (ville d'arrivée uniquement) ──
    location = stage["end"]

    # ── URL ──
    url = "" if is_rest else STAGE_URL_TEMPLATE.format(num=stage["num"])

    # ── DATES (événement journée entière) ──
    dtstart = date_obj.strftime("%Y%m%d")
    dtend = (date_obj + timedelta(days=1)).strftime("%Y%m%d")

    # ── Assemblage VEVENT ──
    lines = [
        "BEGIN:VEVENT",
        fold_line(f"UID:{make_uid(stage)}"),
        f"DTSTAMP:{now}",
        f"DTSTART;VALUE=DATE:{dtstart}",
        f"DTEND;VALUE=DATE:{dtend}",
        fold_line(f"SUMMARY:{ical_escape(summary)}"),
        fold_line(f"DESCRIPTION:{description}"),
        fold_line(f"LOCATION:{ical_escape(location)}"),
    ]

    if url:
        lines.append(fold_line(f"URL:{url}"))

    # Rappel le matin de l'étape
    lines.extend([
        "BEGIN:VALARM",
        "TRIGGER;VALUE=DATE-TIME:" + date_obj.strftime("%Y%m%d") + "T060000Z",
        "ACTION:DISPLAY",
        fold_line(f"DESCRIPTION:{ical_escape(summary)}"),
        "END:VALARM",
    ])

    lines.extend([
        "TRANSP:TRANSPARENT",
        "STATUS:CONFIRMED",
        "END:VEVENT",
    ])

    return "\r\n".join(lines)


# ──────────────────────────────────────────────────────────────────────
#  Génération du fichier .ics complet
# ──────────────────────────────────────────────────────────────────────

def generate_ics(stages: list) -> str:
    header = "\r\n".join([
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//TDF2026//Tour de France 2026//FR",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Tour de France 2026",
        "X-WR-CALDESC:Les 21 étapes du Tour de France 2026 — Barcelone → Paris",
        "X-WR-TIMEZONE:Europe/Paris",
        "REFRESH-INTERVAL;VALUE=DURATION:P1D",
        "X-PUBLISHED-TTL:P1D",
        "BEGIN:VTIMEZONE",
        "TZID:Europe/Paris",
        "BEGIN:DAYLIGHT",
        "TZOFFSETFROM:+0100",
        "TZOFFSETTO:+0200",
        "TZNAME:CEST",
        "DTSTART:19700329T020000",
        "RRULE:FREQ=YEARLY;BYDAY=-1SU;BYMONTH=3",
        "END:DAYLIGHT",
        "BEGIN:STANDARD",
        "TZOFFSETFROM:+0200",
        "TZOFFSETTO:+0100",
        "TZNAME:CET",
        "DTSTART:19701025T030000",
        "RRULE:FREQ=YEARLY;BYDAY=-1SU;BYMONTH=10",
        "END:STANDARD",
        "END:VTIMEZONE",
    ])

    events = "\r\n".join(stage_to_vevent(s) for s in stages)
    footer = "END:VCALENDAR"

    return f"{header}\r\n{events}\r\n{footer}\r\n"


# ──────────────────────────────────────────────────────────────────────
#  Main
# ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Génère le calendrier iCal du Tour de France 2026"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="public/tdf2026.ics",
        help="Chemin du fichier .ics en sortie (défaut : public/tdf2026.ics)",
    )
    parser.add_argument(
        "--stages", "-s",
        type=str,
        default="stages.json",
        help="Chemin du fichier JSON des étapes (défaut : stages.json)",
    )
    args = parser.parse_args()

    # Assure un affichage UTF-8 même sur les consoles Windows (cp1252)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    # Lecture des données
    stages_path = Path(args.stages)
    if not stages_path.exists():
        print(f"❌ Fichier introuvable : {stages_path}")
        return 1

    with open(stages_path, "r", encoding="utf-8") as f:
        stages = json.load(f)

    # Génération
    ics_content = generate_ics(stages)

    # Écriture
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        f.write(ics_content)

    n_stages = sum(1 for s in stages if not str(s["num"]).startswith("R"))
    n_rest = sum(1 for s in stages if str(s["num"]).startswith("R"))

    print(f"✅ {output_path}")
    print(f"   {n_stages} étapes + {n_rest} repos = {len(stages)} événements")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
