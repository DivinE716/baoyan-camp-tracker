# 🎓 Postgraduate Recommendation Summer Camp Information Organizer (保研夏令营/预推免进度动态看板)

一个专为保研党（夏令营/预推免）设计的轻量级进度管理看板。基于 **Streamlit** 前端框架与 **JSONBin.io** 云端存储，实现手机、电脑双端实时同步，并支持根据截止时间的紧迫程度自动进行动态重排序与条目置顶。

## ✨ 核心特性

- ⏳ **迫切度动态排序**：全自动根据截止日期倒计时排序，最紧急的申请始终置于最上方。
- 📍 **一键精确置顶**：支持对重点关注的院校/重点项目进行置顶（📌 标签高亮标识）。
- 📱 **移动端响应式适配**：完美的卡片流布局，在手机微信或浏览器中打开时自动适配屏幕，支持“添加到主屏幕”作为独立 Web App 使用。
- 🛠️ **全生命周期管理**：支持卡片内直接“修改记录”、“取消置顶”和“一键删除”，操作即时同步云端。
- ☁️ **独立轻量云同步**：放弃传统大厂繁琐的 API 鉴权，采用极简 JSON 仓库作为后端，零成本、零延迟、永久免费。

## 🛠️ 技术栈

- **Frontend & UI**: Streamlit (Python)
- **Data Process**: Pandas (Dataframe 矩阵操作与绝对索引匹配)
- **Backend & DB**: JSONBin.io (Cloud JSON Storage API)
- **Deployment**: Streamlit Community Cloud + GitHub

## 📂 目录结构

```text
POSTGRADUATE RECOMMENDATION SUMMER CAMP INFORMATION ORGANIZER/
│
├── .streamlit/
│   └── secrets.toml       # 本地云端密钥配置文件（已加入 .gitignore）
│
├── app.py                 # Streamlit 主程序核心代码
├── requirements.txt       # 云端服务器依赖环境声明
└── .gitignore             # Git 忽略配置文件（防止凭证泄露）
```

## 🚀 本地快速开始

### 1. 克隆并进入项目
```bash
git clone [https://github.com/你的用户名/你的仓库名.git](https://github.com/你的用户名/你的仓库名.git)
cd Postgraduate-Recommendation-Summer-Camp-Information-Organizer
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置本地密钥
在 `.streamlit/secrets.toml` 中填入你的 JSONBin 凭证：
```toml
[jsonbin]
bin_id = "YOUR_JSONBIN_BIN_ID"
api_key = "YOUR_JSONBIN_X_MASTER_KEY"
```

### 4. 本地运行
```bash
streamlit run app.py
```

## ☁️ 云端部署指南 (Streamlit Cloud)

1. 将代码推送至你的 GitHub 私有仓库（由于有 `.gitignore`，本地的 `secrets.toml` 不会被上传）。
2. 登录 [Streamlit Community Cloud](https://share.streamlit.io/)，点击 **New App**。
3. 选择对应的仓库、分支（`main`）以及主文件（`app.py`）。
4. **关键步骤**：点击右下角 **Advanced settings...**，在 **Secrets** 文本框中将你的 `secrets.toml` 内容完整粘贴进去，点击 Save。
5. 点击 **Deploy!** 即可生成公网可访问的专属网址。

## 📱 移动端最佳实践

- **iOS (Safari)**：使用 Safari 打开部署好的网址 -> 点击分享按钮 -> 选择 **“添加到主屏幕”**。
- **Android**：在手机浏览器或微信打开网址 -> 点击右上角 `...` -> 选择 **“添加到桌面”**。
- 体验升级：可将其作为微信**「浮窗」**挂在后台，刷到保研公众号通知时，一键切入录入。

## 📄 License

Project is personal-use oriented and distributed under the MIT License.