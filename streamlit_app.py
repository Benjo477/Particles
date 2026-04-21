
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Feeding Optimisation Tool", layout="wide")

# -------------------------
# Helper functions
# -------------------------

def estimate_biomass(tank_type, stocking):
    if tank_type == "Shrimp Tank":
        return {"Light": 5, "Moderate": 15, "Heavy": 30}[stocking]
    else:
        return {"Light": 20, "Moderate": 60, "Heavy": 120}[stocking]

def feed_to_percent(feed_level):
    mapping = {
        "Very Light": 1,
        "Light": 2,
        "Normal": 3,
        "Heavy": 5,
        "Very Heavy": 7
    }
    return mapping[feed_level]

def grams_from_feed(biomass, percent):
    return biomass * (percent / 100)

def pellet_equivalent(grams):
    pellets = int(grams * 30)
    if pellets < 5:
        return "a few pellets"
    elif pellets < 20:
        return "small cluster of pellets"
    else:
        return "heavy feeding amount"

def simulate(feed_times, feed_amount, decay, length):
    y = np.zeros(length)
    for t in feed_times:
        if t < length:
            y[t] += feed_amount
    for i in range(1, length):
        y[i] += y[i-1] * (1 - decay)
    return y

def classify_risk(peak):
    if peak < 3:
        return "LOW", "🟢"
    elif peak < 6:
        return "MODERATE", "🟡"
    else:
        return "HIGH", "🔴"

# -------------------------
# Sidebar
# -------------------------

st.sidebar.title("Tank Setup")

tank_type = st.sidebar.selectbox("Tank Type", ["Shrimp Tank", "Fish Tank"])
tank_size = st.sidebar.slider("Tank Size (L)", 10, 300, 60)

stocking = st.sidebar.selectbox("Stocking Level", ["Light", "Moderate", "Heavy"])
filter_rate = st.sidebar.slider("Filter Flow Rate (L/h)", 50, 1000, 300)

feed_type = st.sidebar.selectbox("Feed Type", ["Pellets", "Flakes", "Powder"])

feed_level = st.sidebar.selectbox(
    "Feed Amount",
    ["Very Light", "Light", "Normal", "Heavy", "Very Heavy"]
)

interval_minutes = st.sidebar.selectbox(
    "Time per interval",
    [5, 10, 15, 30, 60],
    index=2
)

feed_times_input = st.sidebar.text_input("Feeding Times (intervals)", "10")

# -------------------------
# Core calculations
# -------------------------

biomass = estimate_biomass(tank_type, stocking)
percent = feed_to_percent(feed_level)
grams = grams_from_feed(biomass, percent)

feed_times = [int(x) for x in feed_times_input.split(",") if x.strip().isdigit()]

decay = min(filter_rate / tank_size / 10, 0.6)
length = 100

data = simulate(feed_times, grams, decay, length)

peak = max(data)
risk, icon = classify_risk(peak)

recovery_idx = next((i for i, v in enumerate(data) if v < peak * 0.1), None)
recovery_time = recovery_idx * interval_minutes if recovery_idx else None

# -------------------------
# UI
# -------------------------

st.title("Feeding Optimisation Tool")

# Decision Box
st.subheader("✅ What to do next")

if risk == "LOW":
    st.success(f"You’re feeding correctly. Keep feeding ~{round(grams,2)}g per feed.")
elif risk == "MODERATE":
    st.warning(f"Slight overfeeding. Reduce to ~{round(grams*0.8,2)}g.")
else:
    st.error(f"Overfeeding detected. Reduce to ~{round(grams*0.6,2)}g and increase spacing.")

# Metrics
col1, col2, col3, col4 = st.columns(4)

col1.metric("Peak Waste", round(peak,2))
col2.metric("Recovery Time", f"{round(recovery_time/60,1)}h" if recovery_time else "N/A")
col3.metric("Feed per event", f"{round(grams,2)} g")
col4.metric("Waste Risk", f"{icon} {risk}")

# Practical equivalents
st.subheader("Practical Feed Equivalent")
st.write(f"≈ {round(grams,2)} g per feed")
st.write(f"≈ {pellet_equivalent(grams)}")

# What you'd see
st.subheader("What you'll see in your tank")

if risk == "LOW":
    st.write("• Food clears quickly")
    st.write("• No visible leftovers")
    st.write("• Stable water clarity")
elif risk == "MODERATE":
    st.write("• Some food sits briefly")
    st.write("• Slight waste buildup")
else:
    st.write("• Visible uneaten food")
    st.write("• Cloudy water likely")
    st.write("• Waste accumulation risk")

# Graph
st.subheader("Waste Over Time")

fig, ax = plt.subplots()

ax.plot(data, label="Waste Level")

ax.axhspan(0, 3, alpha=0.1, color="green")
ax.axhspan(3, 6, alpha=0.1, color="yellow")
ax.axhspan(6, 10, alpha=0.1, color="red")

for t in feed_times:
    ax.axvline(t, linestyle="--")

ax.set_xlabel(f"Time ({interval_minutes} min intervals)")
ax.set_ylabel("Waste Level")
ax.legend()

st.pyplot(fig)

# Explanation
st.subheader("Explanation")

st.write(f"This simulation assumes each interval = {interval_minutes} minutes.")
st.write(f"Your feeding level corresponds to ~{percent}% of body weight.")
st.write(f"Estimated biomass: {biomass}g")

# Confidence
st.subheader("Confidence")
st.write("Medium confidence — based on typical aquarium behaviour.")
