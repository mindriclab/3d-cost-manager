# 3D Cost Manager

**Was kostet dieser Druck wirklich? Und was verlange ich dafür?**

Offline-Kostenrechner für 3D-Drucke unter Windows. Material, Stützmaterial, Maschinenstunde, Strom, Düsenverschleiß, Arbeitszeit und Nachbearbeitung gehen in die Grundkosten ein. Darauf kommen Ausfallquote, Gewinnmarge und MwSt. Ergebnis: Netto-, Brutto- und Stückpreis, dazu ein fertiges **Angebots-PDF** mit deinen Firmendaten.

> **Fertige Windows-Version (EXE, ohne Python):** [mindriclab.gumroad.com/l/3d-cost-manager](https://mindriclab.gumroad.com/l/3d-cost-manager)

## Funktionen

- Live-Berechnung mit Ringdiagramm der Kostenanteile
- Stückzahl: Preis pro Teil bei Serien
- Stromkosten aus Leistung (Watt) und Strompreis
- MwSt-Satz frei wählbar, Kleinunternehmer-Modus (§ 19 UStG)
- Währung €, $ oder £
- **Angebot (PDF)** für Kunden: Position, Menge, Einzelpreis, Netto, MwSt, Brutto
- **Kalkulation (PDF)** für dich: komplette Kostenaufschlüsselung und Kennzahlen
- Profile pro Drucker und Material speichern und laden
- Firmendaten und letzte Werte bleiben gespeichert
- Deutsch und Englisch

## Selbst starten

Voraussetzung: Python 3.12

```bash
pip install -r requirements.txt
python app.py
```

EXE bauen: `build.bat` (nutzt PyInstaller, Ergebnis in `dist\`).

## Aufbau

| Datei | Inhalt |
|---|---|
| `app.py` | Oberfläche (CustomTkinter, matplotlib) |
| `costcalc.py` | Berechnung, ohne Oberfläche testbar |
| `pdfgen.py` | Angebot und Kalkulation als PDF (fpdf2) |
| `texts.py` | Alle Texte, Deutsch und Englisch |

Einstellungen liegen unter `%APPDATA%\mindric lab\3D Cost Manager\settings.json`.

## Lizenz

MIT, siehe [LICENSE](LICENSE). Mitgelieferte Bibliotheken: siehe [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).

Gebaut von **mindric lab** · [mindriclab.de](https://www.mindriclab.de)
