from flask import Flask, request, jsonify, send_from_directory
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = Flask(__name__)

OUTPUT_DIR = "files"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 🔑 API-Key aus Umgebungsvariable
API_KEY = os.environ.get("ATB_API_KEY", "mein-super-key")


def create_pdf(datum, start, stop, pause, taetigkeiten, filename):
    filepath = os.path.join(OUTPUT_DIR, filename)
    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4

    c.drawString(100, height - 100, f"Tagesblatt für {datum}")
    c.drawString(100, height - 120, f"Start: {start}")
    c.drawString(100, height - 140, f"Stop: {stop}")
    c.drawString(100, height - 160, f"Pause: {pause}h")

    y = height - 200
    c.drawString(100, y, "Tätigkeiten:")
    for t in taetigkeiten:
        y -= 20
        c.drawString(120, y, f"- {t}")

    c.save()
    return filepath


@app.route("/tagesblatt", methods=["POST"])
def tagesblatt():
    # 🔒 API Key Check
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer ") or auth_header.split(" ")[1] != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(force=True)
    datum = data.get("datum", datetime.today().strftime("%Y-%m-%d"))
    start = data.get("start", "")
    stop = data.get("stop", "")
    pause = data.get("pause", 0)
    taetigkeiten = data.get("taetigkeiten", [])

    filename = f"tagesblatt_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    create_pdf(datum, start, stop, pause, taetigkeiten, filename)

    # 🔒 Fix: HTTPS erzwingen
    base_url = request.url_root.replace("http://", "https://")

    return jsonify({
        "url": f"{base_url}files/{filename}"
    })


@app.route("/files/<path:filename>")
def download_file(filename):
    return send_from_directory(OUTPUT_DIR, filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
