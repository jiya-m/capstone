# Independent reproduction: notes

Script: `repro.py`. Run it with no arguments to write `independent.csv`. It has no options; the old
`--resurgence-exp` switch is gone. It computes central values only, for KEN, NGA, IND, HND and MOZ and cases 1-4:

1. Full US Exit, no response, sudden.
2. Full US Exit, custom theta = 0.25 capped at fiscal capacity (p75), pro rata, sudden.
3. OECD 2025, no response, sudden.
4. Full US Exit, no response, linear phase-out.

Money is conserved exactly in every run: the sum of E plus the nonservice amounts equals L_t. The column for deaths
in 2031-2035 is now called `C.after_2030` (it was `C.deaths`). All other column names are unchanged.

## (a) Places where SPEC.md is ambiguous, incomplete or contradicts the data

1. **§1 Lines / §2 "Direct channels".** The spec lists `Other` as a direct channel and says itself that no such channel
   is in the data. I confirmed this: the data has 11 channel groups and none is `Other`. This has no effect.
2. **§2 Presets table, donor names.** The table writes "US"; in the data the donor is `United States`. I matched "US"
   to `United States`. Germany, France, United Kingdom and Japan match exactly.
3. **§6 "Trend factors": "equal 1 when the 'already-changing death rates' switch is off."** The spec never says
   whether the switch is on or off for an ordinary run. It is only stated for the precomputed files ("trends on",
   §10). I assumed it is on for all four cases.
4. **§4 table, custom: "when 'cap to fiscal space' is on".** The spec gives no default. The task defines case 2 as
   capped, so I capped it.
5. **§4 "Allocation of B_t".** The pro-rata pool contains "positive nonservice amounts", but the spec does not say
   whether nonservice is one amount per bucket or several. §3 defines two kinds: nonservice[care] and
   nonservice[b]. I kept them as separate amounts. Under pro rata the result is the same either way. Because every
   E and nonservice amount here is >= 0 and they add up to L_t, pro rata equals scaling every line by B_t / L_t.
6. **§1 "growth ... 0 if missing" and §4 "capacity = ... (0 if ghes_2023 is missing)".** The spec does not say what
   happens when only the median growth is missing. I set it to 0, which gives surge = g_top. Nothing is missing for
   these countries.
7. **§5 hiv_prev unit cost: "inc = new HIV infections / population x 1000, clipped to 0.05-10 (0.3 if missing)".**
   It is not clear whether 0.3 applies when either input is missing, and the spec does not cover a population of 0.
   I used 0.3 in both cases. Nothing is missing here. IND (0.044) and HND (0.046) hit the 0.05 floor.
8. **§5 "Spraying coverage".**
   - "If PAR is missing, the coverage stays NaN" contradicts the rule just before it, which uses `mal_irs_cov` when
     the implied value is not larger. I read it as: PAR missing gives NaN even if `mal_irs_cov` exists.
   - PAR = 0 is not covered, because the implied value divides by PAR. I treat the implied value as NaN and use
     `mal_irs_cov`.
   - Neither case occurs here. For NGA, `mal_irs_cov` = 0 and the implied value is about 1%, so the implied value is
     used. IND and HND have no MAP value, so they use the implied value. KEN uses MAP (2.7%), which is above the
     implied 1.8%.
9. **§5 "Covered", hiv_art: max(ART % x PLHIV - PMTCT % x HIV+ pregnancies, 0).** The spec does not say what happens
   when HIV+ pregnancies is missing. In that case I subtract nothing. It also says "Covered = ... NaN if either is
   missing" without saying whether that applies here; I made covered NaN only when ART % or PLHIV is missing. Nothing
   is missing here.
10. **§5 TB unit cost, missing income group.** This is guessed from GDP per person. If GDP is also missing, the spec
    does not say whether the 1,000 default from §1 is used before the guess. I used it, which gives `low_income`.
    This does not occur here.
11. **§5 / §1 data note.** `hiv_pos_pregnancies` is not a whole number (HND 292.857 = 164 / 0.56). It appears to be
    derived as women on PMTCT / PMTCT %, so PMTCT % x need simply gives back the number on PMTCT. This is a data
    observation, not a spec gap.
12. **§6 "Duration": "first = the first year t with any non-zero cut in force on any row".** The spec does not say
    what happens if no row is ever cut. I set first = 0, which has no effect because there are then no losses. In all
    four cases first = 0; the linear path has p_0 = 0.2. "Any row" is read as any row of the country, in any bucket,
    not per line.
13. **§6 HIV treatment, "age a = min(age_at_end_2030 + k, 5)".** "age_at_end_2030" could mean the age used in 2030 or
    the age after the 2030 increment ("then every cohort's age increases by 1"). I used the age after the increment:
    - a cohort that starts in 2026 has age 6, so a = 5 from 2031;
    - a cohort that starts in 2030 has age 2 in 2031.

    This is consistent with ages continuing to count up one per year. With the other reading, the 2031 hazard would be
    one step lower for cohorts younger than 5. For sudden cuts this has no effect (a = 5 either way). It matters only
    for the newer cohorts of the linear path (case 4).
