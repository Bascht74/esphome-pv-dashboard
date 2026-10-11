#!/usr/bin/env python3
"""Ende-zu-Ende-Probe des Datenwegs: Panel (host) gegen ein nachgebautes
Home Assistant.

    ~/.venvs/esphome-beta/bin/python tests/ha_probe.py            # bauen + pruefen
    ~/.venvs/esphome-beta/bin/python tests/ha_probe.py --no-build # nur pruefen
    ~/.venvs/esphome-beta/bin/python tests/ha_probe.py --shots    # dazu Bilder

Ablauf: tests/ha-test.yaml bauen (Simulator + .pv-dashboard_ha.yaml + api
ohne Schluessel), das Programm ohne Fenster starten, mit aioesphomeapi als
Home Assistant anmelden. Die Zustaende kommen aus der Tabelle von
tools/ha_bindings.py (Demo-Werte unter den Standard-IDs), die Aktionen
(Wetter, Statistik) beantwortet ein Jinja-Nachbau der Antwortvorlagen; die
Solcast-Aktion scheitert absichtlich (Ersatzweg ueber das Attribut). Was das
Panel zeigt, liest die Probe aus den Zeilen "PROBE {json}" des Programms.

Faelle (Wunsch des Nutzers, 25.09.2026: Referenz weg -> Grafik weg, andere
Entitaet weg -> nur der Wert weg):
  A  vor dem Verbinden bzw. vor ha_ready: fehlender Wert zeigt Striche
  B  Referenz nicht belegt (none) und Referenz fehlt in HA -> Geraet weg
  C  Referenz meldet unavailable -> Geraet weg
  D  Nicht-Referenz unavailable / nicht belegt (FALSE) / fehlt -> nur Wert leer
  E  Referenz bekommt einen Wert -> Geraet wieder da
  F  Referenz faellt zur Laufzeit aus, Nicht-Referenz ebenso
  G  Prognosen und Statistik fuellen die Seiten
  I  leerer Wert in einer Summe (Waermepumpe, Wallbox 1) -> Summe leer
  H  Trennung von HA -> genau eine Sammelmeldung; Verbinden -> sie ist weg
  K  Modus-Schalter Wallbox (Wunsch des Nutzers, 25.09.2026): Tipp (probe_tap,
     LV_EVENT_CLICKED wie ein Finger) -> Teil leuchtet sofort, bleibt bis
     evcc meldet, select.select_option mit Entitaet und Option nach dem
     Attribut options (off/pv/minpv/now bzw. off/smart/now); Fehler oder
     10 s ohne Meldung -> gemeldeter Modus; Wallbox fehlt -> kein Befehl
  L  Faktor je Zahlenwert (Wunsch des Nutzers, 09.10.2026, ha-test.yaml):
     -1 dreht das Vorzeichen (Hauszaehler, Strom Speicher 1), 0.001 macht
     W -> kW (Wallbox 1, die Probe schickt W); unavailable bleibt mit -1
     leer (NAN * -1 = NAN, val_leer erst hinter dem Filter)
  M  Texte der Waermepumpe (Wunsch des Nutzers, 10.10.2026): Rohwerte aus HA
     werden uebersetzt (Jahreszeit on/off -> Sommer/Winter, Bypass on/off
     -> offen/zu, Kompressor englisch -> deutsch), deutsche Formen der Demo
     bleiben sinnvoll, Unbekanntes kommt unveraendert durch
  N  Einspeisegrenze ohne Entitaet (ha_rule_limit none, ha-test.yaml): aus
     feed_limit_pct der Anlage, 60 -> "60 % aktiv"
  O  Tageswerte aus der Statistik (ha-test.yaml, ha_<ziel>: statistik):
     Flaeche 1 aus dem Mittel ihrer Leistung (Stunden + 5 min), Wasch-
     maschine aus ha_dev2_energy_total, Einspeisung heute aus meter1_total
     (change); die Probe rechnet aus ihren eigenen Antworten nach
  P  Summen ohne Entitaet: Erzeugung heute = Summe der Wechselrichter
     (Wert aendert sich mit, unavailable -> leer), Eigenverbrauch = WR 2..4
     - Ueberschuss (docs/01) in "Gespart"
  Q  Stoerung aus dem Statustext (ha_inv3_fault none, inv_fault_hold_s 4):
     "FAULT" -> Meldung und roter Text, "Normal" -> haelt 4 s, dann weg;
     Schleife Fault <-> Normal innerhalb der Haltezeit -> eine Meldung,
     Anzahl 1; "Standby" -> keine
  R  Prognose je Dach (Wunsch des Nutzers, 10.10.2026, ha-test.yaml): eine
     Aktion liest Zustand, estimate10 und detailedForecast (Format wie die
     echte Solcast-Integration: period_start als datetime) von
     ha_pv<N>_fc_d1..7 -> Kacheln nur fuer Flaechen mit Wert heute, Titel
     "bisher / Prognose kWh", Stundenbalken aus der Statistik, Tipp auf
     Vorschau -> "6 Tage" mit der Summe der Folgetage; forecast_curve aus
     der Summe der Daecher
  J  in keinem Label irgendwo "inf" oder "nan", ueber den ganzen Lauf
  S  Ruhiger Start (Wunsch des Nutzers, 10.10.2026): nach dem Start und vor
     dem ersten Wert aus HA ist im Schema nichts zu sehen -- kein Kasten,
     keine Leitung, keine Kugel, auch nicht nach dem Anlauf der Animation;
     mit den Referenzen erscheinen Geraete, Hausanschluss und Leitungen
  T  Datenalter (11.10.2026, data_stale_s 15 in ha-test.yaml): HA schickt
     nur Aenderungen; Quellen bleiben ueber der Grenze, solange HA verbunden
     ist, kommt trotzdem keine Meldung "Keine Daten von ..."
  U  Wallbox ohne Fahrzeug (11.10.2026): Name "Kein Fahrzeug" einmal,
     Statuszeile leer, Ladestand, Limit und Plan auf Strichen; Fahrzeugname
     "db:21" (evcc intern) -> "Fahrzeug"
  V  Wetter (11.10.2026): ohne Sonnenscheindauer in der Tagesvorhersage
     faellt die Zeile Sonne weg (Wind auf y 232, Trennlinien 224 hoch);
     Warnstufe 0 -> "Keine Warnung des DWD", unavailable -> "DWD-Warnungen
     nicht verfuegbar" (nicht belegt -> "... nicht eingerichtet", nur im
     Geraet, Compile-Zeit)
  W  Rest heute (Entscheidung des Nutzers, 11.10.2026): eine Rechnung, P50
     der Halbstunden ab jetzt, die laufende anteilig (die Probe rechnet aus
     ihren eigenen Halbstunden nach). Seite PV = Kopfzeile der Seite
     Prognose, alle Daecher. Statusleiste und Haus: ohne Prognose je Dach
     fuer die vorhandenen Flaechen 3..8 die Solcast-Entitaet; nach dem
     Wiederverbinden (H) hat Flaeche 5 eine Prognose, 3, 4, 6, 7 fallen aus
     -> "Restprognose Haus" aus Flaeche 5; 6 kommt ohne Prognose zurueck ->
     wieder die Entitaet. Halbstunden von gestern (probe_p50_day) zaehlen
     nicht: Seite PV und Kopfzeile "--,-", Statusleiste und Haus mit der
     Entitaet, bis ein Abruf heute stempelt; scheitert danach nur der
     Abruf je Dach, bleibt es dabei (eigener Stempel je Reihe). Ein Tageswert ohne Halbstunden
     (Flaeche 3) -> Entitaet. Ohne jede Prognose je Dach rechnet die Seite
     PV aus den Halbstunden der ganzen Anlage.
  X  Autarkie heute (Entscheidung des Nutzers, 11.10.2026): (Verbrauch -
     Bezug) / Verbrauch mit dem ganzen Verbrauch (ha_total_energy_today),
     die Kachel Verbrauch bleibt ha_home_energy_today; Gesamtverbrauch
     unavailable -> Autarkie aus ha_home_energy_today; Bezug ueber dem
     Verbrauch -> 0 %
  Y  Seite Prognose, laufende Stunde live und Hinweise (Entscheidung des
     Nutzers, 11.10.2026): bis zur ersten Antwort des Abrufs je Dach
     "Prognose wird geladen ...", nie Kacheln ohne Ist und ohne Hinweis,
     erst "Ist wird geladen ...", nach dem Tagesabruf kein Hinweis; die
     5-min-Zeilen der laufenden Stunde (Zahl, Ende, Stunde) kommen an, der
     Balken liegt zwischen dem Mittel von HA und der festen Leistung;
     getrennt waechst die eigene Summe nicht; ohne 5-min-Zeilen ist er die
     eigene Leistung; Kachel 1 zeichnet ihn (halb deckend); ein gescheiterter Tagesabruf zeigt "Ist
     unvollstaendig", der naechste gute nimmt es weg, ebenso nach dem
     Wiederverbinden. Dazu die Zeiten Verbinden -> Kacheln -> Ist (Info).

Liest keine secrets.yaml und nicht .pv-dashboard_anlage.yaml. Ergebnis:
Exit-Code 0, wenn alle Faelle bestehen.
"""
import argparse
import ast
import asyncio
import datetime as dt
import json
import logging
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import ha_bindings as hb  # noqa: E402

