from __future__ import annotations

from typing import List, Tuple, Dict

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
def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


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

    parsed: List[int] = []
    for part in feed_times_text.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            t = int(part)
        except ValueError:
            continue
        if 0 <= t < simulation_length:
            parsed.append(t)

    return sorted(set(parsed))


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


def area_under_curve(values: List[float]) -> float:
    return sum(values)


def max_value(values: List[float]) -> float:
    return max(values) if values else 0.0


def time_to_threshold_after_feed(
    values: List[float],
    start_index: int,
    threshold: float,
) -> int | None:
    if not values or start_index >= len(values):
        return None

    for i in range(start_index, len(values)):
        if values[i] <= threshold:
            return i - start_index
    return None


def time_to_clear(values: List[float], threshold_ratio: float = 0.05) -> int | None:
    peak = max_value(values)
    if peak <= 0:
        return 0
    peak_index = values.index(peak)
    threshold = peak * threshold_ratio
    return time_to_threshold_after_feed(values, peak_index, threshold)


def time_to_baseline(values: List[float], absolute_threshold: float = 0.05) -> int | None:
    peak = max_value(values)
    if peak <= 0:
        return 0
    peak_index = values.index(peak)
    return time_to_threshold_after_feed(values, peak_index, absolute_threshold)


def detect_overlap(values: List[float], feed_times: List[int]) -> bool:
    if len(feed_times) < 2 or not values:
        return False

    first_peak = max_value(values)
    if first_peak <= 0:
        return False

    threshold = first_peak * 0.20
    for ft in feed_times[1:]:
        if 0 <= ft < len(values) and values[ft] > threshold:
            return True
    return False


def average_feed_gap(feed_times: List[int]) -> float | None:
    if len(feed_times) < 2:
        return None
    gaps = [feed_times[i] - feed_times[i - 1] for i in range(1, len(feed_times))]
    return sum(gaps) / len(gaps)


def recommended_gap(values: List[float]) -> int | None:
    clear_time = time_to_clear(values)
    if clear_time is None:
        return None
    return max(clear_time + 2, 1)


def describe_level(score: float) -> str:
    if score >= 8:
        return "Good"
    if score >= 5:
        return "Borderline"
    return "Poor"


def timing_score(values: List[float], feed_times: List[int]) -> float:
    if not feed_times:
        return 0.0

    gap_needed = recommended_gap(values)
    if len(feed_times) < 2:
        return 10.0

    avg_gap = average_feed_gap(feed_times)
    if gap_needed is None or avg_gap is None:
        return 5.0

    overlap_penalty = 3.0 if detect_overlap(values, feed_times) else 0.0
    ratio = avg_gap / gap_needed if gap_needed > 0 else 1.0
    score = 10.0 * clamp(ratio, 0.0, 1.0) - overlap_penalty

    if avg_gap >= gap_needed:
        score = min(10.0, score + 2.0)

    return round(clamp(score, 0.0, 10.0), 1)


def load_score(
    peak: float,
    total_load: float,
    number_of_feeds: int,
    goal: str,
) -> float:
    if number_of_feeds == 0:
        return 0.0

    peak_penalty = peak / 1.5
    load_penalty = total_load / 12.0

    score = 10.0 - peak_penalty - load_penalty

    if goal == "Minimise Waste":
        score -= 1.0 if peak > 5 else 0.0
    elif goal == "Maximise Feeding Frequency":
        score += 0.5
    elif goal == "Balanced Feeding":
        pass

    return round(clamp(score, 0.0, 10.0), 1)


def waste_risk_score(
    timing: float,
    load: float,
) -> float:
    # Higher = better, so invert into risk-friendly score
    # But return as "efficiency-style" score out of 10
    score = (timing * 0.45) + (load * 0.55)
    return round(clamp(score, 0.0, 10.0), 1)


