#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_links.py — Под-проект II: аудит целостности связей vault. ТОЛЬКО отчёт, без правок.
Учитывает Obsidian-алиасы (frontmatter `aliases:`), поэтому ссылки вида [[Yesod]] на файл
`09 Yesod.md` НЕ считаются битыми.

  python3 _scripts/audit_links.py
"""
import os, re, glob, unicodedata
from collections import defaultdict

VAULT = "/Users/mikhail/open_777/obsidian_777_vault"
LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
CAP = 30


def norm_target(raw: str) -> str:
    return raw.split("|")[0].split("#")[0].strip()


def normkey(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).lower()
    return "".join(ch for ch in s if ch.isalnum())   # буквы любых алфавитов + цифры


def parse_aliases(text: str) -> list:
    if not text.startswith("---\n"):
        return []
    end = text.find("\n---\n", 4)
    if end == -1:
        return []
    fm = text[4:end].split("\n")
    out, grab = [], False
    for ln in fm:
        if re.match(r"^aliases:", ln):
            grab = True
            inline = ln.split(":", 1)[1].strip()
            if inline.startswith("["):
                out += [x.strip().strip('"\'') for x in inline.strip("[]").split(",") if x.strip()]
                grab = False
            continue
        if grab:
            m = re.match(r'^\s+-\s*"?([^"]+)"?\s*$', ln)
            if m:
                out.append(m.group(1).strip())
            elif re.match(r"^\S", ln):
                grab = False
    return [a for a in out if a]


def main():
    files = [p for p in glob.glob(os.path.join(VAULT, "**", "*.md"), recursive=True)
             if "/_" not in p[len(VAULT):] and "/.obsidian/" not in p]
    base_to_paths = defaultdict(list)
    alias_to_base = {}
    texts = {}
    for p in files:
        base = os.path.splitext(os.path.basename(p))[0]
        base_to_paths[base].append(p)
        t = open(p, encoding="utf-8").read(); texts[p] = t
        for a in parse_aliases(t):
            alias_to_base.setdefault(a, base)

    def resolve(t):
        if t in base_to_paths:
            return t
        return alias_to_base.get(t)

    outlinks, incoming, broken = {}, defaultdict(set), []
    for p in files:
        base = os.path.splitext(os.path.basename(p))[0]
        tgts = set()
        for m in LINK_RE.finditer(texts[p]):
            t = norm_target(m.group(1))
            if not t:
                continue
            r = resolve(t)
            if r:
                tgts.add(r); incoming[r].add(base)
            else:
                broken.append((base, t))
        outlinks[p] = tgts

    orphans = [os.path.relpath(p, VAULT) for p in files
               if not outlinks[p] and not incoming.get(os.path.splitext(os.path.basename(p))[0])]

    oneway = []
    for p in (glob.glob(os.path.join(VAULT, "01 Sefirot", "*.md")) +
              glob.glob(os.path.join(VAULT, "02 Paths", "*.md"))):
        base = os.path.splitext(os.path.basename(p))[0]
        for t in outlinks[p]:
            ent = base_to_paths[t][0]
            if "06 Entities" in ent and base not in outlinks.get(ent, set()):
                oneway.append((base, t))

    near = defaultdict(set)
    for b in base_to_paths:
        near[normkey(b)].add(b)
    near_dups = {k: v for k, v in near.items() if len(v) > 1 and k}

    print(f"Заметок: {len(files)} | имён: {len(base_to_paths)} | алиасов: {len(alias_to_base)}\n")

    bycount = defaultdict(int)
    for _, t in broken:
        bycount[t] += 1
    print(f"== БИТЫЕ ССЫЛКИ (с учётом алиасов): {len(broken)} всего, {len(bycount)} уникальных целей ==")
    for t, n in sorted(bycount.items(), key=lambda x: -x[1])[:CAP]:
        print(f"  [[{t}]] — {n}")

    print(f"\n== СИРОТЫ: {len(orphans)} ==")
    for o in orphans[:CAP]:
        print(f"  {o}")
    if len(orphans) > CAP:
        print(f"  …ещё {len(orphans)-CAP}")

    print(f"\n== ОДНОСТОРОННИЕ сфира/путь → сущность: {len(oneway)} ==")
    for s, t in oneway[:CAP]:
        print(f"  {s} → {t}")

    print(f"\n== БЛИЗКИЕ ДВОЙНИКИ ИМЁН: {len(near_dups)} ==")
    for k, v in list(near_dups.items())[:CAP]:
        print("  " + " ≈ ".join(sorted(v)))


if __name__ == "__main__":
    main()