from aioesphomeapi import APIClient  # noqa: E402
from jinja2 import StrictUndefined  # noqa: E402
from jinja2.sandbox import ImmutableSandboxedEnvironment  # noqa: E402

NAME = "pv-dashboard-test"
PORT = 16063
CONFIG = ROOT / "tests" / "ha-test.yaml"
DATA = ROOT / ".esphome"
PROGRAMM = DATA / "build" / NAME / ".pioenvs" / NAME / "program"
SHOTS = ROOT / "shots" / "ha_probe"
TZ = ZoneInfo("Europe/Berlin")


# --------------------------------------------------------------------------
# Nachgebautes Home Assistant: Jinja wie in HA (Ausschnitt)
# --------------------------------------------------------------------------
def now():
    return dt.datetime.now(TZ)


def as_datetime(v):
    return v if isinstance(v, dt.datetime) else dt.datetime.fromisoformat(v)


def today_at(s="00:00"):
    h, m = map(int, s.split(":"))
    return now().replace(hour=h, minute=m, second=0, microsecond=0)


ATTR = {}
STATE = {}
env = ImmutableSandboxedEnvironment(undefined=StrictUndefined)
env.globals.update(now=now, as_datetime=as_datetime, as_local=lambda d: d.astimezone(TZ), today_at=today_at,
                   timedelta=dt.timedelta, state_attr=lambda e, a: ATTR.get((e, a)),
                   states=lambda e: STATE.get(e, "unknown"))
env.filters["tojson"] = json.dumps


def render(t, **kw):
    return env.from_string(t).render(**kw)


def parse(s):
    try:
        return ast.literal_eval(s)
    except Exception:
        return s


def E(name):
    return hb.NAMEN[name]["ent"]


# Prognose je Dach (Fall R): IDs wie in tests/ha-test.yaml, Tageswerte P50 /
# P10 in kWh nach dem Muster der echten Integration (Stand 10.10.2026)
DACH = {
    "sensor.solcast_test_sued_prognose_": [(6.9432, 3.112), (6.2651, 1.6718), (10.9892, 3.4028), (5.9857, 0.6437),
                                           (7.0262, 1.6951), (11.1401, 3.3985), (7.5508, 1.2128)],
    "sensor.solcast_test_west_prognose_": [(8.1593, 3.6992), (8.4717, 1.9855)],
}
DACH_TAG = ["heute", "morgen"] + [f"tag_{d}" for d in range(3, 8)]
DACH_SPITZE = {"sensor.solcast_test_sued_prognose_": (1.4475, 13.0), "sensor.solcast_test_west_prognose_": (1.7, 15.0)}
# Fall W: Flaeche 5 (Hausnetz-Kreis), Prognose erst nach dem Wiederverbinden
OST = "sensor.solcast_test_ost_prognose_"
DACH_SPITZE[OST] = (1.2, 10.0)


def dach_halbstunden(praefix, tag=0):
    """detailedForecast wie Solcast: 48 Eintraege, period_start als datetime
    in Ortszeit, pv_estimate / pv_estimate10 / pv_estimate90 in kW."""
    spitze, mitte = DACH_SPITZE[praefix]
    t0 = today_at("00:00") + dt.timedelta(days=tag)
    aus = []
    for i in range(48):
        t = i / 2 + 0.25
        p = round(max(0.0, spitze * (1 - ((t - mitte) / 5.5) ** 2)), 4) if 7.5 <= t <= 18.5 else 0.0
        aus.append({"period_start": t0 + dt.timedelta(minutes=30 * i), "pv_estimate": p,
                    "pv_estimate10": round(p * 0.45, 4), "pv_estimate90": round(p * 1.3, 4), "dampening_factor": 1.0})
    return aus


def rest_aus(werte, m):
    """Rest heute wie das Panel (fc_rest) aus 48 Halbstunden P50 in kW: ab
    Minute m, die laufende anteilig."""
    return sum(v * 0.5 * min(1.0, ((i + 1) * 30 - m) / 30) for i, v in enumerate(werte) if (i + 1) * 30 > m)


def rest_soll(praefixe, m):
    """Rest der Daecher; Werte mit drei Stellen wie in der Antwortvorlage."""
    return sum(rest_aus([float("%.3g" % e["pv_estimate"]) for e in dach_halbstunden(x)], m) for x in praefixe)


def rest_passt(ist, praefixe, m, werte=None):
    """Das Panel rechnet jede Minute neu: Minute m oder die eine davor.
    Mit werte (48 Halbstunden der ganzen Anlage) statt der Daecher."""
    soll = (lambda mm: rest_aus(werte, mm)) if werte is not None else (lambda mm: rest_soll(praefixe, mm))
    return ist is not None and m >= 0 and any(abs(ist - soll(mm)) <= 0.051 for mm in (m, m - 1, m - 2))


def zustaende():
    state = STATE
    state.clear()
    for e in hb.TABELLE:
        ent = hb.entitaet(e)[1]
        v = e["demo"]
        if e["art"] == "b":
            s = "on" if v else "off"
        elif e["art"] == "z":
            s = str(round((now() - dt.datetime(2026, 1, 1, tzinfo=TZ)).total_seconds() / 3600 * v, 2))
        elif isinstance(v, str) and "{{" in v:
            s = render(v)
        else:
            s = str(v)
        if e["attr"]:
            ATTR[(ent, e["attr"])] = s
        else:
            state[ent] = s
    state[E("weather")] = "partlycloudy"
    ATTR[("sun.sun", "next_rising")] = "2026-09-26T05:12:00+00:00"
    ATTR[("sun.sun", "next_setting")] = "2026-09-25T17:21:00+00:00"
    ATTR[(E("solcast_today"), "detailedForecast")] = parse(render(hb.DUMMY_DETAILED))
    for praefix, tage in DACH.items():
        for d, (p50, p10) in enumerate(tage):
            ent = praefix + DACH_TAG[d]
            state[ent] = str(p50)
            ATTR[(ent, "estimate10")] = p10
            ATTR[(ent, "detailedForecast")] = dach_halbstunden(praefix, d)
    state["sensor.solcast_test_weg_prognose_heute"] = "unavailable"
    state[OST + "heute"] = "unavailable"
    # Ausgangslage der Faelle
    del state[E("wb2_mode")]              # B: Referenz fehlt in HA ganz
    state[E("bat3_soc")] = "unavailable"  # C: Referenz nicht verfuegbar
    state[E("inv1_temp")] = "unavailable"  # D: Nicht-Referenz nicht verfuegbar
    del state[E("hp_humidity")]           # D: Nicht-Referenz fehlt ganz
    state[E("wb1_power")] = str(round(hb.NAMEN["wb1_power"]["demo"] * 1000))  # L: W statt kW
    return state


SCHRITT = {"5minute": dt.timedelta(minutes=5), "hour": dt.timedelta(hours=1), "day": dt.timedelta(days=1)}
FAKTOR = {"5minute": 1 / 12, "hour": 1, "day": 24, "month": 600}


def statistik(data):
    """Wie recorder.get_statistics: je ID Zeilen mit start, end, mean (W) und
    change (kWh) -- beides fuer jede ID, die Vorlage nimmt, was sie braucht."""
    start = as_datetime(data["start_time"])
    per = data["period"]
    out = {}
    for n, sid in enumerate(data["statistic_ids"]):
        reihe, t, i = [], start, 0
        while t < now() and i < 400:
            if per == "month":
                nxt = t.replace(month=t.month + 1) if t.month < 12 else t.replace(year=t.year + 1, month=1)
            else:
                nxt = t + SCHRITT[per]
            if nxt > now():
                break
            reihe.append({"start": t.astimezone(dt.timezone.utc).isoformat(),
                          "end": nxt.astimezone(dt.timezone.utc).isoformat(),
                          "mean": round(400 + 100 * n + 80 * (i % 5), 1),
                          "change": round((3 + n) * (1 + (i % 5) * 0.3) * FAKTOR[per] / 10, 3)})
            t, i = nxt, i + 1
        out[sid] = reihe
    return {"statistics": out}


