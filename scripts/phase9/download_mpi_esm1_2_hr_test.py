from pathlib import Path
import cdsapi

client = cdsapi.Client()

out_dir = Path("data/raw/cmip6/mpi_esm1_2_hr/test")
out_dir.mkdir(parents=True, exist_ok=True)

requests = [
    {
        "variable_name": "near_surface_air_temperature",
        "short_name": "tas",
        "output_file": out_dir / "mpi_esm1_2_hr_test_tas_199501.zip",
    },
    {
        "variable_name": "precipitation",
        "short_name": "pr",
        "output_file": out_dir / "mpi_esm1_2_hr_test_pr_199501.zip",
    },
]

for req in requests:
    print("\nDownloading MPI-ESM1-2-HR", req["short_name"])

    client.retrieve(
        "projections-cmip6",
        {
            "temporal_resolution": "monthly",
            "experiment": "historical",
            "variable": req["variable_name"],
            "model": "mpi_esm1_2_hr",
            "year": "1995",
            "month": "01",
            "area": [39, 124, 33, 132],
            "format": "zip",
        },
        str(req["output_file"]),
    )

    print("Saved:", req["output_file"])

print("\nMPI-ESM1-2-HR test download completed.")
