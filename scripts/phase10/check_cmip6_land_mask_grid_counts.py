from pathlib import Path
import pandas as pd
import xarray as xr
import regionmask

model_files = {
    "MPI-ESM1-2-LR": Path("data/processed/cmip6/mpi_esm1_2_lr_historical_1995_2014_processed.nc"),
    "MPI-ESM1-2-HR": Path("data/processed/cmip6/mpi_esm1_2_hr_historical_1995_2014_processed.nc"),
    "ACCESS-CM2": Path("data/processed/cmip6/access_cm2_historical_1995_2014_processed.nc"),
    "CanESM5": Path("data/processed/cmip6/canesm5_historical_1995_2014_processed.nc"),
}

out_dir = Path("results/phase10_land_mask")
out_dir.mkdir(parents=True, exist_ok=True)

countries = regionmask.defined_regions.natural_earth_v5_0_0.countries_50
south_korea_number = 55

rows = []

for model_name, file_path in model_files.items():
    print("\n" + "=" * 80)
    print("MODEL:", model_name)
    print("FILE:", file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Missing file: {file_path}")

    ds = xr.open_dataset(file_path)

    mask = countries.mask(ds["longitude"], ds["latitude"])
    korea_mask = mask == south_korea_number

    total_grid_cells = int(korea_mask.size)
    land_grid_cells = int(korea_mask.sum().values)
    land_grid_ratio = land_grid_cells / total_grid_cells

    print("total grid cells:", total_grid_cells)
    print("south korea land grid cells:", land_grid_cells)
    print("land grid ratio:", round(land_grid_ratio, 4))

    if land_grid_cells <= 2:
        interpretation = "very_limited_not_recommended_for_main_analysis"
    elif land_grid_cells <= 5:
        interpretation = "limited_use_with_caution"
    else:
        interpretation = "usable_as_supplementary_analysis"

    rows.append({
        "model": model_name,
        "lat_size": ds["latitude"].size,
        "lon_size": ds["longitude"].size,
        "total_grid_cells": total_grid_cells,
        "south_korea_land_grid_cells": land_grid_cells,
        "land_grid_ratio": round(land_grid_ratio, 4),
        "interpretation": interpretation,
    })

summary = pd.DataFrame(rows)
out_file = out_dir / "cmip6_land_mask_grid_count_summary.csv"
summary.to_csv(out_file, index=False)

print("\n===== CMIP6 Land Mask Grid Count Summary =====")
print(summary.to_string(index=False))
print("\nSaved:", out_file)
