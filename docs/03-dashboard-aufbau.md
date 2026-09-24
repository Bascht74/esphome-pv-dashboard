# 03 — Aufbau des Dashboards

## Dateien und Packages

`pv-dashboard.yaml` (Gerät) und `pv-dashboard-sim.yaml` (Simulator: `host:` plus
SDL-Fenster 1280 x 800) binden dieselben zwei gemeinsamen Packages ein:

- `.pv-dashboard_utility.yaml` — in zwei Abschnitten: Plex Sans / Mono,
  Symbolschriften und die Bilder aus `images/`, dann Farben, Maße, `alert_max`,
  `idle_timeout`. Die drei Tarife standen bis zum 20.09.2026 hier und gehören
  jetzt zu den Anlagen-Einstellungen (Dokument 01)
- `.pv-dashboard_ui.yaml` — der Kern der Oberfläche: Tagesreihen, gemeinsame
  Skripte, `lvgl:`-Basis, Stile, Verläufe, `top_layer`. Die neun Seiten hängen
  als eigene Packages daran (`.pv-dashboard_page_*.yaml`)

Nur am Gerät: `.pv-dashboard_display.yaml` (I2C, Backlight, DSI-Panel, GT911;
eigener `lvgl:`-Block mit `rotation: 90`), `.pv-dashboard_audio.yaml`
(Audio/Voice) und `.pv-dashboard_core.yaml` — darin alles, was aus dem Panel ein
Gerät macht: SoC, PSRAM, LDO, Funkstrecke zum C6, WLAN, API, Logger, OTA,
Bluetooth, `dash_time` und die Diagnose-Entities, RS485/RS232.

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

Die Oberfläche liegt in **zehn** Dateien: dem Kern `.pv-dashboard_ui.yaml` und
je einer Datei pro Seite. Der Kern bindet die Seiten über einen eigenen
`packages:`-Block ein — **diese Reihenfolge ist die Reihenfolge der Seiten**.
ESPHome hängt Listen aus Packages in der Reihenfolge aneinander, in der die
Packages deklariert sind; die Reiter der Menüleiste zählen auf dieselbe Ordnung:
Übersicht, PV, Speicher, Wallbox, Wärmepumpe, Haus, Netz, Statistik, Meldungen.

| Datei | Zeilen | Blöcke, Zeilennummern |
| --- | --- | --- |
| `.pv-dashboard_ui.yaml` | 1182 | `packages:` 31, `text:` 51, `globals:` 81, `script:` 167, `lvgl:` 359, `interval:` 1179 |
| `.pv-dashboard_page_overview.yaml` | 1281 | `substitutions:` 35, `globals:` 97, `sensor:` 115, `script:` 149, `lvgl:` 263, `interval:` 1082 |
| `.pv-dashboard_page_pv.yaml` | 460 | `globals:` 31, `script:` 49, `lvgl:` 229 |
| `.pv-dashboard_page_battery.yaml` | 323 | `substitutions:` 35, `script:` 42, `lvgl:` 104 |
| `.pv-dashboard_page_wallbox.yaml` | 436 | `substitutions:` 48, `script:` 52, `lvgl:` 184 |
| `.pv-dashboard_page_heatpump.yaml` | 368 | `script:` 49, `lvgl:` 178 |
| `.pv-dashboard_page_house.yaml` | 771 | `substitutions:` 61, `script:` 68, `lvgl:` 463 |
| `.pv-dashboard_page_grid.yaml` | 346 | `substitutions:` 50, `script:` 54, `lvgl:` 204 |
| `.pv-dashboard_page_stats.yaml` | 400 | `globals:` 31, `script:` 46, `lvgl:` 217 |
| `.pv-dashboard_page_alerts.yaml` | 431 | `script:` 20, `lvgl:` 268 |

Im Kern steht nur, was alle Seiten teilen: die Tagesreihen `day_curve` und
`forecast_curve`, die Globals `ota_running` 82, `curve_day` 90, `data_seen` 100
und `data_stale_reported` 105, die Formatierer `fmt_num` 115, `fmt_watt` 129 und
`fmt_power` 145 (Dezimalkomma, Tausenderpunkt, Striche bei `NAN`; alle Seiten
benutzen sie), die Skripte `sys_refresh` 174, `record_hour` 249 und
`update_clock` 304, unter `lvgl:` die Basis, `style_definitions` 406,
`gradients` 483 und `top_layer` 773, und am Ende das `interval:` für
`sys_refresh`. Einen
`pages:`-Schlüssel hat der Kern **nicht** — die Seiten bringen ihn mit.

