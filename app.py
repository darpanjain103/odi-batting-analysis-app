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

# Function to group and summarize with extra metrics, Outs, and Average
def make_group_table(df, group_by_col):
    temp_df = df[df["isWide"] != True]
    
    group = temp_df.groupby(group_by_col).agg(
        Total_Runs=("runsScored", "sum"),
        Balls_Faced=("runsScored", "count"),
        Fours=("runsScored", lambda x: (x==4).sum()),
        Sixes=("runsScored", lambda x: (x==6).sum()),
        Dot_Balls=("runsScored", lambda x: (x==0).sum()),
        Outs=("isWicket", "sum")  # count of True
    ).reset_index()
    
    # Strike rate
    group["Strike Rate"] = round((group["Total_Runs"] / group["Balls_Faced"]) * 100, 2)
    group["Boundary %"] = round(((group["Fours"] + group["Sixes"]) / group["Balls_Faced"]) * 100, 2)
    group["Dot Ball %"] = round((group["Dot_Balls"] / group["Balls_Faced"]) * 100, 2)
    
    # Average = Runs / Outs (avoid division by zero)
    group["Average"] = group.apply(lambda x: round(x["Total_Runs"]/x["Outs"],2) if x["Outs"]>0 else x["Total_Runs"], axis=1)
    
    # Sort by strike rate
    group = group.sort_values(by="Strike Rate", ascending=False).reset_index(drop=True)
    
    # Add total row
    total_row = pd.DataFrame({
        group_by_col: ["Total"],
        "Total_Runs": [group["Total_Runs"].sum()],
        "Balls_Faced": [group["Balls_Faced"].sum()],
        "Fours": [group["Fours"].sum()],
        "Sixes": [group["Sixes"].sum()],
        "Dot_Balls": [group["Dot_Balls"].sum()],
        "Outs": [group["Outs"].sum()],
        "Strike Rate": [round(group["Total_Runs"].sum() / group["Balls_Faced"].sum() * 100, 2)],
        "Boundary %": [round((group["Fours"].sum() + group["Sixes"].sum()) / group["Balls_Faced"].sum() * 100, 2)],
        "Dot Ball %": [round(group["Dot_Balls"].sum() / group["Balls_Faced"].sum() * 100, 2)],
        "Average": [round(group["Total_Runs"].sum() / group["Outs"].sum(),2) if group["Outs"].sum()>0 else group["Total_Runs"].sum()]
    })
    
    group = pd.concat([group, total_row], ignore_index=True)
    
    # Rename columns for display
    group.rename(columns={
        "Total_Runs": "Runs",
        "Balls_Faced": "Balls",
        "Dot_Balls": "Dot Balls"
    }, inplace=True)
    
    return group

# Display Tables in Tabs with custom names
tabs = st.tabs([
    "Batting Feet",
    "Length Type",
    "Line Type",
    "Ball Type",
    "Bowling End",
    "Bowling Type",
    "Bowler"
])

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = tabs

with tab1:
    st.dataframe(make_group_table(filtered_df, "battingFeetId"))

with tab2:
    st.dataframe(make_group_table(filtered_df, "lengthTypeId"))

with tab3:
    st.dataframe(make_group_table(filtered_df, "lineTypeId"))

with tab4:
    st.dataframe(make_group_table(filtered_df, "bowlingDetailId"))

with tab5:
    st.dataframe(make_group_table(filtered_df, "bowlingFromId"))

with tab6:
    st.dataframe(make_group_table(filtered_df, "bowlingTypeId"))

with tab7:
    st.dataframe(make_group_table(filtered_df, "bowlerPlayer"))
