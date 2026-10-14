# Part 3: Logic chain review

Every formula below is written from the code as it stands on `real-modeling-check` (commit `a6a4871` plus the
logic-review files). References are `file:line`.

- **Notation:** l = service line, b = disease bucket, t = year 2026..2030 (t = 1..5), n = Monte Carlo draw (central
  run = every parameter at its central value).
- **Units:** money is US$ a year in constant 2023 US$ unless stated.
- **Purpose:** this is the specification the independent reproduction (Part 5) works from. It must be complete.

---

## Sections 0-6 (the specification): moved

The plain-math specification that was here (inputs, cuts, money by line, government response, people losing each service, deaths, uncertainty) is now part of [`docs/SPEC.md`](../../docs/SPEC.md). It was merged with `audit/METHOD.md` into one current specification that matches the code (IMP-20). The text as reviewed is in git history (`git show 2cfcb14:audit/logic_review/logic.md`). The review commentary below still refers to the code as it stood at that commit.

---

## Review findings by topic

Finding IDs refer to `findings.md`.

### a) People losing ART: full-cost equivalents vs PEPFAR-supported patients (L-01, Critical)

**Two concepts.**
- **Full-cost equivalent (model):** ART money lost / full cost per patient-year (about US$300 in Kenya after the 45%
  above-site markup).
  - Donor money as a whole pays for **7.78M** full-cost equivalents, against **24.71M** people on ART in the 70
    countries (computed from the model, Validation page).
  - Full US Exit removes **5.30M** a year.
- **PEPFAR-supported patients:** everyone on ART at a site PEPFAR supports in any way. "Supported antiretroviral
  treatment for 20.6 million people" (KFF fact sheet, FY2024); "stable compared to Quarter 4 of FY 2024" in FY2025 Q4.
  - Most of these patients' drugs or staff are paid partly by governments and the Global Fund.

**What the hazard was calibrated against.**
- `model_params.csv:13` says the 5-year cumulative 17% "sits between Optima (0.8-2.9M deaths) and UNAIDS ... against
  20.6M people on PEPFAR-supported ART".
- That is, 17% x 20.6M = 3.5M deaths.
- The model applies the same 17.5% to 5.30M people, giving 0.93M ART deaths (1.01M HIV deaths). That is at the bottom
  of the Optima range, not between Optima and UNAIDS. **The calibration is not internally consistent.**

**Evidence on the right per-person risk if people actually stop ART.**
- **Brinkhof 2009** (*PLoS ONE* 4:e5790), patients lost to follow-up: "The combined mortality was 40%"; "among those
  traced 20% to 60% had died".
- **Marsh et al. 2020** (*Lancet HIV* 7:e629), HIV Modelling Consortium: a 6-month ART interruption for 50% of people
  on ART in sub-Saharan Africa gives "a median excess of HIV deaths ... of 296 000" over one year.
  - That is about 3% per person interrupted for only 6 months, versus the model's 1.2% for a full first year.
- **The model's year-1 hazard is therefore low for someone who actually stops ART**, and its 17.5% 5-year total is
  below the 20-60% observed among traced lost-to-follow-up patients.

**Test of the alternative readings** (arithmetic on the model output, Full US Exit, no government response):

| Reading | ART deaths | All deaths 2026-2030 |
|---|---|---|
| As implemented | 0.93M | 1.97M |
| A. Same 5.30M people, risk 40% (Brinkhof combined) | 2.12M | 3.16M (+61%) |
| A, risk 20% / 60% | 1.06M / 3.18M | 2.10M / 4.22M |
| B. Spread across supported patients: 20.6M x 17% (PEPFAR, all 55 countries; an upper bound for the 70 dashboard countries) | about 3.5M | about 4.5M |

**HIV deaths vs benchmarks.**

| Source | HIV deaths |
|---|---|
| Optima (ten Brink et al. 2025, *Lancet HIV*) | 0.77-2.93M, 2025-2030 |
| UNAIDS (July 2025) | "more than 4 million" by 2029 |
| Model as implemented | 1.01M |
| Reading A, 20-60% | 1.1-3.3M |
| Reading B | about 3.6M |

- Both consistent readings move the model toward the middle of the published range.
- **Confidence:** High on the mismatch; Medium on the size.

### b) TB

