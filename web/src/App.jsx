import { useState } from 'react'
import './App.css'
import { postJson } from './api'

const SCREENS = ['Start', 'Checklist', 'Pay', 'Budget', 'Retirement', 'Plan']

const DEFAULT_DEBT_RATES = {
  credit_card: 20,
  personal_loan: 13,
  auto_loan: 8,
  student_loan: 6,
  other: 12,
}

const initialPlan = {
  readiness: {
    emergency1000: '',
    employerMatch: '',
    highInterestDebt: 'no',
    debtType: 'credit_card',
    debtAmount: '',
    debtApr: '',
    debtAprKnown: 'yes',
    retirementSavingsMonthly: '',
    savingMoreRetirement: '',
    otherGoals: '',
  },
  income: {
    payPattern: 'twice_monthly',
    midMonth: '',
    endMonth: '',
    biweeklyNet: '',
    variableLow: '',
    variableTypical: '',
    variableHigh: '',
    additionalMonthly: '',
    rank: 'E-5',
    tis: '6',
    zip: '28310',
    dependents: true,
    militaryEstimate: null,
  },
  budget: {
    housing: '',
    groceries: '',
    utilities: '',
    incomeEarning: '',
    transportation: '',
    nonEssentialBills: '',
    debtMinimums: '',
    eatingOut: '',
    travel: '',
    pets: '',
    subscriptions: '',
    other: '',
    emergencySavings: '',
  },
  retirement: {
    currentAge: '30',
    retireAge: '60',
    currentTsp: '0',
    targetNestEgg: '1000000',
    currentMonthlySavings: '',
  },
  results: {
    budget: null,
    budgetSource: '',
    retirement: null,
    retirementError: '',
  },
}

function App() {
  const [screenIndex, setScreenIndex] = useState(0)
  const [plan, setPlan] = useState(initialPlan)
  const [isWorking, setIsWorking] = useState(false)
  const [apiMessage, setApiMessage] = useState('')

  const updateSection = (section, updates) => {
    setPlan((current) => ({
      ...current,
      [section]: {
        ...current[section],
        ...updates,
      },
    }))
  }

  const updateResults = (updates) => {
    setPlan((current) => ({
      ...current,
      results: {
        ...current.results,
        ...updates,
      },
    }))
  }

  const goNext = () => setScreenIndex((current) => Math.min(current + 1, SCREENS.length - 1))
  const goBack = () => setScreenIndex((current) => Math.max(current - 1, 0))

  const estimateMilitaryPay = async () => {
    setIsWorking(true)
    setApiMessage('')
    try {
      const response = await postJson('/income/calculate', {
        rank: plan.income.rank,
        tis: number(plan.income.tis),
        has_dependents: plan.income.dependents,
        zip_code: plan.income.zip,
        is_oconus: false,
        cola: 0,
        special_pay: 0,
      })
      updateSection('income', { militaryEstimate: response })
      setApiMessage('Military pay estimate loaded.')
    } catch (error) {
      setApiMessage(`API estimate unavailable: ${error.message}`)
    } finally {
      setIsWorking(false)
    }
  }

  const calculateBudget = async () => {
    const payload = buildBudgetPayload(plan)
    setIsWorking(true)
    setApiMessage('')
    try {
      const response = await postJson('/budget/summary', payload)
      updateResults({ budget: response, budgetSource: 'api' })
      setApiMessage('Budget summary calculated through the API.')
      return response
    } catch (error) {
      const fallback = summarizeBudgetLocally(payload)
      updateResults({ budget: fallback, budgetSource: 'local' })
      setApiMessage(`Using local budget math until the API is running: ${error.message}`)
      return fallback
    } finally {
      setIsWorking(false)
    }
  }

  const calculateRetirement = async () => {
    const budget = plan.results.budget || summarizeBudgetLocally(buildBudgetPayload(plan))
    const monthlyIncome = Math.max(1, budget.take_home_monthly)
    const months = Math.max(
      12,
      Math.round((number(plan.retirement.retireAge) - number(plan.retirement.currentAge)) * 12),
    )
    const monthlyContribution =
      number(plan.retirement.currentMonthlySavings) || number(plan.readiness.retirementSavingsMonthly)

    setIsWorking(true)
    setApiMessage('')

    try {
      const incomeSchedule = Array.from({ length: months }, () => monthlyIncome)
      const savings = await postJson('/retirement/solve-savings-rate', {
        target_nest_egg: number(plan.retirement.targetNestEgg),
        current_tsp: number(plan.retirement.currentTsp),
        base_pay_schedule: [],
        civilian_monthly: monthlyIncome,
        mil_months: 0,
        total_months: months,
        allocation: { L: 1 },
        inflation_rate: 0.025,
        prebuilt_income_schedule: incomeSchedule,
      })

      const monteCarlo = await postJson('/retirement/monte-carlo', {
        current_age: number(plan.retirement.currentAge),
        retire_age: number(plan.retirement.retireAge),
        initial_balance: number(plan.retirement.currentTsp),
        monthly_contribution: monthlyContribution || savings.first_month_contribution,
        l_fund_weight: 1,
        manual_allocation: {},
        inflation_rate: 0.025,
        trials: 1000,
        target_balance: number(plan.retirement.targetNestEgg),
        seed: 42,
      })

      updateResults({
        retirement: { savings, monteCarlo },
        retirementError: '',
      })
      setApiMessage('Retirement estimate calculated through the API.')
      goNext()
    } catch (error) {
      updateResults({ retirementError: error.message })
      setApiMessage(`Retirement API unavailable: ${error.message}`)
      goNext()
    } finally {
      setIsWorking(false)
    }
  }

  const continueFromBudget = async () => {
    await calculateBudget()
    goNext()
  }

  const progress = Math.round(((screenIndex + 1) / SCREENS.length) * 100)
  const commonProps = {
    plan,
    updateSection,
    goBack,
    goNext,
    isWorking,
    apiMessage,
  }

  return (
    <main className="app-shell">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />
      <Progress current={screenIndex} progress={progress} />

      {screenIndex === 0 && <WelcomeScreen {...commonProps} />}
      {screenIndex === 1 && <ChecklistScreen {...commonProps} />}
      {screenIndex === 2 && (
        <PayScreen {...commonProps} estimateMilitaryPay={estimateMilitaryPay} />
      )}
      {screenIndex === 3 && (
        <BudgetScreen {...commonProps} calculateBudget={calculateBudget} continueFromBudget={continueFromBudget} />
      )}
      {screenIndex === 4 && (
        <RetirementScreen {...commonProps} calculateRetirement={calculateRetirement} />
      )}
      {screenIndex === 5 && <PlanScreen {...commonProps} calculateBudget={calculateBudget} />}
      <footer className="app-footer">
        FIRE for Effect is for educational planning only. It is not financial, legal, or tax advice.
      </footer>
    </main>
  )
}

