# ===============================================
# Datei: tagesblatt_standard.py
# Standardlayout: Tagesblatt v9 (inkl. Überstunden-Zeile, Werte rechtsbündig, "Tätigkeiten:" fett)
# ===============================================
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from datetime import datetime

# ---------- Konstante Layout-Parameter (Tagesblatt) ----------
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
TB_BLOCK_SHIFT_X = 20 * mm   # Block 15 mm rechts + optische Reserve
TB_BLOCK_SHIFT_Y = 3 * mm    # Block 3 mm nach unten


def _tb_header_footer(c: canvas.Canvas, kw_label: str, page_num: int = 1):
    PAGE_W, PAGE_H = A4
    HEADER_Y = PAGE_H - TB_MARGIN_T
    # Header
    c.setFont(TB_FONT_BOLD, TB_SIZE_HEADER)
    c.drawString(TB_MARGIN_L, HEADER_Y, TB_TITLE_LEFT)
    c.setFont(TB_FONT_REG, TB_SIZE_WEEK)
    c.drawRightString(PAGE_W - TB_MARGIN_R, HEADER_Y, kw_label)
    c.setLineWidth(TB_LINE_THICK)
    c.line(TB_MARGIN_L, HEADER_Y - 3 * mm, PAGE_W - TB_MARGIN_R, HEADER_Y - 3 * mm)
    # Footer
    c.setFont(TB_FONT_REG, TB_SIZE_FOOTER)
    c.drawString(TB_MARGIN_L, TB_MARGIN_B, f"Seite {page_num}")
    c.drawRightString(PAGE_W - TB_MARGIN_R, TB_MARGIN_B, TB_FOOTER_RIGHT)
    return HEADER_Y


def generate_tagesblatt(
    output_path: str,
    datum_str: str,
    kw_str: str,
    start_str: str,
    stop_str: str,
    pause_std: float = 0.5,
    taetigkeiten: list[str] | None = None,
) -> str:
    """
    Erzeugt ein Tagesblatt im Standard v9.
    - Werte rechtsbündig in fixer Spalte (Dezimalausrichtung)
    - Überstunden-Zeile unter Arbeitszeit (Arbeitszeit - 8,0 Std.)
    - "Tätigkeiten:" als fette Abschnittsüberschrift
    """
    taetigkeiten = taetigkeiten or []

    # Zeiten berechnen
    # Hinweis: start/stop werden als Strings erwartet; Arbeits-/Gesamtzeit werden direkt übergeben oder hier berechnet?
    # Wir rechnen hier exemplarisch nicht aus Uhrzeiten, sondern erwarten, dass der Nutzer die tatsächlichen Zeiten
    # durch Start/Stop vorgibt und die Pausen-Standardregel gilt (0,5 Std.), sodass Arbeitszeit = (Stop-Start)-Pause.
    # Für exakte Berechnung aus Strings müsste man Parsing ergänzen.

    arbeitszeit_h = None
    gesamtzeit_h = None
    # Optional: einfache Parsing-Hilfe ("HH:MM Uhr") – robust genug für 08:00 / 17:30
    try:
        def _parse(t: str):
            t = t.replace(" Uhr", "").strip()
            hh, mm = t.split(":")
            return int(hh), int(mm)
        sh, sm = _parse(start_str)
        eh, em = _parse(stop_str)
        gesamtzeit_h = (eh + em/60) - (sh + sm/60)
        arbeitszeit_h = max(0.0, gesamtzeit_h - float(pause_std))
    except Exception:
        # Fallback: keine Berechnung – in dem Fall muss der Aufrufer Texte liefern
        pass

    arbeitszeit_txt = f"{arbeitszeit_h:.1f} Std." if arbeitszeit_h is not None else ""
    gesamtzeit_txt = f"{gesamtzeit_h:.1f} Std." if gesamtzeit_h is not None else ""
    ueberstunden_h = (arbeitszeit_h - 8.0) if arbeitszeit_h is not None else 0.0
    ueberstunden_txt = f"{ueberstunden_h:+.1f} Std."

    # Canvas
    c = canvas.Canvas(output_path, pagesize=A4)
    header_y = _tb_header_footer(c, kw_str, 1)

    PAGE_W, PAGE_H = A4
    VALUE_X = PAGE_W - TB_MARGIN_R - 40 * mm  # feste Spalte rechtsbündig

    # Block
    y = header_y - 15 * mm - TB_BLOCK_SHIFT_Y

    def row(label: str, value: str, bold=False):
        nonlocal y
        c.setFont(TB_FONT_REG, TB_SIZE_TEXT)
        c.drawString(TB_MARGIN_L + TB_BLOCK_SHIFT_X, y, label)
        c.setFont(TB_FONT_BOLD if bold else TB_FONT_REG, TB_SIZE_VALUE)
        c.drawRightString(VALUE_X, y, value)
        y -= 6 * mm

    row("Datum:", datum_str)
    row("Start:", start_str)
    row("Stopp:", stop_str)
    row("Arbeitszeit:", arbeitszeit_txt, bold=True)
    row("Überstunden:", ueberstunden_txt, bold=True)
    row("Gesamtzeit:", gesamtzeit_txt, bold=True)

    # Linie + Abschnittsüberschrift
    y -= 2 * mm
    c.setLineWidth(TB_LINE_THICK)
    c.line(TB_MARGIN_L, y, PAGE_W - TB_MARGIN_R, y)

    y -= 8 * mm
    c.setFont(TB_FONT_BOLD, TB_SIZE_SECTION)
    c.drawString(TB_MARGIN_L + TB_BLOCK_SHIFT_X, y, "Tätigkeiten:")

    y -= 7 * mm
    c.setFont(TB_FONT_REG, TB_SIZE_TEXT)
    for task in taetigkeiten:
        c.drawString(TB_MARGIN_L + TB_BLOCK_SHIFT_X, y, f"• {task}")
        y -= 6 * mm

    c.save()
    return output_path


