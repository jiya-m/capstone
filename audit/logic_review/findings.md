# Logic and evidence review: findings and recommendations

**Branch:** `real-modeling-check`.
**Code reviewed:** commit `a6a4871` (after the cleanup merge); the review files were added on top.
**Rules:** read-only. No model, data or app code was changed.

## Files

| File | Part |
|---|---|
| `findings.md` | 10. This file |
| `URGENT.md` | Critical findings L-01 and L-41 (pushed as found: `12e15a9`, `88bb1b6`) |
| `inputs.csv`, `inputs.md`, `build_inputs.py` | 1. Input review (98 inputs) |
| `assumptions.md`, `sensitivity.py`, `sensitivity.csv`, `tornado.py`, `tornado.png` | 2. Assumptions, evidence and one-at-a-time sensitivity |
| `logic.md` | 3. Logic chain, as plain math with `file:line` |
| `uncertainty_scope.md` | 4. Uncertainty, scope omissions, reproducibility |
| `dashboard.md` | 5. Independent reproduction, labels, consistency, surprising results, claims |
| `benchmarks.md` | 6. External benchmarks |
| `redteam.md`, `redteam_report.md` | 7. Independent red-team review and reconciliation |
| `data_requests.md` | 8. Data requests, with download steps |
| `improvements.md` | 9. Improvements, ranked and sequenced |
| `coverage.md` | 11. Coverage table |
| `reproduction/` (independent `repro.py`, `notes.md`, outputs, cell-by-cell comparison), `range_test.py`, `extra_sensitivity.py`, `build_coverage.py` | Evidence and scripts behind Parts 2, 4, 5 and 11 |

## Summary

| Area | Result |
|---|---|
| Inputs reviewed | **98**.<br>- Concept match: exact 23, close 20, **mismatch 4**, not applicable 51 (parameters and constants; judged in Part 2).<br>- Status: sourced 49, derived 10, assumption 15, hard-coded constant 24.<br>- Currency: 33 data inputs current. 2 one release behind (DTP3, HIV incidence). 6 dated studies or series (ART, TB and DR-TB costs, vaccine delivery cost, GBD-2019 HIV death share, 2021-23 aid base years). |
| Country selection | 71 countries receive **71.5%** of country-coded HIV, TB, malaria and vaccine aid. 18% is coded "Global". Myanmar, Ukraine, Afghanistan, Sudan, Chad and Yemen are missing. No documented selection rule. |
| Assumptions by class | **(a)** supported 15; **(b)** evidence suggests a different value 9; **(c)** genuine assumption 22; **(d)** data exists 7 |
| Sensitivity | 42 inputs varied one at a time; 20 largest in `tornado.png`. Top 4: `art_hazard_mult` -18.6% / +23.3%; `continuity` +18.0% / -23.8%; `asd_share` +17.8% / -12.2%; `hss_kappa` -10.1% / +16.2%. |
| Dashboard numbers reproduced | **1,860 of 1,860 cells within 0.5%**: independent implementation, 5 countries x 4 cases, largest difference 0.17%. `audit/checks.py --quick`: 55 checks, 0 failures. |
| Claims reviewed | **18**: 8 supported, 5 need a qualifier, 5 overclaim or wrong |
| Benchmarks compared | **12** (Cavalcanti; Optima; UNAIDS; Clark; Mandal; MAP/PMI; Gavi; WHO HIV, TB and malaria burden; Thembisa; CEPAC). 2 gaps not fully explained: HIV infections (L-41), vaccine deaths per dollar (L-42). |
| Red-team points | **20**: 9 already found, 6 partly found (extended), 5 new (L-43, L-44, L-45, L-46, L-47). All resolved; 3 disagreements recorded (`redteam.md`). |
| Reproducibility | All of `model_data/`, including the 6 precomputed All Countries files, rebuilt **byte-identical** from `datasets/` in a clean environment. `country_inputs.csv` is numerically identical (float printing differs). Sections 1-3 per-country files **cannot be rebuilt** (scripts not in the repository). |
| Improvements proposed | **24**: Do now 7; Do before presenting 11; Nice to have 6 |
| Findings | **48**: Critical 2; Major 12; Minor 23; Presentation 11 |

