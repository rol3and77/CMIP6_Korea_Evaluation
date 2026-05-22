from pathlib import Path
import xarray as xr

base_dir = Path("data/raw/cmip6/access_cm2/historical")
tas_dir = base_dir / "tas_unzipped"
pr_dir = base_dir / "pr_unzipped"

output_dir = Path("data/processed/cmip6")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "access_cm2_historical_1995_2014_processed.nc"

tas_files = sorted(tas_dir.glob("*.nc"))
pr_files = sorted(pr_dir.glob("*.nc"))

if len(tas_files) == 0:
    raise FileNotFoundError("No ACCESS-CM2 tas files found.")
if len(pr_files) == 0:
    raise FileNotFoundError("No ACCESS-CM2 pr files found.")

print("Opening ACCESS-CM2 tas file:")
for f in tas_files:
    print("-", f)

print("Opening ACCESS-CM2 pr file:")
for f in pr_files:
    print("-", f)

ds_tas = xr.open_mfdataset(tas_files, combine="by_coords")
ds_pr = xr.open_mfdataset(pr_files, combine="by_coords")

tas = ds_tas["tas"] - 273.15
tas.name = "tas"
tas.attrs["long_name"] = "Near-Surface Air Temperature"
tas.attrs["units"] = "degC"
tas.attrs["source_variable"] = "CMIP6 ACCESS-CM2 tas"
tas.attrs["conversion"] = "tas = tas_original - 273.15"

pr = ds_pr["pr"] * 86400.0
pr.name = "pr"
pr.attrs["long_name"] = "Precipitation"
pr.attrs["units"] = "mm/day"
pr.attrs["source_variable"] = "CMIP6 ACCESS-CM2 pr"
pr.attrs["conversion"] = "pr = pr_original * 86400"

tas = tas.rename({"lat": "latitude", "lon": "longitude"})
pr = pr.rename({"lat": "latitude", "lon": "longitude"})

monthly_time = tas["time"].values.astype("datetime64[M]")
tas = tas.assign_coords(time=monthly_time)
pr = pr.assign_coords(time=monthly_time)

ds_out = xr.Dataset(
    {
        "tas": tas,
        "pr": pr,
    }
)

ds_out.attrs["title"] = "Processed CMIP6 ACCESS-CM2 monthly data for Korea region"
ds_out.attrs["model"] = "ACCESS-CM2"
ds_out.attrs["experiment"] = "historical"
ds_out.attrs["variant_label"] = "r1i1p1f1"
ds_out.attrs["grid_label"] = "gn"
ds_out.attrs["region"] = "33-39N, 124-132E"
ds_out.attrs["period"] = "1995-01 to 2014-12"
ds_out.attrs["temperature_unit"] = "degC"
ds_out.attrs["precipitation_unit"] = "mm/day"

ds_out.to_netcdf(output_file)

print("\nProcessed ACCESS-CM2 file saved:")
print(output_file)

print("\n===== Dataset Summary =====")
print(ds_out)

print("\n===== Units =====")
for var in ds_out.data_vars:
    print(var, ds_out[var].attrs.get("units"))

print("\n===== Time Check =====")
print("time size:", ds_out["time"].size)
print("time first:", ds_out["time"].values[0])
print("time last:", ds_out["time"].values[-1])

print("\n===== Coordinate Check =====")
print("latitude:", float(ds_out["latitude"].min()), "to", float(ds_out["latitude"].max()), "size:", ds_out["latitude"].size)
print("longitude:", float(ds_out["longitude"].min()), "to", float(ds_out["longitude"].max()), "size:", ds_out["longitude"].size)

print("\n===== Value Range Check =====")
print("tas min/max:", float(ds_out["tas"].min()), float(ds_out["tas"].max()))
print("pr min/max:", float(ds_out["pr"].min()), float(ds_out["pr"].max()))
