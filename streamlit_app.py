
from __future__ import annotations

from datetime import time
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(page_title="Feeding Optimisation Tool", page_icon="🐟", layout="wide")
st.title("Feeding Optimisation Tool")
st.write("Estimate how different feeding plans affect tank waste, recovery time, and practical feeding guidance.")

TIME_SCALE_OPTIONS = {"1 minute": 1, "5 minutes": 5, "15 minutes": 15, "30 minutes": 30, "1 hour": 60}
FILTER_TYPE_INFO = {
    "Sponge filter": {"efficiency": 0.72, "description": "Gentle flow and strong biological filtration. Best suited to shrimp, fry, and low-waste tanks."},
    "Internal filter": {"efficiency": 0.95, "description": "Moderate all-round filtration. Common in standard home tanks."},
    "Hang-on-back": {"efficiency": 1.05, "description": "Good surface movement with moderate mechanical filtration."},
    "Canister filter": {"efficiency": 1.20, "description": "Strong mechanical and biological filtration. Best for larger or heavier-waste tanks."},
}
FEED_TYPE_INFO = {
    "Pellets": {"spike_multiplier": 1.00, "linger_modifier": 1.00, "description": "Moderate spike and moderate decay. Good all-round reference food.", "visual": "roughly a small cluster of pellets"},
    "Flakes": {"spike_multiplier": 1.20, "linger_modifier": 1.08, "description": "Break up quickly and can create a sharper waste spike if overfed.", "visual": "roughly a light-to-moderate pinch of flakes"},
    "Powder / shrimp food": {"spike_multiplier": 1.35, "linger_modifier": 1.12, "description": "Spreads rapidly through the water column and can spike waste quickly.", "visual": "roughly a visible dusting of powder food"},
    "Frozen / live food": {"spike_multiplier": 1.15, "linger_modifier": 0.92, "description": "Usually richer and messier, but often not as instantly dispersed as powder.", "visual": "roughly a small cube or small chunk equivalent"},
    "Slow-release / wafers / snowflake": {"spike_multiplier": 0.70, "linger_modifier": 0.65, "description": "Releases waste more gradually and tends to linger longer.", "visual": "roughly one wafer or small piece"},
}
STOCKING_INFO = {"Light": "Few animals for the tank size. Lower waste production.", "Moderate": "Typical home stocking level. Balanced waste production.", "Heavy": "High population for the tank size. Higher waste production and less margin for error."}
MATURITY_INFO = {
    "New (<1 month)": {"multiplier": 0.88, "description": "Less biologically stable and less forgiving of waste spikes."},
    "Established (1–6 months)": {"multiplier": 1.00, "description": "More stable and predictable than a new setup."},
    "Mature (6+ months)": {"multiplier": 1.08, "description": "Usually more biologically resilient if maintenance is consistent."},
}
SUBSTRATE_INFO = {
    "Bare bottom": {"multiplier": 0.95, "description": "Less biofilm support and less passive buffering of organic load."},
    "Standard substrate": {"multiplier": 1.00, "description": "Typical balance of cleanliness and biological support."},
    "Planted / biofilm-rich": {"multiplier": 1.08, "description": "More surfaces and biological activity to help process waste."},
}
GOAL_INFO = {
    "Balanced Feeding": "Aims for a practical middle ground between growth and waste control.",
    "Minimise Waste": "Prioritises cleaner water and lower feeding spikes over aggressive feeding.",
    "Maximise Feeding Frequency": "Allows more frequent feeding but tolerates slightly more load.",
}
SIMPLE_FEED_LEVELS = {"Very light": 2.0, "Light": 3.5, "Normal": 5.0, "Heavy": 7.5, "Very heavy": 10.0}

def label(simple: str, advanced: str, advanced_mode: bool) -> str:
    return advanced if advanced_mode else simple

def safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0

def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))

def format_duration(minutes: float) -> str:
    if minutes < 60:
        return f"{minutes:.0f} minutes"
    hours = minutes / 60
    if hours < 24:
        return f"{hours:.1f} hours"
    return f"{hours / 24:.1f} days"

def real_time_text(points: List[int], minutes_per_interval: int) -> str:
    if not points:
        return "None"
    return ", ".join(format_duration(p * minutes_per_interval) for p in points)

def turnover_judgement(turnover: float, tank_type: str) -> str:
    if tank_type == "Shrimp Tank":
        if turnover < 3: return "Low"
        if turnover < 7: return "Moderate"
        return "High"
    if turnover < 3: return "Low"
    if turnover < 6: return "Moderate"
    return "High"

def clearing_label(total_removal: float) -> str:
    if total_removal < 0.30: return "Slow"
    if total_removal < 0.50: return "Moderate"
    return "Fast"

def efficiency_word(score: float) -> str:
    if score >= 8: return "Good"
    if score >= 5: return "Borderline"
    return "Poor"

def risk_word(score: float) -> str:
    if score >= 8: return "Low"
    if score >= 5: return "Moderate"
    return "High"

