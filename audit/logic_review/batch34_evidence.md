# Batch 3+4: money-to-people conversion, unit costs, cap rule, TB treatment costs, continuity

Items: L-05 (overhead counted twice), L-43 (unspecified money), IMP-02, IMP-03 (ART unit costs), IMP-04 / L-44 (cap
rule), IMP-11 (TB treatment costs), IMP-16 / L-14 (continuity). Rules of the batch: every value has a source with a
page or table or is a labelled assumption with a range; every input must measure what the model uses it for, or say
where it differs and carry a labelled adjustment; all costs in constant 2023 US$ through `health_model.inflate`
(CPI-U); no value chosen for its effect on results. Decisions that needed a judgement are marked **Decision** with
the reason. Phase 1 (this part) changes no model code.

Scripts (read-only with respect to the model; outputs beside this file):

| Item | Script | Output |
|---|---|---|
| B | `audit/batch34_gf_shares.py` | `batch34_gf_shares.csv` (210 country-disease lines) |
| D | `audit/batch34_art_costs.py` | `batch34_art_costs.csv` (70 countries) |
| E | `audit/batch34_tb_costs.py` | `batch34_tb_costs.csv` (70 countries) |
| F | `audit/batch34_donor_share.py` | `batch34_donor_share.csv` (70 countries x 4 diseases) |

Before snapshot of every displayed number: `audit/before_batch34.csv` (local, not committed; made with
`audit/snapshot_numbers.py` at commit `cd42746`, 357 tests passing).

## A. L-05: where overhead enters the money-to-people conversion

Baseline money (70 countries, US$M a year, 2021-23 average, `model_data/dah_lines.csv`) and what the current rule
(`health_model.effective`, `unit_costs`) does with it. `kappa` = `hss_kappa` = 0.5; `asd_share` = 0.45, so the
markup on site costs is 1 / (1 - 0.45) = 1.818.

| Disease | Treatment line money | Unspecified | Systems (HSS) | Testing & care | Effective treatment money = own + unspec x mix + kappa x HSS x mix + kappa x care pool | of which kappa x HSS | of which kappa x care |
|---|---|---|---|---|---|---|---|
| HIV | 1,594 | 819 | 1,078 | 760 | 2,808 | 239 (8.5%) | 605 (21.5%) |
| TB | 260 | 700 | 469 | - | 968 | 166 (17.2%) | - |
| Malaria | 365 | 511 | 465 | - | 660 | 93 (14.1%) | - |

Overhead enters in four places:

1. **Unit-cost markup.** ART and TB unit costs are site or provider costs x 1.818 (`unit_costs`): every dollar on the
   treatment line is assumed to carry 45% of above-site cost (management, M&E, supply chain; KFF 2025 on PEPFAR
   expenditure, logic review L-26). Malaria and immunization costs are already full programme costs (no markup).
2. **Systems money converted to services.** kappa x HSS money is added to every direct line by the country's mix
   and then divided by the marked-up unit cost. HSS money (IHME `*_hss_other`, `*_hss_hrh`, `*_hss_me`: supply
   chain, human resources, information systems) is the above-site money that the markup in (1) already prices into
   each patient. Counting it again as money that buys patients at the marked-up cost is the double count (L-05).
3. **Testing and care (HIV).** kappa x (care money + its share of unspecified and HSS) counts toward ART units at the
   marked-up ART cost. Testing and care is a service (diagnosis, retention, OI care), not overhead, so this is not
   the same double count; it is the concept question of L-27 (a flow of diagnoses, not a stock of patients), treated
   under IMP-02 below.
4. **Unspecified money.** Spread over services by mix, then converted at the marked-up cost (L-43, item B).

