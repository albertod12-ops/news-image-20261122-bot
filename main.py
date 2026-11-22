#!/usr/bin/env python3
"""Copy the finished 22 November 2026 front page to the grader's output dir.

The repository holds the finished picture as entry.png (1024x1024, under
1 MiB). This entrypoint does one thing: copy that file to
$MAKEFUN_OUTPUT_DIR/entry.png (default /output), byte for byte, with no
network access and no randomness.

A missing source, an empty source, a source that is not a PNG file, or a
copy that does not match the source byte for byte is a loud failure
(exit 1), never a partial entry.

Run it locally the same way the grader does, with an output directory
of your own:
    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

# v1 entry (2026-11-22): 36 stories, 7 regions, thirteen flat-vector
# pictures (3 heroes + 10 small cards), a numbers strip and a date check.
import hashlib
import os
import shutil
import struct
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parent / "entry.png"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
DRAW = Path(__file__).resolve().parent / "draw.py"


def verify_determinism():
    """Re-render entry.png twice via draw.py and compare hashes.

    The front page is deterministic: two runs of draw.py must produce
    byte-identical files, and both must match the committed entry.png.
    Any mismatch is a loud failure (exit 1).
    """
    import subprocess
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        rendered = []
        for run_no in (1, 2):
            workdir = Path(tmp) / f"run{run_no}"
            workdir.mkdir()
            shutil.copy(DRAW, workdir / "draw.py")
            shutil.copy(Path(__file__).resolve().parent / "world.geo.json",
                        workdir / "world.geo.json")
            proc = subprocess.run([sys.executable, "draw.py"],
                                  cwd=workdir, capture_output=True,
                                  text=True)
            if proc.returncode != 0:
                print(f"draw.py run {run_no} failed:\n{proc.stderr}",
                      file=sys.stderr)
                return 1
            rendered.append(file_sha256(workdir / "entry.png"))
        if rendered[0] != rendered[1]:
            print(f"non-deterministic render: {rendered[0]} vs "
                  f"{rendered[1]}", file=sys.stderr)
            return 1
        if rendered[0] != file_sha256(SOURCE):
            print(f"render differs from committed entry.png: {rendered[0]} "
                  f"vs {file_sha256(SOURCE)}", file=sys.stderr)
            return 1
    print(f"deterministic: {rendered[0]}")
    return 0


def file_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run():
    if not SOURCE.is_file():
        print(f"missing source: {SOURCE}", file=sys.stderr)
        return 1
    if SOURCE.stat().st_size == 0:
        print(f"empty source: {SOURCE}", file=sys.stderr)
        return 1
    with open(SOURCE, "rb") as handle:
        header = handle.read(33)
        if header[:8] != PNG_MAGIC:
            print(f"source is not a PNG file: {SOURCE}", file=sys.stderr)
            return 1
        if len(header) < 33 or header[12:16] != b"IHDR":
            print(f"source has no PNG IHDR chunk: {SOURCE}", file=sys.stderr)
            return 1
        width, height = struct.unpack(">II", header[16:24])
        if (width, height) != (1024, 1024):
            print(f"source is {width}x{height}, expected 1024x1024: "
                  f"{SOURCE}", file=sys.stderr)
            return 1
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output")
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "entry.png"
    shutil.copyfile(SOURCE, target)
    if file_sha256(SOURCE) != file_sha256(target):
        print("copy differs from source", file=sys.stderr)
        return 1
    print(f"wrote {target} ({target.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        raise SystemExit(verify_determinism())
    raise SystemExit(run())
