"""
Parameters for the UW microgrid MILP (values from the progress report).
Units: energy kWh, power kW (1-hour steps, so kW == kWh), money CAD (real).
"""
from dataclasses import dataclass, field

V = [2028, 2040]            # investment years
Y = [2028, 2040, 2052]      # representative operating years
BASE_DATA_YEAR = 2026       # year of the demand data


@dataclass
class Params:
    # --- finance
    W: dict = field(default_factory=lambda: {2028: 5.3295, 2040: 6.9446, 2052: 2.5246})  # year weights W_y
    D: dict = field(default_factory=lambda: {2028: 1.0, 2040: 0.5568, 2043: 0.4810, 2053: 0.2953})  # D_a
    c_PV: dict = field(default_factory=lambda: {2028: 1980.0, 2040: 1300.0})   # CAD/kW
    c_B: dict = field(default_factory=lambda: {2028: 510.0, 2040: 430.0})      # CAD/kWh
    c_rep: float = 410.0        # 2043 battery replacement, CAD/kWh
    m_PV: float = 25.0          # CAD/kW/yr
    m_B_frac: float = 0.04      # battery O&M = 4% of capital cost per year
    F_PV: float = 50_000.0      # fixed project costs, CAD
    F_B: float = 50_000.0

    # --- solar
    E: dict = field(default_factory=lambda: {2028: 65.2, 2040: 9.2, 2052: 0.0})  # existing PV after degradation, kW
    degr: float = 0.005         # d_{y,v} = (1 - degr)^(y - v)
    PV_max: float = 6_860.0     # kW
    solar: str = "avg"          # "avg", "S1", "S2", "S3"

    # --- battery
    eta: float = 0.85 ** 0.5    # one-way efficiency (85% round trip)
    h_B: float = 4.0            # hours
    SOC_min: float = 0.10
    SOC_0: float = 0.50
    B_max: float = 24_000.0     # kWh

    # --- demand
    g: float = 0.02             # annual growth
    alpha: float = 0.0          # demand flexibility share (0 = off; 0.10 for flexibility runs)

    # --- grid
    tou: dict = field(default_factory=lambda: {"off": 0.091, "mid": 0.146, "on": 0.189})  # OEB, Nov 1 2026, CAD/kWh
    c_exp: float = 0.0641       # export credit, CAD/kWh (IESO 2025 avg market price)
    G_imp_max: float = 30_436.0  # kW
    G_exp_max: float = 6_860.0   # kW (0 = no-export scenario)

    # --- run
    days: int = 365             # fewer days only for quick tests
