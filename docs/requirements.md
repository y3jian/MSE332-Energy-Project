# Course requirements (MSE 332 final project)

Text version of `docs/course/project_description.pdf`. Use this to decide what is **in scope**:
if a feature is not needed for an item below, do not build it.

**Final report due Dec 8. 8-minute group presentation in the last week of class.**
We are a group of 5, so we must do **two** of: other low-carbon technologies, demand flexibility,
resilience analysis. We chose **demand flexibility + resilience analysis**; other technologies are
discussed in writing only (wind, hydrogen and thermal storage, each with a justification for leaving it out).

**Clarifications added to the project description (instructor update):**
- If the optimal solution includes no BESS, test that the model works by forcing a non-zero BESS capacity.
- Validation = verifying that the supply and demand linking constraints are satisfied.
- Sensitivity analysis = how varying 2 chosen parameters *independently* influences the chosen system and operations.

Status: [x] done in the model/notebook (`analysis/run_cases.ipynb`), [ ] still to do (mostly report writing).

## The model must
- [x] Represent UW demand, the Ontario grid connection, solar PV and a BESS
- [x] Include capacity and operating constraints for the grid connection, generation, storage and flexible loads
- [x] Use some or all of the provided solar PV scenarios, with a justification for how they are used
- [x] Include at least one meaningful discrete decision (ours: binary build decisions z)
- [x] Take carbon emissions into account (a single grid emission intensity is acceptable)
- [x] Grow demand every year, with a justified growth rate; consider how operations change in later years
- [x] Keep total demand over a defined period (we use a day) unchanged under demand flexibility

## Analysis the report must include
- [x] **Validation:** supply equals demand in every hour, and every constraint is satisfied
- [x] **Sensitivity analysis on 2 parameters** (we do 3: battery cost, import price, PV cost)
- [x] **A non-zero BESS test:** a constraint forcing battery capacity > 0, to see how the battery is operated
- [x] **Different objectives**, at least: (a) minimize total Ontario grid draw, (b) minimize peak grid draw
- [x] **A baseline comparison** (e.g. existing system with no new investment), used to estimate annual savings
- [x] **A small set of stress cases**, explaining *why* the optimum changes (binding constraints, trade-offs)
- [x] **A comparison of formulations or approaches**, covering solution quality and computational effort
      (e.g. base vs enhanced formulation, or optimum vs a simple heuristic)
- [x] **One proposed modelling extension:** why it matters, how it changes the formulation, what it adds (demand flexibility)
- [x] **Resilience:** how the microgrid operates when grid supply is constrained
- [ ] **Limitations**, and how they affect the results (report writing)

## The report must state
- Sets/indices, parameters, decision variables, objective(s), constraints, variable domains, key assumptions
- The model type (ours: **MILP**, with binary z and everything else continuous)
- Sources for technology costs and lifetimes (NLR ATB), TOU prices (OEB), PV area (Campus Plan p. 49)
