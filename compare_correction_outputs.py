#!/usr/bin/env python3
"""
Compare the CSV map outputs of two runs of the sputter/bootstrap correction step.

Intended use: snapshot the output of correction_v4.py, then run a refactored
correction_v<n>.py (n >= 5) and confirm it produces the same numbers.

    cd 3S7_l1b_sputterbootstrap_ram      # or 3S4_l1b_SputterBootstrap
    python3 correction_v4.py
    cp -a outdir outdir_v4_ref
    python3 correction_v5.py
    python3 ../compare_correction_outputs.py outdir_v4_ref outdir

Exit status is 0 only if every file matched.

Stdlib only -- no numpy, no pandas, no third-party imports.

Two output formats are produced by correction_v4.py and both are handled:

  * map_expo_esa{N}.csv   written with np.savetxt -> no header row,
                          '%.18e' formatting, NaN spelled 'nan'
  * everything else       written with pandas .to_csv(index=False) -> a header
                          row of column indices '0,1,...,59', repr()-style
                          formatting, NaN spelled as an empty field

Because the two writers format floats differently, a plain text diff is useless
here; values are parsed and compared numerically.
"""

import argparse
import fnmatch
import math
import sys
from pathlib import Path

INF = float("inf")


# --------------------------------------------------------------------------
# reading
# --------------------------------------------------------------------------


def parse_field(text):
    """Parse one CSV field into a float. Empty fields are NaN (pandas na_rep)."""
    text = text.strip().strip('"')
    if text == "" or text.lower() in ("nan", "na", "n/a", "none"):
        return float("nan")
    return float(text)


def is_index_header(fields):
    """True if `fields` is a pandas column-index header row: 0,1,2,...,n-1."""
    if len(fields) < 2:
        return False
    for position, field in enumerate(fields):
        if field.strip().strip('"') != str(position):
            return False
    return True


def read_grid(path):
    """
    Read a CSV map into a list of rows of floats.

    Returns (grid, dropped_header). Raises ValueError on unparseable content.
    """
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        lines = [line for line in handle.read().splitlines() if line.strip() != ""]

    if not lines:
        return [], False

    rows = [line.split(",") for line in lines]

    dropped_header = False
    if is_index_header(rows[0]) and len(rows) > 1:
        # pandas index header. A real data row of exactly 0,1,2,...,n-1 is not
        # something these maps can contain, so this is unambiguous in practice.
        rows = rows[1:]
        dropped_header = True
    else:
        try:
            [parse_field(field) for field in rows[0]]
        except ValueError:
            # Named header of some other kind.
            rows = rows[1:]
            dropped_header = True

    grid = []
    for row_number, row in enumerate(rows):
        try:
            grid.append([parse_field(field) for field in row])
        except ValueError as exc:
            offset = 2 if dropped_header else 1
            raise ValueError(
                f"line {row_number + offset}: {exc}"
            ) from None

    return grid, dropped_header


def find_csvs(root):
    """Map every *.csv under `root` to its path, keyed by path relative to root."""
    root = Path(root)
    found = {}
    for path in sorted(root.rglob("*.csv")):
        if path.is_file():
            found[path.relative_to(root).as_posix()] = path
    return found


# --------------------------------------------------------------------------
# comparing
# --------------------------------------------------------------------------


def values_equal(left, right, rtol, atol):
    """Return (equal, absolute_difference, relative_difference)."""
    left_nan = math.isnan(left)
    right_nan = math.isnan(right)
    if left_nan and right_nan:
        return True, 0.0, 0.0
    if left_nan or right_nan:
        return False, INF, INF
    if left == right:  # covers matching infinities and +0.0 vs -0.0
        return True, 0.0, 0.0
    if math.isinf(left) or math.isinf(right):
        return False, INF, INF

    absolute = abs(left - right)
    scale = max(abs(left), abs(right))
    relative = absolute / scale if scale > 0.0 else INF
    return (absolute <= atol or relative <= rtol), absolute, relative


