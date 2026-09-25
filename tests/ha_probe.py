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
  J  in keinem Label irgendwo "inf" oder "nan", ueber den ganzen Lauf

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
env = ImmutableSandboxedEnvironment(undefined=StrictUndefined)
env.globals.update(now=now, as_datetime=as_datetime, as_local=lambda d: d.astimezone(TZ), today_at=today_at,
                   timedelta=dt.timedelta, state_attr=lambda e, a: ATTR.get((e, a)))
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


def zustaende():
    state = {}
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
    # Ausgangslage der Faelle
    del state[E("wb2_mode")]              # B: Referenz fehlt in HA ganz
    state[E("bat3_soc")] = "unavailable"  # C: Referenz nicht verfuegbar
    state[E("inv1_temp")] = "unavailable"  # D: Nicht-Referenz nicht verfuegbar
    del state[E("hp_humidity")]           # D: Nicht-Referenz fehlt ganz
    return state


def statistik(data):
    start = as_datetime(data["start_time"])
    per = data["period"]
    out = {}
    for n, sid in enumerate(data["statistic_ids"]):
        reihe, t, i = [], start, 0
        while t < now() and i < 400:
            if per == "month":
                nxt = t.replace(month=t.month + 1) if t.month < 12 else t.replace(year=t.year + 1, month=1)
            else:
                nxt = t + (dt.timedelta(hours=1) if per == "hour" else dt.timedelta(days=1))
            if nxt > now():
                break
            reihe.append({"start": t.astimezone(dt.timezone.utc).isoformat(),
                          "end": nxt.astimezone(dt.timezone.utc).isoformat(),
                          "change": round((3 + n) * (1 + (i % 5) * 0.3)
                                          * (24 if per == "day" else (600 if per == "month" else 1)) / 10, 2)})
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

    def setzen(self, name, wert):
        self.state[E(name)] = wert
        self.cli.send_home_assistant_state(E(name), "", wert)

    def aktion(self, c):
        data = dict(c.data)
        try:
            for k, v in c.data_template.items():
                data[k] = parse(render(v))
            if c.service == "weather.get_forecasts":
                resp = {data["entity_id"]: {"forecast": self.stunde if data["type"] == "hourly" else self.tag}}
            elif c.service == "recorder.get_statistics":
                resp = statistik(data)
            else:
                raise Exception(f"Action {c.service} not found")
            r = parse(render(c.response_template, response=resp)) if c.response_template else resp
            self.aktionen.append((c.service, True))
            self.cli.send_homeassistant_action_response(c.call_id, True, "", json.dumps({"response": r}).encode())
        except Exception as ex:
            self.aktionen.append((c.service, False))
            self.cli.send_homeassistant_action_response(c.call_id, False, str(ex), b"")

    async def bild(self, name):
        if self.cli is None:
            return
        # snapshot.take ueberschreibt nie: alte Datei vorher weg
        (SHOTS / name).unlink(missing_ok=True)
        _, dienste = await self.cli.list_entities_services()
        for d in dienste:
            if d.name == "probe_shot":
                await self.cli.execute_service(d, {"name": name})
                await asyncio.sleep(1.0)


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


def bit(d, platz):
    return (d["dev"] >> dict(hb.PLAETZE)[platz]) & 1


ERGEBNIS = []


def pruefe(fall, text, ok, info=""):
    ERGEBNIS.append((fall, text, bool(ok)))
    print(f"  [{'ok ' if ok else 'FEHLER'}] {fall} {text}" + (f"  ({info})" if info and not ok else ""), flush=True)


async def ablauf(panel, ha, bilder):
    await ha.verbinden()
    print("verbunden", flush=True)

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
    if bilder:
        await ha.bild("probe_1_start.bmp")

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

    # H
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
    await ha.verbinden()
    d = await panel.warten(lambda d: d["link"] == 0, 30)
    pruefe("H", "wieder verbunden: Sammelmeldung behoben", d)
    if bilder:
        await ha.bild("probe_3_wieder.bmp")

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
