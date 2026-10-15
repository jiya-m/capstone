# Part 6: Plausibility against external benchmarks

**Model numbers:**
- Precomputed All Countries files (`model_data/all_countries_<preset>.csv`; central run, no government response,
  sudden cut, death-rate trend on, 70 countries).
- Country rows come from the same files.

**Full US Exit, 2026-2030:**

| Measure | Value |
|---|---|
| All deaths | 1,969,304 |
| HIV | 1,006,114 |
| TB | 460,067 |
| Malaria | 385,713 |
| Immunization | 117,411 |
| Further deaths 2031-35 | 494,715 |
| HIV infections | 1,552,704 |
| Aid at risk | US$3.96B/yr |

## Global benchmarks

### Cavalcanti et al. 2025, *Lancet* 406:283 (USAID defunding)

| | Benchmark | Model |
|---|---|---|
| Result | ">14,051,750 (uncertainty interval 8,475,990-19,662,191) additional all-age deaths, including 4,537,157 ... younger than 5 years, by 2030" (UCLA / ISGlobal summaries of the paper) | Full US Exit 1.97M (Combined 2.16M) |
| Scope | All causes, 133 countries, 83% USAID cut, 2025-2030 | 4 diseases, 70 countries, all US health aid for those 4 diseases, 2026-2030 |
| Method | Panel regression of mortality on USAID spending per person | Unit cost to coverage to deaths |

**Why they differ:**
- Cavalcanti covers all USAID sectors (nutrition, WASH, maternal and child health) and every cause, with one extra
  year and 63 more countries.
- Its regression attributes historical co-movement to USAID. Critics note this may overstate causation (e.g.
  GreaterWrong reproduction, Low).
- The model's Validation page runs its own Lancet-method cross-check (`health_model.py:1347`).

**Verdict:** a gap of about 7x, explained by scope and method. Confidence: Medium.

### HIV: ten Brink et al. 2025, *Lancet HIV* (Optima, 26 countries)

| | Benchmark | Model |
|---|---|---|
| Deaths | "0.77-2.93 million" additional HIV deaths, 2025-2030 | 1.01M (Full US Exit), 1.03M (Combined) |
| Infections | 4.43-10.75M | 1.55M |
| Scenario | 24% cut by top 5 donors plus PEPFAR ending | Full US Exit |

**Deaths:** inside the range, but only because of L-01: the per-person hazard is calibrated against the 20.6M
supported patients, then applied to 5.3M full-cost equivalents.

**The range spans scenarios, not uncertainty in one scenario.** The upper end (2.93M deaths, 10.75M infections) is
"scenario 5", PEPFAR discontinued without mitigation. Science Media Centre Spain expert commentary on the paper: "The
model projections predict in scenario 5 that ... would increase to 10.75 million and 2.93 million transmissions and
deaths respectively".

The scenario behind the lower end (0.77M) is not stated in any source I could reach. The paper and the medRxiv
preprint returned 403: UNVERIFIED. The red-team review reads it as the proportional 24% cut without PEPFAR ending.

So the closest Optima analogue of Full US Exit is about **2.9M** (all LMICs, 2025-2030), not "0.77-2.93M". The model's
1.01M is about a third of it.
- The Validation page's comparison row (`model_section.py:1850-1854`) and the `model_params.csv` source text should
  say this.
- This strengthens L-01. **New finding L-47 (Presentation):** the Validation page presents 0.77-2.93M as the
  comparable range.

**Infections are 2.9-6.9x below Optima's range.** The model's infections come from:
- people off ART x 0.04 a year: about 5.3M x 0.04 x 4.5 years = about 0.95M;
- lost prevention units at US$5,000+ per infection averted (`cpia_ref`).

Under L-01 reading B (20.6M supported patients affected), off-ART infections alone would be about 3.7M, near
Optima's low end. **New finding L-41 (Major):** HIV infections are far below every published estimate. This is
explained by L-01 plus a high cost per infection averted. Confidence: High on the gap, Medium on the cause.

### HIV: UNAIDS (July 2025)

| | Benchmark | Model |
|---|---|---|
| Deaths | "more than 4 million" AIDS-related deaths by 2029 | 1.01M HIV deaths 2026-2030 |
| Infections | 6 million new infections by 2029 | 1.55M |
| Scenario | PEPFAR permanently discontinued and not replaced | Full US Exit |

- The model is about 4x lower. UNAIDS assumes the full loss of PEPFAR-supported treatment for everyone at supported
  sites: the reading-B concept.
- Under reading B the model gives about 3.6M HIV deaths, close to UNAIDS.

**Verdict:** explained by L-01.

### TB: Clark et al. 2025, *Lancet Global Health* (USAID TB funding loss)

| | Benchmark | Model |
|---|---|---|
| Deaths | "537,700 ... excess deaths by 2035", 79 countries | TB deaths 460,067 in 2026-2030, plus TB secondary cases after 2030 |
| Rate | about 54k a year | about 92k a year |
| Scope | USAID TB funding only (about US$400M a year) | All US money for TB, including the Global Fund cut |

- The model's broader US scope explains part of the higher rate.
- The model also front-loads deaths (L-15): each untreated cohort's full case fatality falls in the year of loss.

**Verdict:** within a factor of 2. Confidence: Medium.

### TB: Mandal et al. 2025 (TB modelling of funding cuts)

- **Benchmark:** 100,000 (minimal) to 2.24M (worst case) TB deaths, 2025-2030.
- **Model:** 460,067 (Full US Exit); 586,341 (OECD); 540,522 (Combined).
- **Verdict:** inside the range. Confidence: Medium.

