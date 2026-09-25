#!/usr/bin/env python3
"""
Erzeugt die Flussanimation fuer das Anlagenschema in
.pv-dashboard_page_overview.yaml (Seite 1, Paket von .pv-dashboard_ui.yaml).

    python3 tools/flow_animation.py            # Vorschau, schreibt nichts
    python3 tools/flow_animation.py --write    # baut die Animation ein

Das Skript liest die Leitungen aus der Seitendatei, leitet die Topologie aus den
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

9. LEISTUNG KOMMT AUS KANAELEN (seit 25.09.2026).
   Die Leistung je Strecke steht nicht mehr fest im Block, sondern in dem
   global flow_ch (std::array<float, len(KANAELE)>, Uebersichtsseite). Die
   Skripte ov_* der Uebersicht schreiben hinein, der Block liest je Tick.
   Welche Strecke welchen Kanal zeigt, leitet kanal() aus der Geometrie
   ab: Anfang und Ende der Strecke liegen in einem Geraetekasten oder frei
   (Knoten). Die Kaesten liest kaesten_lesen() aus derselben Datei; ihr
   Name ist die ID des Wert-Labels darin (v_roof_1, v_wr_full, e_batt ...).
   Vorzeichen: positiv = in Zeichenrichtung. Negativ laeuft die Kugel
   rueckwaerts, endlos und ohne etwas auszuloesen (Speicher entlaedt,
   Netzbezug). Unter 10 W steht die Kugel.

10. FEHLENDE GERAETE (Referenz-Entitaeten, dev_present).
   Jede Leitung bekommt die ID lnNN und eine Sichtbarkeitsregel aus der
   Geometrie: Sie ist sichtbar, wenn (a) jedes Geraet, dessen Kasten sie
   beruehrt, vorhanden ist und (b) hinter ihr noch etwas Vorhandenes haengt.
   "Hinter ihr" heisst: Nimmt man die Leitung heraus, faellt ein Teil des
   Schemas vom Hausanschluss (v_grid) ab; mindestens ein Geraet dieses Teils
   muss vorhanden sein. Haengt dort etwas, das es immer gibt (Hausnetz,
   Sonstige), oder faellt nichts ab (Masche), gilt nur (a). Der Block
   vergleicht dev_present je Tick mit dem letzten Stand und blendet
   Leitungen und ihre Kugeln um; eine versteckte Strecke bekommt 0 W.
------------------------------------------------------------------------------
"""
import re
import sys
from pathlib import Path

UI = Path(__file__).resolve().parent.parent / ".pv-dashboard_page_overview.yaml"
TICK = 20          # ms -- nah am LVGL-Refresh (16 ms), damit schnelle
                   # Kugeln oft drankommen; langsame melden sich seltener
DOT = 8            # Kugeldurchmesser in px
MAXMOVE = 13       # Bewegungen je Tick -> 26 von 32 Flaechen. Die restlichen
                   #  6 reichen dem Dashboard: Uhr und Messwerte aendern sich
                   # im Minutentakt, die Stundenbalken nur bei neuen Daten
MARKER = "# >>> flow-animation"
TOL = 6            # px: so weit darf ein Leitungsende neben einem Kasten
                   # liegen und gehoert noch dazu (die Dachleitungen
                   # beginnen 5 px unter dem Dachkasten)
MINWATT = 10       # darunter steht die Kugel (Messrauschen)

# Geraeteplaetze = Bits in dev_present, in dieser Reihenfolge. Dieselbe
# Tabelle steht in .pv-dashboard_ui.yaml (dev_present) und in
# tools/ha_bindings.py (PLAETZE, REFERENZ) -- alle drei gleich halten.
SLOTS = ([f"pv_{i}" for i in range(1, 9)] + [f"inv_{i}" for i in range(1, 5)] +
         ["bat_1", "bat_2", "bat_3", "wb_1", "wb_2", "heatpump", "meter_pv", "meter_house"])
BIT = {s: 1 << i for i, s in enumerate(SLOTS)}
BAT_ALL = BIT["bat_1"] | BIT["bat_2"] | BIT["bat_3"]

