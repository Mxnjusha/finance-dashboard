import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client
from datetime import datetime, date
import os

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Finance Manager",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  .main { background: #0F1117; }
  .block-container { padding: 2rem 2.5rem 2rem 2.5rem; max-width: 1300px; }

  /* Header */
  .dash-header {
    display: flex; align-items: center; gap: 14px;
    padding: 0 0 2rem 0; border-bottom: 1px solid #1E2130;
    margin-bottom: 2rem;
  }
  .dash-title { font-size: 22px; font-weight: 600; color: #F0F2F5; margin: 0; }
  .dash-sub { font-size: 13px; color: #6B7280; margin: 0; }
  .dash-dot { width: 8px; height: 8px; border-radius: 50%; background: #22C55E;
    box-shadow: 0 0 8px #22C55E; flex-shrink: 0; }

  /* Metric cards */
  .metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 2rem; }
  .metric-card {
    background: #161B27; border: 1px solid #1E2535;
    border-radius: 14px; padding: 1.25rem 1.5rem;
  }
  .metric-label { font-size: 12px; color: #6B7280; font-weight: 500;
    letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 8px; }
  .metric-value { font-size: 26px; font-weight: 700; color: #F0F2F5;
    font-family: 'JetBrains Mono', monospace; letter-spacing: -0.5px; }
  .metric-delta { font-size: 12px; margin-top: 4px; }
  .delta-up { color: #EF4444; } .delta-down { color: #22C55E; }

  /* Section labels */
  .section-title {
    font-size: 13px; font-weight: 600; color: #9CA3AF;
    letter-spacing: 0.08em; text-transform: uppercase;
    margin: 0 0 1rem 0;
  }

  /* Category badge */
  .cat-badge {
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 12px; font-weight: 500;
  }

  /* Recent transactions table */
  .txn-row {
    display: flex; align-items: center; gap: 12px;
    padding: 10px 0; border-bottom: 1px solid #1A1F2E;
  }
  .txn-row:last-child { border-bottom: none; }
  .txn-icon { width: 36px; height: 36px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center; font-size: 16px; flex-shrink: 0; }
  .txn-merchant { font-size: 14px; font-weight: 500; color: #E5E7EB; }
  .txn-date { font-size: 12px; color: #6B7280; }
  .txn-amount { font-size: 14px; font-weight: 600; color: #F87171;
    font-family: 'JetBrains Mono', monospace; margin-left: auto; }

  /* Sidebar */
  .sidebar .sidebar-content { background: #0D1117; }
  [data-testid="stSidebar"] { background: #0D1117; border-right: 1px solid #1E2130; }

  /* Hide streamlit branding */
  #MainMenu, footer, header { visibility: hidden; }
  .stDeployButton { display: none; }
</style>
""", unsafe_allow_html=True)

# ── Supabase connection ───────────────────────────────────────
@st.cache_resource
def get_supabase():
    url = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL", ""))
    key = st.secrets.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY", ""))
    if not url or not key:
        st.error("⚠️ Add SUPABASE_URL and SUPABASE_KEY to your Streamlit secrets.")
        st.stop()
    return create_client(url, key)

@st.cache_data(ttl=60)
def load_data():
    sb = get_supabase()
    res = sb.table("transactions").select("*").execute()
    if not res.data:
        return pd.DataFrame()
    df = pd.DataFrame(res.data)
    df["txn_date"] = pd.to_datetime(df["txn_date"])
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    df["month"] = df["txn_date"].dt.to_period("M").astype(str)
    df["month_name"] = df["txn_date"].dt.strftime("%b %Y")
    return df.sort_values("txn_date", ascending=False)

# ── Category config ───────────────────────────────────────────
CAT_COLORS = {
    "Food":          "#F97316",
    "Groceries":     "#84CC16",
    "Transport":     "#38BDF8",
    "Shopping":      "#A78BFA",
    "Entertainment": "#F472B6",
    "Bills":         "#FB923C",
    "Health":        "#34D399",
    "Education":     "#60A5FA",
    "Transfer":      "#94A3B8",
    "Savings":       "#FBBF24",
    "Other":         "#6B7280",
}
CAT_ICONS = {
    "Food": "🍽️", "Groceries": "🛒", "Transport": "🚗",
    "Shopping": "🛍️", "Entertainment": "🎬", "Bills": "⚡",
    "Health": "💊", "Education": "📚", "Transfer": "💸",
    "Savings": "💰", "Other": "📦",
}

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 💸 Finance Manager")
    st.markdown("---")

    df_all = load_data()
    if df_all.empty:
        st.warning("No transactions found.")
        st.stop()

    # Date filter
    st.markdown("**Date Range**")
    min_date = df_all["txn_date"].min().date()
    max_date = df_all["txn_date"].max().date()
    date_from = st.date_input("From", value=min_date, min_value=min_date, max_value=max_date)
    date_to   = st.date_input("To",   value=max_date, min_value=min_date, max_value=max_date)

    st.markdown("**Categories**")
    all_cats = sorted(df_all["category"].dropna().unique().tolist())
    selected_cats = st.multiselect("", all_cats, default=all_cats, label_visibility="collapsed")

    st.markdown("**Source**")
    sources = ["All"] + sorted(df_all["source"].dropna().unique().tolist())
    selected_source = st.selectbox("", sources, label_visibility="collapsed")

    st.markdown("---")
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

# ── Filter data ───────────────────────────────────────────────
df = df_all.copy()
df = df[(df["txn_date"].dt.date >= date_from) & (df["txn_date"].dt.date <= date_to)]
if selected_cats:
    df = df[df["category"].isin(selected_cats)]
if selected_source != "All":
    df = df[df["source"] == selected_source]

debits = df[df["amount"] > 0]

# ── Header ────────────────────────────────────────────────────
st.markdown("""
<div class="dash-header">
  <div class="dash-dot"></div>
  <div>
    <p class="dash-title">AI Finance Manager</p>
    <p class="dash-sub">Personal spending tracker powered by Telegram + Groq AI</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ── KPI Metrics ───────────────────────────────────────────────
total_spend  = debits["amount"].sum()
avg_txn      = debits["amount"].mean() if len(debits) else 0
top_category = debits.groupby("category")["amount"].sum().idxmax() if len(debits) else "—"
top_merchant = debits.groupby("merchant")["amount"].sum().idxmax() if len(debits) else "—"

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class="metric-card">
      <div class="metric-label">Total Spent</div>
      <div class="metric-value">₹{total_spend:,.0f}</div>
      <div class="metric-delta" style="color:#6B7280">{len(debits)} transactions</div>
    </div>""", unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="metric-card">
      <div class="metric-label">Avg Transaction</div>
      <div class="metric-value">₹{avg_txn:,.0f}</div>
      <div class="metric-delta" style="color:#6B7280">per transaction</div>
    </div>""", unsafe_allow_html=True)
with col3:
    top_cat_amt = debits.groupby("category")["amount"].sum().max() if len(debits) else 0
    st.markdown(f"""
    <div class="metric-card">
      <div class="metric-label">Top Category</div>
      <div class="metric-value" style="font-size:20px">{CAT_ICONS.get(top_category,'📦')} {top_category}</div>
      <div class="metric-delta" style="color:#6B7280">₹{top_cat_amt:,.0f} total</div>
    </div>""", unsafe_allow_html=True)
with col4:
    top_merch_amt = debits.groupby("merchant")["amount"].sum().max() if len(debits) else 0
    st.markdown(f"""
    <div class="metric-card">
      <div class="metric-label">Top Merchant</div>
      <div class="metric-value" style="font-size:18px">{top_merchant}</div>
      <div class="metric-delta" style="color:#6B7280">₹{top_merch_amt:,.0f} total</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Row 1: Monthly trend + Category donut ────────────────────
col_left, col_right = st.columns([3, 2], gap="large")

with col_left:
    st.markdown('<p class="section-title">Monthly Spending Trend</p>', unsafe_allow_html=True)
    monthly = debits.groupby("month_name")["amount"].sum().reset_index()
    monthly = monthly.sort_values("month_name")
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=monthly["month_name"], y=monthly["amount"],
        mode="lines+markers",
        line=dict(color="#6366F1", width=2.5),
        marker=dict(size=7, color="#6366F1",
                    line=dict(color="#161B27", width=2)),
        fill="tozeroy",
        fillcolor="rgba(99,102,241,0.08)",
        hovertemplate="<b>%{x}</b><br>₹%{y:,.0f}<extra></extra>"
    ))
    fig_line.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=260, margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(showgrid=False, tickfont=dict(color="#6B7280", size=11),
                   linecolor="#1E2130"),
        yaxis=dict(showgrid=True, gridcolor="#1A1F2E",
                   tickfont=dict(color="#6B7280", size=11),
                   tickprefix="₹"),
        showlegend=False
    )
    st.plotly_chart(fig_line, use_container_width=True, config={"displayModeBar": False})

with col_right:
    st.markdown('<p class="section-title">Spending by Category</p>', unsafe_allow_html=True)
    cat_data = debits.groupby("category")["amount"].sum().reset_index()
    cat_data = cat_data.sort_values("amount", ascending=False)
    colors = [CAT_COLORS.get(c, "#6B7280") for c in cat_data["category"]]
    fig_donut = go.Figure(go.Pie(
        labels=cat_data["category"], values=cat_data["amount"],
        hole=0.65,
        marker=dict(colors=colors, line=dict(color="#0F1117", width=2)),
        textinfo="none",
        hovertemplate="<b>%{label}</b><br>₹%{value:,.0f}<br>%{percent}<extra></extra>"
    ))
    fig_donut.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=260, margin=dict(l=0, r=0, t=0, b=0),
        showlegend=True,
        legend=dict(font=dict(color="#9CA3AF", size=11),
                    bgcolor="rgba(0,0,0,0)", x=1, y=0.5)
    )
    st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})

# ── Row 2: Top merchants bar + Recent transactions ────────────
col_left2, col_right2 = st.columns([3, 2], gap="large")

with col_left2:
    st.markdown('<p class="section-title">Top 10 Merchants</p>', unsafe_allow_html=True)
    top_merch = debits.groupby("merchant")["amount"].sum().nlargest(10).reset_index()
    top_merch = top_merch.sort_values("amount")
    fig_bar = go.Figure(go.Bar(
        x=top_merch["amount"], y=top_merch["merchant"],
        orientation="h",
        marker=dict(
            color=top_merch["amount"],
            colorscale=[[0, "#312E81"], [0.5, "#6366F1"], [1, "#A5B4FC"]],
            line=dict(color="rgba(0,0,0,0)")
        ),
        hovertemplate="<b>%{y}</b><br>₹%{x:,.0f}<extra></extra>",
        text=top_merch["amount"].apply(lambda x: f"₹{x:,.0f}"),
        textposition="outside",
        textfont=dict(color="#9CA3AF", size=11)
    ))
    fig_bar.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=340, margin=dict(l=0, r=60, t=0, b=0),
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(tickfont=dict(color="#D1D5DB", size=12), showgrid=False),
        showlegend=False
    )
    st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

with col_right2:
    st.markdown('<p class="section-title">Recent Transactions</p>', unsafe_allow_html=True)
    recent = debits.head(8)
    rows_html = ""
    for _, row in recent.iterrows():
        icon = CAT_ICONS.get(row.get("category", "Other"), "📦")
        color = CAT_COLORS.get(row.get("category", "Other"), "#6B7280")
        date_str = row["txn_date"].strftime("%d %b") if pd.notna(row["txn_date"]) else ""
        merchant = str(row.get("merchant", "Unknown"))[:20]
        amount = row["amount"]
        rows_html += f"""
        <div class="txn-row">
          <div class="txn-icon" style="background:{color}18">{icon}</div>
          <div>
            <div class="txn-merchant">{merchant}</div>
            <div class="txn-date">{date_str} · {row.get('category','')}</div>
          </div>
          <div class="txn-amount">-₹{amount:,.0f}</div>
        </div>"""
    st.markdown(f'<div style="background:#161B27;border:1px solid #1E2535;border-radius:14px;padding:1rem 1.25rem">{rows_html}</div>',
                unsafe_allow_html=True)

# ── Row 3: Category breakdown table ──────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<p class="section-title">Category Breakdown</p>', unsafe_allow_html=True)

cat_summary = debits.groupby("category").agg(
    Total=("amount", "sum"),
    Count=("amount", "count"),
    Average=("amount", "mean"),
    Max=("amount", "max")
).reset_index().sort_values("Total", ascending=False)

cat_summary["Share"] = (cat_summary["Total"] / cat_summary["Total"].sum() * 100).round(1)

cols = st.columns(len(cat_summary) if len(cat_summary) <= 5 else 5)
for i, (_, row) in enumerate(cat_summary.iterrows()):
    if i >= 5: break
    cat = row["category"]
    color = CAT_COLORS.get(cat, "#6B7280")
    icon = CAT_ICONS.get(cat, "📦")
    with cols[i]:
        st.markdown(f"""
        <div style="background:#161B27;border:1px solid #1E2535;border-radius:12px;
                    padding:1rem;text-align:center">
          <div style="font-size:24px;margin-bottom:6px">{icon}</div>
          <div style="font-size:12px;color:#6B7280;font-weight:500;text-transform:uppercase;
                      letter-spacing:0.05em;margin-bottom:6px">{cat}</div>
          <div style="font-size:20px;font-weight:700;color:#F0F2F5;
                      font-family:'JetBrains Mono',monospace">₹{row['Total']:,.0f}</div>
          <div style="font-size:11px;color:{color};margin-top:4px;font-weight:500">
            {row['Share']}% · {int(row['Count'])} txns</div>
          <div style="height:3px;background:{color};border-radius:2px;
                      margin-top:10px;opacity:0.7;width:{min(row['Share']*3,100)}%"></div>
        </div>""", unsafe_allow_html=True)

if len(cat_summary) > 5:
    st.markdown("<br>", unsafe_allow_html=True)
    cols2 = st.columns(len(cat_summary) - 5)
    for i, (_, row) in enumerate(cat_summary.iloc[5:].iterrows()):
        cat = row["category"]
        color = CAT_COLORS.get(cat, "#6B7280")
        icon = CAT_ICONS.get(cat, "📦")
        with cols2[i]:
            st.markdown(f"""
            <div style="background:#161B27;border:1px solid #1E2535;border-radius:12px;
                        padding:1rem;text-align:center">
              <div style="font-size:24px;margin-bottom:6px">{icon}</div>
              <div style="font-size:12px;color:#6B7280;font-weight:500;text-transform:uppercase;
                          letter-spacing:0.05em;margin-bottom:6px">{cat}</div>
              <div style="font-size:20px;font-weight:700;color:#F0F2F5;
                          font-family:'JetBrains Mono',monospace">₹{row['Total']:,.0f}</div>
              <div style="font-size:11px;color:{color};margin-top:4px;font-weight:500">
                {row['Share']}% · {int(row['Count'])} txns</div>
              <div style="height:3px;background:{color};border-radius:2px;
                          margin-top:10px;opacity:0.7;width:{min(row['Share']*3,100)}%"></div>
            </div>""", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center;color:#374151;font-size:12px;padding-top:1rem;
            border-top:1px solid #1E2130">
  Built with Telegram · n8n · Groq AI · Supabase · Streamlit
</div>""", unsafe_allow_html=True)
