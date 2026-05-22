from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt

era5_file = Path("data/processed/era5/era5_korea_monthly_1995_2014_processed.nc")
cmip6_file = Path("data/processed/cmip6/mpi_esm1_2_lr_historical_1995_2014_processed.nc")

fig_dir = Path("figures/phase8_extreme_proxy")
res_dir = Path("results/phase8_extreme_proxy")

fig_dir.mkdir(parents=True, exist_ok=True)
res_dir.mkdir(parents=True, exist_ok=True)

era5 = xr.open_dataset(era5_file)
cmip6 = xr.open_dataset(cmip6_file)

print("ERA5 grid:", era5["latitude"].size, "x", era5["longitude"].size)
print("CMIP6 grid:", cmip6["latitude"].size, "x", cmip6["longitude"].size)

# ERA5를 CMIP6 격자로 보간
# PHASE 7과 같은 방식이다.
era5_on_cmip6 = era5.interp(
    latitude=cmip6["latitude"],
    longitude=cmip6["longitude"]
)

era5_on_cmip6 = era5_on_cmip6.sel(time=cmip6["time"])

datasets = {
    "ERA5": era5_on_cmip6,
    "CMIP6_MPI_ESM1_2_LR": cmip6,
}

summary_rows = []

# ============================================================
# 1. JJA mean analysis
# ============================================================

for dataset_name, ds in datasets.items():
    jja = ds.sel(time=ds["time"].dt.month.isin([6, 7, 8]))

    jja_tas_map = jja["tas"].mean(dim="time")
    jja_pr_map = jja["pr"].mean(dim="time")

    jja_tas_area_mean = float(jja_tas_map.mean(dim=["latitude", "longitude"]).values)
    jja_pr_area_mean = float(jja_pr_map.mean(dim=["latitude", "longitude"]).values)

    summary_rows.append({
        "dataset": dataset_name,
        "metric": "JJA_mean_temperature",
        "value": round(jja_tas_area_mean, 4),
        "unit": "degC",
    })

    summary_rows.append({
        "dataset": dataset_name,
        "metric": "JJA_mean_precipitation",
        "value": round(jja_pr_area_mean, 4),
        "unit": "mm/day",
    })

# JJA bias maps
era5_jja = era5_on_cmip6.sel(time=era5_on_cmip6["time"].dt.month.isin([6, 7, 8]))
cmip6_jja = cmip6.sel(time=cmip6["time"].dt.month.isin([6, 7, 8]))

jja_tas_bias = cmip6_jja["tas"].mean(dim="time") - era5_jja["tas"].mean(dim="time")
jja_pr_bias = cmip6_jja["pr"].mean(dim="time") - era5_jja["pr"].mean(dim="time")

summary_rows.append({
    "dataset": "CMIP6_minus_ERA5",
    "metric": "JJA_temperature_bias",
    "value": round(float(jja_tas_bias.mean(dim=["latitude", "longitude"]).values), 4),
    "unit": "degC",
})

summary_rows.append({
    "dataset": "CMIP6_minus_ERA5",
    "metric": "JJA_precipitation_bias",
    "value": round(float(jja_pr_bias.mean(dim=["latitude", "longitude"]).values), 4),
    "unit": "mm/day",
})

plt.figure(figsize=(7, 5))
jja_tas_bias.plot()
plt.title("JJA Temperature Bias, CMIP6 - ERA5")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.tight_layout()
out_file = fig_dir / "jja_tas_bias_map.png"
plt.savefig(out_file, dpi=200)
plt.close()
print("Saved:", out_file)

plt.figure(figsize=(7, 5))
jja_pr_bias.plot()
plt.title("JJA Precipitation Bias, CMIP6 - ERA5")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.tight_layout()
out_file = fig_dir / "jja_pr_bias_map.png"
plt.savefig(out_file, dpi=200)
plt.close()
print("Saved:", out_file)

# ============================================================
# 2. Annual maximum monthly temperature and precipitation
# ============================================================

annual_rows_tas = []
annual_rows_pr = []

for dataset_name, ds in datasets.items():
    tas_area = ds["tas"].mean(dim=["latitude", "longitude"])
    pr_area = ds["pr"].mean(dim=["latitude", "longitude"])

    tas_df = tas_area.to_dataframe(name="tas").reset_index()
    pr_df = pr_area.to_dataframe(name="pr").reset_index()

    tas_df["year"] = pd.to_datetime(tas_df["time"]).dt.year
    tas_df["month"] = pd.to_datetime(tas_df["time"]).dt.month

    pr_df["year"] = pd.to_datetime(pr_df["time"]).dt.year
    pr_df["month"] = pd.to_datetime(pr_df["time"]).dt.month

    tas_idx = tas_df.groupby("year")["tas"].idxmax()
    pr_idx = pr_df.groupby("year")["pr"].idxmax()

    tas_max = tas_df.loc[tas_idx, ["year", "month", "tas"]].copy()
    pr_max = pr_df.loc[pr_idx, ["year", "month", "pr"]].copy()

    tas_max["dataset"] = dataset_name
    pr_max["dataset"] = dataset_name

    annual_rows_tas.append(tas_max)
    annual_rows_pr.append(pr_max)

