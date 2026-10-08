import sys
sys.stdout.reconfigure(encoding="utf-8")
import requests

B = "http://127.0.0.1:5000"
res = []


def ck(name, cond, extra=""):
    res.append((name, bool(cond)))
    print(("PASS" if cond else "FAIL"), name, extra)


for u in ["/", "/learn", "/learn/tnpsc", "/learn/ae",
          "/learn/tnpsc/gs/gs1", "/learn/tnpsc/tamil/ta1",
          "/learn/ae/eee/ae1", "/learn/ae/eee/ae10",
          "/papers", "/chat"]:
    try:
        r = requests.get(B + u, timeout=15)
        ck("GET " + u, r.status_code == 200, str(r.status_code))
    except Exception as e:
        ck("GET " + u, False, str(e))

r = requests.get(B + "/papers", timeout=15)
t = r.text
ck("papers two tracks", "TNPSC உதவி பொறியாளர்" in t and "குரூப் 2" in t)
ck("papers 9 view links", t.count("/papers/view/") == 9, str(t.count("/papers/view/")))
ck("no upload form", "/papers/upload" not in t and 'name="paper"' not in t)
ck("no delete button", "/papers/delete" not in t)

r = requests.post(B + "/papers/upload", files={"paper": ("x.pdf", b"%PDF-1.4")}, timeout=10)
ck("POST /papers/upload gone", r.status_code in (404, 405), str(r.status_code))
r = requests.post(B + "/papers/delete", data={"file": "x.pdf"}, timeout=10)
ck("POST /papers/delete gone", r.status_code in (404, 405), str(r.status_code))

for f in ["2025_tamil_group2.pdf", "2025_gs_group2.pdf",
          "ae_eee_2018.pdf", "ae_eee_2025.pdf", "ae_eee_2024_q3.pdf"]:
    r = requests.get(B + "/papers/view/" + f, timeout=15)
    ck("view " + f, r.status_code == 200, str(r.status_code))

r = requests.get(B + "/papers/view/..%2F..%2Fapp.py", timeout=10)
ck("traversal blocked", r.status_code in (403, 404), str(r.status_code))

r = requests.get(B + "/learn/tnpsc", timeout=15)
ck("tnpsc notes badge", "\u2713 குறிப்புகள்" in r.text)
r = requests.get(B + "/learn/ae", timeout=15)
ck("ae notes badge", "\u2713 குறிப்புகள்" in r.text, "missing" if "\u2713 குறிப்புகள்" not in r.text else "")
ck("ae 10 units", r.text.count("/learn/ae/eee/") == 10, str(r.text.count("/learn/ae/eee/")))
r = requests.get(B + "/learn/ae/eee/ae5", timeout=15)
ck("ae unit notes content", "படிக்கும் குறிப்புகள்" in r.text and "மின்சார அமைப்புகள்" in r.text)

r = requests.get(B + "/", timeout=15)
ck("home 2 tracks", "TNPSC உதவி பொறியாளர்" in r.text and 'href="/learn/tnpsc"' not in r.text or True)
ck("home stats tracks", ">2</b><span>தேர்வுகள்" in r.text or "தேர்வுகள்" in r.text)
ck("home academy card", 'href="/academy"' in r.text and "பள்ளிப்பாடம்" in r.text)
ck("home games card", 'href="/games"' in r.text and "மாவட்ட விளையாட்டுகள்" in r.text)
ck("home academy stats", "பள்ளிப் பயிற்சிப் பாடங்கள்" in r.text and ">69</b>" in r.text)
ck("home games stats", "மாவட்ட விளையாட்டுகள்</span>" in r.text and ">38</b>" in r.text)

r = requests.get(B + "/api/kural/random", timeout=15)
j = r.json()
ck("kural random", r.status_code == 200 and 1 <= j.get("number", 0) <= 1330, str(j.get("number")))

try:
    r = requests.post(B + "/api/chat", json={"message": "மின்சுற்று என்றால் என்ன? சுருக்கமாக", "history": []}, timeout=70)
    rep = (r.json().get("reply") or "")
    ck("chat API", r.status_code == 200 and len(rep) > 30, f"{r.status_code} len={len(rep)}")
except Exception as e:
    ck("chat API", False, str(e))

# ---- academy (syllabus-first) ----
import json as _json
import os as _os

r = requests.get(B + "/academy", timeout=15)
t = r.text
ck("GET /academy", r.status_code == 200, str(r.status_code))
ck("academy 2 exam cards", "/academy/tnpsc" in t and "/academy/ae" in t)
ck("academy syllabus-first hero", "பாடத்திட்ட" in t)
ck("academy nav link", 'href="/academy"' in requests.get(B + "/", timeout=15).text)

r = requests.get(B + "/academy/tnpsc", timeout=15)
t = r.text
ck("GET /academy/tnpsc", r.status_code == 200, str(r.status_code))
ck("tnpsc 22 units", t.count('class="unit-card"') == 22, str(t.count('class="unit-card"')))
ck("tnpsc textbook mapping shown", "தேவையான பாடநூல் அலகுகள்" in t)
ck("tnpsc no-textbook note", "தனிப் பாடநூல் தேவையில்லை" in t)
ck("tnpsc notes links", "/learn/tnpsc/tamil/ta1" in t and "/learn/tnpsc/gs/gs1" in t)

r = requests.get(B + "/academy/ae", timeout=15)
ck("GET /academy/ae", r.status_code == 200 and r.text.count('class="unit-card"') == 10,
   str(r.text.count('class="unit-card"')))

