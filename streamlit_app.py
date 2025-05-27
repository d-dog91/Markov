import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests

# --- Page config ---
st.set_page_config(page_title="Guess Explorer", layout="wide")

# --- Load data ---
@st.cache_data(ttl=600)
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
st.sidebar.header("Filter Controls")

min_time = df_full["timestamp"].min().to_pydatetime()
max_time = df_full["timestamp"].max().to_pydatetime()
selected_time = st.sidebar.slider(
    "Only show guesses made before:",
    min_value=min_time,
    max_value=max_time,
    value=max_time,
    format="YYYY-MM-DD HH:mm"
)

df_filtered = df_full[df_full["timestamp"] <= selected_time]
df_filtered = df_filtered[
    (df_filtered["guess"] > 10) &
    (df_filtered["guess"] < 5000) &
    (~df_filtered["guess"].isin({69, 420, 80085}))
]

# --- Frequency counts ---
solo_counts = df_filtered[df_filtered["version"] == "solo"]["guess"].value_counts().sort_index()
social_counts = df_filtered[df_filtered["version"] == "social"]["guess"].value_counts().sort_index()

# --- Plot ---
st.title("Guess Frequency Explorer")

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=solo_counts.index,
    y=solo_counts.values,
    mode='lines',
    name='Solo',
    line=dict(color='blue')
))
fig.add_trace(go.Scatter(
    x=social_counts.index,
    y=social_counts.values,
    mode='lines',
    name='Social',
    line=dict(color='orange')
))

# Label top 10 combined peaks
combined_counts = solo_counts.add(social_counts, fill_value=0)
top_peaks = combined_counts.nlargest(10)
for guess, freq in top_peaks.items():
    y_val = max(solo_counts.get(guess, 0), social_counts.get(guess, 0))
    fig.add_annotation(x=guess, y=y_val + 2, text=str(int(guess)), showarrow=False, font=dict(size=10))

fig.update_layout(
    xaxis_title='Guess',
    yaxis_title='Frequency',
    title='Frequency of Guesses (Solo vs Social)',
    hovermode='x unified',
    height=500,
    margin=dict(t=50, l=50, r=50, b=50)
)
st.plotly_chart(fig, use_container_width=True)

# --- Means ---
mean_solo = round(df_filtered[df_filtered["version"] == "solo"]["guess"].mean())
mean_social = round(df_filtered[df_filtered["version"] == "social"]["guess"].mean())
st.markdown(f"### Mean Solo Guess: {mean_solo}  \nMean Social Guess: {mean_social}")

# --- Guess Checker ---
st.markdown("### Check a Specific Guess")
with st.form("check_guess_form"):
    user_guess = st.number_input("Enter a guess to check:", min_value=0, step=1)
    submitted = st.form_submit_button("Check Guess")
    if submitted:
        solo_match = df_filtered[(df_filtered["version"] == "solo") & (df_filtered["guess"] == user_guess)].shape[0]
        social_match = df_filtered[(df_filtered["version"] == "social") & (df_filtered["guess"] == user_guess)].shape[0]
        st.success(f"Guess {user_guess} appeared {solo_match} times in Solo and {social_match} times in Social.")

# --- Top Guesses ---
with st.expander("📊 Show Top 10 Most Frequent Guesses"):
    top_solo = df_filtered[df_filtered["version"] == "solo"]["guess"].value_counts().nlargest(10).reset_index()
    top_solo.columns = ["Guess", "Solo Frequency"]

    top_social = df_filtered[df_filtered["version"] == "social"]["guess"].value_counts().nlargest(10).reset_index()
    top_social.columns = ["Guess", "Social Frequency"]

    combined_top = pd.concat([top_solo, top_social], axis=1)
    st.dataframe(combined_top)
