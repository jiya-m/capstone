# CLAUDE.md

Guide for Claude (or anyone) working in a fork of this repository. Read this first, then
[`docs/MODEL_GUIDE.md`](docs/MODEL_GUIDE.md) for the full catalogue of code, data and modeling decisions.

## What this is

A Streamlit dashboard on health financing in 71 low- and middle-income countries, and a model of what announced
donor cuts (US, Global Fund, Gavi, other DAC donors) do to **health aid** and then to **service coverage** for HIV,
TB, malaria and immunization, 2026-2030. Dollar figures are constant 2023 US$ unless noted (MOU amounts are nominal).

The chain, end to end:

```
raw downloads (datasets/, untracked)
  -> prep scripts (prepare_model.py + who_inputs / malaria_inputs / fiscal_inputs / batch34_inputs / ...)
  -> processed inputs in git (model_data/, ext_data/, macro_data/, country_data/, spending_data/, ...)
  -> announcement_model/project_cuts.py  -> model_data/announcement_cuts.csv  (yearly cut per country x donor x channel)
  -> health_model.run_country(): money lost -> government response -> people losing each service -> coverage drop
  -> model_section.py + views/1_Dashboard.py (Streamlit)
```

## Run and test

```
python -m pip install -r requirements-dev.txt
python -m streamlit run app.py                 # http://localhost:8501; everything it reads is in git
python -m pytest tests -q                      # ~375 tests, about 1 minute; run before every commit
python audit/checks.py --quick                 # broader consistency checks, ~2 minutes
```

Use the model without Streamlit (notebooks, batch runs):

```python
import health_model as hm, scenarios as scn
I, P = hm.load_inputs(), hm.load_params()
sc = scn.build_scenario(scn.ANNOUNCED, {}, I["ci"])          # or "Custom" with scn.default_opts("Custom", I["ci"])
res = hm.run_country("KEN", sc, hm.Fiscal(), I, P, n_draws=400)
res["lines"][["line", "base_usd", "net_loss_usd", "cov_drop_pp_2030"]]   # per service line
res["years"]                                                            # per year: aid lost, replaced, gap
```

## Where things live (one line each; details in docs/MODEL_GUIDE.md)

| Path | Role |
|---|---|
| `app.py` | Navigation only (`st.navigation`); pages are in `views/` (not `pages/`, which Streamlit would auto-load). |
| `views/1_Dashboard.py` | The main page: header, lede, spending/aid charts, Section 4 (model), revenue & spending. |
| `views/2_All_Countries.py`, `views/4_Methods.py` | All-country view; methods write-up. `views/3_Validation.py` exists but is hidden from the nav. |
| `model_section.py` | All Streamlit UI for the model: scenario bar, charts, coverage grid, fiscal panel, caches. |
| `health_model.py` | The model itself, no Streamlit: `load_inputs`, `Scenario`, `Fiscal`, `run_country`, `run_all`, `policy_money`. |
| `scenarios.py` | Donor presets -> `hm.Scenario`; funding-path shapes; MOU helpers; precomputed-file paths. |
| `announcement_model/project_cuts.py` | Builds the "Announced donor cuts" projection from the announcements workbook. |
| `prepare_model.py` | Rebuilds `model_data/` from IHME raw files; `--precompute-only` reruns the all-country results. |
| `paths_ui.py`, `budget_section.py`, `theme.py`, `country_lists.py` | Funding-path UI, Section 3 boxes, design system, country list. |
| `model_params.csv`, `unit_cost_reference.csv` | Every model parameter (central/low/high, sourced vs assumption, citation); unit-cost studies. |
| `tests/`, `audit/` | pytest suite; audit report, independent recomputation, before/after snapshots. |
| `docs/SPEC.md`, `docs/file_inventory.md` | Compact model specification; which file is used by what. |
| `model_sourced_update/` | Stale early copy of the model. Not imported by anything. Ignore it. |

## Regenerating derived data

- Announced cuts (after changing `project_cuts.py` or the workbook): `python announcement_model/project_cuts.py <aid_cut_projections_announcements.xlsx>`
  then `python prepare_model.py --precompute-only`. The workbook is **not in the repo**; get it from the project owner.
