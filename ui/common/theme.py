"""
Shared Catppuccin Mocha Theme System for QuakMeeting.
Single source of truth for color palette tokens across macOS (AppKit) and Linux (PyQt6).
"""
from typing import Dict, Tuple

class CatppuccinMocha:
    """Standardized Catppuccin Mocha Palette."""

    # 1. Dark Base Surfaces
    CRUST_HEX = "#11111b"
    CRUST_RGB = (0.067, 0.067, 0.106)

    MANTLE_HEX = "#181825"
    MANTLE_RGB = (0.094, 0.094, 0.145)

    BASE_HEX = "#1e1e2e"
    BASE_RGB = (0.118, 0.118, 0.180)

    SURFACE0_HEX = "#313244"
    SURFACE0_RGB = (0.192, 0.196, 0.267)

    SURFACE1_HEX = "#45475a"
    SURFACE1_RGB = (0.271, 0.278, 0.353)

    SURFACE2_HEX = "#585b70"
    SURFACE2_RGB = (0.345, 0.357, 0.439)

    OVERLAY0_HEX = "#6c7086"
    OVERLAY0_RGB = (0.424, 0.439, 0.525)

    OVERLAY1_HEX = "#7f849c"
    OVERLAY1_RGB = (0.498, 0.518, 0.612)

    OVERLAY2_HEX = "#9399b2"
    OVERLAY2_RGB = (0.576, 0.600, 0.698)

    # 2. Typography & Text
    TEXT_HEX = "#cdd6f4"
    TEXT_RGB = (0.804, 0.839, 0.957)

    SUBTEXT1_HEX = "#bac2de"
    SUBTEXT1_RGB = (0.729, 0.761, 0.871)

    SUBTEXT0_HEX = "#a6adc8"
    SUBTEXT0_RGB = (0.651, 0.678, 0.784)

    # 3. Accent Colors
    MAUVE_HEX = "#cba6f7"
    MAUVE_RGB = (0.796, 0.651, 0.969)

    BLUE_HEX = "#89b4fa"
    BLUE_RGB = (0.537, 0.706, 0.980)

    SAPPHIRE_HEX = "#74c7ec"
    SAPPHIRE_RGB = (0.455, 0.780, 0.925)

    SKY_HEX = "#89dceb"
    SKY_RGB = (0.537, 0.863, 0.922)

    TEAL_HEX = "#94e2d5"
    TEAL_RGB = (0.580, 0.886, 0.835)

    GREEN_HEX = "#a6e3a1"
    GREEN_RGB = (0.651, 0.890, 0.631)

    YELLOW_HEX = "#f9e2af"
    YELLOW_RGB = (0.976, 0.886, 0.686)

    PEACH_HEX = "#fab387"
    PEACH_RGB = (0.980, 0.702, 0.529)

    MAROON_HEX = "#eba0ac"
    MAROON_RGB = (0.922, 0.627, 0.675)

    RED_HEX = "#f38ba8"
    RED_RGB = (0.953, 0.545, 0.659)

    FLAMINGO_HEX = "#f2cdcd"
    FLAMINGO_RGB = (0.949, 0.804, 0.804)

    ROSEWATER_HEX = "#f5e0dc"
    ROSEWATER_RGB = (0.961, 0.878, 0.863)

    LAVENDER_HEX = "#b4befe"
    LAVENDER_RGB = (0.706, 0.745, 0.996)


