from pathlib import Path
import xarray as xr
import numpy as np

files = {
    "ERA5": Path("data/processed/era5/era5_korea_monthly_1995_2014_processed.nc"),
    "CMIP6_MPI_ESM1_2_LR": Path("data/processed/cmip6/mpi_esm1_2_lr_historical_1995_2014_processed.nc"),
}

for name, file_path in files.items():
    print("\n" + "=" * 90)
    print(f"DATASET: {name}")
    print(f"FILE: {file_path}")
    print("=" * 90)

    print("File exists:", file_path.exists())

    if not file_path.exists():
        print("ERROR: file not found.")
        continue

    print("File size MB:", round(file_path.stat().st_size / 1024 / 1024, 3))

    ds = xr.open_dataset(file_path)

    print("\n===== Dataset Summary =====")
    print(ds)

    print("\n===== Dimensions =====")
    for dim, size in ds.sizes.items():
        print(f"{dim}: {size}")

    print("\n===== Coordinates =====")
    print(list(ds.coords))

    print("\n===== Variables and Units =====")
    for var in ds.data_vars:
        print(f"{var}: units = {ds[var].attrs.get('units')}")

    print("\n===== Time Check =====")
    print("time size:", ds["time"].size)
    print("time first:", ds["time"].values[0])
    print("time last:", ds["time"].values[-1])

    print("\n===== Coordinate Range Check =====")
    lat_name = "latitude"
    lon_name = "longitude"

    print("latitude min/max:", float(ds[lat_name].min()), float(ds[lat_name].max()))
    print("longitude min/max:", float(ds[lon_name].min()), float(ds[lon_name].max()))

    print("\n===== Missing Value Check =====")
    for var in ["tas", "pr"]:
        if var in ds:
            missing_count = int(ds[var].isnull().sum().values)
            total_count = ds[var].size
            missing_ratio = missing_count / total_count
            print(f"{var}: missing_count = {missing_count}, missing_ratio = {missing_ratio:.6f}")

    print("\n===== Value Range Check =====")
    for var in ["tas", "pr"]:
        if var in ds:
            vmin = float(ds[var].min().values)
            vmax = float(ds[var].max().values)
            vmean = float(ds[var].mean().values)
            print(f"{var}: min = {vmin:.3f}, mean = {vmean:.3f}, max = {vmax:.3f}")

    print("\n===== Monthly Count Check =====")
    month_counts = ds["time"].dt.month.to_series().value_counts().sort_index()
    print(month_counts)

print("\nPHASE 5 processed data check completed.")
