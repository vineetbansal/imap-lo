"""Generate imap_lo_goodtimes_2.csv (good-time windows per day) from L1B goodtimes CDFs.

Replaces the copy of 1S04's auto-goodtimes output that ``update_goodtimes.sh``
distributes into the quickmap ``config_files/`` directories, so that the
quicklook filters its histograms on the same good-time windows the SDC's L2 map
was built from, and the two pipelines share one source of truth for good times.

Why
---
1S04 runs its own good-time state machine over the histograms and writes the CSV
the quicklook reads; the SDC runs the algorithm that ships in imap_processing
and writes the L1B ``goodtimes`` product its L2 map reads.  The two do not
agree.  On 2026-019 the CSV holds 4 windows totalling 41282 s where the L1B
product holds 7 totalling 18185 s, and over the 90 pointings of a 6 month
pivot-90 map the quicklook keeps 12% more exposure than the SDC's map did.  That
is a leading candidate for the residual intensity offset between the two
pipelines, and pointing both at the SDC's windows is what rules it in or out:
running this closes that 12% to about 2%, the rest of which is the two pointings
the SDC's map used from outside the quicklook's date window.

Sibling of ``generate_pointing_file.py``, which does the same for attitude.

Format
------
The file is the one ``l1b_to_spin.estimate_exposure_time`` reads: no header, 14
columns, one row per good-time window::

    YD,gd_start,gd_end,bin_start,bin_end,Instrument,E-Step1..7,Comment
    2026019,506515629,506517313,0,59,Lo,1,1,1,1,1,1,1,# from imap_lo_...cdf

Only ``YD``, ``gd_start`` and ``gd_end`` reach the map.  The consumer builds its
histogram mask from those three, and uses ``bin_start``/``bin_end`` and the seven
``E-Step`` flags only for an exposure estimate it returns and its caller
discards -- the exposure that reaches the map comes from the histogram CDF's own
``exposure_time_6deg``.  They are written to 1S04's constant values anyway
(0, 59 and seven 1s) so the file stays a drop-in for every other reader of it.

The comment is free text and carries the product each row came from.  It must
hold no comma: the consumer reads the file with a fixed list of 14 column names,
so a fifteenth field would shift the parse.

Days
----
Rows are keyed by the day-of-year of the *product's own date*, not of the window,
because that is the key the consumer looks up: ``l1b_to_spin.py`` takes the date
out of the histogram filename it is processing, and the histogram and goodtimes
products of one repointing carry the same date.  A repointing's windows can run
past midnight -- repoint00131 is dated 2026-01-19 and its last window ends on
2026-01-20 -- and those still belong to the day the repointing is named for.

Times
-----
``gd_start``/``gd_end`` are the product's ``gt_start_met``/``gt_end_met``
verbatim, which is the same MET the SDC's map compares its histogram epochs
against.  The quicklook used to compare them against ``(epoch - 2010-01-01)`` in
seconds, which runs 8.409 s behind MET -- 1S04 hand-corrected for this with a
``+9`` in ``met_from_epoch``, commented "we are using an older time kernel".

1S04 also widened every window by 2 s at each end, which this does not, so
expect totals to differ by a few seconds per window even where the two
algorithms agree on where a window falls.

The window bounds are floored and ceiled to whole seconds respectively, so
rounding only ever widens a window, never narrows one.

Usage
-----
Run this AFTER ``./update.sh``, not before.  ``update.sh`` calls
``update_goodtimes.sh``, which re-runs 1S04 and copies its CSV over the very
path this writes, so a file written first is silently replaced before 3S5 ever
reads it.  In the README's sequence this belongs between ``./update.sh -1`` and
``./update_3s5_3s8.sh``, unlike ``generate_pointing_file.py``, which nothing in
``update.sh`` overwrites and so can be run at the start::

    python scripts/generate_goodtimes_file.py \\
        --out 3S5_l1b_ram_maps/config_files/imap_lo_goodtimes_2.csv
    cp 3S5_l1b_ram_maps/config_files/imap_lo_goodtimes_2.csv \\
       3S6_l1b_oxy_ram_maps/config_files/imap_lo_goodtimes_2.csv

Reads the L1B goodtimes products out of the imap-data-access cache by default,
recursively, so it works against the cache's ``<level>/<YYYY>/<MM>/`` layout and
against a flat staged directory alike.  It does not filter by date or by pivot
angle: the consumer looks a day up by key and ignores the rest, so a file
covering every day in the cache costs nothing.
"""

