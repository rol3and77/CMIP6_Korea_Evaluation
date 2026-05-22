from pathlib import Path
import xarray as xr

folders = {
    "tas": Path("data/raw/cmip6/mpi_esm1_2_hr/test/tas_unzipped"),
    "pr": Path("data/raw/cmip6/mpi_esm1_2_hr/test/pr_unzipped"),
}

for var_name, folder in folders.items():
    print("\n" + "=" * 80)
    print("CHECKING:", var_name)
    print("FOLDER:", folder)

    files = sorted(folder.glob("*.nc"))
    print("Number of files:", len(files))

    for f in files:
        print("-", f.name)

    if len(files) == 0:
        raise FileNotFoundError(f"No NetCDF files found in {folder}")

    ds = xr.open_dataset(files[0])

    print("\n===== Variables =====")
    print(list(ds.data_vars))

    target = "tas" if var_name == "tas" else "pr"

    print("\n===== Target Variable Attributes =====")
    print("variable:", target)
    print("long_name:", ds[target].attrs.get("long_name"))
    print("standard_name:", ds[target].attrs.get("standard_name"))
    print("units:", ds[target].attrs.get("units"))

    print("\n===== Time Check =====")
    print("time size:", ds["time"].size)
    print("time first:", ds["time"].values[0])
    print("time last:", ds["time"].values[-1])

    print("\n===== Coordinate Check =====")
    print("lat:", float(ds["lat"].min()), "to", float(ds["lat"].max()), "size:", ds["lat"].size)
    print("lon:", float(ds["lon"].min()), "to", float(ds["lon"].max()), "size:", ds["lon"].size)
