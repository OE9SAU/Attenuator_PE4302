//
// PE4302 Digital Step Attenuator
// by OE9SAU
// OLED SH1106, I2C-Adresse 0x3C
//
// V2.1:
// Grosse Anzeige: Hardware-Einstellwert, 0,5-dB-Schritte
// Kleine Anzeige: Reale Daempfung mit Korrektur
// Korrektur: 0,1-dB-Schritte einstellbar
//
// V3.0:
// Serielle Steuerung ueber USB, 38400 Baud
// Daempfung setzen und abfragen
// Messkorrektur setzen und abfragen
// EEPROM-Speicherung
// Automatische Statusmeldungen
// Synchronisation mit Windows Controller
//
// V3.1:
// Display-Modus zwischen normal und 180° über den Encoder wechseln
// 5 Sekunden halten und Display-Ausrichtung einstellen
//

#include <EEPROM.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SH1106.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

#define OLED_RESET -1

Adafruit_SH1106 display(OLED_RESET);

// PE4302
const int DATA = 6;
const int CLOCK = 7;
const int LE = 8;

// Encoder
const int ra = 2;
const int rb = 3;
const int sw = 4;

// EEPROM
const int ATT_ADDR = 10;
const int CORR_ADDR = 20;
const int ROTATION_ADDR = 30;

// Display-Ausrichtung: 0 = normal, 2 = um 180 Grad gedreht
byte displayRotation = 0;
bool rotationMode = false;

// Hardware-Einstellwert
float att = 0.0;
const float attmin = 0.0;
const float attmax = 31.5;

// Messkorrektur nur fuer die Anzeige
float correction = 0.0;
const float correctionMin = -5.0;
const float correctionMax = 5.0;

bool calibrationMode = false;
bool displayupdate = true;

int alast;

// Serielle Kommunikation
const unsigned long BAUDRATE = 38400;
const byte SERIAL_BUFFER_SIZE = 40;

char serialBuffer[SERIAL_BUFFER_SIZE];
byte serialIndex = 0;
bool serialOverflow = false;

// Encodertaster
bool buttonPressed = false;
bool longPress = false;
unsigned long pressedAt = 0;

// Anzeige nach Speichern
unsigned long savedUntil = 0;

// --------------------------------------------------
// SETUP
// --------------------------------------------------

// Fester Versatz nur bei 180 Grad, ohne zusaetzlichen EEPROM-Wert.
const int DISPLAY_SHIFT_180 = 2;

void showSaved();
void setAttenuator(float attent);
void sendStatus();
void handleSerial();
void handleButton();
void handleEncoder();
void updateDisplay();
void processCommand(char *cmd);
void changeAttenuation(float value);

int displayOffsetX() {
  return displayRotation == 2 ? DISPLAY_SHIFT_180 : 0;
}

void setDisplayCursor(int x, int y) {
  display.setCursor(x + displayOffsetX(), y);
}

