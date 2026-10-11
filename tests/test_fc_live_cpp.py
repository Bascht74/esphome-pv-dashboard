# Rechentest fuer die Live-Fuellung der laufenden Stunde und den Hinweis
# Ist-Werte der Seite Prognose in C++.
#
#   ~/.venvs/esphome-beta/bin/python -m unittest discover tests
#
# Nimmt die echten globals fc_cur_kw, fc_live_tick, fc_val und fc_ist_text
# aus .pv-dashboard_page_forecast.yaml und den Stempel der guten Antwort
# (fc_ist_ms) aus .pv-dashboard_ha.yaml, baut sie mit g++ (id(x) -> x) zu
# einem kleinen Programm und prueft: eigene Summe, Werte von Home Assistant
# bis zum Ende ihrer Zeilen und danach die eigene Summe, falsche Stunde,
# Mindestabdeckung 30 s, Stundenwechsel samt Mitternacht und Luecke,
# Screenshot-Lauf (H = -1) und die Bedingungen des Hinweises, auch das
# Neuzeichnen in derselben Millisekunde wie die Antwort. Ohne g++ wird
# der Test uebersprungen.
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEITE = ROOT / ".pv-dashboard_page_forecast.yaml"
HA = ROOT / ".pv-dashboard_ha.yaml"


def funktion(name):
    text = SEITE.read_text(encoding="utf-8")
    m = re.search(r"  - id: " + name + r"\n    type: [^\n]+\n    restore_value: false\n    initial_value: \|-\n"
                  r"((?:      [^\n]*\n|\n)+)", text)
    if not m:
        raise AssertionError(f"{name} nicht gefunden")
    return m.group(1).rstrip()


def stempel():
    """Ausdruck, den die gute Antwort des Tagesabrufs in fc_ist_ms schreibt
    (j = millis())."""
    m = re.search(r"const uint32_t j = millis\(\);\n *id\(fc_ist_ms\) = ([^;\n]+);", HA.read_text(encoding="utf-8"))
    if not m:
        raise AssertionError("Stempel fc_ist_ms nicht gefunden")
    return m.group(1)


