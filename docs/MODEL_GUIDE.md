# Model guide: every piece of code and data, and how to keep modeling

This is the long companion to [`CLAUDE.md`](../CLAUDE.md). It describes the repository as it is on `main`: what each
module and each data file is, where the data came from, how the pieces connect, how to regenerate derived files, and
the modeling decisions behind the current numbers. Where `README.md` or `docs/SPEC.md` disagree with this file
(mostly about deaths, which the dashboard no longer shows), the code and this file are current.

Contents

1. [The pipeline](#1-the-pipeline)
2. [Code modules](#2-code-modules)
3. [Data catalogue](#3-data-catalogue)
4. [The Announced donor cuts model](#4-the-announced-donor-cuts-model-announcement_modelproject_cutspy)
5. [The service model: money to coverage](#5-the-service-model-money-to-coverage-health_modelpy)
6. [What the Dashboard shows, and which function draws it](#6-what-the-dashboard-shows-and-which-function-draws-it)
7. [Regenerating derived data](#7-regenerating-derived-data)
8. [Recipes for further modeling](#8-recipes-for-further-modeling)
9. [Decision log](#9-decision-log)
10. [Open questions](#10-open-questions)
11. [Gotchas](#11-gotchas)

---

## 1. The pipeline

```
 STAGE 1  raw downloads (datasets/, in .gitignore; only needed to rebuild)
          IHME DAH 1990-2026, IHME health spending 1995-2023 + expected 2024-2050, IHME GDP, MAP malaria,
          KFF MOU tracker, team MOU co-financing sheet, IMF WEO / WoRLD / COFOG, UNAIDS, WHO, Gavi financials,
          aid_cut_projections_announcements.xlsx (announcements workbook)
             |
 STAGE 2  preparation scripts (run by hand, repo root)
          prepare_model.py  (calls who_inputs.apply -> malaria_inputs.apply, fiscal_inputs.apply)
          batch34_inputs.py, hiv_transmission_inputs.py, add_constant_dollars.py
          announcement_model/project_cuts.py
             |
 STAGE 3  processed inputs, committed
          model_data/  ext_data/  macro_data/  spending_data/  country_data/  revenue_data/  cofog_all/
          model_params.csv  unit_cost_reference.csv  announcement_model/oda_history.csv
             |
 STAGE 4  model (pure Python, no Streamlit)
          scenarios.build_scenario(preset)  ->  health_model.Scenario
          health_model.run_country(iso3, scenario, Fiscal, inputs, params, cut_path, gov_add_usd)
          health_model.announcement_totals / announcement_sources   (all health aid, not just 4 diseases)
          budget_section.py (Section 3 boxes)
             |
 STAGE 5  display (Streamlit)
          app.py -> views/1_Dashboard.py, views/2_All_Countries.py, views/4_Methods.py
                    model_section.py, paths_ui.py, theme.py
```

Two money bases run side by side, on purpose:

| | Base | Scope | Used for |
|---|---|---|---|
| Announcement totals | 2019-2023 average, COVID money included | all health aid, every health area | money-lost headline, known vs predicted chart, phase-out by funder, the "Can X fill the gap?" fiscal panel |
| Service model | 2021-2023 average (`dah_lines.csv`) | HIV, TB, malaria, immunization only | people losing each service, coverage drop by year |

The cut **ratio** per country x donor group x channel group from the announcement model is applied to the
service-model cells, so the same % cut lands on a smaller, disease-only base (see `health_model.Scenario.cuts_by_year`).

---

## 2. Code modules

### Runtime (imported when the app runs)

| File | What it does | Key names |
|---|---|---|
| `app.py` | Sets up `st.navigation` with the pages in `theme.PAGES`; re-writes session-state keys with prefixes `m_`, `mb_`, `c1_`, `c2_`, `c3b_`, `c4_year_` so widget values survive page switches. | `PERSIST_PREFIXES` |
| `views/1_Dashboard.py` | Main page. Loads per-country files from `country_data/`, `spending_data/`, `macro_data/`, `revenue_data/`, `cofog_all/`; draws the header, lede, Sections 1-3 and calls `model_section.render_model_section` for Section 4. | `DEFAULT_COUNTRY = "Kenya"`, `FACT_YEAR = 2026`, `MAP_FRAME` |
| `views/2_All_Countries.py` | Every country under the chosen scenario (map, scatter, top-15); thin wrapper around `model_section.cross_country`. Uses precomputed files when settings are default. | |
| `views/3_Validation.py` | Comparisons with published estimates. **Hidden from navigation** (not in `theme.PAGES`), kept working. | |
| `views/4_Methods.py` | Methods write-up; reads parameters and regression estimates from the model's own files. Still describes deaths in places. | |
| `model_section.py` | All Streamlit UI for the model (~2,300 lines). Caches, scenario bar, story lede, known-vs-predicted chart, phase-out by funder, "Where the Money Is Lost", per-service coverage grid + "Biggest Drops", fiscal panel, budget sliders, All Countries tables. | `_inputs` (cache_resource), `_run`, `run_ctl`, `scenario_bar`, `announced_path`, `known_vs_predicted_chart`, `phase_out_by_donor_chart`, `_service_grid`, `_drop_overview_html`, `_fiscal_panel`, `with_all_aid`, `budget_sliders`, `SHOW_GOV_OPTIONS`, `SHOW_BRIEF` |
| `health_model.py` | The model (~1,800 lines, no Streamlit). Inputs, `Scenario` (cuts per cell per year), `Fiscal` (government response), `run_country`, `run_all`, fiscal space, unit costs, coverage, plus the (unshown) mortality chain, regressions cross-checks, `policy_money` (Abuja / tax targets). | `load_inputs`, `load_params`, `draw_params`, `Scenario`, `Fiscal`, `run_country`, `run_all`, `announcement_totals`, `announcement_sources`, `known_loss_by_year`, `policy_money`, `health_budget`, `tax_effort`, `TREAT_SHARE`, `YEAR0 = 2026`, `AID_BASE_YEARS` |
| `scenarios.py` | Donor presets and their descriptions; `build_scenario(preset, opts, ci)`; MOU helpers (`mou_signed`, `mou_schedule`, `mou_group` A/B/C); funding-path shapes; precomputed file paths; `scenario_key` (JSON cache key). | `PRESETS`, `ANNOUNCED`, `UI_PRESETS`, `DEFAULT_FISCAL`, `PATH_SHAPES` |
| `paths_ui.py` | "How Funding Changes" path selector, per-year sliders chart, outcome pills. | |
| `budget_section.py` | Section 3 revenue/spending boxes as numbers (% of GDP), reconciled to IMF WEO totals. | |
| `theme.py` | Colors, fonts, Plotly template, CSS, page list, `section_header`, `source_html`. Every color comes from here. | `PAGES`, `DISEASE_COLORS` |
| `country_lists.py` | The 71 dashboard countries (`ALLOWED_COUNTRIES`); prepare_model keeps a wider panel for regressions. | |
| `malaria_inputs.py` | Imported at runtime only for a constant; mainly a prep script (see below). | |

### Offline (data preparation; run by hand)

| File | What it writes | Notes |
|---|---|---|
| `prepare_model.py` | Everything in `model_data/` except `announcement_*.csv`: `dah_lines.csv`, `ihme_trend.csv`, `country_inputs.csv`, `panel.csv`, `regressions.json`, `mou_signed.csv`, `country_profile.csv`, `all_countries_<preset>[_draws].csv`. | Needs the raw IHME CSVs + MOU sheet (+ KFF tracker). `--download` refreshes `ext_data/`. `--precompute-only` only reruns the all-country results. `MOU_SCHEDULE_EXTRA` holds yearly US amounts for MOUs not in the team sheet (Zambia). `BASE_YEARS = (2021, 2023)`. |
| `announcement_model/project_cuts.py` | `model_data/announcement_cuts.csv`, `model_data/announcement_areas.csv`, audit tables in `announcement_model/output/` (`rows_v4.csv`, `donor_targets_v4.csv`, `us_no_mou_v4.csv`, `fit_v4.txt`; not committed). | Needs the announcements workbook. See section 4. |
| `who_inputs.py` | Patches `country_inputs.csv` with WHO GHO HIV and malaria values (`ext_data/gho/`). Each column gets `_year` and `_source`. | Called by prepare_model. |
| `malaria_inputs.py` | `ext_data/map/` from raw MAP downloads; patches malaria coverage, cases and the malaria death trend. | `--apply-only` skips the raw files. |
| `fiscal_inputs.py` | Interest / revenue for the debt-stress factor; `macro_data/weo_fiscal/`. | `--download` uses the IMF API. |
| `batch34_inputs.py` | Patches `country_inputs.csv`: unspecified-money purpose shares (Global Fund modules), ART and TB unit costs, donor share of disease spending. | Reads evidence tables in `audit/logic_review/`. |
| `hiv_transmission_inputs.py` | HIV transmission rate per unsuppressed person (UNAIDS). | Needs `datasets/UNAIDS_2026/`. |
| `add_constant_dollars.py` | `gdp_usd_bn_2023` in `macro_data/`, `ghes_per_gdp_mean` in `spending_data/`. | |

### Checks

| Path | What |
|---|---|
| `tests/` | pytest, ~375 tests, ~1 min. `test_announcement.py` covers the announced preset, coverage-only UI, per-year services, phase-out, fiscal panel. `conftest.py::ihme_split` fixture pins `TREAT_SHARE=None`. `baseline_sudden.json` (+ `make_baseline.py`) is a regression baseline. |
| `audit/` | `AUDIT.md` (issue log I-01...), per-issue notes, `checks.py` (`--quick` / `--full`), `recompute.py` + `compare_recompute.py` (independent recalculation), `snapshot_numbers.py` (every displayed number, for before/after diffs), `logic_review/` (evidence tables and an independent reproduction). |
| `model_sourced_update/` | An early standalone copy of the model and its README. **Not used**; do not edit it. |

---

## 3. Data catalogue

All dollar values are constant 2023 US$ unless noted. IHME DAH values are in **thousands** of US$ in the raw and
per-country files (`*_dah_23` columns, `base_kusd`); `dah_lines.csv` is in US$.

### Per-country folders (Dashboard Sections 1-3)

| Folder | One file per | Content | Source / vintage | Built by |
|---|---|---|---|---|
| `country_data/` | country **name** (`Kenya.csv`), 72 files | IHME DAH by year x source x channel, with every health-focus-area and program-area column (`hiv_treat_dah_23`, `nch_cnv_dah_23`, `oid_covid_dah_23`, ...) | IHME Financing Global Health DAH database 1990-2026 (release 2026-09-18) | earlier script (not in repo) |
| `spending_data/` | ISO3 | Total health spending by source (government, prepaid private, out-of-pocket, DAH), totals and per capita; `projected` flag for 2024+ | IHME Global Health Spending 1995-2023 + Expected Health Spending 2024-2050 | earlier script; `add_constant_dollars.py` adds `ghes_per_gdp_mean` |
| `macro_data/` | ISO3 | GDP (current US$ bn), population, revenue / expenditure / net lending / debt % of GDP; `gdp_usd_bn_2023` (constant) | IMF World Economic Outlook (Oct 2026); header uses the 2026 values | earlier script; `add_constant_dollars.py` |
| `macro_data/weo_fiscal/` | one file | WEO general-government balances, for interest costs | IMF WEO Oct 2026 via api.imf.org | `fiscal_inputs.py` |
| `revenue_data/` | ISO3 | Government revenue by type (taxes, grants, ...) % of GDP and of revenue, with coverage level | IMF World Revenue Longitudinal Data (WoRLD) | earlier script |
| `cofog_all/` | ISO3 | Government spending by function (COFOG) % of outlays and GDP | IMF GFS COFOG | earlier script |

### `model_data/` (model inputs and outputs)

| File | Content | Built by | Read by |
|---|---|---|---|
| `dah_lines.csv` | Baseline aid, US$/yr, 2021-23 average: `iso3, src_grp, chan_grp, usd, line, bucket`. One row per country x donor group x channel group x service line (see section 5 for lines). | prepare_model | `hm.load_inputs` |
| `country_inputs.csv` | One row per country, ~220 columns: people in need and coverage per service (+ `_year`, `_source`), unit costs, donor shares, unspecified-money purpose shares, fiscal data (`ghes_2023`, growth percentiles, debt, interest), epidemiology, MOU yearly US amounts `mou_us_2026..2030` and reference `mou_us_ref`. | prepare_model, then patched by who/malaria/fiscal/batch34/hiv_transmission scripts | everything |
| `ihme_trend.csv` | IHME 2025 preliminary / 2021-23 ratio by donor group x channel x bucket | prepare_model | IHME preset; project_cuts (non-DAC trend) |
| `announcement_cuts.csv` | **The Announced donor cuts projection.** `iso3, src_grp, chan_grp, base_kusd` (2019-23 avg, k$), `cut_<y>` (total cut share), `known_cut_<y>` (part from published numbers), `mou_pred_cut_<y>` (US bilateral in no-MOU countries), y = 2026-2030. | project_cuts.py | `hm.load_announcement_cuts`, `announcement_totals`, `announcement_sources` |
| `announcement_areas.csv` | Loss by health area (HIV, TB, Malaria, Vaccines, COVID-19, Health systems, ...): `base_kusd`, `lost_<y>`, `known_<y>`. Each flow's loss split by its own 2019-23 area mix. | project_cuts.py | analysis only (not drawn) |
| `mou_signed.csv` | Signed America First MOUs: date, total US funding, source | prepare_model (KFF tracker, 2026-10-08) | `scenarios.mou_signed`, project_cuts |
| `country_profile.csv` | Region, income group, MOU status | prepare_model | Dashboard header |
| `panel.csv`, `regressions.json` | Country-year panel and fixed-effects estimates (fiscal replacement, coverage dose-response, Poisson death regressions) | prepare_model | Methods, cross-checks |
| `all_countries_<preset>.csv`, `..._draws.csv` | `run_all` results for each non-Custom preset at default settings, and the 400 draw totals | `prepare_model.py --precompute-only` | All Countries page |

### `ext_data/` (external series, committed so the build is offline-reproducible)

| Folder | Content | Source |
|---|---|---|
| `wdi/` | World Bank WDI series used by the model (ART/PMTCT coverage, TB detection, DTP3, population, mortality, health share of government spending, debt, revenue) | Gapminder `open-numbers` mirror of WDI on GitHub (`prepare_model.py --download`) |
| `sg/`, `gm/` | Gapminder Systema Globalis / fasttrack (TB incidence, PLHIV, child deaths by cause, IHME HIV death share) | Gapminder GitHub |
| `gho/` | WHO GHO HIV and malaria estimates | WHO GHO API (`who_inputs.py --download`) |
| `map/` | Malaria Atlas Project national series: treatment, ITN use, IRS, Pf/Pv cases, incidence | MAP, downloaded 2026-10-13 |
| `reference/` | Series not used by the model. **Exception:** `project_cuts.py` reads `reference/wdi/ny_gdp_pcap_cd.csv` and `reference/wdi/sh_xpd_ghed_gd_zs.csv` to fill government health spending for the similar-country rule. Don't delete them. | WDI / Gapminder |
| `wb_country_entities.csv`, `who_regions.csv` | Country metadata | WDI, WHO |

### Root and `announcement_model/` data

| File | Content |
|---|---|
| `model_params.csv` | Every model parameter: `param, label, central, low, high, unit, status (sourced/assumption), source`. Drawn as triangular(low, central, high). Editable live in the app's parameter editor. |
| `unit_cost_reference.csv` | Study unit costs (ART site cost by country, Rosen et al. 2021; TB cost by income group), with cost year; inflated with CPI-U to 2023. |
| `announcement_model/oda_history.csv` | Each DAC donor's total ODA 2019-2025 (US$ bn), used for O_d,y in the donor health-budget path. |

### Not in the repo (needed only to rebuild)

`datasets/` raw files, listed with sources in README ("Untracked raw files"). Plus
`aid_cut_projections_announcements.xlsx`, the announcements workbook with sheets `Base_Projection` (flows with
IHME 2019/2022/2023 DAH and a `Rule` per flow), `Donor_ODA` (ODA 2024, filled 2025-2028 outlook), `US_MOU` (per
country: prior US funding, flat whole-agreement multiplier, years, year-by-year source) and `GF_Allocations`
(GC7 original/reduced and GC8 ratios by country). Ask the repository owner for it.

---

## 4. The Announced donor cuts model (`announcement_model/project_cuts.py`)

The only donor preset shown besides Custom. One cut per flow f = (recipient, original donor, channel), per year
2026-2030. Flow f keeps `B_f x m_f,y` in year y, where B_f is the 2019-2023 average (COVID money included; for
workbook countries without yearly files, the mean of 2019, 2022, 2023).

Rules, in the order they are applied (the docstring at the top of the script is the authoritative list):

| Flow | Multiplier m_f,y kept | Known or predicted |
|---|---|---|
| Global Fund (money from every donor) | 2026 = reduced GC7 / original GC7; 2027 = GC8 / GC7; 2028-30 continue the GC7->GC8 change at (GC8/GC7)^(1/3) a year. Where no allocation: 12.64/15.7. | 2026-27 known, rest predicted |
| Gavi | 6.0 / 8.8 for every donor (new-money pledges Gavi 6.0 vs Gavi 5.0); US = 0 | known |
| US through WHO | 0 | known |
| US bilateral + US NGOs with an MOU | MOU's yearly ratio (amount / prior US funding), from the yearly schedule, or whole-agreement ratio x the average schedule shape | known |
| US bilateral, no MOU | 0 from 2026; tracked as `mou_pred_cut_<y>` | predicted ("Predicted MOU cut") |
| US through NGOs, no MOU | mean whole-agreement ratio of the 3 MOU countries with the closest log(aid / government health spending), all within ±log(1.5); else prior-funding-weighted MOU average; spread with the schedule shape | predicted |
| Sweden / UK country exits, UK Africa bilateral path, Netherlands health budget (384/510) and UNICEF (0.5) | as announced | known |
| Foundations, private, non-DAC | IHME 2025 / 2021-23 ratio for that donor group | predicted |
| Every other DAC flow | donor target `B_d x exp(alpha) x O_d,y^eps` minus everything already fixed for that donor, shared equally over its remaining flows: `clip((target - fixed) / rest, 0, 1)` | predicted |

`O_d,y` = donor's total ODA in y / its 2019-23 average = (2025 actual / 2019-23 avg) x (outlook y / outlook 2025);
2029-30 extend the 2025-28 trend. `alpha, eps` come from a WLS fit across donor groups of log(IHME 2025 health
ratio) on log(OECD 2025 ODA ratio), weighted by base, Japan excluded (lumpy Gavi payment). Last fit: health fell
~21% beyond what total aid explains and moves ~0.28x with it.

The Global Fund cut is part of each donor's total (it is a "fixed" flow in the balancing step), so nothing is cut
twice. Outputs are aggregated to the repo's donor groups and channel groups (`src_grp`, `chan_grp`).

How the service model reads it: `hm.load_announcement_cuts` builds `{(iso3, src_grp, chan_grp): 5 cuts}` with
fallbacks to `(iso3, src_grp)`, then pooled `("*", src_grp, chan_grp)` and `("*", src_grp)`.
`Scenario(announcement=True).cuts_by_year` looks up each `dah_lines` cell with `hm.announcement_lookup`.

---

## 5. The service model: money to coverage (`health_model.py`)

Per country, per year t = 2026..2030 (`hm.YEAR0`):

1. **Cells.** Rows of `dah_lines.csv` for the country. Service lines:
   HIV `hiv_art`, `hiv_pmtct`, `hiv_prev`, `hiv_ovc`, plus `hiv_care_ct` (testing and care, linked to ART);
   TB `tb_ds`, `tb_dr`; malaria `mal_itn`, `mal_irs`, `mal_cm`; immunization `imm`; plus per-disease
   `*_unspec` (program area not reported) and `*_hss` (systems). IHME program-area columns per line are in
   `prepare_model.LINES`.
2. **Gross loss** = cell usd x cut[t] x cut_path[t]. A rise in aid counts as no loss (gains not modeled).
3. **Effective money by line.** Unspecified money is split by the country's Global Fund module purpose shares
   (`unspec_<disease>_{treatment,prevention,testing,rssh,pm}`): treatment/prevention to those lines by the
   country's mix, testing partly (kappa) toward treatment, systems joins HSS money (no direct service effect,
   `hss_service_share` default 0), programme management is non-service. `TREAT_SHARE = None` keeps IHME's split.
4. **Government response** (`Fiscal`): `none` (default), `custom` (replace a share), `max`, `gradual`, capped by
   fiscal space = GHES x (strong-year minus typical GHES growth) x debt stress; allocation pro-rata. Extra money
   from the budget sliders arrives as `gov_add_usd` (see `policy_money`).
5. **People losing a service** = net loss / unit cost, capped at the donor-funded pool (people covered x donor
   share of that disease's spending). Unit costs from `country_inputs.csv` and `model_params.csv`.
6. **Coverage drop (pp)** = people losing the service / people in need x 100, per year
   (`cov_drop_pp_<year>`), plus the 5-year average (`cov_drop_pp`).
7. **Uncertainty.** `draw_params` draws every parameter 400 times (seed 7); results report median and 2.5-97.5%.

Main outputs of `run_country`: `res["lines"]` (per service: `base_usd`, `gross_loss_usd`, `replaced_usd`,
`net_loss_usd`, `unit_cost`, `need`, `cov0`, `units_lost[_lo/_hi]`, `cov_drop_pp`, and `net_loss_<y>`,
`units_lost_<y>`, `cov_drop_pp_<y>`), `res["buckets"]`, `res["years"]` (aid lost, response, gov_add, replaced, gap per
year), `res["cells"]`, `res["fiscal"]`, `res["totals"]`. Death columns exist but are not shown.

---

## 6. What the Dashboard shows, and which function draws it

Top to bottom on `views/1_Dashboard.py`:

| Block | Function / data |
|---|---|
| Header: country name, chips (region, income, GDP 2026, population 2026), small region map | Dashboard code; `country_profile.csv`, `macro_data/` (IMF WEO 2026 current US$; falls back to the latest year) |
| Scenario bar (preset: Announced donor cuts or Custom; phase-out by funder list + chart) | `ms.scenario_bar`, `ms._controls`, `ms.phase_out_by_donor_chart` (`announcement_sources`) |
| Lede: money lost headline | `ms.story_lede` (`announcement_totals`) |
| Known vs predicted aid lost (red known, blue predicted MOU cut, light red predicted) | `ms.known_vs_predicted_chart` / `ms.announced_path` |
| Money spent on health over time | `spending_data/` |
| Who is providing the money; where the aid is spent | `country_data/` |
| Section 4: Where the Money Is Lost (by disease, by donor x channel) | `ms._loss_by_bucket_fig`, `ms._who_cut_fig` |
| Service Coverage, Year by Year: small multiples per service; "Biggest Drops" popover (red >= 10 pp, amber 5-10) | `ms._service_grid`, `ms._drop_overview_html` |
| Can the government fill the gap? (all health aid lost under Announced) | `ms._fiscal_panel(ms.with_all_aid(...))` |
| Revenue and Spending, with budget sliders (`bud_share_<iso>`, `bud_tax_<iso>`) | `budget_section.py`, `ms.budget_sliders` -> `hm.policy_money` -> `gov_add` |
| Footer: constant-2023-US$ note and input years | `ms.inputs_years_line` |

---

## 7. Regenerating derived data

| You changed | Run |
|---|---|
| `project_cuts.py` or the announcements workbook | `python announcement_model/project_cuts.py <workbook.xlsx>` then `python prepare_model.py --precompute-only` |
| `model_params.csv` or anything in `health_model.py` that changes numbers | `python prepare_model.py --precompute-only` |
| MOU schedule for a country not in the team sheet | add it to `prepare_model.MOU_SCHEDULE_EXTRA`, rebuild (or patch `mou_us_<y>` in `country_inputs.csv` the same way), then rerun project_cuts and precompute |
| Raw IHME / MAP / IMF files | full rebuild, in the order in README ("Rebuild everything from `datasets/`") |

Then `python -m pytest tests -q`, and for model changes `python audit/snapshot_numbers.py audit/before.csv` /
`after.csv` to diff every displayed number.

---

## 8. Recipes for further modeling

- **Try the model in a notebook.** See the snippet in `CLAUDE.md`. `hm.run_all(sc, hm.Fiscal(), I, P, n_draws=80)`
  gives one row per country.
- **New donor scenario.** Add a description to `scenarios.PRESETS`, a branch in `build_scenario` that sets
  `Scenario` fields (`src_direct`, `src_multi`, `pair`, `chan`, or a per-cell yearly table like `announcement`), and
  add it to `UI_PRESETS` if it should be shown. Precompute and add a test.
- **Change an announcement rule.** Edit the rule loop in `project_cuts.py` (the `for i in range(N)` block), keep
  `KN` (known) and `PM` (predicted MOU) flags right, rerun, and check `announcement_model/output/rows_v4.csv`.
- **New parameter.** Add a row to `model_params.csv` (low/central/high, status, source), read it from `P[...]` in
  `health_model.py`; it is drawn automatically and appears in the Methods table.
- **New input column.** Write it from a prep script into `country_inputs.csv` with `_year` and `_source`; read it
  with `_v(row, col, default)` so a missing value falls back cleanly.
- **New outcome model (e.g. Optima HIV for coverage -> infections).** Keep it out of the UI unless the owner asks;
  coverage-only is the current rule. Optima HIV installs from GitHub (`optimamodel/optima`, GPLv3) and runs ~0.5 s
  per simulation but needs a calibrated country project.

---

## 9. Decision log

Dated choices behind the current numbers (2026). Each was reviewed and approved before it went in.

| Date | Decision |
|---|---|
| 10-21 | US cuts come only from announcements; no modeled probability of signing an MOU. Cuts progressive through 2030. |
| 10-21 | Announcement base = 2019-2023 average including COVID money. GF GC7->GC8 change continues yearly. GF cut counts inside each donor's total; the rest spread over the donor's other channels (no double counting). Gavi-wide 6.0/8.8 ratio, US separate. Health-vs-total-aid elasticity from IHME 2025. Disbursement ignored. US NGO money counted with US bilateral. |
| 10-21 | No inflation adjustment of Gavi / Global Fund / MOU ratios. |
| 10-21 | Dashboard shows only Announced donor cuts + Custom; headline = money lost. Dashboard is coverage-only (no deaths user-facing); Validation hidden. |
| 10-21 | Global Fund cut is one across-the-board % per country applied to IHME's GF split by disease. |
| 10-21 | Per-year service results (`*_<year>` columns); coverage-by-year charts. |
| 10-21 | 80%-to-treatment rule tried, then dropped: `TREAT_SHARE = None` (IHME split, every service). Coverage section = one chart per service + Biggest Drops. Minimal subtitle text. |
| 10-21 | Abuja (15% of government spending) and tax-to-15%-of-GDP options built, phased 20%/yr to 2030; checkboxes hidden (`SHOW_GOV_OPTIONS = False`); budget sliders at the page bottom instead. |
| 10-21 | Fiscal panel uses all health aid lost under Announced (2019-23 base); service model stays on the 4 diseases, 2021-23. |
| 10-22 | Header: country facts as chips; GDP = IMF 2026 current US$. |
| 10-22 | No-MOU countries: only US **bilateral** = 0 from 2026 (blue "Predicted MOU cut"); US money through NGOs keeps the 3-similar-MOU-countries rule. Zambia's yearly MOU amounts added (`MOU_SCHEDULE_EXTRA`). |
| 10-22 | An MOU HIV money optimizer was prototyped and not merged; a separate implementation is in progress outside this repo. |

---

## 10. Open questions

- Should World Bank / development-bank **lending** (loans, "Development-bank lending" donor group) count in the
  funding gap?
- Source of the `Donor_ODA` sheet's 2024 figures in the workbook (they don't match OECD exactly).
- Whether the service model should move to the 2019-23 base and/or drop COVID money from losses (currently the
  headline uses 2019-23 with COVID; services use 2021-23 four-disease money; across all countries about 69% of the 2026 headline loss and 57% of the
  2030 loss is outside the four diseases (Kenya: 75% and 44%) and has no service effect).
- Whether more of the money that has no service effect (HSS, testing, unspecified) should map to people.

---

## 11. Gotchas

- **Streamlit Cloud hot-swap.** Merging to the deployed branch swaps code without restarting; `model_section._inputs`
  (`st.cache_resource`) keeps the old `load_inputs()` dict. New keys must be read with `.get()` and a fallback, or
  reboot the app from the Streamlit Cloud menu.
- Precomputed All Countries files are stale after any model change until you rerun `--precompute-only`.
- `prepare_model.BASE_YEARS` and `health_model.AID_BASE_YEARS` must match (a test checks).
- `country_data/` is keyed by country name; `spending_data/`, `macro_data/`, `revenue_data/`, `cofog_all/` by ISO3.
  Guyana has no 2023 IHME baseline in the projection and uses the pooled fallback cuts.
- `ext_data/reference/wdi/` is read by `project_cuts.py` despite the folder's README.
- `audit/before_*.csv` / `after_*.csv` snapshots are git-ignored; regenerate them.
- Plotly geo maps fetch topojson from cdn.plot.ly; offline or sandboxed screenshots show a blank map.
- Pages live in `views/`, never `pages/`.
- Widget keys: prefix with `m_` (or another `PERSIST_PREFIXES` entry) to keep values across pages; data editors
  (`m_params`, `m_custom_tbl`) cannot be persisted that way.
