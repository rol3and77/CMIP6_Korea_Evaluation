from pathlib import Path
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import numpy as np

asos_file = Path("data/processed/observations/asos/asos_7stations_mean_monthly_1995_2014_processed.csv")
era5_land_file = Path("data/processed/era5/era5_korea_land_masked_monthly_1995_2014.nc")

res_dir = Path("results/phase11_observations")
fig_dir = Path("figures/phase11_observations")
res_dir.mkdir(parents=True, exist_ok=True)
fig_dir.mkdir(parents=True, exist_ok=True)

asos = pd.read_csv(asos_file, encoding="utf-8-sig")
asos["time"] = pd.to_datetime(asos["time"])

era5 = xr.open_dataset(era5_land_file)

rows = []
monthly_rows = []

for var, unit in [
    ("tas", "degC"),
    ("pr", "mm/day"),
]:
    asos_ts = asos[["time", "month", var]].copy()
    asos_ts = asos_ts.rename(columns={var: "ASOS_7stations_mean"})

    era5_ts = era5[var].mean(
        dim=["latitude", "longitude"],
        skipna=True
    ).to_dataframe(name="ERA5_Korea_land").reset_index()

    era5_ts["time"] = pd.to_datetime(era5_ts["time"])

    merged = pd.merge(
        asos_ts,
        era5_ts[["time", "ERA5_Korea_land"]],
        on="time",
        how="inner"
    )

    diff = merged["ERA5_Korea_land"] - merged["ASOS_7stations_mean"]

    mean_bias = diff.mean()
    rmse = np.sqrt((diff ** 2).mean())
    corr = merged["ERA5_Korea_land"].corr(merged["ASOS_7stations_mean"])

    rows.append({
        "comparison": "ERA5_Korea_land_minus_ASOS_7stations_mean",
        "variable": var,
        "unit": unit,
        "time_size": len(merged),
        "mean_bias": round(mean_bias, 4),
        "rmse": round(rmse, 4),
        "correlation": round(corr, 4),
        "asos_7stations_mean": round(merged["ASOS_7stations_mean"].mean(), 4),
        "era5_land_mean": round(merged["ERA5_Korea_land"].mean(), 4),
    })

    monthly = merged.groupby("month").agg(
        ASOS_7stations_mean=("ASOS_7stations_mean", "mean"),
        ERA5_Korea_land=("ERA5_Korea_land", "mean"),
    ).reset_index()

    monthly["difference_ERA5_land_minus_ASOS"] = (
        monthly["ERA5_Korea_land"] - monthly["ASOS_7stations_mean"]
    )

    for _, r in monthly.iterrows():
        monthly_rows.append({
            "variable": var,
            "month": int(r["month"]),
            "ASOS_7stations_mean": round(float(r["ASOS_7stations_mean"]), 4),
            "ERA5_Korea_land": round(float(r["ERA5_Korea_land"]), 4),
            "difference_ERA5_land_minus_ASOS": round(float(r["difference_ERA5_land_minus_ASOS"]), 4),
            "unit": unit,
        })

    plt.figure(figsize=(9, 5))
    plt.plot(monthly["month"], monthly["ASOS_7stations_mean"], marker="o", label="ASOS 7-station mean")
    plt.plot(monthly["month"], monthly["ERA5_Korea_land"], marker="o", label="ERA5 Korea land mean")
    plt.title(f"Monthly Climatology: ASOS 7 Stations vs ERA5 Korea Land ({var})")
    plt.xlabel("Month")
    plt.ylabel(f"{var} ({unit})")
    plt.xticks(range(1, 13))
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    out_fig = fig_dir / f"asos_7stations_vs_era5_land_monthly_{var}.png"
    plt.savefig(out_fig, dpi=200)
    plt.close()

    plt.figure(figsize=(9, 5))
    plt.plot(monthly["month"], monthly["difference_ERA5_land_minus_ASOS"], marker="o")
    plt.axhline(0, linestyle="--", linewidth=1)
    plt.title(f"Monthly Difference: ERA5 Korea Land - ASOS 7 Stations ({var})")
    plt.xlabel("Month")
    plt.ylabel(f"Difference ({unit})")
    plt.xticks(range(1, 13))
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    out_fig = fig_dir / f"asos_7stations_vs_era5_land_difference_{var}.png"
    plt.savefig(out_fig, dpi=200)
    plt.close()

metrics = pd.DataFrame(rows)
monthly_result = pd.DataFrame(monthly_rows)

metrics_file = res_dir / "asos_7stations_vs_era5_land_metrics.csv"
monthly_file = res_dir / "asos_7stations_vs_era5_land_monthly_climatology.csv"

metrics.to_csv(metrics_file, index=False, encoding="utf-8-sig")
monthly_result.to_csv(monthly_file, index=False, encoding="utf-8-sig")

print("\n===== ASOS 7 Stations vs ERA5 Korea Land Metrics =====")
print(metrics.to_string(index=False))

print("\n===== ASOS 7 Stations vs ERA5 Korea Land Monthly Climatology =====")
print(monthly_result.to_string(index=False))

print("\nSaved:", metrics_file)
print("Saved:", monthly_file)
print("PHASE 11-B ASOS 7 stations vs ERA5 land comparison completed.")