class FakeHA:
    def __init__(self):
        self.state = zustaende()
        self.stunde = parse(render(hb.DUMMY_STUNDE))
        self.tag = parse(render(hb.DUMMY_TAG))
        self.cli = None
        self.aktionen = []
        self.select = []           # (entity_id, option) je select.select_option
        self.select_folgt = True   # HA uebernimmt die Option sofort in den Zustand
        self.select_fehler = False  # HA lehnt ab (wie eine unbekannte Option)
        self.stat_heute = {}       # period -> letzte Antwort auf den Tagesabruf (types mean)
        self.dach_fehler = False   # Abruf je Dach scheitert (Fall W), die uebrigen nicht
        self.ohne_5min = False     # Tagesabruf 5 min ohne Zeilen (Fall Y)
        self.heute_fehler = False  # Tagesabruf 5 min scheitert (Fall Y)
        self.heute_n = 0           # Antworten auf den Tagesabruf 5 min

    async def verbinden(self, frist=60):
        self.cli = APIClient("127.0.0.1", PORT, None)
        ende = time.monotonic() + frist
        while True:
            try:
                await self.cli.connect(login=True)
                break
            except Exception:
                if time.monotonic() > ende:
                    raise
                await asyncio.sleep(0.5)
        self.cli.subscribe_home_assistant_states_and_services(lambda s: None, self.aktion, self.abo)
        self.cli.subscribe_states(lambda s: None)

    async def trennen(self):
        await self.cli.disconnect()
        self.cli = None

    def abo(self, ent, attr):
        v = ATTR.get((ent, attr)) if attr else self.state.get(ent)
        if v is not None:
            self.cli.send_home_assistant_state(ent, attr, v if isinstance(v, str) else str(v))

    def heute(self, sid, art):
        """Tageswert, wie das Panel ihn aus den eigenen Antworten rechnen muss."""
        h = self.stat_heute.get("hour", {}).get("statistics", {}).get(sid, [])
        m = self.stat_heute.get("5minute", {}).get("statistics", {}).get(sid, [])
        if art == "m":
            return sum(e["mean"] for e in h) / 1000 + sum(e["mean"] for e in m) / 12000
        return sum(e["change"] for e in h) + sum(e["change"] for e in m)

    def setzen(self, name, wert):
        self.state[E(name)] = wert
        self.cli.send_home_assistant_state(E(name), "", wert)

    def setzen_attr(self, name, attr, wert):
        ATTR[(E(name), attr)] = wert
        self.cli.send_home_assistant_state(E(name), attr, wert)

    def aktion(self, c):
        data = dict(c.data)
        try:
            for k, v in c.data_template.items():
                data[k] = parse(render(v))
            if c.service == "select.select_option":
                self.select.append((data.get("entity_id"), data.get("option")))
                if self.select_fehler:
                    raise Exception(f"Option {data.get('option')} ist nicht gueltig")
                if self.select_folgt:
                    self.state[data["entity_id"]] = data["option"]
                    self.cli.send_home_assistant_state(data["entity_id"], "", data["option"])
                resp = {}
            elif c.service == "weather.get_forecasts":
                # Abruf je Dach: nur seine Vorlage liest estimate10 der Tageswerte
                if self.dach_fehler and "state_attr(e, 'estimate10')" in (c.response_template or ""):
                    raise Exception("Prognose je Dach: Fehler (Probe)")
                resp = {data["entity_id"]: {"forecast": self.stunde if data["type"] == "hourly" else self.tag}}
            elif c.service == "recorder.get_statistics":
                fuenf = "mean" in data.get("types", []) and data["period"] == "5minute"
                if fuenf and self.heute_fehler:
                    raise Exception("Tageswerte 5 min: Fehler (Probe)")
                resp = statistik(data)
                if fuenf and self.ohne_5min:
                    resp = {"statistics": {k: [] for k in resp["statistics"]}}
                if "mean" in data.get("types", []):
                    self.stat_heute[data["period"]] = resp
                if fuenf:
                    self.heute_n += 1
            else:
                raise Exception(f"Action {c.service} not found")
            r = parse(render(c.response_template, response=resp)) if c.response_template else resp
            self.aktionen.append((c.service, True))
            self.cli.send_homeassistant_action_response(c.call_id, True, "", json.dumps({"response": r}).encode())
        except Exception as ex:
            self.aktionen.append((c.service, False))
            self.cli.send_homeassistant_action_response(c.call_id, False, str(ex), b"")

    async def bild(self, name, seite=None):
        if self.cli is None:
            return
        if seite:
            await self.dienst("probe_page", {"page": seite})
            await asyncio.sleep(1.5)
        # snapshot.take ueberschreibt nie: alte Datei vorher weg
        (SHOTS / name).unlink(missing_ok=True)
        await self.dienst("probe_shot", {"name": name})
        await asyncio.sleep(1.0)

    async def dienst(self, name, args):
        _, dienste = await self.cli.list_entities_services()
        for d in dienste:
            if d.name == name:
                await self.cli.execute_service(d, args)
                return
        raise RuntimeError(f"Aktion {name} fehlt in tests/ha-test.yaml")

    async def tippen(self, wb, seg):
        """Tipp auf Teil seg (0 Aus, 1 Smart, 2 Schnell) von Wallbox wb (0, 1)."""
        await self.dienst("probe_tap", {"wb": wb, "seg": seg})

    async def warte_select(self, n, frist=3.0):
        ende = time.monotonic() + frist
        while len(self.select) < n and time.monotonic() < ende:
            await asyncio.sleep(0.1)
        return self.select[n - 1] if len(self.select) >= n else None


