import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="동네별 인구 피라미드", page_icon="👨‍👩‍👧‍👦", layout="centered"
)


# 1. 데이터 불러오기 (캐싱 적용)
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/swan153/population/main/population_ts_yearly_gender.zip"
    df = pd.read_csv(url)

    # 가장 최신 연도 데이터만 추출
    max_year = df["연도"].max()
    latest_df = df[df["연도"] == max_year].copy()
    return latest_df, max_year


# 데이터 로드
try:
    df, latest_year = load_data()
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# 헤더 영역 작성
st.title("👨‍👩‍👧‍👦 우리 동네 인구 피라미드")
st.write(
    f"가장 최근 데이터인 **{latest_year}년** 기준 전국 읍·면·동 인구구조를 확인해 보세요."
)
st.markdown("---")

# 2. 지역 선택 드롭다운 (시도 -> 시군구 -> 동)
col1, col2, col3 = st.columns(3)

with col1:
    sido_list = sorted(df["시도"].dropna().unique())
    selected_sido = st.selectbox("1. 시·도 선택", sido_list)

sigungu_df = df[df["시도"] == selected_sido]
with col2:
    sigungu_list = sorted(sigungu_df["시군구"].dropna().unique())
    selected_sigungu = st.selectbox("2. 시·군·구 선택", sigungu_list)

dong_df = sigungu_df[sigungu_df["시군구"] == selected_sigungu]
with col3:
    dong_list = sorted(dong_df["동"].dropna().unique())
    selected_dong = st.selectbox("3. 읍·면·동 선택", dong_list)

# 3. 선택한 동네 데이터 필터링 및 데이터 가공
target_data = dong_df[dong_df["동"] == selected_dong]

if not target_data.empty:
    row = target_data.iloc[0]

    # 나이 라벨 (0세 ~ 100세 이상)
    age_labels = [f"{i}세" for i in range(100)] + ["100세 이상"]

    # 연령별 인구 및 나이 숫자로 분리 (지표 계산용)
    male_pop = [int(row[f"남_{age}"]) for age in age_labels]
    female_pop = [int(row[f"여_{age}"]) for age in age_labels]
    total_pop_by_age = [m + f for m, f in zip(male_pop, female_pop)]

    # 주요 지표 계산
    total_pop = sum(total_pop_by_age)

    if total_pop > 0:
        # 평균연령 계산 (100세 이상은 100세로 계산)
        ages = list(range(100)) + [100]
        weighted_sum = sum(age * pop for age, pop in zip(ages, total_pop_by_age))
        avg_age = weighted_sum / total_pop

        # 고령화율 (65세 이상 비율) 계산
        elderly_pop = sum(total_pop_by_age[65:])
        aging_rate = (elderly_pop / total_pop) * 100

        # 유소년 (0~14세) 비율 계산 (한 줄 설명용)
        youth_pop = sum(total_pop_by_age[:15])
        youth_rate = (youth_pop / total_pop) * 100
    else:
        avg_age = 0
        aging_rate = 0
        youth_rate = 0

    # 4. 상단 지표 카드 3개 나란히 배치
    m_col1, m_col2, m_col3 = st.columns(3)

    m_col1.metric("총인구", f"{total_pop:,} 명")
    m_col2.metric("평균연령", f"{avg_age:.1f} 세")

    # 고령화율 20% 이상이면 주의 표시(⚠️ 초고령) 추가
    aging_label = "고령화율 (65세+)"
    if aging_rate >= 20.0:
        aging_label += " ⚠️ 초고령"

    m_col3.metric(aging_label, f"{aging_rate:.1f} %")

    st.write("")  # 여백

    # 5. Plotly 가로 막대그래프 (인구 피라미드)
    male_pop_neg = [-val for val in male_pop]

    fig = go.Figure()

    # 남성 막대 (좌측, 주황 계열)
    fig.add_trace(
        go.Bar(
            y=age_labels,
            x=male_pop_neg,
            name="남성",
            orientation="h",
            marker=dict(color="#FF8C42"),
            customdata=male_pop,
            hovertemplate="<b>%{y}</b> 남성: %{customdata:,}명<extra></extra>",
        )
    )

    # 여성 막대 (우측, 따뜻한 로즈 계열)
    fig.add_trace(
        go.Bar(
            y=age_labels,
            x=female_pop,
            name="여성",
            orientation="h",
            marker=dict(color="#E85D75"),
            hovertemplate="<b>%{y}</b> 여성: %{x:,}명<extra></extra>",
        )
    )

    # 그래프 레이아웃 및 축 설정 (0세 맨 아래, 100세 이상 맨 위)
    fig.update_layout(
        title=dict(
            text=f"<b>{selected_sido} {selected_sigungu} {selected_dong}</b> 인구 피라미드",
            font=dict(size=18, color="#333333"),
        ),
        barmode="overlay",
        bargap=0.1,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),
        margin=dict(l=60, r=40, t=80, b=40),
        xaxis=dict(
            title="인구수 (명)",
            zeroline=True,
            zerolinecolor="#CCCCCC",
        ),
        yaxis=dict(
            title="나이",
            type="category",
            categoryorder="array",
            categoryarray=age_labels,  # 0세부터 100세 이상까지 순서 고정
            dtick=10,
        ),
        height=700,
        paper_bgcolor="white",
        plot_bgcolor="#FAFAFA",
    )

    # 피라미드 시각화 출력
    st.plotly_chart(fig, use_container_width=True)

    # 6. 피라미드 하단 한 줄 자동 설명
    st.markdown("---")
    if aging_rate >= 20.0 and youth_rate < 10.0:
        summary_text = f"👵👴 **{selected_dong}**은 어르신(65세 이상 {aging_rate:.1f}%) 비율이 눈에 띄게 높고, 아이들 비율은 낮아 고령화
