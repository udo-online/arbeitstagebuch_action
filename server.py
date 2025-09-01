import os
import uuid
from flask import Flask, request, jsonify, send_from_directory
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)

# Speicherordner für PDFs
FILES_DIR = "files"
os.makedirs(FILES_DIR, exist_ok=True)

# ---- PDF Generator ----
def create_pdf(datum, start, stop, pause, taetigkeiten, filename):
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Titel
    story.append(Paragraph(f"Tagesblatt für {datum}", styles["Heading1"]))
    story.append(Spacer(1, 12))

    # Arbeitszeiten
    story.append(Paragraph(f"Start: {start}", styles["Normal"]))
    story.append(Paragraph(f"Stop: {stop}", styles["Normal"]))
    story.append(Paragraph(f"Pause: {pause}h", styles["Normal"]))
    story.append(Spacer(1, 12))

    # Tätigkeiten
    story.append(Paragraph("Tätigkeiten:", styles["Heading2"]))
    story.append(Spacer(1, 6))

    items = [ListItem(Paragraph(f"- {t}", styles["Normal"])) for t in taetigkeiten]
    story.append(ListFlowable(items, bulletType="bullet", leftIndent=20))

    doc.build(story)

# ---- Endpoint Tagesblatt ----
@app.route("/tagesblatt", methods=["POST"])
def tagesblatt():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Kein JSON erhalten"}), 400

    datum = data.get("datum")
    start = data.get("start")
    stop = data.get("stop")
    pause = data.get("pause", 0.5)
    taetigkeiten = data.get("taetigkeiten", [])

    if not datum or not start or not stop:
        return jsonify({"error": "Datum, Start und Stop sind erforderlich"}), 400

    filename = f"tagesblatt_{uuid.uuid4().hex[:8]}.pdf"
    filepath = os.path.join(FILES_DIR, filename)

    create_pdf(datum, start, stop, pause, taetigkeiten, filepath)

    file_url = f"https://arbeitstagebuch-action.onrender.com/files/{filename}"
    return jsonify({"url": file_url})

# ---- Endpoint Wochenübersicht ----
@app.route("/woche", methods=["POST"])
def woche():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Kein JSON erhalten"}), 400

    kw_label = data.get("kwLabel", "KW")
    week_data = data.get("weekData", [])

    if not week_data:
        return jsonify({"error": "weekData erforderlich"}), 400

    filename = f"wochenbericht_{uuid.uuid4().hex[:8]}.pdf"
    filepath = os.path.join(FILES_DIR, filename)

    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"Woche: {kw_label}", styles["Heading1"]))
    story.append(Spacer(1, 12))

    for day in week_data:
        line = f"{day.get('day')}: {day.get('hours', 0)} Stunden"
        if "special" in day:
            line += f" ({day['special']})"
        story.append(Paragraph(line, styles["Normal"]))

    doc.build(story)

    file_url = f"https://arbeitstagebuch-action.onrender.com/files/{filename}"
    return jsonify({"url": file_url})

# ---- Dateien ausliefern ----
@app.route("/files/<path:filename>", methods=["GET"])
def serve_file(filename):
    return send_from_directory(FILES_DIR, filename)

# ---- Start ----
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
