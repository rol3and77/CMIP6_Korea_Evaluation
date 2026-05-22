from pathlib import Path
import pandas as pd

res_dir = Path("results/phase12_final_synthesis")
res_dir.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------
# Input files
# ------------------------------------------------------------

phase11_cmip6_file = Path("results/phase11_observations/asos_7stations_vs_cmip6_models_metrics.csv")
phase11_era5_file = Path("results/phase11_observations/asos_7stations_vs_era5_land_metrics.csv")

# ------------------------------------------------------------
# Read data
# ------------------------------------------------------------

cmip6_asos = pd.read_csv(phase11_cmip6_file, encoding="utf-8-sig")
era5_asos = pd.read_csv(phase11_era5_file, encoding="utf-8-sig")

# ------------------------------------------------------------
# 1. Main CMIP6 box comparison only
# ------------------------------------------------------------

cmip6_box = cmip6_asos[
    cmip6_asos["comparison_type"] == "CMIP6_box_minus_ASOS_7stations"
].copy()

cmip6_box = cmip6_box[[
    "model",
    "variable",
    "unit",
    "mean_bias",
    "rmse",
    "correlation",
    "asos_mean",
    "model_mean",
    "lat_size",
    "lon_size",
    "total_grid_cells",
    "land_grid_cells",
]]

# Add absolute bias for ranking
cmip6_box["abs_bias"] = cmip6_box["mean_bias"].abs()

# ------------------------------------------------------------
# 2. Variable-wise ranking
#    Lower RMSE is better. Higher correlation is better.
# ------------------------------------------------------------

ranking_rows = []

for var in ["tas", "pr"]:
    sub = cmip6_box[cmip6_box["variable"] == var].copy()

    sub["rank_abs_bias"] = sub["abs_bias"].rank(method="min", ascending=True).astype(int)
    sub["rank_rmse"] = sub["rmse"].rank(method="min", ascending=True).astype(int)
    sub["rank_correlation"] = sub["correlation"].rank(method="min", ascending=False).astype(int)

    # simple total score: lower is better
    sub["total_rank_score"] = (
        sub["rank_abs_bias"] +
        sub["rank_rmse"] +
        sub["rank_correlation"]
    )

    sub["overall_rank"] = sub["total_rank_score"].rank(method="min", ascending=True).astype(int)

    ranking_rows.append(sub)

ranking = pd.concat(ranking_rows, ignore_index=True)

# ------------------------------------------------------------
# 3. ERA5 vs ASOS reference table
# ------------------------------------------------------------

era5_summary = era5_asos[[
    "variable",
    "unit",
    "mean_bias",
    "rmse",
    "correlation",
    "asos_7stations_mean",
    "era5_land_mean",
]].copy()

era5_summary["comparison"] = "ERA5_Korea_land_minus_ASOS_7stations_mean"

# ------------------------------------------------------------
# 4. Final text-friendly summary tables
# ------------------------------------------------------------

tas_rank = ranking[ranking["variable"] == "tas"].sort_values("overall_rank")
pr_rank = ranking[ranking["variable"] == "pr"].sort_values("overall_rank")

# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

cmip6_box_file = res_dir / "final_cmip6_box_vs_asos7_metrics.csv"
ranking_file = res_dir / "final_cmip6_model_ranking_by_variable.csv"
era5_file = res_dir / "final_era5_land_vs_asos7_reference.csv"
tas_rank_file = res_dir / "final_temperature_model_ranking.csv"
pr_rank_file = res_dir / "final_precipitation_model_ranking.csv"

cmip6_box.to_csv(cmip6_box_file, index=False, encoding="utf-8-sig")
ranking.to_csv(ranking_file, index=False, encoding="utf-8-sig")
era5_summary.to_csv(era5_file, index=False, encoding="utf-8-sig")
tas_rank.to_csv(tas_rank_file, index=False, encoding="utf-8-sig")
pr_rank.to_csv(pr_rank_file, index=False, encoding="utf-8-sig")

print("\n===== FINAL CMIP6 Box vs ASOS 7 Stations Metrics =====")
print(cmip6_box.to_string(index=False))

print("\n===== FINAL Temperature Model Ranking =====")
print(tas_rank[[
    "model",
    "mean_bias",
    "rmse",
    "correlation",
    "rank_abs_bias",
    "rank_rmse",
    "rank_correlation",
    "total_rank_score",
    "overall_rank",
]].to_string(index=False))

print("\n===== FINAL Precipitation Model Ranking =====")
print(pr_rank[[
    "model",
    "mean_bias",
    "rmse",
    "correlation",
    "rank_abs_bias",
    "rank_rmse",
    "rank_correlation",
    "total_rank_score",
    "overall_rank",
]].to_string(index=False))

print("\n===== FINAL ERA5 Land vs ASOS 7 Stations Reference =====")
print(era5_summary.to_string(index=False))

print("\nSaved:")
print(cmip6_box_file)
print(ranking_file)
print(era5_file)
print(tas_rank_file)
print(pr_rank_file)
