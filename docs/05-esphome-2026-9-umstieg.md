# 05 — Umstieg auf ESPHome 2026.9

## Entscheidung und min_version

Am 11.09.2026 hat der Nutzer entschieden, das Dashboard direkt auf ESPHome
2026.9.0 zu heben statt auf 2026.8.x zu bleiben. Grundlage war die Durchsicht
der Release Notes 2026.8.x und 2026.9.0b1 bis b3. Neue 9.0-Funktionen dürfen
direkt eingebaut werden.

Im Repo steht `min_version: 2026.9.0` in `pv-dashboard.yaml` und in
`pv-dashboard-sim.yaml`. `pv-dashboard-shots.yaml` erbt sie über das
Simulator-Package. Die Demo-Konfigurationen (`pv-dashboard-demo*.yaml`) stehen
seit dem 25.09.2026 ebenfalls auf `min_version: 2026.9.0`; `esphome config`
läuft für alle drei mit 2026.9.0 durch (gebaut wurden sie dabei nicht).

## Device Builder und Bauumgebungen

Wer baut, muss mit mindestens 2026.9.0 bauen, sonst bricht die Prüfung an der
min_version ab. 2026.9.0 ist seit dem 16.09.2026 stabil; solange nur Betas
verfügbar waren, hieß das für den Device Builder: Beta-Kanal einstellen.

- Stand 12.09.2026: Der Device Builder brachte 2026.8.0 mit und baute remote in
  `.esphome/.remote_builds/venvs/esphome-2026.8.1`. Auf dem Panel lief
  Firmware 2026.7.3.
- Stand 19.09.2026: Daneben liegt eine zweite Umgebung
  `.esphome/.remote_builds/venvs/esphome-2026.9.0`; deren dist-info meldet
  Version 2026.9.0.
- Für lokale Läufe (Simulator, Screenshots, Config-Prüfung) gibt es die
  Arbeitsumgebung `~/.venvs/esphome-beta`. Sie enthält seit dem 20.09.2026
  ESPHome **2026.9.0** (stabil); der Ordnername stammt noch aus der Beta-Zeit,
  der Inhalt nicht. Ein `esphome` im PATH gibt es nicht, jeder Aufruf geht mit
  vollem Pfad und aus dem Projektordner:
  `~/.venvs/esphome-beta/bin/esphome config pv-dashboard.yaml` (nie mit
  `--show-secrets`), entsprechend `run pv-dashboard-sim.yaml` bzw.
  `run pv-dashboard-shots.yaml`.
- Stand 09.10.2026: Zielplattform ist die Beta **2026.10.0b2** (siehe
  Abschnitt „Beta 2026.10.0b2“ unten). Die lokale Umgebung hebt
  `~/.venvs/esphome-beta/bin/pip install -U --pre esphome==2026.10.0b2`; der
  Device Builder muss dafür auf dem Beta-Kanal stehen.

Die drei Umgebungen sind voneinander unabhängig. Vor dem Bauen oder Flashen
prüfen, welche Version die jeweilige tatsächlich enthält.

## OTA: Umstieg auf Noise in zwei Schritten

Der `ota:`-Block in `.pv-dashboard_core.yaml` (Plattform `esphome`) nutzt weiterhin
`password:`. Der Umstieg auf Noise-Verschlüsselung läuft in zwei Schritten,
und die Reihenfolge ist zwingend:

1. **Jetzt (erledigt):** `password:` bleibt stehen.
2. **Offen:** Erst *nach* der ersten erfolgreichen OTA-Installation einer
   2026.9-Firmware `password:` durch `encryption: {}` ersetzen. Als Schlüssel
   dient der API-Schlüssel.

Warum die Reihenfolge: Den Upload prüft die Firmware, die gerade auf dem Gerät
läuft. Die alte Firmware kennt nur das Passwort und würde ein verschlüsseltes
Update abweisen — das nächste OTA bräche ab. Beides zusammen geht nicht, die
Optionen schließen sich aus.

Bis Schritt 2 erledigt ist, warnt 9.0, dass das Passwort rund 3,5 KB Flash
kostet. Das ist für Schritt 1 bewusst in Kauf genommen.

## Audio: I2S-Halbduplex (entfernt am 10.10.2026)

