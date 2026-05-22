from pathlib import Path
import pandas as pd
import xarray as xr
import regionmask
import matplotlib.pyplot as plt

era5_file = Path("data/processed/era5/era5_korea_monthly_1995_2014_processed.nc")

out_dir = Path("results/phase10_land_mask")
fig_dir = Path("figures/phase10_land_mask")
out_dir.mkdir(parents=True, exist_ok=True)
fig_dir.mkdir(parents=True, exist_ok=True)

ds = xr.open_dataset(era5_file)

countries = regionmask.defined_regions.natural_earth_v5_0_0.countries_50

# 앞 단계에서 확인한 South Korea number
south_korea_number = 55

print("Selected Korea region:")
print("number:", south_korea_number)
print("name: South Korea")
print("abbrev: KR")

# regionmask는 longitude, latitude 순서로 mask 생성
mask = countries.mask(ds["longitude"], ds["latitude"])

# South Korea에 해당하는 격자만 True
korea_mask = mask == south_korea_number

valid_grid_count = int(korea_mask.sum().values)
total_grid_count = int(korea_mask.size)

print("\n===== ERA5 Korea Land Mask Check =====")
print("total grid cells:", total_grid_count)
print("korea land grid cells:", valid_grid_count)
print("land grid ratio:", round(valid_grid_count / total_grid_count, 4))

# mask 적용
ds_land = ds.where(korea_mask)

rows = []

for var in ["tas", "pr"]:
    box_mean = ds[var].mean(dim=["latitude", "longitude"])
    land_mean = ds_land[var].mean(dim=["latitude", "longitude"], skipna=True)

    rows.append({
        "dataset": "ERA5",
        "variable": var,
        "box_mean": round(float(box_mean.mean().values), 4),
        "korea_land_mean": round(float(land_mean.mean().values), 4),
        "difference_land_minus_box": round(float((land_mean.mean() - box_mean.mean()).values), 4),
        "unit": ds[var].attrs.get("units"),
        "land_grid_cells": valid_grid_count,
        "total_grid_cells": total_grid_count,
    })

summary = pd.DataFrame(rows)
summary_file = out_dir / "era5_korea_land_mask_summary.csv"
summary.to_csv(summary_file, index=False)

print("\n===== ERA5 Box vs Korea Land Mean =====")
print(summary.to_string(index=False))
print("\nSaved:", summary_file)

# mask 그림 저장
plt.figure(figsize=(7, 5))
korea_mask.plot()
plt.title("ERA5 Korea Land Mask")
plt.tight_layout()
mask_fig = fig_dir / "era5_korea_land_mask.png"
plt.savefig(mask_fig, dpi=200)
plt.close()

print("Saved figure:", mask_fig)

# mask 적용된 ERA5 저장
land_file = Path("data/processed/era5/era5_korea_land_masked_monthly_1995_2014.nc")
ds_land.to_netcdf(land_file)

print("Saved masked ERA5:", land_file)
