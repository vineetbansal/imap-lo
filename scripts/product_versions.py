"""Report the imap_processing version that produced each file of a product.

Walks ``$IMAP_DATA_DIR/imap/<instrument>/<level>/<YYYY>/<MM>/`` for one
descriptor over a date range and prints the ``ground_software_version`` global
attribute of every CDF it finds, keyed by repointing.

The SDC reprocesses on its own schedule, so an archive spanning a few months is
usually *not* homogeneous in code version.  Diffing a quicklook stage against
the archive without checking this first attributes a code change to the wrong
cause -- e.g. the Lo goodtimes thresholds doubled on 2026-06-04, so products
built before then split intervals the current code leaves whole.

Products that carry no ``-repointNNNNN`` in the filename (daily housekeeping,
L2 maps) are keyed by date instead.

Usage
-----
    python scripts/product_versions.py -i lo -l l1b -d goodtimes \
        --start 20260301 --end 20260331
    python scripts/product_versions.py -i lo -l l1b -d histrates --latest
    python scripts/product_versions.py -i hi -l l1c -d 90sensor-pset --summary-only
"""

import argparse
import os
import re
from collections import Counter
from pathlib import Path

import cdflib

# imap_<instrument>_<level>_<descriptor>_<YYYYMMDD>[-repointNNNNN]_v<version>.cdf
FILENAME_RE = re.compile(
    r"^imap_(?P<instrument>[^_]+)_(?P<level>[^_]+)_(?P<descriptor>.+)"
    r"_(?P<date>\d{8})(?:-repoint(?P<repoint>\d+))?"
    r"_v(?P<version>[\d.]+)\.cdf$"
)


def data_root(data_dir: str | None) -> Path:
    """The ``imap/`` tree that holds the products.

    ``IMAP_DATA_DIR`` points at the *parent* of ``imap/``, matching the
    convention imap_data_access uses.  Accept either here, so passing the
    ``imap/`` directory itself does the expected thing rather than silently
    finding nothing.
    """
    given = data_dir or os.environ.get("IMAP_DATA_DIR", "")
    if not given.strip():
        raise SystemExit("IMAP_DATA_DIR is not set; pass --data-dir instead.")
    root = Path(given).expanduser()
    return root if root.name == "imap" else root / "imap"


def find_files(root: Path, instrument: str, level: str, descriptor: str,
               start: str, end: str) -> list[tuple[dict, Path]]:
    """Every matching CDF in the date range, as (parsed filename fields, path)."""
    search = root / instrument / level
    if not search.is_dir():
        raise SystemExit(f"No such directory: {search}")

    found = []
    for path in search.glob("*/*/*.cdf"):
        m = FILENAME_RE.match(path.name)
        if not m:
            continue
        f = m.groupdict()
        if f["descriptor"] != descriptor or not start <= f["date"] <= end:
            continue
        found.append((f, path))

    # Sort by repointing where there is one, else by date; then by file version
    # so that "last wins" in --latest means the highest version.
    return sorted(found, key=lambda fp: (fp[0]["repoint"] or "",
                                         fp[0]["date"],
                                         version_key(fp[0]["version"])))


def version_key(version: str) -> tuple[int, ...]:
    """Sort key for a dotted file version, so v001.0010 follows v001.0009."""
    return tuple(int(p) for p in version.split(".") if p.isdigit())


def read_attrs(path: Path) -> tuple[str, str]:
    """The ``ground_software_version`` and ``Generation_date`` of one CDF."""
    try:
        attrs = cdflib.CDF(path).globalattsget()
    except Exception as exc:  # a truncated or half-written file
        return f"<unreadable: {type(exc).__name__}>", ""
    return first(attrs.get("ground_software_version")), first(attrs.get("Generation_date"))


def first(value: object) -> str:
    """Global attributes come back as single-element lists; flatten them."""
    if isinstance(value, list):
        value = value[0] if value else None
    return "?" if value is None else str(value)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-i", "--instrument", required=True, help="e.g. lo, hi, hit, glows")
    ap.add_argument("-l", "--level", required=True, help="e.g. l1a, l1b, l1c, l2")
    ap.add_argument("-d", "--descriptor", required=True,
                    help="product descriptor, e.g. goodtimes, histrates, 90sensor-pset")
    ap.add_argument("--start", default="00000000", help="YYYYMMDD, inclusive")
    ap.add_argument("--end", default="99999999", help="YYYYMMDD, inclusive")
    ap.add_argument("--data-dir", default=None,
                    help="default: $IMAP_DATA_DIR")
    ap.add_argument("--latest", action="store_true",
                    help="only the highest file version of each repointing")
    ap.add_argument("--summary-only", action="store_true",
                    help="skip the per-repoint table, print only the version tally")
    args = ap.parse_args()

    root = data_root(args.data_dir)
    files = find_files(root, args.instrument, args.level, args.descriptor,
                       args.start, args.end)
    if not files:
        print(f"No imap_{args.instrument}_{args.level}_{args.descriptor} files "
              f"in {args.start}..{args.end} under {root}")
        return 1

    if args.latest:
        # find_files sorts ascending by version, so the last of each key wins.
        keep = {(f["repoint"], f["date"]): (f, p) for f, p in files}
        files = sorted(keep.values(),
                       key=lambda fp: (fp[0]["repoint"] or "", fp[0]["date"]))

    print(f"{root}/{args.instrument}/{args.level}  "
          f"descriptor={args.descriptor}  {args.start}..{args.end}")
    print(f"{len(files)} file(s)\n")

    if not args.summary_only:
        print(f"{'repoint':>8}  {'date':8}  {'file ver':10}  "
              f"{'generated':9}  imap_processing version")
        print("-" * 88)

    versions = Counter()
    per_repoint = {}
    for f, path in files:
        sw, generated = read_attrs(path)
        versions[sw] += 1
        key = f["repoint"] or f["date"]
        per_repoint.setdefault(key, set()).add(sw)
        if not args.summary_only:
            print(f"{f['repoint'] or '-':>8}  {f['date']}  {f['version']:10}  "
                  f"{generated:9}  {sw}")

    print(f"\nDistinct imap_processing versions: {len(versions)}")
    for sw, n in sorted(versions.items()):
        print(f"  {n:5d} file(s)  {sw}")

    mixed = {k: v for k, v in per_repoint.items() if len(v) > 1}
    if mixed:
        print(f"\n{len(mixed)} repointing(s) reprocessed across versions, e.g.:")
        for key, sws in sorted(mixed.items())[:5]:
            print(f"  {key}: {', '.join(sorted(sws))}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
