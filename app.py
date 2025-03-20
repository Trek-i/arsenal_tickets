import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime
import matplotlib.dates as mdates

# 1️⃣ 设置页面配置（标题、图标、布局）
st.set_page_config(
    page_title="Arsenal Ticket Market",
    page_icon="⚽",
    layout="wide",  # 宽屏模式
)

# 2️⃣ 自定义页面顶部标题
st.markdown(
    """
    <h1 style='text-align: center; color: red;'>
        🎟️ Arsenal Ticket Market Data
    </h1>
    <p style='text-align: center;'>
        Explore ticket pricing trends, seat availability, and match-specific data!
    </p>
    """,
    unsafe_allow_html=True
)

# 3️⃣ 读取 Excel 数据文件
file_path = "price_summary.xlsx"
if not os.path.exists(file_path):
    st.error("⚠️ No data found. Please generate 'price_summary.xlsx' first.")
    st.stop()

# 4️⃣ 读取 Excel 的所有 Sheet
excel_file = pd.ExcelFile(file_path)
all_sheets = excel_file.sheet_names  # e.g. ["2025-03-18_byMatch", "2025-03-19_byMatch", ...]

# 筛选出 "_byMatch" 结尾的 Sheet（即每日按比赛区分的汇总）
match_sheets = [sheet for sheet in all_sheets if "_byMatch" in sheet]

# 5️⃣ 读取所有数据，构建比赛列表
match_data = []
for sheet in match_sheets:
    df_sheet = pd.read_excel(file_path, sheet_name=sheet)

    if "Match" in df_sheet.columns and len(df_sheet) > 0:
        match_data.append(df_sheet)

if not match_data:
    st.error("⚠️ No match-specific data available.")
    st.stop()

df_all = pd.concat(match_data, ignore_index=True)

# 确保数据格式正确
df_all["Min_Price"] = pd.to_numeric(df_all["Min_Price"], errors="coerce").fillna(0).astype(int)
df_all["Avg_Price"] = pd.to_numeric(df_all["Avg_Price"], errors="coerce").fillna(0).astype(int)
df_all["Ticket_Count"] = pd.to_numeric(df_all["Ticket_Count"], errors="coerce").fillna(0).astype(int)

# 获取所有比赛的唯一列表
matches = sorted(df_all["Match"].unique())

# 6️⃣ 侧边栏：用户选择比赛 & 日期
st.sidebar.header("🔍 Filter Data")
selected_match = st.sidebar.selectbox("Select a match", matches)
selected_sheet = st.sidebar.selectbox("Select a date", match_sheets[::-1])

# 7️⃣ 筛选用户选择的比赛 & 日期数据
df_selected = df_all[(df_all["Match"] == selected_match)]

if selected_sheet:
    df_selected = df_selected[df_selected["Match"].str.contains(selected_match)]

# 8️⃣ 按 "Seat Type" 进行分组，展示价格趋势
seat_types = sorted(df_selected["Seat Type"].unique())
st.sidebar.subheader("Seat Type Filter")
selected_seats = st.sidebar.multiselect("Choose seat types", seat_types, default=seat_types)

df_selected = df_selected[df_selected["Seat Type"].isin(selected_seats)]

# 9️⃣ **Tab 结构**
tab1, tab2, tab3 = st.tabs(["📊 Match Overview", "📈 Price Trends", "📜 Raw Data"])

# --------------------------
#    Tab 1: Match Overview
# --------------------------
with tab1:
    st.subheader(f"📊 Match Summary: {selected_match}")
    st.dataframe(df_selected[["Seat Type", "Min_Price", "Avg_Price", "Ticket_Count"]])

# --------------------------
#    Tab 2: Price Trends
# --------------------------
with tab2:
    st.subheader(f"📈 Price Trends for {selected_match}")
    col1, col2 = st.columns(2)

    # 📉 **Minimum Price Trend**
    with col1:
        st.subheader("Min Price Trend")
        fig1, ax1 = plt.subplots()
        for seat in selected_seats:
            data = df_selected[df_selected["Seat Type"] == seat]
            ax1.plot(data["Match"], data["Min_Price"], marker="o", label=seat)
        
        ax1.set_xlabel("Match Date")
        ax1.set_ylabel("Min Price (£)")
        ax1.legend()
        ax1.xaxis.set_major_locator(mdates.DayLocator())
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        plt.xticks(rotation=45)
        st.pyplot(fig1)

    # 📉 **Average Price Trend**
    with col2:
        st.subheader("Avg Price Trend")
        fig2, ax2 = plt.subplots()
        for seat in selected_seats:
            data = df_selected[df_selected["Seat Type"] == seat]
            ax2.plot(data["Match"], data["Avg_Price"], marker="o", label=seat)
        
        ax2.set_xlabel("Match Date")
        ax2.set_ylabel("Avg Price (£)")
        ax2.legend()
        ax2.xaxis.set_major_locator(mdates.DayLocator())
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        plt.xticks(rotation=45)
        st.pyplot(fig2)

# --------------------------
#    Tab 3: Raw Data
# --------------------------
with tab3:
    st.subheader(f"📜 Full Data for {selected_match}")
    st.dataframe(df_selected)

    # 📥 **下载按钮**
    st.download_button(
        label="📥 Download CSV",
        data=df_selected.to_csv(index=False).encode("utf-8"),
        file_name=f"{selected_match.replace(' ', '_')}_data.csv",
        mime="text/csv"
    )

st.markdown("<br><hr style='border:1px solid #bbb' />", unsafe_allow_html=True)
st.write("✅ Data successfully loaded & displayed!")
