"""
Step 1: inventory of every number the dashboard displays -> audit/inventory.csv. Run from the repo root:

    .venv/bin/python audit/make_inventory.py

One row per displayed number (or family of numbers drawn by the same code, e.g. every bar of one chart).
Columns: page, section, label, render_fn (file:function that draws it), compute_fn (where the value comes from),
units, time_basis, currency, notes. Line numbers refer to commit 4cbb7ff.
"""
import csv
from pathlib import Path

D, MS, HM, PU, VA, AC, ME = ("views/1_Dashboard.py", "model_section.py", "health_model.py", "paths_ui.py",
                             "views/3_Validation.py", "views/2_All_Countries.py", "views/4_Methods.py")
C23, NA = "constant 2023 US$", "n/a"
R = []


def row(page, section, label, render, compute, units, time, cur=NA, notes=""):
    R.append(dict(page=page, section=section, label=label, render_fn=render, compute_fn=compute, units=units,
                  time_basis=time, currency=cur, notes=notes))


P = "Dashboard"
# ---- header ----
H = "Country header"
row(P, H, "Region", f"{D}:_items (l.292)", "prepare_model.py main: mode of IHME DAH wb_regioncode -> country_profile.csv", "text", NA)
row(P, H, "Income Group", f"{D}:_items", "World Bank classification (Gapminder mirror) -> country_profile.csv; GDP rule if missing", "text", "latest WB list")
row(P, H, "US MOU (MOU Signed / No MOU)", f"{D}:_items", "prepare_model.py l.418-421: 'Signed' if mou_us_2026 present in team sheet (no status column)", "text", NA, NA, "status inferred, see issue I-07")
row(P, H, "GDP, <year>", f"{D}:_items (l.296)", "macro_data gdp_usd_bn_2023, last year with gdp_is_estimate False", "US$ billions", "single year (latest actual, usually 2024)", C23)
row(P, H, "Population, <year>", f"{D}:_items (l.299)", "macro_data population_m, same year as GDP", "millions", "single year")
# ---- hero ----
H = "Story lede (hero)"
row(P, H, "Kicker: scenario, path, response", f"{MS}:story_lede (l.537)", "ctl settings", "text", NA)
row(P, H, "Headline: 'could see about N more deaths by 2030'", f"{MS}:story_lede", f"{HM}:run_country totals.deaths_5y (central run) via round_words", "deaths", "5-year total 2026-2030")
row(P, H, "Headline: 'even if the government replaces X% of the lost aid'", f"{MS}:story_lede", "totals.replaced / totals.gross", "%", "per year (average over the path)")
row(P, H, "Dek: 'Most/The largest share would come from <cause> (X%)'", f"{MS}:story_lede", "bucket deaths_5y / totals.deaths_5y", "%", "5-year total")
row(P, H, "Dek: 'About $X million a year would be lost' / 'could replace $X of the $Y'", f"{MS}:story_lede money_words", "totals.gross, totals.replaced", "US$", "per year (average over the path)", C23)
row(P, H, "Big number 1: Health Aid Lost Each Year", f"{MS}:story_lede money()", "totals.gross = mean over 2026-2030 of G x cut_path", "US$", "per year", C23)
row(P, H, "Big number 1 note: 'X% of aid for these four diseases'", f"{MS}:story_lede", "totals.gross / totals.base (base = all 16 lines, 2021-23 avg)", "%", "per year", C23)
row(P, H, "Big number 2: People Losing Care Each Year (+ top-3 breakdown)", f"{MS}:story_lede care_breakdown (l.491)", "lines.units_lost (central, mean of 5 years), clipped at 0 per line, all lines except hiv_prev and hiv_ovc", "people", "per year (5-year average)")
row(P, H, "Big number 3: Extra Deaths, 2026-2030", f"{MS}:story_lede num()", "totals.deaths_5y (central run)", "deaths", "5-year total 2026-2030")
row(P, H, "Big number 3 note: range lo to hi", f"{MS}:story_lede rng()", "totals.deaths_5y_lo/hi = 2.5th/97.5th percentile of 400 draws", "deaths", "5-year total")
row(P, H, "Big number 3 note: '+N more in 2031-2035' and tooltip parts", f"{MS}:story_lede, after_2030_help (l.737)", "committed.after_2030 and after_parts (central run)", "deaths", "5-year total 2031-2035")
# ---- scenario bar ----
H = "Scenario bar"
row(P, H, "Donor scenario short description (percentages)", f"{MS}:_controls PRESET_SHORT (l.48)", "hard-coded text; scenarios.py US_MULTI_EXITS, OECD_2025", "%", "per year (sustained)", NA, "checked vs sources, see Step 2")
row(P, H, "MOU caption: 'implies a X% cut in US bilateral aid in <year> (US$YM a year before the cut)'", f"{MS}:_preset_options (l.297)", "scenarios.mou_cuts; ci.mou_us_ref", "% / US$ millions", "single MOU year; reference = 2021-25 average", "nominal US$ (team sheet)", "header says all figures constant 2023 US$")
row(P, H, "Slider default: US cut where there is no MOU schedule (%)", f"{MS}:_preset_options", "scenarios.mou_average_cut_pct", "%", "single MOU year")
row(P, H, "Government Response help: '(-0.19 per $1, 95% CI ...)' and '97 countries, 2001-2023'", f"{MS}:_controls (l.343)", f"{HM}:theta_historical(regressions.json fiscal_replacement)", "US$ per US$", "panel 2002-2023 (actual years)")
row(P, H, "Share of Lost Aid Replaced (%) slider", f"{MS}:_controls", "user input", "%", "per year")
row(P, H, "Funding path chart: aid cut in force by year; hover aid lost, government money", f"{PU}:_chart (l.170)", f"{HM}:_money_by_year; gov_add_from_points", "% of full cut; US$", "single year 2026..2030", C23)
row(P, H, "Funding path chart: extra health share (pts) by year", f"{PU}:_chart", "user sliders / scenarios.gov_shape", "percentage points of government budget", "cumulative, by year")
row(P, H, "Caption: health is X% of government spending; fastest sustained rise Y points a year", f"{PU}:outcome_panel (l.213)", f"{HM}:health_budget (IMF WEO 2023 share; WDI history p90)", "% / percentage points", "2023 / 2001-2023")
row(P, H, "Pill: Extra Deaths 2026-2030 (+range)", f"{PU}:outcome_panel", "totals.deaths_5y, lo, hi", "deaths", "5-year total")
row(P, H, "Pill: Further Deaths, 2031-2035, Set in Motion by 2030 (+range)", f"{PU}:outcome_panel", "committed.after_2030, lo, hi", "deaths", "5-year total 2031-2035")
row(P, H, "Pill: Deaths Avoided vs Sudden Cut With No Response ('of N')", f"{PU}:outcome_panel", "base committed.deaths - committed.deaths", "deaths", "2026-2035")
row(P, H, "Pill: Break-Even Budget Increase (+x points a year)", f"{PU}:outcome_panel", f"{HM}:break_even_share", "percentage points per year", "cumulative 2026-2030")
row(P, H, "Outcome sentence ('keeps pace from <year>', 'avoids about N of M deaths')", f"{PU}:outcome_panel", "years.gap_usd; committed deaths", "deaths / years", "2026-2035")
# ---- Section 1 ----
H = "Section 1: Money Spent on Health"
row(P, H, "Health Spending by Source: stacked bars (DAH, government, prepaid private, out-of-pocket)", f"{D}: fig2 (l.352)", "spending_data/<ISO3>.csv *_total_mean / 1e3", "US$ millions/billions", "per year 2015-2023", C23)
row(P, H, "Same chart, US$ per person view", f"{D}: fig2", "spending_data *_per_cap_mean", "US$ per person", "per year 2015-2023", C23)
row(P, H, "Same chart, share of total view", f"{D}: fig2", "100 x part / the_total_mean", "%", "per year 2015-2023")
row(P, H, "Pill: Total Spending, 2023", f"{D}: pill_row (l.375)", "spending_data the_total_mean 2023 / 1e3", "US$", "single year 2023", C23)
row(P, H, "Pill: Foreign Aid Share of Total, 2023", f"{D}: pill_row", "dah_total_mean / the_total_mean (2023), formatted :.0%", "%", "single year 2023", NA, "can show 0% for small non-zero shares")
# ---- Section 2 ----
H = "Section 2: Who Is Providing the Money"
row(P, H, "Pill: Total in <last year>", f"{D}: pill_row (l.453)", "country_data dah_23 (or selected focus/program column) / 1e3, last year with data", "US$", "single year (2023)", C23)
row(P, H, "Pill: Via NGO / Foundation Channels, <year>", f"{D}: pill_row", "share of the year's total through NGO, INTLNGO, US_FOUND, GATES channels", "%", "single year")
row(P, H, "Pill: Largest Funder, <year>", f"{D}: pill_row", "source with the largest total that year", "text", "single year")
row(P, H, "Health Aid by Funder: stacked bars (solid = government-facing, light = NGO/foundation)", f"{D}: fig (l.461)", "country_data grouped by year x source x route", "US$ millions/billions", "per year 2015-2023", C23)
row(P, H, "Annotation: '<funder>: X% of <year> aid'", f"{D}: fig.add_annotation", "largest funder share of last year", "%", "single year")
row(P, H, "Health Aid by What It Pays For: stacked bars by focus area or program area (US$ or %)", f"{D}: fig4 (l.556)", "country_data <focus>_dah_23 / program columns", "US$ millions / %", "per year 2015-2023", C23)
# ---- Section 3 ----
H = "Section 3: Revenue and Spending"
row(P, H, "Treemap revenue boxes (US$ and % of side)", f"{D}:_budget_section node() (l.671)", "revenue_data pct_gdp rescaled to WEO revenue % of GDP x macro gdp_usd_bn_2023", "US$ / %", "single selected year", C23, "mix often central government, total general government")
row(P, H, "Treemap borrowing box", f"{D}:_budget_section", "WEO expenditure - revenue (% of GDP) x GDP", "US$ / %", "single year", C23)
row(P, H, "Treemap spending boxes incl. Health (COFOG)", f"{D}:_budget_section", "cofog_all pct_outlays rescaled to 100 x WEO expenditure % of GDP x GDP", "US$ / %", "single year", C23, "COFOG often central government only")
row(P, H, "Pills: Revenue, Spending, Deficit (Borrowing), Gross Government Debt (US$ and % of GDP)", f"{D}:_budget_section pills (l.777)", "macro_data WEO % of GDP x gdp_usd_bn_2023", "US$ / % of GDP", "single year", C23)
row(P, H, "Caption: IHME puts government health spending at X% of GDP", f"{D}:_budget_section", "spending_data ghes_per_gdp_mean (selected year)", "% of GDP", "single year")
# ---- Section 4 ----
H = "Section 4: The Numbers"
row(P, H, "Aid at Risk (per Year) + 'X% of $Y for these four buckets'", f"{MS}:_headline_items (l.747)", "totals.gross; totals.base", "US$ / %", "per year", C23)
row(P, H, "Replaced by Government + 'X% of the loss'", f"{MS}:_headline_items", "totals.replaced = mean of min(R_t + gov_add, G_t)", "US$ / %", "per year", C23)
row(P, H, "Net Loss to Services ('per year')", f"{MS}:_headline_items", "totals.net = mean(G_t - replaced_t)", "US$", "per year", C23, "includes non-service systems money, see I-12")
row(P, H, "Further Deaths, 2031-2035 (+range, tooltip parts)", f"{MS}:_headline_items", "committed.after_2030, after_2030_lo/hi", "deaths", "5-year total 2031-2035")
row(P, H, "Extra Deaths Over 5 Years (+range)", f"{MS}:_headline_items", "totals.deaths_5y (central), lo/hi percentiles", "deaths", "5-year total 2026-2030")
row(P, H, "New HIV Infections, 5 Years (+range)", f"{MS}:_headline_items", "buckets HIV infections_5y = MEDIAN of 400 draws (not central)", "infections", "5-year total 2026-2030", NA, "see I-05")
row(P, H, "Sentence: 'Government backfill of $X a year averts about N deaths ... ($Y per death averted)'", f"{MS}:_country_results (l.637)", "res0 deaths - res deaths; replaced x 5 / saved", "US$ / deaths", "per year / 5-year", C23)
H = "Section 4: Every US$1 Million Lost (cards)"
for b, ln in (("HIV", "hiv_art"), ("TB", "tb_ds"), ("Malaria", "mal_itn"), ("Immunization", "imm")):
    row(P, H, f"{b} card: People Losing the Service", f"{MS}:_card_html", f"{MS}:_per_million_cards: 1e6 / unit_cost[{ln}] x (1 - continuity)", "people", "per year (for $1M a year)", C23, "ignores proportional scaling and caps, see I-04")
    row(P, H, f"{b} card: Coverage Drop (Percentage Points)", f"{MS}:_card_html", "people / need x 100", "percentage points", "per year")
    row(P, H, f"{b} card: Extra Deaths Over 5 Years", f"{MS}:_card_html", "deaths_per_dollar[line] x 1e6 x (1 - continuity)", "deaths", "5-year total for $1M a year", NA, "excludes TB spread, malaria rebound, HIV infection deaths")
    row(P, H, f"{b} card foot: Cost $X per unit · $Y of aid per death", f"{MS}:_per_million_cards", "unit_cost; 5e6 / deaths", "US$", "unit cost per year; aid per death over 5 years", C23)
