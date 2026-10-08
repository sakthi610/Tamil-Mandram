"""
TNPSC Group 2/2A – Tamil Competitive Exam Learning App
Sections: Learning | Previous Year Papers | AI Doubt Chatbot
Model: Sarvam AI (sarvam-105b)

Run:  pip install -r requirements.txt
      python app.py
Open: http://127.0.0.1:5000
"""
import json
import os
import traceback
from pathlib import Path

import requests
from dotenv import load_dotenv
from flask import (Flask, abort, flash, jsonify, redirect, render_template,
                   request, url_for)
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "tamil-exam-app-secret")
app.config["MAX_CONTENT_LENGTH"] = 40 * 1024 * 1024  # 40 MB upload limit

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
NOTES_DIR = DATA_DIR / "notes"
PAPERS_DIR = BASE_DIR / "static" / "papers"
PAPERS_JSON = DATA_DIR / "papers.json"
NOTES_DIR.mkdir(exist_ok=True)
PAPERS_DIR.mkdir(parents=True, exist_ok=True)

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "sk_gf2byh03_T10h1azKZvePwJbuviRy1M8A")
SARVAM_URL = "https://api.sarvam.ai/v1/chat/completions"
MODEL = "sarvam-105b"

# ---------------------------------------------------------------- helpers

def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


SYLLABUS = load_json(DATA_DIR / "syllabus.json", {"parts": []})
SYLLABUS_AE = load_json(DATA_DIR / "syllabus_ae.json", {"parts": []})

# Learning tracks: tnpsc = Group 2/2A, ae = Assistant Engineer (EEE)
TRACKS = {
    "tnpsc": {"key": "tnpsc", "label": "TNPSC குரூப் 2 & 2A", "syllabus": SYLLABUS},
    "ae": {"key": "ae", "label": "TNPSC உதவி பொறியாளர் (AE – EEE)", "syllabus": SYLLABUS_AE},
}

# Paper tracks: previous year question papers
PAPER_TRACKS = {
    "tnpsc": {"key": "tnpsc", "label": "TNPSC குரூப் 2 & 2A", "icon": "🏛️"},
    "ae": {"key": "ae", "label": "TNPSC உதவி பொறியாளர் (EEE)", "icon": "⚡"},
}

# ---- Verified Tirukkural dataset (all 1330 couplets + 133 adhigarams) ----
def _load_kurals():
    try:
        raw = load_json(DATA_DIR / "tirukkural.json", {})
        kurals = raw.get("kural", []) if isinstance(raw, dict) else raw
        by_num = {}
        for k in kurals:
            try:
                n = int(k.get("Number"))
            except (TypeError, ValueError):
                continue
            by_num[n] = {
                "n": n,
                "text": f"{k.get('Line1','').strip()}\n{k.get('Line2','').strip()}",
                "flat": (str(k.get("Line1", "")) + str(k.get("Line2", ""))).replace(" ", ""),
                "mv": (k.get("mv") or "").strip(),
                "sp": (k.get("sp") or "").strip(),
            }
        chapters = []
        det = load_json(DATA_DIR / "tirukkural_detail.json", [])
        for paal in det[0].get("section", {}).get("detail", []):
            for iyal in paal.get("chapterGroup", {}).get("detail", []):
                for ch in iyal.get("chapters", {}).get("detail", []):
                    chapters.append({
                        "num": ch.get("number"), "name": ch.get("name", ""),
                        "start": ch.get("start"), "end": ch.get("end"),
                        "iyal": iyal.get("name", ""), "paal": paal.get("name", ""),
                    })
        ch_of = {}
        for c in chapters:
            for n in range(c["start"], c["end"] + 1):
                ch_of[n] = c
        return by_num, chapters, ch_of
    except Exception as e:
        print("Tirukkural load failed:", e)
        return {}, [], {}


KURALS, ADHIGARAMS, KURAL_CH = _load_kurals()


