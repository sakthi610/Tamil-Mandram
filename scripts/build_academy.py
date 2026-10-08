"""Academy course skeleton parser v3.
- std6: two TOCs (Term1 line-based units; Term2 பொருண்மை rows)
- std7: body openers 'இயல் <num> <title>' grouped into 3 parts
- std8/9/11/12: line-based TOC walker
- std10: EPUB headings
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(r"C:\Users\ADMIN\Desktop\Tamil")
SRC = BASE / "source_text"
OUT = BASE / "data" / "academy"
SLICES = OUT / "slices"
SLICES.mkdir(parents=True, exist_ok=True)

STD_LABEL = {
    "6": "6ஆம் வகுப்பு தமிழ்", "7": "7ஆம் வகுப்பு தமிழ்", "8": "8ஆம் வகுப்பு தமிழ்",
    "9": "9ஆம் வகுப்பு தமிழ்", "10": "10ஆம் வகுப்பு தமிழ்", "11": "11ஆம் வகுப்பு தமிழ்",
    "12": "12ஆம் வகுப்பு தமிழ்",
}
COLORS = ["#58cc02", "#1cb0f6", "#ce82ff", "#ff9600", "#ff4b4b", "#2b70c9", "#ff9600"]

THEMES = [
    "மொழி, மனிதம்", "மொழி", "இயற்கை, சுற்றுச்சூழல்", "இயற்கை, வேளாண் மமை, சுற்றுச்சூழல்",
    "இயற்கை, வேளாண் மமை", "இயற்கை", "கலை, அழகியல், பண்பாடு", "கலை, அழகியல், புதுமை",
    "கலை, அழகியல்", "கல்வி", "பண்பாடு", "அறிவியல், தொழில்நுட்பம்", "அறிவியல்",
    "சமூகம், வாழ்வியல்", "சமூகம்", "வாழ்வியல்", "பொருளாதாரம்", "அரசியல்",
    "இலக்கியம்", "நாகரிகம், நாடு, சமூகம்", "நாகரிகம்", "அறம், தத்துவம், சிந்தனை",
    "அறம்", "தத்துவம், சிந்தனை", "சுற்றுச்சூழல்", "வேளாண் மமை",
]
CONSONANTS = set("கஙசஞடணதநபமயரலளழவஶஷஸஹ")
MONTHS = {"ஜனவரி", "பிப்ரவரி", "மார்ச்", "ஏப்ரல்", "மே", "ஜூன்", "ஜூலை",
          "ஆகஸ்ட்", "ஆகஸ்டு", "செப்டம்பர்", "அக்டோபர்", "நவம்பர்,", "டிசம்பர்",
          "ஆகஸ்ட்,", "செப்டம்பர்,", "நவம்பர்", "டிசம்பர்,"}
TYPES = {"உரைநடை", "செய்யுள்", "கவிதை", "துணைப்பாடம்", "இலக்கணம்", "ஒலிப்பதிவு",
         "மனப்பாடம்", "நாடகம்", "நேர்காணல்", "கடிதம்", "சிறுகதை", "ஒப்பிடல்",
         "பேச்சு", "கவிதைப்பேழை", "உரைநாடை", "ஒப்பிடல்"}
NOISE = {"பாடத்தலைப்புககள்", "பாடத்தலைப்புகள்", "பபக்க", "பக்க", "எண்", "மாதம்",
         "பொொருளடக்கம்", "பொருளடக்கம்", "Unknown", "V", "X", "XI", "XII",
         "பொருண்மை", "இயல்", "ஆறாம் வகுப்பு", "இரண்டாம் பருவம்", "தொகுதி 1", "தமிழ்"}


def clean_txt(s):
    s = re.sub(r"\s+", " ", s).strip()
    s = "".join(ch for ch in s if ("\u0B80" <= ch <= "\u0BFF") or ch in " ,()\-.\u2013\u2014'’")
    return s.strip(" ,.-*")


def norm(s):
    s = re.sub(r"[^^\u0B80-\u0BFF]", "", s)  # Tamil only
    out = []
    for ch in s:
        if out and ch == out[-1]:
            continue
        out.append(ch)
    return "".join(out)


THEME_NORMS = sorted({norm(t) for t in THEMES}, key=len, reverse=True)


def is_theme_prefix(nj):
    return bool(nj) and any(th.startswith(nj) for th in THEME_NORMS)


def is_noise(tok):
    if tok in NOISE or tok in MONTHS or tok in TYPES:
        return True
    if re.search(r"indd|/20\d\d|Std - Tamil|www\.|\d{1,2}:\d{2}", tok):
        return True
    return False


def line_is_noise(tok):
    return is_noise(tok) or tok.strip(".,") in MONTHS


def walk_toc(chunk, last=0):
    """Line-based walker over a TOC chunk. Returns (units, last_seen)."""
    tokens = [l.strip() for l in chunk.split("\n") if l.strip()]
    units, cur = [], None
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        tk = tok.rstrip(".").strip()
        if is_noise(tok) or tok.strip(".,") in MONTHS:
            i += 1
            continue
        if tk.isdigit() and (tok == tk or tok == tk + "."):
            n = int(tk)
            if n > 14 or n != last + 1:
                i += 1  # page number
                continue
            # lookahead: raw next token — a month after a number means it was a page
            nxt = tokens[i + 1] if i + 1 < len(tokens) else None
            if (nxt is not None and not nxt.isdigit()
                    and nxt.strip(".,") not in MONTHS and not is_noise(nxt)):
                # collect title lines
                title_lines = []
                k = i + 1
                while k < len(tokens):
                    t2 = tokens[k]
                    t2d = t2.rstrip(".").strip()
                    if t2d.isdigit() or line_is_noise(t2) or t2 in TYPES or "*" in t2:
                        break
                    if title_lines:
                        nj_cur = norm(" ".join(title_lines))
                        if any(th == nj_cur or nj_cur.startswith(th) for th in THEME_NORMS):
                            pros = norm(" ".join(title_lines + [t2]))
                            if not any(th.startswith(pros) for th in THEME_NORMS):
                                break
                    title_lines.append(t2)
                    k += 1
                    if len(title_lines) >= 4:
                        break
                title = clean_txt(" ".join(title_lines))
                if not title:
                    title = clean_txt(nxt) if nxt else f"பகுதி {n}"
                cur = {"num": n, "title": title, "lessons": []}
                units.append(cur)
                last = n
                i = k
                continue
            i += 1  # page number
            continue
        # lesson title lines (only inside a unit)
        if cur is not None:
            les = []
            while i < len(tokens) and not tokens[i].rstrip(".").strip().isdigit():
                t2 = tokens[i]
                if line_is_noise(t2) or re.search(r"indd|/20\d\d|Std - Tamil|www\.", t2):
                    i += 1
                    continue
                les.append(t2)
                i += 1
            title = clean_txt(" ".join(les))
            if len(title) >= 3 and title != cur["title"] and title not in cur["lessons"]:
                cur["lessons"].append(title[:55])
            continue
        i += 1
    return units, last


def parse_toc_regions(t):
    markers = [m.start() for m in re.finditer(r"பாட\s*த்?\s*தலைப்பு\s*க\s*கள்", t)]
    units, last = [], 0
    for idx, ms in enumerate(markers):
        limit = markers[idx + 1] if idx + 1 < len(markers) else len(t)
        me = re.search(r"கற்றல்\s*ந", t[ms:min(limit, ms + 4000)])
        end = ms + me.start() if me else min(limit, ms + 3500)
        got, last = walk_toc(t[ms:end], last)
        units += got
    return units


def parse_std6(t):
    units = []
    # Term1 line-based TOC region
    m1 = re.search(r"பாட\s*த்?\s*தலைப்பு\s*க\s*கள்", t)
    if m1:
        # end at first கற்றல் marker or +3500
        m_end = re.search(r"கற்றல்\s*ந", t[m1.start():m1.start() + 5000])
        end = m1.start() + (m_end.start() if m_end else 3500)
        units += walk_toc(t[m1.start():end])[0]
    # Term2 பொருண்மை rows
    for m in re.finditer(r"பொ\s*ருண்?மை,?\s*\n\s*\n", t[120000:]):
        pos = 120000 + m.start()
        seg = t[pos:pos + 1400]
        tm = re.match(r"பொ\s*ருண்?மை,?\s*\n+\s*([^\n]+)\n", seg)
        if not tm:
            continue
        title = clean_txt(tm.group(1))
        if len(title) < 4 or title in ("இயல்",):
            continue
        # first lesson after இயல்,
        lessons = []
        fm = re.search(r"இயல்,\s*([^ப\n][^\n]{3,60})", seg)
        if fm:
            lessons.append(clean_txt(fm.group(1))[:55])
        lessons += [clean_txt(x)[:55] for x in re.findall(r"பாடத்தலைப்பு,\s*\n?\s*([^,\n]{3,60})", seg)]
        units.append({"num": 100 + len(units), "title": title,
                      "lessons": list(dict.fromkeys([l for l in lessons if l]))[:8]})
    return units


def parse_std7(t):
    rows = []
    for m in re.finditer(r"இயல்\s*(ஒன்று|இரண்டு|மூன்று|நான்கு|ஐந்து|ஆறு)\s*([^\n]{3,60})", t):
        rows.append((m.group(1), clean_txt(m.group(2)), m.start()))
    part_order = {"ஒன்று": 1, "இரண்டு": 2, "மூன்று": 3, "நான்கு": 4, "ஐந்து": 5, "ஆறு": 6}
    grouped = {}
    seen_titles = []
    for num, title, pos in rows:
        if not title or any(x in title for x in ("பாடத்தலை", "கற்றல்", "மதிப்பீடு")):
            continue
        # drop fragments that are substrings of already-kept titles
        if any(title in s for s in seen_titles):
            continue
        if title.endswith("்") and len(title) <= 5:
            continue
        seen_titles.append(title)
        grouped.setdefault(part_order.get(num, 9), []).append(title)
    units = []
    for part in sorted(grouped):
        titles = grouped[part]
        units.append({"num": part, "title": f"இயல் {list(part_order.keys())[part - 1]}",
                      "lessons": titles[:8]})
    return units


def parse_std10(t):
    units = []
    for m in re.finditer(r"இயல்\s*(ஒன்று|இரண்டு|மூன்று|நான்கு|ஐந்து|ஆறு|ஏழு)\s+([^\n]{3,55})(?:\n([^\n]{3,55}))?", t):
        title = clean_txt(m.group(2))
        cat = clean_txt(m.group(3)) if m.group(3) else ""
        if not title or title in ("கவிதைப்பேழை", "உரைநடை", "நடிப்பேட்டை"):
            continue
        if cat and (cat in ("கவிதைப்பேழை", "உரைநடை", "நடிப்பேட்டை") or len(cat) > 40):
            title = f"{title} ({cat})"
        if any(u["title"] == title for u in units):
            continue
        units.append({"title": title, "lessons": []})
    for i in range(len(units)):
        start = t.find(units[i]["title"])
        end = t.find(units[i + 1]["title"], start + 5) if i + 1 < len(units) else len(t)
        if start < 0:
            continue
        seg = t[start:end]
        for sm in re.finditer(r"(கவிதைப்பேழை|உரைநடை|நடிப்பேட்டை)\s*\n?\s*([^\n]{3,50})", seg):
            les = clean_txt(sm.group(2))
            if len(les) >= 3 and les != units[i]["title"]:
                units[i]["lessons"].append(f"{sm.group(1)}: {les}"[:65])
    return units


def write_slice(t, std, idx, pos, size=9000):
    p = SLICES / f"std{std}_u{idx}.txt"
    p.write_text(t[pos:pos + size], encoding="utf-8")
    return p.name


course = {"standards": []}
for std in ["6", "7", "8", "9", "10", "11", "12"]:
    t = (SRC / f"std{std}.txt").read_text(encoding="utf-8")
    if std == "6":
        units = parse_std6(t)
    elif std == "7":
        units = parse_std7(t)
    elif std == "10":
        units = parse_std10(t)
    else:
        units = parse_toc_regions(t)
    if not units:
        print(f"std{std}: NO UNITS")
        continue
    def tidy(s):
        s = clean_txt(s)
        out = []
        for ch in s:
            if out and ch == out[-1] and "\u0B80" <= ch <= "\u0BFF":
                continue
            out.append(ch)
        return "".join(out).strip()

    for u in units:
        u["title"] = tidy(u["title"])
        u["lessons"] = [tidy(x) for x in u.get("lessons", []) if tidy(x)]
    # positions for slices
    for i, u in enumerate(units):
        key = u["title"].split(",")[0].split(" ")[0]
        pos = t.find(key) if key else -1
        if pos < 0:
            pos = (i * len(t)) // len(units)
        u["slice"] = write_slice(t, std, i + 1, pos)
        u["lessons"] = list(dict.fromkeys(u.get("lessons", [])))[:8]
        if "cat" in u:
            u["title"] = f"{u['title']} ({u['cat']})"
    course["standards"].append({
        "std": std, "label": STD_LABEL[std], "color": COLORS[int(std) - 6],
        "units": units[:10],
    })
    print(f"std{std}: {len(units)} units")
    for u in units[:10]:
        print(f"   - {u['title']} :: {len(u['lessons'])} lessons :: " +
              " | ".join(u["lessons"][:4]))

(OUT / "course.json").write_text(json.dumps(course, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nWROTE course.json:", len(course["standards"]), "standards,",
      sum(len(s["units"]) for s in course["standards"]), "units")