PROGRAMM = r"""
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <functional>
#include <limits>
#include <string>

#define id(x) x

std::array<std::array<float, 12>, 8> fc_lv_e{}, fc_lv_t{};
std::array<uint8_t, 8> fc_lv_n{}, fc_lv_j{};
std::array<float, 8> fc_lv_prev, fc_r_cur, fc_r_now;
std::array<int, 3> fc_lv_i;
std::array<std::array<float, 24>, 8> fc_r_act;
std::array<std::array<float, 48>, 8> fc_r_p50;
uint32_t fc_ist_ms = 0;
bool fc_ist_fehler = false, fc_ist_je = false;
std::function<float(int, int)> fc_cur_kw;
std::function<void(int, int, float, bool)> fc_live_tick;
std::function<float(int, int, int, int)> fc_val;
std::function<const char *(uint32_t, int, int, uint32_t)> fc_ist_text;

static int fehler = 0;
static void ist(bool ok, const char *was) {
  if (!ok) {
    printf("FEHLER %s\n", was);
    fehler++;
  }
}
// Stempel der guten Antwort wie im Datenweg, j = millis()
static uint32_t stempel(uint32_t j) { return @STEMPEL@; }
static bool nahe(float a, float b) { return std::isfinite(a) && fabsf(a - b) < 1e-4f; }
static void leeren() {
  for (auto &r : fc_lv_e) r.fill(0.0f);
  for (auto &r : fc_lv_t) r.fill(0.0f);
  fc_lv_n.fill(0);
  fc_lv_j.fill(0);
  fc_lv_prev.fill(NAN);
  fc_r_cur.fill(NAN);
  fc_r_now.fill(NAN);
  for (auto &r : fc_r_act) r.fill(NAN);
  // Prognose: Ertrag von 7 bis 19 Uhr
  for (auto &r : fc_r_p50)
    for (int i = 0; i < 48; i++)
      r[i] = i >= 14 && i < 38 ? 1.0f : 0.0f;
  fc_lv_i = {-1, -1, -1};
  fc_ist_ms = 0;
  fc_ist_fehler = false;
  fc_ist_je = false;
}
// n Sekunden mit Leistung p (W) je Dach k in Fach slot der Stunde H
static void laufen(int H, int slot, float p, int n, bool an = true) {
  fc_r_now.fill(NAN);
  fc_r_now[0] = p;
  for (int i = 0; i < n; i++)
    fc_live_tick(H, slot, 1.0f, an);
}

int main() {
  fc_cur_kw =
@FC_CUR_KW@;
  fc_live_tick =
@FC_LIVE_TICK@;
  fc_val =
@FC_VAL@;
  fc_ist_text =
@FC_IST_TEXT@;
  const float LEER = -std::numeric_limits<float>::infinity();
  const int H = 284 * 24 + 13;   // 11.10.2026, 13 Uhr

  // 1 nur eigene Werte: 300 s 2000 W in Fach 0, 300 s 4000 W in Fach 1
  leeren();
  laufen(H, 0, 2000.0f, 300);
  laufen(H, 1, 4000.0f, 300);
  ist(nahe(fc_cur_kw(0, H), 3.0f), "nur eigene Werte: Mittel 3 kW");
  ist(std::isnan(fc_cur_kw(1, H)), "Dach ohne Leistung: NAN");
  ist(nahe(fc_lv_t[0][0], 300.0f) && nahe(fc_lv_t[0][1], 300.0f), "Sekunden je Fach");

  // 2 nur HA: 3 Zeilen bis Fach 3, Mittel 1,2 kW; eigene Summe einer anderen Stunde zaehlt nicht
  leeren();
  laufen(H - 1, 0, 9000.0f, 100);
  fc_lv_i[1] = H;
  fc_lv_n[0] = 3;
  fc_lv_j[0] = 3;
  fc_r_cur[0] = 1.2f;
  ist(nahe(fc_cur_kw(0, H), 1.2f), "nur HA: 1,2 kW");
  ist(nahe(fc_cur_kw(0, H - 1), 9.0f), "andere Stunde: eigene Summe von H - 1");

  // 3 gemischt: HA 2 Zeilen bis Fach 2 (1 kW), eigene Faecher 0/1 (5 kW) zaehlen
  // nicht mehr, Faecher 2/3 (2 kW, je 300 s) zaehlen
  leeren();
  laufen(H, 0, 5000.0f, 300);
  laufen(H, 1, 5000.0f, 300);
  laufen(H, 2, 2000.0f, 300);
  laufen(H, 3, 2000.0f, 300);
  fc_lv_i[1] = H;
  fc_lv_n[0] = 2;
  fc_lv_j[0] = 2;
  fc_r_cur[0] = 1.0f;
  ist(nahe(fc_cur_kw(0, H), 1.5f), "gemischt ab Fach j: (1 kW * 600 s + 2 kW * 600 s) / 1200 s");
  // Luecke in den HA-Zeilen: 1 Zeile, Ende Fach 3 -> eigene ab Fach 3
  fc_lv_n[0] = 1;
  fc_lv_j[0] = 3;
  ist(nahe(fc_cur_kw(0, H), 1.5f), "1 HA-Zeile (1 kW) + Fach 3 (2 kW): 1,5 kW");

  // 4 falsche HA-Stunde: nur eigene Werte
  fc_lv_i[1] = H - 1;
  ist(nahe(fc_cur_kw(0, H), 3.5f), "falsche HA-Stunde: eigene Summe 3,5 kW");

  // 5 unter 30 s Abdeckung: NAN, ab 30 s ein Wert
  leeren();
  laufen(H, 0, 1000.0f, 29);
  ist(std::isnan(fc_cur_kw(0, H)), "29 s: NAN");
  laufen(H, 0, 1000.0f, 1);
  ist(nahe(fc_cur_kw(0, H), 1.0f), "30 s: 1 kW");
  // leer (-inf) und NAN zaehlen nicht, aus zaehlt nicht, dt 0 zaehlt nicht
  laufen(H, 0, LEER, 50);
  laufen(H, 0, NAN, 50);
  laufen(H, 0, 7000.0f, 50, false);
  fc_r_now[0] = 7000.0f;
  fc_live_tick(H, 0, 0.0f, true);
  fc_live_tick(H, 12, 1.0f, true);
  ist(nahe(fc_lv_t[0][0], 30.0f) && nahe(fc_cur_kw(0, H), 1.0f), "leer, NAN, aus, dt 0, Fach 12: nichts");

  // 6 Stundenwechsel: Vorstunde fertig, Faecher leer
  leeren();
  laufen(H, 11, 3000.0f, 60);
  laufen(H + 1, 0, 1000.0f, 1);
  ist(nahe(fc_lv_prev[0], 3.0f) && fc_lv_i[2] == H && fc_lv_i[0] == H + 1, "Stundenwechsel: Vorstunde 3 kW");
  ist(nahe(fc_lv_t[0][0], 1.0f) && fc_lv_t[0][11] == 0.0f, "Stundenwechsel: Faecher geleert");
  ist(std::isnan(fc_lv_prev[1]), "Dach ohne Werte: Vorstunde NAN");
  // Vorstunde mit HA-Zeilen der alten Stunde
  leeren();
  laufen(H, 6, 4000.0f, 300);
  fc_lv_i[1] = H;
  fc_lv_n[0] = 6;
  fc_lv_j[0] = 6;
  fc_r_cur[0] = 2.0f;
  laufen(H + 1, 0, 0.0f, 1);
  ist(nahe(fc_lv_prev[0], (2.0f * 1800 + 4.0f * 300) / 2100), "Vorstunde aus HA-Zeilen und eigener Summe");

  // 7 Mitternacht: 23 Uhr -> 0 Uhr des naechsten Tages ist H + 1
  leeren();
  const int H23 = 284 * 24 + 23;
  laufen(H23, 11, 500.0f, 120);
  laufen(285 * 24 + 0, 0, 0.0f, 1);
  ist(nahe(fc_lv_prev[0], 0.5f) && fc_lv_i[2] == H23, "Mitternacht: Vorstunde gesetzt");

  // 8 Luecke von mehr als einer Stunde: keine Vorstunde
  leeren();
  laufen(H, 11, 3000.0f, 60);
  laufen(H + 2, 0, 1000.0f, 1);
  ist(std::isnan(fc_lv_prev[0]) && fc_lv_i[2] == -1, "Luecke: Vorstunde NAN");

  // 9 fc_val: Zukunft NAN, laufende live, Vorstunde ohne HA-Wert eigen, sonst HA
  leeren();
  fc_r_act[0][11] = 2.5f;
  laufen(H, 11, 3000.0f, 60);
  laufen(H + 1, 0, 1000.0f, 60);   // jetzt 14 Uhr = H + 1
  ist(std::isnan(fc_val(0, 15, 14, H + 1)), "fc_val: Zukunft NAN");
  ist(nahe(fc_val(0, 14, 14, H + 1), 1.0f), "fc_val: laufende Stunde live");
  ist(nahe(fc_val(0, 13, 14, H + 1), 3.0f), "fc_val: Vorstunde ohne HA-Wert aus der eigenen Rechnung");
  ist(nahe(fc_val(0, 11, 14, H + 1), 2.5f), "fc_val: fertige Stunde von HA");
  fc_r_act[0][13] = 2.9f;
  ist(nahe(fc_val(0, 13, 14, H + 1), 2.9f), "fc_val: HA-Stundenwert ersetzt die eigene Vorstunde");
  fc_r_act[0][13] = NAN;
  ist(std::isnan(fc_val(0, 12, 14, H + 1)), "fc_val: aeltere Stunde ohne HA-Wert NAN");
  ist(std::isnan(fc_val(0, 13, 14, H + 2)), "fc_val: eigene Vorstunde nur fuer H - 1");
  // 10 Screenshot-Lauf (H = -1): fc_r_cur und fc_r_act wie bisher
  fc_r_cur[0] = 4.34f;
  ist(nahe(fc_val(0, 14, 14, -1), 4.34f), "Shot-Pfad: laufende Stunde = fc_r_cur");
  ist(nahe(fc_val(0, 11, 14, -1), 2.5f) && std::isnan(fc_val(0, 13, 14, -1)), "Shot-Pfad: Stunden aus fc_r_act");
  ist(nahe(fc_val(0, 11, -1, -1), 2.5f), "ohne Uhr: Stundenwert");

  // 11 Hinweis Ist-Werte
  leeren();
  const uint32_t MIN = 60000u;
  ist(strcmp(fc_ist_text(0, 14, H + 1, 5000), "") == 0, "ohne Datenweg (soll 0): kein Hinweis");
  ist(strcmp(fc_ist_text(1, 14, H + 1, 5000), "Ist wird geladen …") == 0, "vor der ersten Antwort: wird geladen");
  fc_ist_ms = stempel(1000u);
  fc_ist_je = true;
  fc_r_act[0][9] = 0.4f;
  ist(strcmp(fc_ist_text(1, 14, H + 1, 1000 + 5 * MIN), "") == 0, "frische Antwort, Werte da: kein Hinweis");
  ist(strcmp(fc_ist_text(1, 14, H + 1, 1000 + 12 * MIN), "Ist unvollständig") == 0, "Antwort aelter 11 min");
  fc_ist_fehler = true;
  ist(strcmp(fc_ist_text(1, 14, H + 1, 1000 + MIN), "Ist unvollständig") == 0, "letzte Antwort Fehler");
  fc_ist_fehler = false;
  ist(strcmp(fc_ist_text(3, 14, H + 1, 1000 + MIN), "Ist unvollständig") == 0, "Dach 2 ohne fertige Stunde");
  ist(strcmp(fc_ist_text(3, 0, H, 1000 + MIN), "") == 0, "0 Uhr: keine fertige Stunde, kein Hinweis");
  ist(strcmp(fc_ist_text(3, 5, H, 1000 + MIN), "") == 0, "nachts ohne Wert und ohne erwarteten Ertrag: kein Hinweis");
  ist(strcmp(fc_ist_text(3, 14, -1, 1000 + MIN), "") == 0, "ohne Live-Schluessel: nur der Abrufstand");
  fc_ist_ms = 0;
  ist(strcmp(fc_ist_text(1, 14, H + 1, MIN), "Ist unvollständig") == 0, "nach dem Neuverbinden: unvollstaendig");
  // millis()-Ueberlauf: Abstand rechnet unsigned
  fc_ist_ms = 0xFFFFF000u;
  ist(strcmp(fc_ist_text(1, 14, H + 1, 0x00001000u), "") == 0, "millis-Ueberlauf");
  // Antwort und Neuzeichnen in derselben Millisekunde (ha_stat_today_set ->
  // fc_redraw): kein Hinweis, auch bei geradem millis() und bei 0
  for (const uint32_t j : {1000u, 1001u, 0u, 0xFFFFFFFFu}) {
    fc_ist_ms = stempel(j);
    ist(fc_ist_ms != 0, "Stempel nie 0 (0 = keine Antwort)");
    ist(strcmp(fc_ist_text(1, 14, H + 1, j), "") == 0, "Neuzeichnen in derselben Millisekunde");
    ist(strcmp(fc_ist_text(1, 14, H + 1, j + 1), "") == 0, "Neuzeichnen 1 ms spaeter");
  }

  printf("%d Fehler\n", fehler);
  return fehler ? 1 : 0;
}
"""


