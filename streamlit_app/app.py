import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(
    page_title="CMIP6 Korea Climate Dashboard",
    layout="wide"
)

DATA_DIR = Path("data")

@st.cache_data
def load_data():
    metrics = pd.read_csv(DATA_DIR / "asos_7stations_vs_cmip6_models_metrics.csv")
    monthly = pd.read_csv(DATA_DIR / "asos_7stations_vs_cmip6_models_monthly_climatology.csv")
    era5_metrics = pd.read_csv(DATA_DIR / "asos_7stations_vs_era5_land_metrics.csv")
    era5_monthly = pd.read_csv(DATA_DIR / "asos_7stations_vs_era5_land_monthly_climatology.csv")
    return metrics, monthly, era5_metrics, era5_monthly

metrics, monthly, era5_metrics, era5_monthly = load_data()

box_metrics = metrics[
    metrics["comparison_type"] == "CMIP6_box_minus_ASOS_7stations"
].copy()

box_monthly = monthly[
    monthly["comparison_type"] == "CMIP6_box_minus_ASOS_7stations"
].copy()

st.title("CMIP6 한국 기후 재현성 평가 대시보드")
st.caption("1995–2014년 월자료 기준 · ASOS 7개 지점 평균 · ERA5 Korea land mean · CMIP6 historical models")

st.markdown(
    """
    본 대시보드는 CMIP6 모델이 한국 기후를 얼마나 잘 재현하는지 확인하기 위해 구성하였다.
    최종 평가는 ASOS 7개 지점 평균을 관측 기준으로 두고, CMIP6 모델의 box 평균과 비교하였다.
    """
)

st.sidebar.header("설정")

variable = st.sidebar.radio(
    "변수 선택",
    ["tas", "pr"],
    format_func=lambda x: "기온 tas (°C)" if x == "tas" else "강수 pr (mm/day)"
)

metric = st.sidebar.selectbox(
    "성능지표 선택",
    ["mean_bias", "rmse", "correlation"],
    format_func=lambda x: {
        "mean_bias": "Mean Bias",
        "rmse": "RMSE",
        "correlation": "Correlation"
    }[x]
)

unit = "°C" if variable == "tas" else "mm/day"

var_metrics = box_metrics[box_metrics["variable"] == variable].copy()
var_monthly = box_monthly[box_monthly["variable"] == variable].copy()
var_era5_monthly = era5_monthly[era5_monthly["variable"] == variable].copy()
var_era5_metrics = era5_metrics[era5_metrics["variable"] == variable].copy()

rank_df = var_metrics.copy()
rank_df["abs_bias"] = rank_df["mean_bias"].abs()
rank_df["rank_abs_bias"] = rank_df["abs_bias"].rank(method="min", ascending=True).astype(int)
rank_df["rank_rmse"] = rank_df["rmse"].rank(method="min", ascending=True).astype(int)
rank_df["rank_correlation"] = rank_df["correlation"].rank(method="min", ascending=False).astype(int)
rank_df["total_rank_score"] = (
    rank_df["rank_abs_bias"] +
    rank_df["rank_rmse"] +
    rank_df["rank_correlation"]
)
rank_df["overall_rank"] = rank_df["total_rank_score"].rank(method="min", ascending=True).astype(int)
rank_df = rank_df.sort_values(["overall_rank", "total_rank_score"])

best = rank_df.iloc[0]

col1, col2, col3, col4 = st.columns(4)

col1.metric("최종 1위 모델", best["model"])
col2.metric("Bias", f"{best['mean_bias']:.4f} {unit}")
col3.metric("RMSE", f"{best['rmse']:.4f} {unit}")
col4.metric("Correlation", f"{best['correlation']:.4f}")

st.divider()

left, right = st.columns(2)