# Pilot mascot palette mapping
PILOT_THEME_COLORS: Dict[str, Dict[str, str]] = {
    "chef": {
        "accent": CatppuccinMocha.PEACH_HEX,
        "accent_bright": CatppuccinMocha.YELLOW_HEX,
        "btn_gradient_top": CatppuccinMocha.PEACH_HEX,
        "btn_gradient_bot": CatppuccinMocha.MAROON_HEX,
    },
    "captain": {
        "accent": CatppuccinMocha.SAPPHIRE_HEX,
        "accent_bright": CatppuccinMocha.SKY_HEX,
        "btn_gradient_top": CatppuccinMocha.SAPPHIRE_HEX,
        "btn_gradient_bot": CatppuccinMocha.BLUE_HEX,
    },
    "owl": {
        "accent": CatppuccinMocha.MAUVE_HEX,
        "accent_bright": CatppuccinMocha.LAVENDER_HEX,
        "btn_gradient_top": CatppuccinMocha.MAUVE_HEX,
        "btn_gradient_bot": CatppuccinMocha.LAVENDER_HEX,
    },
    "driver": {
        "accent": CatppuccinMocha.YELLOW_HEX,
        "accent_bright": CatppuccinMocha.PEACH_HEX,
        "btn_gradient_top": CatppuccinMocha.YELLOW_HEX,
        "btn_gradient_bot": CatppuccinMocha.PEACH_HEX,
    },
    "zen_duck": {
        "accent": CatppuccinMocha.TEAL_HEX,
        "accent_bright": CatppuccinMocha.SKY_HEX,
        "btn_gradient_top": CatppuccinMocha.TEAL_HEX,
        "btn_gradient_bot": CatppuccinMocha.SKY_HEX,
    },
    "gym": {
        "accent": CatppuccinMocha.RED_HEX,
        "accent_bright": CatppuccinMocha.MAROON_HEX,
        "btn_gradient_top": CatppuccinMocha.RED_HEX,
        "btn_gradient_bot": CatppuccinMocha.MAROON_HEX,
    },
    "duck": {
        "accent": CatppuccinMocha.GREEN_HEX,
        "accent_bright": CatppuccinMocha.TEAL_HEX,
        "btn_gradient_top": CatppuccinMocha.GREEN_HEX,
        "btn_gradient_bot": CatppuccinMocha.TEAL_HEX,
    }
}


