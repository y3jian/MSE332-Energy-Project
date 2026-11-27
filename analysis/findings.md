# Model findings (summary)

All costs are discounted lifecycle costs for 2028–2052 in real 2028 CAD. Emissions are 25-year totals and are not discounted.
Numbers come from `analysis/run_cases.ipynb`. Tables and figures are in `analysis/results/`.

## 1. Base case (minimize lifecycle cost)
- **Lifecycle cost Z\* = $207.37M**, made up of investment $13.73M, O&M $2.34M, remaining value −$0.16M and grid $191.46M.
- **What gets built:** 6,860 kW of PV in 2028 (the maximum; the PV limit (3) is binding) and **no battery**.
- **Emissions:** 173,890 t CO₂e. **Peak grid import:** 26,073 kW, in 2049.
- **Why no battery:** buying power cheap and using it when prices are high saves about $18/kWh per year, which barely beats O&M of $17.81/kWh per year before the purchase cost is counted.
- **No exports or curtailment:** PV output (at most 6.9 MW) is always below campus demand (at least about 8 MW).
- **Import limit never binding:** the peak (26.1 MW) stays below the 30.4 MW limit.

## 2. Baseline comparison (no new investment)
| Case | Z ($M) | Grid ($M) | Imports (GWh) | Emissions (t) |
|---|---|---|---|---|
| Baseline: no investment, no shifting (UW today) | 216.96 | 216.96 | 3,197 | 188,637 |
| Baseline: no investment, with shifting | 212.28 | 212.28 | 3,197 | 188,637 |
| Optimal plan | 207.37 | 191.46 | 2,947 | 173,890 |

| Saving vs UW today | Lifecycle ($M) | Equivalent annual ($M/yr) | Imports avoided (GWh) | Emissions avoided (t) |
|---|---|---|---|---|
| **Total** | **9.59 (4.4%)** | **0.65** | 250 | 14,747 |
| From load shifting | 4.68 | 0.32 | 0 | 0 |
| From PV investment | 4.91 | 0.33 | 250 | 14,747 |

- **Equivalent annual saving** = lifecycle saving ÷ Σ D_a over 2028–2052 (14.8), i.e. the constant yearly amount with the same present value.
- **Load shifting and PV contribute about equally to the savings.** Shifting moves demand to cheaper hours within each day but doesn't reduce imports or emissions. PV is what cuts imports and emissions.
- **Neither reduces the peak** (26.07 MW in all three): the cost objective has no reason to lower it.

## 3. Non-zero battery test (Σ x^B ≥ 4,000 kWh)
- The model builds the **minimum battery (4,000 kWh) as late as possible (2040)**.
- Z = $207.93M, **+$0.56M (+0.27%)** over the base case.
- Emissions rise slightly (+135 t) because the battery loses 15% of each charge.
- The peak rises (+526 kW) because the cost objective doesn't penalize charging in a high-demand hour with a cheap price.
- **How the battery is operated** (`battery_week.png`): on weekdays it charges overnight at off-peak prices and discharges in the 11:00–17:00 summer on-peak window. It sits idle on weekends, which are off-peak all day.

## 4. Alternative objectives (cost cap Z ≤ 1.1 Z\* = $228.1M)
Solved in two stages: first the alternative objective, then the lowest Z among its optimal solutions. This tie-break makes the reported cost and design the cheapest of the equally good options.

| Objective | Z ($M) | ΔZ | Emissions (t) | Peak (kW) | Build |
|---|---|---|---|---|---|
| Min cost (base) | 207.37 | – | 173,890 | 26,073 | 6,860 kW PV in 2028 |
| Min grid imports | 207.37 | 0% | 173,890 | 26,073 | 6,860 kW PV in 2028 (= base) |
| Min peak draw | 211.82 | +2.1% | 181,865 | **21,930** | 6,860 kW PV in 2040, 16,816 kWh battery in 2040 |

- **Min imports gives exactly the base design.** PV is already at its maximum, load shifting keeps each day's total fixed, and a battery only adds losses. So the cost-optimal plan already minimizes imports.
- **Min peak cuts the peak by 4.1 MW (−16%) for +2.1% cost.** It uses a battery of about 17 MWh (about 4.2 MW of discharge) plus load shifting. The cost cap isn't binding.
- **Min peak builds PV in 2040,** most likely because the 2049 peak hour benefits from panels that have degraded less (0.961 vs 0.905 of original output). This delay adds about 8,000 t of emissions.

