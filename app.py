import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO

# ── PAGE CONFIG ──
st.set_page_config(
    page_title="Flipkart SPF Dashboard 2026",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CUSTOM CSS ──
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #f97316, #fb923c);
        padding: 15px 20px;
        border-radius: 10px;
        color: white;
        margin-bottom: 20px;
    }
    .kpi-card {
        background: white;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #f97316;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stMetric {
        background: white;
        padding: 10px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# ── HEADER ──
st.markdown("""
<div class="main-header">
    <h2 style="margin:0">📦 Flipkart SPF Dashboard — Pan India 2026</h2>
    <p style="margin:0;opacity:0.9">Seller Protection Fund · Returns & Claims Intelligence · Manager View</p>
</div>
""", unsafe_allow_html=True)

# ── COLUMN MAPPING ──
COL_MAP = {
    'date':     ['order_date_key', 'Order Date Key', 'date'],
    'qa':       ['QA', 'qa', 'QA Name'],
    'ph':       ['PH', 'ph', 'Hub'],
    'loss':     ['loss_bucket', 'Loss Bucket', 'loss bucket'],
    'claim':    ['approved_claim_amount', 'Approved Claim Amount', 'claim'],
    'asp':      ['ASP_buck', 'ASP', 'asp'],
    'sc':       ['flag_smart_check_done', 'Smart Check', 'sc'],
    'reason':   ['reason', 'Reason'],
    'rtype':    ['return_type', 'Return Type'],
    'cms':      ['cms_vertical', 'CMS Vertical'],
    'rr':       ['return_reason', 'Return Reason'],
    'seller':   ['seller_id', 'Seller ID'],
    'facility': ['source_facility_id', 'Source Facility'],
    'scat':     ['analytic_super_category', 'Super Category'],
    'city':     ['seller_city', 'City'],
    'week':     ['week_num_in_year', 'Week'],
    'obd':      ['seller_obd_status', 'OBD Status'],
    'transit':  ['transit_type_bucket', 'Transit Type'],
    'ekl':      ['ekl_3pl_flag', 'EKL/3PL'],
}

def get_col(df, key):
    """Find column in dataframe using multiple possible names"""
    for name in COL_MAP.get(key, [key]):
        if name in df.columns:
            return name
    return None

def get_val(df, key):
    """Get series for a column"""
    col = get_col(df, key)
    if col:
        return df[col]
    return pd.Series(['—'] * len(df))

# ── SIDEBAR — FILE UPLOAD ──
st.sidebar.markdown("## 📁 Data Upload")
st.sidebar.markdown("**Har mahine nayi CSV yahan upload karo**")

uploaded_files = st.sidebar.file_uploader(
    "CSV files upload karo (Jan, Feb, Mar...)",
    type=['csv'],
    accept_multiple_files=True,
    help="Multiple files select kar sakte ho — sab merge ho jayenge"
)

# ── LOAD DATA ──
@st.cache_data
def load_csv(file_content, filename):
    try:
        df = pd.read_csv(StringIO(file_content), low_memory=False)
        # Extract month from filename
        month = filename.upper()
        for m in ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']:
            if m in month:
                df['_month'] = m
                break
        else:
            df['_month'] = filename.split('.')[0]
        return df
    except Exception as e:
        st.error(f"Error loading {filename}: {e}")
        return None

if not uploaded_files:
    st.info("👈 **Sidebar mein CSV files upload karo** — Jan, Feb, Mar... sab ek saath!")
    st.markdown("""
    ### Kaise Upload Karein:
    1. Left sidebar mein **"Browse files"** click karo
    2. Apni **CSV files select** karo (multiple select kar sakte ho)
    3. **Dashboard automatically** ban jayega! ✅
    
    ### File Naming:
    - `SPF_Jan_2026.csv` ✅
    - `Jan SPF-2026.csv` ✅
    - Naam mein month ka naam hona chahiye
    """)
    st.stop()

# Load all files
dfs = []
for f in uploaded_files:
    content = f.getvalue().decode('utf-8', errors='ignore')
    df = load_csv(content, f.name)
    if df is not None:
        dfs.append(df)
        st.sidebar.success(f"✅ {f.name} — {len(df):,} rows")

if not dfs:
    st.error("Koi file load nahi hui!")
    st.stop()

# Merge all
ALL_DATA = pd.concat(dfs, ignore_index=True)
st.sidebar.markdown(f"**Total: {len(ALL_DATA):,} rows loaded**")

# ── SIDEBAR FILTERS ──
st.sidebar.markdown("---")
st.sidebar.markdown("## 🔍 Filters")

# Month filter
months = sorted(ALL_DATA['_month'].unique().tolist())
selected_months = st.sidebar.multiselect("📅 Month", months, default=months)

# Apply month filter
if selected_months:
    df = ALL_DATA[ALL_DATA['_month'].isin(selected_months)].copy()
else:
    df = ALL_DATA.copy()

# Numeric columns
claim_col = get_col(df, 'claim')
asp_col = get_col(df, 'asp')
sc_col = get_col(df, 'sc')

if claim_col:
    df[claim_col] = pd.to_numeric(df[claim_col], errors='coerce').fillna(0)
if asp_col:
    df[asp_col] = pd.to_numeric(df[asp_col], errors='coerce').fillna(0)
if sc_col:
    df[sc_col] = pd.to_numeric(df[sc_col], errors='coerce').fillna(0)

# QA Filter
qa_col = get_col(df, 'qa')
if qa_col:
    qa_vals = ['All'] + sorted(df[qa_col].dropna().astype(str).unique().tolist())
    selected_qa = st.sidebar.selectbox("👤 QA Name", qa_vals)
    if selected_qa != 'All':
        df = df[df[qa_col].astype(str) == selected_qa]

# Loss Bucket Filter
loss_col = get_col(df, 'loss')
if loss_col:
    loss_vals = ['All'] + sorted(df[loss_col].dropna().astype(str).unique().tolist())
    selected_loss = st.sidebar.selectbox("📊 Loss Bucket", loss_vals)
    if selected_loss != 'All':
        df = df[df[loss_col].astype(str) == selected_loss]

# Week Filter
week_col = get_col(df, 'week')
if week_col:
    week_vals = ['All'] + sorted(df[week_col].dropna().astype(str).unique().tolist())
    selected_week = st.sidebar.selectbox("📆 Week", week_vals)
    if selected_week != 'All':
        df = df[df[week_col].astype(str) == selected_week]

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Filtered: {len(df):,} rows**")

# ── KPIs ──
total_returns = len(df)
total_claim = df[claim_col].sum() if claim_col else 0
avg_asp = df[asp_col].mean() if asp_col else 0
sc_done = df[sc_col].sum() if sc_col else 0
sc_pct = (sc_done / total_returns * 100) if total_returns else 0
total_cr = total_claim / 10000000

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("📦 Total Returns", f"{total_returns:,}")
with col2:
    st.metric("💰 Total SPF (₹)", f"₹{total_claim/100000:.2f}L")
with col3:
    st.metric("📈 SPF in Crore", f"{total_cr:.4f} Cr")
with col4:
    st.metric("🏷️ Avg ASP", f"₹{avg_asp:,.0f}")
with col5:
    st.metric("✅ Smart Check %", f"{sc_pct:.1f}%")

st.markdown("---")

# ── TABS ──
tab1, tab2, tab3, tab4 = st.tabs(["📊 Charts", "👤 QA Analysis", "🗺️ Hub Analysis", "📋 Data Table"])

# ════════════════════════════════
# TAB 1: CHARTS
# ════════════════════════════════
with tab1:
    col1, col2 = st.columns(2)

    # Monthly SPF
    with col1:
        st.subheader("Monthly SPF Trend")
        monthly = ALL_DATA.copy()
        if claim_col:
            monthly[claim_col] = pd.to_numeric(monthly[claim_col], errors='coerce').fillna(0)
        month_order = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']
        if claim_col:
            monthly_grp = monthly.groupby('_month')[claim_col].sum().reset_index()
            monthly_grp.columns = ['Month', 'SPF']
            monthly_grp['Month_Order'] = monthly_grp['Month'].apply(
                lambda x: month_order.index(x) if x in month_order else 99
            )
            monthly_grp = monthly_grp.sort_values('Month_Order')
            monthly_grp['SPF_L'] = monthly_grp['SPF'] / 100000
            fig = px.bar(monthly_grp, x='Month', y='SPF_L',
                        color='SPF_L', color_continuous_scale='Oranges',
                        labels={'SPF_L': 'SPF (₹ Lakh)'},
                        text=monthly_grp['SPF_L'].apply(lambda x: f'₹{x:.1f}L'))
            fig.update_traces(textposition='inside')
            fig.update_layout(showlegend=False, coloraxis_showscale=False,
                            plot_bgcolor='white', height=300)
            st.plotly_chart(fig, use_container_width=True)

    # Weekly SPF
    with col2:
        st.subheader("Weekly SPF Trend")
        if week_col and claim_col:
            weekly_grp = df.groupby(week_col)[claim_col].sum().reset_index()
            weekly_grp.columns = ['Week', 'SPF']
            weekly_grp = weekly_grp.sort_values('Week')
            weekly_grp['SPF_L'] = weekly_grp['SPF'] / 100000
            fig2 = px.line(weekly_grp, x='Week', y='SPF_L',
                          markers=True, color_discrete_sequence=['#3b82f6'],
                          labels={'SPF_L': 'SPF (₹ Lakh)'})
            fig2.update_layout(plot_bgcolor='white', height=300)
            st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)

    # Loss Bucket
    with col3:
        st.subheader("Loss Bucket wise SPF")
        if loss_col and claim_col:
            loss_grp = df.groupby(loss_col)[claim_col].sum().reset_index()
            loss_grp.columns = ['Loss Bucket', 'SPF']
            loss_grp = loss_grp.sort_values('SPF', ascending=False)
            loss_grp['SPF_L'] = loss_grp['SPF'] / 100000
            fig3 = px.bar(loss_grp, x='Loss Bucket', y='SPF_L',
                         color='SPF_L', color_continuous_scale='Reds',
                         labels={'SPF_L': 'SPF (₹ Lakh)'},
                         text=loss_grp['SPF_L'].apply(lambda x: f'₹{x:.2f}L'))
            fig3.update_traces(textposition='outside')
            fig3.update_layout(showlegend=False, coloraxis_showscale=False,
                             plot_bgcolor='white', height=300)
            st.plotly_chart(fig3, use_container_width=True)

    # Top Categories
    with col4:
        st.subheader("Top 10 Categories")
        scat_col = get_col(df, 'scat')
        if scat_col:
            cat_grp = df.groupby(scat_col).size().reset_index()
            cat_grp.columns = ['Category', 'Returns']
            cat_grp = cat_grp.sort_values('Returns', ascending=False).head(10)
            fig4 = px.bar(cat_grp, x='Returns', y='Category',
                         orientation='h',
                         color='Returns', color_continuous_scale='Blues',
                         text='Returns')
            fig4.update_traces(textposition='inside')
            fig4.update_layout(showlegend=False, coloraxis_showscale=False,
                             plot_bgcolor='white', height=350,
                             yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig4, use_container_width=True)

