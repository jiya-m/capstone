# Model specification

This is the single, current specification of the funding-cut model behind Section 4 of the dashboard, the All
Countries page and the Validation page. It replaces `audit/METHOD.md` and the specification part of
`audit/logic_review/logic.md`. It is written so that every displayed Section 4 number can be recomputed with pandas
and numpy from the data files alone, without the model code. The independent reproduction in
`audit/logic_review/reproduction/` is built from this file only.

When the code changes, this file changes in the same commit. References `file:line` point to the implementation for
readers who want to check it; nothing here requires reading the code.

## 0. Conventions

- Money: constant 2023 US$ per year unless stated. MOU amounts are nominal (used only as ratios).
- Years: t = 0..4 is 2026..2030 (code index); "year 1..5" in prose means the same years. POST years k = 0..4 are
  2031..2035.
- Shares are 0-1 in formulas. Coverage columns in `country_inputs.csv` named `sh_*` are percentages: divide by 100.
- A missing value (NaN) in an input is handled as stated next to each formula; nothing is filled silently.
- clip(x, a, b) = min(max(x, a), b).
- The **central run** uses every parameter at `central` from `model_params.csv`. All displayed point values are from
  the central run. Ranges come from the draws (section 9).

## 1. Files and columns

| File | Contents |
|---|---|
| `model_data/dah_lines.csv` | Baseline aid, average of 2021-2023, US$ a year: `iso3, src_grp, chan_grp, usd, line, bucket`. One row = country x donor group x channel group x line |
| `model_data/country_inputs.csv` | One row per country (`iso3`) |
| `model_data/ihme_trend.csv` | IHME 2025 / 2021-23 ratio: `src_grp, chan_grp, bucket, ratio` |
| `model_params.csv` | Parameters: `central, low, high` |
| `unit_cost_reference.csv` | ART site costs (`art_site_cost` by country, `art_site_default` arv / non_arv) and TB costs (`tb_ds_cost`, `tb_dr_cost` by income group), with `cost_year` |

Country columns used (`country_inputs.csv`):

| Symbol | Column | Notes |
|---|---|---|
| PLHIV | `plhiv` | people living with HIV |
| ART % | `sh_hiv_artc_zs` | |
| PMTCT % | `sh_hiv_pmtc_zs` | if missing, ART % is used |
| HIV+ pregnancies | `hiv_pos_pregnancies` | |
| new HIV infections | `sh_hiv_incd_tl` | number a year |
| population | `sp_pop_totl` | |
| TB incidence | `all_forms_of_tb_incidence_estimated` | number a year (not `sh_tbs_incd`, which is per 100,000) |
| TB detection % | `sh_tbs_dtec_zs` | |
| h (TB-HIV share) | `tb_hiv_share` | 0 if missing |
| malaria population at risk (PAR) | `malaria_pop_at_risk` | |
| malaria cases | `malaria_cases` | |
| D0 (malaria deaths, all ages) | `malaria_deaths` | |
| bednet use, spraying, treatment coverage | `mal_itn_cov`, `mal_irs_cov`, `mal_cm_cov` | shares 0-1 (not percentages); NaN = see section 5 |
| births | `births` | |
| DTP3 % | `sh_imm_idpt` | |
| U5MR | `sh_dyn_mort` | 50 if missing |
| trends | `trend_u5mr`, `trend_malaria_deaths` | yearly change (shares); -0.009 if missing |
| GDP per person | `gdp_pc` | 1,000 if missing |
| income group | `income_group` | `low_income`, `lower_middle_income`, `upper_middle_income` |
| GHES | `ghes_2023` | government health spending, US$ |
| growth | `ghes_growth_median`, `ghes_growth_p75`, `ghes_growth_p90` | shares a year; 0 if missing |
| interest | `interest_pct_revenue` | % of revenue; never missing |
| MOU | `mou_us_ref`, `mou_us_2026` .. `mou_us_2030` | nominal US$ |

