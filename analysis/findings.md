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

## 5. Sensitivity analysis (one parameter at a time)
**Battery capital cost** (c^B_2028, c^B_2040 and c^rep × k; F^B and O&M unchanged)
- **No battery at any tested multiplier from 0.50 to 1.50.** Z stays at $207.37M and nothing else changes.
- **Break-even (by bisection): k ≈ 0.11–0.12**, i.e. c^B_2028 ≈ $45–49/kWh, about 89% below today's cost. Below that, the model builds 17,000 kWh in 2040, but it saves only about $0.03M (−0.02%).
- **Why:** savings from charging cheap and discharging at peak prices only just cover battery O&M (unchanged by k) and the $50k fixed cost. The capital cost is not the main obstacle.

**Grid import price** (all TOU prices × k, export credit unchanged)
| k | Z ($M) | ΔZ | PV | Imports (GWh) | Emissions (t) |
|---|---|---|---|---|---|
| 0.50 ⚠ | 95.29 | −54% | none | 4,183 | 246,770 |
| 0.75 | 158.21 | −24% | 6,860 kW in **2040** | 3,073 | 181,299 |
| 1.00 | 207.37 | – | 6,860 kW in 2028 | 2,947 | 173,890 |
| 1.25 | 255.23 | +23% | 6,860 kW in 2028 | 2,947 | 173,890 |
| 1.50 | 303.10 | +46% | 6,860 kW in 2028 | 2,947 | 173,890 |
- **At ×0.75,** PV in 2028 no longer pays back. It moves to 2040, when PV is cheaper ($1,322 vs $1,998 per kW) and more of its value is still left in 2052. A check with the builds fixed confirms it: PV in 2040 costs $158.21M, no PV $159.21M, PV in 2028 $159.50M.
- **⚠ ×0.50 is not a valid result:** the off-peak price (0.0455) is below the export credit (0.0641). The model imports and exports at the same time in 28,740 hours (985 GWh exported) to profit from the difference. *(Waiting on a team decision about the export policy.)*
- **No battery is built at any import price.** Scaling all prices by the same factor leaves the relative TOU structure unchanged, and the gap between on-peak and off-peak prices is too small for storage to pay off.

**PV capital cost** (c^PV_2028 and c^PV_2040 × k; F^PV and O&M unchanged)
| k | Z ($M) | ΔZ | PV build | Imports (GWh) | Emissions (t) |
|---|---|---|---|---|---|
| 0.50 | 200.59 | −3.3% | 6,860 kW in 2028 | 2,947 | 173,890 |
| 0.75 | 203.98 | −1.6% | 6,860 kW in 2028 | 2,947 | 173,890 |
| 1.00 | 207.37 | – | 6,860 kW in 2028 | 2,947 | 173,890 |
| 1.25 | 210.37 | +1.4% | 6,860 kW in **2040** | 3,073 | 181,299 |
| 1.50 | 211.28 | +1.9% | 6,860 kW in **2040** | 3,073 | 181,299 |
- **The full 6,860 kW is always built** (the PV limit (3) is binding in every run). Only the timing changes.
- **At ×1.25 or more, building in 2028 stops paying back,** and the build moves to 2040, when PV is cheaper and more of its value is left at 2052. That adds 126 GWh of imports and about 7,400 t of emissions.
- **The 2028 build is only marginally worth it:** a 25% rise in PV cost, or a 25% fall in import price, delays it by 12 years.

