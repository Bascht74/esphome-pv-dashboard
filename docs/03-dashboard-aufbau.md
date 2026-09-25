# 03 — Aufbau des Dashboards

## Dateien und Packages

`pv-dashboard.yaml` (Gerät) und `pv-dashboard-sim.yaml` (Simulator: `host:` plus
SDL-Fenster 1280 x 800) binden dieselben zwei gemeinsamen Packages ein:

- `.pv-dashboard_utility.yaml` — in zwei Abschnitten: Plex Sans / Mono,
  Symbolschriften und die Bilder aus `images/`, dann Farben, Maße, `alert_max`,
  `idle_timeout`. Die drei Tarife standen bis zum 20.09.2026 hier und gehören
  jetzt zu den Anlagen-Einstellungen (Dokument 01)
- `.pv-dashboard_ui.yaml` — der Kern der Oberfläche: Tagesreihen, gemeinsame
  Skripte, `lvgl:`-Basis, Stile, Verläufe, `top_layer`. Die elf Seiten hängen
  als eigene Packages daran (`.pv-dashboard_page_*.yaml`)

Nur am Gerät: `.pv-dashboard_display.yaml` (I2C, Backlight, DSI-Panel, GT911;
eigener `lvgl:`-Block mit `rotation: 90`), `.pv-dashboard_audio.yaml`
(Audio/Voice) und `.pv-dashboard_core.yaml` — darin alles, was aus dem Panel ein
Gerät macht: SoC, PSRAM, LDO, Funkstrecke zum C6, WLAN, API, Logger, OTA,
Bluetooth, `dash_time` und die Diagnose-Entities, RS485/RS232. Seit dem
25.09.2026 dazu `.pv-dashboard_ha.yaml`, der Datenweg von Home Assistant
(Abschnitt „Datenweg“ unten); erzeugt von `tools/ha_bindings.py`.

Audio sollte nach der Planung als dritter Abschnitt in
`.pv-dashboard_utility.yaml` liegen. Das geht nicht: `i2s_audio`,
`audio_dac` und `micro_wake_word` verlangen die Plattform `esp32`, der
Simulator läuft auf `host`. Bindet er das Package ein, bricht schon
`esphome config` mit „Component i2s_audio requires component esp32“ ab
(geprüft mit 2026.9.0, 20.09.2026). Audio bleibt deshalb ein eigenes Package,
das nur das Gerät einbindet.

`pv-dashboard.yaml` selbst enthält nur noch den `esphome:`-Block, Gerätename und
Zugangsdaten als `substitutions` und die Package-Liste. Die eigene Anlage — jede
anlagenabhängige Beschriftung und die drei Tarife — steht seit dem 23.09.2026 in
`.pv-dashboard_anlage.yaml`, die `pv-dashboard.yaml` mit
`<<: !include .pv-dashboard_anlage.yaml` in ihre `substitutions` einfügt. Diese
Datei steht in `.gitignore` und bleibt auf dem Rechner, im Repo liegt die Vorlage
`.pv-dashboard_anlage.yaml.example`; welche Werte das sind und wie breit sie sein
dürfen, steht in Dokument 01. Beim Einrichten angefasst werden damit diese zwei
Dateien. Der führende Punkt hält die Datei aus der Geräteliste des Device
Builders heraus (`filter_yaml_files` überspringt versteckte Dateien, nachgelesen
in 2026.9.0). **`!secret` steht ausschließlich in `pv-dashboard.yaml`**; die
Packages arbeiten mit `${…}` und sind damit frei von Geheimnissen. Das ist die
Voraussetzung dafür, sie aus dem GitHub-Repo nachzuladen, während
`secrets.yaml` und die eigene Anlage auf dem Rechner bleiben. Welche Schlüssel `secrets.yaml` braucht, zeigt `secrets.yaml.example`;
die echte Datei legt in der Regel der Device Builder an. Im Repo steht von den Werten nichts, die Packages sehen nur `${…}`.
Bei der **Ausgabe** gibt es dagegen einen Unterschied: Mit lokal eingebundenen
Packages zeigen `esphome config` und der Config-Kommentar in `main.cpp` nur
`!secret '<name>'`; mit dem Bezug aus dem Repo (nächster Abschnitt) zeigt
`esphome config` die aufgelösten Werte — im Terminal unsichtbar gestellt, in
einer umgeleiteten Datei aber lesbar. Die Ausgabe deshalb nicht in eine Datei
schreiben und nicht weitergeben (gemessen mit 2026.9.0, 20.09.2026).

### Packages aus dem GitHub-Repo (aktiv seit 20.09.2026)

`pv-dashboard.yaml` lädt die Packages aus diesem Repo statt von der Platte.
Der Block steht direkt unter `packages:`; die lokale Variante liegt darunter
auskommentiert als Rückfall:

```yaml
packages:
  dashboard:
    url: https://github.com/Bascht74/esphome-pv-dashboard
    ref: main
    refresh: 1d
    files:
      - .pv-dashboard_utility.yaml
      - .pv-dashboard_ui.yaml
      - .pv-dashboard_display.yaml
      - .pv-dashboard_audio.yaml
      - .pv-dashboard_core.yaml
      - .pv-dashboard_ha.yaml
```

Er ist seit dem 20.09.2026 aktiv, die lokale Variante steht auskommentiert
darunter. Der Fernblock kommt ohne Zugangsdaten aus, weil
das Repo öffentlich ist — ein nicht öffentliches bräuchte `username`/`password`
und damit einen Token in genau der Datei, die keine Geheimnisse enthalten soll.

Was `esphome/components/packages` in 2026.9.0 wirklich kann (im Quelltext
nachgelesen): die Langform mit `url`, `ref`, `files`, `refresh` und optional
`path`, `username`, `password`; die Kurzform
`github://Bascht74/esphome-pv-dashboard/<datei>.yaml@<zweig>` für eine einzelne
Datei. Versteckte Dateinamen mit führendem Punkt sind erlaubt — geprüft wird
nur die Endung `.yaml`/`.yml`. Mehrere Dateien in einem Block teilen sich einen
Checkout und behalten die Reihenfolge der Liste; die Merge-Reihenfolge bleibt
damit dieselbe wie bei den `!include`-Zeilen.

Drei Dinge, die der Probelauf gezeigt hat (2026.9.0, 20.09.2026, gegen eine
Kopie dieses Repos und gegen ein öffentliches Repo):

- **Die Seitendateien gehören nicht in die Liste.**
  `.pv-dashboard_ui.yaml` holt sie selbst über `!include`, und zwar aus
  demselben Checkout. Listet man sie zusätzlich auf, hängt ESPHome jede Seite
  zweimal an und der Lauf bricht mit „ID redraw_curve redefined“ ab. Genauso
  kommt `images/` aus dem Checkout: ESPHome sucht eine Bilddatei auch neben
  der Paketdatei, nicht nur neben `pv-dashboard.yaml`.
- **Das Gerät baut dann aus dem geschobenen Stand.** Eine Änderung an einem
  Package wirkt erst nach einem `push`, und `refresh: 1d` holt sie frühestens
  am nächsten Tag (`always` sofort, `never` gar nicht). Simulator und
  Screenshots binden weiter die Dateien auf der Platte ein und zeigen den
  Arbeitsstand schon vorher.
- **Die `!secret`-Zusage von oben gilt dann nicht mehr.** Jede nachgeladene
  Paketdatei leert in `yaml_util.load_yaml` die Merkliste, aus der der Dump
  den Namen zurückholt; `esphome config` zeigt danach den Wert statt
  `!secret '<name>'` — im Terminal unsichtbar gestellt, in einer umgeleiteten
  Datei aber lesbar. Die Ausgabe nach der Umstellung also nicht mehr in eine
  Datei schreiben.

`pv-dashboard-shots.yaml` bindet den Simulator ein und schießt die Screenshots
ohne Fenster; `pv-dashboard-demo*.yaml` sind Prototypen der Flussanimation,
`tools/flow_animation.py` ist ihr Generator.

