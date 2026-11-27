"""
UW microgrid MILP (solar PV + battery + grid + demand flexibility), built and solved with Gurobi.
Constraint numbers (1)-(15) and cost terms match docs/formulation.md.

Run from the repo root:
    .venv/bin/python model/microgrid.py              # base case
    .venv/bin/python model/microgrid.py --days 2     # quick test
    .venv/bin/python model/microgrid.py --no-export  # no-export scenario
    .venv/bin/python model/microgrid.py --phi 0      # no demand flexibility
"""
import argparse
import sys
from pathlib import Path

import gurobipy as gp
import numpy as np
import pandas as pd
from gurobipy import GRB

sys.path.insert(0, str(Path(__file__).parent))
from params import BASE_DATA_YEAR, V, Y, Params  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

# Ontario statutory holidays in the data calendar (Oct-Dec 2025, Jan-Sep 2026): off-peak all day
HOLIDAYS = pd.to_datetime(["2025-10-13", "2025-12-25", "2025-12-26", "2026-01-01", "2026-02-16",
                           "2026-04-03", "2026-05-18", "2026-07-01", "2026-08-03", "2026-09-07"])


# ------------------------------------------------------------------ input data
def load_inputs(p: Params) -> pd.DataFrame:
    """Hourly baseline demand L_0,t, solar scenarios (S1-S3 capacity factors) and TOU import price c_imp_t."""
    df = pd.read_csv(ROOT / "data" / "processed" / "demand_hourly.csv")
    solar = pd.read_csv(ROOT / "data" / "processed" / "Solar PV data cleaned.csv")   # cleaned by P2
    assert (solar[["Month", "Day", "Hour"]].values == df[["Month", "Day", "Hour"]].values).all()
    for col in ("S1_frac", "S2_frac", "S3_frac", "Avg CF"):
        df[col] = solar[col]

    # OEB TOU schedule on the data calendar (Oct 2025 to Sep 2026), repeated in every representative year
    # (team decision, Q8) so peak hours stay aligned with the demand profile. Weekends and holidays: off-peak.
    date = pd.to_datetime(dict(year=np.where(df.Month >= 10, 2025, 2026), month=df.Month, day=df.Day))
    h = df.Hour - 1                                            # hour-beginning 0-23
    weekday = (date.dt.dayofweek < 5) & ~date.isin(HOLIDAYS)
    summer = df.Month.between(5, 10)
    midday = h.between(11, 16)                                 # 11:00-17:00
    shoulder = h.between(7, 10) | h.between(17, 18)            # 7-11 and 17-19
    on = weekday & ((summer & midday) | (~summer & shoulder))
    mid = weekday & ((summer & shoulder) | (~summer & midday))
    df["c_imp"] = np.select([on, mid], [p.tou["on"], p.tou["mid"]], p.tou["off"])
    return df


