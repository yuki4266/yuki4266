#!/usr/bin/env python3
"""Living scene: weather-synced sky strip + seasonal garden footer, day & night variants.
Runs in CI every few hours. Deterministic per (weather, season) so unchanged state = no diff.

Usage: gen_scene.py [--weather clear|clouds|rain|snow|fog|storm] [--season spring|summer|autumn|winter] [--force]
"""
import json
import random
import re
import sys
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

LAT, LON = 35.99, -78.90  # Durham, NC
TZ = "America/New_York"
STATE = ".github/scene-state"
SPLINE2 = 'calcMode="spline" keySplines="0.4 0 0.6 1;0.4 0 0.6 1" keyTimes="0;0.5;1"'

# ---------------- night support ----------------
NIGHT_MAP = {
    "#E8603C": "#FF7A50", "#E2542F": "#F4694A", "#F4795B": "#FF9075",
    "#ED8B66": "#FFA584", "#F09A7E": "#FFAC90", "#FBC7B3": "#FFD0BE",
    "#F9B98A": "#FFC79A", "#FFE9CF": "#FFF3E0", "#FFDCA8": "#FFE9C9",
    "#F4B183": "#FFD9A8", "#F4A05B": "#FFC069", "#A33D22": "#C9744F",
    "#7FA36B": "#8FAE7E", "#8CB07A": "#9CBE8B", "#A8C79A": "#B5D3A7",
    "#3B2F2A": "#A99C90",
    # seasonal greens / autumn ochres / winter palettes
    "#5E8B4F": "#6E8F60", "#6FA35E": "#7FA36B", "#87B573": "#93AF80",
    "#C98F4E": "#8F6E45", "#B57B3F": "#7E5A34", "#D9A863": "#9C7E52",
    "#C46A38": "#8F5230", "#D98E4A": "#9C6C3E",
    "#9AA79A": "#707D70", "#B3BDB3": "#828E82", "#8B978B": "#667266",
    # weather furniture
    "#C9D2DE": "#4E5866", "#98A5B8": "#566274", "#8FA8C4": "#6E87A3",
    "#B9C2CE": "#525C68", "#EDF2F7": "#B9C7D6",
}


def nightify(svg):
    return re.sub(r"#[0-9A-Fa-f]{6}", lambda m: NIGHT_MAP.get(m.group(0).upper(), m.group(0)), svg)


def stars(n, xlo, xhi, ylo, yhi, seed):
    rnd = random.Random(seed)
    out = []
    for k in range(n):
        x, y = rnd.randint(xlo, xhi), rnd.randint(ylo, yhi)
        dur, beg = rnd.uniform(1.8, 4.5), rnd.uniform(0, 4)
        if k % 3 == 0:
            out.append(f'<g transform="translate({x},{y}) scale({rnd.uniform(0.6, 1.0):.2f})">'
                       f'<path d="M0 -5 L1.2 -1.2 L5 0 L1.2 1.2 L0 5 L-1.2 1.2 L-5 0 L-1.2 -1.2 Z" fill="#D9E6F5" opacity="0.2">'
                       f'<animate attributeName="opacity" values="0.15;0.9;0.15" keyTimes="0;0.5;1" dur="{dur:.1f}s" begin="{beg:.1f}s" repeatCount="indefinite"/></path></g>')
        else:
            out.append(f'<circle cx="{x}" cy="{y}" r="{rnd.uniform(0.9, 1.5):.1f}" fill="#D9E6F5" opacity="0.2">'
                       f'<animate attributeName="opacity" values="0.1;0.8;0.1" keyTimes="0;0.5;1" dur="{dur:.1f}s" begin="{beg:.1f}s" repeatCount="indefinite"/></circle>')
    return "".join(out)


# ---------------- weather / season ----------------
def fetch_weather():
    url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&current=weather_code"
    code = json.load(urllib.request.urlopen(url, timeout=20))["current"]["weather_code"]
    if code >= 95:
        return "storm"
    if code in (71, 73, 75, 77, 85, 86):
        return "snow"
    if 51 <= code <= 67 or 80 <= code <= 82:
        return "rain"
    if code in (45, 48):
        return "fog"
    if code in (1, 2, 3):
        return "clouds"
    return "clear"


