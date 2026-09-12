#!/usr/bin/env python3
"""
Erzeugt die Flussanimation fuer das Anlagenschema in .pv-dashboard_ui.yaml.

    python3 tools/flow_animation.py            # Vorschau, schreibt nichts
    python3 tools/flow_animation.py --write    # baut die Animation ein

Das Skript liest die Leitungen aus der UI-Datei, leitet die Topologie aus den
Koordinaten ab und erzeugt daraus die Kugel-Widgets samt Steuerlogik. Nach
jeder Aenderung am Schema einfach erneut laufen lassen -- von Hand gepflegte
Koordinatenlisten gibt es dadurch nicht.

--write ersetzt die vorhandenen Kugel-Widgets (IDs flNN, flNNb am Anfang der
Widgets von schema_area) und den Block zwischen den Markern; ein zweiter Lauf
aendert nichts. Die Vorschau meldet, ob die Datei schon aktuell ist.

------------------------------------------------------------------------------
DIE REGELN, jede aus einem konkreten Fehler im Bild entstanden:

1. KREUZUNGEN SIND KNOTEN.
   Eine Zuleitung, die eine Sammelschiene kreuzt, endet dort nicht -- optisch
   laeuft sie durch. Erst wenn man den Schnittpunkt als Knoten nimmt,
   zerfaellt die Schiene in ihre tatsaechlichen Abschnitte.

2. SCHNITTPUNKTE SORTIERT EINFUEGEN.
   Kommen sie aus einem Set, ist die Reihenfolge zufaellig und die Strecke
   zerfaellt in einander ueberlappende Stuecke. Sortieren nach Abstand vom
   Segmentanfang.

3. GETEILTE STUECKE ERBEN DIE ZEICHENRICHTUNG.
   Eine von links nach rechts gezeichnete Schiene ergibt nach dem Teilen ein
   Stueck, das zum Einspeisepunkt zeigt statt von ihm weg. Solche Stuecke
   umdrehen, sonst laufen auf einer Schiene Kugeln gegeneinander.

4. VERTEILSTRECKEN SCHWEIGEN.
   Eine waagerechte Strecke, die sich verzweigt ODER von einem
   Verzweigungsknoten ausgeht, hat keine Richtung -- sie verteilt. Eine Kugel
   darauf wuerde eine Richtung behaupten, die es nicht gibt. Eine einzelne
   Querverbindung ohne Verzweigung behaelt ihre Kugel.

5. ANKUNFT LOEST AUS UND STARTET NEU.
   Kommt eine Kugel am Knoten an, bekommt der Abgang seine Kugel und die
   Zuleitung faengt sofort wieder an. Endlos von sich aus laufen nur die
   speisenden Strecken und die Abgaenge hinter Verteilstrecken -- die koennen
   keinen sichtbaren Impuls bekommen.

6. ZWEI ZULEITUNGEN, ZWEI KUGELN.
   Wo zwei Strecken zusammentreffen, loest jede ankommende Kugel eine eigene
   aus. Der Abgang braucht dafuer ein zweites Widget, sonst geht die zweite
   Zuleitung unter.

7. GESCHWINDIGKEIT AUS LEISTUNG UND LAENGE.
       50..500 W   T = 16 s / (W/50)^0,30103     Verzehnfachung halbiert
       ab 500 W    T =  8 s / (W/500)^0,48945    35 kW ergeben 1 s
   Stetiger Uebergang bei 500 W = 8,00 s. Dazu ein Laengenfaktor
   (L/L_max)^0,5: kurze Strecken laufen deutlich schneller um, weil die Kugel
   dort sonst traege wirkt -- die meisten Abgaenge sind nur 11 bis 16 px lang,
   da bleibt bei gleicher Umlaufzeit kaum Bewegung uebrig. Die laengste
   Strecke bleibt unveraendert. Der Exponent ist die wirksamste Stellschraube
   gegen Ruckeln auf kurzen Strecken -- wirksamer als Takt oder Schwelle.

8. FLAECHENBUDGET.
   LVGL merkt sich 32 ungueltige Flaechen je Bild; laeuft der Puffer ueber,
   wird der ganze Schirm neu gezeichnet (auf 1280x800 sind das 2 MB). Jede
   Bewegung kostet zwei Flaechen. Deshalb ein Deckel auf MAXMOVE Bewegungen
   je Tick, der Rest wartet einen Tick. Das Dashboard braucht zusaetzlich
   Reserve fuer Uhr, Messwerte und die Stundenbalken.
------------------------------------------------------------------------------
"""
import re
import sys
from pathlib import Path

