# Part 4: Uncertainty, scope and reproducibility

## a) Uncertainty

### What is varied

`draw_params` (`health_model.py:136-152`) draws each of the 33 rows of `model_params.csv` 400 times from a
triangular(low, central, high) distribution, seed 7.

| Property | What the code does |
|---|---|
| Displayed central value | the run with every parameter at its central value (not the mean or median of the draws) |
| Displayed "range" | the 2.5th and 97.5th percentiles of the 400 draws |
| Draws within a country | every parameter independent of every other |
| Draws across countries | identical: same seed, same order, so draw i uses the same values in every country (perfect correlation across countries) |

### Inputs that should move together but are drawn independently

| Pair | Why they should be correlated | Effect of drawing them independently |
|---|---|---|
| `uc_art_mult`, `asd_share`, `uc_tb_mult` | One overhead and costing uncertainty: if PEPFAR overhead is higher, both ART and TB full costs rise | Range too narrow for money-to-people. The two largest cost drivers, asd ±15% and uc_art ±12%, partly cancel |
| `art_hazard_mult`, `art_transmission` | Both depend on how many people actually stop ART vs move to thinner care | Range somewhat too narrow |
| `mal_vc_eff`, `mal_cm_eff`, `mal_resurgence` | All depend on local transmission intensity | Small |
| `tb_cfr_untreated_neg`, `tb_cfr_untreated_pos` | WHO derives both from the same historical cohorts | Small |
| `imm_deaths_per_child_ref`, `imm_u5_share` | Both come from the same VIMC model runs | Small |

No published correlation structure exists for these. Proposed fix: a joint "cost" draw and a joint "ART severity"
draw (IMP-09).

### What is not varied at all

| Source of uncertainty | Size (evidence) | Direction |
|---|---|---|
| ART death concept (full-cost equivalents vs supported patients; L-01) | Readings span 2.1M to 4.5M total deaths vs 1.97M central (`URGENT.md`) | Range far too narrow; mostly upward |
| Aid baseline year (2021-23 vs 2024-25; L-06) | US health aid fell 67% in 2025 (IHME FGH 2025); Aid at Risk for US exits could fall by a similar order if measured from 2025 | Downward for the remaining cut; levels unchanged for deaths vs 2021-23 service levels |
| Baseline burden and coverage (UNAIDS, WHO, MAP have their own uncertainty bounds) | PLHIV 41.0M [37.6-45.0M] (UNAIDS 2026); MAP cases vs WHO differ >30% in 20 of 46 countries | Both ways; adds roughly ±10% |
| Aid data (IHME DAH estimation, channel imputation) | IHME does not publish uncertainty for DAH | Unknown |
| Scenario values (OECD cuts, Gavi 15%, MOU schedules) | Fixed per preset; each preset is effectively its own scenario | Not a statistical uncertainty; presented as scenarios, which is correct |
| Model structure (LiST form, cohort hazards, fixed counterfactual, no system effects) | Benchmarks differ by 2-4x (`benchmarks.md`) | Both ways |
| Continuity / private sector by country | One global value | Both ways |

### Adding up country ranges (L-02)

The All Countries total range is the sum of each country's 2.5th and 97.5th percentiles (`model_section.py:1657-1658`,
`:1848`). Because draws are identical across countries, the right total is the percentile of the summed draws.

Measured (Full US Exit, no response, 70 countries, 400 draws; `range_test.py`, run from the repository root):

| Quantity | 2026-2030 deaths |
|---|---|
| Central run | 1,969,304 |
| Sum of country percentiles (displayed) | 1,342,123 - 2,806,374 |
| Percentiles of the summed draws (correct) | 1,393,470 - 2,704,309 |
| Mean / median of summed draws | 1,971,158 / 1,942,795 |

- **Width:** the displayed range is 11% wider than the correct one (1.46M vs 1.31M). Summing percentiles overstates
  the range, because countries are driven by different parameters (ART for Mozambique, TB and malaria for Nigeria).
- **Severity:** Minor (under 3% at each end) but easy to fix (IMP-10).

### What the "95% range" can be called

- **What it is:** the range from drawing the model's parameters within their stated low-high bounds.
- **Not a confidence or credible interval:**
  - it excludes the dominant uncertainties above (the ART concept, data, baseline year, structure);
  - the triangular low-high bounds are themselves mostly judgments (22 genuine assumptions; `assumptions.md`).
- **Suggested label:** "Range across parameter values (2.5th-97.5th percentile of 400 draws); does not include
  uncertainty in the data or the model's structure."
- **Current text:**
  - The dashboard says "95% range" in the headline cards (`model_section.py:912`) and "range" elsewhere.
  - Methods explains the draws (`model_section.py:487`).
  - **L-02 (Presentation/Major):** "95%" invites a reading as a statistical confidence interval.

## b) Scope omissions

