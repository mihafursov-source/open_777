#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
repair_links.py — Под-проект II, ремонт связей (in-place, идемпотентно).
R1: создать хаб-заметку Minor Arcana.
R2: удалить висячие указатели «Отдельный файл источника: [[… - Bonner/path notes]]».
R3: связать числовые Младшие карты в граф (frontmatter: number/sefirah/up/suit).

  python3 _scripts/repair_links.py --dry
  python3 _scripts/repair_links.py
"""
import os, re, glob, argparse

V = "/Users/mikhail/open_777/obsidian_777_vault"
MINOR = os.path.join(V, "03 Tarot", "Minor Arcana")

GROUP_NUM = {"The 4 Aces": 1, "The 4 Twos": 2, "The 4 Threes": 3, "The 4 Fours": 4,
             "The 4 Fives": 5, "The 4 Sixes": 6, "The 4 Sevens": 7, "The 4 Eights": 8,
             "The 4 Nines": 9, "The 4 Tens": 10}
NUM_SEF = {1: "01 Kether", 2: "02 Chokmah", 3: "03 Binah", 4: "04 Chesed", 5: "05 Geburah",
           6: "06 Tiphareth", 7: "07 Netzach", 8: "08 Hod", 9: "09 Yesod", 10: "10 Malkuth"}
SUIT = {"Жезлов": "Жезлы", "Чаш": "Чаши", "Мечей": "Мечи", "Пентаклей": "Пентакли",
        "Динариев": "Динарии"}


def num_chislo():
    out = {}
    for p in glob.glob(os.path.join(V, "07 Numbers", "Число *.md")):
        b = os.path.splitext(os.path.basename(p))[0]
        m = re.match(r"Число (\d+)", b)
        if m:
            out[int(m.group(1))] = b
    return out
CHISLO = num_chislo()


def write(path, text, dry):
    if dry:
        return
    tmp = path + ".tmp"; open(tmp, "w", encoding="utf-8").write(text); os.replace(tmp, path)


# ---------- R1 ----------
def r1_hub(dry):
    p = os.path.join(MINOR, "Minor Arcana.md")
    groups = "\n".join(f"- [[{g}]]" for g in GROUP_NUM)
    body = ("---\ntype: \"index\"\nname: \"Minor Arcana\"\n"
            "aliases:\n  - \"Minor Arcana\"\n  - \"Младшие Арканы\"\n"
            "tags:\n  - \"liber777\"\n  - \"index\"\n---\n\n"
            "# Minor Arcana\n\nХаб Младших Арканов.\n\n"
            "## Числовые группы (масти ×4)\n" + groups + "\n\n"
            "## Дворы\n- [[Court Cards]]\n")
    existed = os.path.exists(p)
    write(p, body, dry)
    print(f"R1 хаб Minor Arcana.md — {'уже был, перезаписан' if existed else 'создан'}")


# ---------- R2 ----------
DANGLE = re.compile(r"^- Отдельный файл источника: \[\[[^\]]+ - (?:Bonner|path notes)\]\]\s*$", re.M)
def r2_dangling(dry):
    n = 0
    for folder in ["01 Sefirot", "02 Paths"]:
        for p in glob.glob(os.path.join(V, folder, "*.md")):
            t = open(p, encoding="utf-8").read()
            t2, c = DANGLE.subn("", t)
            if c:
                t2 = re.sub(r"\n{3,}", "\n\n", t2)   # схлопнуть пустоты после удаления
                write(p, t2, dry); n += c
    print(f"R2 удалено висячих указателей: {n}")


# ---------- R3 ----------
def card_frontmatter(num, suit_word, group):
    sef = NUM_SEF[num]; ch = CHISLO[num]
    lines = ["---", 'type: "minor_arcana"', f'number: "[[{ch}|{num}]]"']
    if suit_word:
        lines.append(f'suit: "{SUIT.get(suit_word, suit_word)}"')
    lines += [f'sefirah: "[[{sef}]]"', "up:", f'  - "[[{group}]]"', '  - "[[Minor Arcana]]"', "---", "", ""]
    return "\n".join(lines)


def r3_minors(dry):
    cards = groups = 0
    for group, num in GROUP_NUM.items():
        gdir = os.path.join(MINOR, group)
        if not os.path.isdir(gdir):
            continue
        for p in sorted(glob.glob(os.path.join(gdir, "*.md"))):
            base = os.path.splitext(os.path.basename(p))[0]
            t = open(p, encoding="utf-8").read()
            if t.startswith("---\n"):       # идемпотентность: уже есть frontmatter
                continue
            if base == group:               # сводная заметка группы
                fm = ("---\n" + 'type: "tarot_group"\n' + f'number: "[[{CHISLO[num]}|{num}]]"\n'
                      + f'sefirah: "[[{NUM_SEF[num]}]]"\n' + 'up:\n  - "[[Minor Arcana]]"\n---\n\n')
                write(p, fm + t, dry); groups += 1
            else:
                suit_word = base.split()[-1]
                write(p, card_frontmatter(num, suit_word, group) + t, dry); cards += 1
    print(f"R3 связано карт: {cards}, сводных заметок групп: {groups}")


def update_types(dry):
    import json
    tp = os.path.join(V, ".obsidian", "types.json")
    j = json.load(open(tp, encoding="utf-8"))
    j["types"]["sefirah"] = "multitext"; j["types"]["suit"] = "text"
    if not dry:
        json.dump(j, open(tp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("types.json: sefirah→multitext, suit→text")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry", action="store_true"); a = ap.parse_args()
    print(f"CHISLO map: {len(CHISLO)} чисел\n")
    r1_hub(a.dry); r2_dangling(a.dry); r3_minors(a.dry); update_types(a.dry)
    print("\n" + ("(dry-run)" if a.dry else "Готово."))


if __name__ == "__main__":
    main()