**Jedes Skript liegt bei der Seite, die es benutzt:** `money_update` 163 und
`redraw_curve` 192 in der Übersicht, `pv_status` 59, `pv_update` 104 und
`pv_redraw_curve` 151 auf der Seite PV & Prognose, `storage_update` 49 im Speicher,
`wallbox_update` 73 und `wallbox_month` 170 bei den Wallboxen, `heatpump_update` 72
und `heatpump_extra` 145 bei der Wärmepumpe, `house_flow` 85, `house_battery` 279,
`house_loadpoint` 314, `house_update` 358 und `house_history` 405 im Haus,
`grid_update` 65, `grid_phase` 113, `grid_meter` 147 und `grid_rules` 176 im Netz,
`stats_update` 58, `stats_show` 89 und `stats_redraw` 115 in der Statistik,
`alert_push` 56, `alert_ack` 170 und `alert_refresh` 202 in den Meldungen. Im Kern
bleiben nur `sys_refresh`, `record_hour` und `update_clock`: Sie fassen kein
Seiten-Widget an, sondern die Tagesreihen beziehungsweise die Leisten und
Fenster im `top_layer`, und sie werden aus Packages gerufen, die keine Seite
sind (`_core`, `-sim`, `-shots`) oder aus dem Kern selbst.

