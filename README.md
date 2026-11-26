# Barcode-Scanner für ESPHome

![Barcode-Scanner für ESPHome](https://user-images.githubusercontent.com/705724/236686920-aefc9c7b-0104-46ff-8f4c-45027e6fa1a7.jpg)
[<img src="https://user-images.githubusercontent.com/705724/236687065-3938ffdd-424e-44a6-9bef-6b1bdbaff480.png" width="300px" alt="Made for ESPHome">](https://esphome.io/guides/made_for_esphome.html)

**Scannen. Fertig. Steht auf der Einkaufsliste.**
Mit dem Barcode-Scanner füllst du deine Einkaufsliste in Home Assistant, ohne App oder Browser zu öffnen und etwas einzutippen. Natürlich lassen sich die gescannten Codes auch für jeden anderen Zweck nutzen – hier sind der Fantasie keine Grenzen gesetzt.

> [!NOTE]
> **Neu in Version 3.0:** Das Projekt wurde komplett neu aufgebaut und läuft wieder sauber.
> Der ESP32 ist nur noch der Scanner. Produktsuche, selbstlernende Datenbank, Seitenleisten-Panel und Push-Nachrichten übernimmt die Home-Assistant-Integration **[SHYS Barcode Scanner](https://github.com/kallejoken/shys-barcode-scanner)**.
>
> Dieses Repository unter `kallejoken/barcode-scanner-test` ist die aktuelle Testversion der Firmware.
> Nach der Testphase zieht das Projekt zurück zu [SmartHome-yourself/barcode-scanner-for-esphome](https://github.com/SmartHome-yourself/barcode-scanner-for-esphome). Wir sagen rechtzeitig Bescheid.

## Überblick

Früher hat der ESP32 die Produktdatenbanken selbst per HTTPS abgefragt. Sobald eine API oder ESPHome sich geändert hat, musste die Firmware neu geflasht werden – genau das hat das Projekt zeitweise lahmgelegt.

Ab **v3.0** ist die Aufgabe klar getrennt:

- **Schlanke ESPHome-Firmware auf dem ESP32** (mind. ESPHome 2026.10.0): Der [GM60](https://www.mikroshop.ch/pdf/GM60Reader.pdf) liest den Code per UART, die Firmware prüft Länge und Zeichen, unterdrückt Doppelscans und schickt das Event `esphome.barcode_scanned` an Home Assistant. Optional zeigt ein OLED den Status, ein Buzzer gibt Rückmeldung.
- **Die komplette Produkt-Logik läuft in Home Assistant** in der Integration **[SHYS Barcode Scanner](https://github.com/kallejoken/shys-barcode-scanner)** (installierbar über den Home Assistant Marketplace):
  - Open Food Facts → [ean-suche.net](https://ean-suche.net) → optional OpengtinDB
  - selbstlernende lokale Datenbank (bekannte Produkte auch offline, mit deinem eigenen Namen)
  - Seitenleisten-Panel zum Anlernen, Umbenennen und Verwalten, auch eigene QR-/EAN-Sticker für lose Ware
  - Push-Nachrichten mit Direkt-Antwort und Verwerfen, auch an mehrere Handys
  - Ziel ist **jede** `todo`-Liste: Home-Assistant-Einkaufsliste, [Bring!](https://www.home-assistant.io/integrations/bring/), [Picnic](https://www.home-assistant.io/integrations/picnic/) und andere

Ändert sich eine API, reicht ein Update der Integration. Der ESP muss dafür nicht neu geflasht werden.

## Video zum Projekt

Ein ausführliches Video zum Aufbau findest du auf YouTube (Hardware und Gehäuse sind weiterhin aktuell, die Software entspricht dem Stand vor v3.0 – die Einrichtung folgt den drei Schritten weiter unten):

[<img src="https://user-images.githubusercontent.com/705724/215211264-53b242de-2256-463d-8e26-3b4dcc7451e5.png" width="400px" alt="Video: Barcode-Scanner für ESPHome auf YouTube">](https://youtu.be/08J4WN4iDI0)

Mehr Hintergrund, Platine und Gehäuse auch im [Blog-Artikel bei SmartHome yourself](https://www.smarthomeyourself.de/blog/home-assistant-einkaufsliste-ueber-barcode-scanner-fuellen-mit-esphome).

## Stückliste, Verdrahtung, Platine und Gehäuse

### Benötigte Bauteile

| Teil | Optional? | Beispiel-Link |
|---|---|---|
| D1 Mini ESP32 (`wemos_d1_mini32`) | Pflicht | [Amazon](https://amzn.to/3kLEt1s)\* |
| Barcode-Scanner GM60 (UART) | Pflicht | [Amazon](https://amzn.to/3mq6vA2)\* |
| Piezo-Buzzer, aktiv oder passiv | Optional | [Aktiver Piezo](https://amzn.to/3Zps3eM)\* |
| 0,96″ OLED SSD1306 128×64 (I2C) | Optional | [Amazon](https://amzn.to/3kH2Ld7)\* |

\* Affiliate-Links, siehe Hinweis am Ende.

### Verdrahtung (Standard der Original-Platine)

| Anschluss | Pin / Wert | Hinweis |
|---|---|---|
| GM60 UART | ESP-TX **GPIO9** → Scanner-RX, ESP-RX **GPIO10** → Scanner-TX | 9600 Baud (manche Module stehen auf 57600). Die Compile-Warnung *„might already be used by the flash interface“* ist auf dieser Platine bekannt und unkritisch. |
| Buzzer | **GPIO16** | Aktiver Piezo: piept selbst bei HIGH (`packages/buzzer-active.yaml`). Passiver Piezo: braucht ein Tonsignal per PWM/RTTTL (`packages/buzzer-passive.yaml`), sonst nur ein leises Knacken. Ohne Buzzer: `packages/buzzer-none.yaml`. |
| OLED SSD1306 128×64 | I2C-Adresse **`0x3C`**, SDA **GPIO21**, SCL **GPIO22** | Nur mit `packages/display.yaml`. Manche Module nutzen `0x3D` – dann `ssd1306_i2c_address` anpassen. |

### Platine

Die Platine kannst du wie immer bei PCBWay bestellen:

![Platine des Barcode-Scanners](https://github.com/SmartHome-yourself/barcode-scanner-for-esphome/assets/705724/773939a7-0420-4d92-8613-689225beb13c)

https://www.pcbway.com/project/shareproject/Barcode_scanner_made_for_ESPHome_bb9bba9a.html

### 3D-gedrucktes Gehäuse

Die STL-Dateien für das Gehäuse liegen auf Thingiverse: [Barcode Scanner for ESPHome (GM60)](https://www.thingiverse.com/thing:6016884)

## Einrichtung in 3 Schritten

### 1. GM60 konfigurieren

Ab Werk liest der GM60 im trägen Lesemodus: Man muss ihn hin- und herbewegen, bis etwas erkannt wird. Einmalig die Einstellungs-Codes aus dem [GM60-Handbuch (PDF)](https://www.mikroshop.ch/pdf/GM60Reader.pdf) abscannen. Am Bildschirm so weit reinzoomen, dass immer nur **ein** Code zu sehen ist.

Die Seitenzahlen sind die **unten auf der Seite gedruckten**. Im PDF-Viewer ist es jeweils **Seite +4**.

1. **Seite 19** (2.2 Setup Code): **Setup code on**
2. **Seite 22** (4.1 Continuous Mode): **Continuous Mode** und darunter bei *Single Read Time* **Infinite**. Optional zusätzlich eine *Break Time* von **500 ms**.
3. **Seite 26/27** (5.1 Breathing Lamp): **Breathing lamp 1-White** (Code oben auf Seite 27) – weißes Licht statt buntem Farbwechsel. Unter rotem oder blauem Licht verlieren viele Barcodes den Kontrast. Alternativen auf Seite 26: **Normal** (Licht nur beim Lesen) oder **Off**.
4. **Seite 19:** **Off**, damit Einstellungs-Codes im Alltag gesperrt sind.

Jeder angenommene Code lässt die grüne LED kurz aufleuchten. Im ESPHome-Log erscheint dabei nichts, das ist normal. Die Einstellungen bleiben dauerhaft gespeichert; **Reset** auf Seite 19 stellt alles zurück.

Weitere Tipps: Schutzfolie von der Linse abziehen, glänzende Verpackungen leicht kippen.

### 2. ESP32 mit ESPHome flashen

Im ESPHome Device Builder eine neue Geräte-YAML anlegen (oder eine vorhandene ersetzen) und den folgenden Stand verwenden. Genau **ein** Buzzer-Paket einbinden, das Display ist optional.

| Paket | Wann |
|---|---|
| `packages/buzzer-passive.yaml` | Passiver Piezo: Töne per PWM + RTTTL |
| `packages/buzzer-active.yaml` | Aktiver Piezo (Original-Stückliste): piept selbst bei HIGH |
| `packages/buzzer-none.yaml` | Kein Buzzer verbaut |
| `packages/display.yaml` | Optional: OLED SSD1306 128×64, I2C `0x3C` |

Aktuell liegt die Firmware im Test-Repo [`kallejoken/barcode-scanner-test`](https://github.com/kallejoken/barcode-scanner-test). Ist das Repo noch privat, braucht ESPHome einen GitHub-Token mit Leserecht auf genau dieses Repository (nicht das Konto-Passwort). Token in die `secrets.yaml` von ESPHome eintragen:

```yaml
wifi_ssid: "MeinWLAN"
wifi_password: "geheim"
github_token: "github_pat_..."
```

Geräte-YAML:

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
      - packages/buzzer-passive.yaml     # oder buzzer-active.yaml / buzzer-none.yaml
      - packages/display.yaml            # ohne OLED diese Zeile weglassen
    refresh: 1h

wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password
```

Ist das Repo später öffentlich, entfallen `username` und `password`. Alles unter `substitutions` überschreibt die Vorgaben aus `barcode.yaml`. Mit `refresh: 1h` holt ESPHome Änderungen aus dem Repo spätestens nach einer Stunde.

Wer die Dateien lokal neben der Geräte-YAML liegen hat, nimmt die Vorlage [`barcode_template.yaml`](barcode_template.yaml):

```yaml
packages:
  barcode: !include barcode.yaml
  buzzer: !include packages/buzzer-passive.yaml    # oder buzzer-active.yaml / buzzer-none.yaml
  # display: !include packages/display.yaml        # mit OLED einkommentieren
```

Fertige Kombinationen (passiv/aktiv/ohne Buzzer, mit oder ohne Display) liegen unter [`examples/`](examples/).

**Hinweis zum Gerätenamen:** `name_add_mac_suffix` ist `false`. Damit zeigt der Device Builder den Online-Status unter dem Hostnamen `barcode-scanner`. Ein Gerät, das noch mit MAC-Anhang läuft (z. B. `barcode-scanner-a1b2c3`), findet er unter dem neuen Namen erst nach dem ersten Flashen. Dafür einmal per USB flashen oder vorübergehend `wifi: use_address: <IP des Geräts>` setzen.

Anschließend den ESP in Home Assistant als ESPHome-Gerät hinzufügen. Eine Freigabe *„Dem Gerät erlauben, Home Assistant-Aktionen auszuführen“* ist für die Scans **nicht** nötig – der Scanner sendet ein Event, keine Aktion.

### 3. Home-Assistant-Integration installieren

Die Produktsuche und die Einkaufsliste kommen erst mit der Integration. Anleitung und aktuelle Version: **[SHYS Barcode Scanner](https://github.com/kallejoken/shys-barcode-scanner)**.

Kurzfassung:

1. *Einstellungen → Marketplace → oben rechts „Über Link hinzufügen“* → `https://github.com/kallejoken/shys-barcode-scanner` eintragen → *Hinzufügen*.
2. **SHYS Barcode Scanner** installieren und Home Assistant neu starten.
3. *Einstellungen → Geräte & Dienste → Integration hinzufügen → SHYS Barcode Scanner* → deine `todo`-Liste wählen (z. B. `todo.shopping_list`, Bring! oder Picnic).

Fertig – einfach scannen. Unbekannte Produkte lernst du im Seitenleisten-Panel **Barcode Scanner** an oder beantwortest die optionale Push-Nachricht direkt auf dem Handy.

## Konfigurierbare Substitutions

Alle Werte kommen aus `barcode.yaml`, `packages/display.yaml` und `packages/buzzer-*.yaml`:

| Name | Standard | Bedeutung |
|---|---|---|
| `name` | `barcode-scanner` | Hostname (ohne MAC-Anhang) |
| `friendly_name` | `Barcode Scanner` | Anzeigename in Home Assistant |
| `uart_tx_pin` | `GPIO9` | ESP-TX → GM60-RX |
| `uart_rx_pin` | `GPIO10` | ESP-RX ← GM60-TX |
| `uart_baud_rate` | `"9600"` | Manche GM60 stehen auf 57600 |
| `beeper_pin` | `GPIO16` | Buzzer (aktiv, passiv oder ungenutzt) |
| `i2c_sda_pin` / `i2c_scl_pin` | `GPIO21` / `GPIO22` | OLED, nur mit `packages/display.yaml` |
| `ssd1306_i2c_address` | `"0x3C"` | I2C-Adresse des OLED |
| `ean_debounce_ms` | `"3000"` | Gleichen Code innerhalb dieser Zeit nur einmal senden |
| `result_timeout_ms` | `"25000"` | Keine Antwort von Home Assistant → Fehler-Piep |
| `buzzer_gain` | `"50%"` | Nur passiver Buzzer: Lautstärke (PWM-Tastgrad) |

## Zusammenspiel mit Home Assistant

Erlaubt sind EAN/GTIN **und** eigene Codes (QR- oder EAN-Sticker für die lokale Datenbank): 4 bis 32 druckbare ASCII-Zeichen. Die EAN-Prüfziffer prüft die Integration, nicht der ESP.

1. Der Scanner schickt das Event `esphome.barcode_scanned` (`ean`, `device`).
2. Die Integration sucht zuerst in der lokalen Datenbank, sonst online, trägt das Produkt auf die Liste und antwortet über die Aktion `esphome.barcode_scanner_show_result` (allgemein `esphome.<name>_show_result`).
3. Der ESP zeigt das Ergebnis auf dem OLED (10 Sekunden) und piept:

| Ergebnis | Aktiver Buzzer | Passiver Buzzer |
|---|---|---|
| Gefunden / auf der Liste | kurzer Piep (120 ms) | kurzer aufsteigender Zweiklang |
| Unbekannt (bitte anlernen) | Doppel-Piep | zwei gleiche Töne |
| Fehler / keine Verbindung zu HA | langer Piep (600 ms) | tiefer, absteigender Ton |

In Home Assistant gibt es dazu den Knopf **Buzzer Test**.

Zum Testen ohne Scanner: *Entwicklerwerkzeuge → Aktionen* → `esphome.barcode_scanner_simulate_scan` mit z. B. `code: "4337256722261"`. Oder im Panel *Barcode Scanner → Test & Backup*.

Auf dem ESP stehen die Text-Sensoren **EAN**, **Brand**, **Product** und der Diagnose-Sensor **Scan Status** zur Verfügung.

## Datenquellen

Die Abfrage macht die [SHYS-Barcode-Scanner-Integration](https://github.com/kallejoken/shys-barcode-scanner), nicht der ESP:

- [Open Food Facts](https://world.openfoodfacts.org): Daten unter ODbL.
- [Produktdaten von EAN-Suche.net](https://ean-suche.net): Bei öffentlicher Nutzung ist ein Link als Quellenangabe Pflicht.
- [OpengtinDB](https://opengtindb.org): nur mit eigener QueryID ([Antrag](https://opengtindb.org/userid.php)).

---

\* Bei allen Amazon-Links handelt es sich um Affiliate-Links. Für jeden Kauf über die Links erhalte ich eine kleine Provision. Ihr bezahlt natürlich weiterhin denselben Preis wie sonst auch. Vielen Dank für eure Unterstützung!

<p align="center">
  <b>SmartHome yourself</b> · Dein smartes Zuhause. Einfach, sicher &amp; kreativ!
</p>