## All findings

**Severity:**
- **Critical:** changes a headline number by more than 10%, or uses the wrong concept for a major input.
- **Major:** 3-10%, or the wrong concept for a minor input.
- **Minor:** under 3%.
- **Presentation:** labels, explanation or claims only.

**Confidence:** High = verified against a primary source or code; Medium = secondary or indirect; Low = judgment.

**Effects:** on all-country deaths 2026-2030, Full US Exit, no government response (base 1,969,304), unless stated.

| ID | Severity | Conf. | Finding and evidence | Effect (tested where possible) | Proposed fix | Needs your data? |
|---|---|---|---|---|---|---|
| L-01 | **Critical** | High (concept), Medium (size) | ART death hazard calibrated as 17% x 20.6M PEPFAR-supported patients (`model_params.csv` art_hazard_mult), applied to 5.30M full-cost equivalents (`health_model.py:438-450`, `:856-858`). HIV deaths 1.01M, about a third of Optima's PEPFAR-ending scenario (2.93M) and a quarter of UNAIDS (>4M). See `URGENT.md`. | Consistent readings: +7% to +115% (Brinkhof 20-60% risk; tested: 2.11M / 3.17M / 4.23M); reading B about +130% | IMP-01: pick one reading, calibrate, show both | No (A); DR-01 (B) |
| L-41 | **Critical** | High (gap), Medium (cause) | HIV infections 1.55M vs Optima 4.43-10.75M and UNAIDS 6M. `art_transmission` was calibrated per supported patient, like L-01. | Reading B: about 3.7M off-ART infections (+140% or more) | IMP-01 | No |
| L-43 | Major | High (mechanism), Low (size) | Unspecified money is spread to services only. TB: US$700M of US$1,522M (46%) becomes patients; effective TB service money is 3.7x the tagged amount. Tajikistan extra TB deaths are 108% of current TB deaths a year. | Est. -5% to -8% (not run) | IMP-02 | No |
| L-44 | Major | High (mechanism), Medium (size) | Proportional-cap rule (`_units_lost`, `health_model.py:438-450`) treats all covered people as donor-funded when donor money ÷ cost > covered. 160 of 695 lines (Validation page). | Est. -3% to -5% (red team; not run) | IMP-04 | DR-04 |
| L-05 | Major | Medium | `hss_kappa` (assumption, no evidence found) converts systems and testing & care money into patients at a cost already marked up by 1/(1-asd): above-site costs counted twice. | Swing -10.1% / +16.2%; kappa = 0 gives -20% (red team) | IMP-02 | No |
| L-14 | Major | Medium | `continuity` 0.15 is one global value with no source. PEPFAR FY25 ART counts were "stable" after the 2025 cuts (KFF). Large private TB sectors (India: 33% of notifications). | Swing +18.0% / -23.8% | IMP-16 | DR-02, DR-07 |
| L-04 | Major | High | Malaria effect sizes (Eisele 2010; Thwing 2011) are for children 1-59 months but are applied to all-age deaths. | **-4.9%** (tested: 1,872,379) | IMP-05 | No |
| L-20 | Major | High | `mal_cm_eff` 0.82 is the severe-malaria effect, applied to effective treatment of all cases. LiST uses 99% for uncomplicated malaria with ACT (Thwing 2011). | +4.1% at 0.99 | IMP-05 | No |
| L-06 | Major | High | Aid baseline 2021-23, but US health aid fell 67% in 2025 (IHME FGH 2025). Coverage is 2024-25, a mix of years. Cuts that began in 2025 start the hazard clock in 2026. IHME has no recipient detail after 2023 (checked). | Aid at Risk overstated for US scenarios (tens of %); deaths relative to 2021-23 service levels | IMP-06 | DR-03 |
| L-08 | Major (MOU preset) | High | The MOU preset ignores partner co-financing commitments, which are the defining feature of the MOUs (KFF tracker). | MOU preset deaths (360K) overstated wherever co-financing is delivered | IMP-08 | DR-12 |
| L-28 | Major (OECD preset) | High | OECD total-ODA changes are applied to health aid. IHME health-specific changes differ (UK -39% vs -10.8%; France -33% vs -10.9%). Labelled in the app. | OECD preset: country and donor mix wrong; total direction unknown | IMP-14; use IHME donor x disease ratios | No |
| L-18 | Major | Medium | Vaccine units are full-schedule children at US$87, but Gavi money buys specific newer vaccines. Losing it rarely means losing DTP3 entirely. | Unknown; see L-42 | IMP-15 | DR-05, DR-09 |
| L-42 | Major (under) | Medium | Vaccine deaths per dollar are 3-10x below Gavi's own claim (more than a million deaths if the US withdraws about US$1.58B). Part is scope (under-5 vs lifetime). | Vaccines are 6% of deaths; could rise severalfold | IMP-15 | DR-09 |
| L-33 | Major (2031-35 number) | High | "Further deaths 2031-35" depend mostly on `art_reengage` 0.5, an assumption. Most deaths from new HIV infections fall after 2035. | 2031-35: 298,801 (0.75) to 850,819 (0.25) vs 494,715 | Label as assumption-driven; show the range | No |
| L-02 | Presentation | High | Ranges are parameter-only but labelled "95% interval" (at least 10 places). The all-country range sums country percentiles: 1.34-2.81M vs the correct 1.39-2.70M. | Range 11% too wide; real uncertainty far larger (L-01) | IMP-09, IMP-10 | No |
| L-03 | Presentation | High | Country scope: 71.5% of country-coded disease aid. Large recipients missing; no documented selection rule. | Totals understate "all LMICs" | State the scope; IMP-23 | No |
| L-07 | Minor | High | 8 countries use an under-5 bednet survey for the whole population. 31 use a 50% default, though older surveys show 4-31% (Indonesia, Namibia, Botswana). | about 0 on deaths; credibility | Use the latest survey with decay, or 0 | No |
| L-09 | Minor | Medium | Gavi -15% default is "our estimate"; Gavi 6.0 has only US$6B in new pledges (Donor Tracker). | Preset only | Keep the label; IMP-13 | No |
| L-10 | Minor | High | `trend_tb_deaths` is defined (`health_model.py:423`) but never applied. TB and HIV counterfactuals are flat while malaria and vaccines trend. | small | Apply it or remove it, and document | No |
| L-11 | Minor | High | `hiv_deaths_est` (Validation, Lancet comparison) uses the GBD-2019 HIV share via Gapminder. Honduras comes out at 85 a year. | Validation page only | Use UNAIDS 2025 deaths | DR-06 |
| L-12 | Minor | High | TB detection rate can exceed 100% by definition (WDI). None does now; there is no guard. | 0 now | Clip at 1 and flag | No |
| L-13 | Minor | High | HIV+ TB untreated CFR = 0.62(1-0.3a) approximates WHO Table 5 (0.78 off ART; 0.49 at 1 year or more on ART). | under +1% | 0.78(1-a) + 0.49a | No |
| L-15 | Minor | High | TB: the whole 10-year case fatality is put in the year of loss (WHO: untreated duration about 3 years). Secondary cases all arrive 1-2 years later. | 2026-30 TB deaths overstated by a few %; moved to 2031-35 | IMP-11 | No |
| L-16 | Minor | High | DR-TB costs from single 2014 studies, pre-BPaLM (GDF US$284 per course), not monotone by income. Global 4% share and 45% coverage, though Central Asia's share is far higher. | about ±0.2% | IMP-03, IMP-11 | DR-02, DR-08 |
| L-17 | Minor | High | DTP3 2024 via the WDI mirror; WUENIC 2025 was released July 2026. | small | Download WUENIC directly | DR-05 |
| L-19 | Minor | Medium | Vaccine deaths scaled by clip(U5MR/50, 0.3, 2.5): our assumption. | Swing in `imm_*` about ±1% | VIMC by country | DR-09 |
| L-21 | Minor | High | MAP IRS is "the proportion of household sprayed", used as the share of people. | under 0.5% | Note it, or convert | No |
| L-22 | Minor | Medium | The IRS max() rule credits money-implied spraying where MAP shows none (Nigeria 0% since 2018). | under 0.1% (Nigeria spraying deaths 1,276) | Use MAP where it exists | No |
| L-23 | Minor | High | MAP vs WHO malaria cases differ by more than 30% in 20 of 46 countries (Pakistan 14.4M vs 3.15M). | -0.5% with WHO cases | Document; show both | No |
| L-24 | Minor | High | Need (births, PLHIV, incidence) held at the latest year, 2026-2030. | +2% to +5% where caps bind | IMP-17 | DR-10 |
| L-25 | Minor | Medium | Malaria death trend = Pf case trend clipped ±5% (clip unsourced). It compounds with resurgence in high-trend countries. | -0.8% / +0.1% | IMP-18 | No (on disk) |
| L-27 | Minor | Low | Testing & care money (US$760M/yr) is counted as lost ART at kappa; it funds a flow of new initiations, not a stock. | inside L-05 | IMP-02 | No |
| L-29 | Minor | Medium | Fiscal capacity is one strong year's growth held flat for 5 years, not cumulative. Stress thresholds unsourced. | 0 on default headlines | Cumulative capacity; cite IMF DSF | No |
| L-31 | Minor | Medium | WEO vintage of `macro_data` is untagged. WDI revenue and debt are central government only, missing for 18 and 41 countries. | display only | Tag the vintage | No |
| L-32 | Minor | Low | `uc_pmtct` 250: the cited review's figures could not be verified. | ±1.5% | Verify or replace | No |
| L-34 | Minor | High | Interest burden mixes IMF net general-government interest (53 countries) and WDI gross central-government interest (17). | fiscal panel only | Document; prefer one | No |
| L-35 | Minor | High | MOU amounts are nominal against a nominal reference, so inflation over 2026-30 is uncounted. Schedules ending 2028 are held flat; increases are counted as 0. | MOU preset understated by about 2-3% a year in real terms | Deflate | No |
| L-38 | Minor | High | Sections 1-3 per-country files can't be rebuilt (scripts not in the repository). | reproducibility | IMP-12 | No |
| L-39 | Minor | High | India's TB systems and unspecified money goes mostly to DR-TB (by own-money mix) at US$14,773 per patient. India's TB card: 638 deaths per US$1M vs about 2,000 elsewhere. | India only | Spread by patients or by the WHO DS/DR split | No |
| L-26 | Presentation | Medium | `asd_share` 45% cited to "PEPFAR 2014", not found. KFF 2025 reports 47%. | none | Fix the citation | No |
| L-30 | Presentation | High | "Lives first (triage)" is an optimisation rule, not observed behaviour. | none | Label "hypothetical best case" | No |
| L-36 | Presentation | High | `audit/METHOD.md` gives a different ART-units formula from the code. Kenya: 451.7k (code) vs about 328k (METHOD.md). | documentation | IMP-20 | No |
| L-37 | Presentation | High | `logic.md` was not enough to reproduce on its own: the independent reproducer needed 12 items from METHOD.md. | documentation | IMP-20 | No |
| L-40 | Presentation | High | "People Losing Care Each Year" sums full-cost-equivalent ART patients, bednet person-years and malaria episodes as people (Kenya: 4.90M of 6.10M are bednet users). | none | Relabel, or split treatment vs prevention | No |
| L-45 | Presentation | High | "Full US Exit" keeps 77% of the US Global Fund pledge and ignores signed MOUs. | none | IMP-14 | No |
| L-46 | Presentation | High | The IHME 2025 preset is called "Data-driven", but the country split is a uniform global ratio. | none | IMP-14 | No |
| L-47 | Presentation | Medium | The Validation page is framed to pass ("should come in below"). The Optima row shows 0.77-2.93M as comparable, though 2.93M is the PEPFAR-ending scenario. The Gavi row is circular. No TB or malaria benchmark. | none | IMP-19 | No |
| L-48 | Presentation | High | Headline and Methods claims overstate certainty (claims C1, C4, C5, C9, C17 in `dashboard.md`). | none | IMP-21 | No |

