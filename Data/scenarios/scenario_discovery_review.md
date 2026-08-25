# Scenario Discovery Review

## Reviewer conclusion

The current data supports several strong evaluation scenarios, but two important weaknesses must be fixed before calling the scenario set fully production-ready:

1. The currently uploaded `fact_inventory_monthly.csv` contains **zero stockout rows**. Therefore a stockout-root-cause scenario cannot currently be evaluated from this uploaded version.
2. Unstructured pricing evidence is sparse: the support dataset contains only 1 Pricing ticket and the sales-call dataset contains only 4 `Price negotiation` outcomes. Pricing can therefore be tested analytically, but cross-source causal validation is currently weak.

The strongest scenarios are therefore not all equally causal. Some are excellent anomaly/diagnostic tests, while others are better treated as hypothesis-generation tests.

## Recommended evaluation set

1. Returns spike — South Korea / A6519160401 / May 2021
2. Channel shift — South Korea / Brick & Mortar / Jan 2021
3. Marketing inefficiency — China / A2520150501 / Apr 2021
4. Competitive pricing pressure — China / A0621150308 / Jan 2021
5. Customer service/delivery deterioration — Indonesia / Mar 2020
6. Category demand collapse — India / Processors / Mar 2020
7. Product-mix shift — Portugal / Wi fi extender / Sep 2019
8. Market-wide unexplained shock — Germany / Mar 2020

## Best 3 polished demo scenarios

### Demo 1 — Marketing inefficiency
China, A2520150501, Apr 2021:
- gross sales fell 85.8%
- marketing spend increased 132.5%
- conversion rate fell from 7.88% to 3.63%

This is a clean structured-data story.

### Demo 2 — Returns spike
South Korea, A6519160401, May 2021:
- gross sales fell 95.7%
- return rate jumped to 39.91%
- returns were $22,557.02 against $648.44 gross sales

This demonstrates that the system must distinguish revenue decline from a returns problem.

### Demo 3 — Channel shift
South Korea, Jan 2021:
- Brick & Mortar gross sales fell 68.5%
- E-Commerce gross sales increased 21.9%
- total South Korea gross sales still fell 57.4%

This demonstrates cross-dimensional reasoning rather than single-table correlation.

## Important interpretation

Do not label every candidate's suspected cause as a proven root cause.

For pricing scenarios, the data proves a price-gap event and sales decline, but the current unstructured evidence is too sparse to prove that price caused the decline.

For the Germany March 2020 case, the data proves a large market shock but does not contain a direct macroeconomic cause. This is useful as an **uncertainty-handling test**: the system should say that the cause is not established rather than hallucinating one.

For the inventory scenario, do not use it until the inventory dataset contains actual stockout events.
