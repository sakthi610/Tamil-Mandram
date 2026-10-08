import re
import sys
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")

IDS = [
    "1qpcfleoHROxIrZ8rastenjROAHcFSh0I",
    "1f1P6f7AB9-k12AnHix7M2z0Zy2dERSBV",
    "1gZL_2CXBM-40x6Lo2ctp6tBs-VOFOpyS",
    "1IqE9XzrctCmKUX-o4UjMFgiAZh8BKmup",
    "166I0ZnRqlMpbwlCg7JuOduRHuZfRrQBQ",
    "1CY9YKyWkqPyjZD2cMYnm9muKg4j9DKmm",
    "1hOWONobVmT-F5GCLiv4dRC41SY-CIs1P",
]

OUT = Path(r"C:\Users\ADMIN\Desktop\Tamil\source_pdfs\tamil_textbooks")
OUT.mkdir(parents=True, exist_ok=True)

s = requests.Session()
s.headers["User-Agent"] = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36")

for i, fid in enumerate(IDS, 1):
    existing = list(OUT.glob("%02d_*" % i))
    if existing:
        print(f"[{i}] skip (exists): {existing[0].name}")
        continue
    url = f"https://drive.google.com/uc?export=download&id={fid}"
    try:
        r = s.get(url, timeout=60)
        ctype = r.headers.get("Content-Type", "")
        disp = r.headers.get("Content-Disposition", "")
        data = None
        if r.status_code == 200 and "text/html" not in ctype:
            data = r.content
        else:
            # scrape direct-download links from warning page
            links = re.findall(r'href="((?:https://drive\.google\.com)?/uc\?[^"]+)"', r.text or "")
            links += re.findall(r'href="((?:https://drive\.usercontent\.google\.com)?/download\?[^"]+)"', r.text or "")
            for link in links:
                link = link.replace("&amp;", "&")
                if not link.startswith("http"):
                    link = "https://drive.google.com" + link
                r2 = s.get(link, timeout=120)
                if r2.status_code == 200 and "text/html" not in r2.headers.get("Content-Type", ""):
                    data = r2.content
                    disp = r2.headers.get("Content-Disposition", "") or disp
                    break
            if data is None:
                # try GET on usercontent endpoint directly
                r3 = s.get("https://drive.usercontent.google.com/download",
                           params={"id": fid, "export": "download", "confirm": "t"}, timeout=120)
                if r3.status_code == 200 and "text/html" not in r3.headers.get("Content-Type", ""):
                    data = r3.content
                    disp = r3.headers.get("Content-Disposition", "") or disp
            if data is None:
                print(f"[{i}] FAIL {fid}: no downloadable link found (page {r.status_code})")
                continue
        name = ""
        m = re.search(r'filename\*=UTF-8\'\'([^;]+)', disp) or re.search(r'filename="([^"]+)"', disp)
        if m:
            from urllib.parse import unquote
            name = unquote(m.group(1))
        if not name:
            head = data[:8]
            ext = ".pdf" if head.startswith(b"%PDF") else (".epub" if head[:2] == b"PK" else (".zip" if head[:2] == b"PK" else ".bin"))
            name = f"book_{i}{ext}"
        safe_name = re.sub(r"[^\w.\-() ]", "_", name)
        path = OUT / ("%02d_%s" % (i, safe_name))
        path.write_bytes(data)
        print(f"[{i}] OK {fid} -> {path.name} ({len(data)//1024} KB)")
    except Exception as e:
        print(f"[{i}] ERROR {fid}: {e}")
