from __future__ import annotations

from datetime import time, datetime, timedelta
from html import escape
from typing import Dict, List, Tuple, Optional

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
import streamlit as st
if not HAS_PLOTLY:
    st.error("Plotly is not installed. Add `plotly` to your requirements.txt and redeploy.")
    st.stop()

st.set_page_config(page_title="AquaFeed Optimiser", page_icon="A", layout="wide")

st.markdown(
    """
    <style>
    #MainMenu, header [data-testid="stToolbar"], header [data-testid="stDecoration"] {
        visibility: hidden;
    }
    .block-container {
        padding-top: 3rem;
        max-width: 1180px;
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(15, 23, 42, 0.98), rgba(17, 24, 39, 0.98));
        border-right: 1px solid rgba(45, 212, 191, 0.18);
    }
    section[data-testid="stSidebar"] h2 {
        font-size: 0.95rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #8fb8bf;
        margin-top: 1.2rem;
    }
    h1, h2, h3 {
        letter-spacing: 0;
    }
    div[data-testid="stMetric"] {
        background: rgba(148, 163, 184, 0.07);
        border: 1px solid rgba(148, 163, 184, 0.16);
        border-radius: 8px;
        padding: 0.85rem 0.95rem;
    }
    div[data-testid="stMetricLabel"] {
        color: #94a3b8;
    }
    div[data-testid="stMetricValue"] {
        font-size: clamp(1.35rem, 2vw, 2rem);
        line-height: 1.15;
        white-space: normal;
        overflow-wrap: anywhere;
    }
    div[data-testid="stMetricDelta"] {
        line-height: 1.25;
    }
    div[data-baseweb="select"],
    div[data-baseweb="select"] *,
    div[data-baseweb="input"],
    div[data-baseweb="input"] *,
    input {
        color: #f8fafc !important;
    }
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] {
        background: rgba(2, 6, 23, 0.68) !important;
        border-color: rgba(148, 163, 184, 0.18) !important;
    }
    button[kind="primary"], button[data-testid="stBaseButton-primary"] {
        background: #0f766e;
        border-color: #0f766e;
        color: #ffffff;
    }
    button[kind="primary"]:hover, button[data-testid="stBaseButton-primary"]:hover {
        background: #0d9488;
        border-color: #0d9488;
        color: #ffffff;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #2dd4bf !important;
        border-bottom: 2px solid #2dd4bf !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] p {
        color: #2dd4bf !important;
    }
    .product-eyebrow {
        color: #8fb8bf;
        display: block;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        line-height: 1.7;
        margin: 0 0 0.3rem;
        min-height: 1.5rem;
        overflow: visible;
        padding-top: 0.35rem;
        text-transform: uppercase;
    }
    .product-title {
        font-size: clamp(2.1rem, 4vw, 3.2rem);
        font-weight: 760;
        margin: 0 0 0.2rem;
        line-height: 1.05;
    }
    .product-subtitle {
        color: #94a3b8;
        font-size: 1.02rem;
        margin: 0 0 1.25rem;
        max-width: 760px;
    }
    .status-card {
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-left-width: 5px;
        border-radius: 8px;
        padding: 1rem 1.1rem;
        margin: 0.75rem 0 1.1rem;
        background: rgba(15, 23, 42, 0.28);
    }
    .status-card.good { border-left-color: #22c55e; }
    .status-card.warn { border-left-color: #f59e0b; }
    .status-card.risk { border-left-color: #ef4444; }
    .status-label {
        color: #94a3b8;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        margin-bottom: 0.25rem;
        text-transform: uppercase;
    }
    .status-text {
        font-size: 1.08rem;
        font-weight: 650;
        margin: 0;
    }
    .summary-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 0.75rem;
        margin: 0.5rem 0 1.25rem;
    }
    .summary-card {
        border: 1px solid rgba(148, 163, 184, 0.16);
        border-radius: 8px;
        padding: 0.9rem 1rem;
        background: rgba(148, 163, 184, 0.06);
    }
    .summary-label {
        color: #94a3b8;
        font-size: 0.78rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
        text-transform: uppercase;
    }
    .summary-value {
        font-size: clamp(1.15rem, 1.8vw, 1.35rem);
        font-weight: 740;
        line-height: 1.2;
        overflow-wrap: anywhere;
    }
    .detail-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.75rem;
        margin: 0.5rem 0 0.75rem;
    }
    .detail-card {
        border: 1px solid rgba(148, 163, 184, 0.16);
        border-radius: 8px;
        padding: 0.9rem 1rem;
        background: rgba(148, 163, 184, 0.06);
        min-height: 6.4rem;
    }
    .detail-label {
        color: #cbd5e1;
        font-size: 0.86rem;
        margin-bottom: 0.45rem;
    }
    .detail-value {
        font-size: clamp(1.05rem, 1.9vw, 1.55rem);
        font-weight: 650;
        line-height: 1.2;
        overflow-wrap: anywhere;
    }
    .note-box {
        border: 1px solid rgba(45, 212, 191, 0.22);
        border-radius: 8px;
        background: rgba(45, 212, 191, 0.06);
        padding: 0.85rem 1rem;
        margin: 0.65rem 0 1rem;
        color: #cbd5e1;
    }
    .note-box strong {
        color: #e2e8f0;
    }
    @media (max-width: 760px) {
        .summary-grid, .detail-grid {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

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
    "Shrimp pellet / stick":          {"spike": 0.92, "linger": 0.95, "description": "Controlled supplemental shrimp food. Easier to remove if uneaten.", "visual": "roughly 1 small pellet/stick fragment",       "grams_per_pellet": None},
    "Bacter / biofilm powder":        {"spike": 1.45, "linger": 1.18, "description": "Useful for shrimplets but disperses quickly. Easy to overdo.",     "visual": "a very light dusting",                       "grams_per_pellet": None},
    "Snowflake / soybean hull":       {"spike": 0.58, "linger": 0.72, "description": "Slow grazing food. Lower spike but can remain in the tank.",       "visual": "one small snowflake piece",                  "grams_per_pellet": None},
    "Mineral food":                   {"spike": 0.75, "linger": 0.85, "description": "Supplemental mineral feed. Usually fed sparingly.",              "visual": "a tiny mineral piece",                       "grams_per_pellet": None},
    "Protein shrimp food":            {"spike": 1.25, "linger": 1.05, "description": "Useful for conditioning, but higher fouling risk.",               "visual": "a small protein pellet fragment",            "grams_per_pellet": None},
    "Blanched vegetable":             {"spike": 0.85, "linger": 1.10, "description": "Grazing food that should be removed if not cleared.",             "visual": "a fingernail-sized piece",                   "grams_per_pellet": None},
}

TANK_PURPOSE_INFO = {
    "General display": "Everyday aquarium feeding with a conservative waste margin.",
    "Shrimp colony / breeder": "Neocaridina/Caridina colony feeding with biofilm, shrimplets, and sale-tank stability in mind.",
    "Fish breeding / grow-out": "Frequent smaller feeds for fry, juveniles, conditioning, or grow-out systems.",
}

SHRIMP_SPECIES_INFO = {
    "Neocaridina": {"surface_per_adult": 22, "description": "Hardy dwarf shrimp. Biofilm and stable grazing surfaces are central to colony success."},
    "Caridina": {"surface_per_adult": 28, "description": "Often more sensitive. Keep recommendations more conservative."},
    "Mixed dwarf shrimp": {"surface_per_adult": 26, "description": "Use conservative estimates when species needs differ."},
}

SHRIMP_COLONY_STAGE_INFO = {
    "Starter colony": {"density_mult": 0.75, "description": "Build stability before pushing feed or stocking."},
    "Growing colony": {"density_mult": 1.0, "description": "Balanced growth and stability."},
    "Breeding colony": {"density_mult": 1.12, "description": "More juveniles and berried females; feed small and consistent."},
    "Sale / holding tank": {"density_mult": 0.82, "description": "Prioritise clean water and stable condition before selling/shipping."},
}

WOOD_TYPE_INFO = {
    "None": {"texture": 0.0, "description": "No wood-based grazing surface."},
    "Cholla": {"texture": 2.4, "description": "Excellent porous shrimp grazing surface."},
    "Spider wood": {"texture": 1.35, "description": "Branching surface with good biofilm development."},
    "Mopani": {"texture": 1.05, "description": "Dense, durable wood with moderate surface texture."},
    "Bogwood / driftwood": {"texture": 1.25, "description": "Variable but usually good once mature."},
    "Manzanita": {"texture": 1.10, "description": "Hard, durable wood with moderate biofilm value."},
    "Unknown aquarium wood": {"texture": 1.0, "description": "Conservative default for aquarium-safe wood."},
}

HARDSCAPE_TYPE_INFO = {
    **WOOD_TYPE_INFO,
    "Lava rock": {"texture": 1.65, "description": "Porous rock with strong grazing surface once mature."},
    "Dragon stone": {"texture": 1.25, "description": "Textured stone with moderate biofilm surface."},
    "Slate / smooth stone": {"texture": 0.55, "description": "Lower texture; useful cover but less grazing surface."},
    "Ceramic cave / media": {"texture": 1.75, "description": "Porous ceramic shelter or media with strong biofilm value."},
}

MOSS_COVER_OPTIONS = {
    "None": 0.0,
    "Small clump (golf-ball size)": 0.10,
    "Moderate (covers 10-25% of hardscape)": 0.22,
    "Dense (covers 25%+ of hardscape)": 0.38,
}
LEAF_LITTER_OPTIONS = {
    "None": 0.0,
    "Few leaves (1-3 small leaves)": 140.0,
    "Moderate (4-8 leaves / light floor cover)": 320.0,
    "Heavy (9+ leaves / obvious leaf bed)": 560.0,
}
VISIBLE_BIOFILM_OPTIONS = {
    "Low (surfaces look clean/new)": 0.82,
    "Moderate (light film, shrimp graze often)": 1.0,
    "Heavy (visible film/algae on hardscape)": 1.18,
}
SNAIL_OPTIONS = {
    "None": 1.0,
    "Few (1-10 visible)": 0.95,
    "Many (10+ visible or breeding)": 0.86,
}

LIVESTOCK_INFO = {
    "Shrimp colony": {"avg_weight": 0.35, "description": "Best for neocaridina/caridina colonies where biofilm and grazing matter."},
    "Small community fish": {"avg_weight": 1.5, "description": "Tetras, rasboras, endlers, small guppies, and similar fish."},
    "Betta / single feature fish": {"avg_weight": 4.0, "description": "Single betta or similar centerpiece fish with light cleanup crew."},
    "Medium fish": {"avg_weight": 6.0, "description": "Gourami, larger livebearers, juvenile cichlids, and similar stock."},
    "Large waste fish": {"avg_weight": 18.0, "description": "Goldfish, large cichlids, plecos, and other heavier-waste fish."},
    "Mixed livestock": {"avg_weight": 3.0, "description": "Use when the tank contains a mix of fish, shrimp, and cleanup crew."},
}

LIFE_STAGE_INFO = {
    "Adult / maintenance": {"feed_mult": 1.0, "description": "Maintenance feeding with a conservative waste margin."},
    "Juvenile / growth": {"feed_mult": 1.25, "description": "Higher growth demand, but water quality margin is tighter."},
    "Breeding / conditioning": {"feed_mult": 1.15, "description": "Slightly higher feeding pressure for conditioning or breeding."},
    "Fry / very young": {"feed_mult": 1.4, "description": "Frequent small feeds. Treat recommendations as rough and observe closely."},
}

FILTER_CONDITION_INFO = {
    "Clean / recently serviced": {"flow_mult": 1.0, "description": "Flow is likely close to normal."},
    "Normal": {"flow_mult": 0.82, "description": "Typical real-world reduction from media and normal use."},
    "Needs maintenance": {"flow_mult": 0.62, "description": "Reduced flow and less margin after feeding."},
}

STOCKING_INFO   = {"Light": "Low stocking: the tank looks understocked and food disappears easily.", "Moderate": "Moderate stocking: active colony/fish group, but open space remains and water stays stable.", "Heavy": "Heavy stocking: crowded, high activity, or frequent visible waste; less margin for error."}
PLANT_INFO      = {"None": "No live plants.", "Low": "Low: 1-3 small plants, a little moss, or less than 10% of the tank footprint covered.", "Moderate": "Moderate: several stems/rosettes/moss patches, about 10-35% coverage.", "High": "High: dense planting, floaters, moss, or 35%+ coverage."}
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

def estimate_biomass_g(
    tank_type: str, tank_size_l: int, stocking_level: str, animal_count: int,
    livestock_profile: str, life_stage: str,
) -> float:
    stage_mult = float(LIFE_STAGE_INFO[life_stage]["feed_mult"])
    if animal_count > 0:
        avg_weight = float(LIVESTOCK_INFO[livestock_profile]["avg_weight"])
        return round(max(animal_count * avg_weight * stage_mult, 2.0), 1)
    density = {
        "Shrimp Tank": {"Light": 0.18, "Moderate": 0.35, "Heavy": 0.60},
        "Fish Tank":   {"Light": 0.50, "Moderate": 1.10, "Heavy": 2.00},
    }.get(tank_type, {"Light": 0.30, "Moderate": 0.70, "Heavy": 1.20})
    profile_mult = clamp(float(LIVESTOCK_INFO[livestock_profile]["avg_weight"]) / 5.0, 0.35, 2.2)
    return round(max(tank_size_l * density[stocking_level] * profile_mult * stage_mult, 2.0), 1)

def feed_amount_to_pct_bw(feed_amount: float) -> float:
    return round(feed_amount * 0.6, 2)

def estimated_feed_grams(feed_amount: float, biomass_g: float) -> float:
    return round(biomass_g * (feed_amount_to_pct_bw(feed_amount) / 100), 3)

def confidence_rating(
    animal_count: int, livestock_profile: str, tank_type: str,
    filter_condition: str, use_custom: bool, schedule_mode: str,
) -> Tuple[str, str]:
    score = 72
    if animal_count <= 0:
        score -= 18
    if livestock_profile in ["Mixed livestock", "Large waste fish"]:
        score -= 8
    if tank_type in ["Mixed Tank", "Custom"]:
        score -= 8
    if filter_condition == "Needs maintenance":
        score -= 10
    if use_custom:
        score -= 5
    if schedule_mode == "Timeline":
        score += 4
    score = int(clamp(score, 20, 90))
    if score >= 75:
        return "High", f"{score}/100"
    if score >= 55:
        return "Medium", f"{score}/100"
    return "Rough", f"{score}/100"

def confidence_guidance(
    animal_count: int, livestock_profile: str, tank_type: str,
    filter_condition: str, use_custom: bool, schedule_mode: str,
) -> Tuple[List[str], List[str]]:
    reasons = []
    actions = []
    if animal_count <= 0:
        reasons.append("Animal count is estimated rather than entered.")
        actions.append("Enter an approximate animal count.")
    if livestock_profile in ["Mixed livestock", "Large waste fish"]:
        reasons.append(f"{livestock_profile.lower()} varies a lot between real tanks.")
        actions.append("Use a more specific livestock profile if one fits.")
    if tank_type in ["Mixed Tank", "Custom"]:
        reasons.append("Mixed/custom tanks are harder to model from broad inputs.")
        actions.append("Use Full mode to fine tune plants, filter, and stocking.")
    if filter_condition == "Needs maintenance":
        reasons.append("Filter condition suggests reduced real-world flow.")
        actions.append("Service the filter or set a more accurate filter condition.")
    if use_custom:
        reasons.append("Manual model-rate overrides are being used.")
        actions.append("Use the automatic model unless you have measured rates.")
    if schedule_mode == "Timeline":
        reasons.append("Timeline scheduling gives more exact feed spacing.")
    else:
        actions.append("Use Full mode with timeline scheduling for exact spacing tests.")
    if not reasons:
        reasons.append("Core tank, livestock, filter, and feeding inputs are specific enough for a practical forecast.")
    if not actions:
        actions.append("Log real feeding outcomes to check whether the forecast matches the tank.")
    return reasons, actions

def setup_risk_flags(
    tank_type: str, tank_size_l: int, animal_count: int, livestock_profile: str,
    filter_condition: str, plant_density: str, tank_maturity: str, feed_type: str,
    water_change_pct: int, feeds_per_day: int,
) -> List[str]:
    flags = []
    if animal_count <= 0:
        flags.append("Animal count is estimated, so gram guidance is less certain.")
    if tank_size_l <= 25:
        flags.append("Small tanks have less buffer after feeding.")
    if "New" in tank_maturity:
        flags.append("New tanks are less stable; feed conservatively.")
    if filter_condition == "Needs maintenance":
        flags.append("Filter maintenance is overdue; recovery may be slower than forecast.")
    if livestock_profile == "Large waste fish":
        flags.append("Large waste-producing fish need a wider safety margin.")
    if plant_density == "High":
        flags.append("Plants improve stability, but they do not instantly remove uneaten food.")
    if feed_type in ["Powder / shrimp food", "Flakes"]:
        flags.append("Fine foods disperse quickly; reduce portions if leftovers or clouding appear.")
    if water_change_pct == 0:
        flags.append("No water change is included in the forecast.")
    if feeds_per_day >= 3:
        flags.append("Frequent feeding should be split into smaller portions and checked with observation.")
    return flags

def pellet_equivalent_text(feed_type: str, grams: float) -> str:
    info = FEED_TYPE_INFO[feed_type]
    if feed_type == "Pellets":
        count = int(max(1, round(grams / info["grams_per_pellet"])))
        if count <= 6:  return f"about {count} small pellets"
        if count <= 20: return f"about {count} small-to-medium pellets"
        return f"about {count} pellets (heavy feed)"
    return str(info["visual"])

def estimate_shrimp_biofilm_surface(
    tank_size_l: int, shrimp_species: str, colony_stage: str,
    wood_type: str, wood_pieces: int, wood_length_cm: float, wood_diameter_cm: float,
    moss_cover: str, plant_density: str, leaf_litter: str, visible_biofilm: str,
    snail_presence: str, hardscape_items: Optional[List[Dict]] = None,
) -> Dict[str, float | str]:
    # This is a husbandry estimate of grazeable surface, not a geometric survey.
    base_surface = tank_size_l * 32.0
    if not hardscape_items:
        hardscape_items = [{
            "type": wood_type, "pieces": wood_pieces,
            "length_cm": wood_length_cm, "diameter_cm": wood_diameter_cm,
        }]

    hardscape_surface = 0.0
    wood_surface = 0.0
    rock_surface = 0.0
    for item in hardscape_items:
        item_type = str(item.get("type", "None"))
        texture = float(HARDSCAPE_TYPE_INFO.get(item_type, HARDSCAPE_TYPE_INFO["Unknown aquarium wood"])["texture"])
        pieces = int(item.get("pieces", 0))
        length_cm = float(item.get("length_cm", 0.0))
        diameter_cm = float(item.get("diameter_cm", 0.0))
        if texture <= 0 or pieces <= 0 or length_cm <= 0:
            continue
        cylinder_area = 3.1416 * max(0.5, diameter_cm) * length_cm
        item_surface = cylinder_area * pieces * texture
        hardscape_surface += item_surface
        if "rock" in item_type.lower() or "stone" in item_type.lower() or "ceramic" in item_type.lower():
            rock_surface += item_surface
        else:
            wood_surface += item_surface

    moss_mult = MOSS_COVER_OPTIONS[moss_cover]
    plant_mult = {"None": 0.0, "Low": 0.08, "Moderate": 0.18, "High": 0.30}[plant_density]
    litter_surface = LEAF_LITTER_OPTIONS[leaf_litter]
    biofilm_mult = VISIBLE_BIOFILM_OPTIONS[visible_biofilm]
    snail_mult = SNAIL_OPTIONS[snail_presence]

    plant_surface = base_surface * (moss_mult + plant_mult)
    estimated_surface = (base_surface + hardscape_surface + plant_surface + litter_surface) * biofilm_mult * snail_mult
    per_adult = float(SHRIMP_SPECIES_INFO[shrimp_species]["surface_per_adult"])
    stage_mult = float(SHRIMP_COLONY_STAGE_INFO[colony_stage]["density_mult"])
    supported = max(5, int((estimated_surface / per_adult) * stage_mult))
    low = max(5, int(supported * 0.7))
    high = max(low + 1, int(supported * 1.25))

    if supported < 40:
        support_word = "Low"
    elif supported < 120:
        support_word = "Moderate"
    else:
        support_word = "High"

    return {
        "surface_cm2": round(estimated_surface),
        "wood_surface_cm2": round(wood_surface),
        "rock_surface_cm2": round(rock_surface),
        "hardscape_surface_cm2": round(hardscape_surface),
        "supported_adults": supported,
        "supported_range": f"{low}-{high}",
        "support_word": support_word,
    }

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
    if overlap and peak > 4: return "Feeds overlap slightly; spacing is worth reviewing."
    if overlap and peak <= 4: return "The graph stays in the safe zone, so the overlap is not a practical concern."
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
    water_change_steps: List[int], water_change_pct: float, minutes_per_interval: int,
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
        changes.append(f"Adjusted feed spacing to a minimum gap of {real_time_text([gn], minutes_per_interval)} between feeds.")
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
    st.markdown('<p class="product-eyebrow">Aquarium feeding planner</p>', unsafe_allow_html=True)
    st.markdown('<h1 class="product-title">AquaFeed Optimiser</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="product-subtitle">Build a practical feeding recommendation from your tank size, livestock, food type, and schedule.</p>',
        unsafe_allow_html=True,
    )

    step  = st.session_state.wizard_step
    wiz   = st.session_state.wizard
    total = 5

    progress = st.progress(step / total)
    st.caption(f"Step {step} of {total}")
    st.divider()

    if step == 1:
        st.markdown("### What kind of tank do you have?")
        cols = st.columns(3)
        options = [("Shrimp tank", "Shrimp Tank"), ("Fish tank", "Fish Tank"), ("Mixed or planted", "Mixed Tank")]
        for col, (label, val) in zip(cols, options):
            with col:
                if st.button(label, use_container_width=True, key=f"wiz_tank_{val}"):
                    wiz["tank_type"] = val
                    st.session_state.wizard_step = 2
                    st.rerun()

    elif step == 2:
        st.markdown("### How big is the tank?")
        size = st.number_input("Exact litres", 10, 500, int(wiz.get("tank_size_l", 60)), 1)
        st.caption("Use the real water volume if you know it. This accepts single-litre values, not just jumps of 10.")
        presets = st.columns(5)
        for col, preset in zip(presets, [20, 30, 45, 60, 100]):
            with col:
                if st.button(f"{preset}L", use_container_width=True, key=f"wiz_size_{preset}"):
                    size = preset
                    wiz["tank_size_l"] = size
                    st.rerun()
        hint = ("Very small — be conservative with feeding." if size <= 20 else
                "Small — less margin for error." if size <= 50 else
                "Medium — reasonable margin." if size <= 100 else
                "Large — more forgiving." if size <= 200 else "Very large — excellent buffering.")
        st.caption(hint)
        wiz["tank_size_l"] = size
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Back"): st.session_state.wizard_step = 1; st.rerun()
        with col2:
            if st.button("Next", type="primary", use_container_width=True):
                st.session_state.wizard_step = 3; st.rerun()

    elif step == 3:
        st.markdown("### How many animals are in it?")
        st.caption("Rough estimate — used to calculate a realistic feed weight.")
        count_label = st.radio("", ["A few (under 15)", "Some (15–40)", "Lots (40+)", "Not sure — skip"], horizontal=True)
        count_map   = {"A few (under 15)": 8, "Some (15–40)": 25, "Lots (40+)": 60, "Not sure — skip": 0}
        wiz["animal_count"] = count_map[count_label]
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Back"): st.session_state.wizard_step = 2; st.rerun()
        with col2:
            if st.button("Next", type="primary", use_container_width=True):
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
            if st.button("Back"): st.session_state.wizard_step = 3; st.rerun()

    elif step == 5:
        st.markdown("### How often do you currently feed?")
        freq_label = st.radio(
            "",
            ["As-needed / irregular", "Twice a week", "Once a week", "Every 2 weeks", "Once a day", "Twice a day"],
            horizontal=True,
        )
        wiz["feed_freq"] = freq_label
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Back"): st.session_state.wizard_step = 4; st.rerun()
        with col2:
            if st.button("See recommendation", type="primary", use_container_width=True):
                st.session_state.onboarding_complete = True
                st.rerun()

    st.divider()
    if st.button("Skip setup and open full planner"):
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
wiz_freq        = wiz.get("feed_freq", "As-needed / irregular" if wiz_tank == "Shrimp Tank" else "Once a day")
wiz_feeds_count = {
    "As-needed / irregular": 1, "Twice a week": 2, "Once a week": 1,
    "Every 2 weeks": 1, "Once a day": 1, "Twice a day": 2,
    "3+ times a day": 3, "Every other day": 1,
}.get(wiz_freq, 1)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

with st.sidebar:
    st.header("Planner controls")

    with st.expander("Presets and saved profiles", expanded=False):
        st.markdown("**Preset tanks**")
        for name in PRESETS:
            if st.button(name, use_container_width=True, key=f"preset_{name}"):
                for k, v in PRESETS[name].items():
                    st.session_state[f"pval_{k}"] = v
                st.rerun()

        st.divider()
        st.markdown("**Saved profiles**")
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

    def pval(key, default):
        return st.session_state.get(f"pval_{key}", default)

    def option_index(options, value, default):
        if value in options:
            return options.index(value)
        for i, option in enumerate(options):
            if str(option).startswith(str(value)):
                return i
        return options.index(default)

    planner_mode = st.radio("Planner mode", ["Simple", "Full"], horizontal=True,
                            help="Simple keeps only the inputs most people need. Full exposes maintenance, simulation, and model controls.")
    tank_purpose = st.selectbox("Tank purpose", list(TANK_PURPOSE_INFO.keys()),
                                index=list(TANK_PURPOSE_INFO.keys()).index(
                                    pval("tank_purpose", "Shrimp colony / breeder" if wiz_tank == "Shrimp Tank" else "General display")
                                ))
    st.caption(TANK_PURPOSE_INFO[tank_purpose])

    st.header("1. Tank basics")
    tank_type_default = "Shrimp Tank" if tank_purpose == "Shrimp colony / breeder" else pval("tank_type", wiz_tank)
    tank_type = st.selectbox("Tank type", ["Shrimp Tank", "Fish Tank", "Mixed Tank", "Custom"],
                             index=["Shrimp Tank","Fish Tank","Mixed Tank","Custom"].index(tank_type_default))
    tank_size_l    = st.slider("Tank size (litres)", 10, 500, pval("tank_size_l", wiz_size), 1)
    animal_count   = st.number_input("Animal count (0 = estimate)", min_value=0, max_value=2000,
                                     value=pval("animal_count", wiz_count), step=1)
    default_livestock = "Shrimp colony" if tank_purpose == "Shrimp colony / breeder" or pval("tank_type", wiz_tank) == "Shrimp Tank" else "Small community fish"
    livestock_profile = st.selectbox("Livestock profile", list(LIVESTOCK_INFO.keys()),
                                     index=list(LIVESTOCK_INFO.keys()).index(pval("livestock_profile", default_livestock)))
    purpose_foods = list(FEED_TYPE_INFO.keys())
    if tank_purpose == "Shrimp colony / breeder":
        purpose_foods = ["Shrimp pellet / stick", "Bacter / biofilm powder", "Snowflake / soybean hull", "Mineral food", "Protein shrimp food", "Blanched vegetable", "Powder / shrimp food", "Slow-release / wafers"]
    elif tank_purpose == "Fish breeding / grow-out":
        purpose_foods = ["Powder / shrimp food", "Frozen / live food", "Flakes", "Pellets"]
    feed_default = pval("feed_type", purpose_foods[0] if tank_purpose == "Shrimp colony / breeder" else wiz_feed)
    if feed_default not in purpose_foods:
        feed_default = purpose_foods[0]
    feed_type      = st.selectbox("Food type", purpose_foods,
                                  index=purpose_foods.index(feed_default))

    shrimp_breeder_enabled = tank_purpose == "Shrimp colony / breeder"
    shrimp_species = "Neocaridina"
    colony_stage = "Growing colony"
    adult_shrimp = int(animal_count)
    juvenile_shrimp = 0
    shrimplet_level = "Some"
    berried_females = "Some present"
    moss_cover = "Moderate (covers 10-25% of hardscape)"
    leaf_litter = "Few leaves (1-3 small leaves)"
    visible_biofilm = "Moderate (light film, shrimp graze often)"
    snail_presence = "Few (1-10 visible)"
    wood_type = "Cholla"
    wood_pieces = 1
    wood_length_cm = 5.0
    wood_diameter_cm = 2.0
    hardscape_items = []

    if shrimp_breeder_enabled:
        st.header("2. Shrimp breeder setup")
        shrimp_species = st.selectbox("Shrimp species", list(SHRIMP_SPECIES_INFO.keys()),
                                      index=list(SHRIMP_SPECIES_INFO.keys()).index(pval("shrimp_species", "Neocaridina")))
        colony_stage = st.selectbox("Colony stage", list(SHRIMP_COLONY_STAGE_INFO.keys()),
                                    index=list(SHRIMP_COLONY_STAGE_INFO.keys()).index(pval("colony_stage", "Growing colony")))
        adult_shrimp = st.number_input("Adult shrimp", min_value=0, max_value=5000,
                                       value=pval("adult_shrimp", max(int(animal_count), 0)), step=1)
        juvenile_shrimp = st.number_input("Juveniles / sub-adults", min_value=0, max_value=5000,
                                          value=pval("juvenile_shrimp", 0), step=1)
        shrimplet_level = st.selectbox("Shrimplets", ["None seen", "Some", "Many"],
                                       index=["None seen", "Some", "Many"].index(pval("shrimplet_level", "Some")))
        berried_females = st.selectbox("Berried females", ["None seen", "Some present", "Many present"],
                                       index=["None seen", "Some present", "Many present"].index(pval("berried_females", "Some present")))

        with st.expander("Tank builder: hardscape and biofilm", expanded=True):
            hardscape_count = st.number_input("Hardscape item types", min_value=0, max_value=6,
                                              value=pval("hardscape_count", 1), step=1,
                                              help="Use one row per wood or rock type. Example: cholla plus lava rock = 2 item types.")
            for i in range(int(hardscape_count)):
                st.markdown(f"**Item {i + 1}**")
                item_default = pval(f"hardscape_{i}_type", pval("wood_type", "Cholla") if i == 0 else "Lava rock")
                if item_default not in HARDSCAPE_TYPE_INFO:
                    item_default = "Unknown aquarium wood"
                item_type = st.selectbox("Type", list(HARDSCAPE_TYPE_INFO.keys()),
                                         index=list(HARDSCAPE_TYPE_INFO.keys()).index(item_default),
                                         key=f"hardscape_type_{i}",
                                         help=HARDSCAPE_TYPE_INFO[item_default]["description"])
                pieces = st.number_input("Pieces", min_value=0, max_value=30,
                                         value=pval(f"hardscape_{i}_pieces", pval("wood_pieces", 1) if i == 0 else 1),
                                         step=1, key=f"hardscape_pieces_{i}")
                length_cm = st.number_input("Average length (cm)", min_value=0.0, max_value=120.0,
                                            value=float(pval(f"hardscape_{i}_length_cm", pval("wood_length_cm", 5.0) if i == 0 else 6.0)),
                                            step=0.5, key=f"hardscape_length_{i}")
                diameter_cm = st.number_input("Average width / diameter (cm)", min_value=0.5, max_value=40.0,
                                              value=float(pval(f"hardscape_{i}_diameter_cm", pval("wood_diameter_cm", 2.0) if i == 0 else 4.0)),
                                              step=0.5, key=f"hardscape_diameter_{i}")
                hardscape_items.append({
                    "type": item_type, "pieces": int(pieces),
                    "length_cm": float(length_cm), "diameter_cm": float(diameter_cm),
                })
                st.caption(HARDSCAPE_TYPE_INFO[item_type]["description"])

            st.markdown("**Biofilm checklist**")
            moss_options = list(MOSS_COVER_OPTIONS.keys())
            litter_options = list(LEAF_LITTER_OPTIONS.keys())
            biofilm_options = list(VISIBLE_BIOFILM_OPTIONS.keys())
            snail_options = list(SNAIL_OPTIONS.keys())
            moss_cover = st.selectbox("Moss / fine plant cover", moss_options,
                                      index=option_index(moss_options, pval("moss_cover", "Moderate (covers 10-25% of hardscape)"), "Moderate (covers 10-25% of hardscape)"))
            leaf_litter = st.selectbox("Leaf litter / botanicals", litter_options,
                                       index=option_index(litter_options, pval("leaf_litter", "Few leaves (1-3 small leaves)"), "Few leaves (1-3 small leaves)"))
            visible_biofilm = st.selectbox("Visible biofilm / algae", biofilm_options,
                                           index=option_index(biofilm_options, pval("visible_biofilm", "Moderate (light film, shrimp graze often)"), "Moderate (light film, shrimp graze often)"))
            snail_presence = st.selectbox("Snails", snail_options,
                                          index=option_index(snail_options, pval("snail_presence", "Few (1-10 visible)"), "Few (1-10 visible)"))
            st.caption("Pick the closest visible condition. These labels are practical estimates, not exact measurements.")

    if planner_mode == "Full":
        life_stage = st.selectbox("Feeding context", list(LIFE_STAGE_INFO.keys()),
                                  index=list(LIFE_STAGE_INFO.keys()).index(pval("life_stage", "Adult / maintenance")))
        stocking_level = st.selectbox("Stocking level", ["Light","Moderate","Heavy"],
                                      index=["Light","Moderate","Heavy"].index(pval("stocking_level","Moderate")))
        with st.expander("Environment and filtration", expanded=False):
            tank_maturity  = st.selectbox("Tank maturity", list(MATURITY_INFO.keys()), index=1)
            substrate_type = st.selectbox("Substrate / biofilm", list(SUBSTRATE_INFO.keys()), index=1)
            plant_density  = st.selectbox("Plant density", list(PLANT_INFO.keys()),
                                          index=list(PLANT_INFO.keys()).index(pval("plant_density", "Low")))
            filter_type    = st.selectbox("Filter type", list(FILTER_TYPE_INFO.keys()),
                                          index=list(FILTER_TYPE_INFO.keys()).index(pval("filter_type", "Internal filter")))
            filter_condition = st.selectbox("Filter condition", list(FILTER_CONDITION_INFO.keys()),
                                            index=list(FILTER_CONDITION_INFO.keys()).index(pval("filter_condition", "Normal")))
            flow_rate_lph  = st.slider("Filter flow rate (L/h)", 50, 3000, pval("flow_rate_lph", 300), 25)
            temperature    = st.slider("Water temperature (°C)", 16, 32, pval("temperature", 24), 1)
            st.caption(STOCKING_INFO[stocking_level])
            st.caption(LIVESTOCK_INFO[livestock_profile]["description"])
            st.caption(LIFE_STAGE_INFO[life_stage]["description"])
            st.caption(FILTER_TYPE_INFO[filter_type]["description"])
            st.caption(FILTER_CONDITION_INFO[filter_condition]["description"])
            st.caption(FEED_TYPE_INFO[feed_type]["description"])
    else:
        life_stage = pval("life_stage", "Adult / maintenance")
        stocking_level = pval("stocking_level", "Moderate")
        tank_maturity = pval("tank_maturity", "Established (1–6 months)")
        substrate_type = pval("substrate_type", "Standard substrate")
        plant_density = pval("plant_density", "Low")
        filter_type = pval("filter_type", "Internal filter")
        filter_condition = pval("filter_condition", "Normal")
        flow_rate_lph = pval("flow_rate_lph", 300)
        temperature = pval("temperature", 24)
        with st.expander("Fine tune tank setup", expanded=False):
            stocking_level = st.selectbox("Stocking level", ["Light","Moderate","Heavy"],
                                          index=["Light","Moderate","Heavy"].index(stocking_level))
            plant_density = st.selectbox("Plant density", list(PLANT_INFO.keys()),
                                         index=list(PLANT_INFO.keys()).index(plant_density))
            filter_condition = st.selectbox("Filter condition", list(FILTER_CONDITION_INFO.keys()),
                                            index=list(FILTER_CONDITION_INFO.keys()).index(filter_condition))

    effective_flow_lph  = int(flow_rate_lph * float(FILTER_CONDITION_INFO[filter_condition]["flow_mult"]))
    turnover            = safe_div(effective_flow_lph, tank_size_l)
    filtration_strength = turnover_judgement(turnover, tank_type)
    st.caption(f"{tank_size_l}L {tank_type.lower()} · {stocking_level.lower()} stocking · {filtration_strength.lower()} filtration")

    if planner_mode == "Full":
        with st.expander("Maintenance and simulation", expanded=False):
            water_change_pct  = st.slider("Water change amount (%)", 0, 50,
                                          pval("water_change_pct", 20), 5)
            water_change_days = st.slider("Every N days", 1, 14,
                                          pval("water_change_days", 7), 1)
            time_scale_label  = st.selectbox("Time interval", list(TIME_SCALE_OPTIONS.keys()), index=1)
            minutes_per_interval = TIME_SCALE_OPTIONS[time_scale_label]
            simulation_length = st.slider("Simulation length (intervals)", 20, 288, 96, 4)
            st.caption(f"Timeline: about {format_duration(simulation_length * minutes_per_interval)} total.")
    else:
        water_change_pct = pval("water_change_pct", 20)
        water_change_days = pval("water_change_days", 7)
        time_scale_label = "15 minutes"
        minutes_per_interval = TIME_SCALE_OPTIONS[time_scale_label]
        simulation_length = 96

    biofilm_result = None
    if shrimp_breeder_enabled:
        biofilm_result = estimate_shrimp_biofilm_surface(
            tank_size_l, shrimp_species, colony_stage, wood_type, int(wood_pieces),
            float(wood_length_cm), float(wood_diameter_cm), moss_cover, plant_density,
            leaf_litter, visible_biofilm, snail_presence, hardscape_items,
        )
        st.caption(
            f"Biofilm support: {biofilm_result['support_word'].lower()} · "
            f"estimated grazing surface {biofilm_result['surface_cm2']:,} cm² · "
            f"biofilm-supported adults {biofilm_result['supported_range']}"
        )

    st.header("3. Feeding plan" if shrimp_breeder_enabled else "2. Feeding plan")
    feed_input_mode = "Simple" if planner_mode == "Simple" else st.radio("Feed amount input", ["Simple", "Advanced"], horizontal=True)
    if shrimp_breeder_enabled:
        shrimplet_estimate = {"None seen": 0, "Some": 25, "Many": 80}[shrimplet_level]
        stage_mult = float(LIFE_STAGE_INFO[life_stage]["feed_mult"])
        biomass_g = round(max((adult_shrimp * 0.35) + (juvenile_shrimp * 0.16) + (shrimplet_estimate * 0.035), 2.0) * stage_mult, 1)
        animal_count_for_confidence = int(adult_shrimp + juvenile_shrimp)
    else:
        biomass_g = estimate_biomass_g(tank_type, tank_size_l, stocking_level, int(animal_count), livestock_profile, life_stage)
        animal_count_for_confidence = int(animal_count)

    if feed_input_mode == "Simple":
        feed_level  = st.select_slider("Feed size", options=list(SIMPLE_FEED_LEVELS.keys()), value="Normal")
        feed_amount = SIMPLE_FEED_LEVELS[feed_level]
    else:
        feed_amount = st.slider("Feed intensity", 0.5, 20.0, 5.0, 0.5,
                                help="Advanced control that scales the estimated grams per feed.")
        feed_level  = practical_feed_label(feed_amount)

    approx_pct_bw  = feed_amount_to_pct_bw(feed_amount)
    approx_grams   = estimated_feed_grams(feed_amount, biomass_g)
    st.caption(f"{feed_level} feed · ~{approx_grams:.3f}g · {pellet_equivalent_text(feed_type, approx_grams)}")

    schedule_mode = "Daily schedule" if planner_mode == "Simple" else st.radio("Schedule mode", ["Daily schedule", "Timeline"], horizontal=True)
    feed_day_offsets: List[int] = []
    feeding_pattern = "Daily"
    if schedule_mode == "Daily schedule":
        one_day_int    = int((24 * 60) / minutes_per_interval)
        daily_pts: List[int] = []
        if shrimp_breeder_enabled:
            pattern_options = ["As-needed / irregular", "Twice a week", "Once a week", "Every 2 weeks", "Daily"]
            saved_pattern = pval("feeding_pattern", wiz_freq if wiz_freq in pattern_options else "As-needed / irregular")
            feeding_pattern = st.selectbox(
                "Feeding pattern", pattern_options,
                index=pattern_options.index(saved_pattern),
                help="Shrimp colonies often do best with light occasional feeding plus constant grazing. Use this instead of forcing a daily schedule.",
            )
            days_to_sim = 14
            simulation_length = max(simulation_length, one_day_int * days_to_sim)
            today = datetime.now().date()
            day_options = list(range(days_to_sim))
            if feeding_pattern == "Twice a week":
                default_days = [0, 3]
            elif feeding_pattern == "Daily":
                default_days = list(range(days_to_sim))
            else:
                default_days = [0]
            if feeding_pattern == "Daily":
                feed_day_offsets = default_days
            else:
                feed_day_offsets = st.multiselect(
                    "Feed days to include",
                    day_options,
                    default=default_days,
                    format_func=lambda d: f"Day {d + 1} - {(today + timedelta(days=d)).strftime('%a %d %b')}",
                    help="Model the days you might feed without pretending shrimp need food every day.",
                )
            fc = st.time_input("Usual feed time", value=time(18, 0), step=900)
            mins_start = fc.hour * 60 + fc.minute
            daily_pts = [int(round(mins_start / minutes_per_interval))]
            st.caption("Irregular shrimp feeding is normal if the tank has mature biofilm and enough grazing surface.")
        else:
            feeds_per_day  = st.slider("Feeds per day", 0, 5, wiz_feeds_count)
            days_to_sim    = 1 if planner_mode == "Simple" else st.slider("Days to simulate", 1, 7, 1)
            simulation_length = max(simulation_length, one_day_int * days_to_sim)
            for i in range(feeds_per_day):
                default_h  = [9, 18, 21, 12, 15][i] if i < 5 else 9
                fc         = st.time_input(f"Feed {i+1}", value=time(default_h, 0), step=900)
                mins_start = fc.hour * 60 + fc.minute
                daily_pts.append(int(round(mins_start / minutes_per_interval)))
            feed_day_offsets = list(range(days_to_sim))
        feed_times: List[int] = sorted(set(
            p + day * one_day_int
            for day in feed_day_offsets
            for p in daily_pts
        ))
        st.caption(f"Calendar window: {days_to_sim} day(s).")
    else:
        days_to_sim = max(1, int((simulation_length * minutes_per_interval) / (24 * 60)))
        n_feeds    = st.slider("Number of feeds", 0, 5, wiz_feeds_count)
        feed_times = []
        for i in range(n_feeds):
            default    = [10, 30, 50, 70, 90][i] if i < 5 else 10 + i * 10
            ft         = st.slider(f"Feed {i+1} (intervals)", 0, simulation_length-1,
                                   min(default, simulation_length-1), 1)
            feed_times.append(ft)
        feed_day_offsets = sorted(set(int((ft * minutes_per_interval) // (24 * 60)) for ft in feed_times))

    if planner_mode == "Full":
        goal = st.selectbox("Optimisation goal", list(GOAL_INFO.keys()))
        st.caption(GOAL_INFO[goal])
    else:
        goal = "Balanced feeding"

    # ── Model options ──
    use_saturation = True
    show_baseline = True
    use_custom = False
    if planner_mode == "Full":
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
                    tank_type, stocking_level, tank_size_l, filter_type, effective_flow_lph,
                    feed_type, tank_maturity, substrate_type, temperature, plant_density
                )
    else:
        k_s, k_c, k_f, _ = map_setup_to_rates(
            tank_type, stocking_level, tank_size_l, filter_type, effective_flow_lph,
            feed_type, tank_maturity, substrate_type, temperature, plant_density
        )

    auto_optimise = st.button("Optimise feeding plan", type="primary")
    if st.button("Start over / change tank"):
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
        feed_type, goal, wc_steps, water_change_pct, minutes_per_interval,
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
spacing_risk  = bool(overlap and peak_value > 4)
recovery_mins = clear_steps * minutes_per_interval
gap_mins      = gap_needed * minutes_per_interval
baseline_load = area_under_curve(baseline_values)
vs_baseline   = total_load - baseline_load
summary_text  = generate_summary(overlap, peak_value, bool(gap_ok), goal)
visible_eff   = visible_tank_effects(tank_type, peak_value, overlap)
reality_chks  = reality_check_list(tank_type)
confidence_label, confidence_score_text = confidence_rating(
    animal_count_for_confidence, livestock_profile, tank_type, filter_condition, use_custom, schedule_mode
)
confidence_reasons, confidence_actions = confidence_guidance(
    animal_count_for_confidence, livestock_profile, tank_type, filter_condition, use_custom, schedule_mode
)
setup_flags = setup_risk_flags(
    tank_type, tank_size_l, animal_count_for_confidence, livestock_profile, filter_condition,
    plant_density, tank_maturity, feed_type, water_change_pct, len(feed_times)
)
visual_equivalent = pellet_equivalent_text(feed_type, approx_grams)
plus20_g      = round(approx_grams * 1.2, 3)
minus20_g     = round(max(0.02, approx_grams * 0.8), 3)
plus20_vals   = run_simulation(feed_times, simulation_length, plus20_g, k_s, k_c, k_f, feed_type,
                               use_saturation=use_saturation, water_change_steps=wc_steps, water_change_pct=water_change_pct)
minus20_vals  = run_simulation(feed_times, simulation_length, minus20_g, k_s, k_c, k_f, feed_type,
                               use_saturation=use_saturation, water_change_steps=wc_steps, water_change_pct=water_change_pct)
suggested_g   = suggest_reduced_feed(approx_grams, peak_value)
suggested_visual = pellet_equivalent_text(feed_type, suggested_g)

# Save profile if pending
if "_pending_save_name" in st.session_state:
    pname = st.session_state.pop("_pending_save_name")
    st.session_state.profiles[pname] = {
        "tank_purpose": tank_purpose, "tank_type": tank_type, "tank_size_l": tank_size_l, "animal_count": int(animal_count),
        "livestock_profile": livestock_profile, "life_stage": life_stage,
        "tank_maturity": tank_maturity, "substrate_type": substrate_type, "plant_density": plant_density,
        "filter_type": filter_type, "flow_rate_lph": flow_rate_lph, "stocking_level": stocking_level,
        "filter_condition": filter_condition, "feed_type": feed_type, "temperature": temperature, "water_change_pct": water_change_pct,
        "water_change_days": water_change_days, "shrimp_species": shrimp_species, "colony_stage": colony_stage,
        "adult_shrimp": int(adult_shrimp), "juvenile_shrimp": int(juvenile_shrimp), "shrimplet_level": shrimplet_level,
        "berried_females": berried_females, "wood_type": wood_type, "wood_pieces": int(wood_pieces),
        "wood_length_cm": float(wood_length_cm), "wood_diameter_cm": float(wood_diameter_cm),
        "moss_cover": moss_cover, "leaf_litter": leaf_litter, "visible_biofilm": visible_biofilm,
        "snail_presence": snail_presence, "feeding_pattern": feeding_pattern,
        "hardscape_count": len(hardscape_items),
    }
    for i, item in enumerate(hardscape_items):
        st.session_state.profiles[pname][f"hardscape_{i}_type"] = item["type"]
        st.session_state.profiles[pname][f"hardscape_{i}_pieces"] = int(item["pieces"])
        st.session_state.profiles[pname][f"hardscape_{i}_length_cm"] = float(item["length_cm"])
        st.session_state.profiles[pname][f"hardscape_{i}_diameter_cm"] = float(item["diameter_cm"])

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────

result_title = "Shrimp colony recommendation" if shrimp_breeder_enabled else ("Grow-out feeding recommendation" if tank_purpose == "Fish breeding / grow-out" else "Feeding recommendation")
st.markdown('<p class="product-eyebrow">AquaFeed Optimiser</p>', unsafe_allow_html=True)
st.markdown(f'<h1 class="product-title">{escape(result_title)}</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="product-subtitle">A practical estimate of feed amount, recovery time, and relative feeding-load risk for the current setup.</p>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="note-box"><strong>Simulation note:</strong> this is a relative feeding-load forecast. It is not a sensor reading and does not predict exact ammonia, nitrite, nitrate, or particle concentration.</div>',
    unsafe_allow_html=True,
)

# ── Optimise changes notification ──
if st.session_state.last_optimise_changes:
    with st.expander("Optimiser changes", expanded=True):
        for c in st.session_state.last_optimise_changes:
            st.write(f"- {c}")

# ── ONE-LINE VERDICT ──
if not feed_times:
    st.info("Add a feeding schedule in the sidebar to see your results.")
elif spacing_risk or peak_value > 6:
    st.markdown(
        f'<div class="status-card risk"><div class="status-label">High attention</div><p class="status-text">{summary_text}</p></div>',
        unsafe_allow_html=True,
    )
elif peak_value > 4 or (not gap_ok and peak_value > 4):
    st.markdown(
        f'<div class="status-card warn"><div class="status-label">Review recommended</div><p class="status-text">{summary_text}</p></div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f'<div class="status-card good"><div class="status-label">Plan status</div><p class="status-text">{summary_text}</p></div>',
        unsafe_allow_html=True,
    )

summary_cards = [
    ("Feed this", escape(visual_equivalent)),
    ("Gram estimate", f"{approx_grams:.3f} g"),
    ("Minimum gap", format_duration(gap_mins)),
    ("Recovery", format_duration(recovery_mins)),
    ("Confidence", confidence_label),
]
if shrimp_breeder_enabled and biofilm_result:
    summary_cards.extend([
        ("Biofilm support", escape(str(biofilm_result["support_word"]))),
        ("Supported adults", escape(str(biofilm_result["supported_range"]))),
    ])

summary_html = '<div class="summary-grid">'
for label, value in summary_cards:
    summary_html += (
        '<div class="summary-card">'
        f'<div class="summary-label">{label}</div>'
        f'<div class="summary-value">{value}</div>'
        '</div>'
    )
summary_html += '</div>'
st.markdown(summary_html, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────

tab_overview, tab_graph, tab_meaning, tab_log, tab_calendar, tab_advanced = st.tabs([
    "Overview", "Graph", "What it means", "Feeding log", "Calendar", "Advanced"
])

# ─── TAB 1: OVERVIEW ───
with tab_overview:
    st.subheader("What to do")
    if not feed_times:
        st.info("Set up a feeding schedule in the sidebar.")
    elif spacing_risk or peak_value > 6:
        st.markdown(
            f'<div class="status-card risk"><div class="status-label">Recommended adjustment</div><p class="status-text">Reduce to {escape(suggested_visual)} (~{suggested_g:.3f}g) and increase spacing to at least {format_duration(gap_mins)} between feeds.</p></div>',
            unsafe_allow_html=True,
        )
    elif peak_value > 4:
        st.markdown(
            f'<div class="status-card warn"><div class="status-label">Recommended adjustment</div><p class="status-text">Consider reducing to {escape(suggested_visual)} (~{suggested_g:.3f}g) per feed and waiting at least {format_duration(gap_mins)} between feeds.</p></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="status-card good"><div class="status-label">Recommended plan</div><p class="status-text">Feed {escape(visual_equivalent)} (~{approx_grams:.3f}g), keep spacing at {format_duration(gap_mins)} or more, and maintain the current plan.</p></div>',
            unsafe_allow_html=True,
        )
    if setup_flags or confidence_reasons:
        with st.expander("Before relying on this result", expanded=(confidence_label == "Rough")):
            st.markdown(f"**Confidence: {confidence_label} ({confidence_score_text})**")
            st.markdown("**Why**")
            for reason in confidence_reasons:
                st.write(f"- {reason}")
            st.markdown("**Improve it**")
            for action in confidence_actions:
                st.write(f"- {action}")
            if setup_flags:
                st.markdown("**Caution flags**")
            for flag in setup_flags:
                st.write(f"- {flag}")
            st.caption("Use tank observation and water tests to confirm the forecast.")

    st.divider()

    if shrimp_breeder_enabled and biofilm_result:
        st.subheader("Shrimp breeder view")
        b1, b2, b3, b4 = st.columns(4)
        b1.metric("Grazing surface", f"{int(biofilm_result['surface_cm2']):,} cm²")
        b2.metric("Biofilm support", str(biofilm_result["support_word"]))
        b3.metric("Adult support range", str(biofilm_result["supported_range"]))
        b4.metric("Wood contribution", f"{int(biofilm_result['wood_surface_cm2']):,} cm²")
        st.caption(
            "The adult support range estimates biofilm-supported grazing capacity, not a hard stocking limit. "
            "Filtration, water changes, minerals, oxygen, genetics, and sale/holding goals still matter."
        )
        if colony_stage == "Sale / holding tank":
            st.warning("Sale/holding tanks should be run cleaner and more conservatively than grow-out tanks.")
        if shrimplet_level != "None seen":
            st.info("Shrimplets present: favour smaller, consistent feeds and keep fine grazing surfaces available.")
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
    s4.metric("Spacing risk",      "Low" if not spacing_risk else "Review", "Safe zone" if overlap and not spacing_risk else ("10/10" if not spacing_risk else "3/10"))

    st.divider()

    # ── Practical feed guide ──
    st.subheader("Practical feed guide")
    st.markdown(
        f"""
        <div class="detail-grid">
            <div class="detail-card">
                <div class="detail-label">Feed level</div>
                <div class="detail-value">{escape(str(feed_level).title())}</div>
            </div>
            <div class="detail-card">
                <div class="detail-label">Amount per feed</div>
                <div class="detail-value">{approx_grams:.3f} g</div>
            </div>
            <div class="detail-card">
                <div class="detail-label">% body weight</div>
                <div class="detail-value">{approx_pct_bw:.1f}%</div>
            </div>
            <div class="detail-card">
                <div class="detail-label">Visual equivalent</div>
                <div class="detail-value">{escape(visual_equivalent)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
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
    with st.expander("Copy results summary"):
        summary_txt = build_summary_text(
            tank_type, tank_size_l, stocking_level, filter_type, flow_rate_lph,
            feed_type, approx_grams, feed_level, turnover, summary_text,
            gap_mins, peak_value, overall_eff, feed_times, minutes_per_interval,
        )
        st.code(summary_txt, language=None)
        st.caption("Click the copy icon in the top-right of the box above to copy to clipboard.")

# ─── TAB 2: GRAPH ───
with tab_graph:
    st.subheader("Feeding load over time")
    st.caption("The shaded bands show relative load risk. Use the shape and recovery time, not the curve as an exact water-chemistry reading.")

    tick_step = max(1, int(round(simulation_length / 8)))
    tick_vals = list(range(0, simulation_length, tick_step))
    if simulation_length - 1 not in tick_vals:
        tick_vals.append(simulation_length - 1)
    tick_text = [format_duration(v * minutes_per_interval) for v in tick_vals]

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
        title=dict(text="Feeding load forecast", x=0, xanchor="left", font=dict(size=17)),
        margin=dict(l=0, r=0, t=44, b=40),
        hovermode="x unified", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=12),
        xaxis=dict(showgrid=False, title="Time",
                   tickmode="array", tickvals=tick_vals, ticktext=tick_text, tickangle=0),
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
            notes.append(f"{plant_density} plant density improves long-term stability and biofilm, but uneaten food still needs to be controlled.")
        notes.append(f"Forecast confidence is **{confidence_label.lower()}** ({confidence_score_text}) based on the inputs provided.")
        for n in notes:
            st.markdown(f"- {n}")

        st.subheader("What you might see in the tank")
        for e in visible_eff:
            st.write(f"- {e}")

    with right:
        st.subheader("What to do")
        actions = []
        if spacing_risk:
            actions.append("Increase the spacing between feeds.")
            better = suggest_better_spacing(feed_times, values, simulation_length)
            if better:
                actions.append(f"Better spacing suggestion: {real_time_text(better, minutes_per_interval)} after start.")
        elif overlap:
            actions.append("Some feeds overlap mathematically, but the curve remains in the safe zone.")
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
with tab_calendar:
    st.subheader("Tank routine calendar")
    st.caption("Use this as a simple planner for feed days, water changes, checks, sale prep, and tank notes.")

    today = datetime.now().date()
    calendar_days = max(7, min(28, int(days_to_sim) if "days_to_sim" in locals() else 14))
    note_key = f"routine_note_{tank_type}_{tank_size_l}"
    saved_notes = st.session_state.setdefault(note_key, {})

    with st.form("calendar_note_form"):
        nc1, nc2 = st.columns([1, 3])
        note_day = nc1.selectbox(
            "Day",
            list(range(calendar_days)),
            format_func=lambda d: f"{(today + timedelta(days=d)).strftime('%a %d %b')}",
        )
        note_text = nc2.text_input("Add note", placeholder="e.g. water test, top-up, cull/sale check, add leaf, observe berried females")
        note_submitted = st.form_submit_button("Add note", type="primary")
        if note_submitted and note_text.strip():
            key = str(note_day)
            saved_notes.setdefault(key, []).append(note_text.strip())
            st.success("Calendar note added.")

    feed_days_set = set(feed_day_offsets)
    wc_days_set = set(range(0, calendar_days, max(1, int(water_change_days)))) if water_change_pct > 0 else set()

    def routine_tasks_for(offset: int) -> List[str]:
        tasks = []
        if offset in feed_days_set:
            tasks.append(f"Feed {visual_equivalent}")
        elif shrimp_breeder_enabled and feeding_pattern == "As-needed / irregular":
            tasks.append("Observe grazing; feed only if needed")
        if offset in wc_days_set and offset != 0:
            tasks.append(f"{water_change_pct}% water change")
        if shrimp_breeder_enabled and offset % 3 == 0:
            tasks.append("Check biofilm, moults, berried females")
        for note in saved_notes.get(str(offset), []):
            tasks.append(f"Note: {note}")
        return tasks or ["No planned task"]

    selected_date = today + timedelta(days=int(note_day))
    st.markdown(f"**Selected day: {selected_date.strftime('%A %d %B')}**")
    for task in routine_tasks_for(int(note_day)):
        st.write(f"- {task}")
    st.divider()

    for week_start in range(0, calendar_days, 7):
        cols = st.columns(7)
        for col, offset in zip(cols, range(week_start, min(week_start + 7, calendar_days))):
            day = today + timedelta(days=offset)
            tasks = routine_tasks_for(offset)
            with col:
                st.markdown(f"**{day.strftime('%a')}**")
                st.caption(day.strftime("%d %b"))
                for task in tasks:
                    st.write(f"- {task}")

    if saved_notes and st.button("Clear calendar notes"):
        st.session_state[note_key] = {}
        st.rerun()

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
