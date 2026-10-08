"""Generate district game content for all 38 TN districts via Sarvam API.
Writes data/games/content/<slug>.json (skips districts that already have valid content).
Run:  python scripts/generate_district_content.py [--only slug]
"""
import json
import os
import re
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(__file__).resolve().parent.parent
load_dotenv(BASE / ".env")

API_KEY = os.getenv("SARVAM_API_KEY", "sk_gf2byh03_T10h1azKZvePwJbuviRy1M8A")
URL = "https://api.sarvam.ai/v1/chat/completions"
MODEL = "sarvam-105b"

GAMES = BASE / "data" / "games"
CONTENT = GAMES / "content"
CONTENT.mkdir(parents=True, exist_ok=True)
LOG = BASE / "scripts" / "games_gen.log"

DIV_NAME = {"north": "வடக்கு மண்டலம்", "central": "மத்திய மண்டலம்",
            "west": "மேற்கு மண்டலம்", "south": "தெற்கு மண்டலம்"}


def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def build_prompt(d):
    return f"""நீ ஒரு குழந்தைகள் விளையாட்டு எழுத்தாளர். தமிழ்நாட்டின் மாவட்டம் ஒன்றைப் பற்றி விளையாட்டு உள்ளடக்கம் எழுது.

மாவட்டம்: {d['name_ta']}
புகழ்: {d['fame']}
மண்டலம்: {DIV_NAME[d['division']]}

சரியாக இந்த JSON வடிவத்தில் மட்டும் பதில் சொல் (``` குறியீட்டுக் கட்டம் வேண்டாம்):
{{
  "story": [
    {{"scene": "காலை", "text": "2-4 வாக்கியக் கதை"}},
    {{"scene": "மதியம்", "text": "..."}},
    {{"scene": "மாலை", "text": "..."}}
  ],
  "quiz": [
    {{"q": "கேள்வி", "options": ["விடை1","விடை2","விடை3","விடை4"], "ans": 0, "ex": "விளக்கம்"}}
  ],
  "puzzles": [
    {{"type": "riddle", "q": "புதிர் கேள்வி", "answer": "ஒரு சொல்", "hint": "குறிப்பு"}},
    {{"type": "riddle", "q": "...", "answer": "...", "hint": "..."}},
    {{"type": "sequence", "q": "சரியான வரிசை எது?", "options": ["வரிசை1","வரிசை2","வரிசை3","வரிசை4"], "ans": 0, "ex": "விளக்கம்"}}
  ],
  "path": {{
    "start": "n1",
    "nodes": {{
      "n1": {{"emoji": "🚶", "text": "பயணி வருகிறார்", "choices": [{{"label": "வழி தேர்வு1", "to": "n2"}}, {{"label": "வழி தேர்வு2", "to": "l1", "wrong": true}}]}},
      "n2": {{"emoji": "🛕", "text": "...", "choices": [{{"label": "...", "to": "win"}}, {{"label": "...", "to": "l1", "wrong": true}}]}},
      "l1": {{"emoji": "⚠️", "end": "lose", "text": "தவறான வழி – மீண்டும் முயற்சி"}},
      "win": {{"emoji": "🏆", "end": "win", "text": "வெற்றி!", "badge": "பட்டம் பெயர்"}}
    }}
  }}
}}

விதிகள்:
- story: கண்டிப்பாக 3 காட்சிகள். பொம்மலாட்டம் நாடகப் பாணியில், குழந்தைகளுக்கு எளிய தமிழில். மாவட்டத்தின் வரலாறு + எதற்குப் புகழ்பெற்றது என்பதைச் சொல். மிகவும் பிரபலமான உண்மைகள் மட்டும்; கற்பனைத் தேதிகள்/பெயர்கள் வேண்டாம்.
- quiz: கண்டிப்பாக 6 கேள்விகள் — மாவட்டம் பற்றி 4 + தமிழ்நாடு பொதுஅறிவு 2. ஒவ்வொரு கேள்விக்கும் 4 விடைகள், சரியானது ஒன்றே; ans சரியான விடையின் (0-3) குறியீடு; ex ஒரு வாக்கிய விளக்கம்.
- puzzles: கண்டிப்பாக 3 — riddle 2 (answer மாவட்டத்துடன் தொடர்புடைய ஒரு பொதுவான தமிழ் சொல், 3-10 எழுத்துகள், hint கொடு) + sequence 1 (சரியான வரிசை காட்டும் MCQ).
- path: பயணி ஒருவர் இம்மாவட்டத்தில் பயணிக்கிறார் — கிளைப்பாதை சாகசம். nodes 6-8 (end உட்பட). ஒவ்வொரு சாதாரண node-க்கும் choices 2-3; சரியான ஒன்றுக்கு wrong குறியீடு இல்லை; மற்றவை wrong: true. wrong choices எல்லாம் ஒரு lose node-க்கு (அல்லது பின்னோட்டம்) செல்ல வேண்டும். சரியான வழிகள் மட்டுமே win node-க்குச் செல்ல வேண்டும். குறைந்தது 1 lose node. node வாக்கியம் 1-2; choice label ≤4 சொற்கள். win node-ல் badge பெயர் இருக்க வேண்டும்.
- அனைத்தும் தமிழில். சரியான JSON மட்டும்."""