function Progress({ current, progress }) {
  return (
    <header className="progress-wrap" aria-label="Progress">
      <div className="progress-topline">
        <span>{SCREENS[current]}</span>
        <span>{progress}%</span>
      </div>
      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${progress}%` }} />
      </div>
    </header>
  )
}

function Screen({ eyebrow, title, children, footer }) {
  return (
    <section className="screen-card">
      <p className="eyebrow">{eyebrow}</p>
      <h1>{title}</h1>
      {children}
      {footer && <div className="footer-actions">{footer}</div>}
    </section>
  )
}

function WelcomeScreen({ goNext }) {
  return (
    <Screen
      eyebrow="FIRE for Effect"
      title="Build the next move from your actual numbers."
      footer={<PrimaryButton onClick={goNext}>Start checklist</PrimaryButton>}
    >
      <p className="lede">
        We will identify where you are in the financial readiness sequence, enter the pay that actually hits your bank
        account, then turn the budget into a short action plan.
      </p>
      <div className="hero-panel">
        <div>
          <span className="mini-label">MVP flow</span>
          <strong>Checklist first</strong>
          <p>No optional navigation, no save code, no fake resume path.</p>
        </div>
        <div>
          <span className="mini-label">Output</span>
          <strong>Next gate</strong>
          <p>A plain recommendation based on the income and spending you enter.</p>
        </div>
      </div>
    </Screen>
  )
}

function ChecklistScreen({ plan, updateSection, goBack, goNext }) {
  const readiness = plan.readiness
  const debtRate = getDebtRate(readiness)
  const monthlyInterest = (number(readiness.debtAmount) * (debtRate / 100)) / 12

  return (
    <Screen
      eyebrow="Step 1"
      title="Where are you right now?"
      footer={<NavButtons onBack={goBack} onNext={goNext} nextLabel="Continue to pay" />}
    >
      <ChoiceGroup
        label="Could you cover a $1,000 emergency without putting it on a credit card and paying it off over months?"
        value={readiness.emergency1000}
        onChange={(value) => updateSection('readiness', { emergency1000: value })}
        options={[
          ['yes', 'Yes'],
          ['no', 'Not yet'],
        ]}
      />

      <ChoiceGroup
        label="Are you getting the full employer match available to you?"
        value={readiness.employerMatch}
        onChange={(value) => updateSection('readiness', { employerMatch: value })}
        options={[
          ['yes', 'Yes'],
          ['no', 'Not yet'],
          ['na', 'Not available'],
        ]}
      />

      <ChoiceGroup
        label="Do you have high-interest debt?"
        value={readiness.highInterestDebt}
        onChange={(value) => updateSection('readiness', { highInterestDebt: value })}
        options={[
          ['no', 'No'],
          ['yes', 'Yes'],
        ]}
      />

      {readiness.highInterestDebt === 'yes' && (
        <div className="field-grid">
          <label>
            Debt type
            <select
              value={readiness.debtType}
              onChange={(event) => updateSection('readiness', { debtType: event.target.value })}
            >
              <option value="credit_card">Credit card</option>
              <option value="personal_loan">Personal loan</option>
              <option value="auto_loan">Auto loan</option>
              <option value="student_loan">Student loan</option>
              <option value="other">Other</option>
            </select>
          </label>
          <MoneyField
            label="Balance"
            value={readiness.debtAmount}
            onChange={(value) => updateSection('readiness', { debtAmount: value })}
          />
          <MoneyField
            label="APR if you know it"
            value={readiness.debtApr}
            suffix="%"
            onChange={(value) => updateSection('readiness', { debtApr: value })}
          />
          <div className="callout">
            <strong>{formatCurrency(monthlyInterest)} per month</strong>
            <span>
              Estimated interest drag at {debtRate.toFixed(1)}% APR. If APR is blank, the app uses a reasonable default
              for the debt type.
            </span>
          </div>
        </div>
      )}

      <MoneyField
        label="How much are you currently saving for retirement each month?"
        value={readiness.retirementSavingsMonthly}
        onChange={(value) => updateSection('readiness', { retirementSavingsMonthly: value })}
      />
    </Screen>
  )
}

function PayScreen({ plan, updateSection, goBack, goNext, estimateMilitaryPay, isWorking, apiMessage }) {
  const income = plan.income
  const monthlyIncome = estimateMonthlyIncome(income)

  return (
    <Screen
      eyebrow="Step 2"
      title="Enter the pay that hits your bank."
      footer={<NavButtons onBack={goBack} onNext={goNext} nextLabel="Continue to budget" />}
    >
      <ChoiceGroup
        label="How does your main pay arrive?"
        value={income.payPattern}
        onChange={(value) => updateSection('income', { payPattern: value })}
        options={[
          ['twice_monthly', 'Mid-month and end-month'],
          ['biweekly', 'Every two weeks'],
          ['variable', 'Variable or estimated'],
        ]}
      />

      {income.payPattern === 'twice_monthly' && (
        <div className="field-grid two">
          <MoneyField
            label="Mid-month deposit"
            value={income.midMonth}
            onChange={(value) => updateSection('income', { midMonth: value })}
          />
          <MoneyField
            label="End-month deposit"
            value={income.endMonth}
            onChange={(value) => updateSection('income', { endMonth: value })}
          />
        </div>
      )}

      {income.payPattern === 'biweekly' && (
        <MoneyField
          label="Net amount per paycheck"
          value={income.biweeklyNet}
          onChange={(value) => updateSection('income', { biweeklyNet: value })}
        />
      )}

      {income.payPattern === 'variable' && (
        <div className="field-grid three">
          <MoneyField
            label="Tough month"
            value={income.variableLow}
            onChange={(value) => updateSection('income', { variableLow: value })}
          />
          <MoneyField
            label="Typical month"
            value={income.variableTypical}
            onChange={(value) => updateSection('income', { variableTypical: value })}
          />
          <MoneyField
            label="Good month"
            value={income.variableHigh}
            onChange={(value) => updateSection('income', { variableHigh: value })}
          />
        </div>
      )}

      <MoneyField
        label="Additional monthly income"
        value={income.additionalMonthly}
        onChange={(value) => updateSection('income', { additionalMonthly: value })}
      />

      <div className="metric-ribbon">
        <span>Estimated monthly take-home</span>
        <strong>{formatCurrency(monthlyIncome)}</strong>
      </div>

      <details className="details-card">
        <summary>Optional military pay estimate</summary>
        <div className="field-grid three">
          <label>
            Rank
            <select value={income.rank} onChange={(event) => updateSection('income', { rank: event.target.value })}>
              {['E-1', 'E-2', 'E-3', 'E-4', 'E-5', 'E-6', 'E-7', 'E-8', 'E-9', 'O-1', 'O-2', 'O-3', 'O-4', 'O-5'].map(
                (rank) => (
                  <option key={rank} value={rank}>
                    {rank}
                  </option>
                ),
              )}
            </select>
          </label>
          <MoneyField label="TIS" value={income.tis} prefix="" onChange={(value) => updateSection('income', { tis: value })} />
          <label>
            ZIP
            <input value={income.zip} onChange={(event) => updateSection('income', { zip: event.target.value })} />
          </label>
        </div>
        <ChoiceGroup
          label="Dependents?"
          value={income.dependents ? 'yes' : 'no'}
          onChange={(value) => updateSection('income', { dependents: value === 'yes' })}
          options={[
            ['yes', 'Yes'],
            ['no', 'No'],
          ]}
        />
        <PrimaryButton onClick={estimateMilitaryPay} disabled={isWorking}>
          Estimate gross military comp
        </PrimaryButton>
        {income.militaryEstimate && (
          <div className="estimate-grid">
            <Metric label="Base pay" value={formatCurrency(income.militaryEstimate.base_pay)} />
            <Metric label={income.militaryEstimate.housing_label} value={formatCurrency(income.militaryEstimate.housing_total)} />
            <Metric label="BAS" value={formatCurrency(income.militaryEstimate.bas)} />
          </div>
        )}
        {apiMessage && <p className="api-note">{apiMessage}</p>}
      </details>
    </Screen>
  )
}

function BudgetScreen({ plan, updateSection, goBack, calculateBudget, continueFromBudget, isWorking, apiMessage }) {
  const budget = plan.budget
  const budgetResult = plan.results.budget
  const debt = plan.readiness.highInterestDebt === 'yes'

  return (
    <Screen
      eyebrow="Step 3"
      title="Map the monthly budget."
      footer={
        <NavButtons
          onBack={goBack}
          onNext={continueFromBudget}
          nextLabel={isWorking ? 'Calculating...' : 'Continue to retirement'}
          disabled={isWorking}
        />
      }
    >
      <div className="section-heading">
        <span>Fixed or required</span>
      </div>
      <div className="field-grid two">
        <MoneyField label="Rent or mortgage" value={budget.housing} onChange={(value) => updateSection('budget', { housing: value })} />
        <MoneyField label="Food and groceries" value={budget.groceries} onChange={(value) => updateSection('budget', { groceries: value })} />
        <MoneyField label="Utilities" value={budget.utilities} onChange={(value) => updateSection('budget', { utilities: value })} />
        <MoneyField
          label="Income-earning expenses"
          value={budget.incomeEarning}
          onChange={(value) => updateSection('budget', { incomeEarning: value })}
        />
        <MoneyField
          label="Transportation"
          value={budget.transportation}
          onChange={(value) => updateSection('budget', { transportation: value })}
        />
        <MoneyField
          label="Debt minimums"
          value={budget.debtMinimums}
          onChange={(value) => updateSection('budget', { debtMinimums: value })}
        />
      </div>

      {debt && (
        <div className="callout">
          <strong>Debt from screening: {formatCurrency(number(plan.readiness.debtAmount))}</strong>
          <span>Use the debt minimums field for required payments. The final plan will recommend extra payoff money separately.</span>
        </div>
      )}

      <div className="section-heading">
        <span>Planned saving</span>
      </div>
      <div className="field-grid two">
        <MoneyField
          label="Emergency fund savings"
          value={budget.emergencySavings}
          onChange={(value) => updateSection('budget', { emergencySavings: value })}
        />
        <MoneyField
          label="Retirement savings"
          value={plan.readiness.retirementSavingsMonthly}
          onChange={(value) => updateSection('readiness', { retirementSavingsMonthly: value })}
        />
      </div>

      <div className="section-heading">
        <span>Flexible and optional</span>
      </div>
      <div className="field-grid two">
        <MoneyField
          label="Non-essential bills"
          value={budget.nonEssentialBills}
          onChange={(value) => updateSection('budget', { nonEssentialBills: value })}
        />
        <MoneyField label="Eating out" value={budget.eatingOut} onChange={(value) => updateSection('budget', { eatingOut: value })} />
        <MoneyField label="Travel" value={budget.travel} onChange={(value) => updateSection('budget', { travel: value })} />
        <MoneyField label="Pets" value={budget.pets} onChange={(value) => updateSection('budget', { pets: value })} />
        <MoneyField
          label="Subscriptions"
          value={budget.subscriptions}
          onChange={(value) => updateSection('budget', { subscriptions: value })}
        />
        <MoneyField label="Other" value={budget.other} onChange={(value) => updateSection('budget', { other: value })} />
      </div>

      <div className="button-split">
        <SecondaryButton onClick={calculateBudget} disabled={isWorking}>
          {isWorking ? 'Checking...' : 'Preview monthly picture'}
        </SecondaryButton>
        {apiMessage && <p className="api-note">{apiMessage}</p>}
      </div>

      {budgetResult && <CashFlowPreview summary={budgetResult} />}
    </Screen>
  )
}

function RetirementScreen({ plan, updateSection, goBack, calculateRetirement, isWorking, apiMessage }) {
  const retirement = plan.retirement
  const budget = plan.results.budget || summarizeBudgetLocally(buildBudgetPayload(plan))
  const months = Math.max(12, Math.round((number(retirement.retireAge) - number(retirement.currentAge)) * 12))

  return (
    <Screen
      eyebrow="Step 4"
      title="Set the retirement target."
      footer={
        <NavButtons
          onBack={goBack}
          onNext={calculateRetirement}
          nextLabel={isWorking ? 'Calculating...' : 'Build my plan'}
          disabled={isWorking}
        />
      }
    >
      <p className="lede small">
        This uses the API to estimate the savings rate required for your target and runs a seeded Monte Carlo view.
      </p>
      <div className="field-grid two">
        <MoneyField label="Current age" prefix="" value={retirement.currentAge} onChange={(value) => updateSection('retirement', { currentAge: value })} />
        <MoneyField label="Target retirement age" prefix="" value={retirement.retireAge} onChange={(value) => updateSection('retirement', { retireAge: value })} />
        <MoneyField label="Current TSP/investments" value={retirement.currentTsp} onChange={(value) => updateSection('retirement', { currentTsp: value })} />
        <MoneyField label="Target nest egg" value={retirement.targetNestEgg} onChange={(value) => updateSection('retirement', { targetNestEgg: value })} />
        <MoneyField
          label="Current monthly retirement saving"
          value={retirement.currentMonthlySavings || plan.readiness.retirementSavingsMonthly}
          onChange={(value) => updateSection('retirement', { currentMonthlySavings: value })}
        />
      </div>

      <div className="estimate-grid">
        <Metric label="Monthly income basis" value={formatCurrency(budget.take_home_monthly)} />
        <Metric label="Months to target" value={months.toLocaleString()} />
      </div>
      {apiMessage && <p className="api-note">{apiMessage}</p>}
    </Screen>
  )
}

function PlanScreen({ plan, goBack, calculateBudget, isWorking, apiMessage }) {
  const budget = plan.results.budget || summarizeBudgetLocally(buildBudgetPayload(plan))
  const recommendations = buildRecommendations(plan, budget)
  const retirement = plan.results.retirement

  return (
    <Screen
      eyebrow="Step 5"
      title="Your next move."
      footer={<NavButtons onBack={goBack} onNext={calculateBudget} nextLabel={isWorking ? 'Refreshing...' : 'Refresh budget'} disabled={isWorking} />}
    >
      <div className="priority-card">
        <span className="mini-label">Current gate</span>
        <h2>{recommendations.gate}</h2>
        <p>{recommendations.action}</p>
      </div>

      <div className="recommendation-grid">
        {recommendations.cards.map((card) => (
          <div className="recommendation-card" key={card.label}>
            <span>{card.label}</span>
            <strong>{card.value}</strong>
            <p>{card.detail}</p>
          </div>
        ))}
      </div>

      <CashFlowPreview summary={budget} />

      {retirement && (
        <div className="details-card open-card">
          <h2>Retirement API result</h2>
          <div className="estimate-grid">
            <Metric label="Required savings rate" value={`${retirement.savings.savings_rate_pct.toFixed(1)}%`} />
            <Metric label="First monthly contribution" value={formatCurrency(retirement.savings.first_month_contribution)} />
            <Metric label="Monte Carlo success" value={`${Math.round(retirement.monteCarlo.success_rate * 100)}%`} />
          </div>
        </div>
      )}

      {plan.results.retirementError && <p className="api-note error">Retirement API check failed: {plan.results.retirementError}</p>}
      <p className="plan-disclaimer">
        This plan is an educational estimate based on the numbers entered here. It is meant to help with decisions, not replace professional advice.
      </p>
      {apiMessage && <p className="api-note">{apiMessage}</p>}
    </Screen>
  )
}

function ChoiceGroup({ label, value, onChange, options }) {
  return (
    <div className="choice-group">
      <span className="field-label">{label}</span>
      <div className="choice-row">
        {options.map(([optionValue, optionLabel]) => (
          <button
            className={value === optionValue ? 'choice selected' : 'choice'}
            key={optionValue}
            onClick={() => onChange(optionValue)}
            type="button"
          >
            {optionLabel}
          </button>
        ))}
      </div>
    </div>
  )
}

function MoneyField({ label, value, onChange, prefix = '$', suffix = '' }) {
  return (
    <label>
      {label}
      <div className="money-input">
        {prefix && <span>{prefix}</span>}
        <input
          inputMode="decimal"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder="0"
        />
        {suffix && <span>{suffix}</span>}
      </div>
    </label>
  )
}

function Metric({ label, value }) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function CashFlowPreview({ summary }) {
  const maxAmount = Math.max(...summary.cash_flow.map((line) => line.monthly_amount), 1)

  return (
    <div className="cash-card">
      <div className="cash-header">
        <div>
          <span className="mini-label">Monthly picture</span>
          <h2>{summary.status === 'deficit' ? 'Over plan' : 'Room to work'}</h2>
        </div>
        <strong className={summary.surplus >= 0 ? 'positive' : 'negative'}>{formatCurrency(summary.surplus)}</strong>
      </div>
      <div className="cash-bars">
        {summary.cash_flow.map((line) => (
          <div className="cash-line" key={`${line.group}-${line.label}`}>
            <div className="cash-line-top">
              <span>{line.label}</span>
              <strong>{formatCurrency(line.monthly_amount)}</strong>
            </div>
            <div className={`bar-track ${line.group}`}>
              <div className="bar-fill" style={{ width: `${Math.max(4, (line.monthly_amount / maxAmount) * 100)}%` }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function NavButtons({ onBack, onNext, nextLabel, disabled = false }) {
  return (
    <>
      <SecondaryButton onClick={onBack}>Back</SecondaryButton>
      <PrimaryButton onClick={onNext} disabled={disabled}>
        {nextLabel}
      </PrimaryButton>
    </>
  )
}

function PrimaryButton({ children, onClick, disabled = false }) {
  return (
    <button className="primary-btn" type="button" onClick={onClick} disabled={disabled}>
      {children}
    </button>
  )
}

function SecondaryButton({ children, onClick, disabled = false }) {
  return (
    <button className="secondary-btn" type="button" onClick={onClick} disabled={disabled}>
      {children}
    </button>
  )
}

function buildBudgetPayload(plan) {
  const income = plan.income
  const budget = plan.budget
  const readiness = plan.readiness
  const incomeStreams = []

  if (income.payPattern === 'twice_monthly') {
    addIncome(incomeStreams, 'Mid-month pay', income.midMonth, 'mid_month')
    addIncome(incomeStreams, 'End-month pay', income.endMonth, 'end_month')
  }

  if (income.payPattern === 'biweekly') {
    addIncome(incomeStreams, 'Biweekly pay', income.biweeklyNet, 'biweekly')
  }

  if (income.payPattern === 'variable') {
    addIncome(incomeStreams, 'Typical variable pay', income.variableTypical, 'monthly')
  }

  addIncome(incomeStreams, 'Additional income', income.additionalMonthly, 'monthly')

  return {
    income_streams: incomeStreams,
    fixed_expenses: compactCategories([
      ['Rent or mortgage', budget.housing],
      ['Food and groceries', budget.groceries],
      ['Utilities', budget.utilities],
      ['Income-earning expenses', budget.incomeEarning],
      ['Transportation', budget.transportation],
      ['Debt minimums', budget.debtMinimums],
    ]),
    investments: compactCategories([
      ['Emergency fund savings', budget.emergencySavings],
      ['Retirement savings', readiness.retirementSavingsMonthly],
    ]),
    flexible_spending: compactCategories([
      ['Non-essential bills', budget.nonEssentialBills],
      ['Eating out', budget.eatingOut],
      ['Travel', budget.travel],
      ['Pets', budget.pets],
      ['Subscriptions', budget.subscriptions],
      ['Other', budget.other],
    ]),
  }
}

function addIncome(streams, label, amount, frequency) {
  if (number(amount) > 0) {
    streams.push({ label, amount: number(amount), frequency })
  }
}

function compactCategories(items) {
  return items
    .filter(([, amount]) => number(amount) > 0)
    .map(([label, amount]) => ({ label, amount: number(amount) }))
}

function summarizeBudgetLocally(payload) {
  const takeHome = payload.income_streams.reduce(
    (total, stream) => total + number(stream.amount) * frequencyMultiplier(stream.frequency),
    0,
  )
  const fixedTotal = sumCategory(payload.fixed_expenses)
  const investmentsTotal = sumCategory(payload.investments)
  const flexibleTotal = sumCategory(payload.flexible_spending)
  const plannedTotal = fixedTotal + investmentsTotal + flexibleTotal
  const surplus = takeHome - plannedTotal
  const categoryBreakdown = [
    ...lineItems(payload.fixed_expenses, 'fixed', takeHome),
    ...lineItems(payload.investments, 'investments', takeHome),
    ...lineItems(payload.flexible_spending, 'flexible', takeHome),
  ]
  const topSpending = categoryBreakdown
    .filter((line) => line.group !== 'investments')
    .sort((a, b) => b.monthly_amount - a.monthly_amount)
    .slice(0, 5)
  const cashFlow = [
    line('Fixed expenses', 'fixed', fixedTotal, takeHome),
    line('Investments and savings', 'investments', investmentsTotal, takeHome),
    line('Flexible spending', 'flexible', flexibleTotal, takeHome),
    line(surplus >= 0 ? 'Unallocated surplus' : 'Monthly deficit', surplus >= 0 ? 'surplus' : 'deficit', Math.abs(surplus), takeHome),
  ]

  return {
    take_home_monthly: round(takeHome),
    take_home_annual: round(takeHome * 12),
    fixed_total: round(fixedTotal),
    investments_total: round(investmentsTotal),
    flexible_total: round(flexibleTotal),
    planned_total: round(plannedTotal),
    surplus: round(surplus),
    surplus_annual: round(surplus * 12),
    fixed_ratio: ratio(fixedTotal, takeHome),
    investments_ratio: ratio(investmentsTotal, takeHome),
    flexible_ratio: ratio(flexibleTotal, takeHome),
    planned_ratio: ratio(plannedTotal, takeHome),
    surplus_ratio: ratio(surplus, takeHome),
    status: takeHome <= 0 ? 'missing_income' : surplus < -5 ? 'deficit' : surplus > 5 ? 'surplus' : 'balanced',
    status_message: surplus < -5 ? 'Your plan spends more than monthly take-home pay.' : 'You have a workable monthly picture.',
    top_spending_categories: topSpending,
    category_breakdown: categoryBreakdown,
    cash_flow: cashFlow,
  }
}

function buildRecommendations(plan, budget) {
  const readiness = plan.readiness
  const top = budget.top_spending_categories
  const first = top[0]?.label || 'your largest flexible category'
  const second = top[1]?.label || 'your second-largest category'
  const targetMonthly = budget.surplus > 250 ? 250 : Math.max(100, Math.min(250, Math.abs(budget.surplus) + 100))
  const emergencyMonths = plan.income.payPattern === 'variable' ? 6 : 3
  const emergencyTarget = budget.planned_total * emergencyMonths
  const debtBalance = number(readiness.debtAmount)
  const debtRate = getDebtRate(readiness)
  const debtInterest = (debtBalance * (debtRate / 100)) / 12
  const debtMonths = debtBalance > 0 ? monthsToPayDebt(debtBalance, debtRate, targetMonthly + number(plan.budget.debtMinimums)) : null

  let gate
  let action

  if (readiness.emergency1000 !== 'yes') {
    gate = 'Build the $1,000 emergency fund'
    action = `Save ${formatCurrency(targetMonthly)} per month in a savings account at your bank. Start by reducing ${first} and ${second}.`
  } else if (readiness.employerMatch === 'no') {
    gate = 'Capture the employer match'
    action = `Use the first available surplus to reach the full match. If cash is tight, trim ${first} before reducing required expenses.`
  } else if (readiness.highInterestDebt === 'yes' && debtBalance > 0) {
    gate = 'Pay high-interest debt'
    action = `Put ${formatCurrency(targetMonthly)} extra toward the highest-rate balance. At ${debtRate.toFixed(1)}% APR, this debt is costing about ${formatCurrency(debtInterest)} per month in interest.`
  } else if (number(readiness.retirementSavingsMonthly) <= 0) {
    gate = 'Start retirement saving'
    action = `Start with a monthly retirement contribution, even if it is small. Use ${first} and ${second} as the first places to create room.`
  } else {
    gate = `${emergencyMonths}-month emergency fund`
    action = `Based on this budget, a ${emergencyMonths}-month emergency fund is about ${formatCurrency(emergencyTarget)}. Build that before adding complicated goal math.`
  }

  return {
    gate,
    action,
    cards: [
      {
        label: 'Monthly action',
        value: formatCurrency(targetMonthly),
        detail: `Suggested amount to redirect from ${first} and ${second}.`,
      },
      {
        label: 'Emergency target',
        value: formatCurrency(emergencyTarget),
        detail: `${emergencyMonths} months because your income is ${plan.income.payPattern === 'variable' ? 'variable' : 'consistent'}.`,
      },
      {
        label: 'Debt timeline',
        value: debtMonths ? `${debtMonths} months` : 'No high-interest debt',
        detail: debtMonths ? `Using minimums plus ${formatCurrency(targetMonthly)} extra.` : 'Keep this gate closed and move on.',
      },
    ],
  }
}

function estimateMonthlyIncome(income) {
  if (income.payPattern === 'twice_monthly') {
    return number(income.midMonth) + number(income.endMonth) + number(income.additionalMonthly)
  }
  if (income.payPattern === 'biweekly') {
    return number(income.biweeklyNet) * (26 / 12) + number(income.additionalMonthly)
  }
  return number(income.variableTypical) + number(income.additionalMonthly)
}

function getDebtRate(readiness) {
  return number(readiness.debtApr) || DEFAULT_DEBT_RATES[readiness.debtType] || DEFAULT_DEBT_RATES.other
}

function monthsToPayDebt(balance, apr, payment) {
  const monthlyRate = apr / 100 / 12
  if (payment <= balance * monthlyRate) {
    return null
  }
  return Math.ceil(Math.log(payment / (payment - balance * monthlyRate)) / Math.log(1 + monthlyRate))
}

function sumCategory(categories) {
  return categories.reduce((total, category) => total + number(category.amount), 0)
}

function lineItems(categories, group, takeHome) {
  return categories.map((category) => line(category.label, group, category.amount, takeHome))
}

function line(label, group, amount, takeHome) {
  return {
    label,
    group,
    monthly_amount: round(amount),
    annual_amount: round(amount * 12),
    pct_of_take_home: ratio(amount, takeHome),
  }
}

function frequencyMultiplier(frequency) {
  const multipliers = {
    monthly: 1,
    mid_month: 1,
    end_month: 1,
    semi_monthly: 2,
    biweekly: 26 / 12,
    weekly: 52 / 12,
    quarterly: 1 / 3,
    annual: 1 / 12,
  }
  return multipliers[frequency] || 1
}

function ratio(amount, base) {
  if (base <= 0) return 0
  return round(amount / base, 4)
}

function round(value, digits = 2) {
  const factor = 10 ** digits
  return Math.round(number(value) * factor) / factor
}

function number(value) {
  const parsed = Number.parseFloat(value)
  return Number.isFinite(parsed) ? parsed : 0
}

function formatCurrency(value) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(number(value))
}

export default App