Vier Seiten tragen vor ihrem `script:` einen eigenen `substitutions:`-Block
mit den Standardbeschriftungen (Dokument 01): Übersicht und Speicher seit dem
20.09.2026, Wallboxen und Haus seit dem 24.09.2026; deshalb beginnt der Rest
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
grep -n '^    - id: page_'  .pv-dashboard_page_*.yaml    # die neun Seiten
grep -n '!include'          .pv-dashboard_ui.yaml        # die Seitenreihenfolge
```

## Seiten

Neun Seiten, Fläche **1280 x 800** (quer). Drei Leisten liegen im `top_layer`, überdecken jede Seite und werden **nie** versteckt: `bar_status` (y 0 bis 44), die Meldungszeile `bar_alert` mit `lbl_alert` (y 44 bis 76) und die Reiterleiste `bar_nav` mit `nav_matrix` (y 744 bis 800).

Die Meldungszeile steht auch ohne Meldung da — `lbl_alert` zeigt dann „Keine Meldungen" bzw. „Keine offenen Meldungen", ein Tipp öffnet die Meldungsseite. Für Seiteninhalt bleiben deshalb **1280 x 668**, y 76 bis y 744: die Höhe, gegen die Regel 1 aus Dokument 04 rechnet.

Kachelkonvention im Repo: x 4, Breite 1272, Kacheln von **y 84 bis y 736** — je 8 px Luft zur Meldungszeile und zur Menüleiste. `schema_area` nutzt die Fläche dagegen voll (x 4, y 76, 904 x 668).

- `page_overview` – links das Anlagenschema (`schema_area`, 904 × 668, 28 Leitungen), rechts die Kennzahlenspalte: Tagesverlauf (16 `bar`-Widgets `bar_h00`…`bar_h15` plus Prognoselinie `line_forecast`; ESPHomes LVGL hat kein chart-Widget), vier Kacheln der Energiebilanz, Tagesertrag, Ringe Autarkie und Eigenverbrauch.
- `page_battery` – drei SoC-Ringe und Tabelle `tbl_storage`: Ladezustand, Strom, Zelle min/max, Zelldifferenz, Temperatur min/max, Zyklen. Erste fertig gebaute Detailseite — **Vorlage für jede neue**.
In der Statusleiste stehen seit dem 25.09.2026 rechts neben der Mitte drei Symbole (`sys_icons`, x 700, 110 × 30): WLAN, Home Assistant, Daten aktuell. Ein Tipp öffnet das Fenster `sys_panel` im `top_layer` (600 × 520 bei x 340, y 150), ein Tipp darauf schließt es. Inhalt und Regeln in Dokument 06, „Systemstatus“.

- `page_pv` – seit 23.09.2026. Oben zwei Kacheln wie die zwei Energiekreise: links Volleinspeisung (x 4, 322 breit), rechts Hausnetz (x 334, 942 breit); je Wechselrichter eine Gruppe aus Wechselrichterkasten und seinen zwei Flächen, Leistung in W und Tageswert in kWh. Unten dieselbe Teilung: links vier Kennzahlen (Ist heute, Prognose heute, Restprognose, Ist zu Prognose der abgeschlossenen Stunden), rechts der Tagesverlauf mit 16 Balken und Prognoselinie im großen Maßstab. Seit 25.09.2026 zeigt jeder Wechselrichterkasten einen Statuspunkt (grün / rot) und die Temperatur in der Unterzeile; bei Störung wird der Rahmen rot und die Unterzeile zeigt den Fehlertext (`pv_status`). Geometrie und Höhenrechnung im Kopf der Datei.
- `page_alerts` – Liste `alert_list`, Kopfkachel mit Zähler, Knöpfe „Alle quittieren“ und „Liste leeren“.
- `page_wallbox` – seit 24.09.2026, am selben Tag nach dem Vorbild von evcc (0.316.0) umgebaut. Zwei Ladepunkt-Karten je 632 × 512: Kopf mit Name und Modus-Schalter Aus / Smart / Schnell, Sitzungswerte Leistung (mit Blitz und drei Phasenstrichen), Geladen, Sonne, Ladedauer; nach der Trennlinie Fahrzeug und Statuszeile, Ladestandsbalken mit dunklerem Rest bis zum Limit und Limit-Marke, darunter Ladestand (mit Reichweite), Ladeplan, Ladelimit. Unten die Monatskachel „Ladevorgänge im Monat“ (Geladen, Sonnenanteil, Kosten, Ø Preis). Akzent `col_evcc`, Flächen und Einheitenregel bleiben die des Dashboards. Höhenrechnung im Kopf der Datei.
- `page_heatpump` – seit 24.09.2026, am selben Tag auf die **Nilan Compact P** umgebaut, im Aufbau der Startseite des Touch-Bedienteils CTS700 (der Nutzer hat das klassische CTS700 mit Textzeilen, will die Seite aber grafisch), auf Wunsch des Nutzers auf dem Dashboard-Grund (Kachel `st_tile`). Links die Nilan-Kachel (760 × 652): Außentemperatur mit Sonne, grünes Haus aus Flächen (`col_nilan_house`; Dach = Quadrat 311 × 311, um 45° gedreht, in einem Behälter mit `transform_scale_y` 0,682 gestaucht, darüber die Wand, damit die Kante am Dachfuß verdeckt ist; Rechnung im Kommentar der Datei), im Dach die Raumtemperatur mit Sollwert, in der Wand Feuchte, CO2 (nur mit Wert sichtbar) und die Warmwasserkachel (`col_nilan_tank`, Rand `col_nilan_tank_edge`) mit rotem Punkt für die Zusatzheizung und Sollwert darunter, rechts die runde Lüftertaste mit Stufe und Zu-/Abluftventilator in %. Unter dem Haus ein gelber Hinweis, solange Enteisung oder Legionellenschutz laufen. Rechts „Information“ wie hinter der Info-Taste (Betriebsart Lüftung, Jahreszeit, Bypass, Kompressor, Zu- und Fortluft, Ventilatoren, Tage bis zum Filterwechsel, ab 7 Tagen gelb) und „Strom“ (Leistungsaufnahme, Verbrauch heute). Das Nilan-Logo ist bewusst nicht nachgebaut.
- `page_grid` – seit 25.09.2026, Netz und Zähler. Vier Kacheln je 632 breit: Hausanschluss (Leistung, grün bei Einspeisung und rot bei Bezug, Frequenz, Balken der Einspeisung gegen die Einspeisegrenze `feed_limit_pct` von `pv_kwp` mit gelber Marke, Grenze in kW, Auslastung, abgeregelte Energie heute), Phasen L1 bis L3 (Spannung, außerhalb 207 bis 253 V gelb, Strom, Wirk- und Scheinleistung, Leistungsfaktor, Neutralleiterstrom), Zählerstände (fünf Zählwerke mit Stand und heute) und Netzvorgaben (Einspeisegrenze, Börsenpreis, rot wenn negativ, negative Viertelstunden, Vergütung bei negativem Preis, Steuersignal § 14a, Smart Meter). Werte nach dem Shelly Pro 3EM, Rechtliches in Dokument 06.
- `page_stats` – seit 25.09.2026, Statistik. Kopf mit Zeitraum, Umschalter Woche / Monat / Jahr und fünf Kennzahlen (Erzeugung, Verbrauch, Autarkie, Eigenverbrauch, Ertrag in €), darunter Balkenpaare Erzeugung (gelb) und Verbrauch (hell) auf gemeinsamem Maßstab, bis 31 Plätze. Autarkie = (Verbrauch − Bezug) / Verbrauch, Eigenverbrauch = (Erzeugung − Einspeisung) / Erzeugung. Die Reihen liegen nur im RAM.
- `page_house` – seit 24.09.2026, am selben Tag nach dem Energiefluss von evcc umgebaut. Oben der evcc-Balken (Eigenverbrauch PV, Eigenverbrauch Speicher, Netzbezug, Einspeisung; Breite nach Anteil) mit den Klammern „In“ (PV, Speicher, Netz) und „Out“ (Verbrauch, Ladepunkte, Speicher laden, Einspeisung) samt Symbolen und Legende. Darunter die ausgeklappte Tabelle in drei Spalten: In (Erzeugung mit Restprognose, Speicher entladen mit Unterzeilen je Speicher, Netzbezug mit Preis), Out (Verbrauch mit Preis, Ladepunkte mit Unterzeilen je Wallbox, Speicher laden, Einspeisung mit Vergütung) und Verbraucher (Wärmepumpe, vier Geräte, Grundlast mit kWh heute). Unten links „Verbrauch jetzt“ (Haus und Ladepunkte) mit Herkunft aus PV, Speicher und Netz als Balken und in %, rechts der Verbrauch der letzten 24 Stunden als Stundenbalken, der PV-gedeckte Teil grün. Farben `col_evcc*`. Geometrie im Kopf der Datei.

**Neue Detailseite.** Vorlage ist `page_battery`. Dazu gehört:

- Kachelkonvention wie oben: x 4, Breite 1272, y 84 bis 736.
- `scrollable: false` **auch auf der Seite selbst** — eine Seite ist ebenfalls
  ein Objekt (Dokument 04, Punkt 4).
- Nav-Knopf und Screenshot-Eintrag sind **schon da**: `nav_matrix` trägt alle
  neun Knöpfe (`btn_nav_overview` … `btn_nav_alerts`), und der Screenshot-Lauf
  nimmt jede Seite auf (`04_wallbox.bmp` und so fort). Eine **zehnte** Seite
  braucht einen neuen Knopf in `nav_matrix` (Breiten neu rechnen), einen Eintrag in
  `shots_nav_clear` und einen eigenen Bildschritt in `pv-dashboard-shots.yaml`.
- Die Flussanimation **nicht** neu erzeugen, solange keine Leitung im Schema
  angefasst wird.
- Datenanbindung: eigene Skript-Schnittstelle nach dem Muster
  `storage_update(...)`, bis dahin Strichmuster — siehe Dokument 06.
- Danach die Checkliste aus Dokument 04, vollständig.

Ebenfalls im `top_layer`, aber normalerweise versteckt: die Overlays `voice_panel` und `ota_panel`. Bei Untätigkeit (`$idle_timeout`, 240 s) fällt die Oberfläche über `on_idle` auf die Übersicht zurück; das Abdunkeln macht derselbe Timeout im Display-Package.

## Tokens und Stile

Einzige Quelle für Farben und Maße; die Regeln für Werte und Einheiten stehen in Dokument 01.

Flächen `col_bg`, `col_surface`, `col_line`; Text `col_ink`, `col_ink2`, `col_ink3`. Leitungen werden nach **Quelle** gefärbt: `col_solar` (Hausnetz-Kreis), `col_full` (Volleinspeisung), `col_batt`, `col_feed`, `col_draw`, dazu `col_warn`/`col_crit`. Maße: `pad_page` 4, `pad_tile` 10, `gap_tile` 8, `radius_tile` 11, `radius_box` 10.

`style_definitions`: `st_tile` (Kachel), `st_box` (Gerätekasten), `st_label`, `st_unit`, `st_sub`, `st_alert_row`, `st_btn`.

## Verläufe

Kräftiger Look, Entscheidung des Nutzers vom 12.09.2026: deutliche Schemaflächen, Licht hinter dem Hausnetz, Randverläufe an den Energiekacheln; die RGB565-Stufen dabei sind in Kauf genommen (Dokument 04). Vorhanden: drei konische Ringverläufe, `grad_day_bar` (Stundenbalken), `grad_lit_*` (Dachgruppen), `grad_box_*` (Schein in den getönten Gerätekästen), `grad_hub` (RADIAL) plus `grad_hub_shade`, `grad_tile_*` (HOR, Kachelkanten), `grad_yield` (LINEAR). `col_tint_*`, `col_box_*`, `col_glow_*` und `col_lit_tail` sind auf die RGB565-Stufen hin gewählt.

Welcher Verlaufstyp wo erlaubt ist und wie die Töne dazu gewählt werden, steht in Dokument 04 (RGB565).

## Skripte und ihre Schnittstellen

Angebunden wird später nur über diese Skripte; wo noch etwas fehlt, steht in Dokument 06.

**`alert_push(severity, device, text)`** – 0 = Info, 1 = Warnung, 2 = Störung; fügt oben in `alert_list` ein, `mode: queued`, `max_runs: $alert_max`. Zeilenaufbau (Reihenfolge nicht umstellen, Zugriff per Index): 0 Schweregrad, 1 Zeit, 2 Gerät, 3 Meldung, 4 Hinweis, 5 Quelle „Gerät: Meldung“, versteckt mit `long_mode: CLIP`. Kind 5 ist nötig, weil `DOT` den Textpuffer verändert (Dokument 04, Punkt 3). Der Zeitstempel steckt im `user_data`. Über `$alert_max` (50) hinaus fällt die älteste **quittierte** Zeile heraus, sonst die älteste überhaupt.

**`alert_ack(row)`** – `row` = Zeilenindex, `-1` = alle offenen. Quittiert heißt gedämpft, nicht gelöscht: Die Zeile bleibt in der Chronologie. Wohin die Quittung später läuft, ist offen (Dokument 06).

**`alert_refresh`** – zählt offene Meldungen, setzt Zeitangaben (heute nur Uhrzeit, sonst mit Datum), Kopfzeile, Meldungszeile und Knöpfe. Läuft aus `on_add`/`on_remove`, nach dem Quittieren, beim Tageswechsel und beim ersten gültigen Zeitpunkt nach dem Start – von Hand ruft es niemand.

**`storage_update(bat, soc, current, cell_min, cell_max, temp_min, temp_max, cycles)`** – `bat` 0…2 = Speicher 1…3, `current` positiv = Laden, `NAN` bzw. `cycles < 0` ergibt „--“. Füllt Spalte `bat + 1` der Tabelle, den Ring und den Mittelwert (nur bei allen drei Werten), die Batteriekästen der Übersicht noch nicht.

**`pv_update(inv, pv, power, energy)`** – Seite PV & Prognose. `inv` 0…3 = Wechselrichter 1…4, `pv` 0…7 = Fläche/Modul 1…8, jeweils `-1` = keiner; ein Aufruf setzt einen Wechselrichter, eine Fläche oder beides. `power` in W, ganzzahlig mit Tausenderpunkt; `energy` in kWh heute, eine Nachkommastelle. `NAN` ergibt das Strichmuster (`--.---` bzw. `-.---`, `W · --,- kWh`). Füllt nur die PV-Seite, die Kästen im Schema der Übersicht noch nicht.

**`wallbox_update(wb, mode, charging, power, phases, energy, solar, minutes, vehicle, status, soc, range, limit, plan)`** – Seite Wallboxen, Namen nach der evcc-API. `wb` 0…1 = Wallbox 1…2; `mode` `off`/`smart`/`now` (ältere evcc-Versionen: `pv` und `minpv` leuchten als Smart); `charging` färbt Blitz und Phasen; `power` in kW, `phases` 0…3, `energy` Sitzung in kWh, `solar` Sonnenanteil in %, `minutes` Ladedauer (< 0 = keine); `vehicle` leer = „Kein Fahrzeug“, `status` freie Zeile; `soc` und `limit` in %, `range` in km, `plan` Text wie „Mo 07:00“ (leer = kein Plan). `NAN` ergibt Striche. Füllt nur diese Seite, die Wallbox-Kästen der Übersicht noch nicht.

**`wallbox_month(energy, solar, cost, price)`** – Monatskachel der Wallbox-Seite: geladene kWh, Sonnenanteil in %, Kosten in €, Durchschnittspreis in ct/kWh. `NAN` ergibt Striche.

**`heatpump_update(outdoor, room, humidity, co2, dhw, eheat, fan, vent_mode, season, bypass, compressor, supply, exhaust, power, energy, alarm)`** – Seite Wärmepumpe (Nilan Compact P). Temperaturen in °C: außen, Raum (Abluft), Warmwasser, Zu- und Fortluft; `humidity` in %, `co2` in ppm (`NAN` blendet die CO2-Gruppe aus); `eheat` zeigt den roten Punkt der Zusatzheizung; `fan` Lüftungsstufe 0…4 (0 = „Aus“, < 0 = unbekannt); `vent_mode`, `season`, `bypass`, `compressor` als Text (leer ergibt „--“); `power` in kW und `energy` in kWh heute, beide elektrisch; `alarm` 0 = nichts, 1 = gelbes, 2 = rotes Warnsymbol. Setzt „Stand HH:MM“. Füllt nur diese Seite, den Kasten im Schema noch nicht.

**`heatpump_extra(room_set, dhw_set, fan_supply, fan_extract, filter_days, defrost, legionella)`** – weitere Werte der Compact P aus dem Registersatz des klassischen CTS700: Sollwerte Raum und Warmwasser in °C, Zu- und Abluftventilator in %, Tage bis zum Filterwechsel (< 0 = unbekannt), Enteisung und Legionellenschutz als Schalter. Adressen und ihre Unsicherheit in Dokument 06.

**`house_flow(pv, bat_out, grid_in, home, loadpoints, bat_in, grid_out, soc, forecast, price_grid, price_home, price_feed)`** – Seite Haus, Energiefluss nach evcc. Leistungen in W (≥ 0) für den Hausnetz-Kreis: PV-Erzeugung, Speicher entladen, Netzbezug, Verbrauch (alles außer Ladepunkten und Speicher, also mit Wärmepumpe), beide Ladepunkte zusammen, Speicher laden, Einspeisung; dazu Speicher-SoC in %, Restprognose in kWh und drei Preise in ct/kWh. Rechnet Eigenverbrauch wie evcc (erst PV, dann Speicher) und füllt Balken, Klammern, die Spalten In und Out und „Verbrauch jetzt“. `NAN` ergibt Striche.

**`house_battery(bat, power, soc)`** und **`house_loadpoint(wb, power, soc)`** – Unterzeilen der Tabelle: je Speicher (0…2, Leistung in W, positiv = entladen) bzw. je Wallbox (0…1, Ladeleistung in W, `soc` des Fahrzeugs, `NAN` = kein Fahrzeug). `house_loadpoint` zählt auch die aktiven Ladepunkte (ab 10 W).

**`house_update(dev, power, energy)`** – Spalte Verbraucher. `dev` 0…5 = Wärmepumpe, Backofen, Waschmaschine, Spülmaschine, Trockner, Grundlast (`name_heatpump`, `name_oven` … `name_baseload`), `power` in W, `energy` in kWh heute. Die Kopfzeile zeigt die Summe, sobald alle sechs da sind.

**`house_history(home, solar, hour)`** – Verbrauch der letzten 24 Stunden: je 24 kommagetrennte kWh-Werte, älteste zuerst, `solar` der aus PV gedeckte Teil, `hour` die Uhrzeit des letzten Werts. Wird nicht gespeichert (Dokument 06).

**`pv_status(inv, ok, text, temp)`** – Zustand eines Wechselrichters (`inv` 0…3): `ok` false färbt Rahmen und Punkt rot, zeigt `text` (leer = „Störung“) in der Unterzeile und legt beim Wechsel in die Störung **eine** Meldung (Schwere 2) an; `temp` in °C erscheint hinter dem Tageswert, `NAN` blendet sie aus.

**`money_update(full_feed, surplus, self_use, grid_in)`** – Übersicht, Kachel Tagesertrag. Energien heute in kWh: Volleinspeisung, Überschusseinspeisung, selbst verbrauchter PV-Strom, Netzbezug. Rechnet mit den drei Tarifen Förderung, Ersparnis, Bezugskosten und Ertrag, schreibt Kachel, globals und vier Sensoren (Dokument 06, „Geldwerte“).

**`grid_update(power, freq, curtailed, n_current)`** – Seite Netz: Leistung am Hausanschluss in W (positiv = Bezug, negativ = Einspeisung, wie `total_act_power` des Shelly Pro 3EM), Frequenz in Hz, heute abgeregelte kWh, Neutralleiterstrom in A.

**`grid_phase(phase, voltage, current, power, apparent, pf)`** – eine Phase (0…2 = L1…L3): V, A, W (positiv = Bezug), VA, Leistungsfaktor.

**`grid_meter(meter, total, today)`** – ein Zählwerk: 0 Hausanschluss Bezug, 1 Hausanschluss Einspeisung, 2 PV-Zähler Einspeisung, 3 Hauszähler Bezug, 4 Hauszähler Einspeisung; Stand und heute in kWh.

**`grid_rules(limit_active, spot_ct, neg_quarters, neg_paid, p14a_active, p14a_kw, smart_meter)`** – Netzvorgaben: Einspeisegrenze aktiv, Börsenpreis in ct/kWh, negative Viertelstunden heute (< 0 = unbekannt), Vergütung bei negativem Preis, Steuersignal § 14a mit Grenze in kW, Smart Meter und Steuerbox eingebaut.

**`stats_update(range, period, labels, prod, cons, imp, exp, money)`** – Seite Statistik: `range` 0 Woche, 1 Monat, 2 Jahr; `period` Zeitraum als Text; `labels` und die vier Reihen (Erzeugung, Verbrauch, Bezug, Einspeisung in kWh) kommagetrennt, gleich viele Werte; `money` Ertrag in €. **`stats_show(range)`** schaltet um und zieht die Knöpfe mit.

**`sys_refresh`** – Kern, alle 10 s und beim Öffnen des Systemfensters: Alter der Werte je Quelle aus `data_seen`, Symbole, WLAN, Home Assistant, Laufzeit, Version (Dokument 06). Von Hand ruft es niemand.

**`pv_redraw_curve`** – Seite PV & Prognose, hängt wie `redraw_curve` an `on_value` beider Reihen und schreibt keine. Zeichnet Balken und Linie auf gemeinsamem Maßstab (Legende nennt die Skala) und rechnet die Kennzahlen: „abgeschlossen" sind die Plätze vor der laufenden Stunde (Stunde − 6), Restprognose ist die Prognose ab der laufenden Stunde bis 22 Uhr, „Ist zu Prognose" braucht mindestens 0,1 kWh Prognose in den abgeschlossenen Stunden. Ohne gültige Uhrzeit bleiben diese beiden auf Strichen.

**`record_hour`** – läuft zur vollen Stunde um HH:00:05 und schreibt die abgelaufene Stunde in Platz `(HH-1) - 6` (06–07 Uhr → Platz 0, 21–22 Uhr → Platz 15). Angebunden wird an der auskommentierten Zeile `// kwh = id(<Erzeugungssensor>).state;`; solange sie steht, wird 0 eingetragen. Die Tagesreihen `day_curve` und `forecast_curve` sind `text`-Entitäten mit 16 kommagetrennten Werten im NVS: überstehen Neustart und OTA, in HA sichtbar und setzbar. Gespeichert wird nur, was über `control()` kommt – daher `make_call()`, nicht `publish_state()`. Tageswechsel über das global `curve_day` (Jahr × 1000 + Tag): Gehört die Reihe zu einem anderen Tag, startet der Lauf mit 16 × 0.

