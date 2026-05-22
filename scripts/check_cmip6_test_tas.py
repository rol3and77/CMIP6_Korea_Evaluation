from pathlib import Path
import xarray as xr

folder = Path("data/raw/cmip6/test/unzipped")
files = sorted(folder.glob("*.nc"))

print("===== Found NetCDF files =====")
for f in files:
    print("-", f.name)

if len(files) == 0:
    raise FileNotFoundError("No NetCDF file found in data/raw/cmip6/test/unzipped")

for file in files:
    print("\n" + "=" * 80)
    print("FILE:", file.name)

    ds = xr.open_dataset(file)

    print("\n===== Dataset Summary =====")
    print(ds)

    print("\n===== Variables =====")
    print(list(ds.data_vars))

    print("\n===== Coordinates =====")
    print(list(ds.coords))

    print("\n===== Variable Attributes =====")
    for var in ds.data_vars:
        print(f"\n[{var}]")
        print("long_name:", ds[var].attrs.get("long_name"))
        print("standard_name:", ds[var].attrs.get("standard_name"))
        print("units:", ds[var].attrs.get("units"))

    print("\n===== Coordinate Ranges =====")
    for coord in ds.coords:
        try:
            if ds[coord].size > 0:
                print(coord, "min:", ds[coord].min().values, "max:", ds[coord].max().values, "size:", ds[coord].size)
        except Exception as e:
            print(coord, "range check skipped:", e)
