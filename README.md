# 📚 TNPSC தயாரிப்பு மையம் – Tamil Learning App

Sarvam AI (sarvam-105b) மாதிரியால் இயங்கும் தமிழ் போட்டித் தேர்வுக்கான கற்றல் இணையதளம் —
**இரு தேர்வுகள்**: TNPSC குரூப் 2 & 2A (முதல்நிலை) மற்றும் TNPSC உதவி பொறியாளர் (AE – EEE).

## பிரிவுகள்

| பிரிவு | இணைப்பு | விவரம் |
|---|---|---|
| 📖 கற்றல் | `/learn` | தேர்வு தேர்வாக → `/learn/tnpsc`, `/learn/ae`: பாடத்திட்ட அலகுகள் + AI தமிழ் குறிப்புகள் |
| 🏫 பள்ளிப்பாடம் | `/academy` | தேர்வுப் பாடத்திட்டம் முதலில் → வகுப்பு 6–12 பாடநூல் அலகுகளுடன் இணைக்கப்பட்ட டூயோலிங்கோ பாணிப் பயிற்சி (69 பாடம்) |
| 🎭 விளையாட்டுகள் | `/games` | **38 மாவட்டங்கள்**: பொம்மலாட்டம் கதை, வினா, புதிர், கிளைப்பாதை சாகசம் |
| 🗂️ வினாத்தாள்கள் | `/papers` | இரு பிரிவுகள்: குரூப் 2 வினாத்தாள்கள் + AE-EEE (2018–2025) – பார்க்க மட்டும் |
| 🤖 AI சந்தேகம் | `/chat` | இரு தேர்வுகளின் பாடத்திட்டமும் அறிந்த தமிழ் சாட்போட் + சரிபார்க்கப்பட்ட திருக்குறள் |

## இயக்கும் முறை

```
cd C:\Users\ADMIN\Desktop\Tamil
pip install -r requirements.txt
python app.py
```

Browser: http://127.0.0.1:5000

## குறிப்புகள் மீண்டும் உருவாக்க (இரு பாடத்திட்டங்களும்)

```
python scripts/generate_notes.py
```

## பள்ளிப்பாடம் (Academy) தரவு மீண்டும் உருவாக்க

```
python scripts/extract_textbooks.py   # PDF → source_text/std6-12.txt (ஏற்கனவே உள்ளது)
python scripts/build_academy.py       # பாடத்தாவல் → data/academy/course.json + slices
python scripts/generate_course.py     # Sarvam AI → data/academy/lessons/*.json (48 அலகு, skip-if-exists)
```

- `data/academy/mapping.json` — தேர்வுப் பாடத்திட்ட அலகு → வகுப்பு 6–12 பாடநூல் அலகு கைமுறை வரைபடம் (TNPSC: 23 இணைப்பு, AE: இல்லை → AI குறிப்புகள் மட்டும்)
- பாடத்திட்ட அலகுகள் பாடநூல் இணைப்பு இல்லாவிட்டால்: தலைப்புகள் + AI குறிப்புகள் மட்டும்
- 6 வகை செயல்பாடுகள்/பாடம்: தேர்வு, இடம் நிரப்பு, பொருத்துக, வாக்கியம் அமை, கேட்டு அறி (SpeechSynthesis), சரியா? தவறா?
- முன்னேற்றம் browser `localStorage` (`academy_progress`, வரம்பு `{exam}:{unit}`): XP, 5 இதயங்கள், தொடர் நாள்

## விளையாட்டுகள் (Games) தரவு மீண்டும் உருவாக்க

```
python scripts/generate_district_content.py   # Sarvam AI → data/games/content/*.json (38, skip-if-exists)
python scripts/build_district_art.py          # → static/games/<slug>.svg (38 பொம்மலாட்டம் காட்சிகள்)
```

