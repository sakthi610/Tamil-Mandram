import re
import sys

import requests

sys.stdout.reconfigure(encoding="utf-8")

FIDS = [
    "1qpcfleoHROxIrZ8rastenjROAHcFSh0I",
    "1f1P6f7AB9-k12AnHix7M2z0Zy2dERSBV",
    "1IqE9XzrctCmKUX-o4UjMFgiAZh8BKmup",
    "1CY9YKyWkqPyjZD2cMYnm9muKg4j9DKmm",
    "1hOWONobVmT-F5GCLiv4dRC41SY-CIs1P",
]

s = requests.Session()
s.headers["User-Agent"] = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) Chrome/124 Safari/537.36")

for fid in FIDS:
    r = s.get(f"https://drive.google.com/uc?export=download&id={fid}", timeout=60)
    t = r.text
    title = re.search(r"<title>(.*?)</title>", t, re.S)
    print("=" * 70)
    print(fid, "| status", r.status_code, "| len", len(t), "| title:", title.group(1).strip() if title else "?")
    # find iframe/preview links and doc ids
    for pat in [r'src="(https://[^"]+)"', r'docs.google.com[^"\s]+', r'"([a-zA-Z0-9_\-]{20,})"']:
        hits = list(dict.fromkeys(re.findall(pat, t)))[:6]
        for h in hits:
            print("  hit:", str(h)[:150])
    body = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))
    print("  body:", body[:400])
