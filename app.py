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
        This page provides daily Arsenal ticket market data and overall trends!
    </p>
    """,
    unsafe_allow_html=True
)

# 3️⃣ 定义数据文件
file_path = "price_summary.xlsx"
if not os.path.exists(file_path):
    st.error("No data found. Please run the analysis to generate 'price_summary.xlsx' first.")
    st.stop()

# 4️⃣ 读取 Excel 的所有 Sheet
excel_file = pd.ExcelFile(file_path)
all_sheets = excel_file.sheet_names  # e.g. ["2025-03-18", "2025-03-19", ...]

# 5️⃣ 构建空列表，用于存储每日汇总 (日期, GlobalMinPrice, TotalTickets)
trend_data = []
for sheet in all_sheets:
    df_sheet = pd.read_excel(file_path, sheet_name=sheet)

    # 确保数据格式正确
    df_sheet["Min_Price"] = pd.to_numeric(df_sheet["Min_Price"], errors="coerce").fillna(0).astype(int)
    df_sheet["Avg_Price"] = pd.to_numeric(df_sheet["Avg_Price"], errors="coerce").fillna(0).astype(int)
    df_sheet["Ticket_Count"] = pd.to_numeric(df_sheet["Ticket_Count"], errors="coerce").fillna(0).astype(int)

    global_min_price = df_sheet["Min_Price"].min() if len(df_sheet) > 0 else 0
    total_tickets = df_sheet["Ticket_Count"].sum() if len(df_sheet) > 0 else 0

    try:
        # 解析 Sheet 名为日期
        date_obj = datetime.strptime(sheet, "%Y-%m-%d").date()
    except:
        date_obj = None

    trend_data.append({
        "Date": date_obj,
        "SheetName": sheet,
        "GlobalMinPrice": global_min_price,
        "TotalTickets": total_tickets
    })

df_trend = pd.DataFrame(trend_data).dropna(subset=["Date"])
df_trend = df_trend.sort_values(by="Date").reset_index(drop=True)

# 6️⃣ 使用 Tabs 分区展示
tab1, tab2, tab3 = st.tabs(["Overview", "Trends", "Daily Data"])

# --------------------------
#    Tab 1: Overview
# --------------------------
with tab1:
    st.subheader("📅 All Days Combined Summary")
    st.dataframe(df_trend[["SheetName", "GlobalMinPrice", "TotalTickets"]])

    st.write(
        """
        - **SheetName**: the date of the data (YYYY-MM-DD)
        - **GlobalMinPrice**: the lowest ticket price across all seat types
        - **TotalTickets**: sum of ticket counts for the day
        """
    )

# --------------------------
#    Tab 2: Trends
# --------------------------
with tab2:
    col1, col2 = st.columns(2)

    # 最低价格走势
    with col1:
        st.subheader("📈 Minimum Price Trend Over Time")
        fig1, ax1 = plt.subplots()
        ax1.plot(df_trend["Date"], df_trend["GlobalMinPrice"], marker="o", color="blue", label="Global Min Price")
        ax1.set_xlabel("Date")
        ax1.set_ylabel("Price (£)")
        ax1.legend()
        # 只显示月-日
        ax1.xaxis.set_major_locator(mdates.DayLocator())
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        plt.xticks(rotation=45)
        st.pyplot(fig1)

    # 票数走势
    with col2:
        st.subheader("📈 Total Tickets Trend Over Time")
        fig2, ax2 = plt.subplots()
        ax2.plot(df_trend["Date"], df_trend["TotalTickets"], marker="o", color="red", label="Total Tickets")
        ax2.set_xlabel("Date")
        ax2.set_ylabel("Tickets")
        ax2.legend()
        # 只显示月-日
        ax2.xaxis.set_major_locator(mdates.DayLocator())
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        plt.xticks(rotation=45)
        st.pyplot(fig2)

# --------------------------
#    Tab 3: Daily Data
# --------------------------
with tab3:
    st.subheader("🔍 View Data for a Specific Day")

    # 逆序让最新日期在上面
    selected_sheet = st.selectbox("Select a date", all_sheets[::-1])

    df_selected = pd.read_excel(file_path, sheet_name=selected_sheet)
    df_selected["Min_Price"] = pd.to_numeric(df_selected["Min_Price"], errors="coerce").fillna(0).astype(int)
    df_selected["Avg_Price"] = pd.to_numeric(df_selected["Avg_Price"], errors="coerce").fillna(0).astype(int)
    df_selected["Ticket_Count"] = pd.to_numeric(df_selected["Ticket_Count"], errors="coerce").fillna(0).astype(int)

    st.dataframe(df_selected)

    st.download_button(
        label="📥 Download Selected Date Data",
        data=df_selected.to_csv(index=False).encode("utf-8"),
        file_name=f"{selected_sheet}_data.csv",
        mime="text/csv"
    )

st.markdown("<br><hr style='border:1px solid #bbb' />", unsafe_allow_html=True)
st.write("✅ Page updated successfully!")
