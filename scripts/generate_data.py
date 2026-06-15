# -*- coding: utf-8 -*-
"""
Genera data/groups.json y data/matches.json para la web del Mundial 2026.
Las horas de cada partido se guardan en UTC (ISO 8601). La pagina web
las convierte sola a la hora local de quien la abra (Chile incluido).

Para regenerar:  python scripts/generate_data.py
"""
import json
import os
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")

# --- Zonas horarias de cada sede en junio 2026 (offset respecto a UTC) ---
# EE.UU./Canada estan en horario de verano (DST). Mexico NO usa DST.
CITY_OFFSET = {
    # Este (EDT, UTC-4)
    "Toronto": -4, "New Jersey": -4, "Boston": -4, "Philadelphia": -4,
    "Atlanta": -4, "Miami": -4,
    # Centro (CDT, UTC-5)
    "Houston": -5, "Dallas": -5, "Kansas City": -5,
    # Pacifico (PDT, UTC-7)
    "Los Angeles": -7, "San Francisco": -7, "Seattle": -7, "Vancouver": -7,
    # Mexico Centro (UTC-6, sin DST)
    "Mexico City": -6, "Zapopan": -6, "Guadalupe": -6,
}

# --- Estadio oficial de cada sede del Mundial 2026 ---
STADIUM = {
    "Mexico City": "Estadio Azteca",
    "Zapopan": "Estadio Akron",
    "Guadalupe": "Estadio Monterrey (BBVA)",
    "Toronto": "BMO Field",
    "Vancouver": "BC Place",
    "Atlanta": "Mercedes-Benz Stadium",
    "Boston": "Gillette Stadium",
    "Dallas": "AT&T Stadium",
    "Houston": "NRG Stadium",
    "Kansas City": "Arrowhead Stadium",
    "Los Angeles": "SoFi Stadium",
    "Miami": "Hard Rock Stadium",
    "New Jersey": "MetLife Stadium",
    "Philadelphia": "Lincoln Financial Field",
    "San Francisco": "Levi's Stadium",
    "Seattle": "Lumen Field",
}