def estimate_biomass_g(tank_type: str, tank_size_l: int, stocking_level: str) -> float:
    if tank_type == "Shrimp Tank":
        density = {"Light": 0.18, "Moderate": 0.35, "Heavy": 0.60}[stocking_level]
    elif tank_type == "Fish Tank":
        density = {"Light": 0.50, "Moderate": 1.10, "Heavy": 2.00}[stocking_level]
    else:
        density = {"Light": 0.30, "Moderate": 0.70, "Heavy": 1.20}[stocking_level]
    return round(max(tank_size_l * density, 5.0), 1)

def feed_amount_to_percent_bodyweight(feed_amount: float) -> float:
    return round(feed_amount * 0.6, 2)

def estimated_feed_grams(feed_amount: float, biomass_g: float) -> float:
    return round(biomass_g * (feed_amount_to_percent_bodyweight(feed_amount) / 100), 3)

def practical_feed_label(feed_amount: float) -> str:
    if feed_amount < 2.5: return "Very light"
    if feed_amount < 4.0: return "Light"
    if feed_amount < 6.5: return "Normal"
    if feed_amount < 9.0: return "Heavy"
    return "Very heavy"

def pellet_equivalent_text(feed_type: str, grams: float) -> str:
    if feed_type == "Pellets":
        pellets = int(max(1, round(grams * 28)))
        if pellets <= 6: return f"about {pellets} small pellets"
        if pellets <= 20: return f"about {pellets} small-to-medium pellets"
        return f"about {pellets} pellets (heavy feeding)"
    return str(FEED_TYPE_INFO[feed_type]["visual"])

def map_setup_to_rates(tank_type: str, stocking_level: str, tank_size_l: int, filter_type: str, flow_rate_lph: int, feed_type: str, tank_maturity: str, substrate_type: str) -> Tuple[float, float, float, Dict[str, float | str]]:
    turnover = safe_div(flow_rate_lph, tank_size_l)
    base_settling = {"Shrimp Tank": 0.16, "Fish Tank": 0.20, "Mixed Tank": 0.18, "Custom": 0.18}[tank_type]
    base_consumption = {"Light": 0.06, "Moderate": 0.10, "Heavy": 0.15}[stocking_level]
    filter_efficiency = float(FILTER_TYPE_INFO[filter_type]["efficiency"])
    feed_linger = float(FEED_TYPE_INFO[feed_type]["linger_modifier"])
    maturity_modifier = float(MATURITY_INFO[tank_maturity]["multiplier"])
    substrate_modifier = float(SUBSTRATE_INFO[substrate_type]["multiplier"])
    if tank_type == "Shrimp Tank":
        tank_flow_modifier = 0.82
        base_settling *= 0.95
    elif tank_type == "Fish Tank":
        tank_flow_modifier = 1.05
        base_consumption *= 1.08
    elif tank_type == "Mixed Tank":
        tank_flow_modifier = 0.95
    else:
        tank_flow_modifier = 1.0
    filtration_rate = clamp((turnover / 10.0) * filter_efficiency * tank_flow_modifier * maturity_modifier, 0.05, 0.42)
    size_modifier = 1.0
    if tank_size_l <= 30: size_modifier = 0.95
    elif tank_size_l >= 150: size_modifier = 1.08
    settling_rate = clamp(base_settling * size_modifier * feed_linger, 0.04, 0.32)
    consumption_rate = clamp(base_consumption * size_modifier * clamp(feed_linger, 0.65, 1.15) * maturity_modifier * substrate_modifier, 0.03, 0.24)
    return settling_rate, consumption_rate, filtration_rate, {"turnover": turnover}

def get_feed_multiplier(feed_type: str) -> float:
    return float(FEED_TYPE_INFO[feed_type]["spike_multiplier"])

def run_simulation(feed_times: List[int], simulation_length: int, feed_amount: float, k_s: float, k_c: float, k_f: float, feed_type: str) -> List[float]:
    p = 0.0
    results: List[float] = []
    total_removal = k_s + k_c + k_f
    spike_multiplier = get_feed_multiplier(feed_type)
    for t in range(simulation_length):
        if t in feed_times:
            p += feed_amount * spike_multiplier
        p = p - total_removal * p
        p = max(p, 0.0)
        results.append(p)
    return results

def area_under_curve(values: List[float]) -> float:
    return sum(values)

def max_value(values: List[float]) -> float:
    return max(values) if values else 0.0

def time_to_threshold_after_feed(values: List[float], start_index: int, threshold: float) -> int | None:
    if not values or start_index >= len(values): return None
    for i in range(start_index, len(values)):
        if values[i] <= threshold:
            return i - start_index
    return None

def time_to_clear(values: List[float], threshold_ratio: float = 0.05) -> int | None:
    peak = max_value(values)
    if peak <= 0: return 0
    peak_index = values.index(peak)
    threshold = peak * threshold_ratio
    return time_to_threshold_after_feed(values, peak_index, threshold)

def time_to_baseline(values: List[float], absolute_threshold: float = 0.05) -> int | None:
    peak = max_value(values)
    if peak <= 0: return 0
    peak_index = values.index(peak)
    return time_to_threshold_after_feed(values, peak_index, absolute_threshold)

