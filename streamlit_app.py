from __future__ import annotations

from datetime import time, datetime
from typing import Dict, List, Tuple, Optional

import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="AquaFeed Optimiser", page_icon="🐟", layout="wide")

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────

TIME_SCALE_OPTIONS = {"10 minutes": 10, "15 minutes": 15, "30 minutes": 30, "1 hour": 60}

FILTER_TYPE_INFO = {
    "Sponge filter":    {"efficiency": 0.72, "description": "Gentle flow, strong biological filtration. Best for shrimp and fry."},
    "Internal filter":  {"efficiency": 0.95, "description": "Moderate all-round filtration. Common in standard home tanks."},
    "Hang-on-back":     {"efficiency": 1.05, "description": "Good surface movement with moderate mechanical filtration."},
    "Canister filter":  {"efficiency": 1.20, "description": "Strong mechanical and biological filtration. Best for larger or heavier-waste tanks."},
}

FEED_TYPE_INFO = {
    "Pellets":                       {"spike": 1.00, "linger": 1.00, "description": "Moderate spike, moderate decay. Good all-round reference food.", "visual": "roughly a small cluster of pellets",         "grams_per_pellet": 0.036},
    "Flakes":                        {"spike": 1.20, "linger": 1.08, "description": "Break up quickly — sharper waste spike if overfed.",              "visual": "roughly a light-to-moderate pinch",          "grams_per_pellet": None},
    "Powder / shrimp food":          {"spike": 1.35, "linger": 1.12, "description": "Spreads fast through the water column — spikes quickly.",         "visual": "roughly a visible dusting",                  "grams_per_pellet": None},
    "Frozen / live food":            {"spike": 1.15, "linger": 0.92, "description": "Richer and messier, but not as instantly dispersed as powder.",   "visual": "roughly a small cube or chunk equivalent",   "grams_per_pellet": None},
    "Slow-release / wafers":         {"spike": 0.70, "linger": 0.65, "description": "Releases waste gradually — lower spike, longer duration.",        "visual": "roughly one wafer or small piece",           "grams_per_pellet": None},
}

STOCKING_INFO   = {"Light": "Few animals for the tank size — lower waste production.", "Moderate": "Typical home stocking — balanced waste.", "Heavy": "High population — higher waste, less margin for error."}
PLANT_INFO      = {"None": "No plants — no additional nutrient uptake.", "Low": "A few stems or low-coverage plants.", "Moderate": "Reasonably planted — some nutrient uptake and biofilm.", "High": "Heavily planted — significant biological buffering."}
MATURITY_INFO   = {
    "New (<1 month)":          {"multiplier": 0.88, "description": "Less stable and less forgiving of waste spikes."},
    "Established (1–6 months)":{"multiplier": 1.00, "description": "More stable and predictable."},
    "Mature (6+ months)":      {"multiplier": 1.08, "description": "More biologically resilient if maintenance is consistent."},
}
SUBSTRATE_INFO  = {
    "Bare bottom":          {"multiplier": 0.95, "description": "Less biofilm support, less passive buffering."},
    "Standard substrate":   {"multiplier": 1.00, "description": "Typical balance of cleanliness and biological support."},
    "Planted / biofilm-rich":{"multiplier": 1.08, "description": "More surface area and biological activity to process waste."},
}
GOAL_INFO = {
    "Balanced feeding":           "Practical middle ground between growth and waste control.",
    "Minimise waste":             "Prioritises cleaner water over aggressive feeding.",
    "Maximise feeding frequency": "Allows more frequent feeds — tolerates slightly more load.",
}
SIMPLE_FEED_LEVELS = {"Very light": 2.0, "Light": 3.5, "Normal": 5.0, "Heavy": 7.5, "Very heavy": 10.0}

PRESETS = {
    "Nano shrimp tank": {
        "tank_type": "Shrimp Tank", "tank_size_l": 20, "tank_maturity": "Established (1–6 months)",
        "substrate_type": "Planted / biofilm-rich", "filter_type": "Sponge filter", "flow_rate_lph": 80,
        "stocking_level": "Moderate", "feed_type": "Powder / shrimp food", "temperature": 23,
        "plant_density": "Moderate", "water_change_pct": 20, "water_change_days": 7,
    },
    "Community fish tank": {
        "tank_type": "Fish Tank", "tank_size_l": 60, "tank_maturity": "Established (1–6 months)",
        "substrate_type": "Standard substrate", "filter_type": "Hang-on-back", "flow_rate_lph": 300,
        "stocking_level": "Moderate", "feed_type": "Flakes", "temperature": 25,
        "plant_density": "Low", "water_change_pct": 25, "water_change_days": 7,
    },
    "Planted discus tank": {
        "tank_type": "Fish Tank", "tank_size_l": 120, "tank_maturity": "Mature (6+ months)",
        "substrate_type": "Planted / biofilm-rich", "filter_type": "Canister filter", "flow_rate_lph": 600,
        "stocking_level": "Light", "feed_type": "Pellets", "temperature": 28,
        "plant_density": "High", "water_change_pct": 30, "water_change_days": 3,
    },
    "Goldfish pond tank": {
        "tank_type": "Fish Tank", "tank_size_l": 200, "tank_maturity": "Mature (6+ months)",
        "substrate_type": "Bare bottom", "filter_type": "Canister filter", "flow_rate_lph": 1000,
        "stocking_level": "Heavy", "feed_type": "Pellets", "temperature": 18,
        "plant_density": "None", "water_change_pct": 20, "water_change_days": 7,
    },
    "Beginner betta tank": {
        "tank_type": "Fish Tank", "tank_size_l": 20, "tank_maturity": "New (<1 month)",
        "substrate_type": "Standard substrate", "filter_type": "Sponge filter", "flow_rate_lph": 100,
        "stocking_level": "Light", "feed_type": "Pellets", "temperature": 26,
        "plant_density": "Low", "water_change_pct": 25, "water_change_days": 7,
    },
}

COMMON_MISTAKES = [
    ("Feeding by the clock, not the tank",    "Fish behaviour tells you more than a schedule. If food disappears in under a minute every single time, you might be able to feed slightly more. If leftovers appear regularly, reduce immediately."),
    ("Using the same amount for every food",  "Flakes and powder spread much faster than pellets. A 'normal pinch' of powder can spike waste 35% higher than the same weight of pellets. Adjust down when switching to fine foods."),
    ("Forgetting smaller tanks concentrate faster", "A 20L tank has one-third the buffering capacity of a 60L tank. What works in a large community tank can crash a nano setup within days."),
    ("Feeding multiple tanks at the same time","Double-feeding happens most in multi-tank homes. Feed one tank, move on, come back — you may not remember which you already fed."),
    ("Ignoring recovery time between feeds",  "Two feeds per day is only safe if the tank has fully cleared from the first. If you feed at 9am and 6pm, check whether your setup can actually recover in 9 hours."),
    ("Overfeeding 'because the fish looks hungry'", "Fish almost always look hungry. They have no satiation signals that humans can read reliably. Judge by leftovers and water clarity, not fish behaviour at the glass."),
]

# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────

def init_session_state():
    defaults = {
        "onboarding_complete": False,
        "wizard_step": 1,
        "wizard": {},
        "profiles": {},
        "feeding_log": [],
        "last_optimise_changes": [],
        "load_preset": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session_state()

# ─────────────────────────────────────────────
# UTILITY FUNCTIONS
# ─────────────────────────────────────────────

def safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0

def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))

def format_duration(minutes: float) -> str:
    if minutes < 60:   return f"{minutes:.0f} min"
    if minutes < 1440: return f"{minutes/60:.1f} h"
    return f"{minutes/1440:.1f} days"

def real_time_text(points: List[int], mpi: int) -> str:
    if not points: return "None"
    return ", ".join(format_duration(p * mpi) for p in points)

def turnover_judgement(turnover: float, tank_type: str) -> str:
    lo, hi = (3, 7) if tank_type == "Shrimp Tank" else (3, 6)
    if turnover < lo: return "Low"
    if turnover < hi: return "Moderate"
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

def risk_colour(score: float) -> str:
    if score >= 8: return "success"
    if score >= 5: return "warning"
    return "error"

def practical_feed_label(feed_amount: float) -> str:
    if feed_amount < 2.5: return "Very light"
    if feed_amount < 4.0: return "Light"
    if feed_amount < 6.5: return "Normal"
    if feed_amount < 9.0: return "Heavy"
    return "Very heavy"

def estimate_biomass_g(tank_type: str, tank_size_l: int, stocking_level: str, animal_count: int) -> float:
    if animal_count > 0:
        avg_weights = {"Shrimp Tank": 0.5, "Fish Tank": 5.0, "Mixed Tank": 2.0, "Custom": 3.0}
        return round(max(animal_count * avg_weights.get(tank_type, 3.0), 5.0), 1)
    density = {
        "Shrimp Tank": {"Light": 0.18, "Moderate": 0.35, "Heavy": 0.60},
        "Fish Tank":   {"Light": 0.50, "Moderate": 1.10, "Heavy": 2.00},
    }.get(tank_type, {"Light": 0.30, "Moderate": 0.70, "Heavy": 1.20})
    return round(max(tank_size_l * density[stocking_level], 5.0), 1)

def feed_amount_to_pct_bw(feed_amount: float) -> float:
    return round(feed_amount * 0.6, 2)

def estimated_feed_grams(feed_amount: float, biomass_g: float) -> float:
    return round(biomass_g * (feed_amount_to_pct_bw(feed_amount) / 100), 3)

def pellet_equivalent_text(feed_type: str, grams: float) -> str:
    info = FEED_TYPE_INFO[feed_type]
    if feed_type == "Pellets":
        count = int(max(1, round(grams / info["grams_per_pellet"])))
        if count <= 6:  return f"about {count} small pellets"
        if count <= 20: return f"about {count} small-to-medium pellets"
        return f"about {count} pellets (heavy feed)"
    return str(info["visual"])

# ─────────────────────────────────────────────
# IMPROVED MODEL
# ─────────────────────────────────────────────

def map_setup_to_rates(
    tank_type: str, stocking_level: str, tank_size_l: int,
    filter_type: str, flow_rate_lph: int, feed_type: str,
    tank_maturity: str, substrate_type: str,
    temperature: float, plant_density: str,
) -> Tuple[float, float, float, Dict]:
    turnover    = safe_div(flow_rate_lph, tank_size_l)
    fe          = float(FILTER_TYPE_INFO[filter_type]["efficiency"])
    fl          = float(FEED_TYPE_INFO[feed_type]["linger"])
    mat_mult    = float(MATURITY_INFO[tank_maturity]["multiplier"])
    sub_mult    = float(SUBSTRATE_INFO[substrate_type]["multiplier"])
    plant_mult  = {"None": 1.0, "Low": 1.05, "Moderate": 1.12, "High": 1.22}[plant_density]
    temp_mult   = 1.0 + (temperature - 24) * 0.025   # warmer = faster biology

    if tank_type == "Shrimp Tank":
        tank_flow_mod  = 0.82
        base_settling  = 0.16 * 0.95
        base_consume   = {"Light": 0.06, "Moderate": 0.10, "Heavy": 0.15}[stocking_level] * 0.65  # shrimp graze slowly
    elif tank_type == "Fish Tank":
        tank_flow_mod  = 1.05
        base_settling  = 0.20
        base_consume   = {"Light": 0.06, "Moderate": 0.10, "Heavy": 0.15}[stocking_level] * 1.08
    else:
        tank_flow_mod  = 0.95
        base_settling  = 0.18
        base_consume   = {"Light": 0.06, "Moderate": 0.10, "Heavy": 0.15}[stocking_level]

    size_mod = 0.95 if tank_size_l <= 30 else (1.08 if tank_size_l >= 150 else 1.0)

    kf = clamp((turnover / 10.0) * fe * tank_flow_mod * mat_mult, 0.05, 0.42)
    ks = clamp(base_settling * size_mod * fl, 0.04, 0.32)
    kc = clamp(base_consume * size_mod * clamp(fl, 0.65, 1.15) * mat_mult * sub_mult * plant_mult * temp_mult, 0.03, 0.28)

    return ks, kc, kf, {"turnover": turnover}


def run_simulation(
    feed_times: List[int], simulation_length: int, feed_amount: float,
    k_s: float, k_c: float, k_f: float, feed_type: str,
    use_saturation: bool = True,
    water_change_steps: Optional[List[int]] = None,
    water_change_pct: float = 0.0,
) -> List[float]:
    p         = 0.0
    satiation = 0.0
    results   = []
    spike     = float(FEED_TYPE_INFO[feed_type]["spike"])
    wc_steps  = set(water_change_steps or [])

    for t in range(simulation_length):
        # Water change event — reduce particle concentration
        if t in wc_steps and water_change_pct > 0:
            p *= (1.0 - water_change_pct / 100.0)

        # Feed event
        if t in feed_times:
            p        += feed_amount * spike
            satiation = min(1.0, satiation + feed_amount * 0.18)

        # Satiation decay — animals get hungry again over time
        satiation = max(0.0, satiation - 0.07)

        # Effective consumption (slows when animals are full)
        kc_eff        = k_c * (max(0.12, 1.0 - satiation * 0.68) if use_saturation else 1.0)
        total_removal = k_s + kc_eff + k_f
        p             = max(0.0, p - total_removal * p)
        results.append(round(p, 4))

    return results


