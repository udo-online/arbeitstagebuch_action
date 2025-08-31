from flask import Flask, request, jsonify, send_from_directory, url_for
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import os
import datetime
import uuid

WOCHENTAGE_DE = {
    0: "Montag",
    1: "Dienstag",
    2: "Mittwoch",
    3: "Donnerstag",
    4: "Freitag",
    5: "Samstag",
    6: "Sonntag"
}

WOCHENTAGE_KURZ_DE = {
    "Mo": "Montag",
    "Di": "Dienstag",
    "Mi": "Mittwoch",
    "Do": "Donnerstag",
    "Fr": "Freitag",
    "Sa": "Samstag",
    "So": "Sonntag"
}

app = Flask(__name__)
OUTPUT_DIR = "files"
os.makedirs(OUTPUT_DIR, exist_ok=True)

API_KEY = os.getenv("ATB_API_KEY", "mein-super-key")


def auth_ok(req):
    auth = req.headers.get("Authorization", "")
    return auth == f"Bearer {API_KEY}"


def create_tagesblatt_pdf(filename, datum, start, stop, pause, arbeitszeit, gesamtzeit, taetigkeiten, kw_label):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 14)
    c.drawString(20 * mm, height - 20 * mm, "Arbeitstagebuch")
    c.setFont("Helvetica", 12)
    c.drawRightString(width - 20 * mm, height - 20 * mm, kw_label)

    c.line(20 * mm, height - 22 * mm, width - 20 * mm, height - 22 * mm)

    date_obj = datetime.datetime.strptime(datum, "%Y-%m-%d")
    weekday_index = date_obj.weekday()
    weekday_de = WOCHENTAGE_DE[weekday_index]
    date_str = date_obj.strftime("%d.%m.%Y")

    c.setFont("Helvetica", 11)
    c.drawString(30 * mm, height - 40 * mm, f"Datum:      {weekday_de}, {date_str}")
    c.drawString(30 * mm, height - 50 * mm, f"Start:      {start}")
    c.drawString(30 * mm, height - 60 * mm, f"Stopp:      {stop}")
    c.drawString(30 * mm, height - 70 * mm, f"Arbeitszeit: {arbeitszeit:.1f} Std.")

    if weekday_index == 6:
        c.drawString(30 * mm, height - 80 * mm, f"Gesamtzeit: {gesamtzeit:.1f} Std. (Sonntagsstunden mit %!)")
    else:
        c.drawString(30 * mm, height - 80 * mm, f"Gesamtzeit: {gesamtzeit:.1f} Std.")

    c.line(20 * mm, height - 90 * mm, width - 20 * mm, height - 90 * mm)

    c.setFont("Helvetica-Bold", 11)
    c.drawString(30 * mm, height - 105 * mm, "Tätigkeiten:")
    c.setFont("Helvetica", 11)

    y = height - 115 * mm
    for taetigkeit in taetigkeiten:
        c.drawString(40 * mm, y, f"• {taetigkeit}")
        y -= 7 * mm

    c.setFont("Helvetica", 9)
    c.drawString(20 * mm, 15 * mm, "Seite 1")
    c.drawRightString(width - 20 * mm, 15 * mm, "(c)2025 – Arbeitstagebuch_UM")

    c.showPage()
    c.save()


def create_wochenuebersicht_pdf(filename, kw_label, weekData, created_date=None):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 14)
    c.drawString(20 * mm, height - 20 * mm, "Wochenübersicht")
    c.setFont("Helvetica", 12)
    c.drawRightString(width - 20 * mm, height - 20 * mm, kw_label)

    c.line(20 * mm, height - 22 * mm, width - 20 * mm, height - 22 * mm)

    total_weekday = 0.0
    total_all = 0.0
    sat = 0.0
    sun = 0.0

    y = height - 40 * mm

    for item in weekData:
        day = item["day"]
        day_name = WOCHENTAGE_KURZ_DE.get(day, day)
        hours = item.get("hours")
        special = item.get("special")

        c.setFont("Helvetica", 11)
        c.drawString(30 * mm, y, f"{day_name}:")

        if special in ("Urlaub", "Krank", "Feiertag"):
            c.drawRightString(width - 40 * mm, y, "8,0 Std.")
            c.drawRightString(width - 20 * mm, y, f"({special})")
            if day in ["Mo", "Di", "Mi", "Do", "Fr"]:
                total_weekday += 8.0
            total_all += 8.0
        elif hours:
            c.drawRightString(width - 40 * mm, y, f"{hours:.1f} Std.")
            if day in ["Mo", "Di", "Mi", "Do", "Fr"]:
                total_weekday += hours
            if day == "Sa":
                sat = hours
            elif day == "So":
                sun = hours
            total_all += hours
        else:
            c.drawRightString(width - 40 * mm, y, "–")

        y -= 8 * mm

    overtime = total_weekday - 40.0

    y -= 5 * mm
    c.line(30 * mm, y, width - 20 * mm, y)

    y -= 10 * mm
    c.setFont("Helvetica", 11)
    c.drawString(30 * mm, y, "Gesamt (Mo–Fr):")
    c.drawRightString(width - 40 * mm, y, f"{total_weekday:.1f} Std.")

    y -= 8 * mm
    c.drawString(30 * mm, y, "Überstunden (Mo–Fr):")
    c.drawRightString(width - 40 * mm, y, f"{overtime:+.1f} Std.")
    c.drawRightString(width - 20 * mm, y, "(Basis 40,0 Std./Woche)")

    if sat > 0:
        y -= 8 * mm
        c.drawString(30 * mm, y, "Samstagsstunden:")
        c.drawRightString(width - 40 * mm, y, f"{sat:.1f} Std.")

    if sun > 0:
        y -= 8 * mm
        c.drawString(30 * mm, y, "Sonntagsstunden:")
        c.drawRightString(width - 40 * mm, y, f"{sun:.1f} Std.")

    y -= 8 * mm
    c.drawString(30 * mm, y, "Gesamt (Mo–So):")
    c.drawRightString(width - 40 * mm, y, f"{total_all:.1f} Std.")

    c.setFont("Helvetica", 9)
    c.drawString(20 * mm, 15 * mm, "Seite 1")
    if created_date:
        created_str = created_date.strftime("Erstellt am: %d.%m.%Y")
        c.drawRightString(width - 20 * mm, 15 * mm, created_str)
    else:
        c.drawRightString(width - 20 * mm, 15 * mm, "(c)2025 – Arbeitstagebuch_UM")

    c.showPage()
    c.save()