void setup() {
  pinMode(DATA, OUTPUT);
  pinMode(CLOCK, OUTPUT);
  pinMode(LE, OUTPUT);

  digitalWrite(DATA, LOW);
  digitalWrite(CLOCK, LOW);
  digitalWrite(LE, LOW);

  pinMode(ra, INPUT_PULLUP);
  pinMode(rb, INPUT_PULLUP);
  pinMode(sw, INPUT_PULLUP);

  EEPROM.get(ATT_ADDR, att);

  if (isnan(att) || isinf(att)) {
    att = 0.0;
  }

  att = constrain(att, attmin, attmax);
  att = round(att * 2.0) / 2.0;

  EEPROM.get(CORR_ADDR, correction);

  if (isnan(correction) ||
      isinf(correction) ||
      correction < correctionMin ||
      correction > correctionMax) {
    correction = 0.0;
  }

  correction = round(correction * 10.0) / 10.0;

  setAttenuator(att);
  alast = digitalRead(ra);

  Serial.begin(BAUDRATE);

  // Gespeicherte Display-Ausrichtung laden
  EEPROM.get(ROTATION_ADDR, displayRotation);

  if (displayRotation != 0 && displayRotation != 2) {
    displayRotation = 0;
  }

  // Display einmal initialisieren und Ausrichtung setzen
  display.begin(SH1106_SWITCHCAPVCC, 0x3C);
  display.setRotation(displayRotation);
  display.clearDisplay();
  display.setTextColor(WHITE, BLACK);
  display.setTextSize(1);

  display.drawLine(15 + displayOffsetX(), 12, 35 + displayOffsetX(), 12, WHITE);
  display.drawRect(36 + displayOffsetX(), 3, 56, 19, WHITE);
  display.drawLine(92 + displayOffsetX(), 12, 112 + displayOffsetX(), 12, WHITE);

  setDisplayCursor(43, 9);
  display.print(F("31.5 dB"));

  setDisplayCursor(34, 30);
  display.print(F("Attenuator"));

  setDisplayCursor(32, 50);
  display.print(F("OE9SAU v3.1"));

  display.display();
  delay(3000);

  displayupdate = true;

  Serial.println(F("PE4302 OE9SAU V3.1 READY"));
  sendStatus();
}

// --------------------------------------------------
// LOOP
// --------------------------------------------------

void loop() {
  handleSerial();
  handleButton();
  handleEncoder();

  if (savedUntil != 0) {
    if ((long)(millis() - savedUntil) < 0) {
      return;
    }

    savedUntil = 0;
    displayupdate = true;
  }

  if (displayupdate) {
    updateDisplay();
    displayupdate = false;
  }
}

// --------------------------------------------------
// SERIAL
// --------------------------------------------------

void handleSerial() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();

    if (c == '\r' || c == '\n') {
      if (serialOverflow) {
        Serial.println(F("ERR LINE TOO LONG"));
      } else if (serialIndex > 0) {
        serialBuffer[serialIndex] = '\0';
        processCommand(serialBuffer);
      }

      serialIndex = 0;
      serialOverflow = false;
    } else if (serialOverflow) {
      // Rest der zu langen Zeile verwerfen
    } else if (serialIndex < SERIAL_BUFFER_SIZE - 1) {
      serialBuffer[serialIndex++] = c;
    } else {
      serialOverflow = true;
    }
  }
}

bool parseValue(const char *text, float &value) {
  while (*text == ' ') {
    text++;
  }

  if (*text == '\0') {
    return false;
  }

  char *endptr;
  double result = strtod(text, &endptr);

  if (endptr == text ||
      isnan(result) ||
      isinf(result)) {
    return false;
  }

  while (*endptr == ' ') {
    endptr++;
  }

  if (*endptr != '\0') {
    return false;
  }

  value = (float)result;
  return true;
}