# ===============================================
# Datei: wochenuebersicht_standard.py
# Standardlayout: Wochenübersicht v22 (Dezimalausrichtung, Linien, Datum, Feiertag-/WE-Logik)
# ===============================================
from typing import Literal

# ---------- Konstante Layout-Parameter (Wochenübersicht) ----------
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
W_WEEKLY_TARGET = 40.0  # nur Mo–Fr

DAY_ORDER = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
SpecialT = Literal["Urlaub", "Krank", "Feiertag", None]


def _w_header_footer(c: canvas.Canvas, week_label: str, page_num: int = 1):
    PAGE_W, PAGE_H = A4
    HEADER_Y = PAGE_H - W_MARGIN_T
    c.setFont(W_FONT_BOLD, W_SIZE_HEADER)
    c.drawString(W_MARGIN_L, HEADER_Y, W_TITLE_LEFT)
    c.setFont(W_FONT_REG, W_SIZE_WEEK)
    c.drawRightString(PAGE_W - W_MARGIN_R, HEADER_Y, week_label)
    c.setLineWidth(W_LINE_THICK)
    c.line(W_MARGIN_L, HEADER_Y - 3 * mm, PAGE_W - W_MARGIN_R, HEADER_Y - 3 * mm)
    c.setFont(W_FONT_REG, W_SIZE_FOOTER)
    c.drawString(W_MARGIN_L, W_MARGIN_B, f"Seite {page_num}")
    c.drawRightString(PAGE_W - W_MARGIN_R, W_MARGIN_B, W_FOOTER_RIGHT)
    return HEADER_Y


