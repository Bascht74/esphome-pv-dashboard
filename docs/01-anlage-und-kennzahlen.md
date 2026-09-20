# 01 — Anlage und Kennzahlen

Der Aufbau der PV-Anlage, wie das Dashboard ihn abbildet, und die
Kennzahlen-Definitionen, die dafür festgelegt sind. Grundlage sind die
Festlegungen vom 30.07.2026 und die Beschriftungen im Anlagenschema in
`.pv-dashboard_page_overview.yaml`.

## Beschriftungen sind einstellbar, im Repo stehen Demo-Werte

Seit dem 20.09.2026 steht **keine** anlagenabhängige Beschriftung mehr fest im
Layout. Jede von ihnen ist eine Substitution:

- Der **Standard** steht im Paket, das den Kasten zeichnet — die acht Flächen, die
  vier Wechselrichter, der Volleinspeise-Rahmen, das Hausnetz, die Verbraucher, die
  Zähler und die Zweitzeile der Eigenverbrauchskachel in
  `.pv-dashboard_page_overview.yaml`, die drei Speichernamen zusätzlich in
  `.pv-dashboard_page_battery.yaml`. Dadurch bauen Simulator und Screenshot-Lauf
  ohne `pv-dashboard.yaml`.
- Die **eigene Anlage** wird in `pv-dashboard.yaml` beschrieben, im Block
  „HIER BESCHREIBEN SIE IHRE ANLAGE“ direkt hinter den Zugangsdaten. Was dort
  steht, sticht den Standard: ESPHome trägt die Substitutions der Hauptdatei zuerst
  ein und überspringt beim Einlesen der Pakete jeden Namen, den es schon kennt
  (in `esphome/components/packages` überspringt
  `_update_substitutions_context` bekannte Schlüssel, und
  `merge_config(paket, hauptdatei)` lässt die Hauptdatei gewinnen).
  Nachgewiesen mit 2026.9.0 im Config-Dump **und** im gerenderten Bild.

Die Werte **im Repo sind Demo-Werte** — neutrale Namen und runde Tarife, damit das
öffentliche Repo nicht die Anlage des Nutzers beschreibt. Dieses Dokument
beschreibt ebenfalls nur den **Aufbau**, nicht eine bestimmte Anlage: Fabrikate,
Typenbezeichnungen und die echten Flächennamen stehen im aktuellen Stand nirgends
mehr. Die Commit-Historie trägt sie noch; wie sie vor dem Veröffentlichen
bereinigt wird, steht in Dokument 06. Wer das Dashboard auf seine eigene Anlage
setzt, trägt seine Namen in `pv-dashboard.yaml` ein und hält seine
Anlagennotizen außerhalb des Repos.

Die Kästen sind knapp gerechnet. Eine längere Beschriftung kürzt LVGL mit „...“
(`long_mode: DOT`) oder sie bricht um. Hinter jeder Substitution in
`pv-dashboard.yaml` steht deshalb die gemessene Breite des Demo-Werts und die
verfügbare Breite. Nach jeder Änderung neu rendern und Dokument 04 durchgehen.

## Zwei getrennte Energiekreise

Der erste Wechselrichter läuft auf **Volleinspeisung**. Er darf deshalb im Schema
nicht durch das Hausnetz geführt werden, sondern geht am Hausnetz vorbei direkt
zum Zähler.

So ist es gezeichnet: Vom Voll-Wechselrichter läuft eine Leitung senkrecht nach
unten zum PV-Zähler und von dort waagerecht zum Hausanschluss. Sie berührt weder
den Kasten "Hausnetz" noch die Verbraucherschiene. Die Gruppe aus den beiden
Flächen `name_pv_1` und `name_pv_2` und dem Voll-Wechselrichter steht zusätzlich in
einem eigenen Rahmen; auf der unteren Rahmenlinie sitzt das zweizeilige Label
Volleinspeisung (`name_feedin`, Demo `"VOLLEIN-\nSPEISUNG"` — das `\n` im Wert ist
der Zeilenumbruch, je Zeile stehen 64 px zur Verfügung).

Alles andere (Mini-WR, beide Hybrid-Wechselrichter, Speicher, Verbraucher) hängt am
Hausnetz, dessen Überschuss über den Hauszähler zum Hausanschluss geht.

**Umstellung nach Ende der Förderung** (Festlegung vom 30.07.2026, noch nicht
gebaut): Läuft die Volleinspeisung aus, soll das eine reine Layoutänderung sein —
die Linie des Voll-Wechselrichters endet dann am Verteilerknoten statt am eigenen
Zähler. PV-Seite und Kacheln bleiben unverändert.

## Erzeugung: Wechselrichter und Dachflächen

Je Wechselrichter zwei Flächen, im Schema als Paar über dem Gerät:

