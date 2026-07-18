"""Privacy page explaining how FocusTracker keeps study data local."""

import streamlit as st

from components.sidebar import render_sidebar


def main():
    """Render the privacy overview page."""

    render_sidebar()

    st.title("🔒 Privacy")
    st.caption("FocusTracker is built to keep your study data on your own computer.")
    st.divider()

    st.success(
        """
    ✔ No login required

    ✔ No cloud storage

    ✔ Data stays on your computer

    ✔ AI scoring happens locally

    ✔ You control your own data
    """
    )

    st.markdown(
        """
    ### How your data is handled

    - **Local-only storage.** Sessions are saved to a JSON file on this device.
    - **No accounts.** Nothing is uploaded, synced, or shared with a server.
    - **Local scoring.** Focus scores are computed on-device, never sent away.
    - **Your control.** Delete the local data file at any time to remove your history.
    """
    )


main()
