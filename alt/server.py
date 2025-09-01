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

    # Kopfzeile
    c.setFont("Helvetica-Bold", 14)
    c.drawString(20 * mm, height - 20 * mm, "Arbeitstagebuch")
    c.setFont("Helvetica", 12)
    c.drawRightString(width - 20 * mm, height - 20 * mm, kw_label)

    c.line(20 * mm, height - 22 * mm, width - 20 * mm, height - 22 * mm)

    # Datum
    date_obj = datetime.datetime.strptime(datum, "%Y-%m-%d")
    weekday_index = date_obj.weekday()
    weekday_de = WOCHENTAGE_DE[weekday_index]
    date_str = date_obj.strftime("%d.%m.%Y")

    c.setFont("Helvetica", 11)
    c.drawString(30 * mm, height - 40 * mm, "Datum:")
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(width - 40 * mm, height - 40 * mm, f"{weekday_de}, {date_str}")

    # Start
    c.setFont("Helvetica", 11)
    c.drawString(30 * mm, height - 50 * mm, "Start:")
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(width - 40 * mm, height - 50 * mm, start)

    # Stopp
    c.setFont("Helvetica", 11)
    c.drawString(30 * mm, height - 60 * mm, "Stopp:")
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(width - 40 * mm, height - 60 * mm, stop)

    # Arbeitszeit
    c.setFont("Helvetica", 11)
    c.drawString(30 * mm, height - 70 * mm, "Arbeitszeit:")
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(width - 40 * mm, height - 70 * mm, f"{arbeitszeit:.1f} Std.")

    # Gesamtzeit (mit Sonntagshinweis)
    c.setFont("Helvetica", 11)
    c.drawString(30 * mm, height - 80 * mm, "Gesamtzeit:")
    c.setFont("Helvetica-Bold", 11)
    if weekday_index == 6:  # Sonntag
        c.drawRightString(width - 40 * mm, height - 80 * mm, f"{gesamtzeit:.1f} Std. (Sonntagsstunden mit %!)")
    else:
        c.drawRightString(width - 40 * mm, height - 80 * mm, f"{gesamtzeit:.1f} Std.")

    # Linie
    c.line(20 * mm, height - 90 * mm, width - 20 * mm, height - 90 * mm)

    # Tätigkeiten
    c.setFont("Helvetica-Bold", 11)
    c.drawString(30 * mm, height - 105 * mm, "Tätigkeiten:")
    c.setFont("Helvetica", 11)
    y = height - 115 * mm
    for t in taetigkeiten:
        c.drawString(40 * mm, y, f"• {t}")
        y -= 7 * mm

    # Fußzeile
    c.setFont("Helvetica", 9)
    c.drawString(20 * mm, 15 * mm, "Seite 1")
    c.drawRightString(width - 20 * mm, 15 * mm, "(c)2025 – Arbeitstagebuch_UM")

    c.showPage()
    c.save()


def create_wochenuebersicht_pdf(filename, kw_label, weekData):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    # Kopfzeile
    c.setFont("Helvetica-Bold", 14)
    c.drawString(20 * mm, height - 20 * mm, "Wochenübersicht")
    c.setFont("Helvetica", 12)
    c.drawRightString(width - 20 * mm, height - 20 * mm, kw_label)

    c.line(20 * mm, height - 22 * mm, width - 20 * mm, height - 22 * mm)

    y = height - 40 * mm
    total_hours = 0

    for item in weekData:
        day = item["day"]
        hours = item.get("hours")
        special = item.get("special")

        day_name = WOCHENTAGE_KURZ_DE.get(day, day)

        c.setFont("Helvetica", 11)
        c.drawString(30 * mm, y, f"{day_name}:")

        if special in ("Urlaub", "Krank", "Feiertag"):
            c.setFont("Helvetica-Bold", 11)
            c.drawRightString(width - 40 * mm, y, "8,0 Std.")
            c.setFont("Helvetica", 11)
            c.drawRightString(width - 20 * mm, y, f"({special})")
            total_hours += 8.0
        elif hours is not None:
            c.setFont("Helvetica-Bold", 11)
            c.drawRightString(width - 40 * mm, y, f"{hours:.1f} Std.")
            total_hours += hours
        else:
            c.setFont("Helvetica", 11)
            c.drawRightString(width - 40 * mm, y, "–")

        y -= 10 * mm

    # Summen
    c.line(20 * mm, y, width - 20 * mm, y)
    y -= 10 * mm

    c.setFont("Helvetica", 11)
    c.drawString(30 * mm, y, "Gesamtstunden:")
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(width - 40 * mm, y, f"{total_hours:.1f} Std.")

    y -= 10 * mm
    c.setFont("Helvetica", 11)
    c.drawString(30 * mm, y, "Überstunden (40,0 Soll):")
    c.setFont("Helvetica-Bold", 11)
    overtime = total_hours - 40.0
    c.drawRightString(width - 40 * mm, y, f"{overtime:+.1f} Std.")

    # Fußzeile
    c.setFont("Helvetica", 9)
    c.drawString(20 * mm, 15 * mm, "Seite 1")
    c.drawRightString(width - 20 * mm, 15 * mm, "(c)2025 – Arbeitstagebuch_UM")

    c.showPage()
    c.save()