def current_season():
    m = datetime.now(ZoneInfo(TZ)).month
    return "spring" if m in (3, 4, 5) else "summer" if m in (6, 7, 8) else "autumn" if m in (9, 10, 11) else "winter"


# ---------------- shared parts ----------------
def butterfly(path, dur):
    return ('<g opacity="0">'
            f'<animate attributeName="opacity" values="0;0.95;0.95;0" keyTimes="0;0.05;0.95;1" dur="{dur}s" begin="1s" repeatCount="indefinite"/>'
            f'<g><animateMotion dur="{dur}s" begin="1s" repeatCount="indefinite" rotate="auto" path="{path}"/>'
            '<g><animateTransform attributeName="transform" type="scale" values="1 1;1 0.3;1 1" keyTimes="0;0.5;1" dur="0.5s" repeatCount="indefinite"/>'
            '<path d="M1 -1 C 7 -15, -13 -17, -6 -2 Z" fill="#F4795B" opacity="0.9"/>'
            '<path d="M-3 -1 C -7 -13, -17 -8, -9 -1 Z" fill="#FBC7B3" opacity="0.85"/>'
            '<path d="M1 1 C 7 15, -13 17, -6 2 Z" fill="#F4795B" opacity="0.9"/>'
            '<path d="M-3 1 C -7 13, -17 8, -9 1 Z" fill="#FBC7B3" opacity="0.85"/></g>'
            '<ellipse rx="5.5" ry="1.8" fill="#A33D22"/>'
            '<path d="M5 -1 Q 9 -5 11 -6 M5 1 Q 9 5 11 6" stroke="#A33D22" stroke-width="0.8" fill="none"/>'
            '</g></g>')


def falling(rnd, shapes, count, h, colors):
    out = []
    for _ in range(count):
        px = rnd.randint(30, 870)
        drift = rnd.choice([-1, 1]) * rnd.randint(16, 34)
        dur = rnd.uniform(7, 12)
        beg = rnd.uniform(0, 6)
        c = rnd.choice(colors)
        out.append(f'<g transform="translate({px},-10)" opacity="0">'
                   f'<animate attributeName="opacity" values="0;0.7;0.7;0" keyTimes="0;0.1;0.75;1" dur="{dur:.1f}s" begin="{beg:.1f}s" repeatCount="indefinite"/>'
                   f'<g><animateTransform attributeName="transform" type="translate" values="0 0;{drift} {h // 2};{drift * 2} {h}" keyTimes="0;0.5;1" dur="{dur:.1f}s" begin="{beg:.1f}s" repeatCount="indefinite"/>'
                   f'<use href="#{shapes}" fill="{c}">'
                   f'<animateTransform attributeName="transform" type="rotate" values="0;170;350" keyTimes="0;0.5;1" dur="{dur:.1f}s" begin="{beg:.1f}s" repeatCount="indefinite"/>'
                   f'</use></g></g>')
    return "".join(out)