def generate_summary(
    overlap: bool,
    peak: float,
    gap_ok: bool,
    goal: str,
) -> str:
    if overlap and peak > 6:
        return "Your schedule is too tight and each feed event is also too heavy for this setup."
    if overlap:
        return "Your feed timing is the main issue here — the system is not recovering before the next feed."
    if not overlap and peak > 6:
        return "Your timing is fine, but each feeding event is too heavy for the chosen setup."
    if gap_ok and peak <= 6:
        if goal == "Minimise Waste":
            return "This schedule looks efficient and keeps waste risk under control."
        if goal == "Maximise Feeding Frequency":
            return "This schedule is handling multiple feeds cleanly for the chosen setup."
        return "This feeding pattern looks balanced for the chosen setup."
    return "This strategy works, but it could be improved further."


def build_human_interpretation(
    values: List[float],
    feed_times: List[int],
    feed_amount: float,
    k_s: float,
    k_c: float,
    k_f: float,
    goal: str,
) -> Tuple[str, str, List[str], List[str], Dict[str, float]]:
    notes: List[str] = []
    actions: List[str] = []

    if not feed_times:
        return (
            "info",
            "No feeding events set",
            ["No feed was added in the current simulation."],
            ["Add one or more feeding times to simulate a real feeding strategy."],
            {
                "peak": 0.0,
                "clear_steps": 0.0,
                "baseline_steps": 0.0,
                "gap_needed": 0.0,
                "total_load": 0.0,
                "timing_score": 0.0,
                "load_score": 0.0,
                "overall_score": 0.0,
            },
        )

    peak = max_value(values)
    clear_steps = time_to_clear(values) or 0
    baseline_steps = time_to_baseline(values) or 0
    gap_needed = recommended_gap(values) or 0
    total_load = area_under_curve(values)
    overlap = detect_overlap(values, feed_times)

    timing = timing_score(values, feed_times)
    load = load_score(peak, total_load, len(feed_times), goal)
    overall = waste_risk_score(timing, load)

    avg_gap = average_feed_gap(feed_times)
    gap_ok = True if len(feed_times) < 2 else (avg_gap is not None and avg_gap >= gap_needed)

    notes.append(f"Each feed event creates a peak particle concentration of about {peak:.2f}.")
    notes.append(f"The system drops to 5% of peak after about {clear_steps} steps.")
    notes.append(f"The tank returns close to baseline after about {baseline_steps} steps.")
    notes.append(f"Combined clearance strength is {k_s + k_c + k_f:.2f} per timestep.")

    if len(feed_times) >= 2:
        notes.append(f"Average gap between feeds is about {avg_gap:.1f} steps.")
        notes.append(f"Recommended minimum gap for this setup is about {gap_needed} steps.")

    if overlap:
        notes.append("The next feed arrives before the system has fully recovered.")
        actions.append("Increase the spacing between feeds.")
    else:
        notes.append("The system fully recovers between feed events.")

    if peak > 7:
        notes.append("Each feeding event introduces a very large waste spike.")
        actions.append("Reduce feed amount per event.")
    elif peak > 5:
        notes.append("Each feeding event introduces a moderately high waste spike.")
        actions.append("Consider reducing feed amount slightly.")
    else:
        notes.append("The feed amount per event is within a manageable range for this setup.")

    if goal == "Minimise Waste":
        actions.append("Prioritise lower peak concentration over feeding frequency.")
    elif goal == "Maximise Feeding Frequency":
        actions.append("Keep multiple feeds, but only if the system still recovers fully.")
    else:
        actions.append("Aim for a balance between clean recovery and practical feeding frequency.")

    summary = generate_summary(overlap, peak, bool(gap_ok), goal)

    if overlap or peak > 7:
        verdict_level = "warning"
        verdict_text = "High waste risk detected"
    elif peak > 5 or not gap_ok:
        verdict_level = "info"
        verdict_text = "Moderate waste risk detected"
    else:
        verdict_level = "success"
        verdict_text = "Low waste risk for the chosen setup"

    return (
        verdict_level,
        verdict_text,
        notes,
        actions,
        {
            "peak": peak,
            "clear_steps": float(clear_steps),
            "baseline_steps": float(baseline_steps),
            "gap_needed": float(gap_needed),
            "total_load": total_load,
            "timing_score": timing,
            "load_score": load,
            "overall_score": overall,
            "summary": summary,  # type: ignore
        },
    )


