# Red-team review: aid-cut mortality dashboard (20 weakest points, most serious first)

**Reviewer stance.** I reviewed this as a skeptical WHO health economist would before publication. I used only README.md, views/4_Methods.py, the model specification (model_spec.md), model_params.csv, unit_cost_reference.csv, model_data/, the running pages (through Streamlit AppTest), and web sources. I read nothing under audit/.

**Headline numbers checked** (precomputed all-country files, no government response, sudden cut):

| Scenario | Aid lost per year | Extra deaths 2026-2030 | HIV | TB | Malaria | Immunization |
|---|---|---|---|---|---|---|
| Full US exit | $3.96B | 1.97M (1.34M-2.81M) | 1.01M | 460K | 386K | 117K |
| OECD 2025 | $3.24B | 1.78M | | | | |
| IHME 2025 | $2.89B | 1.49M | | | | |
| Global Fund & Gavi shortfalls | $1.02B | 683K | | | | |

**Countries rendered:** KEN, NGA, IND, ZAF, MOZ, HND, PAK and ETH, under several presets.

**My own runs.** I ran the model per line (Full US exit, all 70 countries) and some one-way sensitivities. The scripts and outputs are in this redteam/ folder: units_all.py, lines_fullus.csv and sens.py.

---

## 1. The HIV death parameter is calibrated to one count of patients and applied to another. HIV deaths and infections come out 3-4x below the benchmarks it was calibrated to, and the Validation page calls this agreement.

**What is wrong**
- `art_hazard_mult` means about 17% of people die within 5 years of losing ART (1.2 + 2.8 + 3.8 + 4.5 + 5.0%). That figure was set by dividing published death totals for full PEPFAR loss (Optima 0.8-2.9M, UNAIDS more than 4M) by **20.6M PEPFAR-supported patients** (model_params.csv, row `art_hazard_mult`).
- The model then applies it to **full-cost equivalents**: donor ART money ÷ $250-400 per patient-year. That gives only 7.78M donor-funded patients in total (Validation page: "Model: Donor-Funded People on ART 7.78M … PEPFAR: 20.60M"), and 5.30M people off ART under Full US exit (my per-line run).
- So the model cannot reproduce its own calibration target. 17% × 20.6M ≈ 3.5M deaths, but the model gives 1.01M HIV deaths for Full US exit.
- New infections show the same gap. `art_transmission` (0.04) was taken from "UNAIDS 6.6M and Optima 4.4-10.7M extra infections … for 20.6M people". Applied to 5.3M people it gives 1.55M infections over 5 years, against 6-10.75M in the benchmarks.
- The Validation table then lists "Optima … 0.8M to 2.9M | Full US Exit, HIV: 1.01M" as if the two agree. But Optima's 0.77M is its *24%-cut* scenario. The PEPFAR-discontinuation scenario is about 2.9M (Burnet/ten Brink: "770,000 and 2.9 million HIV-related deaths"; https://www.burnet.edu.au/knowledge-and-media/news-plus-updates/hiv-funding-cuts-could-lead-to-293-million-avoidable-deaths-by-2030-study). model_params.csv also mislabels both Optima figures as "estimates for full PEPFAR loss".

**Evidence**
- model_params.csv rows `art_hazard_mult` and `art_transmission`
- health_model.py:81 and :481
- Validation page caption: "It counts full-cost equivalents. PEPFAR counts everyone on ART at sites it supports … so its figure is larger by design."

**Effect on headline results:** HIV is half of all modelled deaths, and HIV deaths are probably understated by 2-3.5x relative to the stated benchmarks (about 1-2.5M missing under Full US exit). The only other way to read the parameter is that it is too high, if most "supported" patients would in fact keep ART. Either way the parameter has no consistent meaning.

**Ask the authors to:**
- Define one population, either patients who actually lose ART or full-cost equivalents.
- Calibrate the hazard on clinical data about ART interruption, separately from the macro-model totals.
- Estimate how many patients lose ART from which inputs donors buy (ARVs and commodities versus staff).
- Re-run the comparison with Optima's PEPFAR-discontinuation scenario specifically.

