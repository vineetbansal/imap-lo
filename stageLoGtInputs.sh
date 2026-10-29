#!/usr/bin/env bash
#
# Stage Lo products from the imap-data-access cache ($IMAP_DATA_DIR) into the
# flat input_* directories that update.sh's drivers read from, then de-duplicate
# so only the newest revision of each repoint survives.
#
# This script does NOT download anything -- populate $IMAP_DATA_DIR first
# (see fetchLoGtInputs.sh).  Run this, then ./update.sh <delaytime>.
#
# Usage: ./stageLoGtInputs.sh [--clean]
#
#   --clean   empty every output/ and outdir/ first, so the run starts from
#             scratch.  Without it, per-date files from previous runs survive
#             and get swept into the `cat ..._*.csv > ...` aggregations in
#             1S04, 1S07, 1S11, 1S19 and 3S2, making merged results cover
#             dates this run never touched.

set -euo pipefail

# Work relative to this script, so it can be invoked from anywhere.
cd "$(dirname "$(readlink -f "$0")")"

CLEAN=0
case "${1:-}" in
    --clean) CLEAN=1 ;;
    "")      ;;
    *)       echo "usage: $0 [--clean]" >&2; exit 2 ;;
esac

# Empty (but keep) every output/ and outdir/.  The drivers assume the directory
# exists -- 1S04's driver ends with `cd $output` -- so only the contents go.
#
# archive/ and baselines/ are excluded: baselines/3S4_correction_v5/outdir is a
# saved reference for compare_correction_outputs.py, not run output.
clean_outputs() {
    local d n total=0 dirs=0
    while IFS= read -r d; do
        # Guard against ever expanding to something unintended.
        [[ -n $d && -d $d ]] || continue
        case "$(basename "$d")" in output|outdir) ;; *) continue ;; esac
        n=$(find "$d" -mindepth 1 -type f | wc -l)
        (( n == 0 )) && continue
        find "$d" -mindepth 1 -delete
        total=$((total+n)); dirs=$((dirs+1))
        printf '  emptied %-46s %7d files\n' "$d" "$n"
    done < <(find . -maxdepth 2 \( -name output -o -name outdir \) -type d \
                 -not -path './archive/*' -not -path './baselines/*' | sort)
    printf 'Cleaned %d directories, %d files total\n\n' "$dirs" "$total"
}

if (( CLEAN )); then
    echo "Emptying output/ and outdir/ (recover with ./sync if needed):"
    clean_outputs
fi

: "${IMAP_DATA_DIR:?IMAP_DATA_DIR is not set}"
D="$IMAP_DATA_DIR/imap/lo"
[[ -d "$D" ]] || { echo "No such directory: $D" >&2; exit 1; }

missing=()

# stage <level> <filename-pattern> <destination>
#
# The cache is laid out as <level>/<YYYY>/<MM>/*.cdf; the input_* dirs are flat,
# hence the -mindepth/-maxdepth 3.
#
# cp deliberately does NOT preserve mtimes: the drivers select work with
# `find ... -mtime "$delaytime"`, so freshly staged files must look new.
stage() {
    local level="$1" pattern="$2" dest="$3"
    local src="$D/$level" n

    if [[ ! -d "$dest" ]]; then
        printf 'SKIP  %-24s no such directory\n' "$dest" >&2
        return
    fi

    # Check the level dir explicitly: `find` on a missing directory exits 1,
    # which pipefail carries through `| wc -l` and set -e turns into a silent
    # abort of the whole script.
    if [[ ! -d "$src" ]]; then
        printf 'SKIP  %-24s no %s/ in the cache\n' "$dest" "$level" >&2
        missing+=("$dest ($level $pattern)")
        return
    fi

    n=$(find "$src" -mindepth 3 -maxdepth 3 -type f -name "$pattern" | wc -l)
    if (( n == 0 )); then
        printf 'SKIP  %-24s nothing matching %s under %s\n' "$dest" "$pattern" "$src" >&2
        missing+=("$dest ($level $pattern)")
        return
    fi

    find "$src" -mindepth 3 -maxdepth 3 -type f -name "$pattern" \
        -exec cp -t "$dest" {} +

    # Keep the highest version per repoint; supersedes go to $dest/old/.
    # Not every input dir has one (input_l1c doesn't), so skip when absent
    # rather than letting set -e abort the whole run.
    if [[ -f "$dest/move_crap.sh" ]]; then
        ( cd "$dest" && bash move_crap.sh )
    fi

    printf 'OK    %-24s %4d copied, %4d kept after dedup\n' \
        "$dest" "$n" "$(find "$dest" -maxdepth 1 -type f -name '*.cdf' | wc -l)"
}

stage l1a '*_de_*.cdf'           ./input_l1a_de
stage l1b '*_histrates_*.cdf'    ./input_l1b_histrates
stage l1b '*_monitorrates_*.cdf' ./input_l1b_monitorrates
stage l1b '*_de_*.cdf'           ./input_de
stage l1b '*_nhk_*.cdf'          ./input_hk
stage l1b '*_shk_*.cdf'          ./input_shk
stage l1b '*_prostar_*.cdf'      ./input_prostar
stage l1c '*_pset_*.cdf'         ./input_l1c

if (( ${#missing[@]} > 0 )); then
    echo
    echo "WARNING: these streams are absent from the cache and were left untouched;"
    echo "         update.sh will reprocess whatever stale files they still hold:"
    printf '  %s\n' "${missing[@]}"
    exit 1
fi
