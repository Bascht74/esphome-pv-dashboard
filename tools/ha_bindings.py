#!/usr/bin/env python3
"""
Erzeugt den Datenweg von Home Assistant zum Panel aus EINER Zuordnungstabelle
(unten, TABELLE und GRUPPEN):

    python3 tools/ha_bindings.py            # Vorschau, schreibt nichts
    python3 tools/ha_bindings.py --write    # schreibt beide Dateien

    .pv-dashboard_ha.yaml         Paket fuer das Geraet (nur pv-dashboard.yaml
                                  bindet es ein, Simulator und Screenshots
                                  nicht)
    ha/pv_dashboard_dummy.yaml    Paket fuer Home Assistant: Ersatz-Entitaeten
                                  mit genau den Standard-IDs, zum Testen ohne
                                  die echten Integrationen

Beide Dateien werden nur von hier geschrieben -- Aenderungen gehoeren in die
Tabelle, danach --write. Die Vorschau meldet, ob die Dateien aktuell sind.

------------------------------------------------------------------------------
SO LAEUFT EIN WERT (docs/03, Abschnitt "Datenweg"):

1. SENSOR. Jede Zeile der Tabelle wird ein homeassistant-Sensor
   (sensor / text_sensor / binary_sensor) mit id ha_<name>,
   entity_id ${ha_<name>} und internal: true. Die entity_id steht als
   Substitution im Paket; eigene IDs gehoeren in .pv-dashboard_anlage.yaml
   (stechen die Standards, docs/03). Attribute lesen eigene Sensoren mit
   attribute:, sie teilen sich die Substitution der Entitaet.

2. DROSSELUNG. Ein neuer Wert ruft KEIN Seitenskript auf, er setzt nur das
   Bit seiner Gruppe(n) in ha_dirty. Ein Intervall von 1 s ruft je
   gesetztem Bit die Skripte der Gruppe einmal auf -- mit allen Werten der
   Gruppe. Damit zeichnet jede Gruppe hoechstens einmal je Sekunde neu,
   egal wie oft Home Assistant sendet (Shelly jede Sekunde, evcc alle paar
   Sekunden, zwanzig Werte auf einmal nach dem Verbinden).
   Uebersprungen wird eine Gruppe, deren Geraet laut dev_present fehlt, und
   eine, von der noch kein einziger Wert da ist (sonst stempelte sie
   data_seen, ohne dass Daten kamen).

3. REFERENZ UND "NICHT BELEGT" (Wunsch des Nutzers, 25.09.2026: keine
   zusaetzlichen Entitaeten, die Logik ergibt sich aus der Zuordnung).
   a) Jeder Platz der Anlage hat EINE Referenz-Entitaet aus der Tabelle
      (REFERENZ unten, z. B. Wallbox -> ihr Modus, Wechselrichter -> seine
      Leistung). Der Platz ist da, solange die Referenz einen gueltigen Wert
      hat (Zahl nicht NAN, Text nicht leer/unavailable/unknown). Faellt sie
      aus, verschwindet die ganze Grafik (Kasten, Werte, Leitungen, Kugeln),
      kommt ein Wert, erscheint sie wieder. dev_present liegt nicht im NVS
      und startet am Geraet mit 0.
   b) Jede Substitution ha_<name> darf none, false, off, null oder "" sein
      (Gross-/Kleinschreibung egal) = nicht belegt. Eine Jinja-Bedingung in
      der Substitution (ESPHome 2026.9, components/substitutions/jinja.py)
      setzt dann eine Ersatz-ID, die es nicht gibt, und eine Konstante
      B_<name> = false fuer den Code. Nicht belegte Referenz = Platz fehlt.
   c) Jeder andere Wert, der nicht belegt, nicht verfuegbar oder (10 s nach
      dem Verbinden) ohne Wert ist, wird LEER angezeigt statt mit Strichen:
      Zahlen als val_leer = -inf (fmt_num & Co. geben dafuer ""), Texte
      als " ". -inf bleibt auf jeder IEEE-754-Plattform (auch RISC-V) beim
      Kopieren und in den Rechenhilfen erhalten.
      Vor dem Verbinden bleiben die gewohnten Striche.

4. LISTEN. Was keine einzelne Entitaet ist, holt homeassistant.action mit
   capture_response und response_template: Home Assistant rechnet die
   Liste mit Jinja zu kurzen, kommagetrennten Reihen zusammen, das Panel
   verteilt sie auf die Skripte. Abruf 20 s nach dem Verbinden (Prognosen)
   bzw. 30 s (Statistik), danach Prognosen alle 30 min und Statistik zu
   jeder Stunde ab Minute 2 -- damit auch beim Tageswechsel.
   Voraussetzung in Home Assistant: beim ESPHome-Geraet die Option
   "Allow the device to perform Home Assistant actions" einschalten,
   sonst lehnt Home Assistant jede Aktion ab (on_error, Log "ha").

5. STEUERN (Wunsch des Nutzers, 25.09.2026). Der Modus-Schalter der Seite
   Wallboxen ruft wallbox_mode_set (.pv-dashboard_page_wallbox.yaml); das
   Paket haengt daran mit !extend select.select_option auf ${ha_wb<N>_mode}
   an. Welche Optionen gelten, liest es aus dem Attribut options der
   Entitaet: marq24/ha-evcc bietet off/smart/now (evcc mit alwaysCharge,
   ab Sommer 2026) oder off/pv/minpv/now (aelter), unter derselben ID.
   Nicht belegt oder Wallbox fehlt: kein Befehl. Nach 10 s bzw. bei einem
   Fehler zeichnet die Karte aus dem gemeldeten Zustand neu.

6. DUMMY. Fuer jede Standard-ID eine Ersatz-Entitaet in Home Assistant:
   Zahlen ueber input_number.pvd_<name> (von Hand verstellbar), Zaehler-
   staende laufen mit der Zeit hoch (fuer recorder.get_statistics), Texte
   und Zeitpunkte fest, dazu eine Template-Wetter-Entitaet mit Vorhersagen.

Kennzeichen in der Tabelle: [A] = Annahme bzw. Vorschlag (Name, Einheit oder
Vorzeichen nicht am eigenen Home Assistant geprueft), Quelle der Vorschlaege:
Recherche vom 25.09.2026 (datenweg/entitaeten.md im Claude-Projekt).
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIEL_PANEL = os.path.join(ROOT, ".pv-dashboard_ha.yaml")
ZIEL_HA = os.path.join(ROOT, "ha", "pv_dashboard_dummy.yaml")

# ---------------------------------------------------------------------------
# Plaetze der Anlage: Name -> Bit in dev_present (wie .pv-dashboard_ui.yaml)
# ---------------------------------------------------------------------------
PLAETZE = (
    [(f"pv_{i}", i - 1) for i in range(1, 9)]
    + [(f"inv_{k}", 7 + k) for k in range(1, 5)]
    + [(f"bat_{n}", 11 + n) for n in range(1, 4)]
    + [("wb_1", 15), ("wb_2", 16), ("heatpump", 17), ("meter_pv", 18), ("meter_house", 19)]
)

# Referenz je Platz: Name der Tabellenzeile, deren Wert "Geraet da" heisst
REFERENZ = dict(
    [(f"pv_{i}", f"pv{i}_power") for i in range(1, 9)]
    + [(f"inv_{k}", f"inv{k}_power") for k in range(1, 5)]
    + [(f"bat_{n}", f"bat{n}_soc") for n in range(1, 4)]
    + [("wb_1", "wb1_mode"), ("wb_2", "wb2_mode"),   # "WB-Status": Modus aus evcc
       ("heatpump", "hp_dhw"),                         # Warmwasser oben (Nilan)
       ("meter_pv", "meter_pv_power"), ("meter_house", "meter_house_power")]
)
FREI_WERTE = "['none', 'false', 'off', 'null', '']"
ERSATZ_ID = "sensor.pv_dashboard_nicht_belegt"


def frei(sub):
    """Jinja-Bedingung (ESPHome-Substitution): Substitution sub nicht belegt."""
    return f"({sub} | string | lower | trim) in {FREI_WERTE}"


def j_entity(sub):
    return f"${{ '{ERSATZ_ID}' if {frei(sub)} else {sub} }}"


def j_belegt(sub):
    return f"${{ 'false' if {frei(sub)} else 'true' }}"

# ---------------------------------------------------------------------------
# Gruppen: Bit in ha_dirty, Geraetemaske (0 = immer), Name, C++-Aufruf.
# Im Aufruf steht @name fuer den Wert: Zahl V(...) bzw. Text T(...) mit
# val_leer / " " fuer nicht belegt oder nicht verfuegbar, an/aus direkt.
# Hilfen im Intervall:
#   num(v, fmt, none)   fmt_num             when(iso, mit_tag)  ha_when
#   da(bit)             Geraet vorhanden    I(v, none)  gerundet, ohne Zahl -> none
#   pos(v)              max(v, 0)           add(a, b)  Summe, NAN zaehlt 0
#   neg(v)              -v                  sub(a, b)  a - b
#   jetzt               dash_time.now()     mul(v, f)  v * f
#   Rechnen nur ueber diese Hilfen: val_leer (-inf) bleibt darin leer und
#   -inf (ein leerer Summand macht die Summe leer), NAN bleibt NAN.
# ---------------------------------------------------------------------------
GRUPPEN = []


def gruppe(bit, maske, name, code):
    GRUPPEN.append({"bit": bit, "maske": maske, "name": name, "code": code.strip("\n")})


for i in range(8):
    n = i + 1
    gruppe(i, 1 << i, f"Flaeche {n}", f"""
id(pv_update).execute(-1, {i}, @pv{n}_power, @pv{n}_energy);
id(ov_roof).execute({i}, @pv{n}_power, @pv{n}_energy);""")
for k in range(4):
    n = k + 1
    gruppe(8 + k, 1 << (8 + k), f"Wechselrichter {n}", f"""
id(pv_update).execute({k}, -1, @inv{n}_power, @inv{n}_energy);
id(ov_inverter).execute({k}, @inv{n}_power, @inv{n}_energy);
id(pv_status).execute({k}, !@inv{n}_fault, @inv{n}_status, @inv{n}_temp);""")
for k in range(3):
    n = k + 1
    gruppe(12 + k, 1 << (12 + k), f"Speicher {n}", f"""