UI = Path(__file__).resolve().parent.parent / ".pv-dashboard_ui.yaml"
TICK = 20          # ms -- nah am LVGL-Refresh (16 ms), damit schnelle
                   # Kugeln oft drankommen; langsame melden sich seltener
DOT = 8            # Kugeldurchmesser in px
MAXMOVE = 13       # Bewegungen je Tick -> 26 von 32 Flaechen. Die restlichen
                   #  6 reichen dem Dashboard: Uhr und Messwerte aendern sich
                   # im Minutentakt, die Stundenbalken nur bei neuen Daten
MARKER = "# >>> flow-animation"


def leitungen_lesen(text):
    block = text[text.index("id: schema_area"):]
    return [
        {"pts": [[int(x), int(y)] for x, y in re.findall(r"\[(\d+),(\d+)\]", m.group(1))],
         "col": m.group(2)}
        for m in re.finditer(
            r"- line: \{ points: \[((?:\[\d+,\d+\],?)+)\], line_color: \$(\w+)", block)
    ]


def auf_strecke(p, a, b):
    (px, py), (ax, ay), (bx, by) = p, a, b
    return ((ax == bx == px and min(ay, by) < py < max(ay, by)) or
            (ay == by == py and min(ax, bx) < px < max(ax, bx)))


def topologie(lines):
    """Regeln 1 bis 4: Knoten finden, teilen, drehen, Verteilstrecken erkennen."""
    knoten = {tuple(l["pts"][0]) for l in lines} | {tuple(l["pts"][-1]) for l in lines}

    # Regel 1 -- echte Kreuzungen waagerecht x senkrecht
    segs = [(l["pts"][k], l["pts"][k + 1]) for l in lines for k in range(len(l["pts"]) - 1)]
    for a0, a1 in segs:
        for b0, b1 in segs:
            if a0[1] == a1[1] and b0[0] == b1[0]:
                x, y = b0[0], a0[1]
                if (min(a0[0], a1[0]) < x < max(a0[0], a1[0]) and
                        min(b0[1], b1[1]) < y < max(b0[1], b1[1])):
                    knoten.add((x, y))

    # Regel 2 -- an den Knoten teilen, Schnittpunkte SORTIERT einfuegen
    teile = []
    for l in lines:
        p = [tuple(x) for x in l["pts"]]
        cut = {k for k in range(1, len(p) - 1) if p[k] in knoten}
        treffer = []
        for k in range(len(p) - 1):
            auf = [e for e in knoten if auf_strecke(e, p[k], p[k + 1])]
            auf.sort(key=lambda e: abs(e[0] - p[k][0]) + abs(e[1] - p[k][1]))
            treffer.append((k, auf))
        for k, auf in reversed(treffer):
            for e in reversed(auf):
                p.insert(k + 1, e)
            cut = {i + len(auf) if i > k else i for i in cut} | {k + 1 + j for j in range(len(auf))}
        idx = sorted(cut)
        if not idx:
            teile.append({"pts": [list(x) for x in p], "col": l["col"]})
            continue
        start = 0
        for c in idx + [len(p) - 1]:
            if c > start:
                teile.append({"pts": [list(x) for x in p[start:c + 1]], "col": l["col"]})
                start = c

    # Regel 3 -- rueckwaerts zeigende Querstuecke umdrehen
    speise = {tuple(l["pts"][-1]) for l in teile if l["pts"][-2][0] == l["pts"][-1][0]}
    for l in teile:
        p = l["pts"]
        waag = all(p[k][1] == p[k + 1][1] for k in range(len(p) - 1))
        if waag and tuple(p[-1]) in speise and tuple(p[0]) not in speise:
            l["pts"] = p[::-1]

    ab = {}
    for i, l in enumerate(teile):
        ab.setdefault(tuple(l["pts"][0]), []).append(i)
    succ = {}
    for i, a in enumerate(teile):
        for j in ab.get(tuple(a["pts"][-1]), []):
            if i != j:
                succ.setdefault(i, []).append(j)

    # Regel 4 -- Verteilstrecken: verzweigen selbst oder gehen von einer
    # Verzweigung aus
    still = [i for i, l in enumerate(teile)
             if all(l["pts"][k][1] == l["pts"][k + 1][1] for k in range(len(l["pts"]) - 1))
             and (len(succ.get(i, [])) >= 2 or len(ab[tuple(l["pts"][0])]) >= 2)]
    return teile, succ, still, ab


