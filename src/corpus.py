"""Download Gutenberg books once, strip the licence header/footer, split into stories,
and write paragraph-numbered files to data/processed/<story_id>.txt.

Per CLAUDE.md rule 8: one download per book, descriptive User-Agent, a delay between requests;
afterwards everything reads the local copy in data/raw/ (which is never edited).
"""
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
USER_AGENT = "course-project (yw5688@nyu.edu)"
URL = "https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.txt"

# raw file name per Gutenberg id
BOOKS = {
    1661: "adventures.txt",
    834: "memoirs.txt",
    108: "return.txt",
    2350: "his_last_bow.txt",
    69700: "case_book.txt",
    244: "study_in_scarlet.txt",
    2852: "hound.txt",
    204: "innocence_of_father_brown.txt",
}


def download(gid, delay=3.0):
    """Download a book once; return its local path."""
    path = RAW / BOOKS[gid]
    if not path.exists():
        req = urllib.request.Request(URL.format(gid=gid), headers={"User-Agent": USER_AGENT})
        path.write_bytes(urllib.request.urlopen(req, timeout=60).read())
        time.sleep(delay)
    return path


def read_body(path):
    """Text between the Gutenberg START and END markers, with \\n line endings."""
    raw = Path(path).read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    s = raw.find("*** START OF")
    s = raw.find("\n", s) + 1
    e = raw.find("*** END OF")
    return raw[s:e]


def book_title(path):
    m = re.search(r"^Title:\s*(.+)$", Path(path).read_text(encoding="utf-8-sig"), re.M)
    return m.group(1).strip() if m else None


def to_paragraphs(chunk):
    """Blank-line separated paragraphs, whitespace collapsed, empty ones dropped."""
    paras = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", chunk)]
    return [p for p in paras if p]


def write_story(story_id, paragraphs, overwrite=False):
    """Write data/processed/<story_id>.txt as '[0001] ...' lines. Refuses to overwrite by default,
    because annotations depend on the paragraph numbers (CLAUDE.md rule 2)."""
    out = PROCESSED / f"{story_id}.txt"
    if out.exists() and not overwrite:
        raise FileExistsError(f"{out} exists; paragraph numbers are frozen")
    with open(out, "w", encoding="utf-8") as f:
        for i, p in enumerate(paragraphs, start=1):
            f.write(f"[{i:04d}] {p}\n\n")
    return out


# ---------------------------------------------------------------------------
# Splitting. Story title lines are excluded; chapter/section lines inside a story are kept
# as paragraphs (they also take paragraph numbers, see the annotation guideline).

ROMAN_LINE = re.compile(r"^[IVXL]+\.?$")


def _trim(paragraphs):
    """Drop trailing 'THE END' and bare roman numerals (Case-Book puts 'VIII' before a heading)."""
    while paragraphs and (paragraphs[-1].upper() == "THE END" or ROMAN_LINE.match(paragraphs[-1])):
        paragraphs = paragraphs[:-1]
    return paragraphs


def toc_titles(body, anchor="Contents"):
    """Titles listed in an indented table of contents that follows a line equal to `anchor`."""
    lines = body.split("\n")
    start = next(i for i, l in enumerate(lines) if l.strip() == anchor) + 1
    titles = []
    for l in lines[start:]:
        if l.strip() and not l.startswith(" "):
            break
        if l.strip():
            titles.append(l.strip())
    return titles


def split_collection(body, heading_re, end_marker=None):
    """Split at column-0 lines matching heading_re (group 1 = title). Returns [(title, paragraphs)]."""
    if end_marker:
        body = body[:body.index(end_marker)]
    hits = list(re.finditer(heading_re, body, re.M))
    out = []
    for i, m in enumerate(hits):
        end = hits[i + 1].start() if i + 1 < len(hits) else len(body)
        out.append((m.group(1).strip(), _trim(to_paragraphs(body[m.end():end]))))
    return out


def split_novel(body, start_re):
    """A single-story book: from the first line matching start_re (kept) to the end."""
    m = re.search(start_re, body, re.M)
    return _trim(to_paragraphs(body[m.start():]))


def book_stories(gid):
    """[(title, paragraphs)] for one book, using its own heading format."""
    body = read_body(RAW / BOOKS[gid])
    if gid == 1661:  # same rule as notebooks/01_prepare_corpus.ipynb
        return [(t.title(), ps) for t, ps in
                split_collection(body, r"^[IVX]+\.\s+([A-Z][A-Z’'\- ]+?)\s*$")]
    if gid == 834:
        return split_collection(body, r"^[IVX]+\. (.+)$")
    if gid == 108:
        return split_collection(body, r"^(THE ADVENTURE OF .+)$")
    if gid == 2350:
        return split_collection(body, r"^(The Adventure of .+|The Disappearance of .+|His Last Bow: .+)$")
    if gid == 69700:
        return split_collection(body, r"^(THE ADVENTURE OF .+|THE PROBLEM OF THOR BRIDGE)$",
                                end_marker="Printed in Great Britain")
    if gid == 204:
        titles = toc_titles(body)
        return split_collection(body, r"^(" + "|".join(map(re.escape, titles)) + r")$")
    if gid == 244:  # after the title line, from "PART I."
        return [("A Study in Scarlet", split_novel(body, r"^PART I\.$"))]
    if gid == 2852:
        return [("The Hound of the Baskervilles", split_novel(body, r"^Chapter 1\.$"))]
    raise KeyError(gid)


def norm_title(t):
    """Normalise a title for matching candidate-list titles to book headings."""
    t = re.sub(r"\(father brown\)", "", t.lower())
    t = re.sub(r"[^a-z0-9]+", " ", t.replace("’", "'")).strip()
    t = re.sub(r"^(the adventure of )", "", t)
    return re.sub(r"^the ", "", t)