def weather_layer(w, rnd, H):
    out = []
    if w in ("clouds", "rain", "storm"):
        col, op = ("#98A5B8", 0.75) if w in ("rain", "storm") else ("#C9D2DE", 0.55)
        for i, (cy, sc) in enumerate([(14, 0.9), (26, 1.25), (18, 1.0)]):
            out.append(f'<g opacity="{op}"><g transform="translate(0,{cy}) scale({sc})">'
                       f'<animateTransform attributeName="transform" type="translate" values="-170 {cy};950 {cy}" dur="{58 + i * 14}s" begin="{-i * 23}s" repeatCount="indefinite" additive="replace"/>'
                       f'<g transform="scale({sc})"><ellipse rx="34" ry="11" fill="{col}"/><ellipse cx="22" cy="-6" rx="23" ry="9" fill="{col}"/><ellipse cx="-24" cy="-4" rx="21" ry="8" fill="{col}"/></g></g></g>')
    if w in ("rain", "storm"):
        for _ in range(26):
            x = rnd.randint(0, 900)
            dur = rnd.uniform(0.8, 1.3)
            out.append(f'<g><animateTransform attributeName="transform" type="translate" values="0 -14;0 {H + 20}" dur="{dur:.2f}s" begin="{-rnd.uniform(0, 1.3):.2f}s" repeatCount="indefinite"/>'
                       f'<line x1="{x}" y1="0" x2="{x - 4}" y2="12" stroke="#8FA8C4" stroke-width="1.3" stroke-linecap="round" opacity="0.55"/></g>')
    if w == "snow":
        for _ in range(20):
            x = rnd.randint(0, 900)
            dx = rnd.choice([-1, 1]) * rnd.randint(6, 16)
            dur = rnd.uniform(6, 11)
            out.append(f'<g><animateTransform attributeName="transform" type="translate" values="0 -8;{dx} {H // 2};{dx * 2} {H + 8}" keyTimes="0;0.5;1" dur="{dur:.1f}s" begin="{-rnd.uniform(0, 8):.1f}s" repeatCount="indefinite"/>'
                       f'<circle cx="{x}" cy="0" r="{rnd.uniform(1.2, 2.4):.1f}" fill="#EDF2F7" opacity="0.85"/></g>')
    if w == "fog":
        for i, y in enumerate([16, 34, 50]):
            out.append(f'<g opacity="0.22"><rect x="{-40 + i * 180}" y="{y}" width="420" height="12" rx="6" fill="#B9C2CE">'
                       f'<animateTransform attributeName="transform" type="translate" values="0 0;110 0;0 0" {SPLINE2} dur="{28 + i * 7}s" repeatCount="indefinite"/></rect></g>')
    if w == "storm":
        x = rnd.randint(220, 680)
        out.append(f'<rect x="0" y="0" width="900" height="{H}" fill="#FFF3C4" opacity="0">'
                   '<animate attributeName="opacity" values="0;0;0.28;0;0.14;0;0" keyTimes="0;0.52;0.545;0.57;0.585;0.61;1" dur="7s" repeatCount="indefinite"/></rect>')
        out.append(f'<path d="M{x} 6 L{x - 7} 26 L{x + 1} 24 L{x - 6} 48" stroke="#FFE9A8" stroke-width="2.5" fill="none" stroke-linecap="round" opacity="0">'
                   '<animate attributeName="opacity" values="0;0;1;0;0.5;0;0" keyTimes="0;0.52;0.545;0.57;0.585;0.61;1" dur="7s" repeatCount="indefinite"/></path>')
    return "".join(out)


SUN = ('<g transform="translate(52,26)">'
       '<circle r="18" fill="#FFD9A0" opacity="0.3"><animate attributeName="opacity" values="0.2;0.42;0.2" keyTimes="0;0.5;1" dur="5s" repeatCount="indefinite"/></circle>'
       '<circle r="9" fill="#FFC069"/>'
       '<g stroke="#FFC069" stroke-width="1.5" opacity="0.65">'
       '<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="70s" repeatCount="indefinite"/>'
       + "".join(f'<line x1="0" y1="-13" x2="0" y2="-18" transform="rotate({a})"/>' for a in range(0, 360, 45))
       + '</g></g>')