**Decision (L-05 fix): option (ii) of IMP-02.** Keep fully loaded unit costs (site cost x 1 / (1 - asd_share)) for
ART and TB, and stop converting systems money into service units: the kappa share of HSS money becomes 0 for every
disease, so HSS money is non-service money that is lost without a modelled service effect. Reason: IHME's treatment
program area is implementing-partner money that includes the partner's own management, so the markup belongs on it;
HSS money is a separate above-site purpose; converting both counts above-site money twice. Option (i) (site-level
costs plus kappa x HSS at site cost) would instead let a dollar of supply-chain money buy a patient-year of ARVs,
which is the wrong concept. `hss_kappa` keeps its role for testing-and-care money (point 3) and is relabelled in the
parameter file; a new parameter `hss_service_share` (central 0, assumption) holds the share of lost systems money
that still cuts services, so the old behaviour (0.5) is a sensitivity case rather than a deleted branch. It is held
constant in the draws (low = high = 0) rather than drawn over 0-0.25 as first tried: a one-sided range above a
central of 0 made every draw convert more systems money than the central run, which put the central run outside the
displayed 2.5-97.5% range in Kenya's malaria result under the Global Fund & Gavi preset (`audit/checks.py --quick`:
3 failures of `range_lo_le_central_le_hi`); the structural alternative is run by setting the parameter, like
`hiv_legacy_art_params`. With the constant, `--quick` then failed the same check in Kenya malaria under every preset
(15 rows): the quick harness used 50 draws, and the malaria parameters (`uc_mal_cm` 14 in 4-47, `uc_itn` 2.2 in
1.4-3.5, `mal_vc_eff` 0.55 in 0.40-0.61, `mal_cm_eff` 0.97 in 0.82-0.99) all have centrals near the end of their
range that gives more deaths, so in a 50-draw sample no draw exceeded the central once kappa's wide range (which had
supplied the upward variation) no longer applied to systems money. With the 400 draws the dashboard uses, Kenya's
malaria range is 5,906-18,311 around a central of 14,509 (passes); with 100 or 150 draws every bucket range in the
nine quick countries x all presets passes. The quick harness's draw count was raised from 50 to 100 (a harness
setting, not an invariant; the invariant and its tolerance are unchanged). Expected effect: -8.5% of effective HIV treatment money, -17% TB, -14%
malaria (table above), so about -5% to -8% of deaths (the red team measured kappa = 0 on everything at -20%).

## B. L-43: splitting unspecified money with Global Fund module shares

**Source.** Global Fund Data Explorer grant budgets by module (`datasets/GlobalFund/GF_budgets_2026-10-14.csv`,
Reference Rate US$, nominal), Grant Cycle 7 (2023-2025 budgets; one country-disease line falls back to GC6); 66 of
the 70 model countries have Global Fund grants (not Fiji, Iraq, Jordan; Libya is not a model country).
Cross-checks: Global Fund expenditure by module (`GF_expenditures_modules_2026-10-14.csv`, latest reported annual
expenditure, GC6-GC7) and WHO national TB programme budget lines (`datasets/WHO_TB/TB_budget_2026-10-14.csv`,
2025 budget). Module-to-category mapping and the allocation of programme-management and RSSH modules to diseases are
in the script header. "Payment for results" rows (results-based disbursement with no purpose tag: India, Rwanda,
Dominican Republic) are excluded from the shares.

**Shares used only as weights.** Nominal US$ are not deflated: only the within-grant shares are used.

**Median shares across the model countries (Global Fund budgets; expenditure cross-check in brackets):**

| Disease | Treatment | Prevention | Testing / case finding | RSSH | Programme management | Current rule: share of unspecified money reaching the treatment line |
|---|---|---|---|---|---|---|
| HIV | 0.345 (0.309) | 0.234 (0.214) | 0.061 (0.066) | 0.111 (0.081) | 0.216 (0.251) | 0.45 |
| TB | 0.486 (0.487) | 0.011 (0.004) | 0.213 (0.170) | 0.104 (0.070) | 0.171 (0.212) | 0.77 |
| Malaria | 0.218 (0.176) | 0.476 (0.445) | 0 | 0.139 (0.064) | 0.154 (0.209) | 0.40 |