@app.route("/tagesblatt", methods=["POST"])
def tagesblatt():
    if not auth_ok(request):
        return "Unauthorized", 401

    data = request.get_json()
    datum = data["datum"]
    start = data["start"]
    stop = data["stop"]
    pause = float(data.get("pause", 0.5))
    taetigkeiten = data.get("taetigkeiten", [])
    kw_label = data.get("kwLabel", "")

    fmt = "%H:%M Uhr"
    start_dt = datetime.datetime.strptime(start, fmt)
    stop_dt = datetime.datetime.strptime(stop, fmt)
    diff = (stop_dt - start_dt).seconds / 3600.0
    arbeitszeit = diff - pause
    gesamtzeit = diff

    file_id = str(uuid.uuid4()).replace("-", "")[:8]
    filename = f"tagesblatt_{file_id}.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)

    create_tagesblatt_pdf(filepath, datum, start, stop, pause, arbeitszeit, gesamtzeit, taetigkeiten, kw_label)

    return jsonify({"url": url_for("get_file", filename=filename, _external=True)})


@app.route("/woche", methods=["POST"])
def woche():
    if not auth_ok(request):
        return "Unauthorized", 401

    data = request.get_json()
    kw_label = data["kwLabel"]
    weekData = data["weekData"]

    file_id = str(uuid.uuid4()).replace("-", "")[:8]
    filename = f"woche_{file_id}.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)

    create_wochenuebersicht_pdf(filepath, kw_label, weekData)

    return jsonify({"url": url_for("get_file", filename=filename, _external=True)})


@app.route("/gesamt", methods=["POST"])
def gesamt():
    if not auth_ok(request):
        return "Unauthorized", 401

    data = request.get_json()
    datum = data["datum"]
    start = data["start"]
    stop = data["stop"]
    pause = float(data.get("pause", 0.5))
    taetigkeiten = data.get("taetigkeiten", [])
    kw_label = data.get("kwLabel", "")
    weekData = data["weekData"]

    fmt = "%H:%M Uhr"
    start_dt = datetime.datetime.strptime(start, fmt)
    stop_dt = datetime.datetime.strptime(stop, fmt)
    diff = (stop_dt - start_dt).seconds / 3600.0
    arbeitszeit = diff - pause
    gesamtzeit = diff

    file_id = str(uuid.uuid4()).replace("-", "")[:8]
    filename_tb = f"tagesblatt_{file_id}.pdf"
    filepath_tb = os.path.join(OUTPUT_DIR, filename_tb)
    create_tagesblatt_pdf(filepath_tb, datum, start, stop, pause, arbeitszeit, gesamtzeit, taetigkeiten, kw_label)

    filename_w = f"woche_{file_id}.pdf"
    filepath_w = os.path.join(OUTPUT_DIR, filename_w)
    create_wochenuebersicht_pdf(filepath_w, kw_label, weekData)

    return jsonify({
        "urls": {
            "tagesblatt": url_for("get_file", filename=filename_tb, _external=True),
            "woche": url_for("get_file", filename=filename_w, _external=True)
        }
    })


@app.route("/files/<path:filename>")
def get_file(filename):
    return send_from_directory(OUTPUT_DIR, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
