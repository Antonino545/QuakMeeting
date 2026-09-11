"""Shared mascot and accessory catalog for the Hangar and banner renderers."""

ANIMALS = (
    ("duck", "🦆 Duck"),
    ("owl", "🦉 Owl"),
    ("bunny", "🐰 Bunny"),
    ("platypus", "🕵️ Perry the Platypus"),
    ("squirrel", "🐿️ Squirrel"),
    ("fox", "🦊 Fox Strategist"),
    ("penguin", "🐧 Dapper Penguin"),
    ("panda", "🐼 Chill Panda"),
)

ACCESSORIES = (
    "fedora",
    "sunglasses",
    "cap",
    "graduation_cap",
    "crown",
    "pilot_helmet",
    "headphones",
    "aviator_goggles",
    "bow_tie",
    "scarf",
    "briefcase",
    "badge",
    "earpiece",
)

LEGACY_OUTFIT_ACCESSORIES = {
    "agent": ("fedora",),
    "student": ("graduation_cap",),
    "captain": ("cap",),
    "racer": ("pilot_helmet",),
    "aviator": ("aviator_goggles",),
}


def normalize_accessories(outfit=None, accessories=None, animal=None):
    """Return a stable accessory tuple while preserving legacy outfit configs."""
    values = []
    if accessories:
        values.extend(accessories if isinstance(accessories, (list, tuple)) else [accessories])
    values.extend(LEGACY_OUTFIT_ACCESSORIES.get(str(outfit or "").lower(), ()))
    if animal == "platypus" and "fedora" not in values:
        values.append("fedora")
    return tuple(dict.fromkeys(value for value in values if value in ACCESSORIES))


def animal_label(animal):
    return dict(ANIMALS).get(animal, str(animal).replace("_", " ").title())
