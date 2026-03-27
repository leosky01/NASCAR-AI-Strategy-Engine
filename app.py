"""
NASCAR AI Strategy Engine - Interactive Dashboard

Streamlit app for visualizing and optimizing race strategies.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

from src.simulator import RaceSimulator
from src.monte_carlo import MonteCarloEvaluator, SimulationResult
from src.strategy import Strategy, PitStop, PRESET_STRATEGIES
from src.sensitivity import StrategySensitivityAnalyzer, create_sensitivity_plot
from src.decision_analyzer import ProbabilisticDecisionEngine, create_decision_summary
from config import TRACK_PROFILES, TrackProfile

# Page configuration
st.set_page_config(
    page_title="NASCAR AI Strategy Engine",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-title {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown('<h1 class="main-title">🏎️ NASCAR AI Strategy Engine</h1>', unsafe_allow_html=True)

# Sidebar
st.sidebar.header("⚙️ Configuration")

# Track selection
st.sidebar.subheader("🏁 Track")
selected_track_key = st.sidebar.selectbox(
    "Select Track",
    list(TRACK_PROFILES.keys()),
    index=1,  # Default: Charlotte
    help="Each track has different tire wear, caution rates, and race length"
)
track_profile = TRACK_PROFILES[selected_track_key]

# Show track info
st.sidebar.caption(f"📍 {track_profile.name}")
st.sidebar.caption(f"{track_profile.description}")
st.sidebar.caption(f"📏 {track_profile.length_miles} mi | 🔄 {track_profile.num_laps} laps | Stages: {track_profile.stage1_end}/{track_profile.stage2_end}")

# Simulation settings
st.sidebar.subheader("Race Configuration")
num_cars = st.sidebar.slider("Number of Cars", 10, 43, 40, 5)
num_laps = track_profile.num_laps

sim_config = {
    'num_cars': num_cars,
    'num_laps': num_laps,
    'track_profile': selected_track_key
}

# Monte Carlo settings
st.sidebar.subheader("Monte Carlo Settings")
num_simulations = st.sidebar.slider("Simulations per Strategy", 50, 500, 200, 50)
show_progress = True

# Initialize components
@st.cache_resource
def get_evaluator(config):
    """Get cached Monte Carlo evaluator"""
    return MonteCarloEvaluator(config, n_jobs=2)

@st.cache_resource
def get_analyzer(_evaluator):
    """Get cached sensitivity analyzer"""
    return StrategySensitivityAnalyzer(_evaluator)

evaluator = get_evaluator(sim_config)
analyzer = get_analyzer(evaluator)

# Main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Strategy Comparison",
    "🔍 Sensitivity Analysis",
    "🎯 Strategy Optimizer",
    "🏁 Race Replay",
    "⚡ Live Decisions"
])

# ============================================================================
# TAB 1: Strategy Comparison
# ============================================================================
with tab1:
    st.header("Strategy Comparison")
    st.write("Compare multiple NASCAR pit strategies using Monte Carlo simulation")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Select Strategies to Compare")

        # Allow selecting preset strategies
        selected_presets = st.multiselect(
            "Choose Preset Strategies",
            list(PRESET_STRATEGIES.keys()),
            default=['standard', 'aggressive', 'conservative']
        )

        # Add custom strategy
        with st.expander("➕ Add Custom Strategy"):
            custom_name = st.text_input("Strategy Name", "Custom")
            pit_laps = st.text_input("Pit Laps (comma-separated)", "50, 100, 150")

            if st.button("Add Custom Strategy"):
                try:
                    laps = [int(l.strip()) for l in pit_laps.split(',')]
                    custom_strategy = Strategy(
                        name=custom_name,
                        description="Custom strategy",
                        pit_stops=[PitStop(lap=lap) for lap in laps]
                    )
                    st.success(f"Added strategy: {custom_name}")
                except:
                    st.error("Invalid pit laps format. Use: 'lap1, lap2, lap3'")

    with col2:
        st.subheader("Comparison Settings")
        run_comparison = st.button("🚀 Run Comparison", type="primary")

    if run_comparison or 'comparison_results' in st.session_state:
        st.write("Running simulations...")

        # Build strategies dict
        strategies = {name: PRESET_STRATEGIES[name] for name in selected_presets}

        # Run comparison
        with st.spinner("Running Monte Carlo simulations..."):
            comparison, results = evaluator.compare_strategies(
                strategies,
                num_simulations=num_simulations,
                show_progress=False
            )

        # Store in session state
        st.session_state['comparison_results'] = (comparison, results)
        st.session_state['strategies'] = strategies

        # Display comparison table
        st.subheader("📊 Results")
        st.dataframe(comparison, use_container_width=True)

        # Visualizations
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Mean Position Comparison")
            fig = go.Figure()

            for name in strategies.keys():
                fig.add_trace(go.Bar(
                    name=name,
                    x=[name],
                    y=[results[name]['mean_position']],
                    error_y=dict(type='data', array=[results[name]['std_position']])
                ))

            fig.update_layout(
                title="Average Finishing Position (with error bars)",
                yaxis_title="Position",
                yaxis=dict(autorange="reversed"),
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Win Rate Comparison")
            win_rates = {name: results[name]['win_rate'] * 100 for name in strategies.keys()}

            fig = go.Figure(data=[
                go.Bar(
                    x=list(win_rates.keys()),
                    y=list(win_rates.values()),
                    marker_color='darkblue'
                )
            ])

            fig.update_layout(
                title="Win Rate (%)",
                yaxis_title="Win Rate (%)",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

        # Position distributions
        st.subheader("📈 Position Distributions")

        fig = go.Figure()

        for name in strategies.keys():
            positions = results[name]['positions']
            fig.add_trace(go.Histogram(
                name=name,
                x=positions,
                opacity=0.6,
                nbinsx=20
            ))

        fig.update_layout(
            title="Distribution of Finishing Positions",
            xaxis_title="Finishing Position",
            xaxis=dict(autorange="reversed"),
            yaxis_title="Frequency",
            barmode='overlay',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

        # Key insights
        st.subheader("🔑 Key Insights")

        # Use raw results dict for numeric values
        best_strategy = min(results.keys(), key=lambda k: results[k]['mean_position'])
        worst_strategy = max(results.keys(), key=lambda k: results[k]['mean_position'])
        highest_win_rate = max(results.keys(), key=lambda k: results[k]['win_rate'])
        most_consistent = min(results.keys(), key=lambda k: results[k]['std_position'])

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Best Strategy", best_strategy, f"{results[best_strategy]['mean_position']:.1f} avg pos")

        with col2:
            st.metric("Highest Win Rate", f"{results[highest_win_rate]['win_rate']:.1%}", highest_win_rate)

        with col3:
            st.metric("Most Consistent", most_consistent, f"±{results[most_consistent]['std_position']:.1f}")

# ============================================================================
# TAB 2: Sensitivity Analysis
# ============================================================================
with tab2:
    st.header("Sensitivity Analysis")
    st.write("Analyze how pit timing affects race outcomes")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Analysis Configuration")

        # Select strategy to analyze
        base_strategy_name = st.selectbox(
            "Base Strategy",
            list(PRESET_STRATEGIES.keys()),
            index=0
        )
        base_strategy = PRESET_STRATEGIES[base_strategy_name]

        # Select pit stop to analyze
        pit_index = st.selectbox(
            "Pit Stop to Analyze",
            range(1, len(base_strategy.pit_stops) + 1),
            index=0
        ) - 1

        original_lap = base_strategy.pit_stops[pit_index].lap
        st.info(f"Original pit lap: {original_lap}")

        # Analysis range
        col_a, col_b = st.columns(2)
        min_lap = col_a.number_input("Min Lap", value=min(max(30, original_lap - 15), num_laps-10), min_value=1, max_value=num_laps-10)
        max_lap = col_b.number_input("Max Lap", value=min(num_laps-5, original_lap + 15), min_value=10, max_value=num_laps)

        # Grid resolution
        lap_step = st.slider("Grid Step (laps)", 1, 5, 2)

        # Simulation quality
        sims_per_point = st.select_slider(
            "Analysis Quality",
            options=['Quick (10 sims)', 'Standard (30 sims)', 'Thorough (50 sims)'],
            value='Standard (30 sims)'
        )
        sims_map = {'Quick (10 sims)': 10, 'Standard (30 sims)': 30, 'Thorough (50 sims)': 50}
        num_sims = sims_map[sims_per_point]

    with col2:
        st.subheader("Run Analysis")
        run_sensitivity = st.button("📊 Analyze Sensitivity", type="primary")

        if run_sensitivity or 'sensitivity_df' in st.session_state:
            st.write("Analyzing pit timing sensitivity...")
            with st.spinner("Running sensitivity analysis..."):
                df = analyzer.analyze_pit_timing(
                    base_strategy,
                    pit_index=pit_index,
                    lap_range=(min_lap, max_lap),
                    lap_step=lap_step,
                    num_sims_per_point=num_sims,
                    show_progress=False
                )

            st.session_state['sensitivity_df'] = df
            st.session_state['original_lap'] = original_lap

    if 'sensitivity_df' in st.session_state:
        df = st.session_state['sensitivity_df']
        original_lap = st.session_state['original_lap']

        # Summary statistics
        st.subheader("📊 Sensitivity Results")

        optimal_lap = df.loc[df['is_optimal'], 'pit_lap'].values[0]
        optimal_pos = df.loc[df['is_optimal'], 'mean_position'].values[0]
        original_pos = df.loc[df['pit_lap'] == original_lap, 'mean_position'].values[0] if (df['pit_lap'] == original_lap).any() else optimal_pos

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Optimal Lap", int(optimal_lap), f"{optimal_pos:.2f} avg pos")

        with col2:
            improvement = original_pos - optimal_pos
            st.metric("Improvement", f"{improvement:.1f} positions", f"{improvement/original_pos*100:.1f}%")

        with col3:
            variance = df['std_position'].mean()
            st.metric("Avg Variance", f"±{variance:.2f}", "Risk level")

        # Sensitivity curve
        st.subheader("📈 Sensitivity Curve")

        fig = go.Figure()

        # Main line
        fig.add_trace(go.Scatter(
            x=df['pit_lap'],
            y=df['mean_position'],
            mode='lines+markers',
            name='Expected Position',
            line=dict(color='blue', width=2)
        ))

        # Confidence interval
        fig.add_trace(go.Scatter(
            x=df['pit_lap'],
            y=df['mean_position'] + df['std_position'],
            mode='lines',
            line=dict(width=0),
            showlegend=False,
            hoverinfo='skip'
        ))

        fig.add_trace(go.Scatter(
            x=df['pit_lap'],
            y=df['mean_position'] - df['std_position'],
            mode='lines',
            line=dict(width=0),
            fillcolor='rgba(0,100,80,0.2)',
            fill='tonexty',
            name='±1 Std Dev',
            hoverinfo='skip'
        ))

        # Mark original
        if (df['pit_lap'] == original_lap).any():
            orig_y = df.loc[df['pit_lap'] == original_lap, 'mean_position'].values[0]
            fig.add_trace(go.Scatter(
                x=[original_lap],
                y=[orig_y],
                mode='markers',
                marker=dict(size=15, color='red', symbol='x'),
                name=f'Original (Lap {original_lap})'
            ))

        # Mark optimal
        fig.add_trace(go.Scatter(
            x=[optimal_lap],
            y=[optimal_pos],
            mode='markers',
            marker=dict(size=20, color='green', symbol='star'),
            name=f'Optimal (Lap {int(optimal_lap)})'
        ))

        fig.update_layout(
            title="Expected Finishing Position vs. Pit Lap",
            xaxis_title="Pit Lap",
            yaxis_title="Expected Finishing Position",
            yaxis=dict(autorange="reversed"),
            hovermode='x unified',
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

        # Win rate curve
        st.subheader("🏆 Win Rate by Pit Lap")

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df['pit_lap'],
            y=df['win_rate'] * 100,
            mode='lines+markers',
            fill='tozeroy',
            line=dict(color='gold', width=2),
            name='Win Rate'
        ))

        # Mark optimal
        fig.add_trace(go.Scatter(
            x=[optimal_lap],
            y=[df.loc[df['pit_lap'] == optimal_lap, 'win_rate'].values[0] * 100],
            mode='markers',
            marker=dict(size=20, color='green', symbol='star'),
            name='Optimal'
        ))

        fig.update_layout(
            title="Win Rate vs. Pit Lap",
            xaxis_title="Pit Lap",
            yaxis_title="Win Rate (%)",
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB 3: Strategy Optimizer
# ============================================================================
with tab3:
    st.header("Strategy Optimizer")
    st.write("Automatically find optimal pit timing for your strategy")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Strategy Configuration")

        # Select base strategy
        optimize_base = st.selectbox(
            "Base Strategy to Optimize",
            list(PRESET_STRATEGIES.keys()),
            index=0,
            key='optimize_base'
        )

        # Configure search ranges for each pit
        strategy = PRESET_STRATEGIES[optimize_base]

        search_ranges = []
        for i, pit in enumerate(strategy.pit_stops):
            st.write(f"\n**Pit Stop {i+1}** (Original: Lap {pit.lap})")

            col_a, col_b = st.columns(2)
            min_range = col_a.number_input(
                f"Min Lap {i+1}",
                value=min(max(30, pit.lap - 15), num_laps-10),
                min_value=1,
                max_value=num_laps-10,
                key=f'min_pit_{i}'
            )
            max_range = col_b.number_input(
                f"Max Lap {i+1}",
                value=min(num_laps-5, pit.lap + 15),
                min_value=10,
                max_value=num_laps,
                key=f'max_pit_{i}'
            )

            search_ranges.append((min_range, max_range))

        # Optimization quality
        opt_sims = st.select_slider(
            "Optimization Quality",
            options=['Quick (10 sims)', 'Standard (30 sims)', 'Thorough (50 sims)'],
            value='Standard (30 sims)',
            key='opt_quality'
        )
        opt_sims_map = {'Quick (10 sims)': 10, 'Standard (30 sims)': 30, 'Thorough (50 sims)': 50}
        opt_num_sims = opt_sims_map[opt_sims]

    with col2:
        st.subheader("Run Optimization")
        run_optimization = st.button("🎯 Optimize Strategy", type="primary")

        if run_optimization or 'optimized_strategy' in st.session_state:
            st.write("Optimizing pit timing...")
            with st.spinner("Finding optimal pit windows..."):
                optimized = analyzer.optimize_complete_strategy(
                    strategy,
                    search_ranges=search_ranges,
                    num_sims_per_point=opt_num_sims
                )

            st.session_state['optimized_strategy'] = optimized
            st.session_state['original_strategy'] = strategy

            # Evaluate both
            with st.spinner("Evaluating strategies..."):
                original_metrics = evaluator.evaluate_strategy(
                    strategy,
                    num_simulations=100,
                    show_progress=False
                )
                optimized_metrics = evaluator.evaluate_strategy(
                    optimized,
                    num_simulations=100,
                    show_progress=False
                )

            st.session_state['original_metrics'] = original_metrics
            st.session_state['optimized_metrics'] = optimized_metrics

    if 'optimized_strategy' in st.session_state:
        original_metrics = st.session_state['original_metrics']
        optimized_metrics = st.session_state['optimized_metrics']

        st.subheader("🎯 Optimization Results")

        # Comparison
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Original", f"{original_metrics['mean_position']:.2f}")

        with col2:
            st.metric("Optimized", f"{optimized_metrics['mean_position']:.2f}")

        with col3:
            improvement = original_metrics['mean_position'] - optimized_metrics['mean_position']
            st.metric("Improvement", f"{improvement:.2f} positions")

        with col4:
            st.metric("Win Rate", f"{original_metrics['win_rate']:.1%} → {optimized_metrics['win_rate']:.1%}")

        # Pit schedule comparison
        st.subheader("📅 Pit Schedule Comparison")

        comparison_data = {
            'Pit Stop': [],
            'Original Lap': [],
            'Optimized Lap': [],
            'Change': []
        }

        for i, (orig, opt) in enumerate(zip(
            st.session_state['original_strategy'].pit_stops,
            st.session_state['optimized_strategy'].pit_stops
        )):
            comparison_data['Pit Stop'].append(f"Pit {i+1}")
            comparison_data['Original Lap'].append(orig.lap)
            comparison_data['Optimized Lap'].append(opt.lap)
            comparison_data['Change'].append(opt.lap - orig.lap)

        df_compare = pd.DataFrame(comparison_data)
        st.dataframe(df_compare, use_container_width=True)

        # Visual comparison
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Position Distribution")

            fig = go.Figure()

            for name, positions, color in [
                ('Original', original_metrics['positions'], 'blue'),
                ('Optimized', optimized_metrics['positions'], 'green')
            ]:
                fig.add_trace(go.Histogram(
                    name=name,
                    x=positions,
                    opacity=0.6,
                    marker_color=color,
                    nbinsx=20
                ))

            fig.update_layout(
                title="Finishing Position Distribution",
                xaxis_title="Position",
                xaxis=dict(autorange="reversed"),
                yaxis_title="Frequency",
                barmode='overlay',
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Performance Metrics")

            metrics_data = {
                'Metric': ['Mean Position', 'Median', 'Std Dev', 'Win Rate', 'Top-5 Rate', 'Top-10 Rate'],
                'Original': [
                    f"{original_metrics['mean_position']:.2f}",
                    f"{original_metrics['median_position']:.2f}",
                    f"{original_metrics['std_position']:.2f}",
                    f"{original_metrics['win_rate']:.1%}",
                    f"{original_metrics['top5_rate']:.1%}",
                    f"{original_metrics['top10_rate']:.1%}"
                ],
                'Optimized': [
                    f"{optimized_metrics['mean_position']:.2f}",
                    f"{optimized_metrics['median_position']:.2f}",
                    f"{optimized_metrics['std_position']:.2f}",
                    f"{optimized_metrics['win_rate']:.1%}",
                    f"{optimized_metrics['top5_rate']:.1%}",
                    f"{optimized_metrics['top10_rate']:.1%}"
                ]
            }

            df_metrics = pd.DataFrame(metrics_data)
            st.dataframe(df_metrics, use_container_width=True)

# ============================================================================
# TAB 4: Race Replay
# ============================================================================
with tab4:
    st.header("🏁 Race Replay")
    st.write("Watch how a strategy plays out lap-by-lap")

    st.info("""
    📌 **Purpose:** See your strategy in action! This simulates a single race and shows:
    - Lap-by-lap position changes (when you gain/lose positions)
    - The impact of pit timing on race dynamics
    - How your strategy performs under real race conditions

    💡 **Perfect for:** Understanding strategy dynamics before race day
    """)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Configure Race")

        st.info("💡 Configure your car (Car #0). All other cars use auto-generated settings.")

        # Starting grid position
        starting_grid = st.selectbox(
            "Starting Grid Qualifying Position",
            ["Front Row (P1-P5)", "Mid-Pack (P15-P25)", "Back Row (P35-P40)"],
            index=0,
            help="⚠️ Note: Due to traffic dynamics, actual starting position may vary. This sets your car's approximate performance level."
        )

        # Quick strategy config
        race_strategy_name = st.selectbox(
            "Your Car's Strategy",
            list(PRESET_STRATEGIES.keys()),
            index=0,
            key='race_strategy'
        )

        # Custom pit stops
        with st.expander("Custom Pit Stops"):
            use_custom = st.checkbox("Use Custom Pit Stops", key='use_custom_pits')

            if use_custom:
                pit_input = st.text_input("Enter pit laps (comma-separated)", "50, 100, 150", key='custom_pits')
                try:
                    custom_pits = [int(p.strip()) for p in pit_input.split(',')]
                    custom_strategy = Strategy(
                        name='Custom',
                        description='Custom race strategy',
                        pit_stops=[PitStop(lap=p) for p in custom_pits]
                    )
                except:
                    st.error("Invalid pit laps")
                    custom_strategy = None
            else:
                custom_strategy = None

    with col2:
        st.subheader("Controls")
        run_simulation = st.button("▶️ Simulate Race", type="primary")

    if run_simulation:
        strategy = custom_strategy if custom_strategy else PRESET_STRATEGIES[race_strategy_name]

        st.write(f"Simulating race with {strategy.name} strategy...")
        st.info(f"🚦 Strategy: {strategy.name}")

        # Run simulation
        with st.spinner("Simulating..."):
            # Create simulator with fixed seed for reproducibility
            sim = RaceSimulator(num_cars=num_cars, num_laps=num_laps, random_seed=42)
            # Apply track-specific parameters
            sim.config.base_lap_time = track_profile.base_lap_time
            sim.config.tire_degradation_rate = track_profile.tire_degradation_rate
            sim.config.caution_base_prob = track_profile.caution_base_prob
            sim.config.traffic_penalty_factor = track_profile.traffic_penalty_factor
            sim.config.min_lap_time = track_profile.base_lap_time - 3.0
            sim.config.max_lap_time = track_profile.base_lap_time + 7.0
            sim.track_length = track_profile.length_miles
            sim.stage_laps = [track_profile.stage1_end, track_profile.stage2_end]
            sim.initialize_cars()

            # Adjust car #0's performance to match requested grid
            target_positions = {
                "Front Row (P1-P5)": 3,
                "Mid-Pack (P15-P25)": 20,
                "Back Row (P35-P40)": 38
            }
            target_pos = target_positions[starting_grid]

            # Collect all physics and sort by speed to find target position
            all_physics = [car.physics for car in sim.cars]
            indices_by_speed = sorted(range(len(all_physics)), key=lambda i: all_physics[i].base_lap_time)
            target_idx = indices_by_speed[target_pos - 1]

            # Swap car #0's physics with the target position's physics
            # This ensures the field stays consistent (no duplicate physics)
            all_physics[0], all_physics[target_idx] = all_physics[target_idx], all_physics[0]

            # Re-initialize cars with the swapped physics
            sim.initialize_cars(car_physics=all_physics)

            # Apply the selected strategy to car #0 (your car)
            # All other cars will use auto-generated default strategies
            our_car_strategy = {
                0: strategy.pit_stops
            }

            # Simulate the race (skip initialization since we've set up car physics)
            result = sim.simulate_race(strategy=our_car_strategy, skip_init=True)

            # Determine actual starting position and grid
            actual_starting_pos = result['lap_history'][0]['positions'][0]

            # Determine which grid this actually is
            if actual_starting_pos <= 5:
                actual_grid = "Front Row (P1-P5)"
            elif actual_starting_pos <= 25:
                actual_grid = "Mid-Pack (P15-P25)"
            else:
                actual_grid = "Back Row (P35-P40)"

            # Show what actually happened
            grid_display = f"{actual_grid}"
            if actual_grid != starting_grid:
                grid_display += f" (Target: {starting_grid})"

        # Display results
        st.success("✅ Simulation Complete!")

        # Calculate actual starting position and finishing position
        actual_starting_pos = result['lap_history'][0]['positions'][0]
        our_finish = result['final_positions'][0]
        positions_gained = actual_starting_pos - our_finish

        # Show grid and results
        st.metric("Starting Position", f"P{actual_starting_pos}", delta=f"{grid_display}")

        # Add explanation if grid doesn't match request
        if actual_grid != starting_grid:
            st.caption("💡 Note: Actual starting position may differ from qualifying target due to:")
            st.caption("   • Traffic dynamics on lap 1 (cars ahead get clean air)")
            st.caption("   • Random variation in lap times even with identical physics")
            st.caption("   • Overtaking ability differences between cars")

        # Show positions gained/lost
        if positions_gained > 0:
            st.success(f"📈 Gained {positions_gained} positions during race!")
        elif positions_gained < 0:
            st.warning(f"📉 Lost {abs(positions_gained)} positions during race")
        else:
            st.info("➖ Maintained position throughout race")

        # Winner
        winner = result['winner']
        if winner == 0:
            st.success(f"🏆 Your Car (#0) Won!")
        else:
            st.info(f"🏆 Winner: Car #{winner}")

        # Final positions
        st.subheader("📊 Final Standings")

        # Create positions table
        positions_data = []
        for car_id, position in result['final_positions'].items():
            positions_data.append({
                'Position': position,
                'Car': car_id,
                'Time': f"{result['final_times'][car_id]:.1f}s"
            })

        df_positions = pd.DataFrame(positions_data).sort_values('Position')
        st.dataframe(df_positions, use_container_width=True, height=400)

        # Lap chart visualization
        st.subheader("📊 Lap Chart - Position History")

        # Prepare lap chart data
        lap_chart_data = []
        for lap_entry in result['lap_history']:
            for car_id, position in enumerate(lap_entry['positions']):
                lap_chart_data.append({
                    'Lap': lap_entry['lap'],
                    'Car': f"Car {car_id}",
                    'Position': position
                })

        df_lap_chart = pd.DataFrame(lap_chart_data)

        # Create lap chart (top 10 cars only for readability)
        top_cars = df_positions['Car'].head(10).tolist()
        df_lap_chart_top = df_lap_chart[df_lap_chart['Car'].isin([f"Car {c}" for c in top_cars])]

        fig = px.line(
            df_lap_chart_top,
            x='Lap',
            y='Position',
            color='Car',
            title='Position Changes Throughout Race (Top 10)',
            markers=False,
            height=500
        )

        fig.update_layout(
            yaxis=dict(autorange="reversed"),
            xaxis_title="Lap Number",
            yaxis_title="Position"
        )

        st.plotly_chart(fig, use_container_width=True)

        # Lap times
        st.subheader("⏱️ Lap Times Analysis")

        # Calculate average lap times by car
        lap_time_data = []
        for lap_entry in result['lap_history']:
            for car_id, lap_time in enumerate(lap_entry['lap_times']):
                lap_time_data.append({
                    'Lap': lap_entry['lap'],
                    'Car': f"Car {car_id}",
                    'Lap Time': lap_time
                })

        df_lap_times = pd.DataFrame(lap_time_data)

        # Average lap times (top 10)
        avg_lap_times = df_lap_times[df_lap_times['Car'].isin([f"Car {c}" for c in top_cars])].groupby('Car')['Lap Time'].mean().sort_values()

        fig = go.Figure(data=[
            go.Bar(
                x=avg_lap_times.values,
                y=avg_lap_times.index,
                orientation='h',
                marker_color='darkblue'
            )
        ])

        fig.update_layout(
            title="Average Lap Time by Car (Top 10)",
            xaxis_title="Average Lap Time (seconds)",
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB 5: Live Decisions
# ============================================================================
with tab5:
    st.header("⚡ Live Race Decisions")
    st.write(f"Get real-time probabilistic recommendations for **{track_profile.name}** ({track_profile.length_miles} mi, {num_laps} laps)")

    # Initialize decision engine
    @st.cache_resource
    def get_decision_engine():
        """Get cached decision engine"""
        return ProbabilisticDecisionEngine(n_bootstrap=1000)

    decision_engine = get_decision_engine()

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Current Race Situation")

        # Race state inputs
        col_a, col_b = st.columns(2)
        current_lap = col_a.number_input("Current Lap", min_value=1, max_value=num_laps, value=min(80, num_laps // 2))
        current_position = col_b.number_input("Current Position", min_value=1, max_value=43, value=15)

        col_c, col_d = st.columns(2)
        tire_age = col_c.number_input("Tire Age (laps)", min_value=0, max_value=100, value=40)
        fuel_level = col_d.slider("Fuel Level (%)", 0, 100, 60)

        # Caution flag
        caution_active = st.checkbox("🚩 Caution Flag Active", value=False)

        # Decision context
        st.info("ℹ️ The system will simulate both pitting now and staying out, then provide a probabilistic recommendation.")

    with col2:
        st.subheader("Analyze Decision")
        num_sims_per_option = st.slider("Simulations per Option", 50, 200, 100, 10)

        # Quick decision quality
        decision_quality = st.select_slider(
            "Analysis Quality",
            options=['Fast (50 sims)', 'Standard (100 sims)', 'Thorough (200 sims)'],
            value='Standard (100 sims)'
        )
        sims_map = {'Fast (50 sims)': 50, 'Standard (100 sims)': 100, 'Thorough (200 sims)': 200}
        num_sims_per_option = sims_map[decision_quality]

        run_decision = st.button("🎲 Analyze Decision", type="primary")

    if run_decision:
        st.write("Analyzing decision...")

        with st.spinner("Running Monte Carlo simulations for both options..."):
            # Create two strategies: pit now vs stay out
            # Strategy 1: Pit now
            remaining_laps = num_laps - current_lap

            # Estimate remaining pit stops based on race length
            if remaining_laps > 100:
                remaining_pits = [current_lap + 50, current_lap + 100]
            elif remaining_laps > 50:
                remaining_pits = [current_lap + 50]
            else:
                remaining_pits = []

            pit_now_strategy = Strategy(
                name="Pit Now",
                description=f"Pit on lap {current_lap}",
                pit_stops=[PitStop(lap=current_lap)] + [PitStop(lap=lap) for lap in remaining_pits]
            )

            # Strategy 2: Stay out - smarter logic
            # Consider tire life, fuel level, and race remaining
            # Modern NASCAR tires can last 80-100+ laps depending on track
            # Charlotte is intermediate, so we use a conservative estimate
            max_tire_life = 120  # Maximum competitive tire life in laps (increased from 100)

            # Calculate if we need to pit based on multiple factors
            need_fuel = fuel_level < 70  # Need fuel if below 70%
            tires_will_be_old = (tire_age + remaining_laps) > max_tire_life
            short_race = remaining_laps < 50  # Short remaining distance

            # Decision logic for Stay Out strategy
            if not need_fuel and not tires_will_be_old:
                # Best case: good fuel, tires can make it
                stay_out_pits = []
            elif not need_fuel and tires_will_be_old and not short_race:
                # Good fuel but tires will wear - schedule strategic pit
                # Pit when tires would be ~90 laps old for optimal performance
                laps_until_pit = max(30, max_tire_life - tire_age - 30)  # Keep some margin
                next_pit_lap = current_lap + laps_until_pit
                # Make sure pit is not after race ends
                if next_pit_lap < num_laps:
                    stay_out_pits = [next_pit_lap]
                else:
                    stay_out_pits = []
            elif short_race:
                # Short remaining distance - stay out regardless
                stay_out_pits = []
            else:
                # Default: need fuel, so plan a pit
                next_pit_lap = current_lap + min(30, remaining_laps // 2)
                if next_pit_lap < num_laps:
                    stay_out_pits = [next_pit_lap]
                else:
                    stay_out_pits = []

            stay_out_strategy = Strategy(
                name="Stay Out",
                description=f"Stay out on lap {current_lap}",
                pit_stops=[PitStop(lap=lap) for lap in stay_out_pits]
            )

            # Prepare mid-race state for realistic simulation
            mid_race_state = {
                'current_lap': current_lap,
                'current_position': current_position,
                'tire_age': tire_age,
                'fuel_level': fuel_level
            }

            # Evaluate both strategies with mid-race state
            pit_metrics = evaluator.evaluate_strategy(
                pit_now_strategy,
                num_simulations=num_sims_per_option,
                show_progress=False,
                mid_race_state=mid_race_state
            )

            stay_out_metrics = evaluator.evaluate_strategy(
                stay_out_strategy,
                num_simulations=num_sims_per_option,
                show_progress=False,
                mid_race_state=mid_race_state
            )

            # Analyze decision probabilistically
            decision = decision_engine.analyze_pit_decision(
                pit_metrics,
                stay_out_metrics,
                decision_context={
                    'lap': current_lap,
                    'position': current_position,
                    'tire_age': tire_age,
                    'fuel_level': fuel_level,
                    'caution': caution_active
                }
            )

            # Store in session state
            st.session_state['decision_result'] = (decision, pit_metrics, stay_out_metrics)
            st.session_state['decision_context'] = {
                'lap': current_lap,
                'position': current_position,
                'tire_age': tire_age,
                'fuel_level': fuel_level
            }

    if 'decision_result' in st.session_state:
        decision, pit_metrics, stay_out_metrics = st.session_state['decision_result']
        context = st.session_state.get('decision_context', {})

        # Display recommendation prominently
        st.subheader("🎯 Recommendation")

        # Color-code recommendation
        rec_color = {
            'pit': '🟢',
            'stay_out': '🔴',
            'toss_up': '🟡'
        }

        st.markdown(f"### {rec_color.get(decision.recommendation, '⚪')} {decision.recommendation.replace('_', ' ').upper()}")
        # decision.probability is P(pit is better). Show the correct % for the recommendation.
        display_prob = decision.probability if decision.recommendation == 'pit' else (1 - decision.probability)
        st.write(f"**Probability:** {display_prob * 100:.1f}% confidence that {decision.recommendation.replace('_', ' ')} is better")
        st.write(f"**Confidence Level:** {decision.confidence.upper()} ({decision.sample_size} total simulations)")

        # Detailed comparison
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("If You Pit 🏁")
            st.metric("Expected Position", f"{pit_metrics['mean_position']:.1f}")
            st.metric("Top-10 Probability", f"{pit_metrics['top10_rate']:.1%}")
            st.metric("Win Probability", f"{pit_metrics['win_rate']:.1%}")
            st.metric("Std Deviation", f"±{pit_metrics['std_position']:.1f}")

        with col2:
            st.subheader("If You Stay Out 🔵")
            st.metric("Expected Position", f"{stay_out_metrics['mean_position']:.1f}")
            st.metric("Top-10 Probability", f"{stay_out_metrics['top10_rate']:.1%}")
            st.metric("Win Probability", f"{stay_out_metrics['win_rate']:.1%}")
            st.metric("Std Deviation", f"±{stay_out_metrics['std_position']:.1f}")

        # Expected improvement
        st.subheader("📊 Expected Impact")

        improvement = stay_out_metrics['mean_position'] - pit_metrics['mean_position']
        if improvement > 0:
            st.success(f"✅ Pitting improves expected finishing position by **{improvement:.1f} positions**")
        elif improvement < 0:
            st.warning(f"⚠️ Staying out improves expected finishing position by **{abs(improvement):.1f} positions**")
        else:
            st.info("ℹ️ Both strategies have similar expected outcomes")

        # Position distributions
        st.subheader("📈 Position Distribution Comparison")

        fig = go.Figure()

        fig.add_trace(go.Histogram(
            name='Pit Now',
            x=pit_metrics['positions'],
            opacity=0.6,
            marker_color='green',
            nbinsx=20
        ))

        fig.add_trace(go.Histogram(
            name='Stay Out',
            x=stay_out_metrics['positions'],
            opacity=0.6,
            marker_color='blue',
            nbinsx=20
        ))

        fig.update_layout(
            title="Distribution of Finishing Positions",
            xaxis_title="Finishing Position",
            xaxis=dict(autorange="reversed"),
            yaxis_title="Frequency",
            barmode='overlay',
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

        # Risk assessment
        st.subheader("⚠️ Risk Assessment")

        pit_p95 = np.percentile(pit_metrics['positions'], 95)
        stay_out_p95 = np.percentile(stay_out_metrics['positions'], 95)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Pitting - Worst 5%",
                f"P{pit_p95:.0f}",
                help="95th percentile (worst case scenario)"
            )

        with col2:
            st.metric(
                "Staying Out - Worst 5%",
                f"P{stay_out_p95:.0f}",
                help="95th percentile (worst case scenario)"
            )

        with col3:
            if pit_p95 < stay_out_p95:
                st.metric("Lower Risk", "Pitting", "Better worst case")
            else:
                st.metric("Lower Risk", "Staying Out", "Better worst case")

        # Effect size interpretation
        st.subheader("📏 Statistical Significance")

        effect_magnitude = abs(decision.effect_size)
        if effect_magnitude < 0.2:
            effect_interp = "Negligible"
        elif effect_magnitude < 0.5:
            effect_interp = "Small"
        elif effect_magnitude < 0.8:
            effect_interp = "Medium"
        else:
            effect_interp = "Large"

        st.write(f"**Effect Size (Cohen's d):** {decision.effect_size:.2f} - {effect_interp} effect")

        if decision.probability >= 0.7 or decision.probability <= 0.3:
            st.success("✅ **Clear Choice** - Strong evidence supports the recommendation")
        elif decision.probability >= 0.6 or decision.probability <= 0.4:
            st.info("ℹ️ **Moderate Preference** - Slight advantage to recommended option")
        else:
            st.warning("⚠️ **Close Call** - Consider other factors like driver preference, track conditions, etc.")

        # Context summary
        st.subheader("📝 Decision Context")
        context_df = pd.DataFrame([{
            'Lap': context.get('lap', '-'),
            'Position': context.get('position', '-'),
            'Tire Age': f"{context.get('tire_age', '-')} laps",
            'Fuel Level': f"{context.get('fuel_level', '-')}%"
        }])
        st.dataframe(context_df, use_container_width=True, hide_index=True)

# ============================================================================
# Footer
# ============================================================================
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: gray;'>
        <p>NASCAR AI Strategy Engine - Built with ❤️ for data science and motorsport</p>
        <p>Using: Physics Simulation | Machine Learning | Monte Carlo | Sensitivity Analysis</p>
    </div>
""", unsafe_allow_html=True)