| Substitution | Demo im Repo | Flächen darüber (Substitution, Demo) |
| --- | --- | --- |
| `name_inv_1` | `Voll-WR 7 kW` | `name_pv_1` → `Dach Süd`; `name_pv_2` → `Dach West` |
| `name_inv_2` | `Mini-WR 0,8 kW` | `name_pv_3` → `Modul 1`; `name_pv_4` → `Modul 2` |
| `name_inv_3` | `Hybrid 10 kW · A` | `name_pv_5` → `Dach Ost`; `name_pv_6` → `Nebendach` |
| `name_inv_4` | `Hybrid 10 kW · B` | `name_pv_7` → `Dach Nord`; `name_pv_8` → `Garagendach` |

`name_pv_1` bis `name_pv_8` stehen im Schema von links nach rechts; Platz 3 und 4
sind die beiden Einzelmodule. Die Leistung gehört in die Beschriftung des
Wechselrichters, sie steht sonst nirgends auf der Seite.

Der Mini-Wechselrichter versorgt zwei Einzelmodule; im Schema steht er mit 0,8 kW.

Damit sind es sechs Dachflächen plus zwei Einzelmodule. Die Dachflächen tragen jeweils
Momentanleistung in W und den Tageswert in kWh.

## Speicher

Drei Speicher hängen über eine Busbar an **beiden** Hybrid-Wechselrichtern. Im
Schema führen von beiden Hybriden Leitungen auf einen gemeinsamen Wertkasten,
von dort geht es auf die Schiene, an der die drei Kästen `name_bat_1`,
`name_bat_2` und `name_bat_3` hängen (Demo `Speicher 1` bis `Speicher 3`).
Dieselben drei Namen tragen auf der Speicherseite die Ringe und die
Tabellenköpfe, dort in Großbuchstaben: Im YAML steht `${ name_bat_1 | upper }`,
der Wert selbst bleibt normal geschrieben. Der Standard steht deshalb doppelt —
in der Übersichts- **und** in der Speicherseite; beide Stellen müssen gleich
lauten, ein Wert aus `pv-dashboard.yaml` sticht ohnehin beide. Laufen die beiden
Pakete auseinander, gewinnt stillschweigend die Speicherseite: Unter Paketen
sticht der spätere Eintrag im `packages:`-Block von `.pv-dashboard_ui.yaml`, und
gemeldet wird das nicht (geprüft mit 2026.9.0) — die Standards in der
Übersichtsseite sind dann wirkungslos. Die Zweitzeile unter dem Mittelwert ist
`name_bat_summary` (Demo „Mittel der drei Speicher“).

Je Speicher zeigt das Schema SoC, Strom und Spannung; die Detailseite zeigt zusätzlich
Zellspannungen, Temperaturen und Zyklen. Das BMS sitzt an einem 16S-LiFePO4-Pack
und wird seriell angebunden; welches Fabrikat, gehört zur jeweiligen Anlage und
steht nicht im Repo. Die Anbindung ist bewusst vertagt (siehe Dokument 06, offene
Punkte).

## Verbraucher

Am Hausnetz hängen vier Kästen auf der Verbraucherschiene:

- `name_heatpump` — Wärmepumpe, Zweitzeile mit COP (Demo `Wärmepumpe`)
- `name_misc` — Sammelposten für alles übrige am Hausnetz; Zweitzeile `kW · Basis --`
  (Demo `Sonstige`)
- `name_wb_1` und `name_wb_2` — zwei Wallboxen (Demo `Wallbox 1`, `Wallbox 2`)

Der Knoten darüber heißt `name_house` (Demo `Hausnetz`).

## Zähler

Drei Kästen in der unteren Reihe des Schemas:

- `name_meter_pv` — eigener Zähler des Volleinspeise-Kreises (Demo `PV-Zähler`)
- `name_meter_house` — Einspeisung/Bezug des Hauskreises (Demo `Hauszähler`)
- `name_grid` — Netzpunkt in der Mitte, Wert in kW mit Richtungsangabe
  (Demo `Hausanschluss`)

## Festgelegte Kennzahlen-Definitionen

Alle drei Definitionen sind am 30.07.2026 festgelegt worden.

### Eigenverbrauchsquote

Bezieht sich **nur auf den Hybrid-Kreis**, nicht auf die Gesamterzeugung.

```
Eigenverbrauchsquote = (Hybrid-Erzeugung − Überschusseinspeisung) / Hybrid-Erzeugung
```

Grund: Der Voll-Wechselrichter läuft auf Volleinspeisung. Seine Erzeugung würde als
"nicht selbst verbraucht" in die Quote eingehen und sie künstlich drücken. Die Kachel
trägt dazu die Zweitzeile `name_selfuse_note` (Demo „ohne Voll-WR“). Bewusst ein
eigener Text und kein Verweis auf `name_inv_1`: Dort steht die Leistung mit,
„ohne Voll-WR 7 kW“ wäre 112 px breit und würde in der nur 92 px schmalen
Kachel umbrechen. Wer `name_inv_1` ändert, zieht hier von Hand nach.

