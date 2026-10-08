const fs = require("fs");
const { JSDOM } = require("jsdom");
const path = require("path");

const BASE = path.join(__dirname, "..");
const results = [];
function ck(name, cond, extra) {
  results.push([name, !!cond]);
  console.log((cond ? "PASS " : "FAIL ") + name + (extra ? "  " + extra : ""));
}
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const fixture = JSON.parse(fs.readFileSync(path.join(BASE, "data", "games", "content", "chennai.json"), "utf8"));

function strip(html, repl) {
  html = html.replace(/\{%[\s\S]*?%\}/g, "");
  html = html.replace(/\{\{[\s\S]*?\}\}/g, (m) => {
    for (const [k, v] of repl) if (m.includes(k)) return v;
    return "X";
  });
  return html;
}

function buildGameDom() {
  const src = fs.readFileSync(path.join(BASE, "templates", "game.html"), "utf8");
  const html = strip(src, [
    ["d|tojson", JSON.stringify({ slug: "chennai" })],
    ["api|tojson", '"/api/games/chennai"'],
    ["art|tojson", '"/static/games/chennai.svg"'],
    ["d.name_ta", "சென்னை"],
    ["d.color", "#d84315"],
    ["division", "வடக்கு மண்டலம் (தொண்டை)"],
    ["art", "/static/games/chennai.svg"],
  ]);
  return new JSDOM(html, {
    runScripts: "dangerously",
    resources: "usable",
    url: "http://127.0.0.1:5000/games/chennai",
    beforeParse(window) {
      window.fetch = () => Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(fixture) });
      window.HTMLMediaElement.prototype.play = () => Promise.resolve();
    },
  });
}

