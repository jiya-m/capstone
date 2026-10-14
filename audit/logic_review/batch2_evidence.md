# Batch 2, Step 1: evidence and proposed values for the ART death risk and HIV transmission (L-01, L-41)

Decision already made: **Option A.** "People losing ART" stays the count of people who stop ART (full-cost
equivalents of the lost money, all donors, all countries). The death risk, re-engagement and transmission are
recalibrated so that they describe people who have actually stopped ART. No model code changes in this step.

Scripts (both read-only with respect to the model): `audit/batch2_cohort.py` (Step 1A cohort calculation, output
`batch2_cohort.csv`) and `audit/batch2_projection.py` (Step 1C rates, `batch2_transmission.csv`; Step 1D projection,
`batch2_projection.csv` and `batch2_optima_compare.csv`). Before snapshot of every displayed number:
`audit/before_batch2.csv` (local; the projection's "current" variant reproduces it to 1e-12).

## A. Death risk after stopping ART

### What the model does now

`ART_HAZARD = [0.012, 0.028, 0.038, 0.045, 0.050]` x `art_hazard_mult` (1, range 0.6-1.5): excess deaths per
person-year in years 1-5 off ART, 17.3% over five years; the year-5 value is used after 2030. The parameter file
says it was set from Optima and UNAIDS totals divided by the 20.6M people at PEPFAR-supported sites, which is the
concept mismatch in L-01.

### Cohort calculation (`audit/batch2_cohort.py`)

Five CD4 stages (>500, 350-500, 200-350, 50-200, <50). On stopping ART people progress at untreated rates and die at
untreated stage-specific rates; the counterfactual keeps them on suppressive ART at the relative death rate.

| Input | Value (range) | Source |
|---|---|---|
| Years to move >500 to 350-500; 350-500 to 200-350; 200-350 to 50-200; 50-200 to <50 | 0.95 (0.62-1.16); 3.00 (2.83-3.16); 3.74 (3.48-4.00); 1.50 (1.13-2.25) | ten Brink et al. 2025, *Lancet HIV*, appendix Table A1, "Disease progression (average years to move)", p. 2 |
| HIV death rate per year, untreated, by stage >500; 350-500; 200-350; 50-200; <50 | 0.36% (0.29-0.44); 0.58% (0.48-0.71); 0.88% (0.75-1.01); 5.9% (5.4-7.9); 32% (29.6-43.2) | same appendix, Table A2, "Death rate (% HIV-related mortality per year)", p. 3 |
| Relative death rate on ART with viral suppression | 23% (15-30) | Table A2, p. 3 |
| Starting CD4 distribution of people on ART: >500 53%, 350-500 22%, 200-350 20%, <200 5% (split 4% / 1% between 50-200 and <50, an assumption) | men: 32 / 28 / 30 / 10%; women: 64 / 20 / 13 / 3% | ZIMPHIA 2020 final report (MOHCC / ICAP, 2023), Table 10.1 "Median CD4 count by HIV diagnosis and antiretroviral therapy status", p. 89, row "Aware of HIV status and on ART": Men "411 (282, 558)", n 748; Women "603 (437, 768)", n 1,794; Total "528 (366, 706)", range 2-1730, n 2,542 (median (Q1, Q3) cells per microliter). Summary on p. 16: "The median CD4 count was 327 cells per microliter (µL) among those who were unaware of their status, 320 cells/µL among those who were aware of their status but not yet on ART, and 528 cells/µL among those who were taking ART." Shares interpolated within quartiles |

Cross-checks on the starting distribution: pooled PHIA surveys 2016-21 (13 countries) give CD4 <200 in 4.3% of
virally suppressed adults and 29.5% of adults on ART but not suppressed (Stelzle et al. 2025, *Lancet Global Health*
13:e437-e446, Findings); seven PHIA countries 2019-23: 4.9% among adults aware and on ART, down from 10.5% in
2015-17 (West et al. 2026, *Open Forum Infect Dis* 13:ofaf753, Results). So about 5% below 200 is right for people
on ART; one country's quartiles (Zimbabwe) set the bands above 200. No multi-country source for those bands was
found (IeDEA reports CD4 at initiation only: de Waal et al. 2025, *Clin Infect Dis* 80:1332-1336: CD4 <200 at
first ART initiation plateaued at 30% or more after 2015).

**Result: excess death probability by year since stopping ART** (share of the starting cohort; Optima central;
ranges = Optima low/high rates, and the men's / women's distributions):

| Year off ART | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 5-yr cum. | 10-yr cum. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Proposed central** (total distribution) | 1.3% | 2.5% | 3.7% | 4.9% | 6.0% | 6.8% | 7.2% | 7.3% | 7.1% | 6.7% | **18.4%** | 53.6% |
| Optima low rates | 1.0 | 1.8 | 2.8 | 3.8 | 4.8 | 5.6 | 6.1 | 6.4 | 6.5 | 6.4 | 14.2 | 45.3 |
| Optima high rates | 2.0 | 3.6 | 5.4 | 6.9 | 8.0 | 8.6 | 8.6 | 8.2 | 7.5 | 6.7 | 26.0 | 65.4 |
| Men's distribution, central | 2.1 | 3.6 | 4.9 | 6.0 | 6.8 | 7.2 | 7.3 | 7.1 | 6.7 | 6.2 | 23.4 | 57.9 |
| Women's distribution, central | 1.0 | 1.9 | 3.1 | 4.3 | 5.6 | 6.5 | 7.1 | 7.4 | 7.3 | 7.0 | 15.8 | 51.1 |
| Widest (women + low; men + high) | 0.7-3.1 | 1.4-5.2 | 2.3-6.9 | 3.3-8.0 | 4.3-8.6 | | | | | | 12.0-31.7 | 42.7-68.9 |
| Current ART_HAZARD | 1.2 | 2.8 | 3.8 | 4.5 | 5.0 | (5.0) | (5.0) | (5.0) | (5.0) | (5.0) | 17.3 | 42.3 |

The five-year total is close to the current value (18.4% vs 17.3%), so the current numbers were not far off for
people who actually stop; the concept and the source text were wrong, and the risk keeps rising after year 5 (the
model now holds it at 5%). About a quarter of the cohort is below 200 cells/µL after five years off ART.

### Direct empirical evidence on mortality after ART interruption

| Study | Finding | Comparison with the cohort calculation |
|---|---|---|
| Brinkhof, Pujades-Rodriguez & Egger 2009, *PLoS One* 4:e5790 (meta-analysis, 17 tracing studies, 6,420 patients lost to follow-up) | "The combined mortality was 40% (95% CI 33%-48%)"; "among those traced 20% to 60% had died" (Results; Conclusions) | Higher. The patients were lost in 2000-2007, started ART with low CD4, and the traced group is enriched for deaths (the untraceable are more often alive and transferred) |
| Zürcher et al. 2017, *Trop Med Int Health* 22:375-387 (32 studies, 20,365 lost, 77.1% found) | Predicted mortality among traced patients fell "from around 56% in 2003 to 24% in 2011" (Results, meta-regression); aOR 0.86 per calendar year; treatment interruptions rising (aOR 1.31 per year) | Falling toward the cohort values as starting CD4 rises |
| Holmes et al. 2018, *PLoS Med* 15:e1002489 (Zambia, 4 provinces, 2013-15, sampling-based tracing) | Of those selected for tracing, 1,007 found alive without a care disruption, 412 had died, 932 could not be traced (29% of those with known status had died); corrected 2-year mortality on ART 7.0%; being lost (>90 days late) associated with death | Higher than the cohort values, but the lost group includes people lost because they were dying, with median CD4 201 at ART start |
| Kaplan et al. 2017, *PLoS Med* 14:e1002407 (Khayelitsha, 2013-14, 9,005 disengaged >180 days) | After a median 16.7 months, 3% had died, 33% had returned to care, 25% were alive and not in care; among those with identification numbers, more than 90% were alive at the end of follow-up | Consistent with 1-2% a year in the first two years for a contemporary, higher-CD4 population |
| SMART 2006, *N Engl J Med* 355:2283-2296 (CD4-guided interruption, CD4 >350, high-income settings) | Opportunistic disease or death 3.3 vs 1.3 per 100 person-years (HR 2.6) | Excess 2 events per 100 person-years with re-initiation below 250 cells: the same order as years 1-2 |
| Trivacan (Danel et al. 2006, *Lancet* 367:1981-1989; Abidjan, nadir CD4 272) | Mortality 1.2 vs 0.6 per 100 person-years (not significant); severe morbidity 2.5x | Same order as year 1 |
| Moolla et al. 2024, *AIDS* 38:1198-1205 (IeDEA Southern Africa, 63,692 adults) | Mortality after resuming ART: HR 4.37 (early interrupters), 2.74 (late) vs no interruption | Risk persists after return; the model does not count it (noted, not proposed) |

**Proposal A.** Replace `ART_HAZARD` with the cohort-calculation values for years 1-10 (years 6-10 used after
2030 for people still off care, instead of the year-5 value). Keep `art_hazard_mult` as the Monte Carlo range,
central 1, **range 0.65-1.7** (women + Optima low to men + Optima high, as multiples of the central 18.4%). Source
text: Optima Tables A1-A2 with the ZIMPHIA 2020 starting distribution.

## B. Re-engagement after 2030 (`art_reengage`)

| Study | Setting | Finding |
|---|---|---|
| Kranzer et al. 2010, *J Acquir Immune Defic Syndr* 55:e17-23 | Primary care ART programme, South Africa, 2004-09 (defaulting = all ART stopped >30 days) | Abstract, Results: "Overall rate of defaulting treatment was 12.8 per 100 person-years (95% confidence interval: 11.4 to 14.4)"; "The probability of resuming therapy within 3 years of defaulting therapy was 42% (event rate = 21.4 per 100 person-years)"; Conclusions: "Resumption of treatment is most likely within the first year of interrupting therapy." |
| Kaplan et al. 2017, *PLoS Med* 14:e1002407 | Khayelitsha, 2013-14 (disengagement = >180 days not attending) | Abstract: "Of the 9,005 who disengaged, the 2 most common initial outcomes were return to ART care after 180 days (33%; n = 2,976) and being alive but not in care in the Western Cape (25%; n = 2,255). After disengagement, a total of 1,459 (16%) patients were hospitalized and 237 (3%) died. The median follow-up from date of disengagement to 30 June 2015 was 16.7 months (IQR 11-22.4)." Results: "A Kaplan-Meier analysis of time to returning to care for patients who disengaged estimated that approximately 50% of patients who disengage will return to care by 2.5 years (S4A Fig)." |
| Mody et al. 2026, *PLoS Med* 23:e1005052 | Zambia, 24 clinics, Aug 2019-Nov 2021, treatment interruption = >30 days late for a scheduled visit | Abstract, Methods and findings: "During the study period, 128,910 clients (n = 69,671 control, n = 59,239 intervention) became >30 days late (64.3% female, median age 38y [IQR 31,45], median years in care 2.5y [IQR 0.6,6.7]). The PCC intervention increased incidence of return after TI at 12-months (72.3% intervention versus 67.7% control, crude risk difference [RD] +4.6% [CI 4.1,5.2], adjusted hazard ratio [aHR] 1.16 [CI 1.12,1.20]" |
| Zürcher et al. 2017 (above) | Sub-Saharan Africa, traced patients | Share found alive with ART interrupted rising over time (aOR 1.31 per year) |

Implied yearly return rates: 0.17 (Kranzer), about 0.3 (Kaplan: half by 2.5 years), 0.68 (Mody, but a >30-day
definition, so it includes short gaps). These are individual disengagements while services continue. The model's
case is different: services were withdrawn and return in 2031; return could be faster (supply-driven) or slower
(people have died, moved, or lost contact; clinics closed). No study of return after a programme-wide stoppage was
found.

**Proposal B.** `art_reengage` central **0.35** a year (range **0.17-0.68**, the span of the three cohorts), status
"sourced (indirect)". Current: 0.5 (0.25-0.75, assumption).

## C. Transmission (`art_transmission`)

### Concept-matched rate from UNAIDS 2025 (`batch2_transmission.csv`)

Rate = new HIV infections (all ages, 2025) / people with unsuppressed viral load (all ages, 2025), where the
denominator = people living with HIV minus people with suppressed viral load (UNAIDS AIDSinfo 2026 estimates,
unrounded `Data value`, Area Level 2; the "People with unsuppressed viral load" indicator itself is a percentage of
the adult population, so it is not used). A person who stops ART becomes a person with unsuppressed viral load.

| Statistic (model countries with data, n = 51) | Value |
|---|---|
| Median | **0.118** infections per unsuppressed person-year |
| Interquartile range | 0.085-0.131 |
| Min, max | 0.061 (Djibouti), 0.308 (Botswana) |
| Regional medians (WHO region) | AFR 0.120 (28 countries), AMR 0.111, EMR 0.102, EUR 0.115, SEA 0.107, WPR 0.156 |
| Focus countries | Kenya 0.070, Nigeria 0.122, Mozambique 0.130, South Africa 0.077, Uganda 0.125 |
| Missing (fallback = regional median): 20 countries | AGO, CAF, CIV, COD, FJI, GTM, IRQ, JAM, JOR, KGZ, MDG, MLI, MNG, NIC, PAK, PNG, SEN, SOM, SSD, VEN |
| UNAIDS infection bounds as multiples of the central rate (median across countries) | 0.71-1.38 |

Current value 0.04 is a third of the median. Cross-check: among serodiscordant couples with an untreated index
partner, 2.24 linked transmissions per 100 person-years (Donnell et al. 2010, *Lancet* 375:2092-2098; figure as
reported in a conference summary of the paper, not verified against the article). A couple-level rate is lower than
a population rate because it counts one partner only.

Two offsetting differences between a person who stops ART and the average unsuppressed person: the population
average includes newly infected people, who transmit 5.6x more during acute infection (Optima Table A1, p. 2) and
are over-represented in it; people who stop ART at low CD4 transmit 3.5-7x more (Table A1, CD4 50-200 and <50).
Neither is quantified here; the country rate is used as is.

**Proposal C1.** `art_transmission` becomes the country's UNAIDS rate (regional median where missing), stored in
`country_inputs.csv`, times a Monte Carlo multiplier `art_transmission_mult` central 1, range **0.71-1.38** (UNAIDS
infection bounds). `ART_INFECT_LAG` (half in year 1) kept.

### Onward infections within 2026-2030

Options: (i) first generation only (people who stopped ART infect others); (ii) first plus second generation (the
people they infect are undiagnosed and unsuppressed, and transmit at the same rate until suppressed).

The rate above is a ratio of all new infections to all unsuppressed people, so it is only concept-consistent if the
newly infected are also counted as unsuppressed while they are. Time to suppression: median time from infection to
diagnosis in sub-Saharan Africa 2.6 years (1.8-3.5) in 2020 (Giguère et al. 2021, *Lancet HIV* 8:e284-e293,
Shiny90 model), plus linkage and the 0.2 years to suppression (Optima Table A2). With an exponential wait, mean =
median / ln 2, so about 4 years (2.5-5.5); under a funding collapse testing and initiation also fall, which argues
against a shorter value. Third and later generations are left out (each adds about a quarter of the previous one
within the window and would need an epidemic model).

**Recommendation: (ii) first plus second generation**, with `hiv_new_inf_unsup_years` = **4 (2.5-5.5)** as a
labelled assumption, because (i) under-counts by construction once the rate is defined per unsuppressed person,
and because the Optima and UNAIDS totals that L-41 compares against are epidemic-model outputs that include onward
transmission. The second generation adds 20% to off-ART infections over 2026-2030 (and more after 2030).

## D. Benchmark (projection under the proposed values, Full US Exit, central, all countries)

`audit/batch2_projection.py`, 2026-2030, sudden cut, no government response:

| Variant | All-disease deaths | HIV deaths | of which ART line | HIV infections | of which off-ART | Further deaths 2031-35 |
|---|---|---|---|---|---|---|
| Current | 1,965,386 | 1,006,114 | 929,704 | 1,552,704 | 954,667 | 495,218 |
| A + B (hazard, re-engagement) | 2,023,727 | 1,064,455 | 988,045 | 1,552,704 | 954,667 | 789,449 |
| + C1 (country transmission) | 2,050,194 | 1,090,922 | 1,014,512 | 3,617,848 | 3,019,811 | 932,964 |
| **+ C2 (second generation) = proposed** | **2,055,584** (+4.6%) | **1,096,312** (+9%) | 1,019,902 | **4,343,196** (x2.8) | 3,745,159 | **983,835** (x2.0) |

Focus countries (current -> proposed): HIV deaths Kenya 88,232 -> 94,069; Nigeria 81,636 -> 89,097; Mozambique
96,114 -> 104,180; South Africa 122,376 -> 131,107; Uganda 74,753 -> 80,631. HIV infections Kenya 116,658 ->
193,160; Nigeria 94,044 -> 303,975; Mozambique 165,675 -> 422,675; South Africa 273,599 -> 416,478; Uganda 121,296
-> 297,225.

**Optima** (ten Brink et al. 2025, appendix Table C2, p. 11; cumulative 2025-2030, scenario minus status quo), 15
overlapping countries (`batch2_optima_compare.csv`):

| | Optima S4 (PEPFAR discontinued, mitigation) | Optima S5 (no mitigation) | Model now | Model proposed |
|---|---|---|---|---|
| HIV deaths | 403,560 | 1,365,370 | 525,023 | 565,873 |
| HIV infections | 2,261,420 | 5,082,860 | 895,529 | 1,869,177 |

All-LMIC extrapolation (Table C3, p. 12): 0.77-2.93M deaths and 4.43-10.75M infections. **UNAIDS**: "if the
funding permanently disappears, there could be an additional 6 million HIV infections and an additional 4 million
AIDS-related deaths by 2029" (UNAIDS, *AIDS, Crisis and the Power to Transform*, 2025 Global AIDS Update, Foreword,
p. 3).

