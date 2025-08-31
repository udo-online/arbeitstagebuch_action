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


# (Rest der create_wochenuebersicht_pdf und Flask-Routen bleiben unverändert wie zuvor)
