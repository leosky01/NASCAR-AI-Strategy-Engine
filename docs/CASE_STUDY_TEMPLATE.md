# NASCAR Case Study Template

**How to validate the framework with real race data**

---

## Overview

This document provides a template for creating compelling case studies by backtesting the strategy optimization framework against real NASCAR races.

---

## Why Case Studies Matter

**For NASCAR Teams:**
- Shows you understand real racing
- Demonstrates practical value
- Proves it works with real data
- Quantifies potential ROI

**For You:**
- Shows you can do more than synthetic demos
- Demonstrates domain knowledge
- Provides portfolio examples
- Credibility builder

---

## Case Study Template

### Format: Real Race + What If Scenario

---

## Example Case Study: Bristol Spring 2024

### Race Information

**Track:** Bristol Motor Speedway
**Date:** March 17, 2024
**Race Name: Food City 500
**Laps:** 500
**Winner:** Denny Hamlin
**Cautions:** 8

### Actual Team Performance

**Hypothetical Team:** Team X
**Drivers:** [Drivers A, B, C]
**Actual Strategy:** 3-stop strategy (laps 130, 260, 390)

**Results:**
- Driver A: 12th place
- Driver B: 18th place
- Driver C: 25th place
- Average: 18.3rd place

---

## Analysis: What Went Wrong

### Data Collection

**Lap-by-Lap Analysis:**
```
Lap 125-135: Green flag run, many cars pitting
  - Team pitted lap 130
  - Lost 4 positions on pit cycle
  - Lost 2 more positions in next 10 laps (tire disadvantage)

Lap 255-265: Another long green run
  - Team pitted lap 260
  - Track position: 15th
  - Came out 18th (heavy traffic)

Lap 385-395: Late race chaos
  - Pitted lap 390
  - Got stuck behind lapped cars
  - Finished 25th
```

**Post-Race Analysis:**
- "We should have pitted earlier on the first stop"
- "Traffic on the second stop killed us"
- "Fresh tires at the end didn't help - stuck in traffic"

---

## Backtesting: What Could We Have Done?

### Using Our Framework

**Step 1: Sensitivity Analysis on First Pit**

```
Question: What if we pitted at lap 120 instead of 130?

Method:
- Ran sensitivity analysis on lap 120-140 range
- 100 simulations per pit lap
- Considered caution probability

Results:
- Lap 120: 14.2 avg position (↑ 4 positions)
- Lap 125: 14.8 avg position (↑ 3 positions)
- Lap 130: 18.3 avg position (actual - baseline)
- Lap 135: 19.1 avg position (↓ 1 position)
- Lap 140: 20.5 avg position (↓ 2 positions)

Conclusion: Pitting 10 laps earlier gives 4-position advantage
```

**Step 2: Traffic Analysis on Second Pit**

```
Question: What caused the traffic issues on lap 260?

Method:
- Analyzed track position history from real race
- Found heavy lapped car traffic at lap 260
- Tested alternative: lap 255 or 265

Results:
- Lap 255: 16.8 avg position (1 position better)
- Lap 260: 18.3 avg position (actual - baseline)
- Lap 265: 17.9 avg position (0.4 position better)

Conclusion: 5 laps earlier avoids heaviest traffic
```

**Step 3: Full Strategy Optimization**

```
Original Strategy: (130, 260, 390)
- Average position: 18.3
- Win probability: 2.1%
- Top-10 probability: 15%
- Top-20 probability: 42%

Optimized Strategy: (120, 255, 385)
- Average position: 14.9 (↑ 3.4 positions)
- Win probability: 4.7% (↑ 2.6%)
- Top-10 probability: 28% (↑ 13%)
- Top-20 probability: 71% (↑ 29%)
```

---

## Quantified Value

### Performance Improvement

| Metric | Original | Optimized | Improvement |
|--------|----------|-----------|-------------|
| **Avg Position** | 18.3 | 14.9 | ↑ 3.4 positions |
| **Win Probability** | 2.1% | 4.7% | ↑ 2.6% |
| **Top-10 Probability** | 15% | 28% | ↑ 87% more likely |
| **Top-20 Probability** | 42% | 71% | ↑ 69% more likely |

