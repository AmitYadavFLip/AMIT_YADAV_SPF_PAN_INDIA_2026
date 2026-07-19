import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json

st.set_page_config(page_title="Flipkart SPF Dashboard 2026", page_icon="🛒", layout="wide")

st.markdown("""
<style>
.block-container{padding-top:0.5rem;max-width:100%}
div[data-testid="metric-container"]{
    background:white;border:1px solid #e2e8f0;border-radius:8px;
    padding:14px;border-left:4px solid #2874F0;
    box-shadow:0 1px 3px rgba(0,0,0,0.08)
}
div[data-testid="stMetricValue"]{color:#2874F0;font-weight:800;font-size:1.8rem}
div[data-testid="stMetricLabel"]{font-weight:600;font-size:0.9rem;color:#475569}
.stTabs [data-baseweb="tab-list"]{background:#f0f4ff;border-radius:10px;padding:5px;gap:5px}
.stTabs [data-baseweb="tab"]{border-radius:8px;font-weight:700;font-size:15px;padding:10px 28px;letter-spacing:0.3px}
.stTabs [aria-selected="true"]{background:#2874F0 !important;color:white !important}
.filter-row > div{display:inline-block}
h2,h3{color:#1a3a7a;font-weight:800}
footer{display:none}
header{display:none}
/* Filter dropdowns styling */
div[data-baseweb="select"] > div{border-radius:6px !important;border-color:#d1d9f0 !important}
</style>
""", unsafe_allow_html=True)

# ── HEADER ──
st.markdown("""
<div style="background:linear-gradient(135deg,#2874F0 0%,#1a5bbf 100%);padding:0;border-radius:12px;color:white;margin-bottom:12px;overflow:hidden;box-shadow:0 4px 12px rgba(40,116,240,0.3)">
  <div style="display:flex;align-items:center;justify-content:space-between;padding:16px 28px;flex-wrap:wrap;gap:12px">
    <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap">
      <div style="background:white;border-radius:10px;padding:8px 16px;display:flex;align-items:center;gap:8px;flex-shrink:0">
        <span style="color:#2874F0;font-size:20px;font-weight:900;letter-spacing:-1px">Flipkart</span>
        <div style="background:#FFD700;color:#2874F0;font-size:9px;font-weight:800;padding:2px 6px;border-radius:4px">PLUS</div>
      </div>
      <div>
        <div style="font-size:18px;font-weight:800;letter-spacing:-0.3px">SPF Dashboard — Pan India 2026</div>
        <div style="font-size:12px;opacity:0.85;margin-top:3px">Seller Protection Fund · Returns & Claims · Manager View</div>
      </div>
    </div>
    <div style="text-align:right;flex-shrink:0">
      <div style="background:rgba(255,255,255,0.2);border-radius:20px;padding:5px 14px;font-size:12px;font-weight:700;display:inline-block">🟢 LIVE</div>
      <div style="font-size:11px;opacity:0.75;margin-top:4px">Data: GitHub · Auto refresh</div>
    </div>
  </div>
  <div style="background:#FFD700;height:3px"></div>
</div>
""", unsafe_allow_html=True)

# ── GITHUB CONFIG ──
GITHUB_RAW = "https://raw.githubusercontent.com/AmitYadavFLip/AMIT_YADAV_SPF_PAN_INDIA_2026/main/"
MONTHS = {'Jan':'Jan_summary.json','Feb':'Feb_summary.json','Mar':'Mar_summary.json',
          'Apr':'Apr_summary.json','May':'May_summary.json','Jun':'Jun_summary.json'}

@st.cache_data(ttl=300)
def load_month(filename):
    r = requests.get(GITHUB_RAW + filename)
    return r.json() if r.status_code == 200 else None

with st.spinner("📊 Data load ho raha hai..."):
    all_data = {}
    for month, filename in MONTHS.items():
        data = load_month(filename)
        if data:
            all_data[month] = data

if not all_data:
    st.error("Data load nahi hua!")
    st.stop()

# ── HELPER FUNCTIONS ──
def merge_months(key, selected):
    dfs = []
    for m in selected:
        if m in all_data and key in all_data[m]:
            df = pd.DataFrame(all_data[m][key])
            df['_month'] = m
            dfs.append(df)
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

def to_num(df, col):
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

# ── TOP FILTER BAR ──
st.markdown("<div style='background:white;border-radius:10px;padding:12px 18px;border:1px solid #e2e8f0;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,0.05)'>", unsafe_allow_html=True)
fc1,fc2,fc3,fc4,fc5,fc6 = st.columns([1.5,1.5,1.5,1.5,1.5,1.5])