def suggest_better_spacing(feed_times: List[int], values: List[float], simulation_length: int) -> List[int]:
    if not feed_times:
        return []

    gap = recommended_gap(values)
    if gap is None:
        return feed_times

    suggested = [feed_times[0]]
    for _ in range(1, len(feed_times)):
        next_t = suggested[-1] + gap
        if next_t < simulation_length:
            suggested.append(next_t)

    return suggested


def suggest_reduced_feed_amount(
    feed_amount: float,
    peak: float,
    target_peak: float = 5.0,
) -> float:
    if peak <= target_peak:
        return round(feed_amount, 2)

    ratio = target_peak / peak
    suggested = feed_amount * ratio
    return round(max(0.5, suggested), 2)


def suggest_split_feed_schedule(
    feed_times: List[int],
    feed_amount: float,
    values: List[float],
    simulation_length: int,
) -> Tuple[List[int], float] | None:
    if not feed_times:
        return None

    gap = recommended_gap(values)
    if gap is None:
        return None

    total_feed = feed_amount * len(feed_times)
    new_count = min(len(feed_times) + 1, 6)
    new_amount = round(total_feed / new_count, 2)

    start = feed_times[0]
    suggested: List[int] = []
    for i in range(new_count):
        t = start + (i * gap)
        if t < simulation_length:
            suggested.append(t)

    if len(suggested) < 2:
        return None

    return suggested, new_amount


def make_export_report(
    tank_type: str,
    filtration_strength: str,
    stocking_level: str,
    simulation_length: int,
    feed_amount: float,
    feed_times: List[int],
    goal: str,
    metrics: Dict[str, float],
    verdict_text: str,
    notes: List[str],
    actions: List[str],
    better_spacing: List[int],
    suggested_feed_amount: float,
    split_schedule: Tuple[List[int], float] | None,
) -> str:
    lines: List[str] = []
    lines.append("FEEDING OPTIMISATION REPORT")
    lines.append("=" * 40)
    lines.append("")
    lines.append("SETUP")
    lines.append(f"Tank Type: {tank_type}")
    lines.append(f"Filtration Strength: {filtration_strength}")
    lines.append(f"Stocking Level: {stocking_level}")
    lines.append(f"Simulation Length: {simulation_length}")
    lines.append(f"Goal: {goal}")
    lines.append("")
    lines.append("CURRENT STRATEGY")
    lines.append(f"Feed Amount per Event: {feed_amount}")
    lines.append(f"Feed Times: {feed_times if feed_times else 'None'}")
    lines.append("")
    lines.append("RESULTS")
    lines.append(f"Verdict: {verdict_text}")
    lines.append(f"Peak Concentration: {metrics['peak']:.2f}")
    lines.append(f"Time to Clear: {int(metrics['clear_steps'])} steps")
    lines.append(f"Time to Baseline: {int(metrics['baseline_steps'])} steps")
    lines.append(f"Recommended Minimum Gap: {int(metrics['gap_needed'])} steps")
    lines.append(f"Total Particle Load: {metrics['total_load']:.2f}")
    lines.append(f"Timing Efficiency Score: {metrics['timing_score']:.1f}/10")
    lines.append(f"Load Efficiency Score: {metrics['load_score']:.1f}/10")
    lines.append(f"Overall Efficiency Score: {metrics['overall_score']:.1f}/10")
    lines.append("")
    lines.append("SUMMARY")
    lines.append(str(metrics["summary"]))
    lines.append("")
    lines.append("INTERPRETATION")
    for note in notes:
        lines.append(f"- {note}")
    lines.append("")
    lines.append("RECOMMENDED ACTIONS")
    for action in actions:
        lines.append(f"- {action}")
    lines.append(f"- Better spacing suggestion: {better_spacing}")
    lines.append(f"- Lower feed amount suggestion: {suggested_feed_amount}")
    if split_schedule is not None:
        lines.append(
            f"- Split-feed suggestion: times {split_schedule[0]} with about {split_schedule[1]} per event"
        )

    return "\n".join(lines)