## 2. TB deaths rest on turning untagged and systems money into "patients left untreated". This gives about twice the published US-cut TB mortality, and impossible country results.

**What is wrong**
- Only 23% of baseline TB aid ($352M of $1,521M a year, dah_lines.csv) is tagged as treatment, diagnosis or DR-TB.
- The untagged 46% ($700M) is assigned *entirely* to tb_ds and tb_dr in proportion to the tagged mix, with none of it going to systems (spec §2). Half of the systems money ($469M) is added as well (κ = 0.5).
- That money is divided by Laurence 2015 provider cost per patient *treated*, marked up 1/(1 − 0.45). The markup comes from a PEPFAR HIV ratio (it gives $638 per patient in lower-middle-income countries).
- Each "unit" is then assumed to be a case left completely untreated, at ΔCFR of about 0.40, plus secondary cases.
- Much donor TB money pays for case finding, laboratory networks and technical assistance, where the cost per extra case detected is far higher than the cost of treating one.

**Evidence**
- Full US exit gives **460K TB deaths in 2026-2030**. Clark et al. (Lancet Global Health 2025, 79 countries) estimate **537,700 excess TB deaths by 2035** from USAID termination (https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12045416/). That is about 49K a year, against the model's 92K a year.
- Country rows (all_countries_Full_US_exit.csv vs country_inputs `tb_deaths_total`):

| Country | Extra TB deaths per year | Share of all current TB deaths |
|---|---|---|
| Mozambique | 14.2K | 73% |
| Tajikistan | 970 | **108%** |
| Cambodia | — | 55% |

- The Kenya dashboard card reads: "TB … About $3K of aid lost per life lost".
- The Validation page gives no TB benchmark at all.

**Effect on headline results:** TB deaths are probably overstated by about 1.5-2.5x, roughly 150-300K of the Full US exit total. TB is the largest bucket in the Global Fund & Gavi preset (313K of 683K) and in the IHME preset (557K of 1.49M), so those headlines move most.

**Ask the authors to:**
- Allocate untagged TB money with the systems/programme share, not 100% to treatment.
- Use a cost per extra case *detected* for diagnosis and case-finding money.
- Drop the PEPFAR markup for TB, or source a TB-specific one.
- Cap extra TB deaths at a plausible share of current TB mortality.
- Add Clark et al. and Mandal et al. (PLOS Global Public Health 2025) to the Validation page.

## 3. Above-service costs are counted twice: in the unit cost, and again by turning systems, testing and care money into extra patients.

**What is wrong**
- Unit costs for ART and TB are divided by (1 − `asd_share`) = 0.55. This adds the 45% that PEPFAR spends above the point of service: management, M&E, supply chain and laboratory systems (health_model.py:390).
- Separately, κ = 50% of IHME-tagged systems money (`hiv_hss`, `tb_hss`, `mal_hss`) and of HIV testing & care money is converted into lost services at that same marked-up cost (spec §2; health_model.py:660, :739). Testing & care is $760M a year, 41% of former treatment money.
- The systems money *is* the above-service spending. Each of these choices alone is defensible, but together they count the same dollars as both overhead and patients.
- Testing and care money also funds diagnosis and *new* enrolment (a flow), yet it is converted into a *stock* of people losing ART at once.
- κ is labelled "Assumption" with a 0.25-0.9 range. `asd_share` comes from a single 2014 PEPFAR analysis and is applied to TB and to every donor.

**Evidence:** my sensitivity runs (sens.py, Full US exit, all countries):

| Change | Total deaths | HIV | TB |
|---|---|---|---|
| Base | 1.97M | 1.01M | 460K |
| κ = 0 | 1.57M (−20%) | 783K | 338K |
| `asd_share` = 0 | 2.88M (+46%) | | |

**Effect on headline results:** about 400K of the 1.97M deaths (20%) come from an assumption that systems money buys patients, while the unit cost has already charged for the same systems. The direction is double counting toward more deaths, but its size depends on fixing point 1.

**Ask the authors to:**
- Use either a site-level unit cost plus κ-converted systems money, or a fully loaded cost with no κ conversion, not both.
- Model testing & care loss as fewer new initiations (a flow).
- Show the κ and `asd_share` sensitivities on the page.