14. **§6 TB spread: "An arriving case dies with probability c x cfr_t + (1 - c) x cfr_u".** The spec does not say
    which year's c is used: the arrival year or the year the case was generated. "Years after 2030 use c_4" suggests
    the arrival year, and I used that.
15. **§6 Vaccines.** The spec defines "level_t" for t <= 4 only through the clipped formula. For t >= 5 it uses
    level_4 x (1 + u5trend)^(t-4), with no clip. I applied that literally. It matters for HND, whose U5MR of 15 puts
    level_t on the 0.3 floor: after 2030 its level keeps falling below the floor. The §1 LAG row for imm
    ("cumulative") is not used for deaths. It is consistent with the weights for a sudden cut (§6, last bullet under
    Vaccines).
16. **§6 Malaria: "If both are 0, divide by 1" and "half each if both are 0".** For the itn/irs split, the spec does
    not cover fi + fr = 0 with fi and fr non-zero and of opposite sign. That cannot happen because units >= 0. I
    followed the text literally (both exactly 0 gives half each).
17. **§6 "Displayed New HIV Infections" and the per-line `infections_5y` columns.** The spec defines only the total.
    I report:
    - `L.hiv_art.infections_5y` = off-ART infections 2026-2030;
    - `L.hiv_prev.infections_5y` = lost-prevention infections;
    - `L.hiv_pmtct.infections_5y` = infant infections (units x pmtct_vt_reduction, no LAG).
18. **§6 Totals: "Further deaths 2031-2035 = parts hiv_art, hiv_infections, imm and tb".** I took
    "hiv_infections" to mean the 2031-2035 deaths from both off-ART and prevention infections, as the bullet under
    "Deaths" says. "tb" is the 2031-2032 TB-spread arrivals. Malaria and PMTCT have nothing after 2030.
19. **§5 Units, `hiv_ovc`.** "hiv_prev and hiv_ovc have no cap (continuity applies)". The spec does not give the
    hiv_ovc output, and it is not among the requested columns. I compute it but do not report it.
20. **§5 "Coverage drop (points) = mean_t units / need x 100".** For hiv_prev the need is "none", so the drop is NaN.
21. **§3 "Displayed per-line money".** For hiv_art, base, gross and net are E[hiv_art] only. The hiv_care_ct E (the
    kappa x pool part) enters ART units through §5 but is not shown on the ART line. I followed this literally.
