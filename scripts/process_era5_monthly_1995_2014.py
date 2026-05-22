from pathlib import Path
import xarray as xr

input_dir = Path("data/raw/era5/monthly_1995_2014/unzipped")
output_dir = Path("data/processed/era5")
output_dir.mkdir(parents=True, exist_ok=True)

t2m_file = input_dir / "data_stream-moda_stepType-avgua.nc"
tp_file = input_dir / "data_stream-moda_stepType-avgad.nc"

output_file = output_dir / "era5_korea_monthly_1995_2014_processed.nc"

print("Opening ERA5 temperature file:")
print(t2m_file)

print("Opening ERA5 precipitation file:")
print(tp_file)

ds_t = xr.open_dataset(t2m_file)
ds_p = xr.open_dataset(tp_file)

ds_t = ds_t.rename({"valid_time": "time"})
ds_p = ds_p.rename({"valid_time": "time"})

tas = ds_t["t2m"] - 273.15
tas.name = "tas"
tas.attrs["long_name"] = "2 metre temperature"
tas.attrs["units"] = "degC"
tas.attrs["source_variable"] = "ERA5 t2m"
tas.attrs["conversion"] = "tas = t2m - 273.15"

pr = ds_p["tp"] * 1000.0
pr.name = "pr"
pr.attrs["long_name"] = "total precipitation"
pr.attrs["units"] = "mm/day"
pr.attrs["source_variable"] = "ERA5 tp"
pr.attrs["conversion"] = "pr = tp * 1000"
pr.attrs["note"] = "ERA5 monthly averaged total precipitation with stepType avgad converted from m to mm/day"

# ERA5 t2m and tp have different valid_time hours.
# For monthly climate analysis, both are aligned to month-start timestamps.
monthly_time = tas["time"].values.astype("datetime64[M]")
tas = tas.assign_coords(time=monthly_time)
pr = pr.assign_coords(time=monthly_time)

ds_out = xr.Dataset(
    {
        "tas": tas,
        "pr": pr,
    }
)

ds_out.attrs["title"] = "Processed ERA5 monthly data for Korea region"
ds_out.attrs["source"] = "ERA5 monthly averaged single levels"
ds_out.attrs["region"] = "33-39N, 124-132E"
ds_out.attrs["period"] = "1995-01 to 2014-12"
ds_out.attrs["temperature_unit"] = "degC"
ds_out.attrs["precipitation_unit"] = "mm/day"
ds_out.attrs["processing_note"] = "Original t2m and tp files were separated after CDS zip download and merged after unit conversion."

ds_out.to_netcdf(output_file)

print("\nProcessed ERA5 monthly file saved:")
print(output_file)

print("\n===== Processed Dataset Summary =====")
print(ds_out)

print("\n===== Variable Units =====")
for var in ds_out.data_vars:
    print(var, ds_out[var].attrs.get("units"))

print("\n===== Time Check =====")
print("time size:", ds_out["time"].size)
print("time first:", ds_out["time"].values[0])
print("time last:", ds_out["time"].values[-1])

print("\n===== Coordinate Check =====")
print("latitude min/max:", float(ds_out["latitude"].min()), float(ds_out["latitude"].max()))
print("longitude min/max:", float(ds_out["longitude"].min()), float(ds_out["longitude"].max()))
