import streamlit as st
import pandas as pd
import plotly.express as px
from io import StringIO, BytesIO

st.set_page_config(
    page_title="Flipkart SPF Dashboard 2026",
    page_icon="📦",
    layout="wide"
)

st.markdown("""
<style>
.block-container{padding-top:1rem}
div[data-testid="metric-container"]{background:white;border:1px solid #e2e8f0;border-radius:8px;padding:12px;border-left:4px solid #f97316}
</style>
""", unsafe_allow_html=True)

# ── HEADER ──
st.markdown("""
<div style="background:linear-gradient(90deg,#f97316,#fb923c);padding:15px 20px;border-radius:10px;color:white;margin-bottom:15px">
<h2 style="margin:0">📦 Flipkart SPF Dashboard — Pan India 2026</h2>
<p style="margin:0;opacity:0.9;font-size:14px">Seller Protection Fund · Returns & Claims · Manager View</p>
</div>
""", unsafe_allow_html=True)

# ── SIDEBAR ──
st.sidebar.markdown("## 📁 Data Upload")
st.sidebar.markdown("CSV files upload karo — sab automatically merge honge")

uploaded_files = st.sidebar.file_uploader(
    "CSV files select karo",
    type=['csv'],
    accept_multiple_files=True
)

if not uploaded_files:
    st.info("👈 **Left sidebar mein CSV files upload karo** — Jan, Feb, Mar... sab ek saath!")
    st.markdown("""
    ### Kaise Use Karein:
    1. Left sidebar mein **Browse files** click karo
    2. **Multiple CSV files** select karo (Ctrl+click)
    3. Dashboard **automatically** ban jayega ✅
    
    ### File name mein month hona chahiye:
    - `Jan SPF-2026.csv` ✅
    - `SPF_Feb_2026.csv` ✅
    - `Mar SPF-2026.csv` ✅
    """)
    st.stop()

# ── LOAD DATA ──
@st.cache_data
def load_files(files_data):
    dfs = []
    month_order = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']
    
    for fname, fcontent in files_data:
        try:
            df = pd.read_csv(BytesIO(fcontent), low_memory=False)
            # Detect month from filename
            fname_up = fname.upper()
            month = 'UNKNOWN'
            for m in month_order:
                if m in fname_up:
                    month = m
                    break
            df['_month'] = month
            df['_filename'] = fname
            dfs.append(df)
        except Exception as e:
            st.sidebar.error(f"❌ {fname}: {e}")
    
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()

# Prepare file data for caching
files_data = [(f.name, f.getvalue()) for f in uploaded_files]
ALL_DATA = load_files(files_data)

if ALL_DATA.empty:
    st.error("Data load nahi hua — CSV file check karo!")
    st.stop()

# Show loaded files
for f in uploaded_files:
    st.sidebar.success(f"✅ {f.name}")
st.sidebar.markdown(f"**Total: {len(ALL_DATA):,} rows**")

# ── DETECT COLUMNS ──
def find_col(df, options):
    for opt in options:
        if opt in df.columns:
            return opt
        # Case insensitive
        for col in df.columns:
            if col.lower() == opt.lower():
                return col
    return None

claim_col    = find_col(ALL_DATA, ['approved_claim_amount','claim_amount','Approved Claim Amount'])
qa_col       = find_col(ALL_DATA, ['QA','qa','QA Name','qa_name'])
ph_col       = find_col(ALL_DATA, ['PH','ph','Hub','hub'])
loss_col     = find_col(ALL_DATA, ['loss_bucket','Loss Bucket','loss bucket'])
asp_col      = find_col(ALL_DATA, ['ASP_buck','ASP','asp'])
sc_col       = find_col(ALL_DATA, ['flag_smart_check_done','Smart Check','sc'])
week_col     = find_col(ALL_DATA, ['week_num_in_year','Week','week'])
scat_col     = find_col(ALL_DATA, ['analytic_super_category','Super Category'])
city_col     = find_col(ALL_DATA, ['seller_city','City','city'])
loss_col     = find_col(ALL_DATA, ['loss_bucket','Loss Bucket'])
reason_col   = find_col(ALL_DATA, ['reason','Reason'])
rtype_col    = find_col(ALL_DATA, ['return_type','Return Type'])
seller_col   = find_col(ALL_DATA, ['seller_id','Seller ID'])
facility_col = find_col(ALL_DATA, ['source_facility_id','Source Facility'])
obd_col      = find_col(ALL_DATA, ['seller_obd_status','OBD Status'])
rr_col       = find_col(ALL_DATA, ['return_reason','Return Reason'])
cms_col      = find_col(ALL_DATA, ['cms_vertical','CMS Vertical'])

