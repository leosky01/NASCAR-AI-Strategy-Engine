<p align="center">
  <a href="https://nascar-ai-strategy-engine-7eakf3pk8e7upe8av6pdaq.streamlit.app/">
    <img src="https://static.streamlit.io/badges/streamlit_badge_black_white.svg" alt="Streamlit App" />
  </a>
  <img src="https://img.shields.io/badge/Portfolio-Project-blue" />
  <img src="https://img.shields.io/badge/Status-Live%20Demo-success" />
  <img src="https://img.shields.io/badge/Tests-Passing-brightgreen" />
</p>

<h1 align="center">🏎️ NASCAR AI Strategy Engine</h1>

<p align="center">
  <strong>Interactive AI-driven tools for NASCAR race strategy analysis</strong>
</p>

<p align="center">
  <a href="https://nascar-ai-strategy-engine-7eakf3pk8e7upe8av6pdaq.streamlit.app/">
    <img src="https://img.shields.io/badge/Live%20Demo-Open%20App-brightgreen" alt="Live Demo" />
  </a>
</p>

<p align="center">
  <em>Built to demonstrate technical skills in machine learning, simulation, and optimization applied to motorsports</em>
</p>

<p align="center">
  <a href="#why-this-matters">Why It Matters</a> •
  <a href="#what-it-does">What It Does</a> •
  <a href="#see-it-in-action">See It In Action</a> •
  <a href="#contact">Contact</a>
</p>

---

## 🌐 **Try the Live Demo!**

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://nascar-ai-strategy-engine-7eakf3pk8e7upe8av6pdaq.streamlit.app/)

**Direct link:** https://nascar-ai-strategy-engine-7eakf3pk8e7upe8av6pdaq.streamlit.app/

**What you can do in the live demo:**
- 🔄 Compare multiple pit strategies side-by-side
- 📊 See Monte Carlo simulation results with statistical analysis
- 🎯 Find optimal pit timing with sensitivity analysis
- 🏁 Simulate races with caution flags
- ⚙️ Customize simulation parameters
- ⚡ **NEW:** Get probabilistic decision recommendations (e.g., "75% pit, 25% stay out")
- 🏆 **NEW:** Optimize for NASCAR stage points instead of just finishing position

*No installation required - runs in your browser!*

---

## 🚀 Interactive Dashboard

This project includes a fully interactive Streamlit dashboard for:

- Strategy comparison using Monte Carlo simulations
- Pit stop optimization
- Live race simulation

### Run Locally

```bash
streamlit run app.py
```

## 👋 About This Project

**This is a portfolio project demonstrating practical skills in data science, simulation, and optimization applied to motorsport strategy.**

I built this to show that I can:
- Apply machine learning and statistical methods to racing strategy problems  
- Build working software tools, not just analysis notebooks  
- Understand NASCAR strategy and translate it into code  
- Write clean, tested, documented code  
- Communicate technical concepts clearly  

**What I'm Looking For:**
A trial period or internship with a NASCAR team where I can apply these skills in a real environment, learn from experienced professionals, and contribute to the team's analytical capabilities.

---

## 🎯 Why This Matters

NASCAR teams make complex strategic decisions every race.

When to pit, how many tires, fuel strategy, track position vs. tire wear — these decisions involve many variables and uncertain outcomes.

This project shows that I can approach these problems using analytical methods and software engineering.

**With This Engine:**
- Compare multiple strategy variations quickly  
- Estimate optimal pit windows with statistical confidence  
- Quantify the risk of different decisions  
- Simulate many race scenarios before making a call  

---

## 📊 What It Does

### Strategy Analysis
- Compare different strategic approaches  
- Run Monte Carlo simulations  
- Evaluate statistical confidence  
- Identify optimal pit windows  

### Decision Support
- Quantitative comparison of strategies  
- Visualization of trade-offs  
- Understanding uncertainty in outcomes  

---

## 🏆 Demonstrated Capabilities

| Capability | What It Shows |
|------------|--------------|
| Monte Carlo Simulation | 200+ race scenarios in seconds |
| Statistical Analysis | Confidence intervals and comparisons |
| Machine Learning | XGBoost caution predictor |
| Optimization | Pit window optimization |
| Probabilistic Decisions | "75% pit, 25% stay out" recommendations |
| NASCAR Points System | Stage points optimization |
| Code Quality | 138/138 tests passing |

---

## 🚀 Engine Capabilities

### 1. Physics-Based Simulation

- Tire degradation modeling  
- Fuel weight impact  
- Traffic / dirty air effects  
- Caution dynamics  

---

### 2. Machine Learning (Caution Prediction)

- XGBoost classifier  
- 18 engineered features  
- Validation AUC ~0.80  

Estimate the probability of cautions during a race.

---

### 3. Monte Carlo Strategy Evaluation

- Hundreds of simulations
- Statistical comparison of strategies
- Confidence intervals

<!-- TODO: Add visualization after running simulations -->

---

### 4. Sensitivity Analysis & Optimization

- Pit window optimization
- Risk/reward analysis