# Kasten (ID seines Wert-Labels) -> Geraeteplatz. "immer" = gibt es in
# jeder Anlage, "speicher" = Summenkasten, da sobald ein Speicher da ist.
KASTEN = {**{f"v_roof_{i}": f"pv_{i}" for i in range(1, 9)},
          "v_wr_full": "inv_1", "v_wr_mini": "inv_2",
          "v_wr_hybrid1": "inv_3", "v_wr_hybrid2": "inv_4",
          "v_bat1": "bat_1", "v_bat2": "bat_2", "v_bat3": "bat_3",
          "e_batt": "speicher", "v_heatpump": "heatpump", "v_wb1": "wb_1",
          "v_wb2": "wb_2", "v_meter_pv": "meter_pv", "v_meter_house": "meter_house",
          "v_house": "immer", "v_misc": "immer", "v_grid": "immer"}
WURZEL = "v_grid"  # Hausanschluss: von hier aus zaehlt "dahinter"

# Kanaele in flow_ch, in dieser Reihenfolge. Vorzeichen: positiv in
# Zeichenrichtung (Erzeugung zum Wechselrichter, Speicher laden, Verbrauch,
# Einspeisung Richtung Netz).
KANAELE = ([f"pv_{i}" for i in range(1, 9)] + [f"inv_{i}" for i in range(1, 5)] +
           ["batt", "bat_1", "bat_2", "bat_3", "home", "heatpump", "misc", "wb_1", "wb_2",
            "meter_pv", "meter_house", "grid"])
VERBRAUCHER = {"v_heatpump": "heatpump", "v_misc": "misc", "v_wb1": "wb_1", "v_wb2": "wb_2"}

# Demo-Leistungen je Kanal, nur host (Simulator), und nur solange niemand
# flow_ch beschrieben hat. Der Screenshot-Lauf setzt eigene Werte.
DEMO = {"pv_1": 2840, "pv_2": 1620, "pv_3": 335, "pv_4": 290, "pv_5": 1910, "pv_6": 1240,
        "pv_7": 680, "pv_8": 1465, "inv_1": 4460, "inv_2": 625, "inv_3": 3150, "inv_4": 2145,
        "batt": 760, "bat_1": 300, "bat_2": 250, "bat_3": 210, "home": 1790,
        "heatpump": 430, "misc": 210, "wb_1": 1150, "wb_2": 0,
        "meter_pv": 4460, "meter_house": 3180, "grid": 7640}


def leitungen_lesen(text):
    block = text[text.index("id: schema_area"):]
    return [
        {"pts": [[int(x), int(y)] for x, y in re.findall(r"\[(\d+),(\d+)\]", m.group(1))],
         "col": m.group(2)}
        for m in re.finditer(
            r"- line: \{ (?:id: \w+, )?points: \[((?:\[\d+,\d+\],?)+)\], line_color: \$(\w+)", block)
    ]


def kaesten_lesen(text):
    """Geraetekaesten im Schema: jedes Widget der obersten Ebene von
    schema_area mit Lage und Groesse in der ersten Zeile und einem Wert-Label
    (v_..., e_batt) darin. Name = ID dieses Labels."""
    block = text[text.index("id: schema_area"):text.index("\ninterval:")]
    starts = [m.start() for m in re.finditer(r"^ {14}- \w+: ", block, re.M)] + [len(block)]
    boxes = {}
    for a, b in zip(starts, starts[1:]):
        chunk = block[a:b]
        erste = chunk.split("\n", 1)[0]
        g = re.search(r"\bx: (\d+), y: (\d+), width: (\d+), height: (\d+)", erste)
        name = re.search(r"\bid: ((?:v|e)_\w+)", chunk)
        if not (g and name and erste.lstrip().startswith("- obj:")):
            continue
        x, y, w, h = map(int, g.groups())
        if name.group(1) not in KASTEN:
            sys.exit(f"Kasten {name.group(1)} fehlt in KASTEN -- Tabelle ergaenzen")
        boxes[name.group(1)] = (x, y, x + w, y + h)
    return boxes