# ── NUMERIC CONVERSION ──
df_work = ALL_DATA.copy()
for col in [claim_col, asp_col, sc_col]:
    if col and col in df_work.columns:
        df_work[col] = pd.to_numeric(df_work[col], errors='coerce').fillna(0)

# ── SIDEBAR FILTERS ──
st.sidebar.markdown("---")
st.sidebar.markdown("## 🔍 Filters")

# Month
months = sorted(df_work['_month'].unique().tolist())
sel_months = st.sidebar.multiselect("📅 Month", months, default=months)
if sel_months:
    df = df_work[df_work['_month'].isin(sel_months)].copy()
else:
    df = df_work.copy()

# QA
if qa_col:
    qa_opts = ['All'] + sorted(df[qa_col].dropna().astype(str).unique().tolist())
    sel_qa = st.sidebar.selectbox("👤 QA Name", qa_opts)
    if sel_qa != 'All':
        df = df[df[qa_col].astype(str) == sel_qa]

# Loss Bucket
if loss_col:
    loss_opts = ['All'] + sorted(df[loss_col].dropna().astype(str).unique().tolist())
    sel_loss = st.sidebar.selectbox("📊 Loss Bucket", loss_opts)
    if sel_loss != 'All':
        df = df[df[loss_col].astype(str) == sel_loss]

# Week
if week_col:
    week_opts = ['All'] + sorted(df[week_col].dropna().astype(str).unique().tolist())
    sel_week = st.sidebar.selectbox("📆 Week", week_opts)
    if sel_week != 'All':
        df = df[df[week_col].astype(str) == sel_week]

st.sidebar.markdown(f"**Filtered: {len(df):,} rows**")

# ── KPIs ──
total_returns = len(df)
total_claim   = df[claim_col].sum() if claim_col else 0
avg_asp       = df[asp_col].mean() if asp_col else 0
sc_done       = df[sc_col].sum() if sc_col else 0
sc_pct        = (sc_done / total_returns * 100) if total_returns else 0
total_cr      = total_claim / 10000000

c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("📦 Total Returns",   f"{total_returns:,}")
c2.metric("💰 SPF (₹ Lakh)",    f"₹{total_claim/100000:.2f}L")
c3.metric("📈 SPF (Crore)",     f"{total_cr:.4f} Cr")
c4.metric("🏷️ Avg ASP",         f"₹{avg_asp:,.0f}")
c5.metric("✅ Smart Check",     f"{sc_pct:.1f}%")

st.markdown("---")

# ── TABS ──
tab1, tab2, tab3, tab4 = st.tabs(["📊 Charts", "👤 QA Analysis", "🗺️ Hub Analysis", "📋 Data Table"])