**Lines.**
- HIV: `hiv_art`, `hiv_pmtct`, `hiv_prev`, `hiv_ovc` (direct), `hiv_care_ct` (linked to `hiv_art`), `hiv_unspec`,
  `hiv_hss`.
- TB: `tb_ds`, `tb_dr` (direct), `tb_unspec`, `tb_hss`.
- Malaria: `mal_itn`, `mal_irs`, `mal_cm` (direct), `mal_unspec`, `mal_hss`.
- Immunization: `imm` (direct).
- Known lines K_b of bucket b = its direct lines, plus `hiv_care_ct` for HIV.

**Constants.**

| Constant | Value |
|---|---|
| DR_TB_SHARE | 0.04 |
| DR_TB_COV | 0.45 |
| ART_HAZARD (by years off ART 1..5) | 0.012, 0.028, 0.038, 0.045, 0.050 |
| ART_INFECT_LAG (by years off ART 1..5) | 0.5, 1, 1, 1, 1 |
| HIV Weibull shape | 2.25 |
| POST_YEARS | 5 |
| CPI-U | 2014: 236.736, 2018: 251.107, 2019: 255.657, 2020: 258.811, 2021: 270.970, 2022: 292.655, 2023: 304.702 |

**LAG** (share of the full yearly effect by years the cut has been in force, index d = 0..4):

| Line | d = 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| hiv_pmtct | 0.6 | 1 | 1 | 1 | 1 |
| tb_ds, tb_dr | 0.7 | 1 | 1 | 1 | 1 |
| mal_itn | 0.5 | 1 | 1 | 1 | 1 |
| mal_irs | 0.8 | 1 | 1 | 1 | 1 |
| mal_cm | 1 | 1 | 1 | 1 | 1 |
| imm (cumulative) | 0.4 | 0.75 | 0.95 | 1 | 1 |

## 2. Scenario cuts

**Direct channels** are `Bilateral agency`, `NGOs`, `Gates direct`, `Other`; every other channel is multilateral.
(`Other` does not occur as a channel in the data; donor "Other / unallocable" is a donor group, not a channel.)

For each row of `dah_lines` (donor s, channel c, bucket b):

    if the IHME preset:  cut = 1 - ratio[s, c, b]      (ratio from ihme_trend.csv; 1 if the cell is not listed)
    else:  x = src_direct[s] if c is direct, else src_multi[s]      (0 if s is not listed)
           x = pair[s, c] if that pair is defined (replaces x)
           y = chan[c]                                               (0 if not listed)
           cut = 1 - (1 - x)(1 - y)
    cut = clip(cut, -1, 1)

**Presets** (any donor or channel not listed: 0):

| Preset | src_direct | src_multi | pair | chan |
|---|---|---|---|---|
| Full US Exit | US 1.0 | none | (US, WHO) 1, (US, Gavi) 1, (US, UNFPA) 1, (US, Global Fund) 0.23 | none |
| America First MOUs | US: country schedule (below) | none | as Full US Exit | none |
| IHME 2025 | (ratio rule above) | | | |
| OECD 2025 | US 0.57, Germany 0.174, France 0.109, United Kingdom 0.108, Japan 0.056 | the same values | none | none |
| Global Fund & Gavi | none | none | none | Global Fund 0.20, Gavi 0.15 (user-set) |
| Combined | US 1.0; Germany, France, UK, Japan as OECD | Germany, France, UK, Japan as OECD (US 0) | as Full US Exit | none |

So under Full US Exit, US money through every other multilateral channel (UNICEF, UNAIDS, development banks, EU
institutions) has cut 0.

**IHME ratio** (built by `prepare_model.py`):
- ratio = IHME 2025 DAH / 2021-23 average DAH for the (donor group, channel group, bucket) cell, global totals.
- If the cell's baseline is under US$20M a year, the donor group x bucket ratio is used instead.
- Missing ratios count as 1; the ratio is clipped to 0-1.5.

