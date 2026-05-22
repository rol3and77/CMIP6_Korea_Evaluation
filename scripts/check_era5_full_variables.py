from pathlib import Path
import xarray as xr

folder = Path("data/raw/era5/monthly_1995_2014/unzipped")
files = sorted(folder.glob("*.nc"))

print("Found files:")
for f in files:
    print("-", f.name)

for file in files:
    print("\n" + "=" * 70)
    print("FILE:", file.name)

    ds = xr.open_dataset(file)

    print("VARIABLES:", list(ds.data_vars))
    print("COORDS:", list(ds.coords))

    for var in ds.data_vars:
        print("VAR:", var)
        print("long_name:", ds[var].attrs.get("long_name"))
        print("units:", ds[var].attrs.get("units"))
        print("GRIB_name:", ds[var].attrs.get("GRIB_name"))
        print("GRIB_stepType:", ds[var].attrs.get("GRIB_stepType"))

    time_name = "valid_time" if "valid_time" in ds.coords else "time"
    print("time_name:", time_name)
    print("time size:", ds[time_name].size)
    print("time first:", ds[time_name].values[0])
    print("time last:", ds[time_name].values[-1])
    print("latitude range:", float(ds["latitude"].min()), float(ds["latitude"].max()))
    print("longitude range:", float(ds["longitude"].min()), float(ds["longitude"].max()))
