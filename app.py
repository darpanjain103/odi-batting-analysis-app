# Function for Length-Line combined tab with totals (lines on X-axis, lengths on Y-axis)
def make_length_line_table(df):
    temp_df = df[df["isWide"] != True]

    # Group by both length and line
    group = temp_df.groupby(["lengthTypeId", "lineTypeId"]).agg(
        Total_Runs=("runsScored", "sum"),
        Balls_Faced=("runsScored", "count"),
        Outs=("isWicket", "sum")
    ).reset_index()

    # Compute Strike Rate and Average
    group["Strike Rate"] = round((group["Total_Runs"] / group["Balls_Faced"]) * 100, 2)
    group["Average"] = group.apply(lambda x: round(x["Total_Runs"]/x["Outs"],2) if x["Outs"]>0 else "-", axis=1)

    # Combine into "SR / Avg" string
    group["SR / Avg"] = group["Strike Rate"].astype(str) + " / " + group["Average"].astype(str)

    # Pivot table: Length (Y-axis) vs Line (X-axis)
    pivot_table = group.pivot(index="lengthTypeId", columns="lineTypeId", values="SR / Avg").fillna("-")

    # Add total column (for each length)
    total_col = []
    for length in pivot_table.index:
        temp = group[group["lengthTypeId"] == length]
        runs = temp["Total_Runs"].sum()
        balls = temp["Balls_Faced"].sum()
        outs = temp["Outs"].sum()
        sr = round(runs / balls * 100, 2) if balls > 0 else 0
        avg = round(runs / outs, 2) if outs > 0 else "-"
        total_col.append(f"{sr} / {avg}")
    pivot_table["Total"] = total_col

    # Add total row (for each line)
    total_row = []
    for line in pivot_table.columns:
        if line == "Total":
            # Grand total
            runs = group["Total_Runs"].sum()
            balls = group["Balls_Faced"].sum()
            outs = group["Outs"].sum()
            sr = round(runs / balls * 100, 2) if balls > 0 else 0
            avg = round(runs / outs, 2) if outs > 0 else "-"
            total_row.append(f"{sr} / {avg}")
        else:
            temp = group[group["lineTypeId"] == line]
            runs = temp["Total_Runs"].sum()
            balls = temp["Balls_Faced"].sum()
            outs = temp["Outs"].sum()
            sr = round(runs / balls * 100, 2) if balls > 0 else 0
            avg = round(runs / outs, 2) if outs > 0 else "-"
            total_row.append(f"{sr} / {avg}")
    pivot_table.loc["Total"] = total_row

    return pivot_table
