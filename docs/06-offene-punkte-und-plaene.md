# 06 — Offene Punkte und Pläne

Was noch aussteht, jeweils mit Entscheidungsstand. Nichts davon wird ungefragt gebaut.

## Detailseiten

Vier Seiten sind nur Platzhalter: `page_pv`, `page_wallbox`, `page_heatpump`,
`page_house` tragen je ein einzelnes zentriertes Label. Jede liegt in ihrer
eigenen Datei `.pv-dashboard_page_*.yaml`, eingebunden vom `packages:`-Block in
`.pv-dashboard_ui.yaml`.

Geplanter Inhalt (Festlegung 30.07.2026):

- **PV & Prognose** — sechs Strings einzeln, Volleinspeise-Kreis getrennt, Prognose gegen Ist-Verlauf
- **Wallboxen** — beide: Modus, Ladeleistung, geladene Energie, Fahrzeug-SoC
- **Wärmepumpe** — Betriebsmodus, Vorlauf/Rücklauf, COP, Leistungsaufnahme, Tagesverbrauch
- **Haus** — Backofen, Waschmaschine, Spülmaschine, Trockner einzeln, plus Grundlast

**Entscheidungsstand:** bewusst vertagt. Der Nutzer hat am 30.07.2026 ausdrücklich gesagt, die
Detailseiten kommen später und sollen nicht ungefragt gebaut werden. Am 12.09.2026 für die
Verläufe wiederholt: Ringe, Tagesbalken und Akzente zuerst nur in der Übersicht, die
Detailseiten PV, Haus, Wallbox und WP bleiben für später.

