import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime
import requests
import streamlit.components.v1 as components

########################################
# 0) 页面配置 + SEO 元信息 (示例)
########################################
st.set_page_config(
    page_title="Arsenal Ticket Market",
    page_icon="⚽",
    layout="wide"
)

# 通过 HTML 注入一些 meta 标签，提升 SEO (有限效果)
seo_html = """
<head>
  <title>Arsenal Ticket Market</title>
  <meta name="description" content="A comprehensive platform for Arsenal match tickets, news, fixtures, and data visualization.">
  <meta name="keywords" content="Arsenal, Tickets, Football, Price, Stats, Premier League">
  <meta name="author" content="Arsenal">
</head>
"""
st.markdown(seo_html, unsafe_allow_html=True)

########################################
# 1) 自定义全局 CSS
########################################
custom_css = """
<style>
/* 引入 Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600&display=swap');

html, body {
    margin: 0;
    padding: 0;
    font-family: 'Open Sans', sans-serif;
    background-color: #f8f9fa; /* 浅灰背景 */
}

/* 顶部导航条 */
.navbar {
    position: fixed;
    top: 0;
    width: 100%;
    background: linear-gradient(90deg, #EF0107 0%, #97010A 100%);
    z-index: 1000;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 60px;
}
.navbar a {
    color: #fff;
    text-decoration: none;
    margin: 0 1.5rem;
    font-weight: 600;
    font-size: 1rem;
    transition: color 0.3s;
}
.navbar a:hover {
    color: #ffe;
}

/* 调整 Streamlit 默认的内边距，以腾出顶部导航空间 */
.css-18e3th9 {
    padding-top: 4rem;
    padding-bottom: 2rem;
    padding-left: 2rem;
    padding-right: 2rem;
}

/* Hero 区域 - 大图背景 */
.hero-section {
    position: relative;
    width: 100%;
    height: 60vh; /* 视窗高度的60% */
    background: url('https://upload.wikimedia.org/wikipedia/commons/8/8c/Emirates_Stadium_-_East_side_-_2015-10-03.jpg');
    background-size: cover;
    background-position: center;
    display: flex;
    justify-content: center;
    align-items: center;
}
.hero-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(239,1,7, 0.6); /* 半透明红色遮罩 */
}
.hero-content {
    position: relative;
    z-index: 2;
    text-align: center;
    color: #fff;
    padding: 1rem;
}
.hero-content h1 {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
    font-weight: 700;
}
.hero-content p {
    font-size: 1.2rem;
    margin-bottom: 1rem;
}

/* 通用标题样式 */
.section-title {
    color: #EF0107;
    font-weight: 600;
    margin: 1rem 0 0.5rem 0;
    font-size: 1.5rem;
    text-align: center;
}

/* 新闻卡片布局 */
.news-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1rem;
    margin: 1rem 0;
}
.news-card {
    background-color: #fff;
    border-radius: 6px;
    overflow: hidden;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    transition: transform 0.3s;
}
.news-card:hover {
    transform: translateY(-3px);
}
.news-card img {
    width: 100%;
    height: 150px;
    object-fit: cover;
}
.news-card-content {
    padding: 0.75rem;
}
.news-card-content h4 {
    margin: 0.5rem 0;
    font-size: 1rem;
    font-weight: 600;
    color: #EF0107;
}
.news-card-content p {
    font-size: 0.9rem;
    color: #555;
}

/* “下一场比赛” & “积分榜” 等模块的卡片 */
.info-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1rem;
    margin: 1rem 0;
}
.info-card {
    background: #fff;
    border-radius: 6px;
    padding: 1rem;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

/* 底部页脚 */
footer {
    text-align: center;
    padding: 1rem;
    color: #555;
    background-color: #f0f0f0;
    font-size: 0.8rem;
    width: 100%;
    border-top: 1px solid #ddd;
    margin-top: 2rem;
}

/* 响应式 */
@media (max-width: 768px) {
    .hero-content h1 {
        font-size: 2rem;
    }
    .hero-content p {
        font-size: 1rem;
    }
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

########################################
# 2) 顶部导航条 (锚点跳转)
########################################
navbar_html = """
<div class="navbar">
    <a href="#home">Home</a>
    <a href="#news">News</a>
    <a href="#matches">Matches</a>
    <a href="#tickets">Tickets</a>
    <a href="#download-data">Download Data</a>