# --- Canales de TV en Chile por partido (de las infografias de Puntaje Ideal) ---
# Cada fila: (equipo1, equipo2, [canales]). El orden de los equipos no importa,
# se busca por el par. Un par solo juega una vez en la fase de grupos.
_CHANNELS_RAW = [
    # Jornada 1
    ("Mexico", "South Africa", ["DSports", "Chilevisión", "Disney+"]),
    ("South Korea", "Czechia", ["DSports"]),
    ("Canada", "Bosnia and Herzegovina", ["DSports", "Chilevisión"]),
    ("United States", "Paraguay", ["DSports", "Chilevisión", "Disney+"]),
    ("Qatar", "Switzerland", ["DSports", "Chilevisión"]),
    ("Brazil", "Morocco", ["DSports", "Chilevisión", "Disney+"]),
    ("Haiti", "Scotland", ["DSports"]),
    ("Australia", "Turkiye", ["DSports"]),
    ("Germany", "Curacao", ["DSports"]),
    ("Netherlands", "Japan", ["DSports 2", "Chilevisión"]),
    ("Ivory Coast", "Ecuador", ["DSports", "Chilevisión", "Disney+"]),
    ("Sweden", "Tunisia", ["DSports"]),
    ("Spain", "Cape Verde", ["DSports"]),
    ("Belgium", "Egypt", ["DSports 2", "Chilevisión"]),
    ("Saudi Arabia", "Uruguay", ["DSports", "Chilevisión"]),
    ("Iran", "New Zealand", ["DSports"]),
    ("France", "Senegal", ["DSports", "Chilevisión", "Disney+"]),
    ("Iraq", "Norway", ["DSports 2"]),
    ("Argentina", "Algeria", ["DSports", "Chilevisión"]),
    ("Austria", "Jordan", ["DSports"]),
    ("Portugal", "DR Congo", ["DSports"]),
    ("England", "Croatia", ["DSports", "Chilevisión"]),
    ("Ghana", "Panama", ["DSports 2"]),
    ("Uzbekistan", "Colombia", ["DSports", "Chilevisión"]),
    # Jornada 2
    ("Czechia", "South Africa", ["DSports"]),
    ("Switzerland", "Bosnia and Herzegovina", ["DSports", "Chilevisión", "Disney+"]),
    ("Canada", "Qatar", ["DSports", "Chilevisión"]),
    ("Mexico", "South Korea", ["DSports"]),
    ("United States", "Australia", ["DSports", "Chilevisión"]),
    ("Scotland", "Morocco", ["DSports", "Chilevisión", "Disney+"]),
    ("Brazil", "Haiti", ["DSports"]),
    ("Turkiye", "Paraguay", ["DSports"]),
    ("Netherlands", "Sweden", ["DSports"]),
    ("Germany", "Ivory Coast", ["DSports", "Chilevisión", "Disney+"]),
    ("Ecuador", "Curacao", ["DSports"]),
    ("Tunisia", "Japan", ["DSports", "Chilevisión"]),
    ("Spain", "Saudi Arabia", ["DSports", "Chilevisión"]),
    ("Belgium", "Iran", ["DSports 2", "Chilevisión"]),
    ("Uruguay", "Cape Verde", ["DSports"]),
    ("New Zealand", "Egypt", ["DSports"]),
    ("Argentina", "Austria", ["DSports", "Chilevisión"]),
    ("France", "Iraq", ["DSports"]),
    ("Norway", "Senegal", ["DSports", "Chilevisión"]),
    ("Jordan", "Algeria", ["DSports"]),
    ("Portugal", "Uzbekistan", ["DSports", "Chilevisión"]),
    ("England", "Ghana", ["DSports", "Chilevisión", "Disney+"]),
    ("Panama", "Croatia", ["DSports 2", "Chilevisión"]),
    ("Colombia", "DR Congo", ["DSports"]),
    # Jornada 3
    ("Switzerland", "Canada", ["DSports"]),
    ("Bosnia and Herzegovina", "Qatar", ["DSports 2"]),
    ("Scotland", "Brazil", ["DSports", "Chilevisión", "Disney+"]),
    ("Morocco", "Haiti", ["DSports+"]),
    ("Czechia", "Mexico", ["DSports", "Chilevisión"]),
    ("South Africa", "South Korea", ["DSports+"]),
    ("Ecuador", "Germany", ["DSports", "Chilevisión"]),
    ("Curacao", "Ivory Coast", ["DSports 2"]),
    ("Tunisia", "Netherlands", ["DSports", "Chilevisión"]),
    ("Japan", "Sweden", ["DSports+"]),
    ("Turkiye", "United States", ["DSports"]),
    ("Paraguay", "Australia", ["DSports 2", "Chilevisión"]),
    ("Norway", "France", ["DSports", "Chilevisión"]),
    ("Senegal", "Iraq", ["DSports 2"]),
    ("Uruguay", "Spain", ["DSports", "Chilevisión"]),
    ("Cape Verde", "Saudi Arabia", ["DSports 2"]),
    ("New Zealand", "Belgium", ["DSports"]),
    ("Egypt", "Iran", ["DSports+"]),
    ("Panama", "England", ["DSports"]),
    ("Croatia", "Ghana", ["DSports+"]),
    ("Colombia", "Portugal", ["DSports", "Chilevisión"]),
    ("DR Congo", "Uzbekistan", ["DSports+"]),
    ("Jordan", "Argentina", ["DSports"]),
    ("Algeria", "Austria", ["DSports+"]),
]
CHANNELS = {frozenset((a, b)): ch for a, b, ch in _CHANNELS_RAW}