void processCommand(char *cmd) {
  // Leerzeichen am Anfang entfernen
  while (*cmd == ' ') {
    cmd++;
  }

  // Kleinbuchstaben in Grossbuchstaben umwandeln
  for (char *p = cmd; *p; p++) {
    if (*p >= 'a' && *p <= 'z') {
      *p -= 32;
    }
  }

  if (strcmp(cmd, "ATT?") == 0) {
    Serial.print(F("ATT "));
    Serial.println(att, 1);
  }

  else if (strcmp(cmd, "REAL?") == 0) {
    Serial.print(F("REAL "));
    Serial.println(att + correction, 1);
  }

  else if (strcmp(cmd, "CORR?") == 0) {
    Serial.print(F("CORR "));
    Serial.println(correction, 1);
  }

  else if (strcmp(cmd, "STATUS?") == 0) {
    sendStatus();
  }

  else if (strcmp(cmd, "IDN?") == 0) {
    Serial.println(F("PE4302,OE9SAU,V3.0"));
  }

  else if (strcmp(cmd, "ATT MIN") == 0 ||
           strcmp(cmd, "MIN") == 0) {
    changeAttenuation(attmin);
  }

  else if (strcmp(cmd, "ATT MAX") == 0 ||
           strcmp(cmd, "MAX") == 0) {
    changeAttenuation(attmax);
  }

  else if (strncmp(cmd, "ATT ", 4) == 0) {
    float value;

    if (!parseValue(cmd + 4, value) ||
        value < attmin ||
        value > attmax) {
      Serial.println(F("ERR ATT RANGE"));
      return;
    }

    changeAttenuation(value);
  }

  else if (strncmp(cmd, "STEP ", 5) == 0) {
    float value;

    if (!parseValue(cmd + 5, value)) {
      Serial.println(F("ERR STEP"));
      return;
    }

    changeAttenuation(att + value);
  }

  else if (strncmp(cmd, "CORR ", 5) == 0) {
    float value;

    if (!parseValue(cmd + 5, value) ||
        value < correctionMin ||
        value > correctionMax) {
      Serial.println(F("ERR CORR RANGE"));
      return;
    }

    correction = round(value * 10.0) / 10.0;
    displayupdate = true;

    Serial.print(F("OK CORR "));
    Serial.println(correction, 1);

    sendStatus();
  }

  else if (strcmp(cmd, "SAVE") == 0) {
    EEPROM.put(ATT_ADDR, att);
    Serial.println(F("OK SAVE ATT"));
    showSaved();
  }

  else if (strcmp(cmd, "SAVE CORR") == 0) {
    EEPROM.put(CORR_ADDR, correction);
    Serial.println(F("OK SAVE CORR"));
    showSaved();
  }

  else if (strcmp(cmd, "HELP") == 0) {
    Serial.println(F("ATT x.x"));
    Serial.println(F("ATT?"));
    Serial.println(F("REAL?"));
    Serial.println(F("CORR x.x"));
    Serial.println(F("CORR?"));
    Serial.println(F("STEP +0.5 / -0.5"));
    Serial.println(F("MIN / MAX"));
    Serial.println(F("SAVE / SAVE CORR"));
    Serial.println(F("STATUS?"));
    Serial.println(F("IDN?"));
    Serial.println(F("HELP"));
  }

  else {
    Serial.println(F("ERR UNKNOWN COMMAND"));
  }
}

// --------------------------------------------------
// DAEMPFUNG
// --------------------------------------------------

void changeAttenuation(float value) {
  value = constrain(value, attmin, attmax);
  value = round(value * 2.0) / 2.0;

  att = value;
  setAttenuator(att);

  Serial.print(F("OK ATT "));
  Serial.println(att, 1);

  sendStatus();
}

void sendStatus() {
  Serial.print(F("STATUS ATT="));
  Serial.print(att, 1);

  Serial.print(F(" REAL="));
  Serial.print(att + correction, 1);

  Serial.print(F(" CORR="));
  Serial.println(correction, 1);
}

// --------------------------------------------------
// TASTER
// --------------------------------------------------

void handleButton() {
  bool pressed = (digitalRead(sw) == LOW);

  if (pressed && !buttonPressed) {
    buttonPressed = true;
    pressedAt = millis();
    longPress = false;
  }

  if (pressed && buttonPressed && !rotationMode) {
    unsigned long heldFor = millis() - pressedAt;

    if (heldFor >= 5000UL) {
      longPress = true;
      calibrationMode = false;
      rotationMode = true;
      displayupdate = true;
    }
    else if (!calibrationMode &&
             !longPress &&
             heldFor >= 2000UL) {
      longPress = true;
      calibrationMode = true;
      displayupdate = true;
    }
  }

  if (!pressed && buttonPressed) {
    buttonPressed = false;

    if (!longPress) {
      if (rotationMode) {
        EEPROM.update(ROTATION_ADDR, displayRotation);
        rotationMode = false;
      }
      else if (calibrationMode) {
        EEPROM.put(CORR_ADDR, correction);
        calibrationMode = false;

        Serial.println(F("OK SAVE CORR"));
      }
      else {
        EEPROM.put(ATT_ADDR, att);

        Serial.println(F("OK SAVE ATT"));
      }

      showSaved();
    }

    alast = digitalRead(ra);
    displayupdate = true;
  }
}