H = "Section 4: Where the Money Is Lost"
row(P, H, "Aid Lost per Year by bucket (lost / replaced)", f"{MS}:_loss_by_bucket_fig (l.866)", "buckets gross_loss_usd, replaced_usd", "US$", "per year", C23)
row(P, H, "Who Cut the Money: donor x channel bars", f"{MS}:_who_cut_fig (l.904)", "cells.loss grouped by src_grp x chan_grp (top 11 + all other)", "US$", "per year (full cut, not path-scaled)", C23)
H = "Section 4: What Each Service Loses (table)"
for col, comp, u, t, c in (("Donor Aid Now", "lines.base_usd (effective baseline incl. spread of unspecified + kappa x systems)", "US$", "per year (2021-23 avg)", C23),
                           ("Aid Lost (after government replacement)", "lines.net_loss_usd (mean over path)", "US$", "per year", C23),
                           ("Cost per Person", f"{HM}:unit_costs (central)", "US$ per unit", "per year of service", C23),
                           ("People Losing Service", "lines.units_lost (central, mean over path)", "people", "per year", NA),
                           ("Coverage before -> after and drop (pts)", "lines.cov0; cov0 - cov_drop_pp/100", "% / percentage points", "single year (latest data) / during cut", NA),
                           ("Extra Deaths (5 years) + range", "lines.deaths_5y central; lo/hi percentiles", "deaths", "5-year total", NA),
                           ("Other Aid row", "totals.base/net minus the rows", "US$", "per year", C23),
                           ("Total row", "totals.base, totals.net, sum of rows' people, totals.deaths_5y + run interval", "US$ / people / deaths", "per year / 5-year", C23)):
    row(P, H, col, f"{MS}:_service_table_html (l.982)", comp, u, t, c)
