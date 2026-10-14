# Independent reproduction: notes

Script: `repro.py` (run with no arguments to write `independent.csv`; `--resurgence-exp t-1` writes
`independent_resurgence_tminus1.csv`, the alternative reading in a.14). This covers central values only, for
KEN/NGA/IND/HND/MOZ and cases 1-4. Money is conserved within 0 US$ in every run: sum of E + non-service = L_t.

Files read: logic.md sections 0-6, METHOD.md (for the gaps below), model_data/dah_lines.csv,
model_data/country_inputs.csv, model_params.csv, unit_cost_reference.csv. The model_data/all_countries_*.csv files
are model outputs. I looked only at their header line, and I did not use them.

## (a) Places where logic.md is ambiguous, incomplete, or contradicts the data

1. **§0 Constants: ART_HAZARD is listed with no value.** I used §5: art_hazard_mult x (0.012, 0.028, 0.038, 0.045,
   0.050). The latest commit message says "ART hazard calibrated per supported patient, applied per full-cost
   equivalent". This suggests the constant may now differ from these numbers, but logic.md gives no other value.
2. **§1 Full US Exit: what happens to US money through other multilateral channels (UNICEF, UNAIDS, Development
   banks, EU institutions) is not stated.** I set it to 0, following METHOD.md: only the WHO, Gavi, UNFPA and Global
   Fund pairs are cut. The table does not say what "the donor's multilateral cut" is for the US.
3. **§1 The direct-channel set includes "Other", but dah_lines.csv has no `Other` channel.** The channels in the data
   are Global Fund, WHO, UNAIDS, NGOs, UNICEF, Bilateral agency, Development banks, UNFPA, Gavi, Gates direct and EU
   institutions. Donor "Other / unallocable" exists, but it is a donor (src_grp), not a channel.
4. **§1 OECD preset: the donor names are not spelled as in the data.** I matched UK -> `United Kingdom` and applied
   each cut to every channel of that donor. Groups such as "Other DAC governments" are not cut.
5. **§1/§3 Linear path.** logic.md says cut x path_t but not how years are counted for LAG, cohorts and resurgence
   under a gradual path. I took "years the cut has lasted" = t, because the cut starts in 2026 in every case.
6. **§2 The per-line gross loss to report is not defined.** It could be raw G[l] or effective E[l]. I report the
   mean over years of E[l,t] (and E_base for base_usd). For hiv_art, base/gross/net are ART's own E only. The units
   calculation adds the kappa part of hiv_care_ct (§4). Diagnostics in the script give care_eb and care_gross per
   country.
7. **§2 "global mix if the country has none".** Not needed for these 5 countries, but the definition is ambiguous:
   is it the global share over K_b, and is hiv_care_ct included? I used the global base over K_b, including care.
8. **§3 Allocation when a line's E is negative.** This cannot happen here, because G is clipped at 0. The
   denominator of "share of the year's effective loss" is taken as L_t.
9. **§4 Several unit-cost inputs are missing from logic.md:**
   - **CPI factor** for "95 x CPI": I used 304.702/251.107 (2018->2023) from METHOD.md, and 2020 for ZWE.
   - **hiv_prev "incidence per 1,000"**: the population is not stated. I used METHOD.md:
     `sh_hiv_incd_tl / sp_pop_totl x 1000`, clipped to [0.05, 10], with 0.3 if missing. IND and HND hit the 0.05
     floor.
   - **Laurence cost table**: which income group to use when the country is upper-middle or unclassified is not
     stated. I used METHOD.md: anything other than LIC or LMIC uses UMIC.
   - **GDP missing default**: not stated (not needed here).
10. **§4 Coverage/need column names are not given.** I identified them by name and magnitude:
    - PLHIV = `plhiv`, not the stale `people_living_with_hiv_number_all_ages` (2009/2011) and not the
      `plhiv_calibration` ratio.
    - ART % = `sh_hiv_artc_zs`; PMTCT % = `sh_hiv_pmtc_zs`; HIV+ pregnancies = `hiv_pos_pregnancies`.
    - TB incidence = `all_forms_of_tb_incidence_estimated` (absolute count), not `sh_tbs_incd`, which is per 100k.
      CDR = `sh_tbs_dtec_zs`.
    - Population at risk = `malaria_pop_at_risk`; ITN = `mal_itn_cov`; IRS = `mal_irs_cov`; cases =
      `malaria_cases`; CM coverage = `mal_cm_cov`; births = `births`; DTP3 = `sh_imm_idpt`.
    - D0 = `malaria_deaths`; h = `tb_hiv_share`; U5MR = `sh_dyn_mort`.
    - Fiscal inputs: `ghes_2023`, `ghes_growth_median`/`_p75`, `interest_pct_revenue`.
