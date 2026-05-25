import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="夏令营进度看板", layout="wide")
st.title("🎓 27夏令营信息管理空间")
st.caption("基于个人独立服务器 (heqiwei.cn) 实时双端同步")

# 1. 从云端 Secrets 读取你博客的私有云凭证
URL = st.secrets["blog"]["url"]
TOKEN = st.secrets["blog"]["token"]

# 初始化“正在编辑的行号”状态
if "editing_idx" not in st.session_state:
    st.session_state.editing_idx = None

# 2. 从阿里云服务器读取数据
@st.cache_data(ttl="2s")
def load_cloud_data():
    try:
        response = requests.get(f"{URL}?token={TOKEN}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if not data:
                return pd.DataFrame(columns=["院校", "学院", "截止时间", "网址", "备注", "置顶"])
            df = pd.DataFrame(data)
            df["置顶"] = df["置顶"].astype(bool)
            return df
        else:
            st.error(f"❌ 独立服务器连接失败，状态码: {response.status_code}")
            return pd.DataFrame(columns=["院校", "学院", "截止时间", "网址", "备注", "置顶"])
    except Exception as e:
        st.error(f"📡 无法连接到 www.heqiwei.cn: {e}")
        return pd.DataFrame(columns=["院校", "学院", "截止时间", "网址", "备注", "置顶"])

# 3. 将数据保存回阿里云服务器
def save_cloud_data(df):
    df_to_save = df.drop(columns=['sort_date', 'orig_idx'], errors='ignore')
    data_dict = df_to_save.to_dict(orient="records")
    for item in data_dict:
        item["截止时间"] = str(item["截止时间"])
    try:
        res = requests.post(f"{URL}?token={TOKEN}", json=data_dict, timeout=10)
        if res.status_code == 200:
            st.toast("💾 数据已成功安全同步至阿里云服务器！", icon="☁️")
        else:
            st.error(f"❌ 同步失败，服务器返回: {res.status_code}")
    except Exception as e:
        st.error(f"💥 写入独立服务器时发生网络崩溃: {e}")

df_current = load_cloud_data()

# 4. 侧边栏：录入新信息
with st.sidebar:
    st.header("📝 录入新简章")
    with st.form("add_form", clear_on_submit=True):
        university = st.text_input("院校名称")
        school = st.text_input("学院名称")
        deadline = st.date_input("截止时间", value=datetime.today())
        url = st.text_input("简章网址")
        remarks = st.text_area("备注信息")
        is_pinned = st.checkbox("置顶该条目")
        
        if st.form_submit_button("一键同步到云端") and university:
            new_row = pd.DataFrame([{
                "院校": university, "学院": school, "截止时间": str(deadline),
                "网址": url, "备注": remarks, "置顶": is_pinned
            }])
            df_updated = pd.concat([df_current, new_row], ignore_index=True)
            save_cloud_data(df_updated)
            st.rerun()
            
    # 一键导出本地备份
    if not df_current.empty:
        st.divider()
        st.subheader("💾 本地安全双保险")
        csv_data = df_current.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 导出当前数据到本地 (CSV)",
            data=csv_data,
            file_name=f"夏令营数据备份_{datetime.today().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

# 5. 主界面：卡片流动态渲染
if df_current.empty:
    st.info("💡 云端暂无数据，请在侧边栏录入第一条夏令营信息。")
else:
    df_current['orig_idx'] = df_current.index
    df_current['sort_date'] = pd.to_datetime(df_current['截止时间'], errors='coerce')
    df_sorted = df_current.sort_values(by=["置顶", "sort_date"], ascending=[False, True]).reset_index(drop=True)
    
    for idx, row in df_sorted.iterrows():
        orig_index = row['orig_idx']
        
        # 状态 A：编辑模式
        if st.session_state.editing_idx == orig_index:
            with st.container(border=True):
                st.markdown(f"🛠️ **正在修改：{row['院校']} - {row['学院']}**")
                edit_uni = st.text_input("院校名称", value=row['院校'], key=f"uni_{idx}")
                edit_sch = st.text_input("学院名称", value=row['学院'], key=f"sch_{idx}")
                try:
                    default_date = pd.to_datetime(row['截止时间']).date()
                except:
                    default_date = datetime.today().date()
                edit_date = st.date_input("截止时间", value=default_date, key=f"date_{idx}")
                edit_url = st.text_input("简章网址", value=row['网址'], key=f"url_{idx}")
                edit_rem = st.text_area("备注信息", value=row['备注'], key=f"rem_{idx}")
                
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("💾 保存修改", key=f"save_{idx}", type="primary", use_container_width=True):
                        df_current.loc[orig_index, "院校"] = edit_uni
                        df_current.loc[orig_index, "学院"] = edit_sch
                        df_current.loc[orig_index, "截止时间"] = str(edit_date)
                        df_current.loc[orig_index, "网址"] = edit_url
                        df_current.loc[orig_index, "备注"] = edit_rem
                        save_cloud_data(df_current)
                        st.session_state.editing_idx = None
                        st.rerun()
                with btn_col2:
                    if st.button("❌ 取消", key=f"cancel_{idx}", use_container_width=True):
                        st.session_state.editing_idx = None
                        st.rerun()
                        
        # 状态 B：看板展示模式
        else:
            title = f"📌 【置顶】{row['院校']} - {row['学院']}" if row['置顶'] else f"🏫 {row['院校']} - {row['学院']}"
            with st.container(border=True):
                col_text, col_btn = st.columns([4, 1])
                with col_text:
                    st.markdown(f"#### {title}")
                    days_left = (pd.to_datetime(row['截止时间']).date() - datetime.today().date()).days
                    status = f"🔴 已截止" if days_left < 0 else (f"🚨 仅剩 {days_left} 天" if days_left <= 3 else f"🟢 剩 {days_left} 天")
                    st.markdown(f"**⏰ 截止:** `{row['截止时间']}` ({status})")
                    if row['备注']: st.markdown(f"**📝 备注:** {row['备注']}")
                    if row['网址']: st.markdown(f"**🌐 链接:** [{row['网址']}]({row['网址']})")
                
                with col_btn:
                    st.write("") 
                    pin_text = "📍 取消置顶" if row['置顶'] else "📌 设为置顶"
                    if st.button(pin_text, key=f"pin_{idx}", use_container_width=True):
                        df_current.loc[orig_index, '置顶'] = not row['置顶']
                        save_cloud_data(df_current)
                        st.rerun()
                    if st.button("📝 修改记录", key=f"edit_btn_{idx}", use_container_width=True):
                        st.session_state.editing_idx = orig_index
                        st.rerun()
                    if st.button("🗑️ 删除", key=f"del_{idx}", use_container_width=True):
                        df_filtered = df_current.drop(index=orig_index)
                        save_cloud_data(df_filtered)
                        st.rerun()