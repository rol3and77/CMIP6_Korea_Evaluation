from pathlib import Path
import pandas as pd
import calendar

raw_file = Path("data/raw/observations/asos/monthly/asos_monthly_7stations_1995_2014.csv")

out_dir = Path("data/processed/observations/asos")
res_dir = Path("results/phase11_observations")

out_dir.mkdir(parents=True, exist_ok=True)
res_dir.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------
# 1. Read ASOS CSV with automatic encoding detection
# ------------------------------------------------------------

encodings = ["utf-8-sig", "utf-8", "cp949", "euc-kr"]

df = None
used_encoding = None

for enc in encodings:
    try:
        df = pd.read_csv(raw_file, encoding=enc)
        used_encoding = enc
        break
    except UnicodeDecodeError:
        continue

if df is None:
    raise UnicodeDecodeError("Could not read CSV with utf-8-sig, utf-8, cp949, or euc-kr.")

print("===== CSV Encoding Used =====")
print(used_encoding)

print("\n===== Raw Columns =====")
print(df.columns.tolist())

print("\n===== Raw Head =====")
print(df.head())

# ------------------------------------------------------------
# 2. Rename columns
# ------------------------------------------------------------

df = df.rename(columns={
    "지점": "station_id",
    "지점명": "station_name",
    "일시": "date_raw",
    "평균기온(°C)": "tas",
    "월합강수량(00~24h만)(mm)": "pr_monthly_mm",
})

required_cols = ["station_id", "station_name", "date_raw", "tas", "pr_monthly_mm"]
missing_cols = [c for c in required_cols if c not in df.columns]

if missing_cols:
    print("\nCurrent columns:")
    print(df.columns.tolist())
    raise ValueError(f"Missing required columns after rename: {missing_cols}")

# ------------------------------------------------------------
# 3. Parse date
#    Expected example: Jan.95, Feb.95, ...
# ------------------------------------------------------------

month_map = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}

def parse_kma_month_date(x):
    x = str(x).strip()

    # Case 1: Jan.95
    if "." in x and x[:3] in month_map:
        mon_text, yy_text = x.split(".")
        month = month_map[mon_text]
        yy = int(yy_text)

        if yy >= 90:
            year = 1900 + yy
        else:
            year = 2000 + yy

        return pd.Timestamp(year=year, month=month, day=1)

    # Case 2: 1995-01 or 1995.01
    x2 = x.replace(".", "-")
    return pd.to_datetime(x2 + "-01" if len(x2) == 7 else x2)

df["time"] = df["date_raw"].apply(parse_kma_month_date)
df["year"] = df["time"].dt.year
df["month"] = df["time"].dt.month

# ------------------------------------------------------------
# 4. Convert precipitation
#    KMA monthly precipitation: mm/month
#    Project unit: mm/day
# ------------------------------------------------------------

df["days_in_month"] = df.apply(
    lambda row: calendar.monthrange(int(row["year"]), int(row["month"]))[1],
    axis=1
)

df["pr"] = df["pr_monthly_mm"] / df["days_in_month"]

# ------------------------------------------------------------
# 5. Keep target period
# ------------------------------------------------------------

df = df[(df["time"] >= "1995-01-01") & (df["time"] <= "2014-12-01")].copy()
df = df.sort_values(["station_id", "time"]).reset_index(drop=True)

# ------------------------------------------------------------
# 6. Final processed station-level table
# ------------------------------------------------------------

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

processed_file = out_dir / "asos_monthly_7stations_1995_2014_processed.csv"
processed.to_csv(processed_file, index=False, encoding="utf-8-sig")

# ------------------------------------------------------------
# 7. Station-level quality check
# ------------------------------------------------------------

station_summary_rows = []