class FileResult:
    def __init__(self, name):
        self.name = name
        self.error = None
        self.shape_ref = None
        self.shape_new = None
        self.header_mismatch = False
        self.mismatches = []  # (row, col, ref, new, absolute, relative)
        self.n_mismatch = 0
        self.n_values = 0
        self.max_abs = 0.0
        self.max_rel = 0.0

    @property
    def ok(self):
        return self.error is None and self.n_mismatch == 0


def compare_file(name, ref_path, new_path, rtol, atol, keep):
    result = FileResult(name)

    try:
        ref_grid, ref_header = read_grid(ref_path)
    except (ValueError, OSError) as exc:
        result.error = f"cannot read reference: {exc}"
        return result
    try:
        new_grid, new_header = read_grid(new_path)
    except (ValueError, OSError) as exc:
        result.error = f"cannot read new: {exc}"
        return result

    result.header_mismatch = ref_header != new_header
    result.shape_ref = (len(ref_grid), len(ref_grid[0]) if ref_grid else 0)
    result.shape_new = (len(new_grid), len(new_grid[0]) if new_grid else 0)

    if len(ref_grid) != len(new_grid):
        result.error = (
            f"row count differs: {len(ref_grid)} vs {len(new_grid)}"
        )
        return result

    for row_index, (ref_row, new_row) in enumerate(zip(ref_grid, new_grid)):
        if len(ref_row) != len(new_row):
            result.error = (
                f"row {row_index}: column count differs: "
                f"{len(ref_row)} vs {len(new_row)}"
            )
            return result

        for col_index, (ref_value, new_value) in enumerate(zip(ref_row, new_row)):
            result.n_values += 1
            equal, absolute, relative = values_equal(
                ref_value, new_value, rtol, atol
            )
            if absolute != INF:
                result.max_abs = max(result.max_abs, absolute)
            if relative != INF:
                result.max_rel = max(result.max_rel, relative)
            if not equal:
                result.n_mismatch += 1
                if len(result.mismatches) < keep:
                    result.mismatches.append(
                        (row_index, col_index, ref_value, new_value,
                         absolute, relative)
                    )

    return result


# --------------------------------------------------------------------------
# reporting
# --------------------------------------------------------------------------


def fmt(value):
    if math.isnan(value):
        return "nan"
    if math.isinf(value):
        return "inf" if value > 0 else "-inf"
    return repr(value)


