# Model findings (summary)

All costs are discounted lifecycle costs for 2028–2052 in real 2028 CAD. Emissions are 25-year totals and are not discounted.
Numbers come from `analysis/run_cases.ipynb`. Every run passes validation: energy balance, battery state of charge and daily shift sum.

## 1. Base case (minimize lifecycle cost)
- **Lifecycle cost Z\* = $207.37M**, made up of investment $13.73M, O&M $2.34M, remaining value −$0.16M and grid $191.46M.
- **What gets built:** 6,860 kW of PV in 2028 (the maximum) and **no battery**.
- **Emissions:** 173,890 t CO₂e. **Peak grid import:** 26,073 kW, in 2049.
- **Why no battery:** buying power cheap and using it when prices are high saves about $18/kWh per year, which barely beats O&M of $17.81/kWh per year before the purchase cost is counted.
- **No exports or curtailment:** PV output (at most 6.9 MW) is always below campus demand (at least about 8 MW).
- **Import limit never binding:** the peak (26.1 MW) stays below the 30.4 MW limit.

## 2. Non-zero battery test (Σ x^B ≥ 4,000 kWh)
- The model builds the **minimum battery (4,000 kWh) as late as possible (2040)**.
- Z = $207.93M, **+$0.56M (+0.27%)** over the base case.
- Emissions rise slightly (+135 t) because the battery loses 15% of each charge.
- The peak rises (+526 kW) because the cost objective doesn't penalize charging in a high-demand hour with a cheap price.

## 3. Alternative objectives (cost cap Z ≤ 1.1 Z\* = $228.1M)
| Objective | Z ($M) | Emissions (t) | Peak (kW) | Build |
|---|---|---|---|---|
| Min cost (base) | 207.37 | 173,890 | 26,073 | 6,860 kW PV in 2028 |
| Min grid imports | 211.83 | 173,890 | 26,073 | 6,860 kW PV in 2028 |
| Min peak draw | 217.92 | 182,490 | **21,930** | 6,860 kW PV in 2040, 17,000 kWh battery in 2040 |

- **Min imports:** imports can't go lower than the base case. PV is already at its maximum, load shifting keeps each day's total fixed, and a battery only adds losses. So the cost-optimal design already minimizes imports.
- **Min peak:** the full 17 MWh battery plus load shifting cuts the peak by about **4.1 MW (−16%)**. The battery size limit (B^max) is what stops it from going lower; the cost cap isn't binding.
- **Caveat:** both objectives have many equally good solutions, so the cost and emissions shown are one arbitrary pick among them. For example, min peak moved PV to 2040 even though building it in 2028 gives the same peak with lower emissions. A second solve that minimizes Z with the alternative objective held fixed would remove this. *(Waiting on a team decision.)*

## 4. Resilience (outage on the peak day, July 2, in every representative year; M = $10/kWh)
| Case | Z ($M) | Cost of unmet demand ($M) | Unmet in the 5 years modelled (MWh) | Emissions (t) |
|---|---|---|---|---|
| Normal (α = 1) | 207.37 | 0 | 0 | 173,890 |
| Partial (α = 0.5) | 217.03 | 9.76 | 369 | 173,765 |
| Complete (α = 0) | 269.30 | 62.71 | 2,174 | 173,234 |

- **Complete outage:** unmet demand = that day's demand − PV, which hand checks confirm.
- **Partial outage:** load shifting fills the halved grid capacity almost all day. Unmet demand grows from 19 MWh (2028) to 169 MWh (2049) as demand grows.
- **The design doesn't change:** at M = $10/kWh, a battery would avoid only about $2k of penalty against about $7M of cost. A sensitivity run on M would show when resilience starts to justify storage.
- **Lower emissions during outages aren't a benefit:** they come from demand that went unserved, not from demand that was avoided.

## 5. Main takeaways
1. Maximum PV in 2028 is the cost-optimal choice. Grid purchases are about 92% of lifecycle cost.
2. A battery isn't worth it at current prices, either for cost or for resilience at M = $10/kWh. It only becomes useful when the goal is a lower peak.
3. Requiring a battery costs little (+0.27%), while cutting the peak by 16% costs about +5% and adds emissions.
4. Ontario's grid is low-carbon (0.059 kg/kWh), so emissions barely differ between designs, except when PV is delayed.

## Still needed for the report
- Citation for e^grid = 0.059 kg CO₂e/kWh and justification for M = $10/kWh.
- Team decision on the second solve for the alternative objectives.
- Baseline definition (no investment, with or without load shifting) and that run.
- Report fixes: CF_t → CF_{y,t} in (6); E_y values (65.2, 64.2, 9.4, 9.1, 0 kW) in the parameter table.