def laenge(pts):
    return sum(abs(pts[k + 1][0] - pts[k][0]) + abs(pts[k + 1][1] - pts[k][1])
               for k in range(len(pts) - 1))


def erzeugen(lines):
    teile, succ, still, ab = topologie(lines)
    n = len(teile)
    ziele = {j for v in succ.values() for j in v}
    frei = {j for i in still for j in succ.get(i, [])}
    root = [i not in ziele or i in frei for i in range(n)]          # Regel 5
    vor = {}
    for i, v in succ.items():
        for j in v:
            vor.setdefault(j, []).append(i)
    # Regel 6: Ausloesen kann nur eine Zuleitung mit Kugel. Stehen vor einer
    # Strecke nur Verteilstrecken (Regel 4), bliebe die zweite Kugel ewig
    # verborgen -- ein totes LVGL-Objekt.
    slot2 = [i for i in range(n) if len(vor.get(i, [])) >= 2
             and any(p not in still for p in vor[i])]

    segs, offs, cnt = [], [], []
    for l in teile:
        p = l["pts"]
        offs.append(len(segs))
        c = 0
        for k in range(len(p) - 1):
            d = abs(p[k + 1][0] - p[k][0]) + abs(p[k + 1][1] - p[k][1])
            if d:
                segs.append((p[k][0], p[k][1], p[k + 1][0], p[k + 1][1], d))
                c += 1
        cnt.append(c)
    sf, so, sc = [], [], []
    for i in range(n):
        so.append(len(sf))
        v = succ.get(i, [])
        sf += v
        sc.append(len(v))
    lmax = max(laenge(l["pts"]) for l in teile)
    return dict(teile=teile, succ=succ, still=still, ab=ab, root=root, slot2=slot2,
                segs=segs, offs=offs, cnt=cnt, sf=sf, so=so, sc=sc, lmax=lmax, n=n)


def bericht(d):
    print(f"{d['n']} Teilstrecken, {sum(d['sc'])} Uebergaenge")
    print(f"{len(d['still'])} Verteilstrecken schweigen (Regel 4)")
    print(f"{sum(d['root'])} laufen endlos, {d['n'] - sum(d['root'])} werden ausgeloest (Regel 5)")
    print(f"{len(d['slot2'])} Strecken mit zweiter Kugel (Regel 6)")
    print(f"laengste Strecke {d['lmax']} px, Laengenfaktor bezieht sich darauf (Regel 7)")
    print(f"Deckel {MAXMOVE} Bewegungen/Tick = {MAXMOVE * 2} von 32 Flaechen (Regel 8)")
    # Ueberlappungsprobe -- Regel 2
    n = 0
    for i, a in enumerate(d["teile"]):
        for b in d["teile"][i + 1:]:
            for k in range(len(a["pts"]) - 1):
                for m in range(len(b["pts"]) - 1):
                    a0, a1 = a["pts"][k], a["pts"][k + 1]
                    b0, b1 = b["pts"][m], b["pts"][m + 1]
                    if a0[1] == a1[1] == b0[1] == b1[1]:
                        ol = (min(max(a0[0], a1[0]), max(b0[0], b1[0])) -
                              max(min(a0[0], a1[0]), min(b0[0], b1[0])))
                        n += ol > 2
                    elif a0[0] == a1[0] == b0[0] == b1[0]:
                        ol = (min(max(a0[1], a1[1]), max(b0[1], b1[1])) -
                              max(min(a0[1], a1[1]), min(b0[1], b1[1])))
                        n += ol > 2
    print(f"Ueberlappungen: {n}" + ("" if n == 0 else "   ACHTUNG"))


