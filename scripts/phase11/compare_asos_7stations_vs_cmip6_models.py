from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
import regionmask
import matplotlib.pyplot as plt

asos_file = Path("data/processed/observations/asos/asos_7stations_mean_monthly_1995_2014_processed.csv")

model_files = {
    "MPI-ESM1-2-LR": Path("data/processed/cmip6/mpi_esm1_2_lr_historical_1995_2014_processed.nc"),
    "MPI-ESM1-2-HR": Path("data/processed/cmip6/mpi_esm1_2_hr_historical_1995_2014_processed.nc"),
    "ACCESS-CM2": Path("data/processed/cmip6/access_cm2_historical_1995_2014_processed.nc"),
    "CanESM5": Path("data/processed/cmip6/canesm5_historical_1995_2014_processed.nc"),
}

res_dir = Path("results/phase11_observations")
fig_dir = Path("figures/phase11_observations")
res_dir.mkdir(parents=True, exist_ok=True)
fig_dir.mkdir(parents=True, exist_ok=True)

asos = pd.read_csv(asos_file, encoding="utf-8-sig")
asos["time"] = pd.to_datetime(asos["time"])

countries = regionmask.defined_regions.natural_earth_v5_0_0.countries_50
south_korea_number = 55

metrics_rows = []
monthly_rows = []

def get_reliability(land_grid_cells):
    if land_grid_cells <= 1:
        return "reference_only_not_recommended"
    elif land_grid_cells <= 3:
        return "very_limited"
    elif land_grid_cells <= 6:
        return "limited_supplementary"
    else:
        return "supplementary_usable"

for model_name, model_file in model_files.items():
    print("\n" + "=" * 90)
    print("MODEL:", model_name)
    print("FILE:", model_file)
    print("=" * 90)

    if not model_file.exists():
        raise FileNotFoundError(f"Missing model file: {model_file}")

    ds = xr.open_dataset(model_file)

    # South Korea land mask for supplementary comparison
    mask = countries.mask(ds["longitude"], ds["latitude"])
    korea_mask = mask == south_korea_number

    total_grid_cells = int(korea_mask.size)
    land_grid_cells = int(korea_mask.sum().values)
    reliability = get_reliability(land_grid_cells)

    print("total grid cells:", total_grid_cells)
    print("south korea land grid cells:", land_grid_cells)
    print("reliability:", reliability)

    ds_land = ds.where(korea_mask)

    for var, unit in [
        ("tas", "degC"),
        ("pr", "mm/day"),
    ]:
        # ASOS 7-station mean
        obs = asos[["time", "month", var]].copy()
        obs = obs.rename(columns={var: "ASOS_7stations_mean"})

        # Model box mean
        model_box_ts = ds[var].mean(dim=["latitude", "longitude"]).to_dataframe(name="CMIP6_box_mean").reset_index()
        model_box_ts["time"] = pd.to_datetime(model_box_ts["time"])

        merged_box = pd.merge(
            obs,
            model_box_ts[["time", "CMIP6_box_mean"]],
            on="time",
            how="inner"
        )

        diff_box = merged_box["CMIP6_box_mean"] - merged_box["ASOS_7stations_mean"]

        metrics_rows.append({
            "comparison_type": "CMIP6_box_minus_ASOS_7stations",
            "model": model_name,
            "variable": var,
            "unit": unit,
            "time_size": len(merged_box),
            "lat_size": ds["latitude"].size,
            "lon_size": ds["longitude"].size,
            "total_grid_cells": total_grid_cells,
            "land_grid_cells": land_grid_cells,
            "reliability": "box_main_comparison",
            "mean_bias": round(float(diff_box.mean()), 4),
            "rmse": round(float(np.sqrt((diff_box ** 2).mean())), 4),
            "correlation": round(float(merged_box["CMIP6_box_mean"].corr(merged_box["ASOS_7stations_mean"])), 4),
            "asos_mean": round(float(merged_box["ASOS_7stations_mean"].mean()), 4),
            "model_mean": round(float(merged_box["CMIP6_box_mean"].mean()), 4),
        })

        monthly_box = merged_box.groupby("month").agg(
            ASOS_7stations_mean=("ASOS_7stations_mean", "mean"),
            CMIP6_value=("CMIP6_box_mean", "mean"),
        ).reset_index()

        monthly_box["difference_CMIP6_minus_ASOS"] = (
            monthly_box["CMIP6_value"] - monthly_box["ASOS_7stations_mean"]
        )

        for _, r in monthly_box.iterrows():
            monthly_rows.append({
                "comparison_type": "CMIP6_box_minus_ASOS_7stations",
                "model": model_name,
                "variable": var,
                "month": int(r["month"]),
                "ASOS_7stations_mean": round(float(r["ASOS_7stations_mean"]), 4),
                "CMIP6_value": round(float(r["CMIP6_value"]), 4),
                "difference_CMIP6_minus_ASOS": round(float(r["difference_CMIP6_minus_ASOS"]), 4),
                "unit": unit,
                "land_grid_cells": land_grid_cells,
                "reliability": "box_main_comparison",
            })

        # Model land-mask supplementary mean
        model_land_ts = ds_land[var].mean(
            dim=["latitude", "longitude"],
            skipna=True
        ).to_dataframe(name="CMIP6_land_mask_mean").reset_index()

        model_land_ts["time"] = pd.to_datetime(model_land_ts["time"])

        merged_land = pd.merge(
            obs,
            model_land_ts[["time", "CMIP6_land_mask_mean"]],
            on="time",
            how="inner"
        )

        diff_land = merged_land["CMIP6_land_mask_mean"] - merged_land["ASOS_7stations_mean"]

        metrics_rows.append({
            "comparison_type": "CMIP6_land_mask_minus_ASOS_7stations_supplementary",
            "model": model_name,
            "variable": var,
            "unit": unit,
            "time_size": len(merged_land),
            "lat_size": ds["latitude"].size,
            "lon_size": ds["longitude"].size,
            "total_grid_cells": total_grid_cells,
            "land_grid_cells": land_grid_cells,
            "reliability": reliability,
            "mean_bias": round(float(diff_land.mean()), 4),
            "rmse": round(float(np.sqrt((diff_land ** 2).mean())), 4),
            "correlation": round(float(merged_land["CMIP6_land_mask_mean"].corr(merged_land["ASOS_7stations_mean"])), 4),
            "asos_mean": round(float(merged_land["ASOS_7stations_mean"].mean()), 4),
            "model_mean": round(float(merged_land["CMIP6_land_mask_mean"].mean()), 4),
        })

        monthly_land = merged_land.groupby("month").agg(
            ASOS_7stations_mean=("ASOS_7stations_mean", "mean"),
            CMIP6_value=("CMIP6_land_mask_mean", "mean"),
        ).reset_index()

        monthly_land["difference_CMIP6_minus_ASOS"] = (
            monthly_land["CMIP6_value"] - monthly_land["ASOS_7stations_mean"]
        )

        for _, r in monthly_land.iterrows():
            monthly_rows.append({
                "comparison_type": "CMIP6_land_mask_minus_ASOS_7stations_supplementary",
                "model": model_name,
                "variable": var,
                "month": int(r["month"]),
                "ASOS_7stations_mean": round(float(r["ASOS_7stations_mean"]), 4),
                "CMIP6_value": round(float(r["CMIP6_value"]), 4),
                "difference_CMIP6_minus_ASOS": round(float(r["difference_CMIP6_minus_ASOS"]), 4),
                "unit": unit,
                "land_grid_cells": land_grid_cells,
                "reliability": reliability,
            })

