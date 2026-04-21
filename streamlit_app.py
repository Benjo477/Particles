from typing import List, Tuple

import matplotlib.pyplot as plt
import streamlit as st


# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(
    page_title="Feeding Optimisation Tool",
    page_icon="🐟",
    layout="wide",
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
    settling_by_tank = {
        "Shrimp Tank": 0.18,
        "Fish Tank": 0.20,
        "Mixed Tank": 0.19,
        "Custom": 0.20,
    }

    filtration_by_strength = {
        "Weak": 0.10,
        "Medium": 0.20,
        "Strong": 0.30,
    }

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

    return sorted(set(parsed_times))


def run_simulation(
    feed_times: List[int],
    simulation_length: int,
    feed_amount: float,
    k_s: float,
    k_c: float,
    k_f: float,
) -> List[float]:
    p = 0.0
    results: List[float] = []

    total_removal = k_s + k_c + k_f

    for t in range(simulation_length):
        if t in feed_times:
            p += feed_amount

        p = p - total_removal * p
        p = max(p, 0.0)
        results.append(p)

    return results


def time_to_clear(values: List[float], threshold_ratio: float = 0.05) -> int | None:
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


def time_to_baseline(values: List[float], absolute_threshold: float = 0.05) -> int | None:
    if not values:
        return None

    peak = max(values)
    if peak <= 0:
        return 0

    peak_index = values.index(peak)

    for i in range(peak_index, len(values)):
        if values[i] <= absolute_threshold:
            return i - peak_index

    return None


def detect_overlap(values: List[float], feed_times: List[int]) -> bool:
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


def recommended_gap(values: List[float]) -> int | None:
    clear_time = time_to_clear(values)
    if clear_time is None:
        return None
    return max(clear_time + 2, 1)


def area_under_curve(values: List[float]) -> float:
    return sum(values)


def build_interpretation(
    values: List[float],
    feed_times: List[int],
    feed_amount: float,
    k_s: float,
    k_c: float,
    k_f: float,
) -> Tuple[str, str, List[str], List[str]]:
    notes: List[str] = []
    actions: List[str] = []

    if not feed_times:
        return (
            "info",
            "No feeding events set",
            ["No feed was added in the current simulation."],
            ["Add at least one feeding time to simulate a real feeding pattern."],
        )

    peak = max(values) if values else 0.0
    clear_time = time_to_clear(values)
    baseline_time = time_to_baseline(values)
    overlap = detect_overlap(values, feed_times)
    total_removal = k_s + k_c + k_f
    gap = recommended_gap(values)

    high_peak = peak > 6
    moderate_peak = 4 < peak <= 6
    slow_clear = clear_time is not None and clear_time > 12
    moderate_clear = clear_time is not None and 7 <= clear_time <= 12
    very_fast_clear = clear_time is not None and clear_time < 4

    notes.append(f"Peak concentration reaches {peak:.2f}.")
    if clear_time is not None:
        notes.append(f"Particle concentration falls to 5% of peak after {clear_time} steps.")
    if baseline_time is not None:
        notes.append(f"The system returns close to baseline after about {baseline_time} steps.")
    notes.append(f"Combined removal strength is {total_removal:.2f} per timestep.")

    if overlap:
        notes.append("A later feeding event occurs before the system has recovered.")
        actions.append("Increase the gap between feeds.")
    if high_peak:
        notes.append("The concentration spike is high, suggesting a stronger waste load.")
        actions.append("Reduce feed amount slightly.")
    elif moderate_peak:
        notes.append("The concentration spike is moderate but worth monitoring.")
    if slow_clear:
        notes.append("Particles remain elevated for a long time, suggesting weak clearance.")
        actions.append("Reduce feed or improve filtration.")
    elif moderate_clear:
        notes.append("Clearance is acceptable, but not especially fast.")
    if very_fast_clear:
        notes.append("The system clears very quickly.")
        actions.append("This setup may tolerate a slightly shorter feeding gap if needed.")

    if gap is not None:
        actions.append(f"Recommended minimum gap between feeds: about {gap} steps.")

    if overlap or high_peak or slow_clear:
        verdict = "warning"
        verdict_text = "Overfeeding or slow-clearance risk detected"
    elif moderate_peak or moderate_clear:
        verdict = "info"
        verdict_text = "Feeding pattern is workable, but could be improved"
    else:
        verdict = "success"
        verdict_text = "Feeding pattern looks balanced for the chosen setup"

    if not actions:
        actions.append("Current setup looks stable. No major change is needed.")

    return verdict, verdict_text, notes, actions


