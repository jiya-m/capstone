# The funding-cut model in plain language (specification for the independent recalculation)

This is the method the dashboard uses, written out from the audit's reading of the code (branch real-modeling-check,
commit 4cbb7ff). It is detailed enough to recompute every Section 4 number for one country with pandas and numpy,
without the model code. All money is constant 2023 US$ per year unless stated. Years t = 1..5 are 2026..2030.

## Files

| File | Contents |
|---|---|
| `model_data/dah_lines.csv` | Baseline aid, average of 2021-2023, US$ per year: `iso3, src_grp, chan_grp, usd, line, bucket` |
| `model_data/country_inputs.csv` | One row per country (`iso3`): epidemiology, coverage, fiscal and MOU columns (named below) |
| `model_data/regressions.json` | Regression coefficients (only `fiscal_replacement` is needed, and only for a mode not used here) |
| `model_params.csv` | Parameters with `central`, `low`, `high`. **Use `central` everywhere** (the "central run") |
| `unit_cost_reference.csv` | ART site costs and TB costs per patient |

## 0. Settings to recompute

Countries: KEN, NGA, HND, IRQ, MOZ. Scenarios: "Full US exit" and "America First MOUs" (default options). Government
responses: "No backfill" and "Replace a set share" at 25% (capped at fiscal space, pro-rata allocation, 75th-percentile
ceiling). Sudden cut (the full cut in every year 2026-2030). Mortality trend switched ON.

## 1. Money: aid lost by service line

Lines: HIV `hiv_art, hiv_care_ct, hiv_pmtct, hiv_prev, hiv_ovc, hiv_unspec, hiv_hss`; TB `tb_ds, tb_dr, tb_unspec, tb_hss`;
Malaria `mal_itn, mal_irs, mal_cm, mal_unspec, mal_hss`; Immunization `imm`. The "direct" lines are
`hiv_art, hiv_pmtct, hiv_prev, hiv_ovc, tb_ds, tb_dr, mal_itn, mal_irs, mal_cm, imm`.

**Cut on each row of dah_lines** (one row = country x donor group x channel group x line):
- Direct channels are `Bilateral agency`, `NGOs`, `Gates direct`, `Other`; every other channel is "multilateral".
- Donor cut x = the scenario's direct-channel cut for that donor if the channel is direct, else its multilateral cut.
  A (donor, channel) pair cut, if the scenario defines one, replaces x.
- Channel cut y = the scenario's cut for that channel for all donors (none in these two scenarios, so y = 0).
- Row cut = 1 - (1 - x)(1 - y). Row loss = usd x row cut.

**Scenarios**
- *Full US exit*: donor `United States`, direct channels: x = 1.0. Pairs: (United States, WHO) = 1.0,
  (United States, Gavi) = 1.0, (United States, UNFPA) = 1.0, (United States, Global Fund) = 0.23. Every other US
  multilateral channel (UNICEF, UNAIDS, development banks, ...) = 0. All other donors 0.
- *America First MOUs*: as Full US exit, except the US direct-channel cut x is country-specific. For a country with
  `mou_us_ref` > 0: take the latest year <= 2028 among `mou_us_2026..mou_us_2028` that is not missing; x =
  clip(1 - mou_us_<year> / mou_us_ref, -0.5, 1). If the country has no such value, x = the non-MOU default =
  round(100 x mean of x over all countries that have one, for 2028) / 100 (expected 0.36).