22. **§1 constants / unit_cost_reference.csv.** The TB costs have `cost_year` 2023, consistent with §5 ("already 2023
    US$"). The ART site costs are 2018 (ZWE 2020), and both years are in the CPI-U table. There is no conflict, but
    `cost_year` for TB is not used.
23. **§2 IHME and MOU, §4 "max", "gradual" and "lives first", §7-§9.** None of these are needed for the four cases,
    so they are not exercised and not checked here. The government-response code includes "max" and "none"/"gradual"
    for completeness, with gov_add = 0.

## (b) Changes made to repro.py to follow SPEC.md

1. **Malaria resurgence exponent.** Changed from (t + 1), the previous default, to dur_t, following §6 "Year t: ...
   (1 + mal_resurgence)^dur_t". The 2026 factor is now 1. The `--resurgence-exp` option and its alternative output
   file were removed.
   - Effect: 5-year deaths fall by about 4.2k in NGA case 1 (2.9-4.2k across NGA cases), 0.3-0.7k in KEN and MOZ, and almost nothing in IND
     (HND has D0 = 0).
2. **Vaccine deaths after 2030.** Changed from the clipped clip(U5MR x f_t / 50) level evaluated in years 5-9 to
   level_4 x (1 + u5trend)^(t-4), following §6 "Vaccines".
   - Effect: HND `C.after_2030` falls by about 0.5-0.9 deaths per case. Nothing else changes, because the clip does
     not bind elsewhere.
3. **Missing malaria trend default.** Changed from 0 to -0.009 (§1 table, §6 "Trend factors"). No effect here.
4. **CPI.** Replaced the hand-coded 2018/2020 factors with the full CPI-U table from §1, used as CPI_2023 /
   CPI_cost_year. No numerical effect.
5. **Missing income group.** Now guessed from GDP per person (< 1,150 low, < 4,500 lower-middle, else upper-middle)
   instead of falling through to upper-middle (§5). No effect here.
6. **Fiscal capacity.** Growth figures that are missing are now 0, and a missing ghes_2023 gives capacity 0 (§1, §4).
   The cap is applied only when "cap to fiscal space" is on, and a "max" mode was added. The budget is
   B_t = min(R_t + gov_add_t, L_t) with gov_add = 0. No effect here.
7. **Pro-rata allocation.** This now follows §4 literally: B_t x amount / sum of all positive E_t[l] (direct lines
   and hiv_care_ct) and positive nonservice amounts. Previously the denominator was L_t. The result is identical here.
8. **Spraying coverage.** Rewritten as §5 states it:
   - implied = clip(E_base[mal_irs] / cost / PAR, 0, 1);
   - use the implied value if `mal_irs_cov` is NaN or the implied value is larger, else `mal_irs_cov`;
   - NaN if PAR is missing.

   The result is identical here.
9. **Malaria guards (§6).** r0 = 0 if the spraying coverage is NaN. The subtracted terms are 0 where PAR or cases are
   missing or 0. A missing D0 now means no malaria deaths. Previously it was filled with 0, which has the same
   effect. No effect here.
10. **Unit cap (§5).** The cap now applies only "if need and coverage both exist". The cap is covered for hiv_art and
    coverage x need otherwise. The result is identical here.
11. **LAG and resurgence indexing.** These now use dur_t from the §6 "Duration" rule instead of the calendar t. The
    result is identical in these cases, because first = 0. Trend factors stay on calendar t.
12. **HIV cohorts.** These are now tracked as explicit (size, age) pairs, following §6:
    - delta of the clipped stock;
    - most recent cohorts leave first;
    - hazard and infection lag indexed by min(age, 5) - 1;
    - the ART_INFECT_LAG table is used in place of a hard-coded 0.5 in year 1;
    - post-2030 age = min(age_at_end_2030 + k, 5), with ART_INFECT_LAG applied after 2030 (it is 1 there);
    - a negative-stock branch is included.

    The result is identical here.
13. **Off-ART count for the infection-death risk.** For 2026-2030 this is now units_hiv_art,t, as stated in §6,
    instead of the sum of cohort sizes. These are equal when the stock is >= 0. cov_t = 0 when PLHIV or ART % is
    missing; previously that gave NaN.
14. **TB spread coverage.** c_t = 0 when TB need or detection % is missing (§6). Previously that gave NaN.
15. **ART % for TB and HIV formulas.** a = 0 if ART % is missing (§6). Previously the value was handled in two ways.
16. **Output column renamed.** `C.deaths` is now `C.after_2030`. It is computed explicitly as the parts listed in §6
    "Totals": hiv_art, hiv_prev (infection deaths), imm and tb_ds (spread). The value is the same as summing every
    line after 2030.
17. **Docstring and comments.** These now cite SPEC.md sections only. All references to logic.md and METHOD.md were
    removed. The constants ART_INFECT_LAG, the Weibull shape and POST_YEARS are defined from §1.

Compared with the previous `independent.csv`, the only values that changed are the following. Everything else
matches to rounding.
- Malaria itn/irs deaths and therefore T.deaths_5y, in all cases for KEN, NGA, IND and MOZ (change 1).
- HND `C.after_2030` (change 2).

## (c) What I consulted

For this rebuild I read only:
- `docs/SPEC.md`;
- the data files `model_data/dah_lines.csv`, `model_data/country_inputs.csv`, `model_data/ihme_trend.csv` (header
  only, since no case uses IHME), `model_params.csv` and `unit_cost_reference.csv`;
- the previous `repro.py` and `notes.md` in this folder.

I did not open `audit/METHOD.md`, `audit/logic_review/logic.md`, any model code (`health_model.py`, `scenarios.py`,
`model_section.py`, `budget_section.py`, `paths_ui.py`, `prepare_model.py`, `views/`), any audit script or snapshot
CSV, or `tests/`. I did not import any model module.

The previous `repro.py` had been built partly from METHOD.md. I checked each of its rules against SPEC.md and kept a
rule only where SPEC.md states it. Every rule taken from METHOD.md in the earlier notes is now written in SPEC.md:
- Full US Exit with the other multilateral channels at 0;
- the CPI table;
- the hiv_prev incidence;
- the TB income-group fallback;
- the TB-spread CFRs and c_t;
- the vaccine weight timing;
- the ART post-2030 re-engagement;
- the Weibull details.

## (d) Result against the dashboard

`compare.py` checks `independent.csv` against the dashboard's own values in an audit snapshot.
- **Run:** `.venv/bin/python audit/logic_review/reproduction/compare.py audit/before_do_now.csv`, with the snapshot
  taken on commit 2cfcb14 before any of the "Do now" changes.
- **Result:** 1,860 cells compared, **1,860 within 0.5%**; largest difference 0.0000%.
- **What changed in SPEC.md afterwards:** ambiguities 3, 5, 7, 8, 12, 13, 16, 17 and 20 above were clarified (the
  default of the death-rate switch; nonservice amounts allocated separately; the prevention incidence fallback;
  spraying coverage when PAR is missing; cohort age after 2030; TB arrival-year coverage; infections by line; the four
  further-death parts; ART's own money in the table). In each case the reading taken here was the code's.
