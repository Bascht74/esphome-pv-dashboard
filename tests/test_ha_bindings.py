# Tests fuer tools/ha_bindings.py (Datenweg von Home Assistant).
#
#   ~/.venvs/esphome-beta/bin/python -m unittest discover tests
#
# Braucht nur, was in der ESPHome-Umgebung steckt (esphome, jinja2, yaml).
# Liest keine secrets.yaml und nicht .pv-dashboard_anlage.yaml.
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import ha_bindings as hb  # noqa: E402
import flow_animation as fa  # noqa: E402

PANEL = ROOT / ".pv-dashboard_ha.yaml"
DUMMY = ROOT / "ha" / "pv_dashboard_dummy.yaml"


def substitutions_block(text):
    """Schluessel -> Wert aus dem substitutions:-Block der erzeugten Datei."""
    werte = {}
    drin = False
    for zeile in text.split("\n"):
        if zeile == "substitutions:":
            drin = True
            continue
        if drin:
            if zeile and not zeile.startswith(" "):
                break
            m = re.match(r"^  ([a-z0-9_]+): (\S+)", zeile)
            if m:
                werte[m.group(1)] = m.group(2)
    return werte


class ErzeugteDateien(unittest.TestCase):
    def test_panel_aktuell(self):
        self.assertEqual(PANEL.read_text(encoding="utf-8"), hb.pruefen(hb.panel_bauen(), PANEL.name),
                         "python3 tools/ha_bindings.py --write laufen lassen")

    def test_dummy_aktuell(self):
        self.assertEqual(DUMMY.read_text(encoding="utf-8"), hb.dummy_bauen(),
                         "python3 tools/ha_bindings.py --write laufen lassen")

    def test_keine_anker_mehr(self):
        text = PANEL.read_text(encoding="utf-8") + DUMMY.read_text(encoding="utf-8")
        self.assertNotIn("ha_anchor_", text)
        self.assertNotIn("binary_sensor.pv_dashboard_", text)

    def test_dev_present_startet_leer(self):
        self.assertEqual(substitutions_block(PANEL.read_text(encoding="utf-8")).get("dev_present_start"), '"0u"')
        ui = (ROOT / ".pv-dashboard_ui.yaml").read_text(encoding="utf-8")
        m = re.search(r"- id: dev_present\n(?:    .*\n)+", ui)
        self.assertIsNotNone(m)
        self.assertIn("restore_value: false", m.group(0))
        self.assertIn("${dev_present_start}", m.group(0))


class Zuordnung(unittest.TestCase):
    def setUp(self):
        self.text = PANEL.read_text(encoding="utf-8")
        self.subs = substitutions_block(self.text)

    def test_jeder_schluessel_hat_standard(self):
        benutzt = set(re.findall(r"\$\{(ha_[a-z0-9_]+)\}", self.text))
        for ausdruck in re.findall(r"\$\{ ([^}]*) \}", self.text):
            benutzt |= set(re.findall(r"\b(ha_[a-z0-9_]+)\b", ausdruck))
        self.assertTrue(benutzt)
        fehlt = sorted(k for k in benutzt if k not in self.subs)
        self.assertEqual(fehlt, [], "ha_*-Schluessel ohne Standard im substitutions:-Block")

    def test_standard_sind_entity_ids(self):
        for k, v in self.subs.items():
            if k.startswith("ha_") and not k.endswith("_faktor"):
                if k.endswith("_energy_total") and k.startswith("ha_dev"):
                    self.assertEqual(v, "none", k)   # nur fuer ha_dev<N>_energy: statistik
                    continue
                if re.match(r"^ha_pv\d_fc_d\d$", k):
                    self.assertEqual(v, "none", k)   # Prognose je Dach: nur eigene Anlage
                    continue
                self.assertRegex(v, r"^[a-z_]+\.[a-z0-9_]+$", k)

    def test_eine_referenz_je_platz(self):
        plaetze = [p for p, _ in hb.PLAETZE]
        self.assertEqual(sorted(hb.REFERENZ), sorted(plaetze))
        for platz, name in hb.REFERENZ.items():
            with self.subTest(platz=platz):
                self.assertIn(name, hb.NAMEN)
                e = hb.NAMEN[name]
                self.assertIsNone(e["attr"], "Referenz darf kein Attribut sein")
                self.assertIn(e["art"], ("n", "t"), "Referenz: Zahl oder Text")
                self.assertTrue(e["gr"], "Referenz braucht einen Sensor (Gruppe)")
                self.assertIn(f"id: ha_{name}\n", self.text)
                self.assertIn(f"ha_{name}", self.subs)

    def test_plaetze_wie_flow_animation(self):
        self.assertEqual([p for p, _ in hb.PLAETZE], fa.SLOTS)
        self.assertEqual([b for _, b in hb.PLAETZE], list(range(len(fa.SLOTS))))

    def test_anwesenheit_im_intervall(self):
        for platz, bit in hb.PLAETZE:
            self.assertIn(f"neu |= 1u << {bit};   // {platz}", self.text)

    def test_gruppen_nur_bekannte_namen(self):
        for g in hb.GRUPPEN:
            for n in re.findall(r"@([a-z0-9_]+)", g["code"]):
                self.assertIn(n, hb.NAMEN, g["name"])

    def test_jeder_sensor_mit_ersatz(self):
        ids = re.findall(r"^    entity_id: (.*)$", self.text, re.M)
        self.assertTrue(ids)
        for v in ids:
            self.assertIn(hb.ERSATZ_ID, v)


