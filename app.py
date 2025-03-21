import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates
import os
from datetime import datetime
import streamlit.components.v1 as components

#############################################
# 0) 页面配置
#############################################
st.set_page_config(
    page_title="Arsenal Ticket Market",
    page_icon="⚽",
    layout="wide"
)

#############################################
# 1) 自定义 CSS 与导航栏（响应式）
#############################################
custom_css = """
<style>
/* 引入 Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600&display=swap');
html, body {
    margin: 0;
    padding: 0;
    font-family: 'Open Sans', sans-serif;
    background-color: #f8f9fa;
}

/* 固定顶部导航栏 */
.navbar {
    position: fixed;
    top: 0;
    width: 100%;
    background: rgba(239, 1, 7, 0.9);  /* Arsenal红色半透明 */
    z-index: 1000;
    display: flex;
    justify-content: center;
    padding: 0.5rem 0;
}
.navbar a {
    color: #fff;
    text-decoration: none;
    margin: 0 1rem;
    font-weight: 600;
    font-size: 1rem;
    transition: color 0.3s;
}
.navbar a:hover {
    color: #ffe;
}

/* 调整 Streamlit 默认内边距 */
.css-18e3th9 {
    padding: 4rem 2rem 2rem 2rem; /* 顶部预留导航栏高度 */
}

/* Banner */
.banner-container {
    text-align: center;
    padding: 1.5rem 1rem;
    background: linear-gradient(90deg, #EF0107 0%, #97010A 100%);
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

/* 子标题 */
h2, h3 {
    color: #EF0107;
    margin-top: 0.75rem;
    margin-bottom: 0.5rem;
    font-weight: 600;
}

/* 按钮样式 */
div.stButton > button, div.stDownloadButton > button {
    background-color: #EF0107 !important;
    color: white !important;
    border: none !important;
    padding: 0.5em 1em !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
    cursor: pointer !important;
}

/* 输入标签 */
div.stTextInput > label, div.stSelectbox > label {
    font-weight: 600;
    color: #333;
}

/* 数据表格 */
[data-testid="stDataFrame"] {
    border: 1px solid #ddd;
    border-radius: 4px;
}

/* 页脚 */
footer {
    text-align: center;
    padding: 0.5rem;
    color: #555;
    background-color: #f0f0f0;
    font-size: 0.8rem;
    position: static;
    width: 100%;
    border-top: 1px solid #ddd;
}

/* 媒体查询，手机端调整 */
@media (max-width: 600px) {
    .navbar a {
        margin: 0 0.5rem;
        font-size: 0.9rem;
    }
    .banner-container h1 {
        font-size: 1.5rem;
    }
    .banner-container p {
        font-size: 0.9rem;
    }
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# 自定义导航栏（点击后通过锚点跳转对应Tab内容）
navbar = """
<div class="navbar">
    <a href="#overview">Overview</a>
    <a href="#price-trends">Price Trends</a>
    <a href="#raw-data">Raw Data</a>
    <a href="#arsenal-news">Arsenal News</a>
</div>
"""
st.markdown(navbar, unsafe_allow_html=True)

#############################################
# 2) 全局图表风格（保留原有设置，不再额外细化网格）
#############################################
sns.set_theme(style="white")
plt.rcParams.update({
    "font.size": 6,
    "axes.titlesize": 6,
    "axes.labelsize": 6,
    "xtick.labelsize": 5,
    "ytick.labelsize": 5,
    "axes.spines.top": True,
    "axes.spines.right": True
})

#############################################
# 3) 顶部 Banner
#############################################
logo_url = "https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg"
st.markdown(
    f"""
    <div class="banner-container" id="overview">
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
    all_sheets = excel_file.sheet_names

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
        df_temp["Ticket_Count"] = pd.to_numeric(df_temp["Ticket_Count"], errors="coerce").fillna(0).astype(int)
        dfs.append(df_temp[["Date", "Match", "Min_Price", "Ticket_Count"]])

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
# 5) 数据聚合：只统计最低票价与剩余票数
#############################################
df_agg = (
    df_all
    .groupby(["Date", "Match"], sort=False)
    .agg({"Min_Price": "min", "Ticket_Count": "sum"})
    .reset_index()
    .rename(columns={"Min_Price": "Lowest_Price", "Ticket_Count": "Remaining_Tickets"})
    .reset_index(drop=True)
)
df_agg["Date"] = df_agg["Date"].astype(str)
max_date = df_agg["Date"].max() if not df_agg.empty else None
df_overview_latest = df_agg[df_agg["Date"] == max_date][["Match", "Lowest_Price", "Remaining_Tickets"]]

