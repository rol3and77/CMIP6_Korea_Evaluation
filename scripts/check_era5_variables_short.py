from pathlib import Path
import xarray as xr

folder = Path("data/raw/era5/test_unzipped")
files = sorted(folder.glob("*.nc"))

for file in files:
    print("\n" + "=" * 60)
    print("FILE:", file.name)

    ds = xr.open_dataset(file)

    print("VARIABLES:", list(ds.data_vars))

    for var in ds.data_vars:
        print("VAR:", var)
        print("long_name:", ds[var].attrs.get("long_name"))
        print("units:", ds[var].attrs.get("units"))
        print("GRIB_name:", ds[var].attrs.get("GRIB_name"))
        print("GRIB_stepType:", ds[var].attrs.get("GRIB_stepType"))

    print("time coord:", "valid_time" if "valid_time" in ds.coords else "time")
    if "valid_time" in ds.coords:
        print("valid_time:", ds["valid_time"].values)
    if "time" in ds.coords:
        print("time:", ds["time"].values)
