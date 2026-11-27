"""
Add-ons applied to the base model built by microgrid.build(). Each function changes only
its own report-defined terms; the base model itself is never copied or rewritten.
Equations: docs/formulation.md, section "Resilience analysis".
"""
import numpy as np

from params import Params


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