#############################################
# 6) Streamlit 界面布局 - Tabs（增加锚点以便导航跳转）
#############################################
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Price Trends", "Raw Data", "Arsenal News"])

# ============ Tab 1: Overview ============
with tab1:
    st.markdown("<div id='overview'></div>", unsafe_allow_html=True)
    st.subheader("Latest Date Overview")
    if max_date is None or df_overview_latest.empty:
        st.warning("No data for latest date.")
    else:
        st.write(f"**Latest Date**: {max_date}")
        st.write("Below shows each match's Lowest_Price & Remaining_Tickets on this date:")
        st.dataframe(df_overview_latest)

# ============ Tab 2: Price Trends ============
with tab2:
    st.markdown("<div id='price-trends'></div>", unsafe_allow_html=True)
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
                # 图1: Lowest Price Trend
                with col1:
                    st.subheader("Lowest Price Trend")
                    fig1, ax1 = plt.subplots(figsize=(3, 2.2))
                    date_x = pd.to_datetime(df_match["Date"], format="%Y-%m-%d")
                    ax1.plot(date_x, df_match["Lowest_Price"], marker="o", markersize=3, linewidth=1.0, color="#EF0107", label="Lowest Price")
                    for x_val, y_val in zip(date_x, df_match["Lowest_Price"]):
                        ax1.text(x_val, y_val + 1, f"{int(y_val)}", ha='center', va='bottom', fontsize=5, color="#EF0107")
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
                # 图2: Remaining Tickets Trend
                with col2:
                    st.subheader("Remaining Tickets Trend")
                    fig2, ax2 = plt.subplots(figsize=(3, 2.2))
                    date_x = pd.to_datetime(df_match["Date"], format="%Y-%m-%d")
                    ax2.plot(date_x, df_match["Remaining_Tickets"], marker="o", markersize=3, linewidth=1.0, color="navy", label="Tickets")
                    for x_val, y_val in zip(date_x, df_match["Remaining_Tickets"]):
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
    st.markdown("<div id='raw-data'></div>", unsafe_allow_html=True)
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
            st.dataframe(df_display)
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
    st.markdown("<div id='arsenal-news'></div>", unsafe_allow_html=True)
    st.subheader("Arsenal Official Twitter (X) Timeline")
    # 限制 Twitter Timeline 宽度为600px，手机端自适应；同时去除 header/footer，保持页面简洁
    twitter_embed_code = """
    <style>
    .twitter-timeline {
      width: 600px !important;
      max-width: 100% !important;
      margin: 0 auto !important;
    }
    </style>
    <a class="twitter-timeline"
       data-width="600"
       data-height="2000"
       data-theme="light"
       data-chrome="noheader nofooter"
       href="https://twitter.com/Arsenal?ref_src=twsrc%5Etfw">
       Posts from @Arsenal
    </a>
    <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
    """
    components.html(twitter_embed_code, height=2100, scrolling=True)

#############################################
# 固定页脚
#############################################
footer_html = """
<footer>
    © 2025 Arsenal Ticket Market. All Rights Reserved.
</footer>
"""
st.markdown(footer_html, unsafe_allow_html=True)
