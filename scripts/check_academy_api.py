import json
import os
import sys
import urllib.request as u

sys.stdout.reconfigure(encoding="utf-8")

mapping = json.load(open("data/academy/mapping.json", encoding="utf-8"))
syll = {"tnpsc": json.load(open("data/syllabus.json", encoding="utf-8")),
        "ae": json.load(open("data/syllabus_ae.json", encoding="utf-8"))}

# 1. mapping integrity
errs = []
for exam, m in mapping.items():
    unit_ids = {x["id"] for p in syll[exam]["parts"] for x in p["units"]}
    for uid, entries in m.items():
        if uid not in unit_ids:
            errs.append(f"{exam}:{uid} not in syllabus")
        for e in entries:
            f = f"data/academy/lessons/std{e['std']}_u{e['unit']}.json"
            if not os.path.exists(f):
                errs.append(f"{exam}:{uid} -> missing {f}")
            elif "why" not in e:
                errs.append(f"{exam}:{uid} -> missing why")
print("mapping errors:", errs or "none")

# 2. every mapped syllabus unit has notes file
notes = {x[:-5] for x in os.listdir("data/notes")}
miss = [f"{e}:{uid}" for e, m in mapping.items() for uid in m if uid not in notes]
print("mapped units without notes:", miss or "none")

# 3. API for every mapped unit
tot_groups = tot_lessons = tot_acts = 0
need = {"choice", "fill", "match", "assemble", "listen", "truefalse"}
bad = []
for exam, m in mapping.items():
    for uid, entries in m.items():
        # find part id
        part = next(p["id"] for p in syll[exam]["parts"] for x in p["units"] if x["id"] == uid)
        d = json.load(u.urlopen(f"http://127.0.0.1:5000/api/academy/{exam}/{part}/{uid}"))
        groups = d["units"]
        keys = [l["key"] for g in groups for l in g["lessons"]]
        if len(keys) != len(set(keys)):
            bad.append(f"{exam}:{uid} duplicate keys")
        if len(groups) != len(entries):
            bad.append(f"{exam}:{uid} groups {len(groups)} != mapped {len(entries)}")
        for g in groups:
            for l in g["lessons"]:
                tot_lessons += 1
                types = {a["type"] for a in l["activities"]}
                if not types <= need or len(l["activities"]) < 5:
                    bad.append(f"{exam}:{uid}:{l['key']} types={types}")
                for a in l["activities"]:
                    tot_acts += 1
                    if a["type"] in ("choice", "fill", "listen") and not (0 <= a.get("ans", -1) < len(a.get("options", []))):
                        bad.append(f"{exam}:{uid}:{l['key']} bad ans")
                    if a["type"] == "match" and len(a.get("pairs", [])) < 3:
                        bad.append(f"{exam}:{uid}:{l['key']} bad pairs")
        tot_groups += len(groups)
        # unmapped api returns empty units
# 4. unmapped unit API → empty
d = json.load(u.urlopen("http://127.0.0.1:5000/api/academy/tnpsc/gs/gs1"))
if d["units"] != [] or not d["notes_url"]:
    bad.append("gs1 should be unmapped with notes_url")
d = json.load(u.urlopen("http://127.0.0.1:5000/api/academy/tnpsc/tamil/ta1"))
if not d["mapped"] or d["scope"] != "tnpsc:ta1" or not d["topics"]:
    bad.append("ta1 api fields wrong")

print(f"API check: {tot_groups} groups, {tot_lessons} lessons, {tot_acts} activities")
print("errors:", bad or "none")
print("RESULT:", "ALL_PASS" if not errs and not bad and not miss else "FAIL")