row(P, "Section 4: Coverage Lost, by Service", "Bars: drop in percentage points; labels before -> after", f"{MS}:_coverage_fig (l.1044)", "rows cov0, after, drop", "percentage points", "during the cut")
H = "Section 4: How the Damage Scales"
row(P, H, "Sentence: 'An even 10% cut to <bucket> aid adds about N extra deaths over 5 years'", f"{MS}:_country_results", f"{HM}:dose_response (21 points, 100 draws) interpolated at 10%", "deaths", "5-year total")
row(P, H, "Even-cut curve and 95% band", f"{MS}:_dose_fig (l.1067)", "dose_response deaths_5y (central), lo/hi (100 draws); hover net loss, coverage drop", "deaths / US$ / pts", "5-year total", C23)
row(P, H, "This-scenario dashed path and dot ('x% cut, N deaths')", f"{MS}:_dose_fig", "_scenario_path (scenario scaled 0-1); bucket gross/base", "deaths / %", "5-year total")
row(P, H, "Extra Deaths Each Year (stacked by bucket)", f"{MS}:_path_fig (l.1113)", "res.path (central run, by year)", "deaths", "single year 2026..2030")
H = "Section 4: Can <Country> Fill the Gap?"
row(P, H, "Pill: Government Health Spending (2023) + per person + % of GDP", f"{MS}:_fiscal_panel (l.1164)", "ci.ghes_2023, ghes_pc_2023, ghes_pct_gdp_2023 (IHME)", "US$", "single year 2023", C23)
row(P, H, "Pill: Aid Lost as % of Government Health Spending", f"{MS}:_fiscal_panel", "fiscal.gross_loss (FULL cut G) / ghes_2023", "%", "per year vs 2023")
row(P, H, "Pill: Aid Lost as % of Government Revenue", f"{MS}:_fiscal_panel", "G / (pop x IHME gdp_pc 2024 x WDI revenue % latest)", "%", "per year vs latest")
row(P, H, "Pill: Health Share of Government Spending (Abuja 15%)", f"{MS}:_fiscal_panel", "ci.sh_xpd_ghed_ge_zs (World Bank WDI)", "%", "latest year (2023)", NA, "differs from the IMF-based share in the path panel, I-14")
row(P, H, "Sentence: 'would take a X% increase ...; grows about Y% faster ...; would cover $Z of the $G gap'", f"{MS}:_fiscal_sentence (l.1143)", "G/ghes; (growth p75 - median) x 100; capacity", "% / pts / US$", "per year", C23)
row(P, H, "The Gap vs. the Budget bars: Aid lost, Budget can absorb, Replaced here, Typical yearly growth", f"{MS}:_fiscal_panel", "G; capacity; fiscal.replacement (existing response only); ghes x max(median growth, 0)", "US$", "per year", C23, "Replaced here excludes gradual budget money")
H = "Section 4: Scenario A vs B (optional)"
row(P, H, "Scenario A and B pills (as The Numbers)", f"{MS}:_comparison (l.770)", "two run_country results", "US$ / deaths", "per year / 5-year", C23)
row(P, H, "Sentence: 'Scenario B averts/adds about N extra deaths'", f"{MS}:_comparison", "difference of deaths_5y", "deaths", "5-year total")
row(P, H, "Extra Deaths by Disease, A vs B", f"{MS}:_comparison", "buckets deaths_5y", "deaths", "5-year total")

