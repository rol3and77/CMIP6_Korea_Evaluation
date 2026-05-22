from pathlib import Path
import xarray as xr

tas_dir = Path("data/raw/cmip6/test/unzipped")
pr_dir = Path("data/raw/cmip6/test/pr_unzipped")
output_dir = Path("data/processed/cmip6/test")
output_dir.mkdir(parents=True, exist_ok=True)

tas_files = sorted(tas_dir.glob("tas_*.nc"))
pr_files = sorted(pr_dir.glob("pr_*.nc"))

if len(tas_files) == 0:
    raise FileNotFoundError("No tas file found.")
if len(pr_files) == 0:
    raise FileNotFoundError("No pr file found.")

tas_file = tas_files[0]
pr_file = pr_files[0]

print("Opening tas file:")
print(tas_file)

print("Opening pr file:")
print(pr_file)

ds_tas = xr.open_dataset(tas_file)
ds_pr = xr.open_dataset(pr_file)

tas = ds_tas["tas"] - 273.15
tas.name = "tas"
tas.attrs["long_name"] = "Near-Surface Air Temperature"
tas.attrs["units"] = "degC"
tas.attrs["source_variable"] = "CMIP6 tas"
tas.attrs["conversion"] = "tas = tas_original - 273.15"

pr = ds_pr["pr"] * 86400.0
pr.name = "pr"
pr.attrs["long_name"] = "Precipitation"
pr.attrs["units"] = "mm/day"
pr.attrs["source_variable"] = "CMIP6 pr"
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

ds_out.attrs["title"] = "Processed CMIP6 test monthly tas and pr data for Korea region"
ds_out.attrs["model"] = "MPI-ESM1-2-LR"
ds_out.attrs["experiment"] = "historical"
ds_out.attrs["variant_label"] = "r1i1p1f1"
ds_out.attrs["grid_label"] = "gn"
ds_out.attrs["region"] = "33-39N, 124-132E"
ds_out.attrs["period"] = "1995-01"
ds_out.attrs["temperature_unit"] = "degC"
ds_out.attrs["precipitation_unit"] = "mm/day"

output_file = output_dir / "cmip6_test_mpi_esm1_2_lr_199501_processed.nc"
ds_out.to_netcdf(output_file)

print("\nProcessed CMIP6 test file saved:")
print(output_file)

print("\n===== Processed Dataset Summary =====")
print(ds_out)

print("\n===== Units =====")
for var in ds_out.data_vars:
    print(var, ds_out[var].attrs.get("units"))

print("\n===== Time Check =====")
print("time:", ds_out["time"].values)

print("\n===== Coordinate Check =====")
print("latitude:", float(ds_out["latitude"].min()), "to", float(ds_out["latitude"].max()))
print("longitude:", float(ds_out["longitude"].min()), "to", float(ds_out["longitude"].max()))

print("\n===== Value Range Check =====")
print("tas min/max:", float(ds_out["tas"].min()), float(ds_out["tas"].max()))
print("pr min/max:", float(ds_out["pr"].min()), float(ds_out["pr"].max()))
