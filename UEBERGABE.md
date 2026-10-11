# Übergabe — Stand 11.10.2026

Diese Datei ist für die Weiterarbeit an anderer Stelle. Sie fasst zusammen, was
gebaut ist, wie gearbeitet wird und was offen ist. Das Fachwissen steht in
`docs/01` bis `docs/06`; hier stehen nur Verweise darauf. Die Regeln in
`CLAUDE.md` gelten weiter, vor allem die zu Geheimnissen.

## Stand in einem Satz

Das Panel (Waveshare ESP32-P4, 10,1 Zoll, LVGL 9) läuft seit dem 10.10.2026
an der Wand mit Release #13. Es bekommt alle Werte aus Home Assistant, die
Kugeln laufen ruhig, und das blaue Flackern ist weg.

## Wo was steht

| Thema | Datei |
|---|---|
| Anlage, Kennzahlen, Einheitenregeln | `docs/01-anlage-und-kennzahlen.md` |
| Hardware, Panel, Funkchip C6, Flashen | `docs/02-hardware-und-panel.md` |
| Aufbau der Dateien, Datenweg, Tests, Diagnose | `docs/03-dashboard-aufbau.md` |
| Prüfliste nach jeder Layoutänderung | `docs/04-lvgl-checkliste.md` |
| ESPHome-Version, Umstieg | `docs/05-esphome-2026-9-umstieg.md` |
| Offene Punkte mit Entscheidungsstand | `docs/06-offene-punkte-und-plaene.md` |
| Arbeitsregeln (Geheimnisse, Git, Bauen) | `CLAUDE.md` |

Erzeugte Dateien nie von Hand ändern:

- `.pv-dashboard_ha.yaml` und `ha/pv_dashboard_dummy.yaml` kommen aus
  `tools/ha_bindings.py --write`.
- Der Block `# >>> flow-animation` und die Widgets `flNN`/`flNNb` kommen aus
  `tools/flow_animation.py`.

## Arbeitsweise

- **Zweige.** Gearbeitet wird auf `dev`. Das Gerät baut per Remote-Package aus
  `main` (`ref: main`, `refresh: always`). Ein Release ist ein PR `dev` →
  `main`.
- **Freigaben des Nutzers (Stand 11.10.2026).** Was gebaut werden darf, darf
  ohne weitere Rückfrage committet, als PR gestellt und gemergt werden.
- **Prüfen vor jedem Release:**
  - `python -m unittest discover tests` (40 Tests)
  - `python tests/ha_probe.py --shots` (76 Prüfungen gegen ein nachgebautes
    Home Assistant, dazu der Bildlauf)
  - Die PNG-Bilder unter `shots/` ansehen.
- **Gerätedateien.** `pv-dashboard.yaml` und die eigene
  `.pv-dashboard_anlage.yaml` liegen im ESPHome-Ordner von Home Assistant.
  Die Anlagedatei bleibt außerhalb des Repos (`.gitignore`). Ihre Werte, also
  Entitäts-IDs, Namen und Tarife, gehören nie ins Repo.
- **Flashen per WLAN** über den Device Builder (Kanal dev, 2026.11.0-dev).
  Dessen WebSocket `/ws` nimmt `firmware/install` mit
  `{configuration: "pv-dashboard.yaml", port: "OTA"}`; den Stand liefert
  `firmware/get_job`. Bauen und Hochladen sind zwei Jobs. Scheitert der Start
  nach einem OTA, fällt das Panel auf die alte Firmware zurück. Nach einem
  seriellen Flash gibt es diesen Rückfall nicht.
- **Diagnose.** Mit dem Schalter „Diagnose“ in Home Assistant liefert das
  Panel alle 10 s Bildzeit, Fläche, Kugeltakt und Loop-Zeit als Sensoren
  (`docs/03`, „Diagnose“).

## Was am 10. und 11.10.2026 geschah

| Release | Inhalt |
|---|---|
| #10 | Tageswerte aus der HA-Statistik, Prognose je Dach, Audio entfernt, leerer Start, Diagnose-Sensoren, Co-Prozessor-Update automatisch |
| #11 | `loop_task_stack_size: 32768`: Mit 8 KB lief der Stapel in `setup()` über, das Panel startete nicht |
| #12 | Pixeltakt 60 statt 80 MHz gegen DSI-Unterlauf (blaues Flackern); Statistik-Abfragen beim Start gestaffelt |
| #13 | Gegen das Ruckeln: Labels nur bei neuem Text (`lbl_set`), Gruppen in 100-ms-Takten. Abrufe ohne Antwort werden wiederholt. PV- und Hausverbrauch gesamt als Summe mehrerer Zähler |

Messung am Panel vor und nach #13:

