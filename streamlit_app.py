import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
from datetime import datetime

# --- Config ---
st.set_page_config(page_title="Guess Tracker", layout="wide")

# --- Load data from Firebase ---
@st.cache_data(ttl=300)
def load_data():
    url = "https://markov-chains-default-rtdb.firebaseio.com/guesses.json"
    response = requests.get(url)
    data = response.json()
    records = []
    for entry in data.values():
        records.append({
            "guess": entry.get("guess"),
            "version": entry.get("version", "unknown"),
            "timestamp": pd.to_datetime(entry.get("timestamp"), unit='ms')
        })
    return pd.DataFrame(records).sort_values("timestamp")

df_full = load_data()

# --- Sidebar controls ---
st.sidebar.header("Filter Options")

# Time slider
min_time = df_full["timestamp"].min()
max_time = df_full["timestamp"].max()
timestamp_bin = df_full["timestamp"].dt.floor("min")
unique_times = sorted(timestamp_bin.unique())

selected_time = st.sidebar.slider(
    "Show data up to:",
    min_value=df_full["timestamp"].min().to_pydatetime(),
    max_value=df_full["timestamp"].max().to_pydatetime(),
    value=df_full["timestamp"].max().to_pydatetime(),
    format="YYYY-MM-DD HH:mm"
)

# --- Filter data ---
df_filtered = df_full[df_full["timestamp"] <= selected_time]
df_filtered = df_filtered[
    (df_filtered["guess"] > 10) &
    (df_filtered["guess"] < 5000) &
    (~df_filtered["guess"].isin({69, 420, 80085}))
]

# --- Calculate frequency ---
guess_range = range(1, 5000)
solo_counts = df_filtered[df_filtered["version"] == "solo"]["guess"].value_counts().reindex(guess_range, fill_value=0)
social_counts = df_filtered[df_filtered["version"] == "social"]["guess"].value_counts().reindex(guess_range, fill_value=0)

freq_df = pd.DataFrame({
    "guess": guess_range,
    "solo": solo_counts.values,
    "social": social_counts.values
})
freq_df["total"] = freq_df["solo"] + freq_df["social"]

# --- Main plot ---
st.title("Guess Frequency Over Time")

fig, ax = plt.subplots(figsize=(14, 6))
ax.plot(freq_df["guess"], freq_df["solo"], label="Solo", linewidth=2)
ax.plot(freq_df["guess"], freq_df["social"], label="Social", linewidth=2, alpha=0.6)

# Label top 10
top_peaks = freq_df.nlargest(10, "total")
for _, row in top_peaks.iterrows():
    guess = row["guess"]
    solo_val = row["solo"]
    social_val = row["social"]
    y = max(solo_val, social_val)
    color = 'blue' if solo_val >= social_val else 'orange'
    ax.text(guess, y + 1, f"{int(guess)}", ha="center", va="bottom", fontsize=9, color=color)

ax.set_xlabel("Guess")
ax.set_ylabel("Frequency")
ax.set_title("Solo vs Social Guess Frequencies")
ax.grid(True)
ax.legend()
ax.set_xticks(range(0, 5001, 250))
st.pyplot(fig)

# --- Mean display ---
mean_solo = round(df_filtered[df_filtered["version"] == "solo"]["guess"].mean())
mean_social = round(df_filtered[df_filtered["version"] == "social"]["guess"].mean())
st.markdown(f"### Mean Solo Guess: {mean_solo}  \nMean Social Guess: {mean_social}")

# --- Guess checker ---
st.markdown("### Check Frequency of a Specific Guess")
guess_check = st.number_input("Enter guess to check:", min_value=0, step=1)
if st.button("Check Guess"):
    solo_freq = df_filtered[(df_filtered["version"] == "solo") & (df_filtered["guess"] == guess_check)].shape[0]
    social_freq = df_filtered[(df_filtered["version"] == "social") & (df_filtered["guess"] == guess_check)].shape[0]
    st.write(f"**Guess {guess_check}** → Solo: {solo_freq}, Social: {social_freq}")

# --- Top guesses toggle ---
if st.toggle("Show Top 10 Guesses"):
    top_solo = (
        df_filtered[df_filtered["version"] == "solo"]["guess"]
        .value_counts().nlargest(10)
        .reset_index().rename(columns={"index": "Guess", "guess": "Solo Frequency"})
    )
    top_social = (
        df_filtered[df_filtered["version"] == "social"]["guess"]
        .value_counts().nlargest(10)
        .reset_index().rename(columns={"index": "Guess", "guess": "Social Frequency"})
    )
    top_combined = pd.concat([top_solo, top_social], axis=1)
    st.markdown("### Top 10 Guesses")
    st.dataframe(top_combined)