@app.route("/tagesblatt", methods=["POST"])
def tagesblatt():
    if not auth_ok(request):
        return "Unauthorized", 401

    data = request.json
    datum = data["datum"]
    start = data["start"]
    stop = data["stop"]
    pause = data.get("pause", 0.5)
    taetigkeiten = data.get("taetigkeiten", [])
    kw_label = data.get("kwLabel", "")

    fmt = "%H:%M Uhr"
    start_dt = datetime.datetime.strptime(start, fmt)
    stop_dt = datetime.datetime.strptime(stop, fmt)

    arbeitszeit = (stop_dt - start_dt).total_seconds() / 3600 - pause
    gesamtzeit = (stop_dt - start_dt).total_seconds() / 3600

    file_id = f"tagesblatt_{uuid.uuid4().hex}.pdf"
    filepath = os.path.join(OUTPUT_DIR, file_id)
    create_tagesblatt_pdf(filepath, datum, start, stop, pause, arbeitszeit, gesamtzeit, taetigkeiten, kw_label)

    url = request.url_root.replace("http://", "https://").rstrip("/") + url_for("serve_file", name=file_id)
    return jsonify({"url": url})


@app.route("/woche", methods=["POST"])
def woche():
    if not auth_ok(request):
        return "Unauthorized", 401

    data = request.json
    kw_label = data["kwLabel"]
    weekData = data["weekData"]
    created_date = datetime.datetime.now()

    file_id = f"woche_{uuid.uuid4().hex}.pdf"
    filepath = os.path.join(OUTPUT_DIR, file_id)
    create_wochenuebersicht_pdf(filepath, kw_label, weekData, created_date)

    url = request.url_root.replace("http://", "https://").rstrip("/") + url_for("serve_file", name=file_id)
    return jsonify({"url": url})


@app.route("/gesamt", methods=["POST"])
def gesamt():
    if not auth_ok(request):
        return "Unauthorized", 401

    data = request.json
    datum = data["datum"]
    start = data["start"]
    stop = data["stop"]
    pause = data.get("pause", 0.5)
    taetigkeiten = data.get("taetigkeiten", [])
    kw_label = data.get("kwLabel", "")

    fmt = "%H:%M Uhr"
    start_dt = datetime.datetime.strptime(start, fmt)
    stop_dt = datetime.datetime.strptime(stop, fmt)
    arbeitszeit = (stop_dt - start_dt).total_seconds() / 3600 - pause
    gesamtzeit = (stop_dt - start_dt).total_seconds() / 3600

    file_id_t = f"tagesblatt_{uuid.uuid4().hex}.pdf"
    filepath_t = os.path.join(OUTPUT_DIR, file_id_t)
    create_tagesblatt_pdf(filepath_t, datum, start, stop, pause, arbeitszeit, gesamtzeit, taetigkeiten, kw_label)

    url_t = request.url_root.replace("http://", "https://").rstrip("/") + url_for("serve_file", name=file_id_t)

    weekData = data["weekData"]
    file_id_w = f"woche_{uuid.uuid4().hex}.pdf"
    filepath_w = os.path.join(OUTPUT_DIR, file_id_w)
    create_wochenuebersicht_pdf(filepath_w, kw_label, weekData, datetime.datetime.now())

    url_w = request.url_root.replace("http://", "https://").rstrip("/") + url_for("serve_file", name=file_id_w)

    return jsonify({"urls": {"tagesblatt": url_t, "woche": url_w}})


@app.route("/files/<name>")
def serve_file(name):
    return send_from_directory(OUTPUT_DIR, name)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