# ════════════════════════════════
# TAB 2: QA ANALYSIS
# ════════════════════════════════
with tab2:
    st.subheader("👤 QA Name — SPF Performance")

    if qa_col and claim_col:
        qa_grp = df.groupby(qa_col).agg(
            Returns=(claim_col, 'count'),
            Total_SPF=(claim_col, 'sum'),
        ).reset_index()
        qa_grp.columns = ['QA Name', 'Returns', 'Total SPF (₹)']
        qa_grp['SPF (Cr)'] = (qa_grp['Total SPF (₹)'] / 10000000).round(6)
        qa_grp['SPF (₹ Lakh)'] = (qa_grp['Total SPF (₹)'] / 100000).round(2)
        qa_grp = qa_grp.sort_values('Total SPF (₹)', ascending=False)

        # Summary metrics
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Total QA Agents", len(qa_grp))
        with c2:
            st.metric("Total SPF", f"₹{qa_grp['Total SPF (₹)'].sum()/100000:.2f}L")
        with c3:
            st.metric("SPF in Cr", f"{qa_grp['Total SPF (₹)'].sum()/10000000:.4f} Cr")

        # Chart
        fig_qa = px.bar(qa_grp.head(20), x='QA Name', y='SPF (₹ Lakh)',
                       color='SPF (₹ Lakh)', color_continuous_scale='Oranges',
                       text=qa_grp.head(20)['SPF (₹ Lakh)'].apply(lambda x: f'₹{x:.1f}L'),
                       title="Top 20 QA by SPF Amount")
        fig_qa.update_traces(textposition='outside')
        fig_qa.update_layout(showlegend=False, coloraxis_showscale=False,
                            plot_bgcolor='white', height=400)
        st.plotly_chart(fig_qa, use_container_width=True)

        # Table
        st.markdown("**Full QA Table** — Sort karne ke liye column header pe click karo")
        qa_display = qa_grp.copy()
        qa_display['Total SPF (₹)'] = qa_display['Total SPF (₹)'].apply(lambda x: f"₹{x:,.2f}")
        qa_display['SPF (Cr)'] = qa_display['SPF (Cr)'].apply(lambda x: f"{x:.6f} Cr")
        st.dataframe(qa_display, use_container_width=True, height=400)
    else:
        st.warning("QA column nahi mila data mein!")