**Schnittstelle je Seite.** Wird eine gebaut, bekommt sie ihre **eigene**
Skript-Schnittstelle nach dem Muster von `storage_update(...)`: ein Skript mit benannten
Parametern, das nur Widgets füllt. Bis Sensoren daran hängen, steht in den Widgets das
Strichmuster aus Dokument 01 (Regel „Fehlender Wert") — keine erfundenen Zahlen. Für die
Wallbox-Seite hieße das Parameter für Modus, Ladeleistung, geladene Energie und
Fahrzeug-SoC; der Aufruf kommt erst mit den Sensoren. Was beim Anlegen einer Seite sonst
dazugehört (Kachelkonvention, `scrollable`, nav-Knopf, Screenshots, Flussanimation), steht
in Dokument 03 unter „Neue Detailseite".

## Offen: Zweitzeile der Autarkie-Kachel

Die Autarkie-Kachel der Übersicht zeigt im Ring den **Tageswert**, ihre Zweitzeile steht in
`.pv-dashboard_page_overview.yaml` aber auf „Monat -- %". Am 20.09.2026 hat der Nutzer bestätigt: Das
„Monat" ist ein Versehen, es bleibt beim Tageswert, und der Text auf dem Panel wird
entsprechend geändert. **Entscheidungsstand: entschieden, Umsetzung offen.** Wer an der
Übersicht arbeitet, erledigt die Textänderung mit — sonst gilt die Seite zu Unrecht als
fertig. Definitionen in Dokument 01, Abschnitt „Autarkie".

## Was das Repo über die Anlage verrät

Seit dem 20.09.2026 sind alle anlagenabhängigen Beschriftungen und die drei Tarife
`substitutions` mit neutralen Demo-Werten; die eigenen Werte stehen in
`pv-dashboard.yaml` und bleiben damit auf dem Rechner (Dokument 01). Am selben Tag
sind auf Wunsch des Nutzers auch die Namen nachgezogen worden, die eine
Beschriftungsänderung überdauern — **erledigt**:

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
  jetzt `tarif_volleinspeisung_ct` — in `pv-dashboard.yaml`, im Standard in
  `.pv-dashboard_page_overview.yaml` und in Dokument 01.
- **Die Dokumente beschrieben die echte Anlage** — Fabrikate, Typenbezeichnungen,
  echte Dachflächennamen, Speichergröße, Förderdauer, das BMS-Kit. Dokument 01, die
  Anlagenbeschreibung in `README.md` und dieses Dokument nennen jetzt nur noch den
  Aufbau. Was zur Anlage des Nutzers gehört, steht in seinen privaten Notizen
  außerhalb des Repos.

**Offen und vor dem Öffentlichmachen zu erledigen: die Commit-Historie.** Die
Generalisierung steht bisher nur im Arbeitsbaum. Vier der fünf Commits bis
`c6a432f` tragen den alten Stand weiter — Fabrikate und Typenbezeichnungen, die
echten Flächennamen, die alten Widget-IDs und den alten Tarifschlüssel mitsamt
einem echten Tarifwert; nur der erste Commit (`28f09ac`, reine
Versionsgeschichte) ist frei davon. Beim Veröffentlichen geht die Historie mit:
`git log` und jeder alte Blob sind dann lesbar, auch wenn der aktuelle Stand
neutral ist. Zwei Wege: ein einziger frischer Initial-Commit auf dem
generalisierten Stand, die alte Historie separat und privat aufgehoben — oder
ein Durchlauf mit `git filter-repo` über die betroffenen Dateien. Danach mit
einem Suchlauf über alle Commits (`git rev-list --all`) gegenprüfen, dass die
alten Namen nirgends mehr auftauchen. Die Umschreibung der Commit-Identität vom
20.09.2026 muss dabei erneut laufen. Das ist ein schreibender Eingriff in die
Historie und bleibt dem Nutzer vorbehalten.

Ein weiterer Punkt bleibt offen; er blockiert das Öffentlichmachen nicht:

- **Der Beispieltext des Sprachassistenten** in `pv-dashboard-shots.yaml` nennt
  „Wallbox 1" im Fließtext. Er ist absichtlich nicht auf `${name_wb_1}` umgestellt:
  Der Satz hat einen Artikel davor („Die Wallbox 1 meldet …"), bei einem frei
  gewählten Namen würde der Satz grammatisch schief. Demo-Prosa, nur im
  Screenshot-Lauf, nie auf dem Gerät.

## Offen: Umschalten auf die Packages aus dem Repo

`pv-dashboard.yaml` trägt seit dem 20.09.2026 den fertigen Fernblock, aber
auskommentiert (Dokument 03). Umgeschaltet wird, sobald die Paketdateien im
Repo liegen: erst `push`, dann die beiden `packages:`-Blöcke tauschen.

Offen bleibt die Entscheidung, ob das die Mühe wert ist: Danach baut das
Gerät aus dem geschobenen Stand, jede Änderung braucht erst einen `push`, und
`esphome config` zeigt die Werte aus `secrets.yaml` nicht mehr als
`!secret '<name>'`. Beides ist in Dokument 03 belegt. Solange der Block aus ist,
ändert sich für den Nutzer nichts — die `!include`-Zeilen bleiben in Kraft.

## Echte Daten anbinden

Übersicht, Speicher und Meldungen sind gebaut, die Datenquellen fehlen. Für diese drei
Flächen gibt es genau vier Anbindungspunkte. Sie decken die **Detailseiten nicht** ab —
jede neue bringt ihre eigene Schnittstelle mit (siehe oben).

**Tagesreihe.** In `record_hour` steht eine einzige auskommentierte Quellzeile für die
Erzeugung der abgelaufenen Stunde in kWh: `// kwh = id(<Erzeugungssensor>).state;`. Solange
sie auskommentiert ist, wird 0 eingetragen. Der Kommentar daneben nennt die Stelle
ausdrücklich „die einzige Stelle zum Anbinden".

**Speicher.** `storage_update(...)` füllt Tabellenspalte und Ring der Speicherseite;
Signatur und Sonderwerte stehen in Dokument 03. Künftige BMS-Sensoren rufen nur dieses
Skript auf.

**Die Batteriekästen der Übersicht füllt `storage_update` nicht.** Sie stehen dort auf
`v_bat1` = „--" und `d_bat1` = „% · --- A · --,- V". Format laut Kommentar: Strom **vor** der
Spannung und ganzzahlig (`%+.0f`), die Nachkommastelle nur in der Tabelle der Speicherseite.
„% · -12 A · 53,2 V" misst 102,8 px bei Innenbreite 108; ab 100 A kürzt `DOT` die Spannung,
nie den Strom samt Vorzeichen.

**Meldungen.** `alert_push(severity, device, text)` — Aufruf später aus BMS-, Modbus- und
HA-Fehlerzuständen. Die Liste liegt nur im RAM und ist nach einem Neustart leer.

**Flussanimation.** Die Leistungen je Teilstrecke stehen in `WATT[]` — „hier binden später die
Sensoren an". Das Feld hat **37 Einträge**, einen je Teilstrecke; die Reihenfolge erzeugt
`tools/flow_animation.py`. Demo-Werte gibt es nur unter `USE_HOST` (Simulator, Screenshots),
auf dem Panel steht alles auf 0, keine erfundenen Flüsse. Das **Vorzeichen** wertet die Logik noch nicht
aus; eine Flussumkehr braucht die Topologie rückwärts und kommt mit der Sensoranbindung. Der
Block ist von `tools/flow_animation.py` erzeugt und wird nicht von Hand geändert.

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

**Problem `check_uart_settings` (geprüft 11.09.2026).** Die Kandidaten-Komponente
`github://nkinnan/esphome-pace-bms` ruft in `pace_bms_component_master.cpp:79` das ab ESPHome
9.0 abgekündigte `check_uart_settings(9600, …)` auf. Folge: Compile-Warnung; ab 2027.3.0
bricht der Build ohne Update des Autors; bei 115200 Baud erscheint in `dump_config` ein
Fehlerlog „Invalid baud_rate". Vor dem Einbau nach einem Update des Autors schauen.
`external_components`, `pace_bms` und `modbus` liegen auskommentiert bereit — erst aktivieren,
wenn das BMS angeschlossen ist, sonst laufen nur Timeouts ins Log.

**Offen: Anzahl der BMS und Zuordnung zu `bat` 0…2.** `storage_update` erwartet `bat` 0…2,
also **drei** getrennte Datenquellen für Speicher 1…3 (Dokument 03). Die dokumentierte
Verdrahtung kennt dagegen nur **eine** RS232-Strecke — Port D, RJ11, 115200 — zu **einem**
BMS (Dokument 02, Dokument 01 „Speicher"). Welches von beiden gilt, steht nirgends im
Repo und ist vor der Umsetzung zu klären: drei BMS am RS485-Strang mit je eigener Adresse,
ein BMS, das alle drei Packs führt, oder zunächst nur Speicher 1 angebunden und 2 und 3 auf
Strichmuster. **Entscheidungsstand: offen** — die Topologie nicht raten.

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
  zwei offenen 9.0-Punkte unten.

## Offene Frage: Quittung nach Home Assistant

Das Quittieren wirkt heute nur auf dem Panel: `alert_ack` setzt die Zeile auf
`LV_STATE_CHECKED` und schreibt „Quittiert HH:MM" in den Hinweis. Der Kommentar über dem
Skript hält den Platz frei — „hier später auch die Quittung an das Gerät bzw. an Home
Assistant". Es geht also noch nichts an Geräte oder HA, und die Liste lebt nur im RAM.
**Entscheidungsstand: offen**, es ist nicht notiert, wie die Quittung zurücklaufen soll.

Vom 9.0-Umstieg sind noch **zwei** Punkte offen, beide in Dokument 05 beschrieben:

- **Schritt 2 des OTA-Umstiegs** — `password:` durch `encryption: {}` ersetzen, erst nach
  der ersten erfolgreichen OTA-Installation einer 9.0-Firmware. Auf dem Panel läuft laut
  Device Builder noch 2026.7.3, der Schritt ist also nicht fällig.
- **Der Hardware-Test des Audio-Halbduplex** — umgesetzt am 11.09.2026, am Gerät nie
  gelaufen. Achtstufiger Testplan und die zwei bekannten ESPHome-Grenzen in Dokument 05.

Der LVGL-`list`-Bug ist mit 2026.9.0 erledigt.

---

Stand: 20.09.2026 (Streckenzahlen aus einem Vorschaulauf von
`tools/flow_animation.py`, Kontrastwerte nachgerechnet; LVGL-`list`-Bug mit 2026.9.0
erledigt, OTA-Schritt 2 und der Audio-Hardware-Test noch offen; neu aufgenommen: die
Zweitzeile der Autarkie-Kachel und die BMS-Zuordnung zu `bat` 0…2; am selben Tag auf
die fertige Paketstruktur nachgezogen und die Reste, die das Repo über die Anlage
verriet — Widget-IDs, Tarifschlüssel, Fabrikate in den Dokumenten, die Geräteseite der
BMS-Verdrahtung — abgeräumt).
Geprüfter Commit: `c6a432f` (12.09.2026).
