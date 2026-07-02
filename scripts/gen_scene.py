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
CYC = 'dur="75s" begin="-8s" repeatCount="indefinite"'  # master cat cycle
C = "#3B2F2A"
PEACH = "#FBC7B3"

# ---------------- night support ----------------
NIGHT_MAP = {
    "#E8603C": "#FF7A50", "#E2542F": "#F4694A", "#F4795B": "#FF9075",
    "#ED8B66": "#FFA584", "#F09A7E": "#FFAC90", "#FBC7B3": "#FFD0BE",
    "#F9B98A": "#FFC79A", "#FFE9CF": "#FFF3E0", "#FFDCA8": "#FFE9C9",
    "#F4B183": "#FFD9A8", "#F4A05B": "#FFC069", "#A33D22": "#C9744F",
    "#7FA36B": "#8FAE7E", "#8CB07A": "#9CBE8B", "#A8C79A": "#B5D3A7",
    "#3B2F2A": "#A99C90",
    "#5E8B4F": "#6E8F60", "#6FA35E": "#7FA36B", "#87B573": "#93AF80",
    "#C98F4E": "#8F6E45", "#B57B3F": "#7E5A34", "#D9A863": "#9C7E52",
    "#C46A38": "#8F5230", "#D98E4A": "#9C6C3E",
    "#9AA79A": "#707D70", "#B3BDB3": "#828E82", "#8B978B": "#667266",
    # weather furniture (day -> night)
    "#CBD5E1": "#4E5866", "#9FB0C2": "#3E4754",
    "#8E9DB2": "#566274", "#6C7B92": "#454F60",
    "#B7C2D2": "#5A6675", "#93A2B8": "#49535F",
    "#707E94": "#3C4656", "#525F75": "#303A4A",
    "#8FA8C4": "#6E87A3", "#9FACBC": "#525C68",
    "#C4D2E0": "#E9F0F8", "#B9C9DA": "#DCE7F2", "#EDF2F7": "#B9C7D6",
    # back-layer grass (day -> night)
    "#B7CCA8": "#7C8F70", "#9DBE8D": "#6E8F60", "#DDBA84": "#9C8258", "#C2CCC2": "#7E8A7E",
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


# ---------------- weather visuals ----------------
CLOUD = ('M-38 8 C -44 8 -48 3 -46 -2 C -44.5 -6 -40 -8 -36 -7 C -35 -13 -28 -16.5 -21 -15 '
         'C -18 -20.5 -9 -22 -3 -18.5 C 2 -22 11 -21 15 -16.5 C 22 -18 30 -14 31 -8 '
         'C 36 -7.5 39 -3 37.5 1.5 C 36 6.5 31 8 27 8 Z')


def cloud_anim(y, sc, fill, shade, op, dur, beg):
    return (f'<g opacity="{op}"><g>'
            f'<animateTransform attributeName="transform" type="translate" values="-180 {y};1000 {y}" dur="{dur}s" begin="{beg}s" repeatCount="indefinite"/>'
            f'<g transform="scale({sc})"><path d="{CLOUD}" fill="{fill}"/>'
            f'<ellipse cx="-4" cy="5" rx="34" ry="5" fill="{shade}" opacity="0.3"/></g></g></g>')


def sun():
    rays = "".join(f'<path d="M0 -15 L2.1 -23 L-2.1 -23 Z" fill="#FFC069" transform="rotate({a})"/>' for a in range(0, 360, 45))
    return ('<g transform="translate(52,27)">'
            '<circle r="25" fill="#FFD9A0" opacity="0.18"><animate attributeName="opacity" values="0.12;0.24;0.12" keyTimes="0;0.5;1" dur="5s" repeatCount="indefinite"/></circle>'
            '<circle r="17" fill="#FFD9A0" opacity="0.28"/>'
            f'<g opacity="0.75"><animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="80s" repeatCount="indefinite"/>{rays}</g>'
            '<circle r="9.5" fill="#FFC069"/><circle r="9.5" fill="#FFE3B8" opacity="0.5"/></g>')


def clouds_for(w, rnd):
    if w == "clouds":
        cols = ("#CBD5E1", "#9FB0C2")
        cfg = [(20, 0.62, 0.55, 96, -30), (14, 0.95, 0.7, 74, -60), (28, 0.78, 0.62, 84, -12)]
    elif w in ("rain",):
        cols = ("#8E9DB2", "#6C7B92")
        cfg = [(12, 0.85, 0.75, 80, -20), (18, 1.1, 0.85, 62, -48), (10, 0.7, 0.7, 92, -70)]
    elif w == "snow":
        cols = ("#B7C2D2", "#93A2B8")
        cfg = [(12, 0.9, 0.7, 88, -30), (18, 0.8, 0.65, 70, -58)]
    elif w == "storm":
        cols = ("#707E94", "#525F75")
        cfg = [(10, 1.0, 0.9, 66, -18), (16, 1.25, 0.95, 52, -40), (8, 0.8, 0.85, 76, -62)]
    else:
        return ""
    return "".join(cloud_anim(y, sc, cols[0], cols[1], op, dur, beg) for (y, sc, op, dur, beg) in cfg)


def rain_anim(rnd, H):
    out = []
    for _ in range(26):
        x = rnd.randint(0, 900)
        dur = rnd.uniform(0.8, 1.2)
        out.append(f'<g><animateTransform attributeName="transform" type="translate" values="0 -14;0 {H + 16}" dur="{dur:.2f}s" begin="{-rnd.uniform(0, 1.2):.2f}s" repeatCount="indefinite"/>'
                   f'<line x1="{x}" y1="0" x2="{x - 3.5}" y2="9" stroke="#8FA8C4" stroke-width="1" stroke-linecap="round" opacity="0.35"/></g>')
    for _ in range(20):
        x = rnd.randint(0, 900)
        dur = rnd.uniform(0.6, 0.95)
        out.append(f'<g><animateTransform attributeName="transform" type="translate" values="0 -20;0 {H + 22}" dur="{dur:.2f}s" begin="{-rnd.uniform(0, 1):.2f}s" repeatCount="indefinite"/>'
                   f'<line x1="{x}" y1="0" x2="{x - 6}" y2="16" stroke="#8FA8C4" stroke-width="1.6" stroke-linecap="round" opacity="0.6"/></g>')
    return "".join(out)


def snow_anim(rnd, H):
    out = []
    for _ in range(16):
        x = rnd.randint(0, 900)
        dx = rnd.choice([-1, 1]) * rnd.randint(6, 16)
        dur = rnd.uniform(6, 11)
        out.append(f'<g><animateTransform attributeName="transform" type="translate" values="0 -8;{dx} {H // 2};{dx * 2} {H + 8}" keyTimes="0;0.5;1" dur="{dur:.1f}s" begin="{-rnd.uniform(0, 8):.1f}s" repeatCount="indefinite"/>'
                   f'<circle cx="{x}" cy="0" r="{rnd.uniform(1.1, 2.2):.1f}" fill="#C4D2E0" opacity="0.9"/></g>')
    for _ in range(7):
        x = rnd.randint(10, 890)
        s = rnd.uniform(2.8, 4.4)
        dx = rnd.choice([-1, 1]) * rnd.randint(8, 18)
        dur = rnd.uniform(8, 13)
        out.append(f'<g><animateTransform attributeName="transform" type="translate" values="0 -8;{dx} {H // 2};{dx * 2} {H + 8}" keyTimes="0;0.5;1" dur="{dur:.1f}s" begin="{-rnd.uniform(0, 9):.1f}s" repeatCount="indefinite"/>'
                   f'<g transform="translate({x},0)"><g stroke="#B9C9DA" stroke-width="1.1" opacity="0.9">'
                   f'<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="{dur:.1f}s" repeatCount="indefinite"/>'
                   f'<line x1="0" y1="{-s:.1f}" x2="0" y2="{s:.1f}"/><line x1="{-s * 0.87:.1f}" y1="{-s / 2:.1f}" x2="{s * 0.87:.1f}" y2="{s / 2:.1f}"/>'
                   f'<line x1="{-s * 0.87:.1f}" y1="{s / 2:.1f}" x2="{s * 0.87:.1f}" y2="{-s / 2:.1f}"/></g></g></g>')
    return "".join(out)


def fog_anim():
    g = ('<defs><linearGradient id="fogg" x1="0" y1="0" x2="1" y2="0">'
         '<stop offset="0" stop-color="#9FACBC" stop-opacity="0"/><stop offset="0.18" stop-color="#9FACBC" stop-opacity="1"/>'
         '<stop offset="0.82" stop-color="#9FACBC" stop-opacity="1"/><stop offset="1" stop-color="#9FACBC" stop-opacity="0"/></linearGradient></defs>')
    bands = ""
    for i, (x, y, w, h, op, dur) in enumerate([(60, 12, 500, 13, 0.38, 30), (300, 28, 560, 14, 0.34, 38),
                                               (-40, 42, 480, 13, 0.3, 33), (420, 52, 460, 12, 0.26, 42)]):
        d = 90 if i % 2 == 0 else -90
        bands += (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h / 2}" fill="url(#fogg)" opacity="{op}">'
                  f'<animateTransform attributeName="transform" type="translate" values="0 0;{d} 0;0 0" {SPLINE2} dur="{dur}s" repeatCount="indefinite"/></rect>')
    return g + bands


def storm_extras(rnd, H):
    x = rnd.randint(240, 660)
    kt = 'keyTimes="0;0.52;0.545;0.57;0.585;0.61;1" dur="7s" repeatCount="indefinite"'
    return (f'<rect x="0" y="0" width="900" height="{H}" fill="#FFF3C4" opacity="0">'
            f'<animate attributeName="opacity" values="0;0;0.26;0;0.13;0;0" {kt}/></rect>'
            f'<g transform="translate({x},4)" opacity="0">'
            f'<animate attributeName="opacity" values="0;0;1;0;0.5;0;0" {kt}/>'
            f'<path d="M6 0 L-5 26 L4 24 L-10 56 M-1 19 L-15 31" stroke="#FFE9A8" stroke-width="6" fill="none" stroke-linecap="round" opacity="0.3"/>'
            f'<path d="M6 0 L-5 26 L4 24 L-10 56 M-1 19 L-15 31" stroke="#FFE9A8" stroke-width="2.4" fill="none" stroke-linecap="round"/></g>')


def weather_layer(w, rnd, H):
    out = [clouds_for(w, rnd)]
    if w in ("rain", "storm"):
        out.append(rain_anim(rnd, H))
    if w == "snow":
        out.append(snow_anim(rnd, H))
    if w == "fog":
        out.append(fog_anim())
    if w == "storm":
        out.append(storm_extras(rnd, H))
    return "".join(out)


# ---------------- butterfly ----------------
def butterfly_body(scale=1.0):
    return (f'<g transform="scale({scale})">'
            '<g><animateTransform attributeName="transform" type="scale" values="1 1;1 0.3;1 1" keyTimes="0;0.5;1" dur="0.5s" repeatCount="indefinite"/>'
            '<path d="M1 -1 C 7 -15, -13 -17, -6 -2 Z" fill="#F4795B" opacity="0.9"/>'
            '<path d="M-3 -1 C -7 -13, -17 -8, -9 -1 Z" fill="#FBC7B3" opacity="0.85"/>'
            '<path d="M1 1 C 7 15, -13 17, -6 2 Z" fill="#F4795B" opacity="0.9"/>'
            '<path d="M-3 1 C -7 13, -17 8, -9 1 Z" fill="#FBC7B3" opacity="0.85"/></g>'
            '<ellipse rx="5.5" ry="1.8" fill="#A33D22"/>'
            '<path d="M5 -1 Q 9 -5 11 -6 M5 1 Q 9 5 11 6" stroke="#A33D22" stroke-width="0.8" fill="none"/></g>')


def butterfly_patrol(path, dur):
    return ('<g opacity="0">'
            f'<animate attributeName="opacity" values="0;0.95;0.95;0" keyTimes="0;0.05;0.95;1" dur="{dur}s" begin="1s" repeatCount="indefinite"/>'
            f'<g><animateMotion dur="{dur}s" begin="1s" repeatCount="indefinite" rotate="auto" path="{path}"/>'
            + butterfly_body() + '</g></g>')


# ---------------- cat (Neko sprites from oneko / adryd325/oneko.js) ----------------
try:
    from cat_sprite import SHEET_B64, SPRITES
except ImportError:
    from scripts.cat_sprite import SHEET_B64, SPRITES

NEKO_DEFS = ('<clipPath id="nekoclip"><rect width="32" height="32"/></clipPath>'
             f'<image id="nekoimg" width="256" height="128" href="data:image/png;base64,{SHEET_B64}" '
             'style="image-rendering:pixelated"/>')


def neko_state(state, v, k, frame_dur=0.2, arc=""):
    """One sprite state, gated to a cycle window; multi-frame states cycle via discrete translate."""
    cells = SPRITES[state]
    if len(cells) > 1:
        vals = ";".join(f"{cx * 32} {cy * 32}" for cx, cy in cells)
        anim = (f'<animateTransform attributeName="transform" type="translate" values="{vals}" '
                f'calcMode="discrete" dur="{len(cells) * frame_dur:.2f}s" repeatCount="indefinite"/>')
        tr = ""
    else:
        anim = ""
        cx, cy = cells[0]
        tr = f' transform="translate({cx * 32},{cy * 32})"'
    inner = f'<g clip-path="url(#nekoclip)"><g{tr}>{anim}<use href="#nekoimg"/></g></g>'
    if arc:
        inner = f'<g>{arc}{inner}</g>'
    return (f'<g opacity="0"><animate attributeName="opacity" values="{v}" keyTimes="{k}" '
            f'calcMode="discrete" {CYC}/>{inner}</g>')


def cat_show(season):
    """75s Neko show: dash in -> spot butterfly -> pounce -> chase -> paw at the progress bar ->
    jump for it (misses) -> yawn -> nap -> startle awake -> dash off."""
    arc_pounce = (f'<animateTransform attributeName="transform" type="translate" '
                  f'values="0 0;0 0;0 -28;0 0;0 0" keyTimes="0;0.21;0.235;0.26;1" {CYC}/>')
    arc_jump = (f'<animateTransform attributeName="transform" type="translate" '
                f'values="0 0;0 0;0 -55;0 0;0 0" keyTimes="0;0.46;0.48;0.50;1" {CYC}/>')
    st = [
        neko_state("W", "0;1;0;1;0;1;0", "0;0.04;0.16;0.26;0.34;0.64;0.72", 0.15),
        neko_state("idle", "0;1;0", "0;0.16;0.185"),
        neko_state("alert", "0;1;0;1;0", "0;0.185;0.21;0.62;0.64"),
        neko_state("NW", "0;1;0", "0;0.21;0.26", 0.15, arc_pounce),
        neko_state("scratchWallN", "0;1;0", "0;0.34;0.46", 0.25),
        neko_state("N", "0;1;0", "0;0.46;0.50", 0.15, arc_jump),
        neko_state("tired", "0;1;0", "0;0.50;0.54"),
        neko_state("sleeping", "0;1;0", "0;0.54;0.62", 0.8),
    ]
    body = f'<g transform="translate(-21,-41) scale(1.3)">{"".join(st)}</g>'
    flyby = ""
    if season != "winter":
        flyby = ('<g opacity="0"><animate attributeName="opacity" values="0;1;0" keyTimes="0;0.17;0.25" '
                 f'calcMode="discrete" {CYC}/>'
                 f'<g><animateMotion path="M980 55 C 880 75 780 48 700 68 C 650 80 610 62 575 70 C 545 76 520 45 470 -25" '
                 f'keyPoints="0;0;0.6;0.75;1;1" keyTimes="0;0.17;0.20;0.21;0.25;1" calcMode="linear" rotate="auto" {CYC}/>'
                 + butterfly_body(0.75) + '</g></g>')
    return ('<g><animateTransform attributeName="transform" type="translate" '
            f'values="950 0;950 0;560 0;560 0;300 0;300 0;-140 0;-140 0" '
            f'keyTimes="0;0.04;0.16;0.26;0.34;0.64;0.72;1" {CYC}/>'
            f'<g transform="translate(0,130)">{body}</g></g>' + flyby)


# ---------------- sky ----------------
def gen_sky(w, s):
    rnd = random.Random(f"sky-{w}-{s}")
    H = 70
    base = ['<defs><path id="spet" d="M0 0 C-4 -5 -4 -13 0 -17 C4 -13 4 -5 0 0 Z"/>'
            '<path id="sleaf" d="M0 0 Q-7 -3 -9 -10 Q-3 -8 0 0 Z"/></defs>']

    def drifting(shape, count, colors):
        out = []
        for _ in range(count):
            px = rnd.randint(30, 870)
            drift = rnd.choice([-1, 1]) * rnd.randint(16, 34)
            dur, beg = rnd.uniform(7, 12), rnd.uniform(0, 6)
            c = rnd.choice(colors)
            out.append(f'<g transform="translate({px},-10)" opacity="0">'
                       f'<animate attributeName="opacity" values="0;0.7;0.7;0" keyTimes="0;0.1;0.75;1" dur="{dur:.1f}s" begin="{beg:.1f}s" repeatCount="indefinite"/>'
                       f'<g><animateTransform attributeName="transform" type="translate" values="0 0;{drift} {H // 2 + 10};{drift * 2} {H + 20}" keyTimes="0;0.5;1" dur="{dur:.1f}s" begin="{beg:.1f}s" repeatCount="indefinite"/>'
                       f'<use href="#{shape}" fill="{c}">'
                       f'<animateTransform attributeName="transform" type="rotate" values="0;170;350" keyTimes="0;0.5;1" dur="{dur:.1f}s" begin="{beg:.1f}s" repeatCount="indefinite"/>'
                       f'</use></g></g>')
        return "".join(out)

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
        base.append(drifting("spet", 2, ["#FBC7B3", "#F4795B"]))
    if s == "autumn":
        base.append(drifting("sleaf", 4, ["#C46A38", "#D98E4A", "#B57B3F"]))
    base.append(weather_layer(w, rnd, H))
    if s in ("spring", "summer") and w in ("clear", "clouds"):
        base.append(butterfly_patrol("M880 30 C700 60 560 5 420 40 C300 68 160 15 20 38 C160 62 340 20 520 50 C680 72 800 45 880 30", 15))
    base.append(f'<text x="893" y="64" text-anchor="end" font-size="9" letter-spacing="1.5" fill="#8b949e">LIVE SKY · {w.upper()} · {s.upper()}</text>')

    def wrap(inner):
        return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 70" width="900" height="70" '
                'font-family="Segoe UI, Ubuntu, Helvetica, Arial, sans-serif">\n<title>sky</title>' + inner + '</svg>\n')

    day = wrap("".join(base))
    night = wrap(stars(9, 30, 870, 8, 58, 11) + nightify("".join(base)))
    return day, night


