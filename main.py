import streamlit as st
import pandas as pd
import pydeck as pdk
from supabase import create_client, Client
from datetime import datetime
import plotly.express as px

# Supabase credentials
SUPABASE_URL = "https://ktboeghkrvogwfjdpmol.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt0Ym9lZ2hrcnZvZ3dmamRwbW9sIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkxMTc4OTEsImV4cCI6MjA2NDY5Mzg5MX0.K_mdg6UlkLfnX_7bnxERQtPdsmcOd3MG5QtXKGUCO-U"

CENTER_LAT, CENTER_LON = 22.6268, 120.5646

hotspot_pairs = [
    "壽比路", "和成巷", "廣濟路", "光明路", "科大路二段", "大同路三段",
    "壽比路623巷", "學府路", "南寧路", "平昌街", "壽比路746巷", "勝利路",
    "學人路", "四維路", "復興路", "屏光路"
]

uncontrolled_spots = [
    "南寧路", "民善路口", "南華路", "南華路186巷口", "新東路", "瀧觀巷口",
    "樹新路", "北寧路二段路口", "原勝路", "原勝路4巷口", "中林路422巷", "聯通街口"
]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data
def load_data(table_name, year):
    response = supabase.table(table_name).select("*").execute()
    df = pd.DataFrame(response.data)
    if df.empty:
        return pd.DataFrame()

    rename_map = {
        "111acidents": {
            "occurred_date 111": "date",
            "occurred_time 111": "time",
            "location_text 111": "location_text",
            "dead_count 111": "dead_count",
            "injured_count 111": "injured_count",
            "longitude111": "longitude",
            "latitude111": "latitude",
            "weather": "weather",
            "light_condition": "light"
        },
        "111uncontrolled_accidents": {
            "occurred_at 11": "occurred_at",
            "location_text 11": "location_text",
            "dead_count 11": "dead_count",
            "injured_count 11": "injured_count",
            "longitude11": "longitude",
            "latitude11": "latitude",
            "weather 1": "weather",
            "light_condition 1": "light"
        },
        "112accidents": {
            "occurred_at 112": "occurred_at",
            "occurred_time 112": "time",
            "location_text 112": "location_text",
            "dead_count 112": "dead_count",
            "injured_count 112": "injured_count",
            "longitude112": "longitude",
            "latitude112": "latitude",
            "weather 2": "weather",
            "light_condition 2": "light"
        },
        "112uncontrolled_accidents": {
            "occurred_at 12": "occurred_at",
            "occurred_time 12": "time",
            "location_text 12": "location_text",
            "dead_count 12": "dead_count",
            "injured_count 12": "injured_count",
            "longitude12": "longitude",
            "latitude12": "latitude",
            "weather 3": "weather",
            "light_condition 3": "light"
        },
        "accidents": {
            "occurred_at": "occurred_at",
            "location_text": "location_text",
            "dead_count": "dead_count",
            "injured_count": "injured_count",
            "longitude": "longitude",
            "latitude": "latitude"
        },
        "uncontrolled_accidents": {
            "occurred_at1": "occurred_at",
            "location_text1": "location_text",
            "dead_count1": "dead_count",
            "injured_count1": "injured_count",
            "longitude1": "longitude",
            "latitude1": "latitude"
        }
    }

    if table_name in rename_map:
        df = df.rename(columns=rename_map[table_name])
        if "date" in df.columns and "time" in df.columns:
            df["occurred_at"] = pd.to_datetime(df["date"].astype(str) + " " + df["time"].astype(str), errors="coerce")
        elif "occurred_at" in df.columns:
            df["occurred_at"] = pd.to_datetime(df["occurred_at"], errors="coerce")

    if "occurred_at" not in df.columns or "location_text" not in df.columns:
        st.error("⚠ 資料表缺少必要欄位（occurred_at 或 location_text）")
        return pd.DataFrame()

    df = df.dropna(subset=["occurred_at"])
    df["month"] = df["occurred_at"].dt.strftime("%Y-%m")
    df["hour"] = df["occurred_at"].dt.hour
    df["time_period"] = pd.cut(df["hour"], bins=[0, 12, 18, 24], labels=["上午", "下午", "晚上"], include_lowest=True)
    return df