### Malaria: Malaria Atlas Project, PMI impact

- **Benchmark:** PMI-funded interventions prevent about 104,000 deaths a year in 27 countries; a 1-year freeze gives
  about 107,000 deaths (MAP / Weiss et al. 2025).
- **Model:** malaria deaths, Full US Exit, about 77,000 a year (385,713 / 5), including the US share of Global Fund
  malaria money.
- **Why it is below:**
  - L-04 (child effect sizes applied to all ages) would push the model down, not up.
  - The model omits malaria chemoprevention (SMC) and other non-vector-control commodities funded by PMI. These are
    in IHME `mal_con_oth`, which the model counts as nets.
  - The model counts only half a year of bednet effect in year 1.
- **Verdict:** same order of magnitude (0.7x). Confidence: Medium.

### Immunization: Gavi

**Gavi's numbers:**
- Gavi said US withdrawal of its 2026-2030 support (US$1.58B pledged in 2024) could cost "more than a million"
  lives.
- 1.2M deaths for US$1.58B is about **US$1,300 per death averted** (lifetime deaths, all Gavi-supported vaccines).
- Exact wording verified only via secondary sources (UNVERIFIED primary).

**The model:**
- Immunization deaths in Full US Exit: 117,411 in 2026-30 plus cohort deaths after 2030 (included in the 494,715).
- Implied aid lost per death from the per-US$1M cards: Kenya US$13k, Nigeria US$4.2k, Mozambique US$8.8k per death
  (2026-30 deaths only).

**Why they differ:**
- The model uses deaths before age 5 within the window (imm_u5_share 0.65 plus timing). Gavi counts lifetime deaths.
- The model costs US$87 for the full schedule; Gavi's marginal cost per child is far lower, and co-financing is
  excluded.
- **L-18:** a full-cost-equivalent child loses all vaccines. In reality Gavi money pays for newer vaccines (PCV,
  rotavirus, malaria, HPV), which avert many deaths per dollar.

**Verdict:** the model likely understates vaccine deaths per dollar by 3-10x relative to Gavi's own claims. Gavi's
claims are themselves VIMC model outputs.
- **New finding L-42 (Major, direction under):** the vaccine death pathway is conservative relative to VIMC/Gavi. VIMC
  country-level deaths averted per US$ would settle it (DR-09).
- Confidence: Medium.

### Global level: WHO burden as a ceiling

| Disease | WHO burden (2024) | Model extra deaths, Full US Exit | Share |
|---|---|---|---|
| HIV | 570,000 deaths in 2025 (UNAIDS 2026) | about 200,000 a year | about 35% |
| TB | 1.23M deaths (WHO GTB 2025) | about 92,000 a year | 7.5% |
| Malaria | 610,000 deaths (WHO WMR 2025) | about 77,000 a year | 13% |

- Global burdens are larger than the 70-country model totals.
- None of the extra-death figures exceeds the existing burden: plausible.

## Country benchmarks

### South Africa (HIV)

| Source | Result |
|---|---|
| UCT/Wits Thembisa modelling for the National Department of Health (preliminary, reported April 2025, GroundUp / EWN) | "between 56,000 and 65,000 additional HIV-related deaths ... by 2028", rising to 500,000-700,000 by 2045 |
| CEPAC (Mass General Brigham, Feb 2025) | full PEPFAR cut: 601,000 HIV deaths over 10 years; 50% cut: 315,000 |
| Model, Full US Exit | 122,376 HIV deaths 2026-30, plus most of 64,882 further deaths 2031-35 |

**Verdict:**
- Prorating Thembisa (about 60k by 2028, 3.5 years) to 5 years gives about 90-100k. The model is 25-35% above it.
- The model is about 40% of CEPAC's per-year rate.
- Within the published range.

The Thembisa costing study ("The cost of the plunge", PMC12262123) projects 2025-2044 with a 2024-coverage baseline.
Its exact deaths figure was not read (UNVERIFIED).

### Mozambique, Kenya, Nigeria, Uganda, Tanzania

**No country-specific published estimate was found** for 2026-2030 deaths from US cuts. Searched: country names plus
"PEPFAR cut deaths modelling 2025".
- Optima's 26-country paper reports country results in its appendix, which was not accessible (Lancet 403).
- The appendix would settle this (DR-11).

**Model values (Full US Exit, 5-year deaths):**

| Country | Deaths |
|---|---|
| Mozambique | 184,307 |
| Nigeria | 217,884 |
| Tanzania | 160,806 |
| South Africa | 151,103 |
| Kenya | 126,146 |
| Democratic Republic of the Congo | 122,945 |
| Uganda | 122,702 |

### India, Indonesia, Philippines, Pakistan (TB)

- **Model:** TB dominates their small totals (India 13,233 TB deaths; Philippines 19,329).
- **Context:** donor TB money is a small share of national TB spending in these countries. Large private sectors mean
  continuity is likely above 15% (L-14).
- **Benchmarks:** none country-specific found (UNVERIFIED).

## Gaps that cannot be fully explained

1. **HIV infections** (L-41): 1.55M vs 4.4-10.8M (Optima) and 6M (UNAIDS). Explained in direction by L-01 and
   `cpia_ref`, but the size is not tested.
2. **Vaccine deaths per dollar** (L-42): 3-10x below Gavi's own claim. Partly scope (lifetime vs under-5, full
   schedule vs marginal). The rest is unquantified.
3. Everything else is explained by scope (Cavalcanti), the concept issue (L-01), or is within the published range
   (TB, malaria, South Africa).
