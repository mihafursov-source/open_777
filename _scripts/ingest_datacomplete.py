#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ingest_datacomplete.py — Под-проект III, Tier 1 (in-place, аддитивно, идемпотентно).
Дозаливает из DataComplete.csv недостающие сущности-соответствия (6 пантеонов богов,
животные, растения, камни, благовония, оружие, клипот) в сфиры/пути.

Делает: dedup против существующих сущностей → создаёт недостающие заметки →
проставляет appears_in (обратная связь) → добавляет ссылки в corresponds_to сфиры/пути.
После него запусти fix_correspondences.py (пересоберёт corr_*) и audit_links.py.

  python3 _scripts/ingest_datacomplete.py --dry
  python3 _scripts/ingest_datacomplete.py
"""
import sys, os, re, csv, glob, argparse
sys.path.insert(0, "/Users/mikhail/open_777/_scripts")
from generate_vault import split_entities, normalize_entity_name, is_noise  # noqa

V = "/Users/mikhail/open_777/obsidian_777_vault"
ENT = os.path.join(V, "06 Entities")
DC = "/Users/mikhail/Downloads/Liber 777 - Aleister Crowley's Kabbalistic Correspondences - DataComplete.csv"

# (точное имя колонки, entity_type, папка)
TIER1 = [
 ("XIX. Selection of Egyptian Gods", "deity", "Deities"),
 ("XX. Practical Egyptian Gods", "deity", "Deities"),
 ("XXII. Small Selection of Hindu Deities", "deity", "Deities"),
 ("XXXIII. Some Scandinavian Gods", "deity", "Deities"),
 ("XXXIV. Some Greek Gods", "deity", "Deities"),
 ("XXXV. Some Roman Gods", "deity", "Deities"),
 ("XXXVI. Selefction of Christian Gods (10); Apostles (12); Evangelists(4); and Churches of Asia (7)", "deity", "Deities"),
 ("XXXVIII. Animals (Real & Imaginary)", "animal", "Animals"),
 ("XXXIX. Plants (Real & Imaginary)", "plant", "Plants"),
 ("XL. Precious Stones", "stone", "Stones"),
 ("XLII. Perfumes", "perfume", "Perfumes"),
 ("XLI. Magical Weapons", "magical_weapon", "Magical Weapons"),
 ("VII. Orders of the Qliphoth", "demon", "Demons"),
]

# Tier 2: для колонок с ивритским первоисточником берём ТРАНСЛИТЕРАЦИОННУЮ колонку (латиница).
# Шумные/описательные колонки (ады арабов с «жителями», алхим. металлы, имена Бога на иврите) — НЕ берём.
TIER2 = [
 ("LIX. Archangels of the Quarters Transliterated", "angel", "Angels"),
 ("LIX. Archangels of the Quarters", "angel", "Angels"),
 ("LXI. Angels of the Elements Transliterated", "angel", "Angels"),
 ("CXCIV. Intelligences (Transliteration)", "angel", "Angels"),
 ("LXXXV. Angels of Briah Transliteration", "angel", "Angels"),
 ("LXXXVI. Choirs of Angels in Briah Transliteration", "angel", "Angels"),
 ("XCIX. Archangels of Assiah Transliterated", "angel", "Angels"),
 ("C. Angels of Assiah Transliterated", "angel", "Angels"),
 ("CXCIII. Spirits of the Planets Transliteration.", "spirit", "Spirits"),
 ("LXXX. Olympic Planetary Spirits", "spirit", "Spirits"),
 ("XLVII. Kings and Princes of the Jinn", "spirit", "Spirits"),
 ("LX. Rulers of the Elements Transliterated", "spirit", "Spirits"),
 ("LXII. Kings of the Elemental Spirits", "spirit", "Spirits"),
 ("LXVIII. The Demon Kings", "demon", "Demons"),
 ("XXXVII. Hindu Legendary Demons", "demon", "Demons"),
 ("CVIII. Some Princes of the Qliphoth Transliterated", "demon", "Demons"),
 ("CIX. Kings of Edom Transliterated", "demon", "Demons"),
 ("CIX. Dukes of Edom Transliterated", "demon", "Demons"),
 ("LXXXI. Metals", "metal", "Metals"),
 ("XLIII. Vegetable Drugs", "drug", "Drugs"),
 ("XLIV. Mineral Drugs", "drug", "Drugs"),
]
TIERS = {1: TIER1, 2: TIER2}
EXTRA_NOISE = {"insufficient information", "n/a", "none", "unknown", "various"}


import unicodedata


def fold(name):
    """Жёсткий ключ дедупа: имя → нормализация генератора → склейка регистра/диакритики/пунктуации.
    Так «Heré»≡«Here», «Dragonís»≡«Dragon's» и т.п. матчатся с существующими заметками."""
    s = unicodedata.normalize("NFKD", normalize_entity_name(name)).lower()
    return "".join(ch for ch in s if ch.isalnum())


def slug(name):
    return re.sub(r'[\\/:*?"<>|]', "", name).strip()


def note_for_number(n):
    if 1 <= n <= 10:
        hits = glob.glob(os.path.join(V, "01 Sefirot", f"{n:02d} *.md"))
    else:
        hits = glob.glob(os.path.join(V, "02 Paths", f"{n} *.md"))
    return hits[0] if hits else None


def split_fm(t):
    if not t.startswith("---\n"):
        return None, t
    e = t.find("\n---\n", 4)
    return (t[4:e].split("\n"), t[e + 5:]) if e != -1 else (None, t)


