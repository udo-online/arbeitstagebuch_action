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
    Initialisiert Google Drive mit den Zugangsdaten aus der Environment Variable GOOGLE_SERVICE_ACCOUNT.
    """
    service_json = os.getenv("GOOGLE_SERVICE_ACCOUNT")
    if not service_json:
        raise RuntimeError("Fehlende GOOGLE_SERVICE_ACCOUNT Variable auf Render")

    creds_dict = json.loads(service_json)
    scope = ['https://www.googleapis.com/auth/drive.file']
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

    gauth = GoogleAuth()
    gauth.credentials = credentials
    return GoogleDrive(gauth)

def upload_to_drive(local_path: str, filename: str, folder_id: str = None):
    """
    Lädt eine Datei nach Google Drive hoch.
    :param local_path: Lokaler Pfad der Datei
    :param filename: Dateiname, der in Google Drive erscheinen soll
    :param folder_id: Google Drive Ordner-ID
    """
    drive = init_drive()
    gfile = drive.CreateFile(
        {"title": filename, "parents": [{"id": folder_id}]} if folder_id else {"title": filename}
    )
    gfile.SetContentFile(local_path)
    gfile.Upload()
    print(f"✅ Datei {filename} erfolgreich nach Google Drive hochgeladen")
    return gfile['id']  # gibt die Google Drive File-ID zurück


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
    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")  # hier Ordner-ID aus Environment
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
        return jsonify({"error": str(e)}), 500


@app.route("/")
def root():
    return "Arbeitstagebuch API läuft 🚀"


# ---------------- Start ---------------- #
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