def kural_info(n):
    k = KURALS.get(n)
    if not k:
        return None
    ch = KURAL_CH.get(n, {})
    return {
        "number": n,
        "adhigaram": ch.get("name", ""),
        "iyal": ch.get("iyal", ""),
        "paal": ch.get("paal", ""),
        "line1": k["text"].split("\n")[0],
        "line2": k["text"].split("\n")[1] if "\n" in k["text"] else "",
        "text": k["text"],
        "meaning_mv": k["mv"],
        "meaning_sp": k["sp"],
    }


def find_kurals(msg):
    """Return verified kurals relevant to msg (never fabricated)."""
    import re
    # 1) explicit kural number: "குறள் 926" / "kural 391"
    m = re.search(r"(?:குறள்|kural)\s*#?\s*(\d{1,4})", msg, re.I)
    if m:
        n = int(m.group(1))
        info = kural_info(n)
        return [info] if info else []
    # 2) adhigaram name mentioned → first kurals of that chapter
    norm = msg.replace(" ", "")
    for c in ADHIGARAMS:
        cname = c["name"].replace(" ", "")
        if len(cname) >= 4 and cname in norm:
            return [kural_info(n) for n in range(c["start"], min(c["start"] + 3, c["end"] + 1)) if kural_info(n)]
    # 3) word-overlap search over all kurals
    words = [w for w in re.findall(r"[஀-௿]{3,}", msg)]
    if not words:
        return []
    scores = []
    for n, k in KURALS.items():
        s = sum(1 for w in words if w in k["flat"])
        if s:
            scores.append((s, n))
    scores.sort(reverse=True)
    return [kural_info(n) for _, n in scores[:5] if kural_info(n)]


def kural_context_block(infos):
    lines = ["[சரிபார்க்கப்பட்ட திருக்குறள் குறிப்புகள் – இவற்றிலிருந்து மட்டுமே மேற்கோள் காட்டுக; வேறு குறள் கற்பனையாக வேண்டாம்]"]
    for i in infos:
        lines.append(
            f"குறள் {i['number']} (அதிகாரம்: {i['adhigaram']}, இயல்: {i['iyal']}, பால்: {i['paal']})\n"
            f"{i['text']}\n"
            f"மு.வ உரை: {i['meaning_mv']}\nசாலமன் உரை: {i['meaning_sp']}"
        )
    return "\n\n".join(lines)


def syllabus_summary():
    out = []
    for track in TRACKS.values():
        s = track["syllabus"]
        out.append(f"{s.get('exam_short', '')} – {s.get('pattern', '')}")
        for part in s.get("parts", []):
            q = part.get("questions")
            out.append(f"{part['title']}" + (f" ({q} கேள்விகள்)" if q else "") + ":")
            for u in part.get("units", []):
                uq = u.get("questions")
                out.append(f"  - {u['title']}" + (f" ({uq} கேள்விகள்)" if uq else ""))
    return "\n".join(out)