def detect_overlap(values: List[float], feed_times: List[int]) -> bool:
    if len(feed_times) < 2 or not values: return False
    first_peak = max_value(values)
    if first_peak <= 0: return False
    threshold = first_peak * 0.20
    return any(0 <= ft < len(values) and values[ft] > threshold for ft in feed_times[1:])

def average_feed_gap(feed_times: List[int]) -> float | None:
    if len(feed_times) < 2: return None
    gaps = [feed_times[i] - feed_times[i - 1] for i in range(1, len(feed_times))]
    return sum(gaps) / len(gaps)

def recommended_gap(values: List[float]) -> int | None:
    clear_time = time_to_clear(values)
    if clear_time is None: return None
    return max(clear_time + 2, 1)

def timing_score(values: List[float], feed_times: List[int]) -> float:
    if not feed_times: return 0.0
    gap_needed = recommended_gap(values)
    if len(feed_times) < 2: return 10.0
    avg_gap = average_feed_gap(feed_times)
    if gap_needed is None or avg_gap is None: return 5.0
    overlap_penalty = 3.0 if detect_overlap(values, feed_times) else 0.0
    ratio = avg_gap / gap_needed if gap_needed > 0 else 1.0
    score = 10.0 * clamp(ratio, 0.0, 1.0) - overlap_penalty
    if avg_gap >= gap_needed: score = min(10.0, score + 2.0)
    return round(clamp(score, 0.0, 10.0), 1)

def load_score(peak: float, total_load: float, number_of_feeds: int, goal: str) -> float:
    if number_of_feeds == 0: return 0.0
    peak_penalty = peak / 1.5
    load_penalty = total_load / 12.0
    score = 10.0 - peak_penalty - load_penalty
    if goal == "Minimise Waste":
        score -= 1.0 if peak > 5 else 0.0
    elif goal == "Maximise Feeding Frequency":
        score += 0.5
    return round(clamp(score, 0.0, 10.0), 1)

def overall_efficiency_score(timing: float, load: float) -> float:
    return round(clamp((timing * 0.45) + (load * 0.55), 0.0, 10.0), 1)

def visible_tank_effects(tank_type: str, peak: float, overlap: bool) -> List[str]:
    effects: List[str] = []
    if peak < 3:
        effects.extend(["Food should clear without obvious leftovers.", "Water clarity should stay stable after feeding."])
    elif peak < 6:
        effects.extend(["You may see some food sitting briefly before it clears.", "The tank should cope, but repeated heavy feeding could build waste."])
    else:
        effects.extend(["Visible leftovers are likely if stock does not clear food quickly.", "Cloudy water or substrate waste is more likely after feeding."])
    if overlap: effects.append("Feeding again too soon may stop the tank from fully recovering.")
    if tank_type == "Shrimp Tank" and peak > 5: effects.append("Shrimp setups are less forgiving of large spikes, so stay conservative.")
    return effects

def reality_check_list(tank_type: str) -> List[str]:
    base = [
        "If food is still clearly visible after the suggested recovery window, reduce feed.",
        "If water clouds after feeding, overfeeding or slow breakdown is likely.",
        "If the tank clears food much faster than predicted, you may be able to feed slightly more.",
    ]
    if tank_type == "Shrimp Tank":
        base.extend([
            "If shrimp swarm food immediately and it disappears fast, the current amount may be fine.",
            "If food sits untouched on substrate, reduce feed or try a different food type.",
        ])
    else:
        base.extend([
            "If fish leave visible leftovers after feeding, reduce feed amount.",
            "If fish become aggressive or food disappears instantly every time, the plan may be too light.",
        ])
    return base

def generate_summary(overlap: bool, peak: float, gap_ok: bool, goal: str) -> str:
    if overlap and peak > 6: return "Your feeds are too close together and each feed is also too heavy for this setup."
    if overlap: return "Your feeds are too close together. The tank is not recovering in time."
    if not overlap and peak > 6: return "Your timing is fine, but each feed is too heavy for this setup."
    if gap_ok and peak <= 6:
        if goal == "Minimise Waste": return "This feeding plan looks efficient and keeps waste risk under control."
        if goal == "Maximise Feeding Frequency": return "This feeding plan handles multiple feeds cleanly for the chosen setup."
        return "This feeding plan looks balanced for the chosen setup."
    return "This feeding plan works, but it could be improved."

