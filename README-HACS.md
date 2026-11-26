# Barcode-Scanner v3 mit HACS-Integration

> **Stand v3.0 (lokal, Branch `feat/hacs-v3`).** Der ESP32 ist nur noch der Scanner.
> Produktsuche, selbstlernende Datenbank und Einkaufsliste erledigt die
> Home-Assistant-Integration **SHYS Barcode Scanner** (HACS).
> Der alte Stand v2.3 (APIs direkt auf dem ESP) bleibt auf `fix/esphome-2026`.

## Warum so?

- Kein HTTP, kein JSON, keine API-Keys auf dem ESP. Die Firmware ist klein und ändert sich kaum.
- Ändert sich eine API, gibt es ein HACS-Update. Niemand muss den ESP neu flashen.
- Bekannte Produkte gehen offline und mit deinem eigenen Namen auf die Liste.
- Unbekannte Produkte lernst du einmal in der Seitenleiste an, auch eigene QR-/EAN-Sticker für lose Ware.

## Einrichtung in 3 Schritten

1. **ESP flashen** mit der Geräte-YAML unten (Buzzer wählen, Display optional).
2. **HACS-Integration installieren:** HACS → Benutzerdefinierte Repositories → Repo der Integration, Typ *Integration* → *SHYS Barcode Scanner* herunterladen → HA neu starten.
3. **Liste wählen:** *Einstellungen → Geräte & Dienste → Integration hinzufügen → SHYS Barcode Scanner* → z. B. `todo.shopping_list` (oder der Picnic-Warenkorb). Fertig.

Der ESP schickt jeden Scan als Event `esphome.barcode_scanned` (`ean`, `device`). Dafür ist **keine**
Freigabe „Dem Gerät erlauben, Home Assistant-Aktionen auszuführen“ nötig. Die Integration antwortet
über die Aktion `esphome.<name>_show_result` (z. B. `esphome.barcode_scanner_show_result`).

## Geräte-YAML

Genau **ein** Buzzer-Paket einbinden, das Display ist optional:

| Paket | Wann |
|---|---|
| `packages/buzzer-passive.yaml` | Passiver Piezo: piept ohne Tonsignal nicht, nur leises Knacken/Knirschen. Töne per PWM + RTTTL |
| `packages/buzzer-active.yaml` | Aktiver Piezo (Original-Stückliste): piept selbst bei HIGH |
| `packages/buzzer-none.yaml` | Kein Buzzer verbaut |
| `packages/display.yaml` | Optional: OLED SSD1306 128×64, I2C 0x3C |

Aus einem (privaten) GitHub-Repo, wie beim Teststand:

```yaml
substitutions:
  name: "barcode-scanner"
  friendly_name: "Barcode Scanner"
  # uart_baud_rate: "57600"   # falls der GM60 nicht auf 9600 steht

packages:
  barcode:
    url: https://github.com/kallejoken/barcode-scanner-test
    ref: main
    username: kallejoken
    password: !secret github_token
    files:
      - barcode.yaml
      - packages/buzzer-passive.yaml     # ODER packages/buzzer-active.yaml
      - packages/display.yaml            # ohne OLED diese Zeile weglassen
    refresh: 1h

wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password
```

Mit lokalen Dateien (neben der Geräte-YAML) siehe `barcode_template.yaml`:

```yaml
packages:
  barcode: !include barcode.yaml
  buzzer: !include packages/buzzer-passive.yaml
  # buzzer: !include packages/buzzer-active.yaml
  display: !include packages/display.yaml
```

### Substitutions

| Name | Standard | Bedeutung |
|---|---|---|
| `name` / `friendly_name` | `barcode-scanner` / `Barcode Scanner` | Hostname und Anzeigename |
| `uart_tx_pin` / `uart_rx_pin` | `GPIO9` / `GPIO10` | GM60 (ESP-TX → Scanner-RX) |
| `uart_baud_rate` | `"9600"` | manche GM60 stehen auf 57600 |
| `beeper_pin` | `GPIO16` | Buzzer |
| `i2c_sda_pin` / `i2c_scl_pin` | `GPIO21` / `GPIO22` | OLED |
| `ean_debounce_ms` | `"3000"` | gleicher Code innerhalb dieser Zeit nur einmal |
| `result_timeout_ms` | `"25000"` | keine Antwort von HA → Fehler-Piep |
| `buzzer_gain` | `"50%"` | nur passiver Buzzer: Lautstärke (PWM-Tastgrad) |

### Töne

| Ergebnis | Aktiv | Passiv |
|---|---|---|
| Gefunden / auf der Liste | kurzer Piep (120 ms) | kurzer aufsteigender Zweiklang |
| Unbekannt (bitte anlernen) | Doppel-Piep | zwei gleiche Töne |
| Fehler / keine Verbindung zu HA | langer Piep (600 ms) | tiefer, absteigender Ton |

In HA gibt es dazu den Knopf **Buzzer Test**.

### Testen ohne Scanner

*Entwicklerwerkzeuge → Aktionen* → `esphome.barcode_scanner_simulate_scan` mit `code: "4337256722261"`.
Oder direkt in der Seitenleiste *Barcode Scanner → Test & Backup*.

## GM60-Einrichtung

Ab Werk liest der GM60 im trägen Lesemodus: Man muss ihn hin- und herbewegen, bis etwas erkannt wird.
Einmalig die Einstellungs-Codes aus dem [GM60-Handbuch (PDF)](https://www.mikroshop.ch/pdf/GM60Reader.pdf)
abscannen. Am Bildschirm so weit reinzoomen, dass immer nur ein Code zu sehen ist. Die Seitenzahlen
sind die unten auf der Seite gedruckten, im PDF-Viewer ist es jeweils Seite +4.

1. **Seite 19** (2.2 Setup Code): **„Setup code on“**
2. **Seite 22** (4.1 Continuous Mode): **„Continuous Mode“** und darunter bei *Single Read Time* **„Infinite“**
3. **Seite 26/27** (5.1 Breathing Lamp): **„Breathing lamp 1-White“** (Code oben auf Seite 27), weißes
   Licht statt buntem Farbwechsel. Unter rotem/blauem Licht verlieren viele Barcodes Kontrast.
   Alternativ auf Seite 26 **„Normal“** (Licht nur beim Lesen) oder **„Off“**.
4. **Seite 19:** **„Off“**, damit Einstellungs-Codes im Alltag gesperrt sind.

Jeder angenommene Code lässt die grüne LED kurz aufleuchten. Im ESPHome-Log erscheint dabei nichts,
das ist normal. Die Einstellungen bleiben dauerhaft gespeichert, „Reset“ (Seite 19) stellt alles zurück.
Optional: Auf Seite 22 lässt sich noch eine *Break time* (z. B. „500ms“) einstellen. Nötig ist das nicht.

Weitere Tipps: Schutzfolie von der Linse abziehen, glänzende Verpackungen leicht kippen.

## Hardware

| Teil | Anschluss |
|---|---|
| ESP32 D1 Mini (`wemos_d1_mini32`) | – |
| GM60 Barcode-Scanner | UART: ESP TX = GPIO9, ESP RX = GPIO10, 9600 Baud |
| Buzzer (aktiv oder passiv) | GPIO16 |
| OLED SSD1306 128×64 (optional) | I2C 0x3C, SDA = GPIO21, SCL = GPIO22 |
