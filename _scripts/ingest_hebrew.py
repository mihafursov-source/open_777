#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ingest_hebrew.py — добавляет ивритское написание букв (in-place, идемпотентно):
  буквы (04 Hebrew Letters): hebrew (глиф) + hebrew_spelled (написание из DataComplete);
  пути (02 Paths): hebrew (глиф буквы) во frontmatter + заполнение пустых «()» в теле-таблице.
Глифы — каноническая каббала; написание — DataComplete (II. Hebrew Names of the Paths).

  python3 _scripts/ingest_hebrew.py --dry | python3 _scripts/ingest_hebrew.py
"""
import os, re, csv, glob, argparse

V = "/Users/mikhail/open_777/obsidian_777_vault"
DC = "/Users/mikhail/Downloads/Liber 777 - Aleister Crowley's Kabbalistic Correspondences - DataComplete.csv"

GLYPH = {"Aleph":"א","Beth":"ב","Gimel":"ג","Daleth":"ד","Heh":"ה","Vav":"ו","Zayin":"ז",
 "Cheth":"ח","Teth":"ט","Yod":"י","Kaph":"כ","Lamed":"ל","Mem":"מ","Nun":"נ","Samekh":"ס",
 "Ayin":"ע","Pe":"פ","Tzaddi":"צ","Qoph":"ק","Resh":"ר","Shin":"ש","Tav":"ת"}


def spelled_map():
    rows = list(csv.reader(open(DC, encoding="utf-8-sig")))
    h = rows[0]; i = h.index("II. Hebrew Names of the Paths")
    it = h.index("II. Transliteration of the Hebrew Names of the Paths")
    m = {}
    for r in rows[1:]:
        if i < len(r) and it < len(r):
            heb, tr = r[i].strip(), r[it].strip()
            if heb and tr and not re.search(r"\s", heb):   # одиночное слово на иврите
                m[tr.lower()] = heb
    return m
SPELLED = spelled_map()


def split_fm(t):
    e = t.find("\n---\n", 4)
    return (t[4:e].split("\n"), t[e + 5:]) if t.startswith("---\n") and e != -1 else (None, t)


def set_scalar(text, key, val):
    fm, body = split_fm(text)
    if fm is None:
        return text
    line = f'{key}: "{val}"'
    for i, l in enumerate(fm):
        if re.match(rf"^{key}:", l):
            fm[i] = line; break
    else:
        at = next((i for i, l in enumerate(fm) if re.match(r"^(name|aliases):", l)), len(fm))
        fm = fm[:at + 1] + [line] + fm[at + 1:]
    return "---\n" + "\n".join(fm) + "\n---\n" + body


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry", action="store_true"); a = ap.parse_args()
    nl = npath = 0
    # буквы
    for note, gl in GLYPH.items():
        p = os.path.join(V, "04 Hebrew Letters", note + ".md")
        if not os.path.exists(p):
            print("  ⚠ нет буквы:", note); continue
        sp = SPELLED.get(note.lower(), "")
        spelled = f"({sp}) {note}" if sp else note
        if a.dry:
            print(f"  {note}: глиф {gl}, написание {spelled}"); nl += 1; continue
        t = open(p, encoding="utf-8").read()
        t = set_scalar(t, "hebrew", gl)
        t = set_scalar(t, "hebrew_spelled", spelled)
        open(p, "w", encoding="utf-8").write(t); nl += 1
    # пути
    for p in glob.glob(os.path.join(V, "02 Paths", "*.md")):
        base = os.path.splitext(os.path.basename(p))[0]
        letter = base.split(" ", 1)[1] if " " in base else base
        gl = GLYPH.get(letter)
        if not gl:
            continue
        if a.dry:
            npath += 1; continue
        t = open(p, encoding="utf-8").read()
        t = set_scalar(t, "hebrew", gl)
        sp = SPELLED.get(letter.lower(), gl)
        # заполнить пустые «( )» в строках таблицы «Hebrew Names»
        t = re.sub(r"(\|\s*[^|]*Hebrew Names\s*\|\s*[^|()]*?)\(\s*\)", rf"\1({sp})", t)
        open(p, "w", encoding="utf-8").write(t); npath += 1
    print(f"\n{'(dry-run) ' if a.dry else ''}буквы: {nl}, пути: {npath}")


if __name__ == "__main__":
    main()
