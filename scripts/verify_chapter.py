#!/usr/bin/env python3
"""Execute every runnable code chunk in a .qmd chapter and report failures.

This is the check each chapter must pass before it is considered finished. It
extracts chunks in document order, runs them in one persistent session per
language, and reports the first error with its chunk label.

    python scripts/verify_chapter.py part1/01-introduction-to-bioinformatics.qmd

Chunks carrying `#| eval: false` are reported as skipped rather than run.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile

CHUNK = re.compile(r"^```\{(\w+)\}\n(.*?)^```\s*$", re.M | re.S)


def parse(path: str):
    text = open(path).read()
    chunks = []
    for match in CHUNK.finditer(text):
        lang, body = match.group(1), match.group(2)
        options = dict(re.findall(r"^#\|\s*([\w.-]+):\s*(.+)$", body, re.M))
        code = "\n".join(l for l in body.splitlines() if not l.startswith("#|"))
        chunks.append({
            "lang": lang.lower(),
            "label": options.get("label", f"unlabelled@{text[:match.start()].count(chr(10)) + 1}"),
            "eval": options.get("eval", "true").strip().lower() not in {"false", "f", "no"},
            "code": code,
        })
    return chunks


def run_python(chunks, workdir):
    script = ["import matplotlib", "matplotlib.use('Agg')", "import sys"]
    for chunk in chunks:
        script.append(f"print('>>> CHUNK {chunk['label']}', file=sys.stderr)")
        script.append(chunk["code"])
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, dir=workdir) as fh:
        fh.write("\n".join(script))
        path = fh.name
    try:
        proc = subprocess.run([sys.executable, path], cwd=workdir,
                              capture_output=True, text=True, timeout=1800)
    finally:
        os.unlink(path)
    return proc


def run_r(chunks, workdir):
    script = []
    for chunk in chunks:
        script.append(f'message(">>> CHUNK {chunk["label"]}")')
        script.append(chunk["code"])
    with tempfile.NamedTemporaryFile("w", suffix=".R", delete=False, dir=workdir) as fh:
        fh.write("\n".join(script))
        path = fh.name
    try:
        proc = subprocess.run(["Rscript", "--vanilla", path], cwd=workdir,
                              capture_output=True, text=True, timeout=1800)
    finally:
        os.unlink(path)
    return proc


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    path = sys.argv[1]
    chunks = parse(path)
    workdir = os.path.dirname(os.path.abspath(path)) or "."

    runnable = [c for c in chunks if c["eval"]]
    skipped = [c for c in chunks if not c["eval"]]
    langs = sorted({c["lang"] for c in runnable})
    print(f"{path}: {len(chunks)} chunks, {len(runnable)} runnable, "
          f"{len(skipped)} marked eval:false, languages={langs or ['none']}")

    executable = {"python", "r"}
    if len(executable & set(langs)) > 1:
        print("FAIL: this file mixes executable {r} and {python} chunks, which the "
              "book's house style forbids (see STYLE.md section 4).")
        return 1

    status = 0
    for lang in langs:
        batch = [c for c in runnable if c["lang"] == lang]
        if lang == "python":
            proc = run_python(batch, workdir)
        elif lang == "r":
            proc = run_r(batch, workdir)
        else:
            print(f"  {lang}: {len(batch)} chunk(s) not executed by this checker "
                  f"(mark them eval:false or use a fenced block without braces)")
            status = 1
            continue
        if proc.returncode == 0:
            print(f"  {lang}: all {len(batch)} chunks ran")
        else:
            trace = proc.stderr.strip().splitlines()
            last_chunk = [l for l in trace if l.startswith(">>> CHUNK")]
            print(f"  {lang}: FAILED in chunk "
                  f"{last_chunk[-1].replace('>>> CHUNK ', '') if last_chunk else '?'}")
            print("  " + "\n  ".join(l for l in trace[-25:] if not l.startswith(">>> CHUNK")))
            status = 1
    for chunk in skipped:
        print(f"  skipped (eval:false): {chunk['label']}")
    return status


if __name__ == "__main__":
    sys.exit(main())
