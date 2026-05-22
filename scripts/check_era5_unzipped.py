from pathlib import Path
import xarray as xr

unzipped_dir = Path("data/raw/era5/test_unzipped")
nc_files = sorted(unzipped_dir.glob("*.nc"))

print("===== Found NetCDF files =====")
for f in nc_files:
    print("-", f)

if len(nc_files) == 0:
    raise FileNotFoundError("No .nc files found.")

for file_path in nc_files:
    print("\n" + "=" * 80)
    print("Opening file:", file_path)
    print("File size:", round(file_path.stat().st_size / 1024, 2), "KB")

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
