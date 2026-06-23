"""Explicit entity normalization rules for the Obsidian Liber 777 vault.

Keep this conservative: only add aliases when the source data clearly uses
multiple names for the same entity in the local dataset.
"""

ENTITY_ALIASES = {
    "The Magus": "The Magician",
    "Magus": "The Magician",
    "The Juggler": "The Magician",
    "Temperence": "Temperance",
    "Judgement": "Last Judgement",
    "Last Judgment": "Last Judgement",
    "Kings / Knights": "Kings - Knights",
    "Bhavani, etc.": "Bhavani, etc",
    "Kundalini [Yama": "Kundalini Yama",
    "blue": "Blue",
    "the Virgin Mary": "The Virgin Mary",
    "Sol": "Sun",
    "Luna": "Moon",
    "Hé": "Heh",
    "Vau": "Vav",
}
