import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# **🌍 Webpage Title**
st.title("🎟️ Arsenal Ticket Market Data")

st.write("📌 This page provides the latest Arsenal ticket market data, updated daily!")

# **📂 Load Data**
df = pd.read_excel("price_summary.xlsx")

# **🔍 Ensure Data Formats**
df["Seat Type"] = df["Seat Type"].astype(str)
df["Min_Price"] = pd.to_numeric(df["Min_Price"], errors="coerce").fillna(0).astype(int)
df["Avg_Price"] = pd.to_numeric(df["Avg_Price"], errors="coerce").fillna(0).astype(int)
df["Ticket_Count"] = pd.to_numeric(df["Ticket_Count"], errors="coerce").fillna(0).astype(int)

# **📊 Display Data Table**
st.subheader("📋 Ticket Prices & Availability")
st.dataframe(df)

# **📥 Download Button**
st.download_button("📥 Download Excel", df.to_csv(index=False).encode("utf-8"), "ticket_data.csv", "text/csv")

# **📈 Price Distribution Chart**
st.subheader("📊 Price Distribution")
fig, ax = plt.subplots()
ax.bar(df["Seat Type"], df["Min_Price"], label="Min Price", alpha=0.7)
ax.bar(df["Seat Type"], df["Avg_Price"], label="Avg Price", alpha=0.7)
plt.xticks(rotation=45)
plt.ylabel("Price (£)")
plt.legend()
st.pyplot(fig)

# **📊 Total Remaining Tickets**
st.metric("🎟️ Total Remaining Tickets", df["Ticket_Count"].sum())
