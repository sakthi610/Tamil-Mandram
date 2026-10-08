import glob
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
files = sorted(
    glob.glob("data/academy/lessons/std*_u*.json"),
    key=lambda p: [int(x) for x in re.findall(r"\d+", p)],
)
for f in files:
    d = json.load(open(f, encoding="utf-8"))
    m = re.findall(r"std(\d+)_u(\d+)", f)
    names = " / ".join(l["name"] for l in d["lessons"])
    print(f"std{m[0][0]} u{m[0][1]} [{d['unit_title']}]: {names}")