class LiveFuellungInCpp(unittest.TestCase):
    def test_rechnung_und_hinweis(self):
        gpp = shutil.which("g++")
        if not gpp:
            self.skipTest("kein g++")
        src = (PROGRAMM.replace("@FC_CUR_KW@", funktion("fc_cur_kw"))
               .replace("@FC_LIVE_TICK@", funktion("fc_live_tick"))
               .replace("@FC_VAL@", funktion("fc_val"))
               .replace("@FC_IST_TEXT@", funktion("fc_ist_text"))
               .replace("@STEMPEL@", stempel()))
        with tempfile.TemporaryDirectory() as d:
            c = Path(d) / "live.cpp"
            c.write_text(src, encoding="utf-8")
            for opt in ("-O0", "-O2"):
                with self.subTest(opt=opt):
                    exe = Path(d) / f"live{opt}"
                    r = subprocess.run([gpp, "-std=gnu++17", opt, "-Wall", str(c), "-o", str(exe)],
                                       capture_output=True, text=True)
                    self.assertEqual(r.returncode, 0, r.stderr[-2000:])
                    r = subprocess.run([str(exe)], capture_output=True, text=True)
                    self.assertEqual(r.returncode, 0, r.stdout)


class LiveFuellungImCode(unittest.TestCase):
    """Wo die Rechnung haengt: 1-s-Takt, Zeichnen, Texte."""

    def setUp(self):
        self.text = SEITE.read_text(encoding="utf-8")

    def test_takt_zeichnet_einmal_je_minute(self):
        m = re.search(r"\ninterval:\n((?:  [^\n]*\n|\n)+)\nlvgl:", self.text)
        self.assertIsNotNone(m)
        takt = m.group(1)
        self.assertNotIn("interval: 60s", takt)
        self.assertEqual(takt.count("- interval:"), 1)
        # erst summieren, dann beim Minutenwechsel genau ein fc_redraw
        a = takt.index("id(fc_live_tick)(t.day_of_year * 24 + t.hour, t.minute / 5, dt, id(fc_live_on));")
        b = takt.index("if (m == alt)")
        self.assertLess(a, b)
        self.assertEqual(takt.count(".execute()"), 1)
        self.assertIn("id(fc_redraw).execute();", takt)

    def test_balken_und_texte_ueber_fc_val(self):
        self.assertEqual(self.text.count("const float v = wert(k, h, hnow, HS);"), 1)
        self.assertIn("const float v = j >= L ? NAN : wert(k, h, hnow, HS);", self.text)
        self.assertIn("add(done, wert(k, h, hnow, HS));", self.text)
        self.assertIn("add(done, wert(k, hnow, hnow, HS) * (m % 60) / 60.0f);", self.text)
        self.assertEqual(self.text.count("const int HS = (id(fc_clock) < 0 && jetzt.is_valid()) ? "
                                         "jetzt.day_of_year * 24 + jetzt.hour : -1;"), 2)
        # Stil der laufenden Stunde bleibt halb deckend
        self.assertIn("lv_obj_set_style_bg_opa(bar, lauf ? LV_OPA_50 : LV_OPA_COVER, 0);", self.text)


if __name__ == "__main__":
    unittest.main()