def selected(name, only_patterns, ignore_patterns):
    base = name.rsplit("/", 1)[-1]
    if only_patterns:
        if not any(
            fnmatch.fnmatch(name, p) or fnmatch.fnmatch(base, p)
            for p in only_patterns
        ):
            return False
    for pattern in ignore_patterns:
        if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(base, pattern):
            return False
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Verify that a refactored correction_v<n>.py reproduces the "
            "output of correction_v4.py."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  %(prog)s outdir_v4_ref outdir\n"
            "  %(prog)s outdir_v4_ref outdir --rtol 1e-12\n"
            "  %(prog)s outdir_v4_ref outdir --ignore 'map_func_*'\n"
            "  %(prog)s outdir_v4_ref outdir --only 'map_flux_*_Hy_sput_cor.csv'\n"
        ),
    )
    parser.add_argument("ref_dir", help="reference tree (correction_v4.py output)")
    parser.add_argument("new_dir", help="tree to check (correction_v5+.py output)")
    parser.add_argument(
        "--rtol",
        type=float,
        default=0.0,
        help=(
            "relative tolerance (default 0.0 = exact). Use ~1e-12 if the "
            "refactor legitimately reorders floating point arithmetic."
        ),
    )
    parser.add_argument(
        "--atol",
        type=float,
        default=0.0,
        help="absolute tolerance (default 0.0 = exact)",
    )
    parser.add_argument(
        "--ignore",
        action="append",
        default=[],
        metavar="GLOB",
        help=(
            "skip files matching GLOB (repeatable). Note that "
            "'map_func_*_Hy_boot_cor.csv' in an existing outdir is stale output "
            "from a retired script and is not written by correction_v4.py."
        ),
    )
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        metavar="GLOB",
        help="restrict comparison to files matching GLOB (repeatable)",
    )
    parser.add_argument(
        "--max-report",
        type=int,
        default=5,
        metavar="N",
        help="show at most N differing values per file (default 5)",
    )
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="do not fail when a reference file has no counterpart",
    )
    parser.add_argument(
        "--allow-extra",
        action="store_true",
        help="do not fail on files present only in the new tree",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="list matching files too, not just failures",
    )
    args = parser.parse_args(argv)

    ref_root = Path(args.ref_dir)
    new_root = Path(args.new_dir)
    for root in (ref_root, new_root):
        if not root.is_dir():
            parser.error(f"not a directory: {root}")
    if ref_root.resolve() == new_root.resolve():
        parser.error("ref_dir and new_dir are the same directory")

    ref_files = find_csvs(ref_root)
    new_files = find_csvs(new_root)

    names = sorted(
        n
        for n in set(ref_files) | set(new_files)
        if selected(n, args.only, args.ignore)
    )
    common = [n for n in names if n in ref_files and n in new_files]
    only_ref = [n for n in names if n not in new_files]
    only_new = [n for n in names if n not in ref_files]

    print(f"reference : {ref_root}  ({len(ref_files)} csv)")
    print(f"new       : {new_root}  ({len(new_files)} csv)")
    print(f"tolerance : rtol={args.rtol:g} atol={args.atol:g}")
    print(f"comparing : {len(common)} file(s)")
    print()

    results = [
        compare_file(
            name,
            ref_files[name],
            new_files[name],
            args.rtol,
            args.atol,
            args.max_report,
        )
        for name in common
    ]

    failed = [r for r in results if not r.ok]
    passed = [r for r in results if r.ok]

    if args.verbose:
        for result in passed:
            rows, cols = result.shape_ref
            print(f"  OK   {result.name}  ({rows}x{cols})")
        if passed:
            print()

    for result in failed:
        print(f"  FAIL {result.name}")
        if result.error:
            print(f"         {result.error}")
        else:
            print(
                f"         {result.n_mismatch} of {result.n_values} values "
                f"differ  (max abs {result.max_abs:.6g}, "
                f"max rel {result.max_rel:.6g})"
            )
            for row, col, ref_value, new_value, absolute, relative in (
                result.mismatches
            ):
                print(
                    f"         [{row},{col}]  ref={fmt(ref_value)}  "
                    f"new={fmt(new_value)}  "
                    f"abs={absolute:.6g}  rel={relative:.6g}"
                )
            if result.n_mismatch > len(result.mismatches):
                remaining = result.n_mismatch - len(result.mismatches)
                print(f"         ... and {remaining} more")
        if result.header_mismatch:
            print(
                "         note: one file has a header row and the other "
                "does not (values were still compared)"
            )
        print()

    for name in only_ref:
        print(f"  MISSING  {name}  (in reference, absent from new)")
    for name in only_new:
        print(f"  EXTRA    {name}  (in new, absent from reference)")
    if only_ref or only_new:
        print()

    # Even when everything passes, surface the worst drift so a "pass" under a
    # loosened tolerance is not mistaken for bit-identical output.
    worst_abs = max((r.max_abs for r in results if r.error is None), default=0.0)
    worst_rel = max((r.max_rel for r in results if r.error is None), default=0.0)

    print("-" * 70)
    print(
        f"{len(passed)} passed, {len(failed)} failed, "
        f"{len(only_ref)} missing, {len(only_new)} extra"
    )
    print(f"largest difference anywhere: abs {worst_abs:.6g}, rel {worst_rel:.6g}")

    ok = not failed
    if only_ref and not args.allow_missing:
        ok = False
    if only_new and not args.allow_extra:
        ok = False

    if ok and worst_abs == 0.0 and worst_rel == 0.0:
        print("RESULT: IDENTICAL")
    elif ok:
        print("RESULT: EQUAL WITHIN TOLERANCE (not bit-identical)")
    else:
        print("RESULT: DIFFERENT")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
