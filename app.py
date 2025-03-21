import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates
import os
from datetime import datetime
import streamlit.components.v1 as components
from st_aggrid import AgGrid  # pip install streamlit-aggrid

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

/* 顶部主 Banner 的背景：增加背景图（可选）及渐变颜色，内边距调整更紧凑 */
.banner-container {
    text-align: center;
    padding: 1.5rem 1rem;
    background: linear-gradient(90deg, #EF0107 0%, #97010A 100%);
    /* 如需添加背景图，可取消下一行注释，并替换 URL */
    /* background-image: url("https://example.com/your_banner_image.jpg"); */
    background-size: cover;
    margin-bottom: 1rem;
}

.banner-container img {
    height: 60px;
    margin-bottom: 0.5rem;
}

.banner-container h1 {
    color: #fff;
    margin: 0.3rem 0;
    font-weight: 600;
    font-size: 1.8rem;
}

.banner-container p {
    color: #ffe;
    font-size: 1rem;
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

/* 页脚样式 */
footer {
    text-align: center;
    padding: 0.5rem;
    color: #555;
    background-color: #f0f0f0; /* 浅灰色背景 */
    font-size: 0.8rem;
    position: static;
    width: 100%;
    border-top: 1px solid #ddd;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

#############################################
# 2) Matplotlib & Seaborn 全局风格
#############################################
sns.set_theme(style="white")
plt.rcParams.update({
    "font.size": 6,           # 全局字体
    "axes.titlesize": 6,      # 坐标轴标题大小
    "axes.labelsize": 6,      # 坐标轴标签大小
    "xtick.labelsize": 5,     # x轴刻度大小
    "ytick.labelsize": 5,     # y轴刻度大小
    "axes.spines.top": True,  # 显示上边框
    "axes.spines.right": True # 显示右边框
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
        <p>One day, one time point! Each match shows its <b>lowest price</b>, <b>average price</b> and <b>remaining tickets</b> over time.</p>
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

    dfs = []
    for sheet in all_sheets:
        try:
            date_obj = datetime.strptime(sheet, "%Y-%m-%d").date()
        except ValueError:
            continue
        
        df_temp = pd.read_excel(file_path, sheet_name=sheet)
        
        required_cols = {"Match", "Seat Type", "Min_Price", "Avg_Price", "Ticket_Count"}
        if not required_cols.issubset(df_temp.columns):
            continue
        
        df_temp["Date"] = date_obj
        df_temp["Min_Price"] = pd.to_numeric(df_temp["Min_Price"], errors="coerce").fillna(0).astype(float)
        df_temp["Avg_Price"] = pd.to_numeric(df_temp["Avg_Price"], errors="coerce").fillna(0).astype(float)
        df_temp["Ticket_Count"] = pd.to_numeric(df_temp["Ticket_Count"], errors="coerce").fillna(0).astype(int)
        
        dfs.append(df_temp)

    if not dfs:
        return None, None

    df_all = pd.concat(dfs, ignore_index=True)
    return df_all, all_sheets

file_path = "price_summary.xlsx"
df_all, sheet_list = load_excel_data(file_path)

if df_all is None:
    st.error("⚠️ No valid data found. Please ensure 'price_summary.xlsx' exists and is properly formatted.")
    st.stop()

#############################################
# 5) 数据聚合：对 [Date, Match] 分组（增加平均票价统计）
#############################################
df_agg = (
    df_all
    .groupby(["Date", "Match"], sort=False)
    .agg({
        "Min_Price": "min",       # 每场比赛的最低票价
        "Avg_Price": "mean",      # 每场比赛的平均票价
        "Ticket_Count": "sum"     # 剩余票数
    })
    .reset_index()
    .rename(columns={
        "Min_Price": "Lowest_Price",
        "Avg_Price": "Average_Price",
        "Ticket_Count": "Remaining_Tickets"
    })
    .reset_index(drop=True)
)

max_date = df_agg["Date"].max() if not df_agg.empty else None
df_overview_latest = df_agg[df_agg["Date"] == max_date][["Match", "Lowest_Price", "Average_Price", "Remaining_Tickets"]]

#############################################
# 6) Streamlit 界面布局 - Tabs
#############################################
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Price Trends", "Raw Data", "Arsenal News"])

# ============ Tab 1: Overview ============
with tab1:
    st.subheader("Latest Date Overview")
    if max_date is None or df_overview_latest.empty:
        st.warning("No data for latest date.")
    else:
        st.write(f"**Latest Date**: {max_date}")
        st.write("Below shows each match's Lowest Price, Average Price & Remaining Tickets on this date:")
        st.dataframe(df_overview_latest)

# ============ Tab 2: Price Trends ============
with tab2:
    st.subheader("Daily Price & Tickets Trend (One day, one point) - Each Match Separately")

    if df_agg.empty:
        st.warning("No data to plot.")
    else:
        all_matches = list(df_agg["Match"].unique())
        search_term = st.text_input("Search matches (Price Trends)", "", help="Type partial keywords to filter the matches below.")
        filtered_matches = [m for m in all_matches if search_term.lower() in m.lower()]
        selected_match = st.selectbox("Select a match to view charts", ["All"] + filtered_matches)

        matches_to_plot = filtered_matches if selected_match == "All" else [selected_match]

        if not matches_to_plot:
            st.warning("No matches found with the given search term.")
        else:
            for match_name in matches_to_plot:
                df_match = df_agg[df_agg["Match"] == match_name]
                if df_match.empty:
                    continue

                st.markdown(f"### {match_name}")
                col1, col2 = st.columns(2)
                
                # -- 图1: Lowest Price & Average Price Trend --
                with col1:
                    st.subheader("Price Trend")
                    fig1, ax1 = plt.subplots(figsize=(3, 2.2))
                    ax1.plot(df_match["Date"], df_match["Lowest_Price"], marker="o", markersize=3, linewidth=1.0, color="#EF0107", label="Lowest Price")
                    ax1.plot(df_match["Date"], df_match["Average_Price"], marker="s", markersize=3, linewidth=1.0, color="green", label="Average Price")
                    
                    for x_val, y_val in zip(df_match["Date"], df_match["Lowest_Price"]):
                        ax1.text(x_val, y_val + 1, f"{int(y_val)}", ha='center', va='bottom', fontsize=5, color="#EF0107")
                    for x_val, y_val in zip(df_match["Date"], df_match["Average_Price"]):
                        ax1.text(x_val, y_val + 1, f"{y_val:.1f}", ha='center', va='bottom', fontsize=5, color="green")
                    
                    ax1.set_xlabel("Date", fontsize=6)
                    ax1.set_ylabel("Price (£)", fontsize=6)
                    ax1.legend(fontsize=5)
                    for spine in ["top", "right", "bottom", "left"]:
                        ax1.spines[spine].set_visible(True)
                    ax1.tick_params(axis='both', which='major', length=4, width=1)
                    ax1.xaxis.set_major_locator(mdates.DayLocator())
                    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    st.pyplot(fig1)
                
                # -- 图2: Remaining Tickets Trend --
                with col2:
                    st.subheader("Remaining Tickets Trend")
                    fig2, ax2 = plt.subplots(figsize=(3, 2.2))
                    ax2.plot(df_match["Date"], df_match["Remaining_Tickets"], marker="o", markersize=3, linewidth=1.0, color="navy", label="Tickets")
                    
                    for x_val, y_val in zip(df_match["Date"], df_match["Remaining_Tickets"]):
                        ax2.text(x_val, y_val + 1, f"{int(y_val)}", ha='center', va='bottom', fontsize=5, color="navy")
                    
                    ax2.set_xlabel("Date", fontsize=6)
                    ax2.set_ylabel("Tickets", fontsize=6)
                    ax2.legend(fontsize=5)
                    for spine in ["top", "right", "bottom", "left"]:
                        ax2.spines[spine].set_visible(True)
                    ax2.tick_params(axis='both', which='major', length=4, width=1)
                    ax2.xaxis.set_major_locator(mdates.DayLocator())
                    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    st.pyplot(fig2)
                
                st.markdown("<hr>", unsafe_allow_html=True)

# ============ Tab 3: Raw Data ============
with tab3:
    st.subheader("Raw Aggregated Data (Per Match, Per Day)")
    all_matches = list(df_agg["Match"].unique())
    search_term_raw = st.text_input("Search matches (Raw Data)", "", help="Type partial keywords to filter the matches below.")
    filtered_matches_raw = [m for m in all_matches if search_term_raw.lower() in m.lower()]
    selected_match_raw = st.selectbox("Select a match to view raw data", ["All"] + filtered_matches_raw)

    if not filtered_matches_raw:
        st.warning("No matches found with the given search term.")
    else:
        matches_to_show = filtered_matches_raw if selected_match_raw == "All" else [selected_match_raw]
        if not matches_to_show:
            st.warning("No matches found with the given search term.")
        else:
            df_display = df_agg[df_agg["Match"].isin(matches_to_show)]
            # 使用 AgGrid 实现分页、排序等功能
            AgGrid(df_display, enable_enterprise_modules=False, height=300, fit_columns_on_grid_load=True)

            if "show_passcode_input" not in st.session_state:
                st.session_state["show_passcode_input"] = False

            download_clicked = st.button("Download CSV")
            if download_clicked:
                st.session_state["show_passcode_input"] = True

            if st.session_state["show_passcode_input"]:
                st.info("We need a passcode to proceed with the download. Please enter your passcode.")
                passcode_input = st.text_input("Enter passcode:", value="", type="password")
                valid_passcodes = [f"Trek{i}" for i in range(1, 10)]
                if passcode_input == "":
                    st.info("Please enter the passcode above.")
                elif passcode_input in valid_passcodes:
                    st.success("Verification success! You can download the CSV file now.")
                    csv_data = df_display.to_csv(index=False).encode("utf-8")
                    st.download_button(label="📥 Download CSV", data=csv_data, file_name="daily_lowest_price_and_tickets.csv", mime="text/csv")
                else:
                    st.error("Invalid passcode. Please try again.")

# ============ Tab 4: Arsenal News ============
with tab4:
    st.subheader("Arsenal Official Twitter (X) Timeline")
    twitter_embed_code = """
    <a class="twitter-timeline" href="https://twitter.com/Arsenal?ref_src=twsrc%5Etfw">
    Tweets by Arsenal
    </a>
    <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
    """
    components.html(twitter_embed_code, height=600)

# ---------------------------
# 固定页脚（可添加版权声明等）
# ---------------------------
footer_html = """
<footer>
    © 2025 Arsenal Ticket Market. All Rights Reserved.
</footer>
"""
st.markdown(footer_html, unsafe_allow_html=True)
