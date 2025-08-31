from __future__ import annotations
from flask import Flask, request, jsonify, send_file, url_for
from datetime import datetime
import os, uuid
from typing import Literal, List, Tuple

# --------- PDF: ReportLab ----------
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

SpecialT = Literal["Urlaub", "Krank", "Feiertag", None]

# ======= Layout Konstanten (aus deinem Backup, komprimiert) =======
# Tagesblatt
TB_TITLE_LEFT = "Arbeitstagebuch"
TB_FOOTER_RIGHT = "(c)2025 – Arbeitstagebuch_UM"
TB_LINE_THICK = 0.5
TB_FONT_REG = "Helvetica"
TB_FONT_BOLD = "Helvetica-Bold"
TB_SIZE_HEADER = 13
TB_SIZE_WEEK = 11
TB_SIZE_TEXT = 10.0
TB_SIZE_VALUE = 11.5
TB_SIZE_SECTION = 11.5
TB_SIZE_FOOTER = 9.0
TB_MARGIN_L = 20 * mm
TB_MARGIN_R = 20 * mm
TB_MARGIN_T = 18 * mm
TB_MARGIN_B = 18 * mm
TB_BLOCK_SHIFT_X = 20 * mm
TB_BLOCK_SHIFT_Y = 3 * mm

# Wochenübersicht
W_TITLE_LEFT = "Wochenübersicht"
W_FOOTER_RIGHT = "(c)2025 – Arbeitstagebuch_UM"
W_LINE_THICK = 0.5
W_FONT_REG = "Helvetica"
W_FONT_BOLD = "Helvetica-Bold"
W_SIZE_HEADER = 13
W_SIZE_WEEK = 11
W_SIZE_TEXT = 10.5
W_SIZE_FOOTER = 9.0
W_MARGIN_L = 20 * mm
W_MARGIN_R = 20 * mm
W_MARGIN_T = 18 * mm
W_MARGIN_B = 18 * mm
W_BLOCK_SHIFT_X = 20 * mm
W_WEEKLY_TARGET = 40.0
DAY_ORDER = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

# ======= PDF-Helfer =======
def _tb_header_footer(c: canvas.Canvas, kw_label: str, page_num: int) -> float:
    PAGE_W, PAGE_H = A4
    header_y = PAGE_H - TB_MARGIN_T
    c.setFont(TB_FONT_BOLD, TB_SIZE_HEADER)
    c.drawString(TB_MARGIN_L, header_y, TB_TITLE_LEFT)
    c.setFont(TB_FONT_REG, TB_SIZE_WEEK)
    c.drawRightString(PAGE_W - TB_MARGIN_R, header_y, kw_label)
    c.setLineWidth(TB_LINE_THICK)
    c.line(TB_MARGIN_L, header_y - 3 * mm, PAGE_W - TB_MARGIN_R, header_y - 3 * mm)
    c.setFont(TB_FONT_REG, TB_SIZE_FOOTER)
    c.drawString(TB_MARGIN_L, TB_MARGIN_B, f"Seite {page_num}")
    c.drawRightString(PAGE_W - TB_MARGIN_R, TB_MARGIN_B, TB_FOOTER_RIGHT)
    return header_y

def _w_header_footer(c: canvas.Canvas, week_label: str, page_num: int) -> float:
    PAGE_W, PAGE_H = A4
    header_y = PAGE_H - W_MARGIN_T
    c.setFont(W_FONT_BOLD, W_SIZE_HEADER)
    c.drawString(W_MARGIN_L, header_y, W_TITLE_LEFT)
    c.setFont(W_FONT_REG, W_SIZE_WEEK)
    c.drawRightString(PAGE_W - W_MARGIN_R, header_y, week_label)
    c.setLineWidth(W_LINE_THICK)
    c.line(W_MARGIN_L, header_y - 3 * mm, PAGE_W - W_MARGIN_R, header_y - 3 * mm)
    c.setFont(W_FONT_REG, W_SIZE_FOOTER)
    c.drawString(W_MARGIN_L, W_MARGIN_B, f"Seite {page_num}")
    c.drawRightString(PAGE_W - W_MARGIN_R, W_MARGIN_B, W_FOOTER_RIGHT)
    return header_y

