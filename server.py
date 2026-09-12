#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Keychron Launcher 本地版服务器
- 服务本地静态文件（Angular SPA 完整离线拷贝）
- 动态资源按需回源官方 CDN 并缓存到本地 static/ 目录：
    /static/i18n/{lang}.json           语言包
    /static/layouts/{name}.json        键位布局
    /static/device/{vpid}/json/*.json  设备键位配置（连接键盘后按 vpid 拉取）
    /static/upload/*                   设备图片等
- 其余未知 /static/ 路径同样先查缓存、后回源
- 移除了 Google Analytics 依赖（index.html 已清理）
"""
import os
import sys
import json
import mimetypes
import urllib.request
import urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(ROOT, 'app')        # Angular SPA 文档根
STATIC = os.path.join(ROOT, 'static')

UPSTREAMS = [
    'https://launcher.keychron.cn/static/',
    'https://launcher.keychron.com/static/',
]
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) KeychronLauncherLocal/1.0'}

# ---------------------------------------------------------------------------
# vapi 接口本地应答层
# 官方 SPA 的 newAPI 硬编码指向官方域名，页面里的 v2/layouts（Layout语言下拉的
# 数据源）与 v2/version 请求不会经过本地服务器。这里生成一段注入脚本，前置拦截
# fetch/XHR，用本地 api_cache/ 的固化数据应答，遥测上报直接置空。
# ---------------------------------------------------------------------------
API_CACHE_DIR = os.path.join(ROOT, 'api_cache')

INJECT_TEMPLATE = """<script>
(function () {
  'use strict';
  var LOCAL_MAP = {
    'https://launcher.keychron.cn/vapi/': '/apiproxy/',
    'https://launcher.keychron.com/vapi/': '/apiproxy/',
    'https://erpapik.keychron.cn/': '/apiproxy/telemetry/',
    'https://launcher.keychron.cn/static/': '/static/',
    'https://launcher.keychron.com/static/': '/static/'
  };
  function rewrite(url) {
    if (typeof url !== 'string') return url;
    for (var from in LOCAL_MAP) {
      if (url.indexOf(from) === 0) return LOCAL_MAP[from] + url.slice(from.length);
    }
    return url;
  }
  var origOpen = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function (m, u) {
    arguments[1] = rewrite(u);
    return origOpen.apply(this, arguments);
  };
  var origFetch = window.fetch;
  window.fetch = function (input, init) {
    try {
      if (typeof input === 'string') {
        input = rewrite(input);
      } else if (input && input.url) {
        input = new Request(rewrite(input.url), input);
      }
    } catch (e) {}
    return origFetch.call(this, input, init);
  };
  // 图片等元素资源: 拦截 error 前重写不现实, 但 img.src 赋值可拦截
  var origSetAttr = Element.prototype.setAttribute;
  Element.prototype.setAttribute = function (name, value) {
    try {
      if (this.tagName === 'IMG' && typeof value === 'string') {
        value = rewrite(value);
      }
    } catch (e) {}
    return origSetAttr.apply(this, arguments);
  };
})();
</script>"""


def _load_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return '{}'


def build_inject():
    return INJECT_TEMPLATE


def upstream_fetch(rel_path):
    """依次尝试官方 CDN 回源，返回 bytes 或 None"""
    for base in UPSTREAMS:
        try:
            req = urllib.request.Request(base + rel_path, headers=UA)
            data = urllib.request.urlopen(req, timeout=25).read()
            if data:
                return data
        except Exception:
            continue
    return None


class LauncherHandler(SimpleHTTPRequestHandler):
    # 不打访问日志，保持控制台干净
    def log_message(self, fmt, *args):
        pass

    def translate_path(self, path):
        # 去掉 query string
        path = path.split('?', 1)[0].split('#', 1)[0]
        # SPA 根路径
        if path in ('/', ''):
            return os.path.join(APP, 'index.html')
        # 去掉开头斜杠，映射到 APP (SPA 文档根)
        rel = path.lstrip('/')
        return os.path.join(APP, rel.replace('/', os.sep))

    def end_headers(self):
        # 允许 WebHID 页面本地使用；禁用缓存避免更新混乱
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def guess_type(self, path):
        # 确保常见类型正确
        guess = super().guess_type(path)
        if guess is None or guess == 'application/octet-stream':
            lower = path.lower()
            if lower.endswith('.js'):
                return 'text/javascript'
            if lower.endswith('.mjs'):
                return 'text/javascript'
            if lower.endswith('.json'):
                return 'application/json'
            if lower.endswith('.svg'):
                return 'image/svg+xml'
            if lower.endswith('.woff2'):
                return 'font/woff2'
            if lower.endswith('.woff'):
                return 'font/woff'
        return guess

    def do_GET(self):
        path_only = self.path.split('?', 1)[0].split('#', 1)[0]

        # /apiproxy/* → vapi 接口本地应答 (api_cache 固化数据, 遥测空响应)
        if path_only.startswith('/apiproxy/'):
            return self.handle_apiproxy(path_only)

        # 静态文件存在 → 直接返回
        fs_path = self.translate_path(self.path)
        if os.path.isfile(fs_path):
            # index.html 注入 vapi 本地应答层
            if fs_path.lower().endswith('index.html'):
                data = open(fs_path, 'rb').read()
                html = data.decode('utf-8', errors='replace')
                inject = build_inject()
                html = html.replace('<body>', '<body>\n' + inject, 1)
                out = html.encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(out)))
                self.end_headers()
                self.wfile.write(out)
                return
            return super().do_GET()

        # /static/ 下的未知文件 → 尝试回源并缓存
        if path_only.startswith('/static/'):
            rel = path_only[len('/static/'):]
            data = upstream_fetch(rel)
            if data is not None:
                local = os.path.join(STATIC, rel.replace('/', os.sep))
                os.makedirs(os.path.dirname(local), exist_ok=True)
                with open(local, 'wb') as f:
                    f.write(data)
                ctype = self.guess_type(local) or 'application/octet-stream'
                self.send_response(200)
                self.send_header('Content-Type', ctype)
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                print(f'[cache] /static/{rel} ({len(data)} bytes)', flush=True)
                return

        # SPA 路由回退：无扩展名的路径回退到 index.html
        if '.' not in os.path.basename(path_only):
            index = os.path.join(APP, 'index.html')
            if os.path.isfile(index):
                data = open(index, 'rb').read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return

        self.send_error(404)

    def handle_apiproxy(self, path_only):
        """vapi 接口的本地应答:
        /apiproxy/v2/layouts            -> api_cache/v2/layouts.json
        /apiproxy/v2/version            -> api_cache/v2/version.json
        /apiproxy/v2/product/{vpid}     -> api_cache/v2/product_{vpid}.json (回源固化)
        遥测/AI/未知                    -> 空对象 200
        """
        rel = path_only[len('/apiproxy/'):].strip('/')

        # 固化接口: 精确匹配缓存文件
        candidates = []
        segs = rel.split('/')
        if len(segs) >= 3 and segs[0] == 'v2' and segs[1] == 'product':
            candidates.append(os.path.join(API_CACHE_DIR, 'v2', f'product_{segs[2]}.json'))
        candidates.append(os.path.join(API_CACHE_DIR, *rel.split('/')) + '.json')
        for c in candidates:
            if os.path.isfile(c):
                body = open(c, 'rb').read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

        # product 接口未固化 → 回源官方并缓存
        if len(segs) >= 3 and segs[0] == 'v2' and segs[1] == 'product':
            try:
                req = urllib.request.Request(
                    f'https://launcher.keychron.cn/vapi/v2/product/{segs[2]}',
                    headers=UA)
                data = urllib.request.urlopen(req, timeout=20).read()
                if data:
                    local = os.path.join(API_CACHE_DIR, 'v2', f'product_{segs[2]}.json')
                    os.makedirs(os.path.dirname(local), exist_ok=True)
                    with open(local, 'wb') as f:
                        f.write(data)
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    print(f'[cache] vapi product {segs[2]} ({len(data)} bytes)', flush=True)
                    return
            except Exception:
                pass

        # 其余(遥测/AI/未知) → 空对象
        body = b'{}'
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        """vapi 遥测/AI 接口的 POST 请求 → 本地空应答"""
        path_only = self.path.split('?', 1)[0].split('#', 1)[0]
        if path_only.startswith('/apiproxy/'):
            # 丢弃请求体
            try:
                length = int(self.headers.get('Content-Length', 0) or 0)
                if length:
                    self.rfile.read(length)
            except Exception:
                pass
            body = b'{}'
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)

    def do_OPTIONS(self):
        """CORS 预检应答"""
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_HEAD(self):
        self.do_GET()


def main():
    port = 1984
    for arg in sys.argv[1:]:
        if arg.startswith('--port='):
            try:
                port = int(arg.split('=', 1)[1])
            except ValueError:
                pass
    server = ThreadingHTTPServer(('127.0.0.1', port), LauncherHandler)
    print(f'Keychron Launcher local server running at http://127.0.0.1:{port}/')
    print('Root:', APP)
    print('Ctrl+C to stop.')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nStopped.')


if __name__ == '__main__':
    main()
