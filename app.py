import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="SPF Dashboard", page_icon="📦", layout="wide")

st.title("📦 Flipkart SPF Dashboard 2026")

st.sidebar.header("📁 Data Upload")
files = st.sidebar.file_uploader("CSV files upload karo", type="csv", accept_multiple_files=True)

if not files:
    st.info("👈 Sidebar mein CSV files upload karo")
    st.stop()

dfs = []
month_names = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']

for f in files:
    try:
        df = pd.read_csv(f, low_memory=False)
        month = 'UNK'
        for m in month_names:
            if m in f.name.upper():
                month = m
                break
        df['_month'] = month
        dfs.append(df)
        st.sidebar.success(f"✅ {f.name} — {len(df):,} rows")
    except Exception as e:
        st.sidebar.error(f"❌ {f.name}: {e}")

if not dfs:
    st.error("Koi file load nahi hui!")
    st.stop()

data = pd.concat(dfs, ignore_index=True)
st.sidebar.markdown(f"**Total: {len(data):,} rows**")

# Find columns
def fc(df, opts):
    for o in opts:
        if o in df.columns: return o
        for c in df.columns:
            if c.lower()==o.lower(): return c
    return None

claim = fc(data, ['approved_claim_amount','claim_amount'])
qa    = fc(data, ['QA','qa'])
ph    = fc(data, ['PH','ph'])
loss  = fc(data, ['loss_bucket'])
week  = fc(data, ['week_num_in_year','week'])
asp   = fc(data, ['ASP_buck','ASP'])
scat  = fc(data, ['analytic_super_category'])
city  = fc(data, ['seller_city'])
rtype = fc(data, ['return_type'])
seller= fc(data, ['seller_id'])
obd   = fc(data, ['seller_obd_status'])
reason= fc(data, ['reason'])

# Numeric
for c in [claim, asp]:
    if c: data[c] = pd.to_numeric(data[c], errors='coerce').fillna(0)

# Sidebar filters
st.sidebar.markdown("---")
months = sorted(data['_month'].unique().tolist())
sel_m = st.sidebar.multiselect("📅 Month", months, default=months)
df = data[data['_month'].isin(sel_m)] if sel_m else data.copy()

if qa:
    qa_opts = ['All'] + sorted(df[qa].dropna().astype(str).unique().tolist())
    s_qa = st.sidebar.selectbox("👤 QA", qa_opts)
    if s_qa != 'All': df = df[df[qa].astype(str)==s_qa]

if loss:
    l_opts = ['All'] + sorted(df[loss].dropna().astype(str).unique().tolist())
    s_l = st.sidebar.selectbox("📊 Loss Bucket", l_opts)
    if s_l != 'All': df = df[df[loss].astype(str)==s_l]

if week:
    w_opts = ['All'] + sorted(df[week].dropna().astype(str).unique().tolist())
    s_w = st.sidebar.selectbox("📆 Week", w_opts)
    if s_w != 'All': df = df[df[week].astype(str)==s_w]

st.sidebar.markdown(f"**Filtered: {len(df):,} rows**")

# KPIs
tot = len(df)
spf = df[claim].sum() if claim else 0
avg = df[asp].mean() if asp else 0
cr  = spf/10000000

c1,c2,c3,c4 = st.columns(4)
c1.metric("📦 Returns", f"{tot:,}")
c2.metric("💰 SPF (Lakh)", f"₹{spf/100000:.2f}L")
c3.metric("📈 SPF (Cr)", f"{cr:.4f} Cr")
c4.metric("🏷️ Avg ASP", f"₹{avg:,.0f}")

st.markdown("---")
tab1,tab2,tab3,tab4 = st.tabs(["📊 Charts","👤 QA","🗺️ Hub","📋 Table"])

with tab1:
    c1,c2 = st.columns(2)
    with c1:
        st.subheader("Monthly SPF")
        if claim:
            mg = data[data['_month'].isin(sel_m)].groupby('_month')[claim].sum().reset_index()
            mg.columns=['Month','SPF']
            mg['SPF_L']=mg['SPF']/100000
            fig=px.bar(mg,x='Month',y='SPF_L',text=mg['SPF_L'].apply(lambda x:f'₹{x:.1f}L'),color='SPF_L',color_continuous_scale='Oranges')
            fig.update_traces(textposition='outside')
            fig.update_layout(showlegend=False,coloraxis_showscale=False,plot_bgcolor='white',height=300,yaxis_title='SPF (₹L)')
            st.plotly_chart(fig,use_container_width=True)

    with c2:
        st.subheader("Weekly SPF")
        if week and claim:
            wg=df.groupby(week)[claim].sum().reset_index()
            wg.columns=['Week','SPF']
            wg=wg.sort_values('Week')
            wg['SPF_L']=wg['SPF']/100000
            fig2=px.line(wg,x='Week',y='SPF_L',markers=True,color_discrete_sequence=['#3b82f6'])
            fig2.update_layout(plot_bgcolor='white',height=300,yaxis_title='SPF (₹L)')
            st.plotly_chart(fig2,use_container_width=True)

    c3,c4=st.columns(2)
    with c3:
        st.subheader("Loss Bucket SPF")
        if loss and claim:
            lg=df.groupby(loss)[claim].sum().reset_index()
            lg.columns=['Loss','SPF']
            lg=lg.sort_values('SPF',ascending=False)
            lg['SPF_L']=lg['SPF']/100000
            fig3=px.bar(lg,x='Loss',y='SPF_L',text=lg['SPF_L'].apply(lambda x:f'₹{x:.2f}L'),color='SPF_L',color_continuous_scale='Reds')
            fig3.update_traces(textposition='outside')
            fig3.update_layout(showlegend=False,coloraxis_showscale=False,plot_bgcolor='white',height=300)
            st.plotly_chart(fig3,use_container_width=True)

    with c4:
        st.subheader("Top Categories")
        if scat:
            cg=df.groupby(scat).size().reset_index()
            cg.columns=['Cat','Count']
            cg=cg.sort_values('Count',ascending=True).tail(10)
            fig4=px.bar(cg,x='Count',y='Cat',orientation='h',text='Count',color='Count',color_continuous_scale='Blues')
            fig4.update_traces(textposition='inside')
            fig4.update_layout(showlegend=False,coloraxis_showscale=False,plot_bgcolor='white',height=300)
            st.plotly_chart(fig4,use_container_width=True)

