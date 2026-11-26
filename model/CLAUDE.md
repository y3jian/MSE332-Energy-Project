# model/: code rules

- The model is built and solved in **Gurobi (`gurobipy`)**, and that's most of the code. Each report
  equation becomes `m.addVar`/`m.addMVar`, `m.addConstr` or a term in `m.setObjective`, so the gurobipy
  code reads like the formulation in `docs/formulation.md`.
- Two files only: `params.py` (numbers) and `microgrid.py` (model). Don't add modules
  unless a new analysis from `docs/requirements.md` truly needs one; ask first.
- `microgrid.py` order: load inputs → variables → constraints (1)–(16) in report order →
  objective (C^inv, C^OM, C^rep, C^RV, C^grid) → solve → validate → save.
- Use vectorized gurobipy (`addMVar`, matrix constraints); no per-hour Python loops (the full model has ~8,760 × 5 hours).
- Scenario and analysis switches (solar scenario, no-export, flexibility, resilience, alternative objective)
  are command-line flags that only change values or toggle report-defined terms. They never add new math.
- Validation must check: hourly energy balance, SOC within limits, daily flexibility sum = 0,
  and print one OK/FAIL line per representative year.
- Keep the output short: total cost, each cost component, installed sizes, validation lines.
