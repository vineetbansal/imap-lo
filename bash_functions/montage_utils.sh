#!/usr/bin/env bash

make_montage () {
  local tile="$1"        # e.g. 3x3
  local outfile="$2"     # output image
  shift 2

  local require_count=""
  if [[ "$1" == --require ]]; then
    require_count="$2"
    shift 2
  fi

  local files=()
  for f in "$@"; do
    [[ -f "$f" ]] && files+=("$f") || echo "Missing: $f"
  done

  if [[ -n "$require_count" ]]; then
    if (( ${#files[@]} != require_count )); then
      echo "Skipping $outfile (need $require_count, found ${#files[@]})"
      return 1
    fi
  else
    (( ${#files[@]} == 0 )) && { echo "No files for $outfile"; return 1; }
  fi

  montage "${files[@]}" -tile "$tile" -geometry +0+0 "$outfile"
  echo "Created $outfile"
}


make_montage_ordered () {
  local tile="$1"
  local outfile="$2"
  shift 2

  local files=()
  for f in "$@"; do
    if [[ -f "$f" ]]; then
      files+=("$f")
    else
      echo "Missing (kept position): $f"
      # optional: add placeholder instead
      # files+=("placeholder.png")
    fi
  done

  (( ${#files[@]} )) || { echo "No files for $outfile"; return 1; }

  montage "${files[@]}" -tile "$tile" -geometry +0+0 "$outfile"
  echo "Created $outfile"
}