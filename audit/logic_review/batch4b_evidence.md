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

## Item 3: why malaria deaths fell 61% in Batch 3+4, and one concept mismatch fixed

Script `audit/batch4b_malaria_decomp.py` (each Batch 3+4 commit run in its own worktree), output
`batch4b_malaria_decomp.csv`. Full US Exit, all countries, central, malaria deaths 2026-30:

| State | Bednets | Spraying | Case management | Malaria total | Change |
|---|---|---|---|---|---|
| Before (`cd42746`) | 175,800 | 5,216 | 188,409 | 369,425 | |
| Item 1 (systems money not converted) | 154,380 | 4,452 | 156,241 | 315,073 | -14.7% |
| Item 2 (unspecified money by purpose) | 148,831 | 4,299 | 123,822 | 276,952 | -12.1% |
| Items 4, 5 (ART, TB costs) | 148,831 | 4,299 | 123,822 | 276,952 | 0 |
| Item 6 (donor-funded pool cap) | 57,955 | 2,178 | 83,756 | 143,889 | -48.0% |
| Item 7 (continuity range only) | 57,955 | 2,178 | 83,756 | 143,889 | 0 |

Items 1 and 2 act through money: effective malaria service money fell from US$489M to US$376M a year (bednets 260
to 214, spraying 62 to 51, case management 167 to 111) because systems money (14% of effective malaria money) is no
longer converted and the Global Fund malaria mix sends 22% of unspecified money to case management and 48% to vector
control instead of the known-line mix (40% to case management). **Item 6 is the driver**: the donor-funded pool
became people covered x the external share of malaria spending (GHED, median 0.25), which binds in 37 bednet, 61
spraying and 49 case-management lines. The five largest malaria countries (before the batch):

| Country | Bednet deaths: before -> item 2 -> item 6 | Case-management deaths: before -> item 2 -> item 6 | External share used (all-source) |
|---|---|---|---|
| Nigeria | 34,146 -> 32,806 -> 1,465 | 27,942 -> 16,643 -> 5,105 | 0.03 |
| DR Congo | 24,830 -> 19,035 -> 12,365 | 14,992 -> 11,733 -> 11,688 | 0.42 |
| Tanzania | 10,130 -> 8,564 -> 3,359 | 22,938 -> 17,560 -> 7,940 | 0.16 |
| Niger | 20,278 -> 17,686 -> 11,155 | 8,080 -> 4,392 -> 4,381 | 0.22 |
| Madagascar | 6,028 -> 4,109 -> 4,106 | 12,508 -> 6,106 -> 6,105 | 0.50 |

**Concept check 1 (asked): systems and programme-management shares.** The share of malaria money classed as
systems or programme management is, by construction, the Global Fund GC7 malaria module share (RSSH median 14%,
programme management 15%; Nigeria 7% and 7%, Kenya 4% and 8%, Uganda 2% and 3%), applied only to IHME's
unspecified malaria money; IHME's own `mal_hss_*` lines are systems money in both. No mismatch there.

**Concept check 2 (found): the cap share for bednets and spraying.** GHED's all-source malaria total includes
household spending on treatment (private share median 35%; Nigeria 87%, Benin 87%, Cameroon 76%, Mali 75%). Dividing
donor malaria funding by that total gave Nigeria an external share of 3%, so the pool of donor-funded net users was
3% of the people covered although campaign nets are financed by donors and governments, not households. **Fix
(commit `7342148`):** bednets and spraying use the external share of *public* malaria spending, external / (external
+ domestic government) (GHED `dis13_ext_usd`, `dis13_gghed_usd`; median 0.56, Nigeria 0.22, DR Congo 0.77, Tanzania
0.22, Niger 0.50, Madagascar 0.74; WHO-region median where missing). Case management keeps the all-source share
(households do pay for treatment). Malaria baseline only rebuilt (84 entries: bednets, spraying and, through the
Lives Saved Tool interaction, case management). Result: malaria deaths 143,889 -> 190,824 (+33%; Nigeria bednets
1,465 -> 11,221, DR Congo 12,365 -> 19,033, Tanzania 3,359 -> 4,569, Niger 11,155 -> 17,654). Headline 1,648,665 ->
1,695,601. `--quick`: 0 failures. The same all-source-vs-public question applies to HIV (private share median 8%;
Nigeria 67%, Guinea 49%, Senegal 44%; `dis11` is HIV *and other STDs*) and immunization; it is outside this item's
scope and recorded as open finding L-51.

## Item 4: TB (no model change)

Full US Exit, central, 2023 US$ (provider cost per course before the 1.818 markup; "full" = after it):