## 5. Resilience (outage on the peak day, July 2, in every representative year; M = $10/kWh)
| Case | Z ($M) | Cost of unmet demand ($M) | Unmet in the 5 years modelled (MWh) | Emissions (t) |
|---|---|---|---|---|
| Normal (α = 1) | 207.37 | 0 | 0 | 173,890 |
| Partial (α = 0.5) | 217.03 | 9.76 | 369 | 173,765 |
| Complete (α = 0) | 269.30 | 62.71 | 2,174 | 173,234 |

- **Complete outage:** unmet demand = that day's demand − PV, which hand checks confirm.
- **Partial outage:** load shifting fills the halved grid capacity almost all day. Unmet demand grows from 19 MWh (2028) to 169 MWh (2049) as demand grows.
- **The design doesn't change:** at M = $10/kWh, a battery would avoid only about $2k of penalty against about $7M of cost.
- **Lower emissions during outages aren't a benefit:** they come from demand that went unserved, not from demand that was avoided.

## 6. Sensitivity analysis (one parameter at a time)
**Battery capital cost** (c^B_2028, c^B_2040 and c^rep × k; F^B and O&M unchanged)
- **No battery at any tested multiplier from 0.50 to 1.50.** Z stays at $207.37M and nothing else changes.
- **Break-even (by bisection): k ≈ 0.11–0.12**, i.e. c^B_2028 ≈ $45–49/kWh, about 89% below today's cost. Below that, the model builds 17,000 kWh in 2040, but it saves only about $0.03M (−0.02%).
- **Why:** savings from charging cheap and discharging at peak prices only just cover battery O&M (unchanged by k) and the $50k fixed cost. The capital cost is not the main obstacle.