id(storage_update).execute({k}, @bat{n}_soc, @bat{n}_current, @bat{n}_cell_min, @bat{n}_cell_max, @bat{n}_temp_min, @bat{n}_temp_max, I(@bat{n}_cycles, -1));
id(ov_battery).execute({k}, @bat{n}_soc, @bat{n}_current, @bat{n}_voltage);
id(house_battery).execute({k}, @bat{n}_power, @bat{n}_soc);""")
gruppe(15, 7 << 12, "Speicher gesamt", """
id(ov_battery_total).execute(neg(@site_battery_power), @bat_charged_today, @bat_discharged_today);""")
for k in range(2):
    n = k + 1
    gruppe(16 + k, 1 << (15 + k), f"Wallbox {n}", f"""
{{
  const bool con = @wb{n}_connected, chg = @wb{n}_charging;
  const float kw = @wb{n}_power, kwh = @wb{n}_energy;
  const char *st = chg ? "Ladevorgang aktiv" : (con ? "Fahrzeug verbunden" : "Kein Fahrzeug");
  id(wallbox_update).execute({k}, @wb{n}_mode, chg, kw, I(@wb{n}_phases, 0), kwh, @wb{n}_solar, I(@wb{n}_minutes, -1),
                             con ? @wb{n}_vehicle : std::string(), std::string(st), @wb{n}_soc, @wb{n}_range,
                             @wb{n}_limit, when(@wb{n}_plan, true));
  id(ov_consumer).execute({2 + k}, mul(kw, 1000.0f), con ? num(kwh, "%.1f", "--,-") + " kWh" : std::string("frei"));
  id(house_loadpoint).execute({k}, mul(kw, 1000.0f), con ? @wb{n}_soc : NAN);
}}""")
gruppe(18, 3 << 15, "Wallboxen Monat", """
{
  const float e = @wb_month_energy, ct = @wb_month_price;
  id(wallbox_month).execute(e, @wb_month_solar, mul(mul(e, ct), 0.01f), ct);
}""")
gruppe(19, 1 << 17, "Waermepumpe", """
{
  const float kw = @hp_power;
  id(heatpump_update).execute(@hp_outdoor, @hp_room, @hp_humidity, NAN, @hp_dhw, @hp_eheat, I(@hp_fan, -1),
                              @hp_vent_mode, @hp_season, @hp_bypass, @hp_compressor, @hp_supply, @hp_exhaust,
                              kw, @hp_energy, I(@hp_alarm, 0));
  id(heatpump_extra).execute(@hp_room_set, @hp_dhw_set, @hp_fan_supply, @hp_fan_extract, I(@hp_filter_days, -1),
                             @hp_defrost, @hp_legionella);
  id(ov_consumer).execute(0, mul(kw, 1000.0f), "WW " + num(@hp_dhw, "%.0f", "--") + "°C");
  id(house_update).execute(0, mul(kw, 1000.0f), @hp_energy);
}""")
gruppe(20, 0, "Verbraucher", "\n".join(
    f"id(house_update).execute({d}, @dev{d}_power, @dev{d}_energy);" for d in range(1, 6)))
gruppe(21, 0, "Hausnetz", """
{
  const float bp = @site_battery_power, gp = @site_grid_power, home = @home_power;
  float lp = NAN;
  if (da(15))
    lp = add(lp, mul(@wb1_power, 1000.0f));
  if (da(16))
    lp = add(lp, mul(@wb2_power, 1000.0f));
  id(house_flow).execute(@site_pv_power, pos(bp), pos(gp), home, lp, pos(neg(bp)), pos(neg(gp)), @site_battery_soc,
                         @solcast_remaining, @tariff_grid, @tariff_home, @tariff_feedin);
  id(ov_house).execute(add(home, lp), @home_energy_today);
  const float hp = da(17) ? mul(@hp_power, 1000.0f) : NAN;
  // Sonstige = Verbrauch ohne Waermepumpe [A]
  id(ov_consumer).execute(1, std::isnan(home) ? home : add(home, neg(hp)),
                          "Basis " + num(mul(@dev5_power, 0.001f), "%.1f", "--,-"));
}""")
gruppe(22, 0, "Netz", """
id(grid_update).execute(@grid_power, @grid_freq, @grid_n_current);
id(ov_grid).execute(@grid_power);
""" + "\n".join(
    f"id(grid_phase).execute({p}, @grid_l{p + 1}_voltage, @grid_l{p + 1}_current, @grid_l{p + 1}_power, "
    f"@grid_l{p + 1}_apparent, @grid_l{p + 1}_pf);" for p in range(3)))
gruppe(23, 0, "Zaehler", "\n".join(
    f"id(grid_meter).execute({m}, @meter{m}_total, @meter{m}_today);" for m in range(5)) + """
if (da(18))
  id(ov_meter).execute(0, @meter_pv_power, @meter2_today);
