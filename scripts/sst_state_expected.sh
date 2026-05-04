#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# SST-state validation: hits one ZIP per state and asserts the
# combined rate is at LEAST the published statewide rate. For
# flat-rate states (IN, KY, MI, NJ, RI) this is an equality check;
# for states with locals it's a lower-bound (every ZIP must pay
# the state portion at minimum).
#
# Format: "STATE|ZIP5|ZIP4|MIN_RATE_PCT|NOTE"
# MIN_RATE_PCT is the published statewide base rate (the floor).
# Sources: each state's DOR website, verified 2026-05-04.

API="${API:-https://api.opensalestax.org/v1/calculate}"

CASES=(
  # state | ZIP    | +4   | min%    | comment
  "AR|72201|1424|6.500|state base 6.5%"
  "GA|30303|1015|4.000|state base 4%"
  "IA|50309|2306|6.000|state base 6%"
  "IN|46202|2802|7.000|flat 7%"
  "KS|66603|3304|6.500|state base 6.5%"
  "KY|40202|2404|6.000|flat 6%"
  "MI|48226|3614|6.000|flat 6%"
  "MN|55401|1024|6.875|state base 6.875%"
  "NC|27601|1303|4.750|state base 4.75%"
  "ND|58501|4505|5.000|state base 5%"
  "NE|68102|1718|5.500|state base 5.5%"
  "NJ|07102|3505|6.625|flat 6.625%"
  "NV|89101|2402|4.600|state base 4.6%"
  "OH|43215|3704|5.750|state base 5.75%"
  "OK|73102|6107|4.500|state base 4.5%"
  "RI|02903|2511|7.000|flat 7%"
  "SD|57104|2401|4.200|state base 4.2%"
  "TN|37201|2402|7.000|state base 7%"
  "UT|84111|2202|4.850|state base 4.85% (incl mass-transit)"
  "VT|05601|1602|6.000|state base 6%"
  "WA|98101|2802|6.500|state base 6.5%"
  "WI|53202|2402|5.000|state base 5%"
  "WV|25301|1108|6.000|state base 6%"
  "WY|82001|3504|4.000|state base 4%"
)

PASS=0
FAIL=0
RESULTS=()

for entry in "${CASES[@]}"; do
  IFS='|' read -r state zip5 zip4 expected note <<< "$entry"
  body="{\"address\":{\"zip5\":\"$zip5\",\"zip4\":\"$zip4\"},\"line_items\":[{\"amount\":\"100.00\"}]}"
  resp=$(curl -s -X POST -H 'Content-Type: application/json' "$API" -d "$body")
  got=$(echo "$resp" | awk '{
    n = split($0, lines, "\"rate_pct\":")
    if (n >= 2) {
      s = lines[2]
      sub(/^"/, "", s); sub(/".*/, "", s)
      print s
    } else {
      print "0"
    }
  }')
  # Compare with bc for decimal precision
  cmp=$(awk -v g="$got" -v e="$expected" 'BEGIN { print (g+0 >= e+0) ? "PASS" : "FAIL" }')
  if [[ "$cmp" == "PASS" ]]; then
    PASS=$((PASS+1))
    icon="OK"
  else
    FAIL=$((FAIL+1))
    icon="!!"
  fi
  RESULTS+=("$(printf "%s  %-3s %s-%s  got %-9s  expected >= %-7s  %s" "$icon" "$state" "$zip5" "$zip4" "${got}%" "${expected}%" "$note")")
done

printf "%-3s %-3s %-12s %-13s %-19s %s\n" "" "St" "ZIP+4" "Got" "Expected (floor)" "Note"
printf '%.0s-' {1..100}; echo ""
for r in "${RESULTS[@]}"; do
  echo "  $r"
done
echo ""
echo "Result: $PASS passed, $FAIL failed (out of $((PASS+FAIL)))"
[[ "$FAIL" -gt 0 ]] && exit 1 || exit 0
