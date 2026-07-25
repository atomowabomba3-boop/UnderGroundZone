LANGUAGES = {

    "en": {
        "name": "🇬🇧 English",

        "welcome": """
⛏️ <b>Welcome to UndergroundZone!</b>

🔥 Underground mining system

🎟️ Tickets:
<b>{tickets}</b>

💎 Gems:
<b>{gems}</b>

⭐ Level:
<b>{level}</b>

Choose your action:
""",

        "profile": """
👤 <b>Your Profile</b>

🎟️ Tickets:
<b>{tickets}</b>

💎 Gems:
<b>{gems}</b>

⭐ Level:
<b>{level}</b>

🌎 Language:
<b>{language}</b>
"""
    },


    "pl": {
        "name": "🇵🇱 Polski",

        "welcome": """
⛏️ <b>Witaj w UndergroundZone!</b>

🔥 System podziemnego kopania

🎟️ Bilety:
<b>{tickets}</b>

💎 Diamenty:
<b>{gems}</b>

⭐ Poziom:
<b>{level}</b>

Wybierz opcję:
""",

        "profile": """
👤 <b>Twój profil</b>

🎟️ Bilety:
<b>{tickets}</b>

💎 Diamenty:
<b>{gems}</b>

⭐ Poziom:
<b>{level}</b>

🌎 Język:
<b>{language}</b>
"""
    },


    "de": {
        "name": "🇩🇪 Deutsch",

        "welcome": """
⛏️ <b>Willkommen bei UndergroundZone!</b>

🔥 Untergrund-Mining-System

🎟️ Tickets:
<b>{tickets}</b>

💎 Edelsteine:
<b>{gems}</b>

⭐ Level:
<b>{level}</b>

Wähle eine Option:
""",

        "profile": """
👤 <b>Dein Profil</b>

🎟️ Tickets:
<b>{tickets}</b>

💎 Edelsteine:
<b>{gems}</b>

⭐ Level:
<b>{level}</b>

🌎 Sprache:
<b>{language}</b>
"""
    }

}


def get_text(language, key):

    if language not in LANGUAGES:
        language = "en"

    return LANGUAGES[language][key]
