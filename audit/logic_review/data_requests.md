# Part 8: Data request list

**Order:** by how much each dataset would improve the model. "Sensitivity" refers to `sensitivity.csv` (all-country
deaths 2026-2030, Full US Exit, no response) or to the tested effects in `findings.md`.

**Saving:** save every file in `datasets/`, which is not in git, under the exact name given.

**Before you start:**
- Some sites need a free account (noted in the steps).
- If a page has moved, search for the dataset title in quotes; the publisher keeps the same title across releases.

---

## DR-01. PEPFAR people on ART by country, and PEPFAR expenditure by programme area

- **Replaces:** the ART population concept (L-01 reading B, L-41) and the "donor-funded share" cap (L-44).
- **Why it matters:** `art_hazard_mult` is the largest sensitivity (-18.6% / +23.3%), and L-01 can move the headline
  by +7% to +130%. Knowing how many people are on PEPFAR-supported ART in each dashboard country, and what share of
  ART cost PEPFAR pays (ARVs vs staff vs above-site), settles which reading is right.
- **Dataset:** PEPFAR Panorama Spotlight (data.pepfar.gov):
  - (1) "MER Results", indicator **TX_CURR** (people currently on ART), by country, FY2023-FY2025;
  - (2) "Financial" / "Expenditure Analysis" by program area (C&T = care and treatment; ASP = above-site programs;
    PM = program management), FY2023-FY2025, by country.
- **Steps:**
  1. Go to https://data.pepfar.gov/ and click **Datasets**.
  2. Find "MER Results" (country level). Download the CSV for the latest fiscal years. If it asks, choose
     "Operating Unit / Country" level.
  3. Save it as `datasets/PEPFAR_MER_TX_CURR_country_FY2023-25.csv`.
  4. Back on Datasets, find "Expenditure" or "Financial Data" by program area, and download it for FY2023-FY2025.
  5. Save it as `datasets/PEPFAR_expenditure_program_area_FY2023-25.csv`.
- **Countries:** every country on the dashboard with PEPFAR programmes (about 40).
- **Format:** CSV.

## DR-02. WHO Global TB Programme data files

- **Replaces:**
  - `DR_TB_SHARE`, `DR_TB_COV` (class d);
  - TB continuity via private-sector notifications (L-14);
  - TB treatment outcomes;
  - national TB budgets and funding sources (donor share, for L-44).
- **Why it matters:** `continuity` swings -23.8% / +18.0%; TB unit cost -8.1% / +11.7%; TB is 23% of deaths.
- **Dataset:** WHO Global Tuberculosis Programme, "TB data" CSV files (the 2026 release is due about November 2026;
  use the latest).
- **Steps:**
  1. Go to https://www.who.int/teams/global-programme-on-tuberculosis-and-lung-health/data
  2. Under "Download data as CSV files", download each of:
     - "Case notifications" → save as `datasets/WHO_TB_notifications.csv`. Contains the public-private mix columns;
       look for `priv_new_dx`. Variable names are UNVERIFIED; the data dictionary on the same page lists them.
     - "MDR/RR-TB burden estimates" → `datasets/WHO_TB_MDR_RR_estimates.csv`
     - "Treatment outcomes" → `datasets/WHO_TB_outcomes.csv`
     - "Budgets" and "Expenditure and utilisation" → `datasets/WHO_TB_budget.csv`, `datasets/WHO_TB_expenditure.csv`
       (these include funding from domestic sources, the Global Fund, USAID and others)
     - "Data dictionary" → `datasets/WHO_TB_data_dictionary.csv`
- **Years and countries:** latest year; all countries (the files are global).
- **Format:** CSV.

## DR-03. 2024-2025 aid by recipient country (a baseline closer to now)

- **Replaces:** the 2021-23 baseline (L-06).
- **Why it matters:** US health aid fell 67% in 2025 (IHME FGH 2025). The IHME file in `datasets/` has recipient
  detail only to 2023: 2024 and 2025 are global totals only (checked: country-coded DAH = 0 for 2024-2025).
- **Datasets:**
  - (a) **ForeignAssistance.gov** country-level US obligations and disbursements by sector, FY2023-FY2025;
  - (b) **Global Fund** disbursements by country and component, 2021-2025 (Data Explorer);
  - (c) **Gavi** country disbursements (already in `datasets/Gavi-Country-Financial-Data-FY2021-25_*.xlsx`; no
    download).
- **Steps for (a):**
  1. Go to https://foreignassistance.gov/data.
  2. Download "Complete dataset" (CSV); it is large.
  3. Save it as `datasets/ForeignAssistance_complete_FY2026Q4.csv` (use the quarter shown on the page).
  4. If it is too large, use the filter page: choose "Health" sector, fiscal years 2023-2025, transaction types
     "Obligations" and "Disbursements", then Download.
