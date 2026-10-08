"""Generate Duolingo-style activities for every academy unit via Sarvam API.
Reads data/academy/course.json + data/academy/slices/*.txt
Writes data/academy/lessons/std{N}_u{M}.json  (skips existing)
Run:  python scripts/generate_course.py [std_filter]
"""
import json
import os
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

ACAD = BASE / "data" / "academy"
SLICES = ACAD / "slices"
LESSONS = ACAD / "lessons"
LESSONS.mkdir(exist_ok=True)

VALID_TYPES = {"choice", "fill", "match", "assemble", "listen", "truefalse"}


def build_prompt(unit, std_label, slice_text):
    provided = " | ".join(unit.get("lessons", [])[:6]) or "(இல்லை)"
    return f"""நீ ஒரு தமிழ் ஆசிரியர். பத்தாம் வகுப்பு பாடப்புத்தகத்திலிருந்து ({std_label}) டூயோலிங்கோ செயலி போன்ற படிப்படியான பயிற்சிப் பாடங்கள் உருவாக்கு.

அலகுத் தலைப்பு: {unit['title']}
பாட வரிசைப் பெயர்கள் (ஏற்கனவே உள்ளன, தேவைப்பட்டால் மேம்படுத்தலாம்): {provided}

கொடுக்கப்பட்ட பாட வெட்டு (PDF எடுப்பில் சில இடங்களில் இரட்டை எழுத்துகள்/தவறான இடைவெளிகள்/தூய தமிழ் அல்லாத குறியீடுகள் வந்திருக்கலாம் — அர்த்தம் புரிந்து, சரியான தமிழில் எழுதுக):
---
{slice_text}
---

சரியாக இந்த JSON வடிவமைப்பில் மட்டும் பதில் சொல் (``` குறியீட்டுக் கட்டம் வேண்டாம், வேறு வாக்கியம் வேண்டாம்):
{{
  "unit_title": "திருத்திய, சரியான எழுத்துப்பிழை இல்லாத அலகுத் தலைப்பு",
  "lessons": [
    {{
      "name": "பாடத்தின் பெயர்",
      "activities": [
        {{"type": "choice", "q": "கேள்வி?", "options": ["விடை", "தவறு1", "தவறு2", "தவறு3"], "ans": 0, "ex": "சிறு விளக்கம்"}},
        {{"type": "fill", "q": "வாக்கியத்தில் காலியிடம்: ___", "options": ["சரியான சொல்", "தவறு1", "தவறு2", "தவறு3"], "ans": 0, "ex": "விளக்கம்"}},
        {{"type": "match", "q": "சொல்லை அதன் பொருளுடன் பொருத்துக", "pairs": [["சொல்1", "பொருள்1"], ["சொல்2", "பொருள்2"], ["சொல்3", "பொருள்3"], ["சொல்4", "பொருள்4"]]}},
        {{"type": "assemble", "q": "சொற்களை வரிசைப்படுத்தி அழகான வாக்கியம் அமைக்கவும்", "words": ["சொல்", "சொல்", "சொல்", "சொல்"], "answer": "சரியான முழு வாக்கியம்"}},
        {{"type": "listen", "speak": "கேட்க வேண்டிய சொல்", "q": "கேட்டதற்கு பொருந்துவது எது?", "options": ["விடை", "தவறு1", "தவறு2", "தவறு3"], "ans": 0}},
        {{"type": "truefalse", "q": "இக்கூற்று சரியா?", "ans": true, "ex": "விளக்கம்"}}
      ]
    }}
  ],
  "keywords": ["முக்கியச் சொல்1", "முக்கியச் சொல்2", "முக்கியச் சொல்3", "முக்கியச் சொல்4"]
}}

விதிகள்:
- "lessons" இல் சரியாக 3 பாடங்கள்; ஒவ்வொரு பாடத்திலும் சரியாக 6 செயல்பாடுகள் (activities).
- ஒவ்வொரு பாடத்திலும் குறைந்தது: 1 choice, 1 fill, 1 match, 1 assemble, 1 listen, 1 truefalse (ஒழுங்கு மாற்றலாம்).
- கேள்விகள் பாட வெட்டில் உள்ள உண்மையான தகவலை அடிப்படையாகக் கொள்ள வேண்டும்; கற்பனைக் கதை வேண்டாம்.
- எல்லா விடைகளும் விளக்கங்களும் தமிழில் இருக்க வேண்டும். choice/fill/listen: ஒவ்வொரு விருப்பத்திலும் 1 சரியானது; "ans" அதன் index (0-3).
- match: "pairs" இல் சரியாக 4 இணைகள். assemble: 4 முதல் 7 சொற்கள், "answer" முழு சரியான வாக்கியம்.
- listen "speak": 1 முதல் 4 சொல் கொண்ட தெளிவான தமிழ் சொல்/சொற்றொடர்.
- இரட்டை எழுத்துப் பிழைகள் (எ.கா. "பண்பபாாடு", "மொொழி"), தேவையற்ற இடைவெளிகள் ஆகியவற்றைத் திருத்தி சரியான தமிழில் மட்டும் எழுது.
- கடினமான சொற்களுக்கு எளிய விளக்கம் கொடு; 6-8 வகுப்பு மாணவர் புரிந்துகொள்ளும் நடை."""


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
    return json.loads(t)


