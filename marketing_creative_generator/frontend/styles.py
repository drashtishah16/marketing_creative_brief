"""Styling utilities, CSS definitions, and HTML UI component helpers for Streamlit."""

from __future__ import annotations

import streamlit as st


def apply_custom_styles() -> None:
    """Inject custom responsive CSS into the Streamlit app."""
    css = """
    <style>
    /* Global App Container */
    .main .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2.5rem;
        max-width: 1200px;
    }

    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, #f8fafc 0%, #edf2f7 100%);
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1.1rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: transform 0.15s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
    }
    .metric-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #1e293b;
        margin: 0.2rem 0;
    }
    .metric-label {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
    }

    /* Status Badges */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.65rem;
        font-size: 0.8rem;
        font-weight: 600;
        border-radius: 9999px;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    .badge-pending {
        background-color: #fef3c7;
        color: #92400e;
        border: 1px solid #fde68a;
    }
    .badge-approved {
        background-color: #d1fae5;
        color: #065f46;
        border: 1px solid #a7f3d0;
    }
    .badge-rejected {
        background-color: #fee2e2;
        color: #991b1b;
        border: 1px solid #fecaca;
    }
    .badge-revision {
        background-color: #e0e7ff;
        color: #3730a3;
        border: 1px solid #c7d2fe;
    }

    /* Severity Badges */
    .badge-high {
        background-color: #fee2e2;
        color: #b91c1c;
        border: 1px solid #fca5a5;
    }
    .badge-medium {
        background-color: #fef3c7;
        color: #b45309;
        border: 1px solid #fcd34d;
    }
    .badge-low {
        background-color: #f1f5f9;
        color: #475569;
        border: 1px solid #cbd5e1;
    }

    /* Variant Display Box */
    .variant-box {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1.25rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }

    /* Disclaimer Bar */
    .compliance-banner {
        background-color: #f8fafc;
        border-left: 4px solid #3b82f6;
        padding: 0.75rem 1rem;
        margin-bottom: 1rem;
        border-radius: 0 6px 6px 0;
        font-size: 0.86rem;
        color: #334155;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_metric_card(label: str, value: Any, color: str = "#1e293b") -> None:
    """Render a styled metric card."""
    html = f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value" style="color: {color};">{value}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def get_status_badge(status: str) -> str:
    """Return HTML string for review status badge."""
    st_lower = status.lower()
    if "approved" in st_lower:
        cls_name = "badge-approved"
    elif "reject" in st_lower:
        cls_name = "badge-rejected"
    elif "revision" in st_lower:
        cls_name = "badge-revision"
    else:
        cls_name = "badge-pending"

    return f'<span class="badge {cls_name}">{status}</span>'


def get_severity_badge(severity: str) -> str:
    """Return HTML string for claim warning severity badge."""
    sev_lower = severity.lower()
    if sev_lower == "high":
        cls_name = "badge-high"
    elif sev_lower == "medium":
        cls_name = "badge-medium"
    else:
        cls_name = "badge-low"

    return f'<span class="badge {cls_name}">{severity} Severity</span>'
