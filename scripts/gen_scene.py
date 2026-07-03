#!/usr/bin/env python3
"""Living scene: weather-synced sky strip + seasonal garden footer, day & night variants.
Runs in CI every few hours. Deterministic per (weather, season) so unchanged state = no diff.

Usage: gen_scene.py [--weather clear|clouds|rain|snow|fog|storm] [--season spring|summer|autumn|winter] [--force]
"""
import json
import math
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


# ---------------- cat ----------------
def cat_head(blink=False, twitch=False):
    # clean all-black silhouette: round head + small ears, no facial features
    ear_anim = (f'<animateTransform attributeName="transform" type="rotate" values="0;0;15;3;11;0;0" '
                f'keyTimes="0;0.492;0.50;0.508;0.516;0.524;1" {CYC}/>') if twitch else ''
    return (f'<g>{ear_anim}<path d="M-7.2 -5 L-6.6 -12.8 L-1.6 -6.8 Z" fill="{C}"/></g>'
            f'<path d="M1.6 -6.8 L6.4 -12.8 L7 -5 Z" fill="{C}"/>'
            f'<circle r="8.2" fill="{C}"/>')


def cat_leg(x, y, a, b, beg, faded=False):
    op = ' opacity="0.75"' if faded else ''
    return (f'<g transform="translate({x},{y})"><path d="M-1.8 0 L1.8 0 L1.4 11.6 Q0 13.2 -1.4 11.6 Z" fill="{C}"{op}>'
            f'<animateTransform attributeName="transform" type="rotate" values="{a};{b};{a}" {SPLINE2} dur="0.6s" begin="{beg}s" repeatCount="indefinite"/></path></g>')


def slim_leg(x1, y1, x2, y2, w=3.2, faded=False):
    op = ' opacity="0.78"' if faded else ''
    return f'<path d="M{x1} {y1} L{x2} {y2}" stroke="{C}" stroke-width="{w}" stroke-linecap="round" fill="none"{op}/>'


CAT_BODY = ('M-13 -24 C -6 -29.5 6 -30 12 -24.5 C 16 -20.5 17 -13.5 14.5 -9 C 13.4 -7.2 11.4 -6.4 9.4 -6.4 '
            'L -7.4 -6.4 C -10.6 -6.4 -12.9 -9.2 -13.7 -13.2 C -14.4 -17.2 -14.2 -21.4 -13 -24 Z')


def cat_gait(gait_dur, amp, bob, tail_vals, tail_dur):
    return ('<g>'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;0 {-bob};0 0" {SPLINE2} dur="{gait_dur}s" repeatCount="indefinite"/>'
            + cat_leg(-6, -12, -amp + 2, amp - 2, -gait_dur / 2, True) + cat_leg(11, -12, amp - 4, -amp + 4, -gait_dur / 2, True)
            + f'<path d="{CAT_BODY}" fill="{C}"/>'
            + cat_leg(-9, -12, amp, -amp, 0) + cat_leg(14, -12, -amp + 3, amp - 3, 0)
            + f'<g transform="translate(13.5,-20)"><path d="M0 1.5 C 7.5 0.5 11.5 -6 9.8 -13.5 C 8.8 -17.5 5.8 -19.8 3.2 -19" stroke="{C}" stroke-width="3.6" fill="none" stroke-linecap="round">'
            f'<animateTransform attributeName="transform" type="rotate" values="{tail_vals}" {SPLINE2} dur="{tail_dur}s" repeatCount="indefinite"/></path></g>'
            + f'<g transform="translate(-15.5,-22.5)">{cat_head()}</g>'
            + '</g>')


def cat_pose_walk():
    return cat_gait(0.5, 18, 1.4, "-8;8;-8", 1.4)


def cat_pose_dash():
    return cat_gait(0.32, 24, 2.0, "-26;-14;-26", 0.4)


