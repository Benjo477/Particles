import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.title("Feeding Optimisation Tool")

feed_amount = st.slider("Feed Amount", 0.0, 10.0, 5.0)
k_total = st.slider("Removal Rate", 0.1, 1.0, 0.5)

time_steps = 50
P = 0
values = []

for t in range(time_steps):
    if t == 10:
        P += feed_amount
    P = P - k_total * P
    P = max(P, 0)
    values.append(P)

fig, ax = plt.subplots()
ax.plot(values)
ax.set_xlabel("Time")
ax.set_ylabel("Particle Concentration")

st.pyplot(fig)

if max(values) > 5:
    st.warning("High concentration → possible overfeeding")
else:
    st.success("Feeding level looks reasonable")
