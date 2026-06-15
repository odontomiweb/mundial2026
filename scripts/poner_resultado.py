# -*- coding: utf-8 -*-
"""
Poner resultados a mano (plan B, sin internet ni API).

Te muestra la lista de partidos, eliges uno por su numero, escribes el
marcador y se guarda en data/matches.json. Al final te pregunta si quieres
subirlo a internet (GitHub) para que se vea en la pagina.

Para usarlo: doble clic en  poner_resultado.bat
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone

# Que la consola de Windows muestre tildes y emojis sin reventar
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
MATCHES_FILE = os.path.join(ROOT, "data", "matches.json")
CHILE_OFFSET = -4  # En junio Chile esta en UTC-4


def chile_str(utc_iso):
    """Convierte la hora UTC del partido a hora de Chile, bonita."""
    try:
        dt = datetime.strptime(utc_iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        loc = dt + timedelta(hours=CHILE_OFFSET)
        dias = ["lun", "mar", "mie", "jue", "vie", "sab", "dom"]
        return "%s %02d/%02d %02d:%02d" % (dias[loc.weekday()], loc.day, loc.month, loc.hour, loc.minute)
    except Exception:
        return utc_iso


def estado_txt(m):
    if m["status"] == "FINISHED":
        return "FINAL  %s-%s" % (m["score1"], m["score2"])
    if m["status"] == "IN_PLAY":
        return "EN VIVO %s-%s" % (m["score1"], m["score2"])
    return "- pendiente -"


def pedir_numero(texto):
    """Pide un numero entero (goles). Vacio = cancelar."""
    while True:
        v = input(texto).strip()
        if v == "":
            return None
        if v.isdigit():
            return int(v)
        print("   (escribe solo un numero, ej: 2)")


def listar(matches):
    print("\n" + "=" * 64)
    jornada = None
    for i, m in enumerate(matches, start=1):
        if m["matchday"] != jornada:
            jornada = m["matchday"]
            print("\n  --- JORNADA %d ---" % jornada)
        marca = "*" if m["status"] != "SCHEDULED" else " "
        print(" %s %2d) %-14s  %-16s vs %-16s  [%s]" % (
            marca, i, chile_str(m["kickoff_utc"]),
            m["team1"]["name"], m["team2"]["name"], estado_txt(m)))
    print("=" * 64)


def editar(m):
    print("\n  >> %s  vs  %s   (%s)" % (m["team1"]["name"], m["team2"]["name"], chile_str(m["kickoff_utc"])))
    print("     (deja en blanco y Enter para cancelar)")
    g1 = pedir_numero("     Goles %s: " % m["team1"]["name"])
    if g1 is None:
        print("     Cancelado.")
        return False
    g2 = pedir_numero("     Goles %s: " % m["team2"]["name"])
    if g2 is None:
        print("     Cancelado.")
        return False
    est = ""
    while est not in ("t", "v"):
        est = input("     Termino o esta en vivo? (t = terminado / v = en vivo): ").strip().lower()
    m["score1"] = g1
    m["score2"] = g2
    m["status"] = "FINISHED" if est == "t" else "IN_PLAY"
    print("     OK: %s %d-%d %s" % (m["team1"]["name"], g1, g2, m["team2"]["name"]))
    return True


def guardar(data):
    data["updated_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(MATCHES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("\n  Guardado en data/matches.json")


def subir():
    r = input("\n  Subir a internet ahora para que se vea en la pagina? (s/n): ").strip().lower()
    if r != "s":
        print("  Listo. (No se subio; puedes subirlo despues.)")
        return
    try:
        subprocess.run(["git", "add", "data/matches.json"], cwd=ROOT, check=True)
        subprocess.run(["git", "commit", "-m", "Actualizar resultados (a mano)"], cwd=ROOT, check=True)
        subprocess.run(["git", "push"], cwd=ROOT, check=True)
        print("\n  Subido! En 1-2 minutos se ve en la pagina. ")
    except Exception as e:
        print("\n  No se pudo subir automaticamente (%s)." % e)
        print("  No te preocupes: el resultado YA quedo guardado en tu compu.")


def main():
    if not os.path.exists(MATCHES_FILE):
        print("No encuentro data/matches.json. Pon este script en la carpeta scripts del proyecto.")
        return 1
    with open(MATCHES_FILE, encoding="utf-8") as f:
        data = json.load(f)
    matches = sorted(data["matches"], key=lambda m: m["kickoff_utc"])

    print("\n  PONER RESULTADOS - Mundial 2026")
    print("  (los partidos con * ya tienen marcador)")
    cambios = 0
    while True:
        listar(matches)
        print("\n  Escribe el NUMERO del partido para poner su marcador.")
        op = input("  Numero  (o 'g' = guardar y salir,  'q' = salir sin guardar): ").strip().lower()
        if op == "q":
            if cambios:
                print("  Saliendo sin guardar los %d cambios." % cambios)
            return 0
        if op == "g":
            if cambios:
                guardar(data)
                subir()
            else:
                print("  No hiciste cambios.")
            return 0
        if op.isdigit() and 1 <= int(op) <= len(matches):
            if editar(matches[int(op) - 1]):
                cambios += 1
        else:
            print("  No entendi. Escribe un numero de la lista, 'g' o 'q'.")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nChao.")
