import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import json
from fpdf import FPDF
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
import os

# --- Configuration & Theme ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Colors
COLOR_PRIMARY = "#2563eb"
COLOR_SECONDARY = "#8b5cf6"
COLOR_SUCCESS = "#10b981"
COLOR_DANGER = "#ef4444" 
COLOR_BG_CARD = "#2b2b2b"
COLOR_TEXT = "#ffffff"
COLOR_TEXT_DIM = "#a0a0a0"

class CostManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("3D Kostenrechner Pro")
        self.geometry("1300x900")
        self.minsize(1200, 800)

        # Data Variables
        self.lang = "de"
        self.vars = {}
        self.labels = {} 
        
        # Speicher für Firmendaten
        self.company_info = {
            "name": ctk.StringVar(value="Ihre Firma"),
            "owner": ctk.StringVar(value="Ihr Name"),
            "address": ctk.StringVar(value="Musterstraße 1, 12345 Musterstadt"),
            "contact": ctk.StringVar(value="info@ihrefirma.de")
        }

        # Initialize Calculation Variables
        self.init_variables()
        
        # Layout Setup
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) 

        # 1. Header
        self.create_header()

        # 2. Main Scrollable Content
        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 80))
        self.main_scroll.grid_columnconfigure(0, weight=1)
        self.main_scroll.grid_columnconfigure(1, weight=1)

        # 3. Content Panels
        self.create_left_panel()
        self.create_right_panel()

        # 4. Footer (Sticky Cost Summary)
        self.create_footer()

        # Initial Calc & Translation
        self.update_language()
        self.calculate()

    def init_variables(self):
        # Default values - "numberParts" entfernt
        defaults = {
            "printTime": 5.0, "totalWeight": 50.0,
            "materialCost": 18.0, "supportWeight": 0.0, "supportCost": 12.0,
            "machineCost": 8.0, "nozzleCost": 5.0, "nozzleLifespan": 15.0,
            "laborCost": 20.0, "laborTime": 1.0, "finishingCost": 0.0,
            "failureRate": 5.0, "profitMargin": 25.0
        }
        
        for key, val in defaults.items():
            self.vars[key] = ctk.StringVar(value=str(val))
            self.vars[key].trace_add("write", self.calculate)

        # Results storage
        self.results = {
            "baseCost": 0.0, "markup": 0.0, "totalCost": 0.0,
            "materialCostValue": 0.0, "laborCostValue": 0.0, 
            "machineCostValue": 0.0, "toolingCostValue": 0.0, "finishingCost": 0.0,
            "failureRate": 0.0, "profitMargin": 0.0, "profitMarkupValue": 0.0, "failureMarkup": 0.0
        }

    # --- UI Construction ---

    def create_header(self):
        self.header_frame = ctk.CTkFrame(self, fg_color=COLOR_PRIMARY, corner_radius=0, height=70)
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        self.header_frame.grid_propagate(False)

        self.title_label = ctk.CTkLabel(self.header_frame, text="3D Kostenrechner Pro", 
                                      font=("Roboto", 24, "bold"), text_color="white")
        self.title_label.pack(side="left", padx=20, pady=20)

        self.lang_btn = ctk.CTkButton(self.header_frame, text="🇬🇧 English", width=100,
                                    fg_color="transparent", border_width=2, border_color="white",
                                    command=self.toggle_language)
        self.lang_btn.pack(side="right", padx=20, pady=20)

    def create_left_panel(self):
        self.left_frame = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Group: Job Parameters - "numberParts" entfernt
        self.create_group("job_params", [
            ("printTime", "print_time_label"),
            ("totalWeight", "total_weight_label")
        ])

        # Group: Material
        self.create_group("material_title", [
            ("materialCost", "material_cost_label")
        ])

        # Group: Support
        self.create_group("support_title", [
            ("supportWeight", "support_weight_label"),
            ("supportCost", "support_cost_label")
        ])

        # Group: Profit & Safety
        self.create_group("profit_title", [
            ("failureRate", "failure_rate_label"),
            ("profitMargin", "profit_margin_label")
        ])
        
        # Buttons Row
        self.btn_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.btn_frame.pack(fill="x", pady=20)
        
        # Save
        self.btn_save = ctk.CTkButton(self.btn_frame, command=self.save_profile, fg_color=COLOR_PRIMARY)
        self.btn_save.pack(side="left", expand=True, fill="x", padx=2)
        self.labels["save_text"] = self.btn_save

        # Load
        self.btn_load = ctk.CTkButton(self.btn_frame, command=self.load_profile, fg_color=COLOR_SECONDARY)
        self.btn_load.pack(side="left", expand=True, fill="x", padx=2)
        self.labels["load_text"] = self.btn_load

        # PDF
        self.btn_pdf = ctk.CTkButton(self.btn_frame, command=self.open_pdf_dialog, fg_color=COLOR_SUCCESS)
        self.btn_pdf.pack(side="left", expand=True, fill="x", padx=2)
        self.labels["pdf_text"] = self.btn_pdf

        # RESET BUTTON
        self.btn_reset = ctk.CTkButton(self.btn_frame, command=self.reset_values, fg_color=COLOR_DANGER)
        self.btn_reset.pack(side="left", expand=True, fill="x", padx=2)
        self.labels["reset_text"] = self.btn_reset

    def create_right_panel(self):
        self.right_frame = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        # Chart Area
        self.chart_frame = ctk.CTkFrame(self.right_frame, fg_color=COLOR_BG_CARD)
        self.chart_frame.pack(fill="x", pady=(0, 20))
        
        # Matplotlib setup
        self.fig = plt.Figure(figsize=(5, 3.5), dpi=100, facecolor=COLOR_BG_CARD)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(COLOR_BG_CARD)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, pady=10)

        # Group: Machine
        self.create_group("machine_title", [
            ("machineCost", "machine_cost_label"),
            ("nozzleCost", "nozzle_cost_label"),
            ("nozzleLifespan", "nozzle_lifespan_label")
        ], parent=self.right_frame)

        # Group: Labor
        self.create_group("labor_title", [
            ("laborCost", "labor_cost_label"),
            ("laborTime", "labor_time_label")
        ], parent=self.right_frame)
        
        # Group: Finishing
        self.create_group("finishing_title", [
            ("finishingCost", "finishing_cost_label")
        ], parent=self.right_frame)

        # Metrics Grid
        self.metrics_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.metrics_frame.pack(fill="x", pady=10)
        self.create_metric("cost_per_hour_label", "metric_cph")
        self.create_metric("cost_per_gram_label", "metric_cpg")
        self.create_metric("final_price_label", "metric_price", highlight=True)

    def create_group(self, title_key, inputs, parent=None):
        if parent is None: parent = self.left_frame
        
        frame = ctk.CTkFrame(parent, fg_color=COLOR_BG_CARD)
        frame.pack(fill="x", pady=(0, 15), ipadx=10, ipady=10)

        lbl_title = ctk.CTkLabel(frame, text="Title", font=("Roboto", 16, "bold"), text_color=COLOR_PRIMARY)
        lbl_title.pack(anchor="w", padx=10, pady=(5, 10))
        self.labels[title_key] = lbl_title

        for var_name, label_key in inputs:
            f = ctk.CTkFrame(frame, fg_color="transparent")
            f.pack(fill="x", padx=10, pady=2)
            
            lbl = ctk.CTkLabel(f, text="Label", font=("Roboto", 12, "bold"), text_color=COLOR_TEXT_DIM)
            lbl.pack(anchor="w")
            self.labels[label_key] = lbl
            
            entry = ctk.CTkEntry(f, textvariable=self.vars[var_name], border_color="#3e3e3e")
            entry.pack(fill="x")

    def create_metric(self, label_key, result_key, highlight=False):
        f = ctk.CTkFrame(self.metrics_frame, fg_color=COLOR_BG_CARD)
        f.pack(side="left", fill="x", expand=True, padx=2)
        
        lbl = ctk.CTkLabel(f, text="Metric", font=("Roboto", 11, "bold"), text_color=COLOR_TEXT_DIM)
        lbl.pack(pady=(5,0))
        self.labels[label_key] = lbl
        
        val = ctk.CTkLabel(f, text="€0.00", font=("Roboto", 18, "bold"), 
                           text_color=COLOR_SECONDARY if not highlight else COLOR_SUCCESS)
        val.pack(pady=(0,5))
        self.labels[result_key] = val

    def create_footer(self):
        self.footer = ctk.CTkFrame(self, height=60, fg_color=COLOR_PRIMARY, corner_radius=0)
        self.footer.grid(row=2, column=0, sticky="ew")
        self.footer.grid_propagate(False)
        
        # Copyright rechts
        ctk.CTkLabel(self.footer, text="(c) by mindric lab", font=("Roboto", 10), text_color="white").pack(side="right", padx=20)

        # Container für Summary links
        container = ctk.CTkFrame(self.footer, fg_color="transparent")
        container.pack(side="left", fill="both", expand=True, padx=40)
        
        # Layout for footer items - "summary_per_part" entfernt
        self.footer_items = {}
        keys = ["summary_base", "summary_markup", "summary_total"]
        
        for i, key in enumerate(keys):
            f = ctk.CTkFrame(container, fg_color="transparent")
            f.pack(side="left", fill="y", expand=True)
            
            lbl = ctk.CTkLabel(f, text="Label:", font=("Roboto", 12, "bold"), text_color="white")
            lbl.pack(side="left", padx=(0,5))
            self.labels[key] = lbl
            
            val = ctk.CTkLabel(f, text="€0.00", font=("Roboto", 16, "bold"), text_color="white")
            val.pack(side="left")
            self.footer_items[key] = val

    # --- Logic & Calculations ---

    def calculate(self, *args):
        # Sicheres Auslesen der StringVar Werte
        v = {}
        for k, var in self.vars.items():
            try:
                val_str = var.get().replace(',', '.')
                if not val_str:
                    v[k] = 0.0
                else:
                    v[k] = float(val_str)
            except ValueError:
                v[k] = 0.0

        # Berechnungen
        material_cost_val = (v["totalWeight"] / 1000) * v["materialCost"] + \
                            (v["supportWeight"] / 1000) * v["supportCost"]
        
        machine_cost_val = v["printTime"] * v["machineCost"]
        
        if v["nozzleLifespan"] > 0:
            tooling_cost_val = ((v["totalWeight"] + v["supportWeight"]) / 1000) / v["nozzleLifespan"] * v["nozzleCost"]
        else:
            tooling_cost_val = 0

        labor_cost_val = v["laborTime"] * v["laborCost"]
        finishing_cost = v["finishingCost"]

        base_cost = material_cost_val + machine_cost_val + tooling_cost_val + labor_cost_val + finishing_cost

        failure_markup = base_cost * (v["failureRate"] / 100)
        cost_with_failure = base_cost + failure_markup
        profit_markup_val = cost_with_failure * (v["profitMargin"] / 100)
        
        total_cost = cost_with_failure + profit_markup_val
        
        # Kosten pro Teil = Gesamtkosten (da "Anzahl Teile" entfernt wurde)
        cost_per_part = total_cost 
        
        cost_per_hour = base_cost / v["printTime"] if v["printTime"] > 0 else 0
        total_w_kg = (v["totalWeight"] + v["supportWeight"]) / 1000
        cost_per_gram = base_cost / (v["totalWeight"] + v["supportWeight"]) if total_w_kg > 0 else 0
        
        final_price = cost_per_part * 1.2

        self.results = {
            "baseCost": base_cost,
            "markup": failure_markup + profit_markup_val,
            "totalCost": total_cost,
            "costPerPart": cost_per_part, # Jetzt identisch mit Total Cost
            "materialCostValue": material_cost_val,
            "laborCostValue": labor_cost_val,
            "machineCostValue": machine_cost_val,
            "toolingCostValue": tooling_cost_val,
            "finishingCost": finishing_cost,
            "failureRate": v["failureRate"],
            "profitMargin": v["profitMargin"],
            "profitMarkupValue": profit_markup_val,
            "failureMarkup": failure_markup
        }

        self.labels["metric_cph"].configure(text=f"€{cost_per_hour:.2f}")
        self.labels["metric_cpg"].configure(text=f"€{cost_per_gram:.4f}")
        self.labels["metric_price"].configure(text=f"€{final_price:.2f}")
        
        self.footer_items["summary_base"].configure(text=f"€{base_cost:.2f}")
        self.footer_items["summary_markup"].configure(text=f"€{(failure_markup + profit_markup_val):.2f}")
        self.footer_items["summary_total"].configure(text=f"€{total_cost:.2f}")
        # "per_part" Label im Footer wurde entfernt

        self.update_chart()

    def update_chart(self):
        self.ax.clear()
        
        labels = ['Material', 'Labor', 'Machine', 'Tooling', 'Finish']
        sizes = [
            self.results["materialCostValue"],
            self.results["laborCostValue"],
            self.results["machineCostValue"],
            self.results["toolingCostValue"],
            self.results["finishingCost"]
        ]
        
        colors = ['#2563eb', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444']
        
        final_labels = []
        final_sizes = []
        final_colors = []
        
        for i, s in enumerate(sizes):
            if s > 0:
                final_labels.append(labels[i])
                final_sizes.append(s)
                final_colors.append(colors[i])

        if not final_sizes:
            final_sizes = [1]
            final_labels = [""]
            final_colors = ["#444"]

        wedges, texts, autotexts = self.ax.pie(final_sizes, labels=final_labels, autopct='%1.0f%%',
                                               startangle=90, colors=final_colors, pctdistance=0.85,
                                               textprops=dict(color="white"))
        
        centre_circle = plt.Circle((0,0), 0.70, fc=COLOR_BG_CARD)
        self.ax.add_artist(centre_circle)
        
        self.ax.axis('equal')
        self.canvas.draw()
        
    def reset_values(self):
        for var in self.vars.values():
            var.set("0")

    # --- Translation ---

    def toggle_language(self):
        if self.lang == "de":
            self.lang = "en"
            self.lang_btn.configure(text="🇩🇪 Deutsch")
        else:
            self.lang = "de"
            self.lang_btn.configure(text="🇬🇧 English")
        self.update_language()

    def update_language(self):
        t = translations[self.lang]
        
        for key, widget in self.labels.items():
            if key in t:
                if isinstance(widget, ctk.CTkButton):
                    icon = ""
                    if key == "save_text": icon = "💾 "
                    if key == "load_text": icon = "📂 "
                    if key == "pdf_text": icon = "📄 "
                    if key == "reset_text": icon = "🗑️ "
                    widget.configure(text=f"{icon}{t[key]}")
                else:
                    widget.configure(text=t[key])
        
        self.title_label.configure(text=t["title"])

    # --- File Operations ---

    def save_profile(self):
        data = {k: v.get() for k, v in self.vars.items()}
        file_path = filedialog.asksaveasfilename(defaultextension=".json", 
                                                 filetypes=[("JSON", "*.json")])
        if file_path:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4)
            messagebox.showinfo("Success", "Profile saved!")

    def load_profile(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                for k, v in data.items():
                    if k in self.vars:
                        self.vars[k].set(v)
            except Exception as e:
                messagebox.showerror("Error", f"Could not load file: {e}")

    # --- PDF Generation & UI ---

    def open_pdf_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title(translations[self.lang]["pdf_modal_title"])
        dialog.geometry("600x650") 
        dialog.grab_set() 
        
        # Hauptcontainer für Padding
        content = ctk.CTkFrame(dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)

        # HILFSFUNKTION FÜR KONSISTENTE ZEILEN
        def create_dialog_row(parent, label_text, entry_var):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", pady=5)
            
            # Label feste Breite (150px)
            lbl = ctk.CTkLabel(row, text=label_text, width=150, anchor="w", 
                               font=("Roboto", 12))
            lbl.pack(side="left")
            
            # Entry füllt den Rest
            entry = ctk.CTkEntry(row, textvariable=entry_var)
            entry.pack(side="left", fill="x", expand=True)

        # --- Section 1: Firmendaten ---
        ctk.CTkLabel(content, text=translations[self.lang]["company_section"], 
                     font=("Roboto", 14, "bold"), text_color=COLOR_PRIMARY).pack(pady=(0, 10))

        create_dialog_row(content, translations[self.lang]["company_name_label"], self.company_info["name"])
        create_dialog_row(content, translations[self.lang]["company_owner_label"], self.company_info["owner"])
        create_dialog_row(content, translations[self.lang]["company_address_label"], self.company_info["address"])
        create_dialog_row(content, translations[self.lang]["company_contact_label"], self.company_info["contact"])

        # --- Section 2: Kundendaten ---
        ctk.CTkLabel(content, text=translations[self.lang]["client_section"], 
                     font=("Roboto", 14, "bold"), text_color=COLOR_PRIMARY).pack(pady=(20, 10))
        
        # Lokale Variablen (StringVars)
        var_cust = ctk.StringVar()
        var_proj = ctk.StringVar()
        var_inv = ctk.StringVar()

        create_dialog_row(content, translations[self.lang]["customer_name_label"], var_cust)
        create_dialog_row(content, translations[self.lang]["project_name_label"], var_proj)
        create_dialog_row(content, translations[self.lang]["invoice_number_label"], var_inv)

        # Generate Button
        def do_generate():
            comp_data = {
                "name": self.company_info["name"].get(),
                "owner": self.company_info["owner"].get(),
                "address": self.company_info["address"].get(),
                "contact": self.company_info["contact"].get()
            }
            client_data = {
                "customer": var_cust.get(),
                "project": var_proj.get(),
                "invoice": var_inv.get()
            }
            self.generate_pdf(comp_data, client_data)
            dialog.destroy()
            
        ctk.CTkButton(content, text=translations[self.lang]["generate_btn"], 
                      fg_color=COLOR_PRIMARY, command=do_generate).pack(pady=30)

    def generate_pdf(self, comp_data, client_data):
        pdf = FPDF()
        pdf.add_page()
        
        # Helper: Safe Text
        def safe_txt(txt):
            return txt.encode('latin-1', 'replace').decode('latin-1')

        # Colors
        blue = (37, 99, 235)
        text_col = (50, 50, 50)
        
        # --- HEADER ---
        pdf.set_font("Arial", "B", 24)
        pdf.set_text_color(*blue)
        pdf.cell(0, 10, safe_txt(comp_data["name"]), 0, 1) 
        
        pdf.set_font("Arial", "", 12)
        pdf.set_text_color(*text_col)
        pdf.cell(0, 6, safe_txt(comp_data["owner"]), 0, 1)
        
        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, safe_txt(comp_data["address"]), 0, 1)
        pdf.cell(0, 5, safe_txt(comp_data["contact"]), 0, 1)
        
        # Trennlinie
        y_after_header = pdf.get_y() + 2
        pdf.set_draw_color(*blue)
        pdf.line(10, y_after_header, 200, y_after_header)
        
        # --- INVOICE DETAILS ---
        pdf.set_y(y_after_header + 10)
        pdf.set_font("Arial", "B", 18)
        pdf.set_text_color(*blue)
        pdf.cell(0, 10, "RECHNUNG" if self.lang == 'de' else "INVOICE", 0, 1)
        
        pdf.set_font("Arial", "B", 10)
        pdf.set_text_color(*text_col)
        
        y_details = pdf.get_y()
        pdf.text(10, y_details + 5, "Nr:" if self.lang == 'de' else "No:")
        pdf.set_font("Arial", "", 10)
        pdf.text(30, y_details + 5, safe_txt(client_data["invoice"] if client_data["invoice"] else "REC-001"))
        
        pdf.set_font("Arial", "B", 10)
        pdf.text(120, y_details + 5, "Date:")
        pdf.set_font("Arial", "", 10)
        pdf.text(140, y_details + 5, datetime.now().strftime("%d.%m.%Y"))
        
        pdf.ln(10)
        
        # --- CUSTOMER BOX ---
        box_y = pdf.get_y()
        pdf.set_fill_color(240, 249, 255)
        pdf.rect(10, box_y, 190, 20, 'F')
        
        pdf.set_xy(12, box_y + 4)
        pdf.set_font("Arial", "B", 10)
        pdf.set_text_color(*blue)
        pdf.cell(30, 5, "Kunde/Client: ", 0, 0)
        
        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(*text_col)
        pdf.cell(0, 5, safe_txt(client_data['customer']), 0, 1) 
        
        pdf.set_x(12)
        pdf.set_font("Arial", "B", 10)
        pdf.set_text_color(*blue)
        pdf.cell(30, 5, "Projekt/Project: ", 0, 0)
        
        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(*text_col)
        pdf.cell(0, 5, safe_txt(client_data['project']), 0, 0)
        
        pdf.set_y(box_y + 25)
        
        # --- TABLE ---
        pdf.set_fill_color(*blue)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(90, 8, safe_txt(translations[self.lang]['breakdown_title']), 1, 0, 'L', True)
        pdf.cell(50, 8, "Betrag/Amount", 1, 0, 'R', True)
        pdf.cell(50, 8, "%", 1, 1, 'R', True)
        
        pdf.set_text_color(*text_col)
        pdf.set_font("Arial", "", 10)
        
        rows = [
            (translations[self.lang]['material_label'], self.results["materialCostValue"]),
            (translations[self.lang]['labor_label'], self.results["laborCostValue"]),
            (translations[self.lang]['machine_label'], self.results["machineCostValue"]),
            (translations[self.lang]['tooling_label'], self.results["toolingCostValue"]),
            (translations[self.lang]['finishing_label'], self.results["finishingCost"])
        ]
        
        fill = False
        base = self.results["baseCost"] if self.results["baseCost"] > 0 else 1
        
        for label, value in rows:
            pdf.set_fill_color(245, 245, 245)
            percent = (value / base) * 100
            pdf.cell(90, 7, safe_txt(label), 1, 0, 'L', fill)
            pdf.cell(50, 7, f"EUR {value:.2f}", 1, 0, 'R', fill)
            pdf.cell(50, 7, f"{percent:.0f}%", 1, 1, 'R', fill)
            fill = not fill
            
        # Total Base
        pdf.set_fill_color(*blue)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(90, 8, safe_txt(translations[self.lang]['base_cost_label']), 1, 0, 'L', True)
        pdf.cell(50, 8, f"EUR {base:.2f}", 1, 0, 'R', True)
        pdf.cell(50, 8, "100%", 1, 1, 'R', True)
        
        # --- SUMMARY ---
        pdf.ln(15)
        pdf.set_text_color(*text_col)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, safe_txt(translations[self.lang]['metrics_title']), 0, 1)
        
        y = pdf.get_y()
        pdf.set_draw_color(139, 92, 246)
        pdf.set_fill_color(243, 232, 255)
        pdf.rect(10, y, 190, 40, 'DF')
        
        pdf.set_xy(15, y+5)
        pdf.set_font("Arial", "", 10)
        pdf.cell(100, 7, f"Markups (Fail {self.results['failureRate']}% + Margin {self.results['profitMargin']}%):", 0, 0)
        pdf.cell(80, 7, f"EUR {(self.results['failureMarkup'] + self.results['profitMarkupValue']):.2f}", 0, 1, 'R')
        
        # Cost per Part line removed from PDF as redundant with Total Cost

        # Final Price
        pdf.ln(15)
        pdf.set_fill_color(*blue)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 14)
        pdf.set_y(y + 50) 
        pdf.rect(10, pdf.get_y(), 190, 12, 'F')
        price = self.results["costPerPart"] * 1.2
        pdf.cell(0, 12, f"Selling Price (+20%): EUR {price:.2f}", 0, 1, 'C')
        
        default_filename = f"Invoice_{datetime.now().strftime('%Y%m%d%H%M')}.pdf"
        file_path = filedialog.asksaveasfilename(
            initialfile=default_filename,
            defaultextension=".pdf",
            filetypes=[("PDF Documents", "*.pdf"), ("All Files", "*.*")]
        )

        if file_path:
            try:
                pdf.output(file_path)
                messagebox.showinfo("Export", f"PDF erfolgreich erstellt:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Fehler", f"PDF konnte nicht gespeichert werden:\n{e}")