def watt_verteilen(teile, ab, root):
    """Demo-Leistungen: nur die speisenden Strecken bekommen einen Startwert,
    alles Weitere folgt der Knotenregel -- was hineinfliesst, kommt heraus.
    Spaeter ersetzt die Sensoranbindung diese Funktion."""
    import random
    zu = {}
    for i, l in enumerate(teile):
        zu.setdefault(tuple(l["pts"][-1]), []).append(i)
    DACH = {55: 2840, 159: 1620, 285: 335, 389: 290,
            515: 1910, 619: 1240, 745: 680, 849: 1465}
    rng = random.Random(7)
    w = [0.0] * len(teile)
    for i, r in enumerate(root):
        if not r:
            continue
        x, y = teile[i]["pts"][0]
        w[i] = (DACH[x] if (y < 140 and x in DACH)
                else 3180 if teile[i]["col"] == "col_feed"
                else rng.choice([210, 430, 760, 1150]))
    gew = {}
    for k, v in ab.items():
        if len(v) > 1:
            g = [rng.uniform(0.6, 1.6) for _ in v]
            gew[k] = [x / sum(g) for x in g]
    for _ in range(len(teile)):
        for kn, ein in zu.items():
            raus = ab.get(kn, [])
            if not raus:
                continue
            su = sum(w[i] for i in ein)
            if su > 0:
                for j, f in zip(raus, gew.get(kn, [1 / len(raus)] * len(raus))):
                    w[j] = su * f
    return [max(50, round(x)) for x in w]


