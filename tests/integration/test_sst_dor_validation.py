# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""DOR-validation regression test for SST states.

Hits the live engine (https://api.opensalestax.org) with a curated
list of major-city ZIP+4 addresses and asserts the combined rate
matches what each state's Department of Revenue calculator
publishes -- within a small tolerance to account for ZIP+4 micro
variation (some +4 ranges within a city carry slightly different
combined rates due to overlapping district boundaries).

Skipped automatically in normal pytest runs (no marker); runs only
when explicitly invoked with ``pytest -m liveapi``. The test is a
guard against regressions in the SST loader / lookup engine rather
than a CI gate (the live engine isn't always reachable from CI).

Each row is one (state, city, ZIP+4, expected_rate_pct, source)
tuple. The expected rate was verified against the linked DOR
publication on the date in the comment. Rates change quarterly --
when a published DOR rate changes, update the row AND record the
date so future maintainers know which entries are fresh.
"""

from __future__ import annotations

import os
from decimal import Decimal

import httpx
import pytest

API = os.environ.get(
    "OPENSALESTAX_LIVE_API",
    "https://api.opensalestax.org/v1/calculate",
)

# (state, city, zip5, zip4, expected_rate_pct_str, tolerance_pct, source_note)
DOR_GRID: list[tuple[str, str, str, str, str, str, str]] = [
    # Tennessee -- TN DOR Local Option Sales Tax 2026-Q1
    ("TN", "Nashville (Metro)", "37201", "2402", "9.750", "0.05", "TN DOR + IMPROVE Act 0.5% transit (effective 2025-02-01)"),
    ("TN", "Memphis", "38103", "2701", "9.750", "0.05", "TN DOR (state 7% + Shelby 2.25% + Memphis 0.5%)"),
    ("TN", "Knoxville", "37902", "1234", "9.250", "0.05", "TN DOR (state 7% + Knox 2.25%)"),
    ("TN", "Chattanooga", "37402", "1015", "9.250", "0.05", "TN DOR (state 7% + Hamilton 2.25%)"),
    # Minnesota -- MN DOR sales-tax-rate calculator 2026-Q2
    ("MN", "Minneapolis", "55401", "1024", "9.025", "0.05", "MN DOR (state + Hennepin + Minneapolis + 3 metro districts)"),
    ("MN", "St. Paul", "55101", "1014", "9.875", "0.05", "MN DOR (state + Ramsey + St. Paul + 2 metro districts)"),
    # Kansas -- KS DOR Jurisdiction Sales Tax Rates 2026-Q1
    ("KS", "Topeka", "66603", "3304", "9.350", "0.05", "KS DOR (state 6.5% + Shawnee 1.35% + Topeka 1.5%)"),
    ("KS", "Wichita", "67202", "2417", "7.500", "0.05", "KS DOR (state 6.5% + Sedgwick 1%; Wichita has no city tax)"),
    ("KS", "Kansas City", "66101", "2204", "9.125", "0.05", "KS DOR (state 6.5% + Wyandotte 1% + KC 1.625%)"),
    # Nebraska -- NE DOR Local Sales and Use Tax Rates 2026-Q1
    ("NE", "Omaha", "68102", "1718", "7.000", "0.05", "NE DOR (state 5.5% + Omaha 1.5%)"),
    ("NE", "Lincoln", "68508", "2802", "7.250", "0.05", "NE DOR (state 5.5% + Lincoln 1.75%)"),
    ("NE", "Norfolk", "68701", "1234", "7.500", "0.05", "NE DOR (state 5.5% + Norfolk 2.0%)"),
    ("NE", "Kearney", "68845", "1234", "7.000", "0.05", "NE DOR (state 5.5% + Kearney 1.5%)"),
    ("NE", "North Platte", "69101", "1234", "7.500", "0.05", "NE DOR (state 5.5% + North Platte 2.0%)"),
    ("NE", "Grand Island", "68803", "1234", "7.500", "0.05", "NE DOR (state 5.5% + Grand Island 2.0%)"),
    ("NE", "Fremont", "68025", "1234", "7.000", "0.05", "NE DOR (state 5.5% + Fremont 1.5%)"),
    ("NE", "Beatrice", "68310", "1234", "7.500", "0.05", "NE DOR (state 5.5% + Beatrice 2.0%)"),
    ("NE", "Columbus", "68601", "1234", "7.000", "0.05", "NE DOR (state 5.5% + Columbus 1.5%)"),
    ("NE", "McCook", "69001", "1234", "7.500", "0.05", "NE DOR (state 5.5% + McCook 2.0%)"),
    # Hastings (68901) friendly name 21415 is wired in ne_names.py but no
    # validation row: ZIP 68901 routes to code 19595 (Grand Island) and
    # 68902 misroutes to a SD overlap in the engine. Add a row once the
    # engine resolves Hastings ZIPs to FIPS Place 21415 cleanly.
    ("NE", "La Vista", "68128", "1234", "7.500", "0.05", "NE DOR (state 5.5% + La Vista 2.0%)"),
    ("NE", "Gretna", "68138", "5000", "7.500", "0.05", "NE DOR (state 5.5% + Gretna 2.0%)"),
    # Nevada -- NV DOR Tax Rates by County 2026
    ("NV", "Las Vegas", "89101", "2402", "8.375", "0.05", "NV DOR (Clark County combined)"),
    ("NV", "Reno", "89501", "1606", "8.265", "0.05", "NV DOR (Washoe County combined)"),
    # Oklahoma -- OK DOR Sales and Use Tax Rate Charts 2026-Q2
    ("OK", "Tulsa", "74103", "3804", "8.517", "0.05", "OK DOR (state 4.5% + Tulsa County 0.367% + Tulsa city 3.65%)"),
    ("OK", "Oklahoma City", "73102", "6107", "8.625", "0.05", "OK DOR (state 4.5% + OKC 4.125%)"),
    # Georgia -- GA DOR Sales Tax Rates 2026-Q1
    ("GA", "Atlanta", "30303", "1015", "8.900", "0.05", "GA DOR (state 4% + Fulton 3% + Atlanta MOST 1.9%)"),
    # North Carolina -- NC DOR Sales and Use Tax Rates 2026-Q1
    ("NC", "Charlotte", "28202", "1402", "7.250", "0.05", "NC DOR (state 4.75% + Mecklenburg 2% + transit 0.5%)"),
    ("NC", "Raleigh", "27601", "1303", "7.250", "0.05", "NC DOR (state 4.75% + Wake 2% + transit 0.5%)"),
    # South Dakota -- SD DOR Municipal Sales Tax 2026-Q1
    ("SD", "Sioux Falls", "57104", "2401", "6.200", "0.05", "SD DOR (state 4.2% + Sioux Falls 2%)"),
    # Utah -- UT DOR sales tax rates 2026-Q2
    ("UT", "Salt Lake City", "84111", "2202", "8.450", "0.05", "UT DOR (state 4.85% + Salt Lake County 2.6% + SLC 1%)"),
    # Washington -- WA DOR Local Sales & Use Tax Rates 2026-Q2
    ("WA", "Bellevue", "98004", "3504", "10.300", "0.05", "WA DOR (state 6.5% + Bellevue combined 3.8%)"),
    # Wisconsin -- WI DOR sales tax rate lookup 2026-Q1
    ("WI", "Milwaukee", "53202", "2402", "5.900", "0.05", "WI DOR (state 5% + Milwaukee County 0.9%)"),
    ("WI", "Madison", "53703", "3505", "5.500", "0.05", "WI DOR (state 5% + Dane County 0.5%)"),
    # West Virginia -- WV DOR sales tax 2026-Q1
    ("WV", "Charleston", "25301", "1108", "7.000", "0.05", "WV DOR (state 6% + Charleston 1%)"),
    # Wyoming -- WY DOR sales tax rates 2026-Q2
    ("WY", "Cheyenne", "82001", "3504", "5.000", "0.05", "WY DOR (state 4% + Laramie 1%)"),
    ("WY", "Casper", "82601", "2401", "5.000", "0.05", "WY DOR (state 4% + Natrona 1%)"),
    # Arkansas -- AR DFA Sales and Use Tax Rates 2026-Q2
    ("AR", "Fort Smith", "72901", "2402", "9.500", "0.05", "AR DFA (state 6.5% + Sebastian 1% + Fort Smith 2%)"),
    ("AR", "Fayetteville", "72701", "5501", "9.750", "0.05", "AR DFA (state 6.5% + Washington 1.25% + Fayetteville 2%)"),
    # Iowa -- IA DOR Local Option Sales Tax 2026-Q1
    ("IA", "Des Moines", "50309", "2306", "7.000", "0.05", "IA DOR (state 6% + Polk LOST 1%)"),
    ("IA", "Cedar Rapids", "52401", "2802", "7.000", "0.05", "IA DOR (state 6% + Linn LOST 1%)"),
    # Indiana -- flat 7%, no locals
    ("IN", "Indianapolis", "46202", "2802", "7.000", "0.01", "IN flat 7% statewide"),
    # Kentucky -- flat 6%
    ("KY", "Louisville", "40202", "2404", "6.000", "0.01", "KY flat 6% statewide"),
    # Michigan -- flat 6%
    ("MI", "Detroit", "48226", "3614", "6.000", "0.01", "MI flat 6% statewide"),
    # New Jersey -- flat 6.625%
    ("NJ", "Newark", "07102", "3505", "6.625", "0.01", "NJ flat 6.625% statewide"),
    # Rhode Island -- flat 7%
    ("RI", "Providence", "02903", "2511", "7.000", "0.01", "RI flat 7% statewide"),
    # ND additional -- ND DOR Local Sales Tax Rates 2026-Q1
    ("ND", "Fargo", "58102", "3703", "7.750", "0.05", "ND DOR (state 5% + Cass 0.5% + Fargo 2.25%)"),
    # SD additional
    ("SD", "Rapid City", "57701", "1701", "6.200", "0.05", "SD DOR (state 4.2% + Rapid City 2%)"),
    # WI additional
    ("WI", "Green Bay", "54301", "3502", "5.500", "0.05", "WI DOR (state 5% + Brown 0.5%)"),
    # WV additional
    ("WV", "Huntington", "25701", "2401", "7.000", "0.05", "WV DOR (state 6% + Huntington 1%)"),
    # OH Cleveland -- different transit district
    ("OH", "Cleveland", "44113", "1417", "8.000", "0.05", "OH DOR (state 5.75% + Cuyahoga 1.25% + RTA 1%)"),
    # OH additional cities (county + transit-authority stack; OH has no city sales tax)
    ("OH", "Cincinnati", "45202", "1234", "7.800", "0.05", "OH DOR (state 5.75% + Hamilton 1.25% + SORTA 0.8%)"),
    ("OH", "Columbus", "43215", "1234", "8.000", "0.05", "OH DOR (state 5.75% + Franklin 1.25% + COTA 1.0%)"),
    ("OH", "Dayton", "45402", "1234", "7.500", "0.05", "OH DOR (state 5.75% + Montgomery 1.25% + GDRTA 0.5%)"),
    ("OH", "Toledo", "43604", "1234", "7.750", "0.05", "OH DOR (state 5.75% + Lucas 1.5% + TARTA 0.5%)"),
    ("OH", "Akron", "44308", "1234", "6.750", "0.05", "OH DOR (state 5.75% + Summit 0.5% + METRO 0.5%)"),
    ("OH", "Youngstown", "44503", "1234", "7.500", "0.05", "OH DOR (state 5.75% + Mahoning 1.5% + WRTA 0.25%)"),
    # WA additional
    ("WA", "Tacoma", "98402", "3502", "10.400", "0.10", "WA DOR (state 6.5% + Tacoma combined ~3.9%)"),
    ("WA", "Vancouver", "98660", "1234", "8.900", "0.05", "WA DOR (state 6.5% + Vancouver combined 2.4%)"),
    ("WA", "Bellingham", "98225", "1234", "9.100", "0.05", "WA DOR (state 6.5% + Bellingham combined 2.6%)"),
    ("WA", "Federal Way", "98003", "1234", "10.300", "0.10", "WA DOR (state 6.5% + Federal Way combined ~3.8%)"),
    ("WA", "Renton", "98055", "1234", "10.500", "0.05", "WA DOR (state 6.5% + Renton combined 4.0%)"),
    ("WA", "Olympia", "98501", "1234", "9.800", "0.05", "WA DOR (state 6.5% + Olympia combined 3.3%)"),
    # OK secondary cities (post-loose-fallback fix; was 12.625% / 13.25% pre-fix)
    ("OK", "Norman", "73069", "6107", "8.750", "0.05", "OK DOR (state 4.5% + Cleveland 0.125% + Norman 4.125%)"),
    ("OK", "Moore", "73160", "2306", "8.500", "0.05", "OK DOR (state 4.5% + Cleveland 0.125% + Moore 3.875%)"),
    ("OK", "Broken Arrow", "74012", "2417", "8.417", "0.05", "OK DOR (state 4.5% + Tulsa 0.367% + Broken Arrow 3.55%)"),
    ("OK", "Lawton", "73505", "1306", "9.000", "0.05", "OK DOR (state 4.5% + Comanche 0.375% + Lawton 4.125%)"),
    # OK additional cities (Tulsa-area suburbs + central-OK / outstate)
    ("OK", "Bixby", "74008", "1234", "8.417", "0.05", "OK DOR (state 4.5% + Tulsa 0.367% + Bixby 3.55%)"),
    ("OK", "Sand Springs", "74063", "1234", "8.917", "0.05", "OK DOR (state 4.5% + Tulsa 0.367% + Sand Springs 4.05%)"),
    ("OK", "Sapulpa", "74066", "1234", "9.667", "0.05", "OK DOR (state 4.5% + Creek 1.167% + Sapulpa 4.0%)"),
    ("OK", "Glenpool", "74033", "1234", "9.967", "0.05", "OK DOR (state 4.5% + Tulsa 0.367% + Glenpool 5.1%)"),
    ("OK", "Edmond", "73034", "1234", "9.000", "0.05", "OK DOR (state 4.5% + Logan County 0.75% + Edmond 3.75%; ZIP 73034 straddles OK/Logan; +4 1234 is in Logan)"),
    ("OK", "Stillwater", "74074", "1234", "9.313", "0.05", "OK DOR (state 4.5% + Payne 0.813% + Stillwater 4.0%)"),
    ("OK", "Enid", "73701", "1234", "9.100", "0.05", "OK DOR (state 4.5% + Garfield 0.35% + Enid 4.25%)"),
    ("OK", "Shawnee", "74801", "1234", "9.995", "0.05", "OK DOR (state 4.5% + Pottawatomie 1.495% + Shawnee 4.0%)"),
    # Bartlesville (74006) and Yukon (73085) friendly names are wired in
    # ok_names.py but DOR validation rows are intentionally omitted: the
    # SST file rates carried by the live engine diverge from current
    # OK DOR published rates by >0.1%, indicating either a stale SST
    # snapshot or a recent municipal rate change. Add validation rows
    # once the next quarterly SST refresh resolves the gap.
    # KS secondary
    ("KS", "Olathe", "66061", "2917", "9.475", "0.05", "KS DOR (state 6.5% + Johnson 1.475% + Olathe 1.5%)"),
    # TN secondary
    ("TN", "Clarksville", "37040", "1407", "9.500", "0.05", "TN DOR (state 7% + Montgomery 2.5%; Clarksville no separate city tax)"),
    ("TN", "Murfreesboro", "37130", "2517", "9.750", "0.05", "TN DOR (state 7% + Rutherford 2.75%)"),
    # SD additional
    ("SD", "Aberdeen", "57401", "3306", "6.200", "0.05", "SD DOR (state 4.2% + Aberdeen 2%)"),
    # AZ -- non-SST, top-20-city TPT loader (v0.23). State 5.6% + per-county + city.
    # Tolerance is 0.01 because rates are exact (no boundary micro-variation; ZIPs map
    # to a single city via the AZ_CITIES table).
    ("AZ", "Phoenix", "85042", "0001", "9.100", "0.01", "AZ DOR May 2026 CSV (state 5.6% + Maricopa 0.7% + Phoenix 2.8%)"),
    ("AZ", "Phoenix downtown", "85003", "0001", "9.100", "0.01", "AZ DOR (Phoenix downtown)"),
    ("AZ", "Scottsdale", "85251", "0001", "8.000", "0.01", "AZ DOR (state 5.6% + Maricopa 0.7% + Scottsdale 1.7%)"),
    ("AZ", "Tucson", "85701", "0001", "8.700", "0.01", "AZ DOR (state 5.6% + Pima 0.5% + Tucson 2.6%)"),
    ("AZ", "Mesa", "85201", "0001", "8.300", "0.01", "AZ DOR (state 5.6% + Maricopa 0.7% + Mesa 2.0%)"),
    ("AZ", "Chandler", "85224", "0001", "7.800", "0.01", "AZ DOR (state 5.6% + Maricopa 0.7% + Chandler 1.5%)"),
    ("AZ", "Glendale", "85301", "0001", "9.200", "0.01", "AZ DOR (state 5.6% + Maricopa 0.7% + Glendale 2.9%)"),
    ("AZ", "Tempe", "85281", "0001", "8.100", "0.01", "AZ DOR (state 5.6% + Maricopa 0.7% + Tempe 1.8%)"),
    ("AZ", "Flagstaff", "86001", "0001", "9.386", "0.01", "AZ DOR (state 5.6% + Coconino 1.3% + Flagstaff 2.486%)"),
    ("AZ", "Yuma", "85364", "0001", "8.412", "0.01", "AZ DOR (state 5.6% + Yuma 1.112% + Yuma city 1.7%)"),
    ("AZ", "Lake Havasu City", "86403", "0001", "7.600", "0.01", "AZ DOR (state 5.6% + Mohave 0.0% + Lake Havasu City 2.0%)"),
    # AZ secondary Phoenix-metro cities (added v0.25 once seeded in az_data.py)
    ("AZ", "Glendale", "85308", "1234", "9.200", "0.01", "AZ DOR (state 5.6% + Maricopa 0.7% + Glendale 2.9%)"),
    ("AZ", "Surprise", "85388", "1234", "9.100", "0.01", "AZ DOR (state 5.6% + Maricopa 0.7% + Surprise 2.8%)"),
    ("AZ", "Goodyear", "85338", "1234", "8.800", "0.01", "AZ DOR (state 5.6% + Maricopa 0.7% + Goodyear 2.5%)"),
    ("AZ", "Gilbert", "85296", "1234", "8.300", "0.01", "AZ DOR (state 5.6% + Maricopa 0.7% + Gilbert 2.0%)"),
    # AZ -- 2026-05-04 expansion (v0.25): representative sample of the 28 newly
    # added cities. Includes every city that brings a previously-uncovered
    # county online (Sierra Vista/Cochise, Nogales/Santa Cruz, Globe & Payson/
    # Gila, Show Low/Navajo) plus one from each other touched county.
    ("AZ", "Sierra Vista", "85635", "0001", "8.050", "0.01", "AZ DOR May 2026 CSV (state 5.6% + Cochise 0.5% + Sierra Vista 1.95%)"),
    ("AZ", "Nogales", "85621", "0001", "8.600", "0.01", "AZ DOR May 2026 CSV (state 5.6% + Santa Cruz 1.0% + Nogales 2.0%)"),
    ("AZ", "Page", "86040", "0001", "9.900", "0.01", "AZ DOR May 2026 CSV (state 5.6% + Coconino 1.3% + Page 3.0%)"),
    ("AZ", "Show Low", "85901", "0001", "8.430", "0.01", "AZ DOR May 2026 CSV (state 5.6% + Navajo 0.83% + Show Low 2.0%)"),
    ("AZ", "Apache Junction", "85119", "0001", "9.100", "0.01", "AZ DOR May 2026 CSV (state 5.6% + Pinal 1.1% + Apache Junction 2.4%)"),
    ("AZ", "Queen Creek", "85140", "0001", "8.550", "0.01", "AZ DOR May 2026 CSV (state 5.6% + Maricopa 0.7% + Queen Creek 2.25%)"),
    ("AZ", "Maricopa", "85138", "0001", "9.200", "0.01", "AZ DOR May 2026 CSV (state 5.6% + Pinal 1.1% + Maricopa city 2.5%)"),
    ("AZ", "Globe", "85501", "0001", "9.900", "0.01", "AZ DOR May 2026 CSV (state 5.6% + Gila 1.0% + Globe 3.3%)"),
    ("AZ", "Payson", "85541", "0001", "10.480", "0.01", "AZ DOR May 2026 CSV (state 5.6% + Gila 1.0% + Payson 3.88%)"),
    ("AZ", "Sedona", "86336", "0001", "9.850", "0.01", "AZ DOR May 2026 CSV (state 5.6% + Yavapai 0.75% + Sedona 3.5%)"),
    ("AZ", "San Luis", "85349", "0001", "10.712", "0.01", "AZ DOR May 2026 CSV (state 5.6% + Yuma 1.112% + San Luis 4.0%)"),
    ("AZ", "Sahuarita", "85629", "0001", "8.100", "0.01", "AZ DOR May 2026 CSV (state 5.6% + Pima 0.5% + Sahuarita 2.0%)"),
    # TN suburb double-counting bug fix verification (was 14.75% / 17.5% pre-v0.24)
    ("TN", "Brentwood", "37027", "1234", "9.750", "0.05", "TN DOR (state 7% + Davidson 2.25% + IMPROVE Act 0.5%) -- post-v0.24 expired-record filter"),
    ("TN", "Franklin", "37067", "1234", "9.750", "0.05", "TN DOR (state 7% + Williamson 2.75%) -- post-v0.24 expired-record filter"),
    # OK Newcastle (city 51150) -- the McClain-side suburb of Norman
    ("OK", "Newcastle", "73072", "1015", "9.000", "0.05", "OK DOR (state 4.5% + McClain 0.5% + Newcastle 4.0%)"),
    # GA Alpharetta -- post-v0.24 fix dropped phantom Atlanta MOST overlay
    ("GA", "Alpharetta", "30022", "1234", "7.750", "0.05", "GA DOR (state 4% + Fulton 3% + Fulton TSPLOST 0.75%) -- post-v0.24 expired-record filter"),
    # MN suburbs
    ("MN", "Eagan", "55121", "1234", "8.125", "0.05", "MN DOR (state + Dakota + 2 metro districts)"),
    ("MN", "Hopkins", "55305", "1234", "8.525", "0.05", "MN DOR (state + Hennepin + Hennepin transit + 2 metro districts)"),
    ("MN", "Bloomington", "55425", "1234", "9.025", "0.05", "MN DOR (state + Hennepin + Hennepin transit + 2 metro districts + Bloomington 0.5%)"),
    ("MN", "St. Louis Park", "55416", "1234", "8.525", "0.05", "MN DOR (state + Hennepin + Hennepin transit + 2 metro districts)"),
    # Connecticut -- flat 6.35% statewide, NO local sales taxes anywhere
    # in the state per Conn. Gen. Stat. section 12-408. The "Hartford"
    # entry is a regression guard ensuring a future maintainer doesn't
    # accidentally introduce phantom local rates.
    ("CT", "Hartford", "06103", "1234", "6.350", "0.01", "CT DRS (Conn. Gen. Stat. section 12-408: flat 6.35% statewide, no locals anywhere in CT)"),
    # Mississippi -- MS DOR + city authorizing acts (verified 2026-05-04)
    # Jackson + Tupelo have general-retail city taxes; Hattiesburg /
    # Gulfport / Biloxi have tourism-only taxes (hotels + restaurants
    # only) so general-retail is the flat 7% statewide.
    ("MS", "Jackson", "39201", "0001", "8.000", "0.05", "MS DOR (state 7% + Jackson 1% Special Sales Tax per Miss. Code Ann. section 27-65-241)"),
    ("MS", "Tupelo", "38801", "0001", "7.250", "0.05", "MS DOR (state 7% + Tupelo 0.25% Water Procurement Facility Tax per H.B. 1685, Laws 2008)"),
    ("MS", "Hattiesburg", "39401", "0001", "7.000", "0.05", "MS DOR (state 7% only -- Hattiesburg's Tourism Tax applies to hotels+restaurants only, not general retail)"),
    ("MS", "Gulfport", "39501", "0001", "7.000", "0.05", "MS DOR (state 7% only -- Harrison County tourism tax is hotels+prepared food only)"),
    ("MS", "Biloxi", "39530", "0001", "7.000", "0.05", "MS DOR (state 7% only -- Harrison County tourism tax is hotels+prepared food only)"),
    # South Carolina -- SC DOR Form ST-500 effective May 1, 2026
    # All 10 covered cities; combined rates are state 6% + per-county
    # local portion (no city-level rate; Myrtle Beach is the only SC
    # city with its own tax and isn't in this set).
    ("SC", "Columbia", "29201", "0001", "8.000", "0.05", "SC DOR ST-500 2026-05-01 (state 6% + Richland LO 1% + Richland TT 1%)"),
    ("SC", "Charleston", "29401", "0001", "9.000", "0.05", "SC DOR ST-500 2026-05-01 (state 6% + Charleston LO 1% + TT 1% + ECI 1%)"),
    ("SC", "Mount Pleasant", "29464", "0001", "9.000", "0.05", "SC DOR ST-500 (Charleston County 3% local)"),
    ("SC", "North Charleston", "29406", "0001", "9.000", "0.05", "SC DOR ST-500 (Charleston County 3% local)"),
    ("SC", "Rock Hill", "29730", "0001", "7.000", "0.05", "SC DOR ST-500 (state 6% + York CP 1%)"),
    ("SC", "Greenville", "29601", "0001", "6.000", "0.05", "SC DOR ST-500 (Greenville County has no local sales tax)"),
    ("SC", "Summerville", "29483", "0001", "7.000", "0.05", "SC DOR ST-500 (state 6% + Dorchester TT 1%)"),
    ("SC", "Spartanburg", "29301", "0001", "7.000", "0.05", "SC DOR ST-500 (state 6% + Spartanburg CP 1%)"),
    ("SC", "Sumter", "29150", "0001", "8.000", "0.05", "SC DOR ST-500 (state 6% + Sumter LO 1% + CP 1%)"),
    ("SC", "Goose Creek", "29445", "0001", "9.000", "0.05", "SC DOR ST-500 (state 6% + Berkeley LO 1% + TT 1% + ECI 1%)"),
    # Virginia -- VA Dept of Taxation rate-by-locality chart (verified 2026-05-04)
    # Hampton Roads / Northern VA / Central VA add 0.7% on top of the
    # 5.3% statewide minimum -> 6.0% combined. Roanoke and Lynchburg
    # are outside all regional add-ons -> 5.3%.
    ("VA", "Virginia Beach", "23451", "0001", "6.000", "0.05", "VA Tax (state 4.3% + local 1% + Hampton Roads 0.7%)"),
    ("VA", "Norfolk", "23510", "0001", "6.000", "0.05", "VA Tax (Hampton Roads region)"),
    ("VA", "Chesapeake", "23320", "0001", "6.000", "0.05", "VA Tax (Hampton Roads region)"),
    ("VA", "Newport News", "23601", "0001", "6.000", "0.05", "VA Tax (Hampton Roads region)"),
    ("VA", "Hampton", "23666", "0001", "6.000", "0.05", "VA Tax (Hampton Roads region)"),
    ("VA", "Portsmouth", "23704", "0001", "6.000", "0.05", "VA Tax (Hampton Roads region)"),
    ("VA", "Suffolk", "23434", "0001", "6.000", "0.05", "VA Tax (Hampton Roads region)"),
    ("VA", "Arlington", "22201", "0001", "6.000", "0.05", "VA Tax (state 4.3% + local 1% + Northern VA 0.7%)"),
    ("VA", "Alexandria", "22314", "0001", "6.000", "0.05", "VA Tax (Northern VA region)"),
    ("VA", "Richmond", "23219", "0001", "6.000", "0.05", "VA Tax (state 4.3% + local 1% + Central VA 0.7%)"),
    ("VA", "Roanoke", "24011", "0001", "5.300", "0.05", "VA Tax (state 4.3% + local 1%; no regional add-on)"),
    ("VA", "Lynchburg", "24501", "0001", "5.300", "0.05", "VA Tax (state 4.3% + local 1%; no regional add-on)"),
    # Missouri -- MO DOR 2026 Sales/Use Tax Rate Tables (verified 2026-05-04)
    # Combined = state 4.225% + county + city (no special-district overlay).
    # Tolerance 0.10 because some +4 ranges within MO cities have CID/TDD
    # overlays that bump the actual rate above the city baseline; the
    # bare combined math yields the engine answer at the city centroid.
    ("MO", "Kansas City", "64108", "0001", "8.850", "0.10", "MO DOR (state 4.225% + Jackson 1.375% + KC 3.25%)"),
    ("MO", "St. Louis", "63103", "0001", "9.679", "0.10", "MO DOR (state 4.225% + St. Louis city 5.454%)"),
    ("MO", "Springfield", "65806", "0001", "8.100", "0.10", "MO DOR (state 4.225% + Greene 1.75% + Springfield 2.125%)"),
    ("MO", "Independence", "64055", "0001", "8.475", "0.10", "MO DOR (state 4.225% + Jackson 1.375% + Independence 2.875%)"),
    ("MO", "Columbia", "65201", "0001", "7.975", "0.10", "MO DOR (state 4.225% + Boone 1.75% + Columbia 2.0%)"),
    ("MO", "Lee's Summit", "64063", "0001", "8.350", "0.10", "MO DOR (state 4.225% + Jackson 1.375% + Lee's Summit 2.75%)"),
    ("MO", "O'Fallon", "63366", "0001", "7.950", "0.10", "MO DOR (state 4.225% + St. Charles 1.725% + O'Fallon 2.0%)"),
    ("MO", "St. Joseph", "64501", "0001", "9.700", "0.10", "MO DOR (state 4.225% + Buchanan 1.6% + St. Joseph 3.875%)"),
    ("MO", "St. Charles", "63301", "0001", "7.950", "0.10", "MO DOR (state 4.225% + St. Charles 1.725% + St. Charles city 2.0%)"),
    ("MO", "Joplin", "64801", "0001", "8.725", "0.10", "MO DOR (state 4.225% + Jasper 1.375% + Joplin 3.125%)"),
    ("MO", "Jefferson City", "65101", "0001", "7.850", "0.10", "MO DOR (state 4.225% + Cole 1.375% + Jefferson City 2.25%)"),
    ("MO", "Cape Girardeau", "63701", "0001", "8.475", "0.10", "MO DOR (state 4.225% + Cape Girardeau 1.5% + Cape Girardeau city 2.75%)"),
    # Florida -- FL DOR Form DR-15DSS effective Jan 1, 2026 (verified 2026-05-04)
    # Combined = state 6% + per-county discretionary surtax. FL has NO city-
    # level general sales tax anywhere; tolerance 0.05 because some +4
    # ranges in covered cities sit in different counties (e.g., a few
    # Jacksonville-postal ZIPs slip into Nassau or Clay counties; the
    # FL_CITIES table excludes those when known).
    ("FL", "Miami", "33130", "0001", "7.000", "0.05", "FL DOR DR-15DSS 2026 (state 6% + Miami-Dade 1%)"),
    ("FL", "Hialeah", "33010", "0001", "7.000", "0.05", "FL DOR DR-15DSS (Miami-Dade 1%)"),
    ("FL", "Orlando", "32801", "0001", "6.500", "0.05", "FL DOR DR-15DSS (state 6% + Orange school 0.5%)"),
    ("FL", "Tampa", "33602", "0001", "7.500", "0.05", "FL DOR DR-15DSS (state 6% + Hillsborough 1.5% -- 0.5% indigent care + 1% community investment)"),
    ("FL", "Jacksonville", "32202", "0001", "7.500", "0.05", "FL DOR DR-15DSS (state 6% + Duval 1.5%)"),
    ("FL", "St. Petersburg", "33701", "0001", "7.000", "0.05", "FL DOR DR-15DSS (state 6% + Pinellas 1%)"),
    ("FL", "Clearwater", "33755", "0001", "7.000", "0.05", "FL DOR DR-15DSS (Pinellas 1%)"),
    ("FL", "Fort Lauderdale", "33301", "0001", "7.000", "0.05", "FL DOR DR-15DSS (state 6% + Broward 1%)"),
    ("FL", "Hollywood", "33020", "0001", "7.000", "0.05", "FL DOR DR-15DSS (Broward 1%)"),
    ("FL", "West Palm Beach", "33401", "0001", "7.000", "0.05", "FL DOR DR-15DSS (state 6% + Palm Beach 1%)"),
    ("FL", "Boca Raton", "33432", "0001", "7.000", "0.05", "FL DOR DR-15DSS (Palm Beach 1%)"),
    ("FL", "Tallahassee", "32301", "0001", "7.500", "0.05", "FL DOR DR-15DSS (state 6% + Leon 1.5%)"),
    ("FL", "Gainesville", "32601", "0001", "7.500", "0.05", "FL DOR DR-15DSS (state 6% + Alachua 1.5%)"),
    ("FL", "Lakeland", "33801", "0001", "7.000", "0.05", "FL DOR DR-15DSS (state 6% + Polk 1%)"),
    ("FL", "Cape Coral", "33904", "0001", "6.500", "0.05", "FL DOR DR-15DSS (state 6% + Lee 0.5% school)"),
    # New York -- NY DTF Publication 718 (verified 2026-05-04;
    # cross-checked NYC + Buffalo + Yonkers against Avalara per-city pages)
    # Combined = state 4% + per-county + MCTD 0.375% (where applicable)
    # + city (NYC 4.5%, Yonkers 1.5%, NR/Mt.V/WP 1%; 0% elsewhere).
    # NYC's five boroughs all share 8.875% via the consolidated city
    # entry "New York City"; Yonkers also lands at 8.875% with a
    # different breakdown (state + Westchester + MCTD + Yonkers city).
    ("NY", "New York City (Manhattan)", "10001", "0001", "8.875", "0.05", "NY DTF Pub 718 (state 4% + NYC 4.5% + MCTD 0.375%)"),
    ("NY", "New York City (Bronx)", "10451", "0001", "8.875", "0.05", "NY DTF Pub 718 (Bronx County borough; same combined rate as Manhattan)"),
    ("NY", "New York City (Brooklyn)", "11201", "0001", "8.875", "0.05", "NY DTF Pub 718 (Kings County borough)"),
    ("NY", "New York City (Queens)", "11354", "0001", "8.875", "0.05", "NY DTF Pub 718 (Queens County borough)"),
    ("NY", "New York City (Staten Island)", "10301", "0001", "8.875", "0.05", "NY DTF Pub 718 (Richmond County borough)"),
    ("NY", "Buffalo", "14202", "0001", "8.750", "0.05", "NY DTF Pub 718 (state 4% + Erie 4.75%; no MCTD upstate)"),
    ("NY", "Rochester", "14604", "0001", "8.000", "0.05", "NY DTF Pub 718 (state 4% + Monroe 4%; no MCTD)"),
    ("NY", "Yonkers", "10701", "0001", "8.875", "0.05", "NY DTF Pub 718 (state 4% + Westchester 3% + MCTD 0.375% + Yonkers 1.5%)"),
    ("NY", "Syracuse", "13202", "0001", "8.000", "0.05", "NY DTF Pub 718 (state 4% + Onondaga 4%; no MCTD)"),
    ("NY", "Albany", "12207", "0001", "8.000", "0.05", "NY DTF Pub 718 (state 4% + Albany 4%; no MCTD)"),
    ("NY", "White Plains", "10601", "0001", "8.375", "0.05", "NY DTF Pub 718 (state 4% + Westchester 3% + MCTD 0.375% + White Plains 1%)"),
    ("NY", "Hempstead", "11550", "0001", "8.625", "0.05", "NY DTF Pub 718 (state 4% + Nassau 4.25% + MCTD 0.375%; no city tax)"),
    ("NY", "Brentwood", "11717", "0001", "8.625", "0.05", "NY DTF Pub 718 (state 4% + Suffolk 4.25% + MCTD 0.375%; no city tax)"),
    # Texas -- Texas Comptroller of Public Accounts "City Sales and Use
    # Tax Rates" + transit-authority publications (verified 2026-05-04).
    # Almost every major TX city lands at the 8.25% local cap; Arlington
    # is the famous DART/FWTA opt-out at 8.0%. Tolerance 0.05% to absorb
    # ZIP+4 micro-variation for special-purpose districts (TIF/MUD/etc.)
    # and the +4 "0001" centroid resolution.
    ("TX", "Houston", "77002", "0001", "8.250", "0.05", "TX Comptroller (state 6.25% + Houston 1.0% + METRO 1.0%)"),
    ("TX", "Dallas", "75201", "0001", "8.250", "0.05", "TX Comptroller (state 6.25% + Dallas 1.0% + DART 1.0%)"),
    ("TX", "Austin", "78701", "0001", "8.250", "0.05", "TX Comptroller (state 6.25% + Austin 1.0% + Capital Metro 1.0%)"),
    ("TX", "San Antonio", "78205", "0001", "8.250", "0.05", "TX Comptroller (state 6.25% + city 1.375% + VIA+ATD 0.625%)"),
    ("TX", "Fort Worth", "76102", "0001", "8.250", "0.05", "TX Comptroller (state 6.25% + city 1.5% + Trinity Metro 0.5%)"),
    ("TX", "El Paso", "79901", "0001", "8.250", "0.05", "TX Comptroller (state 6.25% + El Paso Co 0.5% + city 1.0% + Sun Metro 0.5%)"),
    ("TX", "Arlington", "76010", "0001", "8.000", "0.05", "TX Comptroller (state 6.25% + city 1.75%; opted out of DART/FWTA -- only major TX city below 8.25%)"),
    ("TX", "Plano", "75024", "0001", "8.250", "0.05", "TX Comptroller (state 6.25% + Plano 1.0% + DART 1.0%)"),
    ("TX", "Frisco", "75034", "0001", "8.250", "0.05", "TX Comptroller (state 6.25% + Frisco 2.0%; not a DART member)"),
    ("TX", "Lubbock", "79401", "0001", "8.250", "0.05", "TX Comptroller (state 6.25% + Lubbock 2.0%; no transit district)"),
    ("TX", "Amarillo", "79101", "0001", "8.250", "0.05", "TX Comptroller (state 6.25% + Amarillo 2.0%; no transit district)"),
    ("TX", "Garland", "75040", "0001", "8.250", "0.05", "TX Comptroller (state 6.25% + Garland 1.0% + DART 1.0%)"),
    ("TX", "Irving", "75038", "0001", "8.250", "0.05", "TX Comptroller (state 6.25% + Irving 1.0% + DART 1.0%)"),
    ("TX", "Corpus Christi", "78401", "0001", "8.250", "0.05", "TX Comptroller (state 6.25% + city 1.5% + RTA 0.5%)"),
    ("TX", "McAllen", "78501", "0001", "8.250", "0.05", "TX Comptroller (state 6.25% + McAllen 2.0%; Hidalgo Co. has no county tax)"),
    ("TX", "Round Rock", "78664", "0001", "8.250", "0.05", "TX Comptroller (state 6.25% + Round Rock 2.0%; not in Capital Metro)"),
    ("TX", "Midland", "79701", "0001", "8.250", "0.05", "TX Comptroller (state 6.25% + Midland 2.0%; no transit district)"),
    ("TX", "Wichita Falls", "76301", "0001", "8.250", "0.05", "TX Comptroller (state 6.25% + Wichita Falls 2.0%; no transit district)"),
    ("TX", "Tyler", "75701", "0001", "8.250", "0.05", "TX Comptroller (state 6.25% + Tyler 2.0%; no transit district)"),
    ("TX", "College Station", "77840", "0001", "8.250", "0.05", "TX Comptroller (state 6.25% + College Station 2.0%; no transit district)"),
    # Illinois -- IDOR Tax Rate Database / Tax Rate Finder (verified 2026-05-04).
    # Combined = state 6.25% + per-county + RTA (Cook 1.0% / Collar 0.75% / 0
    # downstate) + city home-rule. Tolerance 0.05% to absorb ZIP+4 micro-
    # variation for SSAs / business-improvement districts not modeled here.
    ("IL", "Chicago", "60601", "0001", "10.250", "0.05", "IDOR Tax Rate Finder (state 6.25% + Cook 1.75% + Chicago HR 1.25% + RTA Cook 1.00%)"),
    ("IL", "Cicero", "60804", "0001", "10.750", "0.05", "IDOR Tax Rate Finder (state 6.25% + Cook 1.75% + Cicero HR 1.75% + RTA Cook 1.00%)"),
    ("IL", "Evanston", "60201", "0001", "10.250", "0.05", "IDOR Tax Rate Finder (state 6.25% + Cook 1.75% + Evanston HR 1.25% + RTA Cook 1.00%)"),
    ("IL", "Aurora", "60505", "0001", "8.250", "0.05", "IDOR Tax Rate Finder (state 6.25% + Kane 0% + Aurora HR 1.25% + RTA Collar 0.75%)"),
    ("IL", "Naperville", "60540", "0001", "7.750", "0.05", "IDOR Tax Rate Finder (state 6.25% + DuPage 0% + Naperville HR 0.75% + RTA Collar 0.75%)"),
    ("IL", "Springfield", "62701", "0001", "9.500", "0.05", "IDOR Tax Rate Finder (state 6.25% + Sangamon 1.0% + Springfield HR 2.25%; no RTA downstate)"),
    ("IL", "Rockford", "61101", "0001", "8.750", "0.05", "IDOR Tax Rate Finder (state 6.25% + Winnebago 1.5% + Rockford HR 1.0%; no RTA downstate)"),
    ("IL", "Peoria", "61602", "0001", "9.000", "0.05", "IDOR Tax Rate Finder (state 6.25% + Peoria Co 1.0% + Peoria HR 1.75%; no RTA downstate)"),
]


@pytest.mark.liveapi
@pytest.mark.parametrize(
    ("state", "city", "zip5", "zip4", "expected", "tolerance", "source"),
    DOR_GRID,
    ids=[f"{r[0]}-{r[2]}-{r[3]}" for r in DOR_GRID],
)
def test_combined_rate_matches_dor(
    state: str,
    city: str,
    zip5: str,
    zip4: str,
    expected: str,
    tolerance: str,
    source: str,
) -> None:
    """Combined rate at this ZIP+4 should match the published DOR rate.

    Tolerance is 0.05% by default to absorb ZIP+4 micro-variation
    (e.g. some +4 ranges fall in additional special districts).
    """
    response = httpx.post(
        API,
        json={
            "address": {"zip5": zip5, "zip4": zip4},
            "line_items": [{"amount": "100.00"}],
        },
        timeout=10.0,
    )
    assert response.status_code == 200, f"engine HTTP {response.status_code}: {response.text}"
    data = response.json()
    got = Decimal(str(data["lines"][0]["rate_pct"]))
    expected_dec = Decimal(expected)
    tol = Decimal(tolerance)
    diff = abs(got - expected_dec)
    msg = (
        f"{state} {city} {zip5}-{zip4}: got {got}%, "
        f"expected {expected}% (+/- {tol}). source: {source}"
    )
    assert diff <= tol, msg