# --- Translations Data ---
translations = {
    'de': {
        'title': '3D Kostenrechner Pro',
        'job_params': 'Druckparameter',
        'print_time_label': 'Druckzeit (Stunden)',
        'total_weight_label': 'Gesamtgewicht (g)',
        'material_title': 'Material',
        'material_cost_label': 'Kosten pro kg (€)',
        'support_title': 'Stützmaterial',
        'support_weight_label': 'Stützgewicht (g)',
        'support_cost_label': 'Kosten pro kg (€)',
        'machine_title': 'Maschinenoperation',
        'machine_cost_label': 'Kosten pro Stunde (€)',
        'nozzle_cost_label': 'Düsenkosten (€)',
        'nozzle_lifespan_label': 'Düsenlebensdauer (kg)',
        'labor_title': 'Arbeitskosten',
        'labor_cost_label': 'Kosten pro Stunde (€)',
        'labor_time_label': 'Arbeitszeit (Stunden)',
        'finishing_title': 'Nachbearbeitung',
        'finishing_cost_label': 'Kosten (€)',
        'profit_title': 'Gewinn & Sicherheit',
        'failure_rate_label': 'Ausfallquote (%)',
        'profit_margin_label': 'Gewinnmarge (%)',
        'metrics_title': 'Wichtige Kennzahlen',
        'cost_per_hour_label': 'Kosten pro Stunde',
        'cost_per_gram_label': 'Kosten pro Gramm',
        'final_price_label': 'Verkaufspreis',
        'base_cost_label': 'Grundkosten',
        'save_text': 'Speichern',
        'load_text': 'Laden',
        'pdf_text': 'PDF Rechnung',
        'reset_text': 'Reset (Null)',
        'summary_base': 'Grundkosten',
        'summary_markup': '+ Aufschläge',
        'summary_total': '= Gesamtkosten',
        'breakdown_title': 'Kostenaufschlüsselung',
        'material_label': 'Material',
        'labor_label': 'Arbeit',
        'machine_label': 'Maschine',
        'tooling_label': 'Werkzeuge',
        'finishing_label': 'Nachbearbeitung',
        'pdf_modal_title': 'PDF Rechnung erstellen',
        'customer_name_label': 'Kundenname',
        'project_name_label': 'Projektname',
        'invoice_number_label': 'Rechnungsnummer',
        'generate_btn': 'PDF Erstellen',
        'company_section': 'Ihre Firmendaten (Absender)',
        'client_section': 'Kundendaten (Empfänger)',
        'company_name_label': 'Firmenname:',
        'company_owner_label': 'Inhaber/Zusatz:',
        'company_address_label': 'Adresse:',
        'company_contact_label': 'E-Mail/Kontakt:'
    },
    'en': {
        'title': '3D Cost Calculator Pro',
        'job_params': 'Job Parameters',
        'print_time_label': 'Print Time (hours)',
        'total_weight_label': 'Total Weight (g)',
        'material_title': 'Material',
        'material_cost_label': 'Cost per kg (€)',
        'support_title': 'Support Material',
        'support_weight_label': 'Support Weight (g)',
        'support_cost_label': 'Cost per kg (€)',
        'machine_title': 'Machine Operation',
        'machine_cost_label': 'Cost per hour (€)',
        'nozzle_cost_label': 'Nozzle Cost (€)',
        'nozzle_lifespan_label': 'Nozzle Lifespan (kg)',
        'labor_title': 'Labor Costs',
        'labor_cost_label': 'Cost per hour (€)',
        'labor_time_label': 'Labor Time (hours)',
        'finishing_title': 'Post-Processing',
        'finishing_cost_label': 'Cost (€)',
        'profit_title': 'Profit & Safety',
        'failure_rate_label': 'Failure Rate (%)',
        'profit_margin_label': 'Profit Margin (%)',
        'metrics_title': 'Quick Metrics',
        'cost_per_hour_label': 'Cost per Hour',
        'cost_per_gram_label': 'Cost per Gram',
        'final_price_label': 'Selling Price',
        'base_cost_label': 'Base Cost',
        'save_text': 'Save',
        'load_text': 'Load',
        'pdf_text': 'PDF Invoice',
        'reset_text': 'Reset (Zero)',
        'summary_base': 'Base Cost',
        'summary_markup': '+ Markups',
        'summary_total': '= Total Cost',
        'breakdown_title': 'Cost Breakdown',
        'material_label': 'Material',
        'labor_label': 'Labor',
        'machine_label': 'Machine',
        'tooling_label': 'Tooling',
        'finishing_label': 'Finishing',
        'pdf_modal_title': 'Generate PDF Invoice',
        'customer_name_label': 'Customer Name',
        'project_name_label': 'Project Name',
        'invoice_number_label': 'Invoice Number',
        'generate_btn': 'Generate PDF',
        'company_section': 'Your Company (Sender)',
        'client_section': 'Client Details (Recipient)',
        'company_name_label': 'Company Name:',
        'company_owner_label': 'Owner/Subtitle:',
        'company_address_label': 'Address:',
        'company_contact_label': 'Email/Contact:'
    }
}

if __name__ == "__main__":
    app = CostManagerApp()
    app.mainloop()