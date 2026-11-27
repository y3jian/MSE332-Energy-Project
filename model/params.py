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
    # CF_{y,t}: EV3 scenario used in each representative year (team decision; columns of the cleaned solar file)
    solar: dict = field(default_factory=lambda: {2028: "S1_frac", 2031: "S2_frac", 2037: "S3_frac",
                                                 2043: "S1_frac", 2049: "S2_frac"})

    # --- battery
    c_B: dict = field(default_factory=lambda: {2028: 410.2, 2040: 309.4})  # CAD/kWh (NLR 2025 battery cost
                                              # projections: USD 293 / 221 x 1.4)
    c_rep: float = 292.6                      # 2043 replacement, CAD/kWh (NLR: USD 209 x 1.4)
    # m^B_{y,v}, CAD/kWh/yr (IESO APO 2024 Resource Costs): 2028 battery 17.81, 2040 battery 14.23,
    # replacement battery 13.34 (team decision: the 2028 battery uses the replacement rate from y = 2043).
    m_B: dict = field(default_factory=lambda: {
        (2031, 2028): 17.81, (2037, 2028): 17.81, (2043, 2028): 13.34, (2049, 2028): 13.34,
        (2043, 2040): 14.23, (2049, 2040): 14.23})
    F_B: float = 50_000.0                     # fixed project cost, CAD (DOE cost benchmarks)
    B_min: float = 4_000.0                    # kWh (NLR ATB 2025 commercial battery)
    B_max: float = 17_000.0                   # kWh (group assumption)
    eta: float = 0.85 ** 0.5                  # one-way efficiency (85% round trip, NLR ATB)
    h_B: float = 4.0                          # storage duration, h
    SOC_min: float = 0.10
    SOC_0: float = 0.50

    # --- demand
    g: float = 0.02                           # annual demand growth (IESO APO)
    phi: float = 0.10                         # max hourly demand shift, fraction of demand

    # --- grid
    # Grid values are constant in every representative year (team decision, Q7): prices constant in real terms
    tou: dict = field(default_factory=lambda: {"off": 0.091, "mid": 0.146, "on": 0.189})  # CAD/kWh (OEB, Nov 2026)
    c_exp: float = 0.0641                     # export credit, CAD/kWh (IESO 2025)
    G_imp_max: float = 30_436.0               # kW (P5: projected 2052 peak + 10% margin)
    G_exp_max: float = 6_860.0                # kW (P5; 0 = no-export scenario)
    dt: float = 1.0                           # interval length, h

    # --- resilience extension (docs/team/resilience.pdf); not used by the base model
    M: float = 10.0                           # unmet-demand penalty, CAD/kWh (team decision; justification TBD in report)

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

    def missing(self, skip=("M",)):
        """Unconfirmed parameters (None, also inside dicts). Extension-only parameters are
        skipped here and checked by the extension that uses them."""
        out = []
        for name, value in vars(self).items():
            if name in skip:
                continue
            if value is None:
                out.append(name)
            elif isinstance(value, dict):
                out += [f"{name}{key}" for key, v in value.items() if v is None]
        return out
