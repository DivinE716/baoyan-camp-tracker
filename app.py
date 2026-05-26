import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="27夏令营信息管理空间", layout="wide")
st.title("🎓 27夏令营信息管理空间")
st.caption("基于heqiwei.cn部署")

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
                return pd.DataFrame(columns=["院校", "学院", "截止时间", "网址", "备注", "置顶", "已处理"])
            df = pd.DataFrame(data)
            
            # 【向下兼容】如果老数据中没有“已处理”字段，自动初始化为 False
            if "已处理" not in df.columns: 
                df["已处理"] = False
            
            # 严格规整数据类型
            df["置顶"] = df["置顶"].astype(bool)
            df["已处理"] = df["已处理"].astype(bool)
            return df
        else:
            st.error(f"❌ 独立服务器连接失败，状态码: {response.status_code}")
            return pd.DataFrame(columns=["院校", "学院", "截止时间", "网址", "备注", "置顶", "已处理"])
    except Exception as e:
        st.error(f"📡 无法连接到 www.heqiwei.cn: {e}")
        return pd.DataFrame(columns=["院校", "学院", "截止时间", "网址", "备注", "置顶", "已处理"])

# 3. 将数据保存回阿里云服务器
def save_cloud_data(df):
    df_to_save = df.drop(columns=['sort_date', 'orig_idx'], errors='ignore')
    data_dict = df_to_save.to_dict(orient="records")
    for item in data_dict:
        item["截止时间"] = str(item["截止时间"])
        item["置顶"] = bool(item["置顶"])
        item["已处理"] = bool(item["已处理"])
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
                "网址": url, "备注": remarks, "置顶": is_pinned, "已处理": False
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

# 5. 主界面：双列卡片流渲染
if df_current.empty:
    st.info("💡 云端暂无数据，请在侧边栏录入第一条夏令营信息。")
