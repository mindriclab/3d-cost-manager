"""3D Cost Manager – Kostenrechner für 3D-Drucke (mindric lab)."""

import json
import os
import sys
from datetime import datetime
from tkinter import filedialog, messagebox

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import Circle

import costcalc
import pdfgen
from texts import TEXTS

APP_VERSION = "1.1"

COLOR_PRIMARY = "#2563eb"
COLOR_SECONDARY = "#8b5cf6"
COLOR_SUCCESS = "#10b981"
COLOR_WARN = "#f59e0b"
COLOR_DANGER = "#ef4444"
COLOR_BG_CARD = "#2b2b2b"
COLOR_TEXT_DIM = "#a0a0a0"
FONT = "Segoe UI"

CHART_PARTS = [
    ("material", "chart_material", "#2563eb"),
    ("machine", "chart_machine", "#8b5cf6"),
    ("energy", "chart_energy", "#f59e0b"),
    ("tooling", "chart_tooling", "#64748b"),
    ("labor", "chart_labor", "#10b981"),
    ("finishing", "chart_finishing", "#ef4444"),
]

SETTINGS_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "mindric lab", "3D Cost Manager")
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")


def resource_path(name: str) -> str:
    """Pfad zu mitgelieferten Dateien, auch in der PyInstaller-EXE."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def load_settings() -> dict:
    try:
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_settings(data: dict) -> None:
    try:
        os.makedirs(SETTINGS_DIR, exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


class CostManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.settings = load_settings()
        self.lang = self.settings.get("lang", "de")
        self.currency = ctk.StringVar(value=self.settings.get("currency", "EUR"))
        self.small_business = ctk.BooleanVar(value=self.settings.get("smallBusiness", False))
        self.company = self.settings.get("company", {})

        self.title(f"3D Cost Manager {APP_VERSION} – mindric lab")
        self.geometry("1180x800")
        self.minsize(960, 620)
        try:
            self.iconbitmap(resource_path("icon.ico"))
        except Exception:
            pass

        self.vars = {}
        self.labels = {}
        self.results = {}
        last = self.settings.get("values", {})
        for key, default in costcalc.DEFAULTS.items():
            var = ctk.StringVar(value=self.fmt_input(last.get(key, default)))
            var.trace_add("write", self.calculate)
            self.vars[key] = var
        self.currency.trace_add("write", self.calculate)
        self.small_business.trace_add("write", self.calculate)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.create_header()
        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_scroll.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 8))
        self.main_scroll.grid_columnconfigure((0, 1), weight=1, uniform="col")
        self.create_left_panel()
        self.create_right_panel()
        self.create_footer()

        self.update_language()
        self.calculate()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------- Aufbau ----------

    def t(self, key: str) -> str:
        return TEXTS[self.lang][key]

    def fmt_input(self, value) -> str:
        """Zahl fürs Eingabefeld: ohne ".0", im Deutschen mit Komma."""
        s = f"{costcalc.parse_number(value):g}"
        return s.replace(".", ",") if self.lang == "de" else s

    def create_header(self):
        header = ctk.CTkFrame(self, fg_color=COLOR_PRIMARY, corner_radius=0, height=64)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        header.grid_propagate(False)
        self.title_label = ctk.CTkLabel(header, text="3D Cost Manager", font=(FONT, 22, "bold"), text_color="white")
        self.title_label.pack(side="left", padx=20)

        self.lang_btn = ctk.CTkButton(header, width=110, fg_color="transparent", border_width=2,
                                      border_color="white", command=self.toggle_language)
        self.lang_btn.pack(side="right", padx=(8, 20))
        ctk.CTkOptionMenu(header, values=list(costcalc.CURRENCIES), variable=self.currency, width=80).pack(side="right")
        self.labels["currency_label"] = ctk.CTkLabel(header, text="", text_color="white", font=(FONT, 12))
        self.labels["currency_label"].pack(side="right", padx=8)

    def create_group(self, parent, title_key, fields):
        frame = ctk.CTkFrame(parent, fg_color=COLOR_BG_CARD)
        frame.pack(fill="x", pady=(0, 12))
        title = ctk.CTkLabel(frame, text="", font=(FONT, 15, "bold"), text_color=COLOR_PRIMARY)
        title.pack(anchor="w", padx=12, pady=(8, 4))
        self.labels[title_key] = title
        for var_name, label_key in fields:
            row = ctk.CTkFrame(frame, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=2)
            lbl = ctk.CTkLabel(row, text="", font=(FONT, 12), text_color=COLOR_TEXT_DIM, anchor="w")
            lbl.pack(anchor="w")
            self.labels[label_key] = lbl
            ctk.CTkEntry(row, textvariable=self.vars[var_name], border_color="#3e3e3e").pack(fill="x")
        ctk.CTkFrame(frame, height=8, fg_color="transparent").pack()
        return frame

    def create_left_panel(self):
        left = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self.create_group(left, "job_params", [
            ("printTime", "print_time_label"),
            ("totalWeight", "total_weight_label"),
            ("quantity", "quantity_label"),
        ])
        self.create_group(left, "material_title", [("materialCost", "material_cost_label")])
        self.create_group(left, "support_title", [
            ("supportWeight", "support_weight_label"),
            ("supportCost", "support_cost_label"),
        ])
        self.create_group(left, "profit_title", [
            ("failureRate", "failure_rate_label"),
            ("profitMargin", "profit_margin_label"),
        ])
        tax = self.create_group(left, "tax_title", [("vatRate", "vat_label")])
        self.sb_check = ctk.CTkCheckBox(tax, text="", variable=self.small_business)
        self.sb_check.pack(anchor="w", padx=12, pady=(0, 10))

        buttons = ctk.CTkFrame(left, fg_color="transparent")
        buttons.pack(fill="x", pady=(4, 12))
        buttons.grid_columnconfigure((0, 1), weight=1)
        specs = [
            ("quote_text", lambda: self.open_pdf_dialog("quote"), COLOR_SUCCESS, 0, 0),
            ("calc_text", lambda: self.open_pdf_dialog("calc"), COLOR_PRIMARY, 0, 1),
            ("save_text", self.save_profile, "#3f3f46", 1, 0),
            ("load_text", self.load_profile, "#3f3f46", 1, 1),
            ("reset_text", self.reset_values, COLOR_DANGER, 2, 0),
        ]
        for key, cmd, color, r, c in specs:
            btn = ctk.CTkButton(buttons, text="", command=cmd, fg_color=color, height=34)
            btn.grid(row=r, column=c, sticky="ew", padx=3, pady=3)
            self.labels[key] = btn

    def create_right_panel(self):
        right = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        chart = ctk.CTkFrame(right, fg_color=COLOR_BG_CARD)
        chart.pack(fill="x", pady=(0, 12))
        self.fig = Figure(figsize=(5, 3.2), dpi=100, facecolor=COLOR_BG_CARD)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, pady=8)

        metrics = ctk.CTkFrame(right, fg_color="transparent")
        metrics.pack(fill="x", pady=(0, 12))
        metrics.grid_columnconfigure((0, 1, 2), weight=1, uniform="m")
        for i, (label_key, value_key, color) in enumerate([
            ("cost_per_hour_label", "metric_cph", COLOR_SECONDARY),
            ("cost_per_gram_label", "metric_cpg", COLOR_SECONDARY),
            ("price_per_piece_label", "metric_piece", COLOR_SUCCESS),
        ]):
            box = ctk.CTkFrame(metrics, fg_color=COLOR_BG_CARD)
            box.grid(row=0, column=i, sticky="ew", padx=3)
            lbl = ctk.CTkLabel(box, text="", font=(FONT, 11, "bold"), text_color=COLOR_TEXT_DIM)
            lbl.pack(pady=(6, 0))
            self.labels[label_key] = lbl
            val = ctk.CTkLabel(box, text="", font=(FONT, 17, "bold"), text_color=color)
            val.pack(pady=(0, 6))
            self.labels[value_key] = val

        self.create_group(right, "machine_title", [
            ("machineCost", "machine_cost_label"),
            ("powerWatt", "power_label"),
            ("energyPrice", "energy_price_label"),
            ("nozzleCost", "nozzle_cost_label"),
            ("nozzleLifespan", "nozzle_lifespan_label"),
        ])
        self.create_group(right, "labor_title", [
            ("laborCost", "labor_cost_label"),
            ("laborTime", "labor_time_label"),
        ])
        self.create_group(right, "finishing_title", [("finishingCost", "finishing_cost_label")])

    def create_footer(self):
        footer = ctk.CTkFrame(self, height=56, fg_color=COLOR_PRIMARY, corner_radius=0)
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_propagate(False)
        ctk.CTkLabel(footer, text="mindric lab · mindriclab.de", font=(FONT, 11), text_color="#dbeafe").pack(side="right", padx=20)
        box = ctk.CTkFrame(footer, fg_color="transparent")
        box.pack(side="left", fill="both", expand=True, padx=20)
        self.footer_values = {}
        for key in ("summary_base", "summary_markup", "summary_net", "summary_gross"):
            f = ctk.CTkFrame(box, fg_color="transparent")
            f.pack(side="left", expand=True)
            lbl = ctk.CTkLabel(f, text="", font=(FONT, 12, "bold"), text_color="white")
            lbl.pack(side="left", padx=(0, 6))
            self.labels[key] = lbl
            val = ctk.CTkLabel(f, text="", font=(FONT, 16, "bold"), text_color="white")
            val.pack(side="left")
            self.footer_values[key] = val

    # ---------- Rechnen und Anzeigen ----------

    def current_values(self) -> dict:
        return {k: v.get() for k, v in self.vars.items()}

    def money(self, value, decimals=2):
        return costcalc.fmt_money(value, self.currency.get(), self.lang, decimals)

    def calculate(self, *_):
        r = costcalc.calculate(self.current_values(), self.small_business.get())
        self.results = r
        self.labels["metric_cph"].configure(text=self.money(r["costPerHour"]))
        self.labels["metric_cpg"].configure(text=self.money(r["costPerGram"], 4))
        self.labels["metric_piece"].configure(text=self.money(r["grossPerPiece"]))
        self.footer_values["summary_base"].configure(text=self.money(r["base"]))
        self.footer_values["summary_markup"].configure(text=self.money(r["markup"]))
        self.footer_values["summary_net"].configure(text=self.money(r["net"]))
        self.footer_values["summary_gross"].configure(text=self.money(r["gross"]))
        self.update_chart()

    def update_chart(self):
        self.ax.clear()
        self.ax.set_facecolor(COLOR_BG_CARD)
        parts = [(self.t(lbl), self.results[key], col) for key, lbl, col in CHART_PARTS if self.results[key] > 0]
        if not parts:
            parts = [("", 1, "#444444")]
        labels, sizes, colors = zip(*parts)
        total = sum(sizes)
        # Kleine Anteile ohne Prozentzahl im Ring, sonst überlappen die Beschriftungen; Namen stehen in der Legende
        wedges, _texts, _auto = self.ax.pie(
            sizes, startangle=90, colors=colors, pctdistance=0.78,
            autopct=lambda p: f"{p:.0f}%" if p >= 6 else "",
            textprops=dict(color="white", fontsize=9))
        self.ax.add_artist(Circle((0, 0), 0.58, fc=COLOR_BG_CARD))
        self.ax.axis("equal")
        if labels[0]:
            legend = [f"{lab}  {s / total * 100:.0f}%" for lab, s in zip(labels, sizes)]
            self.ax.legend(wedges, legend, loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False,
                           labelcolor="white", fontsize=9)
        self.fig.subplots_adjust(left=0.02, right=0.62)
        self.canvas.draw_idle()

    def update_language(self):
        for key, widget in self.labels.items():
            if key in TEXTS[self.lang]:
                widget.configure(text=self.t(key))
        self.sb_check.configure(text=self.t("small_business_label"))
        self.lang_btn.configure(text=self.t("switch_lang"))

    def toggle_language(self):
        self.lang = "en" if self.lang == "de" else "de"
        for var in self.vars.values():
            var.set(self.fmt_input(var.get()))
        self.update_language()
        self.calculate()

    def reset_values(self):
        for key, default in costcalc.DEFAULTS.items():
            self.vars[key].set(self.fmt_input(default))

    # ---------- Dateien ----------

    def persist(self):
        self.settings.update({
            "lang": self.lang,
            "currency": self.currency.get(),
            "smallBusiness": self.small_business.get(),
            "company": self.company,
            "values": self.current_values(),
        })
        save_settings(self.settings)

    def on_close(self):
        self.persist()
        self.destroy()

    def save_profile(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not path:
            return
        data = dict(self.current_values(), currency=self.currency.get())
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        messagebox.showinfo(self.t("saved_title"), self.t("profile_saved"))

    def load_profile(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            for key, value in data.items():
                if key in self.vars:
                    self.vars[key].set(str(value))
            if data.get("currency") in costcalc.CURRENCIES:
                self.currency.set(data["currency"])
        except (OSError, ValueError) as e:
            messagebox.showerror(self.t("error_title"), self.t("load_error").format(err=e))

    # ---------- PDF ----------

    def open_pdf_dialog(self, kind: str):
        dialog = ctk.CTkToplevel(self)
        dialog.title(self.t("quote_dialog_title" if kind == "quote" else "calc_dialog_title"))
        dialog.geometry("560x600")
        dialog.transient(self)
        dialog.after(100, dialog.grab_set)
        content = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=16, pady=16)

        def row(label_key, value=""):
            r = ctk.CTkFrame(content, fg_color="transparent")
            r.pack(fill="x", pady=4)
            ctk.CTkLabel(r, text=self.t(label_key), width=170, anchor="w", font=(FONT, 12)).pack(side="left")
            var = ctk.StringVar(value=value)
            ctk.CTkEntry(r, textvariable=var).pack(side="left", fill="x", expand=True)
            return var

        ctk.CTkLabel(content, text=self.t("company_section"), font=(FONT, 14, "bold"),
                     text_color=COLOR_PRIMARY).pack(anchor="w", pady=(0, 6))
        comp = {key: row(f"company_{key}_label", self.company.get(key, ""))
                for key in ("name", "owner", "address", "contact", "tax")}

        ctk.CTkLabel(content, text=self.t("client_section"), font=(FONT, 14, "bold"),
                     text_color=COLOR_PRIMARY).pack(anchor="w", pady=(16, 6))
        cust = row("customer_name_label")
        proj = row("project_name_label")
        number = row("doc_number_label", f"A-{datetime.now():%Y%m%d-%H%M}")

        def generate():
            self.company = {k: v.get().strip() for k, v in comp.items()}
            self.persist()
            client = {"customer": cust.get().strip(), "project": proj.get().strip(), "number": number.get().strip()}
            prefix = ("Angebot" if self.lang == "de" else "Quote") if kind == "quote" else ("Kalkulation" if self.lang == "de" else "Calculation")
            path = filedialog.asksaveasfilename(
                parent=dialog,
                initialfile=f"{prefix}_{client['number'] or datetime.now().strftime('%Y%m%d')}.pdf".replace("/", "-"),
                defaultextension=".pdf",
                filetypes=[("PDF", "*.pdf")],
            )
            if not path:
                return
            build = pdfgen.build_quote if kind == "quote" else pdfgen.build_calculation
            try:
                build(path, self.results, self.company, client, self.lang, self.currency.get(), self.small_business.get())
                messagebox.showinfo("PDF", self.t("pdf_saved").format(path=path), parent=dialog)
                dialog.destroy()
            except Exception as e:  # z. B. Datei ist in einem PDF-Programm geöffnet
                messagebox.showerror(self.t("error_title"), self.t("pdf_error").format(err=e), parent=dialog)

        ctk.CTkButton(content, text=self.t("generate_btn"), fg_color=COLOR_SUCCESS if kind == "quote" else COLOR_PRIMARY,
                      height=38, command=generate).pack(fill="x", pady=20)


if __name__ == "__main__":
    CostManagerApp().mainloop()