# -----------------------------
# Sidebar
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

    st.header("Goal")
    goal = st.selectbox(
        "Optimisation Goal",
        ["Balanced Feeding", "Minimise Waste", "Maximise Feeding Frequency"],
    )

    st.header("Comparison")
    show_baseline = st.checkbox("Compare with baseline single-feed scenario", value=True)


# -----------------------------
# Main calculations
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

verdict_level, verdict_text, notes, actions, metrics = build_human_interpretation(
    values=values,
    feed_times=feed_times,
    feed_amount=feed_amount,
    k_s=k_s,
    k_c=k_c,
    k_f=k_f,
    goal=goal,
)

peak_value = metrics["peak"]
clear_steps = int(metrics["clear_steps"])
gap_needed = int(metrics["gap_needed"])
total_removal = k_s + k_c + k_f
total_load = metrics["total_load"]

timing_eff = metrics["timing_score"]
load_eff = metrics["load_score"]
overall_eff = metrics["overall_score"]

baseline_load = area_under_curve(baseline_values)
vs_baseline_load = total_load - baseline_load

better_spacing = suggest_better_spacing(feed_times, values, simulation_length)
suggested_feed_amount = suggest_reduced_feed_amount(feed_amount, peak_value)
split_schedule = suggest_split_feed_schedule(feed_times, feed_amount, values, simulation_length)

summary_text = str(metrics["summary"])


# -----------------------------
# Top summary
# -----------------------------
st.markdown(f"### {summary_text}")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Peak Concentration", f"{peak_value:.2f}")
m2.metric("Time to Clear", f"{clear_steps} steps")
m3.metric("Recommended Feed Gap", f"{gap_needed} steps")
m4.metric("Total Removal Rate", f"{total_removal:.2f}")

s1, s2, s3 = st.columns(3)
s1.metric("Timing Efficiency", f"{timing_eff}/10", describe_level(timing_eff))
s2.metric("Load Efficiency", f"{load_eff}/10", describe_level(load_eff))
s3.metric("Overall Efficiency", f"{overall_eff}/10", describe_level(overall_eff))


# -----------------------------
# Main graph
# -----------------------------
fig, ax = plt.subplots(figsize=(12, 6))
time_axis = list(range(simulation_length))

ax.plot(time_axis, values, linewidth=2.8, label="Current Strategy")

if show_baseline:
    ax.plot(
        time_axis,
        baseline_values,
        linewidth=2.2,
        linestyle="--",
        label="Baseline Single Feed",
    )

for idx, ft in enumerate(feed_times):
    ax.axvline(
        x=ft,
        linestyle="--",
        linewidth=1.3,
        alpha=0.6,
        label="Feed Event" if idx == 0 else None,
    )

# Mark recommended next feed point from first event
if feed_times and gap_needed > 0:
    recommended_t = feed_times[0] + gap_needed
    if recommended_t < simulation_length:
        ax.axvline(
            x=recommended_t,
            linestyle=":",
            linewidth=1.6,
            alpha=0.8,
            label="Recommended Next Feed",
        )
        ax.text(
            recommended_t + 1,
            peak_value * 0.55 if peak_value > 0 else 0.5,
            f"Recommended gap ≈ {gap_needed}",
            fontsize=10,
        )

# Shade recovery zone after first feed
if feed_times and clear_steps > 0:
    start = feed_times[0]
    end = min(feed_times[0] + clear_steps, simulation_length - 1)
    ax.axvspan(start, end, alpha=0.08)

# Annotate spikes
for ft in feed_times:
    if 0 <= ft < len(values):
        local_y = values[ft]
        ax.annotate(
            "Feed spike",
            xy=(ft, local_y),
            xytext=(ft + 3, local_y + 0.5),
            arrowprops={"arrowstyle": "->"},
            fontsize=9,
        )

