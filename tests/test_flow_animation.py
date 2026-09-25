# Tests fuer tools/flow_animation.py (Kugeln und Leitungen der Uebersicht).
#
#   ~/.venvs/esphome-beta/bin/python -m unittest discover tests
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import flow_animation as fa  # noqa: E402


class FlowAnimation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = fa.UI.read_text(encoding="utf-8")
        cls.lines = fa.leitungen_lesen(cls.text)
        cls.boxes = fa.kaesten_lesen(cls.text)
        cls.d = fa.erzeugen(cls.lines, cls.boxes)

    def test_datei_aktuell(self):
        dots, logik = fa.yaml_bauen(self.d)
        self.assertEqual(fa.einbauen(self.text, dots, logik), self.text,
                         "python3 tools/flow_animation.py --write laufen lassen")

    def test_jeder_kasten_hat_platz(self):
        erlaubt = set(fa.SLOTS) | {"speicher", "immer"}
        for kasten in self.boxes:
            with self.subTest(kasten=kasten):
                self.assertIn(kasten, fa.KASTEN)
                self.assertIn(fa.KASTEN[kasten], erlaubt)

    def test_jeder_platz_hat_kasten(self):
        self.assertEqual(sorted(set(fa.KASTEN.values()) & set(fa.SLOTS)), sorted(fa.SLOTS))

    def test_jede_strecke_hat_kanal_oder_schweigt(self):
        self.assertEqual(len(self.d["ch"]), self.d["n"])
        for i, ch in enumerate(self.d["ch"]):
            with self.subTest(strecke=i):
                if i in self.d["still"]:
                    self.assertIsNone(ch)
                else:
                    self.assertIn(ch, fa.KANAELE)

    def test_strecken_enden_an_kasten_oder_knoten(self):
        for i, t in enumerate(self.d["teile"]):
            for p in (t["pts"][0], t["pts"][-1]):
                k = fa.kasten_bei(p, self.boxes)
                if k is not None:
                    self.assertIn(k, fa.KASTEN, f"Strecke {i}")

    def test_jede_leitung_hat_sichtbarkeitsregel(self):
        self.assertEqual(len(self.d["sicht"]), len(self.lines))
        alle_bits = (1 << len(fa.SLOTS)) - 1
        for k, (al, a, _b) in enumerate(self.d["sicht"]):
            self.assertEqual(al & ~alle_bits, 0, f"ln{k:02d}")
            self.assertEqual(a & ~alle_bits, 0, f"ln{k:02d}")

    def test_jedes_geraet_steuert_eine_leitung(self):
        """Fehlt ein Geraet, muss mindestens eine Leitung davon abhaengen."""
        for bit, platz in enumerate(fa.SLOTS):
            m = 1 << bit
            self.assertTrue(any((al & m) or (a & m) for al, a, _ in self.d["sicht"]), platz)

    def test_kanaele_24(self):
        self.assertEqual(len(fa.KANAELE), 24)


if __name__ == "__main__":
    unittest.main()