SYSTEM_PROMPT = f"""நீ ஒரு TNPSC தேர்வுகளுக்கான உதவிகரமான தமிழ் AI ஆசிரியர் நண்பன் — குறிப்பாக குரூப் 2/2A மற்றும் உதவி பொறியாளர் (AE – EEE) தேர்வுகள்.

முக்கிய விதிகள்:
1. எப்போதும் தமிழ் எழுத்துக்களில் மட்டுமே பதில் சொல். Tanglish / Roman எழுத்துக்களில் ஒருபோதும் பதில் சொல்லாதே.
2. பயனர் English-ல் அல்லது Tanglish-ல் கேட்டாலும், நீ தூய தமிழில் பதில் சொல்.
3. இது தேர்வு வேட்பாளர்களுக்கான சந்தேகத் தீர்வு சாட்போட் – தேர்வு சார்ந்த கேள்விகளுக்கு துல்லியமான, பரீட்சைக்கு ஏற்ற பதில் சொல். AE-EEE (இயந்திரம், மின்சுற்று, மின்சக்தி மின்னணுவியல் போன்ற) கேள்விகளுக்கும் பொருத்தமான பதில் சொல்.
4. எளிய, இனிமையான, நட்பான தமிழில் பேசு. பதில்கள் சுருக்கமாகவும் தெளிவாகவும் இருக்கட்டும்.
5. தேவைப்பட்டால் எடுத்துக்காட்டுகள், முக்கியக் கருத்துகள் பட்டியலாக சொல்.
6. பாடத்திட்டம் தெரிந்திருக்கும்போது அந்த அலகுக்கு தொடர்புடைய விடயத்தை மட்டுமே சொல்.
7. மேற்கோள் விதி (மிக முக்கியம்): திருக்குறள், நாலடியார், சங்க இலக்கியம் போன்ற நூல்களிலிருந்து வரிகளை அப்படியே மேற்கோள் காட்டும்போது —
   - உரையாடலில் "சரிபார்க்கப்பட்ட திருக்குறள் குறிப்புகள்" என தரப்பட்டால் அந்த வரிகளை மட்டுமே பயன்படுத்து.
   - சரிபார்ப்புக் குறிப்பு இல்லாதபோது குறள் எண், அதிகாரப் பெயர் அல்லது வரிகளைக் கற்பனையாகச் சொல்லாதே. சரியான வரிகள் ஞாபகம் இல்லாவிட்டால் "சரியான வரிகள் ஞாபகம் இல்லை" என்று நேர்மையாகச் சொல்லி, அந்தக் கருத்தை எளிமையாக விளக்கு.
   - பொய்யான/தவறான மேற்கோள் ஒருபோதும் ஏற்புடையதல்ல.

பாடத்திட்டச் சுருக்கம் (இரு தேர்வுகளும்):
{syllabus_summary()}
"""

# ---------------------------------------------------------------- pages

def _track_stats(syllabus):
    units = [u for p in syllabus.get("parts", []) for u in p.get("units", [])]
    return {
        "parts": len(syllabus.get("parts", [])),
        "units": len(units),
        "questions": sum(int(u.get("questions") or 0) for u in units),
    }


@app.route("/")
def home():
    stats = {
        "tracks": len(TRACKS),
        "units": sum(_track_stats(t["syllabus"])["units"] for t in TRACKS.values()),
        "papers": len(get_papers()),
        "academy_units": sum(len(v) for m in _academy_map().values() for v in m.values()),
        "academy_lessons": sum(
            _lesson_count(e.get("std"), e.get("unit"))
            for m in _academy_map().values() for v in m.values() for e in v
        ),
        "games_total": len(_games_manifest().get("districts", [])),
        "games_ready": len(list(GAMES_CONTENT.glob("*.json"))),
    }
    tracks = [
        {
            "key": t["key"],
            "label": t["label"],
            "stats": _track_stats(t["syllabus"]),
        }
        for t in TRACKS.values()
    ]
    return render_template("home.html", tracks=tracks, stats=stats)


@app.route("/learn")
def learn():
    tracks = [
        {
            "key": t["key"],
            "label": t["label"],
            "exam": t["syllabus"].get("exam", ""),
            "pattern": t["syllabus"].get("pattern", ""),
            "breakdown": t["syllabus"].get("breakdown", ""),
            "stats": _track_stats(t["syllabus"]),
        }
        for t in TRACKS.values()
    ]
    return render_template("learn.html", tracks=tracks)


@app.route("/learn/<track>")
def learn_track(track):
    t = TRACKS.get(track)
    if not t:
        abort(404)
    notes_available = {p.stem for p in NOTES_DIR.glob("*.json")}
    return render_template("track.html", track=t, syllabus=t["syllabus"],
                           notes=notes_available, stats=_track_stats(t["syllabus"]))


