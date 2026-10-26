# PE4302 Attenuator Controller v2.0
**by OE9SAU**

## Beschreibung
Windows-Steuersoftware für einen digitalen HF-Abschwächer mit PE4302 und Arduino.

Der PE4302 ermöglicht eine einstellbare Dämpfung von 0 bis 31,5 dB in Schritten von 0,5 dB.

## Funktionen
- Grafische Windows-Bedienoberfläche
- Dämpfung über Schieberegler oder Direkteingabe
- Schrittweiten: 0,5 / 1 / 3 / 6 dB
- Vier Speicherplätze für Dämpfungswerte
- Grafische HF-Darstellung und Frequenzkennlinien
- Kommandoeingabe und Statusanzeige
- USB-/COM-Port-Steuerung vorbereitet

## Installation
1. Python 3 unter Windows installieren.
2. Software entpacken.
3. `start_windows.bat` ausführen.
4. PySide6 wird bei Bedarf automatisch installiert.

## Aktueller Stand
Version 2.0 arbeitet im **Simulationsmodus**. Alle Dämpfungseinstellungen werden intern verarbeitet. Eine USB-Verbindung zum Arduino ist noch nicht implementiert.

## Geplante Erweiterungen
- USB-Steuerung des Arduino
- Automatischer Dämpfungs-Sweep
- SCPI-Befehlsunterstützung

---
**Entwicklung: OE9SAU**  
Version: 2.0  
Stand: Oktober 2026