async function main() {
  const dom = buildGameDom();
  const { window } = dom;
  const doc = window.document;
  const $ = (s) => doc.querySelector(s);
  const $$ = (s) => Array.from(doc.querySelectorAll(s));
  const click = (el) => el.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
  const store = () => JSON.parse(window.localStorage.getItem("games_progress"));

  await wait(400); // external script + fetch boot

  ck("script loaded (scene rendered)", $("#sceneCard") && $("#sceneCard").style.display === "block");
  ck("scene 1 tag", $("#sceneTag").textContent === fixture.story[0].scene, $("#sceneTag").textContent);
  ck("xp starts 0", $("#xpVal").textContent === "0", $("#xpVal").textContent);

  // ---- story: walk3 scenes ----
  click($("#sceneNext"));
  ck("scene 2", $("#sceneTag").textContent === fixture.story[1].scene, $("#sceneTag").textContent);
  ck("prev enabled", !$("#scenePrev").disabled);
  click($("#scenePrev"));
  ck("back to scene 1", $("#sceneTag").textContent === fixture.story[0].scene);
  click($("#sceneNext"));
  click($("#sceneNext"));
  ck("last scene", $("#sceneTag").textContent === fixture.story[2].scene);
  click($("#sceneNext")); // finish → quiz
  ck("story done saved", store().d.chennai.story === 1);
  ck("story xp 20", store().xp === 20 && $("#xpVal").textContent === "20", String(store().xp));
  ck("quiz tab active", $("#tab-quiz").classList.contains("active"));
  ck("quiz q1 rendered", $("#quizBox .qtext") && $("#quizBox .qtext").textContent === fixture.quiz[0].q);

  // ---- quiz: all6 correct ----
  for (let i = 0; i < fixture.quiz.length; i++) {
    await wait(20);
    const opts = $$("#qOpts .opt");
    ck("quiz has 4 options q" + i, opts.length === 4, String(opts.length));
    click(opts[fixture.quiz[i].ans]);
    ck("quiz feedback shown q" + i, $("#qFb .ex") !== null);
    if (i < fixture.quiz.length - 1) {
      click($("#qGo"));
    } else {
      click($("#qGo"));
    }
  }
  await wait(30);
  ck("quiz result screen", $(".qresult") !== null);
  ck("quiz perfect score", $(".qresult h3").textContent.includes("6 / 6"), $(".qresult h3").textContent);
  ck("quiz done saved", store().d.chennai.quizDone === 1);
  ck("quiz best 6", store().d.chennai.best === 6, String(store().d.chennai.best));
  ck("xp 110 (20+90)", store().xp === 110 && $("#xpVal").textContent === "110", String(store().xp));

  // ---- puzzles ----
  click($("#qToPz"));
  await wait(30);
  ck("puzzle 1 riddle", $("#puzzleBox .qtext") !== null && $("#pzIn") !== null);

  // wrong attempts
  $("#pzIn").value = "தவறானவை";
  click($("#pzCheck"));
  ck("wrong feedback", $("#pzFb .wrong") !== null);
  ck("no xp on wrong", store().xp === 110);
  $("#pzIn").value = "தவறு";
  click($("#pzCheck"));
  ck("hint auto-shown after 2", $("#pzHint").style.display === "block");
  ck("wrong still no xp", store().xp === 110);

  // correct answer
  $("#pzIn").value = "  " + fixture.puzzles[0].answer + " ";
  click($("#pzCheck"));
  ck("riddle correct", $("#pzFb .ex:not(.wrong)") !== null);
  ck("riddle xp +15", store().xp === 125, String(store().xp));
  ck("puzzle 0 saved", (store().d.chennai.pz || []).includes(0));
  click($("#pzGo")); // → puzzle 2 (riddle)
  await wait(20);
  ck("puzzle 2 riddle", $("#pzIn") !== null && $$("#pzOpts .opt").length === 0);
  $("#pzIn").value = fixture.puzzles[1].answer;
  click($("#pzCheck"));
  ck("riddle2 correct xp", store().xp === 140, String(store().xp));
  ck("puzzle 1 saved", (store().d.chennai.pz || []).includes(1));
  click($("#pzGo")); // → puzzle 3
  await wait(20);
  const seqI = fixture.puzzles.findIndex((p) => p.type === "sequence");
  ck("puzzle 3 sequence", seqI !== -1 && $$("#pzOpts .opt").length === 4, String($$("#pzOpts .opt").length));
  click($$("#pzOpts .opt")[fixture.puzzles[seqI].ans]);
  ck("sequence correct xp", store().xp === 155, String(store().xp));
  click($("#pzGo")); // finish → banner
  await wait(20);
  ck("puzzles finished banner", $("#pzToPath") !== null);
  ck("puzzles all saved", (store().d.chennai.pz || []).length === 3, JSON.stringify(store().d.chennai.pz));
  ck("xp 155", store().xp === 155, String(store().xp));

  // ---- path: win via correct choices ----
  click($("#pzToPath"));
  await wait(30);
  ck("path tab active", $("#tab-path").classList.contains("active"));
  ck("path start node", $("#pathText").textContent === fixture.path.nodes[fixture.path.start].text,
     $("#pathText").textContent.slice(0, 40));

  let cur = fixture.path.start;
  let steps = 0;
  while (!fixture.path.nodes[cur].end && steps < 20) {
    const node = fixture.path.nodes[cur];
    const good = node.choices.find((c) => !c.wrong);
    ck("node has correct choice " + cur, !!good);
    const btns = $$("#pathChoices .path-choice");
    const gi = node.choices.indexOf(good);
    click(btns[gi]);
    cur = good.to;
    steps++;
  }
  ck("reached win", fixture.path.nodes[cur].end === "win", cur);
  ck("win overlay shown", $("#pathWin").classList.contains("show"));
  ck("win badge text", $("#winText").textContent.includes(fixture.path.nodes[cur].badge || "x"),
     $("#winText").textContent.slice(0, 60));
  ck("path done saved", store().d.chennai.path === 1);
  ck("xp 195 (155+40)", store().xp === 195 && $("#xpVal").textContent === "195", String(store().xp));

  // ---- path: wrong choice → lose overlay → retry ----
  click($("#pathAgain"));
  await wait(20);
  ck("restart hides overlay", !$("#pathWin").classList.contains("show"));
  const startNode = fixture.path.nodes[fixture.path.start];
  const bad = startNode.choices.findIndex((c) => c.wrong);
  ck("start has wrong choice", bad !== -1);
  const wbtns = $$("#pathChoices .path-choice");
  click(wbtns[bad]);
  ck("wrong choice styled", wbtns[bad].classList.contains("chosen-bad"));
  ck("wrong toast", $("#toast").classList.contains("show"));
  await wait(950); // 850ms delay to lose node
  ck("lose overlay shown", $("#pathLose").classList.contains("show"), cur);
  click($("#pathRetry"));
  await wait(20);
  ck("retry restarts", !$("#pathLose").classList.contains("show") &&
     $("#pathText").textContent === fixture.path.nodes[fixture.path.start].text);
  ck("no extra xp on replay", store().xp === 195, String(store().xp));

  // ---- grid page progress display ----
  const gsrc = fs.readFileSync(path.join(BASE, "templates", "games.html"), "utf8");
  const ghtml = strip(gsrc, [
    ["total", "38"],
    ["div.name", "வடக்கு மண்டலம் (தொண்டை)"],
    ["d.slug", "chennai"],
    ["d.art", "/static/games/chennai.svg"],
    ["d.name_ta", "சென்னை"],
    ["d.fame", "தலைநகர்"],
    ["d.color", "#d84315"],
    ["ready", "True"],
  ]);
  const gdom = new JSDOM(ghtml, {
    runScripts: "dangerously",
    url: "http://127.0.0.1:5000/games",
    beforeParse(window) {
      window.localStorage.setItem("games_progress",
        JSON.stringify({ xp: 195, d: { chennai: { story: 1, quizDone: 1, pz: [0, 1, 2], path: 1 } } }));
    },
  });
  await wait(60);
  const gdoc = gdom.window.document;
  ck("grid stat done", gdoc.getElementById("statDone").textContent === "1",
     gdoc.getElementById("statDone").textContent);
  ck("grid stat xp", gdoc.getElementById("statXp").textContent === "195",
     gdoc.getElementById("statXp").textContent);
  const card = gdoc.querySelector('.dcard[data-slug="chennai"]');
  ck("chennai card done class", card && card.classList.contains("done"));
  ck("card progress 4/4", gdoc.querySelector('[data-slug-p="chennai"]').textContent === "4/4",
     gdoc.querySelector('[data-slug-p="chennai"]').textContent);

  const fails = results.filter((r) => !r[1]).map((r) => r[0]);
  console.log("==== RESULT: " + (fails.length ? "FAILS=" + JSON.stringify(fails) : "ALL_PASS"));
  process.exit(fails.length ? 1 : 0);
}

main().catch((e) => { console.error("ERROR:", e); process.exit(1); });