@app.route("/learn/<track>/<part_id>/<unit_id>")
def unit(track, part_id, unit_id):
    t = TRACKS.get(track)
    if not t:
        abort(404)
    syllabus = t["syllabus"]
    part = next((p for p in syllabus.get("parts", []) if p["id"] == part_id), None)
    if not part:
        abort(404)
    u = next((x for x in part.get("units", []) if x["id"] == unit_id), None)
    if not u:
        abort(404)
    note = load_json(NOTES_DIR / f"{unit_id}.json", None)
    return render_template("unit.html", track=t, syllabus=syllabus, part=part,
                           unit=u, note=note)


@app.route("/papers")
def papers():
    all_papers = get_papers()
    groups = []
    for key, meta in PAPER_TRACKS.items():
        items = [p for p in all_papers if p.get("track", "tnpsc") == key]
        if items:
            groups.append({"meta": meta, "papers": items})
    return render_template("papers.html", groups=groups, total=len(all_papers))


@app.route("/papers/view/<filename>")
def view_paper(filename):
    safe = secure_filename(filename)
    if not safe.lower().endswith(".pdf") or not (PAPERS_DIR / safe).is_file():
        abort(404)
    meta = next((p for p in get_papers() if p["file"] == safe), None)
    if not meta:
        meta = {"file": safe, "title": safe, "exam": "", "year": "", "subject": ""}
    return render_template("view_paper.html", meta=meta, filename=safe)


@app.route("/chat")
def chat_page():
    return render_template("chat.html", syllabus=SYLLABUS)


# ---------------------------------------------------------------- academy (syllabus-first, Duolingo-style)

ACADEMY_JSON = DATA_DIR / "academy" / "course.json"
ACADEMY_LESSONS_DIR = DATA_DIR / "academy" / "lessons"
ACADEMY_MAP_JSON = DATA_DIR / "academy" / "mapping.json"


def _academy_map():
    return load_json(ACADEMY_MAP_JSON, {})


def _std_obj(std):
    course = load_json(ACADEMY_JSON, {"standards": []})
    return next((s for s in course.get("standards", []) if s.get("std") == str(std)), None)


def _std_label(std):
    s = _std_obj(std)
    return (s or {}).get("label", f"{std}ஆம் வகுப்பு")


def _std_color(std):
    s = _std_obj(std)
    return (s or {}).get("color", "#58cc02")


def _unit_title(std, uidx):
    s = _std_obj(std)
    if not s:
        return ""
    units = s.get("units", [])
    return units[uidx - 1].get("title", "") if 1 <= uidx <= len(units) else ""


def _lesson_count(std, uidx):
    gen = load_json(ACADEMY_LESSONS_DIR / f"std{std}_u{uidx}.json", None)
    return len(gen.get("lessons", [])) if gen else 0


def _mapped_entries(exam, unit_id):
    """mapped textbook units for a syllabus unit → display-ready list."""
    out = []
    for e in (_academy_map().get(exam, {}) or {}).get(unit_id, []):
        std, uidx = e.get("std"), e.get("unit")
        out.append({
            "std": std,
            "std_label": _std_label(std),
            "color": _std_color(std),
            "unit_title": _unit_title(std, uidx),
            "why": e.get("why", ""),
            "lessons": _lesson_count(std, uidx),
        })
    return out


def _exam_obj(exam):
    return TRACKS.get(exam)


def _find_part_unit(exam, part, unit):
    tr = _exam_obj(exam)
    if not tr:
        return None, None, None
    p = next((x for x in tr["syllabus"].get("parts", []) if x.get("id") == part), None)
    if not p:
        return tr, None, None
    u = next((x for x in p.get("units", []) if x.get("id") == unit), None)
    return tr, p, u


