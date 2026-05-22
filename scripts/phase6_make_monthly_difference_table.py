from pathlib import Path
import pandas as pd

input_file = Path("results/phase6_baseline/monthly_climatology_spatial_mean.csv")
output_file = Path("results/phase6_baseline/monthly_climatology_difference_table.csv")

df = pd.read_csv(input_file)

wide = df.pivot_table(
    index=["variable", "month", "unit"],
    columns="dataset",
    values="value"
).reset_index()

wide["CMIP6_minus_ERA5"] = wide["CMIP6_MPI_ESM1_2_LR"] - wide["ERA5"]

wide.to_csv(output_file, index=False)

print(wide.to_string(index=False))
print("\nSaved to:", output_file)
