from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt

era5_file = Path("data/processed/era5/era5_korea_monthly_1995_2014_processed.nc")

model_files = {
    "MPI-ESM1-2-LR": Path("data/processed/cmip6/mpi_esm1_2_lr_historical_1995_2014_processed.nc"),
    "MPI-ESM1-2-HR": Path("data/processed/cmip6/mpi_esm1_2_hr_historical_1995_2014_processed.nc"),
    "ACCESS-CM2": Path("data/processed/cmip6/access_cm2_historical_1995_2014_processed.nc"),
    "CanESM5": Path("data/processed/cmip6/canesm5_historical_1995_2014_processed.nc"),
}

fig_dir = Path("figures/phase9_resolution_expansion")
res_dir = Path("results/phase9_resolution_expansion")
fig_dir.mkdir(parents=True, exist_ok=True)
res_dir.mkdir(parents=True, exist_ok=True)

era5 = xr.open_dataset(era5_file)

metrics_rows = []
monthly_rows = []

for model_name, model_file in model_files.items():
    print("\n" + "=" * 90)
    print("Evaluating model:", model_name)
    print("File:", model_file)
    print("=" * 90)

    if not model_file.exists():
        raise FileNotFoundError(f"Missing model file: {model_file}")

    model = xr.open_dataset(model_file)

    print("Model grid:", model["latitude"].size, "x", model["longitude"].size)

    # 핵심 원칙:
    # CMIP6를 ERA5 격자로 올리지 않고,
    # ERA5를 각 CMIP6 모델의 고유 격자로 맞춘다.
    era5_on_model = era5.interp(
        latitude=model["latitude"],
        longitude=model["longitude"]
    )

    era5_on_model = era5_on_model.sel(time=model["time"])

    for var, unit in [
        ("tas", "degC"),
        ("pr", "mm/day"),
    ]:
        model_var = model[var]
        ref_var = era5_on_model[var]

        diff = model_var - ref_var

        model_ts = model_var.mean(dim=["latitude", "longitude"])
        ref_ts = ref_var.mean(dim=["latitude", "longitude"])

        mean_bias = float(diff.mean().values)
        rmse = float(np.sqrt((diff ** 2).mean()).values)
        corr = float(xr.corr(model_ts, ref_ts, dim="time").values)

        metrics_rows.append({
            "model": model_name,
            "variable": var,
            "unit": unit,
            "lat_size": model["latitude"].size,
            "lon_size": model["longitude"].size,
            "grid_cells": model["latitude"].size * model["longitude"].size,
            "mean_bias_CMIP6_minus_ERA5": round(mean_bias, 4),
            "rmse": round(rmse, 4),
            "correlation_area_mean_time_series": round(corr, 4),
        })

        monthly_bias = diff.mean(dim=["latitude", "longitude"]).groupby("time.month").mean()

        for month in range(1, 13):
            monthly_rows.append({
                "model": model_name,
                "variable": var,
                "month": month,
                "monthly_bias_CMIP6_minus_ERA5": round(float(monthly_bias.sel(month=month).values), 4),
                "unit": unit,
            })

metrics = pd.DataFrame(metrics_rows)
monthly_bias = pd.DataFrame(monthly_rows)

metrics_file = res_dir / "four_model_evaluation_metrics.csv"
monthly_bias_file = res_dir / "four_model_monthly_bias.csv"

metrics.to_csv(metrics_file, index=False)
monthly_bias.to_csv(monthly_bias_file, index=False)

print("\n===== PHASE 9-B Four-model Evaluation Metrics =====")
print(metrics.to_string(index=False))
print("\nSaved:", metrics_file)

print("\n===== PHASE 9-B Four-model Monthly Bias =====")
print(monthly_bias.to_string(index=False))
print("\nSaved:", monthly_bias_file)

# 모델별 평균 bias, RMSE, correlation 그림
for var, unit in [("tas", "degC"), ("pr", "mm/day")]:
    sub = metrics[metrics["variable"] == var].copy()

    plt.figure(figsize=(9, 5))
    plt.bar(sub["model"], sub["mean_bias_CMIP6_minus_ERA5"])
    plt.axhline(0, linestyle="--", linewidth=1)
    plt.title(f"Mean Bias by Model: {var}")
    plt.xlabel("Model")
    plt.ylabel(f"Mean Bias ({unit})")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(fig_dir / f"four_model_mean_bias_{var}.png", dpi=200)
    plt.close()

    plt.figure(figsize=(9, 5))
    plt.bar(sub["model"], sub["rmse"])
    plt.title(f"RMSE by Model: {var}")
    plt.xlabel("Model")
    plt.ylabel(f"RMSE ({unit})")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(fig_dir / f"four_model_rmse_{var}.png", dpi=200)
    plt.close()

    plt.figure(figsize=(9, 5))
    plt.bar(sub["model"], sub["correlation_area_mean_time_series"])
    plt.title(f"Area-Mean Time Series Correlation by Model: {var}")
    plt.xlabel("Model")
    plt.ylabel("Correlation")
    plt.ylim(-1, 1)
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(fig_dir / f"four_model_correlation_{var}.png", dpi=200)
    plt.close()

# 월별 bias 그림
for var, unit in [("tas", "degC"), ("pr", "mm/day")]:
    sub = monthly_bias[monthly_bias["variable"] == var]

    plt.figure(figsize=(10, 5))
    for model_name in sub["model"].unique():
        model_sub = sub[sub["model"] == model_name]
        plt.plot(
            model_sub["month"],
            model_sub["monthly_bias_CMIP6_minus_ERA5"],
            marker="o",
            label=model_name,
        )

    plt.axhline(0, linestyle="--", linewidth=1)
    plt.title(f"Monthly Bias by Model: {var}, CMIP6 - ERA5")
    plt.xlabel("Month")
    plt.ylabel(f"Bias ({unit})")
    plt.xticks(range(1, 13))
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(fig_dir / f"four_model_monthly_bias_{var}.png", dpi=200)
    plt.close()

# 해상도 비교용: MPI LR vs HR만 따로 저장
mpi_sub = metrics[metrics["model"].isin(["MPI-ESM1-2-LR", "MPI-ESM1-2-HR"])].copy()
mpi_file = res_dir / "mpi_lr_hr_comparison_metrics.csv"
mpi_sub.to_csv(mpi_file, index=False)

print("\n===== MPI LR vs HR Comparison =====")
print(mpi_sub.to_string(index=False))
print("\nSaved:", mpi_file)

print("\nPHASE 9-B four-model and resolution evaluation completed.")