</div>
"""
st.markdown(navbar_html, unsafe_allow_html=True)

########################################
# 3) Hero Section - 大图背景 + 介绍语
########################################
st.markdown("""
<div class="hero-section" id="home">
  <div class="hero-overlay"></div>
  <div class="hero-content">
    <h1>Arsenal Ticket Market</h1>
    <p>Your one-stop hub for Gunners match tickets, news & real-time stats!</p>
  </div>
</div>
""", unsafe_allow_html=True)

########################################
# 4) 准备数据 (缓存读取 Excel 并聚合)
########################################
@st.cache_data(show_spinner=True)
def load_ticket_data(file_path: str):
    if not os.path.exists(file_path):
        return None
    import pandas as pd
    from datetime import datetime

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
        return None

    df_all = pd.concat(dfs, ignore_index=True)
    # 按 [Date, Match] 分组，统计最低票价 & 剩余票数
    df_agg = (
        df_all
        .groupby(["Date", "Match"], sort=False)
        .agg({"Min_Price": "min", "Ticket_Count": "sum"})
        .reset_index()
        .rename(columns={"Min_Price": "Lowest_Price", "Ticket_Count": "Remaining_Tickets"})
    )
    df_agg["Date"] = df_agg["Date"].astype(str)
    return df_agg

file_path = "price_summary.xlsx"
df_agg = load_ticket_data(file_path)

########################################
# 5) 最新新闻 (示例 - 本地化假数据)
########################################
# 在实际项目中，你可以改用 RSS / API 获取真实新闻
demo_news = [
    {
        "title": "Arsenal secures big win in North London Derby",
        "image": "https://upload.wikimedia.org/wikipedia/commons/c/c8/Arsenal_celebrating.jpg",
        "summary": "The Gunners delivered a stunning performance to beat Tottenham...",
        "link": "https://www.arsenal.com/news"  # 或者真实新闻链接
    },
    {
        "title": "Injury update: Key players returning",
        "image": "https://upload.wikimedia.org/wikipedia/commons/5/5c/Arsenal_training_session.jpg",
        "summary": "Team medical staff provides the latest updates on injured players ahead of the weekend fixture...",
        "link": "https://www.arsenal.com/news/injury-update"
    },
    {
        "title": "Emirates Stadium expansion plan",
        "image": "https://upload.wikimedia.org/wikipedia/commons/1/14/Emirates_Stadium_panorama.jpg",
        "summary": "Arsenal board announces a potential expansion to increase stadium capacity by 5,000 seats...",
        "link": "https://www.arsenal.com/news/stadium-expansion"
    }
]

########################################
# 6) 积分榜/下一场比赛等信息 (示例 - 假数据)
########################################
# 你可以改用真实接口或数据库获取
demo_table = pd.DataFrame({
    "Position": [1, 2, 3, 4, 5],
    "Team": ["Arsenal", "Man City", "Liverpool", "Man Utd", "Chelsea"],
    "Points": [72, 70, 65, 60, 55]
})

demo_next_match = {
    "date": "2025-04-01",
    "opponent": "Liverpool",
    "venue": "Emirates Stadium",
    "time": "15:00"
}

########################################
# 7) News Section
########################################
st.markdown('<div id="news"></div>', unsafe_allow_html=True)
st.markdown('<h2 class="section-title">Latest News</h2>', unsafe_allow_html=True)

news_html = '<div class="news-container">'
for item in demo_news:
    news_html += f"""
    <div class="news-card">
        <img src="{item['image']}" alt="news image">
        <div class="news-card-content">
            <h4>{item['title']}</h4>
            <p>{item['summary']}</p>
            <a href="{item['link']}" target="_blank">Read more</a>
        </div>
    </div>
    """
news_html += '</div>'
st.markdown(news_html, unsafe_allow_html=True)

########################################
# 8) Matches Section (下一场比赛 & 积分榜)
########################################
st.markdown('<div id="matches"></div>', unsafe_allow_html=True)
st.markdown('<h2 class="section-title">Matches & Standings</h2>', unsafe_allow_html=True)

# 使用 info-cards 布局
st.markdown('<div class="info-cards">', unsafe_allow_html=True)

# Card 1: 下一场比赛
next_match_html = f"""
<div class="info-card">
  <h3 style="margin-top:0; color:#EF0107;">Next Match</h3>
  <p><b>Date:</b> {demo_next_match['date']}</p>
  <p><b>Opponent:</b> {demo_next_match['opponent']}</p>
  <p><b>Venue:</b> {demo_next_match['venue']}</p>
  <p><b>Kick-off:</b> {demo_next_match['time']}</p>