def sensor_bloecke(text):
    """id -> (Abschnitt sensor/text_sensor/binary_sensor, Block) der homeassistant-Sensoren."""
    bloecke = {}
    abschnitt = None
    for teil in re.split(r"(?m)^(?=[a-z_]+:$)|^(?=  - platform: homeassistant$)", text):
        m = re.match(r"^([a-z_]+):$", teil.split("\n", 1)[0])
        if m:
            abschnitt = m.group(1)
            continue
        m = re.search(r"^    id: (ha_[a-z0-9_]+)$", teil, re.M)
        if teil.startswith("  - platform: homeassistant") and m:
            bloecke[m.group(1)] = (abschnitt, teil)
    return bloecke


class Faktor(unittest.TestCase):
    """ha_<name>_faktor (09.10.2026): Vorzeichen bzw. Einheit je Zahlenwert."""

    def setUp(self):
        self.text = PANEL.read_text(encoding="utf-8")
        self.subs = substitutions_block(self.text)
        self.bloecke = sensor_bloecke(self.text)

    def test_jeder_zahlensensor_hat_faktor(self):
        zahl = [e for e in hb.TABELLE if e["gr"] and e["art"] in ("n", "z")]
        self.assertTrue(any(e["attr"] for e in zahl), "auch Attribute")
        for e in zahl:
            with self.subTest(name=e["name"]):
                k = f"ha_{e['name']}_faktor"
                self.assertEqual(self.subs.get(k), '"1"', "Standard 1")
                abschnitt, block = self.bloecke[f"ha_{e['name']}"]
                self.assertEqual(abschnitt, "sensor")
                filt = re.findall(r"^      - multiply: (\S+)$", block, re.M)
                self.assertTrue(filt, "Filter fehlt")
                self.assertEqual(filt[0], "${" + k + "}", "Faktor ist der erste Filter")
                if e["mul"] is not None:
                    self.assertEqual(len(filt), 2, "eingebaute Umrechnung bleibt")

    def test_text_und_an_aus_ohne_faktor(self):
        for e in hb.TABELLE:
            if e["art"] in ("t", "b"):
                with self.subTest(name=e["name"]):
                    self.assertNotIn(f"ha_{e['name']}_faktor", self.subs)
                    if f"ha_{e['name']}" in self.bloecke:
                        self.assertNotIn("filters:", self.bloecke[f"ha_{e['name']}"][1])

    def test_kein_faktor_ohne_sensor(self):
        for k in self.subs:
            if k.endswith("_faktor"):
                with self.subTest(k=k):
                    self.assertIn(k[:-len("_faktor")], self.bloecke)

    def test_faktor_durch_esphome(self):
        """Eigener Faktor sticht den Standard, ESPHome liest ihn als Zahl."""
        try:
            from esphome import yaml_util
            import esphome.config_validation as cv
            from esphome.components.substitutions import do_substitution_pass
        except ImportError:
            self.skipTest("esphome nicht importierbar -- mit der ESPHome-Umgebung starten")
        y = ('substitutions:\n  ha_a_faktor: "1"\n  ha_b_faktor: "-1"\n  ha_c_faktor: "0.001"\n'
             '  ha_d_faktor: -1\nx:\n')
        for k in "abcd":
            y += f"  {k}: ${{ha_{k}_faktor}}\n"
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "t.yaml"
            p.write_text(y, encoding="utf-8")
            x = do_substitution_pass(yaml_util.load_yaml(p))["x"]
        werte = {k: cv.float_(x[k]) for k in "abcd"}
        self.assertEqual(werte, {"a": 1.0, "b": -1.0, "c": 0.001, "d": -1.0})


