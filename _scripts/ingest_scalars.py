#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ingest_scalars.py — Под-проект III, скаляры → тело (in-place, идемпотентно).
Добавляет в тело сфир/путей маркированную таблицу курированных СКАЛЯРНЫХ соответствий
из DataComplete (перевод пути, сознание адепта, магическая сила, мораль, грейд, образ,
чакра, части души, титул козыря…). Без HEX/нумераций/сырых транслитов/иврита.
Ссылок не добавляет — только текст-справку.

  python3 _scripts/ingest_scalars.py --dry
  python3 _scripts/ingest_scalars.py
"""
import os, re, csv, glob, argparse

V = "/Users/mikhail/open_777/obsidian_777_vault"
DC = "/Users/mikhail/Downloads/Liber 777 - Aleister Crowley's Kabbalistic Correspondences - DataComplete.csv"
START, END = "<!-- DC_SCALARS:START -->", "<!-- DC_SCALARS:END -->"

CURATED = [
 ("III. Translation of the Names of the Paths", "Перевод названия пути"),
 ("IV. Consciousness of the Adept", "Сознание адепта"),
 ("VII. Meanings of the Symbols", "Значение символов"),
 ("IX. The Sword and the Serpent", "Меч и Змей"),
 ("X. Mystic Numbers of the Sephiroth", "Мистическое число"),
 ("XI. The Elements and their Planetary Rulers", "Стихия / управитель"),
 ("XII. Position on the Glyph of the Tree of Life", "Положение на Древе"),
 ("XIII. Paths of the Sefer Yetzirah", "Путь Сефер Йецира"),
 ("XXI. The Perfected Man", "Совершенный человек"),
 ("XXIII. The Forty Buddhist Meditations", "Буддийская медитация"),
 ("XXIV. Certain of the Hindu/Buddhist Results", "Плод (инд./будд.)"),
 ("XLV. Magical Powers [Western Mysticism]", "Магическая сила"),
 ("XLVI. System of Taoism", "Даосизм"),
 ("L. Transcendental Morality (10 Virtues; 7 Deadly Sins; 4 Magic Powers)", "Трансц. мораль"),
 ("LV. The Elements and Senses", "Стихия и чувства"),
 ("LXIX. The Alchemical Elements", "Алхим. стихия"),
 ("LXX. Attribution of the Pentagram", "Атрибуция пентаграммы"),
 ("LXXV. Descriptions of the Tatwas", "Таттва"),
 ("LXXVI. The Five Skandhas (English)", "Скандха"),
 ("XCVIII. Parts of the Soul English", "Часть души"),
 ("CXVIII. The Chakras Meaning", "Чакра"),
 ("CXIX. The Ten Fetters (English)", "Путы (оковы)"),
 ("CXX. Magical Images of the Sephiroth", "Магический образ"),
 ("CXCI. The Four Noble Truths", "Благородная истина"),
 ("CXCII. The Noble Eightfold Path (English)", "Восьмеричный путь"),
 ("CXXI. Names of the Grades", "Грейд"),
 ("CLXXIX. Numbers printed on Tarot Trumps", "№ на козыре"),
 ("CLXXX. Title of Tarot Trumps", "Титул козыря"),
 ("CLXXXI. Correct Design of Tarot Trumps", "Верный дизайн козыря"),
 ("CLXXXII. The Human Body", "Тело человека"),
]


def clean(v):
    v = re.sub(r"\s+", " ", v.replace("\n", "; ")).strip(" ;")
    return v.replace("|", "/")


def note_for_number(n):
    g = (glob.glob(os.path.join(V, "01 Sefirot", f"{n:02d} *.md")) if 1 <= n <= 10
         else glob.glob(os.path.join(V, "02 Paths", f"{n} *.md")))
    return g[0] if g else None


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry", action="store_true"); a = ap.parse_args()
    rows = list(csv.reader(open(DC, encoding="utf-8-sig")))
    hdr = rows[0]; ci = {h: i for i, h in enumerate(hdr)}
    cols = [(ci[c], lab) for c, lab in CURATED if c in ci]
    miss = [c for c, _ in CURATED if c not in ci]
    if miss:
        print("⚠ НЕ НАЙДЕНЫ колонки:", miss)
    done = 0
    for r in rows[1:]:
        ks = r[0].strip()
        if not ks.isdigit():
            continue
        note = note_for_number(int(ks))
        if not note:
            continue
        trows = []
        for idx, lab in cols:
            val = clean(r[idx]) if idx < len(r) else ""
            if not val or re.fullmatch(r"[.\-—_/]+", val) or re.search(r"[֐-׿]", val):
                continue
            trows.append(f"| {lab} | {val} |")
        if not trows:
            continue
        block = (START + "\n## Соответствия Liber 777 (полная таблица)\n\n"
                 "| Шкала | Значение |\n|---|---|\n" + "\n".join(trows) + "\n" + END)
        t = open(note, encoding="utf-8").read()
        pat = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
        new = pat.sub(block, t) if pat.search(t) else t.rstrip() + "\n\n" + block + "\n"
        if not a.dry and new != t:
            open(note, "w", encoding="utf-8").write(new)
        done += 1
        if a.dry and ks in ("9", "15"):
            print(f"\n--- {os.path.basename(note)} ({len(trows)} строк) ---")
            print("\n".join(trows[:8]))
    print(f"\n{'(dry-run) ' if a.dry else ''}заметок со скаляр-таблицей: {done}")


if __name__ == "__main__":
    main()