**`redraw_curve`** – hängt an `on_value` beider Reihen, zeichnet Balken (Ist) und Linie (Prognose) auf gemeinsamem Maßstab und setzt die Unterzeile mit beiden Tagessummen. Schreibt keine Reihe: keine Schleife.

**`update_clock`** – `mode: restart`, gerufen bei `on_time_sync` und zu jeder vollen Minute. Setzt Uhr und Datum (Wochentag und Monat von Hand, `strftime` liefert Englisch) und stößt beim Tageswechsel `alert_refresh` an. Während eines Firmware-Updates (`ota_running`) tut es nichts – der Redraw kostet PSRAM-Bandbreite, die der Upload braucht; künftige periodische Anzeigen fragen das Flag ebenso ab.

**`display_wake`** – nur Gerät (Display-Package), `mode: restart`, ausgelöst von `on_touch` des GT911; fährt das Backlight in 150 ms auf 100 %.

## Flussanimation

Die Kugeln sind erzeugter Code. `tools/flow_animation.py` liest die Leitungen aus `.pv-dashboard_page_overview.yaml`, leitet die Topologie aus den Koordinaten ab und schreibt die Kugel-Widgets (`flNN`, `flNNb` am Anfang von `schema_area`) und den Block zwischen `# >>> flow-animation` und `# <<< flow-animation`.

