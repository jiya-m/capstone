# Batch 4b: ART unit cost consistency (L-50), malaria and TB explanations

Follows Batch 3+4 (`batch34_evidence.md`). Rules: real citations only; labelled assumptions with ranges where no
evidence exists; never tune to a benchmark. Before snapshot: `audit/before_batch4b.csv` (local; commit `c1b0846`).

## Item 1: diagnosis of the ART cost per patient-year (no model change)

Script `audit/batch4b_art_check.py`, output `batch4b_art_check.csv` (one row per model country).

**The cost now used.** Site cost per patient-year (`art_site_cost`, 2023 US$, Batch 3+4 item 4) x 1 / (1 - 0.45) =
full cost. 7 countries have their own value (Kenya 354 from one GHCC record, 2016 prices, economic x 0.981; Uganda
371 from two GHCC records (2016) and Rosen 2021; Malawi 151, Eswatini 255, Zimbabwe 220, Lesotho 148, Zambia 141);
63 use the AFR median of those (220) or an income-group median (220). Full cost: 400 in 60 countries, 464 Eswatini,
274 Malawi, 270 Lesotho, 256 Zambia, **644 Kenya and 675 Uganda**.

**How US$675 got through the gate.** The item D gate ("every country ART cost between US$50 and US$600 per
patient-year") was applied to the site-level value before the markup (`audit/batch34_art_costs.py`, `LO, HI = 50,
600` on `site_cost`): Kenya 354 and Uganda 371 pass it, and the markup then takes them to 644 and 675. It was not
skipped and no range endpoint was used; the gate was enforced on a different metric from the one the model applies.
On the full cost, 2 of 70 countries fail the gate (Kenya, Uganda).

**Observed HIV treatment spending per person on ART** = total HIV spending x treatment-and-care share / people
receiving ART, in 2023 US$ (CPI-U annual averages, BLS: 2015 237.017, 2016 240.007, 2017 245.120, 2018-2023 as in
`health_model.CPI_U`):
- total HIV spending: ten Brink et al. 2025 appendix Table B2 (p. 8) for the 15 modelled Optima countries (most
  recent GAM year); otherwise WHO GHED `dis11_usd` (HIV/AIDS and other STDs, million current US$; latest year);
  available for 43 countries (Optima 14, GHED 29; Côte d'Ivoire has no UNAIDS ART count for 2022);
- treatment-and-care share: the country's Global Fund GC7 module share (`unspec_hiv_treatment`, Batch 3+4 item 2);
- people receiving ART: UNAIDS AIDSinfo 2026 estimates, "People receiving antiretroviral therapy", all ages,
  unrounded `Data value`, same year as the spending.

| Country | Full cost now (a) | Total HIV spending per person on ART | Treatment share (GF) | Observed treatment spending per person on ART (b) | (a) / (b) |
|---|---|---|---|---|---|
| Azerbaijan | 400 | 1,982 | 0.38 | 754 | 0.53 |
| Cambodia | 400 | 506 | 0.39 | 195 | 2.05 |
| Côte d'Ivoire | 400 | - | 0.45 | - (no 2022 ART count) | - |
| Dominican Republic | 400 | 1,524 | 0.03 | 51 | 7.80 |
| Eswatini | 463 | 635 | 0.13 | 80 | 5.77 |
| Kenya | 644 | 616 | 0.50 | 308 | 2.09 |
| Kyrgyzstan | 400 | 1,970 | 0.27 | 537 | 0.75 |
| Malawi | 274 | 305 | 0.65 | 199 | 1.38 |
| Moldova | 400 | 1,249 | 0.16 | 199 | 2.01 |
| Mongolia | 400 | 11,692 | 0.10 | 1,188 | 0.34 |
| Mozambique | 400 | 497 | 0.46 | 227 | 1.76 |
| South Africa | 400 | 307 | 0.11 | 35 | 11.49 |
| Tajikistan | 400 | 335 | 0.35 | 116 | 3.46 |
| Uganda | 675 | 560 | 0.56 | 314 | 2.15 |
| Zimbabwe | 400 | 252 | 0.51 | 129 | 3.10 |

Across the 43 countries with a value: (a) / (b) median 1.85 (IQR 1.14-3.07), above 1 in 35; by WHO region, median
(b) / (a) = AFR 0.50 (32 countries), AMR 1.66 (3), EMR 0.68 (1), EUR 0.92 (4), WPR 0.89 (3), SEA none. Per-country
values for all 70 countries are in the CSV.

**Reading.** In every large African programme the GHCC-based full cost is 1.4-3 times what is actually spent on
treatment and care per person on ART, and in Kenya and Uganda it is above the country's total HIV spending per
person on ART. The GHCC economic site costs (overheads, OI care, hospitalisation; 2015-2016 prices) plus the
programme-wide 47% non-service markup measure a fully loaded economic cost, not what a dollar of lost treatment money
buys. **Caveat on (b):** where the Global Fund grant funds little treatment, its module share understates the
treatment share of national spending: South Africa (0.11; ART is domestically financed), Dominican Republic (0.03),
Eswatini (0.13), Namibia (0.03), Niger (0.19), Mali (0.33) give (b) of US$29-80, below the price of the drugs. The
item 2 floor (first-line drugs plus viral load) catches these; the mismatch is recorded with the rule.

## Item 2: the rule now used (one commit)

**Rule.** ART cost per patient-year = the lower of (a) the GHCC-based full cost and (b) the observed treatment
spending per person on ART (item 1); where (b) is unavailable (27 countries), (a) x the WHO-region median of (b)/(a)
(AFR 0.50, EUR 0.92, WPR 0.89, EMR 0.68, AMR 1.66 so (a) itself; SEA has none, so the overall median 0.54). Floor:
first-line drugs plus one viral load test a year = "a first-line HIV treatment for under US$45 per person, per year"
(Global Fund news release, "Global Fund agreements substantially reduce the price of first-line HIV treatment to below
US$45 a year", 30 August 2023; TLD) + viral load at the "global access price from Roche of US$9.40 per test" (CHAI,
Case Study: Viral Load Access, 2015; 2015 US$ x 304.702 / 237.017 = 12.08) = **US$57.08** (2023 US$; one test a year
per WHO's routine monitoring schedule, an assumption about frequency). Gate US$50-600 on the final value (no country
touches it). Reason: concept match, the model needs what a dollar of lost treatment money pays for per patient.
Implementation: `country_inputs.csv` `art_cost_full` (+ `_lo`, `_hi`, `_source`), written by `batch34_inputs.py
--art-full` from `batch4b_art_check.csv`; `health_model.unit_costs` uses it without applying the markup again.

**Result** (2023 US$ per patient-year): median 274 (57-400). From observed spending: 43 countries, of which the
GHCC-based value was the lower in 8 (Nigeria 400 vs 569, Azerbaijan, Kyrgyzstan, Mongolia, Guyana, Haiti, Liberia,
Madagascar); floored: South Africa (35 -> 57) and the Dominican Republic (51 -> 57), where the Global Fund treatment
share (0.11, 0.03) understates the national treatment share. Kenya 308 (was 644), Uganda 314 (675), Mozambique 227
(400), Malawi 199 (274), Zimbabwe 129 (400), Eswatini 80 (463), India 216 (400, regional ratio).

**Monte Carlo range.** `uc_art_mult` keeps 0.68-1.38: below 1 the draw scales the value down (the spread of the cost
studies, Batch 3+4); above 1 it moves the value toward `art_cost_full_hi` = the higher of (a) and (b) capped at 600,
reaching it at 1.38 (Kenya 308 -> 600, Mozambique 227 -> 400, South Africa 57 -> 400). The central therefore sits
inside the displayed range.

**Effect** (Full US Exit, all countries, central): deaths 2026-30 1,379,963 -> 1,648,665 (+19.5%); HIV deaths
669,366 -> 938,069 (+40%); HIV infections 2.80M -> 3.79M; people who stop ART 3,184,530 -> 4,563,706 (+43%); TB,
malaria and vaccines unchanged. HIV baseline only rebuilt (83 entries; 13 lives-first entries also moved other lines
through the refill order). `--quick`: 0 failures, 6 known warnings.