import argparse
import datetime as dt
import math
import os
from pathlib import Path

import numpy as np
from spacepy import pycdf

# The columns the consumer reads for nothing that reaches the map, at the
# constant values 1S04 wrote them at: the whole spin and every ESA step.
BIN_START, BIN_END = 0, 59
INSTRUMENT = "Lo"
ESA_FLAGS = "1,1,1,1,1,1,1"


def parse_version(name: str) -> tuple[int, int]:
    """Return (major, revision) from ``..._vNNN[.NNNN].cdf``; (-1, -1) if absent."""
    tail = name.rsplit("_v", 1)
    if len(tail) != 2:
        return (-1, -1)
    parts = tail[1].removesuffix(".cdf").split(".")
    try:
        return (int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)
    except ValueError:
        return (-1, -1)


def parse_stem(name: str) -> tuple[str, str] | None:
    """Return the (date, repointing) a product is of, or None if it names neither.

    One file in the archive is dated but untagged --
    ``imap_lo_l1b_goodtimes_20260706_v001.0002.cdf``, alongside the
    repoint00301 product of the same day -- and a window that cannot be
    attributed to a repointing cannot be checked against the pointing the SDC's
    map accumulated, so it is reported and skipped rather than merged in.
    """
    fields = name.split("_")
    if len(fields) < 5:
        return None
    date, _, repointing = fields[4].partition("-repoint")
    if not repointing or len(date) != 8:
        return None
    return date, repointing


def products_by_repointing(
    root: Path,
) -> tuple[dict[tuple[str, str], Path], list[str]]:
    """Map (date, repointing) -> the best product for it, plus what was skipped.

    Highest version wins, as elsewhere: the cache holds every revision the SDC
    ever wrote, and the map was built from the newest of them.
    """
    candidates: dict[tuple[str, str], list[tuple[tuple[int, int], Path]]] = {}
    untagged: list[str] = []

    for path in sorted(root.rglob("imap_lo_l1b_goodtimes_*.cdf")):
        stem = parse_stem(path.name)
        if stem is None:
            untagged.append(path.name)
            continue
        candidates.setdefault(stem, []).append((parse_version(path.name), path))

    return {stem: max(v)[1] for stem, v in candidates.items()}, untagged


def read_windows(path: Path) -> tuple[np.ndarray, np.ndarray, float]:
    """Return the good-time window bounds [MET s] of one product, and its pivot.

    ``epoch`` is deliberately not read. It is absent from 31 of the 239 products
    in the archive, and where it is present it does not reliably pair with the
    window starts -- ``gt_start_met - epoch`` runs from 0 to 22 s across the
    archive -- so the MET arrays are the only bounds to go on.
    """
    with pycdf.CDF(str(path)) as cdf:
        start = np.atleast_1d(np.asarray(cdf["gt_start_met"][...], dtype=float))
        end = np.atleast_1d(np.asarray(cdf["gt_end_met"][...], dtype=float))
        pivot = float(np.atleast_1d(cdf["pivot"][...])[0])

    if start.size != end.size:
        raise ValueError(
            f"{path.name}: {start.size} window starts against {end.size} ends"
        )
    return start, end, pivot


def day_of_year(date: str) -> int:
    """A YYYYMMDD product date as the YYYYDDD the consumer keys its rows by."""
    return int(dt.datetime.strptime(date, "%Y%m%d").strftime("%Y%j"))


def histogram_days(directory: Path) -> set[int]:
    """The YYYYDDD of every histogram product staged for the pipeline to read.

    Used only to report the days the CSV would leave uncovered.
    ``estimate_exposure_time`` raises on a day it has no row for, and
    ``l1b_to_spin.py`` catches that per file and prints "Skipping" -- which is
    how 5 of the 90 pointings of a pivot-90 map went missing from the quicklook
    without the map that came out saying so.
    """
    days = set()
    for path in sorted(directory.glob("imap_lo_l1b_histrates_*.cdf")):
        stem = parse_stem(path.name)
        if stem is not None:
            days.add(day_of_year(stem[0]))
    return days