else:
    # 建立绝对索引，防止排序后定位错乱
    df_current['orig_idx'] = df_current.index
    df_current['sort_date'] = pd.to_datetime(df_current['截止时间'], errors='coerce')
    
    # 【核心排序逻辑】
    # 1. 已处理(True)排在未处理(False)后面 -> 已处理升序 (False -> True)
    # 2. 未处理内部，置顶(True)排在未置顶(False)前面 -> 置顶降序 (True -> False)
    # 3. 同等条件下，截止时间越近越靠前 -> 时间升序
    df_sorted = df_current.sort_values(
        by=["已处理", "置顶", "sort_date"], 
        ascending=[True, False, True]
    ).reset_index(drop=True)
    
    # 联动看板统计
    total_active = len(df_sorted[df_sorted['已处理'] == False])
    st.markdown(f"📊 待处理有效申请：`{total_active}` 条 | 总计：`{len(df_sorted)}` 条")
    
    # 【核心布局：默认双列排列】
    # 步长为2，每次循环渲染一行（包含左右两个独立卡片）
    for i in range(0, len(df_sorted), 2):
        cols = st.columns(2)
        
        for j in range(2):
            if i + j < len(df_sorted):
                row = df_sorted.iloc[i + j]
                orig_index = row['orig_idx']
                idx = i + j  # 针对组件生成唯一 key
                
                # 计算时间状态
                days_left = (pd.to_datetime(row['截止时间']).date() - datetime.today().date()).days
                is_expired = days_left < 0
                is_processed = row['已处理']
                
                # 【不醒目处理判断】只要“超过截止日期”或“已处理”，均触发灰色不醒目状态
                is_dimmed = is_expired or is_processed
                
                with cols[j]:
                    # ---------------- 状态 A：编辑模式 ----------------
                    if st.session_state.editing_idx == orig_index:
                        with st.container(border=True):
                            st.markdown(f"🛠️ **修改记录：{row['院校']}**")
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
                                if st.button("💾 保存", key=f"save_{idx}", type="primary", use_container_width=True):
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
                                    
                    # ---------------- 状态 B：看板展示模式 ----------------
                    else:
                        # 生成标题文本
                        base_title = f"{row['院校']} - {row['学院']}"
                        if is_processed:
                            title_text = f"✅ [已处理] {base_title}"
                        elif is_expired:
                            title_text = f"⏳ [已截止] {base_title}"
                        elif row['置顶']:
                            title_text = f"📌 [置顶] {base_title}"
                        else:
                            title_text = f"🏫 {base_title}"
                        
                        # 生成状态标签
                        if is_processed:
                            status_str = "⚪ 流程已完结"
                        elif is_expired:
                            status_str = f"🪦 已截止 ({abs(days_left)}天前)"
                        elif days_left == 0:
                            status_str = "🟠 今天截止！"
                        elif days_left <= 3:
                            status_str = f"🚨 仅剩 {days_left} 天 (极度紧迫)"
                        else:
                            status_str = f"🟢 剩 {days_left} 天截止"
                        
                        # 渲染容器
                        with st.container(border=True):
                            # 【不醒目核心实现】：通过 Markdown 的 :gray[] 语法和 ~~删除线~~ 降低视觉权重
                            if is_dimmed:
                                st.markdown(f"#### ~~:gray[{title_text}]~~")
                                st.markdown(f"**⏰ 截止:** `:gray[{row['截止时间']}]` &nbsp;&nbsp; **⏳ 状态:** :gray[{status_str}]")
                                if row['备注']: 
                                    st.markdown(f"**📝 备注:** :gray[{row['备注']}]")
                                if row['网址']: 
                                    st.markdown(f"**🌐 链接:** [:gray[点击跳转]]({row['网址']})")
                            else:
                                st.markdown(f"#### {title_text}")
                                st.markdown(f"**⏰ 截止:** `{row['截止时间']}` &nbsp;&nbsp; **⏳ 状态:** {status_str}")
                                if row['备注']: 
                                    st.markdown(f"**📝 备注:** {row['备注']}")
                                if row['网址']: 
                                    st.markdown(f"**🌐 链接:** [点击跳转]({row['网址']})")
                            
                            st.write("") # 留白空行规整视效
                            
                            # 卡片内部的功能按钮矩阵（紧凑的2x2网格，完美适配双列布局）
                            act_col1, act_col2 = st.columns(2)
                            with act_col1:
                                # 1. 置顶按钮：若已处理，则禁用置顶，节省精力
                                pin_label = "📍 取消置顶" if row['置顶'] else "📌 设为置顶"
                                if st.button(pin_label, key=f"pin_{idx}", use_container_width=True, disabled=is_processed):
                                    df_current.loc[orig_index, '置顶'] = not row['置顶']
                                    save_cloud_data(df_current)
                                    st.rerun()
                                    
                                # 2. 修改记录
                                if st.button("📝 修改记录", key=f"edit_btn_{idx}", use_container_width=True):
                                    st.session_state.editing_idx = orig_index
                                    st.rerun()
                                    
                            with act_col2:
                                # 3. 已处理 / 未处理 切换按钮（核心控制）
                                process_label = "↩️ 设为未办" if is_processed else "✅ 标为已办"
                                # 未办时高亮按钮(primary)，已办时变为弱化按钮(secondary)
                                if st.button(process_label, key=f"prc_{idx}", use_container_width=True, type="primary" if not is_processed else "secondary"):
                                    df_current.loc[orig_index, '已处理'] = not is_processed
                                    # 【人性化联动】：当标为已处理时，自动取消置顶，符合正常流程习惯
                                    if df_current.loc[orig_index, '已处理']:
                                        df_current.loc[orig_index, '置顶'] = False
                                    save_cloud_data(df_current)
                                    st.rerun()
                                    
                                # 4. 删除
                                if st.button("🗑️ 删除", key=f"del_{idx}", use_container_width=True):
                                    df_filtered = df_current.drop(index=orig_index)
                                    save_cloud_data(df_filtered)
                                    st.rerun()