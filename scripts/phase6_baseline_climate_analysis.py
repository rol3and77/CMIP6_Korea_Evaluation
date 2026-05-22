from pathlib import Path
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt

files = {
    "ERA5": Path("data/processed/era5/era5_korea_monthly_1995_2014_processed.nc"),
    "CMIP6_MPI_ESM1_2_LR": Path("data/processed/cmip6/mpi_esm1_2_lr_historical_1995_2014_processed.nc"),
}

fig_dir = Path("figures/phase6_baseline")
res_dir = Path("results/phase6_baseline")
fig_dir.mkdir(parents=True, exist_ok=True)
res_dir.mkdir(parents=True, exist_ok=True)

summary_rows = []

for name, path in files.items():
    ds = xr.open_dataset(path)

    for var, label, unit in [
        ("tas", "Temperature", "degC"),
        ("pr", "Precipitation", "mm/day"),
    ]:
        # 1) 1995-2014 mean map
        clim_map = ds[var].mean(dim="time")
        plt.figure(figsize=(7, 5))
        clim_map.plot()
        plt.title(f"{name} {label} Climatology, 1995-2014")
        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
        plt.tight_layout()
        out_fig = fig_dir / f"{name.lower()}_{var}_climatology_map.png"
        plt.savefig(out_fig, dpi=200)
        plt.close()

        # 2) monthly climatology and spatial mean seasonal cycle
        monthly = ds[var].groupby("time.month").mean(dim="time")
        spatial_monthly = monthly.mean(dim=["latitude", "longitude"])

        for month in range(1, 13):
            value = float(spatial_monthly.sel(month=month).values)
            summary_rows.append({
                "dataset": name,
                "variable": var,
                "month": month,
                "value": round(value, 4),
                "unit": unit,
            })

summary = pd.DataFrame(summary_rows)
summary_file = res_dir / "monthly_climatology_spatial_mean.csv"
summary.to_csv(summary_file, index=False)

# 3) seasonal cycle figures
for var, label, unit in [
    ("tas", "Temperature", "degC"),
    ("pr", "Precipitation", "mm/day"),
]:
    plt.figure(figsize=(8, 5))
    for name, path in files.items():
        ds = xr.open_dataset(path)
        monthly = ds[var].groupby("time.month").mean(dim="time")
        spatial_monthly = monthly.mean(dim=["latitude", "longitude"])
        plt.plot(spatial_monthly["month"], spatial_monthly, marker="o", label=name)

    plt.title(f"Baseline Seasonal Cycle of {label}, 1995-2014")
    plt.xlabel("Month")
    plt.ylabel(f"{label} ({unit})")
    plt.xticks(range(1, 13))
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    out_fig = fig_dir / f"seasonal_cycle_{var}.png"
    plt.savefig(out_fig, dpi=200)
    plt.close()

print("PHASE 6 baseline climate analysis completed.")
print("Saved table:", summary_file)
print("Saved figures to:", fig_dir)
print(summary.head())
