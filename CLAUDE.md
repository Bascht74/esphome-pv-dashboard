# Arbeitsregeln für dieses Repo

Gilt für jede Assistenz-Sitzung in `~/esphome`; Inhaltliches steht in `docs/01`
bis `docs/06`.

## Geheimnisse

- **Niemals** lesen, ausgeben, greppen oder zitieren: `secrets.yaml`,
  `.device-builder*`, `.receiver_peers.json`, `.esphome/storage/` — auch nicht
  ausschnittsweise, auch nicht zur Prüfung, ob ein Schlüssel existiert. Bei
  Suchen ausschließen (`grep --exclude=secrets.yaml`).
- Werte nur über `!secret <name>`, und das steht **nur** in `pv-dashboard.yaml`.
- `.pv-dashboard_anlage.yaml` hält die eigene Anlage (Beschriftungen, Tarife)
  und bleibt lokal (`.gitignore`). Zum Messen von Breiten darf sie gelesen
  werden; ihre Werte aber nie in Repo-Dateien, Commits oder Doku übernehmen.
  Im Repo steht nur die Vorlage `.pv-dashboard_anlage.yaml.example`.
  Neuer Schlüssel: dem Nutzer den Namen nennen, den er selbst einträgt und in
  `secrets.yaml.example` dokumentiert.
- Keine Zugangsdaten, WLAN-Namen, Schlüssel, IP- oder MAC-Adressen in Ausgaben.
- **Bauartefakte nur gezielt:** Die Ordnernamen unter
  `.esphome/.remote_builds/venvs/` (ESPHome-Version) sind unbedenklich. Aus
  `.esphome/build/…/src/main.cpp` **nur einzelne, nachweislich harmlose Zeilen**
  zitieren, etwa `line_height` einer Schrift. **Nie am Stück ausgeben, nie
  greppen ohne engen Filter:** Die Datei enthält WLAN-, AP- und OTA-Passwort
  sowie den API-Schlüssel im Klartext (`set_ssid`, `set_password`, PSK-Array).

## Git

Niemals von sich aus committen oder pushen — auch nicht „gleich mit", nur auf
ausdrückliche Aufforderung. Nach Änderungen berichten, was geändert wurde.

**Gearbeitet wird auf `dev`, nicht auf `main`.** Jede Änderung geht auf diesen
Zweig; `main` wird nur angefasst, wenn der Nutzer es ausdrücklich sagt. Das Gerät
baut aus `main` (`ref: main` im `packages:`-Block), eine Änderung auf `dev` erreicht
das Panel also nicht — genau das ist der Zweck. Ist eine Änderung geprüft, führt der
Nutzer sie nach `main`. Sitzungen, denen die Umgebung einen eigenen Zweig zuweist,
arbeiten trotzdem gegen `dev` und fragen, bevor etwas nach `main` geht.

## Rückfragen

Als Chattext stellen, Optionen als kurze Liste mit Empfehlung. **Nie** über
einen Auswahldialog; ein weggeklickter Dialog ist keine Entscheidung.

## Nichts erfinden

Versionen, Pins, Koordinaten, Maße und Menünamen nicht raten, sondern
gegenprüfen: `grep` über die YAML, `line_height` aus `main.cpp`, Streckenzahlen
aus einem Vorschaulauf von `tools/flow_animation.py`. Sonst offen nennen.

## Bauen und Prüfen

Kein `esphome` im PATH; jeder Aufruf mit vollem Pfad und aus dem Projektordner,
ESPHome 2026.9.0 (`docs/05`):

```
~/.venvs/esphome-beta/bin/esphome run pv-dashboard-shots.yaml
sips -s format png shots/*.bmp --out shots/
~/.venvs/esphome-beta/bin/esphome compile pv-dashboard-sim.yaml
~/.venvs/esphome-beta/bin/esphome config pv-dashboard.yaml
```

**Die Kette bis zum Bild ist Pflicht.** Die Config-Prüfung findet nur Syntax
und Semantik, Überläufe und Kollisionen erst das Bild. Der shots-Lauf schreibt
**BMP**, das eine Sitzung nicht öffnen kann: umwandeln (zweiter Befehl), die
**PNG** ansehen, Ausschnitte vergrößern, jede geänderte Stelle einzeln. Mehr in
`docs/03`; die Checkliste `docs/04` gilt nach **jeder** Layoutänderung,
Kastenhöhen ausrechnen statt schätzen.

`compile -sim` baut nur, ohne Fenster — der Weg zu `line_height`.
`config pv-dashboard.yaml` ist **erlaubt**, die einzige lokale Kontrolle der
geräteeigenen Pakete, nie mit `--show-secrets`; `run`/`compile` darauf
**nicht**, das macht der Device Builder. Lokal laufen nur `-sim`
(**blockiert**), `-shots` und `-demo*`.

## Packages kommen aus dem Repo

`pv-dashboard.yaml` lädt die Packages von GitHub (`ref: main`, `refresh: 1d`);
die lokale Variante steht darunter auskommentiert. Folgen für die Arbeit:

- Das **Gerät** baut aus dem geschobenen Stand: erst Simulator und Screenshots
  prüfen, dann `push`, dann im Device Builder bauen. Ohne `push` sieht das
  Gerät die Änderung nicht.
- **Simulator und Screenshots bleiben lokal** und zeigen den Arbeitsstand
  sofort — dort also prüfen, nicht am Gerät.
- `esphome config pv-dashboard.yaml` zeigt die Werte aus `secrets.yaml` jetzt
  **aufgelöst** statt als `!secret '<name>'` (ESPHome leert die Merkliste beim
  Nachladen der Pakete). Die Ausgabe deshalb **nie** in eine Datei umleiten,
  nie zitieren, nie weitergeben. Im Repo steht davon nichts.

## Sprache

YAML-Kommentare: Deutsch **ohne Umlaute** (`ae/oe/ue/ss`). Markdown und Chat:
normales Deutsch mit Umlauten.

## Kurz und wichtig

- Zum Anfassen sind `pv-dashboard.yaml` und die lokale
  `.pv-dashboard_anlage.yaml`. Daneben
  `.pv-dashboard_core.yaml`, `_display`, `_audio`, `_utility` und die
  Oberfläche: Kern `.pv-dashboard_ui.yaml` plus sieben Seitendateien in der
  Reihenfolge seines `packages:`-Blocks. Nicht am Stück lesen — Dateitabelle in
  `docs/03`. Ein neues Skript gehört zu der Seite, die es benutzt.
- Der Block zwischen `# >>> flow-animation` und `# <<< flow-animation` und die
  Widgets `flNN`/`flNNb` der Übersichtsseite stammen **nur** von
  `tools/flow_animation.py` — nie von Hand ändern.
- Die BMS-Anbindung ist bewusst ein Platzhalter. Nur bauen, wenn der Nutzer
  es verlangt (`docs/06`). Alle vier Detailseiten sind gebaut (PV & Prognose
  23.09.2026, Wallboxen, Wärmepumpe und Haus 24.09.2026); ihre Werte kommen
  über je ein Skript, bis dahin stehen Striche.
- Die sechs `docs/`-Dateien liegen als Kopie im Claude-Projekt; nach einer
  Änderung sagen, welche neu hochzuladen ist (Anleitung im Ordner
  `~/esphome-claude-projekt`).
