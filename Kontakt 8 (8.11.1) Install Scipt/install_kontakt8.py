#!/usr/bin/env python3
"""
install_kontakt8.py — Manually replicate the Kontakt 8 Windows installer's
filesystem + registry footprint into a Wine prefix, using data reverse-engineered
from a real ProcMon capture + the installer's own MSI database.

WHAT THIS DOES:
  1. Reads kontakt8_file_manifest.csv (dest Windows path -> source relative path
     inside the extracted installer payload) and copies every file into place
     under your Wine prefix's drive_c.
  2. Imports kontakt8_registry.reg into that same prefix via `wine regedit`,
     writing the registry keys Native Access / Kontakt use to detect the install.

WHAT THIS DOES NOT DO:
  - Does not perform NI license/activation (Native Access still needs to run and
    authenticate separately — that's a server-side check, not a file/registry one).
  - Does not fabricate the actual plugin/engine binaries. It only copies files that
    already exist in your extracted installer payload folder.

USAGE:
  python3 install_kontakt8.py \
      --payload-root /path/to/extracted/installer \
      --wineprefix ~/.wine \
      [--manifest kontakt8_file_manifest.csv] \
      [--reg kontakt8_registry.reg] \
      [--dry-run]

  --payload-root should be the folder that directly contains "data/OFFLINE/...".
    (i.e. wherever you extracted "Kontakt 8 Setup PC.exe" to.)
  --wineprefix should be the WINEPREFIX root (the folder containing drive_c),
    NOT drive_c itself.
"""

import argparse
import csv
import os
import shutil
import subprocess
import sys
import unicodedata


def win_to_unix_relpath(win_path: str) -> str:
    """Convert 'C:\\Program Files\\Foo\\Bar.txt' -> 'Program Files/Foo/Bar.txt'"""
    assert win_path[1:3] == ":\\", f"Unexpected path format: {win_path!r}"
    rest = win_path[3:]  # strip 'C:\'
    return rest.replace("\\", "/")


def find_case_insensitive(root: str, rel_path: str) -> str | None:
    """
    Resolve rel_path (posix-style, '/'-separated) under root on a case-sensitive
    filesystem, tolerating case mismatches between the manifest and what's
    actually on disk. Returns the real path if found, else None.
    """
    parts = [p for p in rel_path.split("/") if p not in ("", ".")]
    cur = root
    for i, part in enumerate(parts):
        direct = os.path.join(cur, part)
        if os.path.exists(direct):
            cur = direct
            continue
        # case-insensitive fallback
        try:
            entries = os.listdir(cur)
        except (FileNotFoundError, NotADirectoryError):
            return None
        match = None
        target = part.lower()
        for e in entries:
            if e.lower() == target:
                match = e
                break
        if match is None:
            return None
        cur = os.path.join(cur, match)
    return cur


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--payload-root", required=True, help="Folder containing extracted installer payload (has data/OFFLINE/... inside)")
    ap.add_argument("--wineprefix", required=True, help="WINEPREFIX root (folder containing drive_c)")
    ap.add_argument("--manifest", default=os.path.join(os.path.dirname(__file__), "kontakt8_file_manifest.csv"))
    ap.add_argument("--reg", default=os.path.join(os.path.dirname(__file__), "kontakt8_registry.reg"))
    ap.add_argument("--dry-run", action="store_true", help="Print planned actions without copying/writing anything")
    ap.add_argument("--skip-registry", action="store_true", help="Skip the wine regedit import step")
    args = ap.parse_args()

    payload_root = os.path.abspath(args.payload_root)
    wineprefix = os.path.abspath(args.wineprefix)
    drive_c = os.path.join(wineprefix, "drive_c")

    if not os.path.isdir(payload_root):
        sys.exit(f"ERROR: --payload-root does not exist: {payload_root}")
    if not os.path.isdir(drive_c):
        sys.exit(f"ERROR: no drive_c found under --wineprefix ({drive_c}). "
                  f"Create/initialize the prefix first (e.g. `WINEPREFIX={wineprefix} wineboot`).")

    total = 0
    copied = 0
    skipped_exists = 0
    missing_source = []

    with open(args.manifest, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Manifest has {len(rows)} files to place.")

    for row in rows:
        total += 1
        dest_win = row["dest_path_windows"]
        src_rel = row["source_relative_path"]

        dest_rel_unix = win_to_unix_relpath(dest_win)
        dest_full = os.path.join(drive_c, dest_rel_unix)

        # src_rel looks like "./data/OFFLINE/HASH1/HASH2/Filename.ext"
        src_rel_clean = src_rel[2:] if src_rel.startswith("./") else src_rel
        src_full = find_case_insensitive(payload_root, src_rel_clean)

        if src_full is None or not os.path.isfile(src_full):
            missing_source.append((dest_win, src_rel))
            continue

        if args.dry_run:
            print(f"[dry-run] {src_full}  ->  {dest_full}")
            continue

        os.makedirs(os.path.dirname(dest_full), exist_ok=True)
        if os.path.exists(dest_full) and os.path.getsize(dest_full) == os.path.getsize(src_full):
            skipped_exists += 1
            continue

        shutil.copy2(src_full, dest_full)
        copied += 1
        if copied % 500 == 0:
            print(f"  ...{copied} files copied so far")

    print()
    print(f"Done. {copied} copied, {skipped_exists} already present/unchanged, "
          f"{len(missing_source)} missing from payload, {total} total.")

    if missing_source:
        print("\nWARNING: the following files were listed in the manifest but not found in "
              "--payload-root (check your extraction, or these may be optional/unshipped variants):")
        for dest_win, src_rel in missing_source[:25]:
            print(f"  {dest_win}  (expected source: {src_rel})")
        if len(missing_source) > 25:
            print(f"  ...and {len(missing_source) - 25} more")

    if args.skip_registry or args.dry_run:
        print("\nSkipping registry import (--skip-registry or --dry-run set).")
        return

    print(f"\nImporting registry keys via wine regedit into prefix {wineprefix} ...")
    env = os.environ.copy()
    env["WINEPREFIX"] = wineprefix
    try:
        subprocess.run(["wine", "regedit", "/S", os.path.abspath(args.reg)], env=env, check=True)
        print("Registry import complete.")
    except FileNotFoundError:
        print("ERROR: `wine` not found on PATH. Import the .reg file manually with:\n"
              f"  WINEPREFIX={wineprefix} wine regedit \"{os.path.abspath(args.reg)}\"")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: wine regedit exited with code {e.returncode}. "
              f"You can retry manually with the command above.")


if __name__ == "__main__":
    main()
