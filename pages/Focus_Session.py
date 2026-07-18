"""Focus-session page for starting, pausing, ending, scoring, and saving sessions."""

import streamlit as st

from components.sidebar import render_sidebar
from components.timer import render_timer_ui


def main():
    """Render the focus-session page with the shared timer UI."""

    render_sidebar()

    st.title("⏱️ Focus Session")
    st.caption("Start a focused work block, pause when needed, and end with an AI-style score.")
    render_timer_ui()


main()