Ohne YAML kommen die übrigen Dateien des Repos aus: `README.md` (Überblick,
Dateitabelle und der kurze Weg „Inbetriebnahme" vom Clone zum eigenen Panel),
`CLAUDE.md` (Regeln für Assistenz-Sitzungen), `LICENSE` (MIT),
`secrets.yaml.example` und die sechs Dokumente unter `docs/`.

Die Oberfläche steht genau einmal da; Gerät und Simulator erwarten dieselben IDs `main_display`, `main_touchscreen`, `dash_time`. Beim Bauen führt ESPHome beide `lvgl:`-Blöcke zusammen — deshalb kann die Drehung im geräteeigenen Package stehen: Im gemeinsamen Block würde sie den Simulator mitdrehen, dessen SDL-Fenster schon quer liegt. Warum sie nicht in den `display:`-Block darf, steht in Dokument 02.

## Einstieg in die Oberfläche

Die Oberfläche liegt in **zwölf** Dateien: dem Kern `.pv-dashboard_ui.yaml` und
je einer Datei pro Seite. Der Kern bindet die Seiten über einen eigenen
`packages:`-Block ein — **diese Reihenfolge ist die Reihenfolge der Seiten**.
ESPHome hängt Listen aus Packages in der Reihenfolge aneinander, in der die
Packages deklariert sind; die Reiter der Menüleiste zählen auf dieselbe Ordnung:
Übersicht, PV, Prognose, Wetter, Speicher, Wallboxen, Wärmepumpe, Haus, Netz, Statistik, Meldungen. Der Reiter der Seite PV & Prognose heißt seit dem 25.09.2026 nur noch „PV“, damit elf Reiter in die Leiste passen (Lücke 6 px statt der Vorgabe, `pad_column`); „Wärmepumpe“ ist der breiteste und hat links und rechts noch etwa 5 px Luft.

| Datei | Zeilen | Blöcke, Zeilennummern |
| --- | --- | --- |
| `.pv-dashboard_ui.yaml` | 1407 | `substitutions:` 24, `packages:` 36, `text:` 58, `globals:` 88, `script:` 215, `lvgl:` 559, `interval:` 1404 |
| `.pv-dashboard_page_overview.yaml` | 1617 | `substitutions:` 43, `globals:` 105, `sensor:` 145, `script:` 179, `lvgl:` 533, `interval:` 1369 |
| `.pv-dashboard_page_pv.yaml` | 479 | `globals:` 31, `script:` 54, `lvgl:` 248 |
| `.pv-dashboard_page_forecast.yaml` | 439 | `globals:` 43, `script:` 66, `interval:` 268, `lvgl:` 273 |
| `.pv-dashboard_page_weather.yaml` | 522 | `globals:` 49, `script:` 96, `lvgl:` 320 |
| `.pv-dashboard_page_battery.yaml` | 348 | `substitutions:` 35, `globals:` 43, `script:` 49, `lvgl:` 129 |
| `.pv-dashboard_page_wallbox.yaml` | 438 | `substitutions:` 48, `script:` 52, `lvgl:` 184 |
| `.pv-dashboard_page_heatpump.yaml` | 373 | `script:` 52, `lvgl:` 180 |
| `.pv-dashboard_page_house.yaml` | 782 | `substitutions:` 61, `script:` 68, `lvgl:` 474 |
| `.pv-dashboard_page_grid.yaml` | 350 | `substitutions:` 52, `script:` 56, `lvgl:` 208 |
| `.pv-dashboard_page_stats.yaml` | 400 | `globals:` 31, `script:` 46, `lvgl:` 217 |
| `.pv-dashboard_page_alerts.yaml` | 721 | `globals:` 26, `script:` 41, `lvgl:` 473 |
| `.pv-dashboard_ha.yaml` (nur Gerät, erzeugt) | 2925 | `substitutions:` 47, `globals:` 270, `sensor:` 377, `text_sensor:` 1494, `binary_sensor:` 1619, `script:` 1726, `interval:` 2307 |

Im Kern steht nur, was alle Seiten teilen: die Tagesreihen `day_curve` und
`forecast_curve`, die Globals `ota_running` 89, `curve_day` 97, `data_seen` 108,
`dev_present` 129 und `data_stale_reported` 135, der Sonderwert `val_leer` 153,
die Formatierer `fmt_num` 157, `fmt_watt` 173 und `fmt_power` 191
(Dezimalkomma, Tausenderpunkt, Striche bei `NAN`, **leer** bei `val_leer`; alle
Seiten benutzen sie), die Skripte `sys_refresh` 225, `record_hour`
330, `dev_apply` 395 und `update_clock` 504, unter `lvgl:` die Basis,
`style_definitions` 608, `gradients` 685 und `top_layer` 975, und am Ende das
`interval:` für `sys_refresh`. Einen
`pages:`-Schlüssel hat der Kern **nicht** — die Seiten bringen ihn mit.

**Jedes Skript liegt bei der Seite, die es benutzt:** `money_update` 193, die
Eingabeskripte `ov_roof` 255, `ov_inverter` 272, `ov_battery` 291,
`ov_battery_total` 312, `ov_consumer` 329, `ov_meter` 353, `ov_grid` 373,
`ov_house` 388, `ov_totals` 407 und `ov_status` 447 sowie `redraw_curve` 462 in
der Übersicht (dazu dort die globals `flow_ch` 134 und `ov_now` 140),
`pv_status` 65, `pv_update` 123 und
`pv_redraw_curve` 170 auf der Seite PV & Prognose, `fc_today` 79, `fc_slots` 114,
`fc_day` 149 und `fc_redraw` 175 in der Prognose, `wx_now` 110, `wx_hour` 160,
`wx_day` 198, `wx_warning` 243 und `wx_redraw` 268 im Wetter (dazu dort das global
`wx_cond` 52, das auch die Prognose benutzt), `storage_update` 56 und `storage_mean` 113 im Speicher (global `storage_soc` 44),
`wallbox_update` 73 und `wallbox_month` 170 bei den Wallboxen, `heatpump_update` 75
und `heatpump_extra` 147 bei der Wärmepumpe, `house_flow` 85, `house_battery` 282,
`house_loadpoint` 317, `house_update` 362 und `house_history` 416 im Haus,
`grid_update` 67, `grid_phase` 117, `grid_meter` 151 und `grid_rules` 180 im Netz,
`stats_update` 58, `stats_show` 89 und `stats_redraw` 115 in der Statistik,
`alert_push` 83, `alert_ack` 259, `alert_clear` 290 und `alert_refresh` 330 in den Meldungen. Im Kern
bleiben nur `sys_refresh`, `record_hour`, `dev_apply` und `update_clock`: Sie fassen kein
Seiten-Widget an, sondern die Tagesreihen beziehungsweise die Leisten und
Fenster im `top_layer`, und sie werden aus Packages gerufen, die keine Seite
sind (`_core`, `-sim`, `-shots`) oder aus dem Kern selbst. Ausnahme ist
`dev_apply`: Es blendet auf mehreren Seiten zugleich aus (Übersicht, PV,
Speicher, Wallboxen, Wärmepumpe, Haus) und gehört deshalb keiner einzelnen.

Fünf Seiten tragen vor ihrem `script:` einen eigenen `substitutions:`-Block
mit den Standardbeschriftungen (Dokument 01): Übersicht und Speicher seit dem
20.09.2026, Wallboxen und Haus seit dem 24.09.2026, Netz seit dem 25.09.2026
(`pv_kwp`, `feed_limit_pct`); deshalb beginnt der Rest
der Datei dort später als vorher. **`name_wb_1` und `name_wb_2` stehen wie die
Speichernamen doppelt**, in der Übersicht und auf der Seite Wallboxen; es gilt
dasselbe wie im nächsten Absatz, das Wallbox-Paket steht später und gewinnt.

**`name_bat_1` bis `name_bat_3` stehen in beiden Blöcken** — in der Übersichts-
und in der Speicherseite. Laufen die zwei Stellen auseinander, gewinnt
stillschweigend das Speicher-Paket, weil es im `packages:`-Block des Kerns
später steht; unter Packages sticht der spätere Eintrag (geprüft mit 2026.9.0).
Gemeldet wird das nicht, die drei Zeilen in der Übersicht sind dann tote Zeilen.
Wer eine der beiden Seiten anfasst, zieht die andere mit nach. Ein Wert aus
`.pv-dashboard_anlage.yaml` sticht ohnehin beide.

Zeilennummern im **Arbeitsstand vom 25.09.2026**. Sie altern mit jeder
Änderung, sie sind nur der Einstieg; gefunden wird mit `grep`:

```
grep -n '^[a-z_]*:'         .pv-dashboard_ui.yaml        # die Bloecke des Kerns
grep -n '^  [a-z_]*:'       .pv-dashboard_ui.yaml        # Unterbloecke von lvgl:
grep -n '^  - id: '         .pv-dashboard_*.yaml         # Globals und Skripte
grep -n '^    - id: page_'  .pv-dashboard_page_*.yaml    # die elf Seiten
grep -n '!include'          .pv-dashboard_ui.yaml        # die Seitenreihenfolge
```

## Seiten

Elf Seiten, Fläche **1280 x 800** (quer). Drei Leisten liegen im `top_layer`, überdecken jede Seite und werden **nie** versteckt: `bar_status` (y 0 bis 44), die Meldungszeile `bar_alert` mit `lbl_alert` (y 44 bis 76) und die Reiterleiste `bar_nav` mit `nav_matrix` (y 744 bis 800).

Die Meldungszeile steht auch ohne Meldung da — `lbl_alert` zeigt dann „Keine Meldungen" bzw. „Keine offenen Meldungen", ein Tipp öffnet die Meldungsseite. Mit offenen Meldungen zeigt sie die Zahl je Schweregrad, schwerster zuerst, und die jüngste Meldung des höchsten Schweregrads, etwa „2 Störungen · 1 Warnung · Gerät: Text". Der Grund von `bar_alert` ist dann rot (Störung), gelb (Warnung) oder türkis (nur Info) getönt. Für Seiteninhalt bleiben deshalb **1280 x 668**, y 76 bis y 744: die Höhe, gegen die Regel 1 aus Dokument 04 rechnet.

Kachelkonvention im Repo: x 4, Breite 1272, Kacheln von **y 84 bis y 736** — je 8 px Luft zur Meldungszeile und zur Menüleiste. `schema_area` nutzt die Fläche dagegen voll (x 4, y 76, 904 x 668).

- `page_overview` – links das Anlagenschema (`schema_area`, 904 × 668, 37 Leitungen, seit 25.09.2026 mit IDs `ln00` … `ln36`), rechts die Kennzahlenspalte: Tagesverlauf (16 `bar`-Widgets `bar_h00`…`bar_h15` plus Prognoselinie `line_forecast`; ESPHomes LVGL hat kein chart-Widget), vier Kacheln der Energiebilanz, Tagesertrag, Ringe Autarkie und Eigenverbrauch.
- `page_pv` – seit 23.09.2026. Oben zwei Kacheln wie die zwei Energiekreise: links Volleinspeisung (x 4, 322 breit), rechts Hausnetz (x 334, 942 breit); je Wechselrichter eine Gruppe aus Wechselrichterkasten und seinen zwei Flächen, Leistung in W und Tageswert in kWh. Unten dieselbe Teilung: links vier Kennzahlen (Ist heute, Prognose heute, Restprognose, Ist zu Prognose der abgeschlossenen Stunden), rechts der Tagesverlauf mit 16 Balken und Prognoselinie im großen Maßstab. Seit 25.09.2026 zeigt jeder Wechselrichterkasten einen Statuspunkt (grün / rot) und die Temperatur in der Unterzeile; bei Störung wird der Rahmen rot und die Unterzeile zeigt den Fehlertext (`pv_status`). Geometrie und Höhenrechnung im Kopf der Datei.
- `page_forecast` – seit 25.09.2026, Prognose nach Solcast, mit den Werten, die der Blueprint ha-pv-optimizer benutzt. Links „Solcast · heute“ (P50 groß, Spanne P10 bis P90, Rest heute, jetzt, nächste Stunde, Spitze mit Uhrzeit, Stand und API-Abrufe), rechts die Halbstunden 05:00 bis 22:00 als Band P10 bis P90 mit P50-Linie und Marke „jetzt“ (zieht jede Minute nach), unten sieben Tage mit Wetterbild (Lage von der Seite Wetter), P50 als Balken, P10 bis P90 als Strich. Geometrie im Kopf der Datei.
- `page_weather` – seit 25.09.2026, Wetter vom DWD (HACS-Integration „DWD Weather“). Links „jetzt“ mit großem Wetterbild (`f_wx_xl`), Temperatur, Lage, Höchst- und Tiefstwert, Wind mit Richtung, Böen, Feuchte, Luftdruck, Wolken, Regen heute, Sonne auf und unter, Sonnenscheindauer; rechts zwölf Spalten zu 2 Stunden mit Bild, Temperatur als Kurve, Regen als Balken und Wahrscheinlichkeit; unten sieben Tage mit Bild (`f_wx_l`), Lage, Höchst, Tiefst, Regen, Sonne, Wind und oben rechts der DWD-Warnung.
- `page_battery` – drei SoC-Ringe und Tabelle `tbl_storage`: Ladezustand, Strom, Zelle min/max, Zelldifferenz, Temperatur min/max, Zyklen. Erste fertig gebaute Detailseite — **Vorlage für jede neue**.
- `page_wallbox` – seit 24.09.2026, am selben Tag nach dem Vorbild von evcc (0.316.0) umgebaut. Zwei Ladepunkt-Karten je 632 × 512: Kopf mit Name und Modus-Schalter Aus / Smart / Schnell, Sitzungswerte Leistung (mit Blitz und drei Phasenstrichen), Geladen, Sonne, Ladedauer; nach der Trennlinie Fahrzeug und Statuszeile, Ladestandsbalken mit dunklerem Rest bis zum Limit und Limit-Marke, darunter Ladestand (mit Reichweite), Ladeplan, Ladelimit. Unten die Monatskachel „Ladevorgänge im Monat“ (Geladen, Sonnenanteil, Kosten, Ø Preis). Akzent `col_evcc`, Flächen und Einheitenregel bleiben die des Dashboards. Höhenrechnung im Kopf der Datei.
- `page_heatpump` – seit 24.09.2026, am selben Tag auf die **Nilan Compact P** umgebaut, im Aufbau der Startseite des Touch-Bedienteils CTS700 (der Nutzer hat das klassische CTS700 mit Textzeilen, will die Seite aber grafisch), auf Wunsch des Nutzers auf dem Dashboard-Grund (Kachel `st_tile`). Links die Nilan-Kachel (760 × 652): Außentemperatur mit Sonne, grünes Haus aus Flächen (`col_nilan_house`; Dach = Quadrat 311 × 311, um 45° gedreht, in einem Behälter mit `transform_scale_y` 0,682 gestaucht, darüber die Wand, damit die Kante am Dachfuß verdeckt ist; Rechnung im Kommentar der Datei), im Dach die Raumtemperatur mit Sollwert, in der Wand Feuchte, CO2 (nur mit Wert sichtbar) und die Warmwasserkachel (`col_nilan_tank`, Rand `col_nilan_tank_edge`) mit rotem Punkt für die Zusatzheizung und Sollwert darunter, rechts die runde Lüftertaste mit Stufe und Zu-/Abluftventilator in %. Unter dem Haus ein gelber Hinweis, solange Enteisung oder Legionellenschutz laufen. Rechts „Information“ wie hinter der Info-Taste (Betriebsart Lüftung, Jahreszeit, Bypass, Kompressor, Zu- und Fortluft, Ventilatoren, Tage bis zum Filterwechsel, ab 7 Tagen gelb) und „Strom“ (Leistungsaufnahme, Verbrauch heute). Das Nilan-Logo ist bewusst nicht nachgebaut.
- `page_house` – seit 24.09.2026, am selben Tag nach dem Energiefluss von evcc umgebaut. Oben der evcc-Balken (Eigenverbrauch PV, Eigenverbrauch Speicher, Netzbezug, Einspeisung; Breite nach Anteil) mit den Klammern „In“ (PV, Speicher, Netz) und „Out“ (Verbrauch, Ladepunkte, Speicher laden, Einspeisung) samt Symbolen und Legende. Darunter die ausgeklappte Tabelle in drei Spalten: In (Erzeugung mit Restprognose, Speicher entladen mit Unterzeilen je Speicher, Netzbezug mit Preis), Out (Verbrauch mit Preis, Ladepunkte mit Unterzeilen je Wallbox, Speicher laden, Einspeisung mit Vergütung) und Verbraucher (Wärmepumpe, vier Geräte, Grundlast mit kWh heute). Unten links „Verbrauch jetzt“ (Haus und Ladepunkte) mit Herkunft aus PV, Speicher und Netz als Balken und in %, rechts der Verbrauch der letzten 24 Stunden als Stundenbalken, der PV-gedeckte Teil grün. Farben `col_evcc*`. Geometrie im Kopf der Datei.
- `page_grid` – seit 25.09.2026, Netz und Zähler. Vier Kacheln je 632 breit: Hausanschluss (Leistung, grün bei Einspeisung und rot bei Bezug, Frequenz, Balken der Einspeisung gegen die Einspeisegrenze `feed_limit_pct` von `pv_kwp` mit gelber Marke, Grenze in kW, Auslastung, abgeregelte Energie heute), Phasen L1 bis L3 (Spannung, außerhalb 207 bis 253 V gelb, Strom, Wirk- und Scheinleistung, Leistungsfaktor, Neutralleiterstrom), Zählerstände (fünf Zählwerke mit Stand und heute) und Netzvorgaben (Einspeisegrenze, Börsenpreis, rot wenn negativ, negative Viertelstunden, Vergütung bei negativem Preis, Steuersignal § 14a, Smart Meter). Werte nach dem Shelly Pro 3EM, Rechtliches in Dokument 06.
- `page_stats` – seit 25.09.2026, Statistik. Kopf mit Zeitraum, Umschalter Woche / Monat / Jahr und fünf Kennzahlen (Erzeugung, Verbrauch, Autarkie, Eigenverbrauch, Ertrag in €), darunter Balkenpaare Erzeugung (gelb) und Verbrauch (hell) auf gemeinsamem Maßstab, bis 31 Plätze. Autarkie = (Verbrauch − Bezug) / Verbrauch, Eigenverbrauch = (Erzeugung − Einspeisung) / Erzeugung. Die Reihen liegen nur im RAM.
- `page_alerts` – Liste `alert_list`, Kopfkachel mit drei Zählern je Schweregrad (`btn_af_2`/`_1`/`_0`, zugleich Filter: Tippen zeigt nur diesen Schweregrad, erneutes Tippen alle), Knöpfe „Alle quittieren“ und „Liste leeren“. Es stehen nur Meldungen da, deren Ursache noch besteht; gleiche Meldungen (gleiches Gerät, gleicher Text) stehen als eine Zeile mit „×3 seit 08:12“ im Hinweis.

In der Statusleiste stehen seit dem 25.09.2026 rechts neben der Mitte drei Symbole (`sys_icons`, x 700, 110 × 30): WLAN, Home Assistant, Daten aktuell. Ein Tipp öffnet das Fenster `sys_panel` im `top_layer` (600 × 592 bei x 340, y 114), ein Tipp darauf schließt es. Inhalt und Regeln in Dokument 06, „Systemstatus“.

**Neue Detailseite.** Vorlage ist `page_battery`. Dazu gehört:

- Kachelkonvention wie oben: x 4, Breite 1272, y 84 bis 736.
- `scrollable: false` **auch auf der Seite selbst** — eine Seite ist ebenfalls
  ein Objekt (Dokument 04, Punkt 4).
- Nav-Knopf und Screenshot-Eintrag sind **schon da**: `nav_matrix` trägt alle
  elf Knöpfe (`btn_nav_overview` … `btn_nav_alerts`), und der Screenshot-Lauf
  nimmt jede Seite auf (`04_wallbox.bmp` und so fort). Eine **zwölfte** Seite
  passt nicht mehr in die Leiste, ohne die Beschriftungen zu kürzen oder die
  Leiste zu teilen; sonst braucht sie einen neuen Knopf in `nav_matrix`, einen Eintrag in
  `shots_nav_clear` und einen eigenen Bildschritt in `pv-dashboard-shots.yaml`.
- Die Flussanimation **nicht** neu erzeugen, solange keine Leitung im Schema
  angefasst wird.
- Datenanbindung: eigene Skript-Schnittstelle nach dem Muster
  `storage_update(...)`, bis dahin Strichmuster — siehe Dokument 06.
- Danach die Checkliste aus Dokument 04, vollständig.

Ebenfalls im `top_layer`, aber normalerweise versteckt: die Overlays `voice_panel` und `ota_panel`. Bei Untätigkeit (`$idle_timeout`, 240 s) fällt die Oberfläche über `on_idle` auf die Übersicht zurück; das Abdunkeln macht derselbe Timeout im Display-Package.

## Tokens und Stile

Einzige Quelle für Farben und Maße; die Regeln für Werte und Einheiten stehen in Dokument 01.

Flächen `col_bg`, `col_surface`, `col_line`; Text `col_ink`, `col_ink2`, `col_ink3`. Leitungen werden nach **Quelle** gefärbt: `col_solar` (Hausnetz-Kreis), `col_full` (Volleinspeisung), `col_batt`, `col_feed`, `col_draw`, dazu `col_warn`/`col_crit`. Maße: `pad_page` 4, `pad_tile` 10, `gap_tile` 8 (nur Konvention: definiert, aber nirgends als `$gap_tile` benutzt, nur in Kommentaren genannt), `radius_tile` 11, `radius_box` 10.

`style_definitions`: `st_tile` (Kachel), `st_box` (Gerätekasten), `st_label`, `st_unit`, `st_sub`, `st_alert_row`, `st_btn`.

## Verläufe

Kräftiger Look, Entscheidung des Nutzers vom 12.09.2026: deutliche Schemaflächen, Licht hinter dem Hausnetz, Randverläufe an den Energiekacheln; die RGB565-Stufen dabei sind in Kauf genommen (Dokument 04). Vorhanden: drei konische Ringverläufe, `grad_day_bar` (Stundenbalken), `grad_lit_*` (Dachgruppen), `grad_box_*` (Schein in den getönten Gerätekästen), `grad_hub` (RADIAL) plus `grad_hub_shade`, `grad_tile_*` (HOR, Kachelkanten), `grad_yield` (LINEAR). `col_tint_*`, `col_box_*`, `col_glow_*` und `col_lit_tail` sind auf die RGB565-Stufen hin gewählt.

Welcher Verlaufstyp wo erlaubt ist und wie die Töne dazu gewählt werden, steht in Dokument 04 (RGB565).

## Skripte und ihre Schnittstellen

Angebunden wird später nur über diese Skripte; wo noch etwas fehlt, steht in Dokument 06.

**`alert_push(severity, device, text)`** – 0 = Info, 1 = Warnung, 2 = Störung; fügt oben in `alert_list` ein, `mode: queued`, `max_runs: $alert_max`. Zeilenaufbau (Reihenfolge nicht umstellen, Zugriff per Index): 0 Schweregrad, 1 Zeit, 2 Gerät, 3 Meldung, 4 Hinweis, 5 Quelle „Gerät: Meldung“, versteckt mit `long_mode: CLIP`, 6 Zählung „Anzahl erstes_Auftreten behoben_um“, versteckt. Kind 5 ist nötig, weil `DOT` den Textpuffer verändert (Dokument 04, Punkt 3), und dient zugleich als Schlüssel: Steht dieselbe Meldung schon in der Liste, legt `alert_push` keine neue Zeile an, sondern zählt die vorhandene hoch, setzt ihre Zeit auf jetzt, hebt die Quittung auf und schiebt sie nach oben; war sie länger als einen Tag behoben, zählt sie neu ab 1. Der Zeitstempel steckt im `user_data`, der Schweregrad in den Merkern `LV_OBJ_FLAG_USER_2` (Warnung) und `USER_3` (Störung), „behoben“ in `USER_4`. Über `$alert_max` (50) hinaus fällt die älteste **behobene** Zeile heraus, dann die älteste quittierte, sonst die älteste überhaupt.

**`alert_ack(row)`** – `row` = Zeilenindex, `-1` = alle offenen. Quittiert heißt gedämpft, nicht gelöscht: Die Zeile bleibt in der Chronologie. Wohin die Quittung später läuft, ist offen (Dokument 06).

**`alert_clear(device, text)`** – die Ursache ist behoben: Die Zeile verschwindet aus der Anzeige, bleibt aber versteckt in der Liste, damit ein Wiederauftreten mitzählt. `text` leer = alle Meldungen dieses Geräts. Rufen heute `pv_status` (Wechselrichter wieder in Ordnung oder anderer Fehlertext), `sys_refresh` (Quelle liefert wieder; der Text heißt fest „Keine Daten von …“) und `wx_warning` (Warnung aufgehoben oder ersetzt).

**`alert_refresh`** – zählt die Meldungen, setzt Zeitangaben (heute nur Uhrzeit, sonst mit Datum), die Hinweise („×3 seit 08:12“ bzw. „seit 23.09.“), die drei Zähler, die Meldungszeile samt Farbe und die Knöpfe, und blendet behobene sowie vom Filter (`alert_filter`, −1 = alle) ausgeschlossene Zeilen aus. Läuft aus `on_add`/`on_remove`, nach Auffrischen, Beheben, Filtern und dem Quittieren, beim Tageswechsel und beim ersten gültigen Zeitpunkt nach dem Start – von Hand ruft es niemand.

**`storage_update(bat, soc, current, cell_min, cell_max, temp_min, temp_max, cycles)`** – `bat` 0…2 = Speicher 1…3, `current` positiv = Laden, `NAN` bzw. `cycles < 0` ergibt „--“. Füllt Spalte `bat + 1` der Tabelle und den Ring und ruft `storage_mean`: Mittelwert über die laut `dev_present` vorhandenen Speicher, nur wenn jeder einen Wert hat. Fehlt der Speicher, kehrt es sofort zurück. Die Batteriekästen der Übersicht füllt `ov_battery`.

**`pv_update(inv, pv, power, energy)`** – Seite PV & Prognose. `inv` 0…3 = Wechselrichter 1…4, `pv` 0…7 = Fläche/Modul 1…8, jeweils `-1` = keiner; ein Aufruf setzt einen Wechselrichter, eine Fläche oder beides. `power` in W, ganzzahlig mit Tausenderpunkt; `energy` in kWh heute, eine Nachkommastelle. `NAN` ergibt das Strichmuster (`--.---` bzw. `-.---`, `W · --,- kWh`). Füllt nur die PV-Seite; die Kästen im Schema füllen `ov_roof` und `ov_inverter`.

**`wallbox_update(wb, mode, charging, power, phases, energy, solar, minutes, vehicle, status, soc, range, limit, plan)`** – Seite Wallboxen, Namen nach der evcc-API. `wb` 0…1 = Wallbox 1…2; `mode` `off`/`smart`/`now` (ältere evcc-Versionen: `pv` und `minpv` leuchten als Smart); `charging` färbt Blitz und Phasen; `power` in kW, `phases` 0…3, `energy` Sitzung in kWh, `solar` Sonnenanteil in %, `minutes` Ladedauer (< 0 = keine); `vehicle` leer = „Kein Fahrzeug“, `status` freie Zeile; `soc` und `limit` in %, `range` in km, `plan` Text wie „Mo 07:00“ (leer = kein Plan). `NAN` ergibt Striche. Füllt nur diese Seite; den Wallbox-Kasten der Übersicht füllt `ov_consumer`.

**`wallbox_month(energy, solar, cost, price)`** – Monatskachel der Wallbox-Seite: geladene kWh, Sonnenanteil in %, Kosten in €, Durchschnittspreis in ct/kWh. `NAN` ergibt Striche.

**`heatpump_update(outdoor, room, humidity, co2, dhw, eheat, fan, vent_mode, season, bypass, compressor, supply, exhaust, power, energy, alarm)`** – Seite Wärmepumpe (Nilan Compact P). Temperaturen in °C: außen, Raum (Abluft), Warmwasser, Zu- und Fortluft; `humidity` in %, `co2` in ppm (`NAN` blendet die CO2-Gruppe aus); `eheat` zeigt den roten Punkt der Zusatzheizung; `fan` Lüftungsstufe 0…4 (0 = „Aus“, < 0 = unbekannt); `vent_mode`, `season`, `bypass`, `compressor` als Text (leer ergibt „--“); `power` in kW und `energy` in kWh heute, beide elektrisch; `alarm` 0 = nichts, 1 = gelbes, 2 = rotes Warnsymbol. Setzt „Stand HH:MM“ und zusätzlich die Zweitzeile `d_heatpump` im Schema der Übersicht (Warmwasser statt COP).

**`heatpump_extra(room_set, dhw_set, fan_supply, fan_extract, filter_days, defrost, legionella)`** – weitere Werte der Compact P aus dem Registersatz des klassischen CTS700: Sollwerte Raum und Warmwasser in °C, Zu- und Abluftventilator in %, Tage bis zum Filterwechsel (< 0 = unbekannt), Enteisung und Legionellenschutz als Schalter. Adressen und ihre Unsicherheit in Dokument 06.

**`house_flow(pv, bat_out, grid_in, home, loadpoints, bat_in, grid_out, soc, forecast, price_grid, price_home, price_feed)`** – Seite Haus, Energiefluss nach evcc. Leistungen in W (≥ 0) für den Hausnetz-Kreis: PV-Erzeugung, Speicher entladen, Netzbezug, Verbrauch (alles außer Ladepunkten und Speicher, also mit Wärmepumpe), beide Ladepunkte zusammen, Speicher laden, Einspeisung; dazu Speicher-SoC in %, Restprognose in kWh und drei Preise in ct/kWh. Rechnet Eigenverbrauch wie evcc (erst PV, dann Speicher) und füllt Balken, Klammern, die Spalten In und Out und „Verbrauch jetzt“. `NAN` ergibt Striche.

**`house_battery(bat, power, soc)`** und **`house_loadpoint(wb, power, soc)`** – Unterzeilen der Tabelle: je Speicher (0…2, Leistung in W, positiv = entladen) bzw. je Wallbox (0…1, Ladeleistung in W, `soc` des Fahrzeugs, `NAN` = kein Fahrzeug). `house_loadpoint` zählt auch die aktiven Ladepunkte (ab 10 W).

**`house_update(dev, power, energy)`** – Spalte Verbraucher. `dev` 0…5 = Wärmepumpe, Backofen, Waschmaschine, Spülmaschine, Trockner, Grundlast (`name_heatpump`, `name_oven` … `name_baseload`), `power` in W, `energy` in kWh heute. Die Kopfzeile zeigt die Summe, sobald alle sechs da sind (ohne Wärmepumpe laut `dev_present`: die übrigen fünf).

**`house_history(home, solar, hour)`** – Verbrauch der letzten 24 Stunden: je 24 kommagetrennte kWh-Werte, älteste zuerst, `solar` der aus PV gedeckte Teil, `hour` die Uhrzeit des letzten Werts. Wird nicht gespeichert (Dokument 06).

**`pv_status(inv, ok, text, temp)`** – Zustand eines Wechselrichters (`inv` 0…3): `ok` false färbt Rahmen und Punkt rot, zeigt `text` (leer = „Störung“) in der Unterzeile und legt beim Wechsel in die Störung **eine** Meldung (Schwere 2) an; `temp` in °C erscheint hinter dem Tageswert, `NAN` blendet sie aus. Fehlt der Wechselrichter laut `dev_present`, tut es nichts.

**`money_update(full_feed, surplus, self_use, grid_in)`** – Übersicht, Kachel Tagesertrag. Energien heute in kWh: Volleinspeisung, Überschusseinspeisung, selbst verbrauchter PV-Strom, Netzbezug. Rechnet mit den drei Tarifen Förderung, Ersparnis, Bezugskosten und Ertrag, schreibt Kachel, globals und vier Sensoren (Dokument 06, „Geldwerte“).

**`grid_update(power, freq, curtailed, n_current)`** – Seite Netz: Leistung am Hausanschluss in W (positiv = Bezug, negativ = Einspeisung, wie `total_act_power` des Shelly Pro 3EM), Frequenz in Hz, heute abgeregelte kWh, Neutralleiterstrom in A.

**`grid_phase(phase, voltage, current, power, apparent, pf)`** – eine Phase (0…2 = L1…L3): V, A, W (positiv = Bezug), VA, Leistungsfaktor.

**`grid_meter(meter, total, today)`** – ein Zählwerk: 0 Hausanschluss Bezug, 1 Hausanschluss Einspeisung, 2 PV-Zähler Einspeisung, 3 Hauszähler Bezug, 4 Hauszähler Einspeisung; Stand und heute in kWh.

**`grid_rules(limit_active, spot_ct, neg_quarters, neg_paid, p14a_active, p14a_kw, smart_meter)`** – Netzvorgaben: Einspeisegrenze aktiv, Börsenpreis in ct/kWh, negative Viertelstunden heute (< 0 = unbekannt), Vergütung bei negativem Preis, Steuersignal § 14a mit Grenze in kW, Smart Meter und Steuerbox eingebaut.

**`stats_update(range, period, labels, prod, cons, imp, exp, money)`** – Seite Statistik: `range` 0 Woche, 1 Monat, 2 Jahr; `period` Zeitraum als Text; `labels` und die vier Reihen (Erzeugung, Verbrauch, Bezug, Einspeisung in kWh) kommagetrennt, gleich viele Werte; `money` Ertrag in €. **`stats_show(range)`** schaltet um und zieht die Knöpfe mit.

**`fc_today(p50, p10, p90, remaining, power_now, next_hour, peak_kw, peak_time, updated, api_used, api_limit)`** – Seite Prognose, Kennzahlen heute aus der Solcast-Integration: Tagesprognose P50, P10, P90 in kWh, Rest heute in kWh, Leistung jetzt in W, nächste Stunde in kWh, Spitze in kW mit Uhrzeit („HH:MM“), Zeit des letzten Abrufs, API-Abrufe heute und Grenze (< 0 = unbekannt). Stempelt `data_seen[6]`.

**`fc_slots(p50, p10, p90)`** – je 48 kommagetrennte Halbstundenwerte in kW ab 00:00, wie `detailedForecast` sie liefert (`pv_estimate`, `pv_estimate10`, `pv_estimate90`); P10 und P90 dürfen leer sein. Die Globals `fc_p50`, `fc_p10` und `fc_p90` starten mit `NAN`, nicht mit 0: Vor den ersten Daten bleibt der Verlauf leer statt eine Null-Linie zu zeigen.

**`fc_day(day, label, cond, p50, p10, p90)`** – ein Tag (0 = heute … 6): Beschriftung, Wetterlage nach Home Assistant (für das Bild), Tagesprognose in kWh.

**`wx_now(cond, temp, tmax, tmin, humidity, pressure, wind, bearing, gust, clouds, rain, sun_h, sunrise, sunset, updated)`** – Seite Wetter, Werte jetzt: Lage, °C, %, hPa, km/h, Richtung in Grad, Wolken in %, Regen heute in mm, Sonnenscheindauer in h, Zeiten als „HH:MM“. Stempelt `data_seen[7]`.

**`wx_hour(slot, hour, cond, temp, rain, prob)`** – eine der zwölf 2-Stunden-Spalten (0 = nächste), Uhrzeit, Lage, °C, mm, %.

**`wx_day(day, label, cond, tmax, tmin, rain, prob, sun_h, wind)`** – ein Tag (0 = heute … 6).

**`wx_warning(level, text)`** – DWD-Warnstufe 0 bis 4 und Kurztext; ab Stufe 1 oben rechts in der Kachel Tage, jede neue Warnung einmal als Meldung (Stufe 3 und 4 als Störung).

**Eingänge des Anlagenschemas** (Übersicht, seit 25.09.2026). Jedes füllt seine Kästen, stempelt `data_seen` und schreibt die Leistung seines Kanals in `flow_ch` (Abschnitt Flussanimation); ein laut `dev_present` fehlendes Gerät bekommt 0 W. Einheiten wie im Schema, `NAN` ergibt Striche.

- **`ov_roof(n, power, energy)`**, **`ov_inverter(n, power, energy)`** – Fläche 0…7 bzw. Wechselrichter 0…3, W und kWh heute.
- **`ov_battery(n, soc, current, voltage)`** – Speicher 0…2, %, A (+ = Laden), V; Kanal = A × V.
- **`ov_battery_total(power, charged, discharged)`** – Summenkasten, W (+ = Laden), kWh heute geladen und entladen (Pfeil runter / hoch).
- **`ov_consumer(n, power, sub)`** – 0 Wärmepumpe, 1 Sonstige, 2 Wallbox 1, 3 Wallbox 2; W; `sub` ist der Text hinter „kW · “, leer lässt die Zeile stehen.
- **`ov_meter(n, power, energy)`** – 0 PV-Zähler, 1 Hauszähler; W (+ = Einspeisung), kWh heute.
- **`ov_grid(power)`** – Hausanschluss, W, + = **Bezug** (wie `grid_update`); Betrag in kW, Richtung in der Zweitzeile, Bezug rot.
- **`ov_house(power, energy)`** – Hausnetz: alles auf der Verbraucherschiene, W und kWh heute.
- **`ov_totals(gen, use, feed, draw, full_feed, surplus, remaining)`** – die vier Kacheln, beide Ringe (Autarkie = (Verbrauch − Bezug) / Verbrauch, Eigenverbrauch = (Hybrid-Erzeugung − Überschuss) / Hybrid-Erzeugung, Hybrid = `gen − full_feed`) und die Restprognose.
- **`ov_status`** – Statusleiste links: Autarkie jetzt aus Hausnetz und Bezug, Restprognose. Nur von den Skripten oben gerufen.

**`dev_apply`** – Kern. Liest `dev_present` (ein Bit je Platz: 0–7 Flächen, 8–11 Wechselrichter, 12–14 Speicher, 15/16 Wallboxen, 17 Wärmepumpe, 18 PV-Zähler, 19 Hauszähler; **nicht** im NVS, Anfangswert `dev_present_start`: im Simulator alle an, am Gerät 0, bis die Referenz-Entitäten melden) und blendet fehlende Geräte aus, ohne dass sich etwas verschiebt: Kästen, Dachgruppen und Rahmen der Übersicht, Wechselrichter und Flächen der Seite PV, Ring, Name und Tabellenspalte im Speicher, Karten der Wallboxen, Kacheln der Wärmepumpe, Unterzeilen der Seite Haus. Setzt die Kanäle fehlender Geräte auf 0, hebt die Störung eines fehlenden Wechselrichters auf und rechnet den Speicher-Mittelwert neu. Leitungen und Kugeln zieht der erzeugte Block selbst nach (Regel 10). Gerufen beim Start (`on_boot` von `bar_status`) und vom Datenweg, sobald eine Referenz-Entität kommt oder geht. Fehlt jedes Gerät einer Quelle, meldet `sys_refresh` für sie keine veralteten Daten („kein Gerät“).

**`sys_refresh`** – Kern, alle 10 s und beim Öffnen des Systemfensters: Alter der Werte je Quelle aus `data_seen`, Symbole, WLAN, Home Assistant, Laufzeit, Version (Dokument 06). Von Hand ruft es niemand.

**`pv_redraw_curve`** – Seite PV & Prognose, hängt wie `redraw_curve` an `on_value` beider Reihen und schreibt keine. Zeichnet Balken und Linie auf gemeinsamem Maßstab (Legende nennt die Skala) und rechnet die Kennzahlen: „abgeschlossen" sind die Plätze vor der laufenden Stunde (Stunde − 6), Restprognose ist die Prognose ab der laufenden Stunde bis 22 Uhr, „Ist zu Prognose" braucht mindestens 0,1 kWh Prognose in den abgeschlossenen Stunden. Ohne gültige Uhrzeit bleiben diese beiden auf Strichen.

**`record_hour`** – läuft zur vollen Stunde um HH:00:05 und schreibt die abgelaufene Stunde in Platz `(HH-1) - 6` (06–07 Uhr → Platz 0, 21–22 Uhr → Platz 15). Angebunden wird an der auskommentierten Zeile `// kwh = id(<Erzeugungssensor>).state;`; solange sie steht, wird 0 eingetragen. Am Gerät überschreibt der Datenweg die ganze Reihe ab Minute 2 jeder Stunde aus der Statistik von Home Assistant, die 0 der abgelaufenen Stunde hält also nur kurz. Die Tagesreihen `day_curve` und `forecast_curve` sind `text`-Entitäten mit 16 kommagetrennten Werten im NVS: überstehen Neustart und OTA, in HA sichtbar und setzbar. Gespeichert wird nur, was über `control()` kommt – daher `make_call()`, nicht `publish_state()`. Tageswechsel über das global `curve_day` (Jahr × 1000 + Tag): Gehört die Reihe zu einem anderen Tag, startet der Lauf mit 16 × 0.

**`redraw_curve`** – hängt an `on_value` beider Reihen, zeichnet Balken (Ist) und Linie (Prognose) auf gemeinsamem Maßstab und setzt die Unterzeile mit beiden Tagessummen. Schreibt keine Reihe: keine Schleife.

**`update_clock`** – `mode: restart`, gerufen bei `on_time_sync` und zu jeder vollen Minute. Setzt Uhr und Datum (Wochentag und Monat von Hand, `strftime` liefert Englisch) und stößt beim Tageswechsel `alert_refresh` an. Während eines Firmware-Updates (`ota_running`) tut es nichts – der Redraw kostet PSRAM-Bandbreite, die der Upload braucht; künftige periodische Anzeigen fragen das Flag ebenso ab.

**`display_wake`** – nur Gerät (Display-Package), `mode: restart`, ausgelöst von `on_touch` des GT911; fährt das Backlight in 150 ms auf 100 %.

**`voice_panel_hide`** – nur Gerät (`.pv-dashboard_audio.yaml`), `mode: restart`: blendet `voice_panel` nach 6 s aus. Gestartet von `on_end` und `on_error` (manche Fehler enden ohne `on_end`), gestoppt von `on_listening` — eine Anschlussfrage hält das Fenster also offen, statt dass ein altes `delay` es mitten in der neuen Sitzung schließt.

## Flussanimation

Die Kugeln sind erzeugter Code. `tools/flow_animation.py` liest die Leitungen aus `.pv-dashboard_page_overview.yaml`, leitet die Topologie aus den Koordinaten ab und schreibt die Kugel-Widgets (`flNN`, `flNNb` am Anfang von `schema_area`) und den Block zwischen `# >>> flow-animation` und `# <<< flow-animation`.

```
python3 tools/flow_animation.py            # Vorschau, schreibt nichts
python3 tools/flow_animation.py --write    # baut die Animation ein
```

Der Vorschaulauf meldet seit dem 25.09.2026: **37 Leitungen und 24 Gerätekästen, daraus 37 Teilstrecken und 20 Übergänge, 24 Kanäle in `flow_ch`, 31 Strecken mit Kanal, 37 Leitungen mit Sichtbarkeitsregel**. Die Zahl der Leitungen ist von 28 auf 37 gestiegen, weil die Dach-, Speicher- und Verbraucherschienen an den Kästen geteilt sind (je Stück eine eigene Sichtbarkeit), die Topologie ist dieselbe. Die **53 Liniensegmente** meldet er nicht — sie stehen nur im erzeugten Block: 37 ist die Länge von `pos[]` und `dots[]`, 53 die von `SX`, `SY`, `EX`, `EY` und `SL`; beides lässt sich dort abzählen. Diese Zahlen nie schätzen; `-v` gibt die Tabelle Strecke → Kanal → Leitung aus.

**Den Block nie von Hand ändern.** Nach jeder Änderung an den Leitungen oder Kästen das Skript erneut laufen lassen; ein Lauf ohne Änderung schreibt nichts.

**Woher die Leistung kommt (Regel 9).** Früher stand sie als feste Tabelle `WATT[]` im Block. Jetzt liest der Block je Tick das global `flow_ch` (24 Kanäle, Übersicht): 0–7 Flächen, 8–11 Wechselrichter, 12 Speicher gesamt, 13–15 Speicher 1–3, 16 Hausnetz, 17 Wärmepumpe, 18 Sonstige, 19/20 Wallboxen, 21 PV-Zähler, 22 Hauszähler, 23 Hausanschluss. Geschrieben wird es nur von den Eingabeskripten `ov_*`. Welche Strecke welchen Kanal zeigt, leitet das Werkzeug aus der Geometrie ab: Die Kästen findet es über die ID ihres Wert-Labels (`v_roof_1`, `v_wr_full`, `e_batt` …), eine Strecke, die an einem Kasten beginnt oder endet, zeigt dessen Kanal. Positiv heißt in Zeichenrichtung; negativ läuft die Kugel rückwärts, endlos und ohne etwas auszulösen (Speicher entlädt, Netzbezug); unter 10 W steht sie. Im Simulator füllt eine Demo nur dann `flow_ch`, wenn es leer ist und `USE_HOST` gilt — am Gerät nie.

**Fehlende Geräte (Regel 10).** Jede Leitung trägt die ID `lnNN` und drei Masken gegen `dev_present`: sichtbar, wenn jedes berührte Gerät da ist und hinter der Leitung (vom Hausanschluss aus gesehen) noch etwas Vorhandenes hängt. Der Block vergleicht `dev_present` je Tick mit dem letzten Stand und blendet Leitungen und Kugeln um; eine versteckte Strecke bekommt 0 W. Eine Folge der Zeichnung: Fehlen die Hybrid-Wechselrichter 3 und 4, hängen Hausnetz und Speicher ohne Leitung da, weil ihr Weg zum Hausanschluss über diese Kästen führt (Screenshot `01_overview_reduced`).

Eckwerte: Takt 20 ms, Kugeln 8 px, Deckel 13 Bewegungen je Tick – LVGL merkt sich nur 32 ungültige Flächen je Bild, jede Bewegung kostet zwei. Die 13 steht als Konstante `MAXMOVE` in `tools/flow_animation.py`; im erzeugten Block ist sie ausgeschrieben, ein `grep MAXMOVE` über die YAML findet also nichts.

## Datenweg von Home Assistant

Seit dem 25.09.2026, nur am Gerät: `.pv-dashboard_ha.yaml`, **erzeugt** von
`tools/ha_bindings.py` aus einer Zuordnungstabelle im Werkzeug (Name, Art,
Standard-entity_id, Attribut, Gruppe, Umrechnung, Demo-Wert). Das Werkzeug
schreibt zugleich `ha/pv_dashboard_dummy.yaml`, ein Paket für Home Assistant
mit Ersatz-Entitäten unter genau den Standard-IDs.

```
python3 tools/ha_bindings.py            # Vorschau: aktuell oder veraltet
python3 tools/ha_bindings.py --write    # schreibt beide Dateien
```

**Beide Dateien nie von Hand ändern**, sondern die Tabelle und `--write`.

- **Sensoren.** Jeder Wert ist ein `homeassistant`-Sensor (`sensor`,
  `text_sensor`, `binary_sensor`) mit `id: ha_<name>`, `entity_id:
  ${ha_<name>}` und `internal: true`; Attribute (`estimate10`,
  `temperature`, `next_rising` …) lesen eigene Sensoren mit `attribute:`.
  Die Standards stehen im `substitutions:`-Block der Datei und sind
  Vorschläge [A]; eigene IDs gehören als `ha_<name>: …` in
  `.pv-dashboard_anlage.yaml` und stechen die Standards. Umrechnungen
  (Wh → kWh, €/kWh → ct, s → h) als `filters: multiply`.
- **Drosselung.** Ein neuer Wert ruft kein Seitenskript auf, er setzt nur das
  Bit seiner Gruppe in `ha_dirty` (29 Gruppen: je Fläche, Wechselrichter,
  Speicher und Wallbox eine, dazu Speicher gesamt, Wallbox-Monat,
  Wärmepumpe, Verbraucher, Hausnetz, Netz, Zähler, Netzvorgaben,
  Tageswerte, Prognose, Wetter, Warnung). Ein Intervall von 1 s ruft je
  gesetztem Bit die Skripte der Gruppe einmal auf, mit allen Werten der
  Gruppe — jede Gruppe zeichnet also höchstens einmal je Sekunde neu, auch
  wenn der Shelly jede Sekunde sendet oder nach dem Verbinden alle Werte auf
  einmal kommen. Übersprungen wird eine Gruppe, deren Gerät laut
  `dev_present` fehlt, und – bis `ha_ready` – eine, von der noch kein Wert
  da ist (sonst stempelte sie `data_seen` ohne Daten).
- **Referenz-Entitäten statt eigener Schalter** (Wunsch des Nutzers,
  25.09.2026: „Die Logik ergibt sich aus den eingesetzten oder rausgenommenen
  Entitäten“). Je Geräteplatz ist **eine** der zugeordneten Entitäten die
  Referenz (`REFERENZ` im Werkzeug, Liste auch oben in der erzeugten Datei):

  | Platz | Referenz | Platz | Referenz |
  | --- | --- | --- | --- |
  | `pv_1` … `pv_8` | `ha_pv<N>_power` | `wb_1`, `wb_2` | `ha_wb<N>_mode` (Modus aus evcc, „WB-Status“) |
  | `inv_1` … `inv_4` | `ha_inv<N>_power` | `heatpump` | `ha_hp_dhw` (Warmwasser oben) |
  | `bat_1` … `bat_3` | `ha_bat<N>_soc` | `meter_pv`, `meter_house` | `ha_meter_pv_power`, `ha_meter_house_power` |

  Das Intervall (1 s) rechnet daraus `dev_present`: Bit an, solange die
  Referenz einen gültigen Wert hat (Zahl nicht `NAN`, Text nicht leer,
  `unavailable` oder `unknown`). Ändert sich etwas, ruft es `dev_apply` und
  markiert alle Gruppen neu – in beide Richtungen, auch zur Laufzeit.
  `dev_present` liegt **nicht** im NVS und startet am Gerät mit 0
  (`dev_present_start: "0u"` im Paket sticht `"0xFFFFFu"` aus dem Kern).
- **Nicht belegt.** Jede Substitution `ha_<name>` darf statt einer ID
  `none`, `false`, `off`, `null` oder `""` sein (Groß-/Kleinschreibung egal).
  Umgesetzt mit ESPHomes Jinja in den Substitutionen: `entity_id` wird dann
  zu `sensor.pv_dashboard_nicht_belegt` (gibt es nicht, Home Assistant
  schickt nichts), und im Intervall steht `constexpr bool B_<name> = false`.
  Eine nicht belegte **Referenz** nimmt das Gerät ganz heraus.
- **Grafik weg oder Wert weg.** Referenz ohne gültigen Wert → die ganze
  Grafik des Geräts verschwindet (Kasten, Werte, Leitungen, Kugeln). Jede
  **andere** Entität, die nicht belegt, nicht verfügbar oder 10 s nach dem
  Verbinden (`ha_ready`) noch ohne Wert ist, lässt nur **ihren** Wert leer,
  das Gerät bleibt. Zahlen gehen dafür als `val_leer` in die Seitenskripte,
  Texte als " ". `val_leer` ist **−∞** (`-std::numeric_limits<float>::infinity()`):
  Das ist IEEE 754 und überlebt auf jeder Plattform, auch dem RISC-V des P4,
  Kopieren und die Rechnungen hier (−∞ + x, −∞ · k, −∞ / k bleiben −∞). Eine
  frühere Fassung mit einem NAN mit eigener Kennung ist verworfen, weil der
  RISC-V bei jeder Rechnung ein kanonisches NAN liefert. Regeln:
  - `fmt_num`, `fmt_watt`, `fmt_power`: `std::isinf` → "" (leer, beide
    Vorzeichen), `NAN` → Striche wie bisher. Kein Text zeigt je „inf“.
  - Wo Werte Geometrie, Kugeln, Farben, Richtungen oder Ringe steuern, gilt
    nur `std::isfinite` als „Wert da“ (vorher `!std::isnan`); `flow_ch`
    bekommt für leer 0, also keine Kugel.
  - Rechnen nur so, dass −∞ nicht kippt: im Datenweg über `add`, `sub`,
    `neg`, `pos`, `mul`, `I` (leer in einem Summanden macht die Summe leer,
    nie ∞ − ∞, ∞ · 0 oder ein Vorzeichenwechsel); in den Seiten ebenso
    ausdrücklich (`money_update`, `ov_totals`, `ov_status`, Summen der Seite
    Haus, Zellspreizung im Speicher). Nach außen (Globals, Sensoren an Home
    Assistant) geht statt −∞ ein `NAN`.
  - Vor dem Verbinden und in Simulator und Screenshots bleiben die gewohnten
    Striche. An/aus-Werte (`binary_sensor`) kennen kein „leer“, ohne Wert
    gelten sie als aus.
- **Listen** über `homeassistant.action` mit `capture_response` und
  `response_template`: Die Jinja-Vorlage rechnet in Home Assistant die
  Antwort auf kurze, kommagetrennte Reihen zusammen, das Panel verteilt sie.
  `weather.get_forecasts` stündlich (12 Spalten zu 2 h ab der nächsten
  vollen Stunde: Regen als Summe, Wahrscheinlichkeit als Maximum; dazu Böen
  und Wolken der ersten Stunde für `wx_now`) und täglich (`wx_day`,
  Höchst/Tiefst/Regen heute, Lage je Tag für `fc_day`);
  `solcast_solar.query_forecast_data` für `fc_slots` — scheitert sie,
  liest ein zweiter Aufruf das Attribut `detailedForecast`; aus den
  Halbstunden entsteht zugleich die Tagesreihe `forecast_curve`;
  `recorder.get_statistics` (ab Home Assistant 2025.6) für die Statistik
  (Woche und Monat je Tag, Jahr je Monat, `types: change`, kWh) und für die
  letzten 24 Stunden (`house_history`, dazu `day_curve` aus der Erzeugung
  heute). Den Ertrag der Statistik rechnet das Panel mit den Tarifen wie
  `money_update` [A].
- **Zeitplan.** Ein Intervall von 10 s erkennt das Verbinden: Prognosen
  20 s danach und dann alle 30 min, Statistik 30 s danach und dann zu
  jeder neuen Stunde ab Minute 2 (damit auch beim Tageswechsel).
- **Voraussetzung in Home Assistant:** beim ESPHome-Gerät die Option
  **„Allow the device to perform Home Assistant actions“** einschalten.
  Ohne sie lehnt Home Assistant jede Aktion ab; Prognosen, Stundenwerte
  und Statistik bleiben auf Strichen, das Log „ha“ nennt den Fehler.
- **Hilfen** im Paket: `ha_split` (Reihe → Liste), `ha_when`
  (Zeitstempel → „HH:MM“ bzw. „Mo 07:00“ in Ortszeit), `ha_day_label`
  („Heute“, „Morgen“, „Sa 27.09.“).

Simulator und Screenshot-Lauf binden das Paket **nicht** ein, sie haben keine
API. Geprüft wird es mit den Tests unten (Abschnitt „Tests“), die es samt
Simulator gegen ein nachgebautes Home Assistant laufen lassen; ein Lauf gegen
ein echtes Home Assistant steht aus (Dokument 06).

**Dummy in Home Assistant.** `ha/pv_dashboard_dummy.yaml` nach
`<config>/packages/` kopieren und in `configuration.yaml` einbinden:

```yaml
homeassistant:
  packages:
    pv_dashboard_dummy: !include packages/pv_dashboard_dummy.yaml
```

Zahlen hängen an `input_number.pvd_<name>` (unter Helfer von Hand
verstellbar), Zählerstände laufen mit der Zeit hoch (damit die Statistik
etwas findet), Texte und Zeitpunkte sind fest, das Wetter ist eine
Template-Wetter-Entität mit Vorhersagen, `detailedForecast` hängt als
Attribut an der Solcast-Tagesprognose. Ein Gerät lässt sich hier testweise
wegnehmen, indem man den Helfer seiner Referenz löscht oder in
`.pv-dashboard_anlage.yaml` `ha_<referenz>: none` setzt. `sun.sun` kommt aus
der Integration Sonne. **Umstellen auf die Originale:** das Paket wieder
austragen, dann in `.pv-dashboard_anlage.yaml` nur die IDs eintragen, die vom
Standard abweichen – und `none` für alles, was es in der Anlage nicht gibt –,
und neu bauen.

## Tests

Seit dem 25.09.2026 im Ordner `tests/`, beide aus dem Projektordner und mit der
Python-Umgebung von ESPHome (nichts nachzuinstallieren):

```
~/.venvs/esphome-beta/bin/python -m unittest discover tests
~/.venvs/esphome-beta/bin/python tests/ha_probe.py            # --no-build, --shots
```

- **`test_leer_cpp.py`** (Sekunden, braucht `g++`): baut die echten
  Rechenhilfen aus `.pv-dashboard_ha.yaml` und die echten Formatierer aus
  `.pv-dashboard_ui.yaml` zu einem kleinen C++-Programm (`-O0` und `-O2`):
  leer bleibt −∞ durch Summe, Differenz, Vorzeichen, `· 0`; Formatierer geben
  "" für ±∞ und Striche für `NAN`, nie „inf“/„nan“; keine NAN-Kennung mehr im
  Repo; der Datenweg rechnet nicht an den Hilfen vorbei. Einen RISC-V-Compiler
  gibt es hier nicht, −∞ ist aber IEEE 754 und dort gleich.
- **`test_ha_bindings.py`, `test_flow_animation.py`** (Sekunden): erzeugte
  Dateien aktuell (`ha_bindings.py`, `flow_animation.py`), jeder `ha_*`-Schlüssel
  mit Standard, je Platz eine Referenz (Zahl oder Text, kein Attribut),
  dieselbe Platzliste in beiden Werkzeugen, keine Anker mehr, `dev_present`
  ohne NVS; `none`, `FALSE`, `Off`, `""`, `null` … laufen durch ESPHomes eigene
  Substitution und ergeben Ersatz-ID und `B_… = false`; jeder Kasten des
  Schemas hat einen Platz, jede Strecke einen Kanal oder schweigt, jede Leitung
  eine Sichtbarkeitsregel, jedes Gerät steuert mindestens eine Leitung.
- **`ha_probe.py`** (etwa 2 min, erster Bau länger): baut `tests/ha-test.yaml`
  (Simulator + `.pv-dashboard_ha.yaml` + `api:` ohne Schlüssel auf Port 16063,
  nur localhost; Build unter `.esphome/build/pv-dashboard-test/`), startet es
  ohne Fenster und meldet sich mit `aioesphomeapi` als Home Assistant an:
  Zustände aus der Tabelle des Werkzeugs, Antworten auf Wetter- und
  Statistik-Aktionen über einen Jinja-Nachbau der Vorlagen, Solcast-Aktion
  scheitert absichtlich. Das Panel schreibt je Sekunde eine Zeile
  `PROBE {json}` (nur in der Testkonfiguration) mit `dev_present`,
  ausgeblendeten Kästen, einzelnen Labeltexten, offenen Systemmeldungen und
  den Prognose- und Statistikreihen. Fälle: Striche vor `ha_ready`; Referenz
  `none` und Referenz fehlt in HA → Gerät weg; Referenz `unavailable` → weg,
  Wert kommt → wieder da; Referenz fällt zur Laufzeit aus; Nicht-Referenz
  `unavailable`, `FALSE` oder fehlend → nur der Wert leer; leerer Wert in
  einer Summe (Leistung Wärmepumpe und Wallbox 1) → „Sonstige“, Hausnetz und
  die Summen der Seite Haus leer, Geräte bleiben; Prognosen und Statistik
  gefüllt; Trennung → genau eine Sammelmeldung, Verbinden → weg; über den
  ganzen Lauf in keinem der rund 770 Labels aller Seiten „inf“ oder „nan“.
  `--shots` legt dazu drei BMP nach `shots/ha_probe/` (vorher gelöscht, `snapshot.take` überschreibt nicht). Exit-Code 0 = alles
  bestanden.

## Simulator und Screenshots

Ein `esphome` im PATH gibt es **nicht**. Beide Läufe starten aus dem
Projektordner, mit vollem Pfad in die Arbeitsumgebung (ESPHome 2026.9.0):

```
~/.venvs/esphome-beta/bin/esphome run pv-dashboard-sim.yaml
~/.venvs/esphome-beta/bin/esphome run pv-dashboard-shots.yaml
```

`pv-dashboard-sim.yaml` öffnet ein SDL-Fenster und **blockiert**, bis das Fenster geschlossen wird; **F12** speichert ein Bild nach `.esphome/snapshots/pv-dashboard-sim/`, `ESPHOME_SNAPSHOT_DIR` lenkt es um.

`pv-dashboard-shots.yaml` bindet den Simulator als Package ein, rendert headless alle elf Seiten, die Statistik zusätzlich als Monat, plus die drei Fenster als BMP (`01_overview.bmp` … `12_system.bmp`, dazu `13_forecast.bmp` und `14_weather.bmp`, angehängt statt umnummeriert, und `09_alerts_filter.bmp` mit dem Filter „Störungen“; zum Schluss eine kleinere Anlage über `dev_present` als `01_overview_reduced.bmp`, `02_pv_reduced.bmp`, `03_battery_reduced.bmp` und `06_house_reduced.bmp`; in der verkleinerten Übersicht sind zudem drei Werte über `val_leer` leer: Ertrag des ersten Wechselrichters, Spannung von Speicher 2, Leistung des Hauszählers) nach `shots/` unter dem Startverzeichnis und beendet sich selbst – deshalb im Projektordner starten. `snapshot.take` überschreibt nie, darum löscht `shots_take` vorher.

Beispieldaten für Meldungen, Speicher, PV-Werte, Wallboxen, Wärmepumpe, Haus, Netz, Statistik, Prognose, Wetter, Tagesreihen und Ringe stehen in `shots_run`, also **nur** im Screenshot-Lauf. Die Übersicht füllt `shots_run` über die Eingabeskripte `ov_*`, also auf demselben Weg wie später der Datenweg. Die Demo-Leistungen der Flussanimation stehen dagegen unter `#ifdef USE_HOST` und greifen nur, solange `flow_ch` leer ist — im Simulator also, im Screenshot-Lauf nicht mehr. Im Gerät steht beides nicht.

**Laufzeit.** `-sim` und `-shots` sind **getrennte Bauziele** unter `.esphome/build/`. Der erste Lauf eines Ziels ist ein Vollbuild über mehrere Minuten und holt die Schriften über `gfonts://` aus dem Netz, die Symbolschrift als Web-Font von Material Design Icons, seit 25.09.2026 fest auf das Release v7.4.47 statt `master` (Substitution `mdi_font_url` in `.pv-dashboard_utility.yaml`, Dokument 04); spätere Läufe nutzen den Cache. Ein kurzes Kommando-Zeitlimit bricht den ersten Lauf ab — kein Fehler der Konfiguration.

### Vom BMP zum ansehbaren Bild

Die **einzige ausführliche Quelle** dafür; README, CLAUDE.md, Dokument 04 und
die YAML-Köpfe verweisen nur hierher.

ESPHome schreibt **BMP** (1280 x 800, 24 Bit, 3.072.054 Bytes je Bild), und eine
Assistenz-Sitzung kann BMP **nicht** öffnen. Der Screenshot-Lauf allein erledigt
die Rendering-Kontrolle aus Dokument 04 deshalb nicht. Zwei geprüfte Wege, beide
aus dem Projektordner:

```
sips -s format png shots/*.bmp --out shots/

~/.venvs/esphome-beta/bin/python -c "from PIL import Image; import glob; [Image.open(f).save(f[:-4]+'.png') for f in glob.glob('shots/*.bmp')]"
```

`sips` bringt macOS mit, Pillow steckt in der ESPHome-Umgebung. Beide legen die
PNG neben die BMP und lassen die BMP stehen. Je nach Seite und Weg wiegt die PNG
rund 10 bis 120 kB — Pillow packt dichter als `sips` (nachgemessen über alle
damals neun Bilder: 9,9 bis 96,3 kB gegen 21,6 bis 116,2 kB). Angesehen wird danach die
**PNG**.

Ausschnitt vergrößern, wieder mit Pillow — `crop` nimmt
`(links, oben, rechts, unten)` in Bildpunkten, also dieselben Koordinaten wie
im YAML:

```
~/.venvs/esphome-beta/bin/python -c "from PIL import Image; im = Image.open('shots/01_overview.png').crop((908, 76, 1280, 460)); im.resize((im.width*2, im.height*2)).save('shots/zoom.png')"
```

---

Stand: 25.09.2026, abends (Referenz-Entitäten statt Anker, „nicht belegt“ per `none`, `val_leer` = −∞ samt Rechenregeln, Abschnitt „Tests“, Zeilennummern von Kern, Übersicht und Datenweg neu abgezählt); davor 25.09.2026, später Tag (Datenweg von Home Assistant samt Dummy-Paket, Eingabeskripte `ov_*`, `flow_ch`, `dev_present` und `dev_apply`, Flussanimation mit 37 Leitungen, Tabelle und Skriptliste neu abgezählt); davor 25.09.2026 (Meldungen: Lagebild, Zähler mit Filter, Zusammenfassen, `alert_clear`; danach alle Zeilennummern der Tabelle und der Skriptliste neu abgezählt, Seitenliste in Reiterreihenfolge, `sys_panel`-Maße, `voice_panel_hide`, MDI-Font auf v7.4.47); davor 24.09.2026 (Seiten Wallboxen, Wärmepumpe und Haus samt ihren
Skripten, Tabelle neu abgezählt); davor 23.09.2026 (eigene Anlage in `.pv-dashboard_anlage.yaml`, Seite PV &
Prognose samt `pv_update` und `pv_redraw_curve`, Tabelle und Zeilennummern neu
abgezählt; davor 20.09.2026: Streckenzahlen aus einem Vorschaulauf; Zeilennummern gegen
den **Arbeitsstand** dieses Tages, Umwandlungsbefehle und Bildgrößen
nachgemessen; Tabelle nach den Standardblöcken in Übersichts- und Speicherseite
neu abgezählt; am selben Tag auf die fertige Paketstruktur samt Lizenz und
Inbetriebnahme nachgezogen). Geprüfter Stand: Commit `0e2bd3d` (25.09.2026); die
Zeilennummern gelten für den Arbeitsstand danach und können von diesem Commit abweichen.
