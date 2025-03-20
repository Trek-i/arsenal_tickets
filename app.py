import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime

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

excel_file = pd.ExcelFile(file_path)
all_sheets = excel_file.sheet_names  # e.g. ["2025-03-18", "2025-03-19", ...]

# 4️⃣ 读取所有 Sheet，并合并到一个 DataFrame，增加一列 "SheetName" 存放日期
dfs = []
for sheet in all_sheets:
    df_temp = pd.read_excel(file_path, sheet_name=sheet)
    # 确保含有关键列，且非空
    if all(col in df_temp.columns for col in ["Match", "Seat Type", "Min_Price", "Avg_Price", "Ticket_Count"]):
        df_temp["SheetName"] = sheet
        dfs.append(df_temp)

if not dfs:
    st.error("⚠️ No valid sheets with columns: Match, Seat Type, Min_Price, Avg_Price, Ticket_Count.")
    st.stop()

df_all = pd.concat(dfs, ignore_index=True)

# 确保数据格式正确
df_all["Min_Price"] = pd.to_numeric(df_all["Min_Price"], errors="coerce").fillna(0).astype(int)
df_all["Avg_Price"] = pd.to_numeric(df_all["Avg_Price"], errors="coerce").fillna(0).astype(int)
df_all["Ticket_Count"] = pd.to_numeric(df_all["Ticket_Count"], errors="coerce").fillna(0).astype(int)

# 5️⃣ 侧边栏：让用户先选择日期(Sheet)，再选择比赛，最后多选 Seat Type
st.sidebar.header("🔍 Filter Data")

# （1）选择日期
selected_sheet = st.sidebar.selectbox("Select a date (SheetName)", all_sheets[::-1])

# 筛选出该 Sheet 的数据
df_sheet_selected = df_all[df_all["SheetName"] == selected_sheet]
if df_sheet_selected.empty:
    st.warning(f"No data found for sheet: {selected_sheet}")
    st.stop()

# （2）从该 Sheet 中获取所有比赛
matches = sorted(df_sheet_selected["Match"].unique())
selected_match = st.sidebar.selectbox("Select a match", matches)

# 再次筛选比赛
df_selected = df_sheet_selected[df_sheet_selected["Match"] == selected_match]

# （3）多选 Seat Type
seat_types = sorted(df_selected["Seat Type"].unique())
st.sidebar.subheader("Seat Type Filter")
selected_seats = st.sidebar.multiselect("Choose seat types", seat_types, default=seat_types)

df_selected = df_selected[df_selected["Seat Type"].isin(selected_seats)]

# 6️⃣ **Tab 结构**
tab1, tab2, tab3 = st.tabs(["📊 Match Overview", "📈 Price Trends", "📜 Raw Data"])

# --------------------------
#    Tab 1: Match Overview
# --------------------------
with tab1:
    st.subheader(f"📊 Match Summary: {selected_match} (Sheet: {selected_sheet})")
    if df_selected.empty:
        st.warning("No data after filtering seat types.")
    else:
        st.dataframe(df_selected[["Seat Type", "Min_Price", "Avg_Price", "Ticket_Count"]])

# --------------------------
#    Tab 2: Price Trends
# --------------------------
with tab2:
    st.subheader(f"📈 Price Trends for {selected_match}")
    if df_selected.empty:
        st.warning("No data to plot.")
    else:
        col1, col2 = st.columns(2)

        # **Minimum Price Trend**
        with col1:
            st.subheader("Min Price Trend")
            fig1, ax1 = plt.subplots()
            for seat in selected_seats:
                data = df_selected[df_selected["Seat Type"] == seat]
                ax1.plot(data["Match"], data["Min_Price"], marker="o", label=seat)
            
            ax1.set_xlabel("Match")
            ax1.set_ylabel("Min Price (£)")
            ax1.legend()
            plt.xticks(rotation=45)
            st.pyplot(fig1)

        # **Average Price Trend**
        with col2:
            st.subheader("Avg Price Trend")
            fig2, ax2 = plt.subplots()
            for seat in selected_seats:
                data = df_selected[df_selected["Seat Type"] == seat]
                ax2.plot(data["Match"], data["Avg_Price"], marker="o", label=seat)
            
            ax2.set_xlabel("Match")
            ax2.set_ylabel("Avg Price (£)")
            ax2.legend()
            plt.xticks(rotation=45)
            st.pyplot(fig2)

# --------------------------
#    Tab 3: Raw Data
# --------------------------
with tab3:
    st.subheader(f"📜 Full Data for {selected_match} (Sheet: {selected_sheet})")
    if df_selected.empty:
        st.warning("No data to display.")
    else:
        st.dataframe(df_selected)

        # **下载按钮**
        csv_data = df_selected.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=f"{selected_sheet}_{selected_match.replace(' ', '_')}_data.csv",
            mime="text/csv"
        )

st.markdown("<br><hr style='border:1px solid #bbb' />", unsafe_allow_html=True)
st.write("✅ Data successfully loaded & displayed!")