# ------------------------------------------------------------------ model
def build(p: Params):
    full = load_inputs(p)
    df = full.iloc[:24 * p.days]
    H = len(df)
    L0, c_imp = df.demand_kW.to_numpy(), df.c_imp.to_numpy()
    L0_crit = df.groupby("k").demand_kW.transform("min").to_numpy()   # daily minimum of L_0
    L0_peak = full.demand_kW.max()                                     # full-year peak of L_0
    scale = 365 / p.days            # test runs: scale operating cost up to a full year

    m = gp.Model("uw_microgrid")

    # Investment decisions
    xPV = m.addVars(V, name="xPV")                       # new PV, kW
    xB = m.addVars(V, name="xB")                         # new battery, kWh
    zPV = m.addVars(V, vtype=GRB.BINARY, name="zPV")
    zB = m.addVars(V, vtype=GRB.BINARY, name="zB")

    m.addConstrs((xPV[v] >= p.PV_min * zPV[v] for v in V), "1_pv_min")      # (1)
    m.addConstrs((xPV[v] <= p.PV_max * zPV[v] for v in V), "1_pv_max")
    m.addConstrs((xB[v] >= p.B_min * zB[v] for v in V), "2_b_min")          # (2)
    m.addConstrs((xB[v] <= p.B_max * zB[v] for v in V), "2_b_max")
    m.addConstr(xPV.sum() <= p.PV_max, "3_pv_total")                         # (3)
    m.addConstr(xB.sum() <= p.B_max, "4_b_total")                            # (4)

    C_grid, ops = 0, {}
    for y in Y:
        running = [v for v in V if v < y]                # builds operate from the year after install
        grow = (1 + p.g) ** (y - BASE_DATA_YEAR)
        L = L0 * grow                                    # L_{y,t}
        CF = df[p.solar[y]].to_numpy()                   # CF_{y,t}: this year's EV3 scenario
        F_dn = np.minimum(p.phi * L, (L0 - L0_crit) * grow)   # F-_{y,t}: critical load floor
        F_up = np.minimum(p.phi * L, (L0_peak - L0) * grow)   # F+_{y,t}: no new peak

        CapB = m.addMVar(1, name=f"CapB_{y}")
        PVcap = m.addMVar(1, name=f"PVcap_{y}")          # E_y + sum d_{y,v} x_v (helper for (6))
        pv = m.addMVar(H, name=f"pv_{y}")
        ch = m.addMVar(H, name=f"ch_{y}")
        dis = m.addMVar(H, name=f"dis_{y}")
        soc = m.addMVar(H, name=f"soc_{y}")              # soc at end of hour t; soc_0 enters (7) directly
        imp = m.addMVar(H, ub=p.G_imp_max * p.dt, name=f"imp_{y}")   # (12)
        exp = m.addMVar(H, ub=p.G_exp_max * p.dt, name=f"exp_{y}")   # (13)
        f = m.addMVar(H, lb=-F_dn, ub=F_up, name=f"f_{y}")           # (14)
        u = m.addMVar(H, ub=0.0, name=f"u_{y}")          # unmet demand: fixed at 0 here; extensions.add_outage loosens it

        m.addConstr(CapB[0] == gp.quicksum(xB[v] for v in running), f"5_capB_{y}")            # (5)
        m.addConstr(PVcap[0] == p.E(y) + gp.quicksum(p.d(y, v) * xPV[v] for v in running))
        m.addConstr(pv <= CF * PVcap * p.dt, f"6_pv_{y}")                                     # (6)
        m.addConstr(soc[0] == p.SOC_0 * CapB[0] + p.eta * ch[0] - dis[0] / p.eta)            # (7)+(10), t = 1
        m.addConstr(soc[1:] == soc[:-1] + p.eta * ch[1:] - dis[1:] / p.eta, f"7_soc_{y}")     # (7)
        m.addConstr(soc >= p.SOC_min * CapB, f"8_socmin_{y}")                                 # (8)
        m.addConstr(soc <= CapB, f"8_socmax_{y}")
        m.addConstr(ch <= CapB / p.h_B * p.dt, f"9_ch_{y}")                                   # (9)
        m.addConstr(dis <= CapB / p.h_B * p.dt, f"9_dis_{y}")
        m.addConstr(soc[H - 1] == p.SOC_0 * CapB[0], f"10_socend_{y}")                        # (10)
        m.addConstr(imp + pv + dis + u == L + f + ch + exp, f"11_balance_{y}")                # (11), u = 0 in base
        m.addConstr(f.reshape(H // 24, 24).sum(axis=1) == 0, f"15_day_{y}")                  # (15)

        C_grid += p.W(y) * scale * (c_imp @ imp - p.c_exp * exp.sum())
        ops[y] = dict(L=L, f=f, u=u, imp=imp, exp=exp, pv=pv, ch=ch, dis=dis, soc=soc, CapB=CapB)

    # Objective: min Z = C_inv + C_OM + C_rep - C_RV + C_grid
    cost = {
        "C_inv": gp.quicksum(p.D(v) * (p.c_PV[v] * xPV[v] + p.F_PV * zPV[v] + p.c_B[v] * xB[v] + p.F_B * zB[v])
                             for v in V),
        "C_OM": gp.quicksum(p.W(y) * (p.m_PV * xPV[v] + p.m_B[y, v] * xB[v]) for y in Y for v in V if v < y),
        "C_rep": p.D(2043) * p.c_rep * xB[2028],
        "C_RV": p.D(2053) * (1 / 25 * p.c_PV[2028] * xPV[2028] + 13 / 25 * p.c_PV[2040] * xPV[2040]
                             + 3 / 15 * p.c_B[2040] * xB[2040] + 6 / 15 * p.c_rep * xB[2028]),
        "C_grid": C_grid,
    }
    m.setObjective(cost["C_inv"] + cost["C_OM"] + cost["C_rep"] - cost["C_RV"] + cost["C_grid"], GRB.MINIMIZE)
    m._scale = scale                # extensions weight their operating terms the same way as C_grid
    return m, dict(xPV=xPV, xB=xB, zPV=zPV, zB=zB), ops, cost


# ------------------------------------------------------------------ validation
def validate(p: Params, ops, tol=1e-3):
    """Hourly energy balance, battery SOC limits and daily flexibility sum = 0."""
    for y, o in ops.items():
        imp, exp, pv, ch, dis, soc, f, u = (o[k].X for k in ("imp", "exp", "pv", "ch", "dis", "soc", "f", "u"))
        capB = o["CapB"].X[0]
        bal = np.abs(imp + pv + dis + u - (o["L"] + f + ch + exp)).max()
        day = np.abs(f.reshape(-1, 24).sum(axis=1)).max()
        ok = bal < tol and day < tol and soc.min() >= p.SOC_min * capB - tol and soc.max() <= capB + tol
        print(f"  {y}: {'OK' if ok else 'FAIL'} | balance error {bal:.1e} kWh | daily shift sum {day:.1e} | "
              f"SOC {soc.min():,.0f}-{soc.max():,.0f} of {capB:,.0f} kWh | unmet {u.sum():,.0f} kWh")


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=365)
    ap.add_argument("--solar", choices=["S1_frac", "S2_frac", "S3_frac", "Avg CF"],
                    help="sensitivity: use one scenario in every year (default: per-year mapping in params.py)")
    ap.add_argument("--growth", type=float, default=0.02)
    ap.add_argument("--phi", type=float, default=0.10, help="demand flexibility share (0 = off)")
    ap.add_argument("--no-export", action="store_true")
    a = ap.parse_args()
    p = Params(days=a.days, g=a.growth, phi=a.phi, G_exp_max=0.0 if a.no_export else Params.G_exp_max)
    if a.solar:
        p.solar = {y: a.solar for y in Y}
    if p.missing():
        sys.exit(f"Cannot run: unconfirmed parameters in model/params.py: {', '.join(p.missing())}")

    m, inv, ops, cost = build(p)
    m.optimize()
    if m.SolCount == 0:
        print("No solution, status", m.Status)
        return

    print(f"\nTotal discounted cost Z = ${m.ObjVal:,.0f}")
    for k, e in cost.items():
        print(f"  {k:7s} ${e.getValue():,.0f}")
    for v in V:
        print(f"  {v}: PV {inv['xPV'][v].X:,.0f} kW, battery {inv['xB'][v].X:,.0f} kWh")
    print("Validation:")
    validate(p, ops)

    out = ROOT / "model" / "results"
    out.mkdir(exist_ok=True)
    for y, o in ops.items():
        pd.DataFrame({"L": o["L"], **{k: o[k].X for k in ("f", "imp", "exp", "pv", "ch", "dis", "soc")}}
                     ).to_csv(out / f"hourly_{y}.csv", index=False)


if __name__ == "__main__":
    main()