P = "All Countries"
H = "Pills"
row(P, H, "Aid Lost per Year, N of 71 Countries (+ Net of Backfill)", f"{MS}:cross_country (l.1247)", "sum of precomputed gross_loss_usd / net_loss_usd (countries with gross > 0)", "US$", "per year", C23)
row(P, H, "Further Deaths, 2031-2035 (+range)", f"{MS}:cross_country", "sum of deaths_after_2030 and of country lo/hi", "deaths", "5-year total 2031-2035")
row(P, H, "Extra Deaths Over 5 Years (+range)", f"{MS}:cross_country", "sum of deaths_5y; sum of country 2.5th/97.5th percentiles", "deaths", "5-year total")
row(P, H, "New HIV Infections, 5 Years", f"{MS}:cross_country", "sum of country MEDIAN infections", "infections", "5-year total")
row(P, "Map", "Extra Deaths per 100,000 People (color), hover deaths, aid lost, % of GHES", f"{MS}:_world_map (l.1343)", "deaths_5y / sp_pop_totl x 1e5; gross_loss_usd; loss_pct_ghes", "deaths per 100,000 / US$ / %", "5-year total / per year", C23)
row(P, "Scatter", "Budget Exposure vs. Deaths (x: aid lost % of GHES; y: deaths per 100,000; size: net loss)", f"{MS}:cross_country", "loss_pct_ghes x 100; deaths_per_100k; net_loss_usd", "% / per 100,000", "per year / 5-year", C23)
row(P, "Top 15", "Most Extra Deaths, 5 Years (stacked by bucket) and rank note", f"{MS}:cross_country", "deaths_5y_<bucket>", "deaths", "5-year total")