# ---------------- sky ----------------
def gen_sky(w, s):
    rnd = random.Random(f"sky-{w}-{s}")
    H = 70
    base = ['<defs><path id="spet" d="M0 0 C-4 -5 -4 -13 0 -17 C4 -13 4 -5 0 0 Z"/>'
            '<path id="sleaf" d="M0 0 Q-7 -3 -9 -10 Q-3 -8 0 0 Z"/></defs>']
    if s in ("spring", "summer") and w in ("clear", "clouds"):
        for (sx, sy, sc, dur, beg) in [(330, 50, 0.6, 4.2, 1.6), (560, 22, 0.9, 3.8, 2.4), (720, 48, 0.7, 4.4, 0.9)]:
            base.append(f'<g transform="translate({sx},{sy}) scale({sc})"><g opacity="0">'
                        f'<animate attributeName="opacity" values="0;0.8;0" keyTimes="0;0.5;1" dur="{dur}s" begin="{beg}s" repeatCount="indefinite"/>'
                        f'<animateTransform attributeName="transform" type="rotate" from="0" to="90" dur="{dur}s" begin="{beg}s" repeatCount="indefinite"/>'
                        f'<path d="M0 -7 L1.6 -1.6 L7 0 L1.6 1.6 L0 7 L-1.6 1.6 L-7 0 L-1.6 -1.6 Z" fill="#F4B183"/></g></g>')
    if s in ("spring", "summer"):
        for (px, py, c, dur, beg) in [(220, 40, "#F4795B", 6.0, 1.0), (470, 55, "#FBC7B3", 7.5, 2.2), (650, 35, "#ED8B66", 6.8, 3.1)]:
            base.append(f'<g transform="translate({px},{py})"><g>'
                        f'<animateTransform attributeName="transform" type="translate" values="0 3;0 -6;0 3" {SPLINE2} dur="{dur}s" begin="{beg}s" repeatCount="indefinite"/>'
                        f'<circle r="2" fill="{c}" opacity="0"><animate attributeName="opacity" values="0;0.55;0" keyTimes="0;0.5;1" dur="{dur}s" begin="{beg}s" repeatCount="indefinite"/></circle></g></g>')
    if s == "spring":
        base.append(falling(rnd, "spet", 2, H + 20, ["#FBC7B3", "#F4795B"]))
    if s == "autumn":
        base.append(falling(rnd, "sleaf", 4, H + 20, ["#C46A38", "#D98E4A", "#B57B3F"]))
    base.append(weather_layer(w, rnd, H))
    if s in ("spring", "summer") and w in ("clear", "clouds"):
        base.append(butterfly("M880 30 C700 60 560 5 420 40 C300 68 160 15 20 38 C160 62 340 20 520 50 C680 72 800 45 880 30", 15))
    base.append(f'<text x="893" y="64" text-anchor="end" font-size="9" letter-spacing="1.5" fill="#8b949e">LIVE SKY · {w.upper()} · {s.upper()}</text>')

    def wrap(inner):
        return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 70" width="900" height="70" '
                'font-family="Segoe UI, Ubuntu, Helvetica, Arial, sans-serif">\n<title>sky</title>' + inner + '</svg>\n')

    day = wrap((SUN if w == "clear" else "") + "".join(base))
    night = wrap(stars(9, 30, 870, 8, 58, 11) + nightify("".join(base)))
    return day, night


# ---------------- footer ----------------
SEASON_CFG = {
    "spring": dict(greens=["#7FA36B", "#8CB07A", "#A8C79A"], daisies=4, fireflies=5, ground=("#FBC7B3", 0.2)),
    "summer": dict(greens=["#5E8B4F", "#6FA35E", "#87B573"], daisies=4, fireflies=7, ground=("#F9B98A", 0.22)),
    "autumn": dict(greens=["#C98F4E", "#B57B3F", "#D9A863"], daisies=1, fireflies=3, ground=("#D9A863", 0.22)),
    "winter": dict(greens=["#9AA79A", "#B3BDB3", "#8B978B"], daisies=0, fireflies=0, ground=("#EDF2F7", 0.45)),
}
FIREFLY_SPOTS = [(150, 70, 9, 2.0, 2.4), (320, 50, 11, 3.2, 3.0), (480, 82, 8.5, 2.6, 2.2),
                 (610, 45, 10, 4.0, 2.8), (760, 72, 9.5, 3.5, 2.5), (870, 55, 11.5, 2.2, 3.2), (60, 46, 10.5, 4.4, 2.6)]
DAISY_SPOTS = [(120, 118, 0.9, 1.2), (382, 124, 0.7, 1.6), (633, 120, 0.85, 1.4), (818, 126, 0.65, 1.8)]