# Nombre en espannol (con tildes) + bandera (emoji) por seleccion.
TEAMS = {
    "Mexico": ("México", "\U0001F1F2\U0001F1FD"),
    "South Africa": ("Sudáfrica", "\U0001F1FF\U0001F1E6"),
    "South Korea": ("Corea del Sur", "\U0001F1F0\U0001F1F7"),
    "Czechia": ("Chequia", "\U0001F1E8\U0001F1FF"),
    "Canada": ("Canadá", "\U0001F1E8\U0001F1E6"),
    "Bosnia and Herzegovina": ("Bosnia y Herzegovina", "\U0001F1E7\U0001F1E6"),
    "Qatar": ("Catar", "\U0001F1F6\U0001F1E6"),
    "Switzerland": ("Suiza", "\U0001F1E8\U0001F1ED"),
    "Brazil": ("Brasil", "\U0001F1E7\U0001F1F7"),
    "Morocco": ("Marruecos", "\U0001F1F2\U0001F1E6"),
    "Haiti": ("Haití", "\U0001F1ED\U0001F1F9"),
    "Scotland": ("Escocia", "\U0001F3F4\U000E0067\U000E0062\U000E0073\U000E0063\U000E0074\U000E007F"),
    "United States": ("Estados Unidos", "\U0001F1FA\U0001F1F8"),
    "Paraguay": ("Paraguay", "\U0001F1F5\U0001F1FE"),
    "Australia": ("Australia", "\U0001F1E6\U0001F1FA"),
    "Turkiye": ("Turquía", "\U0001F1F9\U0001F1F7"),
    "Germany": ("Alemania", "\U0001F1E9\U0001F1EA"),
    "Curacao": ("Curazao", "\U0001F1E8\U0001F1FC"),
    "Ivory Coast": ("Costa de Marfil", "\U0001F1E8\U0001F1EE"),
    "Ecuador": ("Ecuador", "\U0001F1EA\U0001F1E8"),
    "Netherlands": ("Países Bajos", "\U0001F1F3\U0001F1F1"),
    "Japan": ("Japón", "\U0001F1EF\U0001F1F5"),
    "Sweden": ("Suecia", "\U0001F1F8\U0001F1EA"),
    "Tunisia": ("Túnez", "\U0001F1F9\U0001F1F3"),
    "Belgium": ("Bélgica", "\U0001F1E7\U0001F1EA"),
    "Egypt": ("Egipto", "\U0001F1EA\U0001F1EC"),
    "Iran": ("Irán", "\U0001F1EE\U0001F1F7"),
    "New Zealand": ("Nueva Zelanda", "\U0001F1F3\U0001F1FF"),
    "Spain": ("España", "\U0001F1EA\U0001F1F8"),
    "Cape Verde": ("Cabo Verde", "\U0001F1E8\U0001F1FB"),
    "Saudi Arabia": ("Arabia Saudita", "\U0001F1F8\U0001F1E6"),
    "Uruguay": ("Uruguay", "\U0001F1FA\U0001F1FE"),
    "France": ("Francia", "\U0001F1EB\U0001F1F7"),
    "Senegal": ("Senegal", "\U0001F1F8\U0001F1F3"),
    "Iraq": ("Irak", "\U0001F1EE\U0001F1F6"),
    "Norway": ("Noruega", "\U0001F1F3\U0001F1F4"),
    "Argentina": ("Argentina", "\U0001F1E6\U0001F1F7"),
    "Algeria": ("Argelia", "\U0001F1E9\U0001F1FF"),
    "Austria": ("Austria", "\U0001F1E6\U0001F1F9"),
    "Jordan": ("Jordania", "\U0001F1EF\U0001F1F4"),
    "Portugal": ("Portugal", "\U0001F1F5\U0001F1F9"),
    "DR Congo": ("RD Congo", "\U0001F1E8\U0001F1E9"),
    "Uzbekistan": ("Uzbekistán", "\U0001F1FA\U0001F1FF"),
    "Colombia": ("Colombia", "\U0001F1E8\U0001F1F4"),
    "England": ("Inglaterra", "\U0001F3F4\U000E0067\U000E0062\U000E0065\U000E006E\U000E0067\U000E007F"),
    "Croatia": ("Croacia", "\U0001F1ED\U0001F1F7"),
    "Ghana": ("Ghana", "\U0001F1EC\U0001F1ED"),
    "Panama": ("Panamá", "\U0001F1F5\U0001F1E6"),
}

GROUPS = {
    "A": ["Mexico", "South Africa", "South Korea", "Czechia"],
    "B": ["Canada", "Bosnia and Herzegovina", "Qatar", "Switzerland"],
    "C": ["Brazil", "Morocco", "Haiti", "Scotland"],
    "D": ["United States", "Paraguay", "Australia", "Turkiye"],
    "E": ["Germany", "Curacao", "Ivory Coast", "Ecuador"],
    "F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
    "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "H": ["Spain", "Cape Verde", "Saudi Arabia", "Uruguay"],
    "I": ["France", "Senegal", "Iraq", "Norway"],
    "J": ["Argentina", "Algeria", "Austria", "Jordan"],
    "K": ["Portugal", "DR Congo", "Uzbekistan", "Colombia"],
    "L": ["England", "Croatia", "Ghana", "Panama"],
}

