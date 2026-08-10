mkdir -p old

for base in $(ls *_v*.cdf | sed -E 's/_v[0-9]+(\s*\([0-9]+\))?\.cdf$//' | sort -u); do
    ls "${base}"_v*.cdf 2>/dev/null | sort -V | sed '$d' |
    while read f; do
        mv "$f" old/
    done
done
