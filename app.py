import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime

st.title("🎟️ Arsenal Ticket Market Data")

st.write("📌 This page provides daily Arsenal ticket market data and overall trends!")

# 1️⃣ 定义文件
file_path = "price_summary.xlsx"

# 2️⃣ 如果文件不存在，提示错误
if not os.path.exists(file_path):
    st.error("No data found. Please run the analysis to generate 'price_summary.xlsx' first.")
    st.stop()

# 3️⃣ 读取 Excel 所有 Sheet
excel_file = pd.ExcelFile(file_path)
all_sheets = excel_file.sheet_names  # e.g. ["2025-03-18", "2025-03-19", ...]

# 4️⃣ 构建一个空列表，用于存储每日汇总(日期、全场最低价、总票数)
trend_data = []

# 5️⃣ 逐个 Sheet 读取数据，并计算 "GlobalMinPrice" & "TotalTickets"
for sheet in all_sheets:
    df_sheet = pd.read_excel(file_path, sheet_name=sheet)
    
    # 确保数据格式正确
    df_sheet["Min_Price"] = pd.to_numeric(df_sheet["Min_Price"], errors="coerce").fillna(0).astype(int)
    df_sheet["Avg_Price"] = pd.to_numeric(df_sheet["Avg_Price"], errors="coerce").fillna(0).astype(int)
    df_sheet["Ticket_Count"] = pd.to_numeric(df_sheet["Ticket_Count"], errors="coerce").fillna(0).astype(int)
    
    # 计算当天的全场最低价 & 总票数
    global_min_price = df_sheet["Min_Price"].min()
    total_tickets = df_sheet["Ticket_Count"].sum()
    
    # 将结果追加到列表
    # Sheet 名就是日期(YYYY-MM-DD)，转换成真正的日期类型便于排序
    try:
        date_obj = datetime.strptime(sheet, "%Y-%m-%d")
    except:
        # 如果 Sheet 名不是标准日期格式，就跳过或做其他处理
        date_obj = None
    
    trend_data.append({
        "Date": date_obj,
        "SheetName": sheet,  # 保留原始 Sheet 名
        "GlobalMinPrice": global_min_price,
        "TotalTickets": total_tickets
    })

# 6️⃣ 转换为 DataFrame，并按日期排序
df_trend = pd.DataFrame(trend_data).dropna(subset=["Date"])
df_trend = df_trend.sort_values(by="Date").reset_index(drop=True)

# 7️⃣ 显示所有天数的总表
st.subheader("📅 All Days Combined Summary")
st.dataframe(df_trend[["SheetName", "GlobalMinPrice", "TotalTickets"]])

# 8️⃣ 绘制 "最低票价走势"
st.subheader("📈 Minimum Price Trend Over Time")
fig1, ax1 = plt.subplots()
ax1.plot(df_trend["Date"], df_trend["GlobalMinPrice"], marker="o", color="blue", label="Global Min Price")
ax1.set_xlabel("Date")
ax1.set_ylabel("Price (£)")
ax1.legend()
plt.xticks(rotation=45)
st.pyplot(fig1)

# 9️⃣ 绘制 "剩余票数走势"
st.subheader("📈 Total Tickets Trend Over Time")
fig2, ax2 = plt.subplots()
ax2.plot(df_trend["Date"], df_trend["TotalTickets"], marker="o", color="red", label="Total Tickets")
ax2.set_xlabel("Date")
ax2.set_ylabel("Tickets")
ax2.legend()
plt.xticks(rotation=45)
st.pyplot(fig2)

# 🔟 查看最新一天 or 指定一天的详细数据
st.subheader("🔍 View Data for a Specific Day")
selected_sheet = st.selectbox("Select a date", all_sheets[::-1])  # 逆序，让最新日期在最上面
df_selected = pd.read_excel(file_path, sheet_name=selected_sheet)

# 确保数据格式正确
df_selected["Min_Price"] = pd.to_numeric(df_selected["Min_Price"], errors="coerce").fillna(0).astype(int)
df_selected["Avg_Price"] = pd.to_numeric(df_selected["Avg_Price"], errors="coerce").fillna(0).astype(int)
df_selected["Ticket_Count"] = pd.to_numeric(df_selected["Ticket_Count"], errors="coerce").fillna(0).astype(int)

st.dataframe(df_selected)

# 可选：下载按钮（下载选定日期数据）
st.download_button(
    label="📥 Download Selected Date Data",
    data=df_selected.to_csv(index=False).encode("utf-8"),
    file_name=f"{selected_sheet}_data.csv",
    mime="text/csv"
)

st.write("✅ Page updated successfully!")
