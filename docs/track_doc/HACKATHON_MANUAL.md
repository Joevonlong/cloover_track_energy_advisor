# {Tech: Europe} Energy x AI Hackathon Manual 

> 

**>5€ Price Pool distributed across cash, hardware & credits**

## Important Links:

Discord Server - [https://discord.gg/brSqTjJVdh](https://discord.gg/brSqTjJVdh)
Project Submission Form - TBA

Wifi - Reonic 
Password - s0larh4ckers

## Agenda

### **Saturday**

10:00 - Door’s Open & Networking
10:30 - Opening & Matchmaking
12:30 - Lunch
18:30 - Dinner

### **Sunday**

12:30 - Lunch
**14:00 - Competition Opt-In Deadline**
15:00 - Announcement of Finalists
15:15 - Finalist Pitches
16:30 - Award Ceremony

## **Competition Rules & Submission Guidelines**

To compete in the hackathon and have your project considered by the jury, all participants must adhere to the following rules and submission requirements. Failure to meet these guidelines may result in disqualification.

---

## **Submission Requirements**

To qualify for the final judging, you must
  - **Submit your project by Sunday at 14:00**
  - **Be a team of max. 5 people**
  - **Have created your project newly at this hackathon** (boilerplates are allowed)

### What needs to be submitted

**Project Presentation**
  - Record a **2-minute video demo** of your project (using Loom or equivalent platform)
  - Your presentation must include:
    - Detailed explanation of your solution
    - Demonstration of key features with a live walkthrough
**Open Source Repository**
  - Provide a **public GitHub repository** containing your project's source code
  - Your repository must include:
    - Comprehensive **README** with setup and installation instructions
    - Clear documentation of all APIs, frameworks, and tools utilized
    - Sufficient technical documentation to enable thorough jury evaluation

---

## **Competition Mode**

Our hackathon features a** two-stage competition format**, culminating in a **live final presentation** event.

### Stage 1: Pre-Selection

  - Build anything aligned with your creative vision - complete freedom of topic choice
  - **4**** finalist teams (4  Track Winner)** will advance to the Finalist Stage
  - Judging criteria: creativity, technical complexity, with bonus points for effective use of partner technologies

### Stage 2: Finalist Stage

  - All finalists will showcase their projects **live before the jury and audience**
  - Each team delivers a **5-minute presentation**
  - After all presentations, the jury will select the **top 3 winners**
  - These top 1 teams will be awarded the Finalist Stage Prizes

## Hackathon Tracks, Side Challenges & Prizes

## Tracks

### [Reonic](https://reonic.com/de-de/) – AI-Powered Marketing to Enable Renewable Installers

**🏆 Track Prize: Reonic Car package + AirPods **
  - Challenge
**Background**
Solar installers spend time crafting personalized pitches to close sales, but they often lose momentum after sending the initial quote. Homeowners hesitate, get distracted, or receive competing offers. The gap between “quote sent” and “contract signed” is where deals die.**The opportunity:** Use AI to auto-generate personalized marketing sequences that keep prospects engaged, address their specific hesitations, reinforce ROI in *their* language, and create just enough urgency to push them over the line—without being pushy.Different customer types need different approaches:
    - A **family** wants reassurance and peace of mind (“predictable bills, no surprises”)
    - An **investor** wants hard ROI numbers and comparisons (“13% annual return vs. stock market”)
    - An **environmentalist** wants impact narrative (“offset 150 tons of CO₂ over 25 years”)
    - A **skeptic** needs objection handling (“yes, panels work in winter too”)
**The Challenge**
Build a system that takes a homeowner’s profile and quote data, then **generates a strategic communication chain** designed to move them from “quote received” to “contract signed.”The challenge is not just to generate emails—it’s to suggest a **coherent marketing approach** with reasoning, timing, and flexibility. Think of it as a persuasion strategy that an installer can understand, trust, and iterate on.Core Problem
    - Homeowners hesitate after receiving quotes
    - Installers lack time to personalize follow-up at scale
    - Generic templates don’t move the needle
    - There’s no clear “why this, at this time, in this tone?”
**Your job**: Help installers understand *why* a certain communication strategy makes sense for *this customer*, and give them tools to execute and adapt it.What You’ll BuildA working prototype that takes customer + quote data as input and outputs a **communication strategy** that’s:
    1. **Strategically sound** – based on the customer’s actual motivations and concerns
    1. **Visually compelling** – something an installer would want to show their sales manager (or the customer)
    1. **Actionable & (bonus points) iterative** – not just “send this email,” but “here’s the approach, here’s why, and here’s how you can adjust it”
    1. **Multi-channel aware (bonus points)** – emails are one option, but so are SMS, calls, video messages, proposals, or other creative touches
That’s it. No massive documentation needed. Impress us with what you build, not what you write about building it.Bonus Points 🚀
    - **Multi-channel smarts** – suggests not just emails, but calls, SMS, video, or creative touches
    - **Iteration built-in** – the installer can adjust strategy on the fly
    - **Predictive insights** – warns “this customer might ghost” or “they’re ready to close now”
    - **A/B testing framework** – suggests how to test different messaging
    - **Beautiful UX** – something you’d be proud to show a customer
    - **Localization** – works for different regions, languages, market conditions
    - **Something unexpected** – an idea we didn’t think of that actually works
Good luck! 🌞

### [Cloover](https://www.cloover.com/) – **The household energy transition planner**

**🏆 Track Prize: AirPods and Powerbank per team member**
  - Challenge
**The problem**
Today a customer is sold an energy installation with financing option first, then an energy tariff bolted on afterwards. That's backwards. Build a single checkout / advisor that sells the *outcome*: a full home-energy upgrade — solar, battery, heat pump, EV charger — plus its financing and a dynamic tariff, presented as **one product with one clear monthly number**.That number — the **North Star** — is the **monthly saving**: how much lower the household's total monthly outgoings are once the upgrade and its financing are in, versus what they pay today. You still need to know what they spend now and what the installment is — that's the input — but the figure you put front and centre is what they *save* per month. (Where the installment outweighs the savings early in the loan, show it honestly — e.g. near cost-neutral now, €X/month saved once it's paid off.)The hard part is producing a *credible* savings number. That means modelling all aspects, and the right answer changes per household:
    - **Savings certainty** — local irradiance, the dynamic tariff, applicable subsidies, and self-consumption ratio
    - **Household fit** — current spend across electricity, heating, and mobility determines how much of the output is genuinely displaced spend vs. low-value feed-in.
