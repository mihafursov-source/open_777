#!/usr/bin/env python3
"""Generate an Obsidian vault from Open 777 correspondence data.

The generator is intentionally conservative. It preserves every raw CSV value
in the sefirah/path notes, and creates entity notes only from columns that have
clear semantic categories. Ambiguous phrases remain plain raw text.
"""

from __future__ import annotations

import importlib.util
import re
import shutil
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import csv
import json

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
VAULT_DIR = REPO_ROOT / "obsidian_777_vault"
CSV_PATH = REPO_ROOT / "docs" / "liber_777.csv"
STRUCTURE_JS = REPO_ROOT / "src" / "structure.js"
LIBER_JS_CANDIDATES = [
    REPO_ROOT / "src" / "liber_777.js",
    REPO_ROOT / "src" / "constants" / "liber_777.js",
]

spec = importlib.util.spec_from_file_location("entity_aliases", SCRIPT_DIR / "entity_aliases.py")
aliases_module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(aliases_module)
ENTITY_ALIASES: dict[str, str] = aliases_module.ENTITY_ALIASES

SOURCE = {"repo": "open_777", "file": "docs/liber_777.csv"}
JS_SOURCE = {"repo": "open_777", "file": "src/constants/liber_777.js"}

STOP_ENTITIES = {
    "",
    "-",
    "—",
    "...",
    "none",
    "n/a",
    "unknown",
    "and",
    "or",
    "the",
    "of",
    "etc",
    "etc.",
    "&c",
    "&c.",
    "& c",
    "& c.",
    "not a valid color description",
    "no attribution possible",
}

SEFIROT = {
    1: "Kether",
    2: "Chokmah",
    3: "Binah",
    4: "Chesed",
    5: "Geburah",
    6: "Tiphareth",
    7: "Netzach",
    8: "Hod",
    9: "Yesod",
    10: "Malkuth",
}

PATHS = {
    11: "Aleph",
    12: "Beth",
    13: "Gimel",
    14: "Daleth",
    15: "Heh",
    16: "Vav",
    17: "Zayin",
    18: "Cheth",
    19: "Teth",
    20: "Yod",
    21: "Kaph",
    22: "Lamed",
    23: "Mem",
    24: "Nun",
    25: "Samekh",
    26: "Ayin",
    27: "Pe",
    28: "Tzaddi",
    29: "Qoph",
    30: "Resh",
    31: "Shin",
    32: "Tav",
}

PLANETS = {"Saturn", "Jupiter", "Mars", "Sun", "Sol", "Venus", "Mercury", "Moon", "Luna"}
ZODIAC = {
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
}
ELEMENTS = {"Fire", "Water", "Air", "Earth", "Spirit"}

ENTITY_COLUMNS = {
    "14 - General Attribution of Tarot": "tarot",
    "15 - The King Scale Colors (Yud)": "color",
    "16 - Queen Scale Colors (Heh)": "color",
    "17 - Emperor Scale Colors (Vav)": "color",
    "18 - Empress Scale Colors (Heh)": "color",
    "19 - Egyption Gods": "deity",
    "20 - Practical Egyption Gods": "deity",
    "22 - Hindu Deities": "deity",
    "33 - Scandinavian Gods": "deity",
    "34 - Greek Gods": "deity",
    "35 - Roman Gods": "deity",
    "36 - Christian Lore": "spirit",
    "38 - Animals (Real & Imaginary)": "animal",
    "39 - Plants (Real & Imaginary)": "plant",
    "40 - Precious Stones": "stone",
    "41 - Magical Weapons": "magical_weapon",
    "42 - Perfumes": "perfume",
    "43 - Vegetable Drugs": "plant",
    "44 - Mineral Drugs": "stone",
    "45 - Magical Powers": "spirit",
    "Magical Forumalæ (see Col. 41)": "other",
    "46- System of Taoism": "other",
    "48 - Figures related to Pure Number": "other",
    "49 - Lineal Figures of the Planets, &c., and Geomany": "other",
}

SUMMARY_COLUMNS = [
    "2 - Hebrew Names",
    "3 - English of II",
    "11 - Elements & Rulers",
    "12 - Tree of Life",
    "13 - Paths of Sepher Yetzirah",
    "14 - General Attribution of Tarot",
    "19 - Egyption Gods",
    "20 - Practical Egyption Gods",
    "22 - Hindu Deities",
    "38 - Animals (Real & Imaginary)",
    "39 - Plants (Real & Imaginary)",
    "40 - Precious Stones",
    "41 - Magical Weapons",
    "42 - Perfumes",
]