| Omission | Likely direction of bias in deaths | Rough size, with evidence |
|---|---|---|
| Other health aid: maternal and child health (non-vaccine), nutrition, family planning, NTDs, WASH, emergency health | Under | Cavalcanti et al. 2025 (*Lancet*): an 83% USAID cut gives >14M all-age deaths by 2030, of which HIV 25%, malaria and NTDs about 22%, plus large shares from diarrhoea, respiratory infections and nutrition. The model covers roughly half the causes they model (`benchmarks.md`) |
| Countries not on the dashboard (28.5% of country-coded disease aid; "Global" US$2.67B/yr) | Under | Myanmar, Afghanistan, Sudan, Yemen and Chad have high burden; maybe +10-25% if deaths scale with aid (Low confidence) |
| Health-system and supply-chain effects beyond kappa (procurement, drug stock-outs across programmes, data systems, surveillance) | Under | Not quantified. USAID funded much of the supply chain (GHSC-PSM) and DHS surveys |
| Staff losses: donor-paid health workers (e.g. about 50,000 PEPFAR-funded health workers; UNVERIFIED) | Under | Partly captured via above-site share and kappa |
| Effects after 2035, and lost epidemic control (HIV incidence rebound, TB transmission beyond 2 years, malaria resurgence beyond growth 0.10) | Under | Optima: infections 4.4-10.7M by 2030; each infection carries lifetime deaths |
| Behavioral responses (people seeking care privately, reduced testing) | Both ways | Continuity (0.15) is the only lever |
| Other donors or governments stepping in (beyond the response options) | Over | PEPFAR FY25 ART counts were stable despite 2025 cuts; other donors cut too (UK -39% health, IHME) |
| Drug resistance (HIV after interruptions; artemisinin partial resistance) | Under, long term | Not quantified |
| Price changes (BPaLM, lenacapavir PrEP, cheaper nets) | Over (costs too high give too few people losing) or under | DR-TB small |
| Indirect health effects of economic shocks | Under | Not in scope |
| Population growth and epidemic trends in need (L-24) | Under for growing-need countries | Births in sub-Saharan Africa are rising about 2%/yr (WPP); PLHIV about 1%/yr |

## c) Reproducibility

**How the rebuild was run.**
- **Environment:** a clean Python 3.13 virtual environment, built from `requirements.txt` only, in the scratchpad.
- **Code:** a fresh clone of `real-modeling-check` at `12e15a9`.
- **Data:** `datasets/` linked read-only.
- **Commands:** the documented commands from README "Rebuild everything from `datasets/`", in order:

```
python malaria_inputs.py
python fiscal_inputs.py --download
python prepare_model.py --dah ... --spend ... --expected ... --gdp ... --mou ...
python add_constant_dollars.py
```

Then `git status` and a cell-by-cell comparison were run against the committed files.

| Output | Result |
|---|---|
| `model_data/dah_lines.csv`, `ihme_trend.csv`, `panel.csv`, `regressions.json`, `mou_signed.csv`, `country_profile.csv` | **Byte-identical** |
| All six `model_data/all_countries_<preset>.csv` (precomputed All Countries results) | **Byte-identical**. Rebuilt totals match the dashboard: Full US Exit 1,969,304; MOUs 360,307; IHME 1,485,463; OECD 1,777,310; Global Fund & Gavi 682,633; Combined 2,155,022 |
| `model_data/country_inputs.csv` | **Numerically identical** (all 156 columns equal within 1e-9). The text differs in the last 1-2 digits of some floats (e.g. `0.0225783611269629` vs `0.022578361126962987`), a float-printing difference between the pandas version that wrote the committed file and the clean environment's |
| `ext_data/map/`, `macro_data/weo_fiscal/` (MAP and WEO, rebuilt from `datasets/` and the IMF API) | Identical (no git difference) |
| `macro_data/` and `spending_data/` constant-dollar columns (`add_constant_dollars.py`) | Identical |

**What could not be rebuilt.**
1. **Per-country files for Sections 1-3** (`country_data/`, `spending_data/`, `macro_data/`, `revenue_data/`,
   `cofog_all/`). The scripts that built them are not in the repository (README says so). Only the constant-dollar
   columns can be regenerated. **L-38 (Minor, reproducibility).**
2. **`ext_data/` WDI, GHO and Gapminder series** were not re-downloaded: `--download` was not used, and the
   open-numbers mirror changes over time. A rebuild with `--download` today would pull newer series, so the result
   would legitimately differ. Pin and archive the downloaded vintage (IMP-12).
3. **`fiscal_inputs.py --download`** fetches the WEO from the IMF API each time. The October 2026 vintage gives the
   same values today; after April 2027 it won't. The raw response is saved in `datasets/`, which is not in git.

**Warnings during rebuild.** pandas PerformanceWarnings (frame fragmentation, `prepare_model.py:441-442`) and one
divide-by-zero in a log (no effect on outputs). None changes results.
