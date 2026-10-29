# User Guide: Marketing Creative Brief & Ad Variant Generator

This guide provides end-to-end instructions for launching, configuring, and operating the **Marketing Creative Brief & Ad Variant Generator**.

---

## 1. Quick Launch & Environment Startup

### Step 1: Open Terminal in Project Directory
Open PowerShell or Windows Terminal:
```powershell
cd "c:\skips\sem-3\New folder\marketing_creative_generator"
```

### Step 2: Launch Streamlit
```powershell
streamlit run app.py
```
Or if invoking Python directly:
```powershell
python -m streamlit run app.py
```

The Streamlit web application will start and open your web browser at `http://localhost:8501`.

---

## 2. Platform Navigation Overview

The sidebar provides seven intuitive modules:
1. **📊 Dashboard:** High-level metrics, review status breakdown, and marketing angle charts.
2. **📁 Campaigns Directory:** Search, filter, duplicate, and manage all saved marketing campaigns.
3. **➕ Create New Campaign:** Input product details, audience parameters, offers, and brand rules.
4. **📝 Campaign Workspace:**
   - **Tab 1: Creative Brief:** View, edit, regenerate, and download synthesized brief.
   - **Tab 2: Ad Variants Generator:** Generate 1 to 10 copy variants, edit headlines/hooks/copy, and inspect compliance warnings.
   - **Tab 3: Human Review & Approval:** Review copy, inspect evidence requirements, approve (with high-severity gating), reject, or request revisions.
   - **Tab 4: Campaign Settings:** Update original campaign parameters.
5. **🛡️ Brand Guidelines:** Create and manage reusable brand guidelines profiles.
6. **⚖️ Claims & Evidence Audit:** Inspect detected claims across campaigns, update substantiation decisions, and attach proof documentation.
7. **💾 Exports & Reports:** Download ad variants as CSV, briefs as Markdown, and complete campaign records as JSON.

---

## 3. Step-by-Step User Workflows

### Workflow A: Seeding Demonstration Campaigns
For a fast walk-through or academic presentation:
1. Locate the sidebar on the left.
2. Click the green **"🌱 Seed Sample Campaigns"** button.
3. The platform will automatically populate three realistic campaigns:
   - **FlowSync Q4 Enterprise Sprint** (B2B SaaS / Search Ads)
   - **PureHydro Summer Hydration** (Consumer Goods / Social Media)
   - **PulsePeak Recovery Awareness** (Health & Fitness App / Email)
4. Navigate to the **📊 Dashboard** to view live counters and Plotly charts.

---

### Workflow B: Creating a New Marketing Campaign
1. Click **➕ Create New Campaign** in the sidebar.
2. Fill in the required fields:
   - **Campaign Name:** e.g., `SwiftPay Fintech Expansion`
   - **Product Name:** e.g., `SwiftPay POS Gateway`
   - **Product Description:** High-level overview of the product.
   - **Features:** Bullet points of key technical functions (one per line).
   - **Benefits:** Tangible customer advantages (one per line).
   - **Target Audience:** e.g., `E-commerce merchants and retail store operators`.
   - **Objective:** Select from `Awareness`, `Traffic`, `Leads`, `Conversions`, or `Retention`.
   - **Channel:** Select from `Social Media`, `Search Advertising`, `Email`, or `Display Advertising`.
   - **Tone of Voice:** Select from `Professional`, `Friendly`, `Conversational`, `Educational`, `Premium`, or `Playful`.
3. *(Optional)* Add promotional offer terms, verified facts, required phrases, or prohibited terms.
4. Click **🚀 Create Campaign & Continue**.
5. The system will create the campaign, synthesize the initial creative brief, and redirect you to the **Campaign Workspace**.

---

### Workflow C: Reviewing and Editing the Creative Brief
1. Navigate to **📝 Campaign Workspace** ➔ **📋 Creative Brief** tab.
2. Review the structured brief:
   - Campaign Overview & Product Summary
   - Target Audience, Need, and Suggested Customer Insight
   - Proposed Value Proposition & Primary Message
   - Communication Angle & Tone
   - Message Hierarchy & Recommended CTA
   - Verified Product Facts vs. Missing Evidence Checklist
3. Click **"✏️ Edit Creative Brief Sections"** to make manual adjustments if desired.
4. Click **"📥 Download Creative Brief (.md)"** to save the brief locally as a Markdown document.

---

### Workflow D: Generating and Editing Ad Variants
1. In the **📝 Campaign Workspace**, open the **✨ Ad Variants Generator** tab.
2. Choose how many variants you want to produce (default: 3, max: 10).
3. Select specific marketing angles or leave blank to let the system suggest angles aligned with your campaign objective.
4. Click **✨ Generate Variants**.
5. Inspect the generated variants:
   - Note how each variant features a distinct hook formula and marketing angle.
   - Channel formatting is automatically tailored (e.g. Email includes subject lines and preview text; Search Ads include dual headlines).
   - Review detected compliance and brand warnings attached to each card.
6. Click **✏️ Edit Copy** under any variant to refine text. Editing text automatically resets the variant status to `Pending Review` for safety.

---

### Workflow E: Conducting Human Review & Approval
1. Open the **🛡️ Human Review & Approval** tab.
2. Locate a variant marked `Pending Review`.
3. Review the copy, detected claim warnings, and evidence requirements.
4. **To Approve:**
   - If the variant contains unresolved High-severity warnings, the system will prevent automatic approval.
   - To proceed, either resolve the claim in the **Claims & Evidence Audit Center** or supply an explicit override justification in the provided text area.
   - Click **✅ Approve**.
5. **To Reject:**
   - Enter a clear rejection rationale and click **❌ Reject**.
6. **To Request Revisions:**
   - Enter copywriter feedback notes and click **🔄 Request Revision**.
7. Scroll down to review the immutable **Review Audit History** timeline showing timestamps, reviewers, and status transitions.

---

### Workflow F: Auditing Claims & Logging Proof
1. Click **⚖️ Claims & Evidence Audit** in the sidebar.
2. Expand any claim warning item (e.g., `Multiplier Performance Claim: '3x faster'`).
3. Under **Update Review Decision**:
   - Change decision from `Unresolved` to `Accepted with Evidence`.
   - Enter the Evidence Source URL (e.g., `https://internal.company.com/benchmarks-2026.pdf`).
   - Enter the Document Reference / Section # (e.g., `Section 3.2 Benchmark Test`).
   - Add reviewer notes.
4. Click **Record Decision**. The claim is now documented and will no longer block variant approval.

---

### Workflow G: Exporting Data
1. Click **💾 Exports & Reports** in the sidebar.
2. Select your campaign from the dropdown.
3. Choose your export format:
   - **Download Ad Variants CSV:** Standardized table with variant ID, angle, hook, headline, body copy, CTA, status, and warnings.
   - **Download Creative Brief (.md):** Formatted Markdown report.
   - **Download Full Campaign Backup (.json):** Complete JSON archive including campaign metadata, briefs, variants, claim audits, and review history.
