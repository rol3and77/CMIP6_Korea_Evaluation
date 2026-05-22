from pathlib import Path
import pandas as pd
import xarray as xr
import regionmask
import matplotlib.pyplot as plt

model_files = {
    "MPI-ESM1-2-LR": Path("data/processed/cmip6/mpi_esm1_2_lr_historical_1995_2014_processed.nc"),
    "MPI-ESM1-2-HR": Path("data/processed/cmip6/mpi_esm1_2_hr_historical_1995_2014_processed.nc"),
    "ACCESS-CM2": Path("data/processed/cmip6/access_cm2_historical_1995_2014_processed.nc"),
    "CanESM5": Path("data/processed/cmip6/canesm5_historical_1995_2014_processed.nc"),
}

res_dir = Path("results/phase10_land_mask")
fig_dir = Path("figures/phase10_land_mask")
res_dir.mkdir(parents=True, exist_ok=True)
fig_dir.mkdir(parents=True, exist_ok=True)

countries = regionmask.defined_regions.natural_earth_v5_0_0.countries_50
south_korea_number = 55

summary_rows = []
monthly_rows = []

for model_name, file_path in model_files.items():
    print("\n" + "=" * 90)
    print("MODEL:", model_name)
    print("FILE:", file_path)
    print("=" * 90)

    if not file_path.exists():
        raise FileNotFoundError(f"Missing file: {file_path}")

    ds = xr.open_dataset(file_path)

    mask = countries.mask(ds["longitude"], ds["latitude"])
    korea_mask = mask == south_korea_number

    total_grid_cells = int(korea_mask.size)
    land_grid_cells = int(korea_mask.sum().values)
    land_grid_ratio = land_grid_cells / total_grid_cells

    if land_grid_cells <= 1:
        reliability = "reference_only_not_recommended"
    elif land_grid_cells <= 3:
        reliability = "very_limited"
    elif land_grid_cells <= 6:
        reliability = "limited_supplementary"
    else:
        reliability = "supplementary_usable"

    print("total grid cells:", total_grid_cells)
    print("south korea land grid cells:", land_grid_cells)
    print("land grid ratio:", round(land_grid_ratio, 4))
    print("reliability:", reliability)

    ds_land = ds.where(korea_mask)

    for var, unit in [
        ("tas", "degC"),
        ("pr", "mm/day"),
    ]:
        box_ts = ds[var].mean(dim=["latitude", "longitude"])
        land_ts = ds_land[var].mean(dim=["latitude", "longitude"], skipna=True)

        box_mean = float(box_ts.mean().values)
        land_mean = float(land_ts.mean().values)
        diff_mean = land_mean - box_mean

        summary_rows.append({
            "model": model_name,
            "variable": var,
            "box_mean": round(box_mean, 4),
            "korea_land_mean": round(land_mean, 4),
            "difference_land_minus_box": round(diff_mean, 4),
            "unit": unit,
            "lat_size": ds["latitude"].size,
            "lon_size": ds["longitude"].size,
            "total_grid_cells": total_grid_cells,
            "south_korea_land_grid_cells": land_grid_cells,
            "land_grid_ratio": round(land_grid_ratio, 4),
            "reliability": reliability,
        })

        box_monthly = box_ts.groupby("time.month").mean()
        land_monthly = land_ts.groupby("time.month").mean()
        diff_monthly = land_monthly - box_monthly

        for month in range(1, 13):
            monthly_rows.append({
                "model": model_name,
                "variable": var,
                "month": month,
                "box_mean": round(float(box_monthly.sel(month=month).values), 4),
                "korea_land_mean": round(float(land_monthly.sel(month=month).values), 4),
                "difference_land_minus_box": round(float(diff_monthly.sel(month=month).values), 4),
                "unit": unit,
                "south_korea_land_grid_cells": land_grid_cells,
                "reliability": reliability,
            })

# Save tables
summary = pd.DataFrame(summary_rows)
monthly = pd.DataFrame(monthly_rows)

summary_file = res_dir / "cmip6_land_mask_supplementary_summary.csv"
monthly_file = res_dir / "cmip6_land_mask_supplementary_monthly.csv"

summary.to_csv(summary_file, index=False)
monthly.to_csv(monthly_file, index=False)

print("\n===== CMIP6 Land Mask Supplementary Summary =====")
print(summary.to_string(index=False))
print("\nSaved:", summary_file)

print("\n===== CMIP6 Land Mask Supplementary Monthly Table =====")
print(monthly.to_string(index=False))
print("\nSaved:", monthly_file)

# Figures: land-box annual mean difference by model
for var, unit in [
    ("tas", "degC"),
    ("pr", "mm/day"),
]:
    sub = summary[summary["variable"] == var].copy()

    plt.figure(figsize=(9, 5))
    plt.bar(sub["model"], sub["difference_land_minus_box"])
    plt.axhline(0, linestyle="--", linewidth=1)
    plt.title(f"CMIP6 Korea Land - Box Mean Difference: {var}")
    plt.xlabel("Model")
    plt.ylabel(f"Land - Box Difference ({unit})")
    plt.xticks(rotation=20)
    plt.tight_layout()

    out_fig = fig_dir / f"cmip6_land_minus_box_summary_{var}.png"
    plt.savefig(out_fig, dpi=200)
    plt.close()
    print("Saved:", out_fig)

# Figures: monthly land-box difference
for var, unit in [
    ("tas", "degC"),
    ("pr", "mm/day"),
]:
    sub = monthly[monthly["variable"] == var]

    plt.figure(figsize=(10, 5))
    for model_name in sub["model"].unique():
        model_sub = sub[sub["model"] == model_name]
        plt.plot(
            model_sub["month"],
            model_sub["difference_land_minus_box"],
            marker="o",
            label=model_name,
        )

    plt.axhline(0, linestyle="--", linewidth=1)
    plt.title(f"CMIP6 Monthly Korea Land - Box Difference: {var}")
    plt.xlabel("Month")
    plt.ylabel(f"Land - Box Difference ({unit})")
    plt.xticks(range(1, 13))
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()

    out_fig = fig_dir / f"cmip6_land_minus_box_monthly_{var}.png"
    plt.savefig(out_fig, dpi=200)
    plt.close()
    print("Saved:", out_fig)

# Figures: grid count
grid_info = summary[["model", "south_korea_land_grid_cells", "total_grid_cells", "reliability"]].drop_duplicates()

plt.figure(figsize=(9, 5))
plt.bar(grid_info["model"], grid_info["south_korea_land_grid_cells"])
plt.title("South Korea Land Grid Cells by CMIP6 Model")
plt.xlabel("Model")
plt.ylabel("Number of Land Grid Cells")
plt.xticks(rotation=20)
plt.tight_layout()

out_fig = fig_dir / "cmip6_south_korea_land_grid_cells.png"
plt.savefig(out_fig, dpi=200)
plt.close()
print("Saved:", out_fig)

print("\nPHASE 10.5 CMIP6 land mask supplementary analysis completed.")
