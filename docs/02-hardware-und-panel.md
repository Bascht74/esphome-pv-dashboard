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
- Erwartete Adressen: GT911 0x5D oder 0x14, ES8311 0x18, ES7210 0x40.

Logger: `level: INFO`, `hardware_uart: UART0`; das Log geht über den
USB-UART-Port (Type-C, Beschriftung "UART").

## Funk: C6-Co-Prozessor

`esp32_hosted` mit `variant: ESP32C6` über einen 4-Bit-SDIO-Bus: Reset GPIO54,
CLK GPIO18, CMD GPIO19, D0–D3 GPIO14–GPIO17, `active_high: true`,
`use_psram: true` (SDIO-Puffer ins PSRAM statt in den internen RAM).

Die Werksfirmware des C6 war zu alt: Beim ersten Boot meldete ESPHome
`Co-processor not responding; BLE disabled.` — WLAN lief, die Abfrage der
Bluetooth-Firmwareversion blieb unbeantwortet. Dafür gibt es die Update-Entity
`"Co-Prozessor-Firmware"` (`platform: esp32_hosted`, `type: http`, Manifest
`.../esp-hosted-firmware/manifest/esp32c6.json`, `update_interval: 6h`, dazu
`http_request: verify_ssl: false`). Sie aktualisiert über die SDIO-Strecke,
ohne Ausbau, und wählt die höchste Version, die zur einkompilierten
esp_hosted-Bibliothek passt (seit 2026.8.0: 2.12.12). `on_update_available`
schiebt eine Info in die Meldungsliste.

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

## Audio-Hardware

- Wiedergabe: ES8311 (I2C 0x18), 48 kHz
- Aufnahme: ES7210 (I2C 0x40), Dual-Mic-Array mit Echo-Unterdrückung, 16 kHz
- Verstärker-Enable GPIO53 — sonst bleibt der Lautsprecher stumm. Die
  GPIO-Switch-Entität heißt `"Lautsprecher-Verstaerker"`.
- **Ein gemeinsamer I2S-Bus:** MCLK GPIO13, BCLK GPIO12, LRCLK GPIO10,
  DOUT GPIO9 (zum Codec), DIN GPIO11 (vom ADC)

Ein Bus für beide Richtungen heißt Halbduplex — der Konflikt ist auch
physikalisch, ein BCLK kann nicht gleichzeitig 48 kHz und 16 kHz takten. Wie
`.pv-dashboard_audio.yaml` das löst und welcher Test dafür aussteht: Dokument 05.

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
Bauumgebungen enthalten und was `min_version: 2026.9.0` dafür bedeutet, steht
in Dokument 05.

`.esphome/`, `.device-builder*`, `.receiver_peers.json` und `secrets.yaml` sind
per `.gitignore` aus dem Repo ausgeschlossen. **Zugangsdaten** tragen davon
`secrets.yaml`, `.device-builder*`, `.receiver_peers.json` und
`.esphome/storage/` — die gehören weder in Ausgaben noch in Zitate. Die übrigen
Inhalte von `.esphome/` sind reine Bauartefakte und dürfen gelesen und zitiert
werden; genau das verlangen Dokument 04 (`line_height` aus
`.esphome/build/pv-dashboard-sim/src/main.cpp`) und Dokument 05 (ESPHome-Version
aus den Ordnernamen unter `.esphome/.remote_builds/venvs/`).

---

Stand: 20.09.2026 (Konfigurationsfakten 12.09.2026 oder älter; Versionsstände
siehe Dokument 05). Geprüfter Commit: `c6a432f` (12.09.2026).
