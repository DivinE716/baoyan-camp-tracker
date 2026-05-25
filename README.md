# 🎓 27夏令营信息管理空间 (Postgraduate Recommendation Summer Camp Organizer)

一个专为保研党（夏令营/预推免）设计的轻量级进度管理看板。前端基于 **Streamlit** 框架并部署于云端，后端数据彻底脱离不稳定的第三方平台依赖，采用**自有云服务器（PHP + JSON）**自主控权，实现手机、电脑双端公网实时高可用同步。

## ✨ 核心特性

- ⏳ **迫切度动态排序**：全自动根据截止日期倒计时排序，最紧急的申请始终置于最上方。
- 📍 **一键精确置顶**：支持对重点关注的院校/项目进行置顶（📌 标签高亮标识）。
- 📱 **移动端响应式适配**：完美的卡片流布局，支持在手机微信或浏览器中“添加到主屏幕”作为独立 Web App 使用。
- 🛠️ **全生命周期管理**：支持卡片内直接“修改记录”、“取消置顶”和“一键删除”，操作即时同步。
- 🔒 **100% 私有数据自主权**：数据通过自建私有 API 安全读写，存放在自己的服务器磁盘中，无网络频次限制，不依赖任何第三方云仓。
- 💾 **双保险本地导出**：侧边栏原生集成一键导出当前数据为本地 CSV 格式（Excel 可直接打开），保障数据多备份。

## 🛠️ 技术栈

- **Frontend & UI**: Streamlit (Python)
- **Data Process**: Pandas (Dataframe 矩阵操作与绝对索引匹配)
- **Backend & DB**: PHP + Native JSON Storage (Hosted on personal Alibaba Cloud Server)
- **Deployment**: Streamlit Community Cloud + GitHub

## 📂 仓库目录结构 (GitHub)

```text
POSTGRADUATE RECOMMENDATION SUMMER CAMP INFORMATION ORGANIZER/
│
├── .streamlit/
│   └── secrets.toml       # 独立服务器 API 凭证及 Token（已加入 .gitignore，安全隔离）
│
├── app.py                 # Streamlit 主程序核心代码
├── requirements.txt       # 云端服务器依赖环境声明
└── .gitignore             # Git 忽略配置文件
```

## 🚀 本地快速开始

### 1. 克隆项目
```bash
git clone [https://github.com/你的用户名/你的仓库名.git](https://github.com/你的用户名/你的仓库名.git)
cd "Postgraduate Recommendation Summer Camp Information Organizer"
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置凭证
在 `.streamlit/secrets.toml` 中填入你的自有服务器接口配置：
```toml
[blog]
url = "[https://www.heqiwei.cn/camp_api.php](https://www.heqiwei.cn/camp_api.php)"
token = "YOUR_EXCLUSIVE_TOKEN"
```

### 4. 本地运行
```bash
streamlit run app.py
```

## ☁️ 服务端与云端部署指南

### 1. 服务器后端部署 (宝塔面板/阿里云)
1. 在你的网站根目录下新建 `camp_api.php`。
2. 写入自建的 PHP 接口代码（包含请求劫持验证与安全 Token 校验）。
3. 确保该目录拥有读写权限，当前端首次发起写入后，会自动在同级目录下生成私有数据库 `camp_data.json`。

### 2. 前端部署 (Streamlit Cloud)
1. 将本地代码推送至你的 GitHub 仓库（由于有 `.gitignore`，本地的 `secrets.toml` 不会被上传）。
2. 登录 [Streamlit Community Cloud](https://share.streamlit.io/) 绑定该仓库。
3. **关键步骤**：点击右下角 **Advanced settings...**，在 **Secrets** 文本框中将本地 `secrets.toml` 中的 `[blog]` 凭证完整粘贴进去，点击 Save。
4. 点击 **Deploy!** 即可生成公网专属网址。

## 📱 移动端最佳实践

- **iOS (Safari)**：使用 Safari 打开部署好的网址 -> 点击分享按钮 -> 选择 **“添加到主屏幕”**。
- **Android**：在手机浏览器或微信打开网址 -> 点击右上角 `...` -> 选择 **“添加到桌面”**。
- **高频技巧**：在手机微信端将其设为**「浮窗」**，刷到各大高校保研公众号通知时，一键切入录入，随时随地掌握进度。

## 📄 License

Project is personal-use oriented and distributed under the MIT License.