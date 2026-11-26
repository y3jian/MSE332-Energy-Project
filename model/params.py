"""
Parameters for the UW microgrid MILP. Values and sources: docs/formulation.md.
Units: energy kWh, power kW (1-hour steps, so kW == kWh), money CAD (real 2028 dollars).
"""
from dataclasses import dataclass, field

V = [2028, 2040]                              # investment years
Y = [2028, 2031, 2037, 2043, 2049]            # representative operating years
A_Y = {2028: range(2028, 2029), 2031: range(2029, 2035), 2037: range(2035, 2041),
       2043: range(2041, 2047), 2049: range(2047, 2053)}   # calendar years represented by y
START_YEAR = 2028                             # discounting base year
BASE_DATA_YEAR = 2026                         # year of the demand data
EXISTING_PV = [(60.0, 2012), (10.0, 2024)]    # J: (E^PV_j kW, install year a_j), EV3 arrays


@dataclass
class Params:
    # --- finance
    r: float = 0.05                                                            # real discount rate (ISED)

    # --- solar
    c_PV: dict = field(default_factory=lambda: {2028: 1998.0, 2040: 1322.0})   # CAD/kW (NLR ATB 2025)
    F_PV: float = 25_300.0                    # fixed project cost, CAD (NLR 83586: USD 18,053 x 1.4)
    m_PV: float = 24.68                       # CAD/kW/yr (NLR ATB 2025)
    PV_min: float = 200.0                     # kW (ATB reference system)
    PV_max: float = 6_860.0                   # kW (Campus Plan carport lots)
    delta: float = 0.005                      # annual PV degradation
    l_PV: int = 25                            # PV lifespan, years
    solar: str = "Avg CF"                     # CF column: "Avg CF", "S1_frac", "S2_frac", "S3_frac"

    # --- battery
    c_B: dict = field(default_factory=lambda: {2028: 410.0, 2040: 309.0})      # CAD/kWh (report sync note; confirm)
    c_rep: float = 293.0                      # 2043 replacement, CAD/kWh (report sync note; confirm)
    F_B: float = 50_000.0                     # fixed project cost, CAD (group assumption)
    m_B_frac: float = 0.04                    # TBD: m^B = 4% of capital cost/yr (progress-report placeholder)
    B_min: float = 4_000.0                    # kWh (ATB 1 MW, 4 h system)
    B_max: float = 17_000.0                   # kWh (group assumption)
    eta: float = 0.85 ** 0.5                  # one-way efficiency (85% round trip, NLR ATB)
    h_B: float = 4.0                          # storage duration, h
    SOC_min: float = 0.10
    SOC_0: float = 0.50

    # --- demand
    g: float = 0.02                           # annual demand growth (IESO APO)
    phi: float = 0.10                         # max hourly demand shift, fraction of demand

    # --- grid
    tou: dict = field(default_factory=lambda: {"off": 0.091, "mid": 0.146, "on": 0.189})  # CAD/kWh (OEB, Nov 2026)
    c_exp: float = 0.0641                     # export credit, CAD/kWh (IESO 2025)
    G_imp_max: float = 30_436.0               # kW (P5)
    G_exp_max: float = 6_860.0                # kW (P5; 0 = no-export scenario)
    dt: float = 1.0                           # interval length, h

    # --- run
    days: int = 365                           # fewer days only for quick tests

    # --- derived parameters (formulas from docs/formulation.md)
    def D(self, a):
        """Discount factor D_a for calendar year a."""
        return (1 + self.r) ** -(a - START_YEAR)

    def W(self, y):
        """Discounted weight W_y of representative year y."""
        return sum(self.D(a) for a in A_Y[y])

    def E(self, y):
        """Existing PV capacity in year y after degradation; arrays retire after l_PV years."""
        return sum(cap * (1 - self.delta) ** (y - a) for cap, a in EXISTING_PV if y < a + self.l_PV)

    def d(self, y, v):
        """Remaining output fraction in year y of PV built in year v (runs from v + 1)."""
        return (1 - self.delta) ** (y - v - 1)

    def m_B(self, y, v):
        """Battery O&M rate; the 2028 battery uses the replacement cost from 2043 on."""
        cost = self.c_rep if (v == 2028 and y >= 2043) else self.c_B[v]
        return self.m_B_frac * cost