FOLDER_FOR_ENTITY_TYPE = {
    "tarot": "03 Tarot/Major Arcana",
    "minor_tarot": "03 Tarot/Minor Arcana",
    "hebrew_letter": "04 Hebrew Letters",
    "planet": "05 Astrology/Planets",
    "zodiac": "05 Astrology/Zodiac",
    "element": "05 Astrology/Elements",
    "deity": "06 Entities/Deities",
    "angel": "06 Entities/Angels",
    "demon": "06 Entities/Demons",
    "spirit": "06 Entities/Spirits",
    "plant": "06 Entities/Plants",
    "stone": "06 Entities/Stones",
    "perfume": "06 Entities/Perfumes",
    "animal": "06 Entities/Animals",
    "color": "06 Entities/Colors",
    "magical_weapon": "06 Entities/Magical Weapons",
    "other": "06 Entities/Other",
}

ENTITY_TYPE_PRIORITY = {
    "hebrew_letter": 100,
    "planet": 95,
    "zodiac": 95,
    "element": 95,
    "tarot": 90,
    "minor_tarot": 85,
    "deity": 60,
    "angel": 55,
    "demon": 55,
    "spirit": 50,
    "plant": 40,
    "stone": 40,
    "perfume": 40,
    "animal": 40,
    "color": 30,
    "magical_weapon": 30,
    "other": 10,
}

MANAGED_DIRS = [
    "00 Index",
    "01 Sefirot",
    "02 Paths",
    "03 Tarot",
    "04 Hebrew Letters",
    "05 Astrology",
    "06 Entities",
    "90 Dashboards",
    "_source",
    "_templates",
]


@dataclass
class ScaleNote:
    number: int
    name: str
    kind: str
    row: dict[str, str]
    connects: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)


@dataclass
class Entity:
    name: str
    entity_type: str
    appears_in: set[str] = field(default_factory=set)
    related_entities: set[str] = field(default_factory=set)
    source_rows: set[int] = field(default_factory=set)
    source_refs: set[str] = field(default_factory=set)
    raw_values: set[str] = field(default_factory=set)


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" ?\n ?", " ", text)
    return text.strip()


