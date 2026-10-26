PE4302 Windows Controller – Version 0.1 (Simulation)

Voraussetzung: Python 3.10 oder neuer unter Windows.
Start: start_windows.bat doppelklicken.

Bedienung:
- Schieberegler: Dämpfung 0 bis 31,5 dB in 0,5-dB-Schritten
- Plus/Minus: gewählte Schrittweite
- Schnellwahltasten: direkte Dämpfung
- Speicher M1–M4: Linksklick abrufen, Rechtsklick aktuellen Wert speichern
- Befehlsvorschau: simulierte ATT-Kommandos

WICHTIG: Noch keine USB-/COM-Kommunikation. Die COM-Liste ist ein Platzhalter.
Speicherwerte gelten nur bis zum Beenden der Anwendung.

Vorgesehenes späteres Textprotokoll (noch nicht implementiert):
ATT 10.5
ATT?
STEP +0.5
STEP -0.5
IDN?
HELP

Optional später eine EXE erstellen:
py -m pip install pyinstaller
py -m PyInstaller --onefile --windowed --name PE4302_Controller pe4302_gui.py
Ergebnis im Ordner dist.
