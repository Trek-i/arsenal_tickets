import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime
import matplotlib.dates as mdates

# 1️⃣ 页面基本设置
st.set_page_config(
    page_title="Arsenal Ticket Market",
    page_icon="⚽",
    layout="wide",  # 宽屏模式
)

# 2️⃣ 顶部标题
st.markdown(
    """
    <h1 style='text-align: center; color: red;'>
        🎟️ Arsenal Ticket Market Data
    </h1>
    <p style='text-align: center;'>
        One day, one time point! Each match shows its <b>lowest price</b> and <b>remaining tickets</b> over time.
    </p>
    """,
    unsafe_allow_html=True
)

# 3️⃣ 检查并读取 Excel
file_path = "price_summary.xlsx"
if not os.path.exists(file_path):
    st.error("⚠️ No data found. Please generate 'price_summary.xlsx' first.")
    st.stop()

excel_file = pd.ExcelFile(file_path)
all_sheets = excel_file.sheet_names  # e.g. ["2025-03-18", "2025-03-19", ...]

# 4️⃣ 读取所有符合格式的 Sheet，并拼接到一个 DataFrame
dfs = []
for sheet in all_sheets:
    # 先判断 Sheet 名是否是 YYYY-MM-DD 格式
    try:
        date_obj = datetime.strptime(sheet, "%Y-%m-%d").date()
    except ValueError:
        # Sheet 名不是日期格式，跳过或根据需求处理
        continue
    
    df_temp = pd.read_excel(file_path, sheet_name=sheet)
    
    # 确保含有关键列
    required_cols = {"Match", "Seat Type", "Min_Price", "Avg_Price", "Ticket_Count"}
    if not required_cols.issubset(df_temp.columns):
        continue
    
    # 加入 "Date" 列
    df_temp["Date"] = date_obj
    
    # 转换列类型
    df_temp["Min_Price"] = pd.to_numeric(df_temp["Min_Price"], errors="coerce").fillna(0).astype(float)
    df_temp["Ticket_Count"] = pd.to_numeric(df_temp["Ticket_Count"], errors="coerce").fillna(0).astype(int)
    
    dfs.append(df_temp)

if not dfs:
    st.error("⚠️ No valid daily sheets found (like 'YYYY-MM-DD') or missing required columns.")
    st.stop()

df_all = pd.concat(dfs, ignore_index=True)

# 5️⃣ 聚合：对 [Date, Match] 分组，得到「每日每场」的最低价 & 剩余票数
#    - Lowest_Price: 在所有座位类型里取 Min_Price 的最小值
#    - Remaining_Tickets: 将所有 Ticket_Count 相加
df_agg = df_all.groupby(["Date", "Match"]).agg({
    "Min_Price": "min",     # 每场比赛的最低价
    "Ticket_Count": "sum"   # 每场比赛剩余票数
}).reset_index()

# 重命名列更直观
df_agg.rename(columns={
    "Min_Price": "Lowest_Price",
    "Ticket_Count": "Remaining_Tickets"
}, inplace=True)

# 按日期排序
df_agg = df_agg.sort_values(by="Date").reset_index(drop=True)

# 6️⃣ 搭建 Tab 布局
tab1, tab2, tab3 = st.tabs(["📊 Overview", "📈 Price Trends", "📜 Raw Data"])

# --------------------------
#    Tab 1: Overview
# --------------------------
with tab1:
    st.subheader("📊 Daily Overview (Per Match)")
    st.dataframe(df_agg)

# --------------------------
#    Tab 2: Price Trends
# --------------------------
with tab2:
    st.subheader("📈 Daily Price & Tickets Trend (One day, one point) - **Each Match Separately**")

    if df_agg.empty:
        st.warning("No data to plot.")
    else:
        # 获取所有比赛
        all_matches = sorted(df_agg["Match"].unique())
        
        for match_name in all_matches:
            df_match = df_agg[df_agg["Match"] == match_name]
            if df_match.empty:
                continue
            
            # 标题
            st.markdown(f"### {match_name}")
            col1, col2 = st.columns(2)
            
            # 图1: Lowest Price
            with col1:
                st.subheader("Lowest Price Trend")
                fig1, ax1 = plt.subplots()
                ax1.plot(df_match["Date"], df_match["Lowest_Price"], marker="o", color="blue", label="Lowest Price")
                ax1.set_xlabel("Date")
                ax1.set_ylabel("Price (£)")
                ax1.legend()
                ax1.xaxis.set_major_locator(mdates.DayLocator())
                ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
                plt.xticks(rotation=45)
                st.pyplot(fig1)
            
            # 图2: Remaining Tickets
            with col2:
                st.subheader("Remaining Tickets Trend")
                fig2, ax2 = plt.subplots()
                ax2.plot(df_match["Date"], df_match["Remaining_Tickets"], marker="o", color="red", label="Tickets")
                ax2.set_xlabel("Date")
                ax2.set_ylabel("Tickets")
                ax2.legend()
                ax2.xaxis.set_major_locator(mdates.DayLocator())
                ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
                plt.xticks(rotation=45)
                st.pyplot(fig2)
            
            st.markdown("---")  # 分割线

# --------------------------
#    Tab 3: Raw Data
# --------------------------
with tab3:
    st.subheader("📜 Raw Aggregated Data (Per Match, Per Day)")
    st.dataframe(df_agg)

    # 下载按钮
    csv_data = df_agg.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download CSV",
        data=csv_data,
        file_name="daily_lowest_price_and_tickets.csv",
        mime="text/csv"
    )

st.markdown("<br><hr style='border:1px solid #bbb' />", unsafe_allow_html=True)
st.write("✅ Data successfully loaded & displayed!")