def kasten_bei(p, boxes):
    x, y = p
    treffer = [n for n, (x0, y0, x1, y1) in boxes.items()
               if x0 - TOL <= x <= x1 + TOL and y0 - TOL <= y <= y1 + TOL]
    if len(treffer) > 1:
        sys.exit(f"Punkt {p} liegt an zwei Kaesten {treffer} -- TOL zu gross")
    return treffer[0] if treffer else None


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
    for li, l in enumerate(lines):
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
            teile.append({"pts": [list(x) for x in p], "col": l["col"], "src": li})
            continue
        start = 0
        for c in idx + [len(p) - 1]:
            if c > start:
                teile.append({"pts": [list(x) for x in p[start:c + 1]], "col": l["col"], "src": li})
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


def kanal(teil, boxes, still):
    """Regel 9: welchen Kanal eine Strecke zeigt, aus den Kaesten an ihrem
    Anfang (a) und Ende (e). Die erste passende Zeile gewinnt."""
    if still:
        return None                                    # Verteilstrecke, keine Kugel
    a = kasten_bei(teil["pts"][0], boxes)
    e = kasten_bei(teil["pts"][-1], boxes)
    ka, ke = KASTEN.get(a), KASTEN.get(e)
    if ke and ke.startswith("bat_"):
        return ke                                      # Schiene -> Speicher n
    if "speicher" in (ka, ke):
        return "batt"                                  # zum / vom Summenkasten
    if "v_house" in (a, e):
        return "home"                                  # ins Hausnetz / zur Schiene
    if e in VERBRAUCHER:
        return VERBRAUCHER[e]                          # Abgang zum Verbraucher
    if ka and ka.startswith("pv_"):
        return ka                                      # Dach -> Knoten
    if ke and ke.startswith("inv_") and a is None:
        return ke                                      # Knoten -> Wechselrichter
    if ke == "meter_house" or ka in ("meter_pv", "meter_house"):
        return ke if ke == "meter_house" else ka       # Zaehler Richtung Netz
    if ka and ka.startswith("inv_"):
        return ka                                      # Wechselrichter weiter
    if a == WURZEL:
        return "grid"                                  # Hausanschluss -> Netz
    sys.exit(f"Strecke {teil['pts']} passt auf keine Kanalregel ({a} -> {e})")


def sichtbarkeit(lines, boxes):
    """Regel 10: je Leitung drei Masken fuer dev_present.
    alle  jedes dieser Bits muss gesetzt sein (beruehrte Kaesten)
    a, b  0 = keine Bedingung, sonst mindestens ein Bit gesetzt
          (a: was hinter der Leitung haengt, b: Summenkasten Speicher)"""
    def knoten(p):
        return kasten_bei(p, boxes) or tuple(p)

    enden = {tuple(p) for l in lines for p in (l["pts"][0], l["pts"][-1])}
    mengen = []
    for l in lines:
        m = {knoten(l["pts"][0]), knoten(l["pts"][-1])}
        # Knoten, die mitten auf der Leitung liegen, gehoeren auch dazu
        for k in range(len(l["pts"]) - 1):
            m |= {knoten(p) for p in enden if auf_strecke(p, l["pts"][k], l["pts"][k + 1])}
        mengen.append(m)

    def bit(n):
        s = KASTEN.get(n) if isinstance(n, str) else None
        return BAT_ALL if s == "speicher" else BIT.get(s, 0)

    out = []
    for i, m in enumerate(mengen):
        # Zusammenhang ohne Leitung i (Union-Find ueber die Knoten)
        eltern = {}

        def wurzel(x):
            while eltern.get(x, x) != x:
                x = eltern[x]
            return x
        for j, mm in enumerate(mengen):
            if j == i:
                continue
            mm = list(mm)
            for x in mm[1:]:
                ra, rb = wurzel(mm[0]), wurzel(x)
                if ra != rb:
                    eltern[ra] = rb
        alle_knoten = set().union(*mengen)
        ab = {wurzel(n) for n in m if wurzel(n) != wurzel(WURZEL)}
        hinter = [n for n in alle_knoten if wurzel(n) in ab]
        if any(KASTEN.get(n) == "immer" for n in hinter if isinstance(n, str)):
            a = 0
        else:
            a = 0
            for n in hinter:
                a |= bit(n)
        alle = 0
        b = 0
        for n in m:
            if isinstance(n, str):
                if KASTEN[n] == "speicher":
                    b = BAT_ALL
                else:
                    alle |= BIT.get(KASTEN[n], 0)
        out.append((alle, a, b))
    return out