def _academy_exam_cards():
    cards = []
    for key in ("tnpsc", "ae"):
        tr = _exam_obj(key)
        syl = tr["syllabus"]
        m = (_academy_map().get(key, {}) or {})
        n_lessons = 0
        for uid, entries in m.items():
            for e in entries:
                n_lessons += _lesson_count(e.get("std"), e.get("unit"))
        cards.append({
            "key": key,
            "label": tr["label"],
            "exam": syl.get("exam_short") or syl.get("exam", ""),
            "pattern": syl.get("pattern", ""),
            "parts": len(syl.get("parts", [])),
            "units": sum(len(p.get("units", [])) for p in syl.get("parts", [])),
            "linked": len(m),
            "lessons": n_lessons,
            "color": "#c62828" if key == "tnpsc" else "#1d4ed8",
        })
    return cards


@app.route("/academy")
def academy():
    return render_template("academy.html", exams=_academy_exam_cards())


@app.route("/academy/<exam>")
def academy_exam(exam):
    tr = _exam_obj(exam)
    if not tr:
        abort(404)
    m = _academy_map().get(exam, {}) or {}
    notes = {p.stem for p in NOTES_DIR.glob("*.json")}
    parts = []
    for p in tr["syllabus"].get("parts", []):
        units = []
        for u in p.get("units", []):
            uid = u.get("id")
            mapped = _mapped_entries(exam, uid)
            units.append({
                "id": uid,
                "title": u.get("title", ""),
                "questions": u.get("questions"),
                "topics": u.get("topics", []),
                "mapped": mapped,
                "has_path": bool(mapped),
                "has_notes": uid in notes,
                "lessons": sum(x["lessons"] for x in mapped),
            })
        parts.append({
            "id": p.get("id"),
            "title": p.get("title", ""),
            "color": p.get("color", "#58cc02"),
            "level": p.get("level", ""),
            "alt": p.get("alt"),
            "units": units,
        })
    return render_template("academy_exam.html", exam={
        "key": exam,
        "label": tr["label"],
        "syllabus": tr["syllabus"],
        "parts": parts,
    })


@app.route("/academy/<exam>/<part>/<unit>")
def academy_unit(exam, part, unit):
    tr, p, u = _find_part_unit(exam, part, unit)
    if not tr or not p or not u:
        abort(404)
    uid = u.get("id")
    mapped = _mapped_entries(exam, uid)
    has_notes = uid in {x.stem for x in NOTES_DIR.glob("*.json")}
    return render_template(
        "academy_path.html",
        exam_key=exam,
        exam_label=tr["label"],
        part_id=p.get("id"),
        part_title=p.get("title", ""),
        unit=u,
        scope=f"{exam}:{uid}",
        color=p.get("color", "#58cc02"),
        topics=u.get("topics", []),
        mapped=mapped,
        has_path=bool(mapped),
        notes_url=f"/learn/{exam}/{p.get('id')}/{uid}" if has_notes else "",
        api_url=f"/api/academy/{exam}/{p.get('id')}/{uid}",
    )


@app.route("/api/academy/<exam>/<part>/<unit>")
def api_academy_unit(exam, part, unit):
    tr, p, u = _find_part_unit(exam, part, unit)
    if not tr or not p or not u:
        return jsonify({"error": "not found"}), 404
    uid = u.get("id")
    groups = []
    for e in (_academy_map().get(exam, {}) or {}).get(uid, []):
        std, uidx = e.get("std"), e.get("unit")
        gen = load_json(ACADEMY_LESSONS_DIR / f"std{std}_u{uidx}.json", None)
        if not gen:
            continue
        lessons = []
        for li, les in enumerate(gen.get("lessons", [])):
            acts = les.get("activities", [])
            if acts:
                lessons.append({
                    "key": f"s{std}u{uidx}l{li}",
                    "name": les.get("name", f"பாடம் {li + 1}"),
                    "activities": acts,
                })
        if lessons:
            groups.append({
                "idx": f"s{std}u{uidx}",
                "title": f"{std}ஆம் வகுப்பு – {gen.get('unit_title') or _unit_title(std, uidx)}",
                "keywords": gen.get("keywords", []),
                "lessons": lessons,
            })
    notes_url = f"/learn/{exam}/{part}/{uid}" if uid in {x.stem for x in NOTES_DIR.glob("*.json")} else ""
    return jsonify({
        "exam": exam,
        "part": part,
        "unit": uid,
        "label": u.get("title", ""),
        "color": p.get("color", "#58cc02"),
        "scope": f"{exam}:{uid}",
        "topics": u.get("topics", []),
        "mapped": _mapped_entries(exam, uid),
        "notes_url": notes_url,
        "units": groups,
    })

