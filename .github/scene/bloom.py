#!/usr/bin/env python3
"""Paint the live weather into the bloom header.

yuki4266/living-scene looks up the weather and writes it to .github/scene-state
as e.g. "rain-autumn". This script reads that state, renders a weather layer in
the header's own palette and writes it between the <!--WEATHER--> markers of
bloom-header.svg. bloom-header-night.svg is then regenerated from the day file
(night palette, stars, moon), so only the day file is ever edited by hand.

    python3 .github/scene/bloom.py                          # follow .github/scene-state
    python3 .github/scene/bloom.py --weather snow --season winter   # pin a scene to preview it
"""
import argparse
import random
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

W, H = 900, 300
WEATHERS = ("clear", "clouds", "rain", "snow", "fog", "storm")
SEASONS = ("spring", "summer", "autumn", "winter")
SPLINE2 = 'calcMode="spline" keySplines="0.4 0 0.6 1;0.4 0 0.6 1" keyTimes="0;0.5;1"'
MARK = re.compile(r"<!--WEATHER[^>]*-->.*?<!--/WEATHER-->", re.S)

# same day -> night mapping living-scene uses for the footer, so both agree
NIGHT_MAP = {
    "#E8603C": "#FF7A50", "#E2542F": "#F4694A", "#F4795B": "#FF9075",
    "#ED8B66": "#FFA584", "#F09A7E": "#FFAC90", "#FBC7B3": "#FFD0BE",
    "#F9B98A": "#FFC79A", "#FFE9CF": "#FFF3E0", "#FFDCA8": "#FFE9C9",
    "#F4B183": "#FFD9A8", "#F4A05B": "#FFC069", "#A33D22": "#C9744F",
    "#7FA36B": "#8FAE7E", "#8CB07A": "#9CBE8B", "#A8C79A": "#B5D3A7",
    "#3B2F2A": "#A99C90",
}

# weather furniture, tuned per theme rather than colour-mapped: the day set sits
# on GitHub's white, the night set on #0d1117
PAL = {
    "day": dict(
        sun_glow="#FFD9A0", sun="#FFC069", sun_hi="#FFE3B8",
        cloud=("#EFE4DE", "#D9C9C1"), cloud_rain=("#DBD8E5", "#BDB7CE"),
        cloud_snow=("#E7E9F0", "#CBD0DD"), cloud_storm=("#B9B4C7", "#8F88A5"),
        rain="#A9BAD1", rain_heavy="#96A9C4", snow="#C4D2E0", snow_big="#B9C9DA",
        fog="#C9D1DC", flash="#FFF1C2", bolt="#FFD98A",
        leaf=("#C46A38", "#D98E4A", "#B57B3F"),
    ),
    "night": dict(
        moon="#F2E6C4", star="#D9E6F5", firefly="#FFD98A",
        cloud=("#3D465C", "#2B3245"), cloud_rain=("#363C51", "#262B3C"),
        cloud_snow=("#3F475B", "#2F3648"), cloud_storm=("#2F3447", "#1F2331"),
        rain="#6F84A6", rain_heavy="#7B90B2", snow="#E9F0F8", snow_big="#DCE7F2",
        fog="#7C89A0", flash="#C9D6FF", bolt="#E6EDFF",
        leaf=("#8F5230", "#9C6C3E", "#7E5A34"),
    ),
}


def nightify(svg):
    return re.sub(r"#[0-9A-Fa-f]{6}", lambda m: NIGHT_MAP.get(m.group(0).upper(), m.group(0)), svg)


def current_season(tz="America/New_York"):
    m = datetime.now(ZoneInfo(tz)).month
    return "spring" if m in (3, 4, 5) else "summer" if m in (6, 7, 8) else "autumn" if m in (9, 10, 11) else "winter"