11. **§4 IRS "donor IRS money / cost / population at risk": which money?** I used E_base[mal_irs] (the effective
    baseline) and clipped it to 1. If MAP is missing, the money-based value is used alone (METHOD.md).
12. **§4 Units for ART: logic.md and METHOD.md disagree in the else branch.**
    - logic.md: units = N/cost, where N includes the care-kappa part.
    - METHOD.md: raw = min(covered, Eb_art/cost) x N/(Eb_art + Eb_care_kappa).
    - I followed logic.md (units = (N_art + N_care,kappa)/cost). In KEN case 1 that gives 451.7k units per year;
      METHOD.md's formula would give about 328k. This is a material difference.
13. **§4 hiv_prev has no need or coverage.** I applied (1 - continuity) to it and only clipped at 0. logic.md does
    not say whether continuity applies to prevention.
14. **§5 Malaria resurgence exponent is ambiguous.**
    - logic.md writes `(1 + 0.10)^(years the cut has lasted)`, which is 1 in 2026 if "lasted" is counted the same
      way as LAG. METHOD.md writes `(1 + mal_resurgence)^(t-1)`.
    - I used the literal logic.md reading (exponent = t) in `independent.csv`. The t-1 alternative is in
      `independent_resurgence_tminus1.csv`.
    - The difference in 5-year deaths: NGA about 3-4k, MOZ and KEN 0.3-0.7k, IND and HND about 0.
15. **§5 Malaria year factors.** logic.md says "x LAG"; I applied each line's own LAG to its share. The 0.5/0.8/1 LAG
    values come from §5's ramp list ("treatment 1" taken to mean mal_cm).
16. **§5 Malaria split when both falls are 0 is not stated.** I used half each (METHOD.md).
17. **§5 TB secondary cases: CFR_treated/CFR_untreated are not defined** (HIV blend? ART adjustment?). Other gaps:
    - whether units are taken before or after LAG;
    - which c_t applies after 2030.
    I used METHOD.md:
    - cfr = (1-h) x neg + h x pos x (1 - 0.3a);
    - units without LAG;
    - c_t = clip(cov - units_ds,t/need, 0, 1), with the year-5 value after 2030.
    Secondary deaths are put on the tb_ds line. logic.md also does not say which line they belong to.
18. **§5 Immunization timing: "die over the following years 0.40, 0.35, 0.20, 0.05" is ambiguous.** Does the first
    weight fall in the year of loss or the next year? I used METHOD.md: weight 0 = same year. Two related points:
    - The level is evaluated in the death year.
    - After 2030 I kept logic.md's clip(U5MR_t/50, 0.3, 2.5) formula. METHOD.md instead says "2030 level x
      (1+trend)^k". The two differ when the clip binds: HND U5MR 15 sits on the 0.3 floor, so HND's post-2030
      vaccine deaths depend on this choice.
19. **§5 ART after 2030.** logic.md gives the 0.5/yr re-engagement but not the timing. Also missing: the hazard for
    years 6+ ("year-5 value after that" is in the cohort sentence), and whether transmission continues. I used
    METHOD.md:
    - still off = size x 0.5^(k+0.5), with k = 0 in 2031;
    - hazard by each cohort's own years off, capped at the year-5 value;
    - transmission at 0.04/yr continues, and those infections feed infection deaths up to 2035.
