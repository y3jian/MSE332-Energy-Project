"""
Add-ons applied to the base model built by microgrid.build(). Each function changes only
its own report-defined terms; the base model itself is never copied or rewritten.
Equations: docs/formulation.md, sections "Alternative objectives and non-zero battery test"
and "Resilience analysis".
"""
import numpy as np
from gurobipy import GRB

from params import A_Y, Params


def force_battery(m, inv, p: Params):
    """Non-zero battery test: sum_v x^B_v >= B^Test (lifecycle cost objective kept)."""
    m.addConstr(inv["xB"].sum() >= p.B_test, "battery_test")


def cost_cap(m, p: Params, Z_star):
    """Z <= (1 + eps) Z*: keeps alternative-objective designs within eps of the minimum lifecycle cost.
    Z is the base objective expression set in microgrid.build(); call this before replacing it."""
    m.update()
    m.addConstr(m.getObjective() <= (1 + p.eps) * Z_star, "cost_cap")


def min_imports(m, ops, p: Params, Z_star):
    """Alternative objective 1: min Z^imp = sum_y n_y sum_t g^imp_{y,t} (undiscounted), with Z <= (1 + eps) Z*."""
    cost_cap(m, p, Z_star)
    m.setObjective(sum(len(A_Y[y]) * m._scale * o["imp"].sum() for y, o in ops.items()), GRB.MINIMIZE)


def min_peak(m, ops, p: Params, Z_star):
    """Alternative objective 2: min Z^peak = P^peak, with g^imp_{y,t} <= P^peak and Z <= (1 + eps) Z*."""
    cost_cap(m, p, Z_star)
    P_peak = m.addMVar(1, name="P_peak")                       # kW, max grid draw over the horizon
    for y, o in ops.items():
        m.addConstr(o["imp"] <= P_peak, f"peak_{y}")
    m.setObjective(P_peak.sum(), GRB.MINIMIZE)


def peak_day(df_full):
    """Day index k (1..365) of the peak-demand day. Demand grows by the same factor every
    hour, so it's the same day in every representative year (July 2 in our data)."""
    return int(df_full.loc[df_full.demand_kW.idxmax(), "k"])


def add_outage(m, ops, cost, p: Params, alpha, k):
    """Resilience variant: grid availability alpha (0.5 partial, 0 complete outage) for the
    24 hours of day k in every representative year. Implements modified (11)-(13), the
    unmet-demand bound and C_unmet = M sum_y W_y sum_t u_{y,t}."""
    if p.M is None:
        raise ValueError("M (unmet-demand penalty) is unconfirmed: set it in params.py")
    H = len(ops[next(iter(ops))]["L"])
    hours = np.arange(24 * (k - 1), 24 * k)
    if hours[-1] >= H:
        raise ValueError(f"outage day {k} is outside the {H // 24} modelled days")

    a = np.ones(H)                          # alpha_{y,t}: 1 except during the disruption
    a[hours] = alpha
    for y, o in ops.items():
        o["imp"].UB = a * p.G_imp_max * p.dt               # modified (12)
        o["exp"].UB = a * p.G_exp_max * p.dt               # modified (13)
        o["u"].UB = (1 - a) * o["L"]                       # u_{y,t} <= (1 - alpha_{y,t}) L_{y,t}
        o["u"].Obj = p.M * p.W(y) * m._scale               # adds C_unmet to the objective
    cost["C_unmet"] = sum(p.M * p.W(y) * m._scale * o["u"].sum() for y, o in ops.items())