def maske_text(v):
    return "+".join(s for s in SLOTS if v & BIT[s]) or "-"


def laenge(pts):
    return sum(abs(pts[k + 1][0] - pts[k][0]) + abs(pts[k + 1][1] - pts[k][1])
               for k in range(len(pts) - 1))


def erzeugen(lines, boxes):
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
    ch = [kanal(l, boxes, i in still) for i, l in enumerate(teile)]
    sicht = sichtbarkeit(lines, boxes)
    return dict(teile=teile, succ=succ, still=still, ab=ab, root=root, slot2=slot2,
                segs=segs, offs=offs, cnt=cnt, sf=sf, so=so, sc=sc, lmax=lmax, n=n,
                ch=ch, sicht=sicht, nl=len(lines), lines=lines)


def bericht(d):
    print(f"{d['n']} Teilstrecken, {sum(d['sc'])} Uebergaenge")
    print(f"{len(d['still'])} Verteilstrecken schweigen (Regel 4)")
    print(f"{sum(d['root'])} laufen endlos, {d['n'] - sum(d['root'])} werden ausgeloest (Regel 5)")
    print(f"{len(d['slot2'])} Strecken mit zweiter Kugel (Regel 6)")
    print(f"laengste Strecke {d['lmax']} px, Laengenfaktor bezieht sich darauf (Regel 7)")
    print(f"Deckel {MAXMOVE} Bewegungen/Tick = {MAXMOVE * 2} von 32 Flaechen (Regel 8)")
    print(f"{len(KANAELE)} Kanaele in flow_ch, {sum(c is not None for c in d['ch'])} Strecken zeigen einen (Regel 9)")
    print(f"{d['nl']} Leitungen mit Sichtbarkeitsregel (Regel 10)")
    if "-v" in sys.argv:
        print("\nStrecke  Leitung  Kanal        von -> nach")
        for i, l in enumerate(d["teile"]):
            print(f"  {i:2d}      ln{l['src']:02d}     {d['ch'][i] or '(verteilt)':12s} {l['pts'][0]} -> {l['pts'][-1]}")
        print("\nLeitung  alle vorhanden        eines davon (dahinter)             Speicher")
        for k, (al, a, b) in enumerate(d["sicht"]):
            print(f"  ln{k:02d}   {maske_text(al):22s} {maske_text(a):34s} {'ja' if b else '-'}")
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