### Financial Impact (Hypothetical)

**NASCW Cup Series Prize Money (2024):**
```
Position 12: $185,000
Position 15: $152,000
Difference: $33,000

Position 14.9 avg ≈ $168,000 (if realized)
Improvement: +$16,000 per driver

Over 36 races:
- 3.4 position improvement = significant cumulative value
- More top-10s = bonus pool money
- Better finishes = better charter value
```

---

## Visual Analysis

### Pit Strategy Comparison

```
Original Strategy:
  Pit 1: Lap 130 (green flag run of 55 laps)
  Pit 2: Lap 260 (green flag run of 130 laps)
  Pit 3: Lap 390 (late race)

  Issues:
  - Pit 1: Too late, lost track position
  - Pit 2: Heavy traffic, lost 3 positions
  - Pit 3: Too late to capitalize on fresh tires

Optimized Strategy:
  Pit 1: Lap 120 (earlier, maintains track position)
  Pit 2: Lap 255 (avoids heavy traffic)
  Pit 3: Lap 385 (earlier, more time to use fresh tires)

  Benefits:
  + Maintains better track position all race
  + Avoids heavy traffic cycles
  + More aggressive late-race moves
```

---

## Key Insights

### What We Learned

**1. Pit Timing is Critical**
- 10-lap difference on first pit = 4 position swing
- Traffic patterns matter more than fresh tires late in race

**2. Caution Gambling vs. Track Position**
- Staying out under caution gains positions
- But heavy traffic negates advantage
- **Optimal:** Balance between track position and clean air

**3. Late Race Strategy**
- Fresh tires with < 20 laps = limited value
- Better to pit earlier and have clean air
- Track position trumps tire advantage

**4. Variance vs. Expected Value**
- Original strategy: 18.3 avg, but high variance
- Optimized: 14.9 avg, more consistent
- Lower variance = more predictable finishes

---

## Why This Matters

### For Team Decision Makers

**Before:**
> "We've always pitted around lap 130 here at Bristol, that's our spot."

**After (with data):**
> "Analysis shows pitting at lap 120 gives us 3.4 position improvement on average. We should adjust our strategy."

### For Crew Chiefs

**Question:** "When should we pit?"

**Answer:**
> "Let me check the sensitivity analysis...
>
> Current lap 125, we have 3 strategies:
> - Pit now: Expected 15.2 position
> - Pit lap 130: Expected 18.1 position
> - Stay out: Expected 14.8 position (but risky)
>
> Recommendation: Stay out until lap 128, then pit."

### For Drivers

**Question:** "What can you tell me about my strategy?"

**Answer:**
> "Your optimized strategy has you:
> - Pitting lap 120, 255, and 385
> - Expected 15th place finish
> - 28% chance of top-10
> - 71% chance of top-20
>
> Variance: ±6 positions
>
> Best case: 9th, Worst case: 24th"

---

## Creating Your Own Case Studies

### Step 1: Choose a Race

**Good Candidates:**
- Races with multiple strategies visible
- Close finishes (show strategy mattered)
- High caution races (show risk/reward)
- Tracks your team actually races at

### Step 2: Get Data

**Sources:**
- Racing-Reference.com (free)
- NASCAR.com/results (free)
- NASCAR Loop Data API (paid)
- Team's own data (best!)

**Data Needed:**
```
- Lap-by-lap results
- Pit stop records (who, when, how long)
- Causions (when, how long)
- Lap times by car
```

### Step 3: Analyze What Happened

**Questions to Ask:**
1. What was the team's strategy?
2. How did it work out?
3. Where did they gain/lose positions?
4. What did they say afterwards?
5. What could they have done differently?

### Step 4: Backtest with Framework

**Process:**
```python
# 1. Recreate their actual strategy
actual_strategy = Strategy(
    name='Bristol Spring Actual',
    pit_stops=[130, 260, 390]
)

# 2. Evaluate with your simulator
metrics = evaluate_strategy(
    actual_strategy,
    num_simulations=500
)

# 3. Compare to actual result
actual_finish = 18.3
predicted_finish = metrics['mean_position']

# 4. Run optimization
optimized = optimize_strategy(
    actual_strategy,
    search_ranges=[(115, 135), (250, 270), (380, 400)]
)

# 5. Compare
optimized_finish = optimized['mean_position']
improvement = actual_finish - optimized_finish

print(f"Actual: {actual_finish}")
print(f"Optimized: {optimized_finish}")
print(f"Improvement: {improvement} positions")
```