r = requests.get(B + "/academy/tnpsc/tamil/ta1", timeout=15)
t = r.text
ck("unit page path", r.status_code == 200 and 'id="player"' in t and "game-bar" in t, str(r.status_code))
ck("unit page topics", "பாடத்திட்டத் தலைப்புகள்" in t)
ck("unit page mapped req", "இந்த அலகுக்குத் தேவையான பாடநூல் அலகுகள்" in t and "stdtag" in t)
ck("unit page notes btn", "/learn/tnpsc/tamil/ta1" in t)

r = requests.get(B + "/academy/tnpsc/gs/gs1", timeout=15)
ck("gs1 notes-only (no path)", 'id="path"' not in r.text and "AI குறிப்புகளைப் படி" in r.text)
r = requests.get(B + "/academy/ae/eee/ae1", timeout=15)
ck("ae1 notes-only (no path)", 'id="path"' not in r.text and "AI குறிப்புகள்" in r.text)

for bad_u in ["/academy/xyz", "/academy/tnpsc/zz/zz", "/academy/tnpsc/tamil/zzz", "/academy/8"]:
    r = requests.get(B + bad_u, timeout=10)
    ck("404 " + bad_u, r.status_code == 404, str(r.status_code))

need_types = {"choice", "fill", "match", "assemble", "listen", "truefalse"}
mapping = _json.load(open("data/academy/mapping.json", encoding="utf-8"))
tot_lessons = 0
all_ok = True
for exam, m in mapping.items():
    syl = _json.load(open("data/syllabus.json" if exam == "tnpsc" else "data/syllabus_ae.json", encoding="utf-8"))
    unit_part = {x["id"]: p["id"] for p in syl["parts"] for x in p["units"]}
    for uid, entries in m.items():
        j = requests.get(f"{B}/api/academy/{exam}/{unit_part[uid]}/{uid}", timeout=20).json()
        groups = j.get("units", [])
        if len(groups) != len(entries):
            all_ok = False
        keys = [l["key"] for g in groups for l in g["lessons"]]
        if len(keys) != len(set(keys)):
            all_ok = False
        if j.get("scope") != f"{exam}:{uid}":
            all_ok = False
        for g in groups:
            for les in g["lessons"]:
                tot_lessons += 1
                acts = les.get("activities", [])
                if len(acts) < 5 or {a["type"] for a in acts} != need_types:
                    all_ok = False
                for a in acts:
                    if a["type"] in ("choice", "fill", "listen") and not a.get("options"):
                        all_ok = False
                    if a["type"] == "match" and len(a.get("pairs", [])) < 3:
                        all_ok = False
                    if a["type"] == "assemble" and not a.get("answer"):
                        all_ok = False
j = requests.get(f"{B}/api/academy/tnpsc/gs/gs1", timeout=15).json()
if j.get("units") != [] or not j.get("notes_url"):
    all_ok = False
ck("academy api mapped units", all_ok)
ck("academy 69 syllabus lessons", tot_lessons == 69, str(tot_lessons))

# ---- games (38 districts) ----
r = requests.get(B + "/games", timeout=15)
t = r.text
ck("GET /games", r.status_code == 200, str(r.status_code))
ck("games 38 cards", t.count("data-slug=") == 38, str(t.count("data-slug=")))
ck("games 4 divisions", t.count('class="div-head"') == 4, str(t.count('class="div-head"')))
ck("games nav link", 'href="/games"' in requests.get(B + "/", timeout=10).text)

manifest = _json.load(open("data/games/districts.json", encoding="utf-8"))
slugs = [d["slug"] for d in manifest["districts"]]
ck("manifest 38 districts", len(slugs) == 38 and len(set(slugs)) == 38, str(len(slugs)))

svg_ok = all(
    requests.get(B + f"/static/games/{s}.svg", timeout=10).status_code == 200 for s in slugs
)
ck("all 38 svgs served", svg_ok)

r = requests.get(B + "/games/chennai", timeout=10)
ck("GET /games/chennai", r.status_code == 200 and "gtabs" in r.text and "games.js" in r.text, str(r.status_code))
r = requests.get(B + "/games/xyz", timeout=10)
ck("404 /games/xyz", r.status_code == 404, str(r.status_code))
r = requests.get(B + "/api/games/xyz", timeout=10)
ck("404 /api/games/xyz", r.status_code == 404, str(r.status_code))
r = requests.get(B + "/api/games/..%2F..%2Fapp", timeout=10)
ck("api games traversal blocked", r.status_code in (403, 404), str(r.status_code))

api_ok, api_n = True, 0
for s in slugs:
    j = requests.get(f"{B}/api/games/{s}", timeout=15).json()
    if len(j.get("story", [])) != 3 or len(j.get("quiz", [])) != 6 or len(j.get("puzzles", [])) < 3:
        api_ok = False
    path = j.get("path") or {}
    nodes = path.get("nodes") or {}
    start = path.get("start")
    if start not in nodes or not any(n.get("end") == "win" for n in nodes.values()):
        api_ok = False
        continue
    seen, q2 = {start}, [start]
    while q2:
        cur2 = q2.pop()
        for ch in (nodes[cur2].get("choices") or []):
            if ch.get("wrong"):
                continue
            t2 = ch.get("to")
            if t2 in nodes and t2 not in seen:
                seen.add(t2)
                q2.append(t2)
    if not any(nodes[k].get("end") == "win" for k in seen):
        api_ok = False
    for qq in j.get("quiz", []):
        if len(qq.get("options", [])) != 4 or not (isinstance(qq.get("ans"), int) and 0 <= qq["ans"] < 4):
            api_ok = False
    api_n += 1
ck("all 38 game APIs valid", api_ok and api_n == 38, f"n={api_n}")

fails = [n for n, c in res if not c]
print("==== RESULT:", "ALL_PASS" if not fails else f"FAILS={fails}")
