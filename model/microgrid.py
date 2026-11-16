"""
UW microgrid MILP (solar PV + battery + grid), solved with Gurobi.
Constraint numbers (1)-(13) match the progress report.

Run from the repo root:
    .venv/bin/python model/microgrid.py              # base case (needs Gurobi academic license)
    .venv/bin/python model/microgrid.py --days 2     # quick test (fits the free license)
    .venv/bin/python model/microgrid.py --no-export  # no-export scenario
    .venv/bin/python model/microgrid.py --flex 0.10  # with demand flexibility
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
    """Hourly demand (2026), solar capacity factor CF_t and TOU import price c_imp_t."""
    df = pd.read_csv(ROOT / "data" / "processed" / "demand_hourly.csv")

    # Solar CF: fill gaps with the mean of the same hour on adjacent days, cap at 100%
    cf = pd.read_csv(ROOT / "data" / "Solar PV data.csv").iloc[:, 3:6]
    cf.columns = ["S1", "S2", "S3"]
    cf = cf.fillna((cf.shift(24) + cf.shift(-24)) / 2).fillna(cf.shift(24)).fillna(cf.shift(-24))
    cf = cf.clip(upper=100) / 100
    df["CF"] = cf.mean(axis=1) if p.solar == "avg" else cf[p.solar]

    # OEB TOU schedule. Weekends and holidays are off-peak all day.
    date = pd.to_datetime(dict(year=np.where(df.Month >= 10, 2025, 2026), month=df.Month, day=df.Day))
    h = df.Hour - 1                                            # hour-beginning 0-23
    weekday = (date.dt.dayofweek < 5) & ~date.isin(HOLIDAYS)
    summer = df.Month.between(5, 10)
    midday = h.between(11, 16)                                 # 11:00-17:00
    shoulder = h.between(7, 10) | h.between(17, 18)            # 7-11 and 17-19
    on = weekday & ((summer & midday) | (~summer & shoulder))
    mid = weekday & ((summer & shoulder) | (~summer & midday))
    df["c_imp"] = np.select([on, mid], [p.tou["on"], p.tou["mid"]], p.tou["off"])
    return df.iloc[:24 * p.days]


# ------------------------------------------------------------------ model
def build(p: Params):
    df = load_inputs(p)
    H = len(df)
    D0, CF, c_imp = df.demand_kW.to_numpy(), df.CF.to_numpy(), df.c_imp.to_numpy()
    scale = 365 / p.days            # test runs: scale operating cost up to a full year

    m = gp.Model("uw_microgrid")

    # Investment decisions
    xPV = m.addVars(V, name="xPV")                       # new PV, kW
    xB = m.addVars(V, name="xB")                         # new battery, kWh
    zPV = m.addVars(V, vtype=GRB.BINARY, name="zPV")
    zB = m.addVars(V, vtype=GRB.BINARY, name="zB")

    m.addConstrs((xPV[v] <= p.PV_max * zPV[v] for v in V), "1_pv_install")   # (1)
    m.addConstrs((xB[v] <= p.B_max * zB[v] for v in V), "2_b_install")       # (2)
    m.addConstr(xPV.sum() <= p.PV_max, "3_pv_max")                            # (3)
    m.addConstr(xB.sum() <= p.B_max, "4_b_max")                               # (4)

    C_grid, ops = 0, {}
    for y in Y:
        built = [v for v in V if v <= y]
        grow = (1 + p.g) ** (y - BASE_DATA_YEAR)
        L = D0 * grow                                    # demand L_{y,t} with growth

        CapB = m.addMVar(1, name=f"CapB_{y}")
        PVcap = m.addMVar(1, name=f"PVcap_{y}")          # E_y + sum d_{y,v} x_v (helper)
        pv = m.addMVar(H, name=f"pv_{y}")
        ch = m.addMVar(H, name=f"ch_{y}")
        dis = m.addMVar(H, name=f"dis_{y}")
        soc = m.addMVar(H, name=f"soc_{y}")
        imp = m.addMVar(H, ub=p.G_imp_max, name=f"imp_{y}")    # (12) import capacity
        exp = m.addMVar(H, ub=p.G_exp_max, name=f"exp_{y}")    # (13) export capacity

        m.addConstr(CapB[0] == gp.quicksum(xB[v] for v in built), f"5_capB_{y}")               # (5)
        m.addConstr(PVcap[0] == p.E[y] + gp.quicksum((1 - p.degr) ** (y - v) * xPV[v] for v in built))
        m.addConstr(pv <= CF * PVcap, f"6_pv_{y}")                                             # (6)
        m.addConstr(soc[0] == p.SOC_0 * CapB[0] + p.eta * ch[0] - dis[0] / p.eta)             # (7), t = 1
        m.addConstr(soc[1:] == soc[:-1] + p.eta * ch[1:] - dis[1:] / p.eta, f"7_soc_{y}")      # (7)
        m.addConstr(soc >= p.SOC_min * CapB, f"8_socmin_{y}")                                  # (8)
        m.addConstr(soc <= CapB, f"8_socmax_{y}")
        m.addConstr(ch <= CapB / p.h_B, f"9_ch_{y}")                                           # (9)
        m.addConstr(dis <= CapB / p.h_B, f"9_dis_{y}")
        m.addConstr(soc[H - 1] == p.SOC_0 * CapB[0], f"10_socend_{y}")                         # (10)

        # Optional demand flexibility (final report): served demand = L + s, daily sum of s = 0
        demand = L
        if p.alpha > 0:
            crit = df.groupby("k").demand_kW.transform("min").to_numpy()   # daily minimum = critical load
            s = m.addMVar(H, lb=-np.minimum(p.alpha * D0, D0 - crit) * grow,
                          ub=np.minimum(p.alpha * D0, D0.max() - D0) * grow, name=f"s_{y}")
            m.addConstr(s.reshape(H // 24, 24).sum(axis=1) == 0, f"flex_day_{y}")
            demand = L + s

        m.addConstr(imp + pv + dis == demand + ch + exp, f"11_balance_{y}")                  # (11)

        C_grid += p.W[y] * scale * (c_imp @ imp - p.c_exp * exp.sum())
        ops[y] = dict(L=L, imp=imp, exp=exp, pv=pv, ch=ch, dis=dis, soc=soc, CapB=CapB)

    # Objective: min Z = C_inv + C_OM + C_rep - C_RV + C_grid
    m_B = {(y, v): p.m_B_frac * (p.c_rep if (y == 2052 and v == 2028) else p.c_B[v]) for y in Y for v in V}
    cost = {
        "C_inv": gp.quicksum(p.D[v] * (p.c_PV[v] * xPV[v] + p.F_PV * zPV[v] + p.c_B[v] * xB[v] + p.F_B * zB[v])
                             for v in V),
        "C_OM": gp.quicksum(p.W[y] * (p.m_PV * xPV[v] + m_B[y, v] * xB[v]) for y in Y for v in V if v <= y),
        "C_rep": p.D[2043] * p.c_rep * xB[2028],
        "C_RV": p.D[2053] * (12 / 25 * p.c_PV[2040] * xPV[2040] + 2 / 15 * p.c_B[2040] * xB[2040]
                             + 5 / 15 * p.c_rep * xB[2028]),
        "C_grid": C_grid,
    }
    m.setObjective(cost["C_inv"] + cost["C_OM"] + cost["C_rep"] - cost["C_RV"] + cost["C_grid"], GRB.MINIMIZE)
    return m, dict(xPV=xPV, xB=xB, zPV=zPV, zB=zB), ops, cost


# ------------------------------------------------------------------ validation
def validate(p: Params, ops, tol=1e-3):
    """Energy balance, battery limits and simultaneous charge/discharge check."""
    for y, o in ops.items():
        imp, exp, pv, ch, dis, soc = (o[k].X for k in ("imp", "exp", "pv", "ch", "dis", "soc"))
        capB = o["CapB"].X[0]
        bal = abs((imp + pv + dis - ch - exp).sum() - o["L"].sum())   # flexibility nets to zero each day
        both = int(((ch > tol) & (dis > tol)).sum())
        ok = bal < 1 and soc.min() >= p.SOC_min * capB - tol and soc.max() <= capB + tol
        print(f"  {y}: {'OK' if ok else 'FAIL'} | energy balance error {bal:.1e} kWh | "
              f"SOC {soc.min():,.0f}-{soc.max():,.0f} of {capB:,.0f} kWh | simultaneous ch/dis hours: {both}")


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=365)
    ap.add_argument("--solar", default="avg", choices=["avg", "S1", "S2", "S3"])
    ap.add_argument("--growth", type=float, default=0.02)
    ap.add_argument("--no-export", action="store_true")
    ap.add_argument("--flex", type=float, default=0.0, help="demand flexibility share, e.g. 0.10")
    a = ap.parse_args()
    p = Params(days=a.days, solar=a.solar, g=a.growth, alpha=a.flex,
               G_exp_max=0.0 if a.no_export else Params.G_exp_max)

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
        pd.DataFrame({"L": o["L"], **{k: o[k].X for k in ("imp", "exp", "pv", "ch", "dis", "soc")}}
                     ).to_csv(out / f"hourly_{y}.csv", index=False)


if __name__ == "__main__":
    main()
