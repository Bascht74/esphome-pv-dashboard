# 02 — Hardware und Panel

Werte aus `pv-dashboard.yaml` und den `.pv-dashboard_*.yaml`-Paketen.

## Das Gerät

Waveshare ESP32-P4-WIFI6-Touch-LCD-10.1, **SKU 33150** ("X"-Serie):

- SoC ESP32-P4 (RISC-V Dual-Core), **kein eigenes Funkmodul**
- Funk: ESP32-C6-MINI-1U als Co-Prozessor über SDIO (`esp32_hosted`)
- Display 10,1" 800x1280 IPS, MIPI-DSI 2-Lane, JD9365 · Touch GT911 an I2C
- PSRAM 32 MB im Chip-Package (HEX-Mode) · Flash 32 MB NOR

## Silizium, Board und Takt

Der Chip ist **ECO2**, kein Serien-Silizium; das Boot-ROM meldet sich mit
`ESP-ROM:esp32p4-eco2-20240710` (geprüft beim ersten Flashen am 31.07.2026).

Mit `board: esp32-p4_r3-evboard` stürzt bereits der Bootloader ab: `entry
0x4ffab2ca`, gefolgt von `Guru Meditation Error: Core 0 panic'ed (Illegal
instruction)` mit dem PC auf dieser Adresse — Dauerneustart, die App wird nie
erreicht. Deshalb steht im `esp32:`-Block:

- `board: esp32-p4-evboard`, `variant: esp32p4`
- `engineering_sample: true` — Pflicht für Silizium vor Rev. 3.00
- `flash_size: 32MB`, `cpu_frequency: 360MHz`

