# Team formulation (source of truth for the code)

Text version of `docs/team/formulation.pdf` (updated base model, v3) and `docs/team/parameters.pdf` (v4).
`model/` must implement exactly this. If the team changes the formulation, update this file first.

The model is a **MILP**: z^PV_v, z^B_v ∈ {0,1}; everything else is continuous.

## Sets
| Symbol | Meaning |
|---|---|
| V = {2028, 2040} | investment years |
| Y = {2028, 2031, 2037, 2043, 2049} | representative operating years |
| T = {1..8760} | hours (t = 1 is Jan 1, 1 AM) |
| A = {2028..2052}, A_y | calendar years, and the calendar years represented by y |
| D = {1..365}, T_d = {24(d−1)+1, …, 24d} | days, and the 24 hours of day d |
| J | existing campus PV arrays |

| y | A_y | W_y | Builds operating |
|---|---|---|---|
| 2028 | 2028 | 1.000 | existing PV only (2028 build is paid for, not yet running) |
| 2031 | 2029–2034 | 5.076 | existing + 2028 build |
| 2037 | 2035–2040 | 3.788 | existing + 2028 build (2040 build paid for, not yet running) |
| 2043 | 2041–2046 | 2.826 | existing + 2028 and 2040 builds (2028 battery replaced in 2043) |
| 2049 | 2047–2052 | 2.109 | existing + 2028 and 2040 builds |

## Decision variables
x^PV_v, x^B_v ≥ 0; z^PV_v, z^B_v ∈ {0,1}; CapB_y ≥ 0;
pv_{y,t}, g^imp_{y,t}, g^exp_{y,t}, ch_{y,t}, dis_{y,t} ≥ 0; soc_{y,t} ≥ 0 (t = 0..8760); f_{y,t} free (demand shift)

## Objective
min Z = C^inv + C^OM + C^rep − C^RV + C^grid
- C^inv = Σ_v D_v (c^PV_v x^PV_v + F^PV z^PV_v + c^B_v x^B_v + F^B z^B_v)
- C^OM = Σ_y W_y ( m^PV Σ_{v<y} x^PV_v + Σ_{v<y} m^B_{y,v} x^B_v )
- C^rep = D_2043 c^rep_2043 x^B_2028
- C^RV = D_2053 ( 1/25 c^PV_2028 x^PV_2028 + 13/25 c^PV_2040 x^PV_2040 + 3/15 c^B_2040 x^B_2040 + 6/15 c^rep_2043 x^B_2028 )
- C^grid = Σ_y W_y Σ_t ( c^imp_t g^imp_{y,t} − c^exp_t g^exp_{y,t} ), with c^exp_t = min(c^exp, c^imp_t) (team decision:
  the export credit never exceeds the hour's import price, so buying and selling back earns nothing; only active when
  import prices fall below 6.41¢/kWh, i.e. the import price × 0.5 sensitivity)

## Carbon emissions (reported, not optimized; code: `emissions()` in `model/microgrid.py`)
E^CO2 = Σ_y n_y Σ_t e^grid g^imp_{y,t}, with n_y = |A_y| (1, 6, 6, 6, 6)
- Calculated after solving from the chosen imports; not in the objective or constraints.
- Not discounted (a kg of CO₂ has the same impact in any year); exports get no avoided-emissions credit.
- Reported for every run (base, resilience, alternative objectives).

## Constraints (numbering used in the code)
1. PV^min z^PV_v ≤ x^PV_v ≤ PV^max z^PV_v  ∀v
2. B^min z^B_v ≤ x^B_v ≤ B^max z^B_v  ∀v
3. Σ_v x^PV_v ≤ PV^max
4. Σ_v x^B_v ≤ B^max
5. CapB_y = Σ_{v<y} x^B_v  ∀y
6. pv_{y,t} ≤ CF_{y,t} (E_y + Σ_{v<y} d_{y,v} x^PV_v) Δt
7. soc_{y,t} = soc_{y,t−1} + η ch_{y,t} − dis_{y,t}/η
8. SOC^min CapB_y ≤ soc_{y,t} ≤ CapB_y
9. ch_{y,t}, dis_{y,t} ≤ CapB_y / h^B · Δt
10. soc_{y,0} = soc_{y,8760} = SOC^0 CapB_y
11. g^imp + pv + dis = L + f + ch + g^exp
12. g^imp_{y,t} ≤ G^imp,max Δt
13. g^exp_{y,t} ≤ G^exp,max Δt
14. −F⁻_{y,t} ≤ f_{y,t} ≤ F⁺_{y,t}
15. Σ_{t∈T_d} f_{y,t} = 0  ∀y, d