# ---------------------------------------------------------------- Games (38 districts)
GAMES_MANIFEST = DATA_DIR / "games" / "districts.json"
GAMES_CONTENT = DATA_DIR / "games" / "content"


def _games_manifest():
    return load_json(GAMES_MANIFEST, {"divisions": [], "districts": []})


def _game_district(slug):
    return next((d for d in _games_manifest().get("districts", []) if d.get("slug") == slug), None)


@app.route("/games")
def games_index():
    m = _games_manifest()
    divs = {d["id"]: {**d, "districts": []} for d in m.get("divisions", [])}
    have = {p.stem for p in GAMES_CONTENT.glob("*.json")}
    for d in m.get("districts", []):
        bucket = divs.get(d.get("division"))
        if not bucket:
            continue
        bucket["districts"].append({
            "slug": d["slug"],
            "name_ta": d["name_ta"],
            "fame": d["fame"],
            "color": d.get("color", "#58cc02"),
            "art": f"/static/games/{d['slug']}.svg",
            "ready": d["slug"] in have,
        })
    return render_template(
        "games.html",
        divisions=[x for x in divs.values() if x["districts"]],
        total=len(m.get("districts", [])),
        ready=len(have),
    )


@app.route("/games/<slug>")
def game_page(slug):
    d = _game_district(slug)
    if not d:
        abort(404)
    div = next((x for x in _games_manifest().get("divisions", []) if x["id"] == d.get("division")), {"name": ""})
    return render_template(
        "game.html",
        d=d,
        division=div.get("name", ""),
        art=f"/static/games/{d['slug']}.svg",
        api=f"/api/games/{d['slug']}",
    )


@app.route("/api/games/<slug>")
def api_game(slug):
    if not _game_district(slug):
        return jsonify({"error": "not found"}), 404
    content = load_json(GAMES_CONTENT / f"{slug}.json", None)
    if not content:
        return jsonify({"error": "content not generated yet"}), 404
    return jsonify(content)

# ---------------------------------------------------------------- API

@app.route("/api/kural/random")
def kural_random():
    """Verified random kural from local dataset – no AI involved."""
    import random
    if not KURALS:
        return jsonify({"error": "திருக்குறள் தரவு இல்லை."}), 500
    n = random.choice(sorted(KURALS))
    return jsonify(kural_info(n))


