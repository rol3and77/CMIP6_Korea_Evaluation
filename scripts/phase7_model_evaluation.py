from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt

era5_file = Path("data/processed/era5/era5_korea_monthly_1995_2014_processed.nc")
cmip6_file = Path("data/processed/cmip6/mpi_esm1_2_lr_historical_1995_2014_processed.nc")

fig_dir = Path("figures/phase7_evaluation")
result_dir = Path("results/phase7_evaluation")
fig_dir.mkdir(parents=True, exist_ok=True)
result_dir.mkdir(parents=True, exist_ok=True)

era5 = xr.open_dataset(era5_file)
cmip6 = xr.open_dataset(cmip6_file)

print("ERA5 grid:", era5["latitude"].size, "x", era5["longitude"].size)
print("CMIP6 grid:", cmip6["latitude"].size, "x", cmip6["longitude"].size)

# 1. Regrid ERA5 to CMIP6 grid using linear interpolation
# This is not increasing CMIP6 resolution.
# It only puts ERA5 and CMIP6 on the same grid for fair comparison.
era5_on_cmip6 = era5.interp(
    latitude=cmip6["latitude"],
    longitude=cmip6["longitude"]
)

# 2. Make sure time coordinates match
era5_on_cmip6 = era5_on_cmip6.sel(time=cmip6["time"])

metrics_rows = []

for var, unit, label in [
    ("tas", "degC", "Temperature"),
    ("pr", "mm/day", "Precipitation"),
]:
    print("\n" + "=" * 80)
    print("Evaluating:", var)
    print("=" * 80)

    model = cmip6[var]
    ref = era5_on_cmip6[var]

    diff = model - ref

    # Overall bias map: time mean of difference
    bias_map = diff.mean(dim="time")

    # RMSE map
    rmse_map = np.sqrt((diff ** 2).mean(dim="time"))

    # Area mean time series
    model_ts = model.mean(dim=["latitude", "longitude"])
    ref_ts = ref.mean(dim=["latitude", "longitude"])
    diff_ts = model_ts - ref_ts

    # Overall scalar metrics
    mean_bias = float(diff.mean().values)
    rmse = float(np.sqrt((diff ** 2).mean()).values)
    corr = float(xr.corr(model_ts, ref_ts, dim="time").values)

    metrics_rows.append({
        "variable": var,
        "unit": unit,
        "mean_bias_CMIP6_minus_ERA5": round(mean_bias, 4),
        "rmse": round(rmse, 4),
        "correlation_area_mean_time_series": round(corr, 4),
    })

    print("Mean bias:", mean_bias, unit)
    print("RMSE:", rmse, unit)
    print("Correlation:", corr)

    # Save monthly time series table
    ts_df = pd.DataFrame({
        "time": model_ts["time"].values,
        f"ERA5_{var}": ref_ts.values,
        f"CMIP6_{var}": model_ts.values,
        f"bias_{var}_CMIP6_minus_ERA5": diff_ts.values,
    })
    ts_file = result_dir / f"timeseries_area_mean_{var}.csv"
    ts_df.to_csv(ts_file, index=False)
    print("Saved:", ts_file)

    # Bias map
    plt.figure(figsize=(7, 5))
    bias_map.plot()
    plt.title(f"CMIP6 - ERA5 Bias Map: {label}, 1995-2014")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.tight_layout()
    out_file = fig_dir / f"bias_map_{var}.png"
    plt.savefig(out_file, dpi=200)
    plt.close()
    print("Saved:", out_file)

    # RMSE map
    plt.figure(figsize=(7, 5))
    rmse_map.plot()
    plt.title(f"RMSE Map: {label}, 1995-2014")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.tight_layout()
    out_file = fig_dir / f"rmse_map_{var}.png"
    plt.savefig(out_file, dpi=200)
    plt.close()
    print("Saved:", out_file)

    # Area mean time series
    plt.figure(figsize=(10, 5))
    plt.plot(ref_ts["time"], ref_ts, label="ERA5")
    plt.plot(model_ts["time"], model_ts, label="CMIP6 MPI-ESM1-2-LR")
    plt.title(f"Area-Mean Monthly Time Series: {label}, 1995-2014")
    plt.xlabel("Time")
    plt.ylabel(f"{label} ({unit})")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    out_file = fig_dir / f"timeseries_area_mean_{var}.png"
    plt.savefig(out_file, dpi=200)
    plt.close()
    print("Saved:", out_file)

    # Monthly climatological bias
    monthly_bias = diff.mean(dim=["latitude", "longitude"]).groupby("time.month").mean()

    monthly_bias_df = pd.DataFrame({
        "month": monthly_bias["month"].values,
        f"monthly_bias_{var}_CMIP6_minus_ERA5": monthly_bias.values,
        "unit": unit,
    })
    monthly_bias_file = result_dir / f"monthly_bias_{var}.csv"
    monthly_bias_df.to_csv(monthly_bias_file, index=False)
    print("Saved:", monthly_bias_file)

    plt.figure(figsize=(8, 5))
    plt.plot(monthly_bias["month"], monthly_bias, marker="o")
    plt.axhline(0, linestyle="--", linewidth=1)
    plt.title(f"Monthly Mean Bias: {label}, CMIP6 - ERA5")
    plt.xlabel("Month")
    plt.ylabel(f"Bias ({unit})")
    plt.xticks(range(1, 13))
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    out_file = fig_dir / f"monthly_bias_{var}.png"
    plt.savefig(out_file, dpi=200)
    plt.close()
    print("Saved:", out_file)

# Save scalar metrics
metrics = pd.DataFrame(metrics_rows)
metrics_file = result_dir / "model_evaluation_metrics.csv"
metrics.to_csv(metrics_file, index=False)

print("\n===== PHASE 7 Model Evaluation Metrics =====")
print(metrics.to_string(index=False))
print("\nSaved:", metrics_file)

print("\nPHASE 7 model evaluation completed.")