# ════ TAB 1: CHARTS ════
with tab1:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📅 Monthly SPF")
        if claim_col:
            m_grp = df_work[df_work['_month'].isin(sel_months)].groupby('_month')[claim_col].sum().reset_index()
            m_grp.columns = ['Month','SPF']
            month_order = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']
            m_grp['order'] = m_grp['Month'].apply(lambda x: month_order.index(x) if x in month_order else 99)
            m_grp = m_grp.sort_values('order')
            m_grp['SPF_L'] = (m_grp['SPF']/100000).round(2)
            fig = px.bar(m_grp, x='Month', y='SPF_L',
                        text=m_grp['SPF_L'].apply(lambda x: f'₹{x:.1f}L'),
                        color='SPF_L', color_continuous_scale='Oranges')
            fig.update_traces(textposition='outside')
            fig.update_layout(showlegend=False, coloraxis_showscale=False,
                            plot_bgcolor='white', height=320,
                            yaxis_title='SPF (₹ Lakh)')
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("📆 Weekly SPF")
        if week_col and claim_col:
            w_grp = df.groupby(week_col)[claim_col].sum().reset_index()
            w_grp.columns = ['Week','SPF']
            w_grp = w_grp.sort_values('Week')
            w_grp['SPF_L'] = (w_grp['SPF']/100000).round(2)
            fig2 = px.line(w_grp, x='Week', y='SPF_L',
                          markers=True, color_discrete_sequence=['#3b82f6'])
            fig2.update_layout(plot_bgcolor='white', height=320,
                              yaxis_title='SPF (₹ Lakh)')
            st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("📊 Loss Bucket SPF")
        if loss_col and claim_col:
            l_grp = df.groupby(loss_col)[claim_col].sum().reset_index()
            l_grp.columns = ['Loss Bucket','SPF']
            l_grp = l_grp.sort_values('SPF', ascending=False)
            l_grp['SPF_L'] = (l_grp['SPF']/100000).round(2)
            fig3 = px.bar(l_grp, x='Loss Bucket', y='SPF_L',
                         text=l_grp['SPF_L'].apply(lambda x: f'₹{x:.2f}L'),
                         color='SPF_L', color_continuous_scale='Reds')
            fig3.update_traces(textposition='outside')
            fig3.update_layout(showlegend=False, coloraxis_showscale=False,
                             plot_bgcolor='white', height=320,
                             yaxis_title='SPF (₹ Lakh)')
            st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.subheader("📦 Top Categories")
        if scat_col:
            cat_grp = df.groupby(scat_col).size().reset_index()
            cat_grp.columns = ['Category','Returns']
            cat_grp = cat_grp.sort_values('Returns', ascending=True).tail(10)
            fig4 = px.bar(cat_grp, x='Returns', y='Category',
                         orientation='h', text='Returns',
                         color='Returns', color_continuous_scale='Blues')
            fig4.update_traces(textposition='inside')
            fig4.update_layout(showlegend=False, coloraxis_showscale=False,
                             plot_bgcolor='white', height=320)
            st.plotly_chart(fig4, use_container_width=True)

# ════ TAB 2: QA ANALYSIS ════
with tab2:
    st.subheader("👤 QA Name — SPF Performance")

    if qa_col and claim_col:
        qa_grp = df.groupby(qa_col).agg(
            Returns=(claim_col,'count'),
            SPF=(claim_col,'sum')
        ).reset_index()
        qa_grp.columns = ['QA Name','Returns','Total SPF (₹)']
        qa_grp['SPF (Lakh)'] = (qa_grp['Total SPF (₹)']/100000).round(2)
        qa_grp['SPF (Cr)']   = (qa_grp['Total SPF (₹)']/10000000).round(6)
        qa_grp = qa_grp.sort_values('Total SPF (₹)', ascending=False)

        # Summary
        c1,c2,c3 = st.columns(3)
        c1.metric("Total QA Agents", f"{len(qa_grp):,}")
        c2.metric("Total SPF", f"₹{qa_grp['Total SPF (₹)'].sum()/100000:.2f}L")
        c3.metric("SPF in Cr", f"{qa_grp['Total SPF (₹)'].sum()/10000000:.4f} Cr")

        # Chart
        fig_qa = px.bar(
            qa_grp.head(20), x='QA Name', y='SPF (Lakh)',
            text=qa_grp.head(20)['SPF (Lakh)'].apply(lambda x: f'₹{x:.1f}L'),
            color='SPF (Lakh)', color_continuous_scale='Oranges',
            title="Top 20 QA by SPF"
        )
        fig_qa.update_traces(textposition='outside')
        fig_qa.update_layout(showlegend=False, coloraxis_showscale=False,
                            plot_bgcolor='white', height=400)
        st.plotly_chart(fig_qa, use_container_width=True)

        # Table
        st.markdown("**Full QA Table** — Column header pe click karke sort karo")
        disp = qa_grp.copy()
        disp['Total SPF (₹)'] = disp['Total SPF (₹)'].apply(lambda x: f"₹{x:,.2f}")
        disp['SPF (Cr)']      = disp['SPF (Cr)'].apply(lambda x: f"{x:.6f} Cr")
        st.dataframe(disp, use_container_width=True, height=450)
    else:
        st.warning("⚠️ QA column data mein nahi mila!")