**Incidence vs notified.** Need = WHO estimated incidence (all forms, 2024). Coverage = WDI `SH.TBS.DTEC.ZS`.
- Definition (World Bank, from WHO Global TB Report): "the number of new and relapse tuberculosis cases notified to
  WHO in a given year, divided by WHO's estimate of the number of incident tuberculosis cases for the same year".
- So covered = notified cases. This is a **close match** for "people on TB treatment" (it counts notification, not
  completion). It includes private-sector notifications: India 33% private in 2023 (India TB Report via GroundUp).
- **L-12 (Minor):** the ratio can exceed 100%.

**Case fatality.** WHO TB burden methods (Glaziou et al., arXiv 1603.00278):
- Table 4: "Not on TB treatment 0.43 (0.28-0.53) ... On TB treatment 0.03 (0-0.07)".
- Table 5 (HIV+): off ART and off treatment 0.78; under 1 year on ART 0.62; 1 year or more on ART 0.49; treated
  0.09 / 0.06 / 0.04.
- The model uses 0.62 x (1 - 0.3 x ART coverage) for HIV+ untreated (`:461`), an approximation of Table 5.
  - **L-13 (Minor):** at 90% ART coverage it gives 0.45 vs WHO's 0.49 (1 year or more on ART); for people off ART it
    should be 0.78.

**What "untreated" means.**
- The model assumes a patient whose donor-funded treatment is lost gets no treatment at all, except the 15%
  `continuity`.
- In India (about 50% of patients treated privately: Solapur 2024; national notifications 33% private) and other
  large private-sector countries, many would be treated elsewhere.
- Donor TB money is a small share of TB spending in India and Indonesia, so units lost are small there. The
  assumption matters most where donors fund most TB care.
- **L-14 (Major):** continuity is one global value. Evidence that it should vary by country: private-sector share of
  notifications (WHO GTB data).

**Timing.**
- WHO: "the mean duration of untreated disease ... is about three years" (same methods paper).
- The model puts each untreated cohort's full 10-year case fatality into the year of loss (x 0.7 in year 1). Deaths
  of people losing treatment in 2029-2030 are partly after 2030.
- **L-15 (Minor):** 2026-2030 deaths are front-loaded; the 5-year total is overstated and 2031-2035 understated, by a
  few percent of TB deaths.

**DR-TB cost.**
- `unit_cost_reference.csv`: lower-middle-income DR-TB US$8,125, from Laurence 2015 (2014 US$), which was based on
  18-24-month regimens.
- WHO now recommends the 6-month all-oral BPaLM regimen. The Stop TB Global Drug Facility price fell to "$284 per
  course" (September 2025). The Laurence costs predate it.
- **L-16 (Minor):** DR-TB is about 1% of deaths (`tb_dr_dcfr` sensitivity -0.2%/+0.2%), so the effect is small.

**Country TB costs.**
- The model uses income-group means (Laurence 2015) x 1/(1-0.45).
- Lower-middle-income: 351 / 0.55 = US$638 per patient. Sweeney et al. 2024 (*Lancet Global Health*) give US$450
  (India), US$560 (Philippines) and US$730 (South Africa) per person treated, standard of care.
- The 45% above-site markup makes the model higher than these for India.
- For Indonesia, Pakistan and Nigeria no 2020s provider costing was found. **UNVERIFIED**; see `data_requests.md` for
  GHCC.

**Implied cost per TB death.**
- Kenya card: 1,945 deaths per US$1M a year over 5 years, i.e. **US$2,570 per death**.
- Published: TB treatment cost per DALY averted is typically a few hundred dollars. At about 20 DALYs per TB death,
  that is roughly US$2,000-6,000 per death averted. **Medium** (secondary synthesis; see `benchmarks.md`).

**TB deaths vs benchmarks.**
- Model, Full US Exit TB deaths 2026-2030: 460,067.
- Clark et al. 2025 (*Lancet Global Health*), loss of USAID TB funding: "537 700 ... excess deaths by 2035" (79
  countries).
- Mandal et al. 2025: 100,000 (minimal) to 2.24M (worst) TB deaths, 2025-2030.
- The model is within the published range, at the high end per year relative to Clark (USAID only, 10 years). See
  `benchmarks.md`.

### c) Immunization

