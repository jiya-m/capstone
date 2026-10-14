# File inventory

Every tracked file, whether it is used when the app runs, only by offline scripts (data preparation, audit, tests), or not at all, with the evidence (which code references it). Per-country folders are listed once, with their file count. Generated from `git ls-files` on the cleanup branch.

| File or folder | Size | Status | Evidence |
|---|---|---|---|
| `.devcontainer/devcontainer.json` | 1 KB | config | Streamlit / Codespaces / git configuration |
| `.gitattributes` | 0 KB | config | Streamlit / Codespaces / git configuration |
| `.gitignore` | 1 KB | config | Streamlit / Codespaces / git configuration |
| `.streamlit/config.toml` | 1 KB | config | Streamlit / Codespaces / git configuration |
| `README.md` | 2 KB | docs | documentation |
| `README_MODEL.md` | 7 KB | docs | documentation |
| `add_constant_dollars.py` | 3 KB | offline (code) | audit/test/prep script, run by hand |
| `app.py` | 1 KB | runtime (code) | imported by app.py / views/ (directly or through model_section, health_model) |
| `audit/AUDIT.md` | 45 KB | offline (audit/test output or reference) | written or read by audit/ or tests/ scripts |
| `audit/I-01.md` | 9 KB | offline (audit/test output or reference) | written or read by audit/ or tests/ scripts |
| `audit/I-02_I-03_I-08.md` | 11 KB | offline (audit/test output or reference) | written or read by audit/ or tests/ scripts |
| `audit/I-05.md` | 5 KB | offline (audit/test output or reference) | written or read by audit/ or tests/ scripts |
| `audit/I-06_I-11_malaria.md` | 17 KB | offline (audit/test output or reference) | written or read by audit/ or tests/ scripts |
| `audit/I-07.md` | 8 KB | offline (audit/test output or reference) | written or read by audit/ or tests/ scripts |
| `audit/I-09_I-27_I-04.md` | 13 KB | offline (audit/test output or reference) | written or read by audit/ or tests/ scripts |
| `audit/I-10.md` | 4 KB | offline (audit/test output or reference) | written or read by audit/ or tests/ scripts |
| `audit/I-13_I-14_I-15_I-16.md` | 10 KB | offline (audit/test output or reference) | written or read by audit/ or tests/ scripts |
| `audit/I-26_I-17.md` | 10 KB | offline (audit/test output or reference) | written or read by audit/ or tests/ scripts |
| `audit/METHOD.md` | 13 KB | offline (audit/test output or reference) | written or read by audit/ or tests/ scripts |
| `audit/analysis.json` | 18 KB | offline (audit/test output or reference) | written or read by audit/ or tests/ scripts |
| `audit/archive/README.md` | 1 KB | offline (audit/test output or reference) | written or read by audit/ or tests/ scripts |
| `audit/archive/analysis.py` | 18 KB | offline (code) | audit/test/prep script, run by hand |
| `audit/checks.py` | 39 KB | offline (code) | audit/test/prep script, run by hand |
| `audit/checks_results.csv` | 8.00 MB | offline (audit/test output or reference) | written or read by audit/ or tests/ scripts |
| `audit/checks_summary.csv` | 3 KB | offline (audit/test output or reference) | written or read by audit/ or tests/ scripts |
| `audit/checks_summary.md` | 3 KB | offline (audit/test output or reference) | written or read by audit/ or tests/ scripts |
| `audit/compare_recompute.py` | 5 KB | offline (code) | audit/test/prep script, run by hand |
| `audit/cosmetic_fixes.md` | 6 KB | offline (audit/test output or reference) | written or read by audit/ or tests/ scripts |
| `audit/fallbacks.csv` | 3 KB | offline (audit/test output or reference) | written or read by audit/ or tests/ scripts |
| `audit/fiscal_diff.py` | 4 KB | offline (code) | audit/test/prep script, run by hand |
| `audit/hiv_diff.py` | 5 KB | offline (code) | audit/test/prep script, run by hand |
| `audit/i01_before_after.py` | 3 KB | offline (code) | audit/test/prep script, run by hand |
| `audit/i07_diff.py` | 3 KB | offline (code) | audit/test/prep script, run by hand |
| `audit/inventory.csv` | 25 KB | offline (audit/test output or reference) | written or read by audit/ or tests/ scripts |
| `audit/make_inventory.py` | 20 KB | offline (code) | audit/test/prep script, run by hand |
| `audit/malaria_diff.py` | 4 KB | offline (code) | audit/test/prep script, run by hand |
| `audit/minor_diff.py` | 4 KB | offline (code) | audit/test/prep script, run by hand |
| `audit/minor_diff_counts.csv` | 6 KB | offline (audit/test output or reference) | written or read by audit/ or tests/ scripts |
| `audit/outliers.csv` | 41 KB | offline (audit/test output or reference) | written or read by audit/ or tests/ scripts |
| `audit/recompute.py` | 19 KB | offline (code) | audit/test/prep script, run by hand |
| `audit/recompute_compare.csv` | 87 KB | offline (audit/test output or reference) | written or read by audit/ or tests/ scripts |
| `audit/recompute_notes.md` | 6 KB | offline (audit/test output or reference) | written or read by audit/ or tests/ scripts |
| `audit/recompute_results.csv` | 0.12 MB | offline (audit/test output or reference) | written or read by audit/ or tests/ scripts |
| `audit/sensitivity.csv` | 9 KB | offline (audit/test output or reference) | written or read by audit/ or tests/ scripts |
| `audit/snapshot_numbers.py` | 7 KB | offline (code) | audit/test/prep script, run by hand |
| `budget_section.py` | 7 KB | runtime (code) | imported by app.py / views/ (directly or through model_section, health_model) |
| `cofog_all/ (46 files)` | 0.92 MB | runtime (data) | folder read by: views/1_Dashboard.py; offline: audit/checks.py |
| `cofog_data/ (20 files)` | 39 KB | unused | folder read by: - |
| `country_data/ (72 files)` | 83.53 MB | runtime (data) | folder read by: views/1_Dashboard.py; offline: audit/checks.py |
| `country_inputs.csv` | 83 KB | unused | stale copy (2026-10-07); every read and write uses model_data/country_inputs.csv |
| `country_lists.py` | 2 KB | runtime (code) | imported by app.py / views/ (directly or through model_section, health_model) |
| `dah_lines.csv` | 2.66 MB | unused | stale copy (2026-10-07); every read and write uses model_data/dah_lines.csv |
| `data_notes.txt` | 0 KB | unused | empty file |
| `ext_data/gho/HIV_0000000001.csv` | 0.12 MB | runtime (data) | read by: views/4_Methods.py; offline: who_inputs.py |
| `ext_data/gho/HIV_0000000016.csv` | 31 KB | runtime (data) | read by: views/4_Methods.py; offline: who_inputs.py |
| `ext_data/gho/HIV_0000000020.csv` | 34 KB | runtime (data) | read by: views/4_Methods.py; offline: who_inputs.py |
| `ext_data/gho/HIV_ARTCOVERAGE.csv` | 85 KB | runtime (data) | read by: views/4_Methods.py; offline: who_inputs.py |
| `ext_data/gho/MALARIA_EST_CASES.csv` | 79 KB | runtime (data) | read by: views/4_Methods.py; offline: who_inputs.py |
| `ext_data/gho/MALARIA_EST_DEATHS.csv` | 62 KB | runtime (data) | read by: views/4_Methods.py; offline: who_inputs.py |
| `ext_data/gho/MALARIA_EST_INCIDENCE.csv` | 0.11 MB | runtime (data) | read by: views/4_Methods.py; offline: who_inputs.py |
| `ext_data/gho/MALARIA_ITN_USE.csv` | 17 KB | offline (data) | read by: -; offline: who_inputs.py |
| `ext_data/gm/ddf--datapoints--ihme_hiv_death--by--country--time.csv` | 99 KB | offline (data) | read by: -; offline: prepare_model.py |
| `ext_data/map/incidence_prevalence.csv` | 0.65 MB | runtime (data) | read by: malaria_inputs.py |
| `ext_data/map/irs.csv` | 0.28 MB | runtime (data) | read by: views/1_Dashboard.py, views/3_Validation.py, views/4_Methods.py, model_section.py, health_model.py, scenarios.py, paths_ui.py, theme.py, budget_section.py, malaria_inputs.py; offline: prepare_model.py, who_inputs.py, fiscal_inputs.py, audit/archive/analysis.py, audit/checks.py, audit/compare_recompute.py, audit/fiscal_diff.py, audit/i01_before_after.py, audit/malaria_diff.py, audit/recompute.py, audit/snapshot_numbers.py, tests/make_baseline.py, tests/test_fiscal.py, tests/test_malaria.py, tests/test_mou.py, tests/test_paths.py |
| `ext_data/map/itn.csv` | 0.33 MB | runtime (data) | read by: views/4_Methods.py, model_section.py, health_model.py, malaria_inputs.py; offline: prepare_model.py, who_inputs.py, audit/checks.py, audit/make_inventory.py, audit/malaria_diff.py, audit/recompute.py, tests/test_malaria.py, tests/test_paths.py |
| `ext_data/map/pf_cases.csv` | 0.28 MB | runtime (data) | read by: views/3_Validation.py, malaria_inputs.py; offline: tests/test_malaria.py |
| `ext_data/map/pv_cases.csv` | 0.27 MB | runtime (data) | read by: views/3_Validation.py, malaria_inputs.py; offline: tests/test_malaria.py |
| `ext_data/map/treatment.csv` | 0.34 MB | runtime (data) | read by: views/3_Validation.py, views/4_Methods.py, model_section.py, health_model.py, malaria_inputs.py; offline: prepare_model.py, audit/archive/analysis.py, audit/checks.py, audit/make_inventory.py, audit/recompute.py, tests/make_baseline.py, tests/test_malaria.py, tests/test_paths.py |
| `ext_data/sg/ddf--datapoints--all_forms_of_tb_incidence_estimated--by--geo--time.csv` | 73 KB | runtime (data) | read by: model_section.py, health_model.py; offline: prepare_model.py, audit/recompute.py |
| `ext_data/sg/ddf--datapoints--all_forms_of_tb_number_of_deaths_estimated--by--geo--time.csv` | 69 KB | offline (data) | read by: -; offline: prepare_model.py |
| `ext_data/sg/ddf--datapoints--all_forms_of_tb_treatment_coverage_percent--by--geo--time.csv` | 60 KB | unused | read by: - |
| `ext_data/sg/ddf--datapoints--annual_hiv_deaths_number_all_ages--by--geo--time.csv` | 42 KB | unused | read by: - |
| `ext_data/sg/ddf--datapoints--hiv_deaths_in_children_1_59_months_total_deaths--by--geo--time.csv` | 67 KB | unused | read by: - |
| `ext_data/sg/ddf--datapoints--malaria_deaths_in_children_1_59_months_total_deaths--by--geo--time.csv` | 54 KB | offline (data) | read by: -; offline: prepare_model.py |
| `ext_data/sg/ddf--datapoints--malaria_number_of_cases_reported--by--geo--time.csv` | 24 KB | unused | read by: - |
| `ext_data/sg/ddf--datapoints--malaria_number_of_deaths_reported--by--geo--time.csv` | 10 KB | unused | read by: - |
| `ext_data/sg/ddf--datapoints--measles_deaths_in_children_1_59_months_total_deaths--by--geo--time.csv` | 60 KB | offline (data) | read by: -; offline: prepare_model.py |
| `ext_data/sg/ddf--datapoints--meningitis_deaths_in_children_1_59_months_total_deaths--by--geo--time.csv` | 75 KB | unused | read by: - |
| `ext_data/sg/ddf--datapoints--newly_hiv_infected_number_all_ages--by--geo--time.csv` | 48 KB | unused | read by: - |
| `ext_data/sg/ddf--datapoints--number_of_child_deaths--by--geo--time.csv` | 0.59 MB | unused | read by: - |
| `ext_data/sg/ddf--datapoints--people_living_with_hiv_number_all_ages--by--geo--time.csv` | 49 KB | offline (data) | read by: -; offline: prepare_model.py |
| `ext_data/sg/ddf--datapoints--pertussis_deaths_in_children_1_59_months_total_deaths--by--geo--time.csv` | 2 KB | unused | read by: - |
| `ext_data/sg/ddf--datapoints--pneumonia_deaths_in_children_1_59_months_total_deaths--by--geo--time.csv` | 79 KB | offline (data) | read by: -; offline: prepare_model.py |
| `ext_data/sg/ddf--datapoints--tb_hivplus_incidence_estimated--by--geo--time.csv` | 57 KB | offline (data) | read by: -; offline: prepare_model.py |
| `ext_data/sg/ddf--datapoints--tb_hivplus_number_of_deaths_estimated--by--geo--time.csv` | 56 KB | offline (data) | read by: -; offline: prepare_model.py |
| `ext_data/wb_country_entities.csv` | 53 KB | offline (data) | read by: -; offline: prepare_model.py |
| `ext_data/wdi/gc_dod_totl_gd_zs.csv` | 29 KB | runtime (data) | read by: health_model.py; offline: prepare_model.py |
| `ext_data/wdi/gc_rev_xgrt_gd_zs.csv` | 83 KB | runtime (data) | read by: health_model.py; offline: prepare_model.py |
| `ext_data/wdi/gc_xpn_intp_rv_zs.csv` | 77 KB | offline (data) | read by: -; offline: prepare_model.py, fiscal_inputs.py, audit/archive/analysis.py, tests/test_fiscal.py |
| `ext_data/wdi/gc_xpn_totl_gd_zs.csv` | 79 KB | offline (data) | read by: -; offline: prepare_model.py |
| `ext_data/wdi/ny_gdp_pcap_cd.csv` | 0.23 MB | unused | read by: - |
| `ext_data/wdi/sh_dth_comm_zs.csv` | 19 KB | unused | read by: - |
| `ext_data/wdi/sh_dth_imrt.csv` | 0.16 MB | unused | read by: - |
| `ext_data/wdi/sh_dth_mort.csv` | 0.16 MB | runtime (data) | read by: health_model.py; offline: prepare_model.py |
| `ext_data/wdi/sh_dyn_aids_zs.csv` | 68 KB | offline (data) | read by: -; offline: prepare_model.py |
| `ext_data/wdi/sh_dyn_mort.csv` | 0.16 MB | runtime (data) | read by: model_section.py, health_model.py; offline: prepare_model.py, audit/archive/analysis.py, audit/recompute.py |
| `ext_data/wdi/sh_dyn_nmrt.csv` | 0.14 MB | unused | read by: - |
| `ext_data/wdi/sh_hiv_0014.csv` | 43 KB | offline (data) | read by: -; offline: prepare_model.py |
| `ext_data/wdi/sh_hiv_artc_zs.csv` | 41 KB | runtime (data) | read by: model_section.py, health_model.py; offline: prepare_model.py, who_inputs.py, audit/archive/analysis.py, audit/checks.py, audit/recompute.py |
| `ext_data/wdi/sh_hiv_incd_tl.csv` | 70 KB | runtime (data) | read by: health_model.py; offline: prepare_model.py, audit/archive/analysis.py, audit/recompute.py |
| `ext_data/wdi/sh_hiv_pmtc_zs.csv` | 24 KB | runtime (data) | read by: model_section.py, health_model.py; offline: prepare_model.py, who_inputs.py, audit/archive/analysis.py, audit/checks.py, audit/recompute.py |
| `ext_data/wdi/sh_imm_hepb.csv` | 56 KB | unused | read by: - |
| `ext_data/wdi/sh_imm_idpt.csv` | 97 KB | runtime (data) | read by: model_section.py, health_model.py; offline: prepare_model.py, audit/checks.py, audit/recompute.py |
| `ext_data/wdi/sh_imm_meas.csv` | 95 KB | offline (data) | read by: -; offline: prepare_model.py |
| `ext_data/wdi/sh_mlr_incd_p3.csv` | 38 KB | runtime (data) | read by: model_section.py, malaria_inputs.py; offline: prepare_model.py, audit/archive/analysis.py |
| `ext_data/wdi/sh_mlr_nets_zs.csv` | 4 KB | runtime (data) | read by: model_section.py, malaria_inputs.py; offline: prepare_model.py, who_inputs.py, audit/archive/analysis.py, audit/checks.py |
| `ext_data/wdi/sh_mlr_tret_zs.csv` | 4 KB | runtime (data) | read by: model_section.py, malaria_inputs.py; offline: prepare_model.py, audit/archive/analysis.py, audit/checks.py |
| `ext_data/wdi/sh_mmr_dths.csv` | 94 KB | runtime (data) | read by: health_model.py; offline: prepare_model.py |
| `ext_data/wdi/sh_tbs_cure_zs.csv` | 53 KB | offline (data) | read by: -; offline: prepare_model.py |
| `ext_data/wdi/sh_tbs_dtec_zs.csv` | 60 KB | runtime (data) | read by: model_section.py, health_model.py; offline: prepare_model.py, audit/checks.py, audit/recompute.py |
| `ext_data/wdi/sh_tbs_incd.csv` | 65 KB | offline (data) | read by: -; offline: prepare_model.py |
| `ext_data/wdi/sh_uhc_sci.csv` | 56 KB | offline (data) | read by: -; offline: prepare_model.py |
| `ext_data/wdi/sh_uhc_sci_id.csv` | 56 KB | unused | read by: - |
| `ext_data/wdi/sh_xpd_ghed_gd_zs.csv` | 77 KB | unused | read by: - |
| `ext_data/wdi/sh_xpd_ghed_ge_zs.csv` | 79 KB | runtime (data) | read by: model_section.py, health_model.py; offline: prepare_model.py, audit/checks.py, audit/make_inventory.py |
| `ext_data/wdi/sp_dyn_cbrt_in.csv` | 0.21 MB | offline (data) | read by: -; offline: prepare_model.py |
| `ext_data/wdi/sp_dyn_cdrt_in.csv` | 0.21 MB | offline (data) | read by: -; offline: prepare_model.py |
| `ext_data/wdi/sp_pop_0014_to.csv` | 0.23 MB | offline (data) | read by: -; offline: prepare_model.py |
| `ext_data/wdi/sp_pop_1564_to.csv` | 0.23 MB | offline (data) | read by: -; offline: prepare_model.py |
| `ext_data/wdi/sp_pop_totl.csv` | 0.24 MB | runtime (data) | read by: model_section.py, health_model.py; offline: prepare_model.py, who_inputs.py, audit/archive/analysis.py, audit/make_inventory.py, audit/recompute.py |
| `fiscal_inputs.py` | 7 KB | offline (code) | audit/test/prep script, run by hand |
| `health_model.py` | 78 KB | runtime (code) | imported by app.py / views/ (directly or through model_section, health_model) |
| `ihme_trend.csv` | 38 KB | unused | stale copy (2026-10-07); every read and write uses model_data/ihme_trend.csv |
| `macro_data/ (72 files)` | 0.27 MB | runtime (data) | folder read by: views/1_Dashboard.py, health_model.py; offline: fiscal_inputs.py, add_constant_dollars.py, audit/checks.py, tests/test_minor.py |
| `macro_data/weo_fiscal/weo_balances.csv` | 0.45 MB | offline (data) | folder read by: -; offline: fiscal_inputs.py |
| `malaria_inputs.py` | 9 KB | runtime (code) | imported by app.py / views/ (directly or through model_section, health_model) |
| `model_data/all_countries_America_First_MOUs.csv` | 7 KB | runtime (data) | read by: views/3_Validation.py, model_section.py, scenarios.py; offline: prepare_model.py, audit/archive/analysis.py, audit/checks.py, audit/i01_before_after.py, audit/make_inventory.py, audit/snapshot_numbers.py, tests/test_i07.py, tests/test_mou.py |
| `model_data/all_countries_Combined_retreat.csv` | 28 KB | runtime (data) | read by: views/3_Validation.py, model_section.py, scenarios.py; offline: prepare_model.py, audit/archive/analysis.py, audit/checks.py, audit/i01_before_after.py, audit/make_inventory.py, audit/snapshot_numbers.py, tests/test_i07.py, tests/test_mou.py |
| `model_data/all_countries_Full_US_exit.csv` | 28 KB | runtime (data) | read by: views/3_Validation.py, model_section.py, scenarios.py; offline: prepare_model.py, audit/archive/analysis.py, audit/checks.py, audit/i01_before_after.py, audit/make_inventory.py, audit/snapshot_numbers.py, tests/test_i07.py, tests/test_mou.py |
| `model_data/all_countries_Global_Fund_Gavi_shortfalls.csv` | 28 KB | runtime (data) | read by: views/3_Validation.py, model_section.py, scenarios.py; offline: prepare_model.py, audit/archive/analysis.py, audit/checks.py, audit/i01_before_after.py, audit/make_inventory.py, audit/snapshot_numbers.py, tests/test_i07.py, tests/test_mou.py |
| `model_data/all_countries_IHME_2025_preliminary_estimates.csv` | 28 KB | runtime (data) | read by: views/3_Validation.py, model_section.py, scenarios.py; offline: prepare_model.py, audit/archive/analysis.py, audit/checks.py, audit/i01_before_after.py, audit/make_inventory.py, audit/snapshot_numbers.py, tests/test_i07.py, tests/test_mou.py |
| `model_data/all_countries_OECD_reported_2025_aid_cuts.csv` | 28 KB | runtime (data) | read by: views/3_Validation.py, model_section.py, scenarios.py; offline: prepare_model.py, audit/archive/analysis.py, audit/checks.py, audit/i01_before_after.py, audit/make_inventory.py, audit/snapshot_numbers.py, tests/test_i07.py, tests/test_mou.py |
| `model_data/country_inputs.csv` | 0.12 MB | runtime (data) | read by: views/4_Methods.py, health_model.py, malaria_inputs.py; offline: prepare_model.py, who_inputs.py, fiscal_inputs.py, audit/recompute.py, tests/make_baseline.py |
| `model_data/country_profile.csv` | 4 KB | runtime (data) | read by: views/1_Dashboard.py; offline: prepare_model.py, audit/make_inventory.py, tests/test_mou.py |
| `model_data/dah_lines.csv` | 2.21 MB | runtime (data) | read by: health_model.py; offline: prepare_model.py, audit/recompute.py |
| `model_data/ihme_trend.csv` | 37 KB | runtime (data) | read by: health_model.py; offline: prepare_model.py, audit/archive/analysis.py |
| `model_data/mou_signed.csv` | 9 KB | runtime (data) | read by: scenarios.py; offline: prepare_model.py |
| `model_data/panel.csv` | 1.12 MB | offline (data) | read by: -; offline: prepare_model.py |
| `model_data/regressions.json` | 5 KB | runtime (data) | read by: views/4_Methods.py, model_section.py, health_model.py; offline: prepare_model.py, audit/make_inventory.py |
| `model_params.csv` | 10 KB | runtime (data) | read by: model_section.py, health_model.py |
| `model_section.py` | 0.12 MB | runtime (code) | imported by app.py / views/ (directly or through model_section, health_model) |
| `panel.csv` | 0.89 MB | unused | stale copy (2026-10-07); every read and write uses model_data/panel.csv |
| `paths_ui.py` | 16 KB | runtime (code) | imported by app.py / views/ (directly or through model_section, health_model) |
| `prepare_model.py` | 36 KB | offline (code) | audit/test/prep script, run by hand |
| `prior_dashboard_versions/kenya_health_data.csv` | 6 KB | unused | earlier dashboard versions; no code imports or reads them |
| `prior_dashboard_versions/version_1.py` | 25 KB | unused | earlier dashboard versions; no code imports or reads them |
| `prior_dashboard_versions/version_2.py` | 20 KB | unused | earlier dashboard versions; no code imports or reads them |
| `prior_dashboard_versions/version_3.py` | 31 KB | unused | earlier dashboard versions; no code imports or reads them |
| `prior_dashboard_versions/version_4.py` | 41 KB | unused | earlier dashboard versions; no code imports or reads them |
| `regressions.json` | 3 KB | unused | stale copy (2026-10-07); every read and write uses model_data/regressions.json |
| `requirements.txt` | 0 KB | config | Streamlit / Codespaces / git configuration |
| `revenue_data/ (71 files)` | 1.77 MB | runtime (data) | folder read by: views/1_Dashboard.py; offline: audit/checks.py |
| `scenarios.py` | 11 KB | runtime (code) | imported by app.py / views/ (directly or through model_section, health_model) |
| `spending_data/ (72 files)` | 0.31 MB | runtime (data) | folder read by: views/1_Dashboard.py, health_model.py; offline: add_constant_dollars.py, audit/checks.py, audit/make_inventory.py, tests/test_minor.py |
| `tests/baseline_sudden.json` | 0.43 MB | offline (audit/test output or reference) | written or read by audit/ or tests/ scripts |
| `tests/make_baseline.py` | 12 KB | offline (code) | audit/test/prep script, run by hand |
| `tests/test_budget_section.py` | 2 KB | offline (code) | audit/test/prep script, run by hand |
| `tests/test_fiscal.py` | 3 KB | offline (code) | audit/test/prep script, run by hand |
| `tests/test_hiv.py` | 6 KB | offline (code) | audit/test/prep script, run by hand |
| `tests/test_i07.py` | 4 KB | offline (code) | audit/test/prep script, run by hand |
| `tests/test_malaria.py` | 8 KB | offline (code) | audit/test/prep script, run by hand |
| `tests/test_minor.py` | 6 KB | offline (code) | audit/test/prep script, run by hand |
| `tests/test_mou.py` | 5 KB | offline (code) | audit/test/prep script, run by hand |
| `tests/test_paths.py` | 10 KB | offline (code) | audit/test/prep script, run by hand |
| `theme.py` | 32 KB | runtime (code) | imported by app.py / views/ (directly or through model_section, health_model) |
| `unit_cost_reference.csv` | 2 KB | runtime (data) | read by: health_model.py |
| `views/1_Dashboard.py` | 47 KB | runtime (code) | imported by app.py / views/ (directly or through model_section, health_model) |
| `views/2_All_Countries.py` | 1 KB | runtime (code) | imported by app.py / views/ (directly or through model_section, health_model) |
| `views/3_Validation.py` | 22 KB | runtime (code) | imported by app.py / views/ (directly or through model_section, health_model) |
| `views/4_Methods.py` | 66 KB | runtime (code) | imported by app.py / views/ (directly or through model_section, health_model) |
| `who_inputs.py` | 7 KB | offline (code) | audit/test/prep script, run by hand |
