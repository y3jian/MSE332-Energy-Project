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
- C^grid = Σ_y W_y Σ_t ( c^imp_t g^imp_{y,t} − c^exp g^exp_{y,t} )

## Constraints (numbering used in the code)
1. PV^min z^PV_v ≤ x^PV_v ≤ PV^max z^PV_v  ∀v
2. B^min z^B_v ≤ x^B_v ≤ B^max z^B_v  ∀v
3. Σ_v x^PV_v ≤ PV^max
4. Σ_v x^B_v ≤ B^max
5. CapB_y = Σ_{v<y} x^B_v  ∀y
6. pv_{y,t} ≤ CF_t (E_y + Σ_{v<y} d_{y,v} x^PV_v) Δt
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
| CF_t | `Avg CF` from `data/processed/Solar PV data cleaned.csv` (S1–S3 for sensitivity) | given data (P2) |
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

## Open questions
Values marked UNCONFIRMED are `None` in `model/params.py`, and the model refuses to run until they're set.

**Answered by parameters v4:** battery costs (Q1), battery O&M (Q2; 2028 battery uses 13.34 from y = 2043), export price and cap still
6.41¢ / 6,860 kW (Q5), B^min = 4,000 confirmed (Q6), flexibility symbol is φ (Q9; Table 4 of the report still says β).

**Documents still disagree: code follows the report formulation until answered**
- Q3. Existing PV E_y: the formula retires the 60 kW EV3 array after 25 years (65.2, 64.2, 9.4, 9.1, 0 kW); parameters v4 still
  lists 65.2, 64.2, 62.3, 60.5, 58.7 kW (no retirement). Which one? (Code: formula.)
- Q4. Solar profile: the formulation uses one CF_t; parameters v4 says "alternating scenarios per representative year".
  Which? If alternating, which scenario goes with which year? (Code: average of S1–S3.)

**Not stated anywhere: code made a choice that needs approval**
- Q7. G^imp,max_y and c^imp_{y,t} are indexed by y but given one value or schedule. Same in every representative year? (Code: yes.)
- Q8. TOU calendar: on/mid/off-peak hours follow the weekdays and Ontario holidays of the data calendar
  (Oct 2025 to Sep 2026) in every representative year. OK, or use each representative year's own calendar?

**Course requirements not in the formulation yet** (see `docs/requirements.md`)
- Q10. Carbon emissions: an emission intensity value or hourly series, and is it a cost, a cap, or reported only?
- Q11. Resilience: how will it be formulated (v3 removed u and α), and what does unmet demand cost?
- Q12. Alternative objectives (minimize total grid draw, minimize peak grid draw) and the non-zero BESS test: exact equations?
