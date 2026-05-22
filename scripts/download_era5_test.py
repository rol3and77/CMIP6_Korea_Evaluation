import cdsapi
from pathlib import Path

client = cdsapi.Client()

out_dir = Path("data/raw/era5")
out_dir.mkdir(parents=True, exist_ok=True)

client.retrieve(
    "reanalysis-era5-single-levels-monthly-means",
    {
        "product_type": ["monthly_averaged_reanalysis"],
        "variable": [
            "2m_temperature",
            "total_precipitation",
        ],
        "year": ["1995"],
        "month": ["01"],
        "time": ["00:00"],
        "area": [39, 124, 33, 132],
        "data_format": "netcdf",
        "download_format": "unarchived",
    },
    str(out_dir / "era5_korea_monthly_199501.nc"),
)

print("ERA5 test download completed.")