**MOU schedule** for country i (America First MOUs only; countries without a schedule cannot run this preset):
- Requires `mou_us_ref` > 0 and `mou_us_2026` present.
- For each year y = 2026..2030: if `mou_us_<y>` is present, cut_y = clip(1 - mou_us_<y> / mou_us_ref, 0, 1);
  otherwise the last available year's cut is held.
- On US direct-channel rows the yearly cut is x_t = pair[US, c] if defined, else cut_t; then
  1 - (1 - x_t)(1 - y), clipped to -1..1.
- All other rows use the same cut every year.

**Funding path** p_t (share of the full cut in force in year t; 1 for every year = "Sudden"):

| Path | p_t, with u = (t+1)/5 |
|---|---|
| Linear phase-out | u: 0.2, 0.4, 0.6, 0.8, 1.0 |
| Front-loaded | 1 - (1 - u)^2 |
| Back-loaded | u^2 |
| S-curve | s_t / s_4, with s_t = 1 / (1 + exp(-1.5 (t + 1 - 3))) |

The cut in force on row r in year t is cut_r,t x p_t. MOU schedules are never multiplied by a path in the app.

**Gross loss by line and year:** G[l,t] = sum over the country's rows of line l of usd x cut x p_t. If G[l,t] < 0
(aid rises), the rise is recorded as a gain and G[l,t] = 0. Gains are not modelled.

**Aid at Risk** (headline) = mean over t of L_t, with L_t = sum over all lines (direct, linked, unspec, hss, ovc) of
G[l,t].
**Deepest-year loss** `gross_full` = max over t of the same sum with p_t = 1 (fiscal panel and break-even only).
**Baseline aid** = sum of `usd` over all the country's rows.

## 3. Money by service line (effective loss)

