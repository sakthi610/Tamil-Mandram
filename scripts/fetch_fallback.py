import re
import sys
from pathlib import Path
from urllib.parse import unquote

import requests

sys.stdout.reconfigure(encoding="utf-8")

OUT = Path(r"C:\Users\ADMIN\Desktop\Tamil\source_pdfs\tamil_textbooks")
OUT.mkdir(parents=True, exist_ok=True)

BLOCKED = {
    "1qpcfleoHROxIrZ8rastenjROAHcFSh0I", "1V4Hja2PcjsBOww41E4FkAx4DZAFxW3CV",
    "1f1P6f7AB9-k12AnHix7M2z0Zy2dERSBV", "15BCL_6nXLmo2EHLe9CqausqosLARAevS",
    "1Yt61t7stH2pigoZxBomChi8p8WfgemNX", "1IvIPrpxpgZn15jmn_Um1gWCMDX_VyVxm",
    "1RyGqFYSlZH9QszD-ci-VhHVPtWpRPnHs", "1eks90EpMJGvb_NfiR_olAl-Ecz1os1XM",
    "1IqE9XzrctCmKUX-o4UjMFgiAZh8BKmup", "1CY9YKyWkqPyjZD2cMYnm9muKg4j9DKmm",
    "1hOWONobVmT-F5GCLiv4dRC41SY-CIs1P",
}

s = requests.Session()
s.headers["User-Agent"] = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) Chrome/124 Safari/537.36")


def candidates(html):
    """All link URLs from rows whose first cell is Tamil/தமிழ், in document order.
    Direct (non-drive) links first at equal row priority... we return document order,
    caller tries direct-then-drive."""
    rows = re.findall(r"<tr>(.*?)</tr>", html, re.S)
    direct, drives = [], []
    for row in rows:
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
        if not cells:
            continue
        label = re.sub(r"<[^>]+>|\s", "", cells[0])
        if label not in ("Tamil", "தமிழ்"):
            continue
        urls = re.findall(r'href="([^"]+)"', row)
        for u in urls:
            u = u.replace("&amp;", "&")
            if "drive.google.com" in u:
                m = re.search(r"/file/d/([-\w]+)", u) or re.search(r"open\?id=([-\w]+)", u)
                if m and m.group(1) not in BLOCKED:
                    drives.append(m.group(1))
            elif u.startswith("http") and not any(x in u for x in ("blogger", "google.com/img")):
                if re.search(r"tamil|Tamil|%20Tamil", u, re.I) or "syllabuspdf" in u:
                    direct.append(u)
    return direct, drives


def download(url, std):
    try:
        if "drive.google.com" in url or "drive.usercontent" in url:
            if "file/d/" in url:
                fid = re.search(r"/file/d/([-\w]+)", url).group(1)
                url = f"https://drive.google.com/uc?export=download&id={fid}"
            elif "open?id=" in url:
                fid = re.search(r"open\?id=([-\w]+)", url).group(1)
                url = f"https://drive.google.com/uc?export=download&id={fid}"
            r = s.get(url, timeout=120)
            if "Quota exceeded" in (r.headers.get("Content-Type", "").startswith("text/html") and r.text or ""):
                print("   QUOTA", url[-60:])
                return False
        else:
            r = s.get(url, timeout=180, allow_redirects=True)
        if r.status_code != 200 or not r.content:
            print("   status", r.status_code, url[-70:])
            return False
        head = r.content[:4]
        if head == b"%PDF":
            ext = ".pdf"
        elif head[:2] == b"PK" and len(r.content) > 50000:
            ext = ".epub" if b"mimetype" in r.content[:100] else ".zip"
        else:
            print("   not a file:", r.content[:60], url[-70:])
            return False
        disp = r.headers.get("Content-Disposition", "")
        m = re.search(r'filename\*=UTF-8\'\'([^;]+)', disp) or re.search(r'filename="([^"]+)"', disp)
        if m:
            name = unquote(m.group(1))
        else:
            base = unquote(url.split("/")[-1].split("?")[0]) or f"std{std}_book"
            name = base
        if not name.lower().endswith((".pdf", ".epub", ".zip")):
            name += ext
        idx = {"6": 6, "7": 7, "9": 9, "11": 11, "12": 12}[str(std)]
        path = OUT / ("%02d_%s" % (idx, re.sub(r"[^\w.\-() ]", "_", name)))
        if path.exists() and path.stat().st_size > 100000:
            print("   exists:", path.name)
            return True
        path.write_bytes(r.content)
        print("   OK ->", path.name, "(%d KB)" % (len(r.content) // 1024))
        return True
    except Exception as e:
        print("   ERR", e)
        return False


for std in [6, 7, 9, 11, 12]:
    print("=" * 60)
    print("std", std)
    r = s.get("https://www.tntextbooks.in/p/%dth-books.html" % std, timeout=60)
    direct, drives = candidates(r.text)
    print("  direct:", direct)
    print("  drive:", drives)
    ok = False
    for u in direct:  # prefer non-Drive mirrors
        if download(u, std):
            ok = True
            break
    if not ok:
        for fid in drives:
            if download(f"https://drive.google.com/file/d/{fid}/view", std):
                ok = True
                break
    print("  =>", "SUCCESS" if ok else "FAILED")