### Autarkie

Momentanwert und Tageswert dürfen auseinanderlaufen, das ist gewollt: Als Tageswert
liegt die Autarkie praktisch nie bei 100 %, weil nachts immer etwas Netzbezug anfällt.

- Statusleiste: Momentanwert, zusammen mit der Restprognose
  (`Autarkie -- % · Restprognose --,- kWh`)
- Kachel: Tageswert im Ring; die Zweitzeile der Kachel steht in
  `.pv-dashboard_page_overview.yaml` noch auf "Monat -- %". Das ist ein Versehen: Am
  20.09.2026 hat der Nutzer entschieden, dass die Kachel beim **Tageswert**
  bleibt und die Zweitzeile ihn auch so benennen soll. Die Textänderung am Panel
  steht noch aus — **offen, siehe Dokument 06**.

### Geldwerte und Tarife

Die Tarife gehören zur Anlage, nicht zur Oberfläche. Sie standen bis zum 20.09.2026
im Abschnitt „Farben und Maße“ von `.pv-dashboard_utility.yaml` und stehen jetzt bei
den übrigen Anlagen-Einstellungen in `pv-dashboard.yaml`. Damit bleiben die eigenen
Tarife auf dem Rechner, auch wenn die Pakete aus dem GitHub-Repo nachgeladen
werden. Ein Standard liegt in `.pv-dashboard_page_overview.yaml`, der Seite mit der
Kachel „TAGESERTRAG“, damit Simulator und Screenshot-Lauf weiterbauen.

Im Repo stehen runde Demo-Werte:

```yaml
tarif_volleinspeisung_ct: "20.0"  # Volleinspeisung
tarif_ueberschuss_ct: "10.0"      # Ueberschusseinspeisung
tarif_bezug_ct: "30.0"            # Strombezug
```

Benutzt wird bisher keiner der drei: Die Kachel zeigt Strichmuster, die Geldrechnung
ist noch nicht gebaut (Dokument 06).

Die Kachel "TAGESERTRAG" zeigt einen Gesamtbetrag in Euro und daneben drei Zeilen:
Förderung, Gespart, Bezug.

## Regeln für Werte und Einheiten

Diese Regeln gelten für jeden angezeigten Wert:

- **Die Einheit steht unter dem Wert, nie dahinter.** Kein Wert ohne Einheit.
- **Geld auf zwei Nachkommastellen, Energie auf eine.**
- **Zweitzeile:** Einheit und Tageswert teilen sich eine Zeile. Muster im Schema:
  `kW · --,- kWh` bzw. `W · --,- kWh` — die Einheit des Hauptwerts steht am Anfang,
  danach der Tageswert mit eigener Einheit, getrennt durch ` · `. Das spart je Kasten
  rund 17 px plus einen Zeilenabstand.
- **Kacheln der rechten Spalte:** Titel in Großbuchstaben, darunter der Wert, darunter
  die Zweitzeile (z. B. "kWh heute").
- **Ringkacheln** (Autarkie, Eigenverbrauch): Wert und "%" mittig im Ring, Beschriftung
  und Zweitzeile daneben.
- **Speicherwerte im Schema:** Strom **vor** der Spannung und ganzzahlig
  (`% · -12 A · 53,2 V`). Die Nachkommastelle beim Strom gibt es nur in der Tabelle der
  Speicherseite.
- **Fehlender Wert** wird als Strichmuster in der Stellenzahl des erwarteten Werts
  gezeigt: `--,-`, `-.---`, `--,--`.

Die Breiten sind knapp gerechnet; jede Änderung an Texten oder Einheiten geht gegen die
Prüfliste in Dokument 04 (LVGL-Checkliste).

## Datenquellen

- **Wärmepumpe:** über Home Assistant.
- **Alles andere:** möglichst nativ über **Modbus RTU**, nicht über Modbus TCP.
- **Zeit:** kommt auf dem Gerät von Home Assistant (`time: platform: homeassistant`),
  im Simulator von der Systemuhr.

Angebunden ist bisher nichts davon. Die Oberfläche hat dafür feste Schnittstellen
(`alert_push`, `storage_update`, `record_hour`, `WATT[]`), siehe Dokument 03 zum Dashboard-Aufbau.

---

Stand: 20.09.2026 (Aufbau- und Kennzahlenfestlegungen vom 30.07.2026; die
Entscheidung zur Autarkie-Zweitzeile vom 20.09.2026; Beschriftungen und Tarife am
20.09.2026 auf Substitutions mit Demo-Werten umgestellt; am selben Tag Fabrikate,
Typenbezeichnungen und echte Flächennamen aus dem Dokument genommen). Geprüfter Commit:
`c6a432f` (12.09.2026).