```
python3 tools/flow_animation.py            # Vorschau, schreibt nichts
python3 tools/flow_animation.py --write    # baut die Animation ein
```

Der Vorschaulauf meldet drei Zahlen: **28 Leitungen, daraus 37 Teilstrecken und 20 Übergänge**. Die vierte, **53 Liniensegmente**, meldet er nicht — sie steht nur im erzeugten Block: 37 ist die Länge von `WATT[]`, `pos[]` und `dots[]`, 53 die von `SX`, `SY`, `EX`, `EY` und `SL`; beides lässt sich dort abzählen. Diese Zahlen nie schätzen.

**Den Block nie von Hand ändern.** Nach jeder Änderung an den Leitungen das Skript erneut laufen lassen; ein Lauf ohne Änderung schreibt nichts. Die Leistung je Teilstrecke steht in `WATT[]` – die Sensoranbindung dort steht in Dokument 06.

Eckwerte: Takt 20 ms, Kugeln 8 px, Deckel 13 Bewegungen je Tick – LVGL merkt sich nur 32 ungültige Flächen je Bild, jede Bewegung kostet zwei. Die 13 steht als Konstante `MAXMOVE` in `tools/flow_animation.py`; im erzeugten Block ist sie ausgeschrieben, ein `grep MAXMOVE` über die YAML findet also nichts.