- `data/games/districts.json` — 38 மாவட்டம் (4 மண்டலம்: வடக்கு 10, மத்திய 9, மேற்கு 10, தெற்கு 9) + புகழ் + நினைவுச்சின்ன வகை + நிறம்
- ஒவ்வொரு மாவட்டக் கோப்பிலும்: 3 காட்சிக் கதை, 6 MCQ, 3 புதிர் (2 ஊகம் + 1 வரிசை), கிளைப்பாதைப் பயணம் (சரியான வழி → வெற்றி)
- உள்ளடக்கம் சரிபார்க்கப்படுகிறது (schema + graph reachability) — தோல்வியுற்றால் மீண்டும் முயற்சி (validate + retry, Tamil quote repair)
- முன்னேற்றம் `localStorage` (`games_progress`): XP (கதை 20, வினா 10/சரி + 30 சர்வசமம், புதிர் 15, பாதை வெற்றி 40)

## Routes

- `/`, `/learn`, `/learn/<track>`, `/learn/<track>/<part>/<unit>` (track: `tnpsc` | `ae`)
- `/academy` (2 தேர்வுகள்), `/academy/<exam>`, `/academy/<exam>/<part>/<unit>` (exam: `tnpsc` | `ae`)
- `/games` (38 மாவட்ட அட்டவணை), `/games/<slug>`
- `/papers`, `/papers/view/<filename>` (பார்க்க மட்டும் — பதிவேற்றம்/நீக்கம் இல்லை)
- `/chat`, `POST /api/chat`, `GET /api/kural/random`

## Files

- `app.py` — Flask routes, dual-track setup, academy, games, chat API, Tirukkural verification
- `data/syllabus.json` — குரூப் 2/2A பாடத்திட்டம் (குறியீடு 495, 12.12.2024)
- `data/syllabus_ae.json` — AE-EEE பாடத்திட்டம் (10 அலகுகள், பட்டப்படிப்புத்தரம்)
- `data/academy/` — course.json, mapping.json, slices/ (பாடத்தாவல்), lessons/ (48 செயல்பாடு கோப்புகள்)
- `data/games/` — districts.json + content/ (38 மாவட்ட விளையாட்டுகள்)
- `data/notes/*.json` — AI தமிழ் குறிப்புகள் (ஒவ்வொரு அலகிற்கும்)
- `data/papers.json` — வினாத்தாள் பட்டியல் (track: `tnpsc` | `ae`)
- `data/tirukkural.json`, `tirukkural_detail.json` — 1330 குறள் + 133 அதிகாரம் (சரிபார்க்கப்பட்ட தரவு)
- `source_pdfs/tamil_textbooks/`, `source_text/` — 7 வகுப்பு பாடநூல்கள் (PDF/EPUB) + எடுக்கப்பட்ட உரை
- `static/papers/` — PDF கோப்புகள் (குரூப் 2 × 2, AE-EEE × 7)
- `static/games/` — 38 SVG (பொம்மலாட்டம் மேடை + நினைவுச்சின்னம்)
- `static/js/games.js` — விளையாட்டு engine (கதை/வினா/புதிர்/கிளைப்பாதை)
- `templates/` — base, home, learn, track, unit, papers, view_paper, chat, academy, academy_exam, academy_path, games, game
- `.env` — SARVAM_API_KEY (பகிர வேண்டாம்!)

## API

- `POST /api/chat` — {message, history} → {reply} (தமிழ் மட்டும்)
- `GET /api/kural/random` — சரிபார்க்கப்பட்ட திருக்குறள் (AI இல்லை)
- `GET /api/academy/<exam>/<part>/<unit>` — {scope, topics, mapped, units: [{idx, title, lessons: [...]}]}
- `GET /api/games/<slug>` — {story, quiz, puzzles, path} (38 மாவட்டங்கள்)

## Tests

```
python scripts/e2e_test.py      # 63 HTTP tests (server must be running)
npm install jsdom               # one-time
node scripts/player_test.js     # Academy player UI tests (jsdom, 24 checks)
node scripts/game_test.js       # Games engines UI tests (jsdom, 69 checks)
```
