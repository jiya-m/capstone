# URGENT: Critical findings (logic and evidence review)

Each item meets the Part 10 "Critical" definition. The full analysis is in `findings.md` and `logic.md`.

## L-01. ART death risk is calibrated per PEPFAR-supported patient but applied to full-cost-equivalent patients

**Severity:** Critical (wrong concept for the largest input: HIV treatment is 47% of all modelled deaths). Under any
internally consistent reading, the headline changes by more than 10%.
**Confidence:** High that the two concepts differ (code and parameter file); Medium on the size of the effect.

### What the code does

1. **People losing ART are full-cost equivalents.** People losing ART = net ART money lost / full cost per
   patient-year x (1 - continuity), capped at people on ART outside PMTCT (`health_model.py:438-450`, `:783-796`).
   - This counts how many patients the lost money would fully pay for. It is not the number of patients whose care
     is touched.
   - Full US Exit, all 70 countries: **5.30 million** a year.
   - Donor money as a whole pays for **7.78 million** (Validation page), out of **24.71 million** people on ART in
     the dashboard countries.
2. **Each of them gets the ART hazard ramp** 1.2%, 2.8%, 3.8%, 4.5%, 5.0% a year x `art_hazard_mult`
   (`health_model.py:81`, `:856-858`): **17.5%** cumulative deaths over 5 years. Measured: 929,704 ART deaths / 5.30M
   people = 0.175.
3. **The hazard was calibrated on a different population.** `model_params.csv`, `art_hazard_mult`, source column:
   > "Calibrated: 5-yr cumulative ~17% of people losing PEPFAR-supported ART sits between Optima (0.8-2.9M deaths)
   > and UNAIDS Goals (4.2M deaths) ... estimates for full PEPFAR loss, 2025-29, against 20.6M people on
   > PEPFAR-supported ART"

   - That is, 17% x 20.6M = 3.5M deaths: the calibration treats **all 20.6 million** people at PEPFAR-supported sites
     as at risk.
   - The model applies the same per-person risk to **5.3 million** full-cost equivalents.
   - So the calibration's own target (3.5M) cannot be reached. Full US Exit gives **1.01M** HIV deaths, at the bottom
     of the Optima range, not "between Optima and UNAIDS" as the parameter file says.

### Why the two concepts are not interchangeable

- **17% is an average risk per supported patient**, most of whom keep some care. A person who actually stops ART
  faces a much higher risk.
  - Brinkhof, Pujades-Rodriguez & Egger 2009, *PLoS ONE* 4(6):e5790 (systematic review of patients lost to
    follow-up in ART programmes): "The combined mortality was 40%" (95% CI 33-48%); "among those traced 20% to 60%
    had died". https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0005790
- **A full-cost equivalent is not a person who stops treatment.** If support is withdrawn thinly (staff, labs,
  outreach) across all 20.6M supported patients, more people are affected, each with a smaller risk.

### Consistent alternatives (tested by arithmetic on the model's own outputs, Full US Exit, no response)

| Reading | People at risk | 5-year risk | ART deaths 2026-30 | Change in all-cause headline (1.97M) |
|---|---|---|---|---|
| As implemented (mixed) | 5.30M full-cost equivalents | 17.5% | 0.93M | (as is) |
| A. Full-cost equivalents who actually stop ART, risk from Brinkhof et al. (20-60% among traced; combined 40%) | 5.30M | 20-60% | 1.06-3.19M | +7% to +115% (central 40%: +2.12M, +61%) |
| B. Loss spread across everyone at donor-supported sites, calibrated average risk | up to 20.6M (PEPFAR, 55 countries; fewer in the 70 dashboard countries) | 17% | up to ~3.5M | up to +130% |

- **Benchmarks.** Optima HIV, ten Brink et al. 2025, *Lancet HIV* (DOI 10.1016/S2352-3018(25)00074-8): 0.77-2.93
  million extra HIV deaths 2025-2030. UNAIDS (July 2025): "more than 4 million" AIDS-related deaths by 2029 if US
  funding is not replaced.
- The current 1.01M lies inside the Optima range only because the two inconsistencies partly cancel.

### Context that cuts the other way

PEPFAR FY2025 Q4 results: "the number of people on antiretroviral therapy was stable compared to Quarter 4 of FY 2024"
(KFF PEPFAR fact sheet, https://www.kff.org/global-health-policy/fact-sheet/the-u-s-presidents-emergency-plan-for-aids-relief-pepfar/).
So far, actual ART interruptions after the 2025 cuts have been far smaller than a full-exit scenario implies. This
bears on the scenario's realism, not on the internal consistency above.

### Proposed fix (not implemented)

Pick one reading and calibrate to it:
- **(A)** Keep full-cost equivalents; replace the hazard with mortality among people who stop ART (Brinkhof 2009;
  newer LTFU cohorts; ART-interruption trials) and re-check against Optima and UNAIDS.
- **(B)** Count everyone at donor-supported sites as affected, with a smaller per-person risk calibrated to the
  benchmarks.

Show the result as a range across the two. Update the `model_params.csv` source text, which currently misstates the
calibration. Needs data from you: no for (A); for (B), PEPFAR site-level patient counts (PEPFAR Panorama / MER).
