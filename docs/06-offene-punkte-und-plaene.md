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

- [ ] **Echte Daten anbinden** — vier Anbindungspunkte plus `WATT[37]`. Am 20.09.2026
      vertagt: die neuen Geräte laufen beim Nutzer noch nicht.
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

Alle vier Detailseiten sind gebaut. Jede liegt in ihrer eigenen Datei
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
- **Wärmepumpe:** Nilan Compact P mit Bedienteil CTS700 Touch. Die Farben sind
  aus dem Bild der Nilan-Anleitung abgelesen, keine offiziellen Werte. Die
  Compact P heizt Luft und Warmwasser und hat keinen Heizwasserkreis:
  **Vorlauf, Rücklauf und COP der Festlegung vom 30.07.2026 entfallen**, dafür
  Raumtemperatur, Feuchte, CO2, Lüftungsstufe, Zu- und Fortluft, Bypass,
  Sommer/Winter und Kompressorbetrieb. Leistungsaufnahme und Tagesverbrauch
  sind elektrisch und kommen nicht aus der Nilan-Steuerung selbst, sondern
  vermutlich von einem Zähler (offen). Auf Wunsch des Nutzers steht die Seite
  auf dem Dashboard-Grund; Haus und Warmwasserkachel sind dafür abgedunkelt
  (weiße Schrift 6,5 bzw. 8,2 : 1, gerechnet). Eine Jahreszeit-Anzeige hat im
  neuen Registersatz (unten) kein eigenes Register, nur die Umschalttemperatur.
- **Nilan-Modbus (Recherche 24.09.2026, nicht am Gerät geprüft).** Es gibt drei
  Registersätze, welcher gilt, hängt am Bedienteil und ist offen:
  - **CTS700 Touch, „CTS700 Modbus User Guide“ (2018)** – vermutlich der des
    Nutzers (Annahme): Modbus TCP, Port 502, Slave 1 = Compact P, Temperaturen
    ×10. Raum 20286 (T3 Abluft), außen 20282 (T1), Zuluft 20284 (T2), Fortluft
    20288 (T4), Warmwasser oben/unten 20520/20522 (T11/T12), Feuchte 21776,
    CO2 21778, Betriebszustand 21770 (0 Auto, 1 Kühlen, 2 Heizen), Zu-/Abluft
    % 21771/21772, Bypass 21773 (0 zu, 1 offen), Kompressor 21775 (nur „0 Aus“
    lesbar), Zusatzheizung 21788, Enteisung 21789/21790, Legionellen 21785,
    Lüftungsstufe 20148 (101–104), Sollwerte Raum 20260, Warmwasser 20460,
    Filtertage 20103/20107, Alarm 22490. Laut Anleitung beim Lesen mit einer
    SPS +1 auf die Adresse; die Umsetzungen lesen ohne. Quelle: Anleitung auf
    manualslib (Nr. 1620619) und github.com/pjuzeliunas/nilan.
  - **Älteres CTS700 ohne Touch (Rev. 2.01)**, Adressen 47xx/51xx/55xx
    (github.com/matej/homebridge-nilan). Welches Bedienteil diesen Satz nutzt,
    widersprechen sich die Quellen.
  - **CTS602** (github.com/veista/nilan), dort Compact P als Gerätetyp 44 –
    gilt laut dessen README **nicht** für CTS700.
  - Eine Leistungs- oder Energieangabe hat keiner der drei Sätze.
  Offen: Der Wärmepumpen-Kasten im Schema der Übersicht trägt noch die
  Zweitzeile mit COP; die liefert die Compact P nicht (unverändert gelassen).
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

**Entscheidungsstand:** erledigt, alle vier gebaut (23. und 24.09.2026). Vorher
bewusst vertagt: Der Nutzer hatte am 30.07.2026 ausdrücklich gesagt, die
Detailseiten kommen später und sollen nicht ungefragt gebaut werden. Am 12.09.2026 für die
Verläufe wiederholt: Ringe, Tagesbalken und Akzente zuerst nur in der Übersicht, die
Detailseiten PV, Haus, Wallbox und WP bleiben für später.

**Schnittstelle je Seite.** Wird eine gebaut, bekommt sie ihre **eigene**
Skript-Schnittstelle nach dem Muster von `storage_update(...)`: ein Skript mit benannten
Parametern, das nur Widgets füllt. Bis Sensoren daran hängen, steht in den Widgets das
Strichmuster aus Dokument 01 (Regel „Fehlender Wert") — keine erfundenen Zahlen. So
gebaut sind `pv_update`, `wallbox_update`, `wallbox_month`, `heatpump_update`,
`heatpump_extra` und die fünf `house_*`-Skripte; die
Aufrufe kommen erst mit den Sensoren. Was beim Anlegen einer Seite sonst
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
  Anlagenbeschreibung in `README.md` und dieses Dokument nennen jetzt nur noch den
  Aufbau. Was zur Anlage des Nutzers gehört, steht in seinen privaten Notizen
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

Stand: 24.09.2026 (Detailseiten Wallboxen, Wärmepumpe und Haus gebaut, danach nach evcc
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
Geprüfter Commit: `7ddb5c5` (20.09.2026).
