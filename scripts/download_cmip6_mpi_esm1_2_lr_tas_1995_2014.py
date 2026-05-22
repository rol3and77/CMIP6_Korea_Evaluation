from pathlib import Path
import cdsapi

client = cdsapi.Client()

out_dir = Path("data/raw/cmip6/mpi_esm1_2_lr/historical")
out_dir.mkdir(parents=True, exist_ok=True)

years = [str(y) for y in range(1995, 2015)]
months = [f"{m:02d}" for m in range(1, 13)]

output_file = out_dir / "tas_mpi_esm1_2_lr_historical_1995_2014.zip"

client.retrieve(
    "projections-cmip6",
    {
        "temporal_resolution": "monthly",
        "experiment": "historical",
        "variable": "near_surface_air_temperature",
        "model": "mpi_esm1_2_lr",
        "year": years,
        "month": months,
        "area": [39, 124, 33, 132],
        "format": "zip",
    },
    str(output_file),
)

print("CMIP6 tas 1995-2014 download completed.")
print("Saved to:", output_file)