# Get filter options from all data
def get_unique(key, col):
    df = merge_months(key, list(all_data.keys()))
    if not df.empty and col in df.columns:
        return sorted(df[col].dropna().astype(str).unique().tolist())
    return []

with fc1:
    months_list = list(all_data.keys())
    sel_months = st.multiselect("📅 Month", months_list, default=months_list, label_visibility="visible")

if not sel_months:
    sel_months = months_list

with fc2:
    qa_opts = ['All QA'] + get_unique('qa', 'L1')
    sel_qa = st.selectbox("👤 QA Name (L1)", qa_opts)

with fc3:
    loss_opts = ['All Loss Bucket'] + get_unique('loss', 'loss_bucket')
    sel_loss = st.selectbox("📊 Loss Bucket", loss_opts)

with fc4:
    rr_opts = ['All Return Reason'] + get_unique('rr', 'return_reason')
    sel_rr = st.selectbox("🔄 Return Reason", rr_opts)

with fc5:
    rt_opts = ['All Return Type'] + get_unique('rtype', 'return_type')
    sel_rt = st.selectbox("📦 Return Type", rt_opts)

with fc6:
    ekl_opts = ['All EKL/3PL'] + get_unique('ekl', 'ekl_3pl_flag')
    sel_ekl = st.selectbox("🚚 EKL/3PL Flag", ekl_opts)

st.markdown("</div>", unsafe_allow_html=True)

# ── MERGE & FILTER DATA ──
# Base data for KPIs
kpi_df = merge_months('kpis', sel_months)
kpi_df = to_num(kpi_df, 'total_spf')
total_spf = kpi_df['total_spf'].sum() if not kpi_df.empty else 0
total_cr = total_spf / 10000000

