# Course requirements (MSE 332 final project)

Text version of `docs/course/project_description.pdf`. Use this to decide what is **in scope**:
if a feature is not needed for an item below, do not build it.

**Final report due Dec 8. 8-minute group presentation in the last week of class.**
We are a group of 5, so we must do **two** of: other low-carbon technologies, demand flexibility,
resilience analysis. We chose **demand flexibility + resilience analysis**; other technologies are
discussed in writing only (wind, hydrogen and thermal storage, each with a justification for leaving it out).

## The model must
- [ ] Represent UW demand, the Ontario grid connection, solar PV and a BESS
- [ ] Include capacity and operating constraints for the grid connection, generation, storage and flexible loads
- [ ] Use some or all of the provided solar PV scenarios, with a justification for how they are used
- [ ] Include at least one meaningful discrete decision (ours: binary build decisions z)
- [ ] Take carbon emissions into account (a single grid emission intensity is acceptable)
- [ ] Grow demand every year, with a justified growth rate; consider how operations change in later years
- [ ] Keep total demand over a defined period (we use a day) unchanged under demand flexibility

## Analysis the report must include
- [ ] **Validation:** supply equals demand in every hour, and every constraint is satisfied
- [ ] **Sensitivity analysis on 2 parameters**
- [ ] **A non-zero BESS test:** a constraint forcing battery capacity > 0, to see how the battery is operated
- [ ] **Different objectives**, at least: (a) minimize total Ontario grid draw, (b) minimize peak grid draw
- [ ] **A baseline comparison** (e.g. existing system with no new investment), used to estimate annual savings
- [ ] **A small set of stress cases**, explaining *why* the optimum changes (binding constraints, trade-offs)
- [ ] **A comparison of formulations or approaches**, covering solution quality and computational effort
      (e.g. base vs enhanced formulation, or optimum vs a simple heuristic)
- [ ] **One proposed modelling extension:** why it matters, how it changes the formulation, what it adds
- [ ] **Resilience:** how the microgrid operates when grid supply is constrained
- [ ] **Limitations**, and how they affect the results

## The report must state
- Sets/indices, parameters, decision variables, objective(s), constraints, variable domains, key assumptions
- The model type (ours: **MILP**, with binary z and everything else continuous)
- Sources for technology costs and lifetimes (NLR ATB), TOU prices (OEB), PV area (Campus Plan p. 49)