def clamp(ans, n):
    try:
        a = int(ans)
    except (TypeError, ValueError):
        return 0
    return max(0, min(n - 1, a))


def validate(data):
    lessons = data.get("lessons")
    if not isinstance(lessons, list) or len(lessons) < 3:
        return None
    lessons = lessons[:3]
    for les in lessons:
        acts = les.get("activities")
        if not isinstance(acts, list):
            return None
        kept = []
        for a in acts[:8]:
            t = a.get("type")
            if t not in VALID_TYPES:
                continue
            if t in ("choice", "fill", "listen"):
                opts = [str(o) for o in a.get("options", []) if str(o).strip()]
                if len(opts) < 2:
                    continue
                a["options"] = opts[:4]
                a["ans"] = clamp(a.get("ans"), len(a["options"]))
            elif t == "match":
                pairs = [[str(x), str(y)] for x, y in a.get("pairs", [])][:6]
                if len(pairs) < 3:
                    continue
                a["pairs"] = pairs
            elif t == "assemble":
                words = [str(w) for w in a.get("words", []) if str(w).strip()]
                if len(words) < 3 or not str(a.get("answer", "")).strip():
                    continue
                a["words"] = words[:8]
            elif t == "truefalse":
                a["ans"] = bool(a.get("ans"))
            a["q"] = str(a.get("q", "")).strip() or a.get("speak", "பயிற்சி")
            if t == "listen" and not str(a.get("speak", "")).strip():
                continue
            a.setdefault("ex", "")
            kept.append(a)
        les["activities"] = kept
        les["name"] = str(les.get("name", "")).strip() or "பாடம்"
    if any(len(l.get("activities", [])) < 5 for l in lessons):
        return None
    return {
        "unit_title": str(data.get("unit_title", "")).strip(),
        "keywords": [str(k) for k in data.get("keywords", [])][:8],
        "lessons": lessons,
    }


def generate(std_label, unit, slice_text):
    resp = requests.post(
        URL,
        headers={"api-subscription-key": API_KEY, "Content-Type": "application/json"},
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "நீ ஒரு தமிழ் ஆசிரியர். தரமான பயிற்சிகள் உருவாக்கு. சரியான JSON மட்டும் பதில் சொல்."},
                {"role": "user", "content": build_prompt(unit, std_label, slice_text)},
            ],
            "temperature": 0.5,
            "max_tokens": 7000,
            "reasoning_effort": None,
        },
        timeout=180,
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]
    return validate(clean_json(content))


def main():
    std_filter = sys.argv[1] if len(sys.argv) > 1 else None
    course = json.loads((ACAD / "course.json").read_text(encoding="utf-8"))
    jobs = []
    for s in course["standards"]:
        if std_filter and s["std"] != std_filter:
            continue
        for idx, u in enumerate(s["units"], 1):
            jobs.append((s, idx, u))

    ok, fail, skip = 0, 0, 0
    for i, (s, idx, u) in enumerate(jobs, 1):
        out = LESSONS / f"std{s['std']}_u{idx}.json"
        if out.exists():
            skip += 1
            continue
        slice_path = SLICES / f"std{s['std']}_u{idx}.txt"
        text = slice_path.read_text(encoding="utf-8") if slice_path.exists() else ""
        text = text[:6500]
        if len(text) < 300:
            print(f"[{i}/{len(jobs)}] skip tiny slice: {out.name}")
            skip += 1
            continue
        print(f"[{i}/{len(jobs)}] generating {out.name} :: {u['title'][:35]} ...", flush=True)
        t0 = time.time()
        for attempt in (1, 2):
            try:
                data = generate(s["label"], u, text)
                if not data:
                    raise ValueError("validation failed")
                data["std"] = s["std"]
                data["unit_idx"] = idx
                out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
                n = sum(len(l["activities"]) for l in data["lessons"])
                print(f"  ok ({len(data['lessons'])} lessons, {n} activities, {time.time()-t0:.0f}s)")
                ok += 1
                break
            except Exception as e:
                print(f"  attempt {attempt} failed: {e}", flush=True)
                if attempt == 2:
                    fail += 1
                time.sleep(4)
    print(f"DONE: {ok} generated, {fail} failed, {skip} skipped, {len(jobs)} total")


if __name__ == "__main__":
    main()