## 4. Wrong counterfactual and timing: cuts that began in 2025 are modelled as starting in 2026, from a 2021-23 aid baseline.

**What is wrong**
- Baseline aid is the 2021-23 average, but coverage is 2024-25 and deaths are 2024 (Methods "Data Years").
- The US stop-work orders and USAID closure, the OECD-measured falls, and IHME's 2025 preliminary changes all happened in **2025**. The presets nevertheless apply them as a sudden cut in 2026, with ART hazard year 1 = 2026 (1.2%) and TB, net and vaccine ramp-ups restarting in 2026.
- So:
  - 2025 deaths are excluded;
  - people who lost ART in 2025 are put in the low-hazard year-1 band in 2026;
  - aid changes between 2023 and 2025 (Gavi and Global Fund cycle effects, earlier US/UK cuts) are invisible.
- The IHME 2025 preset is explicitly "IHME 2025 / 2021-23" but its deaths are counted over 2026-2030 (spec §1).
- Methods admits: "A 2025 baseline … would reflect aid already lost after 2023; this is planned as a future option."

**Evidence**
- views/4_Methods.py "Data Years" table and Limitations bullet "Post-2023 aid is not observed by recipient"
- The dashboard kicker: "Inputs: aid 2021-23 average; coverage 2024-25 … applied to 2026-2030 without projection."

**Effect on headline results:** the direction is mixed. Late ramp-up understates deaths inside 2026-2030 for cuts that really began in 2025 (HIV year-1 hazard 1.2% vs year-2 2.8%). Using a 2021-23 baseline overstates "aid at risk" where aid had already fallen or moved by 2025. Either way, the "2026-2030" label does not describe the period the deaths belong to.

**Ask the authors to:**
- Set t = 1 at 2025 for scenarios that represent 2025 events, and report 2025-2030.
- Or rebase the cuts on IHME's 2025 preliminary levels and model only *further* cuts from 2026.

## 5. The OECD preset applies each donor's 2025-vs-2024 cut in *total* ODA to *health* aid measured in 2021-23.

**What is wrong**
- `OECD_2025 = {"United States": 0.57, "Germany": 0.174, …}` (scenarios.py:19). These are changes in total ODA from 2024 to 2025, including humanitarian, refugee and in-donor costs.
- They are applied identically to bilateral and multilateral *health* aid for HIV, TB, malaria and immunization, against a 2021-23 baseline.
- Donors' health aid did not move by the same share as their total ODA. Germany's and the UK's falls in total ODA were driven largely by in-donor refugee costs and bilateral budget lines; US global health saw PEPFAR bridge and MOU funding continue while USAID's other sectors were cut.