# Cada partido: (fecha_local, hora_local "HH:MM", grupo, equipo1, equipo2, ciudad)
# La fecha/hora es LOCAL de la sede. El script calcula el UTC.
MATCHES = [
    # --- Jornada 1 ---
    ("2026-06-11", "13:00", "A", "Mexico", "South Africa", "Mexico City"),
    ("2026-06-11", "20:00", "A", "South Korea", "Czechia", "Zapopan"),
    ("2026-06-12", "15:00", "B", "Canada", "Bosnia and Herzegovina", "Toronto"),
    ("2026-06-12", "18:00", "D", "United States", "Paraguay", "Los Angeles"),
    ("2026-06-13", "12:00", "B", "Qatar", "Switzerland", "San Francisco"),
    ("2026-06-13", "18:00", "C", "Brazil", "Morocco", "New Jersey"),
    ("2026-06-13", "21:00", "C", "Haiti", "Scotland", "Boston"),
    ("2026-06-13", "18:00", "D", "Australia", "Turkiye", "Vancouver"),
    ("2026-06-14", "12:00", "E", "Germany", "Curacao", "Houston"),
    ("2026-06-14", "15:00", "F", "Netherlands", "Japan", "Dallas"),
    ("2026-06-14", "19:00", "E", "Ivory Coast", "Ecuador", "Philadelphia"),
    ("2026-06-14", "20:00", "F", "Sweden", "Tunisia", "Guadalupe"),
    ("2026-06-15", "12:00", "H", "Spain", "Cape Verde", "Atlanta"),
    ("2026-06-15", "12:00", "G", "Belgium", "Egypt", "Vancouver"),
    ("2026-06-15", "18:00", "H", "Saudi Arabia", "Uruguay", "Miami"),
    ("2026-06-15", "18:00", "G", "Iran", "New Zealand", "Los Angeles"),
    ("2026-06-16", "15:00", "I", "France", "Senegal", "New Jersey"),
    ("2026-06-16", "18:00", "I", "Iraq", "Norway", "Boston"),
    ("2026-06-16", "20:00", "J", "Argentina", "Algeria", "Kansas City"),
    ("2026-06-16", "21:00", "J", "Austria", "Jordan", "San Francisco"),
    ("2026-06-17", "12:00", "K", "Portugal", "DR Congo", "Houston"),
    ("2026-06-17", "15:00", "L", "England", "Croatia", "Dallas"),
    ("2026-06-17", "19:00", "L", "Ghana", "Panama", "Toronto"),
    ("2026-06-17", "20:00", "K", "Uzbekistan", "Colombia", "Mexico City"),
    # --- Jornada 2 ---
    ("2026-06-18", "12:00", "A", "Czechia", "South Africa", "Atlanta"),
    ("2026-06-18", "12:00", "B", "Switzerland", "Bosnia and Herzegovina", "Los Angeles"),
    ("2026-06-18", "15:00", "B", "Canada", "Qatar", "Vancouver"),
    ("2026-06-18", "19:00", "A", "Mexico", "South Korea", "Zapopan"),
    ("2026-06-19", "18:00", "C", "Scotland", "Morocco", "Boston"),
    ("2026-06-19", "12:00", "D", "United States", "Australia", "Seattle"),
    ("2026-06-19", "20:30", "C", "Brazil", "Haiti", "Philadelphia"),
    ("2026-06-19", "21:00", "D", "Turkiye", "Paraguay", "San Francisco"),
    ("2026-06-20", "12:00", "F", "Netherlands", "Sweden", "Houston"),
    ("2026-06-20", "16:00", "E", "Germany", "Ivory Coast", "Toronto"),
    ("2026-06-20", "19:00", "E", "Ecuador", "Curacao", "Kansas City"),
    ("2026-06-20", "22:00", "F", "Tunisia", "Japan", "Guadalupe"),
    ("2026-06-21", "12:00", "H", "Spain", "Saudi Arabia", "Atlanta"),
    ("2026-06-21", "12:00", "G", "Belgium", "Iran", "Los Angeles"),
    ("2026-06-21", "18:00", "H", "Uruguay", "Cape Verde", "Miami"),
    ("2026-06-21", "18:00", "G", "New Zealand", "Egypt", "Vancouver"),
    ("2026-06-22", "12:00", "J", "Argentina", "Austria", "Dallas"),
    ("2026-06-22", "17:00", "I", "France", "Iraq", "Philadelphia"),
    ("2026-06-22", "20:00", "I", "Norway", "Senegal", "New Jersey"),
    ("2026-06-22", "20:00", "J", "Jordan", "Algeria", "San Francisco"),
    ("2026-06-23", "12:00", "K", "Portugal", "Uzbekistan", "Houston"),
    ("2026-06-23", "16:00", "L", "England", "Ghana", "Boston"),
    ("2026-06-23", "19:00", "L", "Panama", "Croatia", "Toronto"),
    ("2026-06-23", "20:00", "K", "Colombia", "DR Congo", "Zapopan"),
    # --- Jornada 3 ---
    ("2026-06-24", "12:00", "B", "Switzerland", "Canada", "Vancouver"),
    ("2026-06-24", "12:00", "B", "Bosnia and Herzegovina", "Qatar", "Seattle"),
    ("2026-06-24", "18:00", "C", "Scotland", "Brazil", "Miami"),
    ("2026-06-24", "18:00", "C", "Morocco", "Haiti", "Atlanta"),
    ("2026-06-24", "19:00", "A", "Czechia", "Mexico", "Mexico City"),
    ("2026-06-24", "19:00", "A", "South Africa", "South Korea", "Guadalupe"),
    ("2026-06-25", "16:00", "E", "Ecuador", "Germany", "New Jersey"),
    ("2026-06-25", "16:00", "E", "Curacao", "Ivory Coast", "Philadelphia"),
    ("2026-06-25", "18:00", "F", "Japan", "Sweden", "Dallas"),
    ("2026-06-25", "18:00", "F", "Tunisia", "Netherlands", "Kansas City"),
    ("2026-06-25", "19:00", "D", "Turkiye", "United States", "Los Angeles"),
    ("2026-06-25", "19:00", "D", "Paraguay", "Australia", "San Francisco"),
    ("2026-06-26", "15:00", "I", "Norway", "France", "Boston"),
    ("2026-06-26", "15:00", "I", "Senegal", "Iraq", "Toronto"),
    ("2026-06-26", "19:00", "H", "Cape Verde", "Saudi Arabia", "Houston"),
    ("2026-06-26", "18:00", "H", "Uruguay", "Spain", "Zapopan"),
    ("2026-06-26", "20:00", "G", "Egypt", "Iran", "Seattle"),
    ("2026-06-26", "20:00", "G", "New Zealand", "Belgium", "Vancouver"),
    ("2026-06-27", "17:00", "L", "Panama", "England", "New Jersey"),
    ("2026-06-27", "17:00", "L", "Croatia", "Ghana", "Philadelphia"),
    ("2026-06-27", "19:30", "K", "Colombia", "Portugal", "Miami"),
    ("2026-06-27", "19:30", "K", "DR Congo", "Uzbekistan", "Atlanta"),
    ("2026-06-27", "21:00", "J", "Algeria", "Austria", "Kansas City"),
    ("2026-06-27", "21:00", "J", "Jordan", "Argentina", "Dallas"),
]