def clean_json(text):
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```")[1]
        if t.startswith("json"):
            t = t[4:]
    t = t.strip()
    start, end = t.find("{"), t.rfind("}")
    if start != -1 and end != -1:
        t = t[start:end + 1]
    # repair: model sometimes writes Tamil string values without quotes
    t = re.sub(r'":\s+([஀-௿][^"\n]*)"\s*([,}\]])',
               lambda m: '": "' + m.group(1).strip() + '"' + m.group(2), t)
    t = re.sub(r'":\s+([஀-௿][^"\n]*?)(\s*[,}\]])',
               lambda m: '": "' + m.group(1).strip() + '"' + m.group(2), t)
    return json.loads(t)


def validate(c, d):
    errs = []
    story = c.get("story")
    if not isinstance(story, list) or len(story) < 3:
        errs.append("story needs >=3 scenes")
    else:
        for s in story:
            if not (isinstance(s, dict) and str(s.get("scene", "")).strip() and len(str(s.get("text", "")).strip()) > 20):
                errs.append("bad story scene")
    quiz = c.get("quiz")
    if not isinstance(quiz, list) or len(quiz) != 6:
        errs.append(f"quiz needs exactly 6, got {len(quiz) if isinstance(quiz, list) else 0}")
    else:
        for q in quiz:
            opts = q.get("options") or []
            if not (str(q.get("q", "")).strip() and len(opts) == 4 and len(set(opts)) == 4):
                errs.append("bad quiz item shape")
            elif not (isinstance(q.get("ans"), int) and 0 <= q["ans"] < 4):
                errs.append("quiz ans out of range")
            if not str(q.get("ex", "")).strip():
                errs.append("quiz missing ex")
    pz = c.get("puzzles")
    if not isinstance(pz, list) or len(pz) < 3:
        errs.append("puzzles needs >=3")
    else:
        nr = sum(1 for p in pz if p.get("type") == "riddle")
        ns = sum(1 for p in pz if p.get("type") == "sequence")
        if nr < 2 or ns < 1:
            errs.append(f"need 2 riddles + 1 sequence (got riddle={nr}, seq={ns})")
        for p in pz:
            if p.get("type") == "riddle":
                if not (str(p.get("q", "")).strip() and len(str(p.get("answer", "")).strip()) >= 3 and str(p.get("hint", "")).strip()):
                    errs.append("bad riddle")
            elif p.get("type") == "sequence":
                opts = p.get("options") or []
                if not (len(opts) == 4 and isinstance(p.get("ans"), int) and 0 <= p["ans"] < 4):
                    errs.append("bad sequence")
            else:
                errs.append("unknown puzzle type")
    path = c.get("path") or {}
    nodes = path.get("nodes") or {}
    start = path.get("start")
    if not isinstance(nodes, dict) or start not in nodes:
        errs.append("path start missing")
        return errs
    wins = [k for k, n in nodes.items() if n.get("end") == "win"]
    loses = [k for k, n in nodes.items() if n.get("end") == "lose"]
    if not wins:
        errs.append("no win ending")
    if not loses:
        errs.append("no lose ending")
    for k, n in nodes.items():
        if n.get("end"):
            if n.get("end") not in ("win", "lose") or not str(n.get("text", "")).strip():
                errs.append(f"bad end node {k}")
            continue
        ch = n.get("choices") or []
        if len(ch) < 2:
            errs.append(f"node {k} needs >=2 choices")
        good = 0
        for c2 in ch:
            if c2.get("to") not in nodes:
                errs.append(f"node {k} choice -> missing {c2.get('to')}")
            if not str(c2.get("label", "")).strip():
                errs.append(f"node {k} empty label")
            if not c2.get("wrong"):
                good += 1
        if good < 1:
            errs.append(f"node {k} has no correct choice")
    # reachability: win via correct-only, lose via some wrong, all reachable
    def bfs(allow_wrong):
        seen, q = {start}, [start]
        while q:
            cur = q.pop()
            for ch in (nodes[cur].get("choices") or []):
                if ch.get("wrong") and not allow_wrong:
                    continue
                t2 = ch.get("to")
                if t2 in nodes and t2 not in seen:
                    seen.add(t2)
                    q.append(t2)
        return seen
    reach_all = bfs(True)
    reach_good = bfs(False)
    if not any(w in reach_good for w in wins):
        errs.append("win not reachable via correct choices")
    if not any(l in reach_all for l in loses):
        errs.append("lose not reachable")
    unseen = set(nodes) - reach_all
    if unseen:
        errs.append(f"unreachable nodes: {sorted(unseen)}")
    # a wrong choice must exist among reachable correct-path nodes
    has_wrong = any(ch.get("wrong") for k in reach_good for ch in (nodes[k].get("choices") or []))
    if not has_wrong:
        errs.append("no wrong choices on main path")
    return errs


def generate(d, feedback=""):
    prompt = build_prompt(d)
    if feedback:
        prompt += "\n\nமுந்தைய பதிலில் இந்தப் பிழைகள் இருந்தன — திருத்து:\n" + feedback
    resp = requests.post(
        URL,
        headers={"api-subscription-key": API_KEY, "Content-Type": "application/json"},
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "நீ குழந்தைகள் விளையாட்டு எழுத்தாளர். சரியான JSON மட்டும் பதில் சொல்."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.5,
            "max_tokens": 4200,
            "reasoning_effort": None,
        },
        timeout=180,
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]
    return clean_json(content)


def main():
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]
    districts = json.loads((GAMES / "districts.json").read_text(encoding="utf-8"))["districts"]
    ok = skip = fail = 0
    for i, d in enumerate(districts, 1):
        if only and d["slug"] != only:
            continue
        out = CONTENT / f"{d['slug']}.json"
        if out.exists():
            try:
                prev = json.loads(out.read_text(encoding="utf-8"))
                if not validate(prev, d):
                    skip += 1
                    log(f"[{i}/{len(districts)}] skip (valid): {d['slug']}")
                    continue
            except Exception:
                pass  # regenerate invalid file
        log(f"[{i}/{len(districts)}] generating: {d['slug']} ...")
        last_errs = []
        for attempt in (1, 2, 3):
            try:
                c = generate(d, " ".join(last_errs))
                c["slug"] = d["slug"]
                c["name_ta"] = d["name_ta"]
                c["division"] = d["division"]
                c["fame"] = d["fame"]
                errs = validate(c, d)
                if errs:
                    last_errs = errs
                    raise ValueError("; ".join(errs))
                out.write_text(json.dumps(c, ensure_ascii=False, indent=2), encoding="utf-8")
                log(f"  ok (attempt {attempt})")
                ok += 1
                break
            except Exception as e:
                log(f"  attempt {attempt} failed: {str(e)[:300]}")
                if attempt == 3:
                    fail += 1
                time.sleep(4)
        time.sleep(1)
    log(f"DONE: {ok} generated, {skip} skipped, {fail} failed")


if __name__ == "__main__":
    main()
