from pathlib import Path
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt

era5_box_file = Path("data/processed/era5/era5_korea_monthly_1995_2014_processed.nc")
era5_land_file = Path("data/processed/era5/era5_korea_land_masked_monthly_1995_2014.nc")

res_dir = Path("results/phase10_land_mask")
fig_dir = Path("figures/phase10_land_mask")
res_dir.mkdir(parents=True, exist_ok=True)
fig_dir.mkdir(parents=True, exist_ok=True)

box = xr.open_dataset(era5_box_file)
land = xr.open_dataset(era5_land_file)

rows = []

for var, unit in [
    ("tas", "degC"),
    ("pr", "mm/day"),
]:
    box_monthly = box[var].mean(dim=["latitude", "longitude"]).groupby("time.month").mean()
    land_monthly = land[var].mean(dim=["latitude", "longitude"], skipna=True).groupby("time.month").mean()
    diff_monthly = land_monthly - box_monthly

    for month in range(1, 13):
        rows.append({
            "dataset": "ERA5",
            "variable": var,
            "month": month,
            "box_mean": round(float(box_monthly.sel(month=month).values), 4),
            "korea_land_mean": round(float(land_monthly.sel(month=month).values), 4),
            "difference_land_minus_box": round(float(diff_monthly.sel(month=month).values), 4),
            "unit": unit,
        })

    plt.figure(figsize=(9, 5))
    plt.plot(box_monthly["month"], box_monthly, marker="o", label="Box mean")
    plt.plot(land_monthly["month"], land_monthly, marker="o", label="Korea land mean")
    plt.title(f"ERA5 Box vs Korea Land Monthly Climatology: {var}")
    plt.xlabel("Month")
    plt.ylabel(f"{var} ({unit})")
    plt.xticks(range(1, 13))
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()

    out_fig = fig_dir / f"era5_box_vs_land_monthly_{var}.png"
    plt.savefig(out_fig, dpi=200)
    plt.close()

    print("Saved:", out_fig)

    plt.figure(figsize=(9, 5))
    plt.plot(diff_monthly["month"], diff_monthly, marker="o")
    plt.axhline(0, linestyle="--", linewidth=1)
    plt.title(f"ERA5 Korea Land - Box Difference: {var}")
    plt.xlabel("Month")
    plt.ylabel(f"Difference ({unit})")
    plt.xticks(range(1, 13))
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    out_fig = fig_dir / f"era5_land_minus_box_monthly_{var}.png"
    plt.savefig(out_fig, dpi=200)
    plt.close()

    print("Saved:", out_fig)

summary = pd.DataFrame(rows)
summary_file = res_dir / "era5_box_vs_land_monthly_climatology.csv"
summary.to_csv(summary_file, index=False)

print("\n===== ERA5 Box vs Korea Land Monthly Climatology =====")
print(summary.to_string(index=False))
print("\nSaved:", summary_file)

print("\nPHASE 10 ERA5 monthly land-mask comparison completed.")
