from pathlib import Path
import cdsapi

client = cdsapi.Client()

out_dir = Path("data/raw/era5/monthly_1995_2014")
out_dir.mkdir(parents=True, exist_ok=True)

years = [str(y) for y in range(1995, 2015)]
months = [f"{m:02d}" for m in range(1, 13)]

output_file = out_dir / "era5_korea_monthly_1995_2014.zip"

client.retrieve(
    "reanalysis-era5-single-levels-monthly-means",
    {
        "product_type": ["monthly_averaged_reanalysis"],
        "variable": [
            "2m_temperature",
            "total_precipitation",
        ],
        "year": years,
        "month": months,
        "time": ["00:00"],
        "area": [39, 124, 33, 132],
        "data_format": "netcdf",
        "download_format": "zip",
    },
    str(output_file),
)

print("ERA5 monthly 1995-2014 download completed.")
print("Saved to:", output_file)