**Evidence**
- OECD press release, April 2026: "United States … aid fell 56.9% … Germany 17.4% … France 10.9% … United Kingdom 10.8%" (https://www.oecd.org/en/about/news/press-releases/2026/04/international-aid-fell-sharply-in-2025-says-oecd.html).
- The Methods table admits: "Each donor's 2025 change in total aid applied to its health aid".

**Effect on headline results:** the size and direction of the 1.78M headline are unknown. The preset is presented as "OECD-reported" data, but it is a modelling assumption.

**Ask the authors to:**
- Use OECD CRS health-sector (purpose code 12xxx/13040) changes, or IHME's own 2025 donor x disease ratios.
- Rename the preset "Total-ODA cut applied proportionally" and state the assumption in the headline.

## 6. The "America First MOUs" preset leaves out the defining feature of the MOUs: binding domestic co-financing.

**What is wrong**
- The MOUs are five-year transition plans: US money falls *and* the partner pledges rising domestic health spending, with penalties in some cases.
- Examples: Kenya pledged +$850M over 5 years, and Ethiopia, Kenya, Mozambique, Cameroon and Malawi lose $1 for each $1 of co-financing shortfall.
- The preset models only the US decline, with the default of no government replacement.
- MOU amounts are nominal while the baseline is constant 2023 US$, so real cuts are understated (by about 2-3% a year of inflation, compounding to about 10% by 2030).
- The US money now flows government-to-government instead of through NGOs, but the preset treats it with the same per-dollar effect as before.

**Evidence**
- Methods table row "America First MOUs"
- Dashboard caption (ETH): "US bilateral aid cut: 23% (2026), 7%, 8%, 30%, 49% (2030) … MOU amounts (nominal US$, as written in the MOU)"
- KFF tracker: "each partner pledges to raise domestic health spending as U.S. assistance falls" (https://www.kff.org/global-health-policy/kff-tracker-america-first-mou-bilateral-global-health-agreements/)
- The EastAfrican on Kenya's $850M pledge (https://www.theeastafrican.co.ke/tea/sustainability/health/us-signs-pact-with-kenya-under-america-first-health-plan-5287210)

**Effect on headline results:** the MOU headline (360K deaths, 16 countries) is overstated wherever co-financing is delivered. In Kenya, $850M over 5 years ($170M a year) is larger than the whole MOU-implied loss.

**Ask the authors to:**
- Pre-load each MOU's co-financing schedule as the default government response, with a compliance slider.
- Deflate nominal MOU amounts.

## 7. The default of no government replacement, and the headline sentence "historically governments have not replaced falling aid", go beyond the evidence.

**What is wrong**
- Every headline uses no replacement, justified by a two-way fixed-effects regression with θ = −0.19, 95% CI −0.45 to +0.07, and within-R² 0.033 (regressions.json `fiscal_replacement`, 97 countries, 2002-2023).
- That regression is identified from small, mostly gradual year-to-year aid changes. It is out of sample for a 50-100% abrupt exit, and its CI includes modest replacement.
- 2025 offers direct evidence of partial replacement: South Africa's emergency HIV allocation, Nigeria's supplementary health budget, and the MOU co-financing pledges.
- The headline dek asserts the regression result as fact on every country page.

**Evidence**
- Dashboard (KEN): "About $278 million a year would be lost, and historically governments have not replaced falling aid."
- Methods: "governments did not, on average, replace falling aid."

**Effect on headline results:** all headlines are a worst case for domestic response. Even 10-20% replacement, inside the CI's mirror image and seen in 2025, would remove about 10-20% of deaths, more where lives-first allocation is used.

**Ask the authors to:**
- Label the headline "if no one replaces the money".
- Show a second number with a plausible response, for example the MOU pledges or the θ upper bound.
- Drop the causal wording, and test the regression on large-shock episodes only.

## 8. The 95% ranges cover only parameter noise. They leave out the structural choices that move results most, and are presented as if complete.

**What is wrong**
- Ranges are the 2.5-97.5 percentiles of 400 independent triangular draws. No data input, scenario value or model structure is varied (spec §6).
- The structural choices matter far more than the drawn ranges:

| Choice or comparison | Effect |
|---|---|
| `asd_share` = 0 | +46% |
| HIV death benchmarks (point 1) | 3-4x |
| The page's own three methods (Validation, Kenya) | Poisson malaria = 0.1x the model; Lancet rate ratios HIV = 2.5x; under-5 Poisson has the wrong sign |

- Every country uses the same seed and draws, and all-country ranges add country percentiles.
- Headlines show the central run, not the median.

**Evidence**
- Dashboard (KEN): "126K Extra Deaths, 2026-2030 range 83K to 187K".
- Validation: "the Poisson regression for malaria is 0.1x the model (lower); the Lancet rate-ratio estimate for HIV is 2.5x the model (higher)".

**Effect on headline results:** the stated ±40% band understates real uncertainty, which is at least a factor of 2-3 around the HIV and TB components.

**Ask the authors to:**
- Add scenario- and structure-level uncertainty, at least κ, `asd_share`, the unit-cost concept, and calibration denominator A vs B.
- Or relabel the band "parameter uncertainty only" in every headline and pill.

## 9. The "donor money exceeds cost" rule assumes everyone covered is donor-funded. It affects 160 lines in 65 countries.

**What is wrong**
- Where baseline donor aid ÷ unit cost exceeds the people covered, people losing the service = covered × (aid lost ÷ donor aid) (spec §4, `_units_lost`).
- This implicitly assumes donors fund 100% of covered people, so a 30% donor cut removes 30% of *all* patients, including those the government treats.
- The Validation caption says the excess "pays for things other than the service", which contradicts scaling the loss over all covered people.

**Evidence**
- Validation page: "Country-Service Lines Affected 160 of 695 modelled; Countries With At Least One 65 of 71".
- Examples in my run:

| Country, line | Donor money would buy | People covered |
|---|---|---|
| Zimbabwe, TB (tb_ds) | 129,224 patients | 20,400 |
| Tajikistan, TB (tb_ds) | — | all 4,424 treated as donor-funded |
| Honduras, ART | 14,656 patients | 14,820 |

- These lines produce 133K deaths under Full US exit (7%). They drive the Tajikistan TB result of 108% of current TB deaths.

**Effect on headline results:** more deaths in these lines, roughly 50-100K overstated under Full US exit.

**Ask the authors to:**
- Cap the donor-funded share at an external estimate (NHA/GHED donor share of disease spending, or Global Fund/PEPFAR commodity shares).
- At the least, cap it below 100% of covered people.

## 10. Immunization: the cost, the effect and the coverage measure each describe a different intervention.

**What is wrong**
- **Cost.** `uc_imm` = $87 is the *full* cost of a fully immunized child: delivery $45.6 plus vaccines. Donor (mostly Gavi) money pays largely for vaccines, especially new ones (PCV, rotavirus, HPV, malaria, measles-rubella). The authors' own check shows "donor vaccine aid per immunized child has a median of $40". Gavi's own projection, 75M children for about $1.58B, is about $21 a child. So the model understates children affected by about 2-4x.
- **Effect.** Deaths per child is Gavi's *all-antigen lifetime* figure (20.6M ÷ 1.2B, accumulated 2000-2024 at higher mortality), but it is re-referenced to U5MR = 50. The births-weighted U5MR of the dashboard countries is 48, so today's figure comes out at 0.019 against Gavi's historical 0.017, when lower mortality should push it down.
- **Coverage.** The coverage drop is shown on DTP3, which most countries finance themselves. The child who loses Gavi money loses PCV and rotavirus, not the whole schedule.
- **Circular validation.** The Validation row "Gavi … About 0.017 | 0.019 per child" compares the model with the source it was calibrated from.

**Evidence**
- model_params.csv `uc_imm` and `imm_deaths_per_child_ref`
- health_model.py:471
- Gavi's projection for a US withdrawal: "75 million children … more than 1.2 million" deaths (https://www.developmentaid.org/news-stream/post/193780/us-slashing-gavi-vaccine-funding), against the model's 117K for Full US exit.

**Effect on headline results:** probably understated overall: fewer children, partly offset by too many deaths per child. Gavi's own claim is 10x the model's. The IHME preset gives only 18K immunization deaths.

**Ask the authors to:**
- Model loss of specific Gavi-funded antigens, using VIMC deaths averted per vaccinated child by antigen and country, and the Gavi price per dose.
- Show coverage for those antigens, not DTP3.

## 11. The hero figure "People Losing Care Each Year" adds bednet person-years, malaria cases and ART patient-years as if they were people.

**What is wrong**
- The hero sums every service line except prevention and OVC (model_section.py:596).
- In Kenya: "6.10M People Losing Care Each Year — 4.90M bednet users · 466K malaria patients · 452K on HIV treatment". So 80% of the headline is $2.20-per-person-year net use.
- South Africa, which has about 10 malaria deaths a year, shows "52K bednet users · 13K people under indoor spraying".
- Each "person" is in fact a full-cost equivalent or person-year (the Validation caption concedes "It counts full-cost equivalents").
- A malaria case treated is an episode, not a person; one person can have several.

**Effect on headline results:** no effect on deaths, but the second-largest number on every page is dominated by the cheapest commodity and is not a count of people.

**Ask the authors to:**
- Drop the summed hero, or replace it with "people losing HIV treatment" plus "TB patients untreated".
- Label units honestly (person-years of net use, treatment episodes).

## 12. Malaria: child effect sizes are applied to all-age deaths, and two growth multipliers compound.

**What is wrong**
- E_v = 0.55 (Eisele et al. 2010) and E_c = 0.82 (Thwing et al. 2011) are Lives Saved Tool effects estimated for *children 1-59 months*. They are applied to all-age WHO malaria deaths D0 (Methods: "D₀ = all-age malaria deaths").
- Lost vector-control deaths are then multiplied by (1 + 0.10)^years (an assumption labelled "Assumption on size"). That is on top of the baseline trend from MAP *P. falciparum* cases, clipped at ±5% a year, and 10 countries sit at +5% (Ethiopia, Madagascar, Zambia …).
- By year 5 the factor on lost vector-control deaths is 1.10⁴ × 1.05⁴ ≈ 1.78.
- The trend is fitted on *cases*. Using it for *deaths* assumes the case fatality rate is constant.

**Evidence**
- views/4_Methods.py, "Malaria" and "Already-changing death rates" sections
- model_params.csv `mal_resurgence`
- health_model.py:865

**Effect on headline results:** more deaths. Probably 15-30% too many malaria deaths in high-trend countries (Full US exit malaria total 386K).

**Ask the authors to:**
- Apply the LiST effects to under-5 deaths, with a reduced adult effect.
- Choose either the resurgence term or the case trend for the post-cut dynamic, not both.
- Benchmark against a published malaria funding-cut model (e.g. Malaria Atlas Project / Imperial projections for PMI loss).

## 13. TB secondary transmission comes too early and too large.

**What is wrong**
- 0.4 secondary active cases per untreated patient are assumed, all arriving 1-2 years later.
- Vynnycky & Fine put most of the 5-10% disease risk over 2-5 years, plus later reactivation.
- In high-burden settings many contacts are already infected, and prior infection partly protects against new disease.
- Untreated index cases also die (43-62%) and stop transmitting.
- The parameter text calls itself "conservative", but timing and the uninfected-contact assumption push the other way within 2030.

**Evidence**
- model_params.csv `tb_secondary`
- health_model.py:846
- My run with `tb_secondary` = 0 gives TB deaths of 411K instead of 460K.

**Effect on headline results:** about 49K deaths (2.5%) under Full US exit. More important is the "conservative" framing, which a reviewer will contest.

**Ask the authors to:**
- Spread arrival over 5 years with a published time-from-infection distribution.
- Reduce the risk for already-infected contacts.
- Count transmission over a realistic infectious period weighted by survival.

## 14. Bednet use defaults to 50% where surveys show 4-31%. Survey values before 2015 are discarded.

**What is wrong**
- Where MAP has no ITN estimate and the survey is older than 2015, use is set to 50% (`mal_itn_default_use`).
- Validation table: "Indonesia 4% (2007) → 50% (assumed)", "Namibia 6% (2013) → 50% (assumed)", "Botswana 31% (2012) → 50% (assumed)". South Africa, Philippines, Bangladesh, Venezuela and Bolivia are also at 50%.
- 31 of 70 countries are on the default ("MAP 31 · default 31 · survey 8").
- 50% inflates the people who can lose nets, the hero counts (South Africa 52K, India 410K bednet users) and the LiST baseline.

**Evidence:** Validation page, "Malaria Inputs" table; health_model.py:554 and :760.

**Effect on headline results:** small on deaths (these are low-burden countries), but a visible credibility problem.

**Ask the authors to:**
- Use the latest survey of any year with a decay, or the WHO World Malaria Report modelled ITN use.
- Set use to 0 or "not modelled" where vector control is not a national strategy.

## 15. "Full US exit" is neither full nor realistic, and in MOU countries it contradicts the MOU preset.

**What is wrong**
- The headline says "If U.S. health aid ends", but the preset keeps 77% of the US Global Fund pledge (scenarios.py:18).
- It ignores signed MOUs: Kenya shows the "MOU Signed" pill alongside the headline "If U.S. health aid ends, Kenya could see about 126,000 more deaths". Under the MOU schedule, US money continues through 2030.
- No preset represents the actual 2026 policy mix of US bilateral funding: MOU transition, PEPFAR bridge, Gavi exit and the Global Fund pledge together.

**Evidence:** dashboard header and headline for KEN; Methods presets table.

**Effect on headline results:** the 1.97M figure will be quoted as "the" US-cut toll, although it is an extreme counterfactual.

**Ask the authors to:**
- Rename it "Hypothetical: all US bilateral aid ends".
- Make a "current US policy" preset the default for MOU countries.

## 16. Fiscal space is a one-year "strong-year surge" held flat for five years.

**What is wrong**
- capacity = GHES_2023 × (p75 growth − median growth) × debt stress (health_model.py:269-301).
- This is the extra growth of one good year, and it is applied as the same replacement ceiling in every year 2026-2030 instead of building up cumulatively.
- The debt-stress factor's thresholds (10% and 40% of revenue, floor 0.25) are unsourced.
- It is not linked to the MOU co-financing pledges or to the Abuja-share logic used elsewhere on the same page (the budget-increase sliders use health's share of spending, a different definition of fiscal space).

**Evidence:** dashboard (KEN): "In a strong year the health budget could add about $21 million/yr … (fiscal space)", against a $278M a year loss.

**Effect on headline results:** no effect on default headlines, but the "Can Kenya Fill the Gap?" panel understates what governments can do by year 5.

**Ask the authors to:**
- Make capacity cumulative.
- Source the stress thresholds (IMF debt-sustainability analysis interest-to-revenue norms).
- Use one fiscal-space concept throughout.

## 17. The "IHME 2025 preliminary" preset applies one global ratio to every country but is presented as "data-driven".

**What is wrong**
- IHME's 2025 figures have no recipient split. The preset applies each source × channel × disease global ratio to every country (cells under $20M use source × disease), clipped to 0-1.5.
- Real 2025 cuts were highly country-specific: USAID program terminations and the Global Fund's GC7 reprioritisation differed by country.
- The scenario description says "Data-driven", but the country distribution is an assumption.
- It produces 1.49M deaths, including 557K TB deaths (see point 2).

**Evidence:** scenarios.py PRESETS text: "Data-driven: applies IHME's own 2025 preliminary DAH estimates … (IHME has no recipient-level split after 2023, so the global change is applied …)".

**Effect on headline results:** the country rankings and the All Countries map are unreliable for this preset. The direction of the total is unknown.

**Ask the authors to:**
- Drop "data-driven".
- Show country results only as "if the global change applied uniformly".
- Where available, use country-level 2025 data (Global Fund allocation letters, PEPFAR country operational plan cuts, KFF).

## 18. The Validation page is framed to pass, and its HIV baseline is wrong.

**What is wrong**
- The caption pre-empts any test: "The published studies cover more causes, sectors or years than the model, so the model should come in below most of these figures" (views/3_Validation.py:102).
- With that framing, a model 3-4x below the comparable HIV studies (point 1) looks validated.
- There are no TB (Clark/Mandal), malaria or SA-specific benchmarks. For South Africa, the Thembisa model estimates 56-65K extra AIDS deaths in 2025-2028 if PEPFAR ends (https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12262123/), against the model's 122K HIV deaths for 2026-2030.
- The Gavi check is circular (point 10).
- The Lancet rate-ratio comparison uses `hiv_deaths_est` = IHME's 2019 HIV share × crude death rate × population (prepare_model.py:442). That gives Honduras 85 HIV deaths a year and São Tomé 0.4, while CDC/UNAIDS show Honduras with "<500" adult AIDS deaths (2022).
- On this baseline the model's Honduras HIV deaths are 3x total current HIV deaths, and São Tomé's 18x.

**Effect on headline results:** no direct effect on the totals, but this is the page a WHO reviewer will read first, and it currently gives false comfort.

**Ask the authors to:**
- Compare like with like: same scenario, horizon and country set.
- Report the ratio of model to benchmark with a pre-stated acceptance band.
- Use UNAIDS AIDS-related deaths for the HIV baseline.

## 19. Post-2030 deaths assume funding returns in 2031, which caps "committed deaths".

**What is wrong**
- "Further deaths 2031-2035" assume funding is fully restored in 2031, with 50% of people off ART re-engaging each year (`art_reengage`, an assumption).
- HIV infection deaths are counted only to 2035. With Weibull median survival of 10.5 years, most deaths from the 1.55M modelled infections fall after 2035.
- The headline shows only 2026-2030.

**Evidence:** Methods "Committed deaths" section; Further Deaths pill (KEN: "+37K more in 2031-2035").

**Effect on headline results:** long-run deaths are understated, most for HIV. A lifetime horizon would add hundreds of thousands of deaths under Full US exit.

**Ask the authors to:**
- Report a lifetime (or 2026-2040) committed-death figure with discounting, or say plainly that most HIV deaths from new infections are excluded.
- Make funding restoration in 2031 a scenario choice.

## 20. Drug-resistant TB inputs are fixed, global and inconsistent.

**What is wrong**
- DR-TB is set at 4% of incidence with 45% coverage everywhere (health_model.py constants `DR_TB_SHARE`, `DR_TB_COV`).
- In Central Asia, MDR/RR-TB is a much larger share of TB (WHO Global TB Report: well above 10% of new cases and over 25% of previously treated cases in Tajikistan, Kyrgyzstan and Azerbaijan).
- Costs come from single studies in Laurence 2015 and are not monotone: lower-middle income $8,125 > upper-middle income $6,800 > low income $1,568 (unit_cost_reference.csv). They then get the PEPFAR 1/(1 − 0.45) markup, giving $14,773 per patient in lower-middle-income countries.
- These costs predate the cheaper BPaLM regimen.
- `tb_dr_dcfr` = 0.45 is an assumption.

**Effect on headline results:** small globally (13K deaths under Full US exit), but wrong in the Central Asian countries, where the model's TB results are already outliers (Tajikistan, Kyrgyzstan).

**Ask the authors to:**
- Use WHO country estimates of RR-TB incidence and treatment enrolment.
- Use Global Drug Facility BPaLM prices with WHO-CHOICE delivery costs.
- Drop the PEPFAR markup for TB.

---

### Summary of likely net direction

| Component | Likely error | Points |
|---|---|---|
| HIV deaths and infections | Understated 2-4x against the stated benchmarks | 1 |
| TB deaths | Overstated about 1.5-2.5x | 2, 9, 13 |
| Systems/care money conversion | Inflates all buckets by about 20% | 3 |
| Malaria | Modestly overstated | 12, 14 |
| Immunization | Probably understated | 10 |
| MOU preset and default no-response headlines | Overstated | 6, 7 |

The overall Full US exit total of 1.97M is therefore not reliably high or low: a large HIV error partly offsets a large TB error. The headline's agreement with the benchmarks is partly coincidental, and the per-disease split, which drives the "most would come from…" sentences, is the least reliable output.

### Sources used
- ten Brink et al. 2025, Lancet HIV (Optima), via Burnet Institute: https://www.burnet.edu.au/knowledge-and-media/news-plus-updates/hiv-funding-cuts-could-lead-to-293-million-avoidable-deaths-by-2030-study
- Clark et al. 2025, Lancet Global Health (TB, USAID termination): https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12045416/
- Mandal et al. 2025, PLOS Global Public Health (via EATG): https://www.eatg.org/hiv-news/cuts-to-us-foreign-aid-could-drive-millions-of-new-tb-cases-and-deaths-finds-new-study/
- Thembisa, South Africa PEPFAR cessation: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12262123/
- Gavi projection of US withdrawal: https://www.developmentaid.org/news-stream/post/193780/us-slashing-gavi-vaccine-funding
- OECD preliminary 2025 ODA: https://www.oecd.org/en/about/news/press-releases/2026/04/international-aid-fell-sharply-in-2025-says-oecd.html
- KFF MOU tracker: https://www.kff.org/global-health-policy/kff-tracker-america-first-mou-bilateral-global-health-agreements/
- Kenya MOU co-financing: https://www.theeastafrican.co.ke/tea/sustainability/health/us-signs-pact-with-kenya-under-america-first-health-plan-5287210
- CDC Honduras profile (AIDS deaths <500): https://espanol.cdc.gov/globalhivtb/where-we-work/Honduras.pdf
