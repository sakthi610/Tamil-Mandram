const fs = require("fs");
const { JSDOM } = require("jsdom");

const SRC = require("path").join(__dirname, "..", "templates", "academy_path.html");
const results = [];
function ck(name, cond, extra) {
  results.push([name, !!cond]);
  console.log((cond ? "PASS " : "FAIL ") + name + (extra ? "  " + extra : ""));
}

// ---- fixture: 1 unit, 2 lessons, 6 activities each (one of every type) ----
function lesson(key, name, ansIdx) {
  return {
    key, name,
    activities: [
      { type: "choice", q: "தேர்வு கேள்வி?", options: ["அ", "ஆ", "இ", "ஈ"], ans: ansIdx, ex: "விளக்கம்" },
      { type: "fill", q: "இடம் நிரப்பு ____", options: ["சொல்1", "சொல்2", "சொல்3"], ans: ansIdx % 3, ex: "" },
      { type: "match", q: "பொருத்துக", pairs: [["வே1", "வி1"], ["வே2", "வி2"], ["வே3", "வி3"]] },
      { type: "assemble", q: "வாக்கியம் அமை", words: ["முதல்", "இரண்டாம்", "மூன்றாம்"], answer: "முதல் இரண்டாம் மூன்றாம்" },
      { type: "listen", q: "கேட்டு அறி", options: ["செவி1", "செவி2", "செவி3"], ans: ansIdx % 3, speak: "செவி2", ex: "" },
      { type: "truefalse", q: "இது சரியா?", ans: true, ex: "ஆம்" },
    ],
  };
}
const fixture = {
  std: "8", label: "8ஆம் வகுப்பு தமிழ்", color: "#0f9d58",
  units: [{ idx: 1, title: "அலகு ஒன்று", keywords: ["சொல்"], lessons: [lesson("u1l1", "முதல் பாடம்", 2), lesson("u1l2", "இரண்டாம் பாடம்", 1)] }],
};

// ---- html prep: strip jinja ----
let html = fs.readFileSync(SRC, "utf8");
html = html.replace(/\{%[\s\S]*?%\}/g, "");
html = html.replace(/\{\{[\s\S]*?\}\}/g, (m) => {
  if (m.includes("scope")) return "tnpsc:ta1";
  if (m.includes("api_url")) return "/api/academy/tnpsc/tamil/ta1";
  if (m.includes("color")) return "#a41212";
  return "X";
});

const dom = new JSDOM(html, {
  runScripts: "dangerously",
  url: "http://127.0.0.1:5000/academy/tnpsc/tamil/ta1",
  beforeParse(window) {
    window.fetch = () => Promise.resolve({ json: () => Promise.resolve(fixture) });
  },
});
const { window } = dom;
const doc = window.document;
const $ = (s) => doc.querySelector(s);
const $$ = (s) => Array.from(doc.querySelectorAll(s));
const click = (el) => el.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
function store() { return JSON.parse(window.localStorage.getItem("academy_progress")); }

const TYPE_OF = { "தேர்வு": "choice", "இடம் நிரப்பு": "fill", "கேட்டு அறி": "listen", "சரியா? தவறா?": "truefalse", "பொருத்துக": "match", "வாக்கியம் அமை": "assemble" };

function answerCurrent(correct) {
  const type = TYPE_OF[$(".q-type").textContent.trim()];
  if (type === "choice" || type === "fill" || type === "listen") {
    // fixture: correct idx for lesson = l1:2, l2:1 (fill/listen use %3 → l1:2, l2:1)
    let idx = correct ? curAns : (curAns + 1) % $$("#pBody .opt").length;
    click($(`#pBody .opt[data-i="${idx}"]`));
  } else if (type === "truefalse") {
    // all ans = true → correct is data-i=1
    click($(`#pBody .opt[data-i="${correct ? 1 : 0}"]`));
  } else if (type === "match") {
    for (let i = 0; i < 3; i++) {
      click($(`#mLeft .mt[data-i="${i}"]`));
      click($(`#mRight .mt[data-i="${i}"]`));
    }
  } else if (type === "assemble") {
    const words = correct ? ["முதல்", "இரண்டாம்", "மூன்றாம்"] : ["மூன்றாம்", "இரண்டாம்", "முதல்"];
    for (const w of words) {
      const chip = $$("#bank .chip").find(c => c.textContent === w && c.style.visibility !== "hidden");
      click(chip);
    }
    // correct order == answer; reversed != answer
  }
}

