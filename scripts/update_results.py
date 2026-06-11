# -*- coding: utf-8 -*-
"""
Actualiza data/matches.json con los resultados reales del Mundial 2026.
Fuente: football-data.org (gratis). Necesita una clave en la variable de
entorno FOOTBALL_DATA_TOKEN (en GitHub se guarda como "secret").

Lo corre solo GitHub Actions cada cierto rato. Tambien puedes correrlo a mano:
    FOOTBALL_DATA_TOKEN=tu_clave  python scripts/update_results.py

Solo usa la libreria estandar de Python (no hay que instalar nada).
"""
import json
import os
import sys
import unicodedata
import urllib.request
import urllib.error
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
MATCHES_FILE = os.path.join(HERE, "..", "data", "matches.json")
API_URL = "https://api.football-data.org/v4/competitions/WC/matches"

# Nombres alternativos que puede usar la API -> nuestra clave interna
ALIASES = {
    "turkey": "Turkiye", "turkiye": "Turkiye",
    "usa": "United States", "unitedstatesofamerica": "United States",
    "czechrepublic": "Czechia",
    "korearepublic": "South Korea", "republicofkorea": "South Korea",
    "ivorycoast": "Ivory Coast", "cotedivoire": "Ivory Coast",
    "caboverde": "Cape Verde", "capeverdeislands": "Cape Verde",
    "drcongo": "DR Congo", "congodr": "DR Congo",
    "democraticrepublicofcongo": "DR Congo", "congodemocraticrepublic": "DR Congo",
    "bosniaherzegovina": "Bosnia and Herzegovina", "bosnia": "Bosnia and Herzegovina",
    "iranislamicrepublicof": "Iran",
}


def norm(s):
    """minusculas, sin acentos, sin espacios ni signos."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return "".join(c for c in s.lower() if c.isalnum())


def build_key_index(matches):
    """diccionario nombre_normalizado -> clave interna, segun nuestros datos."""
    idx = {}
    for m in matches:
        for side in ("team1", "team2"):
            k = m[side]["key"]
            idx[norm(k)] = k
    for alias, key in ALIASES.items():
        idx[norm(alias)] = key
    return idx


def resolve(name, idx):
    return idx.get(norm(name))


def fetch_api(token):
    req = urllib.request.Request(API_URL, headers={"X-Auth-Token": token})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    token = os.environ.get("FOOTBALL_DATA_TOKEN", "").strip()
    if not token:
        print("ERROR: falta FOOTBALL_DATA_TOKEN", file=sys.stderr)
        return 1

    with open(MATCHES_FILE, encoding="utf-8") as f:
        data = json.load(f)
    matches = data["matches"]
    idx = build_key_index(matches)

    try:
        api = fetch_api(token)
    except urllib.error.HTTPError as e:
        print("ERROR HTTP %s: %s" % (e.code, e.read().decode("utf-8", "ignore")), file=sys.stderr)
        return 1
    except Exception as e:
        print("ERROR de red: %s" % e, file=sys.stderr)
        return 1

    api_matches = api.get("matches", [])
    print("La API devolvio %d partidos" % len(api_matches))

    # Indexamos nuestros partidos por par de equipos (sin importar orden)
    def pair(a, b):
        return tuple(sorted([a, b]))

    ours = {}
    for m in matches:
        ours.setdefault(pair(m["team1"]["key"], m["team2"]["key"]), []).append(m)

    changed = 0
    for am in api_matches:
        if am.get("stage") not in (None, "GROUP_STAGE", "GROUP"):
            continue
        h = resolve(am.get("homeTeam", {}).get("name") or "", idx)
        a = resolve(am.get("awayTeam", {}).get("name") or "", idx)
        if not h or not a:
            continue
        cands = ours.get(pair(h, a))
        if not cands:
            continue
        # si hay 2 partidos entre el mismo par (no pasa en grupos), tomamos el 1ro pendiente
        target = cands[0]

        status = am.get("status", "SCHEDULED")
        ft = am.get("score", {}).get("fullTime", {})
        s1, s2 = ft.get("home"), ft.get("away")

        # Asignar marcador respetando quien es local en NUESTROS datos
        new1, new2 = None, None
        if s1 is not None and s2 is not None:
            if target["team1"]["key"] == h:
                new1, new2 = s1, s2
            else:
                new1, new2 = s2, s1

        new_status = "SCHEDULED"
        if status in ("IN_PLAY", "PAUSED"):
            new_status = "IN_PLAY"
        elif status == "FINISHED":
            new_status = "FINISHED"

        # actualizar hora si la API la corrigio
        utc = am.get("utcDate")
        if utc:
            utc = utc.replace("+00:00", "Z")
            if not utc.endswith("Z"):
                utc = utc + "Z"

        if (target["score1"] != new1 or target["score2"] != new2 or
                target["status"] != new_status or (utc and target["kickoff_utc"] != utc)):
            target["score1"] = new1
            target["score2"] = new2
            target["status"] = new_status
            if utc:
                target["kickoff_utc"] = utc
            changed += 1

    data["updated_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(MATCHES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("Listo: %d partidos actualizados." % changed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
