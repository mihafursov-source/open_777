#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ingest_astro.py — астрологические соответствия картам Таро (in-place, идемпотентно).
Старшие (12 знаков), Младшие 2–10 (планета-в-знаке + декан), Дворы (зод. сектор, кроме Принцесс).
Тузы и Принцессы — без зодиака (помечаем). Добавляет corr_astrology (ссылки на 05 Astrology) +
читаемое поле astro. Источник — таблица пользователя (Книга Тота / GD).

  python3 _scripts/ingest_astro.py --dry
  python3 _scripts/ingest_astro.py
"""
import os, re, glob, argparse

V = "/Users/mikhail/open_777/obsidian_777_vault"
MA = os.path.join(V, "03 Tarot", "Major Arcana")
MIN = os.path.join(V, "03 Tarot", "Minor Arcana")
CC = os.path.join(MIN, "Court Cards")

PL_RU = {"Mars": "Марс", "Sun": "Солнце", "Venus": "Венера", "Saturn": "Сатурн",
         "Jupiter": "Юпитер", "Mercury": "Меркурий", "Moon": "Луна"}
SIGN_RU = {"Aries": "Овен", "Taurus": "Телец", "Gemini": "Близнецы", "Cancer": "Рак",
           "Leo": "Лев", "Virgo": "Дева", "Libra": "Весы", "Scorpio": "Скорпион",
           "Sagittarius": "Стрелец", "Capricorn": "Козерог", "Aquarius": "Водолей", "Pisces": "Рыбы"}
LOC = {"Aries": "в Овне", "Taurus": "в Тельце", "Gemini": "в Близнецах", "Cancer": "в Раке",
       "Leo": "во Льве", "Virgo": "в Деве", "Libra": "в Весах", "Scorpio": "в Скорпионе",
       "Sagittarius": "в Стрельце", "Capricorn": "в Козероге", "Aquarius": "в Водолее", "Pisces": "в Рыбах"}
GEN = {"Aries": "Овна", "Taurus": "Тельца", "Gemini": "Близнецов", "Cancer": "Рака", "Leo": "Льва",
       "Virgo": "Девы", "Libra": "Весов", "Scorpio": "Скорпиона", "Sagittarius": "Стрельца",
       "Capricorn": "Козерога", "Aquarius": "Водолея", "Pisces": "Рыб"}

# Старшие: знак -> имя заметки
MAJORS = {"Aries": "The Emperor", "Taurus": "The Hierophant", "Gemini": "The Lovers",
          "Cancer": "The Chariot", "Leo": "Strength", "Virgo": "Hermit", "Libra": "Justice",
          "Scorpio": "Death", "Sagittarius": "Temperance", "Capricorn": "The Devil",
          "Aquarius": "The Star", "Pisces": "The Moon"}

# Младшие 2-10: (масть_ru, число) -> (планета, знак, декан)
MINORS = {}
def _m(suit, data):
    for num, pl, sg, dc in data:
        MINORS[(suit, num)] = (pl, sg, dc)
_m("Жезлы", [(2,"Mars","Aries",1),(3,"Sun","Aries",2),(4,"Venus","Aries",3),
             (5,"Saturn","Leo",1),(6,"Jupiter","Leo",2),(7,"Mars","Leo",3),
             (8,"Mercury","Sagittarius",1),(9,"Moon","Sagittarius",2),(10,"Saturn","Sagittarius",3)])
_m("Чаши", [(2,"Venus","Cancer",1),(3,"Mercury","Cancer",2),(4,"Moon","Cancer",3),
            (5,"Mars","Scorpio",1),(6,"Sun","Scorpio",2),(7,"Venus","Scorpio",3),
            (8,"Saturn","Pisces",1),(9,"Jupiter","Pisces",2),(10,"Mars","Pisces",3)])
_m("Мечи", [(2,"Moon","Libra",1),(3,"Saturn","Libra",2),(4,"Jupiter","Libra",3),
            (5,"Venus","Aquarius",1),(6,"Mercury","Aquarius",2),(7,"Moon","Aquarius",3),
            (8,"Jupiter","Gemini",1),(9,"Mars","Gemini",2),(10,"Sun","Gemini",3)])
_m("Пентакли", [(2,"Jupiter","Capricorn",1),(3,"Mars","Capricorn",2),(4,"Sun","Capricorn",3),
                (5,"Mercury","Taurus",1),(6,"Moon","Taurus",2),(7,"Saturn","Taurus",3),
                (8,"Sun","Virgo",1),(9,"Venus","Virgo",2),(10,"Mercury","Virgo",3)])

# Дворы Тота -> папка/имя в хранилище + (знак1, знак2). Принцессы -> без зодиака.
SUIT_CC = {"Wands": "Жезлов", "Cups": "Чаш", "Swords": "Мечей", "Disks": "Пентаклей"}
COURTS = {  # (тип_папка, ru_титул): {масть: (s1,s2)}
 ("Kings", "Король"): {"Wands":("Scorpio","Sagittarius"),"Cups":("Aquarius","Pisces"),
                       "Swords":("Taurus","Gemini"),"Disks":("Leo","Virgo")},
 ("Queens", "Дама"): {"Wands":("Pisces","Aries"),"Cups":("Gemini","Cancer"),
                      "Swords":("Virgo","Libra"),"Disks":("Sagittarius","Capricorn")},
 ("Princes", "Рыцарь"): {"Wands":("Cancer","Leo"),"Cups":("Libra","Scorpio"),
                         "Swords":("Capricorn","Aquarius"),"Disks":("Aries","Taurus")},
}


def split_fm(t):
    e = t.find("\n---\n", 4)
    return (t[4:e].split("\n"), t[e + 5:]) if t.startswith("---\n") and e != -1 else (None, t)


def add_links(text, key, items):
    fm, body = split_fm(text)
    if fm is None:
        fm, body = [], text.lstrip("\n")
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
    if add:
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


def set_scalar(text, key, val):
    fm, body = split_fm(text)
    if fm is None:
        fm, body = [], text.lstrip("\n")
    line = f'{key}: "{val}"'
    for i, l in enumerate(fm):
        if re.match(rf"^{key}:", l):
            fm[i] = line
            break
    else:
        at = next((i for i, l in enumerate(fm) if re.match(r"^tags:", l)), len(fm))
        fm = fm[:at] + [line] + fm[at:]
    return "---\n" + "\n".join(fm) + "\n---\n" + body


def minor_index():
    idx = {}
    for p in glob.glob(os.path.join(MIN, "The 4 *", "*.md")):
        b = os.path.splitext(os.path.basename(p))[0]
        if b.startswith("The 4 "):
            continue
        t = open(p, encoding="utf-8").read()
        ms = re.search(r'^suit:\s*"([^"]+)"', t, re.M)
        mn = re.search(r'number:\s*"\[\[[^|]+\|(\d+)\]\]"', t)
        if ms and mn:
            idx[(ms.group(1).strip(), int(mn.group(1)))] = p
    return idx


def apply(path, links, astro, dry):
    if not os.path.exists(path):
        print("  ⚠ нет:", os.path.relpath(path, V)); return 0
    if not dry:
        t = open(path, encoding="utf-8").read()
        if links:
            t = add_links(t, "corr_astrology", links)
        t = set_scalar(t, "astro", astro)
        open(path, "w", encoding="utf-8").write(t)
    return 1


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry", action="store_true"); a = ap.parse_args()
    n = 0
    # Старшие
    for sg, name in MAJORS.items():
        n += apply(os.path.join(MA, name + ".md"), [sg], f"{SIGN_RU[sg]} (знак)", a.dry)
    # Младшие 2-10
    midx = minor_index()
    for (suit, num), (pl, sg, dc) in MINORS.items():
        p = midx.get((suit, num))
        if not p:
            print("  ⚠ нет младшей:", suit, num); continue
        n += apply(p, [pl, sg], f"{PL_RU[pl]} {LOC[sg]}, {dc}-й декан {GEN[sg]}", a.dry)
    # Дворы (Knight/Queen/Prince)
    for (folder, ru), suits in COURTS.items():
        for suit_en, (s1, s2) in suits.items():
            p = os.path.join(CC, folder, f"{ru} {SUIT_CC[suit_en]}.md")
            n += apply(p, [s1, s2], f"21° {GEN[s1]} — 20° {GEN[s2]}", a.dry)
    # Принцессы (Паж) — без зодиака
    for suit_en, suf in SUIT_CC.items():
        p = os.path.join(CC, "Princesses", f"Паж {suf}.md")
        n += apply(p, [], "без зодиакального соответствия (Принцесса — трон стихии)", a.dry)
    # Тузы — без зодиака
    for p in glob.glob(os.path.join(MIN, "The 4 Aces", "*.md")):
        if os.path.basename(p).startswith("The 4 "):
            continue
        n += apply(p, [], "без зодиакального соответствия (Туз — корень стихии)", a.dry)
    print(f"\n{'(dry-run) ' if a.dry else ''}обработано карт: {n}")


if __name__ == "__main__":
    main()