def yaml_bauen(d):
    """Kugel-Widgets und Steuerlogik erzeugen."""
    n, lmax, nl = d["n"], d["lmax"], d["nl"]
    if nl > 64:
        sys.exit("mehr als 64 Leitungen -- die Maske im Block ist ein uint64_t")
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
    lref = ",\n            ".join(
        ", ".join(f"id(ln{j:02d})->obj" for j in range(i, min(i + 5, nl)))
        for i in range(0, nl, 5))
    ch = ",".join(str(KANAELE.index(c)) if c else "-1" for c in d["ch"])
    lnof = ",".join(str(l["src"]) for l in d["teile"])
    m_all = ",".join(f"0x{s[0]:X}" for s in d["sicht"])
    m_a = ",".join(f"0x{s[1]:X}" for s in d["sicht"])
    m_b = ",".join(f"0x{s[2]:X}" for s in d["sicht"])
    demo = ", ".join(f"{DEMO[k]}" for k in KANAELE)
    kan_doc = "\n".join(
        "          //   " + "  ".join(f"{j:2d} {KANAELE[j]:<11s}" for j in range(i, min(i + 4, len(KANAELE))))
        for i in range(0, len(KANAELE), 4))
    # AC ist der Zaehler der jeweiligen Kugel: acc fuer die Haupt-Kugel, accB
    # fuer die zweite (Regel 6). Ein gemeinsamer Zaehler gaebe die ganze
    # Bewegung der Kugel, die gerade die Schwelle ueberschreitet -- die
    # andere stuende bei 0,25 bis 0,5 px/Tick still.
    schritt = lambda AC: f"""
            float wl = fabsf(WATT[i]), umlauf;
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
    # Haupt-Kugel: rueckwaerts (rev) laeuft sie endlos und loest nichts
    # aus; die zweite Kugel (B) laeuft nur vorwaerts.
    lauf = lambda P, AC, LV, LX, LY, D, haupt: f"""{schritt(AC)}
            {P}[i] += sch + {AC}[i];
            {AC}[i] = 0;
            if ({P}[i] >= total) {{
              {P}[i] = 0; {LV}[i] = {'rev || ROOT[i]' if haupt else 'false'};
              {'if (!rev) ' if haupt else ''}for (int s = 0; s < SCNT[i]; s++) {{
                int t = SUCC[SOFF[i] + s];
                if (!live[t]) live[t] = true;
                else if (dotsB[t] && !liveB[t]) {{ liveB[t] = true; posB[t] = 0; }}
              }}
              if (!{LV}[i]) {{ lv_obj_add_flag({D}[i], LV_OBJ_FLAG_HIDDEN); continue; }}
            }}
            float rest = {'rev ? total - pos[i] : pos[i]' if haupt else P + '[i]'};
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
          // Kanal in flow_ch je Strecke (-1 = Verteilstrecke ohne Kugel) und
          // die Leitung lnNN, aus der die Strecke stammt. flow_ch fuellen die
          // Skripte ov_* der Uebersicht, in W, positiv in Zeichenrichtung:
{kan_doc}
          static const int8_t   CH[] = {{{ch}}};
          static const uint8_t  LN[] = {{{lnof}}};
          // Sichtbarkeit je Leitung gegen dev_present (Bits wie dort):
          // alle Bits aus L_ALL gesetzt und, wo nicht 0, je eines aus L_A
          // (dahinter) und L_B (Summenkasten Speicher).
          static const uint32_t L_ALL[] = {{{m_all}}};
          static const uint32_t L_A[] = {{{m_a}}};
          static const uint32_t L_B[] = {{{m_b}}};
          static_assert(sizeof(id(flow_ch)) == {len(KANAELE)} * sizeof(float), "flow_ch passt nicht zu KANAELE in tools/flow_animation.py");
          static float   pos[{n}] = {{0}}, posB[{n}] = {{0}}, acc[{n}] = {{0}}, accB[{n}] = {{0}};
          static bool    live[{n}] = {{false}}, liveB[{n}] = {{false}};
          static int16_t lx[{n}], ly[{n}], lxB[{n}], lyB[{n}];
          static bool    init = false;
          static uint8_t next = 0;
          static uint32_t gesehen = 0xFFFFFFFFu;
          static uint64_t lvis = ~0ULL;
          lv_obj_t *const dots[{n}] = {{
            {ref("")} }};
          lv_obj_t *const dotsB[{n}] = {{
            {ref("b")} }};
          // Anlauf abwarten: Das Intervall laeuft ab dem ersten Tick, LVGL
          // baut seine Objekte aber erst auf. Ein Zugriff darauf endet in
          // einem Load access fault (get_prop_core) und damit im Rollback.
          static uint16_t anlauf = 0;
          if (anlauf < {startticks}) {{ anlauf++; return; }}
          if (!init) {{
            init = true;
            for (int i = 0; i < {n}; i++) live[i] = ROOT[i];
            // Demo-Leistungen nur auf der host-Plattform (Simulator), und
            // nur solange noch kein Skript flow_ch beschrieben hat. Auf dem
            // Panel bleibt alles 0, bis Werte kommen: keine erfundenen Fluesse.
            #ifdef USE_HOST
            static const float DEMO[] = {{{demo}}};
            bool leer = true;
            for (float v : id(flow_ch)) if (v != 0.0f) leer = false;
            if (leer) for (int k = 0; k < {len(KANAELE)}; k++) id(flow_ch)[k] = DEMO[k];
            #endif
          }}
          // Fehlende Geraete (Referenz): Leitungen um- und ausblenden, sobald
          // sich dev_present aendert. Kostet nur beim Wechsel etwas.
          const uint32_t da = id(dev_present);
          if (da != gesehen) {{
            gesehen = da;
            lv_obj_t *const lines[{nl}] = {{
            {lref} }};
            for (int k = 0; k < {nl}; k++) {{
              const bool v = (da & L_ALL[k]) == L_ALL[k] && (!L_A[k] || (da & L_A[k])) && (!L_B[k] || (da & L_B[k]));
              if (v) {{ lvis |= 1ULL << k; lv_obj_remove_flag(lines[k], LV_OBJ_FLAG_HIDDEN); }}
              else   {{ lvis &= ~(1ULL << k); lv_obj_add_flag(lines[k], LV_OBJ_FLAG_HIDDEN); }}
            }}
          }}
          // Leistung je Strecke aus ihrem Kanal; versteckte Strecken und
          // Werte unter {MINWATT} W zaehlen als 0 (Kugel steht, loest nichts aus).
          float WATT[{n}];
          for (int i = 0; i < {n}; i++) {{
            float w = (CH[i] >= 0 && ((lvis >> LN[i]) & 1ULL)) ? id(flow_ch)[CH[i]] : 0.0f;
            WATT[i] = (std::isfinite(w) && fabsf(w) >= {MINWATT}.0f) ? w : 0.0f;
          }}
          int bewegt = 0;
          for (int q = 0; q < {n}; q++) {{
            int i = (next + q) % {n};
            // Verteilstrecken haben keine Kugel (nullptr) und loesen nichts
            // aus; ihre Abgaenge laufen als ROOT endlos (Regel 4 und 5).
            // Negativ: rueckwaerts, endlos, ohne Ausloesen (Regel 9).
            const bool rev = WATT[i] < 0.0f;
            if (dots[i] && rev) live[i] = true;
            if (!dots[i] || !live[i] || WATT[i] == 0.0f) {{ if (dots[i]) lv_obj_add_flag(dots[i], LV_OBJ_FLAG_HIDDEN); continue; }}
{lauf("pos", "acc", "live", "lx", "ly", "dots", True)}
          }}
          for (int i = 0; i < {n}; i++) {{
            if (!dotsB[i]) continue;
            if (!liveB[i] || WATT[i] <= 0.0f) {{ lv_obj_add_flag(dotsB[i], LV_OBJ_FLAG_HIDDEN); continue; }}{lauf("posB", "accB", "liveB", "lxB", "lyB", "dotsB", False)}
          }}
          next = (next + bewegt + 1) % {n};
  # <<< flow-animation