# ---------------- sky furniture ----------------
def sun(p, op=1.0):
    rays = "".join(f'<path d="M0 -15 L2.1 -23 L-2.1 -23 Z" fill="{p["sun"]}" transform="rotate({a})"/>' for a in range(0, 360, 45))
    return (f'<g transform="translate(846,38)" opacity="{op}">'
            f'<circle r="26" fill="{p["sun_glow"]}" opacity="0.16"><animate attributeName="opacity" values="0.1;0.22;0.1" keyTimes="0;0.5;1" dur="6s" repeatCount="indefinite"/></circle>'
            f'<circle r="17" fill="{p["sun_glow"]}" opacity="0.28"/>'
            f'<g opacity="0.7"><animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="90s" repeatCount="indefinite"/>{rays}</g>'
            f'<circle r="9.5" fill="{p["sun"]}"/><circle r="9.5" fill="{p["sun_hi"]}" opacity="0.5"/></g>')


def moon(p, op=1.0):
    return (f'<g transform="translate(846,36)" opacity="{op}">'
            '<mask id="nightmoon"><rect x="-22" y="-22" width="44" height="44" fill="white"/><circle cx="7" cy="-4" r="13" fill="black"/></mask>'
            f'<circle r="24" fill="{p["moon"]}" opacity="0.1"><animate attributeName="opacity" values="0.07;0.16;0.07" keyTimes="0;0.5;1" dur="6s" repeatCount="indefinite"/></circle>'
            f'<circle r="15" fill="{p["moon"]}" opacity="0.92" mask="url(#nightmoon)"/></g>')


def stars(p, n, rnd):
    out = []
    for k in range(n):
        x, y = rnd.randint(30, 800), rnd.randint(10, 96)
        dur, beg = rnd.uniform(1.8, 4.5), rnd.uniform(0, 4)
        if k % 3 == 0:
            out.append(f'<g transform="translate({x},{y}) scale({rnd.uniform(0.6, 1.0):.2f})">'
                       f'<path d="M0 -5 L1.2 -1.2 L5 0 L1.2 1.2 L0 5 L-1.2 1.2 L-5 0 L-1.2 -1.2 Z" fill="{p["star"]}" opacity="0.2">'
                       f'<animate attributeName="opacity" values="0.15;0.9;0.15" keyTimes="0;0.5;1" dur="{dur:.1f}s" begin="{beg:.1f}s" repeatCount="indefinite"/></path></g>')
        else:
            out.append(f'<circle cx="{x}" cy="{y}" r="{rnd.uniform(0.9, 1.5):.1f}" fill="{p["star"]}" opacity="0.2">'
                       f'<animate attributeName="opacity" values="0.1;0.8;0.1" keyTimes="0;0.5;1" dur="{dur:.1f}s" begin="{beg:.1f}s" repeatCount="indefinite"/></circle>')
    return "".join(out)


def cloud(x, y, sc, cols, op, sway, dur, beg):
    """A puffy cloud: a pill with three bumps. Group opacity keeps the overlaps flat.
    It hovers in place with a slow sway instead of crossing the banner, so the
    composition stays balanced whenever you look."""
    body, shade = cols
    return (f'<g transform="translate({x},{y})"><g opacity="{op}">'
            f'<animateTransform attributeName="transform" type="translate" values="{-sway} 0;{sway} 3;{-sway} 0" {SPLINE2} dur="{dur}s" begin="{beg}s" repeatCount="indefinite"/>'
            f'<g transform="scale({sc})" fill="{body}">'
            '<rect x="-52" y="-8" width="104" height="22" rx="11"/>'
            '<circle cx="-24" cy="-10" r="17"/><circle cx="2" cy="-20" r="23"/><circle cx="27" cy="-9" r="18"/>'
            f'<ellipse cx="0" cy="10" rx="46" ry="4" fill="{shade}" opacity="0.45"/>'
            '</g></g></g>')


