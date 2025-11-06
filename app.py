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

# Corrected function to count Balls Faced (isWide=True excluded, False or blank included)
def make_group_table(df, group_by_col):
    # Keep only balls where isWide is not True (blank or False counts as legal ball)
    temp_df = df[df["isWide"] != True]
    
    # Group and calculate Total Runs and Balls Faced
    group = temp_df.groupby(group_by_col)["runsScored"].agg(
        Total_Runs="sum",
        Balls_Faced="count"
    ).reset_index()
    
    # Calculate Strike Rate
    group["Strike Rate"] = round((group["Total_Runs"] / group["Balls_Faced"]) * 100, 2)
    
    # Rename columns to match original app
    group.rename(columns={"Total_Runs": "Total Runs", "Balls_Faced": "Balls Faced"}, inplace=True)
    
    return group.sort_values(by="Strike Rate", ascending=False)

# Display Tables
st.header("📊 BattingFeetId Summary")
st.dataframe(make_group_table(filtered_df, "battingFeetId"))

st.header("📊 LengthTypeId Summary")
st.dataframe(make_group_table(filtered_df, "lengthTypeId"))

st.header("📊 LineTypeId Summary")
st.dataframe(make_group_table(filtered_df, "lineTypeId"))
