#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_script_names.py — Item 1: слить иврит-дубли заметок-сущностей в их латинские версии.
Для каждой ивритской заметки, чей транслит (из DataComplete) совпадает с существующей
латинской заметкой: перенести appears_in → латинскую, добавить иврит-алиас, перенаправить
[[иврит]] → [[латиница]] во всём vault, удалить ивритскую заметку. Коптские/греческие — оставить.

  python3 _scripts/fix_script_names.py --dry
  python3 _scripts/fix_script_names.py
"""
import csv, glob, os, re, unicodedata, sys, argparse
sys.path.insert(0, "/Users/mikhail/open_777/_scripts")
from generate_vault import normalize_entity_name

V = "/Users/mikhail/open_777/obsidian_777_vault"
DC = "/Users/mikhail/Downloads/Liber 777 - Aleister Crowley's Kabbalistic Correspondences - DataComplete.csv"


def fold(n):
    s = unicodedata.normalize("NFKD", normalize_entity_name(n)).lower()
    return "".join(c for c in s if c.isalnum())


def is_script(s):
    return bool(re.search(r"[֐-׿Ⲁ-ⳳα-ωΑ-Ω]", s))


def build_map():
    rows = list(csv.reader(open(DC, encoding="utf-8-sig")))
    hdr = rows[0]; m = {}
    for i, h in enumerate(hdr[:-1]):
        if not any(k in hdr[i + 1].lower() for k in ["translit", "transl", "eng", "english", "name"]):
            continue
        for r in rows[1:]:
            if i + 1 < len(r):
                a, b = r[i].strip(), r[i + 1].strip()
                if a and b and is_script(a) and not is_script(b):
                    aa = [x.strip() for x in re.split(r"[,;]| ו ", a) if x.strip()]
                    bb = [x.strip() for x in re.split(r"[,;]", b) if x.strip()]
                    if len(aa) == len(bb):
                        for x, y in zip(aa, bb):
                            if is_script(x) and not is_script(y):
                                m.setdefault(fold(x), y)
                    else:
                        m.setdefault(fold(a), bb[0] if bb else b)
    return m


def split_fm(t):
    e = t.find("\n---\n", 4)
    return (t[4:e].split("\n"), t[e + 5:]) if t.startswith("---\n") and e != -1 else (None, t)


def add_items(text, key, items, link):
    fm, body = split_fm(text)
    if fm is None:
        return text
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


def list_items(text, key):
    fm, _ = split_fm(text)
    if fm is None:
        return []
    out, grab = [], False
    for l in fm:
        if re.match(rf"^{key}:\s*$", l):
            grab = True; continue
        if grab:
            mm = re.match(r'^\s+-\s*"?\[\[([^\]|]+)', l)
            if mm:
                out.append(mm.group(1).strip())
            elif re.match(r"^\S", l):
                grab = False
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry", action="store_true"); a = ap.parse_args()
    m = build_map()
    latin = {}
    for p in glob.glob(os.path.join(V, "**", "*.md"), recursive=True):
        if "/.obsidian/" in p or "/_" in p[len(V):]:
            continue
        b = os.path.splitext(os.path.basename(p))[0]
        if not is_script(b):
            latin.setdefault(fold(b), p)
    merged = 0
    for hp in glob.glob(os.path.join(V, "06 Entities", "**", "*.md"), recursive=True):
        hb = os.path.splitext(os.path.basename(hp))[0]
        if not is_script(hb):
            continue
        lat = m.get(fold(hb))
        if not lat or fold(lat) not in latin:
            continue
        lp = latin[fold(lat)]
        latname = os.path.splitext(os.path.basename(lp))[0]
        print(f"{'(dry) ' if a.dry else ''}MERGE {hb} → {latname}")
        if a.dry:
            continue
        # 1) перенести appears_in в латинскую + алиас
        appin = list_items(open(hp, encoding="utf-8").read(), "appears_in")
        lt = open(lp, encoding="utf-8").read()
        lt = add_items(lt, "appears_in", appin, link=True)
        lt = add_items(lt, "aliases", [hb], link=False)
        open(lp, "w", encoding="utf-8").write(lt)
        # 2) перенаправить ссылки [[иврит]] → [[латиница]]
        pat = re.compile(r"\[\[" + re.escape(hb) + r"(\||\]\])")
        for p in glob.glob(os.path.join(V, "**", "*.md"), recursive=True):
            if os.path.abspath(p) in (os.path.abspath(hp),):
                continue
            t = open(p, encoding="utf-8").read()
            n = pat.sub(f"[[{latname}\\1", t)
            if n != t:
                open(p, "w", encoding="utf-8").write(n)
        # 3) удалить ивритскую
        os.remove(hp); merged += 1
    print(f"\n{'(dry-run) ' if a.dry else ''}слито: {merged}")


if __name__ == "__main__":
    main()