# --------------------------------------------------------------------------
# Panel: Programm starten, PROBE-Zeilen lesen
# --------------------------------------------------------------------------
class Panel:
    def __init__(self):
        self.letzte = None
        self.alle = []
        self.log = []
        self.proc = None

    def starten(self):
        SHOTS.mkdir(parents=True, exist_ok=True)
        e = dict(os.environ, SDL_VIDEODRIVER="offscreen", ESPHOME_SNAPSHOT_DIR=str(SHOTS))
        self.proc = subprocess.Popen([str(PROGRAMM)], cwd=str(ROOT), env=e, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True, errors="replace")
        threading.Thread(target=self._lesen, daemon=True).start()

    def _lesen(self):
        for zeile in self.proc.stdout:
            if zeile.startswith("PROBE "):
                try:
                    d = json.loads(zeile[6:])
                except ValueError:
                    continue
                self.letzte = d
                self.alle.append(d)
            else:
                self.log.append(zeile.rstrip())

    def stoppen(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(5)
            except subprocess.TimeoutExpired:
                self.proc.kill()

    async def warten(self, bedingung, frist):
        ende = time.monotonic() + frist
        while time.monotonic() < ende:
            if self.proc.poll() is not None:
                raise RuntimeError("Programm beendet:\n" + "\n".join(self.log[-20:]))
            d = self.letzte
            if d is not None and bedingung(d):
                return d
            await asyncio.sleep(0.25)
        return None


def kopf_rest(d):
    """Rest aus der Kopfzeile der Seite Prognose ("... · Rest 3,4 kWh · ..."), sonst None."""
    m = re.search(r"· Rest (\d+,\d) kWh", d["fc"]["total"])
    return m.group(1) if m else None


def bit(d, platz):
    return (d["dev"] >> dict(hb.PLAETZE)[platz]) & 1


def zahl(text):
    """Erste Zahl mit Dezimalkomma ("W · 6,0 kWh" -> 6.0), sonst None."""
    m = re.search(r"-?\d+,\d+", text or "")
    return float(m.group(0).replace(",", ".")) if m else None


ERGEBNIS = []


def pruefe(fall, text, ok, info=""):
    ERGEBNIS.append((fall, text, bool(ok)))
    print(f"  [{'ok ' if ok else 'FEHLER'}] {fall} {text}" + (f"  ({info})" if info and not ok else ""), flush=True)


async def ablauf_y(panel, ha, n_verbunden):
    """Fall Y: Ladehinweise und laufende Stunde der Seite Prognose."""
    alle = list(panel.alle)
    i0 = next((i for i, x in enumerate(alle) if x["fc"]["tiles"] > 0), None)
    vorher = alle[:i0] if i0 is not None else alle
    pruefe("Y", "bis zur ersten Antwort je Dach: \"Prognose wird geladen …\" statt \"Keine Prognose\"",
           i0 is not None and vorher and all(x["fc"]["empty"] == "Prognose wird geladen …" and x["fc"]["empty_hid"] == 0
                                              for x in vorher), sorted({x["fc"]["empty"] for x in vorher}))
    erste = alle[i0] if i0 is not None else None
    pruefe("Y", "erste Zeile mit Kacheln: noch ohne Ist, Hinweis \"Ist wird geladen …\"",
           erste and erste["fc"]["act"][0] == 0 and erste["fc"]["hint"] == "Ist wird geladen …",
           erste and (erste["fc"]["act"], erste["fc"]["hint"]))
    ohne = [x for x in alle if x["fc"]["tiles"] > 0 and x["fc"]["mode"] == 0 and x["fc"]["act"][0] == 0
            and x["fc"]["min"] >= 60 and x["fc"]["hint"] == ""]
    pruefe("Y", "nie Kacheln ohne Ist und ohne Hinweis", not ohne, ohne[:1] and ohne[0]["fc"])
    d = await panel.warten(lambda d: d["fc"]["act"][0] > 0 and d["fc"]["hint"] == "", 10)
    pruefe("Y", "nach dem Tagesabruf: Ist da, kein Hinweis", d, panel.letzte["fc"]["hint"])
    # Zeiten (Info) ab dem Verbinden: Kacheln (Linien), Ist-Balken. millis()
    # zaehlt auf dem Rechner nicht ab dem Programmstart, darum nur Abstaende
    alle = list(panel.alle)
    t_v = alle[n_verbunden]["ms"] if len(alle) > n_verbunden else None
    t_k = next((x["ms"] for x in alle if x["fc"]["tiles"] > 0), None)
    t_i = next((x["ms"] for x in alle if x["fc"]["tiles"] > 0 and x["fc"]["act"][0] > 0), None)
    if None not in (t_v, t_k, t_i):
        print(f"  Zeiten ab dem Verbinden: Kacheln/Linien {(t_k - t_v) / 1000:.0f} s, "
              f"Ist-Balken {(t_i - t_v) / 1000:.0f} s", flush=True)

    # 5-min-Zeilen der laufenden Stunde; nicht ueber die volle Stunde hinweg
    while (now().minute == 59 and now().second >= 30) or (now().minute == 0 and now().second < 10):
        await asyncio.sleep(1)
    own = float(ha.state[E("pv1_power")]) / 1000

    async def heute_abrufen():
        """Tagesabruf ausloesen und auf die 5-min-Antwort warten; laeuft er
        gerade (Takt, Skript single), noch einmal."""
        n0 = ha.heute_n
        for _ in range(2):
            await ha.dienst("probe_fetch_today", {})
            ende = time.monotonic() + 8
            while ha.heute_n == n0 and time.monotonic() < ende:
                await asyncio.sleep(0.2)
            if ha.heute_n != n0:
                return True
        return False

    await heute_abrufen()
    hs = now().replace(minute=0, second=0, microsecond=0)
    lauf = [r for r in ha.stat_heute["5minute"]["statistics"].get(E("pv1_power"), []) if as_datetime(r["start"]) >= hs]
    n_soll = len(lauf)
    j_soll = max((int((as_datetime(r["end"]) - hs).total_seconds() // 300) for r in lauf), default=0)
    d = await panel.warten(lambda d: d["fc"]["hh"] == 1 and d["fc"]["n"] == n_soll and d["fc"]["j"] == j_soll, 5)
    pruefe("Y", f"5-min-Zeilen der laufenden Stunde: {n_soll} Zeilen bis Fach {j_soll}, Stunde laut HA = Panel", d,
           {k_: panel.letzte["fc"][k_] for k_ in ("n", "j", "hh")})
    c = sum(r["mean"] for r in lauf) / len(lauf) / 1000 if lauf else own
    cur = panel.letzte["fc"]["cur"]
    pruefe("Y", f"laufende Stunde zwischen HA-Mittel {c:.3f} und fester Leistung {own:.3f} kW",
           cur is not None and min(c, own) - 0.01 <= cur <= max(c, own) + 0.01, cur)
    # gezeichnet: Kachel 1 hat den halb deckenden Balken der laufenden Stunde
    # Die Achse zeigt hoechstens 20 Stunden; die Testwerte haben Ist ab 0 Uhr,
    # ab 20 Uhr liegt die laufende Stunde darum hinter der Achse
    achse = now().hour < 20
    pruefe("Y", "Kachel 1 zeichnet den Balken der laufenden Stunde" + ("" if achse else " (ab 20 Uhr nicht auf der Achse)"),
           panel.letzte["fc"]["lauf_h"] > 0 if achse else panel.letzte["fc"]["lauf_h"] == 0,
           panel.letzte["fc"]["lauf_h"])
    # ohne 5-min-Zeilen: nur die eigene Summe
    ha.ohne_5min = True
    await heute_abrufen()
    d = await panel.warten(lambda d: d["fc"]["n"] == 0 and d["fc"]["j"] == 0 and d["fc"]["cur"] is not None
                           and abs(d["fc"]["cur"] - own) <= 0.005, 5)
    pruefe("Y", f"ohne 5-min-Zeilen: Balken = eigene Leistung {own:.3f} kW", d,
           {k_: panel.letzte["fc"][k_] for k_ in ("n", "j", "cur")})
    # Ohne 5-min-Zeilen hat HA kein Mittel der Stunde (fc_r_cur leer): ein
    # Balken kommt dann nur aus der eigenen Summe
    pruefe("Y", "ohne 5-min-Zeilen: Kachel 1 zeichnet den Balken aus der eigenen Summe"
           + ("" if achse else " (ab 20 Uhr nicht auf der Achse)"),
           panel.letzte["fc"]["lauf_h"] > 0 if achse else panel.letzte["fc"]["lauf_h"] == 0, panel.letzte["fc"]["lauf_h"])
    ha.ohne_5min = False
    # Tagesabruf scheitert -> "Ist unvollstaendig"; der naechste gute nimmt es weg
    ha.heute_fehler = True
    await ha.dienst("probe_fetch_today", {})
    d = await panel.warten(lambda d: d["fc"]["hint"] == "Ist unvollständig", 10)
    pruefe("Y", "Tagesabruf scheitert: \"Ist unvollständig\"", d, panel.letzte["fc"]["hint"])
    ha.heute_fehler = False
    beantwortet = await heute_abrufen()
    d = await panel.warten(lambda d: d["fc"]["hint"] == "" and d["fc"]["hh"] == 1, 5)
    pruefe("Y", "naechster Tagesabruf gelingt: kein Hinweis", d,
           (beantwortet, panel.letzte["fc"]["hint"], panel.letzte["fc"]["hh"],
            [z for z in panel.log if "ha" in z or "fc" in z or "cript" in z][-6:]))


async def ablauf(panel, ha, bilder):
    # S: vor dem Verbinden, nach dem Anlauf der Flussanimation (150 Takte
    # zu 20 ms) -- vorher stand dort nichts Pruefbares
    d = await panel.warten(lambda d: d["ms"] > 6000, 30)
    pruefe("S", "vor dem ersten Wert: kein Geraet, keine Leitung, keine Kugel im Schema",
           d and d["dev"] == 0 and d["schema_vis"] == 0,
           d and {k: d[k] for k in ("dev", "schema_vis", "schema_lines")})

    await ha.verbinden()
    print("verbunden", flush=True)
    n_verbunden = len(panel.alle)

    # A: vor ha_ready -- Heizungsgruppe gelaufen (Raum leer, weil FALSE),
    # Luftfeuchte fehlt noch ohne Urteil -> Striche
    d = await panel.warten(lambda d: d["ready"] == 0 and d["txt"]["hp_room"] == "", 15)
    pruefe("A", "vor ha_ready: fehlender Wert zeigt Striche", d and d["txt"]["hp_humidity"] == "--",
           d and d["txt"]["hp_humidity"])

    d = await panel.warten(lambda d: d["ready"] == 1, 30)
    pruefe("-", "ha_ready 10-20 s nach dem Verbinden", d)
    if not d:
        return
    await asyncio.sleep(2.5)
    d = panel.letzte
    # B
    pruefe("B", "Referenz none (Flaeche 8): Bit aus, Kasten weg", bit(d, "pv_8") == 0 and d["hid"]["roof8"] == 1)
    pruefe("B", "Referenz fehlt in HA (Wallbox 2): Bit aus, Kasten weg", bit(d, "wb_2") == 0 and d["hid"]["wb2"] == 1)
    pruefe("B", "uebrige Geraete da", all(bit(d, p) for p, _ in hb.PLAETZE if p not in ("pv_8", "wb_2", "bat_3"))
           and d["hid"]["roof1"] == 0 and d["hid"]["wb1"] == 0 and d["hid"]["heatpump"] == 0, hex(d["dev"]))
    # S: mit den Referenzen kommt das Schema
    pruefe("S", "nach den Referenzen: Hausanschluss und Hausnetz da, Leitungen sichtbar",
           bit(d, "grid") == 1 and d["hid"]["grid"] == 0 and d["hid"]["house"] == 0 and d["schema_lines"] > 20,
           {k: d[k] for k in ("dev", "schema_vis", "schema_lines")})
    # C
    pruefe("C", "Referenz unavailable (Speicher 3): Bit aus, Kasten weg", bit(d, "bat_3") == 0 and d["hid"]["bat3"] == 1)
    # D
    t = d["txt"]
    pruefe("D", "WR 1 Temperatur unavailable: Kasten da, nur Temperatur leer",
           d["hid"]["pv_inv1"] == 0 and d["hid"]["inv1"] == 0 and d["inv_temp"][0] == "leer"
           and d["inv_temp"][1] not in ("leer", "nan"), d["inv_temp"])
    pruefe("D", "Raumtemperatur FALSE: leer, Waermepumpe da", t["hp_room"] == "" and d["hid"]["heatpump"] == 0,
           repr(t["hp_room"]))
    pruefe("D", "Luftfeuchte fehlt in HA: nach ha_ready leer", t["hp_humidity"] == "", repr(t["hp_humidity"]))
    # L: Faktor
    pruefe("L", "Faktor -1: Hauszaehler 5126 W -> -5,1 kW", t["v_meter_house"] == "-5,1" and bit(d, "meter_house") == 1,
           repr(t["v_meter_house"]))
    pruefe("L", "Faktor -1: Strom Speicher 1 12,4 A -> -12 A", "· -12 A ·" in d["txt"]["d_bat1"],
           repr(d["txt"]["d_bat1"]))
    pruefe("L", "Faktor 0.001: Wallbox 1 7400 W -> 7,4 kW", t["v_wb1"] == "7,4", repr(t["v_wb1"]))
    # M: Ausgangslage aus der Tabelle (deutsche Demo-Formen)
    pruefe("M", "Demo Sommer / Geschlossen / Warmwasser -> Sommer / zu / Warmwasser",
           (t["hp_season"], t["hp_bypass"], t["hp_compressor"]) == ("Sommer", "zu", "Warmwasser"),
           (t["hp_season"], t["hp_bypass"], t["hp_compressor"]))
    # N
    pruefe("N", "Einspeisegrenze nicht belegt: aus feed_limit_pct 60 -> aktiv", t["gr_rule_0"] == "60 % aktiv",
           repr(t["gr_rule_0"]))
    if bilder:
        await ha.bild("probe_1_start.bmp")

    # M: Rohwerte aus HA
    for season, bypass, comp, soll in [
            ("on", "off", "Heating + hot water", ("Sommer", "zu", "Heizen + Warmwasser")),
            ("off", "on", "Standby", ("Winter", "offen", "Bereit")),
            ("OFF", "On", "hot water", ("Winter", "offen", "Warmwasser")),
            ("on", "off", "Heating", ("Sommer", "zu", "Heizen")),
            ("unknown_x", "teilweise", "Abtauen", ("unknown_x", "teilweise", "Abtauen"))]:
        ha.setzen("hp_season", season)
        ha.setzen("hp_bypass", bypass)
        ha.setzen("hp_compressor", comp)
        d = await panel.warten(lambda d: (d["txt"]["hp_season"], d["txt"]["hp_bypass"], d["txt"]["hp_compressor"])
                               == soll, 5)
        pruefe("M", f"{season} / {bypass} / {comp} -> {' / '.join(soll)}", d,
               panel.letzte and tuple(panel.letzte["txt"][k] for k in ("hp_season", "hp_bypass", "hp_compressor")))

    # E
    ha.setzen("bat3_soc", "64")
    d = await panel.warten(lambda d: bit(d, "bat_3") == 1, 5)
    pruefe("E", "Referenz bekommt Wert: Speicher 3 wieder da",
           d and d["hid"]["bat3"] == 0 and d["txt"]["v_bat3"] == "64", d and d["txt"]["v_bat3"])

    # F
    ha.setzen("bat2_soc", "unavailable")
    ha.setzen("bat1_voltage", "unavailable")
    d = await panel.warten(lambda d: bit(d, "bat_2") == 0, 5)
    pruefe("F", "Referenz faellt zur Laufzeit aus: Speicher 2 weg", d and d["hid"]["bat2"] == 1)
    await asyncio.sleep(2)
    d = panel.letzte
    sub = d["txt"]["d_bat1"]
    pruefe("F", "Nicht-Referenz faellt aus: Speicher 1 da, Spannung leer",
           d["hid"]["bat1"] == 0 and bit(d, "bat_1") == 1 and sub.endswith(" V") and not re.search(r"\d\s*V$", sub)
           and "A" in sub, repr(sub))

    # L: unavailable mit Faktor -1 bleibt leer (nie +inf)
    ha.setzen("bat1_current", "unavailable")
    await asyncio.sleep(2)
    sub = panel.letzte["txt"]["d_bat1"]
    pruefe("L", "Faktor -1 und unavailable: Strom leer, Speicher 1 da",
           "·  A ·" in sub and panel.letzte["hid"]["bat1"] == 0, repr(sub))

    # I: leerer Wert in einer Summe -> Summe leer, Geraet bleibt
    ha.setzen("hp_power", "unavailable")
    ha.setzen("wb1_power", "unavailable")
    await asyncio.sleep(3)
    d = panel.letzte
    t = d["txt"]
    pruefe("I", "Waermepumpe Leistung leer, Geraet da", t["v_heatpump"] == "" and d["hid"]["heatpump"] == 0
           and bit(d, "heatpump") == 1, repr(t["v_heatpump"]))
    pruefe("I", "Sonstige = Haus - Waermepumpe: leer", t["v_misc"] == "", repr(t["v_misc"]))
    pruefe("I", "Summe Verbraucher (Seite Haus): leer", t["ht_c_total"] == "", repr(t["ht_c_total"]))
    pruefe("I", "Hausnetz = Haus + Ladepunkte (Wallbox 1 leer): leer, Wallbox da",
           t["v_house"] == "" and d["hid"]["wb1"] == 0 and bit(d, "wb_1") == 1, repr(t["v_house"]))
    pruefe("I", "Out-Summe der Seite Haus: leer", t["ht_out_total"] == "", repr(t["ht_out_total"]))
    if bilder:
        await ha.bild("probe_2_laufzeit.bmp")

    # G
    d = await panel.warten(lambda d: d["stats_week"] and d["wx_stamp"]
                           and len(d["forecast_curve"].split(",")) == 16, 60)
    pruefe("G", "Prognosen und Statistik gefuellt", d,
           panel.letzte and {k: panel.letzte[k] for k in ("stats_week", "wx_stamp", "forecast_curve")})
    pruefe("G", "Aktionen beantwortet (Wetter, Statistik)",
           any(s == "weather.get_forecasts" and ok for s, ok in ha.aktionen)
           and any(s == "recorder.get_statistics" and ok for s, ok in ha.aktionen), ha.aktionen)

    # V: Tagesvorhersage ohne sun_duration (DUMMY_TAG) -> Zeile Sonne weg
    d = panel.letzte
    pruefe("V", "ohne Sonnenscheindauer: Zeile Sonne weg, Wind auf 232, Trennlinien 224",
           d["wx_sun"] == [1, 232, 224], d["wx_sun"])
    pruefe("V", "Warnstufe 1 aus HA: Text der Warnung", d["txt"]["wx_warn"].startswith("DWD-Warnung: "),
           repr(d["txt"]["wx_warn"]))
    ha.setzen("warn_level", "0")
    d = await panel.warten(lambda d: d["txt"]["wx_warn"] == "Keine Warnung des DWD", 5)
    pruefe("V", "Warnstufe 0: Keine Warnung des DWD", d, repr(panel.letzte["txt"]["wx_warn"]))
    if bilder:
        await ha.bild("probe_14_wetter.bmp", "weather")
    ha.setzen("warn_level", "unavailable")
    d = await panel.warten(lambda d: d["txt"]["wx_warn"] == "DWD-Warnungen nicht verfügbar", 5)
    pruefe("V", "Warnstufe unavailable: nicht verfuegbar statt keine Warnung", d,
           repr(panel.letzte["txt"]["wx_warn"]))

    # K: Modus-Schalter Wallbox 1 (Wallbox 2 fehlt in HA, s. B)
    ent1 = E("wb1_mode")
    d = panel.letzte
    pruefe("K", "Ausgang: Wallbox 1 meldet pv -> Smart leuchtet", d["wb_seg"][0] == 1, d["wb_seg"])
    ha.select_folgt = False
    await ha.tippen(0, 2)
    d = await panel.warten(lambda d: d["wb_seg"][0] == 2, 3)
    pruefe("K", "Tipp Schnell: leuchtet sofort, bevor HA etwas meldet", d, panel.letzte["wb_seg"])
    s = await ha.warte_select(1)
    pruefe("K", "Tipp Schnell: select.select_option mit Entitaet und now", s == (ent1, "now"), s)
    ha.setzen("wb1_energy", "13.1")        # anderer Wert der Karte, Modus noch pv
    await asyncio.sleep(2.5)
    pruefe("K", "bis evcc meldet, bleibt der getippte Teil (anderer Wert kam)", panel.letzte["wb_seg"][0] == 2,
           panel.letzte["wb_seg"])
    ha.setzen("wb1_mode", "now")
    await asyncio.sleep(2)
    pruefe("K", "evcc meldet now: Schnell leuchtet", panel.letzte["wb_seg"][0] == 2, panel.letzte["wb_seg"])
    ha.select_folgt = True
    await ha.tippen(0, 1)
    s = await ha.warte_select(2)
    pruefe("K", "Optionen off/pv/minpv/now: Smart schickt pv", s == (ent1, "pv"), s)
    d = await panel.warten(lambda d: d["wb_seg"][0] == 1, 3)
    pruefe("K", "Zustand pv kommt zurueck: Smart leuchtet", d, panel.letzte["wb_seg"])
    ha.setzen_attr("wb1_mode", "options", str(hb.MODUS_OPTIONEN_NEU))
    ha.setzen("wb1_mode", "off")
    await asyncio.sleep(2)
    await ha.tippen(0, 1)
    s = await ha.warte_select(3)
    pruefe("K", "Optionen off/smart/now: Smart schickt smart", s == (ent1, "smart"), s)
    d = await panel.warten(lambda d: d["wb_seg"][0] == 1, 3)
    await ha.tippen(0, 0)
    s = await ha.warte_select(4)
    pruefe("K", "Tipp Aus: off", s == (ent1, "off"), s)
    await asyncio.sleep(1.5)
    n = len(ha.select)
    seg2 = panel.letzte["wb_seg"][1]
    await ha.tippen(1, 2)
    await asyncio.sleep(2)
    pruefe("K", "Wallbox 2 fehlt: kein Befehl, Schalter unveraendert",
           len(ha.select) == n and panel.letzte["wb_seg"][1] == seg2, (ha.select[n:], panel.letzte["wb_seg"]))
    # HA lehnt ab -> sofort zurueck auf den gemeldeten Modus (off = Aus)
    ha.select_fehler = True
    await ha.tippen(0, 2)
    await ha.warte_select(n + 1)
    d = await panel.warten(lambda d: d["wb_seg"][0] == 0, 4)
    pruefe("K", "HA lehnt ab: zurueck auf den gemeldeten Modus", d and ("select.select_option", False) in ha.aktionen,
           panel.letzte["wb_seg"])
    ha.select_fehler = False
    # HA nimmt an, evcc meldet nichts -> nach 10 s zurueck
    ha.select_folgt = False
    await ha.tippen(0, 1)
    d = await panel.warten(lambda d: d["wb_seg"][0] == 1, 3)
    d2 = await panel.warten(lambda d: d["wb_seg"][0] == 0, 15)
    pruefe("K", "keine Meldung von evcc: nach etwa 10 s zurueck", d and d2, panel.letzte["wb_seg"])
    ha.select_folgt = True
    if bilder:
        await ha.bild("probe_4_wallbox.bmp")

    # U: Wallbox 1 ohne Fahrzeug, dann mit evcc-internem Namen
    ha.setzen("wb1_connected", "off")
    d = await panel.warten(lambda d: d["txt"]["wb1_vehicle"] == "Kein Fahrzeug", 5)
    t = panel.letzte["txt"]
    pruefe("U", "ohne Fahrzeug: Name einmal, Status leer, Ladestand/Limit/Plan Striche",
           d and t["wb1_status"] == "" and (t["wb1_soc"], t["wb1_limit"], t["wb1_plan"]) == ("--", "--", "--"),
           {k: t[k] for k in ("wb1_vehicle", "wb1_status", "wb1_soc", "wb1_limit", "wb1_plan")})
    if bilder:
        await ha.bild("probe_13_wallbox_ohne_fahrzeug.bmp", "wallbox")
    ha.setzen("wb1_vehicle", "db:21")
    ha.setzen("wb1_connected", "on")
    soc = str(hb.NAMEN["wb1_soc"]["demo"])
    d = await panel.warten(lambda d: d["txt"]["wb1_vehicle"] == "Fahrzeug", 5)
    pruefe("U", f"Fahrzeug db:21 -> \"Fahrzeug\", Ladestand wieder {soc}", d and panel.letzte["txt"]["wb1_soc"] == soc,
           {k: panel.letzte["txt"][k] for k in ("wb1_vehicle", "wb1_status", "wb1_soc")})
    ha.setzen("wb1_vehicle", str(hb.NAMEN["wb1_vehicle"]["demo"]))
    if bilder:
        await ha.dienst("probe_page", {"page": "overview"})

    # O: Tageswerte aus der Statistik -- erst Stunden, dann 5 min ab deren Ende
    ende = time.monotonic() + 60
    while "5minute" not in ha.stat_heute and time.monotonic() < ende:
        await asyncio.sleep(0.5)
    pruefe("O", "Tagesabruf: Stunden, dann 5 min (types mean, change)",
           "hour" in ha.stat_heute and "5minute" in ha.stat_heute, list(ha.stat_heute))
    await asyncio.sleep(2.5)
    for name, sid, art, feld in [
            ("Flaeche 1 aus Mittel der Leistung", E("pv1_power"), "m", "pv_sub1"),
            ("Waschmaschine aus ha_dev2_energy_total", "sensor.waschmaschine_energie_gesamt", "c", "dev2_d"),
            ("Einspeisung heute aus meter1_total", E("meter1_total"), "c", "meter1_today")]:
        soll = ha.heute(sid, art)
        ist = zahl(panel.letzte["txt"][feld])
        pruefe("O", f"{name}: {soll:.2f} kWh", ist is not None and soll > 0 and abs(ist - soll) <= 0.051,
               repr(panel.letzte["txt"][feld]))
    # P: Erzeugung heute = Summe der Wechselrichter, Eigenverbrauch nach docs/01
    t = panel.letzte["txt"]
    inv = [hb.NAMEN[f"inv{k}_energy"]["demo"] for k in range(1, 5)]
    pruefe("P", f"Erzeugung heute ohne Entitaet: Summe WR {sum(inv):.1f}", t["val_gen"] == f"{sum(inv):.1f}".replace(
        ".", ","), repr(t["val_gen"]))
    eigen = sum(inv[1:]) - hb.NAMEN["meter4_today"]["demo"]
    gespart = f"+{eigen * 0.30:.2f} €".replace(".", ",")
    pruefe("P", f"Eigenverbrauch = WR 2..4 - Ueberschuss = {eigen:.1f} kWh -> Gespart {gespart}",
           gespart in t["money_split"], repr(t["money_split"]))
    ha.setzen("inv1_energy", "40.0")
    soll = f"{40.0 + sum(inv[1:]):.1f}".replace(".", ",")
    d = await panel.warten(lambda d: d["txt"]["val_gen"] == soll, 5)
    pruefe("P", f"WR 1 aendert sich -> Summe {soll}", d, panel.letzte["txt"]["val_gen"])
    ha.setzen("inv4_energy", "unavailable")
    d = await panel.warten(lambda d: d["txt"]["val_gen"] == "", 5)
    pruefe("P", "Tageswert eines WR unavailable -> Summe leer", d, repr(panel.letzte["txt"]["val_gen"]))
    ha.setzen("inv4_energy", str(inv[3]))
    d = await panel.warten(lambda d: d["txt"]["val_gen"] == soll, 5)
    pruefe("P", "Wert kommt wieder -> Summe wieder da", d, panel.letzte["txt"]["val_gen"])
    # X: Autarkie heute mit dem ganzen Verbrauch, ohne ihn mit dem Haus
    v_haus, v_ges, v_bez = (hb.NAMEN[n]["demo"] for n in ("home_energy_today", "total_energy_today", "meter0_today"))
    kx = lambda v: f"{v:.1f}".replace(".", ",")  # noqa: E731

    def autarkie(v):
        return str(round(max(0.0, min(100.0, (v - v_bez) / v * 100))))

    t = panel.letzte["txt"]
    pruefe("X", f"Autarkie aus dem Gesamtverbrauch: ({kx(v_ges)} - {kx(v_bez)}) / {kx(v_ges)} = {autarkie(v_ges)} %, "
           f"Kachel Verbrauch {kx(v_haus)}", t["val_autarky"] == autarkie(v_ges) and t["val_use"] == kx(v_haus),
           (t["val_autarky"], t["val_use"]))
    ha.setzen("total_energy_today", "unavailable")
    d = await panel.warten(lambda d: d["txt"]["val_autarky"] == autarkie(v_haus), 5)
    pruefe("X", f"Gesamtverbrauch unavailable: aus dem Hausverbrauch {autarkie(v_haus)} %, Kachel unveraendert",
           d and d["txt"]["val_use"] == kx(v_haus), (panel.letzte["txt"]["val_autarky"], panel.letzte["txt"]["val_use"]))
    ha.setzen("total_energy_today", "2.0")
    d = await panel.warten(lambda d: d["txt"]["val_autarky"] == "0", 5)
    pruefe("X", f"Bezug {kx(v_bez)} ueber dem Gesamtverbrauch 2,0: 0 %", d, panel.letzte["txt"]["val_autarky"])
    ha.setzen("total_energy_today", str(v_ges))
    d = await panel.warten(lambda d: d["txt"]["val_autarky"] == autarkie(v_ges), 5)
    pruefe("X", f"Gesamtverbrauch wieder da: {autarkie(v_ges)} %", d, panel.letzte["txt"]["val_autarky"])
    # R: Prognose je Dach
    sued, west = DACH["sensor.solcast_test_sued_prognose_"], DACH["sensor.solcast_test_west_prognose_"]
    k = lambda v: f"{v:.1f}".replace(".", ",")  # noqa: E731
    d = await panel.warten(lambda d: d["fc"]["on"] == 3 and d["fc"]["tiles"] == 2, 30)
    pruefe("R", "Kacheln nur fuer Flaechen mit Wert heute (1 und 2; 3 und 5 unavailable)", d, panel.letzte["fc"])
    await asyncio.sleep(1.5)
    fc = panel.letzte["fc"]
    pruefe("R", "Kachel 1 heisst wie Flaeche 1", fc["t0n"] == "Dach Süd", repr(fc["t0n"]))
    bisher = ha.heute(E("pv1_power"), "m")
    m = re.match(r"^(\d+,\d) / (\d+,\d) kWh$", fc["t0"])
    pruefe("R", f"Titel Flaeche 1: bisher {k(bisher)} / Prognose {k(sued[0][0])} kWh",
           m and m.group(2) == k(sued[0][0]) and abs(float(m.group(1).replace(",", ".")) - bisher) <= 0.051,
           repr(fc["t0"]))
    pruefe("R", f"Kopfzeile: Prognose = Summe heute {k(sued[0][0] + west[0][0])} kWh",
           f"/ Prognose {k(sued[0][0] + west[0][0])} kWh · Rest " in fc["total"], repr(fc["total"]))
    pruefe("R", f"Stundenbalken aus der Statistik: {now().hour} volle Stunden je Dach",
           fc["act"] == [now().hour, now().hour], fc["act"])
    p = [dach_halbstunden(x) for x in DACH]
    soll = sum((q[24]["pv_estimate"] + q[25]["pv_estimate"]) / 2 for q in p)
    ist = panel.letzte["forecast_curve"].split(",")
    pruefe("R", f"forecast_curve aus der Summe der Daecher (12 Uhr {soll:.2f})",
           len(ist) == 16 and abs(float(ist[6]) - soll) <= 0.02, panel.letzte["forecast_curve"])
    if bilder:
        await ha.bild("probe_11_prognose.bmp", "forecast")
    await ha.dienst("probe_fc_mode", {"mode": 1})
    soll_t0 = "6 Tage " + k(sum(x for x, _ in sued[1:])) + " kWh"
    soll_t1 = "6 Tage " + k(west[1][0]) + " kWh"
    d = await panel.warten(lambda d: d["fc"]["mode"] == 1 and d["fc"]["t0"] == soll_t0, 4)
    pruefe("R", f"Tipp Vorschau: Kachel 1 {soll_t0}", d, panel.letzte["fc"])
    fc = panel.letzte["fc"]
    pruefe("R", f"Vorschau: Kachel 2 nur morgen ({soll_t1})", fc["t1"] == soll_t1, repr(fc["t1"]))
    pruefe("R", f"Vorschau: Kopfzeile Morgen {k(sued[1][0] + west[1][0])} kWh",
           fc["total"].startswith(f"Morgen {k(sued[1][0] + west[1][0])} kWh · 6 Tage "), repr(fc["total"]))
    if bilder:
        await ha.bild("probe_12_prognose_vorschau.bmp", "forecast")
    await ha.dienst("probe_fc_mode", {"mode": 0})
    d = await panel.warten(lambda d: d["fc"]["mode"] == 0 and d["fc"]["t0"].endswith(f"/ {k(sued[0][0])} kWh"), 4)
    pruefe("R", "Tipp Heute: zurueck auf bisher / Prognose", d, panel.letzte["fc"])

    # Y: Seite Prognose -- Start, laufende Stunde live, Hinweise
    await ablauf_y(panel, ha, n_verbunden)

    # W: Rest heute, Teil 1 -- Daecher 1 und 2 (Volleinspeisung) mit
    # Prognose, Flaechen 3..7 da, aber ohne Prognose je Dach
    entitaet = k(hb.NAMEN["solcast_remaining"]["demo"])
    d = await panel.warten(lambda d: kopf_rest(d) is not None and kopf_rest(d) == d["txt"]["pv_rest"], 65)
    pruefe("W", "Seite PV = Kopfzeile Prognose (alle Daecher, eine Rechnung)", d,
           (panel.letzte["txt"]["pv_rest"], panel.letzte["fc"]["total"]))
    d = panel.letzte
    pruefe("W", "Rest = P50 der Halbstunden ab jetzt, laufende anteilig (Flaechen 1, 2)",
           rest_passt(zahl(d["txt"]["pv_rest"]), list(DACH), d["fc"]["min"]),
           (d["txt"]["pv_rest"], d["fc"]["min"], round(rest_soll(list(DACH), d["fc"]["min"]), 2)))
    pruefe("W", f"Hausdaecher ohne Prognose je Dach: Statusleiste und Haus mit der Entitaet {entitaet}",
           d["txt"]["status_left"].endswith(f"· Restprognose {entitaet} kWh")
           and d["txt"]["ht_rest"] == f"Rest {entitaet} kWh", (d["txt"]["status_left"], d["txt"]["ht_rest"]))
    # Teil 2 vorbereiten: Flaeche 5 bekommt eine Prognose; das Panel liest
    # sie mit dem naechsten Abruf, also nach dem Wiederverbinden in Fall H
    STATE[OST + "heute"] = "9.84"
    ATTR[(OST + "heute", "estimate10")] = 4.43
    ATTR[(OST + "heute", "detailedForecast")] = dach_halbstunden(OST)

    if bilder:
        await ha.bild("probe_5_pv.bmp", "pv")
        await ha.bild("probe_6_haus.bmp", "house")
        await ha.bild("probe_7_netz.bmp", "grid")
        await ha.bild("probe_8_uebersicht.bmp", "overview")

    # Q: Stoerung aus dem Statustext (WR 3)
    def stoerung(d):
        return [a for a in d["alerts"] if a[0].lower().endswith(": fault")]

    pruefe("Q", "Ausgang Normal: keine Stoerung WR 3", not stoerung(panel.letzte), panel.letzte["alerts"])
    ha.setzen("inv3_status", "FAULT")
    d = await panel.warten(lambda d: stoerung(d) and d["txt"]["inv_sub3"] == "FAULT", 4)
    pruefe("Q", "Text FAULT (Gross-/Kleinschreibung egal) -> Meldung, Zweitzeile FAULT", d,
           (panel.letzte["alerts"], panel.letzte["txt"]["inv_sub3"]))
    if bilder:
        await ha.bild("probe_9_meldungen.bmp", "alerts")
        await ha.bild("probe_10_pv_stoerung.bmp", "pv")
        await ha.dienst("probe_page", {"page": "overview"})
    ha.setzen("inv3_status", "Normal")
    await asyncio.sleep(2)
    pruefe("Q", "Normal: Meldung haelt (inv_fault_hold_s 4)", stoerung(panel.letzte), panel.letzte["alerts"])
    d = await panel.warten(lambda d: not stoerung(d) and d["txt"]["inv_sub3"].startswith("W ·"), 8)
    pruefe("Q", "nach der Haltezeit: Meldung weg, Zweitzeile wieder normal", d,
           (panel.letzte["alerts"], panel.letzte["txt"]["inv_sub3"]))
    ha.setzen("inv3_status", "Fault")
    d = await panel.warten(lambda d: stoerung(d), 4)
    n0 = len(panel.alle)
    anzahl = stoerung(panel.letzte)[0][1] if d else -1
    for _ in range(3):
        ha.setzen("inv3_status", "Normal")
        await asyncio.sleep(1.2)
        ha.setzen("inv3_status", "Fault")
        await asyncio.sleep(1.2)
    zeilen = panel.alle[n0:]
    pruefe("Q", f"Schleife Fault <-> Normal: Meldung durchgehend offen, Anzahl bleibt {anzahl}",
           d and zeilen and all(len(stoerung(x)) == 1 and stoerung(x)[0][1] == anzahl for x in zeilen),
           [x["alerts"] for x in zeilen[-2:]])
    ha.setzen("inv3_status", "Standby")
    d = await panel.warten(lambda d: not stoerung(d), 9)
    pruefe("Q", "Standby (kein Stoerungstext): nach der Haltezeit weg", d, panel.letzte["alerts"])
    await asyncio.sleep(2)
    pruefe("Q", "Standby bleibt ohne Meldung", not stoerung(panel.letzte), panel.letzte["alerts"])

    # T: verbunden -- Quellen ueber der Grenze, aber keine Meldung je Quelle
    zeilen = panel.alle[n_verbunden:]
    alt = max((max(x["age"]) for x in zeilen), default=-1)
    keine = [a[0] for x in zeilen for a in x["alerts"] if a[0].startswith("System: Keine Daten von")]
    pruefe("T", f"verbunden: aeltester Wert {alt} s (Grenze 15 s), keine Meldung Keine Daten von",
           alt > 15 and not keine, keine[:3] or alt)

    # H
    n_trennen = len(panel.alle)
    await ha.trennen()
    d = await panel.warten(lambda d: d["link"] >= 1, 30)
    pruefe("H", "Trennung: Sammelmeldung da", d, panel.letzte and panel.letzte["txt"]["lbl_alert"])
    if d:
        await asyncio.sleep(1.5)
        d = panel.letzte
        pruefe("H", "genau eine Systemmeldung, keine je Quelle", d["sys_open"] == 1 and d["link"] == 1,
               f'sys_open={d["sys_open"]}')
        pruefe("H", "Meldungszeile nennt sie", "Keine Verbindung zu Home Assistant" in d["txt"]["lbl_alert"],
               d["txt"]["lbl_alert"])
    # Getrennt bleiben, bis der 10-s-Takt des Datenwegs die Trennung sicher
    # gesehen hat: Erst dann ruft er nach dem Verbinden die Prognosen neu ab
    # (Fall W, Teil 2); eine kuerzere Trennung fiele zwischen zwei Takte
    await asyncio.sleep(10.5)
    # Y: getrennt zaehlt die alte Leistung nicht (fc_live_on aus)
    getrennt = [x for x in panel.alle[n_trennen:] if x["fc"]["live"] == 0]
    pruefe("Y", f"getrennt: eigene Summe der laufenden Stunde waechst nicht ({len(getrennt)} Zeilen)",
           len(getrennt) >= 5 and all(b["fc"]["own_t"] <= a["fc"]["own_t"] for a, b in zip(getrennt, getrennt[1:])),
           [x["fc"]["own_t"] for x in getrennt[:6]])
    n_wieder = len(panel.alle)
    await ha.verbinden()
    d = await panel.warten(lambda d: d["link"] == 0, 30)
    pruefe("H", "wieder verbunden: Sammelmeldung behoben", d)
    if bilder:
        await ha.bild("probe_3_wieder.bmp")

    # W: Teil 2 -- Flaeche 5 mit Prognose (Abruf nach dem Verbinden), die
    # uebrigen Flaechen des Hausnetz-Kreises fallen aus
    for n in (3, 4, 6, 7):
        ha.setzen(f"pv{n}_power", "unavailable")
    d = await panel.warten(lambda d: d["fc"]["on"] == 0b10011 and "Restprognose Haus " in d["txt"]["status_left"], 60)
    pruefe("W", "Flaeche 5 mit Prognose, einzige des Hausnetz-Kreises: Statusleiste \"Restprognose Haus\"", d,
           (panel.letzte["fc"]["on"], panel.letzte["txt"]["status_left"]))
    await asyncio.sleep(1.5)
    d = panel.letzte
    m = d["fc"]["min"]
    haus = zahl(d["txt"]["status_left"])
    pruefe("W", "Statusleiste: Rest nur aus Flaeche 5 (dieselbe Rechnung)", rest_passt(haus, [OST], m),
           (d["txt"]["status_left"], m, round(rest_soll([OST], m), 2)))
    pruefe("W", "Haus: derselbe Rest wie die Statusleiste", zahl(d["txt"]["ht_rest"]) == haus,
           (d["txt"]["ht_rest"], d["txt"]["status_left"]))
    d = await panel.warten(lambda d: kopf_rest(d) is not None and kopf_rest(d) == d["txt"]["pv_rest"], 65)
    pruefe("W", "Seite PV = Kopfzeile Prognose, jetzt mit Flaeche 5",
           d and rest_passt(zahl(d["txt"]["pv_rest"]), list(DACH) + [OST], d["fc"]["min"]),
           (panel.letzte["txt"]["pv_rest"], panel.letzte["fc"]["total"]))
    # Y: nach dem Wiederverbinden "Ist unvollstaendig", bis der Tagesabruf antwortet
    d = await panel.warten(lambda d: d["fc"]["tiles"] > 0 and d["fc"]["hint"] == "" and d["fc"]["live"] == 1, 60)
    nach = panel.alle[n_wieder:]
    pruefe("Y", "wiederverbunden: erst \"Ist unvollständig\", nach dem Tagesabruf kein Hinweis",
           d and any(x["fc"]["hint"] == "Ist unvollständig" for x in nach),
           sorted({x["fc"]["hint"] for x in nach}))
    if bilder:
        await ha.bild("probe_15_rest_uebersicht.bmp", "overview")
        await ha.bild("probe_16_rest_haus.bmp", "house")
        await ha.dienst("probe_page", {"page": "overview"})
    # Teil 3: Flaeche 6 kommt ohne Prognose je Dach zurueck -> Entitaet
    ha.setzen("pv6_power", str(hb.NAMEN["pv6_power"]["demo"]))
    d = await panel.warten(lambda d: d["txt"]["status_left"].endswith(f"· Restprognose {entitaet} kWh")
                           and d["txt"]["ht_rest"] == f"Rest {entitaet} kWh", 10)
    pruefe("W", f"Flaeche 6 da, ohne Prognose je Dach: wieder die Entitaet {entitaet}", d,
           (panel.letzte["txt"]["status_left"], panel.letzte["txt"]["ht_rest"]))
    # Teil 4: Tageswechsel -- Halbstunden von gestern zaehlen nicht, bis ein
    # Abruf den Tag stempelt
    ha.setzen("pv6_power", "unavailable")
    d = await panel.warten(lambda d: "Restprognose Haus " in d["txt"]["status_left"], 10)
    pruefe("W", "Flaeche 6 wieder weg: Statusleiste \"Restprognose Haus\"", d, panel.letzte["txt"]["status_left"])

    def mit_entitaet(d):
        return (d["txt"]["status_left"].endswith(f"· Restprognose {entitaet} kWh")
                and d["txt"]["ht_rest"] == f"Rest {entitaet} kWh")

    await ha.dienst("probe_p50_day", {"shift": -1})
    d = await panel.warten(lambda d: d["txt"]["pv_rest"] == "--,-" and "· Rest --,- kWh" in d["fc"]["total"]
                           and mit_entitaet(d), 5)
    pruefe("W", "Halbstunden von gestern: Seite PV und Kopfzeile --,-, Statusleiste und Haus mit der Entitaet", d,
           (panel.letzte["txt"]["pv_rest"], panel.letzte["fc"]["total"], panel.letzte["txt"]["status_left"]))
    await ha.dienst("probe_fetch_fc", {})
    d = await panel.warten(lambda d: "Restprognose Haus " in d["txt"]["status_left"] and kopf_rest(d) is not None
                           and kopf_rest(d) == d["txt"]["pv_rest"], 15)
    pruefe("W", "Abruf heute: Rest wieder aus den Halbstunden", d,
           (panel.letzte["txt"]["pv_rest"], panel.letzte["txt"]["status_left"]))
    # Nach 0 Uhr gelingt nur der Abruf der ganzen Anlage, der je Dach
    # scheitert: die Halbstunden je Dach bleiben von gestern und zaehlen nicht
    await ha.dienst("probe_p50_day", {"shift": -1})
    await panel.warten(lambda d: d["txt"]["pv_rest"] == "--,-" and mit_entitaet(d), 5)
    ha.dach_fehler = True
    n0 = len(ha.aktionen)
    await ha.dienst("probe_fetch_fc", {})
    await asyncio.sleep(3)
    neu = ha.aktionen[n0:]
    # neu rechnen lassen (fc_redraw), ohne auf den Minutenwechsel zu warten
    await ha.dienst("probe_p50_day", {"shift": 0})
    await asyncio.sleep(1.5)
    d = panel.letzte
    pruefe("W", "nur der Abruf je Dach scheitert: Seite PV und Kopfzeile --,-, Statusleiste und Haus mit der Entitaet",
           ("weather.get_forecasts", False) in neu and ("weather.get_forecasts", True) in neu
           and d["txt"]["pv_rest"] == "--,-" and "· Rest --,- kWh" in d["fc"]["total"] and mit_entitaet(d),
           (neu, d["txt"]["pv_rest"], d["fc"]["total"], d["txt"]["status_left"]))
    ha.dach_fehler = False
    await ha.dienst("probe_fetch_fc", {})
    d = await panel.warten(lambda d: "Restprognose Haus " in d["txt"]["status_left"] and kopf_rest(d) is not None
                           and kopf_rest(d) == d["txt"]["pv_rest"], 15)
    pruefe("W", "Abruf je Dach gelingt wieder: Rest aus den Halbstunden", d,
           (panel.letzte["txt"]["pv_rest"], panel.letzte["txt"]["status_left"]))
    # Teil 5: Flaeche 3 (ohne Leistung) mit Tageswert, aber ohne Halbstunden
    # -> Entitaet statt eines Hausrests ohne dieses Dach
    STATE["sensor.solcast_test_weg_prognose_heute"] = "5.0"
    await ha.dienst("probe_fetch_fc", {})
    d = await panel.warten(lambda d: d["fc"]["on"] == 0b10111 and mit_entitaet(d), 15)
    pruefe("W", f"Flaeche 3 mit Tageswert ohne Halbstunden: Statusleiste und Haus mit der Entitaet {entitaet}", d,
           (panel.letzte["fc"]["on"], panel.letzte["txt"]["status_left"], panel.letzte["txt"]["ht_rest"]))
    # Teil 6: keine Prognose je Dach mehr -> Seite PV aus den Halbstunden der
    # ganzen Anlage (fc_sys_p50, Antwortvorlage mit zwei Stellen)
    for x in list(DACH) + [OST, "sensor.solcast_test_weg_prognose_"]:
        STATE[x + "heute"] = "unavailable"
    anlage = [round(e["pv_estimate"], 2) for e in ATTR[(E("solcast_today"), "detailedForecast")]]
    await ha.dienst("probe_fetch_fc", {})
    d = await panel.warten(lambda d: d["fc"]["on"] == 0 and rest_passt(zahl(d["txt"]["pv_rest"]), [], d["fc"]["min"],
                                                                        anlage), 15)
    pruefe("W", "ohne Prognose je Dach: Seite PV aus den Halbstunden der ganzen Anlage, Statusleiste mit der Entitaet",
           d and mit_entitaet(d), (panel.letzte["fc"]["on"], panel.letzte["txt"]["pv_rest"], panel.letzte["fc"]["min"],
                                   round(rest_aus(anlage, panel.letzte["fc"]["min"]), 2)))

    # J: in keiner PROBE-Zeile des ganzen Laufs ein Label mit "inf"/"nan"
    schlecht = [x for x in panel.alle if x["bad"]]
    n_lab = min((x["labels"] for x in panel.alle), default=0)
    pruefe("J", f"Label-Suche erreicht alle Seiten ({n_lab} Labels)", n_lab > 300, n_lab)
    pruefe("J", f"kein Label zeigt inf oder nan ({len(panel.alle)} Zeilen, alle Seiten)", panel.alle and not schlecht,
           schlecht and schlecht[0]["bad_txt"])


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--no-build", action="store_true", help="nicht bauen, vorhandenes Programm nehmen")
    ap.add_argument("--shots", action="store_true", help="Bilder nach shots/ha_probe/ (BMP)")
    a = ap.parse_args()
    logging.getLogger("aioesphomeapi").setLevel(logging.CRITICAL)   # Fehlversuche beim Warten
    env = dict(os.environ, ESPHOME_DATA_DIR=str(DATA))
    if not a.no_build:
        esphome = Path(sys.executable).parent / "esphome"
        print("baue tests/ha-test.yaml ...", flush=True)
        r = subprocess.run([str(esphome), "compile", str(CONFIG.relative_to(ROOT))], cwd=str(ROOT), env=env,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
        if r.returncode:
            print("\n".join(r.stdout.splitlines()[-30:]))
            sys.exit("Bauen fehlgeschlagen")
    if not PROGRAMM.exists():
        sys.exit(f"{PROGRAMM} fehlt -- ohne --no-build aufrufen")
    panel = Panel()
    panel.starten()
    try:
        asyncio.run(ablauf(panel, FakeHA(), a.shots))
    finally:
        panel.stoppen()
    fehler = [e for e in ERGEBNIS if not e[2]]
    print(f"\n{len(ERGEBNIS) - len(fehler)} von {len(ERGEBNIS)} Pruefungen bestanden")
    sys.exit(1 if fehler or not ERGEBNIS else 0)


if __name__ == "__main__":
    main()
