from pathlib import Path
import cdsapi

client = cdsapi.Client()

out_dir = Path("data/raw/cmip6/access_cm2/historical")
out_dir.mkdir(parents=True, exist_ok=True)

years = [str(y) for y in range(1995, 2015)]
months = [f"{m:02d}" for m in range(1, 13)]

requests = [
    {
        "variable_name": "near_surface_air_temperature",
        "short_name": "tas",
        "output_file": out_dir / "access_cm2_tas_historical_1995_2014.zip",
    },
    {
        "variable_name": "precipitation",
        "short_name": "pr",
        "output_file": out_dir / "access_cm2_pr_historical_1995_2014.zip",
    },
]

for req in requests:
    print("\nDownloading ACCESS-CM2", req["short_name"], "1995-2014")

    client.retrieve(
        "projections-cmip6",
        {
            "temporal_resolution": "monthly",
            "experiment": "historical",
            "variable": req["variable_name"],
            "model": "access_cm2",
            "year": years,
            "month": months,
            "area": [39, 124, 33, 132],
            "format": "zip",
        },
        str(req["output_file"]),
    )

    print("Saved:", req["output_file"])

print("\nACCESS-CM2 1995-2014 download completed.")