def cat_pose_sit():
    look = (f'<animateTransform attributeName="transform" type="rotate" values="0;0;-14;-14;0;0" '
            f'keyTimes="0;0.492;0.50;0.51;0.518;1" {CYC}/>')
    return ('<g>'
            f'<g transform="translate(12,-2)"><path d="M0 0 C 3 2.5 -1 4.2 -7 4 C -13.5 3.8 -18 2.2 -19.5 0.2" stroke="{C}" stroke-width="3.4" fill="none" stroke-linecap="round">'.replace("{C}", C)
            + f'<animateTransform attributeName="transform" type="rotate" values="0;0;7;0;0" keyTimes="0;0.7;0.79;0.88;1" dur="6s" repeatCount="indefinite"/></path></g>'
            + '<g><animateTransform attributeName="transform" type="scale" values="1 1;1 1.018;1 1" keyTimes="0;0.5;1" dur="3.4s" repeatCount="indefinite"/>'
            + f'<path d="M-9.5 0 C -10.5 -7 -9.5 -15 -5.5 -20.5 C -2.5 -24.5 3.5 -26 8 -23.5 C 12.5 -21 14.5 -15.5 14 -9.5 C 13.7 -5.5 12.8 -2 12 0 Z" fill="{C}"/>'
            + f'<rect x="-9.2" y="-10" width="3.2" height="10" rx="1.5" fill="{C}"/>'
            + f'<g transform="translate(-4.5,-27)"><g>{look}{cat_head(blink=True, twitch=True)}</g></g>'
            + '</g></g>')


def cat_pose_stretch():
    return ('<g>'
            f'<g transform="translate(15.5,-17)"><path d="M0 0 C 5 -4 6 -11 2.5 -15 C 0.5 -17.5 -2.5 -18 -4 -16.5" stroke="{C}" stroke-width="3.4" fill="none" stroke-linecap="round">'.replace("{C}", C)
            + f'<animateTransform attributeName="transform" type="rotate" values="-10;10;-10" {SPLINE2} dur="1.8s" repeatCount="indefinite"/></path></g>'
            + f'<rect x="9.5" y="-9" width="3.2" height="9" rx="1.5" fill="{C}"/>'
            + f'<rect x="13" y="-8.5" width="3.2" height="8.5" rx="1.5" fill="{C}" opacity="0.8"/>'
            + f'<path d="M-12 -6 C -6 -9 0 -13.5 5 -17.5 C 9 -20.5 14 -19.5 15.7 -15 C 17 -11 16 -6 13.8 -3.2 C 12.8 -1.8 11 -1.2 9.2 -1.2 L 2 -1.2 C -3 -1.2 -8 -3.5 -12 -6 Z" fill="{C}"/>'
            + f'<path d="M-10 -5.5 L-18.5 -0.8 Q-19.6 0 -18.4 0.4 L-15.4 0.4 L-8.4 -3.6 Z" fill="{C}"/>'
            + f'<path d="M-8 -4.5 L-15.5 -0.2 Q-16.4 0.5 -15.2 0.8 L-12.4 0.8 L-6 -2.8 Z" fill="{C}" opacity="0.8"/>'
            + f'<g transform="translate(-14.5,-11) rotate(12)">{cat_head()}</g>'
            '</g>')


def cat_pose_crouch():
    return ('<g>'
            '<g><animateTransform attributeName="transform" type="rotate" values="0;2.5;0;-2;0" keyTimes="0;0.25;0.5;0.75;1" dur="0.5s" repeatCount="indefinite"/>'
            f'<g transform="translate(13,-6)"><path d="M0 0 C 6.5 1.5 10 -2 9.5 -8 C 9.2 -11.5 7 -13.5 5 -13" stroke="{C}" stroke-width="3.6" fill="none" stroke-linecap="round">'
            '<animateTransform attributeName="transform" type="rotate" values="-6;10;-6" keyTimes="0;0.5;1" dur="0.5s" repeatCount="indefinite"/></path></g>'
            f'<ellipse cx="8.5" cy="-8.5" rx="7" ry="6" fill="{C}"/></g>'
            f'<path d="M-14 -9 C -8 -14.5 4 -15.5 11 -12 C 15 -10 16 -6.5 14.5 -4 C 13.5 -2.2 11 -1.8 9 -1.8 L -10 -1.8 C -13.2 -1.8 -15 -5.5 -14 -9 Z" fill="{C}"/>'
            + slim_leg(-11, -3, -7, -1.4, 3.4)
            + f'<g transform="translate(-16.5,-10.5)">{cat_head()}</g>'
            '</g>')


def cat_pose_pounce():
    return ('<g transform="rotate(-16)">'
            f'<g transform="translate(13,-13)"><path d="M0 0 C 6 -2 8.5 -8 6.5 -14 C 5.5 -17 3 -18.5 1 -17.5" stroke="{C}" stroke-width="3.6" fill="none" stroke-linecap="round"/></g>'
            + slim_leg(9, -9, 20, -3.5, 3.4, True)
            + slim_leg(11, -10, 22, -6, 3.4)
            + f'<path d="M-15 -13.5 C -9 -19 3 -20 9.5 -16.5 C 13.8 -14 15 -10.5 13.5 -7.5 C 12.2 -5 8.5 -4.5 5.5 -5 L -12 -8 C -15 -8.6 -16.2 -11 -15 -13.5 Z" fill="{C}"/>'
            + slim_leg(-11, -9, -21.5, -1.5, 3.4, True)
            + slim_leg(-9, -8, -19.5, 0.5, 3.4)
            + f'<g transform="translate(-17.5,-15.5) rotate(-8)">{cat_head()}</g>'
            '</g>')