def build_human_interpretation(values: List[float], feed_times: List[int], tank_type: str, tank_size_l: int, feed_amount_grams: float, k_s: float, k_c: float, k_f: float, goal: str, turnover: float, feed_type: str, minutes_per_interval: int) -> Tuple[str, str, List[str], List[str], Dict[str, float | str]]:
    notes: List[str] = []
    actions: List[str] = []
    if not feed_times:
        return ("info","No feeding events set",["No feed was added in the current simulation."],["Add one or more feeding points to simulate a real feeding plan."],{"peak":0.0,"clear_steps":0.0,"baseline_steps":0.0,"gap_needed":0.0,"total_load":0.0,"timing_score":0.0,"load_score":0.0,"overall_score":0.0,"summary":"No feeding plan entered."})

    peak = max_value(values)
    clear_steps = time_to_clear(values) or 0
    baseline_steps = time_to_baseline(values) or 0
    gap_needed = recommended_gap(values) or 0
    total_load = area_under_curve(values)
    overlap = detect_overlap(values, feed_times)

    timing = timing_score(values, feed_times)
    load = load_score(peak, total_load, len(feed_times), goal)
    overall = overall_efficiency_score(timing, load)

    avg_gap = average_feed_gap(feed_times)
    gap_ok = True if len(feed_times) < 2 else (avg_gap is not None and avg_gap >= gap_needed)

    recovery_minutes = clear_steps * minutes_per_interval
    baseline_minutes = baseline_steps * minutes_per_interval
    gap_minutes = gap_needed * minutes_per_interval

    notes.extend([
        f"Each feed creates a highest waste spike of about {peak:.2f}.",
        f"The tank recovers to a low level after about {format_duration(recovery_minutes)}.",
        f"The tank returns close to baseline after about {format_duration(baseline_minutes)}.",
        f"Estimated tank turnover is {turnover:.1f}x per hour.",
        f"Feed type selected: {feed_type}.",
        f"Approximate feed amount is {feed_amount_grams:.3f}g per feed.",
    ])

    if len(feed_times) >= 2 and avg_gap is not None:
        notes.append(f"Average time between feeds is about {format_duration(avg_gap * minutes_per_interval)}.")
        notes.append(f"Recommended minimum delay for this setup is about {format_duration(gap_minutes)}.")

    if turnover < 3:
        notes.append("Filtration is on the weak side for faster waste clearance.")
        actions.append("Increase flow rate or improve filtration if you want faster recovery.")
    elif turnover > 8 and tank_type == "Shrimp Tank":
        notes.append("Flow may be strong for a typical shrimp setup.")
        actions.append("Check whether flow is too aggressive for shrimp comfort.")

    if overlap:
        notes.append("The next feed arrives before the tank has fully recovered.")
        actions.append("Increase the spacing between feeds.")
    else:
        notes.append("The tank fully recovers between feed events.")

    if peak > 7:
        notes.append("Each feed creates a very large waste spike.")
        actions.append("Reduce feed amount per event.")
    elif peak > 5:
        notes.append("Each feed creates a moderately high waste spike.")
        actions.append("Consider reducing feed amount slightly.")
    else:
        notes.append("The feed amount per event is manageable for this setup.")

    if tank_size_l <= 30 and peak > 5:
        notes.append("Small tanks have less margin for error because waste concentrates faster.")
        actions.append("Be more conservative with feed amount in smaller tanks.")

    if goal == "Minimise Waste":
        actions.append("Prioritise lower waste spikes over feeding frequency.")
    elif goal == "Maximise Feeding Frequency":
        actions.append("Keep multiple feeds only if the tank still recovers fully.")
    else:
        actions.append("Aim for a balance between clean recovery and practical feeding frequency.")

    summary = generate_summary(overlap, peak, bool(gap_ok), goal)
    if overlap or peak > 7:
        verdict_level, verdict_text = "warning", "High waste risk detected"
    elif peak > 5 or not gap_ok:
        verdict_level, verdict_text = "info", "Moderate waste risk detected"
    else:
        verdict_level, verdict_text = "success", "Low waste risk for the chosen setup"

    return (verdict_level, verdict_text, notes, actions, {"peak":peak,"clear_steps":float(clear_steps),"baseline_steps":float(baseline_steps),"gap_needed":float(gap_needed),"total_load":total_load,"timing_score":timing,"load_score":load,"overall_score":overall,"summary":summary})

def suggest_better_spacing(feed_times: List[int], values: List[float], simulation_length: int) -> List[int]:
    if not feed_times or len(feed_times) < 2: return []
    gap = recommended_gap(values)
    if gap is None: return []
    suggested = [feed_times[0]]
    for _ in range(1, len(feed_times)):
        next_time = suggested[-1] + gap
        if next_time < simulation_length:
            suggested.append(next_time)
    return suggested

def suggest_reduced_feed_amount(feed_amount_grams: float, peak: float, target_peak: float = 5.0) -> float:
    if peak <= target_peak: return round(feed_amount_grams, 3)
    ratio = target_peak / peak
    return round(max(0.02, feed_amount_grams * ratio), 3)

def suggest_split_feed_schedule(feed_times: List[int], feed_amount_grams: float, values: List[float], simulation_length: int, goal: str) -> Tuple[List[int], float] | None:
    peak = max_value(values)
    load = area_under_curve(values)
    if peak <= 5 and load <= 10 and goal != "Maximise Feeding Frequency": return None
    if not feed_times: return None
    gap = recommended_gap(values)
    if gap is None: return None
    total_feed = feed_amount_grams * len(feed_times)
    new_count = min(len(feed_times) + 1, 6)
    new_amount = round(total_feed / new_count, 3)
    start = feed_times[0]
    suggested: List[int] = []
    for i in range(new_count):
        t = start + (i * gap)
        if t < simulation_length:
            suggested.append(t)
    if len(suggested) < 2: return None
    return suggested, new_amount