**Grid import price** (all TOU prices × k; export credit 6.41¢, capped at each hour's import price)
| k | Z ($M) | ΔZ | PV | Imports (GWh) | Emissions (t) |
|---|---|---|---|---|---|
| 0.50 | 106.14 | −49% | none | 3,203 | 188,982 |
| 0.75 | 158.21 | −24% | 6,860 kW in **2040** | 3,073 | 181,299 |
| 1.00 | 207.37 | – | 6,860 kW in 2028 | 2,947 | 173,890 |
| 1.25 | 255.23 | +23% | 6,860 kW in 2028 | 2,947 | 173,890 |
| 1.50 | 303.10 | +46% | 6,860 kW in 2028 | 2,947 | 173,890 |
- **At ×0.75,** PV in 2028 no longer pays back. It moves to 2040, when PV is cheaper ($1,322 vs $1,998 per kW) and more of its value is still left in 2052. A check with the builds fixed confirms it: PV in 2040 costs $158.21M, no PV $159.21M, PV in 2028 $159.50M.
- **At ×0.5, no PV is built:** grid power is cheaper than solar.
  - The off-peak price (4.55¢) falls below the 6.41¢ export credit, so the credit is capped at the import price in those hours. Without the cap, the model would buy power and sell it straight back for a profit.
  - 142 hours still show importing and exporting at once (5.8 GWh). With the cap they earn exactly nothing, so they don't affect cost or the design.
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
- **At ×1.25 or more, building in 2028 stops paying back,** and the build moves to 2040. That adds 126 GWh of imports and about 7,400 t of emissions.
- **The 2028 build is only marginally worth it:** a 25% rise in PV cost, or a 25% fall in import price, delays it by 12 years.

## 7. Stress cases
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
- **In the recovery runs** (same M = $10/kWh as resilience), imports sit at the grid limit for about 2,580 hours, and unmet demand falls in the peak hours of the later years. All three limits are binding: PV at PV^max, battery at B^max and imports at the grid limit.
- **The battery (17,000 kWh, built in 2040) is the only one chosen without being forced.** It shifts energy into the hours when the grid limit is reached.
- **No export credit changes nothing**, because the base case never exports.
- **Low solar barely matters:** S1 is only 12% below S3, and PV supplies a small share of demand.

## 8. Comparison of approaches (solution quality and computational effort)
| Approach | Z ($M) | vs MILP | Design | Peak (MW) | Binaries | Solve time |
|---|---|---|---|---|---|---|
| MILP (base formulation) | 207.37 | – | PV 6,860 kW 2028, no battery | 26.07 | 4 | 13.9 s |
| LP relaxation (z ∈ [0, 1]) | 207.37 | 0.00% | identical, z = 1 / 0 | 26.07 | 0 | 2.9 s |
| MILP without flexibility (φ = 0) | 212.05 | +2.26% | identical | 25.09 | 4 | 15.4 s |

All three have the same size: 350,418 variables and 308,450 constraints.
- **The LP relaxation is tight here:** it reaches the same optimum, with z exactly 0 or 1, in about one fifth of the time.
  - This is because PV is built at its maximum (so z^PV = x/PV^max = 1) and no battery is built.
  - The binaries would matter if a build landed between 0 and its minimum size, or if fixed costs were large compared with the capacity cost.
  - The MILP is still the correct formulation, and with 4 binaries it costs only about 11 s more.
- **Demand flexibility (our extension) is worth $4.68M (2.3%)** at no extra computational cost.
  - The variables and constraints for load shifting are part of the base model in both runs; φ = 0 only sets their bounds to 0.
  - The flexibility raises the grid peak by about 1 MW (25.09 → 26.07 MW). Load moves into cheap hours up to the baseline-peak limit in (14), and the cost objective doesn't penalize that.

## 9. Which parameters matter most
- **Lifecycle cost:** import price (−49% to +46%), then discount rate (−16% to +22%) and demand growth (+29% physical cost plus penalties). PV cost moves it by −3.3% to +1.9%. Battery cost, solar scenario and export credit change it by less than 0.5%.
- **PV investment:** the full 6,860 kW is built in every run except import ×0.5, where none is built. What otherwise changes is timing: PV cost ×1.25 or more, or import price ×0.75, delays it to 2040.
- **Battery investment:** only when capital cost drops about 89% (k ≤ 0.11), or when demand outgrows the grid connection (4% growth).
- **Grid dependence and emissions:** demand growth (+37% imports), then lower import prices (+4% at ×0.75, +9% at ×0.5). Emissions track imports.
- **Feasibility:** only demand growth. At 4%/yr, the 30.4 MW grid connection is too small by the 2040s.
- **Is a battery ever economically attractive?** Not on energy-cost grounds under any realistic tested condition. It becomes worthwhile only as capacity, to serve demand the grid connection can't supply, or to lower the peak.

**Computational effort:**
- MILP runs solve to optimality (MIP gap 0) in 10–17 s.
- The LP relaxation takes 2.9 s, and the baselines (builds fixed) 0.2–0.3 s.
- Infeasibility is proven in about 0.2 s.

**Validation** (39 solved runs; Gurobi checks every constraint, bound and binary):
- No run has any constraint, bound or binary violation.
- In each cost-objective run, the objective equals the sum of its cost components.
- No run charges and discharges the battery in the same hour.
- The only hours with simultaneous import and export are the 142 zero-profit hours in the import ×0.5 run.

## 10. Main takeaways
1. **Maximum PV in 2028 is the cost-optimal choice.** It saves $9.6M (about $0.65M/yr) against UW today, half of that from load shifting. Grid purchases are still about 92% of lifecycle cost.
2. **A battery isn't worth it at current prices**, either for cost or for resilience at M = $10/kWh. It only becomes useful for lowering the peak or when demand outgrows the grid connection.
3. **Requiring a battery costs little (+0.27%).** Cutting the peak by 16% costs about +2.1% and adds emissions.
4. **Emissions barely differ between designs**, because Ontario's grid is low-carbon (0.059 kg/kWh). The exception is when PV is delayed.
5. **The 2028 PV build is close to break-even:** a 25% change in PV cost or import price delays it to 2040.

## Still needed for the report
- Citation for e^grid = 0.059 kg CO₂e/kWh and justification for M = $10/kWh; check the F^B = $50,000 source (P3).
- Report fixes: CF_t → CF_{y,t} in (6); E_y values (65.2, 64.2, 9.4, 9.1, 0 kW) in the parameter table; add the export-credit cap c^exp_t = min(c^exp, c^imp_t), the tie-break for the alternative objectives, the baseline definition and the approach comparison.
- Stress-case wording: "lowest-generation scenario in every year", not "replace the average".
- Limitations section and the written discussion of the technologies left out (wind, hydrogen, thermal storage).