- **Steps for (b):**
  1. Go to https://data.theglobalfund.org/
  2. Choose "Disbursements", filter years 2021-2025, and group by "Geography" and "Component" (HIV, TB, Malaria,
     RSSH).
  3. Export CSV and save as `datasets/GlobalFund_disbursements_2021-2025.csv`.
  4. Also export "Allocations" for the 2023-2025 and 2026-2028 cycles (GC7 and GC8) and save as
     `datasets/GlobalFund_allocations_GC7_GC8.csv`. This also serves IMP-13.

## DR-04. Country donor share of HIV, TB, malaria and immunization spending (WHO GHED disease accounts)

- **Replaces:** the implicit 100% donor-funded assumption in the proportional-cap branch (L-44).
- **Also:** gives an external check on "Aid at Risk" relative to total disease spending.
- **Dataset:** WHO Global Health Expenditure Database, "Disease and condition" spending by financing source (HIV/AIDS
  and other STDs, Tuberculosis, Malaria, Vaccine-preventable diseases), latest available years (country coverage
  varies).
- **Steps:**
  1. Go to https://apps.who.int/nha/database/Select/Indicators/en
  2. Under "Expenditure by disease and conditions", tick the HIV/AIDS, TB, malaria and vaccine-preventable diseases
     indicators, including "of which external".
  3. Select all countries and all years, then Download → Excel.
  4. Save as `datasets/WHO_GHED_disease_spending.xlsx`.

## DR-05. WUENIC 2025 immunization coverage, from the source

- **Replaces:** DTP3 2024 via the WDI mirror (L-17).
- **Dataset:** WHO/UNICEF Estimates of National Immunization Coverage, 2025 revision (released July 2026), all
  antigens (DTP3, PCV3, ROTAC, MCV1, HepB3, MAL).
- **Steps:**
  1. Go to https://immunizationdata.who.int/ → "Download data" → "Immunization coverage" (WUENIC).
  2. Download the Excel file for all countries and antigens.
  3. Save as `datasets/WUENIC_2025_revision.xlsx`.
- **Why the extra antigens:** PCV3 and rotavirus coverage let the vaccine line model the Gavi-funded antigens (L-18).

## DR-06. UNAIDS 2026 estimates (AIDSinfo)

- **Replaces:**
  - new HIV infections (WDI 2024 → UNAIDS 2025);
  - AIDS-related deaths 2025 (replaces the GBD-2019-based `hiv_deaths_est`, L-11);
  - pregnant women needing ARVs (replaces the 1.15-factor fallback for 10 countries);
  - uncertainty bounds for people living with HIV (Part 4).
- **Steps:**
  1. Go to https://aidsinfo.unaids.org/ → "Download" (top right) or "Data sheet".
  2. Choose indicators:
     - "New HIV infections (all ages)";
     - "AIDS-related deaths (all ages)";
     - "People living with HIV (all ages)" with lower and upper estimates;
     - "Pregnant women needing ARVs for PMTCT";
     - "Coverage of pregnant women who receive ARV for PMTCT".
  3. Choose all countries and years 2015-2025, then download CSV.
  4. Save as `datasets/UNAIDS_AIDSinfo_2026.csv`.

## DR-07. Evidence on what happens to patients when donor support stops (continuity)

- **Replaces:** `continuity` (second-largest sensitivity, -23.8% / +18.0%; class c).
- **Datasets:**
  - (a) PEPFAR FY2025 quarterly TX_CURR and IIT ("interruption in treatment", TX_ML) by country (same Panorama site
    as DR-01). Save as `datasets/PEPFAR_MER_TX_ML_FY2024-25.csv`. TX_ML counts patients lost or interrupted, so it
    shows how much of the 2025 cut actually became interruption.
  - (b) UNAIDS 2025 funding-cut situation reports (country surveys of facility closures and service disruptions):
    https://www.unaids.org/en/topic/funding-cuts. Save the PDFs in `datasets/UNAIDS_situation_reports/`.

## DR-08. Unit costs from the Global Health Cost Consortium (GHCC) Unit Cost Study Repository

- **Replaces:** income-group TB costs and extrapolated ART costs (`uc_art_mult` -10.6% / +14.5%; `uc_tb_mult` -8.1% /
  +11.7%; IMP-03). Also DR-TB costs under current regimens (L-16).
- **Steps:**
  1. Go to https://ghcosting.org/pages/data/ucsr/app/ (free registration may be needed).
  2. Filter Disease = HIV, Intervention = ART; download all records (Export → CSV). Save as
     `datasets/GHCC_UCSR_HIV_ART.csv`.
  3. Repeat with Disease = TB, Intervention = "Treatment" (DS and DR), and save as `datasets/GHCC_UCSR_TB.csv`.
- **Also:** Sweeney et al. 2024, *Lancet Global Health*, supplementary appendix (cost per person treated, India,
  Philippines, South Africa, Georgia, etc.). Download the appendix PDF from the article page and save as
  `datasets/Sweeney2024_TB_costs_appendix.pdf`.