def optimise_feed_plan(current_feed_times: List[int], current_feed_amount_grams: float, simulation_length: int, k_s: float, k_c: float, k_f: float, feed_type: str, goal: str) -> Tuple[List[int], float]:
    if not current_feed_times: return [], current_feed_amount_grams
    test_values = run_simulation(current_feed_times, simulation_length, current_feed_amount_grams, k_s, k_c, k_f, feed_type)
    better_times = suggest_better_spacing(current_feed_times, test_values, simulation_length)
    peak = max_value(test_values)
    better_amount = current_feed_amount_grams
    if goal in ["Minimise Waste", "Balanced Feeding"]:
        better_amount = suggest_reduced_feed_amount(current_feed_amount_grams, peak)
    return better_times, better_amount

# Sidebar
with st.sidebar:
    st.header("View")
    advanced_mode = st.toggle("Show advanced terms", value=False)

    st.header("Tank Setup")
    tank_type = st.selectbox("Tank Type", ["Shrimp Tank", "Fish Tank", "Mixed Tank", "Custom"])
    tank_size_l = st.slider("Tank size (litres)", 10, 500, 60, 5)
    tank_maturity = st.selectbox("Tank maturity", list(MATURITY_INFO.keys()), index=1)
    substrate_type = st.selectbox("Substrate / biofilm level", list(SUBSTRATE_INFO.keys()), index=1)
    filter_type = st.selectbox("Filter type", list(FILTER_TYPE_INFO.keys()))
    flow_rate_lph = st.slider("Filter flow rate (L/h)", 50, 3000, 300, 25)
    stocking_level = st.selectbox("Stocking Level", ["Light", "Moderate", "Heavy"], index=1)
    feed_type = st.selectbox("Feed type", list(FEED_TYPE_INFO.keys()))
    turnover = safe_div(flow_rate_lph, tank_size_l)
    filtration_strength_text = turnover_judgement(turnover, tank_type)
    st.caption(STOCKING_INFO[stocking_level])
    st.caption(MATURITY_INFO[tank_maturity]["description"])
    st.caption(SUBSTRATE_INFO[substrate_type]["description"])
    st.caption(str(FILTER_TYPE_INFO[filter_type]["description"]))
    st.caption(str(FEED_TYPE_INFO[feed_type]["description"]))
    st.caption(f"Estimated turnover: {turnover:.1f}x per hour ({filtration_strength_text.lower()} filtration)")

    time_scale_label = st.selectbox("What does one interval represent?", list(TIME_SCALE_OPTIONS.keys()), index=2)
    minutes_per_interval = TIME_SCALE_OPTIONS[time_scale_label]
    simulation_length = st.slider(label("How long to simulate", "Simulation Length", advanced_mode), 20, 200, 80, 5)
    st.caption(f"Current timeline length: about {format_duration(simulation_length * minutes_per_interval)} total.")

    st.header("Feeding Plan")
    feed_input_mode = st.radio("Feed amount input", ["Simple", "Advanced"], horizontal=True)
    biomass_g = estimate_biomass_g(tank_type, tank_size_l, stocking_level)
    if feed_input_mode == "Simple":
        feed_level = st.select_slider("Feed size", options=list(SIMPLE_FEED_LEVELS.keys()), value="Normal")
        feed_amount = SIMPLE_FEED_LEVELS[feed_level]
    else:
        feed_amount = st.slider(label("Feed amount each time", "Feed Amount per Event", advanced_mode), 0.5, 20.0, 5.0, 0.5)
        feed_level = practical_feed_label(feed_amount)
    approx_pct_bw = feed_amount_to_percent_bodyweight(feed_amount)
    approx_grams = estimated_feed_grams(feed_amount, biomass_g)
    st.caption(f"Practical guide: **{feed_level}** feed size. Roughly **{approx_pct_bw:.1f}%** of estimated livestock biomass per feed, or about **{approx_grams}g** for this setup.")
    st.caption(f"Estimated livestock biomass for this setup: about **{biomass_g}g** total.")
    st.caption(f"This is an estimate, not an exact weight. Feed type chosen: {pellet_equivalent_text(feed_type, approx_grams)}.")

    schedule_mode = st.radio("Schedule mode", ["Daily schedule", "Timeline"], horizontal=True)
    if schedule_mode == "Daily schedule":
        feeds_per_day = st.slider("How many feeds per day?", 0, 5, 1)
        days_to_simulate = st.slider("How many days to simulate?", 1, 7, 1)
        one_day_intervals = int((24 * 60) / minutes_per_interval)
        simulation_length = max(simulation_length, one_day_intervals * days_to_simulate)
        daily_points: List[int] = []
        for i in range(feeds_per_day):
            default_hour = [9, 18, 21, 12, 15][i] if i < 5 else 9
            feed_clock = st.time_input(f"Feed {i + 1} time", value=time(default_hour, 0), step=900)
            minutes_from_start = feed_clock.hour * 60 + feed_clock.minute
            interval_point = int(round(minutes_from_start / minutes_per_interval))
            daily_points.append(interval_point)
        feed_times: List[int] = []
        for day in range(days_to_simulate):
            for p in daily_points:
                feed_times.append(p + (day * one_day_intervals))
        feed_times = sorted(set(feed_times))
        st.caption(f"Timeline now covers about {days_to_simulate} day(s).")
    else:
        use_slider_events = st.toggle("Use feed-event sliders", value=True)
        if use_slider_events:
            number_of_feeds = st.slider("How many times do you feed?", 0, 5, 1)
            feed_times = []
            default_points = [10, 25, 40, 55, 70]
            for i in range(number_of_feeds):
                default_value = default_points[i] if i < len(default_points) else min(10 + (i * 10), simulation_length - 1)
                feed_time = st.slider(f"Feed {i + 1} timing", 0, simulation_length - 1, min(default_value, simulation_length - 1), 1)
                feed_times.append(feed_time)
        else:
            text_times = st.text_input(label("When do you feed?", "Feeding Times (timesteps)", advanced_mode), value="10")
            feed_times = sorted(set(int(x.strip()) for x in text_times.split(",") if x.strip().isdigit()))
        st.caption(f"One interval currently means {time_scale_label.lower()}. Spread feeds out enough to let the tank recover.")

    goal = st.selectbox("Optimisation Goal", ["Balanced Feeding", "Minimise Waste", "Maximise Feeding Frequency"])
    st.caption(GOAL_INFO[goal])

    use_custom_rates = st.checkbox("Use custom model rates (advanced)")
    if use_custom_rates:
        k_s = st.slider("Settling Rate (kₛ)", 0.00, 0.50, 0.18, 0.01)
        k_c = st.slider("Consumption Rate (k_c)", 0.00, 0.50, 0.10, 0.01)
        k_f = st.slider("Filtration Rate (k_f)", 0.00, 0.50, 0.20, 0.01)
    else:
        k_s, k_c, k_f, _derived = map_setup_to_rates(tank_type, stocking_level, tank_size_l, filter_type, flow_rate_lph, feed_type, tank_maturity, substrate_type)
    show_baseline = st.checkbox("Compare with a simple single-feed plan", value=True)
    auto_optimise = st.button("Optimise my feeding plan")

