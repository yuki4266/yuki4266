#!/usr/bin/env python3
"""Regenerate water-garden.svg — one flower blooms per watering. Run by the Water workflow."""
import random
import sys

n = int(sys.argv[1]) if len(sys.argv) > 1 else 0
user = sys.argv[2] if len(sys.argv) > 2 else ""

PER_ROW = 16
CAP = 48
shown = min(n, CAP)
rows = max((shown + PER_ROW - 1) // PER_ROW, 1)
H = 46 + rows * 34
SHADES = ["#F4795B", "#ED8B66", "#E2542F"]
rnd = random.Random(1226)

p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 {H}" width="900" height="{H}" '
     'font-family="Segoe UI, Ubuntu, Helvetica, Arial, sans-serif">',
     '<title>community garden</title>']

if n == 0:
    msg = "🌱 这块地还空着 — 做第一个浇水的园丁?"
else:
    extra = f" (+{n - CAP} 朵没画下)" if n > CAP else ""
    by = f" · 最近的园丁 @{user}" if user else ""
    msg = f"🌸 这块地被浇过 {n} 次水,开了 {n} 朵花{extra}{by}"
p.append(f'<text x="450" y="24" text-anchor="middle" font-size="14" fill="#F4795B">{msg}</text>')

if n == 0:
    p.append('<g transform="translate(450,{y})">'.format(y=H - 12)
             + '<path d="M0 0 Q-2 -8 0 -14" stroke="#7FA36B" stroke-width="2.5" fill="none" stroke-linecap="round"/>'
             '<path d="M0 -10 Q-8 -12 -10 -20 Q-3 -18 0 -10 Z" fill="#8CB07A"/>'
             '<path d="M0 -12 Q8 -14 10 -22 Q3 -20 0 -12 Z" fill="#8CB07A">'
             '<animateTransform attributeName="transform" type="rotate" values="-4;4;-4" keyTimes="0;0.5;1" dur="3s" repeatCount="indefinite"/>'
             '</path></g>')
else:
    for k in range(shown):
        row = k // PER_ROW
        col = k % PER_ROW
        cx = 60 + col * 52 + rnd.randint(-6, 6)
        cy = 52 + row * 34
        c = SHADES[k % 3]
        sway = rnd.uniform(3.5, 6.0)
        beg = rnd.uniform(0, 3)
        s = rnd.uniform(0.75, 1.0)
        p.append(
            f'<g transform="translate({cx},{cy}) scale({s:.2f})">'
            f'<g><animateTransform attributeName="transform" type="rotate" values="-5;5;-5" keyTimes="0;0.5;1" '
            f'calcMode="spline" keySplines="0.4 0 0.6 1;0.4 0 0.6 1" dur="{sway:.1f}s" begin="{beg:.1f}s" repeatCount="indefinite"/>'
            f'<circle cx="0" cy="-7" r="3.8" fill="{c}"/><circle cx="6.7" cy="-2.2" r="3.8" fill="{c}"/>'
            f'<circle cx="4.1" cy="5.7" r="3.8" fill="{c}"/><circle cx="-4.1" cy="5.7" r="3.8" fill="{c}"/>'
            f'<circle cx="-6.7" cy="-2.2" r="3.8" fill="{c}"/>'
            f'<circle r="3.2" fill="#FFDCA8" stroke="#E2542F" stroke-width="1"/></g></g>')

p.append('</svg>')
with open("water-garden.svg", "w") as f:
    f.write("\n".join(p) + "\n")
print(f"water-garden.svg written for n={n}")
