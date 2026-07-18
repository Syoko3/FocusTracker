"""Reusable chart helpers for dashboard and history pages."""

import pandas as pd
import streamlit as st


def build_daily_summary(history_df):
    """Create a daily summary table from historical session data."""

    daily_summary = (
        history_df.groupby(history_df["Date"].dt.date)
        .agg(Daily_Study_Time=("Duration (min)", "sum"), Avg_Focus_Score=("Score", "mean"))
        .reset_index()
    )
    daily_summary = daily_summary.rename(columns={"Date": "date"})
    daily_summary["date"] = pd.to_datetime(daily_summary["date"])
    return daily_summary


def build_weekly_summary(history_df):
    """Create a weekly summary table from historical session data."""

    weekly_summary = history_df.copy()
    weekly_summary["week"] = weekly_summary["Date"].dt.to_period("W-MON").astype(str)
    weekly_summary = (
        weekly_summary.groupby("week")
        .agg(Weekly_Study_Time=("Duration (min)", "sum"), Weekly_Avg_Score=("Score", "mean"))
        .reset_index()
    )
    return weekly_summary


def render_daily_study_chart(daily_summary):
    """Render a daily study-time bar chart."""

    if daily_summary.empty:
        return

    st.bar_chart(daily_summary.set_index("date")["Daily_Study_Time"])


def render_focus_trend_chart(daily_summary):
    """Render a focus-score line chart."""

    if daily_summary.empty:
        return

    st.line_chart(daily_summary.set_index("date")["Avg_Focus_Score"])


def render_weekly_progress_chart(weekly_summary):
    """Render a weekly progress bar chart."""

    if weekly_summary.empty:
        return

    st.bar_chart(weekly_summary.set_index("week")["Weekly_Study_Time"])