## 6. Stress cases
| Case | Status | Z ($M) | ΔZ | Build | Imports (GWh) | Emissions (t) | Unmet |
|---|---|---|---|---|---|---|---|
| S1 Low solar (S1 all years) | optimal | 208.06 | +0.3% | same as base | 2,957 | 174,439 | 0 |
| S2 Growth 4% | **infeasible** | – | – | – | – | – | – |
| S2 recovery (M = $10/kWh) | optimal | 268.38 + penalty 26.28 | +29% | PV 2028, 17,000 kWh battery in 2040 | 4,026 | 237,526 | 7,475 MWh; 346 h; max 10.3 MW |
| S3 Discount 3% | optimal | 252.90 | +22% | same as base | 2,947 | 173,890 | 0 |
| S3 Discount 7% | optimal | 174.05 | −16% | same as base | 2,947 | 173,890 | 0 |
| S4 No export credit | optimal | 207.37 | 0% | same as base | 2,947 | 173,890 | 0 |
| S5 Combined financial | optimal | 158.20 | −24% | PV 2040 | 3,073 | 181,325 | 0 |
| S6 Combined supply | **infeasible** | – | – | – | – | – | – |
| S6 recovery (M = $10/kWh) | optimal | 393.80 + penalty 24.59 | +90% | PV 2028, 17,000 kWh battery in 2040 | 4,036 | 238,103 | 6,994 MWh; 319 h; max 10.3 MW |

- **4% growth makes the model infeasible** (Gurobi proves it in 0.2 s): the 2049 peak (about 40.8 MW) exceeds the import limit (30.4 MW) plus what PV, the battery and load shifting can cover.
- **In the recovery runs, which use the same M = $10/kWh as resilience,** imports sit at the grid limit for about 2,580 hours, and unmet demand falls in the peak hours of the later years. All three limits are binding: PV at PV^max, battery at B^max and imports at the grid limit.
- **The battery (17,000 kWh, built in 2040) is the only one chosen without being forced.** It shifts energy into the hours when the grid limit is reached.
- **No export credit changes nothing**, because the base case never exports.
- **Low solar barely matters:** S1 is only 12% below S3, and PV supplies a small share of demand.

## 7. Which parameters matter most
- **Lifecycle cost:** import price (±23–46%), then discount rate (−16% to +22%) and demand growth (+29% physical cost plus penalties). PV cost moves it by −3.3% to +1.9%. Battery cost, solar scenario and export credit change it by less than 0.5%.
- **PV investment:** the full 6,860 kW is always built, except in the flagged import ×0.5 run. What changes is timing: PV cost ×1.25 or more, or import price ×0.75, delays it to 2040.
- **Battery investment:** only when capital cost drops about 89% (k ≤ 0.11), or when demand outgrows the grid connection (4% growth).
- **Grid dependence and emissions:** demand growth (+37% imports) and lower import prices (+4% at ×0.75). Emissions track imports.
- **Feasibility:** only demand growth. At 4%/yr, the 30.4 MW grid connection is too small by the 2040s.
- **Is a battery ever economically attractive?** Not on energy-cost grounds under any realistic tested condition. It becomes worthwhile only as capacity, to serve demand the grid connection can't supply.

**Computational effort:** every feasible run solves to optimality (MIP gap 0) in 10–17 s; infeasibility is proven in about 0.2 s.

Validation: all 29 solved runs have zero constraint, bound and binary violations (Gurobi). In each, the objective equals the sum of its cost components and no battery charges and discharges in the same hour. The only issue found is the simultaneous import and export in the flagged ×0.50 run.

## 8. Main takeaways
1. Maximum PV in 2028 is the cost-optimal choice. Grid purchases are about 92% of lifecycle cost.
2. A battery isn't worth it at current prices, either for cost or for resilience at M = $10/kWh. It only becomes useful when the goal is a lower peak.
3. Requiring a battery costs little (+0.27%), while cutting the peak by 16% costs about +5% and adds emissions.
4. Ontario's grid is low-carbon (0.059 kg/kWh), so emissions barely differ between designs, except when PV is delayed.

## Still needed for the report
- Citation for e^grid = 0.059 kg CO₂e/kWh and justification for M = $10/kWh.
- Team decision on the second solve for the alternative objectives.
- Baseline definition (no investment, with or without load shifting) and that run.
- Report fixes: CF_t → CF_{y,t} in (6); E_y values (65.2, 64.2, 9.4, 9.1, 0 kW) in the parameter table.