### Step 5: Tell the Story

**Structure:**
1. **Context:** Set the scene (track, race conditions)
2. **Reality:** What actually happened
3. **Problem:** What went wrong
4. **Analysis:** Why it went wrong
5. **Solution:** What could have been done
6. **Value:** Quantified improvement

---

## Case Study Examples by Track Type

### Superspeedways (Daytona, Talladega)

**Challenge:** Fuel mileage, track position

**Case Study:**
- Race: Daytona 500 2024
- Issue: Fuel strategy gamble
- Backtest: Show optimal fuel window
- Result: More data-driven approach

---

### Short Tracks (Bristol, Martinsville)

**Challenge:** Track position, cautions

**Case Study:**
- Race: Bristol Night Race 2024
- Issue: Too many cautions, wrong strategy
- Backtest: Optimize for high caution environment
- Result: Adaptive strategy

---

### Intermediate (Phoenix, Richmond)

**Challenge:** Balance everything

**Case Study:**
- Race: Richmond Spring 2024
- Issue: Tires vs. track position
- Backtest: Find optimal tradeoff
- Result: Data-driven balance

---

### Road Courses (Sonoma, Watkins Glen)

**Challenge:** Track position over everything

**Case Study:**
- Race: Watkins Glen 2024
- Issue: Late-race strategy
- Backtest: Optimize for track position
- Result: Position-focused approach

---

## Template for Presentation

### Slide Format

**Title:** [Race Name] - [Optimization Opportunity]

**Section 1: The Race**
- Date, track, cautions
- Team's actual strategy
- Actual results

**Section 2: The Problem**
- What went wrong?
- Where were positions lost?
- What did team say after?

**Section 3: The Analysis**
- Sensitivity analysis results
- Optimization opportunities
- Backtest methodology

**Section 4: The Solution**
- Optimized strategy
- Expected improvement
- Confidence intervals

**Section 5: The Value**
- Quantified improvement
- Financial impact
- Risk analysis

---

## Example: Quick Template

### Title: Bristol Spring 2024 - 3.4 Position Opportunity

**The Race:**
- March 17, 2024 - Bristol Motor Speedway
- Team X ran 3-stop strategy (130, 260, 390)
- Results: 12th, 18th, 25th (avg 18.3)

**The Problem:**
- Pitted too late on first stop (lost 4 positions)
- Got stuck in traffic on second stop (lost 3 positions)
- Late strategy didn't capitalize on fresh tires

**The Analysis:**
- Sensitivity analysis shows:
  - Lap 120 > Lap 130 for first stop (4 position gain)
  - Lap 255 > Lap 260 for second stop (avoids traffic)
  - Earlier final pit gives more time to use fresh tires

**The Solution:**
- Optimized: (120, 255, 385)
- Expected: 14.9 avg position (↑ 3.4)
- Top-10 probability: 28% (vs. 15%)
- Win probability: 4.7% (vs. 2.1%)

**The Value:**
- 3.4 position improvement = more prize money
- More consistent finishes
- Better charter value

---

## Using This Template

### For Real Presentation:

**Before NASCAR Team:**
1. Research 2-3 real races they participated in
2. Get actual results (Racing-Reference)
3. Run framework backtest
4. Create 1-2 case studies
5. Present: "Here's what happened at Bristol, and here's what we could have done differently"

**Key Point:**
> "This demonstrates I understand:
> - Real NASCAR racing
> - The decisions teams face
> - How data could have helped
>
> With your data, I can build on this foundation to create tools for your future races."

---

## Summary

**Case studies show:**
- ✅ You understand NASCAR racing
- ✅ Framework works with real scenarios
- ✅ Data can improve decisions
- ✅ You can provide real value

**Create 2-3 case studies and you'll be taken seriously!** 🏁