| Größe | vorher | nachher |
|---|---|---|
| Bild max | 60 bis 140 ms | etwa 30 ms |
| Fläche max | bis 190.000 px | 20.000 bis 40.000 px |
| Abstand der Kugelschritte (Soll 20 ms) | 80 bis 183 ms | etwa 55 ms |

Die alten Audio-Entitäten sind am 11.10.2026 aus Home Assistant gelöscht.

## Offen

**Wartet auf den Nutzer**

- [ ] **Einmaliges „Blitzen“** kurz nach dem Start von #13 (11.10.2026, etwa
      eine Minute nach dem Neustart). Vermutung: ein einzelner DSI-Unterlauf
      beim ersten vollen Bild. Bestätigt ist das nicht. Gesucht sind Uhrzeit
      und die Logzeile `lcd.dsi: … underrun`. Kommt es wieder, sind die Wege:
      Pixeltakt weiter senken (60 → 50 MHz) oder `buffer_size` verkleinern
      (`docs/06`, „Ruckeln der Kugeln“).
- [ ] **DWD-Warnstufe.** In Home Assistant gibt es nur NINA-Warnungen, keine
      Integration „DWD Weather Warnings“. Empfohlen: diese Integration
      einrichten und `ha_warn_level` auf ihren Sensor „aktuelle Warnstufe“
      setzen. Die Alternative ist ein Umbau des Panels auf NINA.
- [ ] **Statistikseite am Gerät ansehen.** Erzeugung und Verbrauch sollten
      sich seit #13 füllen. Gesehen hat das noch niemand.

**Am Gerät zu prüfen**

- [ ] **„TCP buffer full“ beim Start.** Seit #12 kommt die Meldung nur noch
      einmal je Start. Seit #13 fragt das Panel verlorene Abrufe nach 30 s neu
      ab (Log `ha`: „… Antworten fehlen, frage erneut“). Noch nicht im Log
      gesehen.
- [ ] **WLAN- und HA-Teil des Systemfensters**, die Wallbox-Knöpfe mit evcc.
- [ ] **Farbwirkung im Tageslicht, Touch und Scrollen** (`docs/06`, „Nur am
      Gerät prüfbar“).
- [ ] **Bluetooth-Proxy.** `esp32_ble` hält `loop()` beim Start knapp 300 ms.
      Wird der Proxy nicht gebraucht, wäre Abschalten der einfachste Gewinn.
      Das ist nicht entschieden.

**Später, als eigenes Release**

- [ ] **ESP-IDF 6.0.3** statt 6.0.2, erst wenn das Panel stabil läuft.
- [ ] **Release-Tag setzen** und `ref:` in `pv-dashboard.yaml` auf den Tag
      statt auf `main` stellen, sobald es stabil läuft.

**Bewusst offen (nur auf Zuruf bauen)**

- [ ] **BMS-Anbindung.** Sie ist ein Platzhalter. Bis dahin tragen alle drei
      Speicher die Werte der Deye-Bank, auch die Zyklen; Zellwerte fehlen.
      Zu klären sind die paceic-Version und die Zahl der BMS (`docs/06`, „BMS“).
- [ ] **Mini-WR.** Er ist noch nicht angeschlossen und bleibt ausgeblendet.
- [ ] **Nicht in Home Assistant vorhanden:** Neutralleiterstrom und die
      Leistung eines Verbrauchers (Spülmaschine). Diese Werte bleiben leer.
- [ ] **Kamera, Meldungen über einen Neustart speichern, weiteres Steuern
      vom Panel aus.** Die Gründe stehen in `docs/06`.
- [ ] **Quittung nach Home Assistant, Remote-Packages beibehalten?** Das ist
      noch nicht entschieden (`docs/06`).

## Fallstricke

- `esphome config pv-dashboard.yaml` zeigt wegen der Remote-Packages die
  Geheimnisse aufgelöst. Die Ausgabe nie speichern oder weitergeben
  (`CLAUDE.md`).
- `lv_label_set_text` macht ein Label auch bei gleichem Text ungültig. In
  Seitenskripten deshalb immer `id(lbl_set)(obj, text)` nehmen.
- `homeassistant.action` mit `capture_response`: Eine wegen vollen
  Sendepuffers verworfene Anfrage bekommt weder `on_success` noch `on_error`.
  Abrufe brauchen deshalb einen eigenen Zähler (`ha_offen`).
- Ein Faktor `ha_<name>_faktor` rechnet Vorzeichen und Einheit um. Die
  Anzeigeeinheit in Home Assistant dann nicht zusätzlich umstellen.
- `ha_pv_energy_total` und `ha_home_energy_total` dürfen kommagetrennte
  Listen sein. Die übrigen Schlüssel nehmen genau eine Entität.
