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


def no_investment(m, inv):
    """Baseline: existing system only, x^PV_v = x^B_v = z^PV_v = z^B_v = 0 (lifecycle cost objective kept)."""
    for key in ("xPV", "xB", "zPV", "zB"):
        for v in inv[key]:
            inv[key][v].UB = 0.0


def relax_binaries(m, inv):
    """Approach comparison: LP relaxation, z^PV_v and z^B_v in [0, 1] instead of {0, 1}."""
    for key in ("zPV", "zB"):
        for v in inv[key]:
            inv[key][v].VType = GRB.CONTINUOUS


def cost_cap(m, p: Params, Z_star):
    """Z <= (1 + eps) Z*: keeps alternative-objective designs within eps of the minimum lifecycle cost.
    Z is the base objective expression set in microgrid.build(); call this before replacing it. Returns Z."""
    m.update()
    Z = m.getObjective()
    m.addConstr(Z <= (1 + p.eps) * Z_star, "cost_cap")
    return Z


def set_alternative(m, Z, Z_alt):
    """Lexicographic objectives: minimize Z_alt first, then Z among the Z_alt-optimal solutions (tie-break,
    so the reported cost and design are the cheapest of the equally good alternatives)."""
    m.setObjectiveN(Z_alt, index=0, priority=1, name="alternative")
    m.setObjectiveN(Z, index=1, priority=0, name="Z")


def min_imports(m, ops, p: Params, Z_star):
    """Alternative objective 1: min Z^imp = sum_y n_y sum_t g^imp_{y,t} (undiscounted), with Z <= (1 + eps) Z*."""
    Z = cost_cap(m, p, Z_star)
    set_alternative(m, Z, sum(len(A_Y[y]) * m._scale * o["imp"].sum() for y, o in ops.items()))


def min_peak(m, ops, p: Params, Z_star):
    """Alternative objective 2: min Z^peak = P^peak, with g^imp_{y,t} <= P^peak and Z <= (1 + eps) Z*."""
    Z = cost_cap(m, p, Z_star)
    P_peak = m.addMVar(1, name="P_peak")                       # kW, max grid draw over the horizon
    for y, o in ops.items():
        m.addConstr(o["imp"] <= P_peak, f"peak_{y}")
    set_alternative(m, Z, P_peak.sum())


def allow_unmet(m, ops, cost, p: Params):
    """Stress-case infeasibility recovery: u_{y,t} <= L_{y,t} in every hour, penalized with
    C_unmet = M sum_y W_y sum_t u_{y,t} (same penalty as the resilience runs)."""
    if p.M is None:
        raise ValueError("M (unmet-demand penalty) is unconfirmed: set it in params.py")
    for y, o in ops.items():
        o["u"].UB = o["L"]
        o["u"].Obj = p.M * p.W(y) * m._scale
    cost["C_unmet"] = sum(p.M * p.W(y) * m._scale * o["u"].sum() for y, o in ops.items())


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