if auto_optimise:
    improved_times, improved_amount = optimise_feed_plan(feed_times, approx_grams, simulation_length, k_s, k_c, k_f, feed_type, goal)
    if improved_times:
        feed_times = improved_times
    approx_grams = improved_amount

feed_times = sorted(set([t for t in feed_times if 0 <= t < simulation_length]))
values = run_simulation(feed_times, simulation_length, approx_grams, k_s, k_c, k_f, feed_type)
baseline_times = [10] if simulation_length > 10 else [0]
baseline_values = run_simulation(baseline_times, simulation_length, approx_grams, k_s, k_c, k_f, feed_type)

verdict_level, verdict_text, notes, actions, metrics = build_human_interpretation(values, feed_times, tank_type, tank_size_l, approx_grams, k_s, k_c, k_f, goal, turnover, feed_type, minutes_per_interval)

peak_value = float(metrics["peak"])
clear_steps = int(float(metrics["clear_steps"]))
gap_needed = int(float(metrics["gap_needed"]))
total_removal = k_s + k_c + k_f
total_load = float(metrics["total_load"])
timing_eff = float(metrics["timing_score"])
load_eff = float(metrics["load_score"])
overall_eff = float(metrics["overall_score"])
baseline_load = area_under_curve(baseline_values)
vs_baseline_load = total_load - baseline_load
better_spacing = suggest_better_spacing(feed_times, values, simulation_length)
suggested_feed_amount = suggest_reduced_feed_amount(approx_grams, peak_value)
split_schedule = suggest_split_feed_schedule(feed_times, approx_grams, values, simulation_length, goal)
summary_text = str(metrics["summary"])
recovery_minutes = clear_steps * minutes_per_interval
gap_minutes = gap_needed * minutes_per_interval
visible_effects = visible_tank_effects(tank_type, peak_value, detect_overlap(values, feed_times))
reality_checks = reality_check_list(tank_type)
plus20_grams = round(approx_grams * 1.2, 3)
minus20_grams = round(max(0.02, approx_grams * 0.8), 3)
plus20_values = run_simulation(feed_times, simulation_length, plus20_grams, k_s, k_c, k_f, feed_type)
minus20_values = run_simulation(feed_times, simulation_length, minus20_grams, k_s, k_c, k_f, feed_type)

tab_overview, tab_graph, tab_meaning, tab_advanced = st.tabs(["Overview", "Graph & Compare", "What it means", "Advanced"])

