import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(
    page_title="CMIP6 Korea Climate Dashboard",
    page_icon="🌦️",
    layout="wide"
)

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
STYLE_FILE = APP_DIR / "style.css"

def load_css(css_file):
    with open(css_file, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css(STYLE_FILE)

MODEL_COLORS = {
    "MPI-ESM1-2-LR": "#5B5F97",
    "MPI-ESM1-2-HR": "#5E8C7A",
    "ACCESS-CM2": "#B7795B",
    "CanESM5": "#9A6070",
}

required_files = [
    "asos_7stations_vs_cmip6_models_metrics.csv",
    "asos_7stations_vs_cmip6_models_monthly_climatology.csv",
    "asos_7stations_vs_era5_land_metrics.csv",
    "asos_7stations_vs_era5_land_monthly_climatology.csv",
]

missing = [f for f in required_files if not (DATA_DIR / f).exists()]
if missing:
    st.error("필요한 CSV 파일을 찾지 못했습니다.")
    st.write("현재 찾는 폴더:", DATA_DIR)
    st.write("누락 파일:", missing)
    st.stop()

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

st.markdown(
    """
    <div class="hero">
        <div class="hero-kicker">CMIP6 Korea Climate Evaluation · 1995–2014</div>
        <h1 class="hero-title">CMIP6는 한국 기후를 얼마나 잘 재현할까?</h1>
        <div class="hero-subtitle">
            ERA5 재분석자료와 기상청 ASOS 7개 지점 평균을 기준으로,
            CMIP6 historical 모델의 기온과 강수 재현성을 비교하였다.
            기온은 계절성을 비교적 잘 따라가지만, 여름철 강수 재현에는 한계가 확인되었다.
        </div>
        <div class="hero-actions">
            <a class="btn-primary" href="#model-section">모델 성능 보기</a>
            <a class="btn-secondary" href="#era5-section">ERA5 검증 보기</a>
        </div>
        <div class="mockup-card">
            <div class="mockup-header">
                <span>Final synthesis board</span>
                <span style="color:#667085; font-weight:500;">ASOS · ERA5 · CMIP6</span>
            </div>
            <div class="mockup-grid">
                <div class="mockup-tile" style="background:#EDE7FF;">
                    <b>Temperature</b><br/>MPI-ESM1-2-LR ranked first
                </div>
                <div class="mockup-tile" style="background:#DFF8EA;">
                    <b>Precipitation</b><br/>MPI-ESM1-2-HR ranked first
                </div>
                <div class="mockup-tile" style="background:#FFE9D6;">
                    <b>Summer rainfall</b><br/>Dry bias remains clear
                </div>
                <div class="mockup-tile" style="background:#E2F2FF;">
                    <b>Reference</b><br/>ERA5 follows ASOS seasonality
                </div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown("## 설정")

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

show_table = st.sidebar.checkbox("상세 표 보기", value=False)

unit = "°C" if variable == "tas" else "mm/day"
var_label = "기온" if variable == "tas" else "강수"

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

c1, c2, c3, c4 = st.columns(4)
c1.metric("최종 1위 모델", best["model"])
c2.metric("Mean Bias", f"{best['mean_bias']:.4f} {unit}")
c3.metric("RMSE", f"{best['rmse']:.4f} {unit}")
c4.metric("Correlation", f"{best['correlation']:.4f}")

summary_sentence = (
    "기온은 모든 모델에서 상관계수가 높아 계절 변화 재현성이 비교적 안정적이었다."
    if variable == "tas"
    else "강수는 모든 모델에서 음의 bias가 나타났으며, 특히 여름철 집중강수 재현에 한계가 확인되었다."
)

st.markdown(
    f"""
    <div class="yellow-banner">
        <h3>{var_label} 분석 요약</h3>
        <p>
        현재 선택한 변수는 <b>{variable}</b>이다.
        최종 평가는 ASOS 7개 지점 평균을 관측 기준으로 두고,
        CMIP6 모델의 box 평균과 비교하였다.
        {summary_sentence}
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown('<div id="model-section"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">모델 성능 비교</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-sub">Bias, RMSE, correlation을 이용해 CMIP6 모델의 재현성을 비교하였다. 낮은 RMSE와 높은 correlation이 좋은 성능을 의미한다.</div>',
    unsafe_allow_html=True
)

left, right = st.columns(2)

with left:
    fig = px.bar(
        rank_df,
        x="model",
        y="overall_rank",
        text="overall_rank",
        color="model",
        color_discrete_map=MODEL_COLORS,
        labels={"model": "Model", "overall_rank": "Overall rank"},
        title=f"{var_label} 모델 최종 순위"
    )
    fig.update_yaxes(autorange="reversed", dtick=1)
    fig.update_traces(textposition="outside")
    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Inter"),
        showlegend=False,
        margin=dict(l=20, r=20, t=55, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    fig = px.bar(
        var_metrics,
        x="model",
        y=metric,
        text=metric,
        color="model",
        color_discrete_map=MODEL_COLORS,
        labels={"model": "Model", metric: metric},
        title=f"모델별 {metric}"
    )
    if metric == "mean_bias":
        fig.add_hline(y=0, line_dash="dash", line_color="#667085")
    fig.update_traces(texttemplate="%{text:.3f}", textposition="outside")
    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Inter"),
        showlegend=False,
        margin=dict(l=20, r=20, t=55, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown('<div class="section-title">월별 Bias 패턴</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-sub">월별 bias는 CMIP6 box 평균에서 ASOS 7개 지점 평균을 뺀 값이다. 0보다 작으면 모델이 관측보다 낮게 모의한 것이다.</div>',
    unsafe_allow_html=True
)

fig = go.Figure()

for model in var_monthly["model"].unique():
    sub = var_monthly[var_monthly["model"] == model].sort_values("month")
    fig.add_trace(
        go.Scatter(
            x=sub["month"],
            y=sub["difference_CMIP6_minus_ASOS"],
            mode="lines+markers",
            name=model,
            line=dict(width=3, color=MODEL_COLORS.get(model)),
            marker=dict(size=7)
        )
    )

fig.add_hline(y=0, line_dash="dash", line_color="#667085")
fig.update_layout(
    xaxis_title="Month",
    yaxis_title=f"Bias ({unit})",
    xaxis=dict(tickmode="linear", tick0=1, dtick=1),
    paper_bgcolor="white",
    plot_bgcolor="white",
    font=dict(family="Inter"),
    margin=dict(l=20, r=20, t=25, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
)
st.plotly_chart(fig, use_container_width=True)

st.markdown('<div id="era5-section"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">ERA5와 ASOS 관측값 비교</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-sub">ERA5 Korea land mean이 실제 관측 기준인 ASOS 7개 지점 평균과 얼마나 가까운지 확인하였다.</div>',
    unsafe_allow_html=True
)

e1, e2 = st.columns(2)

with e1:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=var_era5_monthly["month"],
            y=var_era5_monthly["ASOS_7stations_mean"],
            mode="lines+markers",
            name="ASOS 7-station mean",
            line=dict(width=3, color="#5B5F97")
        )
    )
    fig.add_trace(
        go.Scatter(
            x=var_era5_monthly["month"],
            y=var_era5_monthly["ERA5_Korea_land"],
            mode="lines+markers",
            name="ERA5 Korea land mean",
            line=dict(width=3, color="#5E8C7A")
        )
    )
    fig.update_layout(
        title=f"{var_label} 월별 climatology",
        xaxis_title="Month",
        yaxis_title=f"{variable} ({unit})",
        xaxis=dict(tickmode="linear", tick0=1, dtick=1),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Inter"),
        margin=dict(l=20, r=20, t=55, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
    )
    st.plotly_chart(fig, use_container_width=True)

with e2:
    fig = px.line(
        var_era5_monthly,
        x="month",
        y="difference_ERA5_land_minus_ASOS",
        markers=True,
        title="ERA5 - ASOS 월별 차이",
        labels={
            "month": "Month",
            "difference_ERA5_land_minus_ASOS": f"Difference ({unit})"
        }
    )
    fig.update_traces(line=dict(width=3, color="#B7795B"), marker=dict(size=8))
    fig.add_hline(y=0, line_dash="dash", line_color="#667085")
    fig.update_xaxes(tickmode="linear", tick0=1, dtick=1)
    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Inter"),
        margin=dict(l=20, r=20, t=55, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown('<div class="section-title">해석 요약</div>', unsafe_allow_html=True)

if variable == "tas":
    st.markdown(
        """
        <div class="soft-card" style="background:#EDE7FF;">
        <span class="purple-badge">Temperature</span>
        <p style="margin:0; line-height:1.7;">
        기온은 모든 CMIP6 모델에서 상관계수가 높아 계절 변화 재현성이 비교적 안정적이었다.
        ASOS 7개 지점 평균 기준으로는 <b>MPI-ESM1-2-LR</b>이 bias, RMSE, correlation을 종합했을 때 가장 좋은 결과를 보였다.
        반면 ACCESS-CM2는 음의 bias가 크게 나타나 RMSE가 상대적으로 크게 계산되었다.
        </p>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        """
        <div class="soft-card" style="background:#FFE9D6;">
        <span class="purple-badge">Precipitation</span>
        <p style="margin:0; line-height:1.7;">
        강수는 모든 CMIP6 모델에서 ASOS 7개 지점 평균보다 적게 모의되는 음의 bias가 나타났다.
        특히 7–8월 여름철 집중강수 시기에 음의 bias가 크게 나타나 강수 재현성의 한계가 뚜렷했다.
        MPI-ESM1-2-HR은 강수 기준에서 상대적으로 가장 좋은 순위를 보였지만, correlation 자체는 높지 않았다.
        </p>
        </div>
        """,
        unsafe_allow_html=True
    )

if not var_era5_metrics.empty:
    ref = var_era5_metrics.iloc[0]
    st.info(
        f"ERA5 land mean은 ASOS 7개 지점 평균과 비교했을 때 "
        f"{variable} correlation이 {ref['correlation']:.4f}로 높았다. "
        f"평균 bias는 {ref['mean_bias']:.4f} {unit}이다."
    )

if show_table:
    st.markdown("### 모델별 평가표")
    st.dataframe(rank_df, use_container_width=True)

    st.markdown("### ERA5 기준 검증표")
    st.dataframe(var_era5_metrics, use_container_width=True)

st.caption(
    "Main comparison: CMIP6 box mean - ASOS 7-station mean. "
    "CMIP6 land-mask results are supplementary because the number of land grid cells is limited."
)