## DR-09. VIMC / Gavi deaths averted per vaccinated child, by country and vaccine

- **Replaces:** `imm_deaths_per_child_ref` with the U5MR/50 scaling (L-18, L-19, L-42).
- **Why it matters:** the model may understate vaccine deaths per dollar 3-10x relative to Gavi's claims.
- **Dataset:** Vaccine Impact Modelling Consortium, central estimates of deaths averted per 1,000 vaccinated, by
  country, vaccine and year.
- **Steps:**
  1. VIMC data are released on request: go to https://www.vaccineimpact.org/ → "Data access" and request "central
     burden estimates and impact ratios, 2021-2030, all Gavi countries". UNVERIFIED that they will release them; Gavi
     publishes impact summaries in its annual progress reports.
  2. As a fallback, download Toor et al. 2021, *eLife* ("Lives saved with vaccination for 10 pathogens across 112
     countries"), supplementary file with country x vaccine impact ratios. Save as
     `datasets/Toor2021_VIMC_impact_ratios.xlsx`.

## DR-10. UN World Population Prospects 2024: projections of births and population, 2026-2030

- **Replaces:** fixed 2024 births and population (L-24).
- **Steps:**
  1. Go to https://population.un.org/wpp/downloads, "CSV format".
  2. Download "Demographic Indicators (Medium variant)", all countries, 1950-2100.
  3. Save as `datasets/WPP2024_Demographic_Indicators_Medium.csv`.
  4. If the 2026 revision is listed, take that instead (UNVERIFIED whether it is out).

## DR-11. Optima country results (ten Brink et al. 2025 appendix)

- **Replaces:** nothing in the model. Gives country-level benchmarks for HIV deaths and infections (`benchmarks.md`).
- **Steps:** open the article (DOI 10.1016/S2352-3018(25)00074-8) → "Supplementary Materials" → download the appendix
  PDF. Save as `datasets/tenBrink2025_Optima_appendix.pdf`.

## DR-12. MOU texts: co-financing schedules

- **Replaces:** "no government response" in the MOU preset (L-08).
- **Dataset:** the signed MOU texts; KFF links each one in its tracker (`datasets/KFF_MOU_Tracker_2026-10-08.xlsx`,
  column with document links).
- **Steps:**
  1. For each country with a schedule (16), open the MOU PDF from the KFF link.
  2. Copy the partner government's co-financing commitments by year into a sheet with columns: iso3, year,
     domestic_commitment_usd, currency, nominal_or_real, page reference.
  3. Save as `datasets/MOU_cofinancing_commitments.xlsx`. Your team's `co-financing_MOU.xlsx` may already hold part of
     this; extend it.

## DR-13. IHME DAH next release (2027) with 2024 recipient detail

**No action now.** When IHME publishes the next DAH database (usually with Financing Global Health, around
mid-2027), download it from GHDx exactly as for the current file and save it under its own name. It will allow a 2024
baseline.

## DR-14. WHO malaria death series (already on disk)

**No download needed.** `ext_data/gho/MALARIA_EST_DEATHS.csv` already has 2000-2024 deaths by country. Using it for
the malaria death trend (L-25) needs only a code change.

---

## Summary table

| ID | Dataset | Fixes | Sensitivity it addresses | Needed for |
|---|---|---|---|---|
| DR-01 | PEPFAR TX_CURR and expenditure | L-01, L-41, L-44 | art_hazard_mult ±20%; headline +7% to +130% | Do before presenting |
| DR-02 | WHO TB data files | L-14, L-16, L-44 | continuity ±20%; TB cost ±10% | Do before presenting |
| DR-03 | ForeignAssistance.gov; Global Fund disbursements | L-06 | aid at risk (order of tens of %) | Do before presenting |
| DR-04 | WHO GHED disease spending | L-44 | 3-5% | Do before presenting |
| DR-05 | WUENIC 2025 | L-17, L-18 | small; credibility | Nice to have |
| DR-06 | UNAIDS AIDSinfo 2026 | L-11, L-24, Part 4 | small; Validation page | Do before presenting |
| DR-07 | PEPFAR TX_ML; UNAIDS situation reports | continuity | ±20% | Do before presenting |
| DR-08 | GHCC UCSR; Sweeney 2024 | IMP-03, L-16 | uc_art ±12%, uc_tb ±10% | Do before presenting |
| DR-09 | VIMC impact ratios | L-18, L-19, L-42 | vaccines (6% of deaths, possibly 3-10x) | Nice to have |
| DR-10 | WPP 2024 projections | L-24 | about +2-5% | Nice to have |
| DR-11 | Optima appendix | benchmarks | none | Nice to have |
| DR-12 | MOU co-financing | L-08 | MOU preset (could more than halve it) | Do before presenting, if MOUs are shown |
| DR-13 | IHME 2027 DAH | L-06 | baseline | later |
| DR-14 | WHO malaria deaths (on disk) | L-25 | -0.8% | Do now (no download) |