Budget vs expenditure treatment share by country-disease: median absolute difference 0.062, 90th percentile 0.196
(n 170). TB: Global Fund treatment share (DS + DR diagnosis, treatment and care) vs WHO budget-line treatment share
(first- and second-line drugs, DS and DR programme costs, patient support): medians 0.479 vs 0.484 (n 68); the
country-level correlation is -0.05, so the two sources agree on the level and not on the ranking. WHO TB budgets are
the whole national programme (domestic and donor), the Global Fund share is one donor's grant mix; the Global Fund
value is used because it is a donor's mix, which is what unspecified donor money is.

**Gate B.** Shares sum to 1 (max |sum - 1| = 2e-16). Treatment share outside 0.05-0.95 in 6 of 210 lines, each with
a data reason: Bangladesh HIV 0.049, Dominican Republic HIV 0.034 (GC6), El Salvador HIV 0, Namibia HIV 0.033 (the
Global Fund HIV grant funds prevention and testing; treatment is domestically financed), Guyana malaria 1.0 (a
US$1.6M case-management-only grant), Liberia malaria 0.031 (vector control grant). They are used as they are.

**Fallback.** 38 of 210 lines (no Global Fund grant for that disease worth US$1M or more in GC7 or GC6): the median
of the model countries with data in the same WHO region (at least 3; EMR 10, AMR 9, AFR 8, WPR 7 lines), else the
median over all model countries (4 lines).

**How the split enters the model (item 2).** For each disease, unspecified money U is split: U x treatment share to
the treatment lines in proportion to their baseline mix (HIV: `hiv_art`; TB: `tb_ds`, `tb_dr`; malaria: `mal_cm`);
U x prevention share to the prevention lines by mix (HIV: `hiv_prev`, `hiv_pmtct`; malaria: `mal_itn`, `mal_irs`;
TB has no prevention line, so its 1% goes to non-service money); U x testing share to the testing-and-care pool
(HIV: `hiv_care_ct`, which converts at kappa; TB: treated the same way, kappa of it counting toward `tb_ds`, the
rest non-service; malaria: 0); U x RSSH share to systems money (non-service after item 1); U x programme-management
share to non-service money. `hiv_ovc` receives nothing (no Global Fund module). Only the treatment share becomes
people on treatment.

## C. IMP-02

IMP-02 has three parts. (a) Spread unspecified money over services and systems: done by item B, which gives each
purpose its own share instead of the mix of known service lines. (b) One treatment of above-site costs: item A,
option (ii). (c) Testing-and-care money as a flow of lost new initiations rather than a stock of people losing ART.