class NichtBelegt(unittest.TestCase):
    """none/FALSE/off/""/null durch ESPHomes eigene Substitution schicken."""

    WERTE = {"a": "none", "b": "FALSE", "c": "Off", "d": '""', "e": "null", "f": "NONE",
             "g": "false", "h": "OFF", "i": "sensor.echt", "j": "select.evcc_mode"}
    FREI = {"a", "b", "c", "d", "e", "f", "g", "h"}

    def test_substitution(self):
        try:
            from esphome import yaml_util
            from esphome.components.substitutions import do_substitution_pass
        except ImportError:
            self.skipTest("esphome nicht importierbar -- mit ~/.venvs/esphome-beta/bin/python starten")
        y = "substitutions:\n" + "".join(f"  ha_{k}: {v}\n" for k, v in self.WERTE.items()) + "x:\n"
        for k in self.WERTE:
            y += f"  e_{k}: \"{hb.j_entity('ha_' + k)}\"\n"
            y += f"  b_{k}: \"constexpr bool B = {hb.j_belegt('ha_' + k)};\"\n"
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "t.yaml"
            p.write_text(y, encoding="utf-8")
            conf = do_substitution_pass(yaml_util.load_yaml(p))
        x = conf["x"]
        for k, v in self.WERTE.items():
            with self.subTest(wert=v):
                if k in self.FREI:
                    self.assertEqual(x[f"e_{k}"], hb.ERSATZ_ID)
                    self.assertEqual(x[f"b_{k}"], "constexpr bool B = false;")
                else:
                    self.assertEqual(x[f"e_{k}"], v)
                    self.assertEqual(x[f"b_{k}"], "constexpr bool B = true;")


def esphome_substitution(subs, werte):
    """werte (Name -> Text mit ${...}) durch ESPHomes Substitution schicken."""
    from esphome import yaml_util
    from esphome.components.substitutions import do_substitution_pass
    y = "substitutions:\n" + "".join(f"  {k}: {v}\n" for k, v in subs.items()) + "x:\n"
    for k, v in werte.items():
        y += f"  {k}: |-\n" + "".join(f"    {z}\n" for z in v.split("\n"))
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "t.yaml"
        p.write_text(y, encoding="utf-8")
        return do_substitution_pass(yaml_util.load_yaml(p))["x"]


TZ_TEST = __import__("datetime").timezone(__import__("datetime").timedelta(hours=2))