For bucket b and any money series X (baseline, or year t's G), with kappa = `hss_kappa`:
- mix_l = base_l / sum_{K_b} base. Here base is the country's raw baseline by line. If that sum is 0, the global mix
  is used: each known line's share of the bucket's known-line baseline summed over all countries in `dah_lines`.
- U = X[b_unspec], S = X[b_hss] (0 if absent; Immunization has neither).
- For each direct line l of b: E[l] = X[l] + (U + kappa x S) x mix_l.
- For the linked line `hiv_care_ct`: pool = X[care] + (U + S) x mix_care. E[care] = kappa x pool;
  nonservice[care] = (1 - kappa) x pool.
- nonservice[b] = (1 - kappa) x S x (1 - mix_care), with mix_care = 0 outside HIV.

Money is conserved: sum of E over K_b plus nonservice = X[direct] + X[care] + U + S.

E_base = the same with X = baseline. **Displayed per-line money** (service table; for hiv_art these are ART's own
amounts: the linked testing-and-care money has its own row, although its kappa share counts toward ART's units):
- base_usd = E_base[l];
- gross = mean over t of E_t[l];
- replaced = mean over t of the replacement allocated to l;
- net = gross - replaced.

## 4. Government response

**Fiscal capacity** (US$ a year):

    surge  = max(0, g_top - max(g_median, 0))      g_top = ghes_growth_p75 (or _p90 for "best years")
    stress = clip(1 - (interest_pct_revenue - 10) / 40, 0.25, 1)
    capacity = ghes_2023 x surge x stress           (0 if ghes_2023 is missing)

**Wanted replacement** in year t for loss L_t:

| Mode | Wanted | Paid R_t |
|---|---|---|
| none | 0 | 0 |
| gradual | 0 | 0 |
| custom | theta x L_t | min(wanted, capacity) when "cap to fiscal space" is on, else wanted |
| max | L_t | min(L_t, capacity) (always capped) |

**Gradual Budget Increase:** gov_add_t = points_t / 100 x gov_spend.
- gov_spend = ghes_2023 / (health share of government spending / 100).
- points_t follow the chosen shape (Steady p x (t+1); Fast start 5p (1 - (1 - u)^2); Slow start 5p u^2), capped at
  the room to the Abuja 15% share.

**Budget** B_t = min(R_t + gov_add_t, L_t): replacement never exceeds the loss.

**Allocation of B_t** over the year's positive effective losses E_t[l] (every money line: direct and `hiv_care_ct`)
and the positive nonservice amounts, each as a separate amount (nonservice[care], and nonservice[b] for each bucket):
- **Pro rata:** each amount gets B_t x amount / (sum of all positive amounts).
- **Lives first:**
  - Money lines are refilled in descending order of central deaths per US$ (dpd), each up to its own loss, until
    B_t runs out.
  - What is left goes to the nonservice amounts in proportion, each up to its own amount.
  - dpd[l] for hiv_pmtct, hiv_prev, hiv_ovc, tb_ds, tb_dr and imm = (sum over d = 0..4 of level_l,d x LAG_l[d]) /
    cost_l. Levels are as in section 6, at the central run, calendar-indexed. hiv_prev and hiv_ovc have level 0.
  - dpd[hiv_art] = art_hazard_mult x sum(ART_HAZARD) / cost_art.
  - dpd for malaria lines = sum over t = 0..4 of (that line's malaria part from section 6, with 1,000,000 / cost_l
    units on that line alone and 0 on the others) x LAG_l[t] x f_mal,t, divided by 1,000,000. This uses calendar t
    and has no rebound factor.
  - dpd[hiv_care_ct] = dpd[hiv_art].

**Net loss** by line: N_t[l] = E_t[l] - replacement_t[l].
**Displayed:** Replaced by Government = mean_t B_t; Net Aid Lost = mean_t (L_t - B_t).

## 5. People losing each service

**Need and baseline coverage:**

| Line | Need | Coverage |
|---|---|---|
| hiv_art | PLHIV | ART % |
| hiv_pmtct | HIV+ pregnancies | PMTCT % (ART % if missing) |
| tb_ds | TB incidence | TB detection % |
| tb_dr | DR_TB_SHARE x TB incidence | DR_TB_COV |
| mal_itn | PAR | `mal_itn_cov`; if NaN, `mal_itn_default_use` |
| mal_irs | PAR | see below |
| mal_cm | malaria cases | `mal_cm_cov`; if NaN, `mal_cm_default_cov` |
| imm | births | DTP3 % |
| hiv_prev, hiv_ovc | none | none |

**Spraying coverage.**
- implied = clip((E_base[mal_irs] at the central run / cost_irs) / PAR, 0, 1).
- If `mal_irs_cov` is NaN, or implied > `mal_irs_cov`, the coverage is implied; otherwise `mal_irs_cov`.
- If PAR is missing or 0, the implied value is not computed and the coverage is `mal_irs_cov` (NaN if that is
  missing too; NaN counts as 0 in section 6).

**Covered** = coverage x need (NaN if either is missing).
- For hiv_art: covered = max(ART % x PLHIV - PMTCT % x HIV+ pregnancies, 0). Women on PMTCT get their ART through the
  PMTCT line and its cost.

**Unit cost** (central run unless drawn):
- markup = 1 / (1 - asd_share).
- sc = (max(gdp_pc, 200) / 1000) ^ uc_scale_elast.
- **hiv_art:** (art_site_cost[country] inflated from its cost_year by CPI-U to 2023), or, if the country has none,
  (arv default + non_arv default x sc) inflated from 2018; then x uc_art_mult x markup.
- **hiv_pmtct** = uc_pmtct (includes the mother's ART). **hiv_ovc** = uc_ovc.
- **hiv_prev** = cpia_ref x (1 / inc)^0.5, with inc = new HIV infections / population x 1000, clipped to 0.05-10.
  inc = 0.3 if either input is missing. Unit: infection averted.
- **tb_ds, tb_dr** = tb_ds_cost or tb_dr_cost for the income group x uc_tb_mult x markup. An income group other than
  low or lower-middle uses upper-middle; a missing group is guessed from GDP per person (< 1,150 low, < 4,500
  lower-middle, else upper-middle). These values are already 2023 US$.
- **mal_itn** = uc_itn; **mal_irs** = uc_irs; **mal_cm** = uc_mal_cm; **imm** = uc_imm.

**Units lost** in year t, for each direct line:
- **Money.** n = N_t[l], with base b = E_base[l] and test base tb = E_base[l].
  - For hiv_art, n = N_t[hiv_art] + N_t[hiv_care_ct], b = E_base[hiv_art] + E_base[hiv_care_ct], and
    tb = E_base[hiv_art] only.
- **Two branches:**
  - If covered is NaN: raw = n / cost.
  - Else, if tb / cost > covered (donor money would buy more than everyone covered): raw = covered x n / b.
  - Else: raw = **n / cost**. (This is the usual case. There is no further scaling here.)
- units = raw x (1 - continuity).
- If need and coverage both exist, units = min(units, cap), with cap = covered for hiv_art and coverage x need
  otherwise.
- units = max(units, 0).
- hiv_prev and hiv_ovc have no cap (continuity applies).

**Displayed:**
- People Losing Service, per Year = mean_t units.
- 5-year total = sum_t units.
- Coverage drop (points) = mean_t units / need x 100 (for hiv_art the need is PLHIV).
- Coverage after = coverage - that.
- People Losing Care Each Year (hero) = sum of the per-year means over hiv_art, hiv_pmtct, tb_ds, tb_dr, mal_itn,
  mal_irs, mal_cm, imm.

## 6. Deaths and infections

**Death-rate switch.** "Account for already-changing death rates" is on by default (the dashboard, the All Countries
files and every audit run use it on). When it is off, every trend factor below is 1.

**Duration.** first = the first year t with any non-zero cut in force on any row (t = 0 for a sudden cut). For
t >= first, dur_t = t - first; otherwise dur_t = 0. LAG and the malaria rebound are indexed by dur_t. Mortality
trends are indexed by calendar t.

**Trend factors.**
- f_u5,t = (1 + trend_u5mr)^t.
- f_mal,t = (1 + trend_malaria_deaths)^t.
- Both use -0.009 if the trend is missing, and equal 1 when the "already-changing death rates" switch is off.

**Per-unit levels** (deaths per unit lost, calendar year t):
- a = ART % / 100 (0 if missing).
- hiv_pmtct: pmtct_vt_reduction x pmtct_infant_mort.
- tb_ds:

      dCFR = (1 - h)(tb_cfr_untreated_neg - tb_cfr_treated_neg) + h (tb_cfr_untreated_pos - tb_cfr_treated_pos)(1 - 0.3a)

- tb_dr: tb_dr_dcfr.
- imm: level_t = imm_deaths_per_child_ref x imm_u5_share x clip(U5MR x f_u5,t / 50, 0.3, 2.5).

**PMTCT, TB treatment:** deaths_t = units_t x level x LAG_l[dur_t].

**TB spread.**
- In each year s, secondary cases = (units_tb_ds,s + units_tb_dr,s) x tb_secondary. Half arrive in year s+1 and half
  in s+2.
- Coverage c_t = clip(TB detection % / 100 - units_tb_ds,t / TB incidence, 0, 1) (0 if TB need or coverage is
  missing). A case arriving in year t uses c_t, the coverage of its **arrival** year; arrivals after 2030 use c_4.
- An arriving case dies with probability c x cfr_t + (1 - c) x cfr_u, where:

      cfr_u = (1 - h) tb_cfr_untreated_neg + h tb_cfr_untreated_pos (1 - 0.3a)
      cfr_t = (1 - h) tb_cfr_treated_neg + h tb_cfr_treated_pos (1 - 0.3a)

- Arrivals in 2027-2030 add to tb_ds deaths in that year (no LAG). Arrivals in 2031-2032 count in further deaths
  (part "tb").

**Vaccines.** (After 2030 the level is level_4 x the trend, without a new clip: a country on the 0.3 floor can fall
below it.)
- Each year s's lost children die over the following years with weights w = (0.40, 0.35, 0.20, 0.05) for k = 0..3
  (k = 0 is the same year).
- Deaths in year t <= 4 = sum over s <= t of units_imm,s x w_(t-s) x level_t.
- For t >= 5 (2031 onward): units_imm,s x w_(t-s) x level_4 x (1 + u5trend)^(t-4). Here u5trend = trend_u5mr
  (-0.009 if missing) when the switch is on, else 0, and these deaths count in further deaths (part "imm").
- For a sudden cut this equals units x level_t x (0.4, 0.75, 0.95, 1, 1).

**HIV treatment** (cohorts):
- **Stock.** stock_t = units_hiv_art,t. Each year, delta = max(stock_t, 0) - max(stock_(t-1), 0) (stock_-1 = 0).
  - A fall (delta < 0) first removes people from the most recent cohorts.
  - A rise adds a new cohort of size delta with age 1.
- **Each year t, for every cohort** (size, age):
  - deaths += size x art_hazard_mult x ART_HAZARD[min(age, 5) - 1];
  - infections += size x art_transmission x ART_INFECT_LAG[min(age, 5) - 1];
  - then every cohort's age increases by 1.
- **Negative stock** (only possible with gains): adds stock_t x hazard[t] and stock_t x art_transmission x
  ART_INFECT_LAG[t].
- **After 2030** (funding back): in year k = 0..4, each cohort still off care has size x (1 - art_reengage)^(k + 0.5)
  people, with age a = min(age_at_end_2030 + k, 5). age_at_end_2030 is the cohort's age after the 2030 increment: a
  cohort that started in 2026 has age 6, so it uses the year-5 values. It adds deaths (people x art_hazard_mult x ART_HAZARD[a - 1],
  part "hiv_art") and infections (people x art_transmission x ART_INFECT_LAG[a - 1]).
- **Sudden cut:** one cohort of size U from 2026, so deaths_t = U x art_hazard_mult x ART_HAZARD[t].

**New HIV infections and their deaths** (10 years, 2026-2035):
- **Infections:**
  - from people off ART (above, 2026-2035);
  - lost prevention = units_hiv_prev,t (2026-2030 only);
  - PMTCT infant infections = units_hiv_pmtct,t x pmtct_vt_reduction. These count as infections but their deaths are
    already in the PMTCT line, so they are not run through the curve.
- **Timing:** λ = hiv_survival_median / ln(2)^(1/2.25) and F(x) = 1 - exp(-(max(x, 0) / λ)^2.25). The share of an
  infection's eventual death in year k after infection (k = 0 is the infection year; infections mid-year) is
  F(k + 0.5) - F(k - 0.5).
- **Risk:**
  - Off-ART count: off_t = units_hiv_art,t for 2026-2030, then the people still off care for 2031-2035.
  - ART coverage: cov_t = clip(ART % / 100 - off_t / PLHIV, 0, 1) (0 if PLHIV or ART % is missing).
  - risk_t = cov_t x hiv_inf_death_treated + (1 - cov_t) x hiv_inf_death_untreated.
- **Deaths** in year t from infections in year s <= t: infections_s x [F(t - s + 0.5) - F(t - s - 0.5)] x risk_t.
  - 2026-2030 deaths from off-ART infections add to hiv_art; those from prevention add to hiv_prev.
  - 2031-2035 deaths from both count in further deaths (part "hiv_infections").
- **Displayed New HIV Infections, 5 Years** = sum over 2026-2030 of off-ART infections + lost-prevention infections +
  PMTCT infant infections. By line: off-ART infections belong to hiv_art, lost prevention to hiv_prev, infant
  infections to hiv_pmtct.

**Malaria** (Lives Saved Tool form), for year t with that year's units:
- **If D0 is missing or ≤ 0:** no malaria deaths.
- **Baseline coverage:**
  - n0 = bednet use (default if NaN);
  - r0 = spraying coverage (0 if NaN);
  - m0 = treatment coverage (default if NaN).
- **After the loss:**
  - n1 = clip(n0 - units_itn / PAR, 0, 1);
  - r1 = clip(r0 - units_irs / PAR, 0, 1);
  - m1 = clip(m0 - units_cm / cases, 0, 1).
  - Where PAR or cases are missing or 0, the subtracted term is 0.
- **Combined vector control:** vc(i, r) = 1 - (1 - i)(1 - r); cv0 = vc(n0, r0), cv1 = vc(n1, r1).
- **Ratios:** rv = (1 - Ev cv1) / (1 - Ev cv0); rc = (1 - Ec m1) / (1 - Ec m0), with Ev = mal_vc_eff and
  Ec = mal_cm_eff.
- **Extra deaths:** total = D0 (rv rc - 1); dv = D0 (rv - 1); dc = D0 (rc - 1).
- **Split:**
  - Vector part = total x |dv| / (|dv| + |dc|); treatment part = total x |dc| / (|dv| + |dc|). If both are 0,
    divide by 1.
  - The vector part splits between itn and irs in proportion to cv0 - vc(n1, r0) and cv0 - vc(n0, r1); half each if
    both are 0.
- **Year t:**
  - mal_itn and mal_irs: part x LAG_l[dur_t] x f_mal,t x (1 + mal_resurgence)^dur_t.
  - mal_cm: part x f_mal,t (its LAG is 1).

**Totals.**
- Extra Deaths 2026-2030 = sum over direct lines and years of deaths.
- Year 1 = 2026.
- Further deaths 2031-2035 = sum of the parts:
  - hiv_art: deaths among people still off ART;
  - hiv_infections: 2031-2035 deaths from all infections (off-ART and lost prevention) in 2026-2035;
  - imm: vaccine cohort deaths after 2030;
  - tb: TB spread cases arriving in 2031-2032.

## 7. Displayed totals by disease

For each bucket:
- deaths = sum over its direct lines;
- base / gross = raw line sums of its lines (all, including unspec, hss, ovc, care);
- replaced = mean_t of the replacement allocated to its money lines and nonservice amounts;
- net = gross - replaced.

Deaths per US$1M (bucket) = deaths_5y / 5 / (net / 1e6), shown only if net > US$10,000.

## 8. "What Every US$1 Million Cut Does" cards

- For a disease with total aid A (all of its rows, including unspec, hss, ovc and care), run sections 2-6 with:
  - every row of that disease cut by c = min(1, 1,000,000 / A) for all donors and channels;
  - every other row cut by 0;
  - sudden path, no government response.
- Then k = 1,000,000 / (that run's disease gross loss).
- **Card values:**
  - people = units on the main line (hiv_art, tb_ds, mal_itn, imm) x k;
  - coverage drop = that line's coverage drop x k;
  - deaths = the disease's 5-year deaths x k;
  - aid per death = 5,000,000 / deaths.

## 9. Uncertainty

**Draws.** Each parameter is drawn 400 times, independently, from triangular(low, central, high), with seed 7, in
the order of `model_params.csv`.
- A parameter with high ≤ low is constant. It still consumes its draws, so the others don't shift.
- The draws are identical in every country.

**Each displayed range** is the 2.5th-97.5th percentile of the draws for that quantity. The point value is the central
run, not the median.

**Name.** These ranges are called "range across parameter values". They reflect uncertainty in model parameters only;
uncertainty in the data and in the model's structure is larger and not included. They are not confidence intervals.

**All Countries totals:**
- Totals add up each country's central value.
- The range is the 2.5th and 97.5th percentile, over the 400 draws, of the all-country total in each draw. Because
  the draws are identical in every country, the total of draw i over countries is draw i of the total. Countries
  with no aid loss contribute 0 in every draw. (Adding up country percentiles, as before, overstates the width.)

## 10. Precomputed All Countries files

`model_data/all_countries_<preset>.csv`:
- every preset except Custom;
- no government response, sudden path, trends on, 400 draws;
- one row per country, with the columns written by `health_model.run_all`.

`model_data/all_countries_<preset>_draws.csv`: one row per draw (`draw` 0-399), with the all-country total of
`deaths_5y` (2026-2030) and `deaths_after_2030` (2031-2035) in that draw. The All Countries and Validation ranges come
from these.
