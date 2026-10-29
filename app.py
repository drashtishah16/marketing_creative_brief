"""Marketing Creative Brief & Ad Variant Generator.

A comprehensive Streamlit application for transforming product information into
structured creative briefs, generating multi-angle advertising variants, enforcing
brand rules, auditing claim substantiation, and managing human review workflows.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if PROJECT_ROOT.name != "marketing_creative_generator":
    nested = PROJECT_ROOT / "marketing_creative_generator"
    if nested.exists() and str(nested) not in sys.path:
        sys.path.insert(0, str(nested))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import plotly.express as px
import streamlit as st

from backend.ad_variant_generator import AdVariantGenerator
from backend.approval_service import ApprovalService
from backend.brief_generator import CreativeBriefGenerator
from backend.campaign_service import CampaignService
from backend.database import DEFAULT_DB_PATH, init_db
from backend.evidence_checker import COMPLIANCE_DISCLAIMER, EvidenceChecker
from backend.export_service import ExportService
from backend.seed_data import seed_sample_data
from frontend.styles import apply_custom_styles, get_severity_badge, get_status_badge, render_metric_card

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("marketing_app")

# Streamlit Page Configuration
st.set_page_config(
    page_title="Marketing Creative Brief & Ad Variant Generator",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply CSS
apply_custom_styles()

# Initialize DB
init_db(DEFAULT_DB_PATH)

# Initialize Services
camp_svc = CampaignService(DEFAULT_DB_PATH)
brief_svc = CreativeBriefGenerator(DEFAULT_DB_PATH)
variant_svc = AdVariantGenerator(DEFAULT_DB_PATH)
appr_svc = ApprovalService(DEFAULT_DB_PATH)
ev_svc = EvidenceChecker(DEFAULT_DB_PATH)
export_svc = ExportService(DEFAULT_DB_PATH)


# =============================================================================
# SIDEBAR NAVIGATION & STATE MANAGEMENT
# =============================================================================

NAV_PAGES = [
    "📊 Dashboard",
    "📁 Campaigns Directory",
    "➕ Create New Campaign",
    "📝 Campaign Workspace",
    "🛡️ Brand Guidelines",
    "⚖️ Claims & Evidence Audit",
    "💾 Exports & Reports",
]

if "nav_choice" not in st.session_state:
    st.session_state["nav_choice"] = "📊 Dashboard"

if st.session_state["nav_choice"] not in NAV_PAGES:
    st.session_state["nav_choice"] = "📊 Dashboard"

current_nav_index = NAV_PAGES.index(st.session_state["nav_choice"])

st.sidebar.title("🎯 Creative Generator")
st.sidebar.caption("M.Sc. IT Marketing & Compliance Platform")

selected_nav = st.sidebar.radio(
    "Navigation",
    NAV_PAGES,
    index=current_nav_index,
    key="nav_radio",
)

# Keep session_state in sync with user radio clicks
if selected_nav != st.session_state["nav_choice"]:
    st.session_state["nav_choice"] = selected_nav
    st.rerun()

nav_choice = st.session_state["nav_choice"]

st.sidebar.divider()

# Sample Data Seeder Button in Sidebar
if st.sidebar.button("🌱 Seed Sample Campaigns", use_container_width=True):
    seed_sample_data(DEFAULT_DB_PATH, force=True)
    st.session_state["seed_banner"] = True
    st.rerun()

if st.session_state.pop("seed_banner", False):
    st.sidebar.success("Demonstration campaigns seeded successfully!")

st.sidebar.info(
    "🔒 **Fact Integrity Guarantee**\n\n"
    "This system uses deterministic templates and grounded logic. "
    "It never fabricates unverified features, statistics, or discounts."
)


# =============================================================================
# PAGE 1: DASHBOARD
# =============================================================================

if nav_choice == "📊 Dashboard":
    st.title("📊 Marketing Campaign & Compliance Dashboard")
    st.write(
        "Real-time visibility into marketing campaigns, copy generation variants, "
        "evidence requirements, and human review decisions."
    )

    metrics = camp_svc.get_dashboard_metrics()

    # Metric Cards Row
    m_col1, m_col2, m_col3, m_col4, m_col5, m_col6 = st.columns(6)
    with m_col1:
        render_metric_card("Total Campaigns", metrics["total_campaigns"], "#2563eb")
    with m_col2:
        render_metric_card("Total Variants", metrics["total_variants"], "#0891b2")
    with m_col3:
        render_metric_card("Pending Review", metrics["pending_review"], "#d97706")
    with m_col4:
        render_metric_card("Approved", metrics["approved_variants"], "#16a34a")
    with m_col5:
        render_metric_card("Rejected", metrics["rejected_variants"], "#dc2626")
    with m_col6:
        render_metric_card("High Warnings", metrics["high_severity_warnings"], "#991b1b")

    st.markdown("---")

    if metrics["total_campaigns"] == 0:
        st.info("💡 No campaigns found in the database yet. Click the **'Seed Sample Campaigns'** button in the sidebar or create a new campaign to begin.")
        col_cta1, col_cta2 = st.columns(2)
        with col_cta1:
            if st.button("🌱 Populate Sample Demonstration Data", type="primary", use_container_width=True):
                seed_sample_data(DEFAULT_DB_PATH, force=True)
                st.rerun()
        with col_cta2:
            if st.button("➕ Create Your First Campaign", use_container_width=True):
                st.session_state["nav_choice"] = "➕ Create New Campaign"
                st.rerun()
    else:
        # Chart Row
        c_col1, c_col2 = st.columns(2)

        with c_col1:
            st.subheader("Variant Review Status")
            st_dist = metrics["status_distribution"]
            if st_dist:
                fig_status = px.pie(
                    names=list(st_dist.keys()),
                    values=list(st_dist.values()),
                    hole=0.45,
                    color=list(st_dist.keys()),
                    color_discrete_map={
                        "Approved": "#22c55e",
                        "Pending Review": "#f59e0b",
                        "Rejected": "#ef4444",
                        "Needs Revision": "#6366f1",
                    },
                )
                fig_status.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300)
                st.plotly_chart(fig_status, use_container_width=True)
            else:
                st.caption("No variants generated yet.")

        with c_col2:
            st.subheader("Variants by Marketing Angle")
            angle_dist = metrics["angle_distribution"]
            if angle_dist:
                fig_angle = px.bar(
                    x=list(angle_dist.values()),
                    y=list(angle_dist.keys()),
                    orientation="h",
                    labels={"x": "Count", "y": "Marketing Angle"},
                    color_discrete_sequence=["#3b82f6"],
                )
                fig_angle.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300)
                st.plotly_chart(fig_angle, use_container_width=True)
            else:
                st.caption("No angle distribution data.")

        # Quick Actions & Recent Campaigns Table
        st.subheader("Recent Campaigns")
        recent_campaigns = camp_svc.list_campaigns()[:5]
        summary_rows = []
        for rc in recent_campaigns:
            summary_rows.append({
                "Campaign Name": rc["name"],
                "Product": rc["product_name"],
                "Objective": rc["objective"].title(),
                "Channel": rc["channel"].title(),
                "Tone": rc["tone_of_voice"],
                "Created": rc["created_at"][:10],
            })
        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

        col_act1, col_act2 = st.columns(2)
        with col_act1:
            if st.button("➕ Create New Campaign", use_container_width=True):
                st.session_state["nav_choice"] = "➕ Create New Campaign"
                st.rerun()
        with col_act2:
            if st.button("⚖️ Open Claims Audit Center", use_container_width=True):
                st.session_state["nav_choice"] = "⚖️ Claims & Evidence Audit"
                st.rerun()


# =============================================================================
# PAGE 2: CAMPAIGNS DIRECTORY
# =============================================================================

elif nav_choice == "📁 Campaigns Directory":
    st.title("📁 Marketing Campaigns Directory")
    st.write("Browse, search, duplicate, or inspect saved marketing campaigns.")

    # Filter Controls
    f_col1, f_col2, f_col3 = st.columns([2, 1, 1])
    with f_col1:
        search_query = st.text_input("🔍 Search by Campaign or Product Name", "")
    with f_col2:
        filter_obj = st.selectbox(
            "Filter by Objective",
            ["All", "Awareness", "Traffic", "Leads", "Conversions", "Retention"],
        )
    with f_col3:
        filter_chan = st.selectbox(
            "Filter by Channel",
            ["All", "Social Media", "Search Advertising", "Email", "Display Advertising"],
        )

    campaigns = camp_svc.list_campaigns(
        search_query=search_query,
        objective=filter_obj,
        channel=filter_chan,
    )

    if not campaigns:
        st.warning("No matching campaigns found.")
        if st.button("➕ Create New Campaign"):
            st.session_state["nav_choice"] = "➕ Create New Campaign"
            st.rerun()
    else:
        st.caption(f"Showing {len(campaigns)} campaign(s)")
        for c in campaigns:
            with st.expander(f"📌 {c['name']} — {c['product_name']} ({c['channel'].title()})", expanded=False):
                c_details_1, c_details_2 = st.columns([3, 1])
                with c_details_1:
                    st.write(f"**Description:** {c['product_description']}")
                    st.write(f"**Target Audience:** {c['target_audience']}")
                    st.write(f"**Tone:** {c['tone_of_voice']} | **Objective:** {c['objective'].title()}")
                    if c.get("offer"):
                        st.write(f"**Active Offer:** {c['offer']}")

                with c_details_2:
                    st.write(f"**ID:** `{c['id']}`")
                    st.write(f"**Updated:** {c['updated_at'][:10]}")

                    # Actions with programmatic navigation
                    if st.button("🚀 Open Workspace", key=f"open_{c['id']}", use_container_width=True):
                        st.session_state["selected_campaign_id"] = c["id"]
                        st.session_state["nav_choice"] = "📝 Campaign Workspace"
                        st.rerun()

                    if st.button("📋 Duplicate", key=f"dup_{c['id']}", use_container_width=True):
                        dup = camp_svc.duplicate_campaign(c["id"])
                        if dup:
                            st.success(f"Duplicated as '{dup['name']}'")
                            st.rerun()

                    # Delete with confirmation popover
                    with st.popover("🗑️ Delete", use_container_width=True):
                        st.write("Are you sure? This permanently deletes the campaign, brief, and all variants.")
                        if st.button("Confirm Delete", key=f"del_confirm_{c['id']}", type="primary"):
                            camp_svc.delete_campaign(c["id"])
                            st.success("Campaign deleted.")
                            st.rerun()


# =============================================================================
# PAGE 3: CREATE NEW CAMPAIGN
# =============================================================================

elif nav_choice == "➕ Create New Campaign":
    st.title("➕ Create New Marketing Campaign")
    st.write(
        "Enter comprehensive product and campaign parameters. All inputs are preserved strictly; "
        "missing facts are never fabricated."
    )

    # Fetch available brand profiles
    brand_profiles = camp_svc.list_brand_profiles()
    bp_options = {"None (Custom Brand Rules)": None}
    for bp in brand_profiles:
        bp_options[f"{bp['name']} ({bp['brand_name']})"] = bp["id"]

    with st.form("create_campaign_form"):
        st.subheader("1. Campaign & Brand Identity")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            camp_name = st.text_input("Campaign Name *", placeholder="e.g. Q4 CloudSync Enterprise Sprint")
            prod_name = st.text_input("Product or Service Name *", placeholder="e.g. CloudSync Pro")
        with col_c2:
            brand_name = st.text_input("Brand Name", placeholder="e.g. Apex Software")
            sel_bp_name = st.selectbox("Link Reusable Brand Profile (Optional)", list(bp_options.keys()))

        st.subheader("2. Product Description & Capabilities")
        prod_desc = st.text_area(
            "Product / Service Description *",
            placeholder="Detailed description of what the product does and its core utility...",
            height=100,
        )
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            features_raw = st.text_area(
                "Main Features (One per line)",
                placeholder="• Instant delta syncing\n• Zero-knowledge 256-bit AES encryption\n• Audit logging",
                height=110,
            )
        with col_f2:
            benefits_raw = st.text_area(
                "Customer Benefits (One per line)",
                placeholder="• Protect client confidentiality\n• Save 5+ hours on document sharing weekly\n• Eliminate data leakage risks",
                height=110,
            )

        st.subheader("3. Target Audience & Strategy")
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            target_aud = st.text_input("Target Audience *", placeholder="e.g. Boutique law firms and compliance officers")
            aud_needs = st.text_area("Audience Needs / Problems / Motivations", placeholder="Struggling with unencrypted attachments and strict privacy compliance.", height=70)
        with col_a2:
            objective = st.selectbox("Campaign Objective *", ["Awareness", "Traffic", "Leads", "Conversions", "Retention"])
            channel = st.selectbox("Advertising Channel *", ["Social Media", "Search Advertising", "Email", "Display Advertising"])
            tone = st.selectbox("Preferred Tone of Voice *", ["Professional", "Friendly", "Conversational", "Educational", "Premium", "Playful"])

        st.subheader("4. Campaign Offer & Incentives (Optional)")
        col_o1, col_o2 = st.columns(2)
        with col_o1:
            offer = st.text_input("Promotional Offer", placeholder="e.g. 20% off annual plan or 14-day free pilot")
        with col_o2:
            offer_conditions = st.text_input("Offer Conditions & Expiry", placeholder="e.g. Minimum 10 seats. Offer ends Nov 30.")

        st.subheader("5. Compliance, Evidence & Brand Rules")
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            facts_raw = st.text_area("Verified Product Facts (One per line)", placeholder="• SOC 2 Type II certified\n• 99.9% historical uptime over 2 years", height=80)
            claims_raw = st.text_area("Claims Requiring Evidence Checklist", placeholder="• Independent benchmark report for time savings claim", height=80)
        with col_v2:
            req_phrases = st.text_input("Required Phrases (Comma-separated)", placeholder="e.g. Built for Legal Compliance")
            proh_phrases = st.text_input("Prohibited Phrases (Comma-separated)", placeholder="e.g. cheapest, 100% bug-free")
            disclaimers = st.text_area("Mandatory Disclaimers", placeholder="e.g. Requires active subscription. Terms and conditions apply.", height=70)

        submitted = st.form_submit_button("🚀 Create Campaign & Continue", use_container_width=True, type="primary")

        if submitted:
            # Validate required fields
            if not camp_name.strip() or not prod_name.strip() or not prod_desc.strip() or not target_aud.strip():
                st.error("Please fill in all mandatory fields marked with an asterisk (*).")
            else:
                try:
                    features_list = [f.strip().lstrip("•- ") for f in features_raw.split("\n") if f.strip()]
                    benefits_list = [b.strip().lstrip("•- ") for b in benefits_raw.split("\n") if b.strip()]
                    facts_list = [v.strip().lstrip("•- ") for v in facts_raw.split("\n") if v.strip()]
                    claims_list = [c.strip().lstrip("•- ") for c in claims_raw.split("\n") if c.strip()]
                    req_list = [r.strip() for r in req_phrases.split(",") if r.strip()]
                    proh_list = [p.strip() for p in proh_phrases.split(",") if p.strip()]
                    disc_list = [d.strip() for d in disclaimers.split("\n") if d.strip()]

                    new_campaign = camp_svc.create_campaign({
                        "name": camp_name,
                        "product_name": prod_name,
                        "product_description": prod_desc,
                        "features": features_list,
                        "benefits": benefits_list,
                        "target_audience": target_aud,
                        "audience_needs": aud_needs,
                        "objective": objective.lower(),
                        "channel": channel.lower(),
                        "offer": offer,
                        "offer_conditions": offer_conditions,
                        "tone_of_voice": tone,
                        "brand_name": brand_name,
                        "brand_profile_id": bp_options[sel_bp_name],
                        "verified_facts": facts_list,
                        "claims_requiring_evidence": claims_list,
                        "required_phrases": req_list,
                        "prohibited_phrases": proh_list,
                        "mandatory_disclaimers": disc_list,
                    })

                    # Automatically generate initial creative brief
                    brief_svc.generate_and_save_brief(new_campaign["id"])

                    # Switch to workspace for this campaign
                    st.session_state["selected_campaign_id"] = new_campaign["id"]
                    st.session_state["nav_choice"] = "📝 Campaign Workspace"
                    st.rerun()
                except Exception as ex:
                    st.error(f"Error creating campaign: {ex}")


# =============================================================================
# PAGE 4: CAMPAIGN WORKSPACE (BRIEF, VARIANTS, APPROVAL)
# =============================================================================

elif nav_choice == "📝 Campaign Workspace":
    campaigns = camp_svc.list_campaigns()
    if not campaigns:
        st.warning("No campaigns available. Create one first or seed sample data.")
        col_w1, col_w2 = st.columns(2)
        with col_w1:
            if st.button("🌱 Seed Demonstration Campaigns", type="primary", use_container_width=True):
                seed_sample_data(DEFAULT_DB_PATH, force=True)
                st.rerun()
        with col_w2:
            if st.button("➕ Create New Campaign", use_container_width=True):
                st.session_state["nav_choice"] = "➕ Create New Campaign"
                st.rerun()
    else:
        # Campaign selector dropdown
        camp_dict = {f"{c['name']} ({c['product_name']})": c["id"] for c in campaigns}
        current_id = st.session_state.get("selected_campaign_id")

        default_idx = 0
        if current_id:
            for idx, cid in enumerate(camp_dict.values()):
                if cid == current_id:
                    default_idx = idx
                    break

        selected_label = st.selectbox("Select Active Campaign", list(camp_dict.keys()), index=default_idx)
        selected_campaign_id = camp_dict[selected_label]
        st.session_state["selected_campaign_id"] = selected_campaign_id

        active_camp = camp_svc.get_campaign(selected_campaign_id)
        if not active_camp:
            st.error("Selected campaign not found. Please select another campaign.")
            st.stop()

        st.caption(f"Campaign ID: `{active_camp['id']}` | Channel: `{active_camp['channel'].title()}` | Objective: `{active_camp['objective'].title()}`")

        # Tabs for Campaign Sub-views
        tab_brief, tab_variants, tab_approval, tab_settings = st.tabs([
            "📋 Creative Brief",
            "✨ Ad Variants Generator",
            "🛡️ Human Review & Approval",
            "⚙️ Campaign Settings",
        ])

        # ---------------------------------------------------------------------
        # TAB 1: CREATIVE BRIEF
        # ---------------------------------------------------------------------
        with tab_brief:
            st.subheader("Marketing Creative Brief")
            brief = brief_svc.get_brief_for_campaign(selected_campaign_id)
            if not brief:
                brief = brief_svc.generate_and_save_brief(selected_campaign_id)

            b_header_col1, b_header_col2 = st.columns([3, 1])
            with b_header_col1:
                st.markdown(f"**Status:** {get_status_badge(brief['status'])}", unsafe_allow_html=True)
            with b_header_col2:
                if st.button("🔄 Regenerate Brief", key="regen_brief", use_container_width=True):
                    brief = brief_svc.generate_and_save_brief(selected_campaign_id)
                    st.success("Creative brief regenerated from latest campaign inputs.")
                    st.rerun()

            # Structured Brief View
            with st.container():
                st.markdown(f"### 1. Campaign Overview\n{brief['overview']}")
                st.markdown(f"### 2. Product Summary\n{brief['product_summary']}")

                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    st.markdown(f"**Target Audience:** {brief['target_audience']}")
                    st.markdown(f"**Audience Problem / Need:** {brief['audience_problem']}")
                    st.markdown(f"**Customer Insight:**\n> {brief['customer_insight']}")
                with col_b2:
                    st.markdown(f"**Objective:** {brief['objective']}")
                    st.markdown(f"**Desired Response:** {brief['desired_response']}")
                    st.markdown(f"**Tone of Voice:** {brief['recommended_tone']}")

                st.markdown("### 3. Value Proposition & Primary Message")
                st.info(f"**Value Proposition:** {brief['value_proposition']}\n\n**Primary Core Message:** {brief['primary_message']}")
                st.markdown(f"**Communication Angle:** {brief['communication_angle']}")

                st.markdown("### 4. Message Hierarchy & Recommended CTA")
                st.write(brief["message_hierarchy"])
                st.success(f"**Recommended Call to Action:** `{brief['recommended_cta']}`")

                st.markdown("### 5. Verified Facts & Compliance Checklist")
                col_chk1, col_chk2 = st.columns(2)
                with col_chk1:
                    st.write("**Supplied Verified Facts:**")
                    facts = brief.get("verified_facts") or []
                    if facts:
                        for f in facts:
                            st.write(f"- 🟢 `[VERIFIED FACT]` {f}")
                    else:
                        st.caption("No explicit verified facts entered.")
                with col_chk2:
                    st.write("**Missing Evidence / Substantiation Needed:**")
                    ev_needed = brief.get("missing_evidence") or []
                    if ev_needed:
                        for e in ev_needed:
                            st.write(f"- ⚠️ `[EVIDENCE REQUIRED]` {e}")
                    else:
                        st.caption("No missing evidence items recorded.")

                st.markdown("### 6. Potential Risk Review")
                risks = brief.get("potential_risks") or []
                for rk in risks:
                    st.warning(rk)

            st.divider()

            # Inline Brief Editor Expander
            with st.expander("✏️ Edit Creative Brief Sections"):
                with st.form("edit_brief_form"):
                    e_overview = st.text_area("Overview", brief["overview"], height=70)
                    e_prod = st.text_area("Product Summary", brief["product_summary"], height=70)
                    e_val_prop = st.text_area("Value Proposition", brief["value_proposition"], height=70)
                    e_prim_msg = st.text_area("Primary Message", brief["primary_message"], height=70)
                    e_cta = st.text_input("Recommended CTA", brief["recommended_cta"])
                    e_status = st.selectbox("Brief Status", ["Needs Review", "Reviewed"], index=0 if brief["status"] == "Needs Review" else 1)

                    if st.form_submit_button("Save Brief Changes"):
                        brief_svc.update_brief_content(brief["id"], {
                            "overview": e_overview,
                            "product_summary": e_prod,
                            "value_proposition": e_val_prop,
                            "primary_message": e_prim_msg,
                            "recommended_cta": e_cta,
                            "status": e_status,
                        })
                        st.success("Creative brief updated successfully.")
                        st.rerun()

            # Export Brief Button
            brief_md = export_svc.export_brief_to_markdown(selected_campaign_id)
            st.download_button(
                "📥 Download Creative Brief (.md)",
                data=brief_md,
                file_name=f"brief_{active_camp['name'].replace(' ', '_').lower()}.md",
                mime="text/markdown",
            )

        # ---------------------------------------------------------------------
        # TAB 2: AD VARIANTS GENERATOR
        # ---------------------------------------------------------------------
        with tab_variants:
            st.subheader("Generate Advertising Variants")
            st.write(
                "Generate multi-angle, channel-optimized ad variants. "
                "Each variant is scanned for claim substantiation and brand rule compliance."
            )

            # Variant Generation Controls
            gen_col1, gen_col2, gen_col3 = st.columns([1, 2, 1])
            with gen_col1:
                var_count = st.number_input("Variant Count", min_value=1, max_value=10, value=3)
            with gen_col2:
                supported_angles = AdVariantGenerator.get_supported_angles()
                suggested = AdVariantGenerator.suggest_angles(
                    active_camp["objective"],
                    has_offer=bool(active_camp.get("offer")),
                    has_evidence=len(active_camp.get("verified_facts", [])) > 0,
                )
                selected_angles = st.multiselect(
                    "Preferred Marketing Angles (Leave blank for auto-suggestion)",
                    options=list(supported_angles.keys()),
                    default=suggested[:3],
                    format_func=lambda k: supported_angles[k]["title"],
                )
            with gen_col3:
                st.write("")
                st.write("")
                generate_clicked = st.button("✨ Generate Variants", type="primary", use_container_width=True)

            if generate_clicked:
                new_vars = variant_svc.generate_variants_for_campaign(
                    campaign_id=selected_campaign_id,
                    variant_count=var_count,
                    preferred_angles=selected_angles if selected_angles else None,
                )
                st.success(f"Generated {len(new_vars)} new ad variant(s)!")
                st.rerun()

            st.divider()

            # List Existing Variants
            variants = variant_svc.list_variants_for_campaign(selected_campaign_id)
            if not variants:
                st.info("No ad variants generated yet. Click '✨ Generate Variants' above to produce initial options.")
            else:
                st.subheader(f"Existing Variants ({len(variants)})")
                for idx, v in enumerate(variants):
                    with st.container():
                        v_col1, v_col2 = st.columns([3, 1])
                        with v_col1:
                            st.markdown(
                                f"### {v['name']}  {get_status_badge(v['review_status'])}",
                                unsafe_allow_html=True,
                            )
                            st.caption(f"Marketing Angle: **{v['angle']}** | Channel: **{v['channel'].title()}**")
                        with v_col2:
                            if st.button("🔄 Regenerate", key=f"regen_var_{v['id']}", use_container_width=True):
                                variant_svc.regenerate_single_variant(v["id"])
                                st.rerun()

                        # Copy Box
                        st.markdown("**Headline:** " + v["headline"])
                        st.markdown("**Hook:** *" + v["hook"] + "*")
                        st.markdown("**Body Copy:**")
                        st.code(v["body_copy"], language="text")
                        st.markdown(f"**Call To Action:** `{v['cta']}`")

                        # Warnings & Evidence Display
                        warnings = v.get("warnings") or []
                        if warnings:
                            st.markdown("**Detected Compliance Warnings:**")
                            for w in warnings:
                                sev_badge = get_severity_badge(w.get("severity", "Medium"))
                                st.markdown(
                                    f"- {sev_badge} **{w.get('rule_name')}:** {w.get('explanation')}",
                                    unsafe_allow_html=True,
                                )

                        # Edit Copy Expander
                        with st.expander(f"✏️ Edit Copy for Variant {idx + 1}"):
                            with st.form(f"edit_variant_{v['id']}"):
                                ed_headline = st.text_input("Headline", v["headline"])
                                ed_hook = st.text_input("Hook", v["hook"])
                                ed_body = st.text_area("Body Copy", v["body_copy"], height=140)
                                ed_cta = st.text_input("Call To Action", v["cta"])
                                if st.form_submit_button("Save Edits (Resets to Pending Review)"):
                                    variant_svc.update_variant_content(
                                        v["id"],
                                        headline=ed_headline,
                                        hook=ed_hook,
                                        body_copy=ed_body,
                                        cta=ed_cta,
                                    )
                                    st.success("Variant updated. Status reset to 'Pending Review' for audit.")
                                    st.rerun()

                        st.markdown("---")

        # ---------------------------------------------------------------------
        # TAB 3: HUMAN REVIEW & APPROVAL WORKFLOW
        # ---------------------------------------------------------------------
        with tab_approval:
            st.subheader("Human Review & Approval Governance")
            st.markdown(
                f'<div class="compliance-banner">{COMPLIANCE_DISCLAIMER}</div>',
                unsafe_allow_html=True,
            )

            variants = variant_svc.list_variants_for_campaign(selected_campaign_id)
            if not variants:
                st.info("No variants available for review.")
            else:
                for idx, v in enumerate(variants):
                    with st.expander(
                        f"Review Variant {idx + 1}: {v['headline'][:50]}... [{v['review_status']}]",
                        expanded=(v["review_status"] == "Pending Review"),
                    ):
                        st.markdown(f"**Current Status:** {get_status_badge(v['review_status'])}", unsafe_allow_html=True)
                        if v.get("rejection_reason"):
                            st.error(f"Rejection Reason: {v['rejection_reason']}")

                        st.write(f"**Headline:** {v['headline']}")
                        st.write(f"**Body Copy:**\n{v['body_copy']}")
                        st.write(f"**CTA:** `{v['cta']}`")

                        # Unresolved High Severity Check
                        unresolved_high = ev_svc.count_unresolved_high_severity(v["id"])

                        # Reviewer Name common input for the card
                        card_reviewer = st.text_input("Reviewer Name", "Compliance Reviewer", key=f"rev_name_{v['id']}")

                        rev_col1, rev_col2, rev_col3 = st.columns(3)
                        with rev_col1:
                            st.write("#### Approve Variant")
                            override_note = ""
                            if unresolved_high > 0:
                                st.warning(
                                    f"⚠️ Found {unresolved_high} unresolved High-severity warning(s). "
                                    "Approval blocked unless you provide an explicit override justification."
                                )
                                override_note = st.text_area(
                                    "Override Justification & Evidence Source *",
                                    placeholder="Enter documented legal/evidence exemption justification...",
                                    key=f"override_{v['id']}",
                                )

                            if st.button("✅ Approve", key=f"btn_appr_{v['id']}", type="primary"):
                                try:
                                    appr_svc.approve_variant(
                                        v["id"],
                                        reviewer_name=card_reviewer,
                                        override_reason=override_note,
                                    )
                                    st.success(f"Variant {idx + 1} approved.")
                                    st.rerun()
                                except Exception as ex:
                                    st.error(str(ex))

                        with rev_col2:
                            st.write("#### Reject Variant")
                            rej_reason = st.text_area(
                                "Rejection Reason *",
                                placeholder="Explain why this variant does not meet brand/compliance standards...",
                                key=f"rej_reason_{v['id']}",
                            )
                            if st.button("❌ Reject", key=f"btn_rej_{v['id']}"):
                                try:
                                    appr_svc.reject_variant(
                                        v["id"],
                                        rejection_reason=rej_reason,
                                        reviewer_name=card_reviewer,
                                    )
                                    st.warning(f"Variant {idx + 1} rejected.")
                                    st.rerun()
                                except Exception as ex:
                                    st.error(str(ex))

                        with rev_col3:
                            st.write("#### Request Revisions")
                            rev_notes = st.text_area(
                                "Revision Instructions *",
                                placeholder="Instructions for copywriter to adjust tone/claims...",
                                key=f"rev_notes_{v['id']}",
                            )
                            if st.button("🔄 Request Revision", key=f"btn_req_rev_{v['id']}"):
                                try:
                                    appr_svc.request_revisions(
                                        v["id"],
                                        revision_notes=rev_notes,
                                        reviewer_name=card_reviewer,
                                    )
                                    st.info(f"Variant {idx + 1} marked for revision.")
                                    st.rerun()
                                except Exception as ex:
                                    st.error(str(ex))

                        # Audit History Trail
                        history = appr_svc.get_review_history(v["id"])
                        if history:
                            st.write("##### Review Audit History")
                            hist_rows = [
                                {
                                    "Timestamp": h["created_at"][:19],
                                    "Action": h["action"],
                                    "Prev Status": h["previous_status"] or "None",
                                    "New Status": h["new_status"],
                                    "Reviewer": h["reviewer_name"],
                                    "Notes / Reason": h["notes"],
                                }
                                for h in history
                            ]
                            st.dataframe(pd.DataFrame(hist_rows), use_container_width=True, hide_index=True)

        # ---------------------------------------------------------------------
        # TAB 4: CAMPAIGN SETTINGS
        # ---------------------------------------------------------------------
        with tab_settings:
            st.subheader("Edit Campaign Settings")
            tones = ["Professional", "Friendly", "Conversational", "Educational", "Premium", "Playful"]
            cur_tone = active_camp["tone_of_voice"].title() if active_camp["tone_of_voice"] else "Professional"
            tone_index = tones.index(cur_tone) if cur_tone in tones else 0

            with st.form("edit_campaign_form"):
                ed_name = st.text_input("Campaign Name", active_camp["name"])
                ed_prod = st.text_input("Product Name", active_camp["product_name"])
                ed_desc = st.text_area("Product Description", active_camp["product_description"])
                ed_aud = st.text_input("Target Audience", active_camp["target_audience"])
                ed_needs = st.text_area("Audience Needs", active_camp.get("audience_needs", ""))
                ed_tone = st.selectbox("Tone of Voice", tones, index=tone_index)
                ed_offer = st.text_input("Offer", active_camp.get("offer", ""))
                ed_offer_cond = st.text_input("Offer Conditions", active_camp.get("offer_conditions", ""))

                if st.form_submit_button("Update Campaign Inputs"):
                    camp_svc.update_campaign(selected_campaign_id, {
                        "name": ed_name,
                        "product_name": ed_prod,
                        "product_description": ed_desc,
                        "target_audience": ed_aud,
                        "audience_needs": ed_needs,
                        "tone_of_voice": ed_tone,
                        "offer": ed_offer,
                        "offer_conditions": ed_offer_cond,
                    })
                    st.success("Campaign updated. Creative brief marked as 'Needs Review'.")
                    st.rerun()


# =============================================================================
# PAGE 5: BRAND GUIDELINES
# =============================================================================

elif nav_choice == "🛡️ Brand Guidelines":
    st.title("🛡️ Brand Guidelines & Voice Profiles")
    st.write(
        "Manage reusable brand profiles that define allowed terminology, prohibited phrases, "
        "required slogans, and mandatory regulatory disclaimers."
    )

    profiles = camp_svc.list_brand_profiles()

    col_bp_list, col_bp_form = st.columns([1, 1])

    with col_bp_list:
        st.subheader("Saved Brand Profiles")
        if not profiles:
            st.info("No brand profiles configured yet. Create one on the right.")
        else:
            for bp in profiles:
                with st.expander(f"🏢 {bp['name']} ({bp['brand_name']})", expanded=False):
                    st.write(f"**Tone:** `{bp['tone_of_voice']}`")
                    st.write(f"**Required Phrases:** {', '.join(bp.get('required_phrases') or []) or 'None'}")
                    st.write(f"**Prohibited Terms:** {', '.join(bp.get('prohibited_terms') or []) or 'None'}")
                    st.write(f"**Disclaimers:** {', '.join(bp.get('mandatory_disclaimers') or []) or 'None'}")
                    st.caption(f"Created: {bp['created_at'][:10]}")

    with col_bp_form:
        st.subheader("Create Brand Profile")
        with st.form("create_bp_form"):
            bp_prof_name = st.text_input("Profile Name *", placeholder="e.g. Apex Enterprise Master Guidelines")
            bp_brand_name = st.text_input("Brand Name *", placeholder="e.g. Apex Systems")
            bp_tone = st.selectbox("Brand Tone *", ["Professional", "Friendly", "Conversational", "Educational", "Premium", "Playful"])
            bp_req = st.text_area("Required Phrases (One per line)", placeholder="Engineered for Reliability\nEnterprise Grade")
            bp_proh = st.text_area("Prohibited Phrases (One per line)", placeholder="bug-free\ncheapest\nguaranteed 100%")
            bp_disc = st.text_area("Mandatory Disclaimers (One per line)", placeholder="Terms and conditions apply. Requires active subscription.")

            if st.form_submit_button("Save Brand Profile", type="primary"):
                if not bp_prof_name.strip() or not bp_brand_name.strip():
                    st.error("Profile Name and Brand Name are required.")
                else:
                    try:
                        camp_svc.create_brand_profile(
                            name=bp_prof_name,
                            brand_name=bp_brand_name,
                            tone_of_voice=bp_tone,
                            required_phrases=[r.strip() for r in bp_req.split("\n") if r.strip()],
                            prohibited_terms=[p.strip() for p in bp_proh.split("\n") if p.strip()],
                            mandatory_disclaimers=[d.strip() for d in bp_disc.split("\n") if d.strip()],
                        )
                        st.success(f"Brand Profile '{bp_prof_name}' saved!")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Error saving profile: {ex}")


# =============================================================================
# PAGE 6: CLAIMS & EVIDENCE AUDIT CENTER
# =============================================================================

elif nav_choice == "⚖️ Claims & Evidence Audit":
    st.title("⚖️ Claims & Evidence Audit Center")
    st.markdown(
        f'<div class="compliance-banner">{COMPLIANCE_DISCLAIMER}</div>',
        unsafe_allow_html=True,
    )

    campaigns = camp_svc.list_campaigns()
    if not campaigns:
        st.info("No campaigns found.")
    else:
        camp_filter = st.selectbox(
            "Filter Claims by Campaign",
            ["All Campaigns"] + [c["name"] for c in campaigns],
        )

        all_claims = []
        if camp_filter == "All Campaigns":
            for c in campaigns:
                all_claims.extend(ev_svc.get_claims_for_campaign(c["id"]))
        else:
            sel_camp = next(c for c in campaigns if c["name"] == camp_filter)
            all_claims = ev_svc.get_claims_for_campaign(sel_camp["id"])

        if not all_claims:
            st.success("🎉 No claim warnings registered for this selection.")
        else:
            st.subheader(f"Claim Review Items ({len(all_claims)})")
            for clm in all_claims:
                with st.expander(
                    f"[{clm['severity']}] {clm['warning_type']}: '{clm['claim_text']}' ({clm['review_decision']})",
                    expanded=(clm["review_decision"] == "Unresolved"),
                ):
                    c_col1, c_col2 = st.columns([2, 1])
                    with c_col1:
                        st.markdown(f"**Severity:** {get_severity_badge(clm['severity'])}", unsafe_allow_html=True)
                        st.write(f"**Claim Fragment:** `{clm['claim_text']}`")
                        st.write(f"**Explanation:** {clm['explanation']}")
                        st.info(f"**Evidence Required:** {clm['evidence_required']}")
                        if clm.get("evidence_source"):
                            st.write(f"**Recorded Evidence Source:** `{clm['evidence_source']}`")
                        if clm.get("document_reference"):
                            st.write(f"**Document Reference:** `{clm['document_reference']}`")

                    with c_col2:
                        st.write("#### Update Review Decision")
                        with st.form(f"decision_form_{clm['id']}"):
                            dec = st.selectbox(
                                "Decision",
                                ["Unresolved", "Accepted with Evidence", "Waived", "Rejected"],
                                index=["Unresolved", "Accepted with Evidence", "Waived", "Rejected"].index(clm["review_decision"]),
                            )
                            src = st.text_input("Evidence Source URL / Citations", clm.get("evidence_source", ""))
                            doc_ref = st.text_input("Doc Reference / Section #", clm.get("document_reference", ""))
                            notes = st.text_area("Reviewer Audit Notes", clm.get("reviewer_notes", ""), height=60)

                            if st.form_submit_button("Record Decision"):
                                ev_svc.update_claim_decision(
                                    claim_id=clm["id"],
                                    decision=dec,
                                    evidence_source=src,
                                    document_reference=doc_ref,
                                    reviewer_notes=notes,
                                )
                                st.success("Claim decision updated.")
                                st.rerun()


# =============================================================================
# PAGE 7: EXPORTS & REPORTS
# =============================================================================

elif nav_choice == "💾 Exports & Reports":
    st.title("💾 Data Exports & Audit Reports")
    st.write("Export ad variants to CSV, creative briefs to Markdown, and full campaign records to JSON.")

    campaigns = camp_svc.list_campaigns()
    if not campaigns:
        st.info("No campaigns available to export.")
    else:
        camp_dict = {f"{c['name']} ({c['product_name']})": c["id"] for c in campaigns}
        selected_label = st.selectbox("Select Campaign to Export", list(camp_dict.keys()))
        selected_cid = camp_dict[selected_label]
        target_camp = camp_svc.get_campaign(selected_cid)

        st.subheader("1. Export Ad Variants (CSV)")
        csv_content = export_svc.export_variants_to_csv(selected_cid)
        st.download_button(
            label="📥 Download Ad Variants CSV",
            data=csv_content,
            file_name=f"variants_{target_camp['name'].replace(' ', '_').lower()}.csv",
            mime="text/csv",
            use_container_width=True,
        )

        st.subheader("2. Export Creative Brief (Markdown)")
        brief_md = export_svc.export_brief_to_markdown(selected_cid)
        st.download_button(
            label="📥 Download Creative Brief (.md)",
            data=brief_md,
            file_name=f"brief_{target_camp['name'].replace(' ', '_').lower()}.md",
            mime="text/markdown",
            use_container_width=True,
        )

        st.subheader("3. Export Full Campaign Audit Package (JSON)")
        backup_dict = export_svc.export_campaign_full_backup(selected_cid)
        json_str = json.dumps(backup_dict, indent=2)
        st.download_button(
            label="📥 Download Full Campaign Backup (.json)",
            data=json_str,
            file_name=f"campaign_backup_{target_camp['name'].replace(' ', '_').lower()}.json",
            mime="application/json",
            use_container_width=True,
        )
