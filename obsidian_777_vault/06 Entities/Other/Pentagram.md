---
type: "entity"
entity_type: "other"
name: "Pentagram"
up:
  - "[[Entity Index]]"
appears_in:
  - "[[27 Pe]]"
related:
  tarot: []
  hebrew_letters:
    - "[[Pe]]"
  sefiros:
    - "[[Hod]]"
    - "[[Netzach]]"
  paths:
    - "[[27 Pe]]"
related_entities:
  - "[[Absinthe]]"
  - "[[Athena]]"
  - "[[Boar]]"
  - "[[Dragonís Blood]]"
  - "[[Graphiel]]"
  - "[[Hod]]"
  - "[[Horus]]"
  - "[[Kan]]"
  - "[[Krishna]]"
  - "[[Mars]]"
  - "[[Mentu]]"
  - "[[Netzach]]"
  - "[[Pe]]"
  - "[[Pepper]]"
  - "[[Pergamos]]"
  - "[[Red]]"
  - "[[Rich amber]]"
  - "[[Ruby]]"
  - "[[Rue]]"
  - "[[Scarlet]]"
  - "[[The House of God]]"
  - "[[The Sword]]"
  - "[[Tuisco]]"
  - "[[Zamael]]"
  - "[[any red stone]]"
tags:
  - "liber777"
  - "entity"
  - "other"
source:
  repo: "open_777"
  file: "docs/liber_777.csv"
---

# Pentagram

## Тип

Other.

## Где встречается

- [[27 Pe]]

## Связанные соответствия

- [[Absinthe]]
- [[Athena]]
- [[Boar]]
- [[Dragonís Blood]]
- [[Graphiel]]
- [[Hod]]
- [[Horus]]
- [[Kan]]
- [[Krishna]]
- [[Mars]]
- [[Mentu]]
- [[Netzach]]
- [[Pe]]
- [[Pepper]]
- [[Pergamos]]
- [[Red]]
- [[Rich amber]]
- [[Ruby]]
- [[Rue]]
- [[Scarlet]]
- [[The House of God]]
- [[The Sword]]
- [[Tuisco]]
- [[Zamael]]
- [[any red stone]]

## Dataview

```dataview
LIST
FROM "01 Sefirot" OR "02 Paths"
WHERE contains(file.outlinks, this.file.link)
```

## Исходные данные

- open_777
- docs/liber_777.csv
- строки исходной таблицы: 27
- дополнительные JS-источники: нет
- raw значения: Pentagram
