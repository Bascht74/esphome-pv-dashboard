# 04 — LVGL-Checkliste und Rendering

Pflichtliste nach **jeder** Layoutänderung, bevor die Änderung als fertig
gemeldet wird. Sie ist aus Fehlern entstanden, die die Konfigurationsprüfung
nicht findet und die im gerenderten Bild sofort zu sehen waren: gedrehte
Oberfläche, überlaufende Batteriewerte, abgeschnittenes "EIGENVERBRAUCH",
fehlende Wechselrichternamen durch zu niedrige Kästen.

Wichtigster Satz vorweg: `esphome config` prüft nur Syntax und Semantik. **Alle**
hier genannten Fehler bestehen die Validierung anstandslos und zeigen sich nur
im gerenderten Bild.

## 1. Kastenhöhen bei Flex ausrechnen, nicht schätzen

`pad_row`/`pad_column` gehören in den **`layout:`-Block** (FLEX/GRID), in
`style_definitions`/`theme` oder in das `layout:` von `lvgl.widget.update` --
direkt am Widget lehnt ESPHome sie ab (`[pad_row] is an invalid option for
[obj]`). Ohne die Angabe gilt der Abstand aus LVGLs Standard-Theme (rund 8 px),
und `flex_align_main: CENTER` schneidet die erste und letzte Zeile dann
**stillschweigend** am Rahmen ab, ohne Fehlermeldung.

Rechnung je Kasten, vor dem Melden aufstellen:

```
Summe Zeilenhoehen + pad_row x (Zeilen - 1)
  <  Hoehe - 2 x pad_all - 2 x border_width      Reserve muss > 0 sein
```

Verfügbare Seitenhöhe: **668 px** (y 76 bis y 744) -- zwischen Statusleiste,
der dauerhaft eingeblendeten Meldungszeile und der Reiterleiste. Seiteninhalt
beginnt bei y 84 (Dokument 03).

**Die vierzehn Schriften des Projekts.** `size:` steht in
`.pv-dashboard_utility.yaml` -- das ist die Stellschraube. `line_height` ist der
**vierte** Parameter von `font::Font(...)` im erzeugten Schriftcode
`.esphome/build/pv-dashboard-sim/src/main.cpp` -- damit wird gerechnet. Beide
Spalten stehen hier nebeneinander, weil die eine aus der anderen **nicht**
hochgerechnet werden darf. Die Schriften sind ein gemeinsames Package, die Werte
gelten auch am Gerät. Abgelesen am 20.09.2026:

| Schrift | `size:` | `line_height` | Weg zum Widget |
| --- | --- | --- | --- |
| `f_text` | 17 | 22 | **Theme** (`text_font`) -- überall, wo nichts anderes gesetzt ist |
| `f_label` | 13 | 17 | `style_definitions` → `st_label` |
| `f_unit` | 13 | 17 | `style_definitions` → `st_unit`, `st_sub`; dazu sehr oft direkt |
| `f_text_s` | 15 | 20 | `style_definitions` → `st_btn`; auch direkt |
| `f_val_s` | 16 | 21 | direkt am Widget |
| `f_alert` | 19 | 25 | direkt am Widget -- Meldungszeile im `top_layer` |
| `f_val_m` | 19 | 25 | direkt am Widget |
| `f_bar` | 22 | 29 | direkt am Widget -- Statusleiste (`lbl_status_left`, `lbl_date`, `lbl_clock`) |
| `f_val_l` | 23 | 30 | direkt am Widget |
| `f_icon` | 24 | 24 | direkt am Widget |
| `f_val_xl` | 30 | 39 | direkt am Widget |
| `f_wx_l` | 44 | 44 | direkt am Widget -- Wetterbilder der Tagesspalten (Prognose, Wetter); abgelesen am 25.09.2026 im shots-Bau |
| `f_wx_xl` | 88 | 88 | direkt am Widget -- Wetterbild „jetzt“; abgelesen am 25.09.2026 im shots-Bau |

Die Modulbilder sind 24 px hoch. Bei einer neuen Schrift den Wert ebenso
nachsehen, nicht schätzen. Zum Auffrischen
`~/.venvs/esphome-beta/bin/esphome compile pv-dashboard-sim.yaml` laufen lassen
-- das baut nur, öffnet kein Fenster -- und `line_height` neu ablesen.
**Wird das `size:` einer vorhandenen Schrift geändert, gilt die Tabelle nicht
mehr:** neu ablesen, nicht hochrechnen.