**DTP3 as coverage.**
- WUENIC DTP3 (WDI `SH.IMM.IDPT`) is the standard proxy for routine coverage (**close match**).
- **Currency (L-17, Minor):** the model uses 2024; WUENIC released 2025 estimates in July 2026 ("DTP3 reached 85%
  in 2025", UNICEF/WHO press release).

**Births.** Crude birth rate x population, 2024 (WDI). Close match; no projection to 2026-2030 (L-24).

**Deaths per child.**
- Gavi: "The cumulative number of deaths averted from 2000 through 2024 is more than 20.6 million"; "more than 1.2
  billion unique children". 20.6M / 1.2B = 0.017; 1.7M / 72M in 2024 = 0.024. Model 0.020 (0.017-0.024).
- These are VIMC-modelled future deaths averted across all Gavi-supported vaccines, per child reached.
- **Concept:**
  - The model treats donor vaccine money / US$87 as children who lose *all* vaccines.
  - Most donor (Gavi) money pays for newer vaccines (PCV, rotavirus, HPV, malaria, measles campaigns) and co-financed
    pentavalent. Losing it rarely means losing DTP3 entirely.
  - Using full-schedule cost with full-schedule deaths per child is internally consistent as a full-cost-equivalent
    calculation. It shares L-01's question of who is actually affected.
  - **L-18 (Major):** concept close; size unknown without country vaccine-by-vaccine impact (VIMC).

**Under-5 share 0.65.**
- Li et al. 2021 (*Lancet*): of cohort deaths averted, "120 million ... 58 million ... measles and 38 million ...
  hepatitis B". Hepatitis B deaths occur in adulthood, and 1 - 38/120 = 0.68.
- **Supported (Medium):** the 0.65 is our derivation, not a published number.

**U5MR scaling.**
- Deaths per child x clip(U5MR / 50, 0.3, 2.5).
- The reference 50 per 1,000 and the clip are our **assumptions** (L-19, Minor): no source found that links VIMC
  impact per child linearly to U5MR.

### d) Malaria

**Effect sizes are for children.**
- Eisele, Larsen & Steketee 2010 (*Int J Epidemiol* 39:i88): ITNs/IRS give a protective efficacy of 55% (49-61%)
  "against malaria-attributable deaths in children aged 1-59 months".
- Thwing et al. 2011 (*BMC Public Health* 11(S3):S14): "PE of ACT treatment of uncomplicated P. falciparum malaria
  ... on reducing malaria mortality in children 1-23 months to be 99%"; severe malaria 82% "in children 1-59 months".
- **The model applies both to D0 = all-age malaria deaths.**
- WHO World Malaria Report 2025: "75% of deaths in the region occurred in children aged under 5 years" (African
  Region).
- **L-04 (Major).** Restricting the effects to under-5 deaths (75% in Africa; less elsewhere) would lower malaria
  deaths by up to about 25%: about -96,000 deaths, -4.9% of the Full US Exit headline. No published adult effect size
  for LiST was found (UNVERIFIED).

**Ec central 0.82 (severe) applied to effective-treatment coverage of uncomplicated cases.**
- MAP effective treatment is coverage of all cases; Thwing gives 99% for uncomplicated malaria with ACT.
- Using 0.82 is conservative. Sensitivity (`mal_cm_eff` 0.6-0.99): -3.5% / +4.1%. **L-20 (Minor).**

**MAP inputs.**
- **Treatment.** MAP "Effective Treatment", in 100 malaria cases (from the raw file's metric and units). A
  MAP-related paper defines it as "the fraction of malaria cases that were effectively treated" (PMC11549775,
  Malaria treatment for prevention). **Exact match** to the LiST coverage concept.
- **Bednets.** MAP ITN "Use", "in 100 people" (Bertozzi-Villa et al. 2021, *Nature Communications*): **exact match**
  for population-level use. Covers 40 African countries; elsewhere a survey from 2015 on (8 countries) or the 50%
  default (31 countries, 9 of them with malaria deaths).
- **Spraying.**
  - MAP: "the proportion of household sprayed with IRS annually" (MAP IRS page). The WHO indicator is "Percentage of
    population at risk protected by IRS".
  - The model uses the household share as the population share. **L-21 (Minor):** close match; the bias depends on
    household size in sprayed areas.
  - MAP models IRS only in Africa; the product page lists 2000-2020, so 2021-2025 values may be carried forward.
    **UNVERIFIED**; MAP metadata would settle it.
- **Spraying max() rule.**
  - Where donor IRS money buys more people than MAP shows sprayed, the model uses the money-based figure.
  - This assumes 2021-23 IRS money still buys spraying in 2025. In Nigeria and Benin, MAP shows spraying stopped
    (Nigeria 0% from 2018), so the money was likely spent on other vector control or not at all.
  - **L-22 (Minor):** under 1% of deaths (Nigeria spraying deaths 1,276).
- **Cases.**
  - MAP Pf + Pv clinical cases are modelled incidence of symptomatic cases (all ages); WHO estimates use case
    surveillance adjusted for completeness.
  - **20 of 46 countries differ by more than 30%.** Pakistan: MAP 14.4M (2025) vs WHO 3.15M (2024); national
    confirmed cases 2.7M in 2023 and "2 million" in 2024 (WHO EMRO; press).
  - Cases only set the treatment denominator (coverage drop = units / cases). Sensitivity, WHO cases instead of MAP:
    -0.5% of all deaths.
  - **L-23 (Minor).**
- **Pf-case trend as proxy for death trend.**
  - P. falciparum causes nearly all malaria deaths (WMR), but case trends and death trends diverge where case
    management or the age mix changes. Ethiopia: Pf trend fit +10.7%/yr, clipped to +5%.
  - The ±5% clip is our assumption; no source found. Sensitivity: trend set to 0 gives -0.8% of all deaths; the
    unclipped fit gives +0.1% (`sensitivity.csv`).
  - **L-25 (Minor).** A direct alternative exists: WHO country malaria death series 2015-2024 (GHO
    `MALARIA_EST_DEATHS`, already in `ext_data/gho`).

### e) HIV inputs

**People living with HIV and ART coverage.**
- GHO `HIV_0000000001` and `HIV_ARTCOVERAGE` (UNAIDS 2026 round, year 2025).
- UNAIDS 2026 fact sheet: "41.0 million ... people globally were living with HIV in 2025"; "32.1 million people
  ... were accessing antiretroviral therapy in 2025".
- **Current (High).** 5 countries use the derived fallback (CIV, GTM, IRQ, JOR, NIC).

**ART cost.**
- Rosen et al. 2021 site costs (2018-2020 US$) x CPI x uc_art_mult / (1 - 0.45).
- The 45% above-service-delivery share is cited to R4D. The search found no confirmation of the exact 45%; the
  closest is KFF (2025, PEPFAR 22 countries 2018-2023), where "non-service delivery accounted for 47% of spending".
- **UNVERIFIED** as cited; supported (Medium) by KFF 47%. **L-26 (Minor):** citation. The sensitivity is large:
  asd_share 0.30 / 0.55 gives +17.8% / -12.2%.

**Transmission.** art_transmission 0.04 per person-year off ART. Untreated serodiscordant couples: about 2.2 per 100
person-years overall, 8.8 at CD4 < 200 (Partners PrEP via aidsmap). Supported (Medium) for people who stop ART.

**PMTCT.**
- WHO: transmission 15-45% without intervention, under 5% with. Newell 2004: 35.2% dead by age 1 and 52.5% by age 2.
- **uc_pmtct 250:** the Health Policy & Planning 2016 review figures could not be checked from the abstract
  (**UNVERIFIED**).

**Testing & Care at kappa.**
- IHME program areas list care and support and counseling & testing separately from treatment (DAH User Guide 2026,
  variable list).
- Counting kappa = 0.5 of that money as lost ART is our assumption. **L-27 (class c).**

### f) Aid data

**Program areas.** `hiv_dah_23` = sum of 11 program areas within IHME's US$1K-per-cell rounding (checked on 147,843
rows, 2021-23).

**Spreading unspecified and systems money.**
- Unspecified money follows the country's known mix; systems money at kappa.
- How much, US$M/yr 2021-23 (`model_data/dah_lines.csv`):

| Bucket | Tagged service lines | Unspecified | Systems |
|---|---|---|---|
| TB | 352 | 700 | 469 |
| HIV | 3,375 (incl. testing & care 760) | 819 | 1,078 |
| Malaria | 924 | 511 | 465 |

- **L-43 (Major).** The known mix excludes systems lines, so 100% of unspecified money becomes service money. Effective TB service money = 352 + 700 + 0.5 x 469 = 1,286, 3.7x the tagged amount. Found with the red-team review (`redteam.md`).
- **L-44 (Major).** Where donor money ÷ cost exceeds people covered, the proportional cap (`health_model.py:438-450`) treats every covered person as donor-funded (160 of 695 lines; Tajikistan extra TB deaths 108% of current TB deaths a year).
- Kappa sensitivity: 0.25 / 0.9 gives -10.1% / +16.2%.

**elim_ch.** Applied once, at load (`prepare_model.py:294`). Every downstream table uses it, including the IHME 2025
ratios and the panel.

**Baseline year (L-06, Major).**
- The model cuts from the 2021-23 average. IHME FGH 2025: DAH "declined 21% between 2024 and 2025, driven largely by
  a 67% drop" in US financing.
- So by 2025 much of the US money a Full US Exit removes was already gone. The model's "aid at risk" includes money
  already lost, and its deaths are relative to 2021-23 service levels.
- The baseline coverage, though, is 2024-25, and partly reflects post-cut service levels. That mix of years is
  internally inconsistent.
- IHME 2025 has no country split, so a 2025 country baseline is not yet available.

**Global and unallocated money (scope).** US$2.67B/yr of HIV, TB, malaria and vaccine aid (18%) is coded to "Global"
and US$0.26B to "Unallocated" (IHME raw 2021-23). None is in the model; omission listed in `uncertainty_scope.md`.

### g) Scenarios

| Preset | Check | Source |
|---|---|---|
| Full US Exit | US Global Fund pledge US$4.6B vs US$6.0B = -23%: verified | EATG / Health Policy Watch, "Global Fund raises $11.4 billion, including $4.6 billion from US"; Results/FY27 cheat sheet |
| Full US Exit | US exits WHO and stops Gavi: verified | AP; CGD |
| Full US Exit | Delivered vs pledged: "the United States has contributed only $3.12 billion of the $6 billion pledged for 2023-25" | ThinkGlobalHealth |
| OECD 2025 | US -56.9%, Germany -17.4%, France -10.9%, UK -10.8%, Japan -5.6%: verified exactly | OECD "A historic decline in foreign aid: Preliminary 2025 ODA data" (April 2026) |
| OECD 2025 | **Concept:** total ODA change applied to health aid. IHME FGH 2025 shows health aid fell differently (UK -39%, France -33%, Germany -12%) | **L-28 (Major)** |
| IHME 2025 | Global ratio by donor x channel x disease applied to every country's mix. IHME publishes no recipient split for 2025 | Labelled correctly in the app |
| Global Fund & Gavi | Gavi 6.0: "only US$6 billion of the funding secured comprises new pledges", the rest reallocated (Donor Tracker, April 2026); US$550M Japan pledge not in the US$9B. The 15% "our estimate" is plausible but **UNVERIFIED** as a disbursement forecast | |
| Global Fund & Gavi | Global Fund final US$12.64B vs US$15.7B = -19.5%: verified | Global Fund Board, Eighth Replenishment page |
| America First MOUs | KFF tracker: "five-year plans ... Partner countries commit to raising domestic health spending while U.S. assistance falls". The model takes the US decline but, by default, no government replacement. The MOU co-financing commitments are in the team sheet but not used | **L-08 (Major)** |
| America First MOUs | "An increase counts as 0" (no gain modelled): consistent with I-15. Schedules ending 2028 held flat to 2030: assumption, labelled | |

### h) Fiscal

**Backfill regression** (`prepare_model.py:526`).
- Specification: d(GHES pc) on falls and rises in DAH pc, with a lag and d(GDP pc), country and year fixed effects,
  2001-2023, 97 countries, n = 2,134; theta = -(b_fall + b_fall_l1) = -0.19 (95% CI -0.45 to +0.07).
- Literature: Lu et al. 2010 (*Lancet*): governments "cut government health and related spending by about $0.43 to
  $1.14 for each $1 of DAH received" (aid to government displaces domestic spending). Dieleman et al. 2013 confirm
  partial fungibility.
- Those estimate the response to aid *rises*. Evidence on the response to aid *falls* is thin. The model's finding of
  no backfill on falls is consistent with Lu (co-movement). **Supported (Medium).**

**Fiscal capacity.**
- GHES 2023 x (p75 - median growth) x stress. A capacity measure of our own construction (L-29, class c).
- Implicitly assumes a strong growth year is fiscally possible every year for 5 years.

**Interest to revenue.**
- IMF primary minus overall balance = net interest. Secondary sources: "primary balance is ... revenues and non-interest
  expenditures" (Macrosynergy); IMF FM label "Primary net lending/borrowing (also referred as primary balance)". The
  IMF glossary itself was not reached (**UNVERIFIED** wording; the concept is standard).
- WDI `GC.XPN.INTP.RV.ZS`: "interest payments on government debt ... to domestic and foreign residents"; central
  government, from IMF GFS.
- **Close match**, with two differences: net vs gross interest, and general vs central government.

**Debt-stress factor.** 10% / 40% thresholds: assumption (class c).

**Health share.** WDI `SH.XPD.GHED.GE.ZS` (WHO GHED), "domestic general government health expenditure (% of general
government expenditure)". GHED updated 12 December 2025. Model year 2023; **current**.

