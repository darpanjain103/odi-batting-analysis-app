import streamlit as st
import pandas as pd

# Title
st.title("ODI Batting & Bowling Analysis")

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
    # ---------- Batting filtered dataset ----------
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

    # ---------- Bowling filtered dataset ----------
    bowling_filtered_df = df.copy()
    if years:
        bowling_filtered_df = bowling_filtered_df[bowling_filtered_df["Year"].isin(years)]
    bowling_filtered_df = bowling_filtered_df[
        (bowling_filtered_df["overNumber"] >= over_range[0]) & (bowling_filtered_df["overNumber"] <= over_range[1])
    ]
    if bowlers:
        bowling_filtered_df = bowling_filtered_df[bowling_filtered_df["bowlerPlayer"].isin(bowlers)]

    # ---------- Batting helper ----------
    def make_group_table(df, group_by_col, display_name=None):
        temp_df = df[(df["isWide"] != True) & (df["isNoBall"] != True)]

        group = temp_df.groupby(group_by_col).agg(
            Total_Runs=("runsScored", "sum"),
            Balls_Faced=("runsScored", "count"),
            Fours=("runsScored", lambda x: (x == 4).sum()),
            Sixes=("runsScored", lambda x: (x == 6).sum()),
            Dot_Balls=("runsScored", lambda x: (x == 0).sum()),
            Outs=("isWicket", "sum"),
            Control=("battingConnectionId", lambda x: x.fillna('None').isin(['Left', 'Middled', 'WellTimed', 'None']).sum())
        ).reset_index()

        group["Strike Rate"] = round((group["Total_Runs"] / group["Balls_Faced"]) * 100, 2)
        group["Boundary %"] = round(((group["Fours"] + group["Sixes"]) / group["Balls_Faced"]) * 100, 2)
        group["Dot Ball %"] = round((group["Dot_Balls"] / group["Balls_Faced"]) * 100, 2)
        group["Control %"] = round((group["Control"] / group["Balls_Faced"]) * 100, 2)
        group["False Shot"] = group["Balls_Faced"] - group["Control"]
        group["False Shot %"] = round((group["False Shot"] / group["Balls_Faced"]) * 100, 2)
        group["Average"] = group.apply(lambda x: round(x["Total_Runs"]/x["Outs"], 2) if x["Outs"] > 0 else "-", axis=1)
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
            "False Shot": [group["False Shot"].sum()],
            "False Shot %": [round((group["False Shot"].sum() / group["Balls_Faced"].sum()) * 100, 2)],
            "Average": ["-" if group["Outs"].sum() == 0 else round(group["Total_Runs"].sum() / group["Outs"].sum(), 2)]
        })

        group = pd.concat([group, total_row], ignore_index=True)
        group.rename(columns={"Total_Runs": "Runs", "Balls_Faced": "Balls", "Dot_Balls": "Dot Balls"}, inplace=True)
        metric_order = [
            "Runs", "Balls", "Outs", "Average", "Strike Rate", "Fours", "Sixes", "Dot Balls",
            "Dot Ball %", "Boundary %", "Control", "Control %", "False Shot", "False Shot %"
        ]
        group = group[[group_by_col] + metric_order]

        if display_name:
            group.rename(columns={group_by_col: display_name}, inplace=True)

        return group

    # ---------- Bowling helper ----------
    def make_bowling_group_table_with_total(df, group_by_col, display_name=None):
        if df.empty:
            return pd.DataFrame(columns=[display_name or group_by_col, "Runs", "Extras", "Balls", "Wickets", "Dot", "Dot %", "Fours", "Sixes", "Boundaries", "Boundary %", "False Shot", "False Shot %", "Average", "Economy"])
        temp = df.copy()
        temp_non_wide = temp[(temp["isWide"] != True) & (temp["isNoBall"] != True)]
        def count_valid_wickets(x):
            return ((x["isWicket"] == True) & (~x["dismissalTypeId"].isin(["RunOut", "RunOutSub"]))).sum()
        group = temp.groupby(group_by_col).apply(count_valid_wickets).reset_index(name="Wickets")
        control_group = temp_non_wide.groupby(group_by_col).agg(
            Control=("battingConnectionId", lambda x: x.fillna('None').isin(['Left', 'Middled', 'WellTimed', 'None']).sum())
        ).reset_index()
        if group_by_col == "battingPlayer":
            runs_agg = temp.groupby(group_by_col).agg(
                Runs=("runsScored", "sum"),
                Extras=("extras", "sum"),
                Dot=("runsConceded", lambda x: (x == 0).sum()),
                Fours=("runsScored", lambda x: (x == 4).sum()),
                Sixes=("runsScored", lambda x: (x == 6).sum())
            ).reset_index()
        else:
            runs_agg = temp.groupby(group_by_col).agg(
                Runs=("runsConceded", "sum"),
                Extras=("extras", "sum"),
                Dot=("runsConceded", lambda x: (x == 0).sum()),
                Fours=("runsConceded", lambda x: (x == 4).sum()),
                Sixes=("runsConceded", lambda x: (x == 6).sum())
            ).reset_index()
        group = pd.merge(group, runs_agg, on=group_by_col, how="left")
        balls_group = temp_non_wide.groupby(group_by_col).agg(Balls=("ballNumber", "count")).reset_index()
        group = pd.merge(group, balls_group, on=group_by_col, how="left")
        group = pd.merge(group, control_group, on=group_by_col, how="left")
        group["Boundaries"] = group["Fours"] + group["Sixes"]
        group["Boundary %"] = round((group["Boundaries"] / group["Balls"]) * 100, 2)
        group["False Shot"] = group["Balls"] - group["Control"]
        group["False Shot %"] = round((group["False Shot"] / group["Balls"]) * 100, 2)
        group["Dot %"] = round((group["Dot"] / group["Balls"]) * 100, 2)
        group["Average"] = group.apply(lambda x: round(x["Runs"]/x["Wickets"], 2) if x["Wickets"] > 0 else "-", axis=1)
        group["Economy"] = group.apply(lambda x: round((x["Runs"] / x["Balls"]) * 6, 2) if x["Balls"] > 0 else "-", axis=1)
        total_row = pd.DataFrame({
            group_by_col: ["Total"],
            "Runs": [group["Runs"].sum()],
            "Extras": [group["Extras"].sum()],
            "Balls": [group["Balls"].sum()],
            "Wickets": [group["Wickets"].sum()],
            "Dot": [group["Dot"].sum()],
            "Dot %": [round((group["Dot"].sum() / group["Balls"].sum()) * 100, 2) if group["Balls"].sum() > 0 else 0],
            "Fours": [group["Fours"].sum()],
            "Sixes": [group["Sixes"].sum()],
            "Boundaries": [group["Boundaries"].sum()],
            "Boundary %": [round((group["Boundaries"].sum() / group["Balls"].sum()) * 100, 2) if group["Balls"].sum() > 0 else 0],
            "False Shot": [group["False Shot"].sum()],
            "False Shot %": [round((group["False Shot"].sum() / group["Balls"].sum()) * 100, 2)],
            "Average": ["-" if group["Wickets"].sum() == 0 else round(group["Runs"].sum() / group["Wickets"].sum(), 2)],
            "Economy": [round((group["Runs"].sum() / group["Balls"].sum()) * 6, 2) if group["Balls"].sum() > 0 else "-"]
        })
        group = pd.concat([group, total_row], ignore_index=True)
        group = group[[group_by_col, "Runs", "Balls", "Wickets", "Average", "Economy", "Dot %", "Boundary %", "False Shot %"]]
        if display_name:
            group.rename(columns={group_by_col: display_name}, inplace=True)
        return group

    # ---------- Display helper ----------
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

    # ---------- Batting Section ----------
    st.subheader("🏏 ODI Batting Analysis")
    if batting_players:
        tabs = st.tabs([
            "Foot Type", "Length", "Line", "Ball Type", "Bowling End", "Bowling Type",
            "Bowler", "Shot", "Bowling Hand", "Shot Area"
        ])
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = tabs

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
            st.markdown("[Strike Rate/Average]:")
            pass
    else:
        st.info("Select batting player(s) in the Filters to view batting analysis.")

    # ---------- Bowling Section ----------
    # Show bowling only if bowling is selected AND batting_players is NOT selected
    if bowlers and not batting_players:
        st.markdown("---")
        st.subheader("🎯 ODI Bowling Analysis")
        bowling_tabs = st.tabs([
            "Foot Type", "Bowling End", "Ball Type", "Shot", "Length", "Line", "Batter"
        ])
        btab1, btab2, btab3, btab4, btab5, btab6, btab7 = bowling_tabs
        with btab1:
            show_table(
                make_bowling_group_table_with_total(bowling_filtered_df, "battingFeetId", display_name="Foot Type"),
                "b_foot"
            )
        with btab2:
            show_table(
                make_bowling_group_table_with_total(bowling_filtered_df, "bowlingFromId", display_name="Bowling End"),
                "b_end"
            )
        with btab3:
            show_table(
                make_bowling_group_table_with_total(bowling_filtered_df, "bowlingDetailId", display_name="Ball Type"),
                "b_ball_type"
            )
        with btab4:
            show_table(
                make_bowling_group_table_with_total(bowling_filtered_df, "battingShotTypeId", display_name="Shot"),
                "b_shot"
            )
        with btab5:
            show_table(
                make_bowling_group_table_with_total(bowling_filtered_df, "lengthTypeId", display_name="Length"),
                "b_length"
            )
        with btab6:
            show_table(
                make_bowling_group_table_with_total(bowling_filtered_df, "lineTypeId", display_name="Line"),
                "b_line"
            )
        with btab7:
            show_table(
                make_bowling_group_table_with_total(bowling_filtered_df, "battingPlayer", display_name="Batter"),
                "b_batter"
            )
    elif not batting_players:
        st.info("Select bowler(s) in the Filters to view bowling analysis for that bowler(s).")

else:
    st.info("👈 Adjust filters and click Fetch to view results.")