# Save tables
metrics = pd.DataFrame(metrics_rows)
monthly = pd.DataFrame(monthly_rows)

metrics_file = res_dir / "asos_7stations_vs_cmip6_models_metrics.csv"
monthly_file = res_dir / "asos_7stations_vs_cmip6_models_monthly_climatology.csv"

metrics.to_csv(metrics_file, index=False, encoding="utf-8-sig")
monthly.to_csv(monthly_file, index=False, encoding="utf-8-sig")

print("\n===== ASOS 7 Stations vs CMIP6 Models Metrics =====")
print(metrics.to_string(index=False))

print("\nSaved:", metrics_file)
print("Saved:", monthly_file)

# Figures: Box comparison metrics
for var, unit in [
    ("tas", "degC"),
    ("pr", "mm/day"),
]:
    sub = metrics[
        (metrics["variable"] == var) &
        (metrics["comparison_type"] == "CMIP6_box_minus_ASOS_7stations")
    ].copy()

    plt.figure(figsize=(9, 5))
    plt.bar(sub["model"], sub["mean_bias"])
    plt.axhline(0, linestyle="--", linewidth=1)
    plt.title(f"CMIP6 Box Mean Bias against ASOS 7 Stations: {var}")
    plt.xlabel("Model")
    plt.ylabel(f"Mean Bias ({unit})")
    plt.xticks(rotation=20)
    plt.tight_layout()
    out_fig = fig_dir / f"asos_7stations_vs_cmip6_box_mean_bias_{var}.png"
    plt.savefig(out_fig, dpi=200)
    plt.close()

    plt.figure(figsize=(9, 5))
    plt.bar(sub["model"], sub["rmse"])
    plt.title(f"CMIP6 Box RMSE against ASOS 7 Stations: {var}")
    plt.xlabel("Model")
    plt.ylabel(f"RMSE ({unit})")
    plt.xticks(rotation=20)
    plt.tight_layout()
    out_fig = fig_dir / f"asos_7stations_vs_cmip6_box_rmse_{var}.png"
    plt.savefig(out_fig, dpi=200)
    plt.close()

    plt.figure(figsize=(9, 5))
    plt.bar(sub["model"], sub["correlation"])
    plt.title(f"CMIP6 Box Correlation against ASOS 7 Stations: {var}")
    plt.xlabel("Model")
    plt.ylabel("Correlation")
    plt.ylim(-1, 1)
    plt.xticks(rotation=20)
    plt.tight_layout()
    out_fig = fig_dir / f"asos_7stations_vs_cmip6_box_correlation_{var}.png"
    plt.savefig(out_fig, dpi=200)
    plt.close()

# Figures: monthly box comparison
for var, unit in [
    ("tas", "degC"),
    ("pr", "mm/day"),
]:
    sub = monthly[
        (monthly["variable"] == var) &
        (monthly["comparison_type"] == "CMIP6_box_minus_ASOS_7stations")
    ]

    plt.figure(figsize=(10, 5))
    for model_name in sub["model"].unique():
        model_sub = sub[sub["model"] == model_name]
        plt.plot(
            model_sub["month"],
            model_sub["difference_CMIP6_minus_ASOS"],
            marker="o",
            label=model_name,
        )

    plt.axhline(0, linestyle="--", linewidth=1)
    plt.title(f"Monthly Bias: CMIP6 Box - ASOS 7 Stations ({var})")
    plt.xlabel("Month")
    plt.ylabel(f"Bias ({unit})")
    plt.xticks(range(1, 13))
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    out_fig = fig_dir / f"asos_7stations_vs_cmip6_box_monthly_bias_{var}.png"
    plt.savefig(out_fig, dpi=200)
    plt.close()

print("\nPHASE 11-C ASOS 7 stations vs CMIP6 models comparison completed.")