### i) Government response allocation

- **Pro rata:** neutral.
- **Lives first:** refills in order of the model's own central deaths per US$, which puts TB and ART first. This is
  an optimisation rule, not a description of behaviour; no source says governments triage this way.
  - Labelled "Lives first (triage)" in the UI; Methods says "refilled in order of deaths averted per dollar".
  - **L-30 (Presentation):** call it a hypothetical best case.
- **Replacement never exceeds the loss** (`budget_t = min(R_t + gov_add_t, L_t)`, `:680`). Checked.
- **Phased paths:** replacement applies to each year's loss. **Gradual increase:** money added each year, capped at
  the loss.

### j) Counterfactual

"Extra deaths" = deaths in the scenario minus deaths if donor money continued at the 2021-23 level, with:

| Assumption | Basis | Where |
|---|---|---|
| Baseline coverage held at 2024-25 levels | | `epi` |
| People in need held at their latest year | no population growth or epidemic change | |
| Baseline malaria deaths change | MAP Pf trend | |
| Vaccine death rates scale with U5MR | 2010-19 trend | |
| TB and HIV deaths per patient constant | | |

- **L-24 (Minor):** no projection of need. PLHIV grows about 1%/yr; births grow in sub-Saharan Africa.
- Internally consistent across diseases in that all use a fixed-coverage counterfactual. They differ in which deaths
  trend (malaria and vaccines only).