# ════ TAB 3: HUB ANALYSIS ════
with tab3:
    st.subheader("🗺️ Hub (PH) wise Analysis")

    if ph_col and claim_col:
        # QA select
        if qa_col:
            qa_list = ['All QA'] + sorted(df[qa_col].dropna().astype(str).unique().tolist())
            sel_qa_hub = st.selectbox("QA Name select karo:", qa_list)
            hub_df = df[df[qa_col].astype(str) == sel_qa_hub] if sel_qa_hub != 'All QA' else df.copy()
        else:
            hub_df = df.copy()

        view_by = st.radio("View by:", ["Hub (PH)", "Loss Bucket", "Seller ID"], horizontal=True)
        grp_map = {"Hub (PH)": ph_col, "Loss Bucket": loss_col, "Seller ID": seller_col}
        grp_col = grp_map.get(view_by)

        if grp_col and grp_col in hub_df.columns:
            h_grp = hub_df.groupby(grp_col).agg(
                Returns=(claim_col,'count'),
                SPF=(claim_col,'sum')
            ).reset_index()
            h_grp.columns = [view_by,'Returns','Total SPF (₹)']
            h_grp['SPF (Lakh)'] = (h_grp['Total SPF (₹)']/100000).round(2)
            h_grp['SPF (Cr)']   = (h_grp['Total SPF (₹)']/10000000).round(6)
            h_grp = h_grp.sort_values('Total SPF (₹)', ascending=False)

            fig_hub = px.bar(
                h_grp.head(15), x=view_by, y='SPF (Lakh)',
                text=h_grp.head(15)['SPF (Lakh)'].apply(lambda x: f'₹{x:.2f}L'),
                color='SPF (Lakh)', color_continuous_scale='Blues'
            )
            fig_hub.update_traces(textposition='outside')
            fig_hub.update_layout(showlegend=False, coloraxis_showscale=False,
                                 plot_bgcolor='white', height=400)
            st.plotly_chart(fig_hub, use_container_width=True)

            disp2 = h_grp.copy()
            disp2['Total SPF (₹)'] = disp2['Total SPF (₹)'].apply(lambda x: f"₹{x:,.2f}")
            st.dataframe(disp2, use_container_width=True, height=400)
    else:
        st.warning("⚠️ PH/Hub column data mein nahi mila!")

# ════ TAB 4: DATA TABLE ════
with tab4:
    st.subheader("📋 Data Table with Filters")

    fc1,fc2,fc3,fc4 = st.columns(4)
    tbl_df = df.copy()

    with fc1:
        if rtype_col and rtype_col in tbl_df.columns:
            rt_opts = ['All'] + sorted(tbl_df[rtype_col].dropna().astype(str).unique().tolist())
            sel_rt = st.selectbox("Return Type", rt_opts)
            if sel_rt != 'All':
                tbl_df = tbl_df[tbl_df[rtype_col].astype(str) == sel_rt]

    with fc2:
        if city_col and city_col in tbl_df.columns:
            city_opts = ['All'] + sorted(tbl_df[city_col].dropna().astype(str).unique().tolist())
            sel_city = st.selectbox("City", city_opts)
            if sel_city != 'All':
                tbl_df = tbl_df[tbl_df[city_col].astype(str) == sel_city]

    with fc3:
        if seller_col and seller_col in tbl_df.columns:
            sel_seller = st.text_input("Seller ID search")
            if sel_seller:
                tbl_df = tbl_df[tbl_df[seller_col].astype(str).str.contains(sel_seller, case=False, na=False)]

    with fc4:
        search_all = st.text_input("🔍 Search anything")
        if search_all:
            mask = tbl_df.astype(str).apply(
                lambda x: x.str.contains(search_all, case=False, na=False)
            ).any(axis=1)
            tbl_df = tbl_df[mask]

    total_filtered = len(tbl_df)
    total_spf_filtered = tbl_df[claim_col].sum() if claim_col else 0
    st.markdown(f"**{total_filtered:,} rows** | SPF: **₹{total_spf_filtered/100000:.2f}L** ({total_spf_filtered/10000000:.4f} Cr)")

    # Display columns
    show_cols = ['_month']
    for col in [claim_col, qa_col, ph_col, loss_col, scat_col, city_col,
                reason_col, rtype_col, asp_col, obd_col, week_col]:
        if col and col in tbl_df.columns:
            show_cols.append(col)

    show_df = tbl_df[show_cols].head(5000).copy()
    if claim_col in show_df.columns:
        show_df = show_df.rename(columns={claim_col: 'SPF (₹)', '_month': 'Month'})

    st.dataframe(show_df, use_container_width=True, height=500)

    # Download
    st.download_button(
        "⬇️ Download Filtered CSV",
        tbl_df.to_csv(index=False).encode('utf-8'),
        "spf_filtered.csv",
        "text/csv"
    )

# ── FOOTER ──
st.markdown("---")
st.caption(f"Flipkart SPF Dashboard 2026 · {len(ALL_DATA):,} total rows · All amounts in ₹ INR")
