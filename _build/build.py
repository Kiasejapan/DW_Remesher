"""
build.py
Concatenates _build/src/*.txt in sorted order into DW_Remesher.py
and optionally stamps VERSION with the current timestamp.

Usage (from repo root or _build/):
    python build.py              # stamps VERSION and builds
    python build.py --no-stamp   # builds without changing VERSION
"""
from __future__ import print_function
import os
import sys
import re
import datetime
import glob

# Detect repo root: this file is in <repo>/_build/build.py
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
SRC_DIR = os.path.join(HERE, "src")
OUT_FILE = os.path.join(REPO, "DW_Remesher.py")

VERSION_RE = re.compile(r'^(VERSION\s*=\s*")([^"]+)(")', re.MULTILINE)


def stamp_version():
    """Rewrite the VERSION = "..." line in all _build/src/*.txt files
    to the current timestamp (YYYY.MM.DD.HHMM)."""
    now = datetime.datetime.now()
    new_ver = now.strftime("%Y.%m.%d.%H%M")
    updated = False
    for txt in sorted(glob.glob(os.path.join(SRC_DIR, "*.txt"))):
        with open(txt, "rb") as f:
            raw = f.read()
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError:
            content = raw.decode("utf-8", errors="replace")
        new_content, n = VERSION_RE.subn(
            r'\g<1>' + new_ver + r'\g<3>', content, count=1)
        if n > 0 and new_content != content:
            with open(txt, "wb") as f:
                f.write(new_content.encode("utf-8"))
            print("  stamped {} -> v{}".format(
                os.path.basename(txt), new_ver))
            updated = True
            break  # stop after the first file that contained VERSION
    if not updated:
        print("  [warn] no VERSION line found to stamp.")
    return new_ver


def build(stamp=True):
    if not os.path.isdir(SRC_DIR):
        print("[ERROR] source folder not found: {}".format(SRC_DIR))
        return 1

    ver = None
    if stamp:
        print("Stamping VERSION ...")
        ver = stamp_version()

    print("Concatenating source files from {} ...".format(SRC_DIR))
    txt_files = sorted(glob.glob(os.path.join(SRC_DIR, "*.txt")))
    if not txt_files:
        print("[ERROR] no .txt files in {}".format(SRC_DIR))
        return 1

    # Concatenate all files in sorted order
    buf = []
    for t in txt_files:
        with open(t, "rb") as f:
            data = f.read()
        try:
            buf.append(data.decode("utf-8"))
        except UnicodeDecodeError:
            buf.append(data.decode("utf-8", errors="replace"))
        print("  + {}".format(os.path.basename(t)))

    merged = "".join(buf)

    # Validate Python syntax before writing
    try:
        compile(merged, OUT_FILE, "exec")
    except SyntaxError as e:
        print("[ERROR] syntax error in concatenated source: {}".format(e))
        return 1

    # Write output
    with open(OUT_FILE, "wb") as f:
        f.write(merged.encode("utf-8"))

    size = os.path.getsize(OUT_FILE)
    print("Built: {} ({} bytes, {} source files)".format(
        os.path.basename(OUT_FILE), size, len(txt_files)))
    if ver:
        print("Version: {}".format(ver))
    return 0


if __name__ == "__main__":
    stamp = "--no-stamp" not in sys.argv
    sys.exit(build(stamp=stamp))