def yaml_bauen(d, w):
    """Kugel-Widgets und Steuerlogik erzeugen."""
    n, lmax = d["n"], d["lmax"]
    A = lambda k: ",".join(str(s[k]) for s in d["segs"])
    I = " " * 14
    dots = [f'{I}- obj: {{ id: fl{i:02d}, x: {l["pts"][0][0]-DOT//2}, y: {l["pts"][0][1]-DOT//2}, '
            f'width: {DOT}, height: {DOT}, radius: CIRCLE, bg_color: ${l["col"]}, bg_opa: COVER, '
            f'border_width: 0, pad_all: 0, hidden: true, scrollable: false }}'
            for i, l in enumerate(d["teile"]) if i not in d["still"]]
    dots += [f'{I}- obj: {{ id: fl{i:02d}b, x: {d["teile"][i]["pts"][0][0]-DOT//2}, '
             f'y: {d["teile"][i]["pts"][0][1]-DOT//2}, width: {DOT}, height: {DOT}, radius: CIRCLE, '
             f'bg_color: ${d["teile"][i]["col"]}, bg_opa: COVER, border_width: 0, pad_all: 0, '
             f'hidden: true, scrollable: false }}' for i in d["slot2"]]
    ref = lambda s: ",\n            ".join(
        ", ".join(f"reinterpret_cast<lv_obj_t *>(id(fl{j:02d}{s}))"
                  if (s == "" and j not in d["still"]) or (s == "b" and j in d["slot2"])
                  else "nullptr" for j in range(i, min(i + 5, n)))
        for i in range(0, n, 5))
    # AC ist der Zaehler der jeweiligen Kugel: acc fuer die Haupt-Kugel, accB
    # fuer die zweite (Regel 6). Ein gemeinsamer Zaehler gaebe die ganze
    # Bewegung der Kugel, die gerade die Schwelle ueberschreitet -- die
    # andere stuende bei 0,25 bis 0,5 px/Tick still.
    schritt = lambda AC: f"""
            float wl = fabsf((float) WATT[i]), umlauf;
            if (wl <= 500.0f) umlauf = 16.0f / powf(fmaxf(wl, 50.0f) / 50.0f, 0.30103f);
            else              umlauf = 8.0f / powf(wl / 500.0f, 0.48945f);
            if (umlauf < 1.0f) umlauf = 1.0f;
            float total = 0;
            for (int s = 0; s < CNT[i]; s++) total += SL[OFF[i] + s];
            umlauf *= powf(total / {lmax}.0f, 0.5f);   // kurze Strecken deutlich schneller
            float sch = total / umlauf * {TICK} / 1000.0f;
            // Langsame Kugeln melden sich seltener: unter 1 px je Tick wird
            // aufsummiert und erst ab 2 px bewegt. Nachgerechnet ueber alle
            // Strecken kostet das im Mittel 6,8 Bewegungen je Tick, also
            // 13,6 von 32 Flaechen -- bei 4 px waeren es 9,8. Die Reserve
            // traegt das, und die langsamen laufen doppelt so glatt.
            // 1,5 px waeren 16,1 Flaechen und damit zu knapp am Deckel.
            // Gestaffelt: sehr langsame Kugeln bewegen sich in 1-px-Schritten,
            // denn sie kommen ohnehin nur alle paar hundert Millisekunden
            // dran. Ab 0,3 px je Tick lohnt die groebere Stufe.
            if (sch < 1.0f) {{
              float grenze = (sch < 0.30f) ? 1.0f : 2.0f;
              {AC}[i] += sch;
              if ({AC}[i] < grenze) continue;              // noch nicht genug
              if (bewegt >= {MAXMOVE}) continue;          // Deckel: {AC} BLEIBT stehen
              // Nicht mehr als eine Stufe auf einmal: sonst sammelt der
              // Zaehler waehrend einer Drosselung weiter an und die Kugel
              // springt danach ueber mehrere Pixel.
              if ({AC}[i] > grenze) {AC}[i] = grenze;
              sch = {AC}[i]; {AC}[i] = 0;
            }} else if (bewegt >= {MAXMOVE}) {{
              {AC}[i] += sch;                              // Zeit merken statt verlieren
              continue;
            }}
            // Schnelle Kugeln laufen mit kleinen Schritten, dafuer bei jedem
            // Tick -- fluessiger als grosse Spruenge. Der Deckel bleibt bei
            // der Kugelgroesse, damit die Spur nicht reisst.
            if (sch > {DOT}.0f) sch = {DOT}.0f;"""
    lauf = lambda P, AC, LV, LX, LY, D, rz: f"""{schritt(AC)}
            {P}[i] += sch + {AC}[i];
            {AC}[i] = 0;
            if ({P}[i] >= total) {{
              {P}[i] = 0; {LV}[i] = {'ROOT[i]' if rz else 'false'};
              for (int s = 0; s < SCNT[i]; s++) {{
                int t = SUCC[SOFF[i] + s];
                if (!live[t]) live[t] = true;
                else if (dotsB[t] && !liveB[t]) {{ liveB[t] = true; posB[t] = 0; }}
              }}
              if (!{LV}[i]) {{ lv_obj_add_flag({D}[i], LV_OBJ_FLAG_HIDDEN); continue; }}
            }}
            float rest = {P}[i];
            int16_t px = SX[OFF[i]], py = SY[OFF[i]];
            for (int s = 0; s < CNT[i]; s++) {{
              int k = OFF[i] + s;
              if (rest <= SL[k] || s == CNT[i] - 1) {{
                float f = SL[k] ? rest / SL[k] : 0;
                if (f > 1) f = 1;
                px = SX[k] + (EX[k] - SX[k]) * f;
                py = SY[k] + (EY[k] - SY[k]) * f;
                break;
              }}
              rest -= SL[k];
            }}
            lv_obj_remove_flag({D}[i], LV_OBJ_FLAG_HIDDEN);
            if (px != {LX}[i] || py != {LY}[i]) {{
              lv_obj_set_pos({D}[i], px - {DOT//2}, py - {DOT//2});
              {LX}[i] = px; {LY}[i] = py; bewegt++;
            }}"""
    startticks = 3000 // TICK   # rund 3 s Anlauf
    logik = f'''interval:
  {MARKER} -- erzeugt von tools/flow_animation.py, nicht von Hand aendern
  - interval: {TICK}ms
    then:
      - lambda: |-
          static const int16_t  SX[] = {{{A(0)}}};
          static const int16_t  SY[] = {{{A(1)}}};
          static const int16_t  EX[] = {{{A(2)}}};
          static const int16_t  EY[] = {{{A(3)}}};
          static const uint16_t SL[] = {{{A(4)}}};
          static const uint16_t OFF[] = {{{",".join(map(str, d["offs"]))}}};
          static const uint8_t  CNT[] = {{{",".join(map(str, d["cnt"]))}}};
          static const uint8_t  SUCC[] = {{{",".join(map(str, d["sf"])) or "0"}}};
          static const uint16_t SOFF[] = {{{",".join(map(str, d["so"]))}}};
          static const uint8_t  SCNT[] = {{{",".join(map(str, d["sc"]))}}};
          static const bool     ROOT[] = {{{",".join("true" if r else "false" for r in d["root"])}}};
          // Leistung je Strecke in W, hier binden spaeter die Sensoren an.
          // Die Kugel laeuft in Zeichenrichtung, ihr Tempo folgt dem Betrag;
          // 0 blendet sie aus, die Strecke loest dann auch nichts aus. Das
          // VORZEICHEN wertet die Logik noch nicht aus -- eine Umkehr braucht
          // die Topologie rueckwaerts und kommt mit der Sensoranbindung.
          // Bis dahin laufen die Demo-Leistungen aus der Knotenregel nur auf
          // der host-Plattform (Simulator, Screenshots). Auf dem Panel steht
          // alles auf 0: keine erfundenen Fluesse.
          #ifdef USE_HOST
          static const int32_t  WATT[] = {{{",".join(map(str, w))}}};
          #else
          static const int32_t  WATT[{n}] = {{0}};
          #endif
          static float   pos[{n}] = {{0}}, posB[{n}] = {{0}}, acc[{n}] = {{0}}, accB[{n}] = {{0}};
          static bool    live[{n}] = {{false}}, liveB[{n}] = {{false}};
          static int16_t lx[{n}], ly[{n}], lxB[{n}], lyB[{n}];
          static bool    init = false;
          static uint8_t next = 0;
          lv_obj_t *const dots[{n}] = {{
            {ref("")} }};
          lv_obj_t *const dotsB[{n}] = {{
            {ref("b")} }};
          // Anlauf abwarten: Das Intervall laeuft ab dem ersten Tick, LVGL
          // baut seine Objekte aber erst auf. Ein Zugriff darauf endet in
          // einem Load access fault (get_prop_core) und damit im Rollback.
          static uint16_t anlauf = 0;
          if (anlauf < {startticks}) {{ anlauf++; return; }}
          if (!init) {{ init = true; for (int i = 0; i < {n}; i++) live[i] = ROOT[i]; }}
          int bewegt = 0;
          for (int q = 0; q < {n}; q++) {{
            int i = (next + q) % {n};
            // Verteilstrecken haben keine Kugel (nullptr) und loesen nichts
            // aus; ihre Abgaenge laufen als ROOT endlos (Regel 4 und 5).
            if (!dots[i] || !live[i] || WATT[i] == 0) {{ if (dots[i]) lv_obj_add_flag(dots[i], LV_OBJ_FLAG_HIDDEN); continue; }}
{lauf("pos", "acc", "live", "lx", "ly", "dots", True)}
          }}
          for (int i = 0; i < {n}; i++) {{
            if (!dotsB[i]) continue;
            if (!liveB[i] || WATT[i] == 0) {{ lv_obj_add_flag(dotsB[i], LV_OBJ_FLAG_HIDDEN); continue; }}{lauf("posB", "accB", "liveB", "lxB", "lyB", "dotsB", False)}
          }}
          next = (next + bewegt + 1) % {n};
  # <<< flow-animation
'''
    return "\n".join(dots), logik