# ════════════════════════════════
# TAB 3: HUB ANALYSIS
# ════════════════════════════════
with tab3:
    st.subheader("🗺️ Hub (PH) wise Analysis")

    ph_col = get_col(df, 'ph')

    if ph_col and claim_col:
        # QA select
        if qa_col:
            qa_list = ['All QA'] + sorted(df[qa_col].dropna().astype(str).unique().tolist())
            selected_qa_hub = st.selectbox("QA Name select karo:", qa_list, key='hub_qa')
            if selected_qa_hub != 'All QA':
                hub_df = df[df[qa_col].astype(str) == selected_qa_hub]
            else:
                hub_df = df.copy()
        else:
            hub_df = df.copy()

        view_by = st.radio("View by:", ["Hub (PH)", "Loss Bucket", "Seller ID"], horizontal=True)

        if view_by == "Hub (PH)":
            grp_col = ph_col
        elif view_by == "Loss Bucket":
            grp_col = loss_col
        else:
            grp_col = get_col(df, 'seller')

        if grp_col:
            hub_grp = hub_df.groupby(grp_col).agg(
                Returns=(claim_col, 'count'),
                SPF=(claim_col, 'sum')
            ).reset_index()
            hub_grp.columns = [view_by, 'Returns', 'Total SPF (₹)']
            hub_grp['SPF (Cr)'] = (hub_grp['Total SPF (₹)'] / 10000000).round(6)
            hub_grp['SPF (₹ Lakh)'] = (hub_grp['Total SPF (₹)'] / 100000).round(2)
            hub_grp = hub_grp.sort_values('Total SPF (₹)', ascending=False)

            # Chart
            fig_hub = px.bar(hub_grp.head(15), x=view_by, y='SPF (₹ Lakh)',
                           color='SPF (₹ Lakh)', color_continuous_scale='Blues',
                           text=hub_grp.head(15)['SPF (₹ Lakh)'].apply(lambda x: f'₹{x:.2f}L'))
            fig_hub.update_traces(textposition='outside')
            fig_hub.update_layout(showlegend=False, coloraxis_showscale=False,
                                 plot_bgcolor='white', height=400)
            st.plotly_chart(fig_hub, use_container_width=True)

            # Table
            hub_display = hub_grp.copy()
            hub_display['Total SPF (₹)'] = hub_display['Total SPF (₹)'].apply(lambda x: f"₹{x:,.2f}")
            st.dataframe(hub_display, use_container_width=True, height=400)