## The 10 most important findings, ranked

1. **L-01 (Critical).** The ART death risk is calibrated per supported patient but applied per full-cost
   equivalent. HIV deaths are about a third of the comparable Optima scenario. Every consistent reading raises the
   headline: +7% to +130%.
2. **L-41 (Critical).** HIV infections are 3-7x below published estimates, for the same reason.
3. **L-43 (Major).** Unspecified disease money (46% of TB aid) is counted entirely as patients' treatment. TB is
   likely overstated, with impossible country results (Tajikistan 108% of current TB deaths).
4. **L-05 (Major).** Above-site costs are counted twice: markup plus kappa conversion of systems money. This is the
   fourth-largest sensitivity and has no evidence behind it.
5. **L-14 (Major).** Continuity is the second-largest sensitivity, a single unsourced value. The 2025 PEPFAR data
   suggest it is higher in the short run.
6. **L-44 (Major).** The cap rule treats all covered people as donor-funded in 160 lines.
7. **L-06 (Major).** The 2021-23 baseline vs cuts that happened in 2025: "Aid at Risk" includes money already gone,
   and the hazard clock starts a year late.
8. **L-02 (Presentation, high visibility).** "95% interval" describes parameter noise only. The real uncertainty is
   several-fold larger.
9. **L-04 + L-20 (Major).** Malaria effect sizes: the wrong age group (-4.9%) and the wrong treatment effect (+4.1%).
10. **L-42 / L-18 (Major).** The vaccine pathway uses full-schedule costs and effects. It is likely conservative by a
    large factor relative to Gavi and VIMC.