@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(force=True) or {}
        user_msg = (data.get("message") or "").strip()
        history = data.get("history") or []

        if not user_msg:
            return jsonify({"error": "வெற்று செய்தி அனுப்ப வேண்டாம்."}), 400

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for m in history[-10:]:
            if isinstance(m, dict) and m.get("role") in ("user", "assistant") and m.get("content"):
                messages.append({"role": m["role"], "content": str(m["content"])[:2000]})

        # Tirukkural questions: attach VERIFIED reference so the model quotes real text
        kural_infos = []
        if any(w in user_msg for w in ("குறள்", "குறள்கள்", "திருக்குறள்", "வள்ளுவர்", "Thirukkural", "thirukkural", "kural")):
            kural_infos = find_kurals(user_msg)
        if kural_infos:
            messages.append({"role": "system", "content": kural_context_block(kural_infos)})
        elif any(w in user_msg for w in ("குறள்", "திருக்குறள்", "வள்ளுவர்")):
            messages.append({"role": "system",
                             "content": "குறிப்பிட்ட குறள்/அதிகாரம் சரிபார்க்கப்பட்ட தரவில் இல்லை. கற்பனையான குறள் எண் அல்லது வரிகள் சொல்லாதே; கருத்தை மட்டும் விளக்கு."})
        messages.append({"role": "user", "content": user_msg})

        try:
            resp = requests.post(
                SARVAM_URL,
                headers={
                    "api-subscription-key": SARVAM_API_KEY,
                    "Content-Type": "application/json",
                },
                json={
                    "model": MODEL,
                    "messages": messages,
                    "temperature": 0.6,
                    "max_tokens": 1024,
                    "reasoning_effort": None,
                },
                timeout=60,
            )
        except requests.exceptions.ConnectionError as e:
            print("Sarvam connection error:", e)
            return jsonify({"error": "இணைய இணைப்பு பிழை. Internet இணைப்பை சரிபார்த்து மீண்டும் முயற்சிக்கவும்."}), 503
        except requests.exceptions.Timeout:
            return jsonify({"error": "நேரம் முடிந்தது. மீண்டும் முயற்சிக்கவும்."}), 504

        if resp.status_code != 200:
            print("Sarvam error:", resp.status_code, resp.text[:1000])
            return jsonify({"error": f"Sarvam API பிழை ({resp.status_code}). மீண்டும் முயற்சிக்கவும்."}), 500

        try:
            out = resp.json()
        except Exception:
            print("Sarvam bad JSON:", resp.text[:1000])
            return jsonify({"error": "Sarvam-லிருந்து தவறான பதில். மீண்டும் முயற்சிக்கவும்."}), 500

        choices = out.get("choices") or []
        if not choices:
            print("Sarvam empty choices:", str(out)[:1000])
            return jsonify({"error": "Sarvam-லிருந்து பதில் இல்லை. மீண்டும் முயற்சிக்கவும்."}), 500

        msg = choices[0].get("message") or {}
        finish = choices[0].get("finish_reason")
        reply = msg.get("content") or msg.get("reasoning_content") or ""
        reply = reply.strip() if isinstance(reply, str) else ""

        if not reply:
            print(f"Sarvam empty content (finish={finish}):", str(out)[:1500])
            if finish == "length":
                return jsonify({"error": "பதில் மிக நீளமாக இருந்ததால் தடைப்பட்டது. கேள்வியை சுருக்கமாக கேளுங்கள்."}), 500
            if finish == "content_filter":
                return jsonify({"error": "இந்த கேள்விக்கு பதில் சொல்ல முடியவில்லை. வேறு கேள்வி கேளுங்கள்."}), 500
            return jsonify({"error": "Sarvam-லிருந்து வெற்று பதில் வந்தது. மீண்டும் முயற்சிக்கவும்."}), 500

        return jsonify({"reply": reply})

    except requests.exceptions.Timeout:
        return jsonify({"error": "நேரம் முடிந்தது. மீண்டும் முயற்சிக்கவும்."}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "இணைய இணைப்பு பிழை. Internet இணைப்பை சரிபார்த்து மீண்டும் முயற்சிக்கவும்."}), 503
    except Exception as e:
        print("Server error:", e)
        traceback.print_exc()
        return jsonify({"error": "சர்வர் பிழை. மீண்டும் முயற்சிக்கவும்."}), 500


def get_papers():
    data = load_json(PAPERS_JSON, {"papers": []})
    papers = data.get("papers", [])
    out = []
    for p in papers:
        if (PAPERS_DIR / p.get("file", "")).is_file():
            out.append(p)
    return sorted(out, key=lambda x: (-(x.get("year") or 0), x.get("title", "")))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