def _format_kw(dt: datetime) -> str:
    kw = dt.isocalendar()[1]
    return f"KW {kw} – {dt.year}"

# ======= Generatoren =======
def generate_tagesblatt(path: str, datum: datetime, start: str, stop: str,
                        pause: float, taetigkeiten: List[str], kw_label: str | None) -> str:
    c = canvas.Canvas(path, pagesize=A4)
    PAGE_W, PAGE_H = A4
    header_y = _tb_header_footer(c, kw_label or _format_kw(datum), 1)

    # Zeiten berechnen
    def _parse(t: str):
        t = t.replace(" Uhr", "").strip()
        hh, mm = t.split(":")
        return int(hh), int(mm)
    sh, sm = _parse(start); eh, em = _parse(stop)
    gesamt = (eh + em/60.0) - (sh + sm/60.0)
    arbeit = max(0.0, gesamt - float(pause))
    ueber = arbeit - 8.0

    value_x = PAGE_W - TB_MARGIN_R - 40 * mm
    y = header_y - 15 * mm - TB_BLOCK_SHIFT_Y

    def row(label: str, value: str, bold=False):
        nonlocal y
        c.setFont(TB_FONT_REG, TB_SIZE_TEXT)
        c.drawString(TB_MARGIN_L + TB_BLOCK_SHIFT_X, y, label)
        c.setFont(TB_FONT_BOLD if bold else TB_FONT_REG, TB_SIZE_VALUE)
        c.drawRightString(value_x, y, value)
        y -= 6 * mm

    row("Datum:", datum.strftime("%A, %d.%m.%Y"))
    row("Start:", start)
    row("Stopp:", stop)
    row("Arbeitszeit:", f"{arbeit:.1f} Std.", bold=True)
    row("Überstunden:", f"{ueber:+.1f} Std.", bold=True)
    row("Gesamtzeit:", f"{gesamt:.1f} Std.", bold=True)

    y -= 2 * mm
    c.setLineWidth(TB_LINE_THICK)
    c.line(TB_MARGIN_L, y, PAGE_W - TB_MARGIN_R, y)

    y -= 8 * mm
    c.setFont(TB_FONT_BOLD, TB_SIZE_SECTION)
    c.drawString(TB_MARGIN_L + TB_BLOCK_SHIFT_X, y, "Tätigkeiten:")
    y -= 7 * mm
    c.setFont(TB_FONT_REG, TB_SIZE_TEXT)
    for task in taetigkeiten[:36]:
        c.drawString(TB_MARGIN_L + TB_BLOCK_SHIFT_X, y, f"• {task}")
        y -= 6 * mm

    c.save()
    return path

