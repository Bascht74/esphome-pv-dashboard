# Rechentest fuer den Sonderwert val_leer (-unendlich) in C++.
#
#   ~/.venvs/esphome-beta/bin/python -m unittest discover tests
#
# Nimmt die echten Rechenhilfen aus dem erzeugten Datenweg
# (.pv-dashboard_ha.yaml) und die echten Formatierer aus
# .pv-dashboard_ui.yaml, baut sie mit g++ zu einem kleinen Programm und
# prueft: leer bleibt leer (auch nach Vorzeichenwechsel, * 0, leer - leer),
# NAN bleibt Striche, keine Ausgabe enthaelt "inf" oder "nan". -inf ist
# IEEE 754 und verhaelt sich auf dem RISC-V des P4 genauso; einen
# RISC-V-Compiler gibt es hier nicht. Ohne g++ wird der Test uebersprungen.
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def hilfen():
    text = (ROOT / ".pv-dashboard_ha.yaml").read_text(encoding="utf-8")
    a = text.index("// Rechnen nur ueber diese Hilfen")
    b = text.index("auto &num = id(fmt_num);", a)
    return text[a:b]


def formatierer(name):
    text = (ROOT / ".pv-dashboard_ui.yaml").read_text(encoding="utf-8")
    m = re.search(r"  - id: " + name + r"\n    type: [^\n]+\n    restore_value: false\n    initial_value: \|-\n"
                  r"((?:      [^\n]*\n|\n)+)", text)
    if not m:
        raise AssertionError(f"{name} nicht gefunden")
    return m.group(1)


def val_leer():
    text = (ROOT / ".pv-dashboard_ui.yaml").read_text(encoding="utf-8")
    m = re.search(r"  - id: val_leer\n    type: float\n    restore_value: false\n    initial_value: '([^']+)'", text)
    if not m:
        raise AssertionError("val_leer nicht gefunden")
    return m.group(1)


PROGRAMM = r"""
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <functional>
#include <limits>
#include <string>

static int fehler = 0;
static void ist(bool ok, const char *was) {
  if (!ok) {
    printf("FEHLER %s\n", was);
    fehler++;
  }
}
static bool text_ok(const std::string &s) {
  std::string t = s;
  for (auto &c : t) c = tolower((unsigned char) c);
  return t.find("inf") == std::string::npos && t.find("nan") == std::string::npos;
}

int main() {
  const float LEER = @VAL_LEER@;
  std::function<std::string(float, const char *, const char *)> fmt_num =
@FMT_NUM@;
  std::function<std::string(float, const char *)> fmt_watt =
@FMT_WATT@;
  std::function<std::string(float)> fmt_power =
@FMT_POWER@;
@HILFEN@
  const float N = NAN;
  const float leer_werte[] = {LEER, neg(LEER), pos(LEER), pos(neg(LEER)), add(LEER, 5.0f), add(5.0f, LEER),
                              add(LEER, N), add(N, LEER), add(LEER, LEER), sub(LEER, LEER), sub(3.0f, LEER),
                              sub(LEER, 3.0f), mul(LEER, 0.0f), mul(LEER, -1000.0f), mul(0.0f, LEER),
                              mul(mul(LEER, 7.0f), 0.01f), add(add(N, mul(LEER, 1000.0f)), 5.0f)};
  int i = 0;
  for (float v : leer_werte) {
    char w[48];
    snprintf(w, sizeof w, "leer bleibt -inf (Fall %d)", i++);
    ist(std::isinf(v) && v < 0, w);
    ist(fmt_num(v, "%.1f", "--,-").empty(), "fmt_num(leer) leer");
    ist(fmt_watt(v, "--.---").empty(), "fmt_watt(leer) leer");
    ist(fmt_power(v).empty(), "fmt_power(leer) leer");
  }
  // auch +inf (etwa fabsf(leer)) gibt leer, nie "inf"
  ist(fmt_num(fabsf(LEER), "%.1f", "--").empty(), "fmt_num(+inf) leer");
  ist(fmt_power(-LEER).empty(), "fmt_power(+inf) leer");
  ist(fmt_num(LEER / 1000.0f, "%.1f", "--").empty(), "kW-Umrechnung bleibt leer");
  // NAN: Striche wie bisher, Rechnen wie bisher
  ist(fmt_num(N, "%.1f", "--,-") == "--,-", "fmt_num(NAN) Striche");
  ist(fmt_watt(N, "--.---") == "--.---", "fmt_watt(NAN) Striche");
  ist(fmt_power(N) == "--", "fmt_power(NAN) Striche");
  ist(std::isnan(neg(N)) && std::isnan(pos(N)) && std::isnan(sub(N, 2.0f)) && std::isnan(mul(N, 2.0f)), "NAN bleibt NAN");
  ist(add(N, 4.0f) == 4.0f && add(4.0f, N) == 4.0f, "add: NAN zaehlt 0");
  ist(pos(-5.0f) == 0.0f && pos(5.0f) == 5.0f && neg(5.0f) == -5.0f, "pos/neg");
  ist(sub(5.0f, 2.0f) == 3.0f && mul(2.0f, 3.0f) == 6.0f, "sub/mul");
  ist(I(LEER, -1) == -1 && I(-LEER, -1) == -1 && I(N, -1) == -1 && I(2.6f, -1) == 3, "I");
  // Zahlen normal, nirgends "inf"/"nan"
  ist(fmt_num(1234.5f, "%.1f", "--") == "1234,5", "fmt_num Zahl");
  ist(fmt_watt(-3412.0f, "--") == "-3.412", "fmt_watt Zahl");
  ist(fmt_power(3200.0f) == "3,2 kW", "fmt_power Zahl");
  for (float v : {LEER, -LEER, N, 0.0f, 1e30f, -1e30f})
    ist(text_ok(fmt_num(v, "%.1f", "--")) && text_ok(fmt_watt(v, "--")) && text_ok(fmt_power(v)), "kein inf/nan im Text");
  printf("%d Fehler\n", fehler);
  return fehler ? 1 : 0;
}
"""


