import os
from flask import Flask, request, jsonify
from datetime import datetime
from arbeitstagebuch_standard_python_skripte_tagesblatt_wochenubersicht import (
    create_tagesblatt_pdf,
    create_wochen_pdf,
)

# Flask App
app = Flask(__name__)

# Speicherordner für PDFs
OUTPUT_DIR = "files"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ---------------- API Endpunkte ---------------- #

@app.route("/tagesblatt", methods=["POST"])
def tagesblatt():
    """
    Erzeugt ein Tagesblatt-PDF (lokal gespeichert).
    """
    try:
        data = request.json
        datum = data.get("datum", datetime.today().strftime("%Y-%m-%d"))

        pdf_filename = f"tagesblatt_{datum}.pdf"
        pdf_path = os.path.join(OUTPUT_DIR, pdf_filename)

        # PDF erzeugen
        create_tagesblatt_pdf(data, pdf_path)

        return jsonify({
            "download_url": f"http://arbeitstagebuch-action.onrender.com/{pdf_path}",
            "local_path": pdf_path
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/wochen", methods=["POST"])
def wochen():
    """
    Erzeugt eine Wochenübersicht-PDF (lokal gespeichert).
    """
    try:
        data = request.json
        kw_label = data.get("kwLabel", "KW_unbekannt")

        pdf_filename = f"wochen_{kw_label}.pdf"
        pdf_path = os.path.join(OUTPUT_DIR, pdf_filename)

        # PDF erzeugen
        create_wochen_pdf(data, pdf_path)

        return jsonify({
            "download_url": f"http://arbeitstagebuch-action.onrender.com/{pdf_path}",
            "local_path": pdf_path
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/")
def root():
    return "Arbeitstagebuch API läuft 🚀"


# ---------------- Start ---------------- #
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