def generate_wochenuebersicht(
    output_path: str,
    kw_str: str,
    # Eintrag pro Tag: (TagKurzel, StundenOderNone, Spezialtyp)
    week_data: list[tuple[str, float | None, SpecialT]],
    created_date: datetime | None = None,
) -> str:
    """
    Erzeugt Wochenübersicht im Standard v22 mit folgenden Regeln:
    - Überstundenberechnung nur Mo–Fr (Basis 40,0 Std.)
    - Sa/So-Arbeit separat (nur ausgewiesen, nicht in Überstunden)
    - Urlaub/Krank/Feiertag: je 8,0 Std. Sollzeit mit Klammer-Hinweis
    - Feiertag mit Arbeit: zusätzlich unten gesammelt als "Feiertagsarbeit (XX+YY+ZZ): SUMME"
    - Dezimalausrichtung der Zahlen (rechtsbündige Spalte)
    - Linie nach Kopf; zweite Linie zwischen So: und Gesamt:; Abschlusslinie gleich lang; Datum am Abschluss rechts
    """
    PAGE_W, PAGE_H = A4
    c = canvas.Canvas(output_path, pagesize=A4)
    header_y = _w_header_footer(c, kw_str, 1)

    NUM_RIGHT_X = PAGE_W - W_MARGIN_R - 60 * mm  # Spalte für Zahlen (rechtsbündig)
    LINE_END_X = PAGE_W - W_MARGIN_R - 15 * mm   # Ende zweite/Abschlusslinie + Basis-Text + Datum

    y = header_y - 15 * mm
    total_weekday_hours = 0.0
    sat_hours = 0.0
    sun_hours = 0.0
    total_all_hours = 0.0
    feiertag_tage: list[str] = []
    feiertag_sum = 0.0

    def draw_num(text: str, bold=True):
        c.setFont(W_FONT_BOLD if bold else W_FONT_REG, W_SIZE_TEXT)
        c.drawRightString(NUM_RIGHT_X, y, text)

    # Tageszeilen
    for day, hours, special in week_data:
        c.setFont(W_FONT_REG, W_SIZE_TEXT)
        c.drawString(W_MARGIN_L + W_BLOCK_SHIFT_X, y, f"{day}:")

        if special == "Urlaub":
            draw_num("8,0 Std.")
            c.setFont(W_FONT_REG, W_SIZE_TEXT)
            c.drawRightString(LINE_END_X, y, "(Urlaub)")
            if day in DAY_ORDER[:5]:
                total_weekday_hours += 8.0
            total_all_hours += 8.0
        elif special == "Krank":
            draw_num("8,0 Std.")
            c.setFont(W_FONT_REG, W_SIZE_TEXT)
            c.drawRightString(LINE_END_X, y, "(Krank)")
            if day in DAY_ORDER[:5]:
                total_weekday_hours += 8.0
            total_all_hours += 8.0
        elif special == "Feiertag":
            draw_num("8,0 Std.")
            c.setFont(W_FONT_REG, W_SIZE_TEXT)
            c.drawRightString(LINE_END_X, y, "(Feiertag)")
            if day in DAY_ORDER[:5]:
                total_weekday_hours += 8.0
            total_all_hours += 8.0
            # tatsächliche Arbeit an diesem Feiertag wird in hours übergeben -> unten gesammelt ausweisen
            if hours is not None and hours > 0:
                feiertag_tage.append(day)
                feiertag_sum += hours
        else:
            # normaler Arbeitstag oder frei
            if hours and hours > 0:
                draw_num(f"{hours:.1f} Std.")
                if day in DAY_ORDER[:5]:
                    total_weekday_hours += hours
                total_all_hours += hours
            else:
                c.setFont(W_FONT_REG, W_SIZE_TEXT)
                c.drawRightString(NUM_RIGHT_X, y, "–")
        
        if day == "Sa":
            sat_hours = hours or 0.0
        elif day == "So":
            sun_hours = hours or 0.0

        y -= 8.0 * mm

    overtime = total_weekday_hours - W_WEEKLY_TARGET

    # Zweite Linie zwischen So: und Gesamt:
    line_y = y + 4 * mm
    c.setLineWidth(W_LINE_THICK)
    c.line(W_MARGIN_L + W_BLOCK_SHIFT_X, line_y, LINE_END_X, line_y)

    # Summen
    y -= 3 * mm
    c.setFont(W_FONT_REG, W_SIZE_TEXT)
    c.drawString(W_MARGIN_L + W_BLOCK_SHIFT_X, y, "Gesamt (Mo–Fr):")
    draw_num(f"{total_weekday_hours:.1f} Std.")

    y -= 8.0 * mm
    c.setFont(W_FONT_REG, W_SIZE_TEXT)
    c.drawString(W_MARGIN_L + W_BLOCK_SHIFT_X, y, "Überstunden (Mo–Fr):")
    draw_num(f"{overtime:+.1f} Std.")
    c.setFont(W_FONT_REG, W_SIZE_TEXT)
    c.drawRightString(LINE_END_X, y, f"(Basis {W_WEEKLY_TARGET:.1f} Std./Woche)")

    # Wochenendarbeit separat
    if sat_hours > 0:
        y -= 8.0 * mm
        c.setFont(W_FONT_REG, W_SIZE_TEXT)
        c.drawString(W_MARGIN_L + W_BLOCK_SHIFT_X, y, "Samstagsarbeit:")
        draw_num(f"{sat_hours:.1f} Std.")
    if sun_hours > 0:
        y -= 8.0 * mm
        c.setFont(W_FONT_REG, W_SIZE_TEXT)
        c.drawString(W_MARGIN_L + W_BLOCK_SHIFT_X, y, "Sonntagsarbeit:")
        draw_num(f"{sun_hours:.1f} Std.")

    # Feiertagsarbeit gesammelt
    if feiertag_tage:
        tage_str = "+".join(feiertag_tage)
        y -= 8.0 * mm
        c.setFont(W_FONT_REG, W_SIZE_TEXT)
        c.drawString(W_MARGIN_L + W_BLOCK_SHIFT_X, y, f"Feiertagsarbeit ({tage_str}):")
        draw_num(f"{feiertag_sum:.1f} Std.")

    # Gesamt (Mo–So)
    y -= 8.0 * mm
    c.setFont(W_FONT_REG, W_SIZE_TEXT)
    c.drawString(W_MARGIN_L + W_BLOCK_SHIFT_X, y, "Gesamt (Mo–So):")
    draw_num(f"{total_all_hours:.1f} Std.")

    # Abschlusslinie + Datum
    c.setLineWidth(W_LINE_THICK)
    c.line(W_MARGIN_L + W_BLOCK_SHIFT_X, y - 8 * mm, LINE_END_X, y - 8 * mm)
    c.setFont(W_FONT_REG, W_SIZE_TEXT)
    created_date = created_date or datetime.now()
    c.drawRightString(LINE_END_X, y - 12 * mm, created_date.strftime("Erstellt am: %d.%m.%Y"))

    c.save()
    return output_path


# =========================
# Beispielnutzung (optional)
# =========================
if __name__ == "__main__":
    # Demo Tagesblatt
    generate_tagesblatt(
        output_path="/mnt/data/_demo_tagesblatt.pdf",
        datum_str="Samstag, 30.08.2025",
        kw_str="KW 35 – 2025",
        start_str="08:00 Uhr",
        stop_str="17:30 Uhr",
        pause_std=0.5,
        taetigkeiten=["Montageübersicht Kran 1", "Montageübersicht Kran 2"],
    )

    # Demo Wochenübersicht
    week_demo = [
        ("Mo", None, "Urlaub"),
        ("Di", None, "Krank"),
        ("Mi", 8.0, "Feiertag"),    # Feiertag mit 8 Std. Arbeit
        ("Do", 8.0, "Feiertag"),    # Feiertag mit 8 Std. Arbeit
        ("Fr", 9.0, None),
        ("Sa", 4.0, None),
        ("So", 0.0, None),
    ]
    generate_wochenuebersicht(
        output_path="/mnt/data/_demo_wochenuebersicht.pdf",
        kw_str="KW 38 – 2025",
        week_data=week_demo,
    )