CLOUDS = {
    # x, y, scale, opacity, sway, dur, begin — the last "clouds" one drifts across the sun
    "clouds": [(215, 58, 0.80, 0.95, 26, 34, -6), (455, 40, 1.00, 1.0, 34, 46, -20),
               (690, 62, 0.62, 0.85, 22, 30, -11), (812, 60, 0.70, 0.95, 18, 40, -3)],
    "rain":   [(200, 54, 0.95, 1.0, 20, 38, -5), (450, 36, 1.15, 1.0, 26, 50, -21),
               (690, 58, 0.85, 0.95, 18, 42, -13), (860, 44, 0.75, 0.9, 16, 36, -9)],
    "snow":   [(240, 50, 0.90, 0.9, 22, 44, -8), (520, 34, 1.05, 0.9, 26, 52, -25),
               (790, 52, 0.80, 0.85, 20, 40, -14)],
    "storm":  [(170, 50, 1.05, 1.0, 16, 30, -4), (420, 32, 1.30, 1.0, 20, 40, -18),
               (660, 56, 1.00, 1.0, 14, 34, -10), (860, 40, 0.85, 0.95, 12, 28, -7)],
}


def clouds(w, p):
    cols = p["cloud"] if w == "clouds" else p[f"cloud_{w}"]
    return "".join(cloud(x, y, sc, cols, op, sway, dur, beg) for (x, y, sc, op, sway, dur, beg) in CLOUDS[w])


def fade_mask():
    # drops appear below the cloud band and thin out at the soil line
    return ('<linearGradient id="wx-fade-g" x1="0" y1="0" x2="0" y2="1">'
            '<stop offset="0.14" stop-color="#fff" stop-opacity="0"/><stop offset="0.32" stop-color="#fff" stop-opacity="1"/>'
            '<stop offset="0.84" stop-color="#fff" stop-opacity="1"/><stop offset="1" stop-color="#fff" stop-opacity="0.2"/></linearGradient>'
            f'<mask id="wx-fade" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
            f'<rect width="{W}" height="{H}" fill="url(#wx-fade-g)"/></mask>')


def rain(rnd, col, n, width, slant, length, speed, op):
    out = []
    for _ in range(n):
        x, dur = rnd.uniform(0, W), rnd.uniform(*speed)
        out.append(f'<g><animateTransform attributeName="transform" type="translate" values="0 0;0 {H + 40}" dur="{dur:.2f}s" begin="{-rnd.uniform(0, dur):.2f}s" repeatCount="indefinite"/>'
                   f'<line x1="{x:.0f}" y1="{-length}" x2="{x - slant:.0f}" y2="0" stroke="{col}" stroke-width="{width}" stroke-linecap="round"/></g>')
    return f'<g mask="url(#wx-fade)" opacity="{op}">' + "".join(out) + "</g>"


def snow(rnd, p):
    def fall(dx, dur):
        return (f'<animateTransform attributeName="transform" type="translate" values="0 -12;{dx:.0f} 100;{-dx:.0f} 205;{dx * 0.5:.0f} 318" '
                f'keyTimes="0;0.33;0.66;1" calcMode="spline" keySplines="0.4 0 0.6 1;0.4 0 0.6 1;0.4 0 0.6 1" dur="{dur:.1f}s" begin="{-rnd.uniform(0, dur):.1f}s" repeatCount="indefinite"/>')
    out = []
    for _ in range(28):
        x, dx, dur = rnd.uniform(0, W), rnd.choice([-1, 1]) * rnd.uniform(8, 18), rnd.uniform(9, 15)
        out.append(f'<g>{fall(dx, dur)}<circle cx="{x:.0f}" cy="0" r="{rnd.uniform(1.3, 2.6):.1f}" fill="{p["snow"]}" opacity="{rnd.uniform(0.6, 0.95):.2f}"/></g>')
    for _ in range(4):
        x, s = rnd.uniform(20, W - 20), rnd.uniform(2.8, 4.2)
        dx, dur = rnd.choice([-1, 1]) * rnd.uniform(10, 20), rnd.uniform(11, 16)
        arms = "".join(f'<line x1="0" y1="{-s:.1f}" x2="0" y2="{s:.1f}" transform="rotate({a})"/>' for a in (0, 60, 120))
        out.append(f'<g>{fall(dx, dur)}<g transform="translate({x:.0f},0)"><g stroke="{p["snow_big"]}" stroke-width="1.1" stroke-linecap="round" opacity="0.9">'
                   f'<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="{dur:.1f}s" repeatCount="indefinite"/>{arms}</g></g></g>')
    return "".join(out)


