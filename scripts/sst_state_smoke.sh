#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# Generic SST-state smoke test. For each state, hit the live engine
# at one representative ZIP+4 per major city and print the combined
# rate + per-jurisdiction breakdown. Designed for hand-comparison
# against each state's own DOR rate calculator.
#
# Each row format: "State|City|ZIP5|ZIP4"
# Comments after # are ignored.

API="${API:-https://api.opensalestax.org/v1/calculate}"

CASES=(
  # --- Arkansas ---
  "AR|Little Rock|72201|1424"
  "AR|Fort Smith|72901|2402"
  "AR|Fayetteville|72701|5501"
  "AR|Jonesboro|72401|2810"
  # --- Georgia ---
  "GA|Atlanta|30303|1015"
  "GA|Savannah|31401|3209"
  "GA|Augusta|30901|3603"
  "GA|Columbus|31901|2735"
  "GA|Macon|31201|2803"
  # --- Iowa ---
  "IA|Des Moines|50309|2306"
  "IA|Cedar Rapids|52401|2802"
  "IA|Davenport|52801|1518"
  "IA|Iowa City|52240|3702"
  # --- Indiana (flat 7%, no locals) ---
  "IN|Indianapolis|46202|2802"
  "IN|Fort Wayne|46802|1102"
  "IN|Evansville|47708|1234"
  # --- Kansas ---
  "KS|Topeka|66603|3304"
  "KS|Wichita|67202|2417"
  "KS|Kansas City|66101|2204"
  "KS|Overland Park|66210|1801"
  # --- Kentucky (flat 6%) ---
  "KY|Louisville|40202|2404"
  "KY|Lexington|40507|1432"
  # --- Michigan (flat 6%) ---
  "MI|Detroit|48226|3614"
  "MI|Grand Rapids|49503|2401"
  "MI|Lansing|48933|1218"
  # --- Minnesota (already validated, smoke just to confirm) ---
  "MN|Minneapolis|55401|1024"
  "MN|St. Paul|55101|1014"
  # --- North Carolina ---
  "NC|Raleigh|27601|1303"
  "NC|Charlotte|28202|1402"
  "NC|Greensboro|27401|3504"
  "NC|Durham|27701|3309"
  # --- North Dakota ---
  "ND|Bismarck|58501|4505"
  "ND|Fargo|58102|3703"
  "ND|Grand Forks|58201|4905"
  # --- Nebraska ---
  "NE|Omaha|68102|1718"
  "NE|Lincoln|68508|2802"
  "NE|Bellevue|68005|3804"
  # --- New Jersey (flat 6.625%) ---
  "NJ|Newark|07102|3505"
  "NJ|Jersey City|07302|6809"
  "NJ|Trenton|08608|2304"
  # --- Nevada ---
  "NV|Las Vegas|89101|2402"
  "NV|Reno|89501|1606"
  "NV|Carson City|89701|4906"
  # --- Ohio ---
  "OH|Columbus|43215|3704"
  "OH|Cleveland|44113|1417"
  "OH|Cincinnati|45202|3401"
  "OH|Toledo|43604|2305"
  # --- Oklahoma ---
  "OK|Oklahoma City|73102|6107"
  "OK|Tulsa|74103|3804"
  "OK|Norman|73069|7035"
  # --- Rhode Island (flat 7%) ---
  "RI|Providence|02903|2511"
  "RI|Warwick|02886|7905"
  # --- South Dakota ---
  "SD|Sioux Falls|57104|2401"
  "SD|Rapid City|57701|1701"
  # --- Tennessee ---
  "TN|Nashville|37201|2402"
  "TN|Memphis|38103|2701"
  "TN|Knoxville|37902|1234"
  "TN|Chattanooga|37402|1015"
  # --- Utah ---
  "UT|Salt Lake City|84111|2202"
  "UT|Provo|84601|3704"
  "UT|Ogden|84401|1303"
  # --- Vermont ---
  "VT|Montpelier|05601|1602"
  "VT|Burlington|05401|2402"
  # --- Washington ---
  "WA|Seattle|98101|2802"
  "WA|Spokane|99201|2402"
  "WA|Tacoma|98402|3502"
  "WA|Bellevue|98004|3504"
  # --- Wisconsin ---
  "WI|Milwaukee|53202|2402"
  "WI|Madison|53703|3505"
  "WI|Green Bay|54301|3502"
  "WI|Kenosha|53140|2402"
  # --- West Virginia ---
  "WV|Charleston|25301|1108"
  "WV|Huntington|25701|2401"
  "WV|Morgantown|26505|2204"
  # --- Wyoming ---
  "WY|Cheyenne|82001|3504"
  "WY|Casper|82601|2401"
  "WY|Laramie|82070|2402"
)

# Parse args: --state XX restricts to one state.
FILTER_STATE=""
if [[ "$1" == "--state" && -n "$2" ]]; then
  FILTER_STATE="$2"
fi

current_state=""
printf "%-4s %-20s %-7s %-5s %-9s %s\n" "St" "City" "ZIP" "+4" "Rate" "Breakdown"
printf '%.0s-' {1..130}
echo ""

for entry in "${CASES[@]}"; do
  IFS='|' read -r state city zip5 zip4 <<< "$entry"
  if [[ -n "$FILTER_STATE" && "$state" != "$FILTER_STATE" ]]; then
    continue
  fi
  if [[ "$state" != "$current_state" && -n "$current_state" ]]; then
    echo ""
  fi
  current_state="$state"
  body="{\"address\":{\"zip5\":\"$zip5\",\"zip4\":\"$zip4\"},\"line_items\":[{\"amount\":\"100.00\"}]}"
  resp=$(curl -s -X POST -H 'Content-Type: application/json' "$API" -d "$body")
  echo "$resp" | awk -v st="$state" -v city="$city" -v zip5="$zip5" -v zip4="$zip4" '
    {
      n = split($0, lines, "\"rate_pct\":")
      rate = "?"
      if (n >= 2) {
        s = lines[2]
        sub(/^"/, "", s); sub(/".*/, "", s)
        rate = s
      }
      breakdown = ""
      m = split($0, juris, "{\"name\":\"")
      for (i = 2; i <= m; i++) {
        s = juris[i]
        name = s; sub(/".*/, "", name)
        ratepart = s; sub(/.*"rate_pct":"/, "", ratepart); sub(/".*/, "", ratepart)
        if (breakdown != "") breakdown = breakdown ", "
        breakdown = breakdown name " " ratepart "%"
      }
      if (breakdown == "") breakdown = "(no jurisdictions)"
      printf "%-4s %-20s %-7s %-5s %-9s %s\n", st, city, zip5, zip4, rate"%", breakdown
    }
  '
done
