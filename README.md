# PV-Dashboard

Wandpanel für die eigene PV-Anlage: ein **Waveshare ESP32-P4-WIFI6-Touch-LCD-10.1**
(SKU 33150, 10,1" 800x1280 IPS, quer betrieben) mit einer ESPHome/LVGL-Oberfläche.
Das Repo enthält die komplette Gerätekonfiguration, dieselbe Oberfläche als
Simulator für den Rechner und den Generator für die Flussanimation.

Der Anlagenaufbau, den das Panel abbildet: ein Wechselrichter auf Volleinspeisung
mit zwei Dachflächen, zwei Hybrid-Wechselrichter mit je zwei Flächen, ein
Mini-Wechselrichter mit zwei Einzelmodulen, drei Speicher über Busbar an beiden
Hybriden, zwei Wallboxen, eine Wärmepumpe sowie Hauszähler und ein separater
Zähler für den Volleinspeise-Kreis. Wechselrichter, Speicher und Flächen sind
neutral beschrieben; Wärmepumpe (Nilan Compact P) und Netzzähler (Shelly Pro 3EM)
sind bewusst benannt, weil die Seiten darauf zugeschnitten sind. Der Aufbau und die festgelegten Kennzahlen-Definitionen stehen in
`docs/01`.

**Die Beschriftungen im Repo sind Demo-Werte.** Jede anlagenabhängige
Beschriftung — Dachflächen, Wechselrichter, Speicher, Verbraucher, Zähler — sowie
die drei Tarife und die Netzanschlusswerte (`pv_kwp`, `feed_limit_pct`) sind `substitutions`. Der Standard steht im jeweiligen Paket, die
eigene Anlage wird in `.pv-dashboard_anlage.yaml` beschrieben und sticht ihn.
Diese Datei steht in `.gitignore` und bleibt auf dem Rechner; im Repo liegt nur
die Vorlage `.pv-dashboard_anlage.yaml.example` mit den Demo-Werten.
Zugangsdaten stehen ohnehin in `secrets.yaml` außerhalb des Repos.


## Was das Panel zeigt

Elf Seiten über eine Menüleiste am unteren Rand, dazu eine Statusleiste mit
Uhr und Systemsymbolen (WLAN, Home Assistant, Daten aktuell) und eine Meldungszeile:

| Seite | Stand |
| --- | --- |
| Übersicht | Anlagenschema mit Flussanimation, rechte Kennzahlenspalte, Ringe und Tagesertrag in Euro (auch als Sensoren für Home Assistant) |
| PV & Prognose | Leistung und Tageswert je Wechselrichter und Fläche, getrennt nach Volleinspeisung und Hausnetz, Status mit Fehlertext und Temperatur; Tagesverlauf Ist gegen Prognose mit vier Kennzahlen |
| Prognose | Solcast: heute P50 mit P10 bis P90, Rest, jetzt, Spitze; Halbstunden als Band mit Linie; sieben Tage mit Wetterbild |
| Wetter | DWD: jetzt mit Wind, Feuchte, Druck, Sonne; nächste 24 Stunden mit Temperaturkurve und Regen; sieben Tage; DWD-Warnung |
| Speicher | Tabelle mit Zellwerten, drei SoC-Ringe |
| Wallboxen | im Stil von evcc: je Wallbox Modus, Leistung mit Phasen, Geladen, Sonnenanteil, Ladedauer, Fahrzeug mit Ladestand, Ladeplan und Limit; Monatswerte |
| Wärmepumpe | grafisch im Aufbau des Nilan-Touch-Bedienteils (Compact P, Werte aus dem klassischen CTS700): außen, Raum, Feuchte, CO2, Warmwasser, Lüftungsstufe mit Ventilatoren; Betriebsart, Bypass, Kompressor, Zu-/Fortluft, Filter, Strom |
| Haus | im Stil von evcc: Energiefluss-Balken, Tabelle In / Out / Verbraucher, Verbrauch jetzt mit Herkunft, Verbrauch der letzten 24 Stunden |
| Netz | Hausanschluss mit Einspeisegrenze, Phasen L1 bis L3 (Shelly Pro 3EM), Zählerstände, Netzvorgaben (Börsenpreis, negative Preise, § 14a) |
| Statistik | Woche, Monat, Jahr: Erzeugung gegen Verbrauch, Autarkie, Eigenverbrauch, Ertrag |
| Meldungen | Bestehende Meldungen, neueste oben; gleiche zusammengefasst („×3 seit 08:12“), Zähler je Schweregrad als Filter, Quittieren per Antippen; oben die schwerste in ihrer Farbe |

Dazu drei Fenster über der Oberfläche: Sprachassistent (`voice_panel`),
Firmware-Update mit Fortschrittsbalken (`ota_panel`) und System (`sys_panel`,
Tipp auf die Symbole oben rechts) mit dem Alter der Werte je Quelle.

**Anbindung.** Die Oberfläche wird über feste Skript-Schnittstellen gefüttert
(`alert_push`, `alert_clear`, `storage_update`, `pv_update`, `pv_status`,
`money_update`, `fc_today`, `fc_slots`, `fc_day`, `wx_now`, `wx_hour`, `wx_day`,
`wx_warning`, `grid_update`, `grid_phase`, `grid_meter`, `grid_rules`,
`stats_update`, `wallbox_update`, `wallbox_month`, `heatpump_update`,
`heatpump_extra`, `house_flow`, `house_battery`, `house_loadpoint`, `house_update`,
`house_history`, `record_hour`, für das Anlagenschema `ov_roof` … `ov_totals`).
Am Gerät ruft sie seit dem 25.09.2026 der **Datenweg von Home Assistant**
(`.pv-dashboard_ha.yaml`, erzeugt von `tools/ha_bindings.py`): jeder Wert als
`homeassistant`-Sensor, gedrosselt auf einen Aufruf je Gruppe und Sekunde;
Vorhersagen, Solcast-Halbstunden und Statistik über Aktionen mit Antwort. Die
Entitäts-IDs sind Vorschläge und zeigen vorerst auf **Dummy-Entitäten**, die
`ha/pv_dashboard_dummy.yaml` in Home Assistant anlegt; eigene IDs kommen als
`ha_<name>` in `.pv-dashboard_anlage.yaml`. In Home Assistant muss beim Gerät
**„Allow the device to perform Home Assistant actions“** eingeschaltet sein.
Jedes Gerät hat eine **Referenz-Entität** (etwa Wallbox → Modus, Speicher →
Ladestand): Liefert sie keinen gültigen Wert, verschwindet die ganze Grafik des
Geräts, die übrigen bleiben an ihrem Platz. Jede andere Entität, die fehlt oder
nicht verfügbar ist, lässt nur ihren Wert leer. Was es nicht gibt, bekommt statt
einer ID `none` (auch `false`, `off`, `""`); zusätzliche Entitäten braucht es
nicht. Einzelheiten in `docs/03`
(„Datenweg von Home Assistant“), Offenes in `docs/06`.

Beispielwerte gibt es nur im Screenshot-Lauf (`shots_run` in
`pv-dashboard-shots.yaml`), der die Übersicht über dieselben Eingabeskripte
füllt und zum Schluss eine kleinere Anlage zeigt (`*_reduced`). Demo-Leistungen
der Flussanimation stehen unter `#ifdef USE_HOST` und greifen nur, solange keine
Werte da sind — also im Simulator. **Auf dem Panel steht ohne Daten alles auf
Strichen**, die Kugeln ruhen.

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
4. **Die eigene Anlage beschreiben.** `cp .pv-dashboard_anlage.yaml.example
   .pv-dashboard_anlage.yaml`, dann dort jede anlagenabhängige Beschriftung,
   die drei Tarife und die Netzanschlusswerte eintragen. Die Datei steht in `.gitignore`, ein
   `git add -A` nimmt sie nicht mit. Hinter jeder Zeile stehen die gemessene
   Breite des Demo-Werts und die verfügbare Breite; wer sie überschreitet,
   bekommt einen gekürzten oder umgebrochenen Text. Jede gelöschte Zeile
   fällt auf den Demo-Wert aus dem jeweiligen Paket zurück. In
   `pv-dashboard.yaml` steht oben nur noch der Gerätename; sie bindet die
   Datei ein und bricht ohne sie mit „Could not find file“ ab.
5. **Prüfen** mit `esphome config pv-dashboard.yaml` — nie mit
   `--show-secrets`. Das ist die einzige lokale Kontrolle für die
   geräteeigenen Packages. (In dieser Arbeitsumgebung gehört der volle Pfad
   davor, siehe nächster Abschnitt.)
6. **Ansehen ohne Gerät:** Screenshot-Lauf starten und die Bilder umwandeln
   (nächster Abschnitt). Nach jeder Änderung an Beschriftungen oder Layout ist
   das Pflicht, siehe `docs/04`.
7. **Bauen und flashen** über den ESPHome Device Builder, siehe
   „Gerät bauen und flashen“.

8. **Home Assistant vorbereiten:** beim ESPHome-Gerät die Option „Allow the
   device to perform Home Assistant actions“ einschalten; zum Testen ohne die
   Integrationen `ha/pv_dashboard_dummy.yaml` als Paket einbinden, sonst die
   abweichenden Entitäts-IDs in `.pv-dashboard_anlage.yaml` eintragen
   (`docs/03`, „Datenweg von Home Assistant“).

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
  dasselbe mit Pillow, das in der ESPHome-Umgebung ohnehin steckt — also mit dem
  `python` dieser Umgebung aufrufen (`~/.venvs/esphome-beta/bin/python`):

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

### Tests

```
~/.venvs/esphome-beta/bin/python -m unittest discover tests
~/.venvs/esphome-beta/bin/python tests/ha_probe.py
```

Der erste Befehl prüft in Sekunden die beiden Werkzeuge und den Sonderwert
„leer“ (−∞) als kleines C++-Programm mit `g++` (erzeugte Dateien aktuell, jede Zuordnung mit Standard und Referenz, `none`/`FALSE`/`""` über
ESPHomes eigene Substitution, jede Leitung der Flussanimation mit Kanal und
Sichtbarkeitsregel). Der zweite baut Simulator plus Datenweg mit einer API ohne
Schlüssel (`tests/ha-test.yaml`), startet ihn ohne Fenster und spielt über
`aioesphomeapi` ein Home Assistant nach: Gerät weg und wieder da über die
Referenz, einzelne Werte leer (auch in Summen), nirgends „inf“, Prognosen
und Statistik, Sammelmeldung beim Trennen. Einzelheiten in `docs/03`, Abschnitt „Tests“.

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
| `pv-dashboard.yaml` | Gerät: Gerätename, die Verweise auf `secrets.yaml` als `substitutions`, das Einbinden von `.pv-dashboard_anlage.yaml`, die Packages aus dem GitHub-Repo; am Ende auskommentiert der Rückfall auf die Dateien von der Platte |
| `.pv-dashboard_anlage.yaml.example` | Vorlage für die eigene Anlage: alle Beschriftungen, die drei Tarife und die Netzanschlusswerte mit Demo-Werten und Breiten. Die eigene Fassung `.pv-dashboard_anlage.yaml` steht in `.gitignore` |
| `secrets.yaml.example` | Dokumentiert, welche Schlüssel `secrets.yaml` enthalten muss — die echte Datei legt der Device Builder an |
| `.pv-dashboard_core.yaml` | Nur Gerät: SoC, PSRAM, LDO, Funkstrecke zum C6, WLAN, API, Logger, OTA, Bluetooth, Zeit und Diagnose, serielle Schnittstellen |
| `.pv-dashboard_ha.yaml` | Nur Gerät, **erzeugt** von `tools/ha_bindings.py`: Datenweg von Home Assistant — Sensoren mit Standard-IDs, Drosselung, Referenz-Entitäten je Gerät, Abrufe von Vorhersagen und Statistik |
| `.pv-dashboard_utility.yaml` | Gemeinsam mit dem Simulator: Schriften (IBM Plex Sans/Mono) und die Bilder aus `images/`, dazu die Design-Tokens für Farben, Maße und Abstände — einzige Quelle dafür |
| `.pv-dashboard_ui.yaml` | Kern der Oberfläche: Tagesreihen, gemeinsame Skripte, `lvgl:`-Basis, Stile, Verläufe, `top_layer`; bindet die elf Seiten ein |
| `.pv-dashboard_page_overview.yaml` | Seite 1 Übersicht: Anlagenschema, Kennzahlenspalte, `money_update`, Eingabeskripte `ov_*`, erzeugter Flussanimations-Block |
| `.pv-dashboard_page_pv.yaml` | Seite 2 PV & Prognose: Wechselrichter und Flächen je Kreis, Tagesverlauf mit Kennzahlen, `pv_status` / `pv_update` / `pv_redraw_curve` |
| `.pv-dashboard_page_forecast.yaml` | Seite 3 Prognose: Solcast heute, Halbstunden, sieben Tage, `fc_*` |
| `.pv-dashboard_page_weather.yaml` | Seite 4 Wetter: DWD jetzt, 24 Stunden, sieben Tage, Warnung, `wx_*` |
| `.pv-dashboard_page_battery.yaml` | Seite 5 Speicher: SoC-Ringe, Zelltabelle, `storage_update` |
| `.pv-dashboard_page_wallbox.yaml` | Seite 6 Wallboxen: Ladepunkt-Karten nach evcc mit bedienbarem Modus-Schalter, Monatskachel, `wallbox_update` / `wallbox_mode_set` / `wallbox_month` |
| `.pv-dashboard_page_heatpump.yaml` | Seite 7 Wärmepumpe: Startseite nach dem Nilan-Touch-Bedienteil, Haus aus Flächen, Information, Strom, `heatpump_update` / `heatpump_extra` |
| `.pv-dashboard_page_house.yaml` | Seite 8 Haus: Energiefluss nach evcc, Tabelle, Verbrauch jetzt und 24 Stunden, `house_*` |
| `.pv-dashboard_page_grid.yaml` | Seite 9 Netz: Hausanschluss, Phasen, Zähler, Netzvorgaben, `grid_*` |
| `.pv-dashboard_page_stats.yaml` | Seite 10 Statistik: Woche / Monat / Jahr, `stats_update` / `stats_show` |
| `.pv-dashboard_page_alerts.yaml` | Seite 11 Meldungen: Liste, Zähler mit Filter, `alert_push` / `alert_ack` / `alert_clear` / `alert_refresh` |
| `.pv-dashboard_display.yaml` | Nur Gerät: I2C, Backlight, MIPI-DSI-Panel, GT911, Drehung |
| `.pv-dashboard_audio.yaml` | Nur Gerät: ES8311/ES7210, Voice Assistant, I2S-Halbduplex |
| `pv-dashboard-sim.yaml` | Simulator: `host:`-Plattform mit SDL-Fenster und SDL-Touchscreen |
| `pv-dashboard-shots.yaml` | Headless-Screenshots aller Seiten, bindet den Simulator als Package ein |
| `pv-dashboard-demo.yaml` | Prototyp: drei Bewegungsmuster für die Flussrichtung nebeneinander |
| `pv-dashboard-demo-a.yaml` | Prototyp: Kettenreaktion auf dem echten Schema |
| `pv-dashboard-demo-b.yaml` | Prototyp: zwei Kennlinien für die Kugelgeschwindigkeit im Vergleich |
| `tools/flow_animation.py` | Generator der Flussanimation; erzeugt den markierten Block in der Übersichtsseite |
| `tools/ha_bindings.py` | Generator des Datenwegs: eine Zuordnungstabelle Wert → Entität → Skript; erzeugt `.pv-dashboard_ha.yaml` und `ha/pv_dashboard_dummy.yaml` |
| `tests/` | Tests: `test_ha_bindings.py`, `test_flow_animation.py`, `test_leer_cpp.py` (unittest), `ha_probe.py` mit `ha-test.yaml` (Panel gegen nachgebautes Home Assistant) |
| `ha/pv_dashboard_dummy.yaml` | Paket für Home Assistant, **erzeugt**: Ersatz-Entitäten unter den Standard-IDs (input_number, input_boolean, Templates, Wetter) |
| `images/` | `solar_panel.png` (Modulfeld) und `solar_module.png` (Einzelmodul); das Haus der Seite Wärmepumpe ist aus LVGL-Flächen gebaut |
| `patches/` | `pace_bms-check_uart_settings.patch` für die externe PACE-BMS-Komponente, Anleitung in `docs/06` |
| `docs/` | Projektwissen, siehe unten |
| `CLAUDE.md` | Regeln für Assistenz-Sitzungen in diesem Repo |
| `LICENSE` | MIT-Lizenz |

Gerät und Simulator binden `utility` und `ui` gemeinsam ein: Eine Änderung an
der Oberfläche, an den Schriften oder an den Farben wirkt auf beiden Seiten.
Nur am Gerät hängen `display`, `audio`, `core` und `ha`.

Die Oberfläche liegt in **zwölf** Dateien: dem Kern `.pv-dashboard_ui.yaml`
(1381 Zeilen) und je einer Datei pro Seite. Der Kern bindet die Seiten über einen
eigenen `packages:`-Block ein — **diese Reihenfolge ist die Reihenfolge der
Seiten**. Jedes Skript liegt bei der Seite, die es benutzt; im Kern bleiben nur
`sys_refresh`, `record_hour` und `update_clock`, die kein Seiten-Widget anfassen,
und `dev_apply`, das auf mehreren Seiten zugleich ausblendet, dazu die gemeinsamen
Formatierer `fmt_num`, `fmt_watt` und `fmt_power`. Die größte handgeschriebene
Einzeldatei ist damit `.pv-dashboard_page_overview.yaml` mit **1600 Zeilen**
(Arbeitsstand 25.09.2026; die Zahl altert mit jeder Änderung), darin der
erzeugte Flussanimations-Block. Nicht am Stück lesen: `docs/03` hat unter
„Einstieg" die Dateitabelle mit Zeilennummern und den passenden grep-Mustern.
Diese Tabelle hier listet die Dateien des Repos; wie die Packages
zusammenspielen, steht ebenfalls in `docs/03`.

`pv-dashboard.yaml` lädt die Packages **aus diesem Repo** (`ref: main`,
täglich aufgefrischt); die lokale Variante steht darunter auskommentiert als
Rückfall. Das heißt: Das Gerät baut aus dem geschobenen Stand, eine Änderung
wirkt dort erst nach `git push`. Simulator und Screenshots bleiben lokal und
zeigen den Arbeitsstand schon vorher — die übliche Reihenfolge ist also erst
Simulator, dann `push`, dann Gerät. Einzelheiten und die Folge für die Ausgabe
von `esphome config` stehen in `docs/03` unter „Packages aus dem GitHub-Repo“.

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
unter `docs/` beschreiben den Aufbau — Wechselrichter, Speicher und Flächen sind
neutral; Wärmepumpe (Nilan Compact P) und Netzzähler (Shelly Pro 3EM) sind bewusst
benannt, weil die Seiten darauf zugeschnitten sind. Ältere Commits tragen den
Stand vor der Generalisierung; das bleibt so (`docs/06`).
