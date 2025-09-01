import os
import json
from flask import Flask, request, jsonify
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime

# Google API
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from oauth2client.service_account import ServiceAccountCredentials

# Flask App
app = Flask(__name__)

# Speicherordner für PDFs
OUTPUT_DIR = "files"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ---------------- Google Drive Upload (v3) ---------------- #
def upload_to_drive(local_path: str, filename: str, folder_id: str = None):
    """
    Lädt eine Datei in Google Drive (API v3, unterstützt Shared Drives).
    """
    # Service Account JSON aus Render Environment laden
    service_account_info = json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT"))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        service_account_info,
        scopes=['https://www.googleapis.com/auth/drive.file']
    )

    # Drive v3 Client
    service = build('drive', 'v3', credentials=creds)

    # Ordner-ID aus Env, falls nicht übergeben
    if not folder_id:
        folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    if not folder_id:
        raise RuntimeError("GOOGLE_DRIVE_FOLDER_ID nicht gesetzt!")

    print(f"🚀 Verwende Ordner-ID: {folder_id}")

    # Datei-Metadaten
    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }
    media = MediaFileUpload(local_path, mimetype='application/pdf')

    # Upload mit supportsAllDrives=True
    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id',
        supportsAllDrives=True
    ).execute()

    file_id = uploaded_file.get('id')
    print(f"✅ Datei {filename} hochgeladen nach Drive mit ID {file_id}")
    return file_id


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
    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    file_id = upload_to_drive(pdf_path, pdf_filename, folder_id)

    return {
        "local_path": pdf_path,
        "drive_file_id": file_id,
        "drive_link": f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
    }


# ---------------- API Endpunkte ---------------- #
@app.route("/tagesblatt", methods=["POST"])
def tagesblatt():
    data = request.json
    try:
        result = create_tagesblatt(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/")
def root():
    return "Arbeitstagebuch API läuft 🚀"


# ---------------- Start ---------------- #
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
