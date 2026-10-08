"""Build parametric puppet-show (பொம்மலாட்டம்) SVG scenes for all districts.
Writes static/games/<slug>.svg. Deterministic; re-run any time.
Run:  python scripts/build_district_art.py
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(__file__).resolve().parent.parent
GAMES = BASE / "data" / "games"
OUT = BASE / "static" / "games"
OUT.mkdir(parents=True, exist_ok=True)

FONT = "'Nirmala UI','Latha','Noto Sans Tamil',sans-serif"
SKY = {
    "north": ("#a8d8ff", "#ffe8c2"),
    "central": ("#6ec6f7", "#d6f1ff"),
    "west": ("#ffb877", "#ffe0b2"),
    "south": ("#7fd1ff", "#d9f7ff"),
}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def landmark(kind, cx, b, hue, accent):
    """Draw a district landmark with baseline y=b centered at cx."""
    g = []
    if kind == "gopuram":
        g.append(f'<rect x="{cx-130}" y="{b-46}" width="260" height="46" fill="#e8c39e" stroke="#b07d52" stroke-width="3"/>')
        g.append(f'<path d="M {cx-34} {b} L {cx-34} {b-30} A 34 34 0 0 1 {cx+34} {b-30} L {cx+34} {b} Z" fill="#4e342e"/>')
        w, y = 210, b - 46
        for i in range(5):
            h = 30
            g.append(f'<rect x="{cx-w//2}" y="{y-h}" width="{w}" height="{h}" fill="{"#f0d3ad" if i % 2 else "#e8c39e"}" stroke="#b07d52" stroke-width="2.5"/>')
            for k in range(w // 44):
                ax = cx - w // 2 + 26 + k * 44
                g.append(f'<path d="M {ax-9} {y-4} L {ax-9} {y-16} A 9 9 0 0 1 {ax+9} {y-16} L {ax+9} {y-4} Z" fill="#b07d52" opacity="0.75"/>')
            y -= h
            w -= 34
        g.append(f'<ellipse cx="{cx}" cy="{y-8}" rx="26" ry="14" fill="{hue}"/>')
        g.append(f'<rect x="{cx-3}" y="{y-34}" width="6" height="16" fill="#f9c74f"/><circle cx="{cx}" cy="{y-37}" r="6" fill="#f9c74f"/>')
    elif kind == "lighthouse":
        g.append(f'<path d="M {cx-40} {b-18} L {cx-16} {b-150} L {cx+16} {b-150} L {cx+40} {b-18} Z" fill="#fdfdf5" stroke="#b0a192" stroke-width="3"/>')
        g.append(f'<path d="M {cx-36} {b-46} L {cx-32} {b-76} L {cx+32} {b-76} L {cx+36} {b-46} Z" fill="{hue}"/>')
        g.append(f'<path d="M {cx-27} {b-106} L {cx-24} {b-136} L {cx+24} {b-136} L {cx+27} {b-106} Z" fill="{hue}"/>')
        g.append(f'<rect x="{cx-26}" y="{b-158}" width="52" height="10" fill="#90a4ae"/>')
        g.append(f'<rect x="{cx-17}" y="{b-184}" width="34" height="26" fill="#fff59d" stroke="#90a4ae" stroke-width="3"/>')
        g.append(f'<path d="M {cx} {b-196} l 0 -12 M {cx-30} {b-176} l -18 -6 M {cx+30} {b-176} l 18 -6" stroke="#f9c74f" stroke-width="4" stroke-linecap="round"/>')
        g.append(f'<path d="M {cx} {b-184} l -70 -34 M {cx} {b-184} l 70 -34" stroke="#f9c74f" stroke-width="3" opacity="0.55"/>')
        g.append(f'<rect x="{cx-56}" y="{b-18}" width="112" height="18" fill="#90a4ae"/>')
        g.append(f'<path d="M {cx-90} {b} q 14 -10 28 0 q 14 10 28 0 q 14 -10 28 0 q 14 10 28 0" fill="none" stroke="#4fc3f7" stroke-width="5"/>')
    elif kind == "hill":
        g.append(f'<circle cx="{cx+80}" cy="{b-140}" r="34" fill="#fff176" opacity="0.9"/>')
        g.append(f'<path d="M {cx-160} {b} L {cx-60} {b-150} L {cx+30} {b} Z" fill="#81c784"/>')
        g.append(f'<path d="M {cx-20} {b} L {cx+80} {b-120} L {cx+170} {b} Z" fill="#66bb6a"/>')
        g.append(f'<path d="M {cx-60} {b-150} L {cx-42} {b-126} L {cx-78} {b-126} Z" fill="#e3f2fd"/>')
        for i in range(7):
            g.append(f'<ellipse cx="{cx-130+i*40}" cy="{b-14-(i%3)*14}" rx="13" ry="7" fill="#2e7d32" opacity="0.7"/>')
        g.append(f'<path d="M {cx-140} {b-46} q 40 -20 80 -6" fill="none" stroke="#efebe9" stroke-width="5" stroke-dasharray="1 12" stroke-linecap="round"/>')
    elif kind == "dam":
        g.append(f'<rect x="{cx-150}" y="{b-128}" width="300" height="56" fill="#81d4fa"/>')
        g.append(f'<path d="M {cx-150} {b-72} q 30 8 60 0 q 30 -8 60 0 q 30 8 60 0 q 30 -8 60 0" fill="none" stroke="#4fc3f7" stroke-width="4"/>')
        g.append(f'<rect x="{cx-140}" y="{b-76}" width="280" height="56" fill="#b0bec5" stroke="#78909c" stroke-width="3"/>')
        for k in range(3):
            gx = cx - 96 + k * 72
            g.append(f'<rect x="{gx-24}" y="{b-70}" width="48" height="42" fill="#78909c" rx="3"/>')
            g.append(f'<path d="M {gx} {b-26} C {gx-10} {b-8} {gx+12} {b+4} {gx} {b+16}" fill="none" stroke="#e3f2fd" stroke-width="7" stroke-linecap="round" opacity="0.9"/>')
        g.append(f'<ellipse cx="{cx}" cy="{b+8}" rx="150" ry="14" fill="#4fc3f7" opacity="0.75"/>')
        g.append(f'<rect x="{cx-150}" y="{b-20}" width="300" height="20" fill="#90a4ae"/>')
    elif kind == "fort":
        g.append(f'<rect x="{cx-150}" y="{b-78}" width="300" height="78" fill="#d7b899" stroke="#a1887f" stroke-width="3"/>')
        for k in range(10):
            g.append(f'<rect x="{cx-150+k*30}" y="{b-94}" width="18" height="18" fill="#d7b899" stroke="#a1887f" stroke-width="2.5"/>')
        for sx in (cx - 150, cx + 150):
            g.append(f'<circle cx="{sx}" cy="{b-44}" r="34" fill="#c8a685" stroke="#a1887f" stroke-width="3"/>')
            g.append(f'<rect x="{sx-34}" y="{b-94}" width="68" height="18" fill="#c8a685" stroke="#a1887f" stroke-width="2.5"/>')
        g.append(f'<path d="M {cx-36} {b} L {cx-36} {b-44} A 36 36 0 0 1 {cx+36} {b-44} L {cx+36} {b} Z" fill="#4e342e"/>')
        g.append(f'<path d="M {cx} {b-80} l 0 -34 l 30 10 l -30 10" fill="{hue}" stroke="#5d4037" stroke-width="2"/>')
        g.append(f'<path d="M {cx+184} {b-94} l 0 -34" stroke="#5d4037" stroke-width="5"/>')
    elif kind == "sea":
        g.append(f'<circle cx="{cx-110}" cy="{b-150}" r="30" fill="#fff176"/>')
        g.append(f'<rect x="{cx-140}" y="{b-64}" width="240" height="34" fill="#5d4037" rx="6"/>')
        g.append(f'<path d="M {cx-140} {b-64} l 26 -26 h 170 l 44 26" fill="#6d4c41"/>')
        g.append(f'<rect x="{cx-90}" y="{b-104}" width="70" height="40" fill="#eceff1"/>')
        g.append(f'<rect x="{cx-74}" y="{b-124}" width="30" height="22" fill="#cfd8dc"/>')
        g.append(f'<path d="M {cx-44} {b-124} l 0 -30 l 24 8 l -24 8" fill="{hue}"/>')
        g.append(f'<rect x="{cx-26}" y="{b-30}" width="10" height="64" fill="#8d6e63"/>')
        for i, (dy, w) in enumerate(((0, 0), (14, 26), (28, -22))):
            g.append(f'<path d="M {cx-170+w} {b-8+dy} q 40 -14 84 0 q 44 14 86 0 q 42 -14 84 0" fill="none" stroke="{"#29b6f6" if i == 0 else "#4fc3f7"}" stroke-width="{10 - i * 2}" stroke-linecap="round" opacity="{0.9 - i * 0.2}"/>')
    elif kind == "palace":
        g.append(f'<rect x="{cx-120}" y="{b-84}" width="240" height="84" fill="#f3e5d0" stroke="#c8a685" stroke-width="3"/>')
        for k in range(3):
            ax = cx - 66 + k * 66
            g.append(f'<path d="M {ax-16} {b} L {ax-16} {b-34} A 16 16 0 0 1 {ax+16} {b-34} L {ax+16} {b} Z" fill="#8d6e63"/>')
        for sx in (cx - 120, cx + 120):
            g.append(f'<rect x="{sx-26}" y="{b-130}" width="52" height="46" fill="#f3e5d0" stroke="#c8a685" stroke-width="3"/>')
            g.append(f'<path d="M {sx-30} {b-130} Q {sx} {b-176} {sx+30} {b-130} Z" fill="{hue}"/>')
            g.append(f'<rect x="{sx-2}" y="{b-192}" width="4" height="16" fill="#f9c74f"/><circle cx="{sx}" cy="{b-194}" r="5" fill="#f9c74f"/>')
        g.append(f'<path d="M {cx-44} {b-84} Q {cx} {b-146} {cx+44} {b-84} Z" fill="{accent}"/>')
        g.append(f'<rect x="{cx-3}" y="{b-164}" width="6" height="18" fill="#f9c74f"/><circle cx="{cx}" cy="{b-167}" r="6" fill="#f9c74f"/>')
        g.append(f'<rect x="{cx-70}" y="{b-118}" width="34" height="34" fill="#b3e5fc" stroke="#c8a685" stroke-width="2"/><rect x="{cx+36}" y="{b-118}" width="34" height="34" fill="#b3e5fc" stroke="#c8a685" stroke-width="2"/>')
    elif kind == "bridge":
        g.append(f'<path d="M {cx-170} {b-76} L {cx+170} {b-76} L {cx+170} {b-68} L {cx-170} {b-68} Z" fill="#90a4ae"/>')
        g.append(f'<path d="M {cx-140} {b-68} A 140 54 0 0 0 {cx+140} {b-68}" fill="none" stroke="#78909c" stroke-width="8"/>')
        for k in range(-3, 4):
            dx = k * 44
            import math as _m
            ay = (b - 68) + 54 * _m.sqrt(max(0.0, 1 - (dx / 140) ** 2))
            g.append(f'<line x1="{cx+dx}" y1="{b-68}" x2="{cx+dx}" y2="{ay:.1f}" stroke="#78909c" stroke-width="5"/>')
        g.append(f'<rect x="{cx-60}" y="{b-100}" width="40" height="24" fill="{hue}"/><rect x="{cx-18}" y="{b-100}" width="40" height="24" fill="{accent}"/><rect x="{cx+24}" y="{b-100}" width="40" height="24" fill="{hue}"/>')
        g.append(f'<rect x="{cx-60}" y="{b-94}" width="104" height="6" fill="#eceff1" opacity="0.8"/>')
        g.append(f'<rect x="{cx-170}" y="{b-68}" width="14" height="66" fill="#78909c"/><rect x="{cx+156}" y="{b-68}" width="14" height="66" fill="#78909c"/>')
        g.append(f'<path d="M {cx-170} {b} q 42 -14 86 0 q 44 14 88 0 q 44 -14 86 0 q 42 14 84 0" fill="none" stroke="#4fc3f7" stroke-width="10" stroke-linecap="round"/>')
        g.append(f'<path d="M {cx-170} {b+16} q 42 -14 86 0 q 44 14 88 0 q 44 -14 86 0 q 42 14 84 0" fill="none" stroke="#29b6f6" stroke-width="8" stroke-linecap="round" opacity="0.7"/>')
    elif kind == "waterfall":
        g.append(f'<path d="M {cx+170} {b} L {cx+170} {b-170} L {cx-10} {b-150} L {cx-40} {b} Z" fill="#8d6e63"/>')
        g.append(f'<path d="M {cx+170} {b-170} L {cx-10} {b-150} L {cx+30} {b-120} L {cx+160} {b-140} Z" fill="#6d4c41"/>')
        for dx, w in ((30, 26), (70, 20), (104, 16)):
            g.append(f'<path d="M {cx+dx} {b-146} C {cx+dx-8} {b-80} {cx+dx+10} {b-40} {cx+dx} {b-14}" fill="none" stroke="#e3f2fd" stroke-width="{w}" stroke-linecap="round" opacity="0.92"/>')
            g.append(f'<path d="M {cx+dx} {b-140} C {cx+dx-6} {b-80} {cx+dx+8} {b-40} {cx+dx} {b-18}" fill="none" stroke="#b3e5fc" stroke-width="{max(6, w-14)}" stroke-linecap="round" opacity="0.8"/>')
        g.append(f'<ellipse cx="{cx+70}" cy="{b-4}" rx="120" ry="20" fill="#4fc3f7"/>')
        for cx2, cy2, r in ((cx + 14, b - 14, 13), (cx + 66, b - 22, 16), (cx + 122, b - 14, 12)):
            g.append(f'<circle cx="{cx2}" cy="{cy2}" r="{r}" fill="#ffffff" opacity="0.85"/>')
        g.append(f'<path d="M {cx-60} {b} l 18 -34 l 18 34 Z" fill="#a5d6a7"/><path d="M {cx-26} {b} l 14 -26 l 14 26 Z" fill="#81c784"/>')
    elif kind == "market":
        for i, sx in enumerate((cx - 96, cx + 30)):
            g.append(f'<rect x="{sx}" y="{b-74}" width="10" height="74" fill="#8d6e63"/><rect x="{sx+116}" y="{b-74}" width="10" height="74" fill="#8d6e63"/>')
            g.append(f'<rect x="{sx-8}" y="{b-104}" width="142" height="30" fill="{"#ef5350" if i == 0 else hue}" rx="4"/>')
            for k in range(4):
                g.append(f'<rect x="{sx-8+k*36}" y="{b-104}" width="18" height="30" fill="#fff8e1" opacity="0.85"/>')
            g.append(f'<rect x="{sx}" y="{b-34}" width="126" height="12" fill="#a1887f"/>')
        for k in range(3):
            g.append(f'<ellipse cx="{cx-66+k*34}" cy="{b-16}" rx="16" ry="18" fill="#fbc02d"/><path d="M {cx-66+k*34-6} {b-30} q 6 -8 12 0" fill="#f57f17"/>')
        for k in range(2):
            g.append(f'<ellipse cx="{cx+56+k*34}" cy="{b-14}" rx="15" ry="16" fill="#bcaaa4"/><ellipse cx="{cx+56+k*34}" cy="{b-28}" rx="10" ry="5" fill="#8d6e63"/>')
        g.append(f'<path d="M {cx-110} {b-118} q 56 22 110 0 q 56 -22 112 0" fill="none" stroke="#f9c74f" stroke-width="4"/>')
    elif kind == "mango":
        g.append(f'<path d="M {cx-16} {b} L {cx-8} {b-90} L {cx+8} {b-90} L {cx+18} {b} Z" fill="#795548"/>')
        g.append(f'<circle cx="{cx-58}" cy="{b-124}" r="46" fill="#66bb6a"/><circle cx="{cx+54}" cy="{b-132}" r="52" fill="#81c784"/><circle cx="{cx}" cy="{b-168}" r="56" fill="#69f0ae"/>')
        g.append(f'<path d="M {cx-4} {b-106} C {cx-64} {b-96} {cx-74} {b-34} {cx-16} {b-20} C {cx+38} {b-8} {cx+74} {b-52} {cx+50} {b-92} C {cx+34} {b-118} {cx+16} {b-114} {cx-4} {b-106} Z" fill="#ffca28" stroke="#f57f17" stroke-width="4"/>')
        g.append(f'<path d="M {cx-4} {b-106} C {cx+4} {b-132} {cx+30} {b-138} {cx+44} {b-132} C {cx+34} {b-112} {cx+16} {b-104} {cx-4} {b-106} Z" fill="#43a047"/>')
        g.append(f'<ellipse cx="{cx-96}" cy="{b-150}" rx="17" ry="20" fill="#ffca28" transform="rotate(-20 {cx-96} {b-150})"/>')
        g.append(f'<ellipse cx="{cx+104}" cy="{b-158}" rx="15" ry="18" fill="#ffb300" transform="rotate(18 {cx+104} {b-158})"/>')
    elif kind == "monument":
        g.append(f'<circle cx="{cx-130}" cy="{b-160}" r="32" fill="#fff176"/>')
        g.append(f'<path d="M {cx-180} {b-10} q 40 -16 84 0 q 44 16 88 0 q 44 -16 88 0 q 44 16 84 0" fill="none" stroke="#4fc3f7" stroke-width="12" stroke-linecap="round"/>')
        g.append(f'<path d="M {cx-170} {b+8} q 44 -14 90 0 q 46 14 92 0 q 46 -14 90 0" fill="none" stroke="#29b6f6" stroke-width="10" stroke-linecap="round" opacity="0.7"/>')
        g.append(f'<path d="M {cx+34} {b-6} L {cx+54} {b-46} L {cx+94} {b-46} L {cx+112} {b-6} Z" fill="#8d6e63"/>')
        g.append(f'<rect x="{cx+64}" y="{b-70}" width="22" height="26" fill="#a1887f"/><path d="M {cx+60} {b-70} Q {cx+75} {b-92} {cx+90} {b-70} Z" fill="#c8a685"/>')
        g.append(f'<rect x="{cx-70}" y="{b-150}" width="26" height="144" fill="#b0bec5" stroke="#78909c" stroke-width="3"/>')
        g.append(f'<rect x="{cx-96}" y="{b-10}" width="78" height="12" fill="#90a4ae"/>')
        g.append(f'<circle cx="{cx-57}" cy="{b-166}" r="13" fill="#8d6e63"/>')
        g.append(f'<path d="M {cx-70} {b-150} L {cx-44} {b-150} L {cx-48} {b-196} L {cx-66} {b-196} Z" fill="#8d6e63"/>')
        g.append(f'<path d="M {cx-46} {b-186} l 14 -18 l 4 6 l -12 16 Z" fill="#8d6e63"/>')
    elif kind == "industry":
        g.append(f'<rect x="{cx-150}" y="{b-78}" width="300" height="78" fill="#b0bec5" stroke="#78909c" stroke-width="3"/>')
        pts = " ".join(f"{cx-150+i*40} {b-78 if (i//2) % 2 == 0 else b-104}" for i in range(8))
        g.append(f'<path d="M {cx-150} {b-78} L {pts} L {cx+150} {b-78} Z" fill="#90a4ae"/>')
        for sx in (cx - 120, cx + 60):
            g.append(f'<rect x="{sx}" y="{b-186}" width="26" height="110" fill="#8d6e63"/>')
            g.append(f'<rect x="{sx-3}" y="{b-192}" width="32" height="8" fill="#6d4c41"/>')
            g.append(f'<circle cx="{sx+34}" cy="{b-210}" r="13" fill="#eceff1" opacity="0.9"/><circle cx="{sx+56}" cy="{b-230}" r="17" fill="#eceff1" opacity="0.75"/><circle cx="{sx+44}" cy="{b-254}" r="14" fill="#eceff1" opacity="0.55"/>')
        for k in range(3):
            g.append(f'<rect x="{cx-60+k*44}" y="{b-44}" width="36" height="44" fill="#ffe082" stroke="#f9a825" stroke-width="2.5"/>')
            g.append(f'<line x1="{cx-60+k*44}" y1="{b-30}" x2="{cx-60+k*44+36}" y2="{b-30}" stroke="#f9a825" stroke-width="2.5"/>')
        g.append(f'<rect x="{cx+96}" y="{b-40}" width="44" height="40" fill="#ef5350" opacity="0.9"/>')
        g.append(f'<rect x="{cx+96}" y="{b-52}" width="44" height="14" fill="#e53935"/>')
    return "\n".join(g)


def puppet(cx, floor_y, hue, female):
    """Marionette puppet; local origin at feet center (0,0 = cx,floor_y)."""
    skin, hair, shirt = "#ffdfc4", "#263238", hue
    trous = "#37474f" if not female else None
    p = [f'<g transform="translate({cx},{floor_y})">']
    if not female:
        p.append('<rect x="-15" y="-62" width="12" height="56" rx="5" fill="#455a64"/>')
        p.append('<rect x="3" y="-62" width="12" height="56" rx="5" fill="#455a64"/>')
        p.append('<ellipse cx="-9" cy="-2" rx="15" ry="7" fill="#4e342e"/><ellipse cx="9" cy="-2" rx="15" ry="7" fill="#4e342e"/>')
        p.append(f'<path d="M -26 -124 L 26 -124 L 22 -64 L -22 -64 Z" fill="{shirt}"/>')
        p.append('<rect x="-24" y="-70" width="48" height="8" fill="#f9c74f"/>')
        p.append(f'<rect x="-16" y="-64" width="32" height="14" fill="#efebe9"/>')
    else:
        p.append('<rect x="-13" y="-52" width="10" height="46" rx="5" fill="#ffccbc"/>')
        p.append('<rect x="3" y="-52" width="10" height="46" rx="5" fill="#ffccbc"/>')
        p.append('<ellipse cx="-8" cy="-2" rx="13" ry="7" fill="#4e342e"/><ellipse cx="8" cy="-2" rx="13" ry="7" fill="#4e342e"/>')
        p.append(f'<path d="M -24 -124 L 24 -124 L 34 -44 L -34 -44 Z" fill="{shirt}"/>')
        p.append(f'<path d="M -34 -44 L 34 -44 L 38 -28 L -38 -28 Z" fill="#efebe9"/>')
        p.append(f'<path d="M -24 -110 L 24 -86" stroke="#ffffff" stroke-width="8" opacity="0.55" stroke-linecap="round"/>')
    # arms
    p.append(f'<line x1="-24" y1="-118" x2="-50" y2="-84" stroke="{shirt}" stroke-width="11" stroke-linecap="round"/>')
    p.append(f'<line x1="24" y1="-118" x2="52" y2="-90" stroke="{shirt}" stroke-width="11" stroke-linecap="round"/>')
    p.append(f'<circle cx="-52" cy="-82" r="8" fill="{skin}"/><circle cx="54" cy="-88" r="8" fill="{skin}"/>')
    # prop in right hand: flower for female, flag for male
    if female:
        p.append('<line x1="54" y1="-88" x2="54" y2="-112" stroke="#43a047" stroke-width="4"/>')
        for a in range(5):
            import math
            px = 54 + 11 * math.cos(a * 72 * math.pi / 180)
            py = -116 + 11 * math.sin(a * 72 * math.pi / 180)
            p.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="6.5" fill="#f48fb1"/>')
        p.append('<circle cx="54" cy="-116" r="6" fill="#fdd835"/>')
    else:
        p.append('<line x1="54" y1="-88" x2="54" y2="-134" stroke="#8d6e63" stroke-width="5"/>')
        p.append(f'<path d="M 54 -134 L 96 -124 L 54 -112 Z" fill="#ff7043"/>')
    # head
    p.append(f'<rect x="-7" y="-134" width="14" height="12" fill="{skin}"/>')
    p.append(f'<circle cx="0" cy="-158" r="27" fill="{skin}"/>')
    if female:
        p.append('<path d="M -27 -162 A 27 27 0 0 1 27 -162 L 27 -156 A 27 27 0 0 0 -27 -156 Z" fill="#1a1a1a"/>')
        p.append('<path d="M -27 -164 Q 0 -196 27 -164 Q 0 -176 -27 -164 Z" fill="#1a1a1a"/>')
        p.append('<circle cx="0" cy="-190" r="14" fill="#1a1a1a"/>')
        p.append('<circle cx="0" cy="-166" r="3.4" fill="#c62828"/>')
    else:
        p.append('<path d="M -27 -164 Q 0 -198 27 -164 Q 0 -180 -27 -164 Z" fill="#1a1a1a"/>')
        p.append('<rect x="-3" y="-172" width="6" height="7" fill="#c62828"/>')
    p.append('<circle cx="-9" cy="-158" r="3.2" fill="#1a1a1a"/><circle cx="9" cy="-158" r="3.2" fill="#1a1a1a"/>')
    p.append('<circle cx="-8" cy="-159" r="1.1" fill="#ffffff"/><circle cx="10" cy="-159" r="1.1" fill="#ffffff"/>')
    p.append('<path d="M -8 -148 Q 0 -141 8 -148" fill="none" stroke="#b71c1c" stroke-width="2.6" stroke-linecap="round"/>')
    p.append('<path d="M -16 -166 Q -9 -169 -3 -166 M 3 -166 Q 9 -169 16 -166" fill="none" stroke="#1a1a1a" stroke-width="2"/>')
    p.append('</g>')
    return "\n".join(p)


def stage(hue, name, division_name, sky_top, sky_bot):
    s = []
    s.append(f'<rect width="960" height="540" fill="#3e2723"/>')
    # backdrop sky
    s.append(f'<rect x="110" y="86" width="740" height="344" fill="url(#sky)"/>')
    s.append(f'<circle cx="790" cy="146" r="30" fill="#fff176" opacity="0.95"/>')
    for cx2, cy2, sc in ((190, 140, 1), (700, 210, 0.8), (330, 116, 0.7)):
        s.append(f'<g opacity="0.9" transform="translate({cx2},{cy2}) scale({sc})"><ellipse cx="0" cy="0" rx="36" ry="16" fill="#ffffff"/><ellipse cx="-24" cy="6" rx="22" ry="12" fill="#ffffff"/><ellipse cx="26" cy="6" rx="24" ry="13" fill="#ffffff"/></g>')
    for bx, by, bs in ((210, 250, 1), (760, 268, 0.8), (640, 130, 0.7)):
        s.append(f'<path d="M {bx-14*bs} {by} q {7*bs} {-8*bs} {14*bs} 0 q {7*bs} {8*bs} {14*bs} 0" fill="none" stroke="#37474f" stroke-width="{2.6*bs}" stroke-linecap="round"/>')
    # landmark
    s.append(landmark(DIST_LM[name["slug"]], 480, 418, hue, DIV_ACC[name["division"]]))
    # grass strip
    s.append('<rect x="110" y="418" width="740" height="12" fill="#7cb342"/>')
    s.append('<rect x="110" y="414" width="740" height="6" fill="#8bc34a"/>')
    # name board
    s.append('<rect x="340" y="100" width="280" height="66" rx="10" fill="#fff8e1" stroke="#f9c74f" stroke-width="5"/>')
    s.append('<rect x="348" y="108" width="264" height="50" rx="6" fill="none" stroke="#c8a685" stroke-width="2"/>')
    s.append(f'<text x="480" y="136" text-anchor="middle" font-family="{FONT}" font-size="30" font-weight="bold" fill="#4e342e" textLength="248" lengthAdjust="spacingAndGlyphs">{esc(name["name_ta"])}</text>')
    s.append(f'<text x="480" y="156" text-anchor="middle" font-family="{FONT}" font-size="15" fill="#8d6e63">{esc(division_name)}</text>')
    # side curtains (behind puppets)
    for sx, flip in ((110, 1), (850, -1)):
        s.append(f'<path d="M {sx} 0 L {sx + 96 * flip} 0 C {sx + 74 * flip} 150 {sx + 96 * flip} 300 {sx + 58 * flip} 430 L {sx} 430 Z" fill="#b71c1c"/>')
        for k in range(3):
            fx = sx + (26 + k * 26) * flip
            s.append(f'<path d="M {fx} 0 C {fx + 14 * flip} 150 {fx + 10 * flip} 300 {fx - 6 * flip} 430" fill="none" stroke="#8b0000" stroke-width="8" opacity="0.55"/>')
        tx = sx + 54 * flip
        s.append(f'<circle cx="{tx}" cy="240" r="10" fill="#f9c74f"/><path d="M {tx} 248 l -8 26 l 16 0 Z" fill="#f9c74f"/>')
    # floor
    s.append('<rect x="0" y="430" width="960" height="110" fill="#a5673f"/>')
    for k in range(6):
        s.append(f'<line x1="0" y1="{448 + k * 18}" x2="960" y2="{448 + k * 18}" stroke="#7f4f2c" stroke-width="3"/>')
    s.append('<rect x="0" y="430" width="960" height="8" fill="#8b5a33"/>')
    s.append('<ellipse cx="310" cy="434" rx="90" ry="16" fill="#fff8e1" opacity="0.35"/>')
    s.append('<ellipse cx="650" cy="434" rx="90" ry="16" fill="#fff8e1" opacity="0.35"/>')
    # top valance
    s.append('<rect x="0" y="0" width="960" height="56" fill="#b71c1c"/>')
    for k in range(8):
        s.append(f'<ellipse cx="{60 + k * 120}" cy="56" rx="60" ry="26" fill="#b71c1c"/>')
        s.append(f'<ellipse cx="{60 + k * 120}" cy="52" rx="54" ry="22" fill="#c62828"/>')
    s.append('<path d="M 0 74 q 60 26 120 0 q 60 -26 120 0 q 60 26 120 0 q 60 -26 120 0 q 60 26 120 0 q 60 -26 120 0 q 60 26 120 0" fill="none" stroke="#f9c74f" stroke-width="5"/>')
    for k in range(13):
        s.append(f'<circle cx="{40 + k * 72}" cy="84" r="6" fill="#f9c74f"/>')
    s.append('<rect x="0" y="0" width="960" height="14" fill="#8b0000"/>')
    # puppets + strings
    for px, fem in ((310, False), (650, True)):
        s.append(puppet(px, 430, hue if not fem else DIV_ACC[SHADE_DIV], fem))
        s.append('<g stroke="rgba(255,255,255,0.7)" stroke-width="1.6">')
        s.append(f'<line x1="{px-46}" y1="118" x2="{px-52}" y2="{430-82}"/>')
        s.append(f'<line x1="{px}" y1="118" x2="{px}" y2="{430-186}"/>')
        s.append(f'<line x1="{px+46}" y1="118" x2="{px+54}" y2="{430-88}"/>')
        s.append('</g>')
        s.append(f'<rect x="{px-54}" y="112" width="108" height="7" rx="3.5" fill="#5d4037"/>')
        s.append(f'<circle cx="{px}" cy="108" r="7" fill="none" stroke="#5d4037" stroke-width="4"/>')
    # frame
    s.append('<rect x="0" y="0" width="960" height="540" fill="none" stroke="#3e2723" stroke-width="18"/>')
    s.append('<rect x="6" y="6" width="948" height="528" fill="none" stroke="#f9c74f" stroke-width="3"/>')
    return "\n".join(s)


def build_svg(d, division_name):
    global DIST_LM, DIV_ACC, SHADE_DIV
    DIST_LM = {x["slug"]: x["landmark"] for x in DISTRICTS}
    DIV_ACC = {"north": "#d84315", "central": "#6a1b9a", "west": "#1565c0", "south": "#2e7d32"}
    SHADE_DIV = d["division"]
    top, bot = SKY[d["division"]]
    body = stage(d["color"], d, division_name, top, bot)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 540" width="960" height="540">'
            f'<defs>'
            f'<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bot}"/></linearGradient>'
            f'</defs>'
            f'{body}</svg>')


if __name__ == "__main__":
    data = json.loads((GAMES / "districts.json").read_text(encoding="utf-8"))
    DISTRICTS = data["districts"]
    divs = {x["id"]: x["name"] for x in data["divisions"]}
    for d in DISTRICTS:
        svg = build_svg(d, divs[d["division"]])
        (OUT / f"{d['slug']}.svg").write_text(svg, encoding="utf-8")
    print(f"built {len(DISTRICTS)} svgs -> {OUT}")
