from pathlib import Path
import xarray as xr

base_dir = Path("data/raw/cmip6/mpi_esm1_2_lr/historical")

folders = {
    "tas": base_dir / "tas_unzipped",
    "pr": base_dir / "pr_unzipped",
}

for name, folder in folders.items():
    print("\n" + "=" * 80)
    print("CHECKING:", name)
    print("FOLDER:", folder)

    files = sorted(folder.glob("*.nc"))
    print("Number of files:", len(files))

    for f in files:
        print("-", f.name)

    if len(files) == 0:
        raise FileNotFoundError(f"No NetCDF files found in {folder}")

    ds = xr.open_mfdataset(files, combine="by_coords")

    print("\n===== Dataset Summary =====")
    print(ds)

    print("\n===== Variables =====")
    print(list(ds.data_vars))

    print("\n===== Coordinates =====")
    print(list(ds.coords))

    for var in ds.data_vars:
        if var in ["tas", "pr"]:
            print("\nVAR:", var)
            print("long_name:", ds[var].attrs.get("long_name"))
            print("standard_name:", ds[var].attrs.get("standard_name"))
            print("units:", ds[var].attrs.get("units"))

    print("\n===== Time Check =====")
    print("time size:", ds["time"].size)
    print("time first:", ds["time"].values[0])
    print("time last:", ds["time"].values[-1])

    print("\n===== Coordinate Check =====")
    print("lat:", float(ds["lat"].min()), "to", float(ds["lat"].max()), "size:", ds["lat"].size)
    print("lon:", float(ds["lon"].min()), "to", float(ds["lon"].max()), "size:", ds["lon"].size)
