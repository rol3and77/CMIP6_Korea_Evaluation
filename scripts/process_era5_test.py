from pathlib import Path
import xarray as xr

input_dir = Path("data/raw/era5/test_unzipped")
output_dir = Path("data/processed/era5")
output_dir.mkdir(parents=True, exist_ok=True)

t2m_file = input_dir / "data_stream-moda_stepType-avgua.nc"
tp_file = input_dir / "data_stream-moda_stepType-avgad.nc"

ds_t = xr.open_dataset(t2m_file)
ds_p = xr.open_dataset(tp_file)

# Rename valid_time to time for easier later analysis
ds_t = ds_t.rename({"valid_time": "time"})
ds_p = ds_p.rename({"valid_time": "time"})

# Convert units
tas_c = ds_t["t2m"] - 273.15
tas_c.name = "tas"
tas_c.attrs["long_name"] = "2 metre temperature"
tas_c.attrs["units"] = "degC"
tas_c.attrs["source_variable"] = "ERA5 t2m"

pr_mm_day = ds_p["tp"] * 1000.0
pr_mm_day.name = "pr"
pr_mm_day.attrs["long_name"] = "total precipitation"
pr_mm_day.attrs["units"] = "mm/day"
pr_mm_day.attrs["source_variable"] = "ERA5 tp"
pr_mm_day.attrs["note"] = "ERA5 monthly averaged total precipitation with stepType avgad converted from m to mm/day"

# Align time coordinate to monthly timestamp.
# ERA5 t2m and tp have slightly different valid_time hours.
# For monthly climate analysis, we use month start as common timestamp.
tas_c = tas_c.assign_coords(time=[ds_t["time"].values[0].astype("datetime64[M]")])
pr_mm_day = pr_mm_day.assign_coords(time=[ds_t["time"].values[0].astype("datetime64[M]")])

ds_out = xr.Dataset(
    {
        "tas": tas_c,
        "pr": pr_mm_day,
    }
)

ds_out.attrs["title"] = "Processed ERA5 monthly test data for Korea region"
ds_out.attrs["region"] = "33-39N, 124-132E"
ds_out.attrs["period"] = "1995-01"
ds_out.attrs["temperature_unit"] = "degC"
ds_out.attrs["precipitation_unit"] = "mm/day"

output_file = output_dir / "era5_korea_monthly_199501_processed.nc"
ds_out.to_netcdf(output_file)

print("Processed ERA5 test file saved:")
print(output_file)
print(ds_out)