FOG_BANKS = [  # cx, cy, rx, ry, opacity, sway, dur, begin — mist pools among the stems, a thin haze up high
    (230, 268, 300, 20, 0.55, 40, 36, -5), (620, 280, 340, 22, 0.5, 50, 44, -20),
    (450, 298, 470, 16, 0.6, 36, 40, -12), (120, 244, 200, 12, 0.35, 30, 32, -8),
    (770, 240, 210, 12, 0.35, 34, 38, -15),
    (330, 80, 300, 13, 0.28, 60, 52, -18), (700, 102, 240, 11, 0.22, 46, 48, -30),
]


def fog(col):
    """Wide, heavily blurred ellipses read as mist; crisp bars read as bars."""
    out = ['<filter id="wx-blur" x="-20%" y="-300%" width="140%" height="700%"><feGaussianBlur stdDeviation="16"/></filter>']
    for (cx, cy, rx, ry, op, sway, dur, beg) in FOG_BANKS:
        out.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{col}" opacity="{op}" filter="url(#wx-blur)">'
                   f'<animateTransform attributeName="transform" type="translate" values="{-sway} 0;{sway} 0;{-sway} 0" {SPLINE2} dur="{dur}s" begin="{beg}s" repeatCount="indefinite"/></ellipse>')
    return "".join(out)


def lightning(p, peak):
    kt = 'keyTimes="0;0.52;0.545;0.57;0.585;0.61;1" dur="9s" repeatCount="indefinite"'
    bolt = 'd="M6 0 L-5 26 L4 24 L-10 56 M-1 19 L-15 31" fill="none" stroke-linecap="round"'
    return (f'<rect x="0" y="0" width="{W}" height="{H}" fill="{p["flash"]}" opacity="0"><animate attributeName="opacity" values="0;0;{peak};0;{peak / 2};0;0" {kt}/></rect>'
            f'<g transform="translate(672,66)" opacity="0"><animate attributeName="opacity" values="0;0;1;0;0.5;0;0" {kt}/>'
            f'<path {bolt} stroke="{p["bolt"]}" stroke-width="6" opacity="0.3"/><path {bolt} stroke="{p["bolt"]}" stroke-width="2.4"/></g>')


def leaves(rnd, cols):
    out = []
    for _ in range(3):
        px, drift = rnd.uniform(80, W - 80), rnd.choice([-1, 1]) * rnd.uniform(24, 48)
        dur, beg = rnd.uniform(9, 13), rnd.uniform(0, 6)
        out.append(f'<g transform="translate({px:.0f},-12)" opacity="0">'
                   f'<animate attributeName="opacity" values="0;0.8;0.8;0" keyTimes="0;0.1;0.8;1" dur="{dur:.1f}s" begin="{beg:.1f}s" repeatCount="indefinite"/>'
                   f'<g><animateTransform attributeName="transform" type="translate" values="0 0;{drift:.0f} 160;{drift * 2:.0f} 320" keyTimes="0;0.5;1" dur="{dur:.1f}s" begin="{beg:.1f}s" repeatCount="indefinite"/>'
                   f'<path d="M0 0 Q-10.5 -4.5 -13.5 -15 Q-4.5 -12 0 0 Z" fill="{rnd.choice(cols)}">'
                   f'<animateTransform attributeName="transform" type="rotate" values="0;170;350" keyTimes="0;0.5;1" dur="{dur:.1f}s" begin="{beg:.1f}s" repeatCount="indefinite"/></path></g></g>')
    return "".join(out)