def cat():
    C = "#3B2F2A"
    leg = ('<g transform="translate({x},{y})"><path d="M-1.7 0 L1.7 0 L1.3 9.5 Q0 11 -1.3 9.5 Z" fill="' + C + '"{extra}>'
           '<animateTransform attributeName="transform" type="rotate" values="{a};{b};{a}" '
           f'{SPLINE2} ' + 'dur="0.6s" begin="{beg}s" repeatCount="indefinite"/></path></g>')
    return ('<g><animateTransform attributeName="transform" type="translate" '
            'values="950 0;950 0;-130 0;-130 0" keyTimes="0;0.6;0.78;1" dur="90s" begin="-25s" repeatCount="indefinite"/>'
            '<g transform="translate(0,129)">'
            f'<g><animateTransform attributeName="transform" type="translate" values="0 0;0 -1.3;0 0" {SPLINE2} dur="0.6s" repeatCount="indefinite"/>'
            '<g transform="translate(14,-15)"><path d="M0 2 C 7 0 10.5 -7 8 -15 C 7 -18.5 4.5 -20.5 2.5 -19.5" '
            f'stroke="{C}" stroke-width="3.2" fill="none" stroke-linecap="round">'
            f'<animateTransform attributeName="transform" type="rotate" values="-9;9;-9" {SPLINE2} dur="1.6s" repeatCount="indefinite"/></path></g>'
            + leg.format(x=-6, y=-4, a=-20, b=20, beg=-0.3, extra=' opacity="0.75"')
            + leg.format(x=11, y=-4, a=17, b=-17, beg=-0.3, extra=' opacity="0.75"')
            + f'<path d="M-12 -20 C -2 -25.5 9 -24.5 14 -18 C 17.2 -14 17.2 -8 14 -4.5 L 12 -3.5 L -9 -3.5 C -13 -9 -14.2 -15 -12 -20 Z" fill="{C}"/>'
            + leg.format(x=-9, y=-4, a=20, b=-20, beg=0, extra='')
            + leg.format(x=14, y=-4, a=-17, b=17, beg=0, extra='')
            + f'<path d="M-11 -17 C -11.5 -23 -15 -26.5 -19.5 -26.5 C -22 -26.5 -24.5 -25 -25.8 -22.5 '
              f'C -27 -20.5 -27 -17.5 -25.5 -15.5 C -23.5 -12.8 -19 -12 -15.5 -13.5 C -13 -14.5 -11.3 -15.5 -11 -17 Z" fill="{C}"/>'
            + f'<path d="M-25.2 -24.5 L-25.8 -31.5 L-20.8 -27.5 Z" fill="{C}"/>'
            + f'<path d="M-18 -27.5 L-14.2 -32.5 L-13.2 -26 Z" fill="{C}"/>'
            + '<circle cx="-22.6" cy="-20.8" r="1" fill="#FBC7B3"/>'
            + '<path d="M-24.6 -25.6 L-24.9 -28.8 L-22.6 -26.9 Z" fill="#FBC7B3" opacity="0.55"/>'
            '</g></g></g>')


