import os
from flask import Flask, request, jsonify
from arbeitstagebuch_standard_python_skripte_tagesblatt_wochenubersicht import (
    generate_tagesblatt,
    generate_wochenuebersicht
)

# Flask App
app = Flask(__name__)

# ---------------- API Endpunkte ---------------- #
@app.route("/tagesblatt", methods=["POST"])
def tagesblatt():
    data = request.json
    try:
        pdf_path = generate_tagesblatt(
            datum=data.get("datum"),
            start=data.get("start"),
            stop=data.get("stop"),
            pause=data.get("pause", 0.5),
            taetigkeiten=data.get("taetigkeiten", [])
        )
        return jsonify({"url": f"/{pdf_path}", "local_path": pdf_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/wochenuebersicht", methods=["POST"])
def wochenuebersicht():
    data = request.json
    try:
        pdf_path = generate_wochenuebersicht(
            kwLabel=data.get("kwLabel"),
            weekData=data.get("weekData", [])
        )
        return jsonify({"url": f"/{pdf_path}", "local_path": pdf_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/")
def root():
    return "Arbeitstagebuch API läuft 🚀"


# ---------------- Start ---------------- #
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
