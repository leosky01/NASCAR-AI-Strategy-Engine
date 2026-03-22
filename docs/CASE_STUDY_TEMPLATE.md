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
