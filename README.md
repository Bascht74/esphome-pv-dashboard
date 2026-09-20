# PV-Dashboard

Wandpanel für die eigene PV-Anlage: ein **Waveshare ESP32-P4-WIFI6-Touch-LCD-10.1**
(SKU 33150, 10,1" 800x1280 IPS, quer betrieben) mit einer ESPHome/LVGL-Oberfläche.
Das Repo enthält die komplette Gerätekonfiguration, dieselbe Oberfläche als
Simulator für den Rechner und den Generator für die Flussanimation.

Der Anlagenaufbau, den das Panel abbildet: ein Wechselrichter auf Volleinspeisung
mit zwei Dachflächen, zwei Hybrid-Wechselrichter mit je zwei Flächen, ein
Mini-Wechselrichter mit zwei Einzelmodulen, drei Speicher über Busbar an beiden
Hybriden, zwei Wallboxen, eine Wärmepumpe sowie Hauszähler und ein separater
Zähler für den Volleinspeise-Kreis. Fabrikate und Typen nennt der aktuelle Stand
nicht. Der Aufbau und die festgelegten Kennzahlen-Definitionen stehen in
`docs/01`.

**Die Beschriftungen im Repo sind Demo-Werte.** Jede anlagenabhängige
Beschriftung — Dachflächen, Wechselrichter, Speicher, Verbraucher, Zähler — und
die drei Tarife sind `substitutions`. Der Standard steht im jeweiligen Paket, die
eigene Anlage wird in `pv-dashboard.yaml` beschrieben und sticht ihn. Im Repo
stehen die Demo-Werte; eigene Angaben gehen nur mit, wenn diese Datei committet
wird. Zugangsdaten stehen ohnehin in `secrets.yaml` außerhalb des Repos.


## Was das Panel zeigt

Sieben Seiten über eine Menüleiste am unteren Rand, dazu eine Statusleiste mit
Uhr und eine Meldungszeile:

| Seite | Stand |
| --- | --- |
| Übersicht | Anlagenschema mit Flussanimation, rechte Kennzahlenspalte, Ringe und Tagesertrag |
| PV & Prognose | Platzhalter |
| Speicher | Tabelle mit Zellwerten, drei SoC-Ringe |
| Wallboxen | Platzhalter |
| Wärmepumpe | Platzhalter |
| Haus | Platzhalter |
| Meldungen | Liste aller Meldungen, neueste oben, Quittieren per Antippen |

Dazu zwei Overlays über der Oberfläche: Sprachassistent (`voice_panel`) und
Firmware-Update mit Fortschrittsbalken (`ota_panel`).

**Es sind noch keine echten Daten angebunden.** Die Oberfläche wird über feste
Skript-Schnittstellen gefüttert (`alert_push`, `storage_update`, `record_hour`).
Beispielwerte für Meldungen und Speicher gibt es nur im Screenshot-Lauf
(`shots_run` in `pv-dashboard-shots.yaml`). Die Demo-Leistungen der
Flussanimation stehen dagegen unter `#ifdef USE_HOST` und laufen auf der ganzen
host-Plattform — im Simulator wie im Screenshot-Lauf. **Auf dem Panel steht
alles auf 0:** `WATT[]` steht auf 37 Nullen, die Flussanimation ruht, solange
keine Sensoren angebunden sind. Was dafür noch fehlt, steht in `docs/06`.

## Inbetriebnahme: vom Clone zum eigenen Panel

Der kurze Weg für alle, die das Repo frisch geklont haben. Für den vollen Weg
braucht es das oben genannte Panel; ansehen lässt sich die Oberfläche auch ohne
Hardware (nächster Abschnitt).

1. **Klonen** und in den Projektordner wechseln — alle Befehle laufen von dort.
2. **ESPHome ab 2026.9.0** bereitstellen; die Konfiguration verlangt
   `min_version: 2026.9.0`. Der Rechner, der baut, braucht Internet: Die
   Schriften kommen über `gfonts://`.
3. **`secrets.yaml` anlegen.** `secrets.yaml.example` nennt die fünf Schlüssel,
   die die Konfiguration erwartet — kopieren und die eigenen Werte eintragen.
   Wer den ESPHome Device Builder benutzt, bekommt die Datei in aller Regel von
   ihm angelegt. `secrets.yaml` steht in `.gitignore` und gehört nicht ins Repo.
4. **`pv-dashboard.yaml` anpassen** — die einzige Datei zum Anfassen. Oben der
   Gerätename, darunter der Block „HIER BESCHREIBEN SIE IHRE ANLAGE“ mit jeder
   anlagenabhängigen Beschriftung und den drei Tarifen. Hinter jeder Zeile
   stehen die gemessene Breite des Demo-Werts und die verfügbare Breite; wer
   sie überschreitet, bekommt einen gekürzten oder umgebrochenen Text. Jede
   nicht angepasste Zeile bleibt auf dem Demo-Wert aus dem jeweiligen Paket.
5. **Prüfen** mit `esphome config pv-dashboard.yaml` — nie mit
   `--show-secrets`. Das ist die einzige lokale Kontrolle für die
   geräteeigenen Packages. (In dieser Arbeitsumgebung gehört der volle Pfad
   davor, siehe nächster Abschnitt.)
6. **Ansehen ohne Gerät:** Screenshot-Lauf starten und die Bilder umwandeln
   (nächster Abschnitt). Nach jeder Änderung an Beschriftungen oder Layout ist
   das Pflicht, siehe `docs/04`.
7. **Bauen und flashen** über den ESPHome Device Builder, siehe
   „Gerät bauen und flashen“.

Angebunden ist noch nichts: Bis Sensoren daran hängen, zeigt die Oberfläche auf
dem Panel Strichmuster und Nullen (`docs/06`).

## Schnellstart: Simulator und Screenshots

Beides braucht **ESPHome ab 2026.9.0** und läuft auf dem Rechner, ohne das Panel
und ohne Flash-Zyklus. Aufgerufen wird aus dem Projektordner:

```
esphome run pv-dashboard-shots.yaml
sips -s format png shots/*.bmp --out shots/
```

Der Lauf legt alle Seiten als **BMP** in `shots/` ab (steht in `.gitignore`);
der zweite Befehl macht daraus **PNG**, denn BMP lässt sich in einer
Assistenz-Sitzung nicht öffnen. Angesehen wird die PNG.

Zwei Dinge sind dabei nur die hiesige Arbeitsumgebung, kein Teil des Projekts:

- **Der volle Pfad statt `esphome`.** Auf dem Rechner des Nutzers gibt es kein
  `esphome` im PATH; dort steht vor jedem Befehl
  `~/.venvs/esphome-beta/bin/` — die Umgebung enthält ESPHome 2026.9.0, der
  Ordnername stammt noch aus der Beta-Zeit. Wer ein `esphome` im PATH hat, ruft
  einfach `esphome` auf. In `CLAUDE.md`, in den YAML-Köpfen und in `docs/03`
  steht durchgehend der volle Pfad, weil diese Texte für Sitzungen auf genau
  diesem Rechner geschrieben sind.
- **`sips`.** Das Werkzeug bringt nur macOS mit. Plattformunabhängig geht
  dasselbe mit Pillow, das in der ESPHome-Umgebung ohnehin steckt:

  ```
  python -c "from PIL import Image; import glob; [Image.open(f).save(f[:-4]+'.png') for f in glob.glob('shots/*.bmp')]"
  ```

  Beide Wege legen die PNG neben die BMP; Einzelheiten und die gemessenen
  Dateigrößen stehen in `docs/03`.

**Einzelheiten stehen in `docs/03`:** der Simulator `pv-dashboard-sim.yaml` mit
SDL-Fenster und **F12**, die Pillow-Variante der Umwandlung, das Vergrößern
eines Ausschnitts und die Dateinamen. Dort steht auch, dass `-sim` und `-shots`
getrennte Bauziele sind: Der erste Lauf eines Ziels ist ein Vollbuild und dauert
mehrere Minuten. Dabei kommen die Schriften aus dem Netz — IBM Plex Sans/Mono
über `gfonts://`, die Symbolschriften und die zwei Pfeil-Glyphen aus dem
Material-Design-Webfont. Der Build-Rechner braucht also Internet.

Die Rendering-Kontrolle nach jeder Layoutänderung ist Pflicht, siehe `docs/04`.

## Gerät bauen und flashen

Gebaut und geflasht wird über den **ESPHome Device Builder**, nicht lokal;
Updates laufen per OTA, das Panel zeigt dabei ein eigenes Fortschrittspanel.
Die Konfiguration verlangt `min_version: 2026.9.0`. Versionsstände und
Bauumgebungen stehen in `docs/05`, Board, Silizium und Toolchain in `docs/02`.

`.esphome/`, `.device-builder*`, `.receiver_peers.json` und `secrets.yaml` sind
per `.gitignore` ausgeschlossen. **Zugangsdaten** tragen davon `secrets.yaml`,
`.device-builder*`, `.receiver_peers.json` und `.esphome/storage/` — die
gehören weder in Ausgaben noch in Zitate, Werte werden ausschließlich über
`!secret` referenziert. Aus `.esphome/` sind die Ordnernamen unter
`.esphome/.remote_builds/venvs/` unbedenklich (ESPHome-Version, siehe
`docs/05`). Aus `.esphome/build/…/src/main.cpp` darf gezielt eine harmlose
Zeile abgelesen werden, etwa `line_height` einer Schrift (`docs/04`) — die
Datei als Ganzes aber nicht: Sie enthält WLAN-, AP- und OTA-Passwort sowie den
API-Schlüssel im Klartext.

## Dateien

| Datei | Inhalt |
| --- | --- |
| `pv-dashboard.yaml` | Die einzige Datei zum Anfassen: Gerätename, die Verweise auf `secrets.yaml` als `substitutions`, der Block „HIER BESCHREIBEN SIE IHRE ANLAGE“ mit allen Beschriftungen und den drei Tarifen, Liste der Packages; am Ende der auskommentierte Block, der dieselben Packages aus dem GitHub-Repo lädt |
| `secrets.yaml.example` | Dokumentiert, welche Schlüssel `secrets.yaml` enthalten muss — die echte Datei legt der Device Builder an |
| `.pv-dashboard_core.yaml` | Nur Gerät: SoC, PSRAM, LDO, Funkstrecke zum C6, WLAN, API, Logger, OTA, Bluetooth, Zeit und Diagnose, serielle Schnittstellen |
| `.pv-dashboard_utility.yaml` | Gemeinsam mit dem Simulator: Schriften (IBM Plex Sans/Mono) und die Bilder aus `images/`, dazu die Design-Tokens für Farben, Maße und Abstände — einzige Quelle dafür |
| `.pv-dashboard_ui.yaml` | Kern der Oberfläche: Tagesreihen, gemeinsame Skripte, `lvgl:`-Basis, Stile, Verläufe, `top_layer`; bindet die sieben Seiten ein |
| `.pv-dashboard_page_overview.yaml` | Seite 1 Übersicht: Anlagenschema, Kennzahlenspalte, erzeugter Flussanimations-Block |
| `.pv-dashboard_page_pv.yaml` | Seite 2 PV & Prognose — Platzhalter |
| `.pv-dashboard_page_battery.yaml` | Seite 3 Speicher: SoC-Ringe, Zelltabelle, `storage_update` |
| `.pv-dashboard_page_wallbox.yaml` | Seite 4 Wallboxen — Platzhalter |
| `.pv-dashboard_page_heatpump.yaml` | Seite 5 Wärmepumpe — Platzhalter |
| `.pv-dashboard_page_house.yaml` | Seite 6 Haus — Platzhalter |
| `.pv-dashboard_page_alerts.yaml` | Seite 7 Meldungen: Liste, Zähler, `alert_push` / `alert_ack` / `alert_refresh` |
| `.pv-dashboard_display.yaml` | Nur Gerät: I2C, Backlight, MIPI-DSI-Panel, GT911, Drehung |
| `.pv-dashboard_audio.yaml` | Nur Gerät: ES8311/ES7210, Voice Assistant, I2S-Halbduplex |
| `pv-dashboard-sim.yaml` | Simulator: `host:`-Plattform mit SDL-Fenster und SDL-Touchscreen |
| `pv-dashboard-shots.yaml` | Headless-Screenshots aller Seiten, bindet den Simulator als Package ein |
| `pv-dashboard-demo.yaml` | Prototyp: drei Bewegungsmuster für die Flussrichtung nebeneinander |
| `pv-dashboard-demo-a.yaml` | Prototyp: Kettenreaktion auf dem echten Schema |
| `pv-dashboard-demo-b.yaml` | Prototyp: zwei Kennlinien für die Kugelgeschwindigkeit im Vergleich |
| `tools/flow_animation.py` | Generator der Flussanimation; erzeugt den markierten Block in der Übersichtsseite |
| `images/` | `solar_panel.png` (Modulfeld) und `solar_module.png` (Einzelmodul) |
| `docs/` | Projektwissen, siehe unten |
| `CLAUDE.md` | Regeln für Assistenz-Sitzungen in diesem Repo |
| `LICENSE` | MIT-Lizenz |

Gerät und Simulator binden `utility` und `ui` gemeinsam ein: Eine Änderung an
der Oberfläche, an den Schriften oder an den Farben wirkt auf beiden Seiten.
Nur am Gerät hängen `display`, `audio` und `core`.

Die Oberfläche liegt in **acht** Dateien: dem Kern `.pv-dashboard_ui.yaml`
(951 Zeilen) und je einer Datei pro Seite. Der Kern bindet die Seiten über einen
eigenen `packages:`-Block ein — **diese Reihenfolge ist die Reihenfolge der
Seiten**. Jedes Skript liegt bei der Seite, die es benutzt; im Kern bleiben nur
`record_hour` und `update_clock`, die kein Seiten-Widget anfassen. Die größte
Einzeldatei ist damit `.pv-dashboard_page_overview.yaml` mit **1185 Zeilen, rund
83 kB** (Arbeitsstand 20.09.2026; die Zahl altert mit jeder Änderung), darin der
erzeugte Flussanimations-Block. Nicht am Stück lesen: `docs/03` hat unter
„Einstieg" die Dateitabelle mit Zeilennummern und den passenden grep-Mustern.
Diese Tabelle hier listet die Dateien des Repos; wie die Packages
zusammenspielen, steht ebenfalls in `docs/03`.

Die Packages liegen heute neben `pv-dashboard.yaml` und werden mit `!include`
eingebunden. Der Fernblock für dieselben Dateien aus diesem Repo steht am Ende
von `pv-dashboard.yaml` schon fertig da, aber auskommentiert: Getauscht wird
erst, wenn die Paketdateien im Repo liegen — und dann baut das Gerät aus dem
geschobenen Stand. Was das bedeutet, steht in `docs/03` unter „Später: Packages
aus dem GitHub-Repo“.

## Weiter lesen

- **[docs/01 — Anlage und Kennzahlen](docs/01-anlage-und-kennzahlen.md)** —
  die beiden Energiekreise, Strings und Dachflächen, Definitionen von Autarkie
  und Eigenverbrauchsquote, Tarife, Regeln für Werte und Einheiten. Beschrieben
  ist der Aufbau, nicht eine bestimmte Anlage.
- **[docs/02 — Hardware und Panel](docs/02-hardware-und-panel.md)** — Board und
  ECO2-Silizium, Takt, Toolchain, Display und Touch, C6-Co-Prozessor, BLE,
  Audio-Hardware, serielle Schnittstellen, Kamera, Bauen und Flashen.
- **[docs/03 — Aufbau des Dashboards](docs/03-dashboard-aufbau.md)** — Packages,
  Einstieg in Kern und Seitendateien, Seitenaufbau, Tokens und Stile, Verläufe,
  Skripte und ihre Schnittstellen, Flussanimation, Simulator und Screenshots
  samt Umwandlung der Bilder.
- **[docs/04 — LVGL-Checkliste](docs/04-lvgl-checkliste.md)** — die neun
  Pflichtprüfungen nach jeder Layoutänderung, von Kastenhöhen über Textüberlauf
  bis zum Rendering.
- **[docs/05 — Umstieg auf ESPHome 2026.9](docs/05-esphome-2026-9-umstieg.md)** —
  `min_version`, Device Builder und Bauumgebungen, OTA auf Noise in zwei
  Schritten, Audio-Halbduplex, der LVGL-`list`-Fehler.
- **[docs/06 — Offene Punkte und Pläne](docs/06-offene-punkte-und-plaene.md)** —
  geplante Detailseiten, echte Daten anbinden, BMS, Modbus-Regeln, Kamera, was
  sich nur am Gerät prüfen lässt.

Für Assistenz-Sitzungen in diesem Repo gelten zusätzlich die Regeln in
[CLAUDE.md](CLAUDE.md).

## Repo und Lizenz

`Bascht74/esphome-pv-dashboard` auf GitHub, Lizenz **MIT** (`LICENSE`).

Zugangsdaten enthält das Repo nicht: Sie stehen ausschließlich in der nicht
mitversionierten `secrets.yaml`. Die Beschriftungen und Tarife im Repo sind
Demo-Werte, die Widget-IDs heißen nach Stellung und Aufgabe, und die Dokumente
unter `docs/` beschreiben den Aufbau — Fabrikate, Typenbezeichnungen und die
echten Flächennamen stehen im aktuellen Stand nirgends mehr. Die Commit-Historie
trägt sie noch; wie sie vor dem Veröffentlichen bereinigt wird, steht in
`docs/06`.
