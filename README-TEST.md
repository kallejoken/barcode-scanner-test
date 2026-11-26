# Barcode-Scanner für ESPHome – Testrepo

> **Hinweis:** Ab v3.0 (Branch `feat/hacs-v3`) gilt [README-HACS.md](README-HACS.md). Diese Datei beschreibt den alten Stand 2.3.
>
> **Teststand 2.3.** Basis ist das Projekt von SmartHome-yourself
> (https://github.com/SmartHome-yourself/barcode-scanner-for-esphome), angepasst an
> ESPHome 2026.10. Kompiliert sauber, Hardware-Test mit neuem GM60 steht noch aus.

## Was macht das?

GM60-Scanner liest eine EAN → ESP32 prüft die Prüfziffer → sucht den Produktnamen:

1. **Open Food Facts** (v3, deutscher Name bevorzugt)
2. **ean-suche.net**, wenn 1 nichts liefert (kostenlos, ca. 60 Abfragen/Stunde)
3. **OpengtinDB**, nur mit eigener QueryID (optional)

Ergebnis: Sensoren `EAN`, `Brand`, `Product` in Home Assistant und ein Eintrag auf der
To-do-Liste (`todo.shopping_list`). Kurzer Piep = gefunden, langer Piep = nichts
gefunden. Dann wird die EAN selbst eingetragen. „Produkt nicht gefunden“ ist kein
Fehler und erscheint im Log nur als Info.

## Hardware

| Teil | Anschluss |
|---|---|
| ESP32 D1 Mini (`wemos_d1_mini32`) | – |
| GM60 Barcode-Scanner | UART: ESP TX = GPIO9, ESP RX = GPIO10, 9600 Baud (manche Module 57600) |
| Aktiver Piezo-Buzzer | GPIO16 |
| OLED SSD1306 128×64 (optional) | I2C 0x3C, SDA = GPIO21, SCL = GPIO22 |

## Dateien

| Datei | Inhalt |
|---|---|
| `barcode.yaml` | Alles Nötige (ohne Display) |
| `packages/display.yaml` | Optionales OLED |
| `barcode-with-display.yaml` | `barcode.yaml` plus Display (lokal) |
| `barcode_template.yaml` | Vorlage mit lokalen Dateien |
| `packages/dashboard_import.yaml` | Nur für die Vorlage (Device-Builder-Adopt) |

## Einbinden in ESPHome aus diesem privaten Repo

Weil das Repo privat ist, braucht ESPHome Zugangsdaten zum Herunterladen.
ESPHome-Remote-Packages unterstützen dafür `username` und `password`
(Doku: https://esphome.io/components/packages/). Als Passwort nimmt man einen
**GitHub-Token**, nicht das Konto-Passwort:

1. GitHub → Settings → Developer settings → *Fine-grained tokens* → *Generate new token*
2. Repository access: *Only select repositories* → `barcode-scanner-test`
3. Permissions: *Contents: Read-only*. Mehr ist nicht nötig.
4. Token in die `secrets.yaml` von ESPHome eintragen:

```yaml
wifi_ssid: "MeinWLAN"
wifi_password: "geheim"
github_token: "github_pat_..."
```

Geräte-YAML im ESPHome Device Builder (z. B. `barcode-scanner.yaml`):

```yaml
substitutions:
  name: "barcode-scanner"
  friendly_name: "Barcode Scanner"
  http_user_agent: "BarcodeScannerESPHome/2.3 (deine-mail@example.com)"
  shopping_list_entity: "todo.shopping_list"
  # uart_baud_rate: "57600"   # falls der GM60 nicht auf 9600 steht

packages:
  barcode:
    url: https://github.com/kallejoken/barcode-scanner-test
    ref: main
    username: kallejoken
    password: !secret github_token
    files:
      - barcode.yaml
      # - packages/display.yaml   # mit OLED einkommentieren
    refresh: 1h

wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password
```

Alles unter `substitutions` überschreibt die Vorgaben aus `barcode.yaml`.
Mit `refresh: 1h` holt ESPHome Änderungen aus dem Repo spätestens nach einer Stunde.

**Hinweis zum Gerätenamen:** `name_add_mac_suffix` ist jetzt `false`. Damit zeigt der
Device Builder den Online-Status. Ein Gerät, das noch mit MAC-Anhang läuft
(z. B. `barcode-scanner-a1b2c3`), findet er unter dem neuen Namen erst nach dem
ersten Flashen. Dafür einmal per USB flashen oder vorübergehend
`wifi: use_address: <IP des Geräts>` setzen.

## Einkaufsliste in Home Assistant

Der Scanner trägt selbst per `todo.add_item` ein. Text: „Marke Produkt“, ohne
Treffer die EAN. Damit das klappt, **einmal** in Home Assistant:

*Einstellungen → Geräte & Dienste → ESPHome → Barcode Scanner → Konfigurieren →
„Dem Gerät erlauben, Home Assistant-Aktionen auszuführen“* aktivieren.

Eine andere Liste stellt man über `shopping_list_entity` ein, z. B. `todo.einkauf`.
Mit `shopping_list_entity: ""` trägt der Scanner nichts ein. Dann kann man es auch
per Automation machen:

```yaml
automation:
  - alias: "Barcode auf Einkaufsliste"
    triggers:
      - trigger: state
        entity_id: sensor.barcode_scanner_product
    conditions:
      - condition: template
        value_template: "{{ trigger.to_state.state not in ['', 'unknown', 'unavailable'] }}"
    actions:
      - action: todo.add_item
        target:
          entity_id: todo.shopping_list
        data:
          item: "{{ trigger.to_state.state }}"
```

(Diese Automation trägt nur gefundene Produkte ein, keine reinen EANs.)

## Testen ohne Scanner

In Home Assistant unter *Entwicklerwerkzeuge → Aktionen* die Aktion
`esphome.barcode_scanner_request_ean` mit `eancode: "4000417025005"` ausführen.
Im Log erscheint dann z. B. `Gefunden: Ritter Sport / Marzipan`.

## Datenquellen und Lizenz

- Open Food Facts: Daten unter ODbL. Bitte einen User-Agent mit eigener Mail setzen.
- [Produktdaten von EAN-Suche.net](https://ean-suche.net): Bei öffentlicher Nutzung
  ist ein Link als Quellenangabe Pflicht.
- OpengtinDB: nur mit eigener QueryID (https://opengtindb.org/userid.php).