**Decision: (c) is BLOCKED.** UNAIDS AIDSinfo has "People initiating ART" (`datasets/UNAIDS_2026`), but the flow
formulation does not reduce the count as IMP-02 expected; it raises it. With the money and cost as they are, lost
initiations each year would equal today's kappa x care money / full ART cost (1.27M full-cost equivalents a year
across the 70 countries), and people who never start accumulate: 1.27M, 2.5M, 3.8M, 5.1M, 6.4M people off ART in
2026-2030 against today's constant 1.27M, i.e. about three times the person-years and deaths, bounded only by the
number of people not yet on ART (PLHIV x (1 - ART coverage)). No evidence was found on the cost of one new
initiation (testing plus linkage per person started; not in GHCC's ART extract) or on how long a missed diagnosis
delays treatment, both of which the flow model needs. Implementing it would change HIV deaths by a structural
amount set by two unsourced inputs, which the evidence standard of this batch does not allow. The current treatment
(kappa of testing-and-care money counts as lost ART, I-09) stays, labelled as a proxy in SPEC.md and on the Methods
page. Item 3 therefore makes no model change: its commit records this and marks IMP-02 partly done.

## D. ART cost per patient-year (IMP-03)

**Source.** GHCC Unit Cost Study Repository, HIV adult ART extract (`datasets/GHCC_UCSR/GHCC_UCSR_HIV_ART.xlsx`, 99
records, 12 countries, 2020 US$ per `datasets/MANIFEST.md`), pooled with the five Rosen et al. 2021 site costs
already in `unit_cost_reference.csv` (Malawi, Zambia, Lesotho, Uganda, Zimbabwe; 2018-2020 US$).

**Eligibility rules (set before the values were looked at).**
- Output unit per person per year ("Per Person Treated Per Year", "Per Patient Year", "Per Person Served Per Year",
  "Per Person Seen In Year On ART"; 67 of 99 records; the rest are per visit).
- Provider perspective (not patient).
- Above-service costs not included ("No Costs Included" or not stated); the 18 records with "Some Costs Included"
  are left out because the model adds its own above-site markup.
- A numeric mean unit cost.
- Price year 2015 or later ("Reported Currency Year", or the reference year where it is "."): ARV prices fell by
  about half between the 2010-2014 regimens and the dolutegravir regimens, so an older cost does not measure what a
  donor's treatment dollar buys today (concept match). 14 GHCC records in 5 countries pass; 49 records in 11
  countries pass every rule but recency (kept as the `site_cost_allyears` column for comparison).
- Financial vs economic: 98 of 99 GHCC ART records are economic. Financial is the central concept, so every economic
  value is multiplied by the financial / economic ratio measured in Value TB where both are costed at the same
  facility and intervention (bottom-up, 1,678 facility-interventions): **0.981** (a labelled adjustment from TB
  facility costing, not an ART measurement; the effect is 2%).
- Inflation: 2020 US$ x CPI-U 304.702 / 258.811 = 1.177 (`inflate`).

**Country values (site cost per patient-year, 2023 US$, financial):**

| Country | Records | Median | Range used (25th-75th pct, or +/-25% when n < 3) | Notes |
|---|---|---|---|---|
| Kenya | 1 | 354 | 266-443 | GHCC, national study, 2016 prices |
| Uganda | 3 | 371 | 278-383 | GHCC 2016 (two regions) and Rosen 2021 (185) |
| Malawi | 5 | 151 | 150-152 | GHCC 2016 trial arms and Rosen 2021 |
| Eswatini | 1 | 255 | 191-319 | GHCC, 2018 |
| Zimbabwe | 1 | 220 | 165-275 | Rosen 2021 |
| Lesotho | 1 | 148 | 111-185 | Rosen 2021 |
| Zambia | 1 | 141 | 106-176 | Rosen 2021 (the 10 GHCC records are 2014 prices: 335 when included) |
| South Africa | 6 | 687 | - | **outside the US$50-600 gate** (2015 trial costs 158-762): fallback used |

**Gate D.** Every own value except South Africa is inside US$50-600. South Africa uses the fallback and is listed.
Indonesia's records (1,161-1,700; 2010 prices) fail recency and would also fail the gate.

**Fallback** (63 countries): the median of the 7 model countries with a value in the same WHO region when there are
at least 3 (AFR: 220; 28 countries), else the median of those in the same World Bank income group (lower-middle
income 220, 19 countries; low income 4 countries), else the median of all 7 (220; 15 countries). Range for fallback
countries: the 25th-75th percentile of the country medians (150-305 in AFR).

**Comparison with the current model** (site cost before markup, 2023 US$): current median 156 (105-224; the
Rosen-based default of ARVs 95 + 23 x GDP scaling, 2018 US$); new median 220 (141-371); all-years variant 295. The
new values are higher because the GHCC economic costs include site overhead, clinical monitoring and in some studies
OI treatment and hospitalisation, while the Rosen conventional-care sites were chosen for low-cost delivery. The
model multiplies the site cost by 1.818, so the full cost per patient-year becomes 400 (Kenya 644, Uganda 674,
Malawi 274). An external consistency check that is reported and not used for selection: total HIV spending per
person on ART from Optima Table B2 (all purposes, all payers, nominal, GAM year) is Kenya 560, Uganda 423, Malawi
292, Zimbabwe 251, Mozambique 266, South Africa 303; a full treatment cost above a country's total HIV spending per
person on ART (Kenya, Uganda) means that the markup and the site cost cannot both be right there. This is recorded
for the reconciliation (Phase 3); the values are applied as the rules give them. `uc_art_mult` keeps its 0.75-1.3
range on top of the country range.

**Countries with their own value: 7 of 70** (Kenya, Uganda, Malawi, Eswatini, Zimbabwe, Lesotho, Zambia); South
Africa has studies but uses the fallback.

## E. TB treatment cost per course (IMP-11)

**Sources.** Value TB patient-level dataset (`datasets/ValueTB/ValueTB_pooled_patient.dta`, codebook
`ValueTB_codebook.docx`: unit cost per intervention = quantity of each service per patient episode x unit cost of
the service, plus drugs; `tcost_USD` is that total and equals the service totals plus `USD_tc_drugs` to within
US$0.001; 2018 US$; Ethiopia, Georgia, India, Kenya, Philippines; 19-24 facilities per country); the other GHCC
TB treatment studies (`GHCC_UCSR_TB.xlsx`, 2020 US$: Vassall et al. 2017 and Cox et al. 2015 for South Africa, Musa
et al. 2016 for Nigeria (intensive phase only, excluded), Trajman 2016 Brazil and Fitzpatrick 2015 China (not model
countries)); WHO TB data for the MDR/RR-TB share and enrolment and the budget cross-check.

**Course construction.** One course = intensive + continuation phase (+ the inpatient intensive phase where costed)
at the same facility and regimen. DS: first-line, new and relapse, adult pulmonary TB. DR: second-line, MDR-TB,
short regimen as central (9-11 months in the 2018 data; the current 6-month BPaLM regimen is cheaper still: the Stop
TB Global Drug Facility price of US$284 a course is cited in `improvements.md` and remains UNVERIFIED here), the long
regimen as the high end. Central = financial, bottom-up, median across facilities; range = the four variants
(financial / economic x bottom-up / top-down) and the 25th-75th percentile of facilities. Inflation 2018 x 1.213,
2020 x 1.177.

| Country | DS course (2023 US$) | DS range | DR short course | DR range (short variants to long) | Facilities |
|---|---|---|---|---|---|
| Ethiopia | 218 | 218-456 | 800 | 662-1,070 | 23 / 3 |
| India | 105 | 105-172 | - | - | 11 |
| Kenya | 150 | 150-173 | 2,818 | 2,818-12,125 | 19 / 3 |
| Philippines | 120 | 120-140 | 1,580 | 1,580-5,013 | 19 / 9 |
| South Africa | 274 | 221-327 | 9,256 | 8,082-10,430 | 2 studies / 2 |

**Gate E.** DS: all 5 inside US$100-3,000. DR: Ethiopia 800 is below US$1,000 (its second-line drug costs in the
data are US$100-400 a phase, which looks like donated drugs left out) and uses the fallback; Kenya, Philippines,
South Africa pass.

**Fallback** (65 countries for DS, 67 for DR): the median over the model countries with a value in the same World
Bank income group, pooled with the Laurence, Griffiths & Vassall 2015 income-group mean already in
`unit_cost_reference.csv` (one record), so that no group rests on one country: DS low income 275 (Ethiopia 218,
Laurence 332), lower-middle 135 (India, Kenya, Philippines, Laurence 351), upper-middle 678 (South Africa 274,
Laurence 1,081); DR low income 1,568 (Laurence only, Ethiopia excluded), lower-middle 2,818 (Kenya, Philippines,
Laurence 8,125), upper-middle 8,028 (South Africa, Laurence 6,800). Range for fallback countries: min-max of the
pool. The pre-markup current values are 332 / 351 / 1,081 (DS) and 1,568 / 8,125 / 6,800 (DR).

**MDR/RR share and enrolment** (WHO 2024, `MDR_RR_TB_burden_estimates`, `TB_burden_countries`, `TB_notifications`):
RR-TB incidence / all-forms incidence, median 0.021 (0.005-0.335; Tajikistan 0.24, Kyrgyzstan and Azerbaijan high),
replacing the global 0.04; RR patients started on treatment / RR incidence, median 0.35 (n 68; capped at 1),
replacing the global 0.45. Both become country inputs; countries without a value keep the old constants (listed in
the CSV).

**Cross-check against WHO budgets.** Blended full cost = ((1 - r) x DS + r x DR) x 1.818, with r = the RR share of
notified patients starting treatment, against the 2025 national TB programme budget per patient expected to start
treatment (`budget_tot / (tx_dstb + tx_mdr)`, nominal US$, whole programme including laboratories, staff and
prevention). n = 60 countries with data; **within a factor of 3 in 35 (58%)**, median ratio 1.98 (budgets above the
blended cost, as expected for a whole-programme budget). Gate E passes. Outside the factor: Kenya 4.6, Nigeria 3.7,
Tajikistan 7.2 (budget per patient US$5,207 with 24% RR), Kyrgyzstan, Moldova, Mongolia and other small programmes
with high fixed costs.

## F. Cap rule: external donor share (IMP-04 / L-44)

**What the cap does.** In the 160 country-service lines where baseline donor money / unit cost exceeds the people
covered, the current rule treats every covered person as donor-funded, so a 30% cut removes 30% of all patients
(red-team point 9; Tajikistan TB deaths 108% of current TB deaths). The new rule: donor-funded pool = min(people
covered x external donor share, donor money / unit cost), and units lost = that pool x share of donor money lost.
Where donor money buys less than the pool, this is unchanged (net loss / cost). The two branches join continuously.

**Sources** (`batch34_donor_share.csv`):

| Disease | Measure | Countries with a value | Median (IQR) | Fallback |
|---|---|---|---|---|
| HIV | WHO GHED: external funding on HIV/AIDS and STDs / spending on HIV/AIDS and STDs = EXT x dis11_ext_ext / 100 / dis11 (latest year 2016-2023) | 40 | 0.59 (0.37-0.76) | WHO-region median of the model countries with data (at least 3), else overall |
| TB | WHO TB financing: funding received from the Global Fund, USAID and other grants / total received, 2024 (`rcvd_tot_*`); 2025 expected funding from the budget file where 2024 is missing | 69 | 0.74 (0.36-0.94) | as above |
| Malaria | GHED dis13, as HIV | 38 | 0.25 (0.10-0.43) | as above |
| Immunization | GHED hc62_ext / hc62 (external funding on immunization programmes / spending on them) | 48 | 0.47 (0.08-0.87) | as above |

TB: the WHO financing share and GHED's dis12 external share correlate at 0.56 (n 41) and WHO is 0.28 higher at the
median (national TB programme budgets exclude the general health staff and facilities that GHED counts). WHO is
used for TB because its denominator is the programme the donor money funds.

**Concept.** A spending share is not the share of covered people whose service donors pay for (donors pay for
commodities for everyone in many countries, governments pay staff). It is the closest external measure available
and is applied with that label; the cap only binds where donor money would otherwise buy more than everyone
covered.

## G. Continuity (IMP-16 / L-14)

Evidence found (web search, 14 October 2026) on the share of services that continued after the 2025 US cuts:

| Source | Finding | What it says about continuity |
|---|---|---|
| Kates, Rouw & Nandakumar, KFF, "What We Know from the Latest PEPFAR Data: Analysis of FY 2025 Quarter 4 Results" (23 April 2026, updated 21 September 2026; PEPFAR Panorama Spotlight) | People on PEPFAR-supported ART "remained relatively stable" at 20.3M (FY2025 Q4) vs 20.4M (FY2024 Q4); newly enrolled on ART 389.1K vs 463.5K (-16%); people tested 19.6M vs 23.7M (-17%); new PrEP initiations 388K vs 659.4K (-41%); OVC served 1.7M vs 6.5M | Treatment stock held through a year in which US health aid fell by about two thirds (IHME); testing and initiations fell about a sixth; prevention fell far more |
| Kandpal & Webster, CGD, "PEPFAR's Stable Numbers are Hiding Lost Progress" (23 April 2026) | ART 20.6M, comparable to FY2024; about a third of countries saw a decline in PEPFAR-supported ART coverage; South Africa about -95,000, Zambia and Malawi over -40,000 each; testing 17.2M vs 21.9M; new diagnoses 307,000 vs 385,000 | Country-level treatment losses of a few percent where they occurred |
| Cust & Chabata 2026, *Lancet Global Health* (PIIS2214-109X(26)00223-8), "HIV service delivery following the PEPFAR and USAID HIV funding withdrawal in Uganda and Zimbabwe: an interrupted time-series study" | Four NGOs whose US funding was withdrawn, January 2023-March 2026, against 2024 averages: treatment -22% to -32%, testing -59% to -64%, PrEP -43% to -72%, prevention -37% to -63%; losses persisted through March 2026; the waiver did not restore treatment | Where the money was fully withdrawn, 68-78% of ART clients, 36-41% of testing and 28-57% of PrEP continued (drugs still supplied through public channels) |
| UNAIDS situation report, 17 March 2025 (`20250317-USstop-sitrep.pdf`) | In one high-burden East African country 46% of people living with HIV reported treatment disruptions and 23% received smaller ARV quantities | Partial, early-freeze disruption |
| WHO Global Tuberculosis Report 2025, "Impact of 2025 funding cuts" | 17 countries surveyed April-August 2025: TB treatment "the least affected, with only three countries reporting a moderate impact"; screening and community engagement severely or moderately disrupted in 11; diagnosis and sample transport in 8. Notifications: Uganda -14%, Zambia about -6% in the first half of 2025 vs 2024 | Treatment continued almost everywhere; case finding fell by a tenth to a seventh |
| aidsmap, July 2026 (AIDS 2026 conference) | 77,163 fewer children on PEPFAR-supported treatment in FY2025 (-14.2%) | Treatment losses concentrated in children and key populations |

None of these measures the model's case exactly: in 2025 the money was partly withdrawn (waivers kept ART
commodities and the Global Fund flowing) and the horizon is one year, while the model removes all of a donor's money
for five years. The observed continuity (ART 0.68-1.0, testing 0.36-0.41, TB treatment near 1, TB case finding
about 0.86) is therefore an upper bound for the model's parameter, which also covers prevention lines.