# ── TOP KPI — SINGLE BIG NUMBER ──
st.markdown(f"""
<div style="background:linear-gradient(135deg,#f0f4ff,#e8edff);border:2px solid #2874F0;border-radius:12px;padding:18px 28px;margin-bottom:16px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px">
  <div>
    <div style="font-size:13px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.8px">Total SPF (Approved Claim Amount)</div>
    <div style="font-size:42px;font-weight:900;color:#2874F0;letter-spacing:-1px;margin-top:4px">{total_cr:.2f} <span style="font-size:24px">Cr</span></div>
    <div style="font-size:13px;color:#64748b;margin-top:2px">₹{total_spf:,.0f} &nbsp;·&nbsp; {kpi_df['total_returns'].sum() if not kpi_df.empty else 0:,.0f} returns</div>
  </div>
  <div style="display:flex;gap:20px;flex-wrap:wrap">
    <div style="text-align:center;background:white;border-radius:10px;padding:12px 20px;border:1px solid #d1d9f0">
      <div style="font-size:11px;color:#64748b;font-weight:600;text-transform:uppercase">Avg ASP</div>
      <div style="font-size:22px;font-weight:800;color:#2874F0">₹{kpi_df['avg_asp'].mean():.0f if not kpi_df.empty else 0}</div>
    </div>
    <div style="text-align:center;background:white;border-radius:10px;padding:12px 20px;border:1px solid #d1d9f0">
      <div style="font-size:11px;color:#64748b;font-weight:600;text-transform:uppercase">Sellers</div>
      <div style="font-size:22px;font-weight:800;color:#2874F0">{kpi_df['total_sellers'].sum() if not kpi_df.empty else 0:,.0f}</div>
    </div>
    <div style="text-align:center;background:white;border-radius:10px;padding:12px 20px;border:1px solid #d1d9f0">
      <div style="font-size:11px;color:#64748b;font-weight:600;text-transform:uppercase">Hubs</div>
      <div style="font-size:22px;font-weight:800;color:#2874F0">{kpi_df['total_hubs'].sum() if not kpi_df.empty else 0:,.0f}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── TABS ──
tab1, tab2, tab3, tab4 = st.tabs(["📊 Loss Bucket View", "👤 QA Analysis", "🗺️ Hub Analysis", "📋 Details"])

# ════ TAB 1: LOSS BUCKET VIEW ════
with tab1:
    st.markdown("### 📊 Loss Bucket wise SPF Analysis")

    # Loss bucket data
    loss_df = merge_months('loss', sel_months)
    loss_df = to_num(loss_df, 'spf')
    loss_df = to_num(loss_df, 'returns')

    if not loss_df.empty:
        lg = loss_df.groupby('loss_bucket').agg(
            returns=('returns','sum'), spf=('spf','sum')
        ).reset_index().sort_values('spf', ascending=False)
        lg['SPF (Cr)'] = (lg['spf']/10000000).round(4)
        lg['SPF (Lakh)'] = (lg['spf']/100000).round(2)

        # Filter by loss bucket
        if sel_loss != 'All Loss Bucket':
            lg = lg[lg['loss_bucket']==sel_loss]

        # Loss bucket cards
        cols = st.columns(len(lg) if len(lg) <= 6 else 6)
        for i, (_, row) in enumerate(lg.iterrows()):
            if i < 6:
                with cols[i]:
                    color = ['#dc2626','#f97316','#f59e0b','#2874F0','#8b5cf6','#14b8a6'][i%6]
                    st.markdown(f"""
                    <div style="background:white;border-radius:10px;padding:16px;border-top:4px solid {color};border:1px solid #e2e8f0;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,0.06)">
                      <div style="font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.5px">{row['loss_bucket']}</div>
                      <div style="font-size:26px;font-weight:900;color:{color};margin:8px 0">{row['SPF (Cr)']:.4f} Cr</div>
                      <div style="font-size:12px;color:#94a3b8">{row['returns']:,.0f} returns</div>
                      <div style="font-size:11px;color:#94a3b8">₹{row['SPF (Lakh)']:.1f}L</div>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Loss bucket bar chart
        fig = px.bar(lg, x='loss_bucket', y='SPF (Cr)',
                    text=lg['SPF (Cr)'].apply(lambda x: f'{x:.4f} Cr'),
                    color='loss_bucket',
                    color_discrete_sequence=['#dc2626','#f97316','#f59e0b','#2874F0','#8b5cf6','#14b8a6'],
                    title="Loss Bucket wise SPF (in Crore)")
        fig.update_traces(textposition='outside', textfont_size=12)
        fig.update_layout(showlegend=False, plot_bgcolor='white', height=380,
                         xaxis_title="Loss Bucket", yaxis_title="SPF (Crore)",
                         title_font_size=16, title_font_color='#1a3a7a')
        fig.update_xaxes(tickfont_size=12)
        st.plotly_chart(fig, use_container_width=True)

        # Monthly trend per loss bucket
        st.markdown("### 📅 Month-wise Loss Bucket Trend")
        monthly_loss = loss_df.groupby(['_month','loss_bucket'])['spf'].sum().reset_index()
        monthly_loss['SPF (Cr)'] = (monthly_loss['spf']/10000000).round(4)
        month_order = ['Jan','Feb','Mar','Apr','May','Jun']
        monthly_loss['order'] = monthly_loss['_month'].apply(lambda x: month_order.index(x) if x in month_order else 99)
        monthly_loss = monthly_loss.sort_values('order')

        fig2 = px.line(monthly_loss, x='_month', y='SPF (Cr)', color='loss_bucket',
                      markers=True, title="Monthly SPF trend by Loss Bucket")
        fig2.update_layout(plot_bgcolor='white', height=350,
                          title_font_size=16, title_font_color='#1a3a7a',
                          legend_title="Loss Bucket")
        st.plotly_chart(fig2, use_container_width=True)

# ════ TAB 2: QA ANALYSIS ════
with tab2:
    st.markdown("### 👤 QA Name (L1) — SPF Performance")

    qa_df = merge_months('qa', sel_months)
    qa_df = to_num(qa_df, 'spf')
    qa_df = to_num(qa_df, 'returns')

    if not qa_df.empty:
        # Apply QA filter
        if sel_qa != 'All QA':
            qa_df = qa_df[qa_df['L1']==sel_qa]

        # Apply loss filter via qa_loss
        if sel_loss != 'All Loss Bucket':
            qa_loss_df = merge_months('qa_loss', sel_months)
            qa_loss_df = to_num(qa_loss_df, 'spf')
            qa_loss_df = qa_loss_df[qa_loss_df['loss_bucket']==sel_loss]
            qa_show = qa_loss_df.groupby('L1')['spf'].sum().reset_index()
        else:
            qa_show = qa_df.groupby('L1')['spf'].sum().reset_index()

        qa_show.columns = ['QA Name','SPF']
        qa_show = qa_show.sort_values('SPF', ascending=False)
        qa_show['SPF (Cr)'] = (qa_show['SPF']/10000000).round(4)
        qa_show['SPF (Lakh)'] = (qa_show['SPF']/100000).round(2)

        # QA KPIs
        c1,c2,c3 = st.columns(3)
        c1.metric("Total QA Agents", f"{len(qa_show)}")
        c2.metric("Total SPF", f"₹{qa_show['SPF'].sum()/100000:.2f}L")
        c3.metric("SPF (Cr)", f"{qa_show['SPF'].sum()/10000000:.4f} Cr")

        # QA Chart
        fig_qa = px.bar(qa_show, x='QA Name', y='SPF (Cr)',
                       text=qa_show['SPF (Cr)'].apply(lambda x: f'{x:.4f} Cr'),
                       color='SPF (Cr)', color_continuous_scale='Blues',
                       title="QA wise SPF (Crore)")
        fig_qa.update_traces(textposition='outside', textfont_size=11)
        fig_qa.update_layout(showlegend=False, coloraxis_showscale=False,
                            plot_bgcolor='white', height=380,
                            title_font_size=16, title_font_color='#1a3a7a')
        st.plotly_chart(fig_qa, use_container_width=True)

        # QA Table
        disp = qa_show.copy()
        disp['SPF (₹)'] = disp['SPF'].apply(lambda x: f"₹{x:,.2f}")
        disp = disp[['QA Name','SPF (₹)','SPF (Lakh)','SPF (Cr)']]
        st.dataframe(disp, use_container_width=True, height=300)

        # Hub drill down
        st.markdown("---")
        st.markdown("### 🔍 QA → Hub Drill Down")
        qa_hub_df = merge_months('qa_hub', sel_months)
        qa_hub_df = to_num(qa_hub_df, 'spf')

        if not qa_hub_df.empty:
            qa_names = ['Select QA'] + sorted(qa_hub_df['L1'].dropna().unique().tolist())
            sel_qa_drill = st.selectbox("QA Name select karo:", qa_names, key='qa_drill')
            if sel_qa_drill != 'Select QA':
                hub_detail = qa_hub_df[qa_hub_df['L1']==sel_qa_drill].copy()
                hub_detail = hub_detail.groupby('Ph')['spf'].sum().reset_index()
                hub_detail = hub_detail.sort_values('spf', ascending=False)
                hub_detail['SPF (Cr)'] = (hub_detail['spf']/10000000).round(4)

                fh = px.bar(hub_detail.head(15), x='Ph', y='SPF (Cr)',
                           text=hub_detail.head(15)['SPF (Cr)'].apply(lambda x: f'{x:.4f} Cr'),
                           color='SPF (Cr)', color_continuous_scale='Blues',
                           title=f"{sel_qa_drill} — Hub wise SPF")
                fh.update_traces(textposition='outside')
                fh.update_layout(showlegend=False, coloraxis_showscale=False,
                                plot_bgcolor='white', height=350)
                st.plotly_chart(fh, use_container_width=True)

                hub_detail['SPF (₹)'] = hub_detail['spf'].apply(lambda x: f"₹{x:,.2f}")
                st.dataframe(hub_detail[['Ph','SPF (₹)','SPF (Cr)']].rename(columns={'Ph':'Hub'}),
                            use_container_width=True, height=300)

# ════ TAB 3: HUB ANALYSIS ════
with tab3:
    st.markdown("### 🗺️ Hub (PH) — SPF Analysis")

    hub_df = merge_months('hub', sel_months)
    hub_df = to_num(hub_df, 'spf')
    hub_df = to_num(hub_df, 'returns')

    if not hub_df.empty:
        hg = hub_df.groupby('Ph').agg(returns=('returns','sum'), spf=('spf','sum')).reset_index()
        hg = hg.sort_values('spf', ascending=False)
        hg['SPF (Cr)'] = (hg['spf']/10000000).round(4)
        hg['SPF (Lakh)'] = (hg['spf']/100000).round(2)

        search = st.text_input("🔍 Hub search karo")
        if search:
            hg = hg[hg['Ph'].str.contains(search, case=False, na=False)]

        c1,c2 = st.columns(2)
        c1.metric("Total Hubs", f"{len(hg):,}")
        c2.metric("Total SPF", f"{hg['spf'].sum()/10000000:.4f} Cr")

        fhub = px.bar(hg.head(20), x='Ph', y='SPF (Cr)',
                     text=hg.head(20)['SPF (Cr)'].apply(lambda x: f'{x:.4f}'),
                     color='SPF (Cr)', color_continuous_scale='Blues',
                     title="Top 20 Hubs by SPF (Crore)")
        fhub.update_traces(textposition='outside')
        fhub.update_layout(showlegend=False, coloraxis_showscale=False,
                          plot_bgcolor='white', height=400,
                          title_font_size=16, title_font_color='#1a3a7a')
        st.plotly_chart(fhub, use_container_width=True)

        hg['SPF (₹)'] = hg['spf'].apply(lambda x: f"₹{x:,.2f}")
        st.dataframe(hg[['Ph','returns','SPF (₹)','SPF (Lakh)','SPF (Cr)']].rename(columns={'Ph':'Hub'}),
                    use_container_width=True, height=400)

# ════ TAB 4: DETAILS ════
with tab4:
    st.markdown("### 📋 Return Details")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**📊 Loss Bucket wise**")
        loss_d = merge_months('loss', sel_months)
        loss_d = to_num(loss_d, 'spf')
        if not loss_d.empty:
            if sel_loss != 'All Loss Bucket':
                loss_d = loss_d[loss_d['loss_bucket']==sel_loss]
            lg2 = loss_d.groupby('loss_bucket').agg(returns=('returns','sum'),spf=('spf','sum')).reset_index()
            lg2 = lg2.sort_values('spf', ascending=False)
            lg2['SPF (Cr)'] = (lg2['spf']/10000000).round(4)
            lg2['SPF (₹)'] = lg2['spf'].apply(lambda x: f"₹{x:,.2f}")
            st.dataframe(lg2[['loss_bucket','returns','SPF (₹)','SPF (Cr)']],
                        use_container_width=True, height=280)

    with c2:
        st.markdown("**🔄 Return Reason wise**")
        rr_d = merge_months('rr', sel_months)
        rr_d = to_num(rr_d, 'spf')
        if not rr_d.empty:
            if sel_rr != 'All Return Reason':
                rr_d = rr_d[rr_d['return_reason']==sel_rr]
            rr2 = rr_d.groupby('return_reason').agg(returns=('returns','sum'),spf=('spf','sum')).reset_index()
            rr2 = rr2.sort_values('spf', ascending=False)
            rr2['SPF (Cr)'] = (rr2['spf']/10000000).round(4)
            rr2['SPF (₹)'] = rr2['spf'].apply(lambda x: f"₹{x:,.2f}")
            st.dataframe(rr2[['return_reason','returns','SPF (₹)','SPF (Cr)']],
                        use_container_width=True, height=280)

    st.markdown("---")
    c3, c4 = st.columns(2)

    with c3:
        st.markdown("**📦 Return Type wise**")
        rt_d = merge_months('rtype', sel_months)
        rt_d = to_num(rt_d, 'spf')
        if not rt_d.empty:
            if sel_rt != 'All Return Type':
                rt_d = rt_d[rt_d['return_type']==sel_rt]
            rt2 = rt_d.groupby('return_type').agg(returns=('returns','sum'),spf=('spf','sum')).reset_index()
            rt2['SPF (Cr)'] = (rt2['spf']/10000000).round(4)
            rt2['SPF (₹)'] = rt2['spf'].apply(lambda x: f"₹{x:,.2f}")
            st.dataframe(rt2, use_container_width=True, height=200)

    with c4:
        st.markdown("**🚚 EKL/3PL wise**")
        ekl_d = merge_months('ekl', sel_months)
        ekl_d = to_num(ekl_d, 'spf')
        if not ekl_d.empty:
            if sel_ekl != 'All EKL/3PL':
                ekl_d = ekl_d[ekl_d['ekl_3pl_flag']==sel_ekl]
            ek2 = ekl_d.groupby('ekl_3pl_flag').agg(returns=('returns','sum'),spf=('spf','sum')).reset_index()
            ek2['SPF (Cr)'] = (ek2['spf']/10000000).round(4)
            ek2['SPF (₹)'] = ek2['spf'].apply(lambda x: f"₹{x:,.2f}")
            st.dataframe(ek2, use_container_width=True, height=200)

# ── FOOTER ──
st.markdown("""
<div style="margin-top:24px;background:linear-gradient(135deg,#2874F0,#1a5bbf);border-radius:10px;padding:14px 24px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
  <div style="color:white;font-size:12px;opacity:0.9">
    📊 Flipkart SPF Dashboard 2026 &nbsp;·&nbsp; Data: GitHub &nbsp;·&nbsp; All amounts in ₹ INR
  </div>
  <div style="background:#FFD700;color:#1a3a7a;font-size:13px;font-weight:800;padding:7px 18px;border-radius:20px">
    ✨ Made By Amit Yadav — QA
  </div>
</div>
""", unsafe_allow_html=True)