def rows(
    products: dict[tuple[str, str], Path]
) -> tuple[list[tuple[int, int, int, str]], float, list[tuple[int, str]]]:
    """Build the CSV rows, in the (day, window) order the file is written in.

    Returns the rows, the good time they hold in seconds, and the (day, product)
    of each pointing that contributed no window.
    """
    written: list[tuple[int, int, int, str]] = []
    empty: list[tuple[int, str]] = []
    total = 0.0

    for (date, repointing), path in sorted(products.items()):
        start, end, pivot = read_windows(path)
        day = day_of_year(date)
        contributed = 0
        for gt_start, gt_end in zip(start, end, strict=True):
            if not gt_end > gt_start:
                continue
            total += gt_end - gt_start
            contributed += 1
            written.append(
                (
                    day,
                    math.floor(gt_start),
                    math.ceil(gt_end),
                    f"# from {path.name} repoint{repointing} pivot={pivot:.3f}",
                )
            )
        if not contributed:
            empty.append((day, path.name))

    return sorted(written), total, empty


def main() -> None:
    """Write the quicklook's good-time CSV from the SDC's L1B goodtimes products."""
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    cache = os.environ.get("IMAP_DATA_DIR")
    ap.add_argument(
        "--goodtimes-dir",
        type=Path,
        default=Path(cache) / "imap/lo/l1b" if cache else None,
        help="Directory holding the L1B goodtimes CDFs, searched recursively "
        "(default: $IMAP_DATA_DIR/imap/lo/l1b)",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("3S5_l1b_ram_maps/config_files/imap_lo_goodtimes_2.csv"),
        help="CSV to write (default: 3S5's config_files copy)",
    )
    ap.add_argument(
        "--histrates-dir",
        type=Path,
        default=Path("input_l1b_histrates"),
        help="Staged histogram products, read only to report the days the CSV "
        "would leave uncovered (default: input_l1b_histrates)",
    )
    args = ap.parse_args()

    if args.goodtimes_dir is None:
        ap.error("--goodtimes-dir not given and IMAP_DATA_DIR is not set")
    if not args.goodtimes_dir.is_dir():
        raise SystemExit(f"no such directory: {args.goodtimes_dir}")

    products, untagged = products_by_repointing(args.goodtimes_dir)
    for name in untagged:
        print(f"skipped {name}: names no repointing, so it belongs to no pointing")
    if not products:
        raise SystemExit(f"no L1B goodtimes products under {args.goodtimes_dir}")

    written, total, empty = rows(products)
    if not written:
        raise SystemExit(
            f"every one of the {len(products)} products under {args.goodtimes_dir} "
            f"reports no good time"
        )
    days = sorted({day for day, _, _, _ in written})

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as fh:
        for day, start, end, comment in written:
            fh.write(
                f"{day},{start},{end},{BIN_START},{BIN_END},"
                f"{INSTRUMENT},{ESA_FLAGS},{comment}\n"
            )

    print(
        f"{args.out}: {len(written)} windows from {len(products) - len(empty)} "
        f"repointings over {len(days)} days [{days[0]}..{days[-1]}], "
        f"{total / 3600:.1f} hours of good time"
    )
    if empty:
        print(
            f"  {len(empty)} repointing(s) report no good time and are left out: "
            + ", ".join(str(day) for day, _ in empty)
        )

    if not args.histrates_dir.is_dir():
        print(f"  {args.histrates_dir} not present, coverage not checked")
        return

    # The days the pipeline will try to process and this file cannot answer for.
    # Both kinds get dropped by the consumer, but they mean different things: a
    # pointing with no good time is the algorithm's verdict, and one with no
    # product at all is a hole in the cache to go and fill.
    uncovered = histogram_days(args.histrates_dir) - set(days)
    blank = {day for day, _ in empty}
    if not uncovered:
        print("  every staged histogram day has at least one window")
        return
    if uncovered & blank:
        print(
            f"  {len(uncovered & blank)} staged histogram day(s) will be dropped, "
            f"their pointing having no good time: {sorted(uncovered & blank)}"
        )
    if uncovered - blank:
        print(
            f"  WARNING: {len(uncovered - blank)} staged histogram day(s) have no "
            f"goodtimes product at all and will be dropped: "
            f"{sorted(uncovered - blank)}"
        )


if __name__ == "__main__":
    main()
