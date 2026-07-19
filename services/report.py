"""Helpers for exporting focus-session reports (PDF, CSV, JSON, plain text).

The text builders return strings and the PDF builders return bytes, so pages can
hand either straight to ``st.download_button``. Durations are surfaced in minutes
for readability while the raw JSON export keeps the canonical records unchanged.
"""

import csv
import io
import json

from fpdf import FPDF

from services import analytics


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


def sessions_to_pdf(sessions) -> bytes:
    """Render all sessions as a titled PDF table and return the file bytes."""

    pdf = _new_pdf()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "FocusTracker Session Report")
    pdf.ln(12)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, _pdf_text(f"Total sessions: {len(sessions)}"))
    pdf.ln(10)

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