## Derived parameters
- D_a = (1+r)^−(a−2028); W_y = Σ_{a∈A_y} D_a
- E_y = Σ_{j∈J} E^PV_j (1−δ)^(y−a_j) if y < a_j + l^PV, else 0
- d_{y,v} = (1−δ)^(y−v−1) for y > v
- L_{y,t} = L_{0,t} (1+g)^(y−2026)
- C_{y,t} = min over the day of t of L_{y,t} (critical load); P^max_y = max_t L_{y,t}
- F⁻_{y,t} = min{φ L_{y,t}, L_{y,t} − C_{y,t}}; F⁺_{y,t} = min{φ L_{y,t}, P^max_y − L_{y,t}}

## Resilience analysis (`docs/team/resilience.pdf`, code: `model/extensions.py`)
A variant of the base model: all base constraints apply unless modified here; PV and battery are re-optimized in each run.
- α_{y,t} ∈ [0,1]: fraction of grid capacity available (1 normal, 0.5 partial restriction, 0 complete outage)
- u_{y,t} ≥ 0: unmet demand (kWh); M = 10 CAD/kWh: penalty per kWh unmet (team decision; the report still needs its justification)
- Objective: min Z^res = C^inv + C^OM + C^rep − C^RV + C^grid + C^unmet, with C^unmet = M Σ_y W_y Σ_t u_{y,t}
- Modified (11): pv + g^imp + dis + u = L + f + ch + g^exp
- Modified (12): g^imp_{y,t} ≤ α_{y,t} G^imp,max;  modified (13): g^exp_{y,t} ≤ α_{y,t} G^exp,max
- New: 0 ≤ u_{y,t} ≤ (1 − α_{y,t}) L_{y,t}  (unmet demand only during disruptions)
- Runs: (1) normal, α = 1 everywhere (= base model); (2) partial, α = 0.5 for the 24 h of the peak-demand day;
  (3) complete outage, α = 0 for the same 24 h. Peak-demand day = July 2 (k = 183), the highest hour and the highest daily
  energy, and the same day in every representative year because growth is uniform.
- Report for each run: PV and battery capacity, lifecycle cost, total unmet demand, emissions.
- Limitations: the outage recurs once per calendar year represented; perfect foresight (the battery can pre-charge).
- Code: the base model contains u with upper bound 0 (so base (11) is unchanged); `add_outage` sets the α bounds,
  the u bound and the M objective coefficients.

## Alternative objectives and non-zero battery test (team answer to Q12, code: `model/extensions.py`)
Each is a separate run on the base model. Z is the base lifecycle cost expression; Z* is its optimum from the base run.
- **Alt. objective 1, minimize grid imports:** min Z^imp = Σ_y n_y Σ_t g^imp_{y,t} (undiscounted: imports are physical
  quantities), subject to all base constraints and the lifecycle cost cap Z ≤ (1 + ε) Z*, ε = 0.10.
- **Alt. objective 2, minimize peak grid draw:** new variable P^peak ≥ 0 (kW); min Z^peak = P^peak, subject to
  g^imp_{y,t} ≤ P^peak ∀y, t, all base constraints and Z ≤ (1 + ε) Z*.
- **Non-zero battery test:** lifecycle cost objective plus Σ_v x^B_v ≥ B^Test, B^Test = B^min = 4,000 kWh
  (with (2), this forces z^B_v = 1 in at least one investment year).

## Sensitivity analysis and stress cases (team spec, code: `analysis/run_cases.ipynb`)
Lifecycle cost objective and all base constraints; every run starts from the base parameters.
- Sensitivity 1, battery capital cost: c^B_2028, c^B_2040 and c^rep_2043 × {0.50, 0.75, 1.00, 1.25, 1.50} (F^B and m^B unchanged;
  C^RV uses the scaled costs). If no battery is built, find the break-even multiplier by bisection.
- Sensitivity 2, grid import price: all TOU prices × {0.50, 0.75, 1.00, 1.25, 1.50}; c^exp unchanged. Where
  c^imp_t < c^exp (× 0.5, off-peak hours) the export credit is capped at c^imp_t, so there is no resale profit.
- S1 low solar: lowest-generation scenario (S1, 1,544 kWh/kW per year) in every representative year.
- S2 high growth: g = 0.04. S3 discount rate: r = 0.03 and 0.07. S4 no export credit: c^exp = 0.
- S5: low solar + battery cost × 1.5 + import price × 0.75. S6: low solar + g = 0.04 + import price × 1.5.
- Sensitivity 3, PV capital cost: c^PV_2028 and c^PV_2040 × {0.50, 0.75, 1.00, 1.25, 1.50} (F^PV and m^PV unchanged;
  C^RV uses the scaled costs).
