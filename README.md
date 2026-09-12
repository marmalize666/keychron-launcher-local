# Keychron Launcher 本地离线版

从官方 `https://launcher.keychron.cn/` 完整下载并离线化的 Keychron 键盘配置 Web 应用（Angular SPA），配合一个纯 Python 标准库本地服务器运行，**断网也能用**。

## 特性

- 完整离线：官方 Angular SPA 全量资源（JS chunk / 素材 / 字体 / 语言包）本地化
- WebHID 可用：`127.0.0.1` 属 secure context，浏览器直连键盘功能正常
- 本地 API 应答层：`/apiproxy/` 接管官方 vapi 接口（layouts / version / product）
  - 产品数据缺失时自动回源官方 CDN 拉取并落盘固化，下次完全离线
- 布局数据清洗：官方接口混入的 SQL 注入测试垃圾数据（如 `gwzgftqb`）已剔除，保留 15 条有效键盘布局
- URL 重写注入层：拦截 XHR / fetch / 图片三处请求，把官方域名改写到本地，零外网流量
- Demo 模式打通：无键盘也能浏览键位 / 磁轴页

## 使用方法

双击 `Start-Keychron-Launcher.bat`（自动找 Python、检测端口、后台起服务并开浏览器），或手动：

```bash
python server.py            # 默认 127.0.0.1:1984
python server.py --port=3000
```

浏览器访问 `http://127.0.0.1:1984/`。

## 依赖

- Python 3.8+（纯标准库，无第三方依赖）
- Chromium 内核浏览器（WebHID 连接真机需要；Chrome / Edge 均可）

## 目录结构

```
├── server.py                     # 本地服务器（静态服务 + apiproxy + 注入 + 回源缓存）
├── Start-Keychron-Launcher.bat   # 双击启动脚本
├── index.html                    # 官方入口（已注入 URL 重写层、移除 GA）
├── api_cache/                    # 固化的 vapi 接口数据（layouts / version / product）
├── static/
│   ├── layouts/                  # keycode-{布局}-{win|mac}.json 键位码表
│   ├── i18n/                     # 25 个语言包
│   └── device/                   # 设备 JSON（按需缓存）
├── assets/                       # 图标、字体、键帽素材
└── main.*.js / *.css             # Angular 应用本体
```

## 说明

- 本仓库仅含 Keychron 官方公开分发的前端资源与个人写的本地服务器胶水代码，仅供个人离线使用，版权归 Keychron 所有，请勿商用。
- 新键盘型号首次连接时会自动回源官方拉取产品描述并缓存，之后该型号也完全离线可用。
