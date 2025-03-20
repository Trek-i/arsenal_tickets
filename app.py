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
        One day, one time point! Each match is displayed in separate charts.
    </p>
    """,
    unsafe_allow_html=True
)

# 3️⃣ 读取 Excel 数据文件
file_path = "price_summary.xlsx"
if not os.path.exists(file_path):
    st.error("⚠️ No data found. Please generate 'price_summary.xlsx' first.")
    st.stop()

excel_file = pd.ExcelFile(file_path)
all_sheets = excel_file.sheet_names  # e.g. ["2025-03-18", "2025-03-19", "2025-03-20", ...]

# 4️⃣ 读取所有 Sheet 并拼接到一个 DataFrame，解析 SheetName 为日期
dfs = []
for sheet in all_sheets:
    try:
        # 尝试把 Sheet 名当成日期解析
        date_obj = datetime.strptime(sheet, "%Y-%m-%d").date()
    except ValueError:
        # 如果 Sheet 名不是日期格式，跳过或忽略
        continue
    
    df_temp = pd.read_excel(file_path, sheet_name=sheet)
    # 确保含有关键列
    required_cols = {"Match", "Seat Type", "Min_Price", "Avg_Price", "Ticket_Count"}
    if not required_cols.issubset(df_temp.columns):
        continue
    
    # 加入 "Date" 列，用于后续聚合
    df_temp["Date"] = date_obj
    
    # 确保数值列正确
    df_temp["Min_Price"] = pd.to_numeric(df_temp["Min_Price"], errors="coerce").fillna(0).astype(float)
    df_temp["Avg_Price"] = pd.to_numeric(df_temp["Avg_Price"], errors="coerce").fillna(0).astype(float)
    df_temp["Ticket_Count"] = pd.to_numeric(df_temp["Ticket_Count"], errors="coerce").fillna(0).astype(int)
    
    dfs.append(df_temp)

if not dfs:
    st.error("⚠️ No valid daily sheets found (like 'YYYY-MM-DD') or missing required columns.")
    st.stop()

df_all = pd.concat(dfs, ignore_index=True)

# 5️⃣ 为了“一天一个时间点”+“区分每场比赛”，按 [Date, Match, Seat Type] 聚合
#    这样：同一天 & 同一场比赛 & 同一 Seat Type 只保留一行
#    若同一天有多场比赛，则会在同一天出现多条(多点)，每场比赛单独一条
df_agg = df_all.groupby(["Date", "Match", "Seat Type"]).agg({
    "Min_Price": "mean",   # 你也可用 "min" 或 "max"
    "Avg_Price": "mean",   # 也可用其他聚合方式
    "Ticket_Count": "sum"
}).reset_index()

# 按日期排序
df_agg = df_agg.sort_values(by="Date").reset_index(drop=True)

# 6️⃣ 侧边栏：多选 Seat Type，默认全选
st.sidebar.header("🔍 Filter Data")
seat_types = sorted(df_agg["Seat Type"].unique())
selected_seats = st.sidebar.multiselect("Choose seat types", seat_types, default=seat_types)

df_filtered = df_agg[df_agg["Seat Type"].isin(selected_seats)]

# 7️⃣ Tab 结构
tab1, tab2, tab3 = st.tabs(["📊 Overview", "📈 Price Trends", "📜 Raw Aggregated Data"])

# --------------------------
#    Tab 1: Overview
# --------------------------
with tab1:
    st.subheader("📊 Daily Overview (Per Match)")
    if df_filtered.empty:
        st.warning("No data after seat-type filtering.")
    else:
        st.dataframe(df_filtered)

# --------------------------
#    Tab 2: Price Trends
# --------------------------
with tab2:
    st.subheader("📈 Daily Price Trends (One day, one point) - **Each Match Separately**")
    if df_filtered.empty:
        st.warning("No data to plot.")
    else:
        # 获取所有比赛
        all_matches = sorted(df_filtered["Match"].unique())
        
        for match_name in all_matches:
            df_match = df_filtered[df_filtered["Match"] == match_name]
            if df_match.empty:
                continue
            
            st.markdown(f"### {match_name}")
            col1, col2 = st.columns(2)
            
            # 图1: Min Price
            with col1:
                st.subheader("Min Price Trend")
                fig1, ax1 = plt.subplots()
                for seat in sorted(df_match["Seat Type"].unique()):
                    data_seat = df_match[df_match["Seat Type"] == seat]
                    ax1.plot(data_seat["Date"], data_seat["Min_Price"], marker="o", label=seat)
                ax1.set_xlabel("Date")
                ax1.set_ylabel("Min Price (£)")
                ax1.legend()
                ax1.xaxis.set_major_locator(mdates.DayLocator())
                ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
                plt.xticks(rotation=45)
                st.pyplot(fig1)
            
            # 图2: Avg Price
            with col2:
                st.subheader("Avg Price Trend")
                fig2, ax2 = plt.subplots()
                for seat in sorted(df_match["Seat Type"].unique()):
                    data_seat = df_match[df_match["Seat Type"] == seat]
                    ax2.plot(data_seat["Date"], data_seat["Avg_Price"], marker="o", label=seat)
                ax2.set_xlabel("Date")
                ax2.set_ylabel("Avg Price (£)")
                ax2.legend()
                ax2.xaxis.set_major_locator(mdates.DayLocator())
                ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
                plt.xticks(rotation=45)
                st.pyplot(fig2)
            
            st.markdown("---")  # 分割线

# --------------------------
#    Tab 3: Raw Aggregated Data
# --------------------------
with tab3:
    st.subheader("📜 Raw Aggregated Data (Per Match, Per Day)")
    if df_filtered.empty:
        st.warning("No data to display.")
    else:
        st.dataframe(df_filtered)

        # 下载按钮
        csv_data = df_filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name="daily_aggregated_data_per_match.csv",
            mime="text/csv"
        )

st.markdown("<br><hr style='border:1px solid #bbb' />", unsafe_allow_html=True)
st.write("✅ Data successfully loaded & displayed!")