| Country | Income group | DS course old -> new | DR course old -> new | RR share of incidence (was 4%) | RR enrolment (was 45%) | RR weight among notified | WHO 2025 budget per expected patient | Blended full cost new | Ratio |
|---|---|---|---|---|---|---|---|---|---|
| Kenya | lower-middle | 351 -> 150 | 8,125 -> 2,818 | 1.3% | 47% | 0.4% | 1,377 | 297 | 4.6 |
| Nigeria | lower-middle | 351 -> 135 | 8,125 -> 2,818 | 1.9% | 38% | 0.8% | 1,049 | 283 | 3.7 |
| Mozambique | low | 332 -> 275 | 1,568 -> 1,568 | 2.9% | 37% | 1.1% | 336 | 534 | 0.6 |
| South Africa | upper-middle | 1,081 -> 274 | 6,800 -> 9,256 | 5.6% | 47% | 3.7% | 1,042 | 1,084 | 1.0 |
| Uganda | low | 332 -> 275 | 1,568 -> 1,568 | 1.0% | 68% | 0.6% | 589 | 522 | 1.1 |
| India | lower-middle | 351 -> 105 | 8,125 -> 2,818 | 4.9% | 40% | 1.8% | 278 | 293 | 0.9 |

(WHO 2024 expenditure per notified patient: Kenya 448, Nigeria 272, Mozambique 291, South Africa 410, Uganda 367,
India 192, nominal US$.) Before the batch, Full US Exit TB treatment lines lost (patients a year, 2023 US$ full
cost): Kenya 9,862 at 638, Nigeria 20,380 at 638, Mozambique 31,573 at 604, South Africa 12,056 at 1,965, Uganda
11,536 at 604, India 5,987 at 638.

**Source of the +91% (item 5, 277,104 -> 530,032).** Re-running the final model with the old income-group costs
restored gives TB deaths 265,626 (DS 258,465 + DR 7,161) against 463,973 now (DS 454,066 + DR 9,907); re-running it
with the global 4% / 45% RR constants restored gives 465,978. So the rise is the lower course costs (more patients
per lost dollar), with the country RR shares and enrolment worth -2,000 deaths. Nothing else changed in item 5. The
new DS costs are facility-level bottom-up financial costs (Value TB) and GHCC South Africa; whether they are low for
the model's purpose is the same concept question as the ART cost in item 1 (what a dollar of lost treatment money
buys): the WHO national programme budget per expected patient is 3.7-4.6 times the blended full cost in Kenya and
Nigeria and 0.6-1.1 times it in the other four.

## Updated reconciliation (15 Optima countries; before = `audit/before_batch4b.csv`, after = this batch)

| Country | GAM year | People on ART (outside PMTCT) | PEPFAR share of HIV spending | All international share | Model share who stop: before | after | ART full cost/yr: before | after | Cap: external HIV share | Optima HIV spending per person on ART | Donor ART aid exceeds the pool |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AZE | 2023 | 9,654 | 0% | 14% | 3% | 3% | $400 | $400 | 0.50 | $1,530 | no |
| KHM | 2022 | 71,656 | 15% | 64% | 2% | 3% | $400 | $195 | 0.84 | $441 | no |
| CIV | 2022 | 166,102 | 56% | 12% | 40% | 45% | $400 | $200 | 0.72 | $1,084 | yes |
| DOM | 2022 | 56,616 | 34% | 42% | 30% | 41% | $400 | $57 | 0.59 | $1,288 | yes |
| SWZ | 2019 | 192,925 | 42% | 59% | 19% | 46% | $463 | $80 | 0.61 | $529 | yes |
| KEN | 2022 | 1,326,509 | 26% | 37% | 14% | 28% | $644 | $308 | 0.67 | $576 | no |
| KGZ | 2023 | 7,502 | 17% | 71% | 16% | 16% | $400 | $400 | 0.50 | $1,669 | yes |
| MWI | 2022 | 859,919 | 60% | 95% | 29% | 40% | $274 | $199 | 0.70 | $302 | no |
| MDA | 2023 | 9,039 | 0% | 45% | 0% | 0% | $400 | $199 | 0.04 | $1,176 | yes |
| MNG | 2021 | 265 | 0% | 52% | 4% | 4% | $400 | $400 | 0.59 | $9,331 | yes |
| MOZ | 2019 | 1,992,180 | 66% | 96% | 15% | 26% | $400 | $227 | 0.84 | $280 | no |
| ZAF | 2023 | 5,899,725 | 21% | 24% | 8% | 8% | $400 | $57 | 0.10 | $316 | yes |
| TJK | 2023 | 11,885 | 0% | 0% | 21% | 20% | $400 | $116 | 0.57 | $295 | yes |
| UGA | 2020 | 1,177,947 | 65% | 80% | 14% | 30% | $675 | $314 | 0.78 | $458 | no |
| ZWE | 2023 | 1,194,700 | 57% | 89% | 13% | 40% | $400 | $129 | 0.96 | $260 | no |

Weighted (by people on ART) share who stop: before 12.8%, after 21.0%; PEPFAR share 39.1%; all international 52.7%

The batch moved the model's share who stop from 13% to 21% (weighted by people on ART), back to where it was before
Batch 3+4, against PEPFAR's 39% share of spending and 53% for all international funding. The remaining gap is the
money that buys no people (systems, programme management, the non-treatment shares of unspecified money, half of
testing and care), continuity (15%), the cap (binding now in Eswatini, Côte d'Ivoire, Dominican Republic, South
Africa, Tajikistan and the small programmes) and the 23% Global Fund cut; the cost term no longer exceeds what the
countries spend.