def build_water_change_steps(
    simulation_length: int, minutes_per_interval: int,
    water_change_pct: float, water_change_days: int,
) -> List[int]:
    if water_change_pct <= 0 or water_change_days <= 0:
        return []
    steps_per_day = int((24 * 60) / minutes_per_interval)
    return [i * steps_per_day * water_change_days for i in range(1, simulation_length // max(1, steps_per_day * water_change_days) + 2)
            if i * steps_per_day * water_change_days < simulation_length]

# ─────────────────────────────────────────────
# SCORING + ANALYSIS
# ─────────────────────────────────────────────

def area_under_curve(values: List[float]) -> float: return sum(values)
def max_value(values: List[float]) -> float:       return max(values) if values else 0.0

def time_to_threshold(values: List[float], start: int, threshold: float) -> Optional[int]:
    for i in range(start, len(values)):
        if values[i] <= threshold:
            return i - start
    return None

def time_to_clear(values: List[float], ratio: float = 0.05) -> Optional[int]:
    peak = max_value(values)
    if peak <= 0: return 0
    pi = values.index(peak)
    return time_to_threshold(values, pi, peak * ratio)

def time_to_baseline(values: List[float], threshold: float = 0.05) -> Optional[int]:
    peak = max_value(values)
    if peak <= 0: return 0
    pi = values.index(peak)
    return time_to_threshold(values, pi, threshold)

def detect_overlap(values: List[float], feed_times: List[int]) -> bool:
    if len(feed_times) < 2 or not values: return False
    peak = max_value(values)
    if peak <= 0: return False
    return any(0 <= ft < len(values) and values[ft] > peak * 0.20 for ft in feed_times[1:])

def average_feed_gap(feed_times: List[int]) -> Optional[float]:
    if len(feed_times) < 2: return None
    gaps = [feed_times[i] - feed_times[i-1] for i in range(1, len(feed_times))]
    return sum(gaps) / len(gaps)

def recommended_gap(values: List[float]) -> Optional[int]:
    ct = time_to_clear(values)
    return None if ct is None else max(ct + 2, 1)

def timing_score(values: List[float], feed_times: List[int]) -> float:
    if not feed_times: return 0.0
    gn = recommended_gap(values)
    if len(feed_times) < 2: return 10.0
    ag = average_feed_gap(feed_times)
    if gn is None or ag is None: return 5.0
    overlap_pen = 3.0 if detect_overlap(values, feed_times) else 0.0
    ratio  = ag / gn if gn > 0 else 1.0
    score  = 10.0 * clamp(ratio, 0, 1) - overlap_pen
    if ag >= gn: score = min(10.0, score + 2.0)
    return round(clamp(score, 0, 10), 1)

def load_score(peak: float, total_load: float, n_feeds: int, goal: str) -> float:
    if n_feeds == 0: return 0.0
    score = 10.0 - (peak / 1.5) - (total_load / 12.0)
    if goal == "Minimise waste" and peak > 5:   score -= 1.0
    if goal == "Maximise feeding frequency":     score += 0.5
    return round(clamp(score, 0, 10), 1)

def overall_efficiency_score(timing: float, load: float) -> float:
    return round(clamp((timing * 0.45) + (load * 0.55), 0, 10), 1)

def generate_summary(overlap: bool, peak: float, gap_ok: bool, goal: str) -> str:
    if overlap and peak > 6: return "Your feeds are too close and each feed is too heavy for this setup."
    if overlap:              return "Your feeds are too close — the tank isn't recovering in time."
    if peak > 6:             return "Your timing is fine, but each feed is too heavy for this setup."
    if goal == "Minimise waste": return "This plan keeps waste risk low — well suited to your goal."
    if goal == "Maximise feeding frequency": return "This plan handles multiple feeds cleanly for your setup."
    return "This feeding plan looks balanced for the chosen setup."

def visible_tank_effects(tank_type: str, peak: float, overlap: bool) -> List[str]:
    effects = []
    if peak < 3:    effects += ["Food should clear without visible leftovers.", "Water clarity should stay stable after feeding."]
    elif peak < 6:  effects += ["Some food may sit briefly before clearing.", "The tank should cope, but repeated heavy feeding can build waste."]
    else:           effects += ["Visible leftovers are likely if animals don't clear food quickly.", "Cloudy water or substrate waste is more probable after feeding."]
    if overlap:     effects.append("Feeding again too soon may prevent full recovery.")
    if tank_type == "Shrimp Tank" and peak > 4:
        effects.append("Shrimp graze slowly — food may look present but still be disappearing.")
    return effects

def reality_check_list(tank_type: str) -> List[str]:
    base = [
        "If food is still visible after the suggested recovery window, reduce feed.",
        "If water clouds after feeding, overfeeding or slow breakdown is likely.",
        "If the tank clears food much faster than predicted, you may be able to feed slightly more.",
    ]
    if tank_type == "Shrimp Tank":
        base += ["Shrimp swarm food quickly when very hungry — but they also graze slowly over hours. Both are normal.",
                 "If food sits untouched after 3 hours, try a different food type or reduce the amount."]
    else:
        base += ["If fish leave visible leftovers after 5 minutes, reduce feed.",
                 "If fish appear frantic and food disappears instantly every time, the plan may be too light."]
    return base

# ─────────────────────────────────────────────
# SUGGESTIONS + OPTIMISER
# ─────────────────────────────────────────────

def suggest_better_spacing(feed_times: List[int], values: List[float], sim_len: int) -> List[int]:
    if not feed_times or len(feed_times) < 2: return []
    gap = recommended_gap(values)
    if gap is None: return []
    out = [feed_times[0]]
    for _ in range(1, len(feed_times)):
        nxt = out[-1] + gap
        if nxt < sim_len: out.append(nxt)
    return out

def suggest_reduced_feed(grams: float, peak: float, target: float = 5.0) -> float:
    if peak <= target: return round(grams, 3)
    return round(max(0.02, grams * (target / peak)), 3)

def optimise_feed_plan(
    feed_times: List[int], feed_grams: float, sim_len: int,
    k_s: float, k_c: float, k_f: float, feed_type: str, goal: str,
    water_change_steps: List[int], water_change_pct: float,
) -> Tuple[List[int], float, List[str]]:
    if not feed_times: return [], feed_grams, []
    orig_times  = list(feed_times)
    orig_amount = feed_grams
    changes     = []

    vals = run_simulation(feed_times, sim_len, feed_grams, k_s, k_c, k_f, feed_type,
                          water_change_steps=water_change_steps, water_change_pct=water_change_pct)
    peak = max_value(vals)
    better_times  = suggest_better_spacing(feed_times, vals, sim_len)
    better_amount = feed_grams

    if goal in ["Minimise waste", "Balanced feeding"]:
        better_amount = suggest_reduced_feed(feed_grams, peak)

    if better_times and better_times != orig_times:
        gn = recommended_gap(vals) or 0
        changes.append(f"Adjusted feed spacing to a minimum gap of {real_time_text([gn], 15)} between feeds.")
    if abs(better_amount - orig_amount) > 0.001:
        changes.append(f"Reduced feed amount from {orig_amount:.3f}g to {better_amount:.3f}g to bring peak load into the safe zone.")
    if not changes:
        changes.append("No significant changes needed — your plan is already well-optimised for the chosen goal.")

    return (better_times or orig_times), better_amount, changes

# ─────────────────────────────────────────────
# SHAREABLE URL + TEXT SUMMARY
# ─────────────────────────────────────────────

def build_summary_text(
    tank_type, tank_size_l, stocking_level, filter_type, flow_rate_lph,
    feed_type, approx_grams, feed_level, turnover, summary_text,
    gap_minutes, peak_value, overall_eff, feed_times, minutes_per_interval,
) -> str:
    lines = [
        "AQUAFEED OPTIMISER — RESULTS SUMMARY",
        "=" * 40,
        f"Tank:     {tank_type} | {tank_size_l}L | {stocking_level} stocking",
        f"Filter:   {filter_type} @ {flow_rate_lph}L/h (turnover: {turnover:.1f}x/h)",
        f"Feed:     {feed_type} | {approx_grams:.3f}g per feed ({feed_level} level)",
        f"Schedule: {real_time_text(feed_times, minutes_per_interval)} after start",
        "",
        f"VERDICT:  {summary_text}",
        f"Feed amount: {approx_grams:.3f}g per feed ({pellet_equivalent_text(feed_type, approx_grams)})",
        f"Wait between feeds: at least {format_duration(gap_minutes)}",
        f"Peak feeding load: {peak_value:.2f}  |  Waste risk: {risk_word(overall_eff)}",
        "",
        "Generated by AquaFeed Optimiser",
    ]
    return "\n".join(lines)

def load_preset_into_session(preset_name: str):
    p = PRESETS[preset_name]
    for k, v in p.items():
        st.session_state[f"preset_{k}"] = v

# ─────────────────────────────────────────────
# ONBOARDING WIZARD
# ─────────────────────────────────────────────

def show_onboarding():
    st.markdown("## Welcome to AquaFeed Optimiser 🐟")
    st.markdown("Answer 5 quick questions and we'll tell you exactly how to feed your tank.")

    step  = st.session_state.wizard_step
    wiz   = st.session_state.wizard
    total = 5

    progress = st.progress(step / total)
    st.caption(f"Step {step} of {total}")
    st.divider()

    if step == 1:
        st.markdown("### What kind of tank do you have?")
        cols = st.columns(3)
        options = [("🦐 Shrimp tank", "Shrimp Tank"), ("🐠 Fish tank", "Fish Tank"), ("🌿 Mixed / planted", "Mixed Tank")]
        for col, (label, val) in zip(cols, options):
            with col:
                if st.button(label, use_container_width=True, key=f"wiz_tank_{val}"):
                    wiz["tank_type"] = val
                    st.session_state.wizard_step = 2
                    st.rerun()

    elif step == 2:
        st.markdown("### How big is the tank?")
        size = st.select_slider("Tank size", options=[10,15,20,30,40,50,60,80,100,120,150,200,300], value=60)
        hint = ("Very small — be conservative with feeding." if size <= 20 else
                "Small — less margin for error." if size <= 50 else
                "Medium — reasonable margin." if size <= 100 else
                "Large — more forgiving." if size <= 200 else "Very large — excellent buffering.")
        st.caption(f"💧 {hint}")
        wiz["tank_size_l"] = size
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("← Back"): st.session_state.wizard_step = 1; st.rerun()
        with col2:
            if st.button("Next →", type="primary", use_container_width=True):
                st.session_state.wizard_step = 3; st.rerun()

    elif step == 3:
        st.markdown("### How many animals are in it?")
        st.caption("Rough estimate — used to calculate a realistic feed weight.")
        count_label = st.radio("", ["A few (under 15)", "Some (15–40)", "Lots (40+)", "Not sure — skip"], horizontal=True)
        count_map   = {"A few (under 15)": 8, "Some (15–40)": 25, "Lots (40+)": 60, "Not sure — skip": 0}
        wiz["animal_count"] = count_map[count_label]
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("← Back"): st.session_state.wizard_step = 2; st.rerun()
        with col2:
            if st.button("Next →", type="primary", use_container_width=True):
                st.session_state.wizard_step = 4; st.rerun()

    elif step == 4:
        st.markdown("### What do you feed them?")
        cols   = st.columns(2)
        ftypes = list(FEED_TYPE_INFO.keys())
        chosen = None
        for i, ft in enumerate(ftypes):
            with cols[i % 2]:
                if st.button(ft, use_container_width=True, key=f"wiz_ft_{i}",
                             help=FEED_TYPE_INFO[ft]["description"]):
                    wiz["feed_type"] = ft
                    st.session_state.wizard_step = 5
                    st.rerun()
        col1, _ = st.columns([1, 3])
        with col1:
            if st.button("← Back"): st.session_state.wizard_step = 3; st.rerun()

    elif step == 5:
        st.markdown("### How often do you currently feed?")
        freq_label = st.radio("", ["Once a day", "Twice a day", "3+ times a day", "Every other day"], horizontal=True)
        wiz["feed_freq"] = freq_label
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("← Back"): st.session_state.wizard_step = 4; st.rerun()
        with col2:
            if st.button("See my results →", type="primary", use_container_width=True):
                st.session_state.onboarding_complete = True
                st.rerun()

    st.divider()
    if st.button("Skip setup — go straight to full tool"):
        st.session_state.onboarding_complete = True
        st.rerun()

# ─────────────────────────────────────────────
# SHOW ONBOARDING IF NEEDED
# ─────────────────────────────────────────────

if not st.session_state.onboarding_complete:
    show_onboarding()
    st.stop()

# ─────────────────────────────────────────────
# DERIVE WIZARD DEFAULTS IF SET
# ─────────────────────────────────────────────

wiz = st.session_state.wizard
wiz_tank        = wiz.get("tank_type", "Fish Tank")
wiz_size        = wiz.get("tank_size_l", 60)
wiz_count       = wiz.get("animal_count", 0)
wiz_feed        = wiz.get("feed_type", "Pellets")
wiz_freq        = wiz.get("feed_freq", "Once a day")
wiz_feeds_count = {"Once a day": 1, "Twice a day": 2, "3+ times a day": 3, "Every other day": 1}.get(wiz_freq, 1)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

with st.sidebar:
    st.header("AquaFeed Optimiser 🐟")

    # ── Presets ──
    with st.expander("Load a preset tank", expanded=False):
        for name in PRESETS:
            if st.button(name, use_container_width=True, key=f"preset_{name}"):
                for k, v in PRESETS[name].items():
                    st.session_state[f"pval_{k}"] = v
                st.rerun()

    # ── Profiles ──
    with st.expander("Saved tank profiles", expanded=False):
        profiles = st.session_state.profiles
        if profiles:
            load_name = st.selectbox("Load profile", ["— select —"] + list(profiles.keys()))
            if load_name != "— select —" and st.button("Load", key="load_prof"):
                for k, v in profiles[load_name].items():
                    st.session_state[f"pval_{k}"] = v
                st.rerun()
        save_name = st.text_input("Save current setup as…")
        if st.button("Save profile") and save_name:
            st.session_state.profiles[save_name] = {}   # populated after sidebar runs
            st.session_state["_pending_save_name"] = save_name
            st.success(f"Profile '{save_name}' saved.")

    # ── Tank Setup ──
    st.header("Tank setup")

    def pval(key, default):
        return st.session_state.get(f"pval_{key}", default)

    tank_type = st.selectbox("Tank type", ["Shrimp Tank", "Fish Tank", "Mixed Tank", "Custom"],
                             index=["Shrimp Tank","Fish Tank","Mixed Tank","Custom"].index(pval("tank_type", wiz_tank)))
    tank_size_l    = st.slider("Tank size (litres)", 10, 500, pval("tank_size_l", wiz_size), 5)
    animal_count   = st.number_input("Approximate animal count (0 = estimate)", min_value=0, max_value=2000,
                                     value=pval("animal_count", wiz_count), step=1)
    tank_maturity  = st.selectbox("Tank maturity", list(MATURITY_INFO.keys()), index=1)
    substrate_type = st.selectbox("Substrate / biofilm", list(SUBSTRATE_INFO.keys()), index=1)
    plant_density  = st.selectbox("Plant density", list(PLANT_INFO.keys()),
                                  index=list(PLANT_INFO.keys()).index(pval("plant_density", "Low")))
    filter_type    = st.selectbox("Filter type", list(FILTER_TYPE_INFO.keys()),
                                  index=list(FILTER_TYPE_INFO.keys()).index(pval("filter_type", "Internal filter")))
    flow_rate_lph  = st.slider("Filter flow rate (L/h)", 50, 3000, pval("flow_rate_lph", 300), 25)
    stocking_level = st.selectbox("Stocking level", ["Light","Moderate","Heavy"],
                                  index=["Light","Moderate","Heavy"].index(pval("stocking_level","Moderate")))
    feed_type      = st.selectbox("Feed type", list(FEED_TYPE_INFO.keys()),
                                  index=list(FEED_TYPE_INFO.keys()).index(pval("feed_type", wiz_feed)))
    temperature    = st.slider("Water temperature (°C)", 16, 32, pval("temperature", 24), 1)

    turnover               = safe_div(flow_rate_lph, tank_size_l)
    filtration_strength    = turnover_judgement(turnover, tank_type)

    st.caption(STOCKING_INFO[stocking_level])
    st.caption(MATURITY_INFO[tank_maturity]["description"])
    st.caption(SUBSTRATE_INFO[substrate_type]["description"])
    st.caption(PLANT_INFO[plant_density])
    st.caption(FILTER_TYPE_INFO[filter_type]["description"])
    st.caption(FEED_TYPE_INFO[feed_type]["description"])
    st.caption(f"Turnover: {turnover:.1f}x/h ({filtration_strength.lower()} filtration) · {temperature}°C")

    # ── Water Changes ──
    st.header("Water changes")
    water_change_pct  = st.slider("Water change amount (%)", 0, 50,
                                  pval("water_change_pct", 20), 5)
    water_change_days = st.slider("Every N days", 1, 14,
                                  pval("water_change_days", 7), 1,
                                  help="Set to 0 to disable water changes in the simulation")
    if water_change_pct > 0:
        st.caption(f"Simulating a {water_change_pct}% water change every {water_change_days} day(s).")

    # ── Simulation Settings ──
    st.header("Simulation")
    time_scale_label   = st.selectbox("Time interval", list(TIME_SCALE_OPTIONS.keys()), index=1)
    minutes_per_interval = TIME_SCALE_OPTIONS[time_scale_label]
    simulation_length  = st.slider("Simulation length (intervals)", 20, 288, 96, 4)
    st.caption(f"Timeline: about {format_duration(simulation_length * minutes_per_interval)} total.")

    # ── Feeding Plan ──
    st.header("Feeding plan")
    feed_input_mode = st.radio("Feed amount input", ["Simple", "Advanced"], horizontal=True)
    biomass_g       = estimate_biomass_g(tank_type, tank_size_l, stocking_level, int(animal_count))

    if feed_input_mode == "Simple":
        feed_level  = st.select_slider("Feed size", options=list(SIMPLE_FEED_LEVELS.keys()), value="Normal")
        feed_amount = SIMPLE_FEED_LEVELS[feed_level]
    else:
        feed_amount = st.slider("Feed amount (model units)", 0.5, 20.0, 5.0, 0.5)
        feed_level  = practical_feed_label(feed_amount)

    approx_pct_bw  = feed_amount_to_pct_bw(feed_amount)
    approx_grams   = estimated_feed_grams(feed_amount, biomass_g)
    st.caption(f"**{feed_level}** feed · ~**{approx_pct_bw:.1f}%** body weight · ~**{approx_grams:.3f}g** for this setup")
    st.caption(f"Estimated livestock biomass: ~**{biomass_g}g**")
    st.caption(f"Visual guide: {pellet_equivalent_text(feed_type, approx_grams)}")

    # ── Schedule ──
    schedule_mode = st.radio("Schedule mode", ["Daily schedule", "Timeline"], horizontal=True)
    if schedule_mode == "Daily schedule":
        feeds_per_day  = st.slider("Feeds per day", 0, 5, wiz_feeds_count)
        days_to_sim    = st.slider("Days to simulate", 1, 7, 1)
        one_day_int    = int((24 * 60) / minutes_per_interval)
        simulation_length = max(simulation_length, one_day_int * days_to_sim)
        daily_pts: List[int] = []
        for i in range(feeds_per_day):
            default_h  = [9, 18, 21, 12, 15][i] if i < 5 else 9
            fc         = st.time_input(f"Feed {i+1}", value=time(default_h, 0), step=900)
            mins_start = fc.hour * 60 + fc.minute
            daily_pts.append(int(round(mins_start / minutes_per_interval)))
        feed_times: List[int] = sorted(set(
            p + day * one_day_int
            for day in range(days_to_sim)
            for p in daily_pts
        ))
        st.caption(f"Covering {days_to_sim} day(s).")
    else:
        n_feeds    = st.slider("Number of feeds", 0, 5, wiz_feeds_count)
        feed_times = []
        for i in range(n_feeds):
            default    = [10, 30, 50, 70, 90][i] if i < 5 else 10 + i * 10
            ft         = st.slider(f"Feed {i+1} (intervals)", 0, simulation_length-1,
                                   min(default, simulation_length-1), 1)
            feed_times.append(ft)

    goal = st.selectbox("Optimisation goal", list(GOAL_INFO.keys()))
    st.caption(GOAL_INFO[goal])

    # ── Model options ──
    with st.expander("Advanced model options"):
        use_saturation = st.checkbox("Consumption saturation model", value=True,
                                     help="Consumption rate slows when animals are full — more realistic for multiple daily feeds.")
        show_baseline  = st.checkbox("Show baseline comparison", value=True)
        use_custom     = st.checkbox("Override model rates manually")
        if use_custom:
            k_s = st.slider("Settling rate (kₛ)", 0.00, 0.50, 0.18, 0.01)
            k_c = st.slider("Consumption rate (k_c)", 0.00, 0.50, 0.10, 0.01)
            k_f = st.slider("Filtration rate (k_f)", 0.00, 0.50, 0.20, 0.01)
        else:
            k_s, k_c, k_f, _ = map_setup_to_rates(
                tank_type, stocking_level, tank_size_l, filter_type, flow_rate_lph,
                feed_type, tank_maturity, substrate_type, temperature, plant_density
            )

    auto_optimise = st.button("✨ Optimise my feeding plan", type="primary")
    if st.button("↩ Start over / change tank"):
        st.session_state.onboarding_complete = False
        st.session_state.wizard_step = 1
        st.session_state.wizard = {}
        st.rerun()

# ─────────────────────────────────────────────
# RUN SIMULATION
# ─────────────────────────────────────────────

feed_times = sorted(set(t for t in feed_times if 0 <= t < simulation_length))

wc_steps = build_water_change_steps(simulation_length, minutes_per_interval, water_change_pct, water_change_days)

optimise_changes = []
if auto_optimise:
    feed_times, approx_grams, optimise_changes = optimise_feed_plan(
        feed_times, approx_grams, simulation_length, k_s, k_c, k_f,
        feed_type, goal, wc_steps, water_change_pct,
    )
    st.session_state.last_optimise_changes = optimise_changes

values = run_simulation(
    feed_times, simulation_length, approx_grams, k_s, k_c, k_f, feed_type,
    use_saturation=use_saturation, water_change_steps=wc_steps, water_change_pct=water_change_pct,
)
baseline_values = run_simulation(
    [10] if simulation_length > 10 else [0], simulation_length, approx_grams,
    k_s, k_c, k_f, feed_type, use_saturation=use_saturation,
    water_change_steps=wc_steps, water_change_pct=water_change_pct,
)

# ── Derived metrics ──
peak_value    = max_value(values)
total_removal = k_s + k_c + k_f
total_load    = area_under_curve(values)
clear_steps   = time_to_clear(values) or 0
baseline_steps= time_to_baseline(values) or 0
gap_needed    = (recommended_gap(values) or 0)
overlap       = detect_overlap(values, feed_times)
timing_eff    = timing_score(values, feed_times)
load_eff      = load_score(peak_value, total_load, len(feed_times), goal)
overall_eff   = overall_efficiency_score(timing_eff, load_eff)
avg_gap       = average_feed_gap(feed_times)
gap_ok        = True if len(feed_times) < 2 else (avg_gap is not None and avg_gap >= gap_needed)
recovery_mins = clear_steps * minutes_per_interval
gap_mins      = gap_needed * minutes_per_interval
baseline_load = area_under_curve(baseline_values)
vs_baseline   = total_load - baseline_load
summary_text  = generate_summary(overlap, peak_value, bool(gap_ok), goal)
visible_eff   = visible_tank_effects(tank_type, peak_value, overlap)
reality_chks  = reality_check_list(tank_type)
plus20_g      = round(approx_grams * 1.2, 3)
minus20_g     = round(max(0.02, approx_grams * 0.8), 3)
plus20_vals   = run_simulation(feed_times, simulation_length, plus20_g, k_s, k_c, k_f, feed_type,
                               use_saturation=use_saturation, water_change_steps=wc_steps, water_change_pct=water_change_pct)
minus20_vals  = run_simulation(feed_times, simulation_length, minus20_g, k_s, k_c, k_f, feed_type,
                               use_saturation=use_saturation, water_change_steps=wc_steps, water_change_pct=water_change_pct)
suggested_g   = suggest_reduced_feed(approx_grams, peak_value)

# Save profile if pending
if "_pending_save_name" in st.session_state:
    pname = st.session_state.pop("_pending_save_name")
    st.session_state.profiles[pname] = {
        "tank_type": tank_type, "tank_size_l": tank_size_l, "animal_count": int(animal_count),
        "tank_maturity": tank_maturity, "substrate_type": substrate_type, "plant_density": plant_density,
        "filter_type": filter_type, "flow_rate_lph": flow_rate_lph, "stocking_level": stocking_level,
        "feed_type": feed_type, "temperature": temperature, "water_change_pct": water_change_pct,
        "water_change_days": water_change_days,
    }

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────

st.title("AquaFeed Optimiser 🐟")

# ── Optimise changes notification ──
if st.session_state.last_optimise_changes:
    with st.expander("✨ Here's what the optimiser changed", expanded=True):
        for c in st.session_state.last_optimise_changes:
            st.write(f"— {c}")

# ── ONE-LINE VERDICT ──
if not feed_times:
    st.info("Add a feeding schedule in the sidebar to see your results.")
elif overlap or peak_value > 6:
    st.error(f"⚠️ {summary_text}")
elif peak_value > 4 or not gap_ok:
    st.warning(f"⚡ {summary_text}")
else:
    st.success(f"✅ {summary_text}")

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────

tab_overview, tab_graph, tab_meaning, tab_log, tab_advanced = st.tabs([
    "Overview", "Graph", "What it means", "Feeding log", "Advanced"
])

# ─── TAB 1: OVERVIEW ───
with tab_overview:
    st.subheader("What to do")
    if not feed_times:
        st.info("Set up a feeding schedule in the sidebar.")
    elif overlap or peak_value > 6:
        st.error(f"Reduce feed to about **{suggested_g:.3f}g** and increase spacing to at least **{format_duration(gap_mins)}** between feeds.")
    elif peak_value > 4:
        st.warning(f"Consider reducing to about **{suggested_g:.3f}g** per feed and waiting at least **{format_duration(gap_mins)}** between feeds.")
    else:
        st.success(f"Feed about **{approx_grams:.3f}g**, keep spacing at **{format_duration(gap_mins)} or more**, and maintain the current plan.")

    st.divider()

    # ── Primary metrics ──
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Feeding load (peak)", f"{peak_value:.2f}", help="How high waste concentration spikes after a feed. Safe zone: under 4. Borderline: 4–6. High risk: over 6.")
    m2.metric("Recovery time",       format_duration(recovery_mins), help="How long until the tank returns to a low-waste state after feeding.")
    m3.metric("Recommended gap",     format_duration(gap_mins),      help="Minimum time to wait before feeding again for this setup.")
    m4.metric("Clearing speed",      clearing_label(total_removal),  help="How quickly your tank removes waste overall.")

    # ── Efficiency scores ──
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Timing efficiency", f"{timing_eff}/10", efficiency_word(timing_eff))
    s2.metric("Load efficiency",   f"{load_eff}/10",   efficiency_word(load_eff))
    s3.metric("Waste risk",        risk_word(overall_eff), f"{overall_eff:.1f}/10")
    s4.metric("Overlap risk",      "Low" if not overlap else "Present", "10/10" if not overlap else "3/10")

    st.divider()

    # ── Practical feed guide ──
    st.subheader("Practical feed guide")
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Feed level",         str(feed_level).title())
    p2.metric("Amount per feed",    f"{approx_grams:.3f} g")
    p3.metric("% body weight",      f"{approx_pct_bw:.1f}%")
    p4.metric("Visual equivalent",  pellet_equivalent_text(feed_type, approx_grams))
    st.caption("Estimates based on tank type, stocking level, and estimated livestock biomass. Use as practical guidance, not exact dosing.")

    st.divider()

    # ── Setup at a glance ──
    st.subheader("Setup at a glance")
    a1, a2, a3, a4, a5, a6 = st.columns(6)
    a1.metric("Tank",        tank_type)
    a2.metric("Size",        f"{tank_size_l}L")
    a3.metric("Temp",        f"{temperature}°C")
    a4.metric("Turnover",    f"{turnover:.1f}x/h")
    a5.metric("Filtration",  filtration_strength)
    a6.metric("Plant cover", plant_density)

    st.divider()

    # ── Copy summary ──
    with st.expander("📋 Copy results summary"):
        summary_txt = build_summary_text(
            tank_type, tank_size_l, stocking_level, filter_type, flow_rate_lph,
            feed_type, approx_grams, feed_level, turnover, summary_text,
            gap_mins, peak_value, overall_eff, feed_times, minutes_per_interval,
        )
        st.code(summary_txt, language=None)
        st.caption("Click the copy icon in the top-right of the box above to copy to clipboard.")

# ─── TAB 2: GRAPH ───
with tab_graph:
    time_labels = [
        (f"{int(i*minutes_per_interval//60):02d}:{int(i*minutes_per_interval%60):02d}" if i % max(1, 60//minutes_per_interval) == 0 else "")
        for i in range(simulation_length)
    ]

    max_y = max(8.0, round(peak_value * 1.25, 1))
    fig   = go.Figure()

    # Background zones
    fig.add_hrect(y0=0, y1=4, fillcolor="rgba(34,197,94,0.07)",  line_width=0, layer="below")
    fig.add_hrect(y0=4, y1=6, fillcolor="rgba(234,179,8,0.07)",  line_width=0, layer="below")
    fig.add_hrect(y0=6, y1=max_y, fillcolor="rgba(239,68,68,0.07)", line_width=0, layer="below")

    # Zone labels
    fig.add_annotation(x=1, y=2,    text="Safe zone",    showarrow=False, font=dict(size=11, color="rgba(34,197,94,0.8)"),  xanchor="left")
    fig.add_annotation(x=1, y=5,    text="Borderline",   showarrow=False, font=dict(size=11, color="rgba(234,179,8,0.8)"),  xanchor="left")
    fig.add_annotation(x=1, y=6.5,  text="High risk",    showarrow=False, font=dict(size=11, color="rgba(239,68,68,0.8)"), xanchor="left")

    # Baseline
    if show_baseline:
        fig.add_trace(go.Scatter(
            x=list(range(simulation_length)), y=baseline_values,
            name="Baseline (single feed)", line=dict(color="rgba(107,114,128,0.5)", width=1.5, dash="dash"),
            hovertemplate="Baseline: %{y:.2f}<extra></extra>",
        ))

    # Water change markers
    for wcs in wc_steps:
        fig.add_vline(x=wcs, line_dash="dot", line_color="rgba(59,130,246,0.4)", line_width=1.5,
                      annotation_text="WC", annotation_font_size=9)

    # Main waste curve
    fig.add_trace(go.Scatter(
        x=list(range(simulation_length)), y=values,
        name="Your plan", fill="tozeroy", fillcolor="rgba(9,105,218,0.06)",
        line=dict(color="#0969da", width=2.5),
        hovertemplate="Time: %{x}<br>Feeding load: %{y:.3f}<extra></extra>",
    ))

    # Feed event markers
    for idx, ft in enumerate(feed_times):
        fig.add_vline(x=ft, line_dash="dash", line_color="rgba(0,0,0,0.35)", line_width=1.5,
                      annotation_text=f"Feed {idx+1}" if len(feed_times) <= 3 else "", annotation_font_size=10)

    # Recommended next feed
    if feed_times and gap_needed > 0:
        rec_t = feed_times[0] + gap_needed
        if rec_t < simulation_length:
            fig.add_vline(x=rec_t, line_dash="dot", line_color="rgba(34,197,94,0.8)", line_width=2,
                          annotation_text=f"Min next feed ({format_duration(gap_mins)})", annotation_font_size=10)

    fig.update_layout(
        title=None, margin=dict(l=0, r=0, t=20, b=40),
        hovermode="x unified", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, title="Time interval",
                   tickmode="array", tickvals=[i for i in range(simulation_length) if time_labels[i]],
                   ticktext=[time_labels[i] for i in range(simulation_length) if time_labels[i]]),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)", title="Feeding load", range=[0, max_y]),
        legend=dict(orientation="h", y=-0.15, x=0),
    )
    st.plotly_chart(fig, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total waste load", f"{total_load:.2f}", help="Cumulative waste over the entire simulation period.")
    c2.metric("vs simple plan",   f"{vs_baseline:+.2f}" if show_baseline else "Hidden")
    c3.metric("Feed events",      str(len(feed_times)))

    # ── Scenario compare ──
    st.subheader("Scenario comparison")
    normal_t  = [10] if simulation_length > 10 else [0]
    double_t  = [10, min(25, simulation_length-1)] if simulation_length > 25 else [0, min(5, simulation_length-1)]
    normal_v  = run_simulation(normal_t,  simulation_length, approx_grams, k_s, k_c, k_f, feed_type, use_saturation=use_saturation)
    double_v  = run_simulation(double_t,  simulation_length, approx_grams, k_s, k_c, k_f, feed_type, use_saturation=use_saturation)
    missed_v  = run_simulation([],        simulation_length, approx_grams, k_s, k_c, k_f, feed_type, use_saturation=use_saturation)

    sc1, sc2, sc3 = st.columns(3)
    for col, label, tv, vv in [(sc1,"Normal",normal_t,normal_v),(sc2,"Double feed",double_t,double_v),(sc3,"Missed feed",[],missed_v)]:
        with col:
            st.markdown(f"**{label}**")
            st.write(f"Peak load: {max_value(vv):.2f}")
            st.write(f"Total load: {area_under_curve(vv):.2f}")
            rc = time_to_clear(vv) or 0
            st.write(f"Recovery: {format_duration(rc * minutes_per_interval)}")

# ─── TAB 3: WHAT IT MEANS ───
with tab_meaning:
    left, right = st.columns(2)

    with left:
        st.subheader("What's happening")
        notes = []
        notes.append(f"Each feed creates a peak feeding load of **{peak_value:.2f}** — {'in the safe zone' if peak_value < 4 else 'borderline' if peak_value < 6 else 'above safe levels'}.")
        notes.append(f"The tank returns to a low load after about **{format_duration(recovery_mins)}**.")
        notes.append(f"Tank turnover is **{turnover:.1f}x/h** ({filtration_strength.lower()} filtration).")
        if len(feed_times) >= 2 and avg_gap:
            notes.append(f"Average gap between feeds: **{format_duration(avg_gap * minutes_per_interval)}**.")
            notes.append(f"Recommended minimum gap for this setup: **{format_duration(gap_mins)}**.")
        if tank_type == "Shrimp Tank":
            notes.append("Shrimp graze slowly — consumption is modelled at a lower instantaneous rate, so recovery takes longer than a fish tank.")
        if temperature > 26:
            notes.append(f"At {temperature}°C, biological processes are faster — waste breaks down quicker but can also spike higher.")
        if water_change_pct > 0:
            notes.append(f"A {water_change_pct}% water change every {water_change_days} day(s) is included in the simulation.")
        if plant_density in ["Moderate","High"]:
            notes.append(f"{plant_density} plant density is adding extra nutrient uptake and biofilm — this helps the tank recover faster.")
        for n in notes:
            st.markdown(f"- {n}")

        st.subheader("What you might see in the tank")
        for e in visible_eff:
            st.write(f"- {e}")

    with right:
        st.subheader("What to do")
        actions = []
        if overlap:
            actions.append("Increase the spacing between feeds.")
            better = suggest_better_spacing(feed_times, values, simulation_length)
            if better:
                actions.append(f"Better spacing suggestion: {real_time_text(better, minutes_per_interval)} after start.")
        else:
            actions.append("Tank recovers between feeds — timing is fine.")
        if peak_value > 6:
            actions.append(f"Reduce feed to about **{suggested_g:.3f}g** per feed.")
        elif peak_value > 4:
            actions.append(f"Consider trimming feed slightly — try **{suggested_g:.3f}g** per feed.")
        else:
            actions.append("Feed amount is manageable for this setup.")
        if turnover < 3:
            actions.append("Increase flow rate or upgrade the filter for faster waste clearance.")
        if goal == "Minimise waste":
            actions.append("Prioritise lower load over feeding frequency.")
        elif goal == "Maximise feeding frequency":
            actions.append("Only feed multiple times if the tank fully recovers between events.")
        else:
            actions.append("Aim for a balance between clean recovery and practical frequency.")
        for a in actions:
            st.markdown(f"- {a}")

        st.subheader("Reality check")
        for r in reality_chks:
            st.write(f"- {r}")

        st.subheader("Confidence")
        st.write("This is a practical estimate based on typical tank behaviour — not a direct sensor measurement. Validate what you see in the tank against these predictions and adjust accordingly.")

    # ── Common mistakes ──
    st.divider()
    st.subheader("Common feeding mistakes")
    for title, desc in COMMON_MISTAKES:
        with st.expander(title):
            st.write(desc)

# ─── TAB 4: FEEDING LOG ───
with tab_log:
    st.subheader("Log a feeding event")
    st.caption("Track what you actually fed vs what the tool recommended. Builds over your session.")
    with st.form("log_form"):
        lc1, lc2, lc3 = st.columns(3)
        log_amount  = lc1.number_input("Amount fed (g)", min_value=0.001, max_value=50.0,
                                        value=float(round(approx_grams, 3)), step=0.001, format="%.3f")
        log_food    = lc2.selectbox("Food type", list(FEED_TYPE_INFO.keys()),
                                     index=list(FEED_TYPE_INFO.keys()).index(feed_type))
        log_note    = lc3.text_input("Notes (optional)", placeholder="e.g. shrimp cleared it in 10 min")
        log_outcome = st.radio("How did it go?", ["Food cleared well", "Some leftovers", "Lots of leftovers", "Water clouded"], horizontal=True)
        submitted   = st.form_submit_button("Log this feed", type="primary")
        if submitted:
            st.session_state.feeding_log.append({
                "time":       datetime.now().strftime("%d %b %H:%M"),
                "amount":     log_amount,
                "food":       log_food,
                "outcome":    log_outcome,
                "notes":      log_note,
                "recommended": approx_grams,
            })
            st.success("Feed logged.")

    log = st.session_state.feeding_log
    if log:
        st.divider()
        st.subheader(f"Feeding history ({len(log)} entries this session)")
        for entry in reversed(log):
            delta = entry["amount"] - entry["recommended"]
            delta_text = f"{delta:+.3f}g vs recommended"
            colour = "green" if abs(delta) < 0.01 else ("orange" if abs(delta) < 0.03 else "red")
            with st.container():
                fc1, fc2, fc3, fc4 = st.columns([2,2,2,4])
                fc1.write(f"**{entry['time']}**")
                fc2.write(f"{entry['amount']:.3f}g — {entry['food']}")
                fc3.write(entry["outcome"])
                fc4.write(f":{colour}[{delta_text}]" + (f" · {entry['notes']}" if entry["notes"] else ""))
        if st.button("Clear log"):
            st.session_state.feeding_log = []
            st.rerun()
    else:
        st.info("No feed events logged yet this session. Log a feed above to start tracking.")

# ─── TAB 5: ADVANCED ───
with tab_advanced:
    with st.expander("Full setup summary", expanded=True):
        cols = st.columns(2)
        with cols[0]:
            st.write(f"**Tank type:** {tank_type}")
            st.write(f"**Tank size:** {tank_size_l}L")
            st.write(f"**Temperature:** {temperature}°C")
            st.write(f"**Maturity:** {tank_maturity}")
            st.write(f"**Substrate:** {substrate_type}")
            st.write(f"**Plant density:** {plant_density}")
            st.write(f"**Animal count:** {'Estimated' if animal_count == 0 else animal_count}")
        with cols[1]:
            st.write(f"**Filter:** {filter_type}")
            st.write(f"**Flow rate:** {flow_rate_lph} L/h")
            st.write(f"**Turnover:** {turnover:.1f}x/h")
            st.write(f"**Stocking:** {stocking_level}")
            st.write(f"**Biomass:** ~{biomass_g}g")
            st.write(f"**Water change:** {water_change_pct}% every {water_change_days}d")
            st.write(f"**Model rates:** kₛ={k_s:.3f}, k_c={k_c:.3f}, k_f={k_f:.3f}")

    with st.expander("Sensitivity — what if feed changes by 20%?", expanded=True):
        w1, w2 = st.columns(2)
        with w1:
            st.metric("+20% feed", f"{plus20_g:.3f}g")
            st.write(f"Peak load: {max_value(plus20_vals):.2f}")
            pc = time_to_clear(plus20_vals) or 0
            st.write(f"Recovery: {format_duration(pc * minutes_per_interval)}")
        with w2:
            st.metric("-20% feed", f"{minus20_g:.3f}g")
            st.write(f"Peak load: {max_value(minus20_vals):.2f}")
            mc = time_to_clear(minus20_vals) or 0
            st.write(f"Recovery: {format_duration(mc * minutes_per_interval)}")

    with st.expander("Model details"):
        st.write("This simulation uses a discrete-time decay model with optional consumption saturation.")
        st.latex(r"P(t+1) = P(t) - (k_s + k_{c,\text{eff}} + k_f) \cdot P(t) + F(t)")
        if use_saturation:
            st.latex(r"k_{c,\text{eff}} = k_c \cdot \max(0.12,\; 1 - \text{satiation} \times 0.68)")
            st.write("Satiation increases with each feed event and decays over time — consumption slows when animals are full.")
        if water_change_pct > 0:
            st.latex(r"P_{\text{WC}} = P \cdot (1 - \text{WC\%} / 100)")
            st.write(f"Water changes of {water_change_pct}% are applied every {water_change_days} day(s).")
        if tank_type == "Shrimp Tank":
            st.write("Shrimp-specific model: instantaneous consumption rate reduced by 35% to reflect slow grazing behaviour.")
        st.write(f"Temperature modifier at {temperature}°C: ×{1.0 + (temperature-24)*0.025:.3f} on biological rates.")
