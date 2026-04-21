import math
from typing import List, Tuple

import matplotlib.pyplot as plt
import streamlit as st


# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(
    page_title="Feeding Optimisation Tool",
    page_icon="🐟",
    layout="centered",
)

st.title("Feeding Optimisation Tool")
st.write(
    "Simulate how feed particles behave over time under different feeding strategies "
    "and tank conditions."
)


# -----------------------------
# Helper functions
# -----------------------------
def map_setup_to_rates(
    tank_type: str,
    filtration_strength: str,
    stocking_level: str,
) -> Tuple[float, float, float]:
    """
    Convert user-friendly real-world choices into model parameters.
    These are starting-point approximations, not exact measured values.
    """

    # Settling rate: how quickly particles drop out of suspension
    settling_by_tank = {
        "Shrimp Tank": 0.18,
        "Fish Tank": 0.20,
        "Mixed Tank": 0.19,
        "Custom": 0.20,
    }

    # Filtration rate: how efficiently the system removes particles
    filtration_by_strength = {
        "Weak": 0.10,
        "Medium": 0.20,
        "Strong": 0.30,
    }

    # Consumption rate: how quickly livestock consume suspended feed
    consumption_by_stock = {
        "Light": 0.06,
        "Moderate": 0.10,
        "Heavy": 0.16,
    }

    k_s = settling_by_tank[tank_type]
    k_f = filtration_by_strength[filtration_strength]
    k_c = consumption_by_stock[stocking_level]

    return k_s, k_c, k_f


def parse_feed_times(feed_times_text: str, simulation_length: int) -> List[int]:
    """
    Parse comma-separated feed times, e.g. '10, 20, 35'
    """
    if not feed_times_text.strip():
        return []

    parsed_times: List[int] = []
    raw_parts = feed_times_text.split(",")

    for part in raw_parts:
        stripped = part.strip()
        if not stripped:
            continue

        try:
            value = int(stripped)
        except ValueError:
            continue

        if 0 <= value < simulation_length:
            parsed_times.append(value)

    # Remove duplicates and sort
    return sorted(set(parsed_times))


def run_simulation(
    feed_times: List[int],
    simulation_length: int,
    feed_amount: float,
    k_s: float,
    k_c: float,
    k_f: float,
) -> List[float]:
    """
    Run the particle concentration simulation.
    """
    p = 0.0
    results: List[float] = []

    total_removal = k_s + k_c + k_f

    for t in range(simulation_length):
        if t in feed_times:
            p += feed_amount

        p = p - total_removal * p
        p = max(p, 0.0)  # enforce non-negativity
        results.append(p)

    return results


def time_to_clear(values: List[float], threshold_ratio: float = 0.05) -> int | None:
    """
    Return the timestep when concentration falls below a fraction of the peak.
    Example: threshold_ratio=0.05 means '5% of peak'.
    """
    if not values:
        return None

    peak = max(values)
    if peak <= 0:
        return 0

    threshold = peak * threshold_ratio

    peak_index = values.index(peak)
    for i in range(peak_index, len(values)):
        if values[i] <= threshold:
            return i - peak_index

    return None


def detect_overlap(values: List[float], feed_times: List[int]) -> bool:
    """
    Simple overlap detection:
    if a later feed occurs while concentration is still > 20% of the first peak,
    treat that as overlap / insufficient recovery.
    """
    if len(feed_times) < 2 or not values:
        return False

    peak = max(values)
    if peak <= 0:
        return False

    threshold = peak * 0.20
    for ft in feed_times[1:]:
        if 0 <= ft < len(values) and values[ft] > threshold:
            return True

    return False


def build_interpretation(
    values: List[float],
    feed_times: List[int],
    feed_amount: float,
    k_s: float,
    k_c: float,
    k_f: float,
) -> Tuple[str, str, List[str]]:
    """
    Return:
    - verdict level
    - short verdict text
    - list of actionable notes
    """
    notes: List[str] = []

    if not feed_times:
        return (
            "info",
            "No feeding events set",
            [
                "Add one or more feeding times to simulate a real feeding pattern."
            ],
        )

    peak = max(values) if values else 0.0
    clear_time = time_to_clear(values)
    overlap = detect_overlap(values, feed_times)
    total_removal = k_s + k_c + k_f

    # Interpretation rules
    high_peak = peak > 6
    slow_clear = clear_time is not None and clear_time > 12
    very_fast_clear = clear_time is not None and clear_time < 4

    if overlap:
        notes.append(
            "A later feeding event occurs before the system has properly recovered."
        )
        notes.append("Try increasing the gap between feeds.")
    if high_peak:
        notes.append(
            "Peak particle concentration is high, which may indicate overfeeding risk."
        )
        notes.append("Try reducing feed amount slightly.")
    if slow_clear:
        notes.append(
            "Particles remain elevated for a long time, suggesting weak clearance."
        )
        notes.append("Consider reducing feed or improving filtration.")
    if very_fast_clear and feed_amount > 0:
        notes.append(
            "The system clears very quickly, which may mean the setup can tolerate more frequent feeding."
        )

    notes.append(
        f"Combined removal strength is {total_removal:.2f} per timestep."
    )

    # Main verdict
    if overlap or high_peak or slow_clear:
        return (
            "warning",
            "Overfeeding or slow-clearance risk detected",
            notes,
        )

    return (
        "success",
        "Feeding pattern looks balanced for the chosen setup",
        notes if notes else ["The concentration spike clears at a reasonable rate."],
    )