def get_combo_title(animal: str, outfit: str) -> str:
    """Returns localized persona combo title for animal and outfit pairs."""
    try:
        from core.services.language_service import get_active_language
        active_lang = get_active_language()
    except Exception:
        active_lang = "en"

    if active_lang == "it":
        titles_it = {
            ("bunny", "student"): "🎓 Coniglio Studente",
            ("bunny", "chef"): "👨‍🍳 Coniglio Pasticcere",
            ("bunny", "captain"): "🧑‍✈️ Primo Ufficiale Coniglio",
            ("bunny", "agent"): "🕵️ Agente Coniglio Segreto",
            ("bunny", "gym"): "🏋️ Coniglio Atleta Cardio",
            ("bunny", "racer"): "🏎️ Coniglio Pilota Turbo",
            ("bunny", "zen"): "🌸 Coniglio Meditazione Zen",
            ("bunny", "aviator"): "🪖 Coniglio Aviatore",
            ("owl", "student"): "🎓 Gufo Rettore Accademico",
            ("owl", "chef"): "👨‍🍳 Gufo Gourmet Chef",
            ("owl", "captain"): "🧑‍✈️ Comandante di Flotta Gufo",
            ("owl", "agent"): "🕵️ Agente Operativo Gufo",
            ("owl", "gym"): "🏋️ Gufo Powerlifter",
            ("owl", "racer"): "🏎️ Gufo Notturno Speedster",
            ("owl", "zen"): "🌸 Gufo della Quiete Zen",
            ("owl", "aviator"): "🪖 Asso dello Squadrone Gufo",
            ("duck", "student"): "🎓 Anatra con Lode Accademica",
            ("duck", "chef"): "👨‍🍳 Master Chef Anatra",
            ("duck", "captain"): "🧑‍✈️ Comandante di Linea Anatra",
            ("duck", "agent"): "🕵️ Spia Sotto Copertura Anatra",
            ("duck", "gym"): "🏋️ Anatra Bodybuilder",
            ("duck", "racer"): "🏎️ Anatra Gran Premio",
            ("duck", "zen"): "🌸 Anatra Zen dello Stagno",
            ("duck", "aviator"): "🪖 Classico Quak Aviatore",
            ("platypus", "agent"): "🕵️ Agente Perry Ornitorinco",
            ("platypus", "student"): "🎓 Ornitorinco Studioso",
            ("platypus", "chef"): "👨‍🍳 Master Chef Ornitorinco",
            ("platypus", "captain"): "🧑‍✈️ Comandante Ornitorinco",
            ("platypus", "gym"): "🏋️ Ornitorinco Atleta",
            ("platypus", "racer"): "🏎️ Pilota Auto Spia Ornitorinco",
            ("platypus", "zen"): "🌸 Ornitorinco Zen",
            ("platypus", "aviator"): "🪖 Ornitorinco Aviatore",
            ("squirrel", "agent"): "🕵️ Scoiattolo Agente Segreto",
            ("squirrel", "student"): "🎓 Scoiattolo Genio Studente",
            ("squirrel", "chef"): "👨‍🍳 Scoiattolo Chef delle Ghiande",
            ("squirrel", "captain"): "🧑‍✈️ Capitano del Cielo Scoiattolo",
            ("squirrel", "gym"): "🏋️ Scoiattolo Cardio Hyper",
            ("squirrel", "racer"): "🏎️ Scoiattolo Turbo Speed",
            ("squirrel", "zen"): "🌸 Scoiattolo Calmo Zen",
            ("squirrel", "aviator"): "🪖 Esploratore Aviatore Scoiattolo"
        }
        return titles_it.get((animal, outfit), f"✨ Pilota {animal.capitalize()} {outfit.capitalize()}")

    titles = {
        ("bunny", "student"): "🎓 Scholar Bunny Pilot",
        ("bunny", "chef"): "👨‍🍳 Pastry Chef Bunny",
        ("bunny", "captain"): "🧑‍✈️ First Officer Bunny",
        ("bunny", "agent"): "🕵️ Secret Agent Bunny P",
        ("bunny", "gym"): "🏋️ Cardio Bunny Athlete",
        ("bunny", "racer"): "🏎️ Turbo Bunny Driver",
        ("bunny", "zen"): "🌸 Zen Meditation Bunny",
        ("bunny", "aviator"): "🪖 Clever Aviator Bunny",
        ("owl", "student"): "🎓 Professor Owl Dean",
        ("owl", "chef"): "👨‍🍳 Gourmet Owl Chef",
        ("owl", "captain"): "🧑‍✈️ Fleet Commander Owl",
        ("owl", "agent"): "🕵️ Intelligence Owl Operative",
        ("owl", "gym"): "🏋️ Powerlifting Owl",
        ("owl", "racer"): "🏎️ Night Owl Speedster",
        ("owl", "zen"): "🌸 Serene Mindfulness Owl",
        ("owl", "aviator"): "🪖 Ace Squadron Owl",
        ("duck", "student"): "🎓 Academic Honors Duck",
        ("duck", "chef"): "👨‍🍳 Master Chef Duck",
        ("duck", "captain"): "🧑‍✈️ Jetliner Captain Duck",
        ("duck", "agent"): "🕵️ Undercover Spy Duck",
        ("duck", "gym"): "🏋️ Gym Bro Muscle Duck",
        ("duck", "racer"): "🏎️ Grand Prix Speed Duck",
        ("duck", "zen"): "🌸 Lotus Pond Zen Duck",
        ("duck", "aviator"): "🪖 Classic Quak Aviator",
        ("platypus", "agent"): "🕵️ Secret Agent Perry Platypus",
        ("platypus", "student"): "🎓 Scholar Agent Platypus",
        ("platypus", "chef"): "👨‍🍳 Master Chef Platypus",
        ("platypus", "captain"): "🧑‍✈️ Airline Captain Platypus",
        ("platypus", "gym"): "🏋️ Athlete Agent Platypus",
        ("platypus", "racer"): "🏎️ Stealth Platypus Speedster",
        ("platypus", "zen"): "🌸 Zen Platypus Guide",
        ("platypus", "aviator"): "🪖 Classic Agent Platypus",
        ("squirrel", "agent"): "🕵️ Secret Agent Squirrel",
        ("squirrel", "student"): "🎓 Academic Honor Squirrel",
        ("squirrel", "chef"): "👨‍🍳 Acorn Pastry Chef Squirrel",
        ("squirrel", "captain"): "🧑‍✈️ Aviator Sky Squirrel",
        ("squirrel", "gym"): "🏋️ Hyper Cardio Squirrel",
        ("squirrel", "racer"): "🏎️ Turbo Speed Squirrel",
        ("squirrel", "zen"): "🌸 Mindfulness Forest Squirrel",
        ("squirrel", "aviator"): "🪖 Scout Aviator Squirrel"
    }
    return titles.get((animal, outfit), f"✨ Pilot {animal.capitalize()} {outfit.capitalize()}")