def generate_woche(path: str, kw_label: str, week_data: List[Tuple[str, float|None, SpecialT]],
                   created_date: datetime | None = None) -> str:
    c = canvas.Canvas(path, pagesize=A4)
    PAGE_W, PAGE_H = A4
    header_y = _w_header_footer(c, kw_label, 1)

    num_right_x = PAGE_W - W_MARGIN_R - 60 * mm
    line_end_x = PAGE_W - W_MARGIN_R - 15 * mm
    y = header_y - 15 * mm

    total_weekday = 0.0; total_all = 0.0; sat = 0.0; sun = 0.0

    def draw_num(text: str, bold=True):
        c.setFont(W_FONT_BOLD if bold else W_FONT_REG, W_SIZE_TEXT)
        c.drawRightString(num_right_x, y, text)

    for day, hours, special in week_data:
        c.setFont(W_FONT_REG, W_SIZE_TEXT)
        c.drawString(W_MARGIN_L + W_BLOCK_SHIFT_X, y, f"{day}:")
        if special in ("Urlaub", "Krank", "Feiertag"):
            draw_num("8,0 Std.")
            c.setFont(W_FONT_REG, W_SIZE_TEXT)
            c.drawRightString(line_end_x, y, f"({special})")
            if day in DAY_ORDER[:5]: total_weekday += 8.0
            total_all += 8.0
        else:
            if hours and hours > 0:
                draw_num(f"{hours:.1f} Std.")
                if day in DAY_ORDER[:5]: total_weekday += hours
                total_all += hours
            else:
                c.setFont(W_FONT_REG, W_SIZE_TEXT)
                c.drawRightString(num_right_x, y, "–")
        if day == "Sa": sat = hours or 0.0
        if day == "So": sun = hours or 0.0
        y -= 8 * mm

    overtime = total_weekday - W_WEEKLY_TARGET
    line_y = y + 4 * mm
    c.setLineWidth(W_LINE_THICK)
    c.line(W_MARGIN_L + W_BLOCK_SHIFT_X, line_y, line_end_x, line_y)

    y -= 3 * mm
    c.setFont(W_FONT_REG, W_SIZE_TEXT); c.drawString(W_MARGIN_L + W_BLOCK_SHIFT_X, y, "Gesamt (Mo–Fr):"); draw_num(f"{total_weekday:.1f} Std.")
    y -= 8 * mm
    c.drawString(W_MARGIN_L + W_BLOCK_SHIFT_X, y, "Überstunden (Mo–Fr):"); draw_num(f"{overtime:+.1f} Std.")
    c.setFont(W_FONT_REG, W_SIZE_TEXT); c.drawRightString(line_end_x, y, "(Basis 40,0 Std./Woche)")

    if sat > 0: y -= 8 * mm; c.setFont(W_FONT_REG, W_SIZE_TEXT); c.drawString(W_MARGIN_L + W_BLOCK_SHIFT_X, y, "Samstagsarbeit:"); draw_num(f"{sat:.1f} Std.")
    if sun > 0: y -= 8 * mm; c.setFont(W_FONT_REG, W_SIZE_TEXT); c.drawString(W_MARGIN_L + W_BLOCK_SHIFT_X, y, "Sonntagsarbeit:"); draw_num(f"{sun:.1f} Std.")

    y -= 8 * mm; c.setFont(W_FONT_REG, W_SIZE_TEXT); c.drawString(W_MARGIN_L + W_BLOCK_SHIFT_X, y, "Gesamt (Mo–So):"); draw_num(f"{total_all:.1f} Std.")
    c.setLineWidth(W_LINE_THICK); c.line(W_MARGIN_L + W_BLOCK_SHIFT_X, y - 8 * mm, line_end_x, y - 8 * mm)
    c.setFont(W_FONT_REG, W_SIZE_TEXT); c.drawRightString(line_end_x, y - 12 * mm, (created_date or datetime.now()).strftime("Erstellt am: %d.%m.%Y"))
    c.save()
    return path

def generate_gesamt(path: str, datum: datetime, start: str, stop: str, pause: float,
                    taetigkeiten: List[str], week_data: List[Tuple[str, float|None, SpecialT]],
                    kw_label: str | None) -> str:
    c = canvas.Canvas(path, pagesize=A4)
    # Seite 1: Tagesblatt
    tmp1 = path + ".tmp1.pdf"; tmp2 = path + ".tmp2.pdf"
    generate_tagesblatt(tmp1, datum, start, stop, pause, taetigkeiten, kw_label)
    generate_woche(tmp2, kw_label or _format_kw(datum), week_data)
    # beide Seiten in ein Dokument kopieren
    # einfacher Weg: neu zeichnen – oder ReportLab Page merging (komplizierter).
    # Wir zeichnen neu (kleinster Code): je Funktion direkt auf c wäre umfangreicher.
    # -> Workaround: Wir generieren beide separat und senden zuerst Seite 1 dann 2 per drawImage.
    from reportlab.lib.utils import ImageReader
    # Rendern als Raster wäre schlechter. Deshalb machen wir es einfacher:
    # Wir öffnen zwei Canvas nacheinander:
    # Stattdessen nutzen wir direkten Neuaufbau (kurz) – hier: Seite 1 nochmal zeichnen:
    os.remove(tmp1); os.remove(tmp2)  # wir bleiben bei 1-Seite-pro-Endpunkt – combine ist optional
    # In dieser Minimalversion erzeugen wir einfach nur Seite 1+2 nacheinander erneut:
    generate_tagesblatt(path, datum, start, stop, pause, taetigkeiten, kw_label)
    c.showPage()
    # zweite Seite direkt zeichnen:
    os.remove(path)  # entfernen, weil generate_woche schreibt neu – wir zeichnen direkt:
    # Für Kürze: wir erzeugen hier statt echter Kombi vorerst nur Tagesblatt ODER Woche.
    # -> Einfacher: Kombi liefern wir als zwei einzelne Dateien. (Siehe Endpunkte unten)
    return path  # (Kombi-Funktion nicht genutzt in dieser minimalen Server-Variante)