class LeerInCpp(unittest.TestCase):
    def test_leer_rechnen_und_formatieren(self):
        gpp = shutil.which("g++")
        if not gpp:
            self.skipTest("kein g++")
        src = (PROGRAMM.replace("@VAL_LEER@", val_leer())
               .replace("@FMT_NUM@", formatierer("fmt_num").rstrip())
               .replace("@FMT_WATT@", formatierer("fmt_watt").rstrip())
               .replace("@FMT_POWER@", formatierer("fmt_power").rstrip())
               .replace("@HILFEN@", hilfen()))
        with tempfile.TemporaryDirectory() as d:
            c = Path(d) / "leer.cpp"
            c.write_text(src, encoding="utf-8")
            for opt in ("-O0", "-O2"):
                with self.subTest(opt=opt):
                    exe = Path(d) / f"leer{opt}"
                    r = subprocess.run([gpp, "-std=gnu++17", opt, "-Wall", str(c), "-o", str(exe)],
                                       capture_output=True, text=True)
                    self.assertEqual(r.returncode, 0, r.stderr[-2000:])
                    r = subprocess.run([str(exe)], capture_output=True, text=True)
                    self.assertEqual(r.returncode, 0, r.stdout)


class LeerIstUnendlich(unittest.TestCase):
    def test_val_leer_minus_unendlich(self):
        self.assertEqual(val_leer(), "-std::numeric_limits<float>::infinity()")

    def test_keine_nan_kennung_mehr(self):
        for p in list(ROOT.glob(".pv-dashboard_*.yaml")) + list((ROOT / "tests").glob("*.yaml")):
            if p.name == ".pv-dashboard_anlage.yaml":
                continue
            self.assertNotIn("7FC0BEEF", p.read_text(encoding="utf-8").upper(), p.name)

    def test_datenweg_rechnet_nur_ueber_hilfen(self):
        import sys
        sys.path.insert(0, str(ROOT / "tools"))
        import ha_bindings as hb
        for g in hb.GRUPPEN:
            code = g["code"]
            with self.subTest(gruppe=g["name"]):
                self.assertIsNone(re.search(r"[-+*/]\s*@", code.replace("!@", "")), "Rechnung vor @wert")
                self.assertIsNone(re.search(r"@[a-z0-9_]+\s*[-+*/]", code), "Rechnung nach @wert")


if __name__ == "__main__":
    unittest.main()