def add_to_list(text, key, new_links):
    """Добавить [[ссылки]] в YAML-список key во frontmatter (создать блок при отсутствии)."""
    fm, body = split_fm(text)
    if fm is None:
        return text, 0
    have, ki, end = set(), None, None
    for i, l in enumerate(fm):
        if re.match(rf"^{re.escape(key)}:\s*(\[\])?\s*$", l):
            ki = i
        elif ki is not None and end is None:
            m = re.match(r'^\s+-\s*"?\[\[([^\]|]+)', l)
            if m:
                have.add(m.group(1).strip())
            elif re.match(r"^\S", l):
                end = i
    add = [n for n in new_links if n not in have]
    if not add:
        return text, 0
    items = [f'  - "[[{n}]]"' for n in add]
    if ki is None:                       # ключа нет — вставить перед tags/в конец
        at = next((i for i, l in enumerate(fm) if re.match(r"^tags:", l)), len(fm))
        fm = fm[:at] + [f"{key}:"] + items + fm[at:]
    else:
        if re.search(r"\[\]\s*$", fm[ki]):    # был key: []
            fm[ki] = f"{key}:"
        ins = end if end is not None else len(fm)
        fm = fm[:ins] + items + fm[ins:]
    return "---\n" + "\n".join(fm) + "\n---\n" + body, len(add)


def make_entity(name, etype, folder, appears, dry):
    path = os.path.join(ENT, folder, slug(name) + ".md")
    if os.path.exists(path):
        return os.path.splitext(os.path.basename(path))[0], False
    fm = ("---\n" 'type: "entity"\n' f'entity_type: "{etype}"\n' f'name: "{name}"\n'
          "up:\n  - \"[[Entity Index]]\"\n" "appears_in:\n" + "".join(f'  - "[[{a}]]"\n' for a in appears) +
          "tags:\n  - \"liber777\"\n  - \"entity\"\n" f"  - \"{etype}\"\n"
          "source:\n  repo: \"open_777\"\n  file: \"DataComplete.csv\"\n---\n\n"
          f"# {name}\n\n## Тип\n\n{etype.title()}.\n\n## Где встречается\n\n"
          + "".join(f"- [[{a}]]\n" for a in appears) + "\n## Источник\n\n- DataComplete.csv (Tier 1)\n")
    if not dry:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w", encoding="utf-8").write(fm)
    return slug(name), True


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry", action="store_true")
    ap.add_argument("--tier", type=int, default=1, choices=[1, 2]); a = ap.parse_args()
    COLS = TIERS[a.tier]
    rows = list(csv.reader(open(DC, encoding="utf-8-sig")))
    hdr = rows[0]
    colidx = {h: i for i, h in enumerate(hdr)}

    # индекс существующих сущностей: норм.имя -> basename
    # (включаем не только 06 Entities, но и планеты/буквы/числа/таро — чтобы
    #  Mars-бог не дублировал Mars-планету и т.п.)
    exist = {}
    for folder in ["06 Entities", "05 Astrology", "04 Hebrew Letters", "03 Tarot", "07 Numbers"]:
        for p in glob.glob(os.path.join(V, folder, "**", "*.md"), recursive=True):
            b = os.path.splitext(os.path.basename(p))[0]
            exist.setdefault(fold(b), b)

    # план: note_path -> set(entity basenames); entity basename -> (type,folder,set(note labels)); + new
    sef_add = {}              # note_path -> set(entity_basename)
    ent_back = {}             # entity_basename -> set(note_label)
    new_ents = {}             # basename -> (etype, folder)
    created = reused = 0

    for col, etype, folder in COLS:
        if col not in colidx:
            print("⚠ нет колонки:", col[:40]); continue
        ci = colidx[col]
        for r in rows[1:]:
            ks = r[0].strip()
            if not ks.isdigit():
                continue
            n = int(ks)
            note = note_for_number(n)
            if not note:
                continue
            label = os.path.splitext(os.path.basename(note))[0]
            for name in split_entities(r[ci] if ci < len(r) else "", etype):
                if not name or is_noise(name):
                    continue
                if name.strip().lower() in EXTRA_NOISE:
                    continue
                if re.search(r"[֐-׿]", name):   # иврит — пропускаем (нужна латиница)
                    continue
                norm = fold(name)
                if norm in exist:
                    base = exist[norm]; reused += 1
                else:
                    base = slug(name); exist[norm] = base
                    new_ents[base] = (etype, folder); created += 1
                sef_add.setdefault(note, set()).add(base)
                ent_back.setdefault(base, set()).add(label)

    print(f"Tier {a.tier}: уникальных привязок-сущностей: {len(ent_back)} | новых заметок: {len(new_ents)} | "
          f"(вхождений: создано={created}, переиспользовано={reused})")
    # по бакетам
    from collections import Counter
    print("  новые по типам:", dict(Counter(t for t, _ in new_ents.values())))

    if a.dry:
        print("\n(dry-run, без записи)"); return

    # 1) создать новые заметки
    for base, (etype, folder) in new_ents.items():
        make_entity(base, etype, folder, sorted(ent_back[base]), dry=False)
    # 2) обратные ссылки в существующие сущности
    for base, labels in ent_back.items():
        if base in new_ents:
            continue
        p = glob.glob(os.path.join(ENT, "**", base + ".md"), recursive=True)
        if not p:
            continue
        t = open(p[0], encoding="utf-8").read()
        t2, _ = add_to_list(t, "appears_in", sorted(labels))
        if t2 != t:
            open(p[0], "w", encoding="utf-8").write(t2)
    # 3) ссылки в corresponds_to сфир/путей
    for note, ents in sef_add.items():
        t = open(note, encoding="utf-8").read()
        t2, _ = add_to_list(t, "corresponds_to", sorted(ents))
        if t2 != t:
            open(note, "w", encoding="utf-8").write(t2)
    print("\nГотово. Запусти: fix_correspondences.py  затем  audit_links.py")


if __name__ == "__main__":
    main()