for station_id, g in processed.groupby("station_id"):
    station_name = g["station_name"].iloc[0]

    for var, unit in [
        ("tas", "degC"),
        ("pr", "mm/day"),
        ("pr_monthly_mm", "mm/month"),
    ]:
        station_summary_rows.append({
            "station_id": station_id,
            "station_name": station_name,
            "variable": var,
            "unit": unit,
            "time_size": len(g),
            "time_first": g["time"].min(),
            "time_last": g["time"].max(),
            "missing_count": int(g[var].isna().sum()),
            "min": round(float(g[var].min()), 4),
            "mean": round(float(g[var].mean()), 4),
            "max": round(float(g[var].max()), 4),
        })

station_summary = pd.DataFrame(station_summary_rows)
station_summary_file = res_dir / "asos_7stations_quality_check_summary.csv"
station_summary.to_csv(station_summary_file, index=False, encoding="utf-8-sig")

# ------------------------------------------------------------
# 8. 7-station mean monthly time series
# ------------------------------------------------------------

multi_station_mean = processed.groupby("time").agg(
    year=("year", "first"),
    month=("month", "first"),
    station_count=("station_id", "nunique"),
    tas=("tas", "mean"),
    pr=("pr", "mean"),
    pr_monthly_mm=("pr_monthly_mm", "mean"),
).reset_index()

multi_station_file = out_dir / "asos_7stations_mean_monthly_1995_2014_processed.csv"
multi_station_mean.to_csv(multi_station_file, index=False, encoding="utf-8-sig")

# ------------------------------------------------------------
# 9. 7-station mean quality check
# ------------------------------------------------------------

overall_rows = []

for var, unit in [
    ("tas", "degC"),
    ("pr", "mm/day"),
    ("pr_monthly_mm", "mm/month"),
]:
    overall_rows.append({
        "dataset": "ASOS_7stations_mean",
        "variable": var,
        "unit": unit,
        "time_size": len(multi_station_mean),
        "time_first": multi_station_mean["time"].min(),
        "time_last": multi_station_mean["time"].max(),
        "missing_count": int(multi_station_mean[var].isna().sum()),
        "min": round(float(multi_station_mean[var].min()), 4),
        "mean": round(float(multi_station_mean[var].mean()), 4),
        "max": round(float(multi_station_mean[var].max()), 4),
    })

overall_summary = pd.DataFrame(overall_rows)
overall_summary_file = res_dir / "asos_7stations_mean_quality_check_summary.csv"
overall_summary.to_csv(overall_summary_file, index=False, encoding="utf-8-sig")

# ------------------------------------------------------------
# 10. 7-station mean monthly climatology
# ------------------------------------------------------------

monthly_clim = multi_station_mean.groupby("month").agg(
    tas=("tas", "mean"),
    pr=("pr", "mean"),
    pr_monthly_mm=("pr_monthly_mm", "mean"),
).reset_index()

monthly_clim["tas"] = monthly_clim["tas"].round(4)
monthly_clim["pr"] = monthly_clim["pr"].round(4)
monthly_clim["pr_monthly_mm"] = monthly_clim["pr_monthly_mm"].round(4)

monthly_clim_file = res_dir / "asos_7stations_mean_monthly_climatology.csv"
monthly_clim.to_csv(monthly_clim_file, index=False, encoding="utf-8-sig")

# ------------------------------------------------------------
# 11. Print checks
# ------------------------------------------------------------

print("\n===== ASOS 7 Stations Included =====")
print(processed[["station_id", "station_name"]].drop_duplicates().to_string(index=False))

print("\n===== ASOS 7 Stations Quality Check Summary =====")
print(station_summary.to_string(index=False))

print("\n===== ASOS 7 Stations Mean Quality Check Summary =====")
print(overall_summary.to_string(index=False))

print("\n===== ASOS 7 Stations Mean Monthly Climatology =====")
print(monthly_clim.to_string(index=False))

print("\nSaved processed file:", processed_file)
print("Saved multi-station mean file:", multi_station_file)
print("Saved station summary file:", station_summary_file)
print("Saved overall summary file:", overall_summary_file)
print("Saved monthly climatology file:", monthly_clim_file)