let curAns = 2; // correct option index for current lesson's choice/fill/listen

async function playLesson(mode) {
  for (let i = 0; i < 6; i++) {
    await wait(15);
    if (!$(".q-type")) throw new Error("activity not rendered at i=" + i);
    const correct = !(mode === "firstWrong" && i === 0);
    answerCurrent(correct);
    if ($("#pBtn").disabled) throw new Error("CHECK still disabled at i=" + i);
    click($("#pBtn")); // check
    const good = $("#pFb").classList.contains("good");
    const bad = $("#pFb").classList.contains("bad");
    const foot = $("#pFoot");
    if (correct && (!good || !foot.classList.contains("correct"))) throw new Error("expected good feedback i=" + i);
    if (!correct && i === 0 && (!bad || !foot.classList.contains("wrong"))) throw new Error("expected wrong feedback");
    click($("#pBtn")); // continue
  }
}

(async () => {
  await wait(120); // boot fetch

  ck("path rendered", $$("#path .node").length === 2, String($$("#path .node").length));
  ck("node1 unlocked", $$("#path .node")[0].classList.contains("cur"));
  ck("node2 locked", $$("#path .node")[1].classList.contains("locked"));
  ck("unit banner", $("#path .unit-banner") && $("#path .unit-banner .ub-t").textContent.includes("அலகு"));

  // locked click → shake + toast, no player
  click($$("#path .node")[1]);
  await wait(10);
  ck("locked click blocked", $("#player").classList.contains("hidden") && $("#toast").classList.contains("show"));

  // start lesson 1 (all correct)
  curAns = 2;
  click($$("#path .node")[0]);
  await wait(20);
  ck("player open", !$("#player").classList.contains("hidden"));
  ck("6 segments", $$("#pSegs i").length === 6);
  ck("game bar XP 0", $("#gXp").textContent === "0");

  await playLesson("all");
  await wait(20);
  ck("done overlay", !$("#doneOv").classList.contains("hidden"));
  ck("xp 90", $("#gXp").textContent === "90", $("#gXp").textContent);
  ck("player hidden after done", $("#player").classList.contains("hidden"));
  ck("progress saved", (store().done["tnpsc:ta1"] || []).includes("u1l1"), JSON.stringify(store().done));
  ck("hearts 5", store().hearts === 5);
  ck("accuracy shown", $("#dAcc").textContent === "100%", $("#dAcc").textContent);

  // back to path → lesson 2 now unlocked
  click($("#dBack"));
  await wait(20);
  ck("node2 now cur", $$("#path .node")[1].classList.contains("cur"));
  ck("node1 done", $$("#path .node")[0].classList.contains("done"));

  // lesson 2: first answer wrong (heart loss), rest correct
  curAns = 1;
  click($$("#path .node")[1]);
  await wait(20);
  await playLesson("firstWrong");
  await wait(20);
  ck("lesson2 done", !$("#doneOv").classList.contains("hidden"));
  ck("hearts 4 after wrong", store().hearts === 4, String(store().hearts));
  ck("xp total 170", $("#gXp").textContent === "170", $("#gXp").textContent);
  ck("both lessons done", (store().done["tnpsc:ta1"] || []).length === 2);

  // quit mid-lesson path re-render + all-done note
  click($("#dBack"));
  await wait(20);
  ck("all done note", $("#path .all-done-note") !== null);
  ck("trophy", $("#path .trophy") !== null);

  // reopen a done lesson (redo, no bonus)
  click($$("#path .node")[0]);
  await wait(20);
  ck("redo opens", !$("#player").classList.contains("hidden"));
  click($("#pQuit"));
  await wait(20);
  ck("quit closes player", $("#player").classList.contains("hidden"));

  const fails = results.filter(r => !r[1]).map(r => r[0]);
  console.log("==== RESULT: " + (fails.length ? "FAILS=" + JSON.stringify(fails) : "ALL_PASS"));
  process.exit(fails.length ? 1 : 0);
})().catch(e => { console.error("ERROR:", e.message); process.exit(1); });