def slugify_filename(name: str) -> str:
    cleaned = clean_text(name)
    cleaned = cleaned.replace("/", "-").replace("\\", "-").replace(":", " -")
    cleaned = re.sub(r'[*?"<>|#^[\]]+', "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    return cleaned[:120] or "Untitled"


def wiki(name: str) -> str:
    return f"[[{name}]]"


def normalize_entity_name(name: str) -> str:
    name = clean_text(name)
    name = name.replace("[", "").replace("]", "")
    name = name.replace(" / ", " - ")
    name = name.strip(" .;:*")
    name = re.sub(r"\s+", " ", name)
    return ENTITY_ALIASES.get(name, name)


def is_noise(value: str) -> bool:
    lowered = clean_text(value).lower().strip(" .;:")
    return lowered in STOP_ENTITIES or bool(re.fullmatch(r"[.\-—_]+", lowered))


def is_probably_atomic(value: str, entity_type: str) -> bool:
    if is_noise(value):
        return False
    if len(value) > 60:
        return False
    words = value.split()
    if len(words) > 6:
        return False
    if re.search(r"\b(as|also|all|with|or|and|the various|see|but|cf)\b", value, re.I):
        return False
    if any(ch in value for ch in ["(", ")", "=", ":", "°"]):
        return False
    if entity_type == "color" and re.search(r"\bflecked|rayed|like|merging|outside\b", value, re.I):
        return False
    return True


def split_entities(raw: str, entity_type: str) -> list[str]:
    text = clean_text(raw)
    if is_noise(text):
        return []

    explicit_links = re.findall(r"\[\[([^\]]+)\]\]", text)
    if explicit_links:
        return [
            normalize_entity_name(link)
            for link in explicit_links
            if is_probably_atomic(normalize_entity_name(link), entity_type)
        ]

    text = re.sub(r"\[\[|\]\]", "", text)
    text = re.sub(r"\[[^\]]+\]", "", text)
    text = text.replace(" - ", ", ")

    if "," in text:
        parts = [part.strip() for part in text.split(",")]
    elif " | " in text:
        parts = [part.strip() for part in text.split("|")]
    else:
        parts = [text.strip()]

    out: list[str] = []
    for part in parts:
        part = normalize_entity_name(part)
        if is_probably_atomic(part, entity_type):
            out.append(part)
    return out


def explicit_wikilink_entities(raw: str) -> list[str]:
    text = clean_text(raw)
    return [
        normalize_entity_name(link)
        for link in re.findall(r"\[\[([^\]]+)\]\]", text)
        if is_probably_atomic(normalize_entity_name(link), "other")
    ]


def tarot_entities(raw: str) -> list[tuple[str, str]]:
    names = split_entities(raw, "tarot")
    out: list[tuple[str, str]] = []
    for name in names:
        if name.startswith("The 4 ") or re.search(r"\b(Aces|Twos|Threes|Fours|Fives|Sixes|Sevens|Eights|Nines|Tens)\b", name):
            out.append((name, "minor_tarot"))
        else:
            out.append((name, "tarot"))
    return out


def load_rows() -> list[dict[str, str]]:
    with CSV_PATH.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return [{key: clean_text(value) for key, value in row.items()} for row in reader]


def row_number(row: dict[str, str]) -> int | None:
    category = row["Category"]
    return int(category) if category.isdigit() else None


def parse_connects(row: dict[str, str]) -> list[str]:
    value = row.get("12 - Tree of Life", "")
    match = re.fullmatch(r"\s*(\d+)\s+to\s+(\d+)\s*", value)
    if not match:
        return []
    return [SEFIROT[int(match.group(1))], SEFIROT[int(match.group(2))]]


def read_structure_summary() -> str:
    parts = []
    if STRUCTURE_JS.exists():
        text = STRUCTURE_JS.read_text(encoding="utf-8")
        columns = re.findall(r'title:\s*"([^"]+)"', text)
        parts.append(f"- `src/structure.js`: {len(columns)} table column declarations found.")
    for candidate in LIBER_JS_CANDIDATES:
        if candidate.exists():
            parts.append(f"- `{candidate.relative_to(REPO_ROOT)}` exists and can be used as a richer JS fallback.")
            break
    return "\n".join(parts) or "- No JavaScript structure fallback found."


def load_liber_js_rows() -> list[dict[str, Any]]:
    for candidate in LIBER_JS_CANDIDATES:
        if not candidate.exists():
            continue
        text = candidate.read_text(encoding="utf-8")
        match = re.search(r"export const Liber777 = (\[.*\]);?\s*$", text, re.S)
        if not match:
            continue
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
    return []


LIBER_JS_ROWS = load_liber_js_rows()


def load_js_path_attributions() -> dict[int, str]:
    for row in LIBER_JS_ROWS:
        if row.get("index") == "VII. Meanings of the Symbols":
            return {number: clean_text(row.get(str(number), "")) for number in PATHS}
    return {}


PATH_ATTRIBUTIONS = load_js_path_attributions()


def path_attribution_names(scale: ScaleNote) -> list[str]:
    values = []
    js_value = PATH_ATTRIBUTIONS.get(scale.number, "")
    if js_value:
        values.append(js_value)
    values.extend(split_entities(scale.row.get("11 - Elements & Rulers", ""), "other"))
    out: list[str] = []
    for value in values:
        canonical = normalize_entity_name(value)
        if canonical in PLANETS or canonical in ZODIAC or canonical in ELEMENTS:
            out.append(canonical)
    return sorted(set(out))


def ensure_dirs() -> None:
    for rel in MANAGED_DIRS:
        (VAULT_DIR / rel).mkdir(parents=True, exist_ok=True)
    for rel in FOLDER_FOR_ENTITY_TYPE.values():
        (VAULT_DIR / rel).mkdir(parents=True, exist_ok=True)


def reset_managed_dirs() -> None:
    for rel in MANAGED_DIRS:
        path = VAULT_DIR / rel
        if path.exists():
            shutil.rmtree(path)
    for file_name in ["README.md"]:
        path = VAULT_DIR / file_name
        if path.exists():
            path.unlink()
    ensure_dirs()


def dump_yaml(data: dict[str, Any]) -> str:
    def scalar(value: Any) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, int):
            return str(value)
        if value is None:
            return "null"
        text = str(value)
        if text == "":
            return '""'
        escaped = text.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

    def render(value: Any, indent: int = 0) -> list[str]:
        pad = " " * indent
        if isinstance(value, dict):
            lines: list[str] = []
            for key, item in value.items():
                if item == []:
                    lines.append(f"{pad}{key}: []")
                elif isinstance(item, (dict, list)):
                    lines.append(f"{pad}{key}:")
                    lines.extend(render(item, indent + 2))
                else:
                    lines.append(f"{pad}{key}: {scalar(item)}")
            return lines
        if isinstance(value, list):
            if not value:
                return [f"{pad}[]"]
            lines = []
            for item in value:
                if isinstance(item, (dict, list)):
                    lines.append(f"{pad}-")
                    lines.extend(render(item, indent + 2))
                else:
                    lines.append(f"{pad}- {scalar(item)}")
            return lines
        return [f"{pad}{scalar(value)}"]

    return "\n".join(render(data)).strip()


