#!/bin/bash
cd "$(dirname "$0")"

mkdir -p ../raw
csplit -skn 5 -f ../raw/output "$1" "/^From /" {99999} 2>/dev/null
for f in output*; do
	tail +2 "$f" | sed 's/^>\(>*From \)/\1/g' > "$f.eml"
	rm "$f"
done
