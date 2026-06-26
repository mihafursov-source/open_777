#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_correspondences.py — Под-проект I полировки vault (in-place, идемпотентно).

Разворачивает сломанный вложенный frontmatter `correspondences` (JSON-блоб, не
кликабельный в Obsidian) в ПЛОСКИЕ типизированные свойства-списки `corr_<тип>`
(кликабельные чипы + чистый YAML для ИИ). `corresponds_to` остаётся как «общее облако».
Тело заметки и любые ручные блоки НЕ трогаются — переписывается только frontmatter.

  python3 _scripts/fix_correspondences.py --dry     # показать план, без записи
  python3 _scripts/fix_correspondences.py           # применить + обновить types.json
"""
import os, re, glob, argparse, json

VAULT = "/Users/mikhail/open_777/obsidian_777_vault"

# подпапка/раздел → имя bucket'а корреспонденции
ENTITY_BUCKET = {
    "Deities": "deities", "Demons": "demons", "Angels": "angels", "Spirits": "spirits",
    "Animals": "animals", "Plants": "plants", "Stones": "stones", "Perfumes": "perfumes",
    "Colors": "colors", "Magical Weapons": "weapons", "Other": "other",
}
# порядок вывода corr_* свойств
BUCKET_ORDER = ["tarot", "letters", "astrology", "numbers", "deities", "demons",
                "angels", "spirits", "animals", "plants", "stones", "perfumes",
                "colors", "weapons", "other"]
LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]")


def build_index() -> dict:
    """basename (без .md) → bucket. Структурные узлы (сфиры/пути) исключаются."""
    idx = {}
    for sub, bucket in ENTITY_BUCKET.items():
        for p in glob.glob(os.path.join(VAULT, "06 Entities", sub, "*.md")):
            idx[os.path.splitext(os.path.basename(p))[0]] = bucket
    for folder, bucket in [("03 Tarot", "tarot"), ("04 Hebrew Letters", "letters"),
                           ("05 Astrology", "astrology"), ("07 Numbers", "numbers")]:
        for p in glob.glob(os.path.join(VAULT, folder, "**", "*.md"), recursive=True):
            idx.setdefault(os.path.splitext(os.path.basename(p))[0], bucket)
    return idx


def split_fm(text: str):
    """Вернёт (frontmatter_lines, body) или (None, text) если нет frontmatter."""
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return None, text
    fm = text[4:end].split("\n")
    body = text[end + 5:]
    return fm, body


def collect_links(fm_lines, body) -> list:
    """Все [[цели]] из frontmatter + тела (для классификации). Дедуп, порядок сохранён."""
    seen, out = set(), []
    for chunk in ["\n".join(fm_lines), body]:
        for m in LINK_RE.finditer(chunk):
            name = m.group(1).strip()
            if name and name not in seen:
                seen.add(name); out.append(name)
    return out


def drop_correspondences(fm_lines) -> list:
    """Убрать вложенный блок `correspondences:` (до следующего ключа indent 0)."""
    out, skip = [], False
    for ln in fm_lines:
        if re.match(r"^correspondences:\s*$", ln) or re.match(r"^correspondences:\s*\{", ln):
            skip = True; continue
        if skip:
            if re.match(r"^\S", ln):   # следующий ключ нулевого отступа — конец блока
                skip = False
            else:
                continue
        out.append(ln)
    return out


def drop_old_corr(fm_lines) -> list:
    """Идемпотентно убрать ранее записанные corr_* свойства (ключ + его список)."""
    out, skip = [], False
    for ln in fm_lines:
        if re.match(r"^corr_[a-z]+:\s*(\[\])?\s*$", ln):
            skip = True
            if ln.rstrip().endswith("[]"):
                skip = False    # пустой инлайн — просто пропустить строку
            continue
        if skip:
            if re.match(r"^\s+-\s", ln):
                continue
            skip = False
        out.append(ln)
    return out


def build_corr_lines(links, idx) -> list:
    buckets = {b: [] for b in BUCKET_ORDER}
    for name in links:
        b = idx.get(name)
        if b:
            buckets[b].append(name)
    lines = []
    for b in BUCKET_ORDER:
        vals = buckets[b]
        if vals:
            lines.append(f"corr_{b}:")
            lines.extend(f'  - "[[{n}]]"' for n in vals)
    return lines, {b: len(buckets[b]) for b in BUCKET_ORDER if buckets[b]}


def process(path, idx, dry):
    text = open(path, encoding="utf-8").read()
    fm, body = split_fm(text)
    if fm is None:
        return None
    links = collect_links(fm, body)
    corr_lines, counts = build_corr_lines(links, idx)
    fm2 = drop_old_corr(drop_correspondences(fm))
    # вставить corr_* перед `tags:` (или в конец frontmatter)
    insert_at = next((i for i, l in enumerate(fm2) if re.match(r"^tags:", l)), len(fm2))
    fm2 = fm2[:insert_at] + corr_lines + fm2[insert_at:]
    new = "---\n" + "\n".join(fm2) + "\n---\n" + body
    if not dry and new != text:
        tmp = path + ".tmp"; open(tmp, "w", encoding="utf-8").write(new); os.replace(tmp, path)
    return counts


def update_types():
    tp = os.path.join(VAULT, ".obsidian", "types.json")
    j = json.load(open(tp, encoding="utf-8"))
    for b in BUCKET_ORDER:
        j["types"][f"corr_{b}"] = "multitext"
    json.dump(j, open(tp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("types.json: corr_* → multitext")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry", action="store_true"); a = ap.parse_args()
    idx = build_index()
    targets = (glob.glob(os.path.join(VAULT, "01 Sefirot", "*.md")) +
               glob.glob(os.path.join(VAULT, "02 Paths", "*.md")))
    print(f"индекс типов: {len(idx)} имён; заметок к обработке: {len(targets)}\n")
    for p in sorted(targets):
        c = process(p, idx, a.dry)
        if c is not None:
            name = os.path.splitext(os.path.basename(p))[0]
            print(f"  {name}: " + ", ".join(f"{k}={v}" for k, v in c.items()))
    if not a.dry:
        update_types()
    print("\n" + ("(dry-run, без записи)" if a.dry else "Готово."))


if __name__ == "__main__":
    main()