## Simulator und Screenshots

Ein `esphome` im PATH gibt es **nicht**. Beide Läufe starten aus dem
Projektordner, mit vollem Pfad in die Arbeitsumgebung (ESPHome 2026.9.0):

```
~/.venvs/esphome-beta/bin/esphome run pv-dashboard-sim.yaml
~/.venvs/esphome-beta/bin/esphome run pv-dashboard-shots.yaml
```

`pv-dashboard-sim.yaml` öffnet ein SDL-Fenster und **blockiert**, bis das Fenster geschlossen wird; **F12** speichert ein Bild nach `.esphome/snapshots/pv-dashboard-sim/`, `ESPHOME_SNAPSHOT_DIR` lenkt es um.

`pv-dashboard-shots.yaml` bindet den Simulator als Package ein, rendert headless alle neun Seiten, die Statistik zusätzlich als Monat, plus die drei Fenster als BMP (`01_overview.bmp` … `12_system.bmp`) nach `shots/` unter dem Startverzeichnis und beendet sich selbst – deshalb im Projektordner starten. `snapshot.take` überschreibt nie, darum löscht `shots_take` vorher.

Beispieldaten für Meldungen, Speicher, PV-Werte, Wallboxen, Wärmepumpe, Haus, Tagesreihen und Ringe stehen in `shots_run`, also **nur** im Screenshot-Lauf. Die Demo-Leistungen der Flussanimation stehen dagegen unter `#ifdef USE_HOST` und laufen auf der ganzen host-Plattform, im Simulator ebenso. Im Gerät steht beides nicht.