with tab2:
    st.subheader("👤 QA Performance")
    if qa and claim:
        qg=df.groupby(qa).agg(Returns=(claim,'count'),SPF=(claim,'sum')).reset_index()
        qg.columns=['QA Name','Returns','SPF (₹)']
        qg['SPF (L)']=( qg['SPF (₹)']/100000).round(2)
        qg['SPF (Cr)']=(qg['SPF (₹)']/10000000).round(6)
        qg=qg.sort_values('SPF (₹)',ascending=False)
        c1,c2=st.columns(2)
        c1.metric("QA Agents",len(qg))
        c2.metric("Total SPF",f"₹{qg['SPF (₹)'].sum()/100000:.2f}L")
        fq=px.bar(qg.head(20),x='QA Name',y='SPF (L)',text=qg.head(20)['SPF (L)'].apply(lambda x:f'₹{x:.1f}L'),color='SPF (L)',color_continuous_scale='Oranges')
        fq.update_traces(textposition='outside')
        fq.update_layout(showlegend=False,coloraxis_showscale=False,plot_bgcolor='white',height=400)
        st.plotly_chart(fq,use_container_width=True)
        d=qg.copy()
        d['SPF (₹)']=d['SPF (₹)'].apply(lambda x:f"₹{x:,.2f}")
        st.dataframe(d,use_container_width=True,height=400)
    else:
        st.warning("QA column nahi mila!")

with tab3:
    st.subheader("🗺️ Hub Analysis")
    if ph and claim:
        if qa:
            qa_h=['All QA']+sorted(df[qa].dropna().astype(str).unique().tolist())
            s_qh=st.selectbox("QA select:",qa_h)
            hdf=df[df[qa].astype(str)==s_qh] if s_qh!='All QA' else df.copy()
        else:
            hdf=df.copy()
        vb=st.radio("View by:",["Hub(PH)","Loss Bucket","Seller"],horizontal=True)
        gc={" Hub(PH)":ph,"Loss Bucket":loss,"Seller":seller}.get(vb,ph)
        if not gc: gc=ph
        hg=hdf.groupby(gc).agg(Returns=(claim,'count'),SPF=(claim,'sum')).reset_index()
        hg.columns=[vb,'Returns','SPF (₹)']
        hg['SPF (L)']=(hg['SPF (₹)']/100000).round(2)
        hg=hg.sort_values('SPF (₹)',ascending=False)
        fh=px.bar(hg.head(15),x=vb,y='SPF (L)',text=hg.head(15)['SPF (L)'].apply(lambda x:f'₹{x:.2f}L'),color='SPF (L)',color_continuous_scale='Blues')
        fh.update_traces(textposition='outside')
        fh.update_layout(showlegend=False,coloraxis_showscale=False,plot_bgcolor='white',height=400)
        st.plotly_chart(fh,use_container_width=True)
        d2=hg.copy()
        d2['SPF (₹)']=d2['SPF (₹)'].apply(lambda x:f"₹{x:,.2f}")
        st.dataframe(d2,use_container_width=True,height=350)

with tab4:
    st.subheader("📋 Data Table")
    fc1,fc2,fc3=st.columns(3)
    tdf=df.copy()
    with fc1:
        if city:
            cv=['All']+sorted(tdf[city].dropna().astype(str).unique().tolist())
            sc=st.selectbox("City",cv)
            if sc!='All': tdf=tdf[tdf[city].astype(str)==sc]
    with fc2:
        if seller:
            ss=st.text_input("Seller ID")
            if ss: tdf=tdf[tdf[seller].astype(str).str.contains(ss,case=False,na=False)]
    with fc3:
        sa=st.text_input("🔍 Search")
        if sa:
            mask=tdf.astype(str).apply(lambda x:x.str.contains(sa,case=False,na=False)).any(axis=1)
            tdf=tdf[mask]

    ts=tdf[claim].sum() if claim else 0
    st.markdown(f"**{len(tdf):,} rows** | SPF: **₹{ts/100000:.2f}L** ({ts/10000000:.4f} Cr)")

    show=[]
    for c in ['_month',claim,qa,ph,loss,scat,city,reason,rtype,asp,obd,week]:
        if c and c in tdf.columns: show.append(c)

    st.dataframe(tdf[show].head(5000),use_container_width=True,height=500)
    st.download_button("⬇️ Download CSV",tdf.to_csv(index=False).encode('utf-8'),"spf_filtered.csv","text/csv")

st.caption(f"Flipkart SPF 2026 · {len(data):,} rows · ₹ INR")
