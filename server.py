import os
from flask import Flask, request, jsonify, send_from_directory
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime

# Flask App
app = Flask(__name__)

# Speicherordner für PDFs
OUTPUT_DIR = "files"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------- PDF Generator ---------------- #
def create_tagesblatt(data):
    """
    Erzeugt ein Tagesblatt-PDF und speichert es lokal im Ordner 'files'.
    """
    datum = data.get("datum", datetime.today().strftime("%Y-%m-%d"))
    start = data.get("start", "08:00 Uhr")
    stop = data.get("stop", "17:00 Uhr")
    pause = float(data.get("pause", 0.5))
    taetigkeiten = data.get("taetigkeiten", [])

    # Dateiname
    pdf_filename = f"tagesblatt_{datum}.pdf"
    pdf_path = os.path.join(OUTPUT_DIR, pdf_filename)

    # PDF generieren
    c = canvas.Canvas(pdf_path, pagesize=A4)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, 800, "Arbeitstagebuch")

    c.setFont("Helvetica", 12)
    c.drawString(40, 770, f"Datum: {datum}")
    c.drawString(40, 750, f"Start: {start}")
    c.drawString(40, 730, f"Stopp: {stop}")

    arbeitszeit = 9 - pause
    c.drawString(40, 710, f"Arbeitszeit: {arbeitszeit:.1f} Std.")

    # Tätigkeiten
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, 680, "Tätigkeiten:")
    c.setFont("Helvetica", 12)
    y = 660
    for t in taetigkeiten:
        c.drawString(60, y, f"- {t}")
        y -= 20

    c.save()

    return pdf_filename, pdf_path

# ---------------- API Endpunkte ---------------- #
@app.route("/tagesblatt", methods=["POST"])
def tagesblatt():
    data = request.json
    try:
        pdf_filename, pdf_path = create_tagesblatt(data)
        return jsonify({
            "local_path": pdf_path,
            "download_url": f"/files/{pdf_filename}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 📂 PDF Download-Endpunkt
@app.route("/files/<path:filename>")
def download_file(filename):
    """
    Gibt gespeicherte PDFs aus dem 'files' Ordner zurück.
    """
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)

@app.route("/")
def root():
    return "Arbeitstagebuch API läuft 🚀"

# ---------------- Start ---------------- #
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