# ---------------- footer ----------------
SEASON_CFG = {
    "spring": dict(greens=["#7FA36B", "#8CB07A", "#A8C79A"], daisies=4, fireflies=5, ground=("#FBC7B3", 0.2)),
    "summer": dict(greens=["#5E8B4F", "#6FA35E", "#87B573"], daisies=4, fireflies=7, ground=("#F9B98A", 0.22)),
    "autumn": dict(greens=["#C98F4E", "#B57B3F", "#D9A863"], daisies=1, fireflies=3, ground=("#D9A863", 0.22)),
    "winter": dict(greens=["#9AA79A", "#B3BDB3", "#8B978B"], daisies=0, fireflies=0, ground=("#EDF2F7", 0.45)),
}
BACK_GREENS = {"spring": "#B7CCA8", "summer": "#9DBE8D", "autumn": "#DDBA84", "winter": "#C2CCC2"}
FIREFLY_SPOTS = [(150, 70, 9, 2.0, 2.4), (320, 50, 11, 3.2, 3.0), (480, 82, 8.5, 2.6, 2.2),
                 (610, 45, 10, 4.0, 2.8), (760, 72, 9.5, 3.5, 2.5), (870, 55, 11.5, 2.2, 3.2), (60, 46, 10.5, 4.4, 2.6)]
