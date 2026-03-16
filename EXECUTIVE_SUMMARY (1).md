# F.I.R.E. for Effect — Project Summary

## Problem

Military compensation is unusually complex. A service member’s income is made up of several different components including base pay, housing allowance (BAH), food allowance (BAS), special pays, and eventually a pension. Each of these is governed by different pay tables and eligibility rules.

Because of this, it is surprisingly difficult for service members to answer basic financial questions such as:

- How much do I actually earn?
- How much should I be saving for retirement?
- Where is my money going each month?

Existing calculators typically answer only one of these questions at a time and are rarely tailored to military pay structures. This project aimed to build a single tool that helps service members quickly understand their income, spending, and retirement planning in one place.

---

## Solution

We developed **F.I.R.E. for Effect**, an interactive Streamlit application designed to help service members understand their financial situation and plan for retirement.

The application allows users to enter basic information such as rank, years of service, location, retirement goals, and investment preferences. Using that information, the system calculates projected income, required savings rates, and a breakdown of monthly spending.

The goal is to give service members a clear financial starting point and help them move toward a financially stable future.

---

## Data Sources

All military compensation data is stored in a structured file called `military_data.json`. This file contains three main datasets:

### Base Pay
Official Department of Defense pay tables organized by **rank and years of service**, allowing the application to estimate income progression across a military career.

### Basic Allowance for Housing (BAH)
BAH rates vary based on **location, rank, and dependent status**. These values come from DoD housing allowance tables.

### ZIP Code to Housing Area Mapping
Because BAH is determined by **Military Housing Areas (MHA)** rather than ZIP codes, we created a mapping file that links user ZIP codes to the correct housing area so the application can retrieve the appropriate BAH rate.

Investment assumptions for Thrift Savings Plan (TSP) funds were derived from historical return and volatility estimates and used in both retirement projections and simulations.

---

## Computational Components

The application uses three primary computational engines.

### Savings Rate Solver

The core function of the tool is determining the **savings rate required to reach a retirement goal**.

The model projects a service member’s income over time using promotion timelines and pay tables. It then simulates monthly contributions to retirement accounts and investment growth until the savings reach the target amount needed to support the user’s retirement income goal.

The system iteratively adjusts the savings rate until it finds the rate that reaches the desired retirement balance.

---

### Monte Carlo Simulation

Investment returns are uncertain, so we added a **Monte Carlo simulation** to test retirement outcomes under different market scenarios.

The simulation generates **1,000 potential market paths** using statistical estimates of investment returns and volatility. It then measures how often the user still reaches their retirement goal.

This produces a **probability of success**, which helps users understand the risk associated with their savings strategy.

---

### Budget Flow Visualization

To help users understand spending, we built a **Sankey diagram** that shows how income flows through a monthly budget.

The diagram displays:

- Gross income
- Taxes
- Take-home pay
- Spending categories
- Investments
- Remaining surplus

This visual format helps users quickly identify where their money is going and how changes in spending affect their savings.

---

## Visualizations

The application includes several interactive charts that help users explore their financial situation:

- **Compensation Projection:** Shows how military income grows over time with promotions and housing allowances.
- **Investment Growth Explorer:** Displays projected growth of TSP investments.
- **Monte Carlo Simulation Chart:** Shows the range of possible retirement outcomes under market uncertainty.
- **Savings Rate Explorer:** Allows users to see how different savings rates affect retirement timelines.
- **Monthly Cash Flow Diagram:** Visualizes how income is allocated across taxes, spending, and investments.

These visual tools make complex financial information easier to understand and explore.

---

## Key Findings

Several insights emerged from building and testing the tool:

- Many service members need to save **significantly more than the 5% required to receive the full TSP match** to meet retirement goals.
- **Early investment years matter the most**, as market performance early in a career has a large impact on long-term outcomes.
- **Housing allowances can represent a large share of total compensation**, especially in high cost-of-living areas.

These findings reinforce the importance of early financial planning and a clear understanding of military compensation.

---

## Future Improvements

Several improvements could expand the tool’s usefulness:

- Automatically updating retirement contribution limits each year
- Modeling retirement spending during the **drawdown phase**
- Adding a **rent vs. buy calculator** tailored to frequent military relocations
- Improving the update process for housing allowance data

These additions would further improve the realism and usefulness of the tool.

---

## Team Contributions

**Brandon** developed the Sankey budget visualization and served as the liaison between the Fortress financial tool and the FIRE for Effect application.

**Shaun** built the Monte Carlo simulation engine and worked on integrating TSP data and generating proxy investment return data.

**Ian** developed the savings rate solver and built out the Streamlit application, integrating the different components into a single interactive platform.