def write_note(path: Path, frontmatter: dict[str, Any], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{dump_yaml(frontmatter)}\n---\n\n{body.strip()}\n", encoding="utf-8")


def markdown_table(rows: list[tuple[str, str]]) -> str:
    lines = ["| Категория | Значения |", "|---|---|"]
    for key, value in rows:
        value = clean_text(value).replace("|", "\\|")
        lines.append(f"| {key} | {value or ''} |")
    return "\n".join(lines)


def escape_source_wikilinks(raw: str) -> str:
    return clean_text(raw).replace("[[", "\\[\\[").replace("]]", "\\]\\]")


def linked_value(raw: str, entities: list[str]) -> str:
    if not entities:
        return escape_source_wikilinks(raw)
    return ", ".join(wiki(entity) for entity in entities)


def build_scales(rows: list[dict[str, str]]) -> tuple[list[ScaleNote], list[ScaleNote]]:
    sefiros: list[ScaleNote] = []
    paths: list[ScaleNote] = []
    by_num = {row_number(row): row for row in rows if row_number(row) is not None}
    for number, name in SEFIROT.items():
        sefiros.append(ScaleNote(number=number, name=name, kind="sefirah", row=by_num[number]))
    for number, name in PATHS.items():
        row = by_num[number]
        paths.append(ScaleNote(number=number, name=name, kind="path", row=row, connects=parse_connects(row)))
    return sefiros, paths


def add_entity(
    entities: dict[str, Entity],
    name: str,
    entity_type: str,
    appears_in: str,
    source_row: int,
    raw_value: str,
    source_ref: str | None = None,
) -> None:
    name = normalize_entity_name(name)
    if not is_probably_atomic(name, entity_type):
        return
    existing = entities.get(name)
    if existing and existing.entity_type != entity_type:
        if ENTITY_TYPE_PRIORITY.get(entity_type, 0) <= ENTITY_TYPE_PRIORITY.get(existing.entity_type, 0):
            entity_type = existing.entity_type
    entity = entities.setdefault(name, Entity(name=name, entity_type=entity_type))
    if ENTITY_TYPE_PRIORITY.get(entity_type, 0) > ENTITY_TYPE_PRIORITY.get(entity.entity_type, 0):
        entity.entity_type = entity_type
    entity.appears_in.add(appears_in)
    entity.source_rows.add(source_row)
    if source_ref:
        entity.source_refs.add(source_ref)
    entity.raw_values.add(clean_text(raw_value))


def js_entity_kind(index: str) -> str | None:
    lowered = index.lower()
    if "goetic demons" in lowered or "demon kings" in lowered or "qliphoth" in lowered:
        return "demon"
    if "spirits of the planets" in lowered or "olympic planetary spirits" in lowered or "elemental spirits" in lowered:
        return "spirit"
    if "archangels" in lowered or "angels" in lowered or "intelligences" in lowered:
        return "angel"
    return None


def should_use_js_entity_row(index: str) -> bool:
    lowered = index.lower()
    if js_entity_kind(index) is None:
        return False
    # Prefer romanized/English rows where paired Hebrew rows exist.
    if any(term in lowered for term in ["hebrew", "number", "planet", "image"]):
        return False
    if "transliteration" in lowered or "transliterated" in lowered or "(transl" in lowered:
        return True
    if "goetic demons" in lowered or "qliphoth" in lowered:
        return False
    return any(term in lowered for term in ["demon kings", "olympic planetary spirits"])


def add_js_entity_rows(entities: dict[str, Entity], scales_by_number: dict[int, ScaleNote]) -> None:
    for row_index, row in enumerate(LIBER_JS_ROWS):
        index = clean_text(row.get("index", ""))
        previous_index = clean_text(LIBER_JS_ROWS[row_index - 1].get("index", "")) if row_index > 0 else ""
        is_goetic_transliteration = "transl" in index.lower() and "goetic demons" in previous_index.lower()
        if not should_use_js_entity_row(index) and not is_goetic_transliteration:
            continue
        kind = "demon" if is_goetic_transliteration else js_entity_kind(index)
        if kind is None:
            continue
        source_index = previous_index if is_goetic_transliteration else index
        for number in range(1, 33):
            scale = scales_by_number.get(number)
            if not scale:
                continue
            scale_link = f"{scale.number:02d} {scale.name}" if scale.kind == "sefirah" else f"{scale.number} {scale.name}"
            raw = clean_text(row.get(str(number), ""))
            for name in split_entities(raw, kind):
                add_entity(
                    entities,
                    name,
                    kind,
                    scale_link,
                    number,
                    raw,
                    source_ref=f"{JS_SOURCE['file']} :: {source_index}",
                )
                if name not in scale.entities:
                    scale.entities.append(name)


def collect_entities(sefiros: list[ScaleNote], paths: list[ScaleNote]) -> dict[str, Entity]:
    entities: dict[str, Entity] = {}
    all_scales = sefiros + paths
    scales_by_number = {scale.number: scale for scale in all_scales}

    for scale in all_scales:
        scale_link = f"{scale.number:02d} {scale.name}" if scale.kind == "sefirah" else f"{scale.number} {scale.name}"
        row = scale.row
        number = scale.number
        local_entities: set[str] = set()

        if scale.kind == "path":
            add_entity(entities, scale.name, "hebrew_letter", scale_link, number, scale.name)
            local_entities.add(scale.name)
            for name in path_attribution_names(scale):
                if name in PLANETS:
                    kind = "planet"
                elif name in ZODIAC:
                    kind = "zodiac"
                elif name in ELEMENTS:
                    kind = "element"
                else:
                    kind = "other"
                name = normalize_entity_name(name)
                add_entity(entities, name, kind, scale_link, number, row.get("11 - Elements & Rulers", ""))
                local_entities.add(name)

        for col, kind in ENTITY_COLUMNS.items():
            raw = row.get(col, "")
            if col == "14 - General Attribution of Tarot":
                pairs = tarot_entities(raw)
            else:
                pairs = [(name, kind) for name in split_entities(raw, kind)]
            for name, entity_type in pairs:
                add_entity(entities, name, entity_type, scale_link, number, raw)
                local_entities.add(normalize_entity_name(name))

        for col, raw in row.items():
            if col == "Category" or col in ENTITY_COLUMNS:
                continue
            for name in explicit_wikilink_entities(raw):
                add_entity(entities, name, "other", scale_link, number, raw)
                local_entities.add(normalize_entity_name(name))

        if scale.kind == "path":
            for connected in scale.connects:
                local_entities.add(connected)

        scale.entities = sorted(local_entities)

    add_js_entity_rows(entities, scales_by_number)
    for scale in all_scales:
        scale.entities = sorted(set(scale.entities))

    for scale in all_scales:
        neighbors = set(scale.entities)
        scale_link = f"{scale.number:02d} {scale.name}" if scale.kind == "sefirah" else f"{scale.number} {scale.name}"
        for name in scale.entities:
            if name in entities:
                entities[name].related_entities.update(neighbors - {name})
                entities[name].appears_in.add(scale_link)

    return entities


def path_filename(scale: ScaleNote) -> str:
    return f"{scale.number} {slugify_filename(scale.name)}.md"


def sefirah_filename(scale: ScaleNote) -> str:
    return f"{scale.number:02d} {slugify_filename(scale.name)}.md"


def generate_sefirah(scale: ScaleNote, paths: list[ScaleNote]) -> None:
    linked_paths = [wiki(f"{p.number} {p.name}") for p in paths if scale.name in p.connects]
    prev_link = wiki(f"{scale.number - 1:02d} {SEFIROT[scale.number - 1]}") if scale.number > 1 else None
    next_link = wiki(f"{scale.number + 1:02d} {SEFIROT[scale.number + 1]}") if scale.number < 10 else None
    frontmatter = {
        "type": "sefirah",
        "number": scale.number,
        "name": scale.name,
        "aliases": [scale.name],
        "hebrew_name": scale.row.get("2 - Hebrew Names", ""),
        "tree_node": True,
        "up": [wiki("Tree of Life")],
        "prev": [prev_link] if prev_link else [],
        "next": [next_link] if next_link else [],
        "paths": linked_paths,
        "corresponds_to": [wiki(entity) for entity in scale.entities if entity not in SEFIROT.values()],
        "correspondences": {
            "tarot": [wiki(name) for name in split_entities(scale.row.get("14 - General Attribution of Tarot", ""), "tarot")],
            "planets": [],
            "deities": [wiki(name) for name in split_entities(scale.row.get("19 - Egyption Gods", ""), "deity")],
            "angels": [],
            "colors": [wiki(name) for col in ["15 - The King Scale Colors (Yud)", "16 - Queen Scale Colors (Heh)", "17 - Emperor Scale Colors (Vav)", "18 - Empress Scale Colors (Heh)"] for name in split_entities(scale.row.get(col, ""), "color")],
        },
        "tags": ["liber777", "sefirah", "tree-of-life"],
        "source": SOURCE,
    }
    summary = []
    for col in SUMMARY_COLUMNS:
        if col not in scale.row:
            continue
        raw = scale.row.get(col, "")
        if col in ENTITY_COLUMNS:
            summary.append((col, linked_value(raw, split_entities(raw, ENTITY_COLUMNS[col]))))
        else:
            summary.append((col, raw))
    all_rows = [(col, escape_source_wikilinks(scale.row.get(col, ""))) for col in scale.row if col != "Category"]
    entities = "\n".join(f"- {wiki(entity)}" for entity in scale.entities) or "- Нет уверенно выделенных сущностей."
    body = f"""# {scale.number:02d} {scale.name}

## Кратко

Данные собраны автоматически из строки шкалы {scale.number}. Отдельного описания в исходном CSV нет.

## Положение на Древе Жизни

- Номер: {scale.number}
- Тип: Сфира
- Связанные пути:
{chr(10).join(f'  - {link}' for link in linked_paths) if linked_paths else '  - Нет данных'}

## Основные соответствия

{markdown_table(summary)}

## Все соответствия

{markdown_table(all_rows)}

## Связанные сущности

{entities}

## Исходные данные

- open_777
- docs/liber_777.csv
- номер строки / номер шкалы: {scale.number}
"""
    write_note(VAULT_DIR / "01 Sefirot" / sefirah_filename(scale), frontmatter, body)


def generate_path(scale: ScaleNote) -> None:
    prev_link = wiki(f"{scale.number - 1} {PATHS[scale.number - 1]}") if scale.number > 11 else None
    next_link = wiki(f"{scale.number + 1} {PATHS[scale.number + 1]}") if scale.number < 32 else None
    tarot_links = [wiki(name) for name, _ in tarot_entities(scale.row.get("14 - General Attribution of Tarot", ""))]
    astrology = {"planets": [], "zodiac": [], "elements": []}
    for name in path_attribution_names(scale):
        canonical = normalize_entity_name(name)
        if canonical in PLANETS:
            astrology["planets"].append(wiki(canonical))
        elif canonical in ZODIAC:
            astrology["zodiac"].append(wiki(canonical))
        elif canonical in ELEMENTS:
            astrology["elements"].append(wiki(canonical))
    connect_links = [wiki(name) for name in scale.connects]
    frontmatter = {
        "type": "path",
        "number": scale.number,
        "name": scale.name,
        "aliases": [f"{scale.number} {scale.name}"],
        "hebrew_letter": wiki(scale.name),
        "tarot": tarot_links,
        "astrology": astrology,
        "connects": connect_links,
        "up": [wiki("Tree of Life")],
        "prev": [prev_link] if prev_link else [],
        "next": [next_link] if next_link else [],
        "corresponds_to": [wiki(entity) for entity in scale.entities],
        "tags": ["liber777", "path", "tree-of-life", "hebrew-letter"],
        "source": SOURCE,
    }
    summary = []
    for col in SUMMARY_COLUMNS:
        if col not in scale.row:
            continue
        raw = scale.row.get(col, "")
        if col in ENTITY_COLUMNS:
            summary.append((col, linked_value(raw, split_entities(raw, ENTITY_COLUMNS[col]))))
        else:
            summary.append((col, raw))
    all_rows = [(col, escape_source_wikilinks(scale.row.get(col, ""))) for col in scale.row if col != "Category"]
    crossings = sorted(set(scale.entities) | set(scale.connects))
    body = f"""# {scale.number} {scale.name}

## Кратко

- Номер: {scale.number}
- Тип: Путь
- Еврейская буква: {wiki(scale.name)}
- Таро: {', '.join(tarot_links) if tarot_links else 'Нет данных'}
- Планета / знак / стихия: {', '.join(astrology['planets'] + astrology['zodiac'] + astrology['elements']) if any(astrology.values()) else clean_text(scale.row.get('11 - Elements & Rulers', '')) or 'Нет данных'}
- Соединяет: {' ↔ '.join(connect_links) if connect_links else 'Нет данных'}

## Место на Древе Жизни

{('Связь между ' + ' и '.join(connect_links) + '.') if connect_links else 'В исходных данных нет уверенно разобранной связи со сфирами.'}

## Основные соответствия

{markdown_table(summary)}

## Все соответствия

{markdown_table(all_rows)}

## Смысловые переклички

{chr(10).join(f'- {wiki(entity)}' for entity in crossings) if crossings else '- Нет уверенно выделенных сущностей.'}

## Исходные данные

- open_777
- docs/liber_777.csv
- номер строки / номер шкалы: {scale.number}
"""
    write_note(VAULT_DIR / "02 Paths" / path_filename(scale), frontmatter, body)


def entity_path(entity: Entity) -> Path:
    folder = FOLDER_FOR_ENTITY_TYPE.get(entity.entity_type, FOLDER_FOR_ENTITY_TYPE["other"])
    return VAULT_DIR / folder / f"{slugify_filename(entity.name)}.md"


def generate_entity(entity: Entity) -> None:
    frontmatter = {
        "type": "entity",
        "entity_type": entity.entity_type,
        "name": entity.name,
        "up": [wiki("Entity Index")],
        "appears_in": [wiki(name) for name in sorted(entity.appears_in)],
        "related": {
            "tarot": [wiki(name) for name in sorted(entity.related_entities) if name in ENTITY_ALIASES.values()],
            "hebrew_letters": [wiki(name) for name in sorted(entity.related_entities) if name in PATHS.values()],
            "sefiros": [wiki(name) for name in sorted(entity.related_entities) if name in SEFIROT.values()],
            "paths": [wiki(name) for name in sorted(entity.appears_in) if re.match(r"^(1[1-9]|2[0-9]|3[0-2]) ", name)],
        },
        "related_entities": [wiki(name) for name in sorted(entity.related_entities) if name != entity.name],
        "tags": ["liber777", "entity", entity.entity_type],
        "source": SOURCE,
    }
    body = f"""# {entity.name}

## Тип

{entity.entity_type.replace('_', ' ').title()}.

## Где встречается

{chr(10).join(f'- {wiki(name)}' for name in sorted(entity.appears_in)) if entity.appears_in else '- Нет данных.'}

## Связанные соответствия

{chr(10).join(f'- {wiki(name)}' for name in sorted(entity.related_entities) if name != entity.name) if entity.related_entities else '- Нет данных.'}

## Dataview

```dataview
LIST
FROM "01 Sefirot" OR "02 Paths"
WHERE contains(file.outlinks, this.file.link)
```

## Исходные данные

- open_777
- docs/liber_777.csv
- строки исходной таблицы: {', '.join(str(n) for n in sorted(entity.source_rows))}
- дополнительные JS-источники: {', '.join(sorted(entity.source_refs)) if entity.source_refs else 'нет'}
- raw значения: {', '.join(escape_source_wikilinks(value) for value in sorted(entity.raw_values))}
"""
    write_note(entity_path(entity), frontmatter, body)


def write_index_pages(sefiros: list[ScaleNote], paths: list[ScaleNote], entities: dict[str, Entity]) -> None:
    sefirah_links = "\n".join(f"- {wiki(f'{s.number:02d} {s.name}')}" for s in sefiros)
    path_links = "\n".join(f"- {wiki(f'{p.number} {p.name}')}" for p in paths)
    categories = "\n".join(f"- {label}: {folder}" for label, folder in sorted(FOLDER_FOR_ENTITY_TYPE.items()))
    home = f"""# Liber 777 Knowledge Vault

## Основные разделы

- [[Tree of Life]]
- [[All Correspondences]]
- [[Sefirot Table]]
- [[Paths Table]]
- [[Entity Index]]
- [[Tarot Table]]
- [[Planetary Correspondences]]
- [[Zodiac Correspondences]]
- [[Elemental Correspondences]]

## Быстрый вход

### Сфиры

{sefirah_links}

### Пути

{path_links}

### Сущности

{categories}
"""
    write_note(VAULT_DIR / "00 Index" / "Home.md", {"type": "index", "tags": ["liber777", "index"]}, home)

    tree_rows = "\n".join(f"- {wiki(f'{p.number} {p.name}')}: {' ↔ '.join(wiki(c) for c in p.connects) if p.connects else 'нет данных'}" for p in paths)
    tree = f"""# Tree of Life

## Сфиры

{sefirah_links}

## Пути

{path_links}

## Связи путей со сфирами

{tree_rows}

## Граф

Граф Obsidian строится через wiki-links между сфирами, путями и сущностями соответствий. Связи путей взяты из колонки `12 - Tree of Life` исходного CSV.
"""
    write_note(VAULT_DIR / "00 Index" / "Tree of Life.md", {"type": "index", "tags": ["liber777", "tree-of-life"]}, tree)

    all_corr = """# All Correspondences

Полные raw-таблицы находятся в каждой заметке сфиры и пути в разделе `Все соответствия`.

```dataview
TABLE number, name, type, source.file
FROM "01 Sefirot" OR "02 Paths"
WHERE contains(tags, "liber777")
SORT number ASC
```
"""
    write_note(VAULT_DIR / "00 Index" / "All Correspondences.md", {"type": "index", "tags": ["liber777", "correspondences"]}, all_corr)

    howto = """# How to Use This Vault

## Рекомендуемые плагины

1. Dataview - таблицы, списки и запросы по YAML metadata.
2. Metadata Menu - удобное редактирование типизированных полей заметок.
3. Breadcrumbs - навигация по полям `up`, `prev`, `next`, `connects`, `corresponds_to`.
4. ExcaliBrain - визуальное исследование связей между заметками.
5. Database Folder - табличный просмотр сущностей и соответствий.
6. Linter - единый стиль Markdown и YAML frontmatter.

## Начало работы

Откройте [[Home]], затем переходите к [[Tree of Life]], таблицам Dataview и заметкам сущностей. Graph View и ExcaliBrain становятся полезнее после включения wiki-links и Dataview.
"""
    write_note(VAULT_DIR / "00 Index" / "How to Use This Vault.md", {"type": "guide", "tags": ["liber777", "guide"]}, howto)


def write_dashboards() -> None:
    dashboards = {
        "Sefirot Table.md": """# Sefirot Table

```dataview
TABLE number, name, paths
FROM "01 Sefirot"
WHERE type = "sefirah"
SORT number ASC
```""",
        "Paths Table.md": """# Paths Table

```dataview
TABLE number, name, hebrew_letter, tarot, astrology.planets, astrology.zodiac, astrology.elements, connects
FROM "02 Paths"
WHERE type = "path"
SORT number ASC
```""",
        "Tarot Table.md": """# Tarot Table

```dataview
TABLE appears_in, related.hebrew_letters, related.paths
FROM "03 Tarot"
SORT file.name ASC
```""",
        "Planetary Correspondences.md": """# Planetary Correspondences

```dataview
TABLE appears_in, related_entities
FROM "05 Astrology/Planets"
WHERE type = "entity"
SORT file.name ASC
```""",
        "Zodiac Correspondences.md": """# Zodiac Correspondences

```dataview
TABLE appears_in, related_entities
FROM "05 Astrology/Zodiac"
WHERE type = "entity"
SORT file.name ASC
```""",
        "Elemental Correspondences.md": """# Elemental Correspondences

```dataview
TABLE appears_in, related_entities
FROM "05 Astrology/Elements"
WHERE type = "entity"
SORT file.name ASC
```""",
        "Entity Index.md": """# Entity Index

```dataview
TABLE entity_type, appears_in
FROM "06 Entities"
WHERE type = "entity"
SORT entity_type ASC, file.name ASC
```""",
    }
    for name, body in dashboards.items():
        write_note(VAULT_DIR / "90 Dashboards" / name, {"type": "dashboard", "tags": ["liber777", "dashboard"]}, body)


def write_templates() -> None:
    templates = {
        "sefirah_template.md": "# {{number}} {{name}}\n\n## Кратко\n\n## Correspondences\n",
        "path_template.md": "# {{number}} {{name}}\n\n## Кратко\n\n## Connects\n",
        "entity_template.md": "# {{name}}\n\n## Тип\n\n## Где встречается\n",
    }
    for name, body in templates.items():
        (VAULT_DIR / "_templates" / name).write_text(body, encoding="utf-8")


def write_source_files(rows: list[dict[str, str]]) -> None:
    shutil.copy2(CSV_PATH, VAULT_DIR / "_source" / "liber_777.csv")
    columns = list(rows[0].keys()) if rows else []
    source_info = f"""# Source Info

- Repository: open_777
- CSV: `docs/liber_777.csv`
- Rows: {len(rows)}
- Columns: {len(columns)}
- Sefirot rows: 1-10
- Path rows: 11-32
- Extra rows preserved in CSV but not promoted to path notes: `32 bis`, `31 bis`

## CSV Columns

{chr(10).join(f'- {column}' for column in columns)}

## JavaScript Source Check

{read_structure_summary()}
"""
    (VAULT_DIR / "_source" / "source_info.md").write_text(source_info, encoding="utf-8")


def write_gitkeep_for_empty_dirs() -> None:
    for folder in [VAULT_DIR / rel for rel in FOLDER_FOR_ENTITY_TYPE.values()]:
        if not any(folder.iterdir()):
            (folder / ".gitkeep").write_text("", encoding="utf-8")


def write_readme(report: dict[str, int]) -> None:
    readme = f"""# Liber 777 Obsidian Vault

This vault was generated from the Open 777 repository data in `docs/liber_777.csv`.

## What Is Included

- {report['sefiros']} sefirah notes.
- {report['paths']} path notes.
- {report['entities']} entity notes across Tarot, Hebrew letters, astrology, deities, plants, stones, perfumes, colors, animals, magical weapons, and other categories.
- Index pages and Dataview dashboards.

## Rebuild

From the repository root:

```bash
python3 _scripts/generate_vault.py
```

Install dependencies first if needed:

```bash
python3 -m pip install -r _scripts/requirements.txt
```

## Recommended Obsidian Plugins

1. Dataview
2. Metadata Menu
3. Breadcrumbs
4. ExcaliBrain
5. Database Folder
6. Linter

## How to Use

Start at `00 Index/Home.md`, then open the sefirah and path notes, browse entity notes, run Dataview dashboards, and use Graph View or ExcaliBrain to inspect wiki-link relationships.
"""
    (VAULT_DIR / "README.md").write_text(readme, encoding="utf-8")


def main() -> None:
    if not CSV_PATH.exists():
        raise SystemExit(f"Missing source CSV: {CSV_PATH}")

    rows = load_rows()
    sefiros, paths = build_scales(rows)
    entities = collect_entities(sefiros, paths)

    reset_managed_dirs()
    for sefirah in sefiros:
        generate_sefirah(sefirah, paths)
    for path in paths:
        generate_path(path)
    for entity in sorted(entities.values(), key=lambda e: (e.entity_type, e.name)):
        generate_entity(entity)
    write_index_pages(sefiros, paths, entities)
    write_dashboards()
    write_templates()
    write_source_files(rows)
    write_gitkeep_for_empty_dirs()

    counts = defaultdict(int)
    for entity in entities.values():
        counts[entity.entity_type] += 1
    report = {
        "sefiros": len(sefiros),
        "paths": len(paths),
        "entities": len(entities),
        "dashboards": 7,
    }
    write_readme(report)

    print("Generated:")
    print(f"- {len(sefiros)} sefiros")
    print(f"- {len(paths)} paths")
    print(f"- {counts['tarot'] + counts['minor_tarot']} tarot notes")
    print(f"- {counts['planet'] + counts['zodiac'] + counts['element']} astrology notes")
    print(f"- {len(entities)} entity notes")
    print("- 7 dashboards")
    print(f"Output: {VAULT_DIR.relative_to(REPO_ROOT)}/")


if __name__ == "__main__":
    main()
