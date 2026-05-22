from pathlib import Path
import xarray as xr
import pandas as pd

files = {
    "ERA5": Path("data/processed/era5/era5_korea_monthly_1995_2014_processed.nc"),
    "CMIP6_MPI_ESM1_2_LR": Path("data/processed/cmip6/mpi_esm1_2_lr_historical_1995_2014_processed.nc"),
}

rows = []

for dataset_name, file_path in files.items():
    print(f"Opening {dataset_name}: {file_path}")

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    ds = xr.open_dataset(file_path)

    for var in ["tas", "pr"]:
        if var not in ds:
            raise KeyError(f"{var} not found in {dataset_name}")

        rows.append({
            "dataset": dataset_name,
            "variable": var,
            "units": ds[var].attrs.get("units"),
            "time_size": ds["time"].size,
            "lat_size": ds["latitude"].size,
            "lon_size": ds["longitude"].size,
            "time_first": str(ds["time"].values[0]),
            "time_last": str(ds["time"].values[-1]),
            "missing_count": int(ds[var].isnull().sum().values),
            "min": round(float(ds[var].min().values), 3),
            "mean": round(float(ds[var].mean().values), 3),
            "max": round(float(ds[var].max().values), 3),
        })

summary = pd.DataFrame(rows)

out_dir = Path("results/phase5_eda")
out_dir.mkdir(parents=True, exist_ok=True)

out_file = out_dir / "processed_data_summary.csv"
summary.to_csv(out_file, index=False)

print("\n===== PHASE 5 EDA Summary Table =====")
print(summary.to_string(index=False))

print("\nSaved to:", out_file)