- Infeasible runs are re-run with u_{y,t} ≤ L_{y,t} in every hour and C^unmet = M Σ_y W_y Σ_t u_{y,t}, with the same
  M = 10 CAD/kWh as the resilience analysis (team decision: one penalty everywhere).
- Physical totals use n_y (undiscounted); financial totals use W_y.

## Parameter values
| Symbol | Value | Source |
|---|---|---|
| r | 0.05 | ISED cost-benefit analysis |
| c^PV_v | 1,998 (2028), 1,322 (2040) CAD/kW | NLR ATB 2025, commercial PV |
| F^PV | 25,300 CAD | NLR 83586 (USD 18,053 × 1.4) |
| m^PV | 24.68 CAD/kW/yr | NLR ATB 2025 |
| PV^max / PV^min | 6,860 / 200 kW | Campus Plan / ATB reference system |
| J: E^PV_j, a_j | 60 kW (2012), 10 kW (2024) | EV3 arrays (progress report, Table 5) |
| l^PV, δ | 25 yr, 0.005 | ATB / UW Climate Institute |
| CF_{y,t} | EV3 scenario by year: 2028 S1, 2031 S2, 2037 S3, 2043 S1, 2049 S2 (`S1_frac`… in `data/processed/Solar PV data cleaned.csv`) | given data (P2); team decision |
| c^B_v | 410.2 (2028), 309.4 (2040) CAD/kWh (USD 293 / 221 × 1.4) | NLR battery cost projections, 2025 update |
| c^rep_2043 | 292.6 CAD/kWh (USD 209 × 1.4) | NLR battery cost projections, 2025 update |
| F^B | 50,000 CAD | DOE PV system cost benchmarks |
| m^B_{y,v} | 2028 battery 17.81, 2040 battery 14.23, replacement 13.34 CAD/kWh/yr (2028 battery uses 13.34 from y = 2043, team decision) | IESO APO 2024 Resource Costs |
| B^max / B^min | 17,000 / 4,000 kWh | Elora-Fergus BESS land use / NLR ATB 2025 |
| η, h^B | 0.92195 (= √0.85), 4 h | NLR ATB 2025 battery |
| SOC^min, SOC^0 | 0.10, 0.50 | |
| g | 0.02 | IESO 2026 APO (about 2.1%/yr reference) |
| φ | 0.10 | |
| c^imp_t | 0.091 / 0.146 / 0.189 CAD/kWh (off / mid / on-peak) | OEB TOU, Nov 2026 |
| c^exp | 0.0641 CAD/kWh (constant) | IESO 2025 Year in Review |
| G^imp,max / G^exp,max | 30,436 / 6,860 kW | P5 |
| Δt | 1 h | |
| e^grid | 0.059 kg CO₂e/kWh (constant) | team formulation (source to be cited in the report) |
| ε | 0.10 (alternative objectives: Z ≤ 1.1 Z*) | team decision (Q12) |
| B^Test | 4,000 kWh (= B^min) | team decision (Q12) |

## Open questions
Values marked UNCONFIRMED are `None` in `model/params.py`, and the model refuses to run until they're set.

**Answered by parameters v4:** battery costs (Q1), battery O&M (Q2; 2028 battery uses 13.34 from y = 2043), export price and cap still
6.41¢ / 6,860 kW (Q5), B^min = 4,000 confirmed (Q6), flexibility symbol is φ (Q9; Table 4 of the report still says β).
**Answered by the team:** Q3, E_y uses the report formula (60 kW EV3 array retires in 2037): 65.2, 64.2, 9.4, 9.1, 0 kW.
  The parameter sheet's 62.3 / 60.5 / 58.7 kW values are outdated.
  Q4, solar uses alternating scenarios CF_{y,t} (not the average): 2028 S1, 2031 S2, 2037 S3, 2043 S1, 2049 S2.
  The report's constraint (6) and Table 4 should change CF_t to CF_{y,t}.
  Q7, G^imp,max = 30,436 kW and the TOU prices are constant in every representative year: the import limit is sized
  on projected 2052 peak demand + 10% margin, and prices are held constant in real terms (demand still grows 2%/yr).
  Q8, the TOU schedule uses the data calendar (Oct 2025 to Sep 2026) in every representative year, so peak hours stay
  aligned with the demand profile's weekdays and holidays (assumption: the same annual calendar pattern repeats).

**Answered by the updated base model (Final Project 6):** Q10, carbon is reported only, E^CO2 = Σ_y n_y Σ_t e^grid g^imp,
  e^grid = 0.059 kg CO₂e/kWh. Q13, emissions are reported for every run, including the resilience runs.
  Still for the report: a citation for 0.059.
**Answered by the team (Final Project 7):** Q12, alternative objectives and the non-zero battery test (section above).