**Und die Änderung bleibt nie lokal.** Die Schriften stehen genau einmal in
`.pv-dashboard_utility.yaml`, einem gemeinsamen Package von Gerät und Simulator.
Über Theme und `style_definitions` (Spalte „Weg zum Widget") hängen sie an
**allen elf Seiten**, nicht nur an der, wegen der geändert wurde. Ein
geändertes `size:` verschiebt jede Zeile, die diese Schrift benutzt. Danach
Pflicht, in dieser Reihenfolge: neu kompilieren, `line_height` neu ablesen,
**jede** betroffene Kastenhöhe mit der Formel oben neu rechnen und alles neu
rendern (Punkt 7) -- nicht nur die geänderte Stelle.

**Was auf der Übersicht hängt** (für Aufträge wie „Schrift größer"): über das
Theme `f_text`, über die Stile `st_label` (`f_label`) und `st_unit`/`st_sub`
(`f_unit`), direkt am Widget `f_val_xl`, `f_val_l`, `f_val_m`, `f_val_s`,
`f_icon` und einmal `f_text_s`. `f_bar` und `f_alert` gehören zu den Leisten im
`top_layer` und liegen damit über **jeder** Seite. Vor dem Ändern klären, welche
davon gemeint ist -- `f_text` und `f_unit` treffen alle elf Seiten.

Die Rechnung hat schon zweimal einen Fehler abgefangen, den sonst erst der
Screenshot gezeigt hätte. Beispiel (Hausnetz-Kasten im Schema): `24 + 20 + 39 + 17 = 100`, plus `3 x pad_row 4 =
112`; innen `128 - 2 x 1 - 2 x 2 = 122` -> Reserve 10.

## 2. Einheitenregel

Die Regeln für Werte und Einheiten stehen in Dokument 01. Fürs Layout zählt
hier: Einheit und Tageswert teilen sich **eine** Zeile ("W · --,- kWh"), das
spart je Kasten 17 px plus einen Abstand. Mehrere Werte in einer Einheitenzeile
trennen Pfeil-Icons direkt vor der Zahl, keine Leerzeichen: `f_unit` hat keine
festen Zeichenbreiten.

## 3. Textüberlauf -- DOT braucht eine feste Höhe

Jedes Label in enger Fläche braucht `width:` **plus** `long_mode`. Ohne Breite
wachsen LVGL-Labels beliebig weit über ihren Container hinaus. Deutsche Wörter
sind lang: "EIGENVERBRAUCH", oder der Entitätsname `"Lautsprecher-Verstaerker"`.
Gelöst ist der erste Fall heute durch einen Umbruch im Text selbst: Die Kachel
trägt `text: "EIGEN-\nVERBRAUCH"` mit `long_mode: WRAP`.

- `DOT` kürzt mit Auslassungspunkten -- **in LVGL 9 nur mit fester `height`**
  (eine Zeile = Zeilenhöhe der Schrift). Ohne Höhe bricht das Label um und
  läuft aus seinem Kasten; das fiel am 11.09.2026 auf der Meldungsseite auf.
- `WRAP` bricht an Leerzeichen um, ohne Silbentrennung. `CLIP` ändert den Text
  nie.

Nebenwirkung von `DOT`: LVGL schreibt das "..." in den **Textpuffer**. Auf einer
nie gezeigten Seite haben die Labels keine Breite, der Text wird ganz zu "...".
Deshalb trägt jede Zeile der Meldungsliste ein verstecktes Kind 5 mit
`long_mode: CLIP`, aus dem die Meldungszeile der Statusleiste liest.

**Die anlagenabhängigen Beschriftungen sind seit dem 20.09.2026 einstellbar**
(`name_pv_1` … `name_meter_house`, Dokument 01). Damit kann jeder dieser Kästen
seinen Text von außen bekommen, ohne dass das Layout es merkt. Zwei Pflichten
folgen daraus:

- Wer einen Standard im Paket **oder** einen Wert in `.pv-dashboard_anlage.yaml`
  ändert, misst die neue Breite und rendert neu. Hinter jeder Substitution steht die
  gemessene Breite des Werts und die verfügbare Breite des Labels.
- Wer die **Breite eines Kastens** ändert, zieht diese Zahlen in
  `.pv-dashboard_anlage.yaml.example` und im Standardblock des Pakets nach. Sie
  sind sonst stillschweigend falsch und die nächste Änderung rechnet mit dem
  alten Wert. Flächen- und Wechselrichternamen stehen zusätzlich auf der Seite
  PV & Prognose (135 bzw. 284 px); die Zahlen gelten für die engere Stelle,
  das Schema der Übersicht.

Nachgemessen wird in der Schrift des Labels (`f_unit` 13, `f_text_s` 15,
`f_label` 13 mit `text_letter_space: 1`): Summe der Glyph-Vorschübe, je Glyph auf
ganze Pixel aufgerundet -- so rechnet ESPHome die Schrift (`pt_to_px` in
`esphome/components/font`), und so summiert LVGL sie. Gegenprobe: "SPEISUNG" in
`f_unit` ergibt 64 px, genau die Breite, mit der der Volleinspeise-Rahmen im
YAML gerechnet ist.

## 4. Scrollbalken UND Verschiebbarkeit

`scrollbar_mode: 'off'` blendet nur die Striche aus -- **gescrollt wird
trotzdem**. Der Nutzer konnte Kacheln und den ganzen Schemabereich mit dem
Finger verschieben. Nötig ist `scrollable: false`, auch auf den Seiten selbst
(`- id: page_…`), die ebenfalls Objekte sind. Laut Quelltextprüfung vom
11.09.2026 reicht das allein; `scroll_dir: NONE` und `scrollbar_mode: 'off'`
sind daneben überflüssig, aber harmlos.

**Einzige Ausnahme:** `alert_list` auf der Meldungsseite, die einzige scrollende
Fläche der Oberfläche. Die Seite bleibt `scrollable: false`;
`scroll_chain: false` reicht einen Wisch am Listenende nicht an die Seite
weiter, `scroll_elastic: false` lässt die Liste nicht nachfedern.

## 5. Symmetrie ist ein Qualitätsmaßstab, kein Bonus

Vom Nutzer am 31.07.2026 zum Standard erklärt:

- gleiche Ränder links und rechts, gleiche Abstände zwischen gleichrangigen
  Elementen; waagerechte Anschlussstücke links und rechts gleich lang
- Wertkästen exakt auf der Mitte der Gruppe, die sie zusammenfassen
- Abzweigungen unter einem Gerät spiegelbildlich um dessen Mitte. Beim dritten
  Wechselrichter (Mitte 567): Solarabgang bei 553 (-14), Speicherleitung bei 581
  (+14); beim vierten (Mitte 797) entsprechend 783 und 811. Die Einspeisung knickt
  gespiegelt zur Solarleitung ab: 553 / 811 = 682 -/+ 129, beide 30 px unter
  den Kästen.

Vor dem Melden die Mitten ausrechnen -- "sieht ungefähr mittig aus" reicht
nicht. Bewusste Ausnahmen als YAML-Kommentar: Der Mini-WR steht mit Mitte 337
über dem Hausnetz mit Mitte 330, der Versatz von 7 folgt dem Dachraster.

## 6. Kollisionen, Leitungen, Containerrand

- **Kollisionen** absolut positionierter Elemente prüfen, besonders
  Werte-Schilder auf Leitungen gegen Gerätebeschriftungen.
- **Leitungsgeometrie** nach jeder Höhenänderung nachziehen: die
  Linienkoordinaten müssen zu den neuen Kastenkanten passen.
- **Nichts über den Containerrand hinaus.** Negative `x`/`y` (etwa ein
  Rahmenlabel bei `y: -9`) werden abgeschnitten, nicht überzeichnet.

## 7. Das Rendering wirklich ansehen

Drei Schritte, keiner darf ausfallen, beide Befehle aus dem Projektordner (ein
`esphome` im PATH gibt es auf diesem Rechner nicht, daher der volle Pfad; `sips`
bringt nur macOS mit, die plattformunabhängige Pillow-Variante steht in
Dokument 03):

```
~/.venvs/esphome-beta/bin/esphome run pv-dashboard-shots.yaml
sips -s format png shots/*.bmp --out shots/
```

Der dritte Schritt ist das Hinsehen: **die PNG öffnen, Ausschnitte vergrößern
und jede geänderte Stelle einzeln ansehen** -- das kostet keinen Flash-Zyklus.
Der Lauf schreibt **BMP**, das eine Assistenz-Sitzung nicht öffnen kann; ohne
die Umwandlung ist dieser Punkt nicht erfüllt. **Alles Weitere steht in
Dokument 03** -- Pillow-Variante, Ausschnittbefehl, Dateinamen, Bauzeiten. Dort
steht die Kette einmal vollständig, hier nur der Pflichtschritt.

Die Headless-Aufnahmen vom 11.09.2026 fanden sofort zwei übersehene Fehler:
abgeschnittene Unterzeilen in fast allen Flex-Kästen der Übersicht und ein
"€", das den letzten Strich von "--,--" überlagerte und wie "£" aussah.

## 8. Generatorskripte

Wenn Layoutblöcke per Python erzeugt werden (`tools/flow_animation.py`): auf
`%` in Formatstrings achten. Ein unmaskiertes Prozentzeichen landete als `%%` im
YAML und damit auf dem Panel. Nach dem Erzeugen `grep -c '%%'` laufen lassen,
Sollwert 0.

## 9. RGB565: was das Panel mit Farben macht

16 Bit Farbtiefe **ohne Dithering** zeigt bei Verläufen Stufen. Kräftige
Verläufe deshalb nur auf schmalen Ringen und Balken; Flächen bekommen Töne,
deren Stufen breit bleiben und nicht farbig flimmern.

**Zwei Mischwege.** `VER` färbt je Zeile und mischt mit `(opa + 4) >> 3`, also
in 32 Stufen für alle Kanäle zugleich. `HOR`, `LINEAR` und `RADIAL` mischen je
Pixel, und **jeder Kanal rundet für sich**: R, G und B springen dann an
verschiedenen Stellen -- Streifen mit Farbstich.

**Warum dunkle warme Mischungen grün werden.** RGB565 führt G mit 6 Bit, R und
B nur mit 5; dunkle warme Mischungen fallen darum auf G-Stufen. Beispiel: Die
vorgemischte Gold-Tönung der Gerätekästen ergab rechnerisch R/G/B 2/7/3 --
türkis, 171 Grad in LCh. Gewählt ist 4/6/2 (`col_box_full`, `col_box_solar`):
L\* 9,1, 66 Grad Orange-Braun. Ebenso stuft `col_lit_tail` zuerst in R statt in
G, sonst wird der Auslauf der Dachgruppen unten grün.

Faustregel: G nur wenig über `col_bg`, B nicht darunter -- sonst fällt B schon
bei kleinster Deckkraft und es wird grünlich. Die ersten Stufen über `col_bg`
können in RGB565 gar nicht warm sein (einzeln +R, +G oder -B). Ändert sich
`col_bg` oder `col_surface`, **im Bild nachmessen**, nicht nur nachrechnen.

**Billig gegen teuer.** LVGL 9.5 rechnet die Farbtabelle bei jedem Zeichnen neu
(kein Cache): `VER` eine Farbe je Zeile, `LINEAR` je Pixel eine Projektion,
`RADIAL` und konisch je Pixel einen Abstand bzw. Winkel.

**Keine teuren Verläufe unter den Flusskugeln.** Die Flussanimation lässt die
Kugeln alle 20 ms neu zeichnen; wo eine Kugel unter einem Kasten verschwindet,
zeichnet LVGL diesen Ausschnitt mit. Dort liegt darum höchstens ein
`VER`-Verlauf, **nie** `HOR`, `LINEAR`, `RADIAL` oder konisch. Konisch und
radial stehen nur auf den Ringen und dem Hausnetz-Schein ohne Kugeln.

**Kanten von Kasten-in-Kasten-Flächen.** Ein Schein auf einer getönten Fläche
muss ohne Kante auslaufen: Kasten deckend getönt bis an den Rahmen, darauf von
oben ein Schein auf voller Innenbreite. Der Hausnetz-Schatten läuft bewusst
nicht auf 0 %, sondern auf 3 % -- LVGL rundet beim Mischen ab, bei 0 wäre die
ganze Breite an einer Stelle um eine Stufe gesprungen, als sichtbare Linie.
Radien konzentrisch zum Rahmen setzen (Schein 6 in Rahmen 7), sonst zeigen die
Ecken eine Tasche.

---

Stand: 20.09.2026 (Zeilenhöhen aus `main.cpp` und `size:` aus
`.pv-dashboard_utility.yaml`, alle zwölf an diesem Tag neu abgelesen; Punkt 3 am
20.09.2026 um die einstellbaren Beschriftungen ergänzt). Geprüfter Commit:
`c6a432f` (12.09.2026).
