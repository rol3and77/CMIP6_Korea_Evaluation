from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt

era5_file = Path("data/processed/era5/era5_korea_monthly_1995_2014_processed.nc")

model_files = {
    "MPI-ESM1-2-LR": Path("data/processed/cmip6/mpi_esm1_2_lr_historical_1995_2014_processed.nc"),
    "ACCESS-CM2": Path("data/processed/cmip6/access_cm2_historical_1995_2014_processed.nc"),
    "CanESM5": Path("data/processed/cmip6/canesm5_historical_1995_2014_processed.nc"),
}

fig_dir = Path("figures/phase9_model_expansion")
res_dir = Path("results/phase9_model_expansion")
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

    # ERA5를 각 CMIP6 모델의 고유 격자로 보간
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

metrics_file = res_dir / "multi_model_evaluation_metrics.csv"
monthly_bias_file = res_dir / "multi_model_monthly_bias.csv"

metrics.to_csv(metrics_file, index=False)
monthly_bias.to_csv(monthly_bias_file, index=False)

print("\n===== PHASE 9 Multi-model Evaluation Metrics =====")
print(metrics.to_string(index=False))
print("\nSaved:", metrics_file)

print("\n===== PHASE 9 Multi-model Monthly Bias =====")
print(monthly_bias.to_string(index=False))
print("\nSaved:", monthly_bias_file)

for var, unit in [("tas", "degC"), ("pr", "mm/day")]:
    sub = metrics[metrics["variable"] == var].copy()

    plt.figure(figsize=(8, 5))
    plt.bar(sub["model"], sub["mean_bias_CMIP6_minus_ERA5"])
    plt.axhline(0, linestyle="--", linewidth=1)
    plt.title(f"Mean Bias by Model: {var}")
    plt.xlabel("Model")
    plt.ylabel(f"Mean Bias ({unit})")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(fig_dir / f"multi_model_mean_bias_{var}.png", dpi=200)
    plt.close()

    plt.figure(figsize=(8, 5))
    plt.bar(sub["model"], sub["rmse"])
    plt.title(f"RMSE by Model: {var}")
    plt.xlabel("Model")
    plt.ylabel(f"RMSE ({unit})")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(fig_dir / f"multi_model_rmse_{var}.png", dpi=200)
    plt.close()

    plt.figure(figsize=(8, 5))
    plt.bar(sub["model"], sub["correlation_area_mean_time_series"])
    plt.title(f"Area-Mean Time Series Correlation by Model: {var}")
    plt.xlabel("Model")
    plt.ylabel("Correlation")
    plt.ylim(-1, 1)
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(fig_dir / f"multi_model_correlation_{var}.png", dpi=200)
    plt.close()

for var, unit in [("tas", "degC"), ("pr", "mm/day")]:
    sub = monthly_bias[monthly_bias["variable"] == var]

    plt.figure(figsize=(9, 5))
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
    plt.savefig(fig_dir / f"multi_model_monthly_bias_{var}.png", dpi=200)
    plt.close()

print("\nPHASE 9 multi-model evaluation completed.")
