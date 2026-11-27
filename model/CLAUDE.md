# model/: code rules

- The model is built and solved in **Gurobi (`gurobipy`)**, and that's most of the code. Each report
  equation becomes `m.addVar`/`m.addMVar`, `m.addConstr` or a term in `m.setObjective`, so the gurobipy
  code reads like the formulation in `docs/formulation.md`.

## Layout: base model + add-ons + case runner (one job per file)
| File | Job |
|---|---|
| `params.py` | every number, with units and source. Nothing else. |
| `microgrid.py` | the **base model only**: report constraints (1)–(15) and the cost objective, plus validation. It must match the base formulation line for line. |
| `extensions.py` | one short function per add-on (carbon, outage/resilience, forced battery, alternative objectives, baseline). Each takes the built model, adds or changes only its own report-defined terms, and is tagged with its equation numbers. |
| `../analysis/run_cases.ipynb` | one cell per case: build base model → apply add-ons → solve → add a row to the results table. Produces the report's tables and figures. |

- **Never copy the base model** into another file or a case. Fix things once, in `microgrid.py`.
- Extensions **don't rewrite existing constraints**. If an add-on needs a variable inside a base
  constraint (e.g. unmet demand u in the balance (11)), the base model includes it fixed at 0
  and the add-on only changes bounds or coefficients.
- Don't add other files; ask first.

## Code rules
- `microgrid.py` order: load inputs → variables → constraints (1)–(15) in report order →
  objective (C^inv, C^OM, C^rep, C^RV, C^grid) → solve → validate → save.
- Use vectorized gurobipy (`addMVar`, matrix constraints); no per-hour Python loops (the full model has ~8,760 × 5 hours).
- Command-line options in `microgrid.py` stay limited to simple value changes (days, solar, growth, φ, no-export).
  Anything that adds equations belongs in `extensions.py`.
- Validation must check: hourly energy balance, SOC within limits, daily flexibility sum = 0,
  and print one OK/FAIL line per representative year.
- Keep the output short: total cost, each cost component, installed sizes, validation lines.