### k) Sections 1-3 (descriptive)

**Section 1.** IHME health spending categories (government, prepaid private, out-of-pocket, DAH), constant 2023 US$.
- The DAH in this database matches the DAH database within 2% for 624 of 630 country-years; 6 are 2-4.4% off
  (`checks.py` warnings).
- The IHME Health Spending 1995-2023 file is the September 2026 release. **Current.**

**Section 2.**
- IHME DAH by source, channel and program area: same file as the model, `elim_ch == 0`. **Current** (September 2026
  release).

**Per-person figures.** WEO population (macro_data). WEO vintage of macro_data: April 2026 (UNVERIFIED; the files
carry no vintage tag). **L-31 (Minor).**

**Section 3** after I-10:
- Breakdowns are by level of government, with WEO general-government totals.
- 26/71 revenue and 16/46 spending breakdowns are general government; the rest central with a grey remainder box.
- Logic checked (`checks.py`: boxes sum to WEO).

## Edge cases checked

| Case | Behaviour | Evidence |
|---|---|---|
| Zero aid in a disease | No loss, "No {disease} aid" card | `tests/test_hiv.py::test_card_without_aid_says_so` |
| Aid increases | Counted as no loss, with a note | I-15, `checks.py` (no negative people or coverage drop) |
| Tiny countries, very low burden | Deaths about 0, "~0" | `model_section.py` (deaths "~0" tooltip) |
| Capped lines | Units at most covered | `checks.py` (people losing at most people covered) |
| Phased paths and MOU schedules that ease | Cohort return-to-care logic | `art_cohorts`; tests in `test_paths.py` |
| Replacement above the gap | Impossible by construction | `:680` |
| Deaths at most people affected | Every line | `checks.py` (deaths at most people affected, 10,208/10,208) |