def ha_jinja(vorlage, json_text=True, states=None, attrs=None, **kw):
    """Vorlage wie Home Assistant rendern (Ausschnitt: today_at, now, as_datetime,
    as_local, states, state_attr, tojson); "jetzt" ist der 10.10.2026, 13:20 (+02:00)."""
    import datetime as dt
    import json
    from jinja2 import StrictUndefined
    from jinja2.sandbox import ImmutableSandboxedEnvironment
    tz = TZ_TEST
    env = ImmutableSandboxedEnvironment(undefined=StrictUndefined)
    env.globals.update(
        today_at=lambda s="00:00": dt.datetime(2026, 10, 10, *map(int, s.split(":")), tzinfo=tz),
        now=lambda: dt.datetime(2026, 10, 10, 13, 20, tzinfo=tz),
        as_local=lambda d: d.astimezone(tz),
        states=lambda e: (states or {}).get(e, "unknown"),
        state_attr=lambda e, a: (attrs or {}).get((e, a)),
        as_datetime=lambda v: v if isinstance(v, dt.datetime) else dt.datetime.fromisoformat(v))
    env.filters["tojson"] = json.dumps
    t = env.from_string(vorlage).render(**kw)
    return json.loads(t) if json_text else t


class TagesStatistik(unittest.TestCase):
    """ha_<ziel>: statistik (10.10.2026): Tageswert aus recorder.get_statistics."""

    def setUp(self):
        try:
            import esphome  # noqa: F401
        except ImportError:
            self.skipTest("esphome nicht importierbar -- mit der ESPHome-Umgebung starten")
        self.text = PANEL.read_text(encoding="utf-8")

    def test_ziele_und_quellen(self):
        ziele = [z for z, _, _ in hb.TAGES_STAT]
        self.assertEqual(ziele, [f"pv{i}_energy" for i in range(1, 9)] + [f"dev{d}_energy" for d in range(1, 6)]
                         + [f"meter{m}_today" for m in range(5)])
        for z, q, art in hb.TAGES_STAT:
            with self.subTest(ziel=z):
                self.assertIn(z, hb.NAMEN)
                self.assertIn(q, hb.NAMEN)
                self.assertEqual(art, "m" if z.startswith("pv") else "c")
                self.assertEqual(hb.NAMEN[q]["art"], "n" if art == "m" else "z")

    def test_substitution(self):
        subs = {"ha_pv1_energy": "Statistik", "ha_pv1_power": "sensor.p1",
                "ha_pv2_energy": "statistik", "ha_pv2_power": "none",
                "ha_pv3_energy": "sensor.e3", "ha_pv3_power": "sensor.p3",
                "ha_pv4_energy": "NONE", "ha_pv4_power": "sensor.p4"}
        werte = {}
        for i in range(1, 5):
            werte[f"e{i}"] = hb.j_entity(f"ha_pv{i}_energy")
            werte[f"b{i}"] = hb.j_belegt(f"ha_pv{i}_energy")
            werte[f"q{i}"] = "<" + hb.j_stat_quelle(f"pv{i}_energy", f"pv{i}_power") + ">"
            werte[f"a{i}"] = hb.j_stat_an(f"pv{i}_energy", f"pv{i}_power")
        x = esphome_substitution(subs, werte)
        self.assertEqual([x[f"e{i}"] for i in range(1, 5)], [hb.ERSATZ_ID, hb.ERSATZ_ID, "sensor.e3", hb.ERSATZ_ID])
        self.assertEqual([x[f"b{i}"] for i in range(1, 5)], ["true", "true", "true", "false"])
        self.assertEqual([x[f"q{i}"] for i in range(1, 5)], ["<sensor.p1>", "<>", "<>", "<>"])
        self.assertEqual([x[f"a{i}"] for i in range(1, 5)], ["true", "false", "false", "false"])

    def test_vorlage_rechnet(self):
        """Stunden: Summe mean / 1000 (Leistung) bzw. change (Zaehler); leer ohne Zeile."""
        subs = {f"ha_{n}": e["ent"] for n, e in hb.NAMEN.items() if not e["attr"]}
        subs.update({"ha_pv1_energy": "statistik", "ha_dev2_energy": "statistik",
                     "ha_dev2_energy_total": "sensor.zaehler2", "ha_meter1_today": "statistik",
                     "ha_meter4_today": "statistik"})
        x = esphome_substitution(subs, {"h": hb.jinja_heute(1000), "m": hb.jinja_heute(12000), "ids": hb.stat_ids()})
        p1, m1, m4 = hb.NAMEN["pv1_power"]["ent"], hb.NAMEN["meter1_total"]["ent"], hb.NAMEN["meter4_total"]["ent"]
        self.assertEqual(ha_jinja(x["ids"], json_text=False), "['%s', 'sensor.zaehler2', '%s', '%s']" % (p1, m1, m4))
        zeile = lambda h, **w: dict(start=f"2026-10-10T{h - 1:02d}:00:00+00:00",  # noqa: E731
                                    end=f"2026-10-10T{h:02d}:00:00+00:00", **w)
        resp = {"statistics": {
            p1: [zeile(6, mean=500.0), zeile(7, mean=1500.0), zeile(8)],
            "sensor.zaehler2": [zeile(6, change=0.25), zeile(9, change=1.0)],
            m1: [zeile(5, change=0)],
        }}
        r = ha_jinja(x["h"], response=resp)
        v = r["v"].split(",")
        self.assertEqual(len(v), len(hb.TAGES_STAT))
        self.assertEqual(float(v[0]), 2.0)          # (500 + 1500) / 1000; Zeile ohne mean zaehlt 0
        self.assertEqual(float(v[9]), 1.25)         # dev2
        self.assertEqual(float(v[14]), 0.0)         # meter1: Zeile mit 0 -> 0, nicht leer
        self.assertEqual(v[17], "")                 # meter4: keine Zeile -> leer
        self.assertEqual([i for i, w in enumerate(v) if w], [0, 9, 14])
        self.assertEqual(r["end"], "2026-10-10T09:00:00+00:00")
        r = ha_jinja(x["m"], response={"statistics": {p1: [zeile(10, mean=1200.0)] * 3}})
        self.assertEqual(float(r["v"].split(",")[0]), 0.3)   # 3 x 1200 / 12000
        r = ha_jinja(x["h"], response={"statistics": {}})
        self.assertEqual(r["v"], "," * (len(hb.TAGES_STAT) - 1))
        self.assertTrue(r["end"].startswith("2026-10-10T00:00:00"))

    def test_ziele_mit_ersatz_und_publish(self):
        bloecke = sensor_bloecke(self.text)
        for z, _, _ in hb.TAGES_STAT:
            with self.subTest(ziel=z):
                self.assertIn(f"(ha_{z} | string | lower | trim) == 'statistik'", bloecke[f"ha_{z}"][1])
        m = re.search(r"sensor::Sensor \*const ZIEL\[(\d+)\] = \{([^}]*)\};", self.text)
        self.assertIsNotNone(m)
        self.assertEqual(int(m.group(1)), len(hb.TAGES_STAT))
        self.assertEqual(m.group(2), ", ".join(f"id(ha_{z})" for z, _, _ in hb.TAGES_STAT))
        # Abruf nur, wenn ein Ziel auf statistik steht; bestehende Statistik bleibt
        self.assertIn("constexpr bool S_ANY = ", self.text)
        self.assertIn("id(ha_fetch_stats).execute();", self.text)
        self.assertEqual(self.text.count("action: recorder.get_statistics"), len(hb.ZEITRAEUME) + 1 + 2)