**Decision.** `continuity` central **0.30**, range **0.10-0.50**, status "sourced (indirect)": below every observed
treatment value because the model's scenario also removes the commodities, above the old 0.15 assumption because
every 2025 observation shows most treatment continuing without the lost money; the high end is the gate's 0.5. One
value for every line, as before (the TB private-sector notification variable (`priv_new_dx`) is not in the 2026 WHO
notifications file, so the per-country TB continuity of IMP-16 cannot be built; a per-line continuity is a
structural change outside this batch). Gate G passes (0 <= 0.30 <= 0.5).

## Gates summary

| Item | Gate | Result |
|---|---|---|
| All | citation with table/page or labelled assumption with range | met (sources above; the US$284 BPaLM price is quoted from `improvements.md` and marked UNVERIFIED, not used as an input) |
| B | shares sum to 1; treatment share 0.05-0.95 or stated reason | met; 6 lines outside with reasons |
| D | site cost US$50-600 | met after fallback (South Africa listed) |
| E | DS 100-3,000, DR 1,000-30,000; WHO cross-check within x3 for at least half | met (Ethiopia DR listed; 35 of 60 = 58%) |
| G | 0 <= continuity <= 0.5 | met (0.30) |
| C | evidence for the flow formulation | **BLOCKED** (no cost per initiation; the flow raises, not lowers, the count) |
