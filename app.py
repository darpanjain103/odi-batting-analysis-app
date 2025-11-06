import streamlit as st
import pandas as pd

# Title
st.title("ODI Batting Analysis App")

# Load the dataset (relative path for Streamlit Cloud)
df = pd.read_csv("Latest ODI Matches Till 2025 Updated.csv")

# Convert ballDateTime to datetime (to extract year easily)
df["ballDateTime"] = pd.to_datetime(df["ballDateTime"], errors="coerce", dayfirst=True)
df["Year"] = df["ballDateTime"].dt.year.astype("Int64")

# Sidebar filters
st.sidebar.header("Filters")
batting_players = st.sidebar.multiselect("Select Batting Player(s)", df["battingPlayer"].dropna().unique())
bowling_types = st.sidebar.multiselect("Select Bowling Type(s)", df["bowlingTypeId"].dropna().unique())
bowlers = st.sidebar.multiselect("Select Bowler(s)", df["bowlerPlayer"].dropna().unique())
over_range = st.sidebar.slider("Over Range", 0, int(df["overNumber"].max()), (0, 10))
years = st.sidebar.multiselect("Select Year(s)", sorted(df["Year"].dropna().unique()))

# Apply filters
filtered_df = df.copy()
if batting_players:
    filtered_df = filtered_df[filtered_df["battingPlayer"].isin(batting_players)]
if bowling_types:
    filtered_df = filtered_df[filtered_df["bowlingTypeId"].isin(bowling_types)]
if bowlers:
    filtered_df = filtered_df[filtered_df["bowlerPlayer"].isin(bowlers)]
if years:
    filtered_df = filtered_df[filtered_df["Year"].isin(years)]
filtered_df = filtered_df[(filtered_df["overNumber"] >= over_range[0]) & (filtered_df["overNumber"] <= over_range[1])]

# Function to group and summarize
def make_group_table(df, group_by_col):
    temp_df = df[df["isWide"] != True]
    
    group = temp_df.groupby(group_by_col)["runsScored"].agg(
        Total_Runs="sum",
        Balls_Faced="count"
    ).reset_index()
    
    group["Strike Rate"] = round((group["Total_Runs"] / group["Balls_Faced"]) * 100, 2)
    group.rename(columns={"Total_Runs": "Total Runs", "Balls_Faced": "Balls Faced"}, inplace=True)
    
    # Sort first, then add total at the end
    group = group.sort_values(by="Strike Rate", ascending=False).reset_index(drop=True)
    
    total_runs = group["Total Runs"].sum()
    total_balls = group["Balls Faced"].sum()
    total_sr = round((total_runs / total_balls) * 100, 2) if total_balls > 0 else 0
    total_row = pd.DataFrame({
        group_by_col: ["Total"],
        "Total Runs": [total_runs],
        "Balls Faced": [total_balls],
        "Strike Rate": [total_sr]
    })
    
    group = pd.concat([group, total_row], ignore_index=True)
    
    return group

# Optional CSS to hide row indices
hide_table_row_index = """
    <style>
    thead tr th:first-child {display:none}
    tbody th {display:none}
    </style>
"""

# Display Tables
st.header("📊 BattingFeetId Summary")
st.dataframe(make_group_table(filtered_df, "battingFeetId"))
st.markdown(hide_table_row_index, unsafe_allow_html=True)

st.header("📊 LengthTypeId Summary")
st.dataframe(make_group_table(filtered_df, "lengthTypeId"))
st.markdown(hide_table_row_index, unsafe_allow_html=True)

st.header("📊 LineTypeId Summary")
st.dataframe(make_group_table(filtered_df, "lineTypeId"))
st.markdown(hide_table_row_index, unsafe_allow_html=True)