annual_tas = pd.concat(annual_rows_tas, ignore_index=True)
annual_pr = pd.concat(annual_rows_pr, ignore_index=True)

annual_tas = annual_tas[["dataset", "year", "month", "tas"]]
annual_pr = annual_pr[["dataset", "year", "month", "pr"]]

annual_tas_file = res_dir / "annual_max_monthly_tas.csv"
annual_pr_file = res_dir / "annual_max_monthly_pr.csv"

annual_tas.to_csv(annual_tas_file, index=False)
annual_pr.to_csv(annual_pr_file, index=False)

print("Saved:", annual_tas_file)
print("Saved:", annual_pr_file)

# Annual maximum monthly temperature time series
plt.figure(figsize=(9, 5))
for dataset_name in annual_tas["dataset"].unique():
    sub = annual_tas[annual_tas["dataset"] == dataset_name]
    plt.plot(sub["year"], sub["tas"], marker="o", label=dataset_name)

plt.title("Annual Maximum Monthly Mean Temperature")
plt.xlabel("Year")
plt.ylabel("Temperature (degC)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
out_file = fig_dir / "annual_max_monthly_tas_timeseries.png"
plt.savefig(out_file, dpi=200)
plt.close()
print("Saved:", out_file)

# Annual maximum monthly precipitation time series
plt.figure(figsize=(9, 5))
for dataset_name in annual_pr["dataset"].unique():
    sub = annual_pr[annual_pr["dataset"] == dataset_name]
    plt.plot(sub["year"], sub["pr"], marker="o", label=dataset_name)

plt.title("Annual Maximum Monthly Mean Precipitation")
plt.xlabel("Year")
plt.ylabel("Precipitation (mm/day)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
out_file = fig_dir / "annual_max_monthly_pr_timeseries.png"
plt.savefig(out_file, dpi=200)
plt.close()
print("Saved:", out_file)

# ============================================================
# 3. Summary metrics for annual maxima
# ============================================================

for dataset_name in annual_tas["dataset"].unique():
    sub_tas = annual_tas[annual_tas["dataset"] == dataset_name]
    sub_pr = annual_pr[annual_pr["dataset"] == dataset_name]

    summary_rows.append({
        "dataset": dataset_name,
        "metric": "mean_annual_max_monthly_temperature",
        "value": round(float(sub_tas["tas"].mean()), 4),
        "unit": "degC",
    })

    summary_rows.append({
        "dataset": dataset_name,
        "metric": "mean_annual_max_monthly_precipitation",
        "value": round(float(sub_pr["pr"].mean()), 4),
        "unit": "mm/day",
    })

era5_tas_max = annual_tas[annual_tas["dataset"] == "ERA5"].set_index("year")
cmip6_tas_max = annual_tas[annual_tas["dataset"] == "CMIP6_MPI_ESM1_2_LR"].set_index("year")

era5_pr_max = annual_pr[annual_pr["dataset"] == "ERA5"].set_index("year")
cmip6_pr_max = annual_pr[annual_pr["dataset"] == "CMIP6_MPI_ESM1_2_LR"].set_index("year")

tas_max_bias = cmip6_tas_max["tas"] - era5_tas_max["tas"]
pr_max_bias = cmip6_pr_max["pr"] - era5_pr_max["pr"]

summary_rows.append({
    "dataset": "CMIP6_minus_ERA5",
    "metric": "mean_bias_annual_max_monthly_temperature",
    "value": round(float(tas_max_bias.mean()), 4),
    "unit": "degC",
})

summary_rows.append({
    "dataset": "CMIP6_minus_ERA5",
    "metric": "mean_bias_annual_max_monthly_precipitation",
    "value": round(float(pr_max_bias.mean()), 4),
    "unit": "mm/day",
})

summary = pd.DataFrame(summary_rows)
summary_file = res_dir / "extreme_proxy_summary.csv"
summary.to_csv(summary_file, index=False)

print("\n===== PHASE 8 Extreme Proxy Summary =====")
print(summary.to_string(index=False))
print("\nSaved:", summary_file)

print("\nPHASE 8 extreme proxy analysis completed.")
