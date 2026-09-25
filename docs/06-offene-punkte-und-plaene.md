# 06 — Offene Punkte und Pläne

Was noch aussteht, jeweils mit Entscheidungsstand. Nichts davon wird ungefragt gebaut.

## ToDo

Kurzfassung aller offenen Punkte; die Einzelheiten stehen jeweils im Abschnitt
darunter. „Vertagt" heißt: entschieden, aber bewusst später — nicht ungefragt bauen.

**Erledigt am 23.09.2026**

- [x] **Eigene Werte aus `pv-dashboard.yaml` herausgelöst.** Beschriftungen und Tarife
      stehen in `.pv-dashboard_anlage.yaml`, die in `.gitignore` steht; im Repo liegt
      nur die Vorlage. Siehe „Was das Repo über die Anlage verrät".
- [x] **Detailseite PV & Prognose gebaut.** Siehe „Detailseiten".

**Erledigt am 24.09.2026**

- [x] **Detailseiten Wallboxen, Wärmepumpe und Haus gebaut**, auf Zuruf des Nutzers.
      Siehe „Detailseiten".
- [x] **Wallboxen nach evcc, Wärmepumpe nach dem Nilan-Bedienteil umgebaut**, auf
      Wunsch des Nutzers; seine Wärmepumpe ist eine Nilan Compact P.

**Erledigt am 25.09.2026** (nach dem Projekt-Review, auf Zuruf des Nutzers)

- [x] **Seite Netz und Zähler** (Shelly Pro 3EM, Einspeisegrenze, Zählerstände,
      Netzvorgaben) und **Seite Statistik** (Woche, Monat, Jahr). Siehe „Netz,
      Zähler und Netzvorgaben“ und Dokument 03.
- [x] **Systemstatus und Alter der Daten**: Symbole oben rechts, Systemfenster,
      Meldung bei veralteten Werten. Siehe „Systemstatus“.
- [x] **Wechselrichter-Status mit Fehlertext** (`pv_status`).
- [x] **Geldrechnung Tagesertrag** (`money_update`), Werte als globals und
      Sensoren für Home Assistant. Siehe „Geldwerte“.
- [x] **Haus der Wärmepumpenseite aus Flächen** statt aus `images/house.png`;
      Bild und Schrift `f_icon_l` entfernt, Kommentare zu `!secret` berichtigt.
- [x] **Nilan: klassisches Bedienteil** (zwei Textzeilen) bestätigt, Registersatz
      entsprechend umgestellt; die Seite bleibt grafisch.
- [x] **Seiten Prognose (Solcast) und Wetter (DWD)**, auf Zuruf des Nutzers. Siehe
      „Prognose und Wetter“. Menüleiste mit elf Reitern, der PV-Reiter heißt „PV“.

**Erledigt am 25.09.2026, später Tag** (auf Zuruf des Nutzers)

- [x] **Datenweg von Home Assistant** gebaut: `.pv-dashboard_ha.yaml`, erzeugt von
      `tools/ha_bindings.py`, dazu das Dummy-Paket `ha/pv_dashboard_dummy.yaml` für
      Home Assistant. Siehe „Echte Daten anbinden“ und Dokument 03.
- [x] **Übersicht speisbar**: Eingabeskripte `ov_*`, Flussanimation liest `flow_ch`
      statt fester `WATT[]` (Regel 9 im Werkzeug).
- [x] **Fehlende Geräte ausblenden**: `dev_present`, `dev_apply`; Leitungen und Kugeln
      nach Regel 10. Screenshots `*_reduced`. Seit dem Abend des 25.09.2026 ohne
      eigene Anker-Entitäten: Je Gerät zeigt eine **Referenz-Entität** aus der
      Zuordnung an, ob es da ist (Referenz ohne Wert → Grafik weg, andere Entität
      ohne Wert → nur der Wert leer); `ha_<name>: none` für „nicht belegt“;
      `dev_present` nicht mehr im NVS. Leer ist −∞ (`val_leer`), plattformunabhängig
      nach IEEE 754, auch auf dem RISC-V des P4 (Dokument 03).
- [x] **Tests** (25.09.2026): `tests/` mit unittest für beide Werkzeuge und
      `ha_probe.py`, das Panel gegen ein nachgebautes Home Assistant (Dokument 03,
      „Tests“).

**Entschieden, nicht zu tun**

- [x] **Commit-Historie bereinigen** — am 20.09.2026 verworfen. Nicht erneut
      vorschlagen.

**BMS (Vorbereitung steht, Umsetzung wartet auf Klärung)**

- [ ] **paceic-Version klären** — `protocol_commandset` 0x20 oder 0x25, nur am Gerät
      feststellbar.
- [ ] **Anzahl der BMS und Zuordnung zu `bat` 0…2 klären** — sind die Packs verkettet?
      Eine Strecke kann drei Packs führen (Master/Slave), aber nur bei 0x25; die
      Topologie nicht raten.