# -----------------------------
# Sidebar / controls
# -----------------------------
with st.sidebar:
    st.header("Tank Setup")

    tank_type = st.selectbox(
        "Tank Type",
        ["Shrimp Tank", "Fish Tank", "Mixed Tank", "Custom"],
    )

    filtration_strength = st.selectbox(
        "Filtration Strength",
        ["Weak", "Medium", "Strong"],
        index=1,
    )

    stocking_level = st.selectbox(
        "Stocking Level",
        ["Light", "Moderate", "Heavy"],
        index=1,
    )

    simulation_length = st.slider(
        "Simulation Length",
        min_value=30,
        max_value=200,
        value=100,
        step=10,
    )

    st.header("Feeding Strategy")

    feed_amount = st.slider(
        "Feed Amount per Event",
        min_value=0.5,
        max_value=20.0,
        value=5.0,
        step=0.5,
    )

    feed_times_text = st.text_input(
        "Feeding Times",
        value="10",
        help="Enter timesteps separated by commas, for example: 10, 20, 35",
    )

    st.caption("Example scenarios:")
    st.caption("- Normal feeding: 10")
    st.caption("- Double feeding: 10, 15")
    st.caption("- Missed feeding: leave blank")

    use_custom_rates = st.checkbox("Use Custom Model Rates")

    if use_custom_rates:
        st.header("Custom Model Rates")
        k_s = st.slider("Settling Rate (kₛ)", 0.00, 0.50, 0.20, 0.01)
        k_c = st.slider("Consumption Rate (k_c)", 0.00, 0.50, 0.10, 0.01)
        k_f = st.slider("Filtration Rate (k_f)", 0.00, 0.50, 0.20, 0.01)
    else:
        k_s, k_c, k_f = map_setup_to_rates(
            tank_type=tank_type,
            filtration_strength=filtration_strength,
            stocking_level=stocking_level,
        )


# -----------------------------
# Main simulation
# -----------------------------
feed_times = parse_feed_times(feed_times_text, simulation_length)
values = run_simulation(
    feed_times=feed_times,
    simulation_length=simulation_length,
    feed_amount=feed_amount,
    k_s=k_s,
    k_c=k_c,
    k_f=k_f,
)

verdict_level, verdict_text, notes = build_interpretation(
    values=values,
    feed_times=feed_times,
    feed_amount=feed_amount,
    k_s=k_s,
    k_c=k_c,
    k_f=k_f,
)


# -----------------------------
# Summary metrics
# -----------------------------
peak_value = max(values) if values else 0.0
clear_steps = time_to_clear(values)
total_removal = k_s + k_c + k_f

metric_col1, metric_col2, metric_col3 = st.columns(3)
metric_col1.metric("Peak Concentration", f"{peak_value:.2f}")
metric_col2.metric(
    "Time to Clear",
    "N/A" if clear_steps is None else f"{clear_steps} steps",
)
metric_col3.metric("Total Removal Rate", f"{total_removal:.2f}")


# -----------------------------
# Main graph
# -----------------------------
fig, ax = plt.subplots(figsize=(10, 5))

time_axis = list(range(simulation_length))
ax.plot(time_axis, values, linewidth=2, label="Particle Concentration")

# Mark feeding events
for idx, ft in enumerate(feed_times):
    ax.axvline(
        x=ft,
        linestyle="--",
        linewidth=1,
        alpha=0.7,
        label="Feed Event" if idx == 0 else None,
    )

ax.set_title("Particle Concentration Over Time")
ax.set_xlabel("Time")
ax.set_ylabel("Particle Concentration")
ax.grid(True, alpha=0.3)
ax.legend()
plt.tight_layout()

st.pyplot(fig)


# -----------------------------
# Real-world setup summary
# -----------------------------
with st.expander("Current Setup Summary", expanded=False):
    st.write(f"**Tank Type:** {tank_type}")
    st.write(f"**Filtration Strength:** {filtration_strength}")
    st.write(f"**Stocking Level:** {stocking_level}")
    st.write(
        f"**Model Rates:** kₛ = {k_s:.2f}, k_c = {k_c:.2f}, k_f = {k_f:.2f}"
    )
    st.write(f"**Feed Times:** {feed_times if feed_times else 'None'}")
    st.write(f"**Feed Amount per Event:** {feed_amount:.2f}")


# -----------------------------
# Verdict / interpretation
# -----------------------------
if verdict_level == "success":
    st.success(verdict_text)
elif verdict_level == "warning":
    st.warning(verdict_text)
else:
    st.info(verdict_text)

st.subheader("Interpretation")
for note in notes:
    st.write(f"- {note}")


# -----------------------------
# Suggested scenarios
# -----------------------------
st.subheader("Quick Scenario Ideas")

quick_col1, quick_col2, quick_col3 = st.columns(3)

with quick_col1:
    st.markdown("**Normal Feeding**")
    st.write("Try: `10`")

with quick_col2:
    st.markdown("**Double Feeding**")
    st.write("Try: `10, 15`")

with quick_col3:
    st.markdown("**Missed Feeding**")
    st.write("Try leaving the field blank")