## The 10 most valuable improvements, ranked (details in `improvements.md`)

1. **IMP-01.** Resolve the ART and infection concept; show readings A and B (Do now).
2. **IMP-02.** Spread unspecified money over services and systems; one treatment of above-site costs (Do before
   presenting).
3. **IMP-10 + IMP-21.** Honest range labels, all-country range from summed draws, claims wording (Do now).
4. **IMP-04.** Cap the donor-funded share with GHED or PEPFAR data (Do before presenting).
5. **IMP-05.** Malaria effects on under-5 deaths; LiST treatment effect (Do now).
6. **IMP-19.** Like-for-like Validation with acceptance bands; add TB, malaria and South Africa benchmarks (Do before
   presenting).
7. **IMP-06.** 2025 aid baseline option from ForeignAssistance.gov, Global Fund and Gavi data (Do before presenting).
8. **IMP-16.** Country-specific continuity (TB private sector; PEPFAR TX_ML) (Do before presenting).
9. **IMP-03.** Country unit costs (GHCC; Sweeney 2024; PEPFAR Expenditure Analysis; BPaLM) (Do before presenting).
10. **IMP-08.** MOU co-financing as the MOU preset's default response, in real terms (Do before presenting).

## What we can and can't claim

### Supported by the model and the evidence, with suggested wording

