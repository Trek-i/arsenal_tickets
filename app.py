import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime
import matplotlib.dates as mdates

#############################################
# 1) Streamlit 页面基础设置
#############################################
st.set_page_config(
    page_title="Arsenal Ticket Market",
    page_icon="⚽",
    layout="wide",  # 宽屏模式
)

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

#############################################
# 2) 读取并整合 Excel 数据
#############################################
file_path = "price_summary.xlsx"
if not os.path.exists(file_path):
    st.error("⚠️ No data found. Please generate 'price_summary.xlsx' first.")
    st.stop()

excel_file = pd.ExcelFile(file_path)
all_sheets = excel_file.sheet_names  # e.g. ["2025-03-18", "2025-03-19", ...]

# 用于收集所有满足条件的 Sheet 数据
dfs = []
for sheet in all_sheets:
    # 判断 Sheet 名是否是 YYYY-MM-DD 格式
    try:
        date_obj = datetime.strptime(sheet, "%Y-%m-%d").date()
    except ValueError:
        # 如果 Sheet 名不是日期格式，跳过
        continue
    
    # 读取当前 Sheet
    df_temp = pd.read_excel(file_path, sheet_name=sheet)
    
    # 确保含有关键列
    required_cols = {"Match", "Seat Type", "Min_Price", "Avg_Price", "Ticket_Count"}
    if not required_cols.issubset(df_temp.columns):
        continue
    
    # 加 "Date" 列
    df_temp["Date"] = date_obj
    
    # 转换列类型
    df_temp["Min_Price"] = pd.to_numeric(df_temp["Min_Price"], errors="coerce").fillna(0).astype(float)
    df_temp["Ticket_Count"] = pd.to_numeric(df_temp["Ticket_Count"], errors="coerce").fillna(0).astype(int)
    
    dfs.append(df_temp)

if not dfs:
    st.error("⚠️ No valid daily sheets found (like 'YYYY-MM-DD') or missing required columns.")
    st.stop()

# 合并所有 Sheet 数据
df_all = pd.concat(dfs, ignore_index=True)

#############################################
# 3) 数据聚合：对 [Date, Match] 分组
#############################################
# 不使用 sort=True，让其保持原数据出现顺序
df_agg = (
    df_all
    .groupby(["Date", "Match"], sort=False)
    .agg({
        "Min_Price": "min",       # 每场比赛的最低票价
        "Ticket_Count": "sum"     # 剩余票数 = 各Seat Type票数之和
    })
    .reset_index()
    .rename(columns={
        "Min_Price": "Lowest_Price",
        "Ticket_Count": "Remaining_Tickets"
    })
    # 不进行额外的 sort_values，以保留原顺序
    .reset_index(drop=True)
)

# 找到最新日期
max_date = df_agg["Date"].max() if not df_agg.empty else None

# 只显示最新日期下的每场比赛信息 (用于 Overview)
df_overview_latest = df_agg[df_agg["Date"] == max_date][["Match", "Lowest_Price", "Remaining_Tickets"]]

#############################################
# 4) Streamlit 界面布局 - Tabs
#############################################
tab1, tab2, tab3 = st.tabs(["Overview", "Price Trends", "Raw Data"])

# ============ Tab 1: Overview ============
with tab1:
    st.subheader("📊 Latest Date Overview")
    if max_date is None or df_overview_latest.empty:
        st.warning("No data for latest date.")
    else:
        st.write(f"**Latest Date**: {max_date}")
        st.write("Below shows each match's Lowest_Price & Remaining_Tickets on this date:")
        st.dataframe(df_overview_latest)

