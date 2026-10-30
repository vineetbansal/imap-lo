#!/usr/bin/env bash
#
# Restrict the input_* directories to a window of DATA dates (the YYYYMMDD in
# each filename), so the whole pipeline runs on that window only.
#
#   ./selectDateRange.sh            apply the window, then run ./update.sh -1
#   ./selectDateRange.sh --restore  put everything back
#
# Two mechanisms, because the pipeline has two kinds of steps:
#
#   * The ~25 driver.sh steps select work with `find ... -mtime "$delaytime"`.
#     In-range files are stamped with the current time so `./update.sh -1`
#     picks them up; out-of-range files would need excluding by mtime, but
#     -mtime cannot express a range, hence the second mechanism.
#
#   * 1S14/1S16 l1b_to_spin.py, 3S2 hist_auto_ram_V2.py and the l1b_to_spin.py
#     inside the 3S2/3S3 quickmap batches just glob the input dir and ignore
#     mtimes entirely.  Only physically moving files out constrains those.
#
# Out-of-range files are moved to input_*/outside_range/.  Both `find -maxdepth 1`
# and Python's Path.glob("*.cdf") are non-recursive, so that subdirectory is
# invisible to every step -- the same trick move_crap.sh uses with old/.
#
# This handles inputs only.  Stale per-date OUTPUTS from earlier runs are a
# separate problem (they get swept into the `cat ..._*.csv` aggregations in
# 1S04, 1S07, 1S11, 1S19, 3S2); use `./stageLoGtInputs.sh --clean` for those.

set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"

# Widened by a day at each end to cover repoint00128 (20260116) and repoint00312
# (20260717).  The SDC's l090-enansnbs 6 month map is built from both, and
# leaving them out cost ~2% of the map's exposure -- see README.md.
START=20260116
END=20260717
HOLD=outside_range

DIRS=(input_l1a_de input_l1b_histrates input_l1b_monitorrates input_de
      input_hk input_shk input_prostar input_l1c)


restore() {
    local d n
    for d in "${DIRS[@]}"; do
        [[ -d "$d/$HOLD" ]] || continue
        n=$(find "$d/$HOLD" -maxdepth 1 -type f -name '*.cdf' | wc -l)
        if (( n > 0 )); then
            find "$d/$HOLD" -maxdepth 1 -type f -name '*.cdf' -exec mv -t "$d" {} +
        fi
        rmdir "$d/$HOLD" 2>/dev/null || true
        printf '%-24s %4d restored\n' "$d" "$n"
    done
}

apply() {
    local d f dt inr out bad
    for d in "${DIRS[@]}"; do
        if [[ ! -d $d ]]; then
            printf 'SKIP  %-24s no such directory\n' "$d" >&2
            continue
        fi
        mkdir -p "$d/$HOLD"
        inr=0; out=0; bad=0
        while IFS= read -r f; do
            # Note: a grep-based extraction would abort the script under
            # `set -e` on any filename that does not match.
            if [[ $(basename "$f") =~ _([0-9]{8})-repoint ]]; then
                dt="${BASH_REMATCH[1]}"
            else
                dt=""
            fi
            if [[ -z $dt ]]; then
                # No parseable data date -- leave it alone rather than guess.
                printf 'WARN  unparsed filename, left in place: %s\n' "$f" >&2
                bad=$((bad+1))
            elif (( dt >= START && dt <= END )); then
                touch "$f"          # make it visible to -mtime -1
                inr=$((inr+1))
            else
                mv "$f" "$d/$HOLD/"
                out=$((out+1))
            fi
        done < <(find "$d" -maxdepth 1 -type f -name '*.cdf')
        rmdir "$d/$HOLD" 2>/dev/null || true
        printf '%-24s %4d kept, %4d held aside%s\n' \
            "$d" "$inr" "$out" "$( ((bad)) && printf ', %d unparsed' "$bad")"
    done
}


case "${1:-}" in
    --restore) restore ;;
    "")        echo "Window: $START .. $END"; apply ;;
    *)         echo "usage: $0 [--restore]" >&2; exit 2 ;;
esac