def fireflies(rnd, col):
    out = []
    for (x, y) in [(250, 226), (392, 258), (548, 240), (668, 270), (300, 276)]:
        dur, beg = rnd.uniform(2.6, 4.2), rnd.uniform(0, 3)
        out.append(f'<g transform="translate({x},{y})"><g>'
                   f'<animateTransform attributeName="transform" type="translate" values="0 3;0 -7;0 3" {SPLINE2} dur="{dur:.1f}s" begin="{beg:.1f}s" repeatCount="indefinite"/>'
                   f'<circle r="2" fill="{col}" opacity="0"><animate attributeName="opacity" values="0;0.85;0" keyTimes="0;0.5;1" dur="{dur:.1f}s" begin="{beg:.1f}s" repeatCount="indefinite"/></circle></g></g>')
    return "".join(out)


# ---------------- layer ----------------
def weather_layer(w, s, theme):
    p = PAL[theme]
    rnd = random.Random(f"bloom-{w}-{s}-{theme}")
    night = theme == "night"
    out = []
    if w in ("rain", "storm"):
        out.append(fade_mask())
    if night and w in ("clear", "clouds"):
        out.append(stars(p, 14 if w == "clear" else 7, rnd))
    # the sky's light source: bright when clear, peeking through clouds, a haze in fog, gone in rain
    light = {"clear": 1.0, "clouds": 1.0, "fog": 0.5, "snow": 0.5 if night else 0.0}.get(w, 0.0)
    if light:
        out.append(moon(p, light) if night else sun(p, light))
    if w in CLOUDS:
        out.append(clouds(w, p))
    if w == "storm":
        out.append(lightning(p, 0.14 if night else 0.22))
    if w == "rain":
        out.append(rain(rnd, p["rain"], 34, 1.3, 3, 12, (1.1, 1.5), 0.6))
    if w == "storm":
        out.append(rain(rnd, p["rain_heavy"], 54, 1.5, 5, 15, (0.8, 1.1), 0.65))
    if w == "snow":
        out.append(snow(rnd, p))
    if w == "fog":
        out.append(fog(p["fog"]))
    if s == "autumn" and w in ("clear", "clouds"):
        out.append(leaves(rnd, p["leaf"]))
    if night and s == "summer" and w in ("clear", "clouds"):
        out.append(fireflies(rnd, p["firefly"]))
    return f"<!--WEATHER {w}-{s} {theme}-->" + "".join(out) + "<!--/WEATHER-->"


def render(day_src, w, s):
    if not MARK.search(day_src):
        raise SystemExit("bloom-header.svg has no <!--WEATHER-->...<!--/WEATHER--> block to paint into")
    day = MARK.sub(lambda _: weather_layer(w, s, "day"), day_src, count=1)
    night = MARK.sub(lambda _: weather_layer(w, s, "night"), nightify(day_src), count=1)
    night = night.replace("</title>", "</title>\n  <!-- generated from bloom-header.svg by .github/scene/bloom.py; edit that file instead -->", 1)
    return day, night


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--state", type=Path, default=Path(".github/scene-state"), help="scene file written by living-scene, e.g. rain-autumn")
    p.add_argument("--weather", choices=WEATHERS, help="pin the weather instead of reading the state file")
    p.add_argument("--season", choices=SEASONS, help="pin the season instead of reading the state file")
    p.add_argument("--day", type=Path, default=Path("bloom-header.svg"), help="header to paint into (also the night template)")
    p.add_argument("--night", type=Path, default=Path("bloom-header-night.svg"), help="where the night variant is written")
    p.add_argument("--out-day", type=Path, help="write the day header here instead of in place")
    p.add_argument("--out-night", type=Path, help="write the night header here instead of --night")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        w, s = args.state.read_text().strip().split("-")
    except (OSError, ValueError):
        w, s = "clear", current_season()
    w, s = args.weather or w, args.season or s
    if w not in WEATHERS or s not in SEASONS:
        raise SystemExit(f"unknown scene {w}-{s}")

    day, night = render(args.day.read_text(), w, s)
    (args.out_day or args.day).write_text(day)
    (args.out_night or args.night).write_text(night)
    print(f"header painted: {w}-{s}")


if __name__ == "__main__":
    main()
