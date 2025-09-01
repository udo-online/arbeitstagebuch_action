import os
import json
from flask import Flask, request, jsonify
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials

# Flask App
app = Flask(__name__)

# Speicherordner für PDFs
OUTPUT_DIR = "files"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------- Google Drive Setup ---------------- #
def init_drive():
    """
    Initialisiert Google Drive mit den Zugangsdaten.
    - Lokal: nimmt die JSON-Datei im Projektordner
    - Render: nimmt die Secret-Datei unter /etc/secrets/arbeitstagebuch-key.json
    """
    service_account_file = "/etc/secrets/arbeitstagebuch-key.json"
    if not os.path.exists(service_account_file):
        service_account_file = "arbeitstagebuch-470720-a7eb9b20a922.json"  # Lokale Datei

    scope = ['https://www.googleapis.com/auth/drive.file']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(service_account_file, scope)

    gauth = GoogleAuth()
    gauth.credentials = credentials
    return GoogleDrive(gauth)


def upload_to_drive(local_path: str, filename: str, folder_id: str = None):
    """
    Lädt eine Datei nach Google Drive hoch.
    Wichtig: Service Accounts haben kein eigenes „My Drive“-Quota,
    deshalb MUSS immer ein Ziel-Ordner (parents) angegeben werden.
    """
    drive = init_drive()

    if folder_id is None:
        folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

    if not folder_id:
        raise RuntimeError("GOOGLE_DRIVE_FOLDER_ID ist nicht gesetzt!")

    # Metadaten inkl. Eltern-Ordner setzen
    metadata = {
        "title": filename,
        "parents": [{"id": folder_id}]
    }

    gfile = drive.CreateFile(metadata)
    gfile.SetContentFile(local_path)
    gfile.Upload()

    print(f"✅ Datei {filename} erfolgreich nach Google Drive hochgeladen in Ordner {folder_id}")
    return gfile['id']


# ---------------- PDF Generator ---------------- #
def create_tagesblatt(data):
    """
    Erzeugt ein Tagesblatt-PDF und lädt es nach Google Drive hoch.
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

    # Google Drive Upload
    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")  # Ordner-ID aus Environment
    if folder_id:
        upload_to_drive(pdf_path, pdf_filename, folder_id)

    return pdf_path


# ---------------- API Endpunkte ---------------- #
@app.route("/tagesblatt", methods=["POST"])
def tagesblatt():
    data = request.json
    try:
        pdf_path = create_tagesblatt(data)
        return jsonify({"url": f"/{pdf_path}"})
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/")
def root():
    return "Arbeitstagebuch API läuft 🚀"


# ---------------- Start ---------------- #
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render nutzt eigenen Port
    app.run(host="0.0.0.0", port=port)