</div>
"""
st.markdown(next_match_html, unsafe_allow_html=True)

# Card 2: 积分榜
st.markdown('<div class="info-card">', unsafe_allow_html=True)
st.markdown('<h3 style="margin-top:0; color:#EF0107;">Premier League Table</h3>', unsafe_allow_html=True)
st.dataframe(demo_table)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)  # 结束 info-cards

########################################
# 9) Tickets Section - 交互式图表 (Plotly)
########################################
st.markdown('<div id="tickets"></div>', unsafe_allow_html=True)
st.markdown('<h2 class="section-title">Ticket Price Analysis</h2>', unsafe_allow_html=True)

if df_agg is None or df_agg.empty:
    st.warning("No ticket data available.")
else:
    all_matches = sorted(df_agg["Match"].unique())
    selected_match = st.selectbox("Select a match to visualize:", all_matches)
    df_match = df_agg[df_agg["Match"] == selected_match].copy()

    # 将 Date 转回 datetime，方便 Plotly 显示
    df_match["Date_dt"] = pd.to_datetime(df_match["Date"], format="%Y-%m-%d")
    # Plotly 交互式折线图
    fig = px.line(
        df_match,
        x="Date_dt",
        y="Lowest_Price",
        markers=True,
        title=f"Lowest Ticket Price Over Time - {selected_match}",
        labels={"Date_dt": "Date", "Lowest_Price": "Price (£)"}
    )
    fig.update_traces(line_color="#EF0107")
    fig.update_layout(
        xaxis=dict(tickformat="%m-%d"),
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

    # 同时可视化剩余票数
    fig2 = px.line(
        df_match,
        x="Date_dt",
        y="Remaining_Tickets",
        markers=True,
        title=f"Remaining Tickets Over Time - {selected_match}",
        labels={"Date_dt": "Date", "Remaining_Tickets": "Tickets"}
    )
    fig2.update_traces(line_color="navy")
    fig2.update_layout(
        xaxis=dict(tickformat="%m-%d"),
        hovermode="x unified"
    )
    st.plotly_chart(fig2, use_container_width=True)

########################################
# 10) 下载数据区 (带提取码)
########################################
st.markdown('<div id="download-data"></div>', unsafe_allow_html=True)
st.markdown('<h2 class="section-title">Download Raw Data</h2>', unsafe_allow_html=True)

if df_agg is not None and not df_agg.empty:
    st.dataframe(df_agg)
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
            csv_data = df_agg.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name="daily_lowest_price_and_tickets.csv",
                mime="text/csv"
            )
        else:
            st.error("Invalid passcode. Please try again.")
else:
    st.warning("No aggregated data to download.")

########################################
# 11) 页脚
########################################
footer_html = """
<footer>
    © 2025 Arsenal Ticket Market. All Rights Reserved. |
    <a href="#home">Back to top</a>
</footer>
"""
st.markdown(footer_html, unsafe_allow_html=True)