- **Direction and order of magnitude.** "Under a sustained end of US health aid with no replacement, the model
  estimates on the order of 2 million extra deaths from HIV, TB, malaria and vaccine-preventable disease in these 71
  countries over 2026-2030."
  - Supported: the central run is 1.97M. Every correction found moves the total in a band of roughly 1.5M to 4.5M (the downward corrections L-04, L-05, L-43 and L-44 together about -25%; L-01 up to +130%),
    and published models for HIV alone reach 2.9-4M.
  - State it as "on the order of", not a precise number.
- **Cross-country pattern.** "The largest losses fall in countries where donors pay for most HIV and TB treatment:
  Mozambique, Nigeria, Tanzania, South Africa, Kenya, Uganda and the DRC."
  - Robust to every alternative tested: L-01 raises these countries most.
- **HIV is the largest single source.** "Most of the extra deaths come from people losing HIV treatment."
  - Robust: L-01 raises HIV's share from 51% to 54-78%. L-43 lowers TB.
  - Don't quote a precise percentage.
- **TB and malaria per dollar.** "Per dollar, TB treatment and malaria programs avert the most deaths."
  - Consistent with the cost-effectiveness literature.
  - Hedge for TB (L-43, L-44). India is an exception for a data reason (L-39).
- **Past replacement.** "In past aid declines (2001-2023), governments on average did not raise their own health
  spending to compensate."
  - Supported by the regression: θ = -0.19, 95% CI -0.45 to +0.07.