<!-- TODO: Add visualization after running analysis -->

---

### 5. Interactive Dashboard

The Streamlit dashboard provides an interface to:

- Compare strategies  
- Run simulations  
- Visualize results  

(See demo above)

---

## 🆕 Latest Features 

### Probabilistic Decision Engine

Instead of binary "pit or don't pit" recommendations, the engine now provides **probability distributions**:

```
Recommendation: PIT - 75.3% probability pitting is better
Confidence: HIGH (200 simulations)

If You Pit              If You Stay Out
─────────────         ──────────────────
Expected: 12.1 pos      Expected: 16.7 pos
Top-10: 68.2%           Top-10: 34.1%
Win: 18.3%              Win: 8.7%
```

**Technical Details:**
- Bootstrap resampling (1,000 iterations) to estimate P(pit < stay_out)
- Cohen's d for effect size calculation
- Confidence levels: high/medium/low based on sample size and effect size
- Real-time analysis: <500ms for 200 simulations

### NASCAR Stage Points Optimization

Now implements the **official NASCAR stage racing points system**:

- **Stage 1 & 2:** Top 10 get points (1st=10, 2nd=9, ..., 10th=1)
- **Final Stage:** 1st=40, 2nd=35, 3rd=34, ..., 36th=1
- **Playoff Points:** 1 per win

**Key Feature:** Optimize for **expected total points** instead of just finishing position. This better aligns with NASCAR's championship format.

### GAM Tire Degradation Models

**Track-specific tire models** using Generalized Additive Models (GAMs):

**Two-Stage Approach:**
1. **Stage 1:** Tire degradation GAM: `s(tire_age) + s(track_temp) + f(compound)`
2. **Stage 2:** Traffic GAM on residuals: `s(traffic_density) + s(overtaking_ability)`

**Supported Tracks:**
- Phoenix (high abrasiveness)
- Charlotte (moderate)
- Darlington (very high abrasiveness)
- Bristol (short track, high wear)
- Talladega (superspeedway, low wear)

**Graceful Fallback:** Automatically uses exponential model when GAM unavailable.

### New Dashboard Tab: ⚡ Live Decisions

Real-time decision analysis for race-day strategy:
- Enter current race state (lap, position, tire age, fuel)
- Get immediate probabilistic recommendation
- See risk assessment (95th percentile worst case)
- Compare expected outcomes

---

## 💼 What I Can Bring

### Technical Skills

- Data science and statistical analysis
- Machine learning (XGBoost, feature engineering)
- Simulation and optimization
- Software engineering best practices
- Cloud deployment (Streamlit Cloud, Docker)
- Interactive visualization (Streamlit, Plotly)  

### What I'm Looking For

Open to:
- Internship  
- Trial period  
- Entry-level role  

During a trial period, I would:
- Learn your systems and data quickly  
- Contribute to analysis and tool development  
- Demonstrate value through practical work  

---

## 🎬 See It In Action

### 🌐 **Live Demo (Recommended - No Installation Required)**

**Try the interactive dashboard now:** [nascar-ai-strategy-engine.streamlit.app](https://nascar-ai-strategy-engine-7eakf3pk8e7upe8av6pdaq.streamlit.app/)

### 💻 **Run Locally**

Want to run it on your own machine?

```bash
# Clone the repository
git clone https://github.com/leosky01/NASCAR-AI-Strategy-Engine.git
cd NASCAR-AI-Strategy-Engine

# Install dependencies
pip install -r requirements.txt

# Run the dashboard
streamlit run app.py
```

---

## 📊 Performance

| Component | Actual |
|-----------|--------|
| Race simulation | 0.037 s |
| Monte Carlo (200 sims) | 3.6 s |
| Full workflow | 2.8 s |

<!-- TODO: Add performance metrics chart -->

---

## 📚 Documentation

- docs/IMPLEMENTATION_ROADMAP.md  
- docs/SIMULATOR_DESIGN.md  
- docs/DEMO_SCRIPT.md  

---

## 📬 Contact & Connect

**Leonardo Schiavoni**
- Email: leonardoschiavoni82@gmail.com
- Telephone: +39 333 199 8914
- LinkedIn: [linkedin.com/in/leonardo-schiavoni-665173340](https://linkedin.com/in/leonardo-schiavoni-665173340)
- GitHub: [github.com/leosky01](https://github.com/leosky01)

---

<p align="center">
  <strong>Ready to explore NASCAR strategy optimization?</strong><br>
  <a href="https://nascar-ai-strategy-engine-7eakf3pk8e7upe8av6pdaq.streamlit.app/">
    <img src="https://img.shields.io/badge/Try%20Live%20Demo-Open%20App-brightgreen" alt="Live Demo" />
  </a>
  <a href="https://github.com/leosky01/NASCAR-AI-Strategy-Engine">
    <img src="https://img.shields.io/badge/GitHub-View%20Source-blue" alt="GitHub" />
  </a>
</p>

<p align="center">
  <em>Built to demonstrate practical skills in motorsport analytics.</em>
</p>