def cat_pose_reach():
    return ('<g>'
            f'<g transform="translate(6,-6)"><path d="M0 0 C 5 3 9.5 1 10.5 -4.5 C 11 -8 9 -10.5 6.5 -10.5" stroke="{C}" stroke-width="3.6" fill="none" stroke-linecap="round">'
            '<animateTransform attributeName="transform" type="rotate" values="-8;8;-8" keyTimes="0;0.5;1" dur="1.2s" repeatCount="indefinite"/></path></g>'
            + slim_leg(-1.5, -7, -2, 0, 3.4)
            + slim_leg(3.5, -6.5, 4, 0, 3.4, True)
            + f'<path d="M-5.5 -8 C -8.5 -14 -8 -25 -3.5 -31.5 C -0.5 -35.5 5 -35 7.5 -30.5 C 10.5 -25 10 -14 7 -7 C 5.5 -3.8 2.5 -3 -0.5 -4 Z" fill="{C}"/>'
            + slim_leg(-4.5, -30, -8.5, -43, 3.2)
            + slim_leg(5, -30, 8, -43.5, 3.2, True)
            + f'<g transform="translate(-2,-36) rotate(-18)">{cat_head()}</g>'
            '</g>')


def cat_pose_jump_up():
    """Airborne, rising: body stretched vertical, hind legs trailing behind, forepaws reaching."""
    return ('<g>'
            f'<g transform="translate(7,-7)"><path d="M0 0 C 4 4 4.5 10 1 14" stroke="{C}" stroke-width="3.4" fill="none" stroke-linecap="round"/></g>'
            + slim_leg(-1, -5, -4, 7, 3.3)
            + slim_leg(4, -4.5, 8, 8, 3.3, True)
            + f'<path d="M-5.5 -8 C -8.5 -14 -8 -25 -3.5 -31.5 C -0.5 -35.5 5 -35 7.5 -30.5 C 10.5 -25 10 -14 7 -7 C 5.5 -3.8 2.5 -3 -0.5 -4 Z" fill="{C}"/>'
            + slim_leg(-4.5, -30, -8.5, -43, 3.2)
            + slim_leg(5, -30, 8, -43.5, 3.2, True)
            + f'<g transform="translate(-2,-36) rotate(-22)">{cat_head()}</g>'
            '</g>')


def cat_pose_fall():
    """Airborne, descending vertically: body upright, forepaws reaching DOWN as landing
    gear, hind legs tucked, tail up for balance, head looking down at the ground."""
    return ('<g>'
            f'<g transform="translate(6,-9)"><path d="M0 0 C 7 -2 10 -9 7 -16" stroke="{C}" stroke-width="3.3" fill="none" stroke-linecap="round"/></g>'
            + slim_leg(-2, -12, -5, -4, 3.3)
            + slim_leg(4, -12, 7, -4, 3.3, True)
            + f'<path d="M-5.5 -8 C -8.5 -14 -8 -25 -3.5 -31.5 C -0.5 -35.5 5 -35 7.5 -30.5 C 10.5 -25 10 -14 7 -7 C 5.5 -3.8 2.5 -3 -0.5 -4 Z" fill="{C}"/>'
            + slim_leg(-3, -9, -6, 7, 3.2)
            + slim_leg(3.5, -9, 6, 7, 3.2, True)
            + f'<g transform="translate(-1,-33) rotate(10)">{cat_head()}</g>'
            '</g>')


def cat_pose_stand():
    return ('<g>'
            + slim_leg(-8, -11, -8.5, 0, 3.4) + slim_leg(-5, -11, -4.5, 0, 3.4, True)
            + slim_leg(11, -11, 11.5, 0, 3.4) + slim_leg(14, -11, 14.5, 0, 3.4, True)
            + f'<path d="M-12.5 -24 C -6 -29.5 5 -30 10.5 -24.8 C 14.5 -21 15.5 -14 13.5 -9.2 C 12.5 -7.3 10.7 -6.4 8.8 -6.4 L -7 -6.4 C -10.2 -6.4 -12.4 -9.2 -13.2 -13.2 C -13.9 -17.2 -13.7 -21.4 -12.5 -24 Z" fill="{C}"/>'
            f'<g transform="translate(12.5,-20)"><path d="M0 1.5 C 7 0.5 10.5 -6 9 -13 C 8 -16.5 5.5 -18.5 3 -17.8" stroke="{C}" stroke-width="3.6" fill="none" stroke-linecap="round">'
            '<animateTransform attributeName="transform" type="rotate" values="-6;6;-6" keyTimes="0;0.5;1" dur="2s" repeatCount="indefinite"/></path></g>'
            + f'<g transform="translate(-13.5,-22.5) rotate(-17)">{cat_head()}</g>'
            '</g>')