P = "Validation & Benchmarks"
row(P, "Published Estimates", "Model: Extra Deaths Over 5 Years, All 70 Countries (by preset x bucket, range)", f"{VA}: rows (l.58)", "precomputed all_countries_<preset>.csv sums", "deaths", "5-year total")
row(P, "Published Estimates", "Published estimates table (Cavalcanti per year and 14.1M, UNAIDS 4.2M, Optima 0.8-2.9M, Gavi 0.017) vs model", f"{VA}: pub (l.74)", "precomputed Full US exit; deaths_per_child_immunised", "deaths / deaths per child", "per year / 5-year / lifetime")
row(P, "Donor money above cost", "Country-Service Lines Affected (of N); Countries With At Least One; Lines in <country>; by-service table", f"{VA}: pills (l.127)", f"{HM}:donor_cost_excess", "count", NA)
row(P, "Three Ways", "Extra Deaths by Method (unit-cost, Poisson, Lancet) chart + table + reading sentence", f"{VA} (l.139-237)", f"{HM}:run_country, poisson_projection, lancet_projection", "deaths", "5-year total")
row(P, "Three Ways", "Note: US-source aid per person before/after; HIV baseline deaths", f"{VA}: notes", "lancet_projection; ci.hiv_deaths_est", "US$ per person / deaths", "per year", "mixed: IHME US-source aid constant 2023 US$")
row(P, "Poisson regressions", "Coefficient, Standard Error, Countries, Observations, Years", f"{VA} (l.268)", "regressions.json", "log-points", "panel years")

