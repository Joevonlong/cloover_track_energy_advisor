# Heimwende Energy Advisor

> **Berlin Energy AI Hackathon 2026** · Cloover Challenge

An AI-powered home energy transition advisor that calculates one clear number: **how much a household saves per month** after a full home-energy upgrade (solar, battery, heat pump, EV charger) combined with financing and a dynamic tariff — presented as a single product.

---

## The Problem

Today, customers are sold an energy installation first and a tariff bolted on afterwards. That's backwards.

This tool builds a single checkout / advisor that sells the *outcome*: a complete home-energy upgrade with financing and a dynamic tariff, front-and-centre as one monthly saving number.

## North Star Metric

**Monthly saving** = what the household pays today − (upgrade installment + new energy costs)

Where the installment outweighs early savings, we show it honestly — e.g. *"near cost-neutral now, €X/month saved once it's paid off."*

## Upgrade Scenarios Modelled

| Configuration | Savings Buckets |
|---|---|
| Solar only | Electricity (self-consumption) |
| PV + Battery | Electricity + dynamic tariff arbitrage |
| PV + Battery + Heat Pump | + Heating (replaces oil/gas) |
| PV + Battery + Heat Pump + EV Charger | + Mobility (replaces petrol) |

The advisor picks the configuration that delivers the **largest monthly saving** per household profile.

## How It Works

1. **Minimal input** — household size, current electricity/heating/mobility spend, postcode
2. **AI modelling** — LLM advisor models savings across all scenarios using local irradiance, grid fees, applicable subsidies, and self-consumption ratios
3. **Clear output** — ranked upgrade paths with plain-language explanation; copy an installer could paste straight into a customer proposal
4. **Up-sell framing** — spots the obvious next step and quantifies it (e.g. *"still on oil heating? A heat pump saves you €X/month"*)

## Tech Stack

> _To be defined during the hackathon_

## Getting Started

```bash
# clone
git clone git@github.com:Joevonlong/heimwende-energy-advisor.git
cd heimwende-energy-advisor

# install & run (update once stack is chosen)
```

## Team

Built at the **Berlin Energy AI Hackathon — June 20, 2026** for the [Cloover](https://cloover.com) challenge track.

Prize: AirPods + Powerbank per team member 🏆
