"""Helpers for exporting focus-session reports (PDF, CSV, JSON, plain text).

The text builders return strings and the PDF builders return bytes, so pages can
hand either straight to ``st.download_button``. Durations are surfaced in minutes
for readability while the raw JSON export keeps the canonical records unchanged.
"""

import csv
import io
import json
import os
import tempfile

from fpdf import FPDF

from services import analytics

try:
    import matplotlib
    import matplotlib.pyplot as plt

    matplotlib.use("Agg")
except ImportError:  # pragma: no cover - exercised when optional dependency absent
    matplotlib = None
    plt = None


CSV_COLUMNS = ["Date", "Duration (min)", "Score", "Pauses", "Title"]


def sessions_to_csv(sessions) -> str:
    """Render sessions as a CSV document string with a header row."""

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_COLUMNS)

    for session in sessions:
        day = analytics.parse_date(session.get("date"))
        writer.writerow(
            [
                day.isoformat() if day else "",
                round(analytics.session_minutes(session), 1),
                round(analytics.session_score(session)),
                analytics.session_pauses(session),
                session.get("title", "Focus Session"),
            ]
        )

    return buffer.getvalue()


def sessions_to_json(sessions) -> str:
    """Render sessions as a pretty-printed JSON array string."""

    return json.dumps(list(sessions), indent=2)


def session_summary_text(session) -> str:
    """Render a single session as a human-readable plain-text report."""

    day = analytics.parse_date(session.get("date"))
    minutes = analytics.session_minutes(session)

    lines = [
        "FocusTracker Session Report",
        "===========================",
        f"Title:    {session.get('title', 'Focus Session')}",
        f"Date:     {day.isoformat() if day else 'Unknown'}",
        f"Duration: {analytics.format_duration(minutes)}",
        f"Score:    {analytics.session_score(session):.0f}%",
        f"Pauses:   {analytics.session_pauses(session)}",
    ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------
def _pdf_text(value) -> str:
    """Coerce a value to text the core PDF fonts (latin-1) can render."""

    return str(value).encode("latin-1", "replace").decode("latin-1")


def _new_pdf() -> FPDF:
    """Create an A4 PDF with a first page and sensible page breaks."""

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    return pdf


def _build_sessions_chart_bytes(sessions) -> bytes | None:
    """Create a simple study-time chart image for the provided sessions."""

    if plt is None:
        return None

    frame = analytics.to_dataframe(sessions)
    if frame.empty:
        return None

    chart_frame = (
        frame.groupby("Date")
        .agg({"Duration (min)": "sum"})
        .reset_index()
    )
    if chart_frame.empty:
        return None

    fig, ax = plt.subplots(figsize=(6.2, 2.8), dpi=120)
    ax.bar(chart_frame["Date"].dt.strftime("%Y-%m-%d"), chart_frame["Duration (min)"], color="#2563eb")
    ax.set_title("Study Time by Day")
    ax.set_ylabel("Duration (min)")
    ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight")
    plt.close(fig)
    return buffer.getvalue()


def _embed_chart_in_pdf(pdf: FPDF, sessions) -> None:
    """Attach a generated chart image to the report when data is available."""

    image_bytes = _build_sessions_chart_bytes(sessions)
    if not image_bytes:
        return

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
        handle.write(image_bytes)
        temp_path = handle.name

    try:
        pdf.ln(10)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, _pdf_text("Study Trend"))
        pdf.ln(8)
        pdf.image(temp_path, x=20, y=pdf.get_y(), w=170)
        pdf.ln(70)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def sessions_to_pdf(sessions) -> bytes:
    """Render all sessions as a titled PDF table and return the file bytes."""

    pdf = _new_pdf()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "FocusTracker Session Report")
    pdf.ln(12)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, _pdf_text(f"Total sessions: {len(sessions)}"))
    pdf.ln(10)

    _embed_chart_in_pdf(pdf, sessions)

    widths = [26, 30, 18, 18, 88]
    pdf.set_font("Helvetica", "B", 10)
    for header, width in zip(CSV_COLUMNS, widths):
        pdf.cell(width, 8, _pdf_text(header), border=1)
    pdf.ln(8)

    pdf.set_font("Helvetica", "", 10)
    for session in sessions:
        day = analytics.parse_date(session.get("date"))
        title = session.get("title", "Focus Session")
        if len(title) > 45:
            title = title[:42] + "..."
        row = [
            day.isoformat() if day else "",
            f"{analytics.session_minutes(session):.1f}",
            f"{analytics.session_score(session):.0f}",
            str(analytics.session_pauses(session)),
            title,
        ]
        for value, width in zip(row, widths):
            pdf.cell(width, 8, _pdf_text(value), border=1)
        pdf.ln(8)

    return bytes(pdf.output())


def session_summary_pdf(session) -> bytes:
    """Render a single session as a one-page PDF report and return the bytes."""

    day = analytics.parse_date(session.get("date"))
    minutes = analytics.session_minutes(session)

    pdf = _new_pdf()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "FocusTracker Session Report")
    pdf.ln(16)

    fields = [
        ("Title", session.get("title", "Focus Session")),
        ("Date", day.isoformat() if day else "Unknown"),
        ("Duration", analytics.format_duration(minutes)),
        ("Score", f"{analytics.session_score(session):.0f}%"),
        ("Pauses", str(analytics.session_pauses(session))),
    ]
    for label, value in fields:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(30, 8, _pdf_text(f"{label}:"))
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 8, _pdf_text(value))
        pdf.ln(8)

    return bytes(pdf.output())
