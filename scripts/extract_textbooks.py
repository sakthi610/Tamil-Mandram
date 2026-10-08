import glob
import re
import sys
import zipfile
from pathlib import Path

import pymupdf

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(r"C:\Users\ADMIN\Desktop\Tamil")
OUT = BASE / "source_text"
OUT.mkdir(exist_ok=True)


def clean(t: str) -> str:
    t = t.replace("\ufffd", "")           # stray replacement chars
    t = t.replace("​", "").replace("\xa0", " ")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    # doubled pulli artifact: "ற்்" -> "ற்" (only when same letter doubled pulli)
    t = re.sub(r"([஀-௿])்்", r"\1்", t)
    return t.strip()


def extract_pdf(path: Path, std: str):
    doc = pymupdf.open(path)
    parts = []
    for i, page in enumerate(doc):
        parts.append(f"\n<<<PAGE {i + 1}>>>\n" + page.get_text())
    doc.close()
    text = clean("".join(parts))
    (OUT / f"std{std}.txt").write_text(text, encoding="utf-8")
    print(f"std{std} pdf: {len(text)} chars from {path.name}")


def extract_epub(path: Path, std: str):
    z = zipfile.ZipFile(path)
    names = sorted(n for n in z.namelist()
                   if re.match(r".*index_split_\d+\.html", n) or
                   (n.endswith((".xhtml", ".html")) and "nav" not in n and "title" not in n))
    parts = []
    for n in names:
        html = z.read(n).decode("utf-8", "ignore")
        txt = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S)
        txt = re.sub(r"<[^>]+>", "\n", txt)
        parts.append(f"\n<<<FILE {n}>>>\n" + txt)
    text = clean("".join(parts))
    (OUT / f"std{std}.txt").write_text(text, encoding="utf-8")
    print(f"std{std} epub: {len(text)} chars from {path.name} ({len(names)} files)")


BOOKS = [
    ("6", "pdf", r"06_*.pdf"),
    ("6", "epub", r"60_*.epub"),   # term2 – appended
    ("7", "pdf", r"07_*.pdf"),
    ("8", "pdf", r"03_*.pdf"),
    ("9", "pdf", r"09_*.pdf"),
    ("10", "epub", r"05_*.epub"),
    ("11", "pdf", r"11_*.pdf"),
    ("12", "pdf", r"12_*.pdf"),
]

for std, kind, pat in BOOKS:
    files = sorted(glob.glob(str(BASE / "source_pdfs" / "tamil_textbooks" / pat)))
    if not files:
        print(f"std{std}: MISSING ({pat})")
        continue
    p = Path(files[0])
    existing = OUT / f"std{std}.txt"
    if existing.exists() and kind == "epub" and existing.stat().st_size > 1000:
        # epub is primary for this std – already done
        print(f"std{std}: exists, skipping")
        continue
    if kind == "pdf":
        extract_pdf(p, std)
    else:
        extract_epub(p, std)
        # std6: also merge pdf term1 if std6 primary will be overwritten by epub later – handled below

# std6 has both term1 pdf + term2 epub: merge both into one file
f6p = sorted(glob.glob(str(BASE / "source_pdfs" / "tamil_textbooks" / "06_*.pdf")))
f6e = sorted(glob.glob(str(BASE / "source_pdfs" / "tamil_textbooks" / "60_*.epub")))
if f6p and f6e:
    doc = pymupdf.open(f6p[0])
    t1 = clean("".join(p.get_text() for p in doc))
    doc.close()
    z = zipfile.ZipFile(f6e[0])
    parts = []
    for n in sorted(z.namelist()):
        if n.endswith((".xhtml", ".html")) and "nav" not in n and "title" not in n:
            html = z.read(n).decode("utf-8", "ignore")
            txt = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S)
            parts.append(re.sub(r"<[^>]+>", "\n", txt))
    t2 = clean("".join(parts))
    (OUT / "std6.txt").write_text(
        f"<<<TERM 1>>>\n{t1}\n<<<TERM 2>>>\n{t2}", encoding="utf-8")
    print(f"std6 merged: term1 {len(t1)} + term2 {len(t2)} chars")

print("\n--- output files ---")
for f in sorted(OUT.glob("*.txt")):
    print(f.name, f.stat().st_size, "bytes")
