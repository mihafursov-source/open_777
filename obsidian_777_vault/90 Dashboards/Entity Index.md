---
type: "dashboard"
tags:
  - "liber777"
  - "dashboard"
---

# Entity Index

```dataview
TABLE entity_type, appears_in
FROM "06 Entities"
WHERE type = "entity"
SORT entity_type ASC, file.name ASC
```
