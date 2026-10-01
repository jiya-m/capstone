# Kenya health financing dashboard

Keep app.py, model.py and kenya_health_data.csv in the same folder.

Run:
```
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The seven health categories are Vaccines, TB, Malaria, HIV, Maternal health, Polio and Other.
The CSV retains supplied figures and citations. They were not independently verified in this edit.
Other holds shared services and unsplit multi-disease funding. It includes all US funding.
Blank maternal-health/polio entries mean not reported. Do not enter zero to stand in for unknown amounts.
Vaccines retains the immunisation total: a separate polio component cannot be extracted without new data.
The KES 6.13bn residual previously attributed to Government now uses the source
"Unattributed on-budget" because subtracting grant totals does not establish the funder.
This source is excluded from the reported external share and source-specific donor cuts.

Preset cuts are explicitly illustrative stress tests, not predictions or claims about announced cuts:
no cuts, US 50% reduction, US withdrawal, Global Fund 20% reduction, all donors 25% reduction.
Custom cuts allow separate US, Gavi and Global Fund percentages.
Each percentage applies to the named source only, for every year of the selected horizon.
Baseline annual funding stays constant. Replacement defaults to zero and is entered as a
total for the selected horizon. It offsets losses proportionately by category, capped at the
loss. Surplus replacement is shown separately. All results are financial sensitivity calculations.

Scenario rows: section=scenario_cut, name=scenario label, detail=funding source,
value=fraction cut. Unspecified sources have no cut.
Health funding amounts are KES billions. status=not_reported allows a blank amount.
original_name preserves the prior category, and source preserves provenance.