def classify_location(location, hotspot_list):
    for item in hotspot_list:
        if item in location:
            return item
    return "其他"

st.sidebar.title("功能選單")
page = st.sidebar.radio("請選擇分析類型", ["📍 十大肇事路口", "🚫 無號誌道路"])
year = st.sidebar.radio("選擇年度", ["110", "111", "112"])

if page == "📍 十大肇事路口":
    st.title(f"📍 {year} 年十大肇事路口事故分析")
    table_name = {
        "110": "accidents",
        "111": "111acidents",
        "112": "112accidents"
    }.get(year, "accidents")
    data = load_data(table_name, year)

    if data.empty or "location_text" not in data.columns:
        st.error("無法載入資料，請確認 Supabase 資料表")
        st.stop()

    data["hotspot"] = data["location_text"].apply(lambda x: classify_location(x, hotspot_pairs))
    filtered = data[data["hotspot"] != "其他"]

    st.subheader("📅 每月事故數量")
    st.line_chart(filtered["month"].value_counts().sort_index())

    st.subheader("🕒 時段事故分布")
    st.bar_chart(filtered["time_period"].value_counts().sort_index())

    st.subheader("🔥 熱點事故次數")
    st.bar_chart(filtered["hotspot"].value_counts())

    st.subheader("☁️ 天氣條件事故分布")
    if "weather" in filtered.columns:
        st.plotly_chart(px.pie(filtered, names="weather", title="天氣條件分布"))

    st.subheader("💡 光線狀況事故分布")
    if "light" in filtered.columns:
        st.plotly_chart(px.pie(filtered, names="light", title="光線條件分布"))

    st.subheader("🗺️ 事故地點地圖")
    map_data = filtered.dropna(subset=["latitude", "longitude"])
    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state=pdk.ViewState(latitude=CENTER_LAT, longitude=CENTER_LON, zoom=13, pitch=45),
        layers=[pdk.Layer(
            "ScatterplotLayer",
            data=map_data,
            get_position='[longitude, latitude]',
            get_color='[200, 30, 0, 160]',
            get_radius=60,
        )]
    ))

elif page == "🚫 無號誌道路":
    st.title(f"🚫 {year} 年無號誌路口事故分析")
    table_name = {
        "110": "uncontrolled_accidents",
        "111": "111uncontrolled_accidents",
        "112": "112uncontrolled_accidents"
    }.get(year, "uncontrolled_accidents")
    data = load_data(table_name, year)

    if data.empty or "location_text" not in data.columns:
        st.error("無法載入資料，請確認 Supabase 資料表")
        st.stop()

    data["uncontrolled"] = data["location_text"].apply(lambda x: classify_location(x, uncontrolled_spots))
    filtered = data[data["uncontrolled"] != "其他"]

    st.subheader("📅 每月事故數量")
    st.line_chart(filtered["month"].value_counts().sort_index())

    st.subheader("🕒 時段事故分布")
    st.bar_chart(filtered["time_period"].value_counts().sort_index())

    st.subheader("🚧 熱點事故次數")
    st.bar_chart(filtered["uncontrolled"].value_counts())

    st.subheader("☁️ 天氣條件事故分布")
    if "weather" in filtered.columns:
        st.plotly_chart(px.pie(filtered, names="weather", title="天氣條件分布"))

    st.subheader("💡 光線狀況事故分布")
    if "light" in filtered.columns:
        st.plotly_chart(px.pie(filtered, names="light", title="光線條件分布"))

    st.subheader("🗺️ 事故地點地圖")
    map_data = filtered.dropna(subset=["latitude", "longitude"])
    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state=pdk.ViewState(latitude=CENTER_LAT, longitude=CENTER_LON, zoom=13, pitch=45),
        layers=[pdk.Layer(
            "ScatterplotLayer",
            data=map_data,
            get_position='[longitude, latitude]',
            get_color='[0, 100, 255, 160]',
            get_radius=60,
        )]
    ))
