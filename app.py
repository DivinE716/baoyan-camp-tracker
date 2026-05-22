import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="夏令营进度看板", layout="wide")
st.title("🎓 27夏令营信息管理空间")
st.caption("基于 JSONBin 独立云端同步 · 支持卡片流内嵌修改")

# 1. 配置你的云端密钥
BIN_ID = st.secrets["jsonbin"]["bin_id"]
API_KEY = st.secrets["jsonbin"]["api_key"]

URL = f"https://api.jsonbin.io/v3/b/{BIN_ID}"
HEADERS = {
    "X-Master-Key": API_KEY,
    "Content-Type": "application/json"
}

# 初始化“正在编辑的行号”状态，None 表示当前没有在编辑任何内容
if "editing_idx" not in st.session_state:
    st.session_state.editing_idx = None

# 2. 从云端读取数据
@st.cache_data(ttl="2s")
def load_cloud_data():
    try:
        res = requests.get(f"{URL}/latest", headers=HEADERS).json()
        data = res.get("record", [])
        if not data:
            return pd.DataFrame(columns=["院校", "学院", "截止时间", "网址", "备注", "置顶"])
        df = pd.DataFrame(data)
        df["置顶"] = df["置顶"].astype(bool)
        return df
    except Exception as e:
        st.error(f"云端连接失败: {e}")
        return pd.DataFrame(columns=["院校", "学院", "截止时间", "网址", "备注", "置顶"])

# 3. 将数据保存回云端（自动过滤掉排序辅助列）
def save_cloud_data(df):
    # 剔除 Python 内部排序和定位用的辅助列，只保留纯净数据进云端
    df_to_save = df.drop(columns=['sort_date', 'orig_idx'], errors='ignore')
    data_dict = df_to_save.to_dict(orient="records")
    for item in data_dict:
        item["截止时间"] = str(item["截止时间"])
    requests.put(URL, headers=HEADERS, json=data_dict)

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
            st.success("🎉 同步成功！")
            st.rerun()

# 5. 主界面：卡片流动态渲染
if df_current.empty:
    st.info("💡 云端暂无数据，请在侧边栏录入第一条夏令营信息。")
else:
    # 核心：在排序前，把 DataFrame 原本的真实行索引（行号）记下来
    df_current['orig_idx'] = df_current.index
    df_current['sort_date'] = pd.to_datetime(df_current['截止时间'], errors='coerce')
    
    # 动态排序：置顶优先，截止时间越近越靠前
    df_sorted = df_current.sort_values(by=["置顶", "sort_date"], ascending=[False, True]).reset_index(drop=True)
    
    for idx, row in df_sorted.iterrows():
        orig_index = row['orig_idx']  # 拿到这条数据在原始未排序数组里的绝对位置
        
        # ---------------- 状态 A：当前行处于【编辑模式】 ----------------
        if st.session_state.editing_idx == orig_index:
            with st.container(border=True):
                st.markdown(f"🛠️ **正在修改：{row['院校']} - {row['学院']}**")
                
                # 渲染表单输入项，并预填入原本的旧数据
                edit_uni = st.text_input("院校名称", value=row['院校'], key=f"uni_{idx}")
                edit_sch = st.text_input("学院名称", value=row['学院'], key=f"sch_{idx}")
                
                # 防止旧数据时间格式解析失败的鲁棒处理
                try:
                    default_date = pd.to_datetime(row['截止时间']).date()
                except:
                    default_date = datetime.today().date()
                edit_date = st.date_input("截止时间", value=default_date, key=f"date_{idx}")
                
                edit_url = st.text_input("简章网址", value=row['网址'], key=f"url_{idx}")
                edit_rem = st.text_area("备注信息", value=row['备注'], key=f"rem_{idx}")
                
                # 提交与取消按钮
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("💾 保存修改", key=f"save_{idx}", type="primary", use_container_width=True):
                        # 精确覆盖原始位置的数据
                        df_current.loc[orig_index, "院校"] = edit_uni
                        df_current.loc[orig_index, "学院"] = edit_sch
                        df_current.loc[orig_index, "截止时间"] = str(edit_date)
                        df_current.loc[orig_index, "网址"] = edit_url
                        df_current.loc[orig_index, "备注"] = edit_rem
                        
                        save_cloud_data(df_current)
                        st.session_state.editing_idx = None  # 退出编辑模式
                        st.success("修改已同步！")
                        st.rerun()
                with btn_col2:
                    if st.button("❌ 取消", key=f"cancel_{idx}", use_container_width=True):
                        st.session_state.editing_idx = None  # 直接退出编辑模式
                        st.rerun()
                        
        # ---------------- 状态 B：当前行处于【正常看板展示模式】 ----------------
        else:
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
                    st.write("") # 垂直居中对齐占位
                    
                    # 1. 置顶/取消置顶
                    pin_text = "📍 取消置顶" if row['置顶'] else "📌 设为置顶"
                    if st.button(pin_text, key=f"pin_{idx}", use_container_width=True):
                        df_current.loc[orig_index, '置顶'] = not row['置顶']
                        save_cloud_data(df_current)
                        st.rerun()
                    
                    # 2. 触发编辑模式
                    if st.button("📝 修改记录", key=f"edit_btn_{idx}", use_container_width=True):
                        st.session_state.editing_idx = orig_index  # 标记当前行进入编辑状态
                        st.rerun()
                    
                    # 3. 删除记录（精确行切片删除）
                    if st.button("🗑️ 删除", key=f"del_{idx}", use_container_width=True):
                        df_filtered = df_current.drop(index=orig_index)
                        save_cloud_data(df_filtered)
                        st.rerun()