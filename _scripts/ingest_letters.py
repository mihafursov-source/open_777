#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ingest_letters.py — данные по буквам иврита в заметки 04 Hebrew Letters (in-place, идемпотентно).
Из CSV: значение буквы, гематрия, и соответствие карте Таро по ДВУМ школам (английской и
французской) — у них разные арканы для одной буквы. Источник — таблица пользователя.

  python3 _scripts/ingest_letters.py --dry
  python3 _scripts/ingest_letters.py
"""
import os, re, csv, argparse

V = "/Users/mikhail/open_777/obsidian_777_vault"
LD = os.path.join(V, "04 Hebrew Letters")
CSV = "/Users/mikhail/Downloads/Соответствия Букв Иврита - Лист1(1).csv"

LET_NOTE = {"Алеф": "Aleph", "Бет": "Beth", "Гимель": "Gimel", "Далет": "Daleth", "Хе": "Heh",
            "Вав": "Vav", "Заин": "Zayin", "Хет": "Cheth", "Тет": "Teth", "Йод": "Yod",
            "Каф": "Kaph", "Ламед": "Lamed", "Мем": "Mem", "Нун": "Nun", "Самех": "Samekh",
            "Айн": "Ayin", "Пе": "Pe", "Цадди": "Tzaddi", "Коф": "Qoph", "Реш": "Resh",
            "Шин": "Shin", "Тау": "Tav"}
ROMAN_NOTE = {"0": "The Fool", "I": "The Magician", "II": "The High Priestess", "III": "The Empress",
              "IV": "The Emperor", "V": "The Hierophant", "VI": "The Lovers", "VII": "The Chariot",
              "VIII": "Justice", "IX": "Hermit", "X": "Wheel of Fortune", "XI": "Strength",
              "XII": "The Hanged Man", "XIII": "Death", "XIV": "Temperance", "XV": "The Devil",
              "XVI": "The House of God", "XVII": "The Star", "XVIII": "The Moon", "XIX": "The Sun",
              "XX": None, "XXI": "The Universe"}  # XX (Эон/Суд) — отдельной заметки нет


def split_fm(t):
    e = t.find("\n---\n", 4)
    return (t[4:e].split("\n"), t[e + 5:]) if t.startswith("---\n") and e != -1 else (None, t)


def set_scalar(text, key, val):
    fm, body = split_fm(text)
    line = f'{key}: "{val}"'
    for i, l in enumerate(fm):
        if re.match(rf"^{key}:", l):
            fm[i] = line; break
    else:
        at = next((i for i, l in enumerate(fm) if re.match(r"^tags:", l)), len(fm))
        fm = fm[:at] + [line] + fm[at:]
    return "---\n" + "\n".join(fm) + "\n---\n" + body


def add_links(text, key, items):
    fm, body = split_fm(text)
    have, ki, end = set(), None, None
    for i, l in enumerate(fm):
        if re.match(rf"^{key}:\s*(\[\])?\s*$", l):
            ki = i
        elif ki is not None and end is None:
            mm = re.match(r'^\s+-\s*"?\[\[([^\]|]+)', l)
            if mm:
                have.add(mm.group(1).strip())
            elif re.match(r"^\S", l):
                end = i
    add = [x for x in items if x not in have]
    if not add:
        return text
    new = [f'  - "[[{x}]]"' for x in add]
    if ki is None:
        at = next((i for i, l in enumerate(fm) if re.match(r"^tags:", l)), len(fm))
        fm = fm[:at] + [f"{key}:"] + new + fm[at:]
    else:
        if re.search(r"\[\]\s*$", fm[ki]):
            fm[ki] = f"{key}:"
        ins = end if end is not None else len(fm)
        fm = fm[:ins] + new + fm[ins:]
    return "---\n" + "\n".join(fm) + "\n---\n" + body


def card_field(roman, ru_name):
    note = ROMAN_NOTE.get(roman)
    return (f"[[{note}]]", note) if note else (f"{ru_name} (нет заметки)", None)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry", action="store_true"); a = ap.parse_args()
    rows = list(csv.reader(open(CSV, encoding="utf-8-sig")))[1:]
    fr_roman = {r[6].strip(): (r[0].strip(), r[5].strip()) for r in rows}   # FR-буква -> (римск, имя)
    done = 0
    for r in rows:
        let = r[2].strip()                     # буква EN-школы = каноническая буква строки
        note = LET_NOTE.get(let)
        if not note:
            print("  ⚠ нет маппинга буквы:", let); continue
        path = os.path.join(LD, note + ".md")
        if not os.path.exists(path):
            print("  ⚠ нет заметки:", note); continue
        meaning, gem = r[10].strip(), r[3].strip()
        en_val, en_note = card_field(r[0].strip(), r[1].strip())
        fr_rom, fr_name = fr_roman.get(let, ("", ""))
        fr_val, fr_note = card_field(fr_rom, fr_name)
        if a.dry:
            print(f"  {note} ({let}): знач={meaning}, гем={gem}, EN={en_val}, FR={fr_val}")
            done += 1; continue
        t = open(path, encoding="utf-8").read()
        t = set_scalar(t, "letter_meaning", meaning)
        t = set_scalar(t, "gematria", gem)
        t = set_scalar(t, "tarot_english", en_val)
        t = set_scalar(t, "tarot_french", fr_val)
        cloud = [x for x in (en_note, fr_note) if x]
        if cloud:
            t = add_links(t, "corr_tarot", cloud)
        open(path, "w", encoding="utf-8").write(t)
        done += 1
    print(f"\n{'(dry-run) ' if a.dry else ''}букв обработано: {done}")


if __name__ == "__main__":
    main()
