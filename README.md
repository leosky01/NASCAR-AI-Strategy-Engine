<p align="center">
  <img src="https://img.shields.io/badge/Portfolio-Project-blue" />
  <img src="https://img.shields.io/badge/Status-Work%20In%20Progress-yellow" />
  <img src="https://img.shields.io/badge/Tests-Passing-brightgreen" />
</p>

<h1 align="center">🏎️ NASCAR AI Strategy Engine</h1>

<p align="center">
  <strong>Interactive AI-driven tools for NASCAR race strategy analysis</strong>
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

## 🚀 Interactive Dashboard

This project includes a fully interactive Streamlit dashboard for:

- Strategy comparison using Monte Carlo simulations
- Pit stop optimization
- Live race simulation

### Run Locally

```bash
streamlit run app.py
```

Or use the provided script:

```bash
./run_dashboard.sh
```

### Deploy on Streamlit Cloud (Free)

**🌐 Try the live demo:** [Coming Soon]

Want to deploy your own copy? See [STREAMLIT_CLOUD_DEPLOYMENT.md](STREAMLIT_CLOUD_DEPLOYMENT.md) for step-by-step instructions.

Quick steps:
1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Select `app.py` as main file
5. Click "Deploy" 🚀

---

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
| Code Quality | 83/83 tests passing |

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

```bash
pip install -r requirements.txt
python train_caution_model.py
./run_dashboard.sh
```

<!-- TODO: Add position distribution visualization -->

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

## 📬 Contact

Email: leonardoschiavoni82@gmail.com  
Telephone: +39 333 199 8914
LinkedIn: linkedin.com/in/leonardo-schiavoni-665173340  

---

<p align="center">
  <em>Built to demonstrate practical skills in motorsport analytics.</em>
</p>