So the tool should compare upgrade scenarios (solar only / PV + battery / + heat pump / + EV charger) against the household's *current* total energy + heating + mobility spend, and find the configuration that lands the biggest monthly saving. Those savings span three buckets:
    - **Electricity** — solar self-consumption, plus a battery charging cheap / discharging expensive on the dynamic tariff.
    - **Heating** — a household on oil or gas; switching to a heat pump swaps fuel spend for (partly self-generated) electricity.
    - **Mobility** — switching from a petrol car to an EV, swapping fuel spend for cheap off-peak charging.
**Up-sell is part of the challenge.** From minimal inputs, the tool should spot the obvious next step and quantify it — e.g. "still on oil heating? A heat pump saves you €X/month" — always framed back to the financing-anchored monthly saving, so a bigger upgrade can actually *increase* what the household saves each month.**AI angle (core):** an LLM advisor that takes minimal input, models the savings, picks the strongest upgrade path, and explains in plain language why this configuration lands the biggest monthly saving — copy an installer could paste straight into a customer proposal. Potentially zip-code-level grid fees for accurate price estimates.

### [Enpal](https://www.enpal.com/?utm_source=luma) – The Smart Energy Companion

**🏆 Track Prize: AI voice recording device (worth 200€) **
  - Challenge
**The context**
Enpal is Europe's largest renewable energy company, offering solar, batteries, heat pumps, and EV charging, installed in hundreds of thousands of homes. But once a home goes electric, the homeowner inherits a new kind of complexity: a solar system producing power, a battery charging and discharging, a heat pump heating the house, an EV pulling load, a dynamic tariff that changes by the hour, and a contract full of terms nobody reads. The data exists, but it's scattered across apps, portals, and PDFs, in a language only an energy engineer could love.
**The problem**
The average homeowner has no clear answer to simple questions: *Am I saving money? Should I run the dishwasher now or at 3pm? Why was my bill higher this month? Is my contract still a good deal?* The information is technically available but practically invisible. As Europe electrifies millions of homes, this comprehension gap becomes the single biggest barrier to people actually benefiting from (and trusting) their energy transition.
**The challenge**
Build an AI-powered web or mobile app that turns a household's messy energy reality into one clear, intuitive view. Pull together the things that today live in separate silos (contract and tariff terms, solar production, battery state, heat-pump and EV consumption, grid import/export) and use AI to make them understandable and *actionable* in real time. You're free to architect the AI layer however you like, including exposing the household data through an MCP server that an LLM can reason over.
The winning solution doesn't just visualize data. It explains it in plain language, anticipates the user's questions, and nudges them toward smarter decisions: when to use energy, how much they're saving, what their bill will likely be, and where money is being left on the table.
**What you'll build (suggested scope)**
A working prototype that demonstrates some combination of:
    - **A unified energy view:** one screen that brings together production, consumption, storage, and grid flows in a way a non-expert immediately understands.
    - **A conversational layer:** let the user ask "why is my bill high?" or "should I charge the car now?" and get a clear, grounded answer.
    - **Tariff intelligence:** parse the tariff and surface what actually matters (rates, dynamic pricing windows, savings vs. a standard tariff).
    - **Proactive insights & nudges:** bill forecasting, anomaly detection ("your heat pump used 40% more this week"), and timing recommendations tied to price or solar surplus.