# ============ Tab 2: Price Trends ============
with tab2:
    st.subheader("📈 Daily Price & Tickets Trend (One day, one point) - Each Match Separately")

    if df_agg.empty:
        st.warning("No data to plot.")
    else:
        # 获取比赛列表（保持原出现顺序）
        all_matches = list(df_agg["Match"].unique())

        # 1) 关键词搜索
        search_term = st.text_input(
            "Search matches (Price Trends)",
            "",
            help="Type partial keywords to filter the matches below."
        )
        # 根据搜索词进行筛选
        filtered_matches = [m for m in all_matches if search_term.lower() in m.lower()]

        # 2) 下拉菜单
        selected_match = st.selectbox("Select a match to view charts", ["All"] + filtered_matches)

        # 确定要显示的比赛列表
        if selected_match == "All":
            matches_to_plot = filtered_matches
        else:
            matches_to_plot = [selected_match]

        # 若搜索结果为空，则提示
        if not matches_to_plot:
            st.warning("No matches found with the given search term.")
        else:
            # 按出现顺序依次画图
            for match_name in matches_to_plot:
                df_match = df_agg[df_agg["Match"] == match_name]
                if df_match.empty:
                    continue

                # 比赛标题
                st.markdown(f"### {match_name}")
                col1, col2 = st.columns(2)
                
                # -- 图1: Lowest Price --
                with col1:
                    st.subheader("Lowest Price Trend")
                    fig1, ax1 = plt.subplots(figsize=(2.5, 2))
                    
                    ax1.plot(
                        df_match["Date"], 
                        df_match["Lowest_Price"],
                        marker="o",
                        markersize=2,      # marker 大小
                        linewidth=0.8,     # 线条粗细
                        color="blue", 
                        label="Lowest Price"
                    )
                    
                    # 在每个点上方标注数值 (略微大一点,让其清晰)
                    for x_val, y_val in zip(df_match["Date"], df_match["Lowest_Price"]):
                        ax1.text(
                            x_val, y_val + 1,
                            f"{int(y_val)}",
                            ha='center', va='bottom',
                            fontsize=4,   # 调大一点，使其清晰
                            color="blue"
                        )
                    
                    ax1.set_xlabel("Date", fontsize=6)
                    ax1.set_ylabel("Price (£)", fontsize=6)
                    ax1.legend(fontsize=5)
                    ax1.tick_params(axis='both', which='major', labelsize=5)
                    
                    ax1.xaxis.set_major_locator(mdates.DayLocator())
                    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
                    plt.xticks(rotation=45)
                    
                    plt.tight_layout()
                    st.pyplot(fig1)
                
                # -- 图2: Remaining Tickets --
                with col2:
                    st.subheader("Remaining Tickets Trend")
                    fig2, ax2 = plt.subplots(figsize=(2.5, 2))
                    
                    ax2.plot(
                        df_match["Date"], 
                        df_match["Remaining_Tickets"],
                        marker="o",
                        markersize=2,
                        linewidth=0.8,
                        color="red", 
                        label="Tickets"
                    )
                    
                    for x_val, y_val in zip(df_match["Date"], df_match["Remaining_Tickets"]):
                        ax2.text(
                            x_val, y_val + 1,
                            f"{int(y_val)}",
                            ha='center', va='bottom',
                            fontsize=4,  # 同样调大一点
                            color="red"
                        )
                    
                    ax2.set_xlabel("Date", fontsize=6)
                    ax2.set_ylabel("Tickets", fontsize=6)
                    ax2.legend(fontsize=5)
                    ax2.tick_params(axis='both', which='major', labelsize=5)
                    
                    ax2.xaxis.set_major_locator(mdates.DayLocator())
                    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
                    plt.xticks(rotation=45)
                    
                    plt.tight_layout()
                    st.pyplot(fig2)
                
                # 分割线
                st.markdown("---")

# ============ Tab 3: Raw Data ============
with tab3:
    st.subheader("📜 Raw Aggregated Data (Per Match, Per Day)")
    
    # 1) 关键词搜索
    all_matches = list(df_agg["Match"].unique())
    search_term_raw = st.text_input(
        "Search matches (Raw Data)",
        "",
        help="Type partial keywords to filter the matches below."
    )
    filtered_matches_raw = [m for m in all_matches if search_term_raw.lower() in m.lower()]

    # 2) 下拉菜单
    selected_match_raw = st.selectbox("Select a match to view raw data", ["All"] + filtered_matches_raw)

    if selected_match_raw == "All":
        matches_to_show = filtered_matches_raw
    else:
        matches_to_show = [selected_match_raw]

    if not matches_to_show:
        st.warning("No matches found with the given search term.")
    else:
        df_display = df_agg[df_agg["Match"].isin(matches_to_show)]
        st.dataframe(df_display)

        # 下载按钮
        csv_data = df_display.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name="daily_lowest_price_and_tickets.csv",
            mime="text/csv"
        )

# 底部分割
st.markdown("<br><hr style='border:1px solid #bbb' />", unsafe_allow_html=True)
st.write("✅ Data successfully loaded & displayed!")
