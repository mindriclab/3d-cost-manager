"""Kostenrechnung für 3D-Drucke – ohne Oberfläche, damit sie testbar bleibt."""

DEFAULTS = {
    # Druckauftrag (Zeit und Gewicht gelten für den ganzen Auftrag, alle Teile zusammen)
    "printTime": 5.0,        # Stunden
    "totalWeight": 50.0,     # Gramm
    "quantity": 1.0,         # Stück im Auftrag
    # Material
    "materialCost": 18.0,    # pro kg
    "supportWeight": 0.0,    # Gramm
    "supportCost": 12.0,     # pro kg
    # Maschine
    "machineCost": 1.5,      # pro Stunde (Abschreibung, Wartung)
    "powerWatt": 150.0,      # durchschnittliche Leistung in Watt
    "energyPrice": 0.35,     # pro kWh
    "nozzleCost": 5.0,       # pro Düse
    "nozzleLifespan": 15.0,  # kg pro Düse
    # Arbeit und Nachbearbeitung
    "laborCost": 20.0,       # pro Stunde
    "laborTime": 0.5,        # Stunden
    "finishingCost": 0.0,    # pauschal
    # Gewinn und Sicherheit
    "failureRate": 5.0,      # Prozent
    "profitMargin": 25.0,    # Prozent
    # Steuer
    "vatRate": 19.0,         # Prozent
}


def parse_number(text) -> float:
    """Akzeptiert Komma und Punkt, leere oder ungültige Eingaben werden 0."""
    try:
        s = str(text).strip().replace(" ", "").replace(",", ".")
        return float(s) if s else 0.0
    except ValueError:
        return 0.0


def calculate(values: dict, small_business: bool = False) -> dict:
    v = {k: parse_number(values.get(k, d)) for k, d in DEFAULTS.items()}
    quantity = max(1.0, round(v["quantity"]))
    weight_kg = (v["totalWeight"] + v["supportWeight"]) / 1000

    material = (v["totalWeight"] / 1000) * v["materialCost"] + (v["supportWeight"] / 1000) * v["supportCost"]
    machine = v["printTime"] * v["machineCost"]
    energy = v["printTime"] * (v["powerWatt"] / 1000) * v["energyPrice"]
    tooling = weight_kg / v["nozzleLifespan"] * v["nozzleCost"] if v["nozzleLifespan"] > 0 else 0.0
    labor = v["laborTime"] * v["laborCost"]
    finishing = v["finishingCost"]

    base = material + machine + energy + tooling + labor + finishing
    failure = base * v["failureRate"] / 100
    profit = (base + failure) * v["profitMargin"] / 100
    net = base + failure + profit
    vat_rate = 0.0 if small_business else v["vatRate"]
    vat = net * vat_rate / 100
    gross = net + vat

    return {
        "material": material,
        "machine": machine,
        "energy": energy,
        "tooling": tooling,
        "labor": labor,
        "finishing": finishing,
        "base": base,
        "failure": failure,
        "profit": profit,
        "markup": failure + profit,
        "net": net,
        "vatRate": vat_rate,
        "vat": vat,
        "gross": gross,
        "quantity": int(quantity),
        "netPerPiece": net / quantity,
        "grossPerPiece": gross / quantity,
        "costPerHour": base / v["printTime"] if v["printTime"] > 0 else 0.0,
        "costPerGram": base / (weight_kg * 1000) if weight_kg > 0 else 0.0,
        "failureRate": v["failureRate"],
        "profitMargin": v["profitMargin"],
    }


CURRENCIES = {"EUR": "€", "USD": "$", "GBP": "£"}


def fmt_money(value: float, currency: str, lang: str, decimals: int = 2) -> str:
    symbol = CURRENCIES.get(currency, currency)
    num = f"{value:,.{decimals}f}"
    if lang == "de":
        # 1,234.56 -> 1.234,56
        num = num.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{num} {symbol}"
    return f"{symbol}{num}"


def fmt_percent(value: float, lang: str) -> str:
    s = f"{value:g}"
    return (s.replace(".", ",") if lang == "de" else s) + " %"
