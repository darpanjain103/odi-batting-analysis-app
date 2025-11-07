[8:03 pm, 7/11/2025] Darpan Jain: import streamlit as st
import pandas as pd

# Title
st.title("ODI Batting Analysis")

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
over_range…
[8:12 pm, 7/11/2025] Darpan Jain: import streamlit as st
import pandas as pd

# Title
st.title("ODI Batting Analysis")

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

# ✅ Add Fetch button
fetch_data = st.sidebar.button("Fetch")

# Apply filters only when Fetch is clicked
if fetch_data:
    filtered_df = df.copy()
    if batting_players:
        filtered_df = filtered_df[filtered_df["battingPlayer"].isin(batting_players)]
    if bowling_types:
        filtered_df = filtered_df[filtered_df["bowlingTypeId"].isin(bowling_types)]
    if bowlers:
        filtered_df = filtered_df[filtered_df["bowlerPlayer"].isin(bowlers)]
    if years:
        filtered_df = filtered_df[filtered_df["Year"].isin(years)]
    filtered_df = filtered_df[
        (filtered_df["overNumber"] >= over_range[0]) & (filtered_df["overNumber"] <= over_range[1])
    ]

    # Function to group and summarize with extra metrics, Outs, Average, Control, and False Shot %
    def make_group_table(df, group_by_col, display_name=None):
        temp_df = df[df["isWide"] != True]
        
        group = temp_df.groupby(group_by_col).agg(
            Total_Runs=("runsScored", "sum"),
            Balls_Faced=("runsScored", "count"),
            Fours=("runsScored", lambda x: (x==4).sum()),
            Sixes=("runsScored", lambda x: (x==6).sum()),
            Dot_Balls=("runsScored", lambda x: (x==0).sum()),
            Outs=("isWicket", "sum"),
            Control=("battingConnectionId", lambda x: x.fillna('None').isin(['Left', 'Middled', 'WellTimed', 'None']).sum())
        ).reset_index()
        
        group["Strike Rate"] = round((group["Total_Runs"] / group["Balls_Faced"]) * 100, 2)
        group["Boundary %"] = round(((group["Fours"] + group["Sixes"]) / group["Balls_Faced"]) * 100, 2)
        group["Dot Ball %"] = round((group["Dot_Balls"] / group["Balls_Faced"]) * 100, 2)
        group["Control %"] = round((group["Control"] / group["Balls_Faced"]) * 100, 2)
        group["False Shot %"] = round(((group["Balls_Faced"] - group["Control"]) / group["Balls_Faced"]) * 100, 2)
        group["Average"] = group.apply(lambda x: round(x["Total_Runs"]/x["Outs"],2) if x["Outs"]>0 else "-", axis=1)
        group = group.sort_values(by="Strike Rate", ascending=False).reset_index(drop=True)
        
        total_row = pd.DataFrame({
            group_by_col: ["Total"],
            "Total_Runs": [group["Total_Runs"].sum()],
            "Balls_Faced": [group["Balls_Faced"].sum()],
            "Fours": [group["Fours"].sum()],
            "Sixes": [group["Sixes"].sum()],
            "Dot_Balls": [group["Dot_Balls"].sum()],
            "Outs": [group["Outs"].sum()],
            "Control": [group["Control"].sum()],
            "Strike Rate": [round(group["Total_Runs"].sum() / group["Balls_Faced"].sum() * 100, 2)],
            "Boundary %": [round((group["Fours"].sum() + group["Sixes"].sum()) / group["Balls_Faced"].sum() * 100, 2)],
            "Dot Ball %": [round(group["Dot_Balls"].sum() / group["Balls_Faced"].sum() * 100, 2)],
            "Control %": [round(group["Control"].sum() / group["Balls_Faced"].sum() * 100, 2)],
            "False Shot %": [round(((group["Balls_Faced"].sum() - group["Control"].sum()) / group["Balls_Faced"].sum()) * 100, 2)],
            "Average": ["-" if group["Outs"].sum()==0 else round(group["Total_Runs"].sum() / group["Outs"].sum(),2)]
        })
        
        group = pd.concat([group, total_row], ignore_index=True)
        group.rename(columns={"Total_Runs": "Runs", "Balls_Faced": "Balls", "Dot_Balls": "Dot Balls"}, inplace=True)
        metric_order = ["Runs", "Balls", "Outs", "Average", "Strike Rate", "Fours", "Sixes", "Dot Balls", "Dot Ball %", "Boundary %", "Control", "Control %", "False Shot %"]
        group = group[[group_by_col] + metric_order]
        
        if display_name:
            group.rename(columns={group_by_col: display_name}, inplace=True)
        
        return group

    def make_length_line_table(df):
        temp_df = df[df["isWide"] != True]
        group = temp_df.groupby(["lengthTypeId", "lineTypeId"]).agg(
            Total_Runs=("runsScored", "sum"),
            Balls_Faced=("runsScored", "count"),
            Outs=("isWicket", "sum")
        ).reset_index()

        group["Strike Rate"] = round((group["Total_Runs"] / group["Balls_Faced"]) * 100, 2)
        group["Average"] = group.apply(lambda x: round(x["Total_Runs"]/x["Outs"],2) if x["Outs"]>0 else "-", axis=1)
        group["SR / Avg"] = group["Strike Rate"].astype(str) + " / " + group["Average"].astype(str)
        pivot_table = group.pivot(index="lengthTypeId", columns="lineTypeId", values="SR / Avg").fillna("-")

        total_col = []
        for length in pivot_table.index:
            temp = group[group["lengthTypeId"] == length]
            runs, balls, outs = temp["Total_Runs"].sum(), temp["Balls_Faced"].sum(), temp["Outs"].sum()
            sr = round(runs / balls * 100, 2) if balls > 0 else 0
            avg = round(runs / outs, 2) if outs > 0 else "-"
            total_col.append(f"{sr} / {avg}")
        pivot_table["Total"] = total_col

        total_row = []
        for line in pivot_table.columns:
            temp = group[group["lineTypeId"] == line] if line != "Total" else group
            runs, balls, outs = temp["Total_Runs"].sum(), temp["Balls_Faced"].sum(), temp["Outs"].sum()
            sr = round(runs / balls * 100, 2) if balls > 0 else 0
            avg = round(runs / outs, 2) if outs > 0 else "-"
            total_row.append(f"{sr} / {avg}")
        pivot_table.loc["Total"] = total_row
        pivot_table.index.name = "Length"

        return pivot_table

    # ✅ FIXED: auto height adjustment per tab
    def show_table(df, key):
        df_display = df.copy()
        if df_display.shape[1] > 0:
            first_col = df_display.columns[0]
            try:
                df_display = df_display.set_index(first_col)
            except Exception:
                df_display[first_col] = df_display[first_col].astype(str)
                df_display = df_display.set_index(first_col)

        row_height = 33
        header_height = 38
        num_rows = len(df_display)
        dynamic_height = int(header_height + (num_rows * row_height))

        st.dataframe(df_display, use_container_width=True, height=dynamic_height)

    tabs = st.tabs([
        "Foot Type", "Length", "Line", "Ball Type", "Bowling End", "Bowling Type",
        "Bowler", "Shot", "Bowling Hand", "Shot Area", "Length-Line"
    ])

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = tabs

    with tab1:
        show_table(make_group_table(filtered_df, "battingFeetId", display_name="Foot Type"), "foot_type")

    with tab2:
        show_table(make_group_table(filtered_df, "lengthTypeId", display_name="Length"), "length")

    with tab3:
        show_table(make_group_table(filtered_df, "lineTypeId", display_name="Line"), "line")

    with tab4:
        show_table(make_group_table(filtered_df, "bowlingDetailId", display_name="Ball Type"), "ball_type")

    with tab5:
        show_table(make_group_table(filtered_df, "bowlingFromId", display_name="Bowling End"), "bowling_end")

    with tab6:
        show_table(make_group_table(filtered_df, "bowlingTypeId", display_name="Bowling Type"), "bowling_type")

    with tab7:
        show_table(make_group_table(filtered_df, "bowlerPlayer", display_name="Bowler"), "bowler")

    with tab8:
        show_table(make_group_table(filtered_df, "battingShotTypeId", display_name="Shot"), "shot")

    with tab9:
        show_table(make_group_table(filtered_df, "bowlingHandId", display_name="Bowling Hand"), "bowling_hand")

    with tab10:
        show_table(make_group_table(filtered_df, "fieldingPosition", display_name="Shot Area"), "shot_area")

    with tab11:
        st.markdown("*[Strike Rate/Average]:*")
        show_table(make_length_line_table(filtered_df), "length_line")

else:
    st.info("👈 Adjust filters and click *Fetch* to view results.")
