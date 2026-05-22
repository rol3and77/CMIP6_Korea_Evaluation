from pathlib import Path
import pandas as pd
import calendar

raw_file = Path("data/raw/observations/asos/monthly/asos_monthly_seoul_108_1995_2014.csv")

out_dir = Path("data/processed/observations/asos")
res_dir = Path("results/phase11_observations")
out_dir.mkdir(parents=True, exist_ok=True)
res_dir.mkdir(parents=True, exist_ok=True)

# 1. Read CSV
df = pd.read_csv(raw_file, encoding="utf-8-sig")

print("===== Raw Columns =====")
print(df.columns.tolist())

print("\n===== Raw Head =====")
print(df.head())

# 2. Rename columns
df = df.rename(columns={
    "지점": "station_id",
    "지점명": "station_name",
    "일시": "date_raw",
    "평균기온(°C)": "tas",
    "월합강수량(00~24h만)(mm)": "pr_monthly_mm",
})

# 3. Parse date like Jan.95, Feb.95 ...
month_map = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,
    "May": 5, "Jun": 6, "Jul": 7, "Aug": 8,
    "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}

def parse_kma_month_date(x):
    x = str(x).strip()
    mon_text, yy_text = x.split(".")
    month = month_map[mon_text]
    yy = int(yy_text)

    if yy >= 90:
        year = 1900 + yy
    else:
        year = 2000 + yy

    return pd.Timestamp(year=year, month=month, day=1)

df["time"] = df["date_raw"].apply(parse_kma_month_date)
df["year"] = df["time"].dt.year
df["month"] = df["time"].dt.month

# 4. Convert precipitation monthly total to mm/day
df["days_in_month"] = df.apply(
    lambda row: calendar.monthrange(int(row["year"]), int(row["month"]))[1],
    axis=1
)

df["pr"] = df["pr_monthly_mm"] / df["days_in_month"]

# 5. Keep analysis period
df = df[(df["time"] >= "1995-01-01") & (df["time"] <= "2014-12-01")].copy()
df = df.sort_values("time").reset_index(drop=True)

# 6. Select final columns
processed = df[[
    "station_id",
    "station_name",
    "time",
    "year",
    "month",
    "tas",
    "pr_monthly_mm",
    "days_in_month",
    "pr",
]].copy()

processed["tas_unit"] = "degC"
processed["pr_unit"] = "mm/day"
processed["pr_monthly_unit"] = "mm/month"

# 7. Save processed CSV
processed_file = out_dir / "asos_monthly_seoul_108_1995_2014_processed.csv"
processed.to_csv(processed_file, index=False, encoding="utf-8-sig")

# 8. Quality check summary
summary_rows = []

for var, unit in [
    ("tas", "degC"),
    ("pr", "mm/day"),
    ("pr_monthly_mm", "mm/month"),
]:
    summary_rows.append({
        "dataset": "ASOS_Seoul_108",
        "variable": var,
        "unit": unit,
        "time_size": len(processed),
        "time_first": processed["time"].min(),
        "time_last": processed["time"].max(),
        "missing_count": int(processed[var].isna().sum()),
        "min": round(float(processed[var].min()), 4),
        "mean": round(float(processed[var].mean()), 4),
        "max": round(float(processed[var].max()), 4),
    })

summary = pd.DataFrame(summary_rows)
summary_file = res_dir / "asos_seoul_108_quality_check_summary.csv"
summary.to_csv(summary_file, index=False, encoding="utf-8-sig")

# 9. Monthly climatology
monthly = processed.groupby("month").agg(
    tas=("tas", "mean"),
    pr=("pr", "mean"),
    pr_monthly_mm=("pr_monthly_mm", "mean"),
).reset_index()

monthly["tas"] = monthly["tas"].round(4)
monthly["pr"] = monthly["pr"].round(4)
monthly["pr_monthly_mm"] = monthly["pr_monthly_mm"].round(4)

monthly_file = res_dir / "asos_seoul_108_monthly_climatology.csv"
monthly.to_csv(monthly_file, index=False, encoding="utf-8-sig")

print("\n===== Processed ASOS Seoul Check =====")
print(processed.head())
print(processed.tail())

print("\n===== ASOS Seoul Quality Check Summary =====")
print(summary.to_string(index=False))

print("\n===== ASOS Seoul Monthly Climatology =====")
print(monthly.to_string(index=False))

print("\nSaved processed file:", processed_file)
print("Saved summary file:", summary_file)
print("Saved monthly climatology file:", monthly_file)