with left:
    st.subheader(f"모델 최종 순위: {variable}")
    fig = px.bar(
        rank_df,
        x="model",
        y="overall_rank",
        text="overall_rank",
        labels={"model": "Model", "overall_rank": "Overall Rank"},
        title="낮은 순위일수록 성능이 좋음"
    )
    fig.update_yaxes(autorange="reversed", dtick=1)
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader(f"모델별 {metric}")
    fig = px.bar(
        var_metrics,
        x="model",
        y=metric,
        text=metric,
        labels={"model": "Model", metric: metric},
        title=f"{metric} by model"
    )
    if metric == "mean_bias":
        fig.add_hline(y=0, line_dash="dash")
    fig.update_traces(texttemplate="%{text:.3f}", textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

st.subheader(f"월별 Bias: CMIP6 box - ASOS 7개 지점 평균 ({variable})")

fig = go.Figure()

for model in var_monthly["model"].unique():
    sub = var_monthly[var_monthly["model"] == model].sort_values("month")
    fig.add_trace(
        go.Scatter(
            x=sub["month"],
            y=sub["difference_CMIP6_minus_ASOS"],
            mode="lines+markers",
            name=model
        )
    )

fig.add_hline(y=0, line_dash="dash")
fig.update_layout(
    xaxis_title="Month",
    yaxis_title=f"Bias ({unit})",
    xaxis=dict(tickmode="linear", tick0=1, dtick=1),
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader(f"ERA5 Korea land mean vs ASOS 7개 지점 평균 ({variable})")

c1, c2 = st.columns(2)

with c1:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=var_era5_monthly["month"],
            y=var_era5_monthly["ASOS_7stations_mean"],
            mode="lines+markers",
            name="ASOS 7-station mean"
        )
    )
    fig.add_trace(
        go.Scatter(
            x=var_era5_monthly["month"],
            y=var_era5_monthly["ERA5_Korea_land"],
            mode="lines+markers",
            name="ERA5 Korea land mean"
        )
    )
    fig.update_layout(
        title="Monthly climatology",
        xaxis_title="Month",
        yaxis_title=f"{variable} ({unit})",
        xaxis=dict(tickmode="linear", tick0=1, dtick=1),
    )
    st.plotly_chart(fig, use_container_width=True)

with c2:
    fig = px.line(
        var_era5_monthly,
        x="month",
        y="difference_ERA5_land_minus_ASOS",
        markers=True,
        title="ERA5 - ASOS monthly difference",
        labels={
            "month": "Month",
            "difference_ERA5_land_minus_ASOS": f"Difference ({unit})"
        }
    )
    fig.add_hline(y=0, line_dash="dash")
    fig.update_xaxes(tickmode="linear", tick0=1, dtick=1)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("해석 요약")

if variable == "tas":
    st.markdown(
        """
        - 기온은 모든 CMIP6 모델에서 상관계수가 높아 계절 변화 재현성이 비교적 안정적이었다.
        - ASOS 7개 지점 평균 기준으로는 MPI-ESM1-2-LR이 bias, RMSE, correlation을 종합했을 때 가장 좋은 결과를 보였다.
        - ACCESS-CM2는 여름철 음의 bias가 크게 나타나 RMSE가 상대적으로 크게 계산되었다.
        """
    )
else:
    st.markdown(
        """
        - 강수는 모든 CMIP6 모델에서 ASOS 7개 지점 평균보다 적게 모의되는 음의 bias가 나타났다.
        - 7–8월 여름철 집중강수 시기에 음의 bias가 크게 나타나 강수 재현성의 한계가 뚜렷했다.
        - MPI-ESM1-2-HR은 강수 기준에서 상대적으로 가장 좋은 순위를 보였지만, correlation 자체는 높지 않았다.
        """
    )

if not var_era5_metrics.empty:
    ref = var_era5_metrics.iloc[0]
    st.info(
        f"ERA5 land mean은 ASOS 7개 지점 평균과 비교했을 때 "
        f"{variable} correlation이 {ref['correlation']:.4f}로 높았다. "
        f"평균 bias는 {ref['mean_bias']:.4f} {unit}이다."
    )

with st.expander("모델별 평가표 보기"):
    st.dataframe(rank_df, use_container_width=True)

with st.expander("ERA5 기준 검증표 보기"):
    st.dataframe(var_era5_metrics, use_container_width=True)

st.caption("Main comparison: CMIP6 box mean - ASOS 7-station mean. CMIP6 land-mask results are treated as supplementary because of limited grid cells.")
