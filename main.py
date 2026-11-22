#!/usr/bin/env python3
"""news-image-20261122 — entrypoint.

Copy-only stdlib: the grader runs `python3 main.py` in a sandbox
with no network and no third-party packages. This script never draws
anything itself — it copies the pre-rendered entry.png (produced by
draw.py with Pillow at build time) into the output directory, then
verifies the copy is byte-identical to the source and is a real
1024x1024 PNG.

--verify  re-renders with draw.py (needs Pillow, build time only)
          and checks the committed entry.png matches, proving the
          committed image is exactly what the code draws.
"""
import hashlib
import os
import shutil
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "entry.png"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify():
    import subprocess
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        shutil.copy(HERE / "draw.py", workdir / "draw.py")
        shutil.copy(HERE / "world.geo.json", workdir / "world.geo.json")
        proc = subprocess.run([sys.executable, "draw.py"], cwd=workdir,
                              capture_output=True, text=True)
        if proc.returncode != 0:
            print("draw.py failed:\n" + proc.stderr, file=sys.stderr)
            return 1
        rendered = _sha256(workdir / "entry.png")
        if rendered != _sha256(SOURCE):
            print("render differs from committed entry.png: %s vs %s"
                  % (rendered, _sha256(SOURCE)), file=sys.stderr)
            return 1
    print("verify: entry.png matches a fresh render (%s)" % rendered)
    return 0


def _run():
    if not SOURCE.is_file():
        print("missing source: %s" % SOURCE, file=sys.stderr)
        return 1
    if SOURCE.stat().st_size == 0:
        print("empty source: %s" % SOURCE, file=sys.stderr)
        return 1
    with open(SOURCE, "rb") as handle:
        header = handle.read(33)
    if header[:8] != PNG_MAGIC or header[12:16] != b"IHDR":
        print("source is not a PNG file: %s" % SOURCE, file=sys.stderr)
        return 1
    width, height = struct.unpack(">II", header[16:24])
    if (width, height) != (1024, 1024):
        print("source is %dx%d, expected 1024x1024" % (width, height),
              file=sys.stderr)
        return 1
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR")
                   or os.environ.get("OUTPUT_DIR") or "/output")
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "entry.png"
    shutil.copyfile(SOURCE, target)
    if _sha256(SOURCE) != _sha256(target):
        print("copy differs from source", file=sys.stderr)
        return 1
    print("wrote %s (%d bytes)" % (target, target.stat().st_size))
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        raise SystemExit(_verify())
    raise SystemExit(_run())