// --------------------------------------------------
// ENCODER
// --------------------------------------------------

void handleEncoder() {
  int aval = digitalRead(ra);

  if (alast == HIGH && aval == LOW) {
    delay(2);

    if (digitalRead(ra) == LOW) {
      int direction;

      if (digitalRead(rb) == HIGH) {
        direction = 1;
      } else {
        direction = -1;
      }

      if (rotationMode) {
        displayRotation = (displayRotation == 0) ? 2 : 0;
        display.setRotation(displayRotation);
        displayupdate = true;
      }
      else if (calibrationMode) {
        correction += direction * 0.1;
        correction = round(correction * 10.0) / 10.0;

        correction = constrain(
          correction, correctionMin, correctionMax
        );

        displayupdate = true;
        sendStatus();
      }
      else {
        float newAtt = constrain(
          att + direction * 0.5,
          attmin,
          attmax
        );

        if (newAtt != att) {
          att = newAtt;
          setAttenuator(att);

          Serial.print(F("EVENT ATT "));
          Serial.println(att, 1);

          sendStatus();
        }
      }
    }
  }

  alast = digitalRead(ra);
}

// --------------------------------------------------
// OLED
// --------------------------------------------------

void updateDisplay() {
  display.clearDisplay();
  display.setTextColor(WHITE, BLACK);
  display.setTextSize(1);
  setDisplayCursor(0, 0);

  if (rotationMode) {
    display.print(F("Display drehen"));

    display.setTextSize(2);
    setDisplayCursor(0, 21);

    if (displayRotation == 0) {
      display.print(F("Normal"));
    } else {
      display.print(F("180 Grad"));
    }

    display.setTextSize(1);
    setDisplayCursor(0, 45);
    display.print(F("Drehen: umschalten"));

    setDisplayCursor(0, 56);
    display.print(F("Druecken: speichern"));
  }
  else if (calibrationMode) {
    display.print(F("Messwert abgleichen"));

    display.setTextSize(2);
    setDisplayCursor(0, 17);

    if (correction >= 0.0) {
      display.print(F("+"));
    }

    display.print(correction, 1);
    display.print(F(" dB"));

    display.setTextSize(1);
    setDisplayCursor(0, 39);
    display.print(F("Real: "));
    display.print(att + correction, 1);
    display.print(F(" dB"));

    setDisplayCursor(0, 54);
    display.print(F("Druecken: speichern"));
  }
  else {
    display.print(F("PE4302 Attenuator"));

    display.setTextSize(2);
    setDisplayCursor(0, 21);
    display.print(att, 1);
    display.print(F(" dB"));

    display.setTextSize(1);
    setDisplayCursor(0, 51);
    display.print(F("Real: "));
    display.print(att + correction, 1);
    display.print(F(" dB"));
  }

  display.display();
}

// --------------------------------------------------
// PE4302 HARDWARE
// --------------------------------------------------

void setAttenuator(float attent) {
  // Keine Messkorrektur an die Hardware senden.
  int attent2 = (int)round(attent * 2.0);

  if (attent2 < 0 || attent2 > 63) {
    return;
  }

  digitalWrite(LE, LOW);
  digitalWrite(CLOCK, LOW);

  for (int b = 6; b > 0; b--) {
    int bitValue = ((attent2 << 1) >> b) & 0x01;

    digitalWrite(DATA, bitValue);
    digitalWrite(CLOCK, HIGH);
    digitalWrite(CLOCK, LOW);
  }

  digitalWrite(LE, HIGH);
  digitalWrite(LE, LOW);

  displayupdate = true;
}

// Speicherbestaetigung
void showSaved() {
  display.clearDisplay();
  display.setTextColor(WHITE, BLACK);
  display.setTextSize(1);
  setDisplayCursor(25, 28);
  display.print(F("- saved -"));
  display.display();

  savedUntil = millis() + 1000UL;
  displayupdate = true;
}