**Erledigt durch Entfernen.** Seit dem 10.10.2026 gibt es kein Audio mehr im
Dashboard (Wunsch des Nutzers nach dem ersten Flashen; Log: `micro_wake_word`
mehrmals je Sekunde „Not enough free bytes in ring buffer“).
`.pv-dashboard_audio.yaml` ist gelöscht, der Testplan unten entfällt. Der
Abschnitt bleibt als Nachweis stehen, falls Audio zurückkommt — das Paket
liegt im Versionsverlauf des Repos.

Umgesetzt war es am 11.09.2026; am Gerät getestet wurde es nie.

Ausgangslage: Wiedergabe und Aufnahme hängen an denselben I2S-Leitungen (Chips
und Pins in Dokument 02), und ESPHome vergibt den Bus exklusiv. Bis 09/2026
lief `micro_wake_word` ab dem API-Connect dauerhaft; der Lautsprecher bekam den
Bus nie und meldete im Sekundentakt „Parent bus is busy“ (Log vom 31.07.2026).
Die Lösung folgt dem ESPHome-Muster für die S3-Box-3 mit demselben Chip-Paar.

Umgesetzt war es in `.pv-dashboard_audio.yaml` (gelöscht):

- `on_wake_word_detected` startet den Voice Assistant; die
  micro_wake_word-ID heißt `mww`.
- Die Scripts `wake_word_pause` und `wake_word_resume` wechseln den Bus
  zwischen Mikrofon und Lautsprecher.
- Die Hooks hängen an `voice_assistant: on_client_connected` /
  `on_client_disconnected`, **nicht** an den api-Triggern: Die feuern auch für
  Log-Clients. Deshalb dürfen unter `api:` in `.pv-dashboard_core.yaml` keine
  `micro_wake_word.start/stop` stehen.
- Der I2S-Lautsprecher bekommt kein `timeout: never`, sonst gibt er den Bus
  nach dem Ende der Wiedergabe nicht frei (Default: 500 ms ohne Daten).

Bewusste Folge der Entscheidung vom 11.09.2026: Solange Musik läuft, ist das
Wakeword aus. Beim Start einer Wiedergabe darf einmal „Parent bus is busy“
erscheinen; der Lautsprecher versucht es nach 1 s erneut.

### Testplan am Gerät (entfallen)

1. Boot, bis Home Assistant abonniert und das Wakeword aktiv ist.
2. „Okay Nabu“, Antwort abwarten; danach muss das Wakeword wieder aktiv sein.
3. Musik starten und regulär enden lassen.
4. Pause, dann Wakeword, dann fortsetzen.
5. Ansage im Leerlauf.
6. Logs während der Musik öffnen und schließen — die Musik muss weiterlaufen.
7. Neustart von Home Assistant während der Musik.
8. Anschlussfrage (continue_conversation).

Abnahmekriterium: „Parent bus is busy“ höchstens einmal pro Wiedergabestart.

### Bekannte Grenzen (Fehler in ESPHome, im YAML nicht lösbar)

Beobachtet an 2026.9.0b3; an 2026.9.0 nicht erneut geprüft.

- Meldet Home Assistant den Voice Assistant ab, während dieser noch in
  STARTING_MICROPHONE wartet, stoppt er seine Mikrofon-Quelle nicht. Das
  Mikrofon hält den Bus dann bis zum Neustart: Musik hängt, das Wakeword bleibt
  aus. Dasselbe, wenn der Pipeline-Start an Home Assistant scheitert.
- Eine Anschlussfrage während laufender Musik wartet mit dem Zuhören, bis die
  Musik endet oder eine Pause von mehr als 500 ms zwischen zwei Titeln den Bus
  freigibt.

Beides wäre ein Upstream-Issue wert; gemeldet ist es bisher nicht.

## LVGL-list: Codegen-Absturz (#19123 / #19177)