def suggest_feed_times(
    original_feed_times: List[int],
    values: List[float],
    simulation_length: int,
) -> str:
    if not original_feed_times:
        return "No suggestion available."

    gap = recommended_gap(values)
    if gap is None:
        return "No suggestion available."

    if len(original_feed_times) == 1:
        return f"If you want a second feed, try around step {original_feed_times[0] + gap}."

    suggested = [original_feed_times[0]]
    for i in range(1, len(original_feed_times)):
        suggested.append(suggested[-1] + gap)

    suggested = [t for t in suggested if t < simulation_length]
    return "Suggested spacing: " + ", ".join(str(t) for t in suggested)


# -----------------------------
# Sidebar controls
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
        max_value=300,
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

    st.header("Comparison")
    show_baseline = st.checkbox("Compare with baseline single-feed scenario", value=True)


# -----------------------------
# Run main simulation
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

baseline_times = [10] if simulation_length > 10 else [0]
baseline_values = run_simulation(
    feed_times=baseline_times,
    simulation_length=simulation_length,
    feed_amount=feed_amount,
    k_s=k_s,
    k_c=k_c,
    k_f=k_f,
)

verdict_level, verdict_text, notes, actions = build_interpretation(
    values=values,
    feed_times=feed_times,
    feed_amount=feed_amount,
    k_s=k_s,
    k_c=k_c,
    k_f=k_f,
)

peak_value = max(values) if values else 0.0
clear_steps = time_to_clear(values)
total_removal = k_s + k_c + k_f
gap = recommended_gap(values)
auc = area_under_curve(values)

baseline_auc = area_under_curve(baseline_values)
auc_diff = auc - baseline_auc


# -----------------------------
# Top metrics
# -----------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Peak Concentration", f"{peak_value:.2f}")
col2.metric("Time to Clear", "N/A" if clear_steps is None else f"{clear_steps} steps")
col3.metric("Recommended Feed Gap", "N/A" if gap is None else f"{gap} steps")
col4.metric("Total Removal Rate", f"{total_removal:.2f}")


# -----------------------------
# Main graph
# -----------------------------
fig, ax = plt.subplots(figsize=(11, 5.5))

time_axis = list(range(simulation_length))
ax.plot(time_axis, values, linewidth=2.5, label="Current Strategy")

if show_baseline:
    ax.plot(
        time_axis,
        baseline_values,
        linewidth=2,
        linestyle="--",
        label="Baseline Single Feed",
    )

for idx, ft in enumerate(feed_times):
    ax.axvline(
        x=ft,
        linestyle="--",
        linewidth=1,
        alpha=0.6,
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
# Comparison section
# -----------------------------
comp1, comp2, comp3 = st.columns(3)
comp1.metric("Total Particle Load", f"{auc:.2f}")
comp2.metric(
    "Vs Baseline Load",
    f"{auc_diff:+.2f}" if show_baseline else "Hidden",
)
comp3.metric(
    "Feed Events",
    f"{len(feed_times)}",
)

if show_baseline:
    if auc_diff > 2:
        st.warning("Your current strategy creates noticeably more total particle load than the baseline.")
    elif auc_diff < -2:
        st.success("Your current strategy creates less total particle load than the baseline.")
    else:
        st.info("Your current strategy is broadly similar to the baseline in total particle load.")


# -----------------------------
# Setup summary
# -----------------------------
with st.expander("Current Setup Summary", expanded=False):
    st.write(f"**Tank Type:** {tank_type}")
    st.write(f"**Filtration Strength:** {filtration_strength}")
    st.write(f"**Stocking Level:** {stocking_level}")
    st.write(f"**Model Rates:** kₛ = {k_s:.2f}, k_c = {k_c:.2f}, k_f = {k_f:.2f}")
    st.write(f"**Feed Times:** {feed_times if feed_times else 'None'}")
    st.write(f"**Feed Amount per Event:** {feed_amount:.2f}")


# -----------------------------
# Verdict
# -----------------------------
if verdict_level == "success":
    st.success(verdict_text)
elif verdict_level == "warning":
    st.warning(verdict_text)
else:
    st.info(verdict_text)


# -----------------------------
# Interpretation and action
# -----------------------------
left, right = st.columns(2)

with left:
    st.subheader("Interpretation")
    for note in notes:
        st.write(f"- {note}")

with right:
    st.subheader("Recommended Action")
    for action in actions:
        st.write(f"- {action}")

    st.write(f"- {suggest_feed_times(feed_times, values, simulation_length)}")


# -----------------------------
# Quick scenarios
# -----------------------------
st.subheader("Quick Scenario Ideas")

q1, q2, q3 = st.columns(3)

with q1:
    st.markdown("**Normal Feeding**")
    st.code("10", language=None)

with q2:
    st.markdown("**Double Feeding**")
    st.code("10, 15", language=None)

with q3:
    st.markdown("**Missed Feeding**")
    st.write("Leave the field blank")