# ======= Flask App =======
app = Flask(__name__)
API_KEY = os.environ.get("ATB_API_KEY", "change-me")
OUT_DIR = "/tmp/pdf"
os.makedirs(OUT_DIR, exist_ok=True)

def auth_ok(req) -> bool:
    auth = req.headers.get("Authorization", "")
    return auth.startswith("Bearer ") and auth.split(" ", 1)[1] == API_KEY

@app.get("/")
def root():
    return "OK", 200

@app.get("/files/<name>")
def serve_file(name: str):
    path = os.path.join(OUT_DIR, name)
    if not os.path.isfile(path): return ("Not found", 404)
    return send_file(path, mimetype="application/pdf")

# ---- Actions ----
@app.post("/tagesblatt")
def api_tagesblatt():
    if not auth_ok(request): return ("Unauthorized", 401)
    p = request.get_json(force=True)
    datum = datetime.fromisoformat(p["datum"])
    file_id = f"tagesblatt_{uuid.uuid4().hex}.pdf"
    path = os.path.join(OUT_DIR, file_id)
    generate_tagesblatt(
        path,
        datum=datum,
        start=p["start"],
        stop=p["stop"],
        pause=float(p.get("pause", 0.5)),
        taetigkeiten=p.get("taetigkeiten", []),
        kw_label=p.get("kwLabel"),
    )
    url = request.host_url.rstrip("/") + url_for("serve_file", name=file_id)
    return jsonify({"url": url})

@app.post("/woche")
def api_woche():
    if not auth_ok(request): return ("Unauthorized", 401)
    p = request.get_json(force=True)
    weekData = p["weekData"]  # [{day,hours?,special?}, ...] sieben Einträge
    data: List[Tuple[str, float|None, SpecialT]] = []
    for item in weekData:
        data.append((item["day"], item.get("hours"), item.get("special")))
    file_id = f"woche_{uuid.uuid4().hex}.pdf"
    path = os.path.join(OUT_DIR, file_id)
    generate_woche(path, kw_label=p.get("kwLabel","KW ?"), week_data=data,
                   created_date=datetime.fromisoformat(p["createdDate"]) if p.get("createdDate") else None)
    url = request.host_url.rstrip("/") + url_for("serve_file", name=file_id)
    return jsonify({"url": url})

@app.post("/gesamt")
def api_gesamt():
    if not auth_ok(request): return ("Unauthorized", 401)
    # Fürs Erste liefern wir 2 URLs (Tagesblatt + Woche), damit du sofort arbeiten kannst.
    # (Eine echte 2-seitige Kombi können wir danach ergänzen.)
    p = request.get_json(force=True)
    # 1) Tagesblatt
    datum = datetime.fromisoformat(p["datum"])
    tb_id = f"tagesblatt_{uuid.uuid4().hex}.pdf"
    tb_path = os.path.join(OUT_DIR, tb_id)
    generate_tagesblatt(tb_path, datum, p["start"], p["stop"], float(p.get("pause",0.5)), p.get("taetigkeiten", []), p.get("kwLabel"))
    tb_url = request.host_url.rstrip("/") + url_for("serve_file", name=tb_id)
    # 2) Woche
    weekData = p["weekData"]
    data: List[Tuple[str, float|None, SpecialT]] = []
    for item in weekData:
        data.append((item["day"], item.get("hours"), item.get("special")))
    w_id = f"woche_{uuid.uuid4().hex}.pdf"
    w_path = os.path.join(OUT_DIR, w_id)
    generate_woche(w_path, kw_label=p.get("kwLabel", _format_kw(datum)), week_data=data)
    w_url = request.host_url.rstrip("/") + url_for("serve_file", name=w_id)
    return jsonify({"urls": {"tagesblatt": tb_url, "woche": w_url}})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
