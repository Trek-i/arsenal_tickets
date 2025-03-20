import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
from datetime import datetime

# ---------------------------
# 自定义 CSS 样式 (Arsenal 风格)
# ---------------------------
custom_css = """
<style>
/* 整体背景和字体 */
body {
    background-color: #f4f4f4;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* 标题与子标题 */
h1, h2, h3 {
    color: #EF0107; /* Arsenal 红 */
}

/* 自定义按钮样式 */
div.stButton > button {
    background-color: #EF0107;
    color: white;
    border: none;
    padding: 0.5em 1em;
    border-radius: 4px;
    font-weight: bold;
}

/* 数据表格样式 */
.css-1d391kg {
    font-size: 0.9em;
}

/* 图表内文字提示调整 */
.matplotlib-text {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ---------------------------
# 页面基础设置与 Banner
# ---------------------------
st.set_page_config(
    page_title="Arsenal Ticket Market",
    page_icon="⚽",
    layout="wide"
)

# 替换为 Arsenal 官方 logo 链接（这里仅示例）
logo_url = "https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg"
st.markdown(
    f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <img src="{logo_url}" alt="Arsenal Logo" style="height:80px;">
        <h1 style='margin: 10px 0; color: #EF0107;'>Arsenal Ticket Market Data</h1>
        <p>One day, one time point! Each match shows its <b>lowest price</b> and <b>remaining tickets</b> over time.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# ---------------------------
# 缓存加载 Excel 数据
# ---------------------------
@st.cache_data(show_spinner=True)
def load_excel_data(file_path):
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

# ---------------------------
# 数据聚合：对 [Date, Match] 分组
# ---------------------------
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
max_date = df_agg["Date"].max() if not df_agg.empty else None
df_overview_latest = df_agg[df_agg["Date"] == max_date][["Match", "Lowest_Price", "Remaining_Tickets"]]

# ---------------------------
# Streamlit 界面布局 - Tabs
# ---------------------------
tab1, tab2, tab3 = st.tabs(["Overview", "Price Trends", "Raw Data"])

# -------- Tab 1: Overview --------
with tab1:
    st.subheader("📊 Latest Date Overview")
    if max_date is None or df_overview_latest.empty:
        st.warning("No data for latest date.")
    else:
        st.write(f"**Latest Date**: {max_date}")
        st.write("Below shows each match's lowest price & remaining tickets on this date:")
        st.dataframe(df_overview_latest)

# -------- Tab 2: Price Trends --------
with tab2:
    st.subheader("📈 Daily Price & Tickets Trend (One day, one point) - Each Match Separately")
    if df_agg.empty:
        st.warning("No data to plot.")
    else:
        all_matches = list(df_agg["Match"].unique())
        search_term = st.text_input(
            "Search matches (Price Trends)",
            "",
            help="Type partial keywords to filter the matches below."
        )
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
                # 图表1：Lowest Price Trend
                with col1:
                    st.subheader("Lowest Price Trend")
                    fig1, ax1 = plt.subplots(figsize=(3, 2.2))
                    ax1.plot(
                        df_match["Date"],
                        df_match["Lowest_Price"],
                        marker="o",
                        markersize=2,
                        linewidth=0.8,
                        color="#EF0107",  # Arsenal 红
                        label="Lowest Price"
                    )
                    for x_val, y_val in zip(df_match["Date"], df_match["Lowest_Price"]):
                        ax1.text(
                            x_val, y_val + 1,
                            f"{int(y_val)}",
                            ha='center', va='bottom',
                            fontsize=4,
                            color="#EF0107"
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
                # 图表2：Remaining Tickets Trend
                with col2:
                    st.subheader("Remaining Tickets Trend")
                    fig2, ax2 = plt.subplots(figsize=(3, 2.2))
                    ax2.plot(
                        df_match["Date"],
                        df_match["Remaining_Tickets"],
                        marker="o",
                        markersize=2,
                        linewidth=0.8,
                        color="navy", 
                        label="Tickets"
                    )
                    for x_val, y_val in zip(df_match["Date"], df_match["Remaining_Tickets"]):
                        ax2.text(
                            x_val, y_val + 1,
                            f"{int(y_val)}",
                            ha='center', va='bottom',
                            fontsize=4,
                            color="navy"
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
                st.markdown("<hr>", unsafe_allow_html=True)

# -------- Tab 3: Raw Data --------
with tab3:
    st.subheader("📜 Raw Aggregated Data (Per Match, Per Day)")
    all_matches = list(df_agg["Match"].unique())
    search_term_raw = st.text_input(
        "Search matches (Raw Data)",
        "",
        help="Type partial keywords to filter the matches below."
    )
    filtered_matches_raw = [m for m in all_matches if search_term_raw.lower() in m.lower()]
    selected_match_raw = st.selectbox("Select a match to view raw data", ["All"] + filtered_matches_raw)
    matches_to_show = filtered_matches_raw if selected_match_raw == "All" else [selected_match_raw]
    if not matches_to_show:
        st.warning("No matches found with the given search term.")
    else:
        df_display = df_agg[df_agg["Match"].isin(matches_to_show)]
        st.dataframe(df_display)
        csv_data = df_display.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name="daily_lowest_price_and_tickets.csv",
            mime="text/csv"
        )

# 底部分割与成功提示
st.markdown("<br><hr style='border:1px solid #bbb' />", unsafe_allow_html=True)
st.write("✅ Data successfully loaded & displayed!")