**Laufzeit.** `-sim` und `-shots` sind **getrennte Bauziele** unter `.esphome/build/`. Der erste Lauf eines Ziels ist ein Vollbuild über mehrere Minuten und holt die Schriften über `gfonts://` aus dem Netz; spätere Läufe nutzen den Cache. Ein kurzes Kommando-Zeitlimit bricht den ersten Lauf ab — kein Fehler der Konfiguration.

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

Stand: 24.09.2026 (Seiten Wallboxen, Wärmepumpe und Haus samt ihren
Skripten, Tabelle neu abgezählt); davor 23.09.2026 (eigene Anlage in `.pv-dashboard_anlage.yaml`, Seite PV &
Prognose samt `pv_update` und `pv_redraw_curve`, Tabelle und Zeilennummern neu
abgezählt; davor 20.09.2026: Streckenzahlen aus einem Vorschaulauf; Zeilennummern gegen
den **Arbeitsstand** dieses Tages, Umwandlungsbefehle und Bildgrößen
nachgemessen; Tabelle nach den Standardblöcken in Übersichts- und Speicherseite
neu abgezählt; am selben Tag auf die fertige Paketstruktur samt Lizenz und
Inbetriebnahme nachgezogen). Geprüfter Commit: `c6a432f` (12.09.2026) — dort liegen die
Zeilennummern ab `alert_push` vier höher.