# Eine vom Werkzeug erzeugte Kugel-Zeile (IDs flNN und flNNb, siehe yaml_bauen)
KUGEL = re.compile(r"^ {14}- obj: \{ id: fl\d{2}b?, x: -?\d+, y: -?\d+, width: \d+, "
                   r"height: \d+, radius: CIRCLE, .*hidden: true, scrollable: false \}\n", re.M)


def einbauen(text, dots, logik):
    """Kugeln und Steuerlogik einsetzen. Vorhandene Kugeln und der Block
    zwischen den Markern werden ERSETZT, nicht verdoppelt -- ein zweiter
    Lauf aendert nichts."""
    text = KUGEL.sub("", text)
    stelle = text.index("\n", text.index("            widgets:", text.index("id: schema_area")))
    text = text[:stelle + 1] + dots + "\n" + text[stelle + 1:]
    if MARKER in text:
        a = text.find("interval:\n  " + MARKER)
        if a < 0:   # alte Markerzeile mit doppeltem "#" (bis 09/2026)
            a = text.index("interval:\n  # " + MARKER)
        b = text.index("# <<< flow-animation", a) + len("# <<< flow-animation\n")
        return text[:a] + logik + text[b:]
    return text.rstrip() + "\n\n" + logik


if __name__ == "__main__":
    text = UI.read_text(encoding="utf-8")
    lines = leitungen_lesen(text)
    print(f"{len(lines)} Leitungen im Schema gefunden\n")
    d = erzeugen(lines)
    bericht(d)
    dots, logik = yaml_bauen(d, watt_verteilen(d["teile"], d["ab"], d["root"]))
    neu = einbauen(text, dots, logik)
    if neu == text:
        print("\nDie Animation in der Datei ist aktuell -- nichts zu schreiben")
    elif "--write" not in sys.argv:
        print("\n(Vorschau -- die Datei weicht ab, mit --write wird die Animation eingebaut)")
    else:
        UI.write_text(neu, encoding="utf-8")
        print(f"\n{UI.name} geschrieben: {len(dots.splitlines())} Kugeln, "
              "Block zwischen den Markern ersetzt")
