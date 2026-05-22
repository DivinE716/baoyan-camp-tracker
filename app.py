import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="夏令营进度看板", layout="wide")
st.title("🎓 保研夏令营进度管理看板")
st.caption("基于 JSONBin 独立云端同步 · 适配微信/移动端")

# 1. 配置你的云端密钥（本地放 secrets.toml，云端部署时填在网页后台）
BIN_ID = st.secrets["jsonbin"]["bin_id"]
API_KEY = st.secrets["jsonbin"]["api_key"]

URL = f"https://api.jsonbin.io/v3/b/{BIN_ID}"
HEADERS = {
    "X-Master-Key": API_KEY,
    "Content-Type": "application/json"
}

# 2. 从云端读取数据
@st.cache_data(ttl="2s") # 缓存2秒，防止高频刷新，同时保证双端近乎实时
def load_cloud_data():
    try:
        # 获取最新记录
        res = requests.get(f"{URL}/latest", headers=HEADERS).json()
        # JSONBin 返回的结构中，实际数据在 'record' 字段里
        data = res.get("record", [])
        if not data:
            return pd.DataFrame(columns=["院校", "学院", "截止时间", "网址", "备注", "置顶"])
        df = pd.DataFrame(data)
        df["置顶"] = df["置顶"].astype(bool)
        return df
    except Exception as e:
        st.error(f"云端连接失败: {e}")
        return pd.DataFrame(columns=["院校", "学院", "截止时间", "网址", "备注", "置顶"])

# 3. 将数据保存回云端
def save_cloud_data(df):
    # 将 DataFrame 转换为字典列表
    data_dict = df.to_dict(orient="records")
    # 清除日期等无法序列化的对象，确保是纯文本
    for item in data_dict:
        item["截止时间"] = str(item["截止时间"])
    requests.put(URL, headers=HEADERS, json=data_dict)

df_current = load_cloud_data()

# 4. 侧边栏：录入信息
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
            st.success("🎉 同步成功！")
            st.rerun()

# 5. 主界面：卡片流动态渲染（对手机屏幕极度友好）
if df_current.empty:
    st.info("💡 云端暂无数据，请在侧边栏录入第一条夏令营信息。")
else:
    # 动态排序：置顶优先，截止时间越近越靠前
    df_current['sort_date'] = pd.to_datetime(df_current['截止时间'], errors='coerce')
    df_sorted = df_current.sort_values(by=["置顶", "sort_date"], ascending=[False, True]).reset_index(drop=True)
    
    for idx, row in df_sorted.iterrows():
        title = f"📌 【置顶】{row['院校']} - {row['学院']}" if row['置顶'] else f"🏫 {row['院校']} - {row['学院']}"
        
        with st.container(border=True):
            col_text, col_btn = st.columns([4, 1])
            with col_text:
                st.markdown(f"#### {title}")
                # 计算倒计时
                days_left = (pd.to_datetime(row['截止时间']).date() - datetime.today().date()).days
                status = f"🔴 已截止" if days_left < 0 else (f"🚨 仅剩 {days_left} 天" if days_left <= 3 else f"🟢 剩 {days_left} 天")
                
                st.markdown(f"**⏰ 截止:** `{row['截止时间']}` ({status})")
                if row['备注']: st.markdown(f"**📝 备注:** {row['备注']}")
                if row['网址']: st.markdown(f"**🌐 链接:** [{row['网址']}]({row['网址']})")
            
            with col_btn:
                st.write("") # 居中对齐
                pin_text = "📍 取消置顶" if row['置顶'] else "📌 设为置顶"
                if st.button(pin_text, key=f"pin_{idx}", use_container_width=True):
                    df_current.loc[df_current['院校'] == row['院校'], '置顶'] = not row['置顶']
                    save_cloud_data(df_current)
                    st.rerun()
                
                if st.button("🗑️ 删除", key=f"del_{idx}", use_container_width=True):
                    df_filtered = df_current[df_current['院校'] != row['院校']]
                    save_cloud_data(df_filtered)
                    st.rerun()