**The gap and why it remains.** The proposed values move infections to the Optima S4-S5 band for the overlapping
countries and to 4.3M for all countries (UNAIDS 6M); deaths stay between Optima S4 and S5 in the overlap and at a
quarter of the UNAIDS figure. The remaining gap is the number of people who stop ART, which Option A keeps:

- Full-cost equivalents are a small share of people on ART where PEPFAR pays a large share of HIV spending. Optima
  Table B2 (p. 8) gives PEPFAR's share of total HIV expenditure: Mozambique 66%, Uganda 65%, Malawi 60%, Zimbabwe
  57%, Côte d'Ivoire 56%, Eswatini 42%, Kenya 26%, South Africa 21%. The model's people stopping ART as a share of
  people on ART: Mozambique 23%, Uganda 28%, Malawi 45%, Zimbabwe 13%, Côte d'Ivoire 56%, Eswatini 35%, Kenya 33%,
  South Africa 11%. Optima's scenario 5 drops ART initiations to zero and lets retention fall toward the share of
  treatment PEPFAR funds (appendix scenario notes, p. 10-11); dividing the lost money by the full cost per
  patient-year (which includes domestic inputs) and netting out the non-service share gives fewer people.
- Optima counts six years (2025-2030) and a dynamic epidemic (prevention cuts, more unsuppressed people raising
  incidence for everyone); UNAIDS counts 2025-2029 for all countries and assumes the full loss of PEPFAR-supported
  services.
