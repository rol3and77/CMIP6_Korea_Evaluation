from pathlib import Path
import xarray as xr

input_dir = Path("data/raw/cmip6/test/unzipped")
output_dir = Path("data/processed/cmip6/test")
output_dir.mkdir(parents=True, exist_ok=True)

files = sorted(input_dir.glob("tas_*.nc"))

if len(files) == 0:
    raise FileNotFoundError("No CMIP6 tas NetCDF file found.")

input_file = files[0]
output_file = output_dir / "cmip6_test_tas_mpi_esm1_2_lr_199501_processed.nc"

print("Opening CMIP6 test file:")
print(input_file)

ds = xr.open_dataset(input_file)

# Convert Kelvin to Celsius
tas = ds["tas"] - 273.15
tas.name = "tas"
tas.attrs["long_name"] = "Near-Surface Air Temperature"
tas.attrs["units"] = "degC"
tas.attrs["source_variable"] = "CMIP6 tas"
tas.attrs["conversion"] = "tas = original tas - 273.15"

# Rename coordinates to match ERA5 naming convention
tas = tas.rename({"lat": "latitude", "lon": "longitude"})

# Align monthly time to month-start timestamp
monthly_time = tas["time"].values.astype("datetime64[M]")
tas = tas.assign_coords(time=monthly_time)

ds_out = xr.Dataset({"tas": tas})

ds_out.attrs["title"] = "Processed CMIP6 test monthly tas data for Korea region"
ds_out.attrs["model"] = "MPI-ESM1-2-LR"
ds_out.attrs["experiment"] = "historical"
ds_out.attrs["variant_label"] = "r1i1p1f1"
ds_out.attrs["grid_label"] = "gn"
ds_out.attrs["region"] = "33-39N, 124-132E"
ds_out.attrs["period"] = "1995-01"
ds_out.attrs["temperature_unit"] = "degC"

ds_out.to_netcdf(output_file)

print("\nProcessed CMIP6 test file saved:")
print(output_file)

print("\n===== Processed Dataset Summary =====")
print(ds_out)

print("\n===== Unit Check =====")
print("tas units:", ds_out["tas"].attrs.get("units"))

print("\n===== Time Check =====")
print("time:", ds_out["time"].values)

print("\n===== Coordinate Check =====")
print("latitude:", float(ds_out["latitude"].min()), "to", float(ds_out["latitude"].max()))
print("longitude:", float(ds_out["longitude"].min()), "to", float(ds_out["longitude"].max()))

print("\n===== Value Range Check =====")
print("tas min/max:", float(ds_out["tas"].min()), float(ds_out["tas"].max()))