def matchday_of(date_str):
    d = datetime.strptime(date_str, "%Y-%m-%d").date()
    if d <= datetime(2026, 6, 17).date():
        return 1
    if d <= datetime(2026, 6, 23).date():
        return 2
    return 3


def to_utc_iso(date_str, time_str, city):
    off = CITY_OFFSET[city]
    local = datetime.strptime(date_str + " " + time_str, "%Y-%m-%d %H:%M")
    # hora local -> UTC: restamos el offset (que es negativo, asi que suma)
    utc = local - timedelta(hours=off)
    return utc.replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build():
    # groups.json
    groups_out = {}
    for g, teams in GROUPS.items():
        groups_out[g] = [
            {"key": t, "name": TEAMS[t][0], "flag": TEAMS[t][1]} for t in teams
        ]

    # matches.json
    matches_out = []
    for i, (date_str, time_str, group, t1, t2, city) in enumerate(MATCHES, start=1):
        matches_out.append({
            "id": i,
            "matchday": matchday_of(date_str),
            "group": group,
            "kickoff_utc": to_utc_iso(date_str, time_str, city),
            "city": city,
            "stadium": STADIUM.get(city, ""),
            "canales": CHANNELS.get(frozenset((t1, t2)), []),
            "team1": {"key": t1, "name": TEAMS[t1][0], "flag": TEAMS[t1][1]},
            "team2": {"key": t2, "name": TEAMS[t2][0], "flag": TEAMS[t2][1]},
            "score1": None,
            "score2": None,
            "status": "SCHEDULED",  # SCHEDULED | IN_PLAY | FINISHED
        })

    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, "groups.json"), "w", encoding="utf-8") as f:
        json.dump(groups_out, f, ensure_ascii=False, indent=2)
    with open(os.path.join(DATA, "matches.json"), "w", encoding="utf-8") as f:
        json.dump({"updated_utc": None, "matches": matches_out}, f,
                  ensure_ascii=False, indent=2)

    print("OK -> %d partidos, %d grupos" % (len(matches_out), len(groups_out)))


if __name__ == "__main__":
    build()