# ════════════════════════════════
# TAB 4: DATA TABLE
# ════════════════════════════════
with tab4:
    st.subheader("📋 Filtered Data Table")

    # Additional filters
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    with col_f1:
        rtype_col = get_col(df, 'rtype')
        if rtype_col:
            rtype_vals = ['All'] + sorted(df[rtype_col].dropna().astype(str).unique().tolist())
            sel_rtype = st.selectbox("Return Type", rtype_vals)
            if sel_rtype != 'All':
                df = df[df[rtype_col].astype(str) == sel_rtype]

    with col_f2:
        city_col = get_col(df, 'city')
        if city_col:
            city_vals = ['All'] + sorted(df[city_col].dropna().astype(str).unique().tolist())
            sel_city = st.selectbox("City", city_vals)
            if sel_city != 'All':
                df = df[df[city_col].astype(str) == sel_city]

    with col_f3:
        seller_col = get_col(df, 'seller')
        if seller_col:
            sel_seller = st.text_input("Seller ID search")
            if sel_seller:
                df = df[df[seller_col].astype(str).str.contains(sel_seller, case=False, na=False)]

    with col_f4:
        search_all = st.text_input("🔍 Search anything")
        if search_all:
            mask = df.astype(str).apply(lambda x: x.str.contains(search_all, case=False, na=False)).any(axis=1)
            df = df[mask]

    st.markdown(f"**{len(df):,} rows** | Total SPF: **₹{df[claim_col].sum()/100000:.2f}L** ({df[claim_col].sum()/10000000:.4f} Cr)")

    # Show top 5000 rows
    display_cols = []
    for key in ['date', 'qa', 'ph', 'scat', 'city', 'loss', 'reason', 'rtype', 'claim', 'asp', 'obd', 'week']:
        col = get_col(df, key)
        if col:
            display_cols.append(col)
    display_cols.append('_month')

    show_df = df[display_cols].head(5000).copy()
    if claim_col in show_df.columns:
        show_df[claim_col] = show_df[claim_col].apply(lambda x: f"₹{x:,.2f}")

    st.dataframe(show_df, use_container_width=True, height=500)

    # Download
    csv_export = df.to_csv(index=False)
    st.download_button(
        "⬇️ Download Filtered Data",
        csv_export,
        "spf_filtered_data.csv",
        "text/csv"
    )

# ── FOOTER ──
st.markdown("---")
st.markdown(f"""
<div style="text-align:center;color:#94a3b8;font-size:12px">
Flipkart SPF Dashboard 2026 · {len(ALL_DATA):,} total rows loaded · All amounts in ₹ INR
</div>
""", unsafe_allow_html=True)