DAISY_SPOTS = [(120, 118, 0.9, 1.2), (382, 124, 0.7, 1.6), (633, 120, 0.85, 1.4), (818, 126, 0.65, 1.8)]


def gen_footer(w, s):
    cfg = SEASON_CFG[s]
    rnd = random.Random(f"footer-{s}")
    p = ['<defs><path id="fpetal" d="M0 0 C-4 -5 -4 -13 0 -17 C4 -13 4 -5 0 0 Z"/>'
         '<path id="fleaf" d="M0 0 Q-7 -3 -9 -10 Q-3 -8 0 0 Z"/>' + NEKO_DEFS + '</defs>']
    g, gop = cfg["ground"]
    p.append(f'<ellipse cx="450" cy="152" rx="480" ry="26" fill="{g}" opacity="{gop}"/>')
    if s == "winter":
        for (dx, rx) in [(180, 120), (450, 160), (740, 110)]:
            p.append(f'<ellipse cx="{dx}" cy="138" rx="{rx}" ry="7" fill="#EDF2F7" opacity="0.55"/>')
    # back layer: dense short blades (depth texture)
    bg = BACK_GREENS[s]
    x = 6
    while x < 896:
        h = rnd.randint(13, 30) if s != "winter" else rnd.randint(9, 20)
        bend = rnd.choice([-1, 1]) * rnd.randint(2, 6)
        p.append(f'<path d="M{x} 140 Q{x + bend} {140 - h * 0.6:.0f} {x + bend * 1.7:.0f} {140 - h}" '
                 f'stroke="{bg}" stroke-width="2" fill="none" stroke-linecap="round" opacity="0.55"/>')
        x += rnd.randint(6, 12) if s != "winter" else rnd.randint(10, 18)
    p.append(cat_show(s))
    # seed stalks: tall, sway strongly
    for _ in range(5 if s != "winter" else 3):
        sx = rnd.randint(40, 860)
        h = rnd.randint(52, 68) if s != "winter" else rnd.randint(38, 50)
        bend = rnd.choice([-1, 1]) * rnd.randint(5, 9)
        g2 = rnd.choice(cfg["greens"])
        sway, beg = rnd.uniform(3, 5), rnd.uniform(0, 3)
        p.append(f'<g transform="translate({sx},140)"><g>'
                 f'<animateTransform attributeName="transform" type="rotate" values="-5;5;-5" '
                 f'{SPLINE2} dur="{sway:.2f}s" begin="-{beg:.2f}s" repeatCount="indefinite"/>'
                 f'<path d="M0 0 Q{bend} {-h * 0.6:.0f} {bend * 1.6:.0f} {-h}" '
                 f'stroke="{g2}" stroke-width="1.8" fill="none" stroke-linecap="round" opacity="0.8"/>'
                 f'<ellipse cx="{bend * 1.6:.0f}" cy="{-h - 3}" rx="2.2" ry="4.5" fill="{g2}" opacity="0.75"/>'
                 f'</g></g>')
    # front clumps: 3-6 fanned blades per root, clump-level sway, grow-in entrance
    x = 20
    while x < 890:
        n = rnd.randint(3, 6)
        sway, beg = rnd.uniform(3.2, 6.2), rnd.uniform(0, 4)
        amp = rnd.uniform(2.5, 5)
        t = rnd.uniform(0.1, 1.1)
        blades = []
        for k in range(n):
            ang = -22 + k * (44 / max(n - 1, 1)) + rnd.uniform(-5, 5)
            h = rnd.randint(26, 58) if s != "winter" else rnd.randint(16, 34)
            g2 = rnd.choice(cfg["greens"])
            w2 = rnd.choice([2.2, 2.6, 3])
            blades.append(f'<g transform="rotate({ang:.0f})"><path d="M0 0 Q{rnd.choice([-1, 1]) * 3} {-h * 0.55:.0f} {rnd.choice([-1, 1]) * 5} {-h}" '
                          f'stroke="{g2}" stroke-width="{w2}" fill="none" stroke-linecap="round" opacity="0.85"/></g>')
        p.append(f'<g transform="translate({x + rnd.randint(-2, 2)},140)"><g opacity="0">'
                 f'<animate attributeName="opacity" from="0" to="1" begin="{t:.2f}s" dur="0.6s" fill="freeze"/>'
                 f'<animateTransform attributeName="transform" type="scale" from="1 0" to="1 1" begin="{t:.2f}s" dur="0.7s" '
                 f'calcMode="spline" keyTimes="0;1" keySplines="0.2 0.8 0.3 1" fill="freeze"/>'
                 f'<g><animateTransform attributeName="transform" type="rotate" values="{-amp:.1f};{amp:.1f};{-amp:.1f}" '
                 f'{SPLINE2} dur="{sway:.2f}s" begin="-{beg:.2f}s" repeatCount="indefinite"/>'
                 + "".join(blades) + '</g></g></g>')
        x += rnd.randint(40, 70) if s != "winter" else rnd.randint(70, 110)
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

    def drifting_footer(shape, count, colors):
        out = []
        for _ in range(count):
            px = rnd.randint(30, 870)
            drift = rnd.choice([-1, 1]) * rnd.randint(16, 34)
            dur, beg = rnd.uniform(7, 12), rnd.uniform(0, 6)
            c = rnd.choice(colors)
            out.append(f'<g transform="translate({px},-10)" opacity="0">'
                       f'<animate attributeName="opacity" values="0;0.7;0.7;0" keyTimes="0;0.1;0.75;1" dur="{dur:.1f}s" begin="{beg:.1f}s" repeatCount="indefinite"/>'
                       f'<g><animateTransform attributeName="transform" type="translate" values="0 0;{drift} 75;{drift * 2} 150" keyTimes="0;0.5;1" dur="{dur:.1f}s" begin="{beg:.1f}s" repeatCount="indefinite"/>'
                       f'<use href="#{shape}" fill="{c}">'
                       f'<animateTransform attributeName="transform" type="rotate" values="0;170;350" keyTimes="0;0.5;1" dur="{dur:.1f}s" begin="{beg:.1f}s" repeatCount="indefinite"/>'
                       f'</use></g></g>')
        return "".join(out)

    if s == "spring":
        p.append(drifting_footer("fpetal", 4, ["#F4795B", "#FBC7B3", "#ED8B66"]))
    if s == "autumn":
        p.append(drifting_footer("fleaf", 6, ["#C46A38", "#D98E4A", "#B57B3F"]))
    if s == "winter" or w == "snow":
        p.append(snow_anim(random.Random(f"fsnow-{s}"), 140))

    def wrap(inner):
        return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 140" width="900" height="140">\n'
                '<title>garden footer - cat: Neko sprites via adryd325/oneko.js</title>' + inner + '</svg>\n')

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