'''
    return "\n".join(dots), logik


# Eine vom Werkzeug erzeugte Kugel-Zeile (IDs flNN und flNNb, siehe yaml_bauen)
KUGEL = re.compile(r"^ {14}- obj: \{ id: fl\d{2}b?, x: -?\d+, y: -?\d+, width: \d+, "
                   r"height: \d+, radius: CIRCLE, .*hidden: true, scrollable: false \}\n", re.M)
# Eine Leitung im Schema, mit oder ohne ID
LEITUNG = re.compile(r"(- line: \{ )(?:id: \w+, )?(points: )")


def einbauen(text, dots, logik):
    """Kugeln, Leitungs-IDs und Steuerlogik einsetzen. Vorhandene Kugeln
    und der Block zwischen den Markern werden ERSETZT, nicht verdoppelt --
    ein zweiter Lauf aendert nichts."""
    text = KUGEL.sub("", text)
    a = text.index("id: schema_area")
    b = text.find("\ninterval:", a)
    zaehler = iter(range(1000))
    schema = LEITUNG.sub(lambda m: f"{m.group(1)}id: ln{next(zaehler):02d}, {m.group(2)}", text[a:b])
    text = text[:a] + schema + text[b:]
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
    boxes = kaesten_lesen(text)
    print(f"{len(lines)} Leitungen und {len(boxes)} Geraetekaesten im Schema gefunden\n")
    d = erzeugen(lines, boxes)
    bericht(d)
    dots, logik = yaml_bauen(d)
    neu = einbauen(text, dots, logik)
    if neu.count("%%"):
        sys.exit("'%%' im erzeugten Text (docs/04, Punkt 8)")
    if neu == text:
        print("\nDie Animation in der Datei ist aktuell -- nichts zu schreiben")
    elif "--write" not in sys.argv:
        print("\n(Vorschau -- die Datei weicht ab, mit --write wird die Animation eingebaut)")
    else:
        UI.write_text(neu, encoding="utf-8")
        print(f"\n{UI.name} geschrieben: {len(dots.splitlines())} Kugeln, {len(lines)} Leitungs-IDs, "
              "Block zwischen den Markern ersetzt")
