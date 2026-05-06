import streamlit as st
import pandas as pd
import sqlite3
import os
import plotly.express as px
import pydeck as pdk

# 1. 페이지 설정 및 데이터베이스 확인
st.set_page_config(page_title="서울시 따릉이 자전거 공공데이터 분석 대시보드", layout="wide")

DB_FILE = "bicycle.db"

def check_db():
    if not os.path.exists(DB_FILE):
        st.error(f"🚨 '{DB_FILE}' 파일을 찾을 수 없습니다. 데이터베이스 파일이 같은 폴더에 있는지 확인해주세요!")
        st.stop()

check_db()

# 데이터베이스 연결 함수
def run_query(query):
    with sqlite3.connect(DB_FILE) as conn:
        return pd.read_sql_query(query, conn)

# 헤더 부분
st.title("🚲 서울시 따릉이 공공데이터 분석 대시보드")
st.markdown("이 대시보드는 SQLite에 저장된 따릉이 이용 데이터를 실시간으로 분석합니다.")

# --- 차트 1: 자치구별 따릉이 사용 빈도 (점밀도 지도) ---
st.header("1. 자치구별 대여소 분포 및 이용 빈도")

query1 = """
SELECT 
    s.보관소명, s.위도, s.경도, s.자치구,
    SUM(i.이용건수) as 총이용건수
FROM 대여소 s
JOIN 이용정보 i ON s.대여소번호 = i.대여소번호
GROUP BY s.대여소번호
"""
df1 = run_query(query1)

# 지도 시각화 (Pydeck 사용)
st.pydeck_chart(pdk.Deck(
    map_style='mapbox://styles/mapbox/light-v9',
    initial_view_state=pdk.ViewState(
        latitude=df1['위도'].mean(),
        longitude=df1['경도'].mean(),
        zoom=10,
        pitch=50,
    ),
    layers=[
        pdk.Layer(
            'ScatterplotLayer',
            data=df1,
            get_position='[경도, 위도]',
            get_color='[200, 30, 0, 160]',
            get_radius='총이용건수',
            radius_scale=0.05,
            pickable=True,
        ),
    ],
))

with st.expander("🔍 SQL 및 인사이트 보기"):
    st.code(query1, language='sql')
    st.write("- **인사이트**: 강남구, 송파구 등 업무지구와 주거지가 밀집한 지역에 대여소가 집중되어 있으며 이용률이 높습니다.")
    st.write("- 점의 크기가 클수록 해당 대여소의 이용 빈도가 높음을 의미합니다.")

st.divider()

# --- 차트 2: 나이대별 이용건수 (막대 그래프) ---
st.header("2. 나이대별 이용건수 비교")

query2 = """
SELECT 연령대코드, SUM(이용건수) as 총이용건수
FROM 이용정보
GROUP BY 연령대코드
ORDER BY 연령대코드
"""
df2 = run_query(query2)

fig2 = px.bar(df2, x='연령대코드', y='총이용건수', 
             color='총이용건수', labels={'총이용건수':'이용 건수'},
             color_continuous_scale='Viridis')
st.plotly_chart(fig2, use_container_width=True)

with st.expander("🔍 SQL 및 인사이트 보기"):
    st.code(query2, language='sql')
    st.write("- **인사이트**: 20대와 30대의 이용률이 압도적으로 높으며, 이는 따릉이가 젊은 층의 주요 이동 수단임을 보여줍니다.")
    st.write("- 시니어 계층(60대 이상)의 이용량은 상대적으로 낮아, 디지털 접근성 개선이 필요할 수 있습니다.")

st.divider()

# --- 차트 3: 사용권 종류별 비율 (원형 그래프) ---
st.header("3. 사용권 종류별 이용 비중")

query3 = """
SELECT 대여구분코드, SUM(이용건수) as 총이용건수
FROM 이용정보
WHERE 대여구분코드 IN ('일일권', '정기권', '단체권')
GROUP BY 대여구분코드
"""
df3 = run_query(query3)

fig3 = px.pie(df3, values='총이용건수', names='대여구분코드', 
             hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
st.plotly_chart(fig3, use_container_width=True)

with st.expander("🔍 SQL 및 인사이트 보기"):
    st.code(query3, language='sql')
    st.write("- **인사이트**: '정기권' 이용자 비중이 높다면 출퇴근 등 고정적인 수요가 많다는 것을 의미합니다.")
    st.write("- '일일권'은 주말이나 공원 근처 대여소에서 발생하는 경향이 있습니다.")

st.caption("데이터 출처: 서울특별시 공공자전거 이용정보")