20. **§5 ART transmission "0.5 in year 1".** I applied it per cohort (each cohort's first year), not only to 2026.
    This only matters for the linear path.
21. **§5 HIV infection deaths: logic.md gives only "Weibull timing x risk_t, cov_t".** I took the rest from
    METHOD.md:
    - mid-year infection, share in year k = F(k+0.5) - F(k-0.5);
    - lambda = median / ln2^(1/2.25);
    - cov_t = clip(ART cov - people off ART_t / PLHIV);
    - deaths from off-ART infections go to hiv_art and deaths from prevention infections to hiv_prev;
    - PMTCT infant infections are not run through the Weibull (their deaths are already in the PMTCT line).
    It is also unclear whether "through 2035" means infections up to 2035 or deaths up to 2035. I used both (infections
    from off-ART people continue after 2030; prevention infections only 2026-30).
22. **§5 PMTCT infections (units x 0.25): no LAG** is applied. logic.md shows LAG only on PMTCT deaths.
23. **§5 TB dCFR as written,** `(1-h)(0.43-0.03) + h(0.62(1-0.3a) - 0.06(1-0.3a))`. It uses tb_cfr_* parameters
    and matches METHOD.md. The "a" used is ART coverage (sh_hiv_artc_zs/100), not reduced coverage.
24. **§3 The fiscal formula does not say how missing values are handled.** No values were missing for these five
    countries. Capacity is used as a flat yearly cap. Replacement in case 2 is theta x L_t, capped:
    - KEN and MOZ are capped by capacity (21.1M and 25.6M);
    - NGA, IND and HND get the full 25%.
25. **§4 Coverage after.** "coverage - mean units / need": for ART I used need = PLHIV, although covered excludes
    PMTCT women.

## (b) Uses of METHOD.md

- Full US Exit treatment of other US multilateral channels (a.2).
- CPI factors (a.9).
- hiv_prev incidence denominator and clip (a.9).
- Income-group fallback for TB (a.9).
- IRS coverage rule when MAP is missing (a.11).
- Malaria split default (a.16).
- TB secondary CFR definitions and c_t (a.17).
- Immunization weight timing (a.18).
- ART post-2030 re-engagement timing and transmission (a.19).
- Weibull infection-death details (a.21).
- Missing-value defaults: U5MR 50, trend -0.009, h 0.
- Column names, cross-checked against METHOD.md's table.

Where METHOD.md conflicted with logic.md, I followed logic.md: the ART units else-branch (a.12), the resurgence
exponent (a.14), and the post-2030 vaccine level (a.18).

## (c) Data observations

- **`malaria_at_risk_share` contradicts `malaria_pop_at_risk`.** For KEN, NGA and MOZ the share is 0.95, but
  `malaria_pop_at_risk` equals the full `sp_pop_totl`, i.e. a share of 1.0.
- **IND and HND population at risk is a default share.** Their population at risk is 0.35 x population (IND 1.36
  billion, HND 9.8M), but HND has 2,559 cases, 0 malaria deaths and `sh_mlr_incd_p3` 0.23 per 1000. These look like
  an assumed share, not data.
- **HND ITN coverage is the default.** It is missing, so the 0.5 default is used, which is implausible for HND.
  There is no deaths impact because D0 = 0.
- **IND ITN coverage is old.** It is a 2021 survey value of 4.4%, with no MAP value.
- **Two population-at-risk sources disagree.** `malaria_pop_at_risk_source` says "WHO: estimated cases / ..." while
  `malaria_cases` comes from MAP 2025. They are different sources and years. WHO `malaria_cases_prev` is similar in
  magnitude.
- **IRS coverage is partly money-based.**
  - NGA MAP IRS = 0.0, so the money-based value (about 1.0%) is used.
  - IND and HND have no MAP IRS, so the money-based value is used: HND 0.2%, IND about 0.005%.
  - KEN uses MAP at 2.7%, which is above the money-based 1.8%.
- **`hiv_pos_pregnancies` is not an integer** (HND 292.857 = 164 / 0.56). It is derived as women receiving PMTCT /
  PMTCT coverage, so PMTCT coverage x need just gives back the number receiving.
- **Stale `people_living_with_hiv_number_all_ages`.** It is from 2009/2011 and very different from `plhiv` (NGA 3.4M
  vs 2.0M; MOZ 1.4M vs 2.5M). `plhiv_calibration` (NGA 1.6, MOZ 0.81) is unexplained in the spec.
- **IND and HND hit the prevention-cost floor.** HIV incidence per 1000 population is below 0.05 (IND 0.044, HND
  0.046), so the cost per infection averted is the ceiling of about 22.4k.
- **DR-TB unit costs are non-monotone across income groups.** LIC 1,568 < UMIC 6,800 < LMIC 8,125 (single
  studies). After markup, MOZ (LIC) pays 2,851 per DR-TB patient vs 14,773 in the LMICs.
- **IND DR-TB aid is large.** IND tb_dr baseline aid (16.2M raw, 69.3M effective) exceeds tb_ds (7.2M raw). Most of
  IND's TB money is tb_hss (82M) and tb_unspec (36M), which the mix pushes mostly to tb_dr.
- **IND malaria trend is clipped.** `trend_malaria_deaths` (-0.05) differs from `trend_malaria_deaths_fit`
  (-0.110) for IND and HND, consistent with a ±5% clip. I used the clipped column.
- **TB-HIV share.** `tb_hiv_share` = tb_hivplus_incidence / TB incidence (KEN 0.214 = 25000/117000). This is
  consistent.
- **Gaps in MOU and fiscal columns.** `mou_gf_ref`, `mou_wb_ref` and `mou_oth_ref` are all NaN for these countries.
  NGA has NaN for every WB fiscal series, but `interest_pct_revenue` is filled from the IMF. These are not used here.
- **Coverage values are within range.** None exceeds 100%. TB case detection for IND is 92%.
- **Units hit the coverage cap in places.** HND hiv_art: donor money / cost (16.6k) exceeds covered ART patients
  (14.7k), so the "covered x N / E_base" branch is used. HND loses about 39% of ART coverage in case 1.