**360 MHz bleibt.** ESPHome-Code (`esp32/__init__.py`) und Doku begrenzen
Engineering-Samples auf 360 MHz; die Validierung lehnt 400 MHz nicht ab, sie
warnt nur (esphome/esphome#13425). Entscheidung des Nutzers am 11.09.2026: gar
nicht erst probieren. Bei Boardtausch diese Werte gegen die neue Revision
prüfen.

## Toolchain und ESP-IDF

- `toolchain: esp-idf` — native ESP-IDF-Toolchain (CMake, idf.py), kein
  PlatformIO. `platformio` ist abgekündigt und fällt in 2027.2.0 weg.
- `framework.version: 6.0.2` — neueste stabile 6.x; von 6.1 existiert bisher
  nur v6.1-beta1. ESPHome-"recommended" ist weiterhin 5.5.5: bei
  Build-Problemen der schnellste Gegentest.
- `enable_idf_experimental_features: true` — Pflicht für 32 MB Flash zusammen
  mit OTA. Die Warnung "Using experimental features in ESP-IDF ..." ist damit
  gewollt, ebenso die zur nicht empfohlenen Framework-Version.

## PSRAM, LDO, Display

- `psram: mode: hex, speed: 200MHz`. Ohne PSRAM kein MIPI-DSI-Framebuffer.
- `esp_ldo` Kanal 3 auf 2,5 V versorgt die MIPI-DSI-PHY (VDD_MIPI_DPHY),
  Pflicht-Abhängigkeit von `mipi_dsi`.
- `display: platform: mipi_dsi`, `model: WAVESHARE-10.1-DSI-TOUCH-A` (Preset
  mit Timings, Lane-Bitrate 1,5 Gbps, Init-Sequenz), `reset_pin: GPIO27`,
  `update_interval: never`, `auto_clear_enabled: false`.
- **Kein `rotation` im `display:`-Block** — zusammen mit LVGL lehnt ESPHome das
  ab. Die Drehung (`rotation: 90`) steht im `lvgl:`-Block von
  `.pv-dashboard_display.yaml`, also im geräteeigenen Package: So
  dreht sie das Panel mit, ohne den Simulator zu erreichen. Der Compiler meldet
  dazu "LVGL will use software rotation (PPA accelerated)".
- Backlight: GPIO26 (LEDC, kalibriert).

## I2C, Touch und Log

`i2c_bus`: SDA GPIO7, SCL GPIO8, 400 kHz, `scan: true`. Der GT911 hängt daran
(`update_interval: 50ms`), INT und RST sind nicht herausgeführt; jede
Berührung löst `display_wake` aus.

Zur I2C-Frage vom ersten Boot (31.07.2026, am 11.09.2026 per Quelltext geklärt):

- `Performing bus recovery` ist eine **normale INFO-Zeile**, die
  `IDFI2CBus::setup()` bei jedem Boot schreibt. Kein Fehler.
- Ein Busfehler ist erst belegt bei `Recovery failed: SCL/SDA is held LOW`.
- Die Scan-Ergebnisse kommen aus `dump_config()` per `ESP_LOGCONFIG` und fehlen
  bei `level: INFO` immer. Der YAML-Kommentar nennt `CONFIG` (oder `DEBUG`), die
  Quelltextprüfung vom 11.09.2026 nennt `DEBUG`: zur Kontrolle einmal mit
  **globalem** Level DEBUG flashen, Pro-Tag-Level heben das nicht an.
- Erwartete Adressen: GT911 0x5D oder 0x14, dazu die verbauten, aber seit
  10.10.2026 ungenutzten Audio-Chips ES8311 0x18 und ES7210 0x40.

Logger: `level: INFO`, `hardware_uart: UART0`; das Log geht über den
USB-UART-Port (Type-C, Beschriftung "UART").

## Funk: C6-Co-Prozessor

`esp32_hosted` mit `variant: ESP32C6` über einen 4-Bit-SDIO-Bus: Reset GPIO54,
CLK GPIO18, CMD GPIO19, D0–D3 GPIO14–GPIO17,
`use_psram: true` (SDIO-Puffer ins PSRAM statt in den internen RAM). Kein
`active_high` mehr: ESPHome 2026.11 kündigt die Option ab und ignoriert sie
(`true` warnt, `false` ist ein Fehler, mit 2027.5.0 fällt sie weg).

Die Werksfirmware des C6 war zu alt: Beim ersten Boot meldete ESPHome
`Co-processor not responding; BLE disabled.` — WLAN lief, die Abfrage der
Bluetooth-Firmwareversion blieb unbeantwortet. Dafür gibt es die Update-Entity
`"Co-Prozessor-Firmware"` (`platform: esp32_hosted`, `type: http`, Manifest
`.../esp-hosted-firmware/manifest/esp32c6.json`, `update_interval: 6h`, dazu
`http_request: verify_ssl: false`). Sie aktualisiert über die SDIO-Strecke,
ohne Ausbau, und wählt die höchste Version, die zur einkompilierten
esp_hosted-Bibliothek passt (ESPHome 2026.11: 3.1.0). `on_update_available`
schiebt eine Info in die Meldungsliste.

**Automatisch installieren (seit 10.10.2026, Wunsch des Nutzers).**
`on_update_available` startet danach das Skript `c6_auto_update`
(`.pv-dashboard_core.yaml`, Update-Entity `id: c6_update`). Es wartet, bis
WLAN und API verbunden sind und das Gerät mindestens 2 min läuft (höchstens
30 min), prüft `update.is_available` und ruft `update.perform` auf. Im Quelltext
von ESPHome 2026.11 nachgelesen (`esp32_hosted/update/esp32_hosted_update.cpp`,
`perform()`; so seit 2026.11.0b2,
[esphome/esphome#22306](https://github.com/esphome/esphome/pull/22306)):

- `perform()` blockiert einen `loop()`-Durchlauf: Firmware laden und über SDIO
  auf den C6 schreiben, der C6 prüft sie. Solange steht die Oberfläche.
- `force` ist nicht nötig — ohne `force` installiert es bei Zustand
  `AVAILABLE`, und genau den setzt die Prüfung.
- Erfolg: Zustand `NO_UPDATE`. Eine Sekunde später beendet der **P4** seine
  Komponenten (`App.safe_shutdown()`), schaltet den C6 auf die neue Firmware
  um (`esp_hosted_slave_ota_activate()`, der C6 startet 500 ms später neu) und
  startet selbst neu. Die Meldungsliste liegt nur im RAM und ist danach leer;
  die nächste Prüfung findet die neue Version und meldet nichts mehr.
- Fehler beim Laden, Schreiben oder Prüfen: Zustand bleibt `AVAILABLE`, kein
  Neustart; dann kommt die Warnung „Firmware-Update fehlgeschlagen“ in die
  Meldungen. Erneut versucht wird erst nach dem nächsten Neustart, weil
  `on_update_available` nur beim Wechsel auf „verfügbar“ auslöst.
- Fehler beim Umschalten: ESPHome schreibt ihn nur ins Log („Failed to
  activate OTA“), der P4 startet trotzdem neu, und der C6 läuft weiter mit der
  alten Firmware. Die Prüfung meldet das Update danach wieder als verfügbar.
  Damit daraus keine Schleife aus Einspielen und Neustart wird, merkt sich das
  Global `c6_auto_done` die zuletzt fehlerfrei geschriebene Version über den
  Neustart (`restore_value`; der P4 sichert sie beim Beenden der Komponenten,
  bevor er den C6 umschaltet). Ist genau sie wieder verfügbar, kommt die
  Warnung „Firmware-Update fehlgeschlagen“ statt eines neuen Versuchs. Von Hand
  (Knopf in Home Assistant) lässt sie sich weiter einspielen.

Im Log steht jeder Schritt („Co-Prozessor-Update: installiere …“, „…
erfolgreich, Neustart in 1 s“, „… fehlgeschlagen“ bzw. „… war schon
geschrieben …“), dazu die Zeilen von `esp32_hosted.update`. Am Gerät erprobt
ist der Ablauf noch nicht.

## Bluetooth LE

BLE läuft über denselben C6; ESPHome erkennt `esp32_hosted` und schaltet den
HCI-Controller über SDIO frei (`CONFIG_ESP_HOSTED_ENABLE_BT_BLUEDROID` /
`..._BLUEDROID_HCI_VHCI`). Der C6 kann Bluetooth 5 / BLE inklusive Coded PHY.

Scan in `.pv-dashboard_core.yaml` (Abschnitt „Bluetooth LE“): `interval: 320ms`, `window: 300ms`,
`connection_scan_window: 30ms`, `active: true`; `bluetooth_proxy: active: true`.
**Warum gesenkt:** WLAN und BLE teilen sich das Funkteil. Ein Dauerscan
(Fenster = Intervall, früher 1100/1100 ms) lässt WLAN keine Luft, ab 2026.9
warnt ESPHome davor — die Lücke gehört WLAN. Hält der Proxy GATT-Verbindungen,
scannt er nur noch 30 ms pro Intervall. Bleibt WLAN instabil: zuerst
`active: false` probieren.

## Audio-Hardware (ungenutzt)

Seit dem 10.10.2026 ist Audio entfernt (Wunsch des Nutzers): kein Wakeword,
kein Mikrofon, kein Lautsprecher, kein Sprachassistent. Im ersten Log am Gerät
meldete `micro_wake_word` mehrmals je Sekunde „Not enough free bytes in ring
buffer“ und kostete Rechenzeit, die der Oberfläche fehlte. Das Paket
`.pv-dashboard_audio.yaml` ist gelöscht; die Chips bleiben verbaut:

- Wiedergabe: ES8311 (I2C 0x18), Aufnahme: ES7210 (I2C 0x40)
- Verstärker-Enable GPIO53 — ohne Konfiguration nicht angesteuert
- I2S-Bus: MCLK GPIO13, BCLK GPIO12, LRCLK GPIO10, DOUT GPIO9, DIN GPIO11

Wer Audio zurückhaben will, findet das Paket samt Halbduplex-Lösung im
Versionsverlauf des Repos (letzter Stand vor dem 10.10.2026, Dokument 05).

## Serielle Schnittstellen über USB

Statt Pegelwandler auf den 40-Pin-Header zu löten, hängt ein Mehrkanal-
Converter am USB-OTG-Type-C-Port — das kostet keinen GPIO. Gerät: Waveshare
"USB TO 4CH Serial Converter", SKU 25790, ASIN B0CM68TPNR, Chip FT4232HL,
VID 0x0403 / PID 0x6011; am Converter sitzt USB Typ B, nötig ist also ein
Kabel USB-B auf USB-C.

**Die Kanäle sind positionsbasiert**: Der Index ergibt sich aus der Reihenfolge
unter `channels:` — deshalb sind auch die ungenutzten Ports A und B deklariert.
`usb_host: enable_hubs: false`; ESPHome ordnet USB-Geräte nur über VID/PID zu.

| Port | Leitung | Verwendung |
|---|---|---|
| A | TTL | ungenutzt (`uart_port_a`, 9600) |
| B | TTL / RS485 | ungenutzt (`uart_port_b`, 9600) |
| C | RS485 / RS422, isoliert | `uart_bms_rs485`, 9600 8N1 — RS485 zur Batterie |
| D | RS232 / RS485, isoliert | `uart_bms_rs232`, 115200 8N1 — RS232 zur Batterie |

Port C und D sind galvanisch getrennt; die Masse eines 16S-LiFePO4-Packs liegt
auf anderem Potential als das Panel. Sitzt das Panel am Ende des RS485-Strangs,
den 120R-Abschluss am Converter per Jumper zuschalten (ab Werk offen).
`pace_bms` — die externe Komponente für PACE-kompatible BMS — und `modbus` liegen
im Paket auskommentiert bereit; die Verdrahtung zum BMS, die Protokollfrage und der
Stand der Anbindung stehen in Dokument 06.

## Kamera

Vorgesehen ist die MIPI-CSI-Kamera **OV5647** (5 MP, 15-Pin-1,0-mm-CSI-
Anschluss, 2-Lane) am CSI-Port des Panels. Im Repo ist sie noch nicht
konfiguriert; sie ist durch einen offenen ESPHome-PR blockiert. Stand,
Einschränkungen und die geplante Konfiguration stehen in Dokument 06.

## Bauen und Flashen

Gebaut und geflasht wird über den **ESPHome Device Builder**, der dieses
Verzeichnis verwaltet (Kopf der `.gitignore`) und remote baut — nicht lokal;
Updates laufen per OTA, mit eigenem Fortschrittspanel. Welche Versionen die
Bauumgebungen enthalten und was `min_version: 2026.11.0` dafür bedeutet, steht
in Dokument 05.

`.esphome/`, `.device-builder*`, `.receiver_peers.json` und `secrets.yaml` sind
per `.gitignore` aus dem Repo ausgeschlossen. **Zugangsdaten** tragen davon
`secrets.yaml`, `.device-builder*`, `.receiver_peers.json` und
`.esphome/storage/` — die gehören weder in Ausgaben noch in Zitate. Aus dem
übrigen `.esphome/` sind die Ordnernamen unter `.esphome/.remote_builds/venvs/`
unbedenklich (ESPHome-Version, Dokument 05). Aus `.esphome/build/…/src/main.cpp`
darf nur eine einzelne, nachweislich harmlose Zeile gelesen werden, etwa
`line_height` einer Schrift (Dokument 04) — **nie** die Datei am Stück: Sie
enthält WLAN-, AP- und OTA-Passwort sowie den API-Schlüssel im Klartext.

---

Stand: 10.11.2026 (`active_high` entfernt, esp_hosted 3.1.0, Ablauf des
C6-Updates nach 2026.11 samt Sperre `c6_auto_done`, `min_version` 2026.11.0);
davor 20.09.2026 (Konfigurationsfakten 12.09.2026 oder älter;
Versionsstände siehe Dokument 05). Geprüfter Commit: `c6a432f` (12.09.2026).