def cat_show(season):
    """75s show: trot in -> spot butterfly, crouch -> POUNCE -> dash chase ->
    stare up at the progress bar -> two jump attempts (both miss) -> sit -> stretch -> zoomies out."""
    pose = ('<g opacity="0"><animate attributeName="opacity" values="{v}" keyTimes="{k}" '
            f'calcMode="discrete" {CYC}/>' + '{body}</g>')
    walk = pose.format(v="0;1;0", k="0;0.04;0.15", body=cat_pose_walk())
    dash = pose.format(v="0;1;0;1;0", k="0;0.235;0.30;0.60;0.70", body=cat_pose_dash())
    # landing compression is played by the crouch pose right after each touchdown
    crouch = pose.format(v="0;1;0;1;0;1;0;1;0;0",
                         k="0;0.15;0.20;0.345;0.362;0.376;0.408;0.423;0.443;1",
                         body=cat_pose_crouch())
    pounce = pose.format(v="0;1;0", k="0;0.20;0.235",
                         body=('<g><animateTransform attributeName="transform" type="translate" '
                               f'values="0 0;0 0;0 -30;0 0;0 0" keyTimes="0;0.20;0.2175;0.235;1" '
                               'calcMode="spline" keySplines="0 0 1 1;0.12 0.88 0.34 1;0.62 0 0.95 0.45;0 0 1 1" '
                               f'{CYC}/>' + cat_pose_pounce() + '</g>'))
    stand = pose.format(v="0;1;0", k="0;0.30;0.345", body=cat_pose_stand())

    def puff(tl):
        """Dust kicked up at touchdown."""
        return ('<g opacity="0">'
                f'<animate attributeName="opacity" values="0;0;0.5;0;0" keyTimes="0;{tl:.4f};{tl + 0.003:.4f};{tl + 0.009:.4f};1" {CYC}/>'
                f'<g><animateTransform attributeName="transform" type="scale" values="0.3;0.3;1.6;0.3" keyTimes="0;{tl:.4f};{tl + 0.009:.4f};1" {CYC}/>'
                '<circle cx="-8" cy="-2" r="2" fill="#BFB49F"/><circle cx="8" cy="-2" r="2.2" fill="#BFB49F"/>'
                '<circle cx="0" cy="-4" r="1.7" fill="#BFB49F"/></g></g>')

    def jump(t0, t1, h, forward=-4.0):
        """Baked physics. Newtonian projectile integrated offline: a short ground-contact
        thrust brings the CoM from rest to v0 = sqrt(2gh), then ballistic flight under
        gravity g traces a true parabola (fast rise -> apex dwell -> accelerating fall),
        then landing compression absorbs the impact. Sampled every ~10ms so SMIL linear
        interpolation reproduces the real trajectory instead of an eyeballed spline."""
        g = 1600.0
        v0 = (2 * g * h) ** 0.5
        t_up = v0 / g
        t_thrust, t_flight, t_absorb, t_settle = 0.11, 2 * t_up, 0.13, 0.09
        total = t_thrust + t_flight + t_absorb + t_settle
        dt = 0.01
        # each sample: (t, y, x, pitch, sx, sy) — sx/sy carry squash & stretch synced to speed
        pts = []
        n = max(int(t_thrust / dt), 1)
        for i in range(n):                                   # thrust: load squash -> explosive stretch
            f = i / n
            sq = math.sin(math.pi * f)
            pts.append((f * t_thrust, -4.0 * sq, 0.0, 10.0 * f, 1 + 0.16 * sq, 1 - 0.22 * sq))
        tf = 0.0
        while tf <= t_flight + 1e-9:                         # flight: exact gravity parabola
            y = v0 * tf - 0.5 * g * tf * tf
            sp = min(abs(v0 - g * tf) / v0, 1.0)             # normalized vertical speed
            pitch = 6.0 * (1 - tf / t_up) if tf <= t_up else -8.0 * ((tf - t_up) / t_up)
            pts.append((t_thrust + tf, y, forward * (tf / t_flight), pitch, 1 - 0.15 * sp, 1 + 0.30 * sp))
            tf += dt
        n = max(int(t_absorb / dt), 1)
        for i in range(1, n + 1):                            # absorb: splat squash on impact, spring back
            f = i / n
            sq = math.sin(math.pi * f)
            pts.append((t_thrust + t_flight + f * t_absorb, -8.0 * sq, forward, -8.0 * (1 - f), 1 + 0.26 * sq, 1 - 0.28 * sq))
        pts.append((total, 0.0, forward, 0.0, 1.0, 1.0))     # settle
        kts, tv, rv, sv = ["0"], ["0 0"], ["0 0 -20"], ["1 1"]
        for (t, y, x, pitch, sx, sy) in pts:
            kts.append(f"{t0 + (t / total) * (t1 - t0):.4f}")
            tv.append(f"{x:.1f} {-y:.1f}")
            rv.append(f"{-pitch:.2f} 0 -20")
            sv.append(f"{sx:.3f} {sy:.3f}")
        kts.append("1"); tv.append("0 0"); rv.append("0 0 -20"); sv.append("1 1")
        kt = ";".join(kts)
        arc = f'<animateTransform attributeName="transform" type="translate" values="{";".join(tv)}" keyTimes="{kt}" calcMode="linear" {CYC}/>'
        spin = f'<animateTransform attributeName="transform" type="rotate" values="{";".join(rv)}" keyTimes="{kt}" calcMode="linear" {CYC}/>'
        squash = f'<animateTransform attributeName="transform" type="scale" values="{";".join(sv)}" keyTimes="{kt}" calcMode="linear" {CYC}/>'
        pb = lambda tt: t0 + (tt / total) * (t1 - t0)
        e_th, e_ap, e_fl = pb(t_thrust), pb(t_thrust + t_up), pb(t_thrust + t_flight)
        rear = pose.format(v="0;1;0", k=f"0;{t0};{e_th:.4f}", body=f'<g transform="rotate(8)">{cat_pose_reach()}</g>')
        rise = pose.format(v="0;1;0", k=f"0;{e_th:.4f};{e_ap:.4f}", body=cat_pose_jump_up())
        fall = pose.format(v="0;1;0", k=f"0;{e_ap:.4f};{e_fl:.4f}", body=cat_pose_fall())
        touch = pose.format(v="0;1;0", k=f"0;{e_fl:.4f};{t1}", body=cat_pose_crouch())
        # nesting: translate(arc) > rotate(spin, about body-centre) > scale(squash, about feet) > pose swaps
        return f'<g>{arc}<g>{spin}<g>{squash}{rear}{rise}{fall}{touch}</g></g></g>' + puff(e_fl)

    jump1 = jump(0.362, 0.376, 50)
    jump2 = jump(0.408, 0.423, 66)
    sit = pose.format(v="0;1;0", k="0;0.443;0.55", body=cat_pose_sit())
    stretch = pose.format(v="0;1;0", k="0;0.55;0.60", body=cat_pose_stretch())
    flyby = ""
    if season != "winter":
        flyby = ('<g opacity="0"><animate attributeName="opacity" values="0;1;0" keyTimes="0;0.12;0.24" '
                 f'calcMode="discrete" {CYC}/>'
                 f'<g><animateMotion path="M980 60 C 860 80 760 50 660 72 C 600 85 560 66 525 76 C 500 82 470 40 430 -25" '
                 f'keyPoints="0;0;0.55;0.75;1;1" keyTimes="0;0.12;0.18;0.20;0.24;1" calcMode="linear" rotate="auto" {CYC}/>'
                 + butterfly_body(0.75) + '</g></g>')
    return ('<g><animateTransform attributeName="transform" type="translate" '
            f'values="950 0;950 0;560 0;560 0;480 0;300 0;300 0;-140 0;-140 0" '
            f'keyTimes="0;0.04;0.15;0.20;0.235;0.30;0.60;0.70;1" {CYC}/>'
            f'<g transform="translate(0,132) scale(1.7)">{{walk}}{{crouch}}{{pounce}}{{dash}}{{stand}}{{jump1}}{{jump2}}{{sit}}{{stretch}}</g></g>'
            .format(walk=walk, crouch=crouch, pounce=pounce, dash=dash, stand=stand,
                    jump1=jump1, jump2=jump2, sit=sit, stretch=stretch) + flyby)


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
         '<path id="fleaf" d="M0 0 Q-7 -3 -9 -10 Q-3 -8 0 0 Z"/></defs>']
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
        # extra headroom above the grass so the (now larger) cat can jump up into frame
        return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -78 900 218" width="900" height="218">\n'
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
