# Simulator Design - Visual Overview

## 🏎️ Lap Time Calculation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    LAP TIME DECOMPOSITION                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Lap_Time = Base + Tire + Fuel + Traffic + Noise                │
│                                                                  │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────┐ │
│  │  Base   │  │  Tire   │  │  Fuel   │  │ Traffic │  │Noise│ │
│  │  48.0s  │  │ 0-5.0s  │  │ 0-3.0s  │  │ 0-1.0s  │  │±0.3s│ │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────┘ │
│       │            │            │            │          │      │
│       └────────────┴────────────┴────────────┴──────────┘      │
│                            │                                    │
│                            ▼                                    │
│                   ┌─────────────────┐                           │
│                   │ Final Lap Time  │                           │
│                   │   ~48-57 sec     │                           │
│                   └─────────────────┘                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 📊 Tire Degradation Function

```
Tire Penalty vs. Age

Penalty (s)
  6 │                                    ┌────────
    │                                  ┌
  5 │                               ┌──       ← CAP (5.0s)
    │                            ┌─
  4 │                         ┌─
    │                      ┌─
  2 │                ┌─────
    │          ┌────┘
  1 │     ┌───┘
    │ ┌───┘
  0 └─└──────────────────────────────────────
    0   10   20   30   40   50   60   70   80
                    Tire Age (laps)
```

**Key Properties**:
- **Exponential acceleration**: Degradation speeds up with age
- **Soft cap**: Maximum 5.0s penalty at ~40 laps
- **Realistic range**: 0-5 seconds slower than new tires

## 🚗 Traffic Penalty Model

```
Traffic Penalty vs. Gap

Penalty (s)
  1 │                ┌───
    │              ┌─
  0.75│          ┌─
    │        ┌─
  0.5│     ┌─
    │  ┌─┘
  0.25┌─┘
    └─└──────────────────────────────
    0.0  0.2  0.4  0.6  0.8  1.0  1.2+
                Gap to car ahead (s)
```

**Key Properties**:
- **Threshold**: Only applies if gap < 1.0s
- **Cap**: Maximum 1.0s penalty
- **Overtaking ability**: Divides penalty (higher = less affected)

## 🔄 Simulation Loop

```
FOR each lap (1 to num_laps):
    FOR each car:
        IF pit_scheduled:
            add pit_duration to cumulative_time
            reset tire_age = 0
            refuel fuel_level = 100%
            record lap_time = pit_duration
        ELSE:
            calculate lap_time (base + tire + fuel + traffic + noise)
            add to cumulative_time
            consume fuel (-0.25%)
            age tires (+1 lap)
            record lap_time

    SORT cars by cumulative_time
    UPDATE positions (1 to num_cars)
    RECORD lap history
```

## 📈 Position Determination

```
BEFORE (Wrong - Random Swapping):
    positions = [1, 2, 3, ..., 40]
    swap random pairs
    ❌ Not physically based

AFTER (Correct - Time-Based):
    cumulative_times = [2400.5, 2401.2, 2399.8, ...]
    sorted_indices = argsort(cumulative_times)
    positions = sorted_indices + 1
    ✅ Physically consistent
```

## 🎯 Key Design Decisions

### ✅ Decisions Made

| Decision | Rationale |
|----------|-----------|
| **Time-based positions** | Realistic, physics-based |
| **Exponential tire wear** | Accelerating degradation matches reality |
| **Tire cap at 5s** | Prevents unrealistic slowdowns |
| **Traffic gap < 1s** | Only close proximity matters |
| **Fuel penalty linear** | Simpler, weight ~constant per lap |
| **Pit time = lap time** | Accurate statistics (not zeros) |

### ❓ Decisions Pending

| Question | Options | Impact |
|----------|---------|--------|
| **Caution integration** | Now vs Phase 2 | Affects strategy complexity |
| **Fuel vs tire balance** | Current vs adjusted | Changes optimal strategy |
| **Car performance spread** | Current vs wider | Affects race competitiveness |
| **Traffic model** | Binary vs continuous | Affects overtaking dynamics |

---

## 🧪 Validation Results

```
✅ All 28 tests passing
✅ 8/8 validation checks passing
✅ Reproducible with same seed
✅ Realistic lap times (45-65s)
✅ No zero lap times
✅ Positions determined by time
```

---

## 💡 Interview Talking Points

**Q: Why time-based positions instead of random swapping?**
A: Random swapping doesn't capture how strategies actually work.
   Time-based means pit stops, tire degradation, and fuel
   all have physical meaning and compound over a race.

**Q: Why exponential tire degradation?**
A: Real NASCAR tires degrade slowly at first, then fall off
   rapidly. The exponential curve captures this "cliff" effect
   while the cap prevents unrealistic slowdowns.

**Q: How do you ensure reproducibility?**
A: We pass a random_seed to the simulator and use self.rng
   (RandomState) everywhere instead of np.random directly.
   This guarantees the same seed produces identical results.

**Q: What's the most complex part of the model?**
A: Traffic effects - we iterate twice to calculate penalties
   because positions affect traffic, which affects lap times,
   which affects positions. The iterative approach converges
   to a consistent solution.