ax.set_title("Particle Concentration Over Time")
ax.set_xlabel("Time")
ax.set_ylabel("Particle Concentration")
ax.grid(True, alpha=0.25)
ax.legend()
plt.tight_layout()

st.pyplot(fig)


# -----------------------------
# Comparison / analytics
# -----------------------------
c1, c2, c3 = st.columns(3)
c1.metric("Total Particle Load", f"{total_load:.2f}")
c2.metric("Vs Baseline Load", f"{vs_baseline_load:+.2f}" if show_baseline else "Hidden")
c3.metric("Feed Events", f"{len(feed_times)}")

if show_baseline:
    if vs_baseline_load > 2:
        st.warning("Your current strategy creates more total waste load than the baseline.")
    elif vs_baseline_load < -2:
        st.success("Your current strategy creates less total waste load than the baseline.")
    else:
        st.info("Your current strategy is broadly similar to the baseline in total waste load.")


# -----------------------------
# Setup summary
# -----------------------------
with st.expander("Current Setup Summary", expanded=False):
    st.write(f"**Tank Type:** {tank_type}")
    st.write(f"**Filtration Strength:** {filtration_strength}")
    st.write(f"**Stocking Level:** {stocking_level}")
    st.write(f"**Goal:** {goal}")
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
# Interpretation + actions
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

    if better_spacing:
        st.write(f"- Better spacing suggestion: {better_spacing}")

    if suggested_feed_amount < feed_amount:
        st.write(f"- Lower feed amount suggestion: about {suggested_feed_amount} per event.")

    if split_schedule is not None:
        split_times, split_amount = split_schedule
        st.write(
            f"- Split-feed suggestion: try {split_times} with about {split_amount} per event."
        )


# -----------------------------
# Scenario comparison cards
# -----------------------------
st.subheader("Scenario Compare Mode")

normal_times = [10] if simulation_length > 10 else [0]
double_times = [10, 15] if simulation_length > 15 else [0, min(5, simulation_length - 1)]
missed_times: List[int] = []

normal_values = run_simulation(normal_times, simulation_length, feed_amount, k_s, k_c, k_f)
double_values = run_simulation(double_times, simulation_length, feed_amount, k_s, k_c, k_f)
missed_values = run_simulation(missed_times, simulation_length, feed_amount, k_s, k_c, k_f)

sc1, sc2, sc3 = st.columns(3)

with sc1:
    st.markdown("**Normal Feeding**")
    st.write(f"Times: {normal_times}")
    st.write(f"Peak: {max_value(normal_values):.2f}")
    st.write(f"Load: {area_under_curve(normal_values):.2f}")

with sc2:
    st.markdown("**Double Feeding**")
    st.write(f"Times: {double_times}")
    st.write(f"Peak: {max_value(double_values):.2f}")
    st.write(f"Load: {area_under_curve(double_values):.2f}")

with sc3:
    st.markdown("**Missed Feeding**")
    st.write("Times: None")
    st.write(f"Peak: {max_value(missed_values):.2f}")
    st.write(f"Load: {area_under_curve(missed_values):.2f}")


# -----------------------------
# Quick scenario ideas
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


# -----------------------------
# Export feature
# -----------------------------
report_text = make_export_report(
    tank_type=tank_type,
    filtration_strength=filtration_strength,
    stocking_level=stocking_level,
    simulation_length=simulation_length,
    feed_amount=feed_amount,
    feed_times=feed_times,
    goal=goal,
    metrics=metrics,
    verdict_text=verdict_text,
    notes=notes,
    actions=actions,
    better_spacing=better_spacing,
    suggested_feed_amount=suggested_feed_amount,
    split_schedule=split_schedule,
)

st.subheader("Export")
st.download_button(
    label="Download Recommendation Report",
    data=report_text,
    file_name="feeding_optimisation_report.txt",
    mime="text/plain",
)