- [ ] **`check_uart_settings` in `nkinnan/esphome-pace-bms`** — der abgekündigte Aufruf
      steht noch drin, das Repo ruht seit 11.12.2025; ab ESPHome 2027.3.0 bricht der
      Build. Ein Patch liegt seit 23.09.2026 in `patches/`, eingesetzt wird er mit
      dem BMS (Anleitung unter „BMS: serielle Anbindung").

**Vertagt (Entscheidung liegt vor, Zeitpunkt offen)**

- [ ] **Echte Daten anbinden** — der Weg steht (Datenweg, 25.09.2026), angebunden
      sind vorerst Dummy-Entitäten. Offen: gegen ein echtes Home Assistant testen,
      dann die echten IDs eintragen. Siehe „Echte Daten anbinden“.
- [ ] **Kamera** — blockiert durch esphome/esphome#16944. Am 20.09.2026 vertagt, der
      PR-Stand ist seit 11.09.2026 nicht nachgeprüft.

**Am Gerät zu erledigen**

- [ ] **OTA-Schritt 2** — `password:` durch `encryption: {}` ersetzen, erst nach der
      ersten erfolgreichen OTA-Installation einer 9.0-Firmware.
- [ ] **Audio-Halbduplex testen** — achtstufiger Testplan in Dokument 05.
- [ ] **Farbwirkung im Tageslicht, Bildzeit, Touch und Scrollen** prüfen.

**Entscheidungen, die noch niemand getroffen hat**

- [ ] **Quittung nach Home Assistant** — wie die Quittung zurücklaufen soll, ist nicht
      notiert.
- [ ] **Remote-Packages beibehalten?** — der Bezug aus dem Repo kostet je Änderung
      einen `push`.

## Detailseiten

Die vier geplanten Detailseiten sind gebaut; dazu seit dem 25.09.2026 Netz,
Statistik, Prognose und Wetter. Jede liegt in ihrer eigenen Datei
`.pv-dashboard_page_*.yaml`, eingebunden vom `packages:`-Block in
`.pv-dashboard_ui.yaml`. **PV & Prognose ist seit dem 23.09.2026 gebaut**, auf
Zuruf des Nutzers („mit der ersten anfangen"): Wechselrichter und Flächen je
Energiekreis, darunter der Tagesverlauf Ist gegen Prognose mit vier Kennzahlen
(Aufbau in Dokument 03). Die Schnittstelle ist `pv_update(inv, pv, power, energy)`,
bis Sensoren daran hängen stehen Striche. Angezeigt werden alle acht Plätze, also
die sechs Dachflächen und die zwei Einzelmodule am Mini-WR — die Festlegung
unten nennt nur „sechs Strings"; das ist eine Annahme, die der Nutzer bestätigen
oder ändern kann.

**Wallboxen, Wärmepumpe und Haus sind seit dem 24.09.2026 gebaut**, auf Zuruf
des Nutzers („die weiteren Detailseiten bauen“). Aufbau in Dokument 03, die
Schnittstellen (`wallbox_*`, `heatpump_*`, `house_*`) ebenda;
bis Sensoren daran hängen, stehen Striche. Annahmen, die der Nutzer bestätigen
oder ändern kann:

- **Wallboxen:** Inhalt nach der Ladepunkt-Karte von evcc 0.316.0 (Modus,
  Leistung mit Phasen, Geladen, Sonnenanteil, Ladedauer, Fahrzeug, Status,
  Ladestand mit Reichweite, Ladeplan, Ladelimit) plus Monatswerte wie unter
  „Ladevorgänge“. Angenommen ist, dass evcc die Werte liefert (über Home
  Assistant oder MQTT); welche Felder die Anbindung wirklich bekommt, steht
  erst dann fest. Kosten und Durchschnittspreis setzen Tarife in evcc voraus.
- **Wärmepumpe:** Nilan Compact P mit dem **klassischen Bedienteil CTS700**
  (zwei Textzeilen, Angabe des Nutzers vom 25.09.2026). Die Seite bleibt auf
  seinen Wunsch grafisch, im Aufbau der Startseite des Touch-Bedienteils; die
  Farben sind aus dem Bild der Nilan-Anleitung abgelesen, keine offiziellen
  Werte. Das Haus ist seit dem 25.09.2026 aus LVGL-Flächen gebaut (ein um 45°
  gedrehtes Quadrat, gestaucht, darunter die Wand), nicht mehr aus einem Bild. Die
  Compact P heizt Luft und Warmwasser und hat keinen Heizwasserkreis:
  **Vorlauf, Rücklauf und COP der Festlegung vom 30.07.2026 entfallen**, dafür
  Raumtemperatur, Feuchte, CO2, Lüftungsstufe, Zu- und Fortluft, Bypass,
  Sommer/Winter und Kompressorbetrieb. Leistungsaufnahme und Tagesverbrauch
  sind elektrisch und kommen nicht aus der Nilan-Steuerung selbst, sondern
  vermutlich von einem Zähler (offen). Auf Wunsch des Nutzers steht die Seite
  auf dem Dashboard-Grund; Haus und Warmwasserkachel sind dafür abgedunkelt
  (weiße Schrift 6,5 bzw. 8,2 : 1, gerechnet).
- **Nilan-Modbus (Recherche 24./25.09.2026, nicht am Gerät geprüft).** Mit dem
  klassischen Bedienteil gilt der **ältere CTS700-Satz (Rev. 2.01)**, Adressen
  1xxx/2xxx/4xxx/5xxx. In `src/cts700Data.ts` von github.com/matej/homebridge-nilan
  (am 25.09.2026 nachgelesen) stehen: Betriebsart der Anlage 1047 (0 Idle,
  1 Auto, 2 Verlängert, 3 Manuell, 4 LON, 5 Service), Pause 4727, gewünschte
  Lüftungsstufe 4747, Raum-Sollwert 4746 (°C × 10), Außen 5152, Feuchte 4716,
  Zuluftventilator 4699 (Abluft 4700 laut `docs/cts700-diagnostics.md` dort),
  Filter-Intervall Zu-/Abluft 1326/1327 und verstrichene Tage 1328/1329,
  Warmwasser oben/unten 5162/5163, Warmwasser-Sollwert 5548, Lüftungsmodus
  2402, Regelmodus 5432, Softwarestand 5065. **Nicht in dieser Quelle belegt**
  und deshalb offen, bis jemand am Gerät liest: Zuluft-, Abluft- und
  Fortlufttemperatur (in der Recherche vom 24.09.2026 als 5153 bis 5155
  notiert), Enteisung (5450), Legionellenschutz (4748) und die
  Sommer/Winter-Umschalttemperatur (2406); Bypass, Kompressor und
  Zusatzheizung sind gar nicht gefunden. **CO2, eine Jahreszeit und ein
  Alarmregister gibt es in diesem Satz nicht**: Die CO2-Gruppe bleibt ohne Wert
  ausgeblendet, Jahreszeit und Warnsymbol bleiben leer, solange keine andere
  Quelle sie liefert (Home Assistant kann die Jahreszeit aus Außentemperatur
  und Umschaltwert ableiten).
  Die zwei anderen Sätze gelten damit **nicht**: der neuere Satz des
  Touch-Bedienteils („CTS700 Modbus User Guide“, 2018, Adressen 2xxxx) und der
  CTS602-Satz (github.com/veista/nilan, laut dessen README nicht für CTS700).
  Eine Leistungs- oder Energieangabe hat keiner der drei Sätze.
  Der Wärmepumpen-Kasten im Schema zeigt deshalb statt COP die
  Warmwassertemperatur („kW · WW 51°C“, gesetzt von `heatpump_update`).
- **Haus:** Umgebaut nach dem Energiefluss von evcc (Wunsch des Nutzers,
  24.09.2026). Annahmen: Alle Leistungen gelten für den Hausnetz-Kreis, die
  Volleinspeisung bleibt außen vor. „Verbrauch“ ist wie in evcc alles außer
  Ladepunkten und Speicher, also mit Wärmepumpe; „Verbrauch jetzt“ zählt die
  Ladepunkte dazu. Die Herkunft rechnet die Seite wie evcc (erst PV, dann
  Speicher, Rest Netz). Preise kommen als Werte herein (Mischpreis des
  Verbrauchs wie in evcc). Die Grundlast kommt als eigener Wert, die Seite
  rechnet sie nicht aus. **Offen:** Die 24-Stunden-Reihe wird nicht
  gespeichert und ist nach einem Neustart leer, bis die Quelle sie neu
  liefert; soll sie wie `day_curve` im NVS stehen, braucht sie eine eigene
  `text`-Entität.

Geplanter Inhalt (Festlegung 30.07.2026):

- **PV & Prognose** — sechs Strings einzeln, Volleinspeise-Kreis getrennt, Prognose gegen Ist-Verlauf (gebaut 23.09.2026)
- **Wallboxen** — beide: Modus, Ladeleistung, geladene Energie, Fahrzeug-SoC (gebaut 24.09.2026, nach evcc erweitert)
- **Wärmepumpe** — Betriebsmodus, Vorlauf/Rücklauf, COP, Leistungsaufnahme, Tagesverbrauch (gebaut 24.09.2026; für die Compact P ohne Vorlauf/Rücklauf/COP, siehe oben)
- **Haus** — Backofen, Waschmaschine, Spülmaschine, Trockner einzeln, plus Grundlast (gebaut 24.09.2026, nach evcc um Energiefluss, Verbrauch jetzt und 24 Stunden erweitert)

**Entscheidungsstand:** erledigt, alle vier geplanten gebaut (23. und 24.09.2026). Vorher
bewusst vertagt: Der Nutzer hatte am 30.07.2026 ausdrücklich gesagt, die
Detailseiten kommen später und sollen nicht ungefragt gebaut werden. Am 12.09.2026 für die
Verläufe wiederholt: Ringe, Tagesbalken und Akzente zuerst nur in der Übersicht, die
Detailseiten PV, Haus, Wallbox und WP bleiben für später.

**Schnittstelle je Seite.** Wird eine gebaut, bekommt sie ihre **eigene**
Skript-Schnittstelle nach dem Muster von `storage_update(...)`: ein Skript mit benannten
Parametern, das nur Widgets füllt. Bis Sensoren daran hängen, steht in den Widgets das
Strichmuster aus Dokument 01 (Regel „Fehlender Wert") — keine erfundenen Zahlen. So
gebaut sind die Skripte aller Detailseiten (Liste in Dokument 03, „Skripte und
ihre Schnittstellen“); die Aufrufe kommen erst mit den Sensoren. Was beim Anlegen einer Seite sonst
dazugehört (Kachelkonvention, `scrollable`, nav-Knopf, Screenshots, Flussanimation), steht
in Dokument 03 unter „Neue Detailseite".

## Erledigt: Zweitzeile der Autarkie-Kachel

Die Autarkie-Kachel der Übersicht zeigt im Ring den **Tageswert**, ihre Zweitzeile stand in
`.pv-dashboard_page_overview.yaml` aber auf „Monat -- %". Am 20.09.2026 hat der Nutzer bestätigt: Das
„Monat" war ein Versehen, es bleibt beim Tageswert. **Erledigt** — das Widget `sub_autarky`
trägt jetzt `text: "Heute -- %"`, der Kommentar darüber nennt die Kennzahl-Festlegung.
Definitionen in Dokument 01, Abschnitt „Autarkie".

## Was das Repo über die Anlage verrät

Seit dem 20.09.2026 sind alle anlagenabhängigen Beschriftungen und die drei Tarife
`substitutions` mit neutralen Demo-Werten; die eigenen Werte stehen seit dem
23.09.2026 in `.pv-dashboard_anlage.yaml` außerhalb des Repos (Dokument 01). Am selben Tag sind auf Wunsch des Nutzers auch die
Namen nachgezogen worden, die eine Beschriftungsänderung überdauern — **erledigt**:

- **Die Widget-IDs der Übersichtsseite** nannten Fabrikat und echte Dachflächen.
  Sie heißen jetzt nach Stellung und Aufgabe: die acht Flächen `v_roof_1` …
  `v_roof_8` und `e_roof_1` … `e_roof_8` von links nach rechts, in derselben
  Zählung wie `name_pv_1` … `name_pv_8`; die Wechselrichter `v_wr_full`,
  `v_wr_mini`, `v_wr_hybrid1`, `v_wr_hybrid2` und die `e_`-Geschwister dazu.
  Alle IDs kommen **nur** in `.pv-dashboard_page_overview.yaml` vor; der erzeugte
  Flussanimations-Block nennt keine von ihnen (nachgeprüft mit `grep` über das Repo
  und über `tools/flow_animation.py`). Die neun Screenshots sind nach dem
  Umbenennen unverändert — IDs werden nicht gezeichnet.
- **Der Tarifschlüssel des Volleinspeise-Kreises** nannte das Fabrikat und heißt
  jetzt `tarif_volleinspeisung_ct` — in der Anlagen-Datei, im Standard in
  `.pv-dashboard_page_overview.yaml` und in Dokument 01.
- **Die Dokumente beschrieben die echte Anlage** — Fabrikate, Typenbezeichnungen,
  echte Dachflächennamen, Speichergröße, Förderdauer, das BMS-Kit. Dokument 01, die
  Anlagenbeschreibung in `README.md` und dieses Dokument beschreiben jetzt den
  Aufbau: Wechselrichter, Speicher und Flächen sind neutral; Wärmepumpe (Nilan
  Compact P) und Netzzähler (Shelly Pro 3EM) sind bewusst benannt, weil die
  Seiten darauf zugeschnitten sind. Was zur Anlage des Nutzers gehört, steht in seinen privaten Notizen
  außerhalb des Repos.

**Erledigt: die eigenen Werte liegen nicht mehr in einer versionierten Datei.** Bis
zum 23.09.2026 standen sie im Block „HIER BESCHREIBEN SIE IHRE ANLAGE“ von
`pv-dashboard.yaml`, die versioniert ist; ein `git add -A` hätte sie mitgeschoben.
Seitdem stehen sie in `.pv-dashboard_anlage.yaml`, die `.gitignore` ausschließt;
`pv-dashboard.yaml` fügt sie mit `<<: !include` in ihre `substitutions` ein, der
Vorrang vor den Standards bleibt derselbe (Dokument 01). Im Repo liegt nur die
Vorlage `.pv-dashboard_anlage.yaml.example` mit den Demo-Werten. Fehlt die eigene
Datei, bricht `esphome config` mit „Could not find file“ ab — wie bei einer
fehlenden `secrets.yaml`. `pv-dashboard.yaml` selbst bleibt versioniert, damit
Änderungen an Paketliste und `min_version` weiter beim Nutzer ankommen.

**Die Commit-Historie bleibt, wie sie ist.** Ältere Commits tragen den Stand vor
dieser Generalisierung. Am 20.09.2026 hat der Nutzer nach Vorlage der Einzelheiten
entschieden, daran nichts zu ändern. **Entscheidungsstand: entschieden, nicht erneut
vorschlagen.**

Ein weiterer Punkt bleibt offen; er blockiert das Öffentlichmachen nicht:

- **Der Beispieltext des Sprachassistenten** in `pv-dashboard-shots.yaml` nennt
  „Wallbox 1" im Fließtext. Er ist absichtlich nicht auf `${name_wb_1}` umgestellt:
  Der Satz hat einen Artikel davor („Die Wallbox 1 meldet …"), bei einem frei
  gewählten Namen würde der Satz grammatisch schief. Demo-Prosa, nur im
  Screenshot-Lauf, nie auf dem Gerät.

## Erledigt: Packages kommen aus dem Repo

Seit dem 20.09.2026 lädt `pv-dashboard.yaml` die Packages aus dem GitHub-Repo
(`ref: main`, `refresh: 1d`); die lokale Variante steht auskommentiert als
Rückfall daneben (Dokument 03).

Folgen, beide in Dokument 03 belegt: Das Gerät baut aus dem geschobenen Stand,
jede Änderung braucht erst einen `push`; und `esphome config` zeigt die Werte aus
`secrets.yaml` aufgelöst statt als `!secret '<name>'` — die Ausgabe deshalb nie in
eine Datei umleiten und nie weitergeben.

## Netz, Zähler und Netzvorgaben

Seite `page_grid`, gebaut am 25.09.2026 auf Zuruf des Nutzers („Fehlende Infos
können wir vom Shelly Pro 3EM nehmen“). Aufbau in Dokument 03.

**Shelly Pro 3EM (Hausanschluss).** Die Phasenwerte sind nach `EM.GetStatus`
benannt (Shelly-API-Dokumentation Gen2, Komponente EM): `a_voltage`,
`a_current`, `a_act_power`, `a_aprt_power`, `a_pf` (b, c ebenso), `n_current`,
`total_act_power`; die Zählerstände nach `EMData.GetStatus`
(`total_act`, `total_act_ret`). Vorzeichen: positiv = Bezug. Die Frequenz
liefert je nach Firmware `a_freq` usw.; nicht am Gerät geprüft. Angebunden
wird am einfachsten über die Home-Assistant-Integration des Shelly; Modbus TCP
kann der Shelly auch, dort ist die Adresszählung (ab 0 oder 1) in den Quellen
nicht eindeutig.

**Rechtslage (Recherche 25.09.2026, keine Rechtsberatung; was gilt, sagt der
Netzbetreiber).** Quellen: EEG 2023 §§ 9, 51, 51a und EnWG § 14a auf
gesetze-im-internet.de, Stand der Änderungen durch das „Solarspitzengesetz“
vom Februar 2025.

- **60 % ist für Inbetriebnahme 2026 richtig.** § 9 Abs. 2 EEG: Anlagen unter
  100 kW mit Einspeisevergütung, die ohne intelligentes Messsystem und
  Steuerbox in Betrieb gehen, dürfen höchstens 60 % der installierten Leistung
  einspeisen, **bis** Messsystem und Steuerung eingebaut und getestet sind.
  Danach fällt die Grenze. `feed_limit_pct` steht deshalb auf 60.
- **Negative Preise:** Neue Anlagen bekommen für Viertelstunden mit negativem
  Börsenpreis keine Vergütung (§ 51); die ausgefallenen Zeiten werden nach
  § 51a am Ende des Förderzeitraums angehängt. Kleine Anlagen ohne
  intelligentes Messsystem sind davon ausgenommen **bis zum Ende des Jahres,
  in dem es eingebaut wird** (Übergang, deshalb `neg_paid`).
- **§ 14a EnWG:** Steuerbar sind Wallboxen, Wärmepumpen und netzladende
  Speicher über 4,2 kW; im Signal darf der Netzbetreiber auf mindestens 4,2 kW
  je Gerät drosseln (bei einem Energiemanagement für mehrere Geräte nach
  Formel mehr, für zwei Wallboxen rund 7,6 kW). Die **Wallboxen fallen
  darunter**, die Nilan Compact P mit ihrer kleinen Leistungsaufnahme
  vermutlich nicht (Einschätzung, nicht geprüft).

**Beide Kreise zusammen oder nur einer?** Am 25.09.2026 im Gesetzestext
nachgelesen (§ 9 EEG auf gesetze-im-internet.de): Begrenzt wird „am
Verknüpfungspunkt“ mit dem Netz auf 60 % der installierten Leistung, und nach
§ 9 Abs. 3 gelten mehrere Solaranlagen auf demselben Grundstück oder Gebäude,
die innerhalb von zwölf aufeinanderfolgenden Kalendermonaten in Betrieb gehen,
für die installierte Leistung als **eine** Anlage. Hängen beide Kreise am selben
Hausanschluss und gehen beide 2026 in Betrieb, ist die Summe richtig: `pv_kwp` =
Modulleistung beider Kreise, gemessen wird die Einspeisung am Hausanschluss (so
rechnet die Seite). Anders nur, wenn ein Kreis mehr als zwölf Monate früher in
Betrieb ging (dann zählt er nicht mit) oder einen eigenen Netzanschluss hat.
Ab zusammen 25 kW verlangt § 9 Abs. 2 Nr. 2 zusätzlich eine Einrichtung, mit
der der Netzbetreiber die Einspeisung fernsteuern kann. Keine Rechtsberatung.

**Offen:** Was der Wechselrichter als „abgeregelt heute“ liefert, hängt am Fabrikat.

## Prognose und Wetter

Seiten `page_forecast` und `page_weather`, gebaut am 25.09.2026 auf Zuruf des
Nutzers. Aufbau und Skripte in Dokument 03.

**Prognose (Solcast).** Welche Werte, hat der Nutzer vorgegeben: die, die sein
Blueprint `ha-pv-optimizer` (github.com/Bascht74/ha-pv-optimizer, am 25.09.2026
gelesen) benutzt. Das sind aus der Solcast-Integration (HACS) der Sensor „heute“
mit dem Attribut `detailedForecast` (Halbstunden mit `pv_estimate`,
`pv_estimate10`, `pv_estimate90` in kW), „verbleibend heute“, „aktuelle Leistung“,
„nächste Stunde“ (mit `estimate10`) und die Folgetage morgen, Tag 3, Tag 4 (mit
`estimate10`, optional `detailedForecast`). Die Seite zeigt die Rohwerte P10, P50,
P90; die Mischung aus P50 und P10, mit der der Blueprint plant, rechnet sie nicht
nach. Spitze mit Uhrzeit, Tage 5 bis 7 und die API-Zähler benutzt der Blueprint
nicht; sie stehen hier, weil die Integration sie anbietet (Annahme: Sensoren
„Peak forecast“, „Peak time“, „API used“, „API limit“; Namen am Gerät prüfen).

**Wetter (DWD).** Quelle ist die HACS-Integration „DWD Weather“ des Nutzers. Die
Skripte sind nach den Feldern der Home-Assistant-Wettervorhersage benannt
(`condition`, `temperature`, `templow`, `precipitation`,
`precipitation_probability`, `wind_speed`, `wind_bearing`, `wind_gust_speed`,
`cloud_coverage`, `humidity`, `pressure`), geholt über `weather.get_forecasts`
(stündlich und täglich). **Nicht geprüft:** unter welchem Namen die Integration
die Sonnenscheindauer liefert und ob stündlich oder nur täglich; Warnungen kommen
aus der eigenen Integration „DWD Weather Warnings“ (Warnstufe und Text). Der
Blueprint benutzt das Wetter nur für die Temperatur; Wetterbilder, Regen und Wind
sind für die Anzeige dazugekommen.

## Systemstatus

Seit dem 25.09.2026. Oben rechts in der Statusleiste drei Symbole: WLAN,
Verbindung zu Home Assistant (API), Daten aktuell. Ein Tipp öffnet das
Systemfenster (`sys_panel`): WLAN, Home Assistant, Laufzeit, ESPHome-Version,
Grenze für veraltete Werte und das Alter der letzten Werte je Seite (PV,
Speicher, Wallboxen, Wärmepumpe, Haus, Netz, Prognose, Wetter). Jedes Update-Skript stempelt
`data_seen[n]`; `sys_refresh` läuft alle 10 s. Älter als `data_stale_s`
(300 s, `.pv-dashboard_utility.yaml`) färbt das Symbol gelb und legt **einmal**
je Quelle eine Warnung in die Meldungsliste. Solange eine Quelle noch nie
geliefert hat, gilt sie nicht als veraltet (sonst stünden vor der Anbindung
acht Warnungen da). Seit dem 25.09.2026 gilt: Fehlt die Verbindung zu Home
Assistant (WLAN oder API), kommt statt einer Warnung je Quelle **eine**
Sammelmeldung „Keine Verbindung zu Home Assistant“ (Störung, sobald eine Quelle
schon geliefert hat); sie verschwindet, wenn die Verbindung wieder steht.

## Geldwerte

Seit dem 25.09.2026 rechnet `money_update(full_feed, surplus, self_use,
grid_in)` in der Übersicht aus den drei Tarifen (Dokument 01): Förderung =
Volleinspeisung × Tarif + Überschuss × Tarif, Gespart = Eigenverbrauch ×
Bezugstarif, Bezug = Netzbezug × Bezugstarif, Ertrag = Förderung + Gespart −
Bezug. Auf Wunsch des Nutzers stehen die Werte als **globals**
(`money_subsidy`, `money_saved`, `money_import`, `money_total`) für andere
Lambdas bereit und als **Sensoren** („Ertrag heute“, „Förderung heute“,
„Ersparnis heute“, „Bezugskosten heute“, Einheit €) in Home Assistant. Die
Energien kommen von außen; die Seite Statistik nimmt den Ertrag eines
Zeitraums als fertigen Wert (`stats_update`).

## Echte Daten anbinden

Alle Seiten sind gebaut. Seit dem 25.09.2026 steht der **Datenweg von Home
Assistant** (`.pv-dashboard_ha.yaml`, erzeugt von `tools/ha_bindings.py`, nur Gerät):
Jeder Wert kommt als `homeassistant`-Sensor, gedrosselt auf einen Aufruf je Gruppe und
Sekunde, Listen über `homeassistant.action` mit Antwort. Nach der Entscheidung des
Nutzers zeigen die Standard-IDs vorerst auf **Dummy-Entitäten**
(`ha/pv_dashboard_dummy.yaml`), die Historie hält Home Assistant und das Panel holt sie
nach jedem Start per `recorder.get_statistics`, fehlende Geräte blendet die
Referenz-Entität je Gerät aus (ohne gültigen Wert → Grafik weg; `ha_<name>: none` =
nicht belegt). Einzelheiten in Dokument 03, „Datenweg von Home Assistant“.

Offen am Datenweg:

- [ ] **Gegen ein echtes Home Assistant testen.** Geprüft ist bisher das Paket
      samt Simulator gegen ein nachgebautes Home Assistant (`tests/ha_probe.py`:
      echte API-Verbindung, Jinja2 außerhalb von Home Assistant für die Vorlagen). Offen: ob
      Home Assistant die Vorlagen so rendert (strenger Modus, `as_datetime` auf den
      Zeitangaben der Statistik), ob die Antwort als Objekt oder als Text ankommt
      (beides wird gelesen), wie groß die Antworten werden, und die Option „Allow
      the device to perform Home Assistant actions“.
- [ ] **Echte IDs eintragen** — die Standards sind Vorschläge (deutsche IDs, Platzhalter
      für Shelly-Gerät, DWD-Station und Warnzelle, evcc-Ladepunkte, Wechselrichter,
      Nilan). Nach `.pv-dashboard_anlage.yaml`, nur die abweichenden.
- [ ] **Annahmen prüfen:** Vorzeichen von `sensor.evcc_battery_power` (+ = Entladen) und
      der Zählerleistungen (+ = Einspeisung); Einheit der Ladedauer (Anzeige in min);
      `sun_duration` der DWD-Tagesprognose in Sekunden; „Sonstige“ = evcc-Hausverbrauch
      ohne Wärmepumpe; „solar“ der 24-h-Reihe = Verbrauch − Netzbezug; Ertrag der
      Statistik aus Erzeugung, Einspeisung, Volleinspeisung und Bezug mit den Tarifen;
      Überschuss ohne Hauszähler = Einspeisung − Volleinspeisung.
- [ ] **Speicher über Home Assistant nur zum Testen** — das BMS kommt nativ ans Panel
      (unten); dann fallen die `bat*`-Zeilen der Tabelle weg.
- [ ] **Netzseite** blendet fehlende Zähler noch nicht aus (nur Übersicht und die Seiten
      PV, Speicher, Wallboxen, Wärmepumpe, Haus).
- [ ] **Laufende Stunde** fehlt in `house_history` und `day_curve`, bis Home Assistant
      die Stundenstatistik geschrieben hat (Minute 2 der Folgestunde).

**Tagesreihe.** In `record_hour` steht eine einzige auskommentierte Quellzeile für die
Erzeugung der abgelaufenen Stunde in kWh: `// kwh = id(<Erzeugungssensor>).state;`. Solange
sie auskommentiert ist, wird 0 eingetragen. Am Gerät schreibt der Datenweg `day_curve`
stündlich ganz neu aus der Statistik (Erzeugung heute 06 bis 22 Uhr) und `forecast_curve`
aus den Solcast-Halbstunden; die Quellzeile bleibt für eine native Quelle.

**Speicher.** `storage_update(...)` füllt Tabellenspalte und Ring der Speicherseite;
Signatur und Sonderwerte stehen in Dokument 03. Künftige BMS-Sensoren rufen nur dieses
Skript auf.

**Die Batteriekästen der Übersicht füllt `ov_battery`** (seit 25.09.2026), nicht
`storage_update`. Ohne Werte stehen sie auf `v_bat1` = „--" und `d_bat1` = „% · --- A · --,- V". Format laut Kommentar: Strom **vor** der
Spannung und ganzzahlig (`%+.0f`), die Nachkommastelle nur in der Tabelle der Speicherseite.
„% · -12 A · 53,2 V" misst 102,8 px bei Innenbreite 108; ab 100 A kürzt `DOT` die Spannung,
nie den Strom samt Vorzeichen.

**Meldungen.** `alert_push(severity, device, text)` — Aufruf später aus BMS-, Modbus- und
HA-Fehlerzuständen. Die Liste liegt nur im RAM und ist nach einem Neustart leer.
`pv_status`, `sys_refresh` und `wx_warning` rufen es schon selbst (Störung eines
Wechselrichters, veraltete Werte, DWD-Warnung) und melden über `alert_clear(device, text)`
auch, wenn die Ursache weg ist. Seit dem 25.09.2026 zeigt die Seite nur Meldungen, deren
Ursache noch besteht (Wunsch Sebastian); gleiche Meldungen zählen in einer Zeile mit, die
Meldungszeile oben zeigt die schwerste. Eine künftige Quelle braucht also beides: `alert_push`
beim Eintreten und `alert_clear` mit demselben Text beim Ende. Meldungen ohne Ende, etwa die
neue Firmware des Co-Prozessors, bleiben bis zum Quittieren und Leeren stehen.

**Gerätewerte vom Nutzer.** Die Beschriftungen und Leistungen der eigenen Anlage
(`name_*`, `pv_kwp`, Tarife) trägt der Nutzer in `.pv-dashboard_anlage.yaml` ein und
misst sie dort gegen die Breiten aus Dokument 01; die Demo-Werte im Repo sind rund
und erfunden.

**Flussanimation.** Seit dem 25.09.2026 gibt es keine feste Tabelle `WATT[]` mehr: Der
erzeugte Block liest je Tick die 24 Kanäle in `flow_ch`, geschrieben von den Skripten
`ov_*` (Dokument 03, Abschnitt Flussanimation). Negative Leistung läuft rückwärts, unter
10 W steht die Kugel. Demo-Werte gibt es nur unter `USE_HOST` und nur, solange `flow_ch`
leer ist; auf dem Panel steht ohne Daten alles still. Der Block ist von
`tools/flow_animation.py` erzeugt und wird nicht von Hand geändert.

## BMS: serielle Anbindung

**Entscheidungsstand:** bewusst vertagt. Am 30.07.2026 hat der Nutzer gesagt, die
BMS-Implementierung solle separat und später erfolgen und nicht ungefragt mit eingebaut
werden.

Die Panel-Seite der Verdrahtung (Converter, Ports C und D, Baudraten, Isolierung,
120R-Abschluss) steht in Dokument 02 und ist in `.pv-dashboard_core.yaml` vorbereitet.
BMS-seitig hängt alles am angeschlossenen Gerät — Buchse und Pinbelegung unterscheiden sich
je Fabrikat, also vor dem Verdrahten gegen dessen Datenblatt prüfen. Notiert ist diese
Belegung:

- Serielle Schnittstelle auf einer RJ11-Buchse: Pin 3 (RXD) ← Converter TXD, Pin 4 (TXD)
  → Converter RXD, Pin 5 (GND) ↔ Converter GND. Pins 1 und 6 sind unbelegt, zählen beim
  Abzählen aber mit. Dieselbe Belegung steht als Kommentar in `.pv-dashboard_core.yaml`.
- Gebraucht wird zusätzlich ein Kabel RJ11 auf Schraubklemme.

**Offene Protokollfrage.** Die paceic-Version (`protocol_commandset` 0x20 oder 0x25) muss vor
der Umsetzung am Gerät geklärt werden. Meldet sich das BMS auf RS232 nicht, ist 9600 der
nächste Versuch. Der RS485-Port solcher BMS dient Wechselrichter und Parallelschaltung
und spricht meist *nicht* paceic.

**Problem `check_uart_settings` (zuletzt geprüft 20.09.2026 an einem Klon von
`main`).** Die Kandidaten-Komponente `github://nkinnan/esphome-pace-bms` ruft in
`pace_bms_component_master.cpp:79` weiterhin das ab ESPHome 9.0 abgekündigte
`check_uart_settings(9600, …)` auf. Unverändert seit der letzten Prüfung: Die Datei
wurde zuletzt am 28.10.2025 angefasst, der jüngste Commit des Repos ist vom
11.12.2025. Folge: Compile-Warnung; ab 2027.3.0 bricht der Build; bei 115200 Baud
erscheint in `dump_config` ein Fehlerlog „Invalid baud_rate". Auf ein Update des Autors
zu warten heißt, auf ein seit Monaten ruhendes Repo zu warten — vor dem Einbau also
erneut nachsehen und, wenn sich nichts getan hat, entscheiden, ob ein eigener Fork oder
ein Patch der Weg ist.

`external_components`, `pace_bms` und `modbus` liegen auskommentiert bereit — erst aktivieren,
wenn das BMS angeschlossen ist, sonst laufen nur Timeouts ins Log.

**Patch für `check_uart_settings` (vorbereitet 23.09.2026).** Die Komponente wird nicht
direkt von GitHub eingebunden, sondern als gepatchte lokale Kopie; ein Fork auf GitHub
ist bewusst nicht angelegt. Der Patch `patches/pace_bms-check_uart_settings.patch`
streicht den Aufruf in `PaceBmsMaster::dump_config()` und ersetzt ihn durch einen
Kommentar. Mehr braucht es nicht: `__init__.py` der Komponente prüft RX und TX schon
über `uart.final_validate_device_schema()`, Baudrate, Parität, Daten- und Stoppbits
setzt der Autor dort absichtlich nicht durch. Der gestrichene Aufruf verlangte 9600
Baud und hätte bei den 115200 von Port D nur einen falschen Fehler ins Log geschrieben.
Bewusst **nicht** in den Python-Teil übernommen: Stoppbits vergleicht
`final_validate_device_schema` als Zahl (`1`), `usb_uart` führt sie aber als Text
(`"1"`) — mit `stop_bits=1` lehnt `esphome config` die FT4232-Konfiguration ab
(„requires 1 stop bits“, erprobt mit 2026.9.0, 23.09.2026).

Einsetzen, aus dem Projektordner (`.pace-bms/` steht in `.gitignore`):

```
git clone https://github.com/nkinnan/esphome-pace-bms .pace-bms
git -C .pace-bms checkout 49985c4
git -C .pace-bms apply ../patches/pace_bms-check_uart_settings.patch
```

`49985c4` ist der jüngste Commit vom 11.12.2025, gegen den der Patch geschrieben ist;
danach in `.pv-dashboard_core.yaml` den `external_components`-Block mit `type: local`
einkommentieren. Geprüft am 23.09.2026 in einer Cloud-Sitzung: Der Patch lässt sich
auf `49985c4` anwenden, und `esphome config` (2026.9.0) nimmt eine Testkonfiguration
mit ESP32-P4, FT4232 und `pace_bms` auf `uart_bms_rs232` (115200) an. **Nicht geprüft:**
das Kompilieren — die Umgebung durfte das ESP-IDF nicht laden. Die Änderung ist eine
reine Streichung eines Aufrufs; ob die Komponente sonst unter 2026.9.0 baut, zeigt erst
der Device Builder. Rührt sich das Repo des Autors, zuerst dort nachsehen, ob der
Aufruf upstream verschwunden ist.

**Offen: Anzahl der BMS und Zuordnung zu `bat` 0…2.** `storage_update` erwartet `bat` 0…2,
also **drei** getrennte Datenquellen für Speicher 1…3 (Dokument 03). Die dokumentierte
Verdrahtung kennt dagegen nur **eine** RS232-Strecke — Port D, RJ11, 115200 — zu **einem**
BMS (Dokument 02, Dokument 01 „Speicher"). Welches von beiden gilt, steht nirgends im
Repo und ist vor der Umsetzung zu klären. **Entscheidungsstand: offen** — die Topologie
nicht raten.

Was die Komponente dazu hergibt (README von `nkinnan/esphome-pace-bms`, gelesen am
20.09.2026 an einem Klon von `main`): Ein Mehr-Pack-Aufbau über **eine** Strecke ist
vorgesehen — der angeschlossene BMS wird `type: MASTER`, die übrigen Packs hängen als
Slaves daran, abgefragt per `slave_query_mode: BROADCAST` (Empfehlung des Autors) oder
`RELAY`. Die eine RS232-Strecke reicht dafür also. Drei Randbedingungen stehen dabei im
README:

- **Nur paceic 0x25.** Mehr-Pack wird für 0x20 nicht unterstützt und soll es laut Autor
  auch nicht werden; bei 0x20 bleibt nur ein ESP je Pack. Damit hängt diese Frage an der
  Protokollfrage oben.
- **`response_timeout` hochsetzen** — als Startwert 2000 ms je Pack, bei drei Packs also
  etwa 6000 ms, weil der Master erst alle Slaves abfragt.
- **`rx_buffer_size` vergrößern** — bei BROADCAST 256 je Pack, bei drei Packs also 768,
  und zwar an `uart` **und** `pace_bms`. Das README merkt ausdrücklich an, dass der
  Speicherbedarf dort zum Thema wird, wo der ESP ohnehin unter Druck steht, und nennt
  LVGL als Beispiel — für dieses Panel also mitzudenken.
- Zur Trennung der gleichnamigen Sensoren je Pack sieht das README die ESPHome-Sub-Devices
  über `device_id` vor. Wie das auf `storage_update(bat: 0…2)` abgebildet wird, ist offen.

Das klärt die Frage nicht — ob die Packs des Nutzers überhaupt verkettet sind und welches
Protokoll sie sprechen, steht weiterhin nirgends. Es zeigt nur, dass eine RS232-Strecke
kein Widerspruch zu drei Datenquellen sein muss.

**Nicht im Simulator prüfbar.** Die seriellen Schnittstellen stehen in `.pv-dashboard_core.yaml`,
einem geräteeigenen Paket; der Simulator bindet es gar nicht ein. Die einzige lokale Kontrolle für Änderungen daran ist
`~/.venvs/esphome-beta/bin/esphome config pv-dashboard.yaml` — aus dem Projektordner, mit
vollem Pfad, nie mit `--show-secrets`. Alles Weitere zeigt sich erst am Gerät.

## Modbus-Regeln für 2026.9

Damit beim Anbinden keine abgekündigte Konfiguration entsteht (geprüft 11.09.2026):

- `reuse_previous_range` statt `register_count` / `force_new_range`
- `custom_pdu` statt `custom_command`
- kein `address: 0`
- kein `skip_updates` — stattdessen ein zweiter Controller mit gleicher Adresse und langsamem
  `update_interval`
- ein `modbus`-Hub pro RS485-Strang, `turnaround_time` und `send_wait_time` am Hub
- Einzelabfragen und Quittieren über die typisierten `modbus_client`-Actions (seit 8.0)
- `continuous: true` nur mit Bedacht
- die positionsbasierte Kanalzuordnung des FT4232 gilt in 9.0 unverändert

Datenquellen-Plan (30.07.2026): die Wärmepumpe über Home Assistant, der Rest möglichst
nativ Modbus, nicht TCP.

## Kamera

Im Repo gibt es noch keine Kamerakonfiguration. Der vorgesehene Sensor (OV5647) und sein
Anschluss stehen in Dokument 02.

Blockiert durch [esphome/esphome#16944](https://github.com/esphome/esphome/pull/16944)
(`esp_video_camera`, V4L2-Plattform für den ESP32-P4). **Stand 11.09.2026:** weiterhin offen
und nicht in 2026.9.0 — mergeable, REVIEW_REQUIRED, kein Milestone, CI grün, letzte Commits
07.09.2026; Maintainer clydebarrow testet aktiv. OV5647 wird unterstützt (800x640, 800x800,
800x1280, 1280x960, 1920x1080) und wurde auf einem Waveshare-Board damit getestet. Für
uns wichtig: MIPI-CSI neben `usb_uart` ist erlaubt, nur `enable_uvc: true` zusammen mit
`usb_host` wird abgelehnt — und `usb_host` brauchen wir für den Serienconverter.

Die Konfiguration wäre dann `esp_video_camera:` mit `device: jpeg`, `resolution: auto` und
`i2c_id` für SCCB. Die External Component `sullb/esphome-p4-csi-camera` ist **kein** Ersatz,
sie ist auf den OV02C10 zugeschnitten. Vor Kamera-Arbeiten den PR-Status prüfen.

## Nur am Gerät prüfbar

Simulator und Screenshots decken Layout und Logik ab, diese Punkte nicht:

- **Farbwirkung im Tageslicht.** Das Panel hängt nicht im abgedunkelten Raum. Die Schrifttöne
  sind ein zweites Mal aufgehellt worden (WCAG-Kontraste gegen `col_bg`, am 20.09.2026
  nachgerechnet: `col_ink` 18,5:1, `col_ink2` 16,9:1, `col_ink3` 11,9:1 statt vorher
  9,1:1). Ob das draußen reicht,
  zeigt erst das Panel. Dasselbe gilt für die Stufen in den Verläufen: LVGL 9 dithert bei
  `LV_COLOR_DEPTH 16` nicht. Die Entscheidung dazu steht in Dokument 03; geprüft wird in jedem Screenshot.
- **Bildzeit auf dem P4.** Die Flussanimation läuft in einem `interval: 20ms` über 37
  Teilstrecken (28 Leitungen, 20 Übergänge — Zahlen aus der Ausgabe von
  `tools/flow_animation.py`). Eine Messung auf dem Panel gibt es nicht.
- **Touch und Scrollen.** Dass `scrollable: false` das Verschieben wirklich unterbindet, ist
  bisher per Quelltext-Prüfung (11.09.2026) und im Simulator belegt, nicht mit dem Finger auf
  dem GT911.
- **Audio-Halbduplex.** Umgesetzt am 11.09.2026, **Hardware-Test steht aus** — siehe die
  zwei offenen Punkte im nächsten Abschnitt.

## Offen aus dem 9.0-Umstieg

Vom 9.0-Umstieg sind noch **zwei** Punkte offen, beide in Dokument 05 beschrieben:

- **Schritt 2 des OTA-Umstiegs** — `password:` durch `encryption: {}` ersetzen, erst nach
  der ersten erfolgreichen OTA-Installation einer 9.0-Firmware. Auf dem Panel läuft laut
  Device Builder noch 2026.7.3, der Schritt ist also nicht fällig.
- **Der Hardware-Test des Audio-Halbduplex** — umgesetzt am 11.09.2026, am Gerät nie
  gelaufen. Achtstufiger Testplan und die zwei bekannten ESPHome-Grenzen in Dokument 05.

Der LVGL-`list`-Bug ist mit 2026.9.0 erledigt.

## Offene Frage: Quittung nach Home Assistant

Das Quittieren wirkt heute nur auf dem Panel: `alert_ack` setzt die Zeile auf
`LV_STATE_CHECKED` und schreibt „Quittiert HH:MM" in den Hinweis. Der Kommentar über dem
Skript hält den Platz frei — „hier später auch die Quittung an das Gerät bzw. an Home
Assistant". Es geht also noch nichts an Geräte oder HA, und die Liste lebt nur im RAM.
**Entscheidungsstand: offen**, es ist nicht notiert, wie die Quittung zurücklaufen soll.

**Nicht gebaut, bewusst (25.09.2026):** Meldungen über einen Neustart hinweg speichern
(NVS-Platz, Quittung nach HA offen) und Steuern der Nilan-Stufe vom Panel aus.
Jeweils auf Zuruf. Der **Wallbox-Modus** (Aus / Smart / Schnell) ist seit dem
25.09.2026 abends vom Panel aus schaltbar, auf Wunsch des Nutzers:
`select.select_option` über Home Assistant (Dokument 03, Datenweg, „Steuern“).
Offen [A]: am eigenen Home Assistant prüfen, welche Optionsliste die
Modus-Entität hat und dass die Aktion ankommt (Option „Allow the device to
perform Home Assistant actions“).
Prognose und Wetter sind seit dem 25.09.2026 gebaut (oben).

---

Stand: 25.09.2026, spätabends (Wallbox-Modus vom Panel aus steuerbar); davor 25.09.2026, abends (Referenz-Entitäten statt Anker, „nicht belegt“ per `none`, Tests in `tests/`); davor 25.09.2026, später Tag (Datenweg von Home Assistant mit Dummy-Paket, Übersicht speisbar, offene Punkte dazu unter „Echte Daten anbinden“); davor 25.09.2026 (Doku abgeglichen: Fabrikate, acht Quellen und Sammelmeldung bei fehlender HA-Verbindung, offene 9.0-Punkte als eigener Abschnitt; Meldungen zusammengefasst und nur noch bestehende angezeigt, Seiten Prognose und Wetter, 60-%-Frage im Gesetz nachgelesen,
Seiten Netz und Statistik, Systemstatus, Wechselrichter-Status,
Geldrechnung, Nilan auf das klassische Bedienteil umgestellt, Rechtslage
recherchiert); davor 24.09.2026 (Detailseiten Wallboxen, Wärmepumpe und Haus gebaut, danach nach evcc
und dem Nilan-Bedienteil umgebaut, Nilan-Register recherchiert); davor
23.09.2026 (eigene Werte nach `.pv-dashboard_anlage.yaml` verlegt, Seite
PV & Prognose gebaut, Patch für `check_uart_settings` vorbereitet; davor 20.09.2026:
Streckenzahlen aus einem Vorschaulauf von
`tools/flow_animation.py`, Kontrastwerte nachgerechnet; LVGL-`list`-Bug mit 2026.9.0
erledigt, OTA-Schritt 2 und der Audio-Hardware-Test noch offen; neu aufgenommen: die
BMS-Zuordnung zu `bat` 0…2; am selben Tag auf die fertige Paketstruktur nachgezogen
und die Reste, die das Repo über die Anlage verriet — Widget-IDs, Tarifschlüssel,
Fabrikate in den Dokumenten, die Geräteseite der BMS-Verdrahtung — abgeräumt.
Zuletzt gegen `7ddb5c5` nachgezogen: die Zweitzeile der Autarkie-Kachel steht im Code
auf „Heute -- %" und gilt als erledigt; die Generalisierung ist geschoben, das Repo
ist öffentlich; die Bereinigung der Commit-Historie hat der Nutzer am selben Tag
ausdrücklich verworfen; `check_uart_settings` in der PACE-BMS-Komponente erneut
geprüft; oben eine ToDo-Liste als Kurzfassung ergänzt).
Geprüfter Stand: Commit `0e2bd3d` (25.09.2026).
