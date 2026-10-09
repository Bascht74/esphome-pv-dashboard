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


if __name__ == "__main__":
    unittest.main()