class PrognoseJeDach(unittest.TestCase):
    """ha_pv<N>_fc_d1..7 (10.10.2026): Seite Prognose je Dachflaeche."""

    def setUp(self):
        try:
            import esphome  # noqa: F401
        except ImportError:
            self.skipTest("esphome nicht importierbar -- mit der ESPHome-Umgebung starten")
        self.text = PANEL.read_text(encoding="utf-8")
        self.subs = substitutions_block(self.text)

    def test_schluessel_ohne_sensoren(self):
        for i in range(1, 9):
            for d in range(1, hb.FC_TAGE + 1):
                with self.subTest(k=f"pv{i}_fc_d{d}"):
                    self.assertEqual(self.subs.get(f"ha_pv{i}_fc_d{d}"), "none")
                    self.assertNotIn(f"id: ha_pv{i}_fc_d{d}\n", self.text)
                    self.assertNotIn(f"ha_pv{i}_fc_d{d}_faktor", self.subs)

    def test_gruppen(self):
        namen = [g["name"] for g in hb.GRUPPEN]
        self.assertNotIn("Prognose", namen)
        for i in range(8):
            self.assertIn(f"id(fc_roof_live).execute({i}, @pv{i + 1}_power, @pv{i + 1}_energy);",
                          hb.GRUPPEN[i]["code"])
        self.assertNotIn("fc_today", self.text)
        self.assertNotIn("fc_day", self.text)
        self.assertNotIn("ha_wx_cond", self.text)

    def _echte_halbstunden(self, tag=0, spitze=1.4475):
        """detailedForecast wie die Solcast-Integration (period_start datetime)."""
        import datetime as dt
        t0 = dt.datetime(2026, 10, 10 + tag, tzinfo=TZ_TEST)
        aus = []
        for i in range(48):
            p = spitze if i in (26, 27) else (0.5 if 16 <= i < 36 else 0.0)
            aus.append({"period_start": t0 + dt.timedelta(minutes=30 * i), "pv_estimate": p,
                        "pv_estimate10": round(p * 0.4, 4), "pv_estimate90": p * 1.3, "dampening_factor": 1.0})
        return aus

    def test_vorlage_dach(self):
        subs = {f"ha_pv{i}_fc_d{d}": "none" for i in range(1, 9) for d in range(1, 8)}
        subs.update({f"ha_pv1_fc_d{d}": f"sensor.solcast_sued_{d}" for d in range(1, 8)})
        subs.update({"ha_pv6_fc_d1": "sensor.solcast_nord_heute", "ha_pv6_fc_d2": "FALSE",
                     "ha_pv7_fc_d1": "sensor.solcast_weg"})
        x = esphome_substitution(subs, {"t": hb.jinja_dach()})
        self.assertNotIn("${", x["t"])
        states = {f"sensor.solcast_sued_{d}": str(5.0 + d) for d in range(1, 8)}
        states["sensor.solcast_sued_5"] = "unavailable"
        states["sensor.solcast_nord_heute"] = "8.0105"
        attrs = {(f"sensor.solcast_sued_{d}", "estimate10"): 1.0 + d * 0.5 for d in range(1, 8)}
        attrs[("sensor.solcast_sued_1", "detailedForecast")] = self._echte_halbstunden()
        attrs[("sensor.solcast_sued_2", "detailedForecast")] = self._echte_halbstunden(1)
        attrs[("sensor.solcast_nord_heute", "estimate10")] = 4.2319
        r = ha_jinja(x["t"], states=states, attrs=attrs)
        # Flaeche 7: belegt, aber ohne Zustand -> Schluessel da, Tag 1 leer
        self.assertEqual(sorted(r), ["a1", "a6", "a7", "b1", "b6", "b7", "d1", "d6", "d7", "e1", "e6", "e7"])
        a = r["a1"].split(",")
        self.assertEqual(len(a), 48)
        self.assertEqual(a[26], "1.45")            # 1.4475 mit drei Stellen
        self.assertEqual(a[0], "0")
        self.assertEqual(a[16], "0.5")
        self.assertEqual(r["b1"].split(",")[26], "0.579")
        self.assertEqual(r["d1"], "6,7,8,9,,11,12")   # Tag 5 unavailable -> leer
        self.assertEqual(r["e1"], "1.5,2,2.5,3,3.5,4,4.5")
        self.assertEqual(r["a6"], "," * 47)            # ohne detailedForecast
        self.assertEqual(r["d6"], "8.011,,,,,,")
        self.assertEqual(r["e6"], "4.232,,,,,,")
        self.assertEqual(r["d7"], ",,,,,,")
        # Groesse: sechs Daecher mit vollen Halbstunden bleiben klein
        self.assertLess(len(__import__("json").dumps(r)) * 6 / 3, 4000)

    def test_heute_stundenbalken(self):
        subs = {f"ha_{n}": e["ent"] for n, e in hb.NAMEN.items() if not e["attr"]}
        subs.update({"ha_pv1_fc_d1": "sensor.solcast_sued", "ha_pv1_energy": "statistik",
                     "ha_pv2_fc_d1": "sensor.solcast_west", "ha_pv2_power": "none",
                     "ha_pv3_fc_d1": "sensor.solcast_ost"})
        x = esphome_substitution(subs, {"h": hb.jinja_heute(1000), "m": hb.jinja_heute(12000),
                                        "ids": hb.stat_ids(), "an": hb.j_kurve_an(3) + hb.j_kurve_an(2)})
        p1, p3 = hb.NAMEN["pv1_power"]["ent"], hb.NAMEN["pv3_power"]["ent"]
        # pv1 einmal (statistik und Balken), pv2 ohne Leistung nicht, pv3 nur Balken
        self.assertEqual(ha_jinja(x["ids"], json_text=False), "['%s', '%s']" % (p1, p3))
        self.assertEqual(x["an"], "truefalse")
        zeile = lambda h, **w: dict(start=f"2026-10-10T{h - 1:02d}:00:00+00:00",  # noqa: E731
                                    end=f"2026-10-10T{h:02d}:00:00+00:00", **w)
        resp = {"statistics": {p1: [zeile(7, mean=812.5), zeile(8, mean=1500.0)], p3: [zeile(9, mean=20.0)]}}
        r = ha_jinja(x["h"], response=resp)
        c = r["c"].split(";")
        self.assertEqual(len(c), 8)
        h1 = c[0].split(",")
        self.assertEqual(len(h1), 24)
        # UTC 06:00 = 08:00 Ortszeit (+02:00)
        self.assertEqual((h1[8], h1[9]), ("0.812", "1.5"))
        self.assertEqual([i for i, v in enumerate(h1) if v], [8, 9])
        self.assertEqual(c[1], "")                      # Flaeche 2: keine Leistung
        self.assertEqual(c[2].split(",")[10], "0.02")
        self.assertEqual(r["end"], "2026-10-10T09:00:00+00:00")
        self.assertEqual(float(r["v"].split(",")[0]), 2.312)   # Tageswert pv1 unveraendert
        r = ha_jinja(x["m"], response={"statistics": {p1: [zeile(10, mean=1200.0), zeile(10, mean=600.0)]}})
        self.assertEqual(r["c"].split(";")[0], "0.9")    # Mittel der 5-min-Mittel in kW
        self.assertEqual(r["c"].split(";")[2], "")

    def test_abruf_und_antwort(self):
        self.assertIn("action: weather.get_forecasts", self.text)
        self.assertIn("id(fc_roof_fc).execute(k, ", self.text)
        self.assertIn("id(fc_roof_hours).execute(k, ", self.text)
        # Tagesreihe aus der Anlage nur ohne Prognose je Dach
        self.assertIn("if (id(fc_roof_on) != 0)\n", self.text)
        self.assertEqual(self.text.count("id(forecast_curve).make_call()"), 3)
        m = re.search(r"constexpr bool S_ANY = ([^;]*);", self.text)
        self.assertIn("ha_pv8_fc_d1", m.group(1))


class StoerungAusText(unittest.TestCase):
    """ha_inv<N>_fault nicht belegt: Statustext aus inv_fault_texts = Stoerung."""

    def setUp(self):
        self.text = PANEL.read_text(encoding="utf-8")
        self.subs = substitutions_block(self.text)

    def test_standards(self):
        self.assertEqual(self.subs.get("inv_fault_texts"), '"Fault,Alarm"')
        self.assertEqual(self.subs.get("inv_fault_hold_s"), '"300"')

    def test_gruppe_nimmt_text_nur_ohne_entitaet(self):
        for n in range(1, 5):
            with self.subTest(wr=n):
                self.assertIn(f"const bool f = B_inv{n}_fault ? id(ha_inv{n}_fault).state : "
                              f"((id(ha_inv_fault_txt) >> {n - 1}) & 1u);", self.text)
                self.assertIn(f"!B_inv{n}_fault && B_inv{n}_status", self.text)
                self.assertIn(f"constexpr bool B_inv{n}_fault = ", self.text)


if __name__ == "__main__":
    unittest.main()
