### Cloover – **The household energy transition planner**

**🏆 Track Prize: AirPods and Powerbank per team member**

- Challenge
  **The problem**
  Today a customer is sold an energy installation with financing option first, then an energy tariff bolted on afterwards. That's backwards. Build a single checkout / advisor that sells the _outcome_: a full home-energy upgrade — solar, battery, heat pump, EV charger — plus its financing and a dynamic tariff, presented as **one product with one clear monthly number**.That number — the **North Star** — is the **monthly saving**: how much lower the household's total monthly outgoings are once the upgrade and its financing are in, versus what they pay today. You still need to know what they spend now and what the installment is — that's the input — but the figure you put front and centre is what they _save_ per month. (Where the installment outweighs the savings early in the loan, show it honestly — e.g. near cost-neutral now, €X/month saved once it's paid off.)The hard part is producing a _credible_ savings number. That means modelling all aspects, and the right answer changes per household:
  - **Savings certainty** — local irradiance, the dynamic tariff, applicable subsidies, and self-consumption ratio
  - **Household fit** — current spend across electricity, heating, and mobility determines how much of the output is genuinely displaced spend vs. low-value feed-in.
    So the tool should compare upgrade scenarios (solar only / PV + battery / + heat pump / + EV charger) against the household's _current_ total energy + heating + mobility spend, and find the configuration that lands the biggest monthly saving. Those savings span three buckets:
  - **Electricity** — solar self-consumption, plus a battery charging cheap / discharging expensive on the dynamic tariff.
  - **Heating** — a household on oil or gas; switching to a heat pump swaps fuel spend for (partly self-generated) electricity.
  - **Mobility** — switching from a petrol car to an EV, swapping fuel spend for cheap off-peak charging.
    **Up-sell is part of the challenge.** From minimal inputs, the tool should spot the obvious next step and quantify it — e.g. "still on oil heating? A heat pump saves you €X/month" — always framed back to the financing-anchored monthly saving, so a bigger upgrade can actually _increase_ what the household saves each month.**AI angle (core):** an LLM advisor that takes minimal input, models the savings, picks the strongest upgrade path, and explains in plain language why this configuration lands the biggest monthly saving — copy an installer could paste straight into a customer proposal. Potentially zip-code-level grid fees for accurate price estimates.
