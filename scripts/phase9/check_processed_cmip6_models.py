from pathlib import Path
import xarray as xr
import pandas as pd

model_files = {
    "MPI-ESM1-2-LR": Path("data/processed/cmip6/mpi_esm1_2_lr_historical_1995_2014_processed.nc"),
    "ACCESS-CM2": Path("data/processed/cmip6/access_cm2_historical_1995_2014_processed.nc"),
    "CanESM5": Path("data/processed/cmip6/canesm5_historical_1995_2014_processed.nc"),
}

rows = []

for model_name, file_path in model_files.items():
    if not file_path.exists():
        raise FileNotFoundError(f"Missing file: {file_path}")

    ds = xr.open_dataset(file_path)

    for var in ["tas", "pr"]:
        rows.append({
            "model": model_name,
            "variable": var,
            "unit": ds[var].attrs.get("units"),
            "time_size": ds["time"].size,
            "time_first": str(ds["time"].values[0]),
            "time_last": str(ds["time"].values[-1]),
            "lat_size": ds["latitude"].size,
            "lon_size": ds["longitude"].size,
            "missing_count": int(ds[var].isnull().sum().values),
            "min": round(float(ds[var].min().values), 3),
            "mean": round(float(ds[var].mean().values), 3),
            "max": round(float(ds[var].max().values), 3),
        })

summary = pd.DataFrame(rows)

out_dir = Path("results/phase9_model_expansion")
out_dir.mkdir(parents=True, exist_ok=True)

out_file = out_dir / "processed_cmip6_model_summary.csv"
summary.to_csv(out_file, index=False)

print("\n===== PHASE 9 Processed CMIP6 Model Summary =====")
print(summary.to_string(index=False))

print("\nSaved to:", out_file)
