import re
import sys
from pathlib import Path
from urllib.parse import unquote

import requests

sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://www.tntextbooks.in/p/%dth-books.html"
OUT = Path(r"C:\Users\ADMIN\Desktop\Tamil\source_pdfs\tamil_textbooks")
OUT.mkdir(parents=True, exist_ok=True)

STDS = [6, 7, 9, 11, 12]

s = requests.Session()
s.headers["User-Agent"] = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) Chrome/124 Safari/537.36")


def drive_ids(url):
    m = re.search(r"drive\.google\.com/file/d/([-\w]+)", url) or re.search(r"drive\.google\.com/open\?id=([-\w]+)", url)
    return m.group(1) if m else None


def parse_page(html):
    """Return list of (label, fmt, drive_id) for Tamil subject links (raw Blogger HTML)."""
    out = []
    sections = re.split(r"<h2>", html)
    for sec in sections:
        head_m = re.match(r"(.*?)</h2>", sec, re.S)
        if not head_m:
            continue
        head = re.sub(r"<[^>]+>", "", head_m.group(1)).strip()
        term_m = re.match(r"Term\s*([123])\s*-\s*Tamil Medium", head, re.I)
        alt_m = re.match(r"(\d+)(?:st|nd|rd|th)\s+Tamil Medium New Books\s*-\s*Term\s*([123])$", head, re.I)
        if term_m:
            term = term_m.group(1)
            # row with <td>Tamil</td> ... two drive links (PDF, EPUB)
            row = re.search(r"<tr>\s*<td>\s*Tamil\s*</td>(.*?)</tr>", sec, re.S | re.I)
            if row:
                ids = re.findall(r"drive\.google\.com/file/d/([-\w]+)", row.group(1)) or \
                      re.findall(r"drive\.google\.com/open\?id=([-\w]+)", row.group(1))
                if len(ids) >= 1:
                    out.append((f"std{term}", "pdf", ids[0]))
                if len(ids) >= 2:
                    out.append((f"std{term}", "epub", ids[1]))
        elif alt_m:
            term = alt_m.group(2)
            row = re.search(r"<tr>\s*<td>\s*தமிழ்\s*</td>(.*?)</tr>", sec, re.S)
            if row:
                ids = re.findall(r"drive\.google\.com/file/d/([-\w]+)", row.group(1)) or \
                      re.findall(r"drive\.google\.com/open\?id=([-\w]+)", row.group(1))
                if ids:
                    out.append((f"alt{term}", "alt", ids[0]))
    seen, res = set(), []
    for item in out:
        if item[2] not in seen:
            seen.add(item[2])
            res.append(item)
    return res


def download(fid, dest_hint, idx):
    def ok(content):
        return content[:4] == b"%PDF" or content[:2] == b"PK" or (content[:5] == b"<?xml" or b"epub" in content[:200].lower())
    urls = [
        f"https://drive.google.com/uc?export=download&id={fid}",
        f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t",
    ]
    for u in urls:
        try:
            r = s.get(u, timeout=120)
        except Exception as e:
            print("   err", e)
            continue
        if r.status_code == 200 and r.content[:4] == b"%PDF":
            ext = ".pdf"
            data = r.content
        elif r.status_code == 200 and r.content[:2] == b"PK" and len(r.content) > 50000:
            # epub or zip – sniff
            ext = ".epub" if b"epub-container.xml" in r.content[:20000] or b"mimetype" in r.content[:100] else ".zip"
            data = r.content
        else:
            continue
        # filename
        disp = r.headers.get("Content-Disposition", "")
        m = re.search(r'filename\*=UTF-8\'\'([^;]+)', disp) or re.search(r'filename="([^"]+)"', disp)
        name = unquote(m.group(1)) if m else ("%s_book%s" % (dest_hint, ext))
        if not name.lower().endswith((".pdf", ".epub", ".zip")):
            name += ext
        path = OUT / ("%02d_%s" % (idx, re.sub(r"[^\w.\-() ]", "_", name)))
        path.write_bytes(data)
        print("   OK ->", path.name, "(%d KB)" % (len(data) // 1024))
        return True
    # quota / fail: scrape warning page
    try:
        r = s.get(f"https://drive.google.com/uc?export=download&id={fid}", timeout=60)
        if "Quota exceeded" in r.text:
            print("   QUOTA EXCEEDED for", fid)
    except Exception:
        pass
    return False


idx = 60  # file numbering prefix
for std in STDS:
    print("=" * 60)
    print("std", std)
    try:
        r = s.get(BASE % std, timeout=60)
        r.raise_for_status()
    except Exception as e:
        print("  page fail:", e)
        continue
    links = parse_page(r.text)
    if not links:
        print("  no tamil links found")
        continue
    # priority: term1 epub -> term1 alt -> term1 pdf -> term2... -> term3...
    def prio(item):
        label, fmt, _ = item
        term = int(label[-1])
        rank = {"epub": 0, "alt": 1, "pdf": 2}.get(fmt, 3)
        return (term, rank)
    links.sort(key=prio)
    print("  candidate links:", [(l, f) for l, f, _ in links])
    got_term1 = False
    tried_terms = set()
    for label, fmt, fid in links:
        term = label[-1]
        if got_term1 and term != "1":
            continue  # after term1 success, still try other terms? keep simple: stop after term1
        if got_term1:
            break
        print("  trying", label, fmt, fid)
        if download(fid, "std%d_term%s" % (std, term), idx):
            idx += 1
            got_term1 = True
    if not got_term1:
        print("  FAILED std", std)
