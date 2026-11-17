# barcode-scanner-for-esphome

![git-thumb](https://user-images.githubusercontent.com/705724/236686920-aefc9c7b-0104-46ff-8f4c-45027e6fa1a7.jpg)
[<img src="https://user-images.githubusercontent.com/705724/236687065-3938ffdd-424e-44a6-9bef-6b1bdbaff480.png" width="300px">](https://esphome.io/guides/made_for_esphome.html)
  
---

## ⚠️ Aktueller Status  
Teststand **2.3** für ESPHome 2026.10: kompiliert, Hardware-Test mit dem GM60 steht noch aus. Anleitung zum Testen (Einbinden aus GitHub, Einkaufsliste, Hardware) in **[README-TEST.md](README-TEST.md)**. Der Web-Installer und `main` des Originalprojekts sind davon unberührt.  

---
  
# 
  
Der Barcode-Scanner für ESPHome ist dafür gedacht, bequem Einträge auf der Einkaufsliste in Home Assistant einzutragen, ohne extra die App oder den Browser starten, und dort etwas eingeben zu müssen. Natürlich lassen sich die Daten auch für jeden anderen Einsatzzweck nutzen.
Hier sind eurer Fantasie keine Grenzen gesetzt.  
  
Zu jedem gescannten Produkt wird anhand der EAN versucht, Hersteller und Produktnamen zu ermitteln und über Sensoren zurückzuliefern. Die Abfrage erfolgt nacheinander über Open Food Facts (v3) und – falls dort kein brauchbarer Name ankommt – über [ean-suche.net](https://ean-suche.net). OpengtinDB ist nur noch ein optionaler dritter Schritt mit eigener QueryID.  
  
## Ein ausführliches Video zum Projekt findet Ihr auf YouTube:  
[<img src="https://user-images.githubusercontent.com/705724/215211264-53b242de-2256-463d-8e26-3b4dcc7451e5.png" width="400px">](https://youtu.be/08J4WN4iDI0)
  
#    
  
&nbsp;
  
## Datenquellen

Die Firmware fragt die Dienste **nacheinander** ab (eine HTTPS-Verbindung zur Zeit). Sobald ein brauchbarer Produktname vorliegt, werden die folgenden Stufen übersprungen. UPCitemdb ist bewusst nicht eingebaut.

#### 1. Open Food Facts (API v3, immer zuerst)

`GET https://world.openfoodfacts.org/api/v3/product/{ean}?fields=product_name,brands,code,product_type&product_type=all`

Kostenlos, ohne API-Key. Der Parameter `product_type=all` deckt auch die Schwesterdatenbanken (Beauty, Products, Pet Food) ab; Redirects werden gefolgt. Mit `fields=` bleibt die JSON-Antwort klein genug für den ESP32. Ein Treffer zählt nur bei v3-Status `success` und nicht-leerem `product_name`. Der User-Agent (Substitution `http_user_agent`) muss im Format `AppName/Version (Kontakt-E-Mail)` gesetzt sein – den Platzhalter vor dem produktiven Einsatz ersetzen.

Lizenz: Daten unter ODbL / Inhalte unter DbCL, Namensnennung nötig. Offizielles Limit: 15 Produkt-GETs/min je IP.

#### 2. EAN-Suche.net (kostenfreier Fallback)

`GET https://ean-suche.net/api/produkt/{ean}`

Anonyme Nutzung, typischerweise kleines JSON, Limit laut Anbieter 60 Anfragen/Stunde je IP (darüber HTTP 429). HTTP 404 bedeutet „EAN gültig, kein Name in der Datenbank“ und ist kein Gerätefehler. Es gibt **kein Herstellerfeld** – der Brand-Sensor bleibt in dieser Stufe leer.

[Produktdaten von EAN-Suche.net](https://ean-suche.net) – bei öffentlicher oder geschäftlicher Nutzung (Website, App, nachgebautes YouTube-Projekt) ist ein sichtbarer Link auf [ean-suche.net](https://ean-suche.net) als Quellenangabe vorgeschrieben. Rein privater Gebrauch ist laut Anbieterdokumentation ohne weitere Bedingungen erlaubt. Keinen gemeinsamen API-Key ins Repository legen.

#### 3. OpengtinDB (optional, nur mit eigener QueryID)

Nur wenn die Substitution `opengtindb_queryid` **nicht leer** ist. Die öffentliche Demo-ID `400000000` wird nicht mehr als Default verwendet (geteiltes Tageslimit, häufig Fehlercode 5). Eine eigene ID beantragt ihr unter https://opengtindb.org/userid.php und tragt sie in den Substitutions (oder in `secrets.yaml`) ein.
  
 
#    
## Benötigte Bauteile
**D1 Mini-ESP32:** https://amzn.to/3kLEt1s *  
**Barcode Scanner GM60:** https://amzn.to/3mq6vA2 *  
**Active Piezo Buzzer:** https://amzn.to/3Zps3eM *  
**0,96" OLED Display:** https://amzn.to/3kH2Ld7 *  
#    
  
## Platine
Die Platine könnt Ihr wie immer bei PCBWay bestellen.  
![image](https://github.com/SmartHome-yourself/barcode-scanner-for-esphome/assets/705724/773939a7-0420-4d92-8613-689225beb13c)
https://www.pcbway.com/project/shareproject/Barcode_scanner_made_for_ESPHome_bb9bba9a.html  
#  

  
## Installation
- ESP mit USB verbinden
- Installieren über Web-Installer
- WLAN Daten über Web-Installer setzen
- Gerät in Home Assistant adoptieren
- Generierten Code um Substitutions anpassen
- Über ESPHome flashen
- In Home Assistant als Integration hinzufügen (Einstellungen - Geräte)


Den Web-Installer incl. Anleitung findet Ihr auf der Projektseite unter:  
https://smarthomeyourself.de/home-assistant-einkaufsliste-ueber-barcode-scanner-fuellen-mit-esphome/
  
#    

### Mögliche Einstellungen (Substitutions)
Mit den folgenden optionalen Substitutions habt Ihr die Möglichkeit, die Standard-Konfiguration an Eure Bedürfnisse anzupassen.

```yaml
substitutions:
  name: "barcode-scanner"            # Hostname (ohne MAC-Anhang)
  friendly_name: "Barcode Scanner"
  uart_tx_pin: GPIO9                 # GM60 (ESP TX)
  uart_rx_pin: GPIO10                # GM60 (ESP RX)
  uart_baud_rate: "9600"             # manche GM60: 57600
  beeper_pin: GPIO16
  display_i2c_sda: GPIO21            # nur mit packages/display.yaml
  display_i2c_scl: GPIO22
  ssd1306_i2c_address: "0x3C"
  http_user_agent: "BarcodeScannerESPHome/2.3 (deine-mail@example.com)"
  shopping_list_entity: "todo.shopping_list"   # "" = nichts eintragen
  opengtindb_queryid: ""             # optional, eigene QueryID
  ean_debounce_ms: "3000"            # gleiche EAN so lange ignorieren
```

  
Nur gültige EAN/UPC/GTIN (Ziffern, Länge 8/12/13/14, korrekte Prüfziffer) lösen eine Abfrage aus – auch über die Aktion `request_ean`. Gefundene Produkte (sonst die EAN) trägt der Scanner per `todo.add_item` in `shopping_list_entity` ein, siehe [README-TEST.md](README-TEST.md). Ohne WLAN-Verbindung wird nicht angefragt. `dashboard_import` (Adopt im Device Builder) liegt optional in `packages/dashboard_import.yaml` bzw. `barcode_template.yaml`, nicht in der Kern-YAML.
  
  
&nbsp;    
   
   
## Dienste
#### esphome.[YOUR_DEVICENAME]_request_ean  
> Über diesen Dienst lässt sich die gleiche Anfrage auslösen, wie wenn ein Barcode über den Scanner gescannt wird.  
> Wird der Code von den APIs erkannt, werden Hersteller und Produktname genau wie beim echten scan über die Sensoren zurückgeliefert.  
>  
>**Parameter**
> | Parameter | Beschreibung |
> | --- | --- |
> | **eancode** | *EAN/GTIN nach der gesucht werden soll* |  
>  
> **Beispiel:**  
> ```
> action: esphome.barcode_scanner_request_ean
> data:
>   eancode: "40084060"
> ```


#### 
*\* Bei allen Amazon Links handelt es sich um Affiliate-Links. Heißt für jeden Kauf über die Links erhalte ich eine kleine Provision. Ihr bezahlt natürlich weiterhin den selben Preis wie sonst auch. 
Vielen Dank für eure Unterstützung!*