if (da(19))
  id(ov_meter).execute(1, @meter_house_power, @meter4_today);""")
gruppe(24, 0, "Netzvorgaben", """
id(grid_rules).execute(@rule_limit, @spot_price, I(@neg_quarters, -1), @rule_neg_paid, @p14a_active, @p14a_kw,
                       @rule_smart_meter);""")
gruppe(25, 0, "Tageswerte", """
{
  // Volleinspeisung nur mit PV-Zaehler; ohne Hauszaehler ist der
  // Ueberschuss die Einspeisung am Hausanschluss ohne die Volleinspeisung [A]
  const float full = da(18) ? @meter2_today : 0.0f;
  const float feed = @meter1_today;
  const float surplus = da(19) ? @meter4_today : sub(feed, full);
  id(ov_totals).execute(@pv_energy_today, @home_energy_today, feed, @meter0_today, full, surplus, @solcast_remaining);
  id(money_update).execute(full, surplus, @selfuse_energy_today, @meter0_today);
}""")
gruppe(26, 0, "Prognose", """
{
  id(fc_today).execute(@solcast_today, @solcast_today_p10, @solcast_today_p90, @solcast_remaining,
                       @solcast_power_now, @solcast_next_hour, @solcast_peak, when(@solcast_peak_time, false),
                       when(@solcast_last_poll, false), I(@solcast_api_used, -1), I(@solcast_api_limit, -1));
  const float p50[7] = {@solcast_today, """ + ", ".join(f"@solcast_d{d}" for d in range(2, 8)) + """};
  const float p10[7] = {@solcast_today_p10, """ + ", ".join(f"@solcast_d{d}_p10" for d in range(2, 8)) + """};
  const float p90[7] = {@solcast_today_p90, """ + ", ".join(f"@solcast_d{d}_p90" for d in range(2, 8)) + """};
  for (int d = 0; d < 7; d++)
    id(fc_day).execute(d, id(ha_day_label)(d, jetzt), id(ha_wx_cond)[d], p50[d], p10[d], p90[d]);
}""")
gruppe(27, 0, "Wetter jetzt", """
{
  const auto &t = id(ha_wx_today);
  const auto &h = id(ha_wx_hour0);
  id(wx_now).execute(@weather, @wx_temp, t[0], t[1], @wx_humidity, @wx_pressure, @wx_wind, @wx_bearing, h[0], h[1],
                     t[2], @wx_sun, when(@sun_rising, false), when(@sun_setting, false), id(ha_wx_stamp));
}""")
gruppe(28, 0, "Wetterwarnung", """
id(wx_warning).execute(I(@warn_level, 0), @warn_text);""")

G = {g["name"]: g["bit"] for g in GRUPPEN}

# ---------------------------------------------------------------------------
# TABELLE. Eine Zeile je Sensor:
#   name   -> id ha_<name>, Substitution ha_<name> (ausser bei Attributen)
#   art    n Zahl, t Text, b an/aus, z Zaehlerstand (Zahl; im Dummy
#          laufend steigend, fuer recorder.get_statistics)
#   ent    Standard-entity_id; bei Attributen der Name der Zeile, deren
#          Entitaet gelesen wird
#   attr   Attribut oder None
#   gr     Gruppen (Bits)
#   einh   Einheit in Home Assistant (fuer den Dummy)
#   mul    Umrechnung auf dem Panel (filters: multiply) oder None
#   demo   Wert im Dummy (bei Zeitpunkten ein Jinja-Ausdruck)
#   hin    Kommentar
# ---------------------------------------------------------------------------
TABELLE = []


def z(name, art, ent, gr, einh="", demo=0, attr=None, mul=None, hin=""):
    TABELLE.append({"name": name, "art": art, "ent": ent, "attr": attr, "gr": gr,
                    "einh": einh, "mul": mul, "demo": demo, "hin": hin})


# --- Seite PV: Flaechen, Wechselrichter [A] --------------------------------
PV_DEMO = [(3412, 20.1), (2980, 19.2), (312, 2.0), (298, 2.0), (4120, 30.4), (3890, 29.1), (3650, 31.2), (0, 0.0)]
for i in range(1, 9):
    w, m = (i - 1) // 2 + 1, (i - 1) % 2 + 1
    z(f"pv{i}_power", "n", f"sensor.wr{w}_pv{m}_leistung", [i - 1], "W", PV_DEMO[i - 1][0],
      hin="W, Flaeche/Modul am Wechselrichter %d, MPPT %d [A]" % (w, m))
    z(f"pv{i}_energy", "n", f"sensor.wr{w}_pv{m}_ertrag_heute", [i - 1], "kWh", PV_DEMO[i - 1][1], hin="kWh heute [A]")
INV_DEMO = [(6214, 38.5, 41.5), (588, 3.9, 38.0), (7835, 58.2, 39.2), (5231, 46.4, 40.1)]
for k in range(1, 5):
    b = 7 + k
    z(f"inv{k}_power", "n", f"sensor.wr{k}_leistung", [b], "W", INV_DEMO[k - 1][0], hin="W [A]")
    z(f"inv{k}_energy", "n", f"sensor.wr{k}_ertrag_heute", [b], "kWh", INV_DEMO[k - 1][1], hin="kWh heute [A]")
    z(f"inv{k}_fault", "b", f"binary_sensor.wr{k}_stoerung", [b], demo=False, hin="an = Stoerung [A]")
    z(f"inv{k}_status", "t", f"sensor.wr{k}_status", [b], demo="Normal", hin="Fehlertext [A]")
    z(f"inv{k}_temp", "n", f"sensor.wr{k}_temperatur", [b], "°C", INV_DEMO[k - 1][2], hin="[A]")

# --- Speicher: das BMS kommt spaeter nativ ans Panel (docs/06); ueber Home
#     Assistant nur zum Testen [A] ---------------------------------------------
BAT_DEMO = [
    (72, 12.4, 53.2, 3.281, 3.302, 18, 21, 412, -660),
    (38, -8.9, 52.1, 3.195, 3.377, 19, 24, 398, 464),
    (100, 0.0, 54.4, 3.402, 3.411, 17, 19, 1287, 0),
]
for n in range(1, 4):
    b = 11 + n
    d = BAT_DEMO[n - 1]
    z(f"bat{n}_soc", "n", f"sensor.speicher{n}_soc", [b], "%", d[0])
    z(f"bat{n}_current", "n", f"sensor.speicher{n}_strom", [b], "A", d[1], hin="A, + = Laden [A]")
    z(f"bat{n}_voltage", "n", f"sensor.speicher{n}_spannung", [b], "V", d[2], hin="[A]")
    z(f"bat{n}_cell_min", "n", f"sensor.speicher{n}_zelle_min", [b], "V", d[3])
    z(f"bat{n}_cell_max", "n", f"sensor.speicher{n}_zelle_max", [b], "V", d[4])
    z(f"bat{n}_temp_min", "n", f"sensor.speicher{n}_temp_min", [b], "°C", d[5])
    z(f"bat{n}_temp_max", "n", f"sensor.speicher{n}_temp_max", [b], "°C", d[6])
    z(f"bat{n}_cycles", "n", f"sensor.speicher{n}_zyklen", [b], "", d[7])
    z(f"bat{n}_power", "n", f"sensor.speicher{n}_leistung", [b], "W", d[8], hin="W, + = Entladen [A]")
z("bat_charged_today", "n", "sensor.speicher_geladen_heute", [G["Speicher gesamt"]], "kWh", 12.3, hin="Helfer [A]")
z("bat_discharged_today", "n", "sensor.speicher_entladen_heute", [G["Speicher gesamt"]], "kWh", 18.5, hin="Helfer [A]")

# --- Hausnetz (evcc, marq24/ha-evcc) ------------------------------------------
HN = G["Hausnetz"]
z("site_pv_power", "n", "sensor.evcc_pv_power", [HN], "W", 13654, hin="W, PV im Hausnetz-Kreis")
z("site_battery_power", "n", "sensor.evcc_battery_power", [HN, G["Speicher gesamt"]], "W", -196,
  hin="W, + = Entladen (evcc)")
z("site_grid_power", "n", "sensor.evcc_grid_power", [HN], "W", -11340, hin="W, + = Bezug (evcc)")
z("home_power", "n", "sensor.evcc_home_power", [HN], "W", 932, hin="W, ohne Ladepunkte")
z("site_battery_soc", "n", "sensor.evcc_battery_soc", [HN], "%", 70)
z("tariff_grid", "n", "sensor.evcc_tariff_grid", [HN], "€/kWh", 0.30, mul=100, hin="EUR/kWh -> ct")
z("tariff_home", "n", "sensor.evcc_tariff_price_home", [HN], "€/kWh", 0.12, mul=100, hin="EUR/kWh -> ct")
z("tariff_feedin", "n", "sensor.evcc_tariff_feed_in", [HN], "€/kWh", 0.10, mul=100, hin="EUR/kWh -> ct")

# --- Ladepunkte (evcc; Ladepunkt-Titel "wallbox_1"/"wallbox_2" [A]) -----------
# Optionen der Modus-Entitaet (marq24/ha-evcc, pyevcc_ha/keys.py): aeltere
# evcc-Versionen MODE_PV_MINPV, mit alwaysCharge MODE_SMART. Der Dummy und
# die Probe nehmen die aeltere Liste; tests/ha_probe.py schaltet um.
MODUS_OPTIONEN_ALT = ["off", "pv", "minpv", "now"]
MODUS_OPTIONEN_NEU = ["off", "smart", "now"]
WB_DEMO = [
    ("pv", True, True, 7.4, 3, 12.8, 64, 104, "Kombi", 58, 212, 80, "{{ (today_at('07:00') + timedelta(days=1)).isoformat() }}"),
    ("off", False, False, 0.0, 0, 0.0, 0, 0, "", 0, 0, 100, "{{ none }}"),
]
for n in range(1, 3):
    g = [G[f"Wallbox {n}"]]
    lp = f"evcc_wallbox_{n}"
    d = WB_DEMO[n - 1]
    z(f"wb{n}_mode", "t", f"select.{lp}_mode", g, demo=d[0], hin="off/smart/now bzw. off/pv/minpv/now")
    z(f"wb{n}_mode_options", "t", f"wb{n}_mode", g, demo=str(MODUS_OPTIONEN_ALT), attr="options")
    z(f"wb{n}_charging", "b", f"binary_sensor.{lp}_charging", g, demo=d[1])
    z(f"wb{n}_connected", "b", f"binary_sensor.{lp}_connected", g, demo=d[2])
    z(f"wb{n}_power", "n", f"sensor.{lp}_charge_power", g + [HN], "kW", d[3], hin="kW")
    z(f"wb{n}_phases", "n", f"sensor.{lp}_phases_active", g, "", d[4])
    z(f"wb{n}_energy", "n", f"sensor.{lp}_session_energy", g, "kWh", d[5])
    z(f"wb{n}_solar", "n", f"sensor.{lp}_session_solar_percentage", g, "%", d[6])
    z(f"wb{n}_minutes", "n", f"sensor.{lp}_charge_duration", g, "min", d[7],
      hin="min (Anzeigeeinheit in Home Assistant, nativ s) [A]")
    z(f"wb{n}_vehicle", "t", f"select.{lp}_vehicle_name", g, demo=d[8])
    z(f"wb{n}_soc", "n", f"sensor.{lp}_vehicle_soc", g, "%", d[9])
    z(f"wb{n}_range", "n", f"sensor.{lp}_vehicle_range", g, "km", d[10])
    z(f"wb{n}_limit", "n", f"sensor.{lp}_effective_limit_soc", g, "%", d[11])
    z(f"wb{n}_plan", "t", f"sensor.{lp}_effective_plan_time", g, demo=d[12], hin="Zeitstempel -> \"Mo 07:00\"")
WM = [G["Wallboxen Monat"]]
z("wb_month_energy", "n", "sensor.evcc_stat30_charged_kwh", WM, "kWh", 182.4, hin="30 Tage, kein Kalendermonat")
z("wb_month_solar", "n", "sensor.evcc_stat30_solar_percentage", WM, "%", 71)
z("wb_month_price", "n", "sensor.evcc_stat30_avg_price", WM, "€/kWh", 0.214, mul=100, hin="EUR/kWh -> ct")

# --- Waermepumpe (Nilan Compact P, eigene Modbus-Sensoren [A]) ----------------
WP = [G["Waermepumpe"]]
for name, art, ent, einh, demo in [
    ("hp_outdoor", "n", "sensor.nilan_aussentemperatur", "°C", 12.4),
    ("hp_room", "n", "sensor.nilan_raumtemperatur", "°C", 21.6),
    ("hp_humidity", "n", "sensor.nilan_luftfeuchte", "%", 48),
    ("hp_dhw", "n", "sensor.nilan_warmwasser_oben", "°C", 51),
    ("hp_eheat", "b", "binary_sensor.nilan_zusatzheizung", "", False),
    ("hp_fan", "n", "sensor.nilan_lueftungsstufe", "", 2),
    ("hp_vent_mode", "t", "sensor.nilan_betriebsart", "", "Auto"),
    ("hp_season", "t", "sensor.nilan_jahreszeit", "", "Sommer"),
    ("hp_bypass", "t", "sensor.nilan_bypass", "", "Geschlossen"),
    ("hp_compressor", "t", "sensor.nilan_kompressor", "", "Warmwasser"),
    ("hp_supply", "n", "sensor.nilan_zuluft", "°C", 19.8),
    ("hp_exhaust", "n", "sensor.nilan_fortluft", "°C", 13.1),
    ("hp_power", "n", "sensor.waermepumpe_leistung", "kW", 0.62),
    ("hp_energy", "n", "sensor.waermepumpe_energie_heute", "kWh", 5.4),
    ("hp_alarm", "n", "sensor.nilan_alarm", "", 0),
    ("hp_room_set", "n", "sensor.nilan_raum_sollwert", "°C", 21),
    ("hp_dhw_set", "n", "sensor.nilan_warmwasser_sollwert", "°C", 50),
    ("hp_fan_supply", "n", "sensor.nilan_zuluftventilator", "%", 45),
    ("hp_fan_extract", "n", "sensor.nilan_abluftventilator", "%", 47),
    ("hp_filter_days", "n", "sensor.nilan_filter_tage", "d", 63),
    ("hp_defrost", "b", "binary_sensor.nilan_enteisung", "", False),
    ("hp_legionella", "b", "binary_sensor.nilan_legionellenschutz", "", False),
]:
    z(name, art, ent, WP + ([HN] if name == "hp_power" else []), einh, demo, hin="[A]")

# --- Verbraucher der Seite Haus (Steckdosen, Helfer [A]) ----------------------
VB = G["Verbraucher"]
for d, (geraet, w, kwh) in enumerate(
        [("backofen", 0, 1.2), ("waschmaschine", 0, 0.8), ("spuelmaschine", 0, 1.1), ("trockner", 0, 0.0),
         ("grundlast", 312, 7.5)], start=1):
    z(f"dev{d}_power", "n", f"sensor.{geraet}_leistung", [VB] + ([HN] if d == 5 else []), "W", w, hin="[A]")
    z(f"dev{d}_energy", "n", f"sensor.{geraet}_energie_heute", [VB], "kWh", kwh, hin="[A]")

# --- Netz (Shelly Pro 3EM, Geraetename "hausanschluss" [A]) --------------------
NZ = [G["Netz"]]
z("grid_power", "n", "sensor.hausanschluss_leistung", NZ, "W", -11340, hin="W, + = Bezug (total_act_power)")
z("grid_freq", "n", "sensor.hausanschluss_phase_a_frequenz", NZ, "Hz", 50.01, hin="ab Werk aus")
z("grid_n_current", "n", "sensor.hausanschluss_neutralleiterstrom", NZ, "A", 0.8, hin="ab Werk aus [A]")
for p, ph in enumerate("abc", start=1):
    z(f"grid_l{p}_voltage", "n", f"sensor.hausanschluss_phase_{ph}_spannung", NZ, "V", [231.2, 230.8, 232.0][p - 1])
    z(f"grid_l{p}_current", "n", f"sensor.hausanschluss_phase_{ph}_strom", NZ, "A", [16.4, 16.1, 16.9][p - 1])
    z(f"grid_l{p}_power", "n", f"sensor.hausanschluss_phase_{ph}_leistung", NZ, "W", [-3780, -3710, -3850][p - 1])
    z(f"grid_l{p}_apparent", "n", f"sensor.hausanschluss_phase_{ph}_scheinleistung", NZ, "VA",
      [3790, 3720, 3860][p - 1])
    z(f"grid_l{p}_pf", "n", f"sensor.hausanschluss_phase_{ph}_leistungsfaktor", NZ, "", -0.99)

# --- Zaehlwerke: Stand (auch fuer die Statistik) und heute --------------------
ZW = [G["Zaehler"]]
TW = G["Tageswerte"]
ZAEHLER = [
    # Stand-Entitaet, Tages-Helfer, Demo heute, Dummy-Zuwachs kWh/h
    ("sensor.hausanschluss_energie", "sensor.netz_bezug_heute", 3.4, 0.4),
    ("sensor.hausanschluss_zurueckgelieferte_energie", "sensor.netz_einspeisung_heute", 119.3, 5.0),
    ("sensor.pv_zaehler_einspeisung_gesamt", "sensor.pv_zaehler_einspeisung_heute", 88.7, 3.6),
    ("sensor.hauszaehler_bezug_gesamt", "sensor.hauszaehler_bezug_heute", 3.3, 0.4),
    ("sensor.hauszaehler_einspeisung_gesamt", "sensor.hauszaehler_einspeisung_heute", 30.6, 1.4),
]
ZW_NAME = ["Hausanschluss Bezug", "Hausanschluss Einspeisung", "PV-Zaehler Einspeisung", "Hauszaehler Bezug",
           "Hauszaehler Einspeisung"]
for m, (stand, heute, demo, rate) in enumerate(ZAEHLER):
    z(f"meter{m}_total", "z", stand, ZW, "kWh", rate, hin=f"kWh, {ZW_NAME[m]} [A]")
    z(f"meter{m}_today", "n", heute, ZW + [TW], "kWh", demo, hin="utility_meter-Helfer [A]")
z("meter_pv_power", "n", "sensor.pv_zaehler_leistung", ZW, "W", 6214, hin="W, + = Einspeisung [A]")
z("meter_house_power", "n", "sensor.hauszaehler_leistung", ZW, "W", 5126, hin="W, + = Einspeisung [A]")

# --- Netzvorgaben (Helfer [A]) ------------------------------------------------
NV = [G["Netzvorgaben"]]
z("rule_limit", "b", "input_boolean.einspeisegrenze_aktiv", NV, demo=True)
z("spot_price", "n", "sensor.boersenstrompreis", NV, "€/kWh", 0.087, mul=100, hin="EUR/kWh -> ct [A]")
z("neg_quarters", "n", "sensor.negative_viertelstunden_heute", NV, "", 0)
z("rule_neg_paid", "b", "input_boolean.neg_preis_verguetet", NV, demo=True)
z("p14a_active", "b", "binary_sensor.p14a_signal", NV, demo=False)
z("p14a_kw", "n", "input_number.p14a_grenze_kw", NV, "kW", 4.2)
z("rule_smart_meter", "b", "input_boolean.smart_meter_eingebaut", NV, demo=False)

# --- Tageswerte und Zaehlerstaende fuer die Statistik -------------------------
z("pv_energy_today", "n", "sensor.pv_erzeugung_heute", [TW], "kWh", 147.0, hin="Summe beider Kreise [A]")
z("home_energy_today", "n", "sensor.hausverbrauch_heute", [TW, HN], "kWh", 21.3, hin="[A]")
z("selfuse_energy_today", "n", "sensor.eigenverbrauch_heute", [TW], "kWh", 19.9, hin="[A]")
z("pv_energy_total", "z", "sensor.pv_erzeugung_gesamt", [], "kWh", 6.1, hin="nur Statistik [A]")
z("home_energy_total", "z", "sensor.hausverbrauch_gesamt", [], "kWh", 0.9, hin="nur Statistik [A]")

# --- Prognose (Solcast, deutsche IDs) -----------------------------------------
FC = [G["Prognose"]]
SC = "sensor.solcast_pv_forecast_"
z("solcast_today", "n", SC + "prognose_heute", FC, "kWh", 155.0)
z("solcast_today_p10", "n", "solcast_today", FC, demo=128.4, attr="estimate10")
z("solcast_today_p90", "n", "solcast_today", FC, demo=171.9, attr="estimate90")
z("solcast_remaining", "n", SC + "prognose_verbleibende_leistung_heute", FC + [TW, HN], "kWh", 12.6)
z("solcast_power_now", "n", SC + "aktuelle_leistung", FC, "W", 9600)
z("solcast_next_hour", "n", SC + "prognose_nachste_stunde", FC, "Wh", 7100, mul=0.001, hin="Wh -> kWh")
z("solcast_peak", "n", SC + "prognose_spitzenleistung_heute", FC, "W", 22000, mul=0.001, hin="W -> kW")
z("solcast_peak_time", "t", SC + "zeitpunkt_spitzenleistung_heute", FC, demo="{{ today_at('13:00').isoformat() }}")
z("solcast_last_poll", "t", SC + "zeitpunkt_letzter_api_abruf", FC,
  demo="{{ now().replace(minute=0, second=0, microsecond=0).isoformat() }}")
z("solcast_api_used", "n", SC + "verwendete_api_abrufe", FC, "", 6)
z("solcast_api_limit", "n", SC + "max_api_abrufe", FC, "", 10)
FC_DEMO = [(171.2, 150.3, 180.6), (48.6, 22.1, 90.4), (72.3, 41.0, 118.2), (121.8, 80.5, 152.7),
           (66.0, 30.2, 124.9), (158.4, 112.0, 175.3)]
for d in range(2, 8):
    ent = SC + ("prognose_morgen" if d == 2 else f"prognose_tag_{d}")
    p50, p10, p90 = FC_DEMO[d - 2]
    z(f"solcast_d{d}", "n", ent, FC, "kWh", p50, hin="ab Tag 3 ab Werk aus" if d == 3 else "")
    z(f"solcast_d{d}_p10", "n", f"solcast_d{d}", FC, demo=p10, attr="estimate10")
    z(f"solcast_d{d}_p90", "n", f"solcast_d{d}", FC, demo=p90, attr="estimate90")

# --- Wetter (DWD; Station und Warnzelle sind Platzhalter [A]) -----------------
WX = [G["Wetter jetzt"]]
z("weather", "t", "weather.dwd_station", WX, demo="partlycloudy", hin="Zustand = Lage")
z("wx_temp", "n", "weather", WX, demo=16.8, attr="temperature")
z("wx_humidity", "n", "weather", WX, demo=62, attr="humidity")
z("wx_pressure", "n", "weather", WX, demo=1016, attr="pressure")
z("wx_wind", "n", "weather", WX, demo=12, attr="wind_speed")
z("wx_bearing", "n", "weather", WX, demo=240, attr="wind_bearing")
z("wx_sun", "n", "sensor.dwd_station_sonnenscheindauer_heute", WX, "s", 22320, mul=1 / 3600,
  hin="s -> h, ab Werk aus")
z("sun", "t", "sun.sun", [], hin="nur fuer die Attribute (Integration sun)")
z("sun_rising", "t", "sun", WX, attr="next_rising")
z("sun_setting", "t", "sun", WX, attr="next_setting")
WW = [G["Wetterwarnung"]]
z("warn_level", "n", "sensor.dwd_warnzelle_aktuelle_warnstufe", WW, "", 1, hin="0..4")
z("warn_text", "t", "warn_level", WW, demo="Windboeen bis 18 Uhr", attr="warning_1_headline")

NAMEN = {e["name"]: e for e in TABELLE}


def entitaet(e):
    """Substitution und Standard-ID einer Zeile (Attribute: die der Basis)."""
    if e["attr"]:
        return entitaet(NAMEN[e["ent"]])
    return "ha_" + e["name"], e["ent"]


# ---------------------------------------------------------------------------
# Jinja fuer response_template. Keine Zeile darf mit '#' beginnen und kein
# "<%" oder "${...}" ausser den gewollten Substitutionen enthalten: ESPHome
# liest solche Strings sonst selbst als Jinja (substitutions/jinja.py).
# Home Assistant rendert mit strict=True -- jeder fehlende Schluessel ist ein
# Fehler (on_error), deshalb ueberall .get() und Pruefung auf number.
# ---------------------------------------------------------------------------
def j_n(ausdruck, runden=None):
    r = f" | round({runden})" if runden is not None else ""
    return f"(({ausdruck}){r}) if ({ausdruck}) is number else 'nan'"


JINJA_STUNDE = """
{%- set ns = namespace(l=[]) -%}
{%- for x in response['${ha_weather}'].forecast -%}
{%- if as_datetime(x.datetime) > now() -%}
{%- set ns.l = ns.l + [x] -%}
{%- endif -%}
{%- endfor -%}
{%- set o = namespace(h=[], c=[], t=[], r=[], p=[]) -%}
{%- for k in range(12) -%}
{%- set a = ns.l[2 * k] if ns.l | length > 2 * k else {} -%}
{%- set b = ns.l[2 * k + 1] if ns.l | length > 2 * k + 1 else {} -%}
{%- set ra = a.get('precipitation') -%}
{%- set rb = b.get('precipitation') -%}
{%- set pp = [a.get('precipitation_probability'), b.get('precipitation_probability')] | select('number') | list -%}
{%- set o.h = o.h + [as_local(as_datetime(a.datetime)).hour if a.get('datetime') else -1] -%}
{%- set o.c = o.c + [a.get('condition') or ''] -%}
{%- set o.t = o.t + [TEMP] -%}
{%- set o.r = o.r + [(((ra if ra is number else 0) + (rb if rb is number else 0)) | round(1)) if (ra is number or rb is number) else 'nan'] -%}
{%- set o.p = o.p + [(pp | max) if pp else 'nan'] -%}
{%- endfor -%}
{%- set f = ns.l[0] if ns.l else {} -%}
{{ {'h': o.h | join(','), 'c': o.c | join(','), 't': o.t | join(','), 'r': o.r | join(','), 'p': o.p | join(','), 'g': (GUST) | string, 'w': (CLOUD) | string} | tojson }}
""".replace("TEMP", j_n("a.get('temperature')", 1)).replace(
    "GUST", j_n("f.get('wind_gust_speed')", 1)).replace("CLOUD", j_n("f.get('cloud_coverage')", 0)).strip("\n")

JINJA_TAG = """
{%- set o = namespace(d=[], c=[], hi=[], lo=[], r=[], p=[], s=[], w=[]) -%}
{%- for x in response['${ha_weather}'].forecast -%}
{%- set d = (as_local(as_datetime(x.datetime)).date() - now().date()).days -%}
{%- if 0 <= d < 7 -%}
{%- set o.d = o.d + [d] -%}
{%- set o.c = o.c + [x.get('condition') or ''] -%}
{%- set o.hi = o.hi + [HI] -%}
{%- set o.lo = o.lo + [LO] -%}
{%- set o.r = o.r + [RAIN] -%}
{%- set o.p = o.p + [PROB] -%}
{%- set o.s = o.s + [SUN] -%}
{%- set o.w = o.w + [WIND] -%}
{%- endif -%}
{%- endfor -%}
{{ {'d': o.d | join(','), 'c': o.c | join(','), 'hi': o.hi | join(','), 'lo': o.lo | join(','), 'r': o.r | join(','), 'p': o.p | join(','), 's': o.s | join(','), 'w': o.w | join(',')} | tojson }}
""".replace("HI", j_n("x.get('temperature')", 1)).replace("LO", j_n("x.get('templow')", 1)).replace(
    "RAIN", j_n("x.get('precipitation')", 1)).replace("PROB", j_n("x.get('precipitation_probability')", 0)).replace(
    "SUN", j_n("x.get('sun_duration')", 0)).replace("WIND", j_n("x.get('wind_speed')", 0)).strip("\n")


def jinja_solcast(quelle):
    return ("{%- set src = " + quelle + " -%}\n" + """
{%- set o = namespace(a=['nan'] * 48, b=['nan'] * 48, c=['nan'] * 48) -%}
{%- for x in src -%}
{%- set ps = x.get('period_start') -%}
{%- set t = as_local(as_datetime(ps) if ps is string else ps) if ps else none -%}
{%- if t and t.date() == now().date() -%}
{%- set i = t.hour * 2 + t.minute // 30 -%}
{%- set o.a = o.a[:i] + [A] + o.a[i + 1:] -%}
{%- set o.b = o.b[:i] + [B] + o.b[i + 1:] -%}
{%- set o.c = o.c[:i] + [C] + o.c[i + 1:] -%}
{%- endif -%}
{%- endfor -%}
{{ {'a': o.a | join(','), 'b': o.b | join(','), 'c': o.c | join(',')} | tojson }}
""".replace("[A]", "[" + j_n("x.get('pv_estimate')", 2) + "]").replace(
        "[B]", "[" + j_n("x.get('pv_estimate10')", 2) + "]").replace(
        "[C]", "[" + j_n("x.get('pv_estimate90')", 2) + "]")).strip("\n")


JINJA_SOLCAST = jinja_solcast("response.get('data') or []")
JINJA_SOLCAST_ATTR = jinja_solcast("state_attr('${ha_solcast_today}', 'detailedForecast') or []")

# Statistik: je Zeitraum Start, Anzahl Plaetze, Index eines Eintrags,
# Zeitraum als Text, Beschriftungen, Periode
STAT_REIHEN = [("p", "${ha_pv_energy_total}"), ("c", "${ha_home_energy_total}"),
               ("i", "${ha_meter0_total}"), ("e", "${ha_meter1_total}"), ("f", "${ha_meter2_total}")]
MONATE = "['Januar', 'Februar', 'Maerz', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', " \
         "'November', 'Dezember']"
ZEITRAEUME = [
    {"range": 0, "name": "Woche", "period": "day",
     "t0": "today_at('00:00') - timedelta(days=now().weekday())", "n": "7",
     "idx": "(s.date() - t0.date()).days",
     "per": "t0.strftime('%d.%m.') ~ ' bis ' ~ (t0 + timedelta(days=6)).strftime('%d.%m.%Y')",
     "lab": "'Mo,Di,Mi,Do,Fr,Sa,So'"},
    {"range": 1, "name": "Monat", "period": "day",
     "t0": "today_at('00:00').replace(day=1)",
     "n": "((t0.replace(day=28) + timedelta(days=4)).replace(day=1) - t0).days",
     "idx": "s.day - 1 if s.month == t0.month else -1",
     "per": MONATE + "[t0.month - 1] ~ ' ' ~ t0.year",
     "lab": "range(1, n + 1) | join(',')"},
    {"range": 2, "name": "Jahr", "period": "month",
     "t0": "today_at('00:00').replace(month=1, day=1)", "n": "12",
     "idx": "s.month - 1 if s.year == t0.year else -1",
     "per": "t0.year | string",
     "lab": "'J,F,M,A,M,J,J,A,S,O,N,D'"},
]


def jinja_reihe(schluessel, sid, idx, n="n"):
    return f"""
{{%- set o_{schluessel} = namespace(l=[0] * {n}) -%}}
{{%- for e in response.statistics.get('{sid}', []) -%}}
{{%- set s = as_local(as_datetime(e.start) if e.start is string else e.start) -%}}
{{%- set i = {idx} -%}}
{{%- if 0 <= i < {n} and e.change is number -%}}
{{%- set o_{schluessel}.l = o_{schluessel}.l[:i] + [e.change | round(2)] + o_{schluessel}.l[i + 1:] -%}}
{{%- endif -%}}
{{%- endfor -%}}""".strip("\n")


def jinja_statistik(zr):
    teile = [f"{{%- set t0 = {zr['t0']} -%}}", f"{{%- set n = {zr['n']} -%}}"]
    teile += [jinja_reihe(k, sid, zr["idx"]) for k, sid in STAT_REIHEN]
    aus = ", ".join(f"'{k}': o_{k}.l | join(',')" for k, _ in STAT_REIHEN)
    teile.append(f"{{{{ {{'per': {zr['per']}, 'lab': {zr['lab']}, {aus}}} | tojson }}}}")
    return "\n".join(teile)


STUNDEN_T0 = "now().replace(minute=0, second=0, microsecond=0) - timedelta(hours=23)"
JINJA_STUNDEN = "\n".join([
    f"{{%- set t0 = {STUNDEN_T0} -%}}",
    "{%- set n = 24 -%}",
    jinja_reihe("h", "${ha_home_energy_total}", "((s - t0).total_seconds() // 3600) | int"),
    jinja_reihe("i", "${ha_meter0_total}", "((s - t0).total_seconds() // 3600) | int"),
    jinja_reihe("v", "${ha_pv_energy_total}", "s.hour - 6 if s.date() == now().date() else -1", "16"),
    "{%- set sol = namespace(l=[]) -%}",
    "{%- for k in range(24) -%}",
    "{%- set sol.l = sol.l + [([o_h.l[k] - o_i.l[k], 0] | max) | round(2)] -%}",
    "{%- endfor -%}",
    "{{ {'home': o_h.l | join(','), 'solar': sol.l | join(','), 'hour': now().hour, 'dc': o_v.l | join(',')}"
    " | tojson }}",
])


# ---------------------------------------------------------------------------
# Paket fuer das Geraet
# ---------------------------------------------------------------------------
def basis(e):
    """Name der Zeile, deren Substitution gilt (bei Attributen die Basis)."""
    return basis(NAMEN[e["ent"]]) if e["attr"] else e["name"]


def c_code(code):
    """@name -> V(...) / T(...) / Zustand; unbekannte Namen sind ein Fehler."""
    def ers(m):
        name = m.group(1)
        if name not in NAMEN:
            sys.exit(f"Fehler: @{name} steht in einer Gruppe, aber nicht in der Tabelle")
        e = NAMEN[name]
        b = "B_" + basis(e)
        if e["art"] == "b":
            return f"id(ha_{name}).state"
        if e["art"] == "t":
            return f"T(id(ha_{name}), {b})"
        return f"V(id(ha_{name}), {b})"
    return re.sub(r"@([a-z0-9_]+)", ers, code)


def belegt_namen(code):
    """Basisnamen, deren B_-Konstante ein Aufruf braucht."""
    return {basis(NAMEN[n]) for n in re.findall(r"@([a-z0-9_]+)", code) if NAMEN[n]["art"] != "b"}


def einr(text, n):
    pad = " " * n
    return "\n".join((pad + z) if z.strip() else "" for z in text.split("\n"))


def antwort_kopf(was):
    """Gemeinsamer Anfang jedes on_success: Antwort als Objekt, auch wenn
    Home Assistant sie als Text liefert (literal_eval gescheitert)."""
    return f"""const bool txt = response["response"].is<const char *>();
JsonDocument doc = txt ? json::parse_json(std::string(response["response"].as<const char *>())) : JsonDocument();
JsonObjectConst r = txt ? doc.as<JsonObjectConst>() : response["response"].as<JsonObjectConst>();
if (r.isNull()) {{
  ESP_LOGW("ha", "{was}: Antwort ohne Inhalt");
  return;
}}
auto S = [&r](const char *k) -> std::string {{
  const char *v = r[k].as<const char *>();
  return v ? std::string(v) : std::string();
}};
auto &L = id(ha_split);
auto F = [](const std::vector<std::string> &v, size_t i) -> float {{
  return (i < v.size() && !v[i].empty()) ? strtof(v[i].c_str(), nullptr) : NAN;
}};"""


def aktion(action, data, data_template, template, erfolg, was, fehler_extra=None, tief=6):
    """Ein homeassistant.action-Block als YAML (Einrueckung tief)."""
    z_ = [f"- homeassistant.action:", f"    action: {action}"]
    if data:
        z_.append("    data:")
        z_ += [f"      {k}: {v}" for k, v in data]
    if data_template:
        z_.append("    data_template:")
        z_ += [f"      {k}: \"{v}\"" for k, v in data_template]
    z_.append("    capture_response: true")
    z_.append("    response_template: |-")
    z_.append(einr(template, 6))
    z_.append("    on_success:")
    z_.append("      - lambda: |-")
    z_.append(einr(antwort_kopf(was) + "\n" + erfolg.strip("\n"), 10))
    z_.append("    on_error:")
    if fehler_extra:
        z_.append(einr(fehler_extra, 6))
    else:
        z_.append(f"      - lambda: 'ESP_LOGW(\"ha\", \"{was}: %s\", error.c_str());'")
    return einr("\n".join(z_), tief)


ERFOLG_STUNDE = """
const auto h = L(S("h")), c = L(S("c")), t = L(S("t")), rr = L(S("r")), p = L(S("p"));
for (int k = 0; k < 12; k++) {
  const int hour = (size_t) k < h.size() ? atoi(h[k].c_str()) : -1;
  if (hour < 0)
    continue;
  id(wx_hour).execute(k, hour, (size_t) k < c.size() ? c[k] : std::string(), F(t, k), F(rr, k), F(p, k));
}
id(ha_wx_hour0)[0] = strtof(S("g").c_str(), nullptr);
id(ha_wx_hour0)[1] = strtof(S("w").c_str(), nullptr);
id(ha_dirty) |= 1u << 27;"""

ERFOLG_TAG = """
const auto d = L(S("d")), c = L(S("c")), hi = L(S("hi")), lo = L(S("lo")), rr = L(S("r")), p = L(S("p")),
           s = L(S("s")), w = L(S("w"));
ESPTime jetzt = id(dash_time).now();
for (size_t k = 0; k < d.size(); k++) {
  const int tag = atoi(d[k].c_str());
  if (tag < 0 || tag > 6)
    continue;
  const std::string lage = k < c.size() ? c[k] : std::string();
  // sun_duration in Sekunden [A], nur mit der DWD-Option fuer Zusatzwerte
  id(wx_day).execute(tag, id(ha_day_label)(tag, jetzt), lage, F(hi, k), F(lo, k), F(rr, k), F(p, k),
                     F(s, k) / 3600.0f, F(w, k));
  id(ha_wx_cond)[tag] = lage;
  if (tag == 0)
    id(ha_wx_today) = {F(hi, k), F(lo, k), F(rr, k)};
}
id(ha_wx_stamp) = jetzt.is_valid() ? jetzt.strftime("%H:%M") : std::string();
id(ha_dirty) |= (1u << 26) | (1u << 27);"""

ERFOLG_SOLCAST = """
id(fc_slots).execute(S("a"), S("b"), S("c"));
// Tagesreihe Prognose (06..22 Uhr, kWh je Stunde) aus den Halbstunden
const auto &p = id(fc_p50);
char buf[128];
int n = 0;
for (int h = 6; h < 22 && n >= 0 && n < (int) sizeof(buf); h++) {
  float v = (p[2 * h] + p[2 * h + 1]) * 0.5f;
  v = std::isfinite(v) ? std::clamp(v, 0.0f, 999.0f) : 0.0f;
  n += snprintf(buf + n, sizeof(buf) - n, h > 6 ? ",%.2f" : "%.2f", v);
}
if (id(forecast_curve).state != buf)
  id(forecast_curve).make_call().set_value(buf).perform();"""


def erfolg_statistik(rng):
    return f"""
const std::string P = S("p"), C = S("c"), I = S("i"), E = S("e"), Fv = S("f");
auto sum = [](const std::string &s) -> float {{
  float t = 0.0f;
  for (const auto &x : id(ha_split)(s))
    t += x.empty() ? 0.0f : strtof(x.c_str(), nullptr);
  return t;
}};
// Ertrag wie money_update: Volleinspeisung, Ueberschuss (Einspeisung ohne
// Volleinspeisung), Eigenverbrauch (Erzeugung ohne Einspeisung) als
// Ersparnis, abzueglich Bezug [A]
const float f = (id(dev_present) & (1u << 18)) ? sum(Fv) : 0.0f;
const float p = sum(P), e = sum(E), i = sum(I);
const float money = (f * ${{tarif_volleinspeisung_ct}} + (e - f) * ${{tarif_ueberschuss_ct}} +
                     (p - e) * ${{tarif_bezug_ct}} - i * ${{tarif_bezug_ct}}) / 100.0f;
id(stats_update).execute({rng}, S("per"), S("lab"), P, C, I, E, money);"""


ERFOLG_STUNDEN = """
id(house_history).execute(S("home"), S("solar"), r["hour"].as<int>());
// Tagesreihe Erzeugung (06..22 Uhr) aus der Statistik; record_hour schreibt
// zur vollen Stunde weiter seine 0 in die abgelaufene Stunde, die Statistik
// dieser Stunde kommt ab Minute 2 hier an und ersetzt sie.
const std::string dc = S("dc");
const ESPTime jetzt = id(dash_time).now();
if (!dc.empty() && jetzt.is_valid() && dc != id(day_curve).state) {
  id(curve_day) = jetzt.year * 1000 + jetzt.day_of_year;
  id(day_curve).make_call().set_value(dc).perform();
}"""


MODUS_SET = '''
  # Modus-Schalter der Seite Wallboxen: wallbox_mode_set
  # (.pv-dashboard_page_wallbox.yaml) laesst den getippten Teil leuchten;
  # hier kommt der Befehl an evcc dazu (!extend: die Schritte laufen nach
  # denen der Seite). Nicht belegt oder Wallbox nicht da: nichts.
  # Optionen nach marq24/ha-evcc (pyevcc_ha/keys.py): MODE_SMART
  # off/smart/now, wenn evcc alwaysCharge kennt, sonst MODE_PV_MINPV
  # off/pv/minpv/now -- beide unter derselben ID. Smart heisst dann "pv"
  # (evcc hat pv in smart umbenannt). Welche Liste gilt, steht im Attribut
  # options; fehlt es, entscheidet der gemeldete Modus, sonst "smart".
  # Faellt die Aktion durch (Option unbekannt, Aktionen in Home Assistant
  # nicht erlaubt) oder meldet evcc nach 10 s nichts Neues, zeichnet die
  # Karte aus dem gemeldeten Zustand neu.
  - id: !extend wallbox_mode_set
    then:
      - if:
          condition:
            lambda: |-
              constexpr bool B[2] = {%(b1)s, %(b2)s};
              return wb >= 0 && wb <= 1 && seg >= 0 && seg <= 2 && B[wb] && ((id(dev_present) >> (15 + wb)) & 1u);
          then:
            - homeassistant.action:
                action: select.select_option
                data:
                  entity_id: !lambda 'return std::string(wb == 0 ? "${ha_wb1_mode}" : "${ha_wb2_mode}");'
                  option: !lambda |-
                    if (seg == 0)
                      return std::string("off");
                    if (seg == 2)
                      return std::string("now");
                    const auto *o = wb == 0 ? id(ha_wb1_mode_options) : id(ha_wb2_mode_options);
                    const auto *m = wb == 0 ? id(ha_wb1_mode) : id(ha_wb2_mode);
                    if (o->has_state() && o->state.find("smart") != std::string::npos)
                      return std::string("smart");
                    if (o->has_state() && o->state.find("pv") != std::string::npos)
                      return std::string("pv");
                    if (m->has_state() && (m->state == "pv" || m->state == "minpv"))
                      return std::string("pv");
                    return std::string("smart");
                on_error:
                  - lambda: |-
                      ESP_LOGW("ha", "select.select_option Wallbox %%d: %%s", wb + 1, error.c_str());
                      id(wb_mode_pending)[wb] = -1;
                      id(ha_dirty) |= 0x%(dirty)08Xu;
            - delay: 10s
            - lambda: 'id(ha_dirty) |= 0x%(dirty)08Xu;'
'''


def panel_bauen():
    out = []
    w = out.append
    w("""##############################################################################
# Package: Datenweg von Home Assistant (nur Geraet)
#
# ERZEUGT von tools/ha_bindings.py -- nicht von Hand aendern. Die Zuordnung
# steht als Tabelle im Werkzeug; nach einer Aenderung dort
#
#     python3 tools/ha_bindings.py --write
#
# Eingebunden nur von pv-dashboard.yaml (Liste files: des Fernpakets bzw.
# lokaler Rueckfallblock). Simulator und Screenshot-Lauf binden es NICHT
# ein: Sie haben keine API-Verbindung.
#
# Voraussetzung in Home Assistant: Einstellungen > Geraete & Dienste >
# ESPHome > dieses Geraet > Optionen > "Allow the device to perform Home
# Assistant actions" einschalten. Ohne die Option lehnt Home Assistant jede
# homeassistant.action ab; Prognosen, Stundenwerte und Statistik bleiben dann
# auf Strichen (Log "ha").
#
# Ablauf (docs/03, Abschnitt "Datenweg"):
#   - Jeder Wert ist ein homeassistant-Sensor mit id ha_<name> und der
#     entity_id ${ha_<name>}. Die Standards stehen unten unter
#     substitutions; eigene IDs gehoeren in .pv-dashboard_anlage.yaml und
#     stechen diese Standards.
#   - Drosselung: Ein neuer Wert setzt nur das Bit seiner Gruppe in
#     ha_dirty. Das Intervall (1 s) ruft je Gruppe die Seitenskripte
#     hoechstens einmal je Sekunde auf, mit allen Werten der Gruppe.
#     Gruppen fehlender Geraete (dev_present) und Gruppen ohne jeden Wert
#     ueberspringt es.
#   - Referenz: Je Geraeteplatz eine der Entitaeten (Liste unter
#     substitutions). Hat sie einen gueltigen Wert, ist das Geraet da; sonst
#     verschwindet seine ganze Grafik (dev_present, dev_apply). dev_present
#     startet leer und bleibt nicht ueber einen Neustart.
#   - Jede andere Entitaet, die nicht belegt (none/false/off/""), nicht
#     verfuegbar oder 10 s nach dem Verbinden ohne Wert ist, zeigt ihren Wert
#     leer statt mit Strichen (val_leer bzw. " "). Vor dem Verbinden: Striche.
#   - Listen (Wetter stuendlich und taeglich, Solcast-Halbstunden,
#     Statistik, Hausverbrauch 24 h) holt homeassistant.action mit
#     capture_response; die Jinja-Vorlage rechnet sie in Home Assistant auf
#     kurze Reihen zusammen. Abruf 20 s / 30 s nach dem Verbinden, dann
#     Prognosen alle 30 min, Statistik stuendlich ab Minute 2.
#   - Steuern: Der Modus-Schalter der Seite Wallboxen (wallbox_mode_set)
#     schickt select.select_option an ${ha_wb<N>_mode}, Optionen nach
#     dem Attribut options (off/smart/now oder off/pv/minpv/now).
#
# [A] = vorgeschlagene ID bzw. Annahme, am eigenen Home Assistant pruefen
# (Einstellungen > Entitaeten). Zum Testen ohne die Integrationen:
# ha/pv_dashboard_dummy.yaml (legt genau diese IDs an).
##############################################################################
""")
    # --- substitutions
    w("substitutions:")
    w("  # dev_present startet leer; die Referenzen (s. u.) melden die Geraete.\n"
      "  # Sticht den Wert aus .pv-dashboard_ui.yaml (Simulator: alles da).")
    w('  dev_present_start: "0u"')
    w("  # Jede ID darf none, false, off, null oder \"\" sein = nicht belegt.\n"
      "  # Referenz je Geraet (nicht verfuegbar oder nicht belegt = Geraet weg):")
    for platz, bit in PLAETZE:
        w(f"  #   {platz:<12} ha_{REFERENZ[platz]}")
    gesehen = set()
    for e in TABELLE:
        if e["attr"]:
            continue
        sub, ent = entitaet(e)
        if sub in gesehen:
            continue
        gesehen.add(sub)
        hin = f"  # {e['hin']}" if e["hin"] else ""
        w(f"  {sub}: {ent}{hin}")
    w("")
    # --- globals
    w("""globals:
  # Gruppen mit neuen Werten, ein Bit je Gruppe (Liste in
  # tools/ha_bindings.py, GRUPPEN); das Intervall unten leert es
  - id: ha_dirty
    type: uint32_t
    restore_value: false
    initial_value: '0'
  # 10 s nach dem Verbinden: Wer jetzt noch keinen Wert hat, bekommt keinen
  # mehr -- ab da leer statt Striche
  - id: ha_ready
    type: bool
    restore_value: false
    initial_value: 'false'
  # Aus den Vorhersagen (weather.get_forecasts): heute Hoechst, Tiefst,
  # Regen; naechste Stunde Boeen, Bewoelkung; Lage je Tag fuer fc_day;
  # Uhrzeit des Abrufs
  - id: ha_wx_today
    type: std::array<float, 3>
    restore_value: false
    initial_value: '{NAN, NAN, NAN}'
  - id: ha_wx_hour0
    type: std::array<float, 2>
    restore_value: false
    initial_value: '{NAN, NAN}'
  - id: ha_wx_cond
    type: std::array<std::string, 7>
    restore_value: false
  - id: ha_wx_stamp
    type: std::string
    restore_value: false
  # "a,b,c" -> {"a", "b", "c"}
  - id: ha_split
    type: std::function<std::vector<std::string>(const std::string &)>
    restore_value: false
    initial_value: |-
      [](const std::string &s) -> std::vector<std::string> {
        std::vector<std::string> v;
        if (s.empty())
          return v;
        size_t a = 0;
        while (true) {
          const size_t b = s.find(',', a);
          v.push_back(s.substr(a, b == std::string::npos ? std::string::npos : b - a));
          if (b == std::string::npos)
            break;
          a = b + 1;
        }
        return v;
      }
  # Zeitstempel von Home Assistant ("2026-09-25T04:12:00+00:00") in
  # Ortszeit: "HH:MM" bzw. mit Tag "Mo 07:00"; leer, wenn er nicht passt
  - id: ha_when
    type: std::function<std::string(const std::string &, bool)>
    restore_value: false
    initial_value: |-
      [](const std::string &s, bool mit_tag) -> std::string {
        int Y, M, D, h, m, sec = 0;
        if (s.size() < 16 || sscanf(s.c_str(), "%d-%d-%d%*c%d:%d:%d", &Y, &M, &D, &h, &m, &sec) < 5)
          return std::string();
        // Versatz hinter der Uhrzeit: Z, +HH:MM oder -HH:MM
        long off = 0;
        const size_t pz = s.find_first_of("Z+-", 16);
        if (pz != std::string::npos && s[pz] != 'Z') {
          int oh = 0, om = 0;
          sscanf(s.c_str() + pz + 1, "%d:%d", &oh, &om);
          off = (s[pz] == '-' ? -1 : 1) * (oh * 3600L + om * 60L);
        }
        // Tage seit 1970 (days_from_civil, H. Hinnant)
        const int y = Y - (M <= 2);
        const int era = (y >= 0 ? y : y - 399) / 400;
        const unsigned yoe = (unsigned) (y - era * 400);
        const unsigned doy = (153 * (M + (M > 2 ? -3 : 9)) + 2) / 5 + D - 1;
        const unsigned doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
        const long tage = era * 146097L + (long) doe - 719468L;
        const time_t t = (time_t) (tage * 86400L + h * 3600L + m * 60L + sec - off);
        const ESPTime l = ESPTime::from_epoch_local(t);
        if (!l.is_valid())
          return std::string();
        static const char *const TAG_NAME[7] = {"So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"};
        char b[16];
        if (mit_tag)
          snprintf(b, sizeof(b), "%s %02d:%02d", TAG_NAME[(l.day_of_week + 6) % 7], l.hour, l.minute);
        else
          snprintf(b, sizeof(b), "%02d:%02d", l.hour, l.minute);
        return std::string(b);
      }
  # Beschriftung eines Tages: 0 "Heute", 1 "Morgen", sonst "Sa 27.09."
  - id: ha_day_label
    type: std::function<std::string(int, const ESPTime &)>
    restore_value: false
    initial_value: |-
      [](int d, const ESPTime &jetzt) -> std::string {
        if (d == 0)
          return "Heute";
        if (d == 1)
          return "Morgen";
        if (!jetzt.is_valid())
          return std::string();
        // von 12 Uhr aus rechnen, damit die Sommerzeit keinen Tag verschiebt
        const time_t mittag = jetzt.timestamp - (jetzt.hour * 3600 + jetzt.minute * 60 + jetzt.second) + 12 * 3600;
        const ESPTime t = ESPTime::from_epoch_local(mittag + (time_t) d * 86400);
        static const char *const TAG_NAME[7] = {"So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"};
        char b[16];
        snprintf(b, sizeof(b), "%s %02d.%02d.", TAG_NAME[(t.day_of_week + 6) % 7], t.day_of_month, t.month);
        return std::string(b);
      }
""")
    # --- Sensoren
    teile = {"n": [], "z": [], "t": [], "b": []}
    for e in TABELLE:
        sub, _ = entitaet(e)
        maske = sum(1 << g for g in e["gr"])
        if not maske:
            continue  # nur Substitution (Statistik, Basis fuer Attribute)
        z_ = [f"  - platform: homeassistant", f"    id: ha_{e['name']}", f"    entity_id: \"{j_entity(sub)}\""]
        if e["attr"]:
            z_.append(f"    attribute: {e['attr']}")
        z_.append("    internal: true")
        if e["mul"] is not None:
            z_.append("    filters:")
            z_.append(f"      - multiply: {e['mul']:.10g}")
        if maske and e["art"] == "b":
            # sonst loest der erste Wert von Home Assistant nicht aus
            z_.append("    trigger_on_initial_state: true")
        if maske:
            trig = "on_state" if e["art"] == "b" else "on_value"
            z_.append(f"    {trig}:")
            z_.append(f"      - lambda: 'id(ha_dirty) |= 0x{maske:08X}u;'")
        teile[e["art"]].append("\n".join(z_))
    w("sensor:")
    w("\n".join(teile["n"] + teile["z"]))
    w("")
    w("text_sensor:")
    w("\n".join(teile["t"]))
    w("")
    w("binary_sensor:")
    w("\n".join(teile["b"]))
    w("")
    # --- Skripte fuer die Abrufe
    w("""script:
  # Prognosen: Wetter stuendlich und taeglich, Solcast-Halbstunden. Die drei
  # Aktionen laufen nebeneinander, jede Antwort kommt fuer sich.
  - id: ha_fetch_fc
    then:""")
    w(aktion("weather.get_forecasts", [("entity_id", "${ha_weather}"), ("type", "hourly")], [],
             JINJA_STUNDE, ERFOLG_STUNDE, "weather.get_forecasts hourly"))
    w(aktion("weather.get_forecasts", [("entity_id", "${ha_weather}"), ("type", "daily")], [],
             JINJA_TAG, ERFOLG_TAG, "weather.get_forecasts daily"))
    w("      # Solcast: Aktion der Integration; scheitert sie (Integration fehlt,\n"
      "      # z. B. mit dem Dummy), liest ha_fetch_solcast_attr das Attribut")
    w(aktion("solcast_solar.query_forecast_data", [],
             [("start_date_time", "{{ today_at('00:00').isoformat() }}"),
              ("end_date_time", "{{ (today_at('00:00') + timedelta(days=1)).isoformat() }}")],
             JINJA_SOLCAST, ERFOLG_SOLCAST, "solcast_solar.query_forecast_data",
             fehler_extra="- lambda: 'ESP_LOGD(\"ha\", \"solcast_solar.query_forecast_data: %s -- lese "
                          "detailedForecast\", error.c_str());'\n- script.execute: ha_fetch_solcast_attr"))
    w("""
  # Ersatzweg fuer die Solcast-Halbstunden: das Attribut detailedForecast der
  # Tagesprognose. Die Vorlage braucht irgendeine Aktion mit Antwort --
  # weather.get_forecasts ist sicher da, ihre Antwort bleibt ungenutzt.
  - id: ha_fetch_solcast_attr
    then:""")
    w(aktion("weather.get_forecasts", [("entity_id", "${ha_weather}"), ("type", "daily")], [],
             JINJA_SOLCAST_ATTR, ERFOLG_SOLCAST, "Solcast detailedForecast"))
    w("""
  # Statistik (recorder.get_statistics, ab Home Assistant 2025.6): Woche und
  # Monat je Tag, Jahr je Monat; dazu die letzten 24 Stunden fuer die Seite
  # Haus und die Tagesreihe Erzeugung. Zaehlerstaende mit state_class
  # total_increasing, types change = Zuwachs je Platz in kWh.
  - id: ha_fetch_stats
    then:""")
    ids = "{{ [" + ", ".join(f"'{sid}'" for _, sid in STAT_REIHEN) + "] }}"
    for zr in ZEITRAEUME:
        w(f"      # {zr['name']}")
        w(aktion("recorder.get_statistics", [("period", zr["period"])],
                 [("statistic_ids", ids), ("start_time", "{{ (" + zr["t0"] + ").isoformat() }}"),
                  ("types", "{{ ['change'] }}"), ("units", "{{ {'energy': 'kWh'} }}")],
                 jinja_statistik(zr), erfolg_statistik(zr["range"]), f"Statistik {zr['name']}"))
    w("      # 24 Stunden: Hausverbrauch, Netzbezug (solar = Verbrauch - Bezug [A]),\n"
      "      # Erzeugung heute 06..22 Uhr fuer day_curve")
    w(aktion("recorder.get_statistics", [("period", "hour")],
             [("statistic_ids", "{{ ['${ha_home_energy_total}', '${ha_meter0_total}', '${ha_pv_energy_total}'] }}"),
              ("start_time", "{{ (" + STUNDEN_T0 + ").isoformat() }}"),
              ("types", "{{ ['change'] }}"), ("units", "{{ {'energy': 'kWh'} }}")],
             JINJA_STUNDEN, ERFOLG_STUNDEN, "Statistik 24 h"))
    w(MODUS_SET % {"b1": j_belegt("ha_wb1_mode"), "b2": j_belegt("ha_wb2_mode"),
                   "dirty": (1 << G["Wallbox 1"]) | (1 << G["Wallbox 2"])})
    # --- Intervalle
    w("""interval:
  # Drosselung: je Gruppe hoechstens ein Aufruf der Seitenskripte je Sekunde
  - interval: 1s
    then:
      - lambda: |-""")
    # belegt ja/nein je Substitution (Jinja zur Compile-Zeit)
    namen_b = set(basis(NAMEN[r]) for r in REFERENZ.values())
    for g in GRUPPEN:
        namen_b |= belegt_namen(g["code"])
    for n in sorted(namen_b):
        w(f"          constexpr bool B_{n} = {j_belegt('ha_' + n)};")
    w("""          const float LEER = id(val_leer);
          const bool ready = id(ha_ready);
          auto T_ok = [](text_sensor::TextSensor *s) -> bool {
            return s->has_state() && !s->state.empty() && s->state != "unavailable" && s->state != "unknown";
          };
          auto V = [&](sensor::Sensor *s, bool b) -> float {
            if (!b)
              return LEER;
            if (!s->has_state())
              return ready ? LEER : NAN;
            return std::isnan(s->state) ? LEER : s->state;
          };
          auto T = [&](text_sensor::TextSensor *s, bool b) -> std::string {
            if (!b)
              return " ";
            if (!s->has_state())
              return ready ? " " : "";
            return T_ok(s) ? s->state : std::string(" ");
          };
          // Referenzen -> dev_present; Aenderung: Grafik umbauen, alles neu
          uint32_t neu = 0;""")
    for platz, bit in PLAETZE:
        r = REFERENZ[platz]
        e = NAMEN[r]
        b = "B_" + basis(e)
        if e["art"] == "t":
            ok = f"{b} && T_ok(id(ha_{r}))"
        else:
            ok = f"{b} && id(ha_{r}).has_state() && !std::isnan(id(ha_{r}).state)"
        w(f"          if ({ok})")
        w(f"            neu |= 1u << {bit};   // {platz}")
    w("""          if (neu != id(dev_present)) {
            id(dev_present) = neu;
            id(dev_apply).execute();
            id(ha_dirty) = 0xFFFFFFFFu;
          }
          const uint32_t d = id(ha_dirty);
          if (d == 0)
            return;
          id(ha_dirty) = 0;
          const uint32_t dev = id(dev_present);
          auto da = [dev](int b) -> bool { return (dev >> b) & 1u; };
          // Rechnen nur ueber diese Hilfen: leer (val_leer, -inf) bleibt leer
          // und immer -inf -- kein Vorzeichenwechsel, nie inf - inf oder inf * 0
          auto I = [](float v, int none) -> int { return std::isfinite(v) ? (int) lroundf(v) : none; };
          auto pos = [LEER](float v) -> float { return std::isinf(v) ? LEER : (std::isnan(v) ? v : std::max(v, 0.0f)); };
          auto neg = [LEER](float v) -> float { return std::isinf(v) ? LEER : -v; };
          auto add = [LEER](float a, float b) -> float {
            if (std::isinf(a) || std::isinf(b))
              return LEER;
            return std::isnan(b) ? a : (std::isnan(a) ? b : a + b);
          };
          auto sub = [LEER](float a, float b) -> float { return (std::isinf(a) || std::isinf(b)) ? LEER : a - b; };
          auto mul = [LEER](float v, float f) -> float {
            if (std::isinf(v) || std::isinf(f))
              return LEER;
            return std::isnan(v) ? v : (std::isnan(f) ? f : v * f);
          };
          auto &num = id(fmt_num);
          auto when = [](const std::string &s, bool mit_tag) -> std::string {
            return s == " " ? s : id(ha_when)(s, mit_tag);
          };
          const ESPTime jetzt = id(dash_time).now();""")
    for g in GRUPPEN:
        mit = [e for e in TABELLE if g["bit"] in e["gr"]]
        if not mit:
            sys.exit(f"Fehler: Gruppe {g['name']} hat keinen Sensor")
        teile_h = [f"id(ha_{e['name']}).has_state()" for e in mit]
        hat = " ||\n               ".join(" || ".join(teile_h[i:i + 3]) for i in range(0, len(teile_h), 3))
        bed = f"(d & (1u << {g['bit']}))"
        if g["maske"]:
            bed += f" && (dev & 0x{g['maske']:08X}u)"
        w(f"          // {g['bit']} {g['name']}")
        w(f"          if ({bed} &&")
        w(f"              (ready || {hat})) {{")
        w(einr(c_code(g["code"]), 12))
        w("          }")
    w("""  # Abrufe: 20 s nach dem Verbinden die Prognosen, 30 s danach die
  # Statistik; dann Prognosen alle 30 min, Statistik zu jeder neuen Stunde
  # ab Minute 2 (Home Assistant schreibt die Stundenstatistik kurz nach der
  # vollen Stunde). Beim Trennen beginnt alles von vorn.
  - interval: 10s
    then:
      - lambda: |-
          static bool war = false;
          static uint32_t seit = 0, fc_zuletzt = 0;
          static int stat_schluessel = -1;
          const bool ist = api::global_api_server != nullptr && api::global_api_server->is_connected_with_state_subscription();
          if (ist != war) {
            war = ist;
            seit = millis();
            fc_zuletzt = 0;
            stat_schluessel = -1;
          }
          const bool bereit = ist && millis() - seit >= 10000;
          if (bereit != id(ha_ready)) {
            id(ha_ready) = bereit;
            id(ha_dirty) = 0xFFFFFFFFu;
          }
          if (!ist || millis() - seit < 20000)
            return;
          if (fc_zuletzt == 0 || millis() - fc_zuletzt >= 30u * 60u * 1000u) {
            fc_zuletzt = millis() | 1u;
            id(ha_fetch_fc).execute();
          }
          if (millis() - seit < 30000)
            return;
          const ESPTime t = id(dash_time).now();
          const int schluessel = t.is_valid() ? t.day_of_year * 24 + t.hour : 0;
          if (schluessel != stat_schluessel && (stat_schluessel < 0 || !t.is_valid() || t.minute >= 2)) {
            stat_schluessel = schluessel;
            id(ha_fetch_stats).execute();
          }""")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# Dummy-Paket fuer Home Assistant
# ---------------------------------------------------------------------------
BEREICH = {  # Einheit -> min, max, Schritt der input_number
    "W": (-30000, 30000, 1), "kW": (-30, 30, 0.01), "kWh": (0, 100000, 0.1), "Wh": (0, 100000, 1),
    "%": (0, 100, 1), "V": (0, 500, 0.001), "A": (-200, 200, 0.1), "°C": (-40, 100, 0.1),
    "Hz": (45, 55, 0.01), "km": (0, 1000, 1), "min": (0, 1440, 1), "€/kWh": (-1, 2, 0.001),
    "VA": (0, 30000, 1), "s": (0, 86400, 1), "d": (0, 400, 1), "": (-100000, 100000, 0.01),
}
SELECT_OPTIONEN = {"mode": MODUS_OPTIONEN_ALT, "vehicle": ["", "Kombi"]}


def y(s):
    """String fuer YAML in doppelten Anfuehrungszeichen."""
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def demo_text(v):
    return y(v)


def dummy_bauen():
    attrs = {}
    for e in TABELLE:
        if e["attr"]:
            _, ent = entitaet(e)
            attrs.setdefault(ent, []).append(e)
    num, zst, txt, sel, bsen, ibool, inum_direkt = [], [], [], [], [], [], []
    inputs = []
    for e in TABELLE:
        if e["attr"]:
            continue
        ent = e["ent"]
        dom, obj = ent.split(".", 1)
        uid = "pvd_" + e["name"]
        if dom in ("weather", "sun"):
            continue
        if dom == "input_boolean":
            ibool.append(f"  {obj}:\n    name: {y(obj)}\n    initial: {'true' if e['demo'] else 'false'}")
            continue
        if dom == "input_number":
            lo, hi, st = BEREICH[e["einh"]]
            inum_direkt.append(f"  {obj}:\n    name: {y(obj)}\n    min: {lo}\n    max: {hi}\n    step: {st}\n"
                               f"    initial: {e['demo']}\n    mode: box\n    unit_of_measurement: {y(e['einh'])}")
            continue
        at = attrs.get(ent, [])
        at_z = ""
        if at or e["name"] == "solcast_today":
            at_z = "\n        attributes:"
            for a in at:
                at_z += f"\n          {a['attr']}: {demo_text(a['demo']) if a['art'] == 't' else a['demo']}"
            if e["name"] == "solcast_today":
                at_z += "\n          detailedForecast: >-\n" + einr(DUMMY_DETAILED, 12)
        if dom == "select":
            opts = SELECT_OPTIONEN["mode" if e["name"].endswith("_mode") else "vehicle"]
            sel.append(f"      - default_entity_id: {ent}\n        unique_id: {uid}\n        name: {y(obj)}\n"
                       f"        optimistic: true\n        options: \"{{{{ {opts} }}}}\"")
            continue
        if e["art"] == "b":
            ib = "pvd_" + e["name"]
            inputs.append(f"  {ib}:\n    name: {y('PVD ' + e['name'])}\n    initial: {'true' if e['demo'] else 'false'}")
            bsen.append(f"      - default_entity_id: {ent}\n        unique_id: {uid}\n        name: {y(obj)}\n"
                        f"        state: \"{{{{ is_state('input_boolean.{ib}', 'on') }}}}\"")
            continue
        if e["art"] == "t":
            zeit = e["name"].endswith(("_plan", "_peak_time", "_last_poll"))
            dc = "\n        device_class: timestamp" if zeit else ""
            txt.append(f"      - default_entity_id: {ent}\n        unique_id: {uid}\n        name: {y(obj)}{dc}\n"
                       f"        state: {demo_text(e['demo'])}{at_z}")
            continue
        einh = f"\n        unit_of_measurement: {y(e['einh'])}" if e["einh"] else ""
        if e["art"] == "z":
            # Zaehlerstand: e["demo"] kWh je Stunde seit dem 01.01.2026
            zst.append(f"      - default_entity_id: {ent}\n        unique_id: {uid}\n        name: {y(obj)}{einh}\n"
                       f"        device_class: energy\n        state_class: total_increasing\n"
                       f"        state: \"{{{{ ((as_timestamp(now()) - as_timestamp('2026-01-01T00:00:00+00:00'))"
                       f" / 3600 * {e['demo']}) | round(2) }}}}\"")
            continue
        lo, hi, st = BEREICH[e["einh"]]
        inputs_num = f"  {uid}:\n    name: {y('PVD ' + e['name'])}\n    min: {lo}\n    max: {hi}\n    step: {st}\n" \
                     f"    initial: {e['demo']}\n    mode: box"
        inputs.append(("n", inputs_num))
        num.append(f"      - default_entity_id: {ent}\n        unique_id: {uid}\n        name: {y(obj)}{einh}\n"
                   f"        state: \"{{{{ states('input_number.{uid}') | float(0) }}}}\"{at_z}")
    in_num = [x[1] for x in inputs if isinstance(x, tuple)]
    in_bool = [x for x in inputs if isinstance(x, str)]
    wx = NAMEN["weather"]["ent"]
    warn_ent = NAMEN["warn_level"]["ent"]
    kopf = f"""##############################################################################
# Home-Assistant-Paket: Ersatz-Entitaeten fuer das PV-Dashboard
#
# ERZEUGT von tools/ha_bindings.py -- nicht von Hand aendern.
#
# Legt jede Entitaet an, die .pv-dashboard_ha.yaml als Standard erwartet,
# damit das Panel ohne Wechselrichter, evcc, Solcast, DWD und Shelly Werte
# bekommt. Einbinden in configuration.yaml:
#
#   homeassistant:
#     packages:
#       pv_dashboard_dummy: !include packages/pv_dashboard_dummy.yaml
#
# (Datei nach <config>/packages/ kopieren, Home Assistant neu starten.)
#
#   - Zahlen: je ein input_number.pvd_<name>, der Sensor mit der Standard-ID
#     zeigt dessen Wert (Einstellungen > Helfer, von Hand verstellbar).
#   - Zaehlerstaende (fuer recorder.get_statistics) laufen gleichmaessig
#     hoch; die Statistik fuellt sich erst mit der Zeit.
#   - Texte und Zeitpunkte fest, Wetter als Template-Wetter mit Vorhersagen,
#     detailedForecast als Attribut der Solcast-Tagesprognose.
#   - Ein Geraet verschwindet am Panel, wenn seine Referenz-Entitaet (Liste
#     in .pv-dashboard_ha.yaml unter substitutions) keinen gueltigen Wert hat,
#     etwa input_number.pvd_bat3_soc hier ausser Betrieb -- oder dauerhaft mit
#     ha_<referenz>: none in .pv-dashboard_anlage.yaml.
#   - sun.sun kommt aus der Integration sun (default_config), nicht von hier.
#
# Umstellen auf die echten Entitaeten: dieses Paket entfernen, dann die
# echten IDs in .pv-dashboard_anlage.yaml als ha_<name>: <entity_id>
# eintragen -- nur die, die vom Standard abweichen. Was es nicht gibt:
# ha_<name>: none (Geraet ohne Referenz faellt ganz weg, sonst nur der Wert).
#
# Die Wetter-Entitaet heisst hier {wx}, die Warnzelle
# {warn_ent} -- beides Platzhalter fuer Station und Warnzelle.
##############################################################################
"""
    teile = [kopf]
    teile.append("input_boolean:\n  # Ersatz fuer an/aus-Werte\n" + "\n".join(in_bool))
    teile.append("\n".join(ibool))
    teile.append("\ninput_number:\n" + "\n".join(in_num + inum_direkt))
    tpl = ["\ntemplate:"]
    tpl.append("  - binary_sensor:\n" + "\n".join(bsen))
    tpl.append("  - sensor:\n" + "\n".join(num + zst + txt))
    tpl.append("  - select:\n" + "\n".join(sel))
    tpl.append(f"""  - weather:
      - default_entity_id: {wx}
        unique_id: pvd_weather
        name: "dwd_station"
        condition: "partlycloudy"
        temperature: "{NAMEN['wx_temp']['demo']}"
        temperature_unit: "°C"
        humidity: "{NAMEN['wx_humidity']['demo']}"
        pressure: "{NAMEN['wx_pressure']['demo']}"
        pressure_unit: "hPa"
        wind_speed: "{NAMEN['wx_wind']['demo']}"
        wind_bearing: "{NAMEN['wx_bearing']['demo']}"
        wind_speed_unit: "km/h"
        forecast_hourly: >-
{einr(DUMMY_STUNDE, 10)}
        forecast_daily: >-
{einr(DUMMY_TAG, 10)}""")
    teile.append("\n".join(tpl))
    return "\n".join(teile) + "\n"


DUMMY_DETAILED = """{%- set ns = namespace(l=[]) -%}
{%- for i in range(48) -%}
{%- set p = [0, 22 - ((i - 26) ** 2) * 0.12] | max -%}
{%- set ns.l = ns.l + [{'period_start': (today_at('00:00') + timedelta(minutes=30 * i)).isoformat(), 'pv_estimate': p | round(2), 'pv_estimate10': (p * 0.8) | round(2), 'pv_estimate90': (p * 1.12) | round(2)}] -%}
{%- endfor -%}
{{ ns.l }}"""

DUMMY_STUNDE = """{%- set ns = namespace(l=[]) -%}
{%- set lage = ['clear-night', 'clear-night', 'fog', 'partlycloudy', 'sunny', 'sunny', 'partlycloudy', 'cloudy', 'rainy', 'pouring', 'rainy', 'cloudy'] -%}
{%- for i in range(24) -%}
{%- set t = now().replace(minute=0, second=0, microsecond=0) + timedelta(hours=i) -%}
{%- set ns.l = ns.l + [{'datetime': t.isoformat(), 'condition': lage[t.hour // 2], 'temperature': 9 + (t.hour if t.hour < 15 else 30 - t.hour) * 0.7, 'precipitation': [0, 0, 0, 0, 0, 0, 0, 0.2, 1.1, 2.3, 0.6, 0.1][t.hour // 2], 'precipitation_probability': [0, 0, 10, 10, 5, 0, 10, 40, 80, 90, 60, 30][t.hour // 2], 'wind_gust_speed': 24, 'cloud_coverage': 40}] -%}
{%- endfor -%}
{{ ns.l }}"""

DUMMY_TAG = """{%- set ns = namespace(l=[]) -%}
{%- set lage = ['partlycloudy', 'sunny', 'rainy', 'cloudy', 'partlycloudy', 'lightning-rainy', 'sunny'] -%}
{%- for i in range(7) -%}
{%- set ns.l = ns.l + [{'datetime': (today_at('00:00') + timedelta(days=i)).isoformat(), 'condition': lage[i], 'temperature': [19, 22, 14, 15, 18, 16, 21][i], 'templow': [8, 9, 10, 9, 7, 11, 8][i], 'precipitation': [2.4, 0, 11.3, 1.2, 0.3, 6.8, 0][i], 'precipitation_probability': [70, 5, 95, 40, 20, 80, 5][i], 'wind_speed': [14, 9, 28, 19, 12, 22, 10][i]}] -%}
{%- endfor -%}
{{ ns.l }}"""


def pruefen(text, name):
    """Zeilen, die ESPHome selbst als Jinja lesen wuerde (nur Paket)."""
    for nr, zeile in enumerate(text.split("\n"), 1):
        if "<%" in zeile:
            sys.exit(f"Fehler: {name}:{nr} enthaelt '<%'")
    return text


if __name__ == "__main__":
    panel = pruefen(panel_bauen(), ".pv-dashboard_ha.yaml")
    dummy = dummy_bauen()
    n_s = sum(1 for e in TABELLE)
    print(f"{n_s} Sensoren ({sum(1 for e in TABELLE if e['attr'])} davon Attribute), "
          f"{len(PLAETZE)} Referenzen, {len(GRUPPEN)} Gruppen")
    aktuell = True
    for pfad, neu in ((ZIEL_PANEL, panel), (ZIEL_HA, dummy)):
        alt = open(pfad, encoding="utf-8").read() if os.path.exists(pfad) else None
        rel = os.path.relpath(pfad, ROOT)
        if alt == neu:
            print(f"{rel}: aktuell")
            continue
        aktuell = False
        if "--write" in sys.argv:
            os.makedirs(os.path.dirname(pfad), exist_ok=True)
            with open(pfad, "w", encoding="utf-8") as f:
                f.write(neu)
            print(f"{rel}: geschrieben ({neu.count(chr(10))} Zeilen)")
        else:
            print(f"{rel}: veraltet -- mit --write neu schreiben")
    sys.exit(0 if aktuell or "--write" in sys.argv else 1)
