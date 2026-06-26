#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R4: слить Heré → Here (одна Гера, обе позиции Древа). Перенаправляет ссылки, удаляет дубль."""
import os, re, glob

V = "/Users/mikhail/open_777/obsidian_777_vault"
D = os.path.join(V, "06 Entities", "Deities")
HERE, HERE2 = os.path.join(D, "Here.md"), os.path.join(D, "Heré.md")


def fm_body(t):
    end = t.find("\n---\n", 4)
    return t[4:end].split("\n"), t[end + 5:]


def top_list(lines, key):
    out, grab = [], False
    for ln in lines:
        if re.match(rf"^{key}:\s*$", ln):
            grab = True; continue
        if grab:
            m = re.match(r'^\s+-\s*"?(\[\[[^\]]+\]\])"?\s*$', ln)
            if m:
                out.append(m.group(1))
            elif re.match(r"^\S", ln):
                grab = False
    return out


def related_sub(lines, sub):
    out, in_rel, grab = [], False, False
    for ln in lines:
        if re.match(r"^related:\s*$", ln):
            in_rel = True; continue
        if in_rel:
            if re.match(r"^\S", ln):
                break
            if re.match(rf"^  {sub}:\s*$", ln):
                grab = True; continue
            if re.match(r"^  \w", ln):
                grab = False
            if grab:
                m = re.match(r'^\s+-\s*"?(\[\[[^\]]+\]\])"?\s*$', ln)
                if m:
                    out.append(m.group(1))
    return out


def union(a, b):
    seen, out = set(), []
    for x in a + b:
        if x not in seen:
            seen.add(x); out.append(x)
    return out


t1, t2 = open(HERE, encoding="utf-8").read(), open(HERE2, encoding="utf-8").read()
f1, _ = fm_body(t1); f2, _ = fm_body(t2)

appears = union(top_list(f1, "appears_in"), top_list(f2, "appears_in"))
rel = {k: union(related_sub(f1, k), related_sub(f2, k))
       for k in ["tarot", "hebrew_letters", "sefiros", "paths"]}
ents = sorted(union(top_list(f1, "related_entities"), top_list(f2, "related_entities")),
              key=str.lower)


def yblock(key, items, indent=0):
    pad = " " * indent
    if not items:
        return [f"{pad}{key}: []"]
    return [f"{pad}{key}:"] + [f'{pad}  - "{x}"' for x in items]


fm = ['type: "entity"', 'entity_type: "deity"', 'name: "Here"',
      "aliases:", '  - "Heré"', '  - "Hera"', '  - "Гера"',
      "up:", '  - "[[Entity Index]]"']
fm += yblock("appears_in", appears)
fm += ["related:"] + [l for k in ["tarot", "hebrew_letters", "sefiros", "paths"]
                      for l in yblock(k, rel[k], indent=2)]
fm += yblock("related_entities", ents)
fm += ["tags:", '  - "liber777"', '  - "entity"', '  - "deity"',
       "source:", '  repo: "open_777"', '  file: "docs/liber_777.csv"']

body = ["# Here", "", "## Тип", "", "Deity.", "", "## Где встречается", ""]
body += [f"- {x}" for x in appears]
body += ["", "## Связанные соответствия", ""] + [f"- {x}" for x in ents]
body += ["", "## Dataview", "", "```dataview", "LIST",
         'FROM "01 Sefirot" OR "02 Paths"',
         "WHERE contains(file.outlinks, this.file.link)", "```", "",
         "## Исходные данные", "", "- open_777", "- docs/liber_777.csv",
         "- строки исходной таблицы: 3, 16",
         "- объединено из Here + Heré (одна Гера, позиции Binah и путь Vav)"]

open(HERE, "w", encoding="utf-8").write("---\n" + "\n".join(fm) + "\n---\n\n" + "\n".join(body) + "\n")
print(f"Here.md обновлён: appears_in={len(appears)}, related_entities={len(ents)}")

# перенаправить ссылки [[Heré]] / [[Heré|x]] → [[Here]] во всём vault
pat = re.compile(r"\[\[Heré(\||\]\])")
changed = 0
for p in glob.glob(os.path.join(V, "**", "*.md"), recursive=True):
    if os.path.abspath(p) in (os.path.abspath(HERE), os.path.abspath(HERE2)):
        continue
    t = open(p, encoding="utf-8").read()
    t2_ = pat.sub(r"[[Here\1", t)
    if t2_ != t:
        open(p, "w", encoding="utf-8").write(t2_); changed += 1
print(f"перенаправлено ссылок в {changed} файлах")

os.remove(HERE2)
print("Heré.md удалён")