- Model parameters (after editing `model_params.csv`): `python prepare_model.py --precompute-only`.
- Full rebuild from raw IHME/MAP/IMF/KFF files: see README "Rebuild everything from `datasets/`".
- Never hand-edit files in `model_data/`; regenerate them. If a script patches `country_inputs.csv` in place
  (who/malaria/fiscal/batch34/hiv_transmission inputs), note it in the commit.

## Modeling decisions you must keep (unless the owner changes them)

1. **Coverage only.** No deaths anywhere user-facing (the model still computes deaths internally; leave it, don't show it).
   Headline = money lost. No LiST/Optima outcome model.
2. **US cuts come only from announcements** (America First MOUs). No modeled probability of signing an MOU.
3. **No MOU -> US bilateral aid = 0 from 2026**, shown separately as the blue "Predicted MOU cut"
   (`mou_pred_cut_<year>`). US money **through NGOs** in no-MOU countries follows the 3 MOU countries with the
   closest aid / government-health-spending ratio (all within ±50%), else the all-MOU average.
4. **Announcement base = 2019-2023 average including COVID money.** The service model's per-line base
   (`dah_lines.csv`) is the 2021-23 average for the four diseases. The cut *ratios* carry across; the dollar bases differ.
5. **Global Fund:** reduced GC7 (2026), GC8 (2027), then the GC7->GC8 change continues yearly. One across-the-board %
   per country, applied to IHME's GF split by disease. Counted inside each donor's total (no double counting).
6. **Gavi:** one Gavi-wide ratio 6.0/8.8 for all donors; the US is 0.
7. **Other DAC flows:** donor health budget target = f(total ODA path) from a WLS fit of IHME 2025 health vs OECD
   2025 total aid; whatever the donor's fixed cuts leave is shared as one equal cut over its other channels.
8. **No inflation adjustment** of Gavi / Global Fund / MOU ratios (nominal ratios). Disbursement lags are ignored.
9. **Service split = IHME program areas** (`hm.TREAT_SHARE = None`). The 80%-to-treatment rule was tried and dropped.
10. Cuts are progressive through 2030 (yearly), not a one-time shock. Gains in aid are not modeled (a rise = no cut).

The owner wants to vet every modeling choice: **propose, show the worked math for one MOU country (Kenya) and one
non-MOU country, and wait for approval before changing model logic.** Estimate unknowns with an explicit
statistical/economic model rather than a plugged-in guess, and explain it step by step.

## Gotchas

- **Streamlit Cloud hot-swaps code on merge without restarting.** `model_section._inputs()` is `st.cache_resource`
  and keeps the old `load_inputs()` output. Any new key you add to `load_inputs()` must be read with
  `.get()` and a fallback (see `Scenario.cuts_by_year` and `_announcement_cuts_default`), or the app must be rebooted.
- Precomputed `model_data/all_countries_<preset>*.csv` go stale whenever the model or inputs change; regenerate them.
- `prepare_model.BASE_YEARS` must equal `health_model.AID_BASE_YEARS` (tested).
- `country_data/` files are named by country name (`Kenya.csv`); most other per-country folders by ISO3.
- Plotly's geo topojson loads from cdn.plot.ly; in sandboxes that block it, header maps render blank in screenshots.
- `scenarios.UI_PRESETS` (Announced, Custom) are the only presets shown; the others stay for tests and audit.
- Hidden UI kept in code: `ms.SHOW_GOV_OPTIONS = False` (Abuja / tax checkboxes), `ms.SHOW_BRIEF = False`, Validation page.
- Session-state keys starting `m_`, `mb_`, `c1_`... persist across pages (`app.py`); name new widgets accordingly.
- README.md and docs/SPEC.md predate the coverage-only switch and still describe deaths. When they disagree with the
  code, the code and this file win.

## Conventions

- Model code stays Streamlit-free (`health_model.py`, `scenarios.py`, `budget_section.py`) so it can be tested.
- Every parameter goes in `model_params.csv` with low/central/high, `status` and a citation, not as a magic number.
- Docstrings end with "Feeds: ..." saying which output uses the function; keep that up when adding functions.
- Add or update a test in `tests/` for every model change; `tests/conftest.py::ihme_split` pins the IHME split.
- Dashboard text: minimal subtitles, title case headings (`model_section.title_case`), colors only from `theme.py`.