You don't need to build all of it. Depth on one compelling experience beats a shallow version of everything.
**What we'll provide**
Sample/synthetic household energy data (production, consumption, tariff structures) and example contract terms so you can build against realistic inputs. *(Adjust to whatever you'll actually hand out.)*
**How we'll judge it**
    - **Clarity & UX:** would a real, non-technical homeowner instantly get it?
    - **Smart use of AI:** does the AI add genuine understanding, not just a chatbot bolted on?
    - **Impact:** does it help the user save money, energy, or carbon, or make a better decision?
    - **Technical execution:** does the prototype actually work end to end?
    - **Originality:** a fresh take on making energy effortless.

### [Nomos](https://www.nomos.energy/) – Build the leading voice agent for the energy market / The leading voice agent for the energy market

**🏆 Track Prize:** 200€ Airbnb voucher per team member
  - Challenge
more info : ‣
**About**
At Nomos, we're building a full-stack, AI-native power company from first principles, with one mission: to create energy abundance in Europe. We develop new energy products together with Europe's leading technology companies and installers, and we embed energy as a cost-saving feature inside the things people already buy: electric vehicles, heat pumps, battery storage and more.**The problem**To supply even a single household, we exchange a constant stream of regulated messages with the rest of the German energy market: grid operators, metering operators, other suppliers. We've already made ourselves autonomous in the two big layers, the machine-to-machine one (EDIFACT) and the written one (email).But the market isn't ready for full automation yet. Sometimes a message bounces with a cryptic error, or a grid operator simply never replies, and the rules push the case off the automated rails and onto a phone call. The only thing that clears it then is a human: pick up the phone, get to the right desk, explain the case, and push until there's an answer.
**Your challenge**
Build the AI voice agent that makes that call, and bridges the gap until the market itself can support full automation.We essentially put emphasis on an agent that Helga, 54, sitting in a grid operator's back office, is happy to talk to and doesn't hang up on in the first ten seconds. It sounds soft, but it's the whole game. We mean an agent that feels warm and genuinely human, one that can slow down and read a long number back cleanly, one digit at a time. That last part is where most voice agents fall apart.It also has to clear the case, not just hold a nice conversation. The agent takes a structured case file, places the call, and runs the whole German conversation on its own, with no human steering it. When it hangs up, it pulls the key facts out, stores them as clean structured data, leaves a short note in plain language (exactly what our back office would write down), and triggers the right next action. Two examples:
    - It gets the market location ID from Helga, writes it into our system, and triggers the next step in the sign-up process
    - It learns the meter is no longer active, since it was only ever there while the house was being built, flags that we need to reach out to the customer, and triggers our mail agent.
We'll give you proprietary resources about our industry and our own processes, everything you need to build the leading voice agent for the energy market. Beyond that, we're genuinely curious how you'll solve it.

## Side Challenge

### Best use of [Eleven Labs](https://elevenlabs.io/)

**To compete in this challenge you have to:**
    - Use [Eleven Labs](https://elevenlabs.io/)** **in your project
    - Confirm in your project submission that you used it
**🏆 The best use of ****[Eleven Labs](https://elevenlabs.io/)**** will win:**
    - 6 months of their Scale tier ($1980 value/team member)

## Finalist Stage Prizes

### 1st Place

  - 🤑 4k€ cash 🤑
  - 3 months of Eleven Labs Pro tier (297 value/team member)

## Resources 

### Infrastructure Partners

  - **OpenAI**
platform.openai.com/p/H3SN8YXXU4YWMENQ
  - **Eleven Labs**
1 free month of the creator tier
    1. Join the Discord server: [https://discord.com/invite/VnBvbbcdEC](https://discord.com/invite/VnBvbbcdEC)
    1. Gain access to the #│coupon-codes channel
    1. Click "Start Redemption"
    1. Select the event and fill out the form using the email used for registration
    1. The bot sends the unique coupon code
[Video Tutorial](https://youtu.be/S143_JtCtV8)

## FAQ

  - **Will there be any food available in the venue for free or to buy?**
Food (lunch and dinner) is provided for all participants free of charge. Snacks and drinks will also be available throughout the hackathon.
  - **Do I need to be in a team, or can I participate solo?**
You can join as a solo hacker or form a team of up to **5 people. **Team matchmaking will happen on Saturday after the opening session.
  - **What exactly needs to be submitted?**
    - A **2-minute video demo** (e.g., Loom)
    - A **GitHub repository (public!)** with source code, README, documentation, and setup instructions.
  - **Where do I find help and announcements during the hackathon?**
Join the **Discord server**: [https://discord.gg/cMxebncsh](https://discord.gg/cMxebncsh) – it’s the main place for updates, team finding, and support.
  - **Can i stay overnight ?**
Yes, but after 10pm you can only exit the office. There are balconies available for smoking