def gen_footer(w, s):
    cfg = SEASON_CFG[s]
    rnd = random.Random(f"footer-{s}")
    p = ['<defs><path id="fpetal" d="M0 0 C-4 -5 -4 -13 0 -17 C4 -13 4 -5 0 0 Z"/>'
         '<path id="fleaf" d="M0 0 Q-7 -3 -9 -10 Q-3 -8 0 0 Z"/></defs>']
    g, gop = cfg["ground"]
    p.append(f'<ellipse cx="450" cy="152" rx="480" ry="26" fill="{g}" opacity="{gop}"/>')
    if s == "winter":  # snow drifts on the ground
        for (dx, rx) in [(180, 120), (450, 160), (740, 110)]:
            p.append(f'<ellipse cx="{dx}" cy="138" rx="{rx}" ry="7" fill="#EDF2F7" opacity="0.55"/>')
    p.append(cat())
    x = 12
    while x < 895:
        h = rnd.randint(22, 52) if s != "winter" else rnd.randint(16, 34)
        bend = rnd.choice([-1, 1]) * rnd.randint(4, 10)
        gc = rnd.choice(cfg["greens"])
        sway, beg, amp = rnd.uniform(3.2, 6.2), rnd.uniform(0, 4), rnd.uniform(3.5, 7)
        t = rnd.uniform(0.1, 1.1)
        p.append(f'<g transform="translate({x},140)"><g opacity="0">'
                 f'<animate attributeName="opacity" from="0" to="0.8" begin="{t:.2f}s" dur="0.6s" fill="freeze"/>'
                 f'<animateTransform attributeName="transform" type="scale" from="1 0" to="1 1" begin="{t:.2f}s" dur="0.7s" '
                 f'calcMode="spline" keyTimes="0;1" keySplines="0.2 0.8 0.3 1" fill="freeze"/>'
                 f'<g><animateTransform attributeName="transform" type="rotate" values="{-amp:.1f};{amp:.1f};{-amp:.1f}" '
                 f'{SPLINE2} dur="{sway:.2f}s" begin="{beg:.2f}s" repeatCount="indefinite"/>'
                 f'<path d="M0 0 Q{bend} {-h * 0.55:.0f} {bend * 1.6:.0f} {-h}" stroke="{gc}" stroke-width="{rnd.choice([2, 2.5, 3])}" '
                 f'fill="none" stroke-linecap="round"/></g></g></g>')
        x += rnd.randint(18, 34) if s != "winter" else rnd.randint(26, 44)
    for (dx, dy, sc, beg) in DAISY_SPOTS[:cfg["daisies"]]:
        p.append(f'<g transform="translate({dx},{dy}) scale({sc})"><g opacity="0">'
                 f'<animate attributeName="opacity" from="0" to="1" begin="{beg}s" dur="0.5s" fill="freeze"/>'
                 f'<animateTransform attributeName="transform" type="scale" from="0" to="1" begin="{beg}s" dur="0.6s" '
                 f'calcMode="spline" keyTimes="0;1" keySplines="0.2 0.9 0.3 1" fill="freeze"/>'
                 f'<g><animateTransform attributeName="transform" type="rotate" values="-4;4;-4" '
                 f'{SPLINE2} dur="5s" begin="{beg + 0.6}s" repeatCount="indefinite"/>'
                 f'<circle cx="0" cy="-7" r="3.6" fill="#F4795B"/><circle cx="6.7" cy="-2.2" r="3.6" fill="#F4795B"/>'
                 f'<circle cx="4.1" cy="5.7" r="3.6" fill="#F4795B"/><circle cx="-4.1" cy="5.7" r="3.6" fill="#F4795B"/>'
                 f'<circle cx="-6.7" cy="-2.2" r="3.6" fill="#F4795B"/><circle r="3" fill="#FFDCA8" stroke="#E2542F" stroke-width="1"/>'
                 f'</g></g></g>')
    for (fx, fy, dur, beg, glow) in FIREFLY_SPOTS[:cfg["fireflies"]]:
        p.append(f'<g transform="translate({fx},{fy})"><g>'
                 f'<animateMotion dur="{dur}s" begin="0s" repeatCount="indefinite" path="M0 0 C 16 -12 36 -6 30 6 C 25 17 6 14 0 0 Z"/>'
                 f'<circle r="5" fill="#F4A05B" opacity="0.15"><animate attributeName="opacity" values="0.08;0.4;0.08" keyTimes="0;0.5;1" dur="{glow}s" begin="{beg}s" repeatCount="indefinite"/></circle>'
                 f'<circle r="1.8" fill="#F4795B" opacity="0.35"><animate attributeName="opacity" values="0.25;1;0.25" keyTimes="0;0.5;1" dur="{glow}s" begin="{beg}s" repeatCount="indefinite"/></circle>'
                 f'</g></g>')
    if s == "spring":
        p.append(falling(rnd, "fpetal", 4, 150, ["#F4795B", "#FBC7B3", "#ED8B66"]))
    if s == "autumn":
        p.append(falling(rnd, "fleaf", 6, 150, ["#C46A38", "#D98E4A", "#B57B3F"]))
    if s == "winter" or w == "snow":
        p.append(weather_layer("snow", random.Random(f"fsnow-{s}"), 140))

    def wrap(inner):
        return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 140" width="900" height="140">\n'
                '<title>garden footer</title>' + inner + '</svg>\n')

    day = wrap("".join(p))
    night = wrap(stars(9, 20, 880, 8, 52, 13) + nightify("".join(p)))
    return day, night


# ---------------- main ----------------
def main():
    args = sys.argv[1:]

    def opt(name):
        return args[args.index(name) + 1] if name in args else None

    w = opt("--weather") or fetch_weather()
    s = opt("--season") or current_season()
    state = f"{w}-{s}"
    try:
        old = open(STATE).read().strip()
    except OSError:
        old = ""
    if state == old and "--force" not in args:
        print(f"scene unchanged ({state}), nothing to do")
        return
    day, night = gen_sky(w, s)
    open("sky.svg", "w").write(day)
    open("sky-night.svg", "w").write(night)
    day, night = gen_footer(w, s)
    open("garden-footer.svg", "w").write(day)
    open("garden-footer-night.svg", "w").write(night)
    open(STATE, "w").write(state + "\n")
    print(f"scene rendered: {state}")


if __name__ == "__main__":
    main()
