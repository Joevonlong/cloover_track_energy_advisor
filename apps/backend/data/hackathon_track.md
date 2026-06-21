# Hackathon Track — Criteria

Build a single checkout / advisor that sells the *outcome*: a full home-energy upgrade — solar, battery, heat pump, EV charger — plus its financing and a dynamic tariff, presented as **one product with one clear monthly number**.

The **North Star** is the **monthly saving**: how much lower the household's total monthly outgoings are once the upgrade and its financing are in, versus what they pay today. Where the installment outweighs savings early in the loan, show it honestly (e.g. near cost-neutral now, €X/month saved once paid off).

## What makes the number credible

- **Savings certainty** — local irradiance, the dynamic tariff, applicable subsidies, and self-consumption ratio
- **Household fit** — current spend across electricity, heating, and mobility determines how much output is genuinely displaced spend vs. low-value feed-in

## The three saving buckets

- **Electricity** — solar self-consumption + battery charging cheap / discharging expensive on the dynamic tariff
- **Heating** — switching from oil/gas to a heat pump swaps fuel spend for (partly self-generated) electricity
- **Mobility** — switching from petrol to EV, swapping fuel spend for cheap off-peak charging

## Up-sell requirement

From minimal inputs, the tool must spot the obvious next step and quantify it — e.g. *"still on oil heating? A heat pump saves you €X/month"* — always framed back to the financing-anchored monthly saving, so a bigger upgrade can actually increase what the household saves each month.

## AI angle (core)

An LLM advisor that takes minimal input, models the savings, picks the strongest upgrade path, and explains in plain language why this configuration lands the biggest monthly saving — copy an installer could paste straight into a customer proposal.
