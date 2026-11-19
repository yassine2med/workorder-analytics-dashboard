"""Streamlit view. Run: streamlit run src/woa/app.py -- data/work_orders.csv"""
from __future__ import annotations

import sys
from datetime import date

import streamlit as st

from woa.metrics import aging_table, backlog_by, closure_stats, load_work_orders, summary

path = sys.argv[1] if len(sys.argv) > 1 else "data/work_orders.csv"
st.title("Work order analytics")
as_of = st.sidebar.date_input("As of", value=date.today())
df = load_work_orders(path)
building = st.sidebar.multiselect("Building", sorted(df["building"].unique()))
if building:
    df = df[df["building"].isin(building)]

stats = summary(df, as_of)
cols = st.columns(4)
cols[0].metric("Open", stats["open"])
cols[1].metric("Closed", stats["closed"])
cols[2].metric("Oldest open (days)", stats["oldest_open_days"])
cols[3].metric("Open over 30 days (%)", stats["pct_open_over_30_days"])
st.subheader("Open orders by priority and age")
st.dataframe(aging_table(df, as_of))
st.subheader("Open orders by trade")
st.bar_chart(backlog_by(df, "trade"))
st.subheader("Days to close by priority")
st.dataframe(closure_stats(df).round(1))