- **Fiscal room.** "Few governments could fill the gap from fiscal space alone: the model's estimate of yearly room
  is small next to the loss (Kenya: about US$21M against US$278M)."
  - Supported as a model statement; capacity rule L-29.
- **Benchmarks.** "The totals sit below all-cause estimates (Cavalcanti et al.), because the model counts four
  disease areas in 71 countries."

### Not supported, or not at the stated strength

- **A precise death count, or a "95% interval".** Ranges are parameter-only (L-02). Structural choices (L-01, L-05,
  L-43) move results far more.
  - Instead: "about 2 million (range across parameter values 1.4-2.7 million; structural choices could put it
    between about 1.5 and 4.5 million)."
- **"N people will lose HIV treatment."** Units are full-cost equivalents, not headcounts (L-01, L-40).
  - Instead: "the lost money would have paid for treatment for about N people".
- **HIV infections.** "1.6 million new HIV infections" is 3-7x below published models (L-41). Don't present it until
  L-01 is resolved.
- **TB deaths per country.** Not reliable for Tajikistan, Cambodia, Mozambique and India until L-43, L-44 and L-39 are
  fixed.
- **Vaccine deaths.** Likely understated (L-42). Present them as a conservative lower estimate.
- **"Between Optima and UNAIDS."** False as calibrated (L-01). Validation agreement with Optima is partly a
  coincidence of offsetting errors (L-47).
- **OECD preset as "OECD-reported health cuts".** It applies total-ODA cuts (L-28).
- **MOU preset as "the effect of the MOUs".** It omits the co-financing that defines them (L-08).
- **"Further deaths 2031-2035" as committed deaths.** It mostly reflects an assumed re-engagement rate (L-33), and it
  excludes most deaths from new infections after 2035.
- **Totals for "low- and middle-income countries".** The model covers 71.5% of country-coded aid and none of the
  "Global" share (L-03).

## Known omissions and their direction of bias

From `uncertainty_scope.md` Part 4b.

| Omission | Bias in extra deaths | Rough size |
|---|---|---|
| Other health aid (maternal and child health beyond vaccines, nutrition, family planning, NTDs, WASH) | Under | Cavalcanti covers all causes: about 7x the model, mostly scope |
| Countries not on the dashboard, and "Global" aid | Under | 28.5% of country-coded disease aid; maybe +10-25% |
| Supply-chain, data-system and surveillance collapse beyond kappa | Under | unquantified |
| Deaths after 2035 (new HIV infections; lost epidemic control) | Under | most deaths from 1.55M+ infections fall after 2035 |
| Other donors or governments stepping in (beyond the response options) | Over | 2025 PEPFAR ART counts were stable (KFF) |
| Behavioral responses (private care) beyond 15% continuity | Over | continuity swing ±20% |
| Population and epidemic growth in need | Under | +2-5% |
| Price falls (BPaLM, cheaper nets, lenacapavir) | Over or under | small |
| Drug resistance after interruptions | Under, long term | unquantified |
