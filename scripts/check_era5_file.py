from pathlib import Path
import xarray as xr

file_path = Path("data/raw/era5/era5_korea_monthly_199501.nc")

print("File exists:", file_path.exists())
print("File size:", file_path.stat().st_size / 1024, "KB")

ds = xr.open_dataset(file_path)

print("\n===== Dataset Summary =====")
print(ds)

print("\n===== Variables =====")
print(list(ds.data_vars))

print("\n===== Coordinates =====")
print(list(ds.coords))

print("\n===== Variable Attributes =====")
for var in ds.data_vars:
    print(f"\n[{var}]")
    print(ds[var].attrs)

print("\n===== Coordinate Ranges =====")
for coord in ds.coords:
    try:
        print(coord, "min:", ds[coord].min().values, "max:", ds[coord].max().values)
    except Exception as e:
        print(coord, "range check skipped:", e)