- Neither benchmark is a target. The proposed values were set from the evidence above and were not adjusted to
  these totals.

## Decisions where the evidence is weak (one line each)

- Starting CD4 bands above 200 cells come from one country's quartiles (ZIMPHIA 2020); the split of the <200 share
  into 50-200 and <50 is an assumption; the men/women distributions set the range.
- Optima progression rates are natural-history rates; after an interruption CD4 falls faster at first (SMART), so
  years 1-2 may be understated; the tracing studies (24-40% dead) are higher but from sicker, earlier cohorts.
- Re-engagement rates come from individual disengagement while services ran, not from a programme restart in 2031.
- The transmission rate is a population average (acute-stage and low-CD4 effects not separated); 20 countries use
  the regional median; the second generation needs an assumed 4 years (2.5-5.5) to suppression.
- Persisting excess mortality after return to care (Moolla 2024) is not modelled.

## Proposed value table

| Parameter | Current | Proposed central | Range | Source with page |
|---|---|---|---|---|
| ART death risk, years 1-5 off ART (then 6-10 after 2030) | 1.2, 2.8, 3.8, 4.5, 5.0% (5.0% after) | 1.3, 2.5, 3.7, 4.9, 6.0%; then 6.8, 7.2, 7.3, 7.1, 6.7% | via `art_hazard_mult` 0.65-1.7 | Optima appendix Tables A1 (p. 2), A2 (p. 3); ZIMPHIA 2020 Table 10.1 (p. 89); checks: Stelzle 2025, West 2026, Brinkhof 2009, Zürcher 2017, Holmes 2018, Kaplan 2017, SMART 2006 |
| `art_hazard_mult` | 1 (0.6-1.5), "calibrated" | 1 | 0.65-1.7 | cohort calculation ranges (`batch2_cohort.csv`) |
| `art_reengage` (per year, 2031-35) | 0.5 (0.25-0.75), assumption | 0.35 | 0.17-0.68 | Kranzer 2010 (JAIDS 55:e17, Results); Kaplan 2017 (PLoS Med 14:e1002407, Results, S4A Fig); Mody 2026 (PLoS Med 23:e1005052, Findings) |
| `art_transmission` (infections per person-year off ART) | 0.04 (0.02-0.08) | country rate, median 0.118 (IQR 0.085-0.131); regional median where missing | `art_transmission_mult` 1 (0.71-1.38) | UNAIDS AIDSinfo 2026 estimates (2025): New HIV Infections / (PLHIV - suppressed), Area Level 2, unrounded |
| Onward infections | first generation only | first + second generation | `hiv_new_inf_unsup_years` 4 (2.5-5.5), assumption | Giguère 2021 (Lancet HIV 8:e284, median time to diagnosis 2.6 years in 2020); Optima Table A2 (0.2 years to suppression) |
| Old values | | kept behind `hiv_legacy_art_params` = 0 (default off) as a sensitivity check | | |
