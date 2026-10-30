# PE4302 Attenuator Controller

## Beschreibung
Arduino-Firmware und Windows-Steuersoftware für den digitalen HF-Abschwächer PE4302.

Der Arduino kann sowohl eigenständig über einen Drehencoder und ein OLED-Display als auch über USB mit der Windows-Software bedient werden. Für den eigenständigen Betrieb ist kein PC erforderlich.

Der PE4302 ermöglicht eine einstellbare Dämpfung von **0 bis 31,5 dB in 0,5-dB-Schritten**.

## Funktionen
- Grafische Windows-Bedienoberfläche
- Dämpfungseinstellung über Schieberegler, Direkteingabe oder Drehencoder
- Wählbare Schrittweiten: 0,5 / 1 / 3 / 6 dB
- Vier Speicherplätze für Dämpfungswerte
- Integrierter HF-Pegelrechner für 50 Ω
- Anzeige der Hardware-Dämpfung und des korrigierten Dämpfungswerts
- Serielle Kommandoeingabe und Statusanzeige
- USB-/COM-Port-Steuerung mit 38400 Baud
- Automatische Synchronisation zwischen Arduino und Windows-Software
- EEPROM-Speicherung der Dämpfung und Messkorrektur

ab V3.1
- Display-Modus normal und 180° Ansicht wählbar


## Installation
1. Python 3 unter Windows installieren.
2. Software herunterladen und entpacken.
3. `start_windows.bat` ausführen.
4. Benötigte Python-Bibliotheken werden bei Bedarf automatisch installiert.
5. COM-Port auswählen und Verbindung zum Arduino herstellen.

## Aktueller Stand
- **Windows Controller:** Version 1.02
- **Arduino-Firmware:** Version 3.1
- **Status:** USB-Steuerung erfolgreich getestet

