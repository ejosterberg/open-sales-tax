#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# Smoke-test the live engine against MN cities within ~60 miles of
# Minneapolis. Each row is one representative ZIP+4; compare manually
# against https://www.revenue.state.mn.us/sales-tax-rate-calculator
# for the same address + the Apr-Jun 2026 effective period.
#
# Format: "City Name|ZIP5|ZIP4"

API="${API:-https://api.opensalestax.org/v1/calculate}"

CASES=(
  # Twin Cities core
  "Minneapolis|55401|1024"
  "Minneapolis (Nokomis)|55417|2130"
  "St. Paul (downtown)|55101|1014"
  "St. Paul (Como)|55103|1209"
  "West St. Paul|55118|2304"
  # Hennepin County suburbs
  "Bloomington|55420|3506"
  "Edina|55424|1027"
  "Eden Prairie|55344|7117"
  "Minnetonka|55305|3700"
  "Plymouth|55441|3303"
  "Maple Grove|55369|7204"
  "Brooklyn Park|55443|3017"
  "Hopkins|55343|7019"
  "St. Louis Park|55426|3127"
  # Ramsey County / North Metro
  "Roseville|55113|3208"
  "New Brighton|55112|3306"
  "White Bear Lake|55110|2727"
  "Maplewood|55109|2502"
  "North Oaks|55127|2802"
  # Anoka County
  "Anoka|55303|2306"
  "Coon Rapids|55448|2105"
  # Dakota County
  "Eagan|55121|2207"
  "Burnsville|55337|3618"
  "Apple Valley|55124|7219"
  "Lakeville|55044|6105"
  "Inver Grove Heights|55077|3801"
  "Hastings|55033|2501"
  # Washington County
  "Woodbury|55125|2208"
  "Cottage Grove|55016|2206"
  "Stillwater|55082|6707"
  "Forest Lake|55025|7616"
  # Carver / Scott Counties
  "Chaska|55318|3201"
  "Shakopee|55379|2417"
  # Goodhue County (~50mi SE)
  "Red Wing|55066|2810"
  # Rice County (~40mi S)
  "Northfield|55057|3034"
)

printf "%-30s %-7s %-5s %-9s %s\n" "City" "ZIP" "+4" "Rate" "Combined breakdown"
printf '%.0s-' {1..120}
echo ""

for entry in "${CASES[@]}"; do
  IFS='|' read -r city zip5 zip4 <<< "$entry"
  body="{\"address\":{\"zip5\":\"$zip5\",\"zip4\":\"$zip4\"},\"line_items\":[{\"amount\":\"100.00\"}]}"
  resp=$(curl -s -X POST -H 'Content-Type: application/json' "$API" -d "$body")
  # Pull rate_pct + a comma-joined "name (rate)" list out of the JSON.
  echo "$resp" | awk -v city="$city" -v zip5="$zip5" -v zip4="$zip4" '
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
      printf "%-30s %-7s %-5s %-9s %s\n", city, zip5, zip4, rate"%", breakdown
    }
  '
done
