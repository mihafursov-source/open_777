---
type: "entity"
entity_type: "minor_tarot"
name: "The 4 Tens"
up:
  - "[[Entity Index]]"
appears_in:
  - "[[10 Malkuth]]"
related:
  tarot:
    - "[[The Virgin Mary]]"
  hebrew_letters: []
  sefiros: []
  paths: []
related_entities:
  - "[[Adonis]]"
  - "[[Aralim]]"
  - "[[Ashim]]"
  - "[[Blue emerald green Grey]]"
  - "[[Calvary Cross]]"
  - "[[Ceres]]"
  - "[[Citrine]]"
  - "[[Corn]]"
  - "[[Dittany of Crete]]"
  - "[[Ecclesia Xsti]]"
  - "[[Khan]]"
  - "[[Lakshmi]]"
  - "[[Lilith]]"
  - "[[Mag. Sulph]]"
  - "[[Michael]]"
  - "[[Osiris]]"
  - "[[Persephone]]"
  - "[[Psyche]]"
  - "[[Rock Crystal]]"
  - "[[Sandalphon]]"
  - "[[Sphinx]]"
  - "[[The Virgin Mary]]"
  - "[[VITRIOL]]"
  - "[[Yellow]]"
tags:
  - "liber777"
  - "entity"
  - "minor_tarot"
source:
  repo: "open_777"
  file: "docs/liber_777.csv"
---

# The 4 Tens

## Тип

Minor Tarot.

## Где встречается

- [[10 Malkuth]]

## Связанные соответствия

- [[Adonis]]
- [[Aralim]]
- [[Ashim]]
- [[Blue emerald green Grey]]
- [[Calvary Cross]]
- [[Ceres]]
- [[Citrine]]
- [[Corn]]
- [[Dittany of Crete]]
- [[Ecclesia Xsti]]
- [[Khan]]
- [[Lakshmi]]
- [[Lilith]]
- [[Mag. Sulph]]
- [[Michael]]
- [[Osiris]]
- [[Persephone]]
- [[Psyche]]
- [[Rock Crystal]]
- [[Sandalphon]]
- [[Sphinx]]
- [[The Virgin Mary]]
- [[VITRIOL]]
- [[Yellow]]

## Dataview

```dataview
LIST
FROM "01 Sefirot" OR "02 Paths"
WHERE contains(file.outlinks, this.file.link)
```

## Исходные данные

- open_777
- docs/liber_777.csv
- строки исходной таблицы: 10
- дополнительные JS-источники: нет
- raw значения: The 4 Tens - Empresses or Princesses