P = "Methods"
row(P, "Text throughout", "Parameter values 'central (low-high)'", f"{ME}:rng_txt (l.46)", "model_params.csv (live)", "various", NA)
row(P, "Step 2", "Fiscal regression: countries, years, country-years, coefficients", f"{ME} (l.315)", "regressions.json", "various", "panel years")
row(P, "Step 3", "Unit cost table (ART site costs inflated, defaults, PMTCT, prevention, OVC, TB, bednets, spraying, malaria treatment, vaccines)", f"{ME} (l.351-360)", "unit_cost_reference.csv, model_params.csv", "US$ per unit", "per year of service", C23)
row(P, "Funding Paths", "Path-shape table (% by year)", f"{ME}", "scenarios.path_shape", "%", "by year")
row(P, "Assumptions / Every parameter", "Parameter tables", f"{ME} (l.638, 678)", "model_params.csv", "various", NA)
row(P, "Regression Estimates", "Regression table", f"{ME} (l.689)", "regressions.json", "various", "panel years")
row(P, "Cross-checks", "'Panel regressions ... imply about N extra deaths ... against M from the unit-cost model'", f"{MS}:_crosscheck_summary", f"{HM}:statistical_crosscheck", "deaths", "5-year total")
row(P, "Cross-checks", "Does This Match Published Estimates? table (Cavalcanti, ten Brink, Gavi) with model figures", f"{MS}:_published_estimates", "all-country results for the current settings", "deaths / deaths per child", "5-year / lifetime")


def main():
    out = Path(__file__).parent / "inventory.csv"
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(R[0]))
        w.writeheader()
        w.writerows(R)
    print(f"{len(R)} rows -> {out}")


if __name__ == "__main__":
    main()