Bis 2026.9.0b3 brach die Codegenerierung mit
`AttributeError: 'NoneType' object has no attribute 'detent'` ab, sobald eine
LVGL-`list` mit `on_add`/`on_remove` von außerhalb des `lvgl:`-Blocks bedient
wurde (gemeldet vom Nutzer am 12.09.2026 als esphome/esphome#19123). **Der
Fix-PR #19177 von clydebarrow ist in 2026.9.0 enthalten** — nachgeprüft am
20.09.2026 an `lv_list.py` in
`.esphome/.remote_builds/venvs/esphome-2026.9.0`, das vor jedem `action_to_code`
ein `_wait_list_triggers_completed()` aufruft. Der lokale Patch in
`~/.venvs/esphome-beta` ist mit dem Upgrade weggeräumt, und die Regel „in
`on_add`/`on_remove` keine globals-IDs" gilt damit **nicht mehr**; hier läuft
keine ältere Umgebung.

`esphome-2026.8.1` bringt das `list`-Widget ohnehin gar nicht mit — dort gibt es
keine `lv_list.py`. Das ist der zweite Grund für `min_version: 2026.9.0`.

Geblieben ist eine Eigenheit: `lvgl.list.clear` akzeptiert nur die Dict-Form
(`lvgl.list.clear: {id: …}`); die Kurzform `lvgl.list.clear: alert_list` lehnt
ESPHome ab.

## Akzeptierte Warnungen bei Prüfung und Bau

Diese Warnungen erscheinen bewusst und sind kein Fehler.

**Bei `esphome config pv-dashboard.yaml`** — der Lauf endet mit „Configuration
is valid!" und gibt dabei **genau diese drei** aus (nachgemessen am 20.09.2026):

- **Nicht empfohlene Framework-Version** — gesetzt ist ESP-IDF 6.0.2, während
  ESPHome weiterhin 5.5.5 empfiehlt. Bei Build-Problemen ist ein Gegentest mit
  der empfohlenen Version der schnellste Schritt. (Steht zweimal im Protokoll.)
- ~~**OTA-Passwort kostet rund 3,5 KB Flash**~~ — entfallen seit dem 10.10.2026:
  OTA läuft nur noch verschlüsselt (`encryption: {}`), ohne Passwort.
- **Geschwärzte Werte in der Config-Ausgabe** — eine Heuristik schwärzt jedes
  Feld mit „_key“ im Namen: hier `transparency_key`, im Simulator zusätzlich
  `snapshot_key: SDLK_F12`. Reine Kosmetik; laut Warnung fällt die Heuristik mit
  2026.12.0 weg. Im YAML steht `transparency_key` nicht; die Warnung kommt vom
  Standardwert in ESPHomes LVGL-Schema und erscheint auch mit 2026.10.0b2
  (geprüft 09.10.2026, siehe „Beta 2026.10.0b2“).

**Erst bei der Code-Erzeugung, nicht bei `esphome config`:**

- **„Using experimental features in ESP-IDF …“** — die Option
  `enable_idf_experimental_features: true` (unter `esp32.framework.advanced`)
  ist Pflicht für 32 MB Flash zusammen mit OTA. ESPHome loggt sie in `to_code`,
  sie erscheint also erst beim Erzeugen des Codes beziehungsweise beim Bauen im
  Device Builder. Wer sie in der Config-Prüfung sucht, sucht einen Fehler, den
  es nicht gibt.

## Weitere 9.0-bedingte Anpassungen

- **BLE-Scan:** Ab 2026.9 warnt ESPHome, wenn Scan-Fenster und Scan-Intervall
  gleich groß sind. Die daraufhin gesenkten Werte stehen in Dokument 02.
- **Screenshots:** `pv-dashboard-sim.yaml` setzt `min_version: 2026.9.0`, weil
  es die Snapshot-Funktion der host-Plattform nutzt. `pv-dashboard-shots.yaml`
  hat **keine** eigene Angabe und erbt sie über das Simulator-Package. Unter den
  **drei aktiven** Konfigurationen gibt es eigene `min_version`-Zeilen also nur
  in `pv-dashboard.yaml` und `pv-dashboard-sim.yaml`; die Demo-Dateien stehen
  ebenfalls auf `2026.9.0` (siehe oben). Jede Datei hat höchstens eine, `grep -n
  min_version *.yaml` findet sie sofort — Zeilennummern altern, deshalb stehen
  hier keine.

## Beta 2026.10.0b2

Am 09.10.2026 hat der Nutzer die Beta **2026.10.0b2** (PyPI, 09.10.2026) als
Plattform gewählt. Geprüft wurde in einer Cloud-Sitzung mit einer eigenen
Umgebung, die 2026.10.0b2 enthält — nicht auf dem Mac und nicht im Device
Builder:

- `compile pv-dashboard-sim.yaml` und `run pv-dashboard-shots.yaml` laufen
  durch, alle 20 Bilder entstehen.
- `python -m unittest discover tests`: 24 Tests, alle grün.
  `tests/ha_probe.py --shots`: 37 von 37 Prüfungen bestanden. Die Probe ruft
  das `esphome` neben dem aufrufenden Python auf, nimmt also automatisch die
  Version der Umgebung, mit der sie gestartet wird.
- Bildvergleich gegen die Aufnahmen vom 25.09.2026 (2026.9.0), pixelgenau:
  Unterschiede nur bei Uhrzeit und Datum, Reiterreihenfolge, zeitabhängigen
  Werten (Restprognose, Jetzt-Linie, Flusspunkte, Meldungszeiten) und den
  Commits nach dem 25.09. Die Wallbox-Seite ist bis auf die Uhr identisch —
  Schriften und Abstände haben sich mit der Beta nicht verschoben.
- Die geräteeigenen Pakete (`_core`, `_display`, `_audio` — seit 10.10.2026
  entfernt —, `_utility`, `_ha`, `_ui` mit Seiten) bestehen `esphome config` mit 2026.10.0b2 — geprüft über
  eine Hilfskonfiguration mit Platzhalterwerten statt `secrets.yaml` und der
  Vorlage `.pv-dashboard_anlage.yaml.example`. Es erscheinen dieselben drei
  Warnungen wie unter 2026.9.0 (siehe „Akzeptierte Warnungen“). Gebaut für den
  ESP32-P4 wurde dabei nicht.

**`transparency_key` geklärt:** Die Warnung kommt nicht aus dem YAML, sondern
aus ESPHomes eigenem LVGL-Schema: `lvgl:` hat den Schlüssel mit Standardwert
`0x000400` (`components/lvgl/__init__.py`), die Config-Ausgabe schwärzt ihn.
Sie bleibt also, bis ESPHome die Heuristik entfernt.

**Durchgesehene Breaking Changes** (Changelog 2026.10.0, Stand b2), soweit sie
das Dashboard berühren:

- **light** (#18997): `restore_mode` wird durch `restore_state` ersetzt.
  `restore_mode` wird weiter angenommen und nur zusammen mit `initial_state`
  bemängelt; das Backlight (`.pv-dashboard_display.yaml`,
  `restore_mode: RESTORE_DEFAULT_ON`) bleibt deshalb unverändert.
- **speaker** (#19074): `codec_support_enabled` entfernt — nicht benutzt.
- **speaker / speaker_source** (#19307, #18412): Lautstärke und Stummschaltung
  des Media Players sind jetzt unabhängig. Kein YAML betroffen; Audio ist seit
  dem 10.10.2026 ohnehin entfernt.
- **host** (#19214): baut mit ninja statt PlatformIO. Simulator, Screenshots und
  `tests/ha-test.yaml` bauen damit ohne Änderung.
- Daneben ohne Handlungsbedarf: OTA komprimiert Uploads auf dem ESP32 (#19037),
  die Empfangsschleife blockiert weiter in einem `loop()`-Durchlauf (die
  `lv_refr_now()`-Begründung in `_core` gilt also weiter); Workaround für einen
  ESP-IDF-Stackfehler auf dem P4 (#20181). Die empfohlene ESP-IDF bleibt 5.5.5,
  der Pin auf 6.0.2 ist unverändert.

**`min_version` bleibt 2026.9.0.** Die Konfiguration nutzt nichts, was erst mit
2026.10 kommt. Und ESPHome ordnet Vorabversionen beim Vergleich **hinter** die
stabile ein (`Version.parse("2026.10.0b2") <= Version.parse("2026.10.0")` ist
`False`): `min_version: 2026.10.0b2` würde die stabile 2026.10.0 ablehnen.

---

Stand: 10.10.2026 (Audio entfernt, Testplan entfallen); davor 09.10.2026 (Beta 2026.10.0b2 geprüft, `transparency_key` geklärt); davor 25.09.2026 (Demo-Konfigurationen auf 2026.9.0, `transparency_key` als
offen markiert); davor 20.09.2026 (#19177 in 2026.9.0 enthalten, in der Bauumgebung
`esphome-2026.9.0` nachgeprüft; `~/.venvs/esphome-beta` an dem Tag auf 2026.9.0
gehoben). Geprüfter Stand: Commit `0e2bd3d` (25.09.2026).
