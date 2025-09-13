# app.py
import streamlit as st
import pandas as pd
import altair as alt
import os

# 페이지 기본 설정
st.set_page_config(page_title="MBTI Top 10 국가 대시보드", layout="wide")

st.title("MBTI 유형별 비율 Top 10 국가 🌍")
st.caption("기본적으로 로컬 폴더의 CSV 파일을 불러오고, 없으면 업로드한 파일을 사용합니다.")

# 기본 CSV 파일 경로
DEFAULT_FILE = "countriesMBTI_16types.csv"

# MBTI 16유형 목록
MBTI_TYPES = [
    "INTJ","INTP","ENTJ","ENTP",
    "INFJ","INFP","ENFJ","ENFP",
    "ISTJ","ISFJ","ESTJ","ESFJ",
    "ISTP","ISFP","ESTP","ESFP"
]

@st.cache_data
def load_and_prepare(file) -> pd.DataFrame:
    df = pd.read_csv(file)
    # 컬럼 정규화
    cols = {c: c.strip() for c in df.columns}
    df = df.rename(columns=cols)

    # 국가 컬럼 추론
    country_col = None
    for cand in ["Country", "country", "국가", "지역", "나라"]:
        if cand in df.columns:
            country_col = cand
            break
    if country_col is None:
        # 첫 번째 컬럼을 국가로 가정
        country_col = df.columns[0]

    # MBTI 컬럼 후보: 표준 16유형 중 존재하는 것만 사용
    mbti_cols = [c for c in df.columns if c.upper() in MBTI_TYPES]

    # 숫자화
    for c in mbti_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # 정리
    df = df[[country_col] + mbti_cols].copy()
    df = df.rename(columns={country_col: "Country"})
    return df, mbti_cols

def top10_for_type(df: pd.DataFrame, mbti_col: str) -> pd.DataFrame:
    temp = df[["Country", mbti_col]].dropna()
    temp = temp.sort_values(mbti_col, ascending=False).head(10)
    return temp

# 1) 먼저 로컬 기본 파일 시도
if os.path.exists(DEFAULT_FILE):
    df, mbti_cols = load_and_prepare(DEFAULT_FILE)
    st.success(f"✅ 로컬 파일 `{DEFAULT_FILE}` 불러옴")
else:
    # 2) 업로드 fallback
    uploaded = st.file_uploader("CSV 파일을 업로드하세요", type=["csv"])
    if uploaded:
        df, mbti_cols = load_and_prepare(uploaded)
        st.success("✅ 업로드한 CSV 파일 불러옴")
    else:
        st.warning("CSV 파일이 필요합니다. (로컬에 기본 파일이 없으니 업로드해 주세요)")
        st.stop()

# MBTI 유형 선택
default_type = mbti_cols[0] if "INFJ" not in mbti_cols else "INFJ"
selected_type = st.selectbox("MBTI 유형을 선택하세요", options=sorted(mbti_cols), index=sorted(mbti_cols).index(default_type))

# Top10 데이터
top10 = top10_for_type(df, selected_type)
top10["label"] = top10[selected_type].round(2).astype(str)

# Altair 차트
bars = alt.Chart(top10).mark_bar().encode(
    x=alt.X(f"{selected_type}:Q", title=f"{selected_type} 비율(%)"),
    y=alt.Y("Country:N", sort="-x", title="국가"),
    tooltip=[
        alt.Tooltip("Country:N", title="국가"),
        alt.Tooltip(f"{selected_type}:Q", title="비율(%)", format=".2f")
    ]
)

text = alt.Chart(top10).mark_text(align="left", dx=4).encode(
    x=alt.X(f"{selected_type}:Q"),
    y=alt.Y("Country:N", sort="-x"),
    text=alt.Text("label:N")
)

chart = (bars + text).properties(
    title=f"💡 {selected_type} 비율이 가장 높은 국가 Top 10"
)

st.altair_chart(chart, use_container_width=True)

# 데이터 미리보기
with st.expander("데이터 미리보기 (상위 20행)"):
    st.dataframe(df.head(20), use_container_width=True)
