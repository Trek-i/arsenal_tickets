import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates
import os
from datetime import datetime

#############################################
# 0) 首先设置页面配置 (必须在任何 st.xxx 调用之前)
#############################################
st.set_page_config(
    page_title="Arsenal Ticket Market",
    page_icon="⚽",
    layout="wide"  # 宽屏模式
)

#############################################
# 1) 自定义 CSS (让页面更专业、品牌化)
#############################################
custom_css = """
<style>
/* 引入 Google Fonts - Open Sans */
@import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600&display=swap');

/* 整体重置与默认字体 */
html, body {
    margin: 0;
    padding: 0;
    font-family: 'Open Sans', sans-serif;
    background-color: #f8f9fa; /* 页面背景 */
}

/* 去掉 Streamlit 默认的边距 */
.css-18e3th9 {
    padding: 1rem 2rem 2rem 2rem; /* 自定义页面内边距 */
}

/* 顶部主 Banner 的背景渐变（阿森纳红色系） */
.banner-container {
    text-align: center;
    padding: 2rem 1rem;
    background: linear-gradient(90deg, #EF0107 0%, #97010A 100%);
    margin-bottom: 1rem;
}

.banner-container img {
    height: 80px;
    margin-bottom: 1rem;
}

.banner-container h1 {
    color: #fff;
    margin: 0.5rem 0;
    font-weight: 600;
    font-size: 2rem;
}

.banner-container p {
    color: #ffe;
    font-size: 1.1rem;
}

/* 调整子标题外观 */
h2, h3 {
    color: #EF0107; /* Arsenal 红 */
    margin-top: 0.75rem;
    margin-bottom: 0.5rem;
    font-weight: 600;
}

/* 自定义按钮样式（下载按钮等） */
div.stButton > button, div.stDownloadButton > button {
    background-color: #EF0107 !important;
    color: white !important;
    border: none !important;
    padding: 0.5em 1em !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
    cursor: pointer !important;
}

/* 输入组件（搜索框、下拉菜单）标签 */
div.stTextInput > label, div.stSelectbox > label {
    font-weight: 600;
    color: #333;
}

/* DataFrame 表格边框与圆角 */
[data-testid="stDataFrame"] {
    border: 1px solid #ddd;
    border-radius: 4px;
}

/* 页脚固定在底部 */
footer {
    text-align: center;
    padding: 1rem;
    color: #fff;
    background-color: #000;
    font-size: 0.9rem;
    position: fixed;
    bottom: 0;
    width: 100%;
    left: 0;
    z-index: 999;
    border-top: 1px solid #333;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

#############################################
# 2) Matplotlib 全局风格
#############################################
sns.set_style("whitegrid")
plt.rcParams.update({
    "font.size": 6,           # 全局字体
    "axes.titlesize": 6,      # 坐标轴标题大小
    "axes.labelsize": 6,      # 坐标轴标签大小
    "xtick.labelsize": 5,     # x轴刻度大小
    "ytick.labelsize": 5,     # y轴刻度大小
})

#############################################
# 3) 顶部 Banner
#############################################
logo_url = "https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg"  # Arsenal Logo 示例
st.markdown(
    f"""
    <div class="banner-container">
        <img src="{logo_url}" alt="Arsenal Logo">
        <h1>Arsenal Ticket Market Data</h1>
        <p>One day, one time point! Each match shows its <b>lowest price</b> and <b>remaining tickets</b> over time.</p>
    </div>
    """,
    unsafe_allow_html=True
)

#############################################
# 4) 读取并整合 Excel 数据
#############################################
@st.cache_data(show_spinner=True)
def load_excel_data(file_path: str):
    if not os.path.exists(file_path):
        return None, None
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
        return None, None

    # 合并所有 Sheet 数据
    df_all = pd.concat(dfs, ignore_index=True)
    return df_all, all_sheets

file_path = "price_summary.xlsx"
df_all, sheet_list = load_excel_data(file_path)

if df_all is None:
    st.error("⚠️ No valid data found. Please ensure 'price_summary.xlsx' exists and is properly formatted.")
    st.stop()

#############################################
# 5) 数据聚合：对 [Date, Match] 分组
#############################################
df_agg = (
    df_all
    .groupby(["Date", "Match"], sort=False)
    .agg({
        "Min_Price": "min",       # 每场比赛的最低票价
        "Ticket_Count": "sum"     # 剩余票数
    })
    .reset_index()
    .rename(columns={
        "Min_Price": "Lowest_Price",
        "Ticket_Count": "Remaining_Tickets"
    })
    .reset_index(drop=True)
)

# 找到最新日期
max_date = df_agg["Date"].max() if not df_agg.empty else None

# 只显示最新日期下的每场比赛信息 (用于 Overview)
df_overview_latest = df_agg[df_agg["Date"] == max_date][["Match", "Lowest_Price", "Remaining_Tickets"]]

#############################################
# 6) Streamlit 界面布局 - Tabs
#############################################
tab1, tab2, tab3 = st.tabs(["Overview", "Price Trends", "Raw Data"])

# ============ Tab 1: Overview ============
with tab1:
    st.subheader("Latest Date Overview")
    if max_date is None or df_overview_latest.empty:
        st.warning("No data for latest date.")
    else:
        st.write(f"**Latest Date**: {max_date}")
        st.write("Below shows each match's Lowest_Price & Remaining_Tickets on this date:")
        st.dataframe(df_overview_latest)

# ============ Tab 2: Price Trends ============
with tab2:
    st.subheader("Daily Price & Tickets Trend (One day, one point) - Each Match Separately")

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
                    fig1, ax1 = plt.subplots(figsize=(3, 2.2))
                    
                    ax1.plot(
                        df_match["Date"], 
                        df_match["Lowest_Price"],
                        marker="o",
                        markersize=3,      # marker 大小
                        linewidth=1.0,     # 线条粗细
                        color="#EF0107",   # Arsenal 红
                        label="Lowest Price"
                    )
                    
                    # 在每个点上方标注数值
                    for x_val, y_val in zip(df_match["Date"], df_match["Lowest_Price"]):
                        ax1.text(
                            x_val, y_val + 1,
                            f"{int(y_val)}",
                            ha='center', va='bottom',
                            fontsize=5,
                            color="#EF0107"
                        )
                    
                    ax1.set_xlabel("Date", fontsize=6)
                    ax1.set_ylabel("Price (£)", fontsize=6)
                    ax1.legend(fontsize=5)
                    
                    ax1.xaxis.set_major_locator(mdates.DayLocator())
                    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
                    plt.xticks(rotation=45)
                    
                    plt.tight_layout()
                    st.pyplot(fig1)
                
                # -- 图2: Remaining Tickets --
                with col2:
                    st.subheader("Remaining Tickets Trend")
                    fig2, ax2 = plt.subplots(figsize=(3, 2.2))
                    
                    ax2.plot(
                        df_match["Date"], 
                        df_match["Remaining_Tickets"],
                        marker="o",
                        markersize=3,
                        linewidth=1.0,
                        color="navy", 
                        label="Tickets"
                    )
                    
                    for x_val, y_val in zip(df_match["Date"], df_match["Remaining_Tickets"]):
                        ax2.text(
                            x_val, y_val + 1,
                            f"{int(y_val)}",
                            ha='center', va='bottom',
                            fontsize=5,
                            color="navy"
                        )
                    
                    ax2.set_xlabel("Date", fontsize=6)
                    ax2.set_ylabel("Tickets", fontsize=6)
                    ax2.legend(fontsize=5)
                    
                    ax2.xaxis.set_major_locator(mdates.DayLocator())
                    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
                    plt.xticks(rotation=45)
                    
                    plt.tight_layout()
                    st.pyplot(fig2)
                
                # 分割线
                st.markdown("<hr>", unsafe_allow_html=True)

# ============ Tab 3: Raw Data ============
with tab3:
    st.subheader("Raw Aggregated Data (Per Match, Per Day)")
    
    all_matches = list(df_agg["Match"].unique())
    search_term_raw = st.text_input(
        "Search matches (Raw Data)",
        "",
        help="Type partial keywords to filter the matches below."
    )
    filtered_matches_raw = [m for m in all_matches if search_term_raw.lower() in m.lower()]
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

# ---------------------------
# 固定页脚（可添加版权声明等）
# ---------------------------
footer_html = """
<footer>
    © 2025 Arsenal Ticket Market. All Rights Reserved.
</footer>
"""
st.markdown(footer_html, unsafe_allow_html=True)