with tab_overview:
    st.markdown(f"## {summary_text}")
    st.subheader("What to do next")
    if verdict_level == "success":
        st.success(f"Feed about **{approx_grams:.3f}g per feed**, keep spacing at about **{format_duration(gap_minutes)} or more**, and keep the current plan.")
    elif verdict_level == "info":
        st.warning(f"Reduce feed to about **{suggested_feed_amount:.3f}g per feed** and aim for at least **{format_duration(gap_minutes)}** between feeds.")
    else:
        st.error(f"Current feeding is risky. Reduce to about **{suggested_feed_amount:.3f}g per feed** and increase spacing to at least **{format_duration(gap_minutes)}**.")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Highest Waste Spike", f"{peak_value:.2f}")
    m2.metric("Tank Recovery Time", format_duration(recovery_minutes))
    m3.metric("Recommended Delay Before Next Feed", format_duration(gap_minutes))
    m4.metric("Tank Clearing Speed", clearing_label(total_removal) if not advanced_mode else f"{total_removal:.2f}")

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Timing Efficiency", f"{timing_eff}/10", efficiency_word(timing_eff))
    s2.metric("Load Efficiency", f"{load_eff}/10", efficiency_word(load_eff))
    s3.metric("Waste Risk", risk_word(overall_eff), f"{overall_eff:.1f}/10")
    overlap_risk = 10.0 if not detect_overlap(values, feed_times) else 3.0
    s4.metric("Overlap Risk", f"{overlap_risk:.1f}/10", "Low" if overlap_risk >= 8 else "Present")

    st.subheader("Practical feed equivalent")
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Feed level", str(feed_level).title())
    p2.metric("Approx feed per event", f"{approx_grams:.3f} g")
    p3.metric("Approx % bodyweight", f"{approx_pct_bw:.1f}%")
    p4.metric("Visual equivalent", pellet_equivalent_text(feed_type, approx_grams))
    st.caption("These feed equivalents are estimates based on tank type, stocking level, and estimated livestock biomass. Use them as practical guidance, not exact dosing.")

    st.subheader("Current setup at a glance")
    a1, a2, a3, a4, a5 = st.columns(5)
    a1.metric("Tank", tank_type)
    a2.metric("Size", f"{tank_size_l}L")
    a3.metric("Turnover", f"{turnover:.1f}x/h")
    a4.metric("Filtration", filtration_strength_text)
    a5.metric("Feed type", feed_type)

with tab_graph:
    fig, ax = plt.subplots(figsize=(12, 6))
    time_axis = list(range(simulation_length))
    ax.plot(time_axis, values, linewidth=2.8, label="Current Strategy")
    if show_baseline:
        ax.plot(time_axis, baseline_values, linewidth=2.2, linestyle="--", label="Baseline Single Feed")
    for idx, ft in enumerate(feed_times):
        ax.axvline(x=ft, linestyle="--", linewidth=1.3, alpha=0.6, label="Feed Event" if idx == 0 else None)
    if feed_times and gap_needed > 0:
        recommended_t = feed_times[0] + gap_needed
        if recommended_t < simulation_length:
            ax.axvline(x=recommended_t, linestyle=":", linewidth=1.6, alpha=0.8, label="Recommended Next Feed")
            ax.text(recommended_t + 1, peak_value * 0.55 if peak_value > 0 else 0.5, f"Recommended delay ≈ {format_duration(gap_minutes)}", fontsize=10)

    ax.axhspan(0, 4, alpha=0.06, color="green")
    ax.axhspan(4, 6, alpha=0.06, color="yellow")
    ax.axhspan(6, max(peak_value + 1, 7), alpha=0.08, color="red")
    ax.text(1, 2.0, "Safe zone", fontsize=10)
    ax.text(1, 5.0, "Borderline zone", fontsize=10)
    ax.text(1, 6.35, "High waste zone", fontsize=10)

    if feed_times and clear_steps > 0:
        start = feed_times[0]
        end = min(feed_times[0] + clear_steps, simulation_length - 1)
        ax.axvspan(start, end, alpha=0.06, color="blue")

    if peak_value > 0 and feed_times:
        ax.annotate(f"Your spike: {peak_value:.2f}", xy=(feed_times[0], values[feed_times[0]]), xytext=(feed_times[0] + 2, values[feed_times[0]] + 0.6), arrowprops={"arrowstyle": "->"}, fontsize=10)

    safe_margin = 6.0 - peak_value
    ax.text(1, 0.35, f"Safe margin remaining: {safe_margin:.2f}" if safe_margin > 0 else "Above safe margin", fontsize=9)

    ax.set_title("Waste Level Over Time")
    ax.set_xlabel("Timeline")
    ax.set_ylabel("Waste Level")
    ax.grid(True, alpha=0.25)
    ax.legend()
    plt.tight_layout()
    st.pyplot(fig)

    c1, c2, c3 = st.columns(3)
    c1.metric("Overall Waste Load", f"{total_load:.2f}")
    c2.metric("Change vs Simple Plan", f"{vs_baseline_load:+.2f}" if show_baseline else "Hidden")
    c3.metric("Feed Events", f"{len(feed_times)}")

    st.subheader("Scenario Compare Mode")
    normal_times = [10] if simulation_length > 10 else [0]
    double_times = [10, min(25, simulation_length - 1)] if simulation_length > 25 else [0, min(5, simulation_length - 1)]
    missed_times: List[int] = []
    normal_values = run_simulation(normal_times, simulation_length, approx_grams, k_s, k_c, k_f, feed_type)
    double_values = run_simulation(double_times, simulation_length, approx_grams, k_s, k_c, k_f, feed_type)
    missed_values = run_simulation(missed_times, simulation_length, approx_grams, k_s, k_c, k_f, feed_type)

    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        st.markdown("**Normal Feeding**")
        st.write(f"Timeline points: {normal_times}")
        st.write(f"Real time: {real_time_text(normal_times, minutes_per_interval)}")
        st.write(f"Highest Waste Spike: {max_value(normal_values):.2f}")
        st.write(f"Overall Waste Load: {area_under_curve(normal_values):.2f}")
    with sc2:
        st.markdown("**Double Feeding**")
        st.write(f"Timeline points: {double_times}")
        st.write(f"Real time: {real_time_text(double_times, minutes_per_interval)}")
        st.write(f"Highest Waste Spike: {max_value(double_values):.2f}")
        st.write(f"Overall Waste Load: {area_under_curve(double_values):.2f}")
    with sc3:
        st.markdown("**Missed Feeding**")
        st.write("Timeline points: None")
        st.write("Real time: None")
        st.write(f"Highest Waste Spike: {max_value(missed_values):.2f}")
        st.write(f"Overall Waste Load: {area_under_curve(missed_values):.2f}")

