from pathlib import Path
import cdsapi

client = cdsapi.Client()

out_dir = Path("data/raw/cmip6/test")
out_dir.mkdir(parents=True, exist_ok=True)

output_file = out_dir / "cmip6_test_pr_mpi_esm1_2_lr_199501.zip"

client.retrieve(
    "projections-cmip6",
    {
        "temporal_resolution": "monthly",
        "experiment": "historical",
        "variable": "precipitation",
        "model": "mpi_esm1_2_lr",
        "year": "1995",
        "month": "01",
        "area": [39, 124, 33, 132],
        "format": "zip",
    },
    str(output_file),
)

print("CMIP6 pr test download completed.")
print("Saved to:", output_file)
