"""Reusable metric card helpers for dashboard-style summaries."""

import streamlit as st


def render_metric_card(title, value, delta=None, icon=""):
    """Render a simple metric card with optional delta text."""

    label = f"{icon} {title}".strip()
    st.metric(label, value, delta=delta)


def render_metric_row(metrics):
    """Render a row of metric cards using Streamlit columns."""

    columns = st.columns(len(metrics))
    for column, metric in zip(columns, metrics):
        with column:
            render_metric_card(metric["title"], metric["value"], metric.get("delta"), metric.get("icon", ""))
