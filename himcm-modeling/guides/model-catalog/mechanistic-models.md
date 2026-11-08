# Mechanistic models: physics, geometry, balances, populations and accounting

Use these when you can **write down how the system works**: water in and out of a lake (2021B), heat flow in a house (2018B, 2021A), drone trajectories (2017A), competing products in a market (2019B), species competition (2023A), emissions from energy use (2023B, 2024B). Mechanistic models need fewer data, extrapolate more safely and are easier to explain than pure curve fits.

## Methods used in the corpus

| Method | Corpus examples | Watch for |
|---|---|---|
| Balance (budget) equations | Water balance in [2021B-11552](../../papers/2021B-11552.md), [2021B-11576](../../papers/2021B-11576.md), [2021B-11823](../../papers/2021B-11823.md), [2021B-12384](../../papers/2021B-12384.md) | Put real magnitudes on each term (2021B-11576 built a budget table and converted the deficit to feet per year, p. 11) |
| Geometry for volumes and areas | Frustums and stacked solids (2021B-11823, [2021B-11898](../../papers/2021B-11898.md)), micro-element sums (2021B-11552), pixel counting (2021B-12384) | Check against given tables (2021B-11823 accepted the formula if error < 5%, p. 11) |
| Physical laws for energy and heat | Heat loss through walls and roof (2021A-11462), coupled room–wall heat ODEs and heat-pump COP ([2018B-8506](../../papers/2018B-8506.md)), evaporation formulas (2021B-11552) | Parameter sources; simplifications stated |
| Kinematics and coordinate geometry | Rigid and non-rigid motion, rotation matrices ([2017A-7359](../../papers/2017A-7359.md)) | Collision checks by simulation |
| Astronomical and climate formulas | Night length from the sunrise hour angle ([2021A-11462](../../papers/2021A-11462.md)); sinusoidal temperature curves (2023A-13643) | Inputs by location |
| Competition (Lotka–Volterra) models | Market shares after a ban ([2019B-9548](../../papers/2019B-9548.md)); native and foreign species ([2023A-14632](../../papers/2023A-14632.md)) | Interaction coefficients usually assumed; vary them |
| Population growth and decline | Exponential decline for feasibility (2020B-10876); logistic death rate (2023A-14140); Leslie matrix (2023A-14076) | Source of rates |
| Saturating ODE | Logistic ODE for average utilization ([2024B-15502](../../papers/2024B-15502.md)) | The saturation level drives the result; give its source |
| Life-cycle assessment and cost | Per-bus cradle-to-grave emissions and costs, grid-mix emission factor ([2023B-13694](../../papers/2023B-13694.md)) | Define the boundary (what is counted) |
| Carbon accounting by energy mix | Country or source emission factors ([2024B-15022](../../papers/2024B-15022.md), 2024B-15502, [2024B-16226](../../papers/2024B-16226.md)) | Keep units (kg, t, Mt) consistent |
| Proxy and bottom-up estimation | Top-down proxy (2024B-15022) and bottom-up from machine specifications with PUE and utilization (2024B-15502) | State the proxy as an assumption; cross-check |
| Economic models | Bioeconomic profit and welfare (2023A-14632); expected cost adjusted for failure risk (2020B-10839) | Many assumed parameters |

## Good practice seen in the corpus

- **Turn the statement's list of factors into an equation** whose terms you can measure or estimate (2021B-11552 wrote inflow as river flow plus precipitation and broke each into measurable quantities, p. 7).
- **Translate results into a unit the reader understands**: a deficit of 1.2 million acre-feet per year as about 12 ft of level per year (2021B-11576, p. 11).
- **Build one unit, then scale up.** 2023B-13694 modeled one bus of each type over its lifetime, then scaled by fleet composition to three cities (p. 4).
- **Use a mechanism to check data**, not only to model it (2018A-8874 used energy conservation to fill and check speeds).
- **Cross-check an estimate two ways or against a published figure** (2024B problem card).

## Outside the corpus

Not seen in the carded papers, but often suitable:

- **Dimensional analysis** to find the form of a relationship and check every equation's units (2021B-11552 used similarity scaling for flow; a full unit check of every equation is a cheap safeguard for any paper).
- **Compartment models** (SIR and variants, stock-and-flow diagrams) for spread, adoption, resource stocks and pollution.
- **Newton's law of cooling and simple heat-transfer models** for temperature problems.
- **Logistic and Gompertz growth** for any population or adoption with a carrying capacity.
- **Input–output or material-flow accounting** for supply chains and recycling.
- **Fermi estimation** to sanity-check any headline number in a few lines before trusting the model's output.
