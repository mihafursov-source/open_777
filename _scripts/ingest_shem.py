#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ingest_shem.py — Item 2 (вариант B): 72 ангела Шем ха-Мефораш (стандарт Золотой Зари).
Ангелы (2k-1, 2k) правят деканом k; декан → Младшая карта (2..10) по канону GD.
Привязывает пару ангелов к каждой числовой Младшей карте (corr_angels) + appears_in у ангела.
Источник — внешняя GD-данность (НЕ DataComplete), помечено в заметках.

  python3 _scripts/ingest_shem.py --dry
  python3 _scripts/ingest_shem.py
"""
import os, re, glob, argparse, unicodedata, sys
sys.path.insert(0, "/Users/mikhail/open_777/_scripts")
from generate_vault import normalize_entity_name

V = "/Users/mikhail/open_777/obsidian_777_vault"
MINOR = os.path.join(V, "03 Tarot", "Minor Arcana")
ANG = os.path.join(V, "06 Entities", "Angels")

SHEM = ["Vehuiah","Jeliel","Sitael","Elemiah","Mahasiah","Lelahel","Achaiah","Cahetel",
 "Haziel","Aladiah","Lauviah","Hahaiah","Iezalel","Mebahel","Hariel","Hekamiah",
 "Lauviah II","Caliel","Leuviah","Pahaliah","Nelchael","Yeiayel","Melahel","Haheuiah",
 "Nith-Haiah","Haaiah","Yerathel","Seheiah","Reiyel","Omael","Lecabel","Vasariah",
 "Yehuiah","Lehahiah","Chavakiah","Menadel","Aniel","Haamiah","Rehael","Ieiazel",
 "Hahahel","Mikael","Veualiah","Yelahiah","Sealiah","Ariel","Asaliah","Mihael",
 "Vehuel","Daniel","Hahasiah","Imamiah","Nanael","Nithael","Mebahiah","Poyel",
 "Nemamiah","Yeialel","Harahel","Mitzrael","Umabel","Iah-Hel","Anauel","Mehiel",
 "Damabiah","Manakel","Eyael","Habuhiah","Rochel","Jabamiah","Haiaiel","Mumiah"]

# зодиак-порядок деканов → (масть EN, [числа 3 деканов])
SIGN_CARDS = [("Wands",[2,3,4]),("Disks",[5,6,7]),("Swords",[8,9,10]),
              ("Cups",[2,3,4]),("Wands",[5,6,7]),("Disks",[8,9,10]),
              ("Swords",[2,3,4]),("Cups",[5,6,7]),("Wands",[8,9,10]),
              ("Disks",[2,3,4]),("Swords",[5,6,7]),("Cups",[8,9,10])]
SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio",
         "Sagittarius","Capricorn","Aquarius","Pisces"]
SUIT_RU = {"Wands":"Жезлы","Cups":"Чаши","Swords":"Мечи","Disks":"Пентакли"}


def fold(n):
    s = unicodedata.normalize("NFKD", normalize_entity_name(n)).lower()
    return "".join(c for c in s if c.isalnum())


def split_fm(t):
    e = t.find("\n---\n", 4)
    return (t[4:e].split("\n"), t[e + 5:]) if t.startswith("---\n") and e != -1 else (None, t)


def add_items(text, key, items, link):
    fm, body = split_fm(text)
    if fm is None:
        # у карты может не быть frontmatter — создать
        fm, body = [], text
    have, ki, end = set(), None, None
    for i, l in enumerate(fm):
        if re.match(rf"^{key}:\s*(\[\])?\s*$", l):
            ki = i
        elif ki is not None and end is None:
            mm = re.match(r'^\s+-\s*"?(.+?)"?\s*$', l)
            if mm:
                have.add(mm.group(1).strip().strip("[]"))
            elif re.match(r"^\S", l):
                end = i
    add = [x for x in items if x.strip("[]") not in have]
    if not add:
        return text
    fmt = (lambda x: f'  - "[[{x}]]"') if link else (lambda x: f'  - "{x}"')
    new = [fmt(x) for x in add]
    if ki is None:
        at = next((i for i, l in enumerate(fm) if re.match(r"^tags:", l)), len(fm))
        fm = fm[:at] + [f"{key}:"] + new + fm[at:]
    else:
        if re.search(r"\[\]\s*$", fm[ki]):
            fm[ki] = f"{key}:"
        ins = end if end is not None else len(fm)
        fm = fm[:ins] + new + fm[ins:]
    return "---\n" + "\n".join(fm) + "\n---\n" + body


def card_index():
    """(масть_ru, число) -> путь карты (по frontmatter suit+number)."""
    idx = {}
    for p in glob.glob(os.path.join(MINOR, "The 4 *", "*.md")):
        b = os.path.splitext(os.path.basename(p))[0]
        if b.startswith("The 4 "):
            continue
        t = open(p, encoding="utf-8").read()
        ms = re.search(r'^suit:\s*"([^"]+)"', t, re.M)
        mn = re.search(r'number:\s*"\[\[[^|]+\|(\d+)\]\]"', t)
        if ms and mn:
            idx[(ms.group(1).strip(), int(mn.group(1)))] = p
    return idx


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry", action="store_true"); a = ap.parse_args()
    cards = card_index()
    # существующие сущности (дедуп)
    exist = {}
    for p in glob.glob(os.path.join(V, "06 Entities", "**", "*.md"), recursive=True):
        exist.setdefault(fold(os.path.splitext(os.path.basename(p))[0]),
                         os.path.splitext(os.path.basename(p))[0])
    # план: card_path -> [angel basenames]; angel -> (sign, card_label, new?)
    card_ang = {}; ang_info = {}
    for k in range(36):                      # деканы 0..35
        sign = SIGNS[k // 3]
        suit_en, nums = SIGN_CARDS[k // 3]
        num = nums[k % 3]
        key = (SUIT_RU[suit_en], num)
        cp = cards.get(key)
        if not cp:
            print("⚠ нет карты:", key); continue
        clabel = os.path.splitext(os.path.basename(cp))[0]
        for which in (2 * k, 2 * k + 1):     # день/ночь ангел
            name = SHEM[which]
            base = exist.get(fold(name), name)
            new = fold(name) not in exist
            if new:
                exist[fold(name)] = base
            card_ang.setdefault(cp, []).append(base)
            ang_info.setdefault(base, (sign, clabel, new))
    new_cnt = sum(1 for _, _, n in ang_info.values() if n)
    print(f"Шем: ангелов={len(ang_info)} (новых={new_cnt}), карт затронуто={len(card_ang)}")
    if a.dry:
        for cp, angs in list(card_ang.items())[:4]:
            print(f"  {os.path.basename(cp)}: {angs}")
        print("\n(dry-run)"); return

    # создать/обновить заметки ангелов
    for base, (sign, clabel, new) in ang_info.items():
        p = os.path.join(ANG, base + ".md")
        if new:
            fm = ("---\n" 'type: "entity"\n' 'entity_type: "angel"\n' f'name: "{base}"\n'
                  'aliases:\n  - "Shem angel"\n' "up:\n  - \"[[Entity Index]]\"\n"
                  f'appears_in:\n  - "[[{clabel}]]"\n  - "[[{sign}]]"\n'
                  'tags:\n  - "liber777"\n  - "entity"\n  - "angel"\n  - "shem"\n'
                  'source:\n  repo: "external"\n  file: "Shem HaMephorash (Golden Dawn standard)"\n---\n\n'
                  f"# {base}\n\n## Тип\n\nAngel (Shem ha-Mephorash).\n\n## Где встречается\n\n"
                  f"- [[{clabel}]]\n- [[{sign}]]\n\n## Источник\n\n- Shem ha-Mephorash, стандарт Золотой Зари (внешний)\n")
            os.makedirs(ANG, exist_ok=True); open(p, "w", encoding="utf-8").write(fm)
        else:
            t = open(p, encoding="utf-8").read()
            t = add_items(t, "appears_in", [clabel, sign], link=True)
            open(p, "w", encoding="utf-8").write(t)
    # привязать к картам
    for cp, angs in card_ang.items():
        t = open(cp, encoding="utf-8").read()
        open(cp, "w", encoding="utf-8").write(add_items(t, "corr_angels", angs, link=True))
    print("Готово. Запусти audit_links.py")


if __name__ == "__main__":
    main()