with tab_meaning:
    left, right = st.columns(2)
    with left:
        st.subheader("What’s happening")
        for note in notes:
            st.write(f"- {note}")
        st.subheader("What you might see in the tank")
        for effect in visible_effects:
            st.write(f"- {effect}")
    with right:
        st.subheader("What you should do")
        for action in actions:
            st.write(f"- {action}")
        if better_spacing:
            st.write(f"- Better spacing suggestion: {better_spacing} ({real_time_text(better_spacing, minutes_per_interval)})")
        if suggested_feed_amount < approx_grams:
            st.write(f"- Lower feed amount suggestion: about {suggested_feed_amount:.3f}g per feed.")
        if split_schedule is not None:
            split_times, split_amount = split_schedule
            st.write(f"- Split-feed suggestion: try {split_times} ({real_time_text(split_times, minutes_per_interval)}) with about {split_amount:.3f}g per feed.")
        st.subheader("Reality check")
        for item in reality_checks:
            st.write(f"- {item}")
        st.subheader("Confidence")
        st.write("This is a practical estimate based on typical tank behaviour, not a direct sensor measurement. Use it as a guide, then judge against what you actually see in the tank.")

with tab_advanced:
    with st.expander("Current Setup Summary", expanded=True):
        st.write(f"**Tank Type:** {tank_type}")
        st.write(f"**Tank Size:** {tank_size_l}L")
        st.write(f"**Tank Maturity:** {tank_maturity}")
        st.write(f"**Substrate / Biofilm:** {substrate_type}")
        st.write(f"**Filter Type:** {filter_type}")
        st.write(f"**Filter Flow:** {flow_rate_lph} L/h")
        st.write(f"**Turnover:** {turnover:.1f}x per hour")
        st.write(f"**Stocking Level:** {stocking_level}")
        st.write(f"**Estimated Biomass:** {biomass_g}g")
        st.write(f"**Feed Type:** {feed_type}")
        st.write(f"**Feed Level:** {str(feed_level).title()}")
        st.write(f"**Approx Feed / Event:** {approx_grams:.3f}g")
        st.write(f"**Approx % Bodyweight / Event:** {approx_pct_bw:.1f}%")
        st.write(f"**Time Scale:** {time_scale_label}")
        st.write(f"**Goal:** {goal}")
        st.write(f"**Feed Times:** {feed_times if feed_times else 'None'}")
        if feed_times:
            st.write(f"**Real-time equivalents:** {real_time_text(feed_times, minutes_per_interval)}")
            if schedule_mode == "Daily schedule":
                st.write(f"**Daily routine wording:** Feed at {real_time_text(feed_times[:min(len(feed_times), 5)], minutes_per_interval)} from the start of the cycle.")
        st.write(f"**Model Rates:** kₛ = {k_s:.2f}, k_c = {k_c:.2f}, k_f = {k_f:.2f}")
        st.write(f"**Raw Total Removal Rate:** {total_removal:.2f}")

    with st.expander("Sensitivity / What-if", expanded=True):
        st.write("**What if feed amount changes by 20%?**")
        w1, w2 = st.columns(2)
        with w1:
            st.metric("+20% feed", f"{plus20_grams:.3f}g")
            st.write(f"Peak waste: {max_value(plus20_values):.2f}")
            plus_clear = time_to_clear(plus20_values) or 0
            st.write(f"Recovery time: {format_duration(plus_clear * minutes_per_interval)}")
        with w2:
            st.metric("-20% feed", f"{minus20_grams:.3f}g")
            st.write(f"Peak waste: {max_value(minus20_values):.2f}")
            minus_clear = time_to_clear(minus20_values) or 0
            st.write(f"Recovery time: {format_duration(minus_clear * minutes_per_interval)}")

    with st.expander("Model Details", expanded=False):
        st.write("This simulation uses a simple discrete decay model.")
        st.latex(r"P(t+1)=P(t)-(k_s+k_c+k_f)P(t)+F(t)")
        st.write("Where:")
        st.write("- P(t): particle concentration at time t")
        st.write("- kₛ: settling rate")
        st.write("- k_c: biological consumption / breakdown rate")
        st.write("- k_f: filtration rate")
        st.write("- F(t): feed input at time t")
