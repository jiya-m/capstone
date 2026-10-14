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
