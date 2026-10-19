"""PDF-Erzeugung: Angebot (für Kunden) und Kalkulation (intern)."""

import logging
import os
from datetime import datetime, timedelta

from fpdf import FPDF

from costcalc import fmt_money, fmt_percent
from texts import TEXTS

# fontTools meldet beim Einbetten von Segoe UI harmlose Hinweise ("MERG NOT subset")
logging.getLogger("fontTools").setLevel(logging.ERROR)

BLUE = (37, 99, 235)
DARK = (40, 40, 40)
GREY = (110, 110, 110)
LIGHT = (240, 245, 255)

# Windows-Schriften mit Unicode (€, £, Umlaute); sonst Helvetica mit Ersatzzeichen
_FONT_DIR = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
_FONTS = {"": "segoeui.ttf", "B": "segoeuib.ttf"}


class _Doc(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(True, margin=18)
        self.unicode = all(os.path.exists(os.path.join(_FONT_DIR, f)) for f in _FONTS.values())
        if self.unicode:
            for style, file in _FONTS.items():
                self.add_font("ui", style, os.path.join(_FONT_DIR, file))
        self.family = "ui" if self.unicode else "helvetica"

    def font(self, style="", size=10, color=DARK):
        self.set_font(self.family, style, size)
        self.set_text_color(*color)

    def txt(self, s):
        s = str(s)
        return s if self.unicode else s.encode("latin-1", "replace").decode("latin-1")


def _header(pdf: _Doc, company: dict, title: str):
    pdf.add_page()
    pdf.font("B", 20, BLUE)
    pdf.cell(0, 10, pdf.txt(company.get("name") or ""), new_x="LMARGIN", new_y="NEXT")
    pdf.font("", 10, GREY)
    for key in ("owner", "address", "contact", "tax"):
        if company.get(key):
            pdf.cell(0, 5, pdf.txt(company[key]), new_x="LMARGIN", new_y="NEXT")
    y = pdf.get_y() + 3
    pdf.set_draw_color(*BLUE)
    pdf.set_line_width(0.6)
    pdf.line(10, y, 200, y)
    pdf.set_y(y + 8)
    pdf.font("B", 18, BLUE)
    pdf.cell(0, 10, pdf.txt(title), new_x="LMARGIN", new_y="NEXT")


def _meta(pdf: _Doc, t: dict, client: dict, valid_days: int | None):
    today = datetime.now()
    pdf.font("", 10)
    parts = [f"{t['pdf_no']} {client.get('number') or 'A-001'}", f"{t['pdf_date']} {today:%d.%m.%Y}"]
    if valid_days:
        parts.append(f"{t['pdf_valid']} {today + timedelta(days=valid_days):%d.%m.%Y}")
    pdf.cell(0, 6, pdf.txt("   ·   ".join(parts)), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    y = pdf.get_y()
    pdf.set_fill_color(*LIGHT)
    pdf.rect(10, y, 190, 16, "F")
    pdf.set_xy(13, y + 2.5)
    pdf.font("B", 10, BLUE)
    pdf.cell(28, 5.5, pdf.txt(t["pdf_customer"] + ":"))
    pdf.font("", 10)
    pdf.cell(0, 5.5, pdf.txt(client.get("customer") or "–"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(13)
    pdf.font("B", 10, BLUE)
    pdf.cell(28, 5.5, pdf.txt(t["pdf_project"] + ":"))
    pdf.font("", 10)
    pdf.cell(0, 5.5, pdf.txt(client.get("project") or t["pdf_default_item"]), new_x="LMARGIN", new_y="NEXT")
    pdf.set_y(y + 22)


def _row(pdf: _Doc, cells, widths, aligns, style="", fill=None, color=DARK, h=7.5):
    pdf.font(style, 10, color)
    if fill:
        pdf.set_fill_color(*fill)
    for text, w, a in zip(cells, widths, aligns):
        pdf.cell(w, h, pdf.txt(text), border=1 if fill is None else 0, align=a, fill=bool(fill))
    pdf.ln(h)


def build_quote(path: str, r: dict, company: dict, client: dict, lang: str, currency: str, small_business: bool):
    t = TEXTS[lang]
    money = lambda v: fmt_money(v, currency, lang)
    pdf = _Doc()
    _header(pdf, company, t["pdf_quote"])
    _meta(pdf, t, client, valid_days=30)

    widths, aligns = (95, 25, 35, 35), ("L", "R", "R", "R")
    pdf.set_draw_color(220, 220, 220)
    pdf.set_line_width(0.2)
    _row(pdf, (t["pdf_position"], t["pdf_qty"], t["pdf_unit_price"], t["pdf_total"]), widths, aligns, "B", BLUE, (255, 255, 255), 8)
    item = client.get("project") or t["pdf_default_item"]
    _row(pdf, (item, str(r["quantity"]), money(r["netPerPiece"]), money(r["net"])), widths, aligns)

    pdf.ln(4)
    label_w, value_w = 155, 35
    def total_line(label, value, bold=False):
        pdf.font("B" if bold else "", 11 if bold else 10)
        pdf.cell(label_w, 7, pdf.txt(label), align="R")
        pdf.cell(value_w, 7, pdf.txt(value), align="R", new_x="LMARGIN", new_y="NEXT")
    total_line(t["pdf_net"], money(r["net"]))
    if not small_business:
        total_line(t["pdf_vat"].format(rate=fmt_percent(r["vatRate"], lang)), money(r["vat"]))
    y = pdf.get_y() + 1
    pdf.set_draw_color(*BLUE)
    pdf.line(120, y, 200, y)
    pdf.ln(2)
    total_line(t["pdf_gross"], money(r["gross"]), bold=True)

    pdf.ln(8)
    pdf.font("", 9, GREY)
    if small_business:
        pdf.multi_cell(0, 5, pdf.txt(t["pdf_small_business"]), new_x="LMARGIN", new_y="NEXT")
    pdf.multi_cell(0, 5, pdf.txt(t["pdf_quote_footer"]), new_x="LMARGIN", new_y="NEXT")
    pdf.output(path)


def build_calculation(path: str, r: dict, company: dict, client: dict, lang: str, currency: str, small_business: bool):
    t = TEXTS[lang]
    money = lambda v: fmt_money(v, currency, lang)
    pdf = _Doc()
    _header(pdf, company, t["pdf_calc"])
    pdf.font("", 9, GREY)
    pdf.cell(0, 5, pdf.txt(t["pdf_calc_note"]), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    _meta(pdf, t, client, valid_days=None)

    widths, aligns = (110, 45, 35), ("L", "R", "R")
    pdf.set_draw_color(220, 220, 220)
    pdf.set_line_width(0.2)
    _row(pdf, (t["pdf_breakdown"], t["pdf_amount"], t["pdf_share"]), widths, aligns, "B", BLUE, (255, 255, 255), 8)
    base = r["base"] if r["base"] > 0 else 1
    for key, label in (("material", "chart_material"), ("machine", "chart_machine"), ("energy", "chart_energy"),
                       ("tooling", "chart_tooling"), ("labor", "chart_labor"), ("finishing", "chart_finishing")):
        share = f"{r[key] / base * 100:.0f} %"
        _row(pdf, (t[label], money(r[key]), share), widths, aligns)
    _row(pdf, (t["pdf_base"], money(r["base"]), "100 %"), widths, aligns, "B")
    _row(pdf, (t["pdf_failure"].format(rate=fmt_percent(r["failureRate"], lang)), money(r["failure"]), ""), widths, aligns)
    _row(pdf, (t["pdf_profit"].format(rate=fmt_percent(r["profitMargin"], lang)), money(r["profit"]), ""), widths, aligns)
    _row(pdf, (t["pdf_net"], money(r["net"]), ""), widths, aligns, "B")
    if not small_business:
        _row(pdf, (t["pdf_vat"].format(rate=fmt_percent(r["vatRate"], lang)), money(r["vat"]), ""), widths, aligns)
    _row(pdf, (t["pdf_gross"], money(r["gross"]), ""), widths, aligns, "B", LIGHT)

    pdf.ln(6)
    pdf.font("B", 12, BLUE)
    pdf.cell(0, 8, pdf.txt(t["pdf_metrics"]), new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(220, 220, 220)
    _row(pdf, (f"{t['pdf_per_piece']} ({r['quantity']} ×)", f"{money(r['netPerPiece'])} / {money(r['grossPerPiece'])}", ""), widths, aligns)
    _row(pdf, (t["pdf_cost_per_hour"], money(r["costPerHour"]), ""), widths, aligns)
    _row(pdf, (t["pdf_cost_per_gram"], fmt_money(r["costPerGram"], currency, lang, 4), ""), widths, aligns)
    if small_business:
        pdf.ln(4)
        pdf.font("", 9, GREY)
        pdf.multi_cell(0, 5, pdf.txt(t["pdf_small_business"]), new_x="LMARGIN", new_y="NEXT")
    pdf.output(path)
