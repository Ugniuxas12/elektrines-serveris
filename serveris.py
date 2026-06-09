from flask import Flask, jsonify, request, send_from_directory
from datetime import datetime
import os

app = Flask(__name__)

# ─── Duomenų saugykla ─────────────────────────────────────────────────────

nustatymai = {
    1: {
        "id": 1,
        "name": "Elektrine 1",
        "vietove": "Valmantiskiai",
        "jautrumas": 50,
        "uzdelsimasSek": 5,
        "infoRinkimasMin": 3,
        "maxVejas": 15,
        "stabdo": True,
        "rankinis": False,
        "kampas": 0,
        "status": "online"
    },
    2: {
        "id": 2,
        "name": "Elektrine 2",
        "vietove": "Eugenijaus",
        "jautrumas": 70,
        "uzdelsimasSek": 2,
        "infoRinkimasMin": 1,
        "maxVejas": 20,
        "stabdo": True,
        "rankinis": False,
        "kampas": 0,
        "status": "online"
    },
    3: {
        "id": 3,
        "name": "Elektrine 3",
        "vietove": "Sadausko",
        "jautrumas": 30,
        "uzdelsimasSek": 10,
        "infoRinkimasMin": 5,
        "maxVejas": 18,
        "stabdo": False,
        "rankinis": True,
        "kampas": 270,
        "status": "standby"
    }
}

busena = {
    1: {"galia": 0, "temp": 0, "apkrova": 0, "paskCartasOnline": None},
    2: {"galia": 0, "temp": 0, "apkrova": 0, "paskCartasOnline": None},
    3: {"galia": 0, "temp": 0, "apkrova": 0, "paskCartasOnline": None},
}

def log(tekstas):
    laika = datetime.now().strftime("%H:%M:%S")
    print(f"[{laika}] {tekstas}")

# ─── Statinis UI puslapis ─────────────────────────────────────────────────

@app.route("/")
def index():
    if os.path.exists("index.html"):
        return send_from_directory(".", "index.html")
    return "<h2>Serveris veikia! API pasiekiamas per /api/</h2>"

# ─── Visi nustatymai ──────────────────────────────────────────────────────

@app.route("/api/settings", methods=["GET"])
def gauti_visus():
    log("GET /api/settings")
    return jsonify(list(nustatymai.values()))

# ─── Vienos elektrinės nustatymai — ESP32 naudoja šį ─────────────────────

@app.route("/api/settings/<int:nr>", methods=["GET"])
def gauti_viena(nr):
    if nr not in nustatymai:
        log(f"GET /api/settings/{nr} -> 404")
        return jsonify({"klaida": "Elektrine nerasta"}), 404

    log(f"GET /api/settings/{nr} <- {nustatymai[nr]['vietove']}")
    return jsonify(nustatymai[nr])

# ─── Atnaujinti nustatymus — UI siunčia ───────────────────────────────────

@app.route("/api/settings/<int:nr>", methods=["POST"])
def atnaujinti(nr):
    if nr not in nustatymai:
        return jsonify({"klaida": "Elektrine nerasta"}), 404

    duomenys = request.get_json()
    if not duomenys:
        return jsonify({"klaida": "Nera duomenu"}), 400

    leistini_laukai = [
        "jautrumas", "uzdelsimasSek", "infoRinkimasMin",
        "maxVejas", "stabdo", "rankinis", "kampas", "status"
    ]

    for laukas in leistini_laukai:
        if laukas in duomenys:
            nustatymai[nr][laukas] = duomenys[laukas]

    log(f"POST /api/settings/{nr} -> atnaujinta: {duomenys}")
    return jsonify({"ok": True, "nustatymai": nustatymai[nr]})

# ─── ESP32 siunčia savo būseną ────────────────────────────────────────────

@app.route("/api/status/<int:nr>", methods=["POST"])
def gauti_busena(nr):
    if nr not in busena:
        return jsonify({"klaida": "Elektrine nerasta"}), 404

    duomenys = request.get_json()
    if duomenys:
        busena[nr].update(duomenys)
        busena[nr]["paskCartasOnline"] = datetime.now().strftime("%H:%M:%S")
        log(f"STATUS {nr} <- {duomenys}")

    return jsonify({"ok": True})

# ─── Visų elektrinių būsena — UI naudoja ─────────────────────────────────

@app.route("/api/status", methods=["GET"])
def visu_busena():
    return jsonify(busena)

# ─── Greita komanda ───────────────────────────────────────────────────────

@app.route("/api/komanda/<int:nr>", methods=["POST"])
def komanda(nr):
    if nr not in nustatymai:
        return jsonify({"klaida": "Elektrine nerasta"}), 404

    duomenys = request.get_json()
    veiksmas = duomenys.get("veiksmas") if duomenys else None

    if veiksmas == "stop":
        nustatymai[nr]["rankinis"] = True
        nustatymai[nr]["kampas"] = 0
        log(f"KOMANDA {nr}: STOP")
    elif veiksmas == "vakarus":
        nustatymai[nr]["rankinis"] = True
        nustatymai[nr]["kampas"] = 90
        log(f"KOMANDA {nr}: VAKARUS")
    elif veiksmas == "rytus":
        nustatymai[nr]["rankinis"] = True
        nustatymai[nr]["kampas"] = 270
        log(f"KOMANDA {nr}: RYTUS")
    elif veiksmas == "auto":
        nustatymai[nr]["rankinis"] = False
        log(f"KOMANDA {nr}: AUTO rezimas")
    else:
        return jsonify({"klaida": f"Nezinomas veiksmas: {veiksmas}"}), 400

    return jsonify({"ok": True})

# ─── Paleidimas ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("  Elektriniu valdymo serveris")
    print("=" * 50)
    print("  http://localhost:5000")
    print("")
    print("  GET  /api/settings      - visi nustatymai")
    print("  GET  /api/settings/1    - elektrine 1")
    print("  POST /api/settings/1    - keisti nustatymus")
    print("  POST /api/status/1      - ESP32 busena")
    print("  GET  /api/status        - visu busena")
    print("  POST /api/komanda/1     - greita komanda")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=False)