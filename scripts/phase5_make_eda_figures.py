from pathlib import Path
import xarray as xr
import matplotlib.pyplot as plt

era5_file = Path("data/processed/era5/era5_korea_monthly_1995_2014_processed.nc")
cmip6_file = Path("data/processed/cmip6/mpi_esm1_2_lr_historical_1995_2014_processed.nc")

out_dir = Path("figures/phase5_eda")
out_dir.mkdir(parents=True, exist_ok=True)

era5 = xr.open_dataset(era5_file)
cmip6 = xr.open_dataset(cmip6_file)

datasets = {
    "ERA5": era5,
    "CMIP6_MPI_ESM1_2_LR": cmip6,
}

# 1. Mean temperature map
for name, ds in datasets.items():
    tas_mean = ds["tas"].mean(dim="time")

    plt.figure(figsize=(7, 5))
    tas_mean.plot()
    plt.title(f"{name} Mean 2m Temperature, 1995-2014")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.tight_layout()

    out_file = out_dir / f"{name.lower()}_tas_mean_map.png"
    plt.savefig(out_file, dpi=200)
    plt.close()

    print("Saved:", out_file)

# 2. Mean precipitation map
for name, ds in datasets.items():
    pr_mean = ds["pr"].mean(dim="time")

    plt.figure(figsize=(7, 5))
    pr_mean.plot()
    plt.title(f"{name} Mean Precipitation, 1995-2014")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.tight_layout()

    out_file = out_dir / f"{name.lower()}_pr_mean_map.png"
    plt.savefig(out_file, dpi=200)
    plt.close()

    print("Saved:", out_file)

# 3. Monthly seasonal cycle: spatial mean temperature
plt.figure(figsize=(8, 5))

for name, ds in datasets.items():
    tas_monthly = ds["tas"].mean(dim=["latitude", "longitude"]).groupby("time.month").mean()
    plt.plot(tas_monthly["month"], tas_monthly, marker="o", label=name)

plt.title("Monthly Seasonal Cycle of Temperature, 1995-2014")
plt.xlabel("Month")
plt.ylabel("Temperature (degC)")
plt.xticks(range(1, 13))
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()

out_file = out_dir / "seasonal_cycle_tas.png"
plt.savefig(out_file, dpi=200)
plt.close()

print("Saved:", out_file)

# 4. Monthly seasonal cycle: spatial mean precipitation
plt.figure(figsize=(8, 5))

for name, ds in datasets.items():
    pr_monthly = ds["pr"].mean(dim=["latitude", "longitude"]).groupby("time.month").mean()
    plt.plot(pr_monthly["month"], pr_monthly, marker="o", label=name)

plt.title("Monthly Seasonal Cycle of Precipitation, 1995-2014")
plt.xlabel("Month")
plt.ylabel("Precipitation (mm/day)")
plt.xticks(range(1, 13))
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()

out_file = out_dir / "seasonal_cycle_pr.png"
plt.savefig(out_file, dpi=200)
plt.close()

print("Saved:", out_file)

print("\nPHASE 5 EDA figures completed.")
