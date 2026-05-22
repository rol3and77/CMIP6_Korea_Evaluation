from pathlib import Path
import xarray as xr

file_path = Path("data/processed/era5/era5_korea_monthly_1995_2014_processed.nc")

print("File exists:", file_path.exists())
print("File size MB:", round(file_path.stat().st_size / 1024 / 1024, 3))

ds = xr.open_dataset(file_path)

print("\n===== Dataset Summary =====")
print(ds)

print("\n===== Variables =====")
print(list(ds.data_vars))

print("\n===== Units =====")
for var in ds.data_vars:
    print(var, ":", ds[var].attrs.get("units"))

print("\n===== Time Check =====")
print("time size:", ds["time"].size)
print("time first:", ds["time"].values[0])
print("time last:", ds["time"].values[-1])

print("\n===== Coordinate Check =====")
print("latitude:", float(ds["latitude"].min()), "to", float(ds["latitude"].max()))
print("longitude:", float(ds["longitude"].min()), "to", float(ds["longitude"].max()))

print("\n===== Value Range Check =====")
print("tas min/max:", float(ds["tas"].min()), float(ds["tas"].max()))
print("pr min/max:", float(ds["pr"].min()), float(ds["pr"].max()))
