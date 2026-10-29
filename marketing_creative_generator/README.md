# Marketing Creative Brief & Ad Variant Generator

An academic-grade (M.Sc. IT level) marketing technology platform built with Python, Streamlit, and SQLite.

This system assists marketing professionals, copywriters, and compliance officers in transforming raw product specifications into structured creative briefs and multi-angle advertising copy variants across 4 major marketing channels (Social Media, Search, Email, and Display). It features an integrated claim audit engine that detects unverified performance claims, enforces brand guidelines, and requires human-in-the-loop review before any variant can be marked as Approved.

---

## 🎯 Key Highlights

- **100% Local & Free of Paid AI APIs**: Runs entirely on your local Windows machine without requiring API keys, cloud subscriptions, or external network requests.
- **Deterministic & Fact-Grounded**: Never hallucinates or fabricates product features, customer statistics, discounts, or awards. Strictly separates verified user facts from suggested insights.
- **11 Marketing Angles & 7 Hook Styles**: Tailors messaging across angles (Problem/Solution, Benefit-Focused, ROI, Use-Case, Educational, etc.) and hook formulas (Question, Scenario, Curiosity, Benefit-Led).
- **Automated Claim & Brand Auditing**: Automatically flags numerical claims, absolute superlatives (#1, safest), guarantees, sensitive health/financial promises, and missing discount terms.
- **Human Governance Workflow**: High-severity compliance warnings gate approval; status lifecycle (`Pending Review` ➔ `Approved` / `Rejected` / `Needs Revision`) with full audit history logging.
- **Live Interactive Dashboard**: Real-time SQLite metrics and Plotly charts tracking campaigns, variants, angle distributions, and approval rates.
- **Standardized Multi-Format Exports**: Export ad variants to CSV (pandas), creative briefs to formatted Markdown, and complete campaign backups to structured JSON.

---

## 🏗️ System Architecture

```
marketing_creative_generator/
│
├── app.py                      # Main Streamlit user interface entry point
├── requirements.txt            # Python dependencies (Streamlit, Pandas, Plotly, Pytest)
├── README.md                   # Windows installation & quickstart guide
├── .gitignore                  # Git ignore rules for virtual environments & SQLite DB
│
├── backend/                    # Core business logic & database services
│   ├── database.py             # SQLite schema, connection pooling & WAL mode
│   ├── campaign_service.py     # Campaign CRUD, duplication & dashboard metrics
│   ├── brief_generator.py      # Structured creative brief synthesis engine
│   ├── ad_variant_generator.py # 11 angles, 7 hooks, channel copy & CTA logic
│   ├── brand_checker.py        # Prohibited/required phrases & brand tone analysis
│   ├── claim_checker.py        # Regex detection for numerical, absolute & sensitive claims
│   ├── evidence_checker.py     # Claim review tracking & evidence documentation
│   ├── approval_service.py     # Human approval lifecycle & warning gating
│   ├── export_service.py       # CSV, Markdown, and JSON serialization
│   └── seed_data.py            # Realistic demonstration campaigns seeder
│
├── frontend/                   # UI presentation layer
│   └── styles.py               # Custom CSS styles, metric cards & status badges
│
├── tests/                      # Automated unit test suite (30 test cases)
│   ├── test_database.py
│   ├── test_brand_checker.py
│   ├── test_claim_checker.py
│   ├── test_campaign_service.py
│   ├── test_brief_generator.py
│   ├── test_ad_variant_generator.py
│   ├── test_approval_and_export.py
│   └── test_seed_data.py
│
├── docs/                       # Academic documentation & test reports
│   ├── PROJECT_OVERVIEW.md     # Architecture, data models & compliance framework
│   ├── USER_GUIDE.md           # Step-by-step application walkthrough
│   └── TEST_REPORT.md          # Automated testing results & coverage matrix
│
└── data/                       # Local SQLite storage (auto-generated)
    └── marketing_generator.db
```

---

## 💻 Windows Installation & Setup Guide

### 1. Prerequisites
- **Operating System:** Windows 10 or Windows 11
- **Python:** Python 3.10+ (Recommended: Python 3.11, 3.12, 3.13, or 3.14)
- **Git** (optional)

### 2. Open PowerShell or Command Prompt
Navigate to your project directory:
```powershell
cd "c:\skips\sem-3\New folder\marketing_creative_generator"
```

### 3. Create and Activate a Virtual Environment (Optional but Recommended)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 4. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 5. Launch the Application
Run Streamlit from the project directory:
```powershell
streamlit run app.py
```
Or from the parent repository directory:
```powershell
python -m streamlit run app.py
```

The application will automatically open in your default browser at `http://localhost:8501`.

---

## 🧪 Running Automated Tests

Run the comprehensive pytest suite:
```powershell
pytest tests/ -v
```
All 30 unit tests will run and report 100% pass status.

---

## 🚀 Quick Demonstration Walkthrough

1. **Launch App:** Run `streamlit run app.py`.
2. **Seed Sample Data:** Click the **'🌱 Seed Sample Campaigns'** button in the sidebar. This pre-populates 3 realistic campaigns:
   - *FlowSync Q4 Enterprise Sprint* (B2B SaaS / Search Ads)
   - *PureHydro Summer Hydration* (Consumer Goods / Social Media)
   - *PulsePeak Recovery Awareness* (Health & Fitness / Email)
3. **Inspect Dashboard:** View live metric counters and Plotly distribution charts.
4. **Explore Workspace:**
   - Review the auto-generated **Creative Brief** distinguishing verified facts from suggestions.
   - Inspect the **Ad Variants** with hooks, channel-formatted copy, and detected warnings.
   - Test the **Human Approval Gate**: Try approving a variant with High-severity warnings to see the compliance block in action, or provide an override justification.
5. **Download Exports:** Navigate to **'💾 Exports & Reports'** to download your variants as CSV or the brief as Markdown.