**Per line**: base_l = sum of usd; gross_l = sum of loss (over that country's rows of line l).

**Aid at risk** G = sum over all lines (direct, unspec, hss, ovc) of max(gross_l, 0).
**Baseline aid** = sum of base_l over all lines.

**Effective loss of each direct line** (kappa = `hss_kappa` central):
for each bucket b, with mix_l = base_l / (sum of base over b's direct lines) (if that sum is 0, use the global mix:
the share of each direct line in that bucket's baseline across all countries in dah_lines):
  eff_l = gross_l + (gross_unspec_b + kappa x gross_hss_b) x mix_l.
The non-service part of systems money is nonserv_b = (1 - kappa) x gross_hss_b. Immunization has no unspec/hss line.
**HIV testing & care** (`hiv_care_ct`, I-09) is a known line for the mix (mix over direct lines + hiv_care_ct) but has no
units: pool = gross_care + (gross_unspec + gross_hss) x mix_care; kappa x pool is service money that adds to hiv_art's
money lost (and base); (1 - kappa) x pool is non-service; nonserv_HIV = (1 - kappa) x gross_hss x (1 - mix_care).
For units, hiv_art uses net_art + net_care_kappa over base eff_base_art + eff_base_care_kappa, but whether donor money
exceeds cost x covered is judged on eff_base_art only (raw = min(covered, eff_base_art / cost) x net / base).
**PMTCT women are outside the ART pool** (I-27): covered_art = ART coverage x PLHIV - PMTCT coverage x HIV+ pregnancies
(not below 0); units of hiv_art are clipped to covered_art. uc_pmtct includes the mother's ART.
Compute the same with base amounts to get the effective baseline eff_base_l.

## 2. Government response

Fiscal capacity per year = ghes_2023 x max(0, ghes_growth_p75 - max(ghes_growth_median, 0)) x stress, where
stress = clip(1 - (interest_pct_revenue - 10) / 40, 0.25, 1). `interest_pct_revenue` (I-26) is the more recent of
World Bank `gc_xpn_intp_rv_zs` and IMF WEO net interest ((GGXONLB_NGDP - GGXCNL_NGDP) / GGR_NGDP x 100, latest actual
year; ties: World Bank), else the income-group median (estimated); it is never missing. Missing
growth values count as 0; missing ghes_2023 gives capacity 0.
- No backfill: replaced R = 0.
- Replace 25%: R = min(0.25 x G, capacity), and never above G.
**Allocation (pro-rata)**: each positive eff_l and each positive nonserv_b gets R x its amount / (sum of all positive
eff_l and nonserv_b). net_l = eff_l - replaced_l. **Net loss** (headline) = G - R.

## 3. Coverage: people losing each service (per year)

**Population in need and current coverage** (country_inputs columns; coverage columns are percentages, divide by 100):

| Line | Need | Coverage now |
|---|---|---|
| hiv_art | `plhiv` | `sh_hiv_artc_zs` |
| hiv_pmtct | `hiv_pos_pregnancies` | `sh_hiv_pmtc_zs`, or ART coverage if missing |
| tb_ds | `all_forms_of_tb_incidence_estimated` | `sh_tbs_dtec_zs` |
| tb_dr | 0.04 x TB incidence | 0.45 |
| mal_itn | `malaria_pop_at_risk` | `mal_itn_cov` (MAP ITN use 2025, or a survey from 2015 on); if missing, `mal_itn_default_use` |
| mal_irs | `malaria_pop_at_risk` | max(`mal_irs_cov` (MAP household IRS coverage 2025, Africa), eff_base_irs / cost_irs / par clipped to 1); the second alone where MAP has no estimate |
| mal_cm | `malaria_cases` (MAP Pf + Pv clinical cases 2025 where MAP has them) | `mal_cm_cov` (MAP effective treatment 2025); if missing, `mal_cm_default_cov` |
| imm | `births` | `sh_imm_idpt` |
| hiv_prev, hiv_ovc | none | none |

**Cost per unit** (central parameters). markup = 1 / (1 - asd_share). gdp = `gdp_pc` (1000 if missing);
sc = (max(gdp, 200) / 1000) ^ uc_scale_elast. CPI factors to 2023: 2018 -> x 304.702/251.107, 2020 -> x 304.702/258.811.
- hiv_art: ART site cost for the country from unit_cost_reference (`art_site_cost`, inflated from its cost_year),
  else (arv default + non_arv default x sc), both inflated from 2018; then x uc_art_mult x markup.
- hiv_pmtct: uc_pmtct. hiv_ovc: uc_ovc.
- hiv_prev (US$ per infection averted): cpia_ref x (1 / inc) ^ 0.5, inc = `sh_hiv_incd_tl` / `sp_pop_totl` x 1000,
  clipped to [0.05, 10] (0.3 if missing).
- tb_ds / tb_dr: `tb_ds_cost` / `tb_dr_cost` for the country's `income_group` (anything other than low or lower-middle
  income uses upper-middle) x uc_tb_mult x markup. These TB values are already 2023 US$.
- mal_itn: uc_itn; mal_irs: uc_irs; mal_cm: uc_mal_cm; imm: uc_imm.

**Units lost** for each direct line, with covered = coverage x need (missing if either is missing):
- if covered is missing: raw = net_l / cost;
- else if eff_base_l / cost > covered (donor money buys more than everyone covered): raw = covered x net_l / eff_base_l;
- else raw = net_l / cost.
units = raw x (1 - continuity). If need and coverage exist, clip units to [-(1 - coverage) x need, coverage x need].
Bednets and spraying each have their own coverage, so each is clipped to its own coverage x par (no shared pool).
**Coverage after** = coverage now - units / need (shown as coverage before -> after and the drop in percentage points).
For a sudden cut the units are the same in every year.

## 4. Lives (central run, years t = 1..5)

Ramp-up shares by years the cut has been in force (year 1..5):
PMTCT 0.6, 1, 1, 1, 1; TB (both) 0.7, 1, 1, 1, 1; bednets 0.5, 1, 1, 1, 1; spraying 0.8, 1, 1, 1, 1;
malaria treatment 1, 1, 1, 1, 1.

- **PMTCT** deaths_t = units x pmtct_vt_reduction x pmtct_infant_mort x ramp_t.
- **TB** h = `tb_hiv_share` (0 if missing), a = ART coverage (0 if missing).
  dCFR = (1 - h)(tb_cfr_untreated_neg - tb_cfr_treated_neg) + h (tb_cfr_untreated_pos - tb_cfr_treated_pos)(1 - 0.3a).
  tb_ds deaths_t = units x dCFR x ramp_t; tb_dr deaths_t = units x tb_dr_dcfr x ramp_t.
  *TB spread*: each year s, secondary cases = (tb_ds units + tb_dr units) x tb_secondary; half arrive in year s+1 and
  half in s+2. A case arriving in year t dies with probability c_t x cfr_treated + (1 - c_t) x cfr_untreated, where
  c_t = clip(TB coverage - tb_ds units / TB need, 0, 1) (year 5 value for years after 2030),
  cfr_untreated = (1 - h) tb_cfr_untreated_neg + h tb_cfr_untreated_pos (1 - 0.3a),
  cfr_treated = (1 - h) tb_cfr_treated_neg + h tb_cfr_treated_pos (1 - 0.3a).
  Arrivals in years 2-5 add to tb_ds deaths in that year; arrivals after 2030 count only in "after 2030".
- **Immunization** U5MR_t = `sh_dyn_mort` (50 if missing) x (1 + `trend_u5mr`)^(t-1) (trend -0.009 if missing).
  level_t = imm_deaths_per_child_ref x imm_u5_share x clip(U5MR_t / 50, 0.3, 2.5).
  Each year's missed cohort (the units of that year) dies over the following years with weights 0.40, 0.35, 0.20,
  0.05: deaths in year t = sum over s <= t of units_s x weight_(t-s) x level_t. (For a sudden cut this equals units x
  level_t x 0.4, 0.75, 0.95, 1, 1.)
- **Malaria** (Lives Saved Tool form), D0 = `malaria_deaths` (none if missing or 0), par = population at risk,
  cases = `malaria_cases`, Ev = mal_vc_eff, Ec = mal_cm_eff, n0 = bednet use, r0 = spraying coverage,
  cc0 = malaria treatment coverage. n1 = clip(n0 - itn units / par, 0, 1); r1 = clip(r0 - irs units / par, 0, 1);
  vc(n, r) = 1 - (1 - n)(1 - r); cv0 = vc(n0, r0), cv1 = vc(n1, r1); cc1 = clip(cc0 - cm units / cases, 0, 1).
  rv = (1 - Ev cv1)/(1 - Ev cv0); rc = (1 - Ec cc1)/(1 - Ec cc0); total = D0 (rv rc - 1); dv = D0 (rv - 1);
  dc = D0 (rc - 1). Vector share = total x |dv| / (|dv| + |dc|), treatment share = total x |dc| / (|dv| + |dc|).
  The vector share splits between itn and irs in proportion to cv0 - vc(n1, r0) and cv0 - vc(n0, r1) (half each if
  both are 0).
  Year t: each part x ramp_t x (1 + `trend_malaria_deaths`)^(t-1) (MAP P. falciparum cases 2015-2025, clipped to
  +/-5%; 0 without MAP data), and bednets and spraying
  also x (1 + mal_resurgence)^(t-1).
- **HIV treatment** hazard by years off ART (1..5) = art_hazard_mult x (0.012, 0.028, 0.038, 0.045, 0.05).
  A sudden cut is one group of size U (the units) off ART from 2026: deaths_t = U x hazard_t. Infections per year from
  people off ART = U x art_transmission x (0.5 in the first year, 1 afterwards).
- **New HIV infections and their deaths.** Infections in year s: from people off ART (above) and from lost prevention
  (hiv_prev units are infections; every year). Each infection happens mid-year. Without treatment, the share of
  eventual HIV deaths falling in year k after infection (k = 0 is the infection year) is F(k + 0.5) - F(k - 0.5),
  with F(x) = 1 - exp(-(max(x, 0)/lambda)^2.25), lambda = hiv_survival_median / ln(2)^(1/2.25).
  Deaths in year t from infections in year s = infections_s x [F(t-s+0.5) - F(t-s-0.5)] x
  (c_t x hiv_inf_death_treated + (1 - c_t) x hiv_inf_death_untreated), with c_t = clip(ART coverage - people off
  ART in year t / PLHIV, 0, 1). Deaths in 2026-2030 from infections caused by people off ART add to the hiv_art line;
  from lost prevention, to the hiv_prev line.
- **New HIV infections, 5 years** = sum over 2026-2030 of infections from people off ART + lost-prevention infections
  + PMTCT infections (PMTCT units x pmtct_vt_reduction).

**Extra deaths over 5 years** = sum over lines and years. **Year 1** = 2026 only.

## 5. Deaths in 2031-2035 ("Further deaths")

Funding is back from 2031. People still off ART at the end of 2030 return to care at art_reengage per year: in year k
(k = 0 for 2031) the number still off is U x (1 - art_reengage)^(k + 0.5); they keep the hazard of their own years
off ART (year 5 value after year 5) and keep transmitting (art_transmission per year). Parts:
people off ART (deaths), new HIV infections (deaths in 2031-2035 from all infections in 2026-2035, as above, with
c_t computed from the people still off ART), missed vaccine cohorts (remaining weights x the 2030 level x
(1 + trend_u5mr)^(years after 2030)), TB spread (arrivals in 2031-2032).

## 6. "What Every US$1 Million Cut Does, by Disease" cards (I-04)

- For each disease with aid B (all its lines in dah_lines, including unspec, hss, ovc and hiv_care_ct): run this whole
  calculation (sections 2-5, sudden cut, no government response) with every row of that disease cut by
  c = min(1, 1,000,000 / B) and every other row by 0. k = 1,000,000 / (c x B).
- People losing the service = units lost on the main line (hiv_art, tb_ds, mal_itn, imm) x k.
- Coverage drop (points) = that / need x 100.
- Extra deaths over 5 years = the disease's deaths 2026-2030 x k (all mechanisms: TB spread, malaria rebound, HIV
  infection deaths).
- Aid per death = 5,000,000 / deaths.
