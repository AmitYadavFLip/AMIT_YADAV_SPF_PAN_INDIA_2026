import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json

st.set_page_config(page_title="Flipkart SPF Dashboard 2026", page_icon="📦", layout="wide")

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
<p style="margin:0;opacity:0.9;font-size:14px">Seller Protection Fund · Returns & Claims · Manager View · 🟢 LIVE</p>
</div>
""", unsafe_allow_html=True)

# ── GITHUB DATA CONFIG ──
GITHUB_RAW = "https://raw.githubusercontent.com/AmitYadavFLip/AMIT_YADAV_SPF_PAN_INDIA_2026/main/"

MONTHS = {
    'Jan': 'Jan_summary.json',
    # 'Feb': 'Feb_summary.json',  # Uncomment jab file upload ho
    # 'Mar': 'Mar_summary.json',
    # 'Apr': 'Apr_summary.json',
    # 'May': 'May_summary.json',
    # 'Jun': 'Jun_summary.json',
}

@st.cache_data(ttl=300)  # 5 min cache
def load_month(filename):
    url = GITHUB_RAW + filename
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()
    return None

# ── LOAD DATA ──
with st.spinner("📊 Data load ho raha hai..."):
    all_data = {}
    for month, filename in MONTHS.items():
        data = load_month(filename)
        if data:
            all_data[month] = data

if not all_data:
    st.error("Data load nahi hua!")
    st.stop()

# ── MONTH FILTER ──
available_months = list(all_data.keys())
col_m1, col_m2 = st.columns([3,1])
with col_m1:
    selected_months = st.multiselect("📅 Month Filter", available_months, default=available_months)
with col_m2:
    st.markdown(f"<div style='padding-top:28px;color:#64748b;font-size:12px'>🟢 {len(available_months)} months live</div>", unsafe_allow_html=True)

if not selected_months:
    selected_months = available_months

# ── MERGE SELECTED MONTHS ──
def merge_months(key, selected):
    dfs = []
    for m in selected:
        if m in all_data and key in all_data[m]:
            df = pd.DataFrame(all_data[m][key])
            df['_month'] = m
            dfs.append(df)
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()

# KPIs merge
kpi_df = merge_months('kpis', selected_months)
total_returns = int(kpi_df['total_returns'].sum()) if not kpi_df.empty else 0
total_spf     = float(kpi_df['total_spf'].sum()) if not kpi_df.empty else 0
avg_asp       = float(kpi_df['avg_asp'].mean()) if not kpi_df.empty else 0
total_sellers = int(kpi_df['total_sellers'].sum()) if not kpi_df.empty else 0

# ── KPI CARDS ──
c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("📦 Total Returns",  f"{total_returns:,}")
c2.metric("💰 SPF (₹ Lakh)",   f"₹{total_spf/100000:.2f}L")
c3.metric("📈 SPF (Crore)",    f"{total_spf/10000000:.4f} Cr")
c4.metric("🏷️ Avg ASP",        f"₹{avg_asp:,.0f}")
c5.metric("🏪 Sellers",        f"{total_sellers:,}")

st.markdown("---")

# ── TABS ──
tab1, tab2, tab3, tab4 = st.tabs(["📊 Charts", "👤 QA Analysis", "🗺️ Hub Analysis", "📋 Details"])

# ════ TAB 1: CHARTS ════
with tab1:
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("📅 Monthly SPF")
        kpi_chart = kpi_df[['_month','total_spf']].copy()
        kpi_chart['SPF_L'] = (kpi_chart['total_spf']/100000).round(2)
        month_order = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        kpi_chart['order'] = kpi_chart['_month'].apply(lambda x: month_order.index(x) if x in month_order else 99)
        kpi_chart = kpi_chart.sort_values('order')
        fig = px.bar(kpi_chart, x='_month', y='SPF_L',
                    text=kpi_chart['SPF_L'].apply(lambda x: f'₹{x:.1f}L'),
                    color='SPF_L', color_continuous_scale='Oranges',
                    labels={'_month':'Month','SPF_L':'SPF (₹ Lakh)'})
        fig.update_traces(textposition='outside')
        fig.update_layout(showlegend=False, coloraxis_showscale=False,
                         plot_bgcolor='white', height=320)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("📆 Weekly SPF")
        week_df = merge_months('weekly', selected_months)
        if not week_df.empty:
            week_df['spf'] = pd.to_numeric(week_df['spf'], errors='coerce').fillna(0)
            wg = week_df.groupby('week_num_in_year')['spf'].sum().reset_index()
            wg = wg.sort_values('week_num_in_year')
            wg['SPF_L'] = (wg['spf']/100000).round(2)
            fig2 = px.line(wg, x='week_num_in_year', y='SPF_L',
                          markers=True, color_discrete_sequence=['#3b82f6'],
                          labels={'week_num_in_year':'Week','SPF_L':'SPF (₹ Lakh)'})
            fig2.update_layout(plot_bgcolor='white', height=320)
            st.plotly_chart(fig2, use_container_width=True)

    c3, c4 = st.columns(2)

    with c3:
        st.subheader("📊 Loss Bucket SPF")
        loss_df = merge_months('loss', selected_months)
        if not loss_df.empty:
            loss_df['spf'] = pd.to_numeric(loss_df['spf'], errors='coerce').fillna(0)
            lg = loss_df.groupby('loss_bucket')['spf'].sum().reset_index()
            lg = lg.sort_values('spf', ascending=False)
            lg['SPF_L'] = (lg['spf']/100000).round(2)
            fig3 = px.bar(lg, x='loss_bucket', y='SPF_L',
                         text=lg['SPF_L'].apply(lambda x: f'₹{x:.2f}L'),
                         color='SPF_L', color_continuous_scale='Reds',
                         labels={'loss_bucket':'Loss Bucket','SPF_L':'SPF (₹ Lakh)'})
            fig3.update_traces(textposition='outside')
            fig3.update_layout(showlegend=False, coloraxis_showscale=False,
                              plot_bgcolor='white', height=320)
            st.plotly_chart(fig3, use_container_width=True)

    with c4:
        st.subheader("📦 Top CMS Verticals")
        cms_df = merge_months('cms', selected_months)
        if not cms_df.empty:
            cms_df['spf'] = pd.to_numeric(cms_df['spf'], errors='coerce').fillna(0)
            cg = cms_df.groupby('cms_vertical')['spf'].sum().reset_index()
            cg = cg.sort_values('spf', ascending=True).tail(10)
            cg['SPF_L'] = (cg['spf']/100000).round(2)
            fig4 = px.bar(cg, x='SPF_L', y='cms_vertical',
                         orientation='h',
                         text=cg['SPF_L'].apply(lambda x: f'₹{x:.2f}L'),
                         color='SPF_L', color_continuous_scale='Blues',
                         labels={'cms_vertical':'CMS Vertical','SPF_L':'SPF (₹ Lakh)'})
            fig4.update_traces(textposition='inside')
            fig4.update_layout(showlegend=False, coloraxis_showscale=False,
                              plot_bgcolor='white', height=320)
            st.plotly_chart(fig4, use_container_width=True)

# ════ TAB 2: QA ANALYSIS ════
with tab2:
    st.subheader("👤 QA Name — SPF Performance")

    qa_df = merge_months('qa', selected_months)
    if not qa_df.empty:
        qa_df['spf'] = pd.to_numeric(qa_df['spf'], errors='coerce').fillna(0)
        qa_df['returns'] = pd.to_numeric(qa_df['returns'], errors='coerce').fillna(0)

        # Loss bucket filter
        loss_df2 = merge_months('qa_loss', selected_months)
        loss_vals = ['All Loss'] + sorted(loss_df2['loss_bucket'].dropna().unique().tolist()) if not loss_df2.empty else ['All Loss']
        sel_loss = st.selectbox("📊 Loss Bucket Filter", loss_vals)

        if sel_loss != 'All Loss' and not loss_df2.empty:
            loss_df2['spf'] = pd.to_numeric(loss_df2['spf'], errors='coerce').fillna(0)
            filtered_qa = loss_df2[loss_df2['loss_bucket']==sel_loss].groupby('QA_Name')['spf'].sum().reset_index()
            filtered_qa.columns = ['QA_Name','spf']
            qa_show = filtered_qa
        else:
            qa_show = qa_df.groupby('QA_Name')['spf'].sum().reset_index()

        qa_show = qa_show.sort_values('spf', ascending=False)
        qa_show['SPF (Lakh)'] = (qa_show['spf']/100000).round(2)
        qa_show['SPF (Cr)']   = (qa_show['spf']/10000000).round(6)

        # KPIs
        c1,c2,c3 = st.columns(3)
        c1.metric("Total QA", len(qa_show))
        c2.metric("Total SPF", f"₹{qa_show['spf'].sum()/100000:.2f}L")
        c3.metric("SPF (Cr)", f"{qa_show['spf'].sum()/10000000:.4f} Cr")

        # Chart
        fq = px.bar(qa_show, x='QA_Name', y='SPF (Lakh)',
                   text=qa_show['SPF (Lakh)'].apply(lambda x: f'₹{x:.1f}L'),
                   color='SPF (Lakh)', color_continuous_scale='Oranges',
                   title="QA wise SPF")
        fq.update_traces(textposition='outside')
        fq.update_layout(showlegend=False, coloraxis_showscale=False,
                        plot_bgcolor='white', height=400)
        st.plotly_chart(fq, use_container_width=True)

        # Table
        st.markdown("**Full QA Table** — Column pe click karke sort karo")
        disp = qa_show[['QA_Name','SPF (Lakh)','SPF (Cr)']].copy()
        disp['SPF (₹)'] = qa_show['spf'].apply(lambda x: f"₹{x:,.2f}")
        st.dataframe(disp, use_container_width=True, height=400)

        # Hub drill down
        st.markdown("---")
        st.subheader("🔍 QA → Hub Drill Down")
        qa_hub_df = merge_months('qa_hub', selected_months)
        if not qa_hub_df.empty:
            qa_hub_df['spf'] = pd.to_numeric(qa_hub_df['spf'], errors='coerce').fillna(0)
            qa_names = ['Select QA'] + sorted(qa_hub_df['QA_Name'].dropna().unique().tolist())
            sel_qa = st.selectbox("QA Name select karo:", qa_names)
            if sel_qa != 'Select QA':
                hub_detail = qa_hub_df[qa_hub_df['QA_Name']==sel_qa].copy()
                hub_detail = hub_detail.sort_values('spf', ascending=False)
                hub_detail['SPF (Lakh)'] = (hub_detail['spf']/100000).round(2)
                hub_detail['SPF (Cr)']   = (hub_detail['spf']/10000000).round(6)

                fh = px.bar(hub_detail.head(15), x='Ph_Name', y='SPF (Lakh)',
                           text=hub_detail.head(15)['SPF (Lakh)'].apply(lambda x: f'₹{x:.2f}L'),
                           color='SPF (Lakh)', color_continuous_scale='Blues',
                           title=f"{sel_qa} — Hub wise SPF")
                fh.update_traces(textposition='outside')
                fh.update_layout(showlegend=False, coloraxis_showscale=False,
                                plot_bgcolor='white', height=350)
                st.plotly_chart(fh, use_container_width=True)

                disp2 = hub_detail[['Ph_Name','returns','SPF (Lakh)','SPF (Cr)']].copy()
                disp2['SPF (₹)'] = hub_detail['spf'].apply(lambda x: f"₹{x:,.2f}")
                st.dataframe(disp2, use_container_width=True, height=350)

# ════ TAB 3: HUB ANALYSIS ════
with tab3:
    st.subheader("🗺️ Hub (PH) — SPF Analysis")

    hub_df = merge_months('hub', selected_months)
    if not hub_df.empty:
        hub_df['spf'] = pd.to_numeric(hub_df['spf'], errors='coerce').fillna(0)
        hub_df['returns'] = pd.to_numeric(hub_df['returns'], errors='coerce').fillna(0)

        hg = hub_df.groupby('Ph_Name').agg(
            returns=('returns','sum'),
            spf=('spf','sum')
        ).reset_index().sort_values('spf', ascending=False)
        hg['SPF (Lakh)'] = (hg['spf']/100000).round(2)
        hg['SPF (Cr)']   = (hg['spf']/10000000).round(6)

        # Search
        search = st.text_input("🔍 Hub search karo")
        if search:
            hg = hg[hg['Ph_Name'].str.contains(search, case=False, na=False)]

        c1,c2 = st.columns(2)
        c1.metric("Total Hubs", len(hg))
        c2.metric("Total SPF", f"₹{hg['spf'].sum()/100000:.2f}L")

        fhub = px.bar(hg.head(20), x='Ph_Name', y='SPF (Lakh)',
                     text=hg.head(20)['SPF (Lakh)'].apply(lambda x: f'₹{x:.2f}L'),
                     color='SPF (Lakh)', color_continuous_scale='Blues',
                     title="Top 20 Hubs by SPF")
        fhub.update_traces(textposition='outside')
        fhub.update_layout(showlegend=False, coloraxis_showscale=False,
                          plot_bgcolor='white', height=400)
        st.plotly_chart(fhub, use_container_width=True)

        disp3 = hg[['Ph_Name','returns','SPF (Lakh)','SPF (Cr)']].copy()
        disp3['SPF (₹)'] = hg['spf'].apply(lambda x: f"₹{x:,.2f}")
        st.dataframe(disp3, use_container_width=True, height=450)

# ════ TAB 4: DETAILS ════
with tab4:
    st.subheader("📋 Loss Bucket & Return Reason Details")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**Loss Bucket wise**")
        loss_detail = merge_months('loss', selected_months)
        if not loss_detail.empty:
            loss_detail['spf'] = pd.to_numeric(loss_detail['spf'], errors='coerce').fillna(0)
            lg2 = loss_detail.groupby('loss_bucket').agg(
                returns=('returns','sum'), spf=('spf','sum')
            ).reset_index().sort_values('spf', ascending=False)
            lg2['SPF (Lakh)'] = (lg2['spf']/100000).round(2)
            lg2['SPF (Cr)'] = (lg2['spf']/10000000).round(6)
            lg2['SPF (₹)'] = lg2['spf'].apply(lambda x: f"₹{x:,.2f}")
            st.dataframe(lg2[['loss_bucket','returns','SPF (₹)','SPF (Lakh)','SPF (Cr)']],
                        use_container_width=True, height=300)

    with c2:
        st.markdown("**Return Reason wise**")
        rr_detail = merge_months('rr', selected_months)
        if not rr_detail.empty:
            rr_detail['spf'] = pd.to_numeric(rr_detail['spf'], errors='coerce').fillna(0)
            rr2 = rr_detail.groupby('return_reason').agg(
                returns=('returns','sum'), spf=('spf','sum')
            ).reset_index().sort_values('spf', ascending=False)
            rr2['SPF (Lakh)'] = (rr2['spf']/100000).round(2)
            rr2['SPF (₹)'] = rr2['spf'].apply(lambda x: f"₹{x:,.2f}")
            st.dataframe(rr2[['return_reason','returns','SPF (₹)','SPF (Lakh)']],
                        use_container_width=True, height=300)

    st.markdown("---")
    st.markdown("**Return Type wise**")
    rtype_detail = merge_months('rtype', selected_months)
    if not rtype_detail.empty:
        rtype_detail['spf'] = pd.to_numeric(rtype_detail['spf'], errors='coerce').fillna(0)
        rt2 = rtype_detail.groupby('return_type').agg(
            returns=('returns','sum'), spf=('spf','sum')
        ).reset_index().sort_values('spf', ascending=False)
        rt2['SPF (Lakh)'] = (rt2['spf']/100000).round(2)
        rt2['SPF (₹)'] = rt2['spf'].apply(lambda x: f"₹{x:,.2f}")
        st.dataframe(rt2, use_container_width=True)

st.caption(f"Flipkart SPF Dashboard 2026 · Data from GitHub · All amounts in ₹ INR · Jan: {total_returns:,} returns")
