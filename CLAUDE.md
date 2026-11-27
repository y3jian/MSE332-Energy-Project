# MSE 332 Group 4: UW Microgrid MILP

Course project: a MILP that sizes solar PV and a battery for the University of Waterloo
and schedules hourly grid imports and exports, battery use and demand shifting over 2028–2052.
Solved in Python with Gurobi.

## Source of truth: read these before changing code
- `docs/formulation.md`: sets, variables, objective, constraints (1)–(16), parameter values.
  **The code implements this document, nothing more.**
- `docs/requirements.md`: what the course asks for. Use it to judge whether something is in scope.
- The PDFs in `docs/course/` and `docs/team/` are the originals. Use the `.md` versions,
  because PDFs can't be read in this environment.

## Rules
1. **Stay in scope.** Only build what `docs/formulation.md` or a `docs/requirements.md` item needs.
   No extra features, options, abstractions, logging, config systems or "nice to have" checks.
   If something seems missing, ask; don't invent it.
2. **Gurobi is the modelling tool.** The bulk of the code is building and solving the model with
   `gurobipy` (variables, constraints, objective). Write the math directly in gurobipy; no other
   solvers or modelling layers (Pyomo, PuLP, CVXPY, scipy).
3. **Keep it simple.** Short plain functions, numpy/pandas/gurobipy only, no new dependencies.
   A teammate who knows the math but not much Python should be able to follow every line.
4. **Match the report.** Every constraint and cost term in the code is commented with its report
   number, e.g. `# (6)`, and uses the report's symbol names where practical.
5. **Numbers live in `model/params.py` only**, each with units and a short source comment.
   No hard-coded parameter values in `model/microgrid.py`.
6. **Make no assumptions; ask.** If a value, mapping or modelling choice isn't stated in
   `docs/formulation.md`, or two documents disagree, don't pick one. Set the value to `None`
   in `params.py` (the model refuses to run), add it to "Open questions" in
   `docs/formulation.md`, and ask the user. Never make up a number or fill a gap with a "reasonable" default.
7. **Flag formulation problems, don't silently fix them.** If the math is wrong or incomplete
   (e.g. a variable with no cost), say so and ask before changing the model.
8. **Raw data is read-only.** `data/*.csv` is never edited. Processed data is produced by the notebooks.
9. **Comments explain *why* or point to the equation.** Don't restate the code.

## Conventions
- Hour index t = 1..8760, Jan 1 1 AM first, `Hour` 1–24 is hour-ending (same as the solar file).
- Units: kWh, kW (1-h steps, so kWh = kW), CAD in real 2028 dollars.
- Demand data year is 2026: L_{y,t} = L⁰_t (1+g)^(y−2026).

## Repo layout
- `data/`: raw inputs; `data/processed/` cleaned demand (`demand_hourly.csv`) and solar files
- `demand/demand_analysis.ipynb`: makes `demand_hourly.csv` (Person 4)
- `model/params.py`: all parameters
- `model/microgrid.py`: the base MILP (constraints (1)–(15), cost objective), solve and validation
- `model/extensions.py`: add-ons applied to the base model (carbon, resilience, forced battery,
  alternative objectives, baseline), one function each
- `analysis/run_cases.ipynb`: runs every case (baseline, sensitivity, stress, objectives) and builds report tables/figures
- `model/results/`: solver output (git-ignored)
- See `model/CLAUDE.md` for the code rules of this layout.

## Running and checking
- Use the project venv: `.venv/bin/python model/microgrid.py`
- Gurobi academic license is at `~/gurobi.lic` (never commit it). Full run: ~5 s. `--days 1` for a quick test.
- After any model change, run the quick test and confirm the validation lines print `OK`.

## Team (who owns what; ask before rewriting someone else's section)
P1 finance, P2 solar PV, P3 battery, P4 demand and flexibility (repo owner), P5 grid, exports and resilience.

## Git
Work on `data-analysis`, merge to `main` through a GitHub PR. Local git is 2.15:
use `git reset HEAD -- <file>` / `git checkout`, not `git restore` / `git switch`.
