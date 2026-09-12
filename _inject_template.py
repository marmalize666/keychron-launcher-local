#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
注入脚本: 前置 fetch/XHR 拦截器
把 vapi 接口请求重定向到本地 api_cache（离线应答），其余放行。
由 server.py 在 serve index.html 时自动内联注入。
"""
INJECT = """
<script>
(function () {
  'use strict';
  // 本地 API 缓存映射 (key: path 后缀)
  var API_CACHE = {
    '/vapi/v2/layouts': __LAYOUTS_JSON__,
    '/vapi/v2/version': __VERSION_JSON__
  };

  function matchCache(url) {
    for (var path in API_CACHE) {
      if (url.indexOf(path) === 0 || url.indexOf(path + '?') === 0) return API_CACHE[path];
    }
    return null;
  }

  var origFetch = window.fetch;
  window.fetch = function (input, init) {
    try {
      var url = typeof input === 'string' ? input : (input && input.url) || '';
      var cached = matchCache(url);
      if (cached !== null) {
        return Promise.resolve(new Response(JSON.stringify(cached), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        }));
      }
      // 屏蔽遥测上报
      if (url.indexOf('eventTracker') !== -1 || url.indexOf('ai-') !== -1) {
        return Promise.resolve(new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } }));
      }
    } catch (e) {}
    return origFetch.apply(this, arguments);
  };

  var origOpen = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function (method, url) {
    this.__localUrl = url;
    return origOpen.apply(this, arguments);
  };
  var origSend = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.send = function () {
    var xhr = this;
    var cached = null;
    try { cached = matchCache(xhr.__localUrl || ''); } catch (e) {}
    if (cached !== null) {
      Object.defineProperty(xhr, 'readyState', { get: function () { return 4; } });
      Object.defineProperty(xhr, 'status', { get: function () { return 200; } });
      Object.defineProperty(xhr, 'responseText', { get: function () { return JSON.stringify(cached); } });
      Object.defineProperty(xhr, 'response', { get: function () { return JSON.stringify(cached); } });
      setTimeout(function () {
        if (typeof xhr.onreadystatechange === 'function') xhr.onreadystatechange();
        if (typeof xhr.onload === 'function') xhr.onload();
        xhr.dispatchEvent(new Event('readystatechange'));
        xhr.dispatchEvent(new ProgressEvent('load'));
        xhr.dispatchEvent(new ProgressEvent('loadend'));
      }, 0);
      return;
    }
    var u = xhr.__localUrl || '';
    if (u.indexOf('eventTracker') !== -1 || u.indexOf('ai-') !== -1) {
      setTimeout(function () {
        Object.defineProperty(xhr, 'readyState', { get: function () { return 4; } });
        Object.defineProperty(xhr, 'status', { get: function () { return 200; } });
        Object.defineProperty(xhr, 'responseText', { get: function () { return '{}'; } });
        Object.defineProperty(xhr, 'response', { get: function () { return '{}'; } });
        if (typeof xhr.onreadystatechange === 'function') xhr.onreadystatechange();
        if (typeof xhr.onload === 'function') xhr.onload();
      }, 0);
      return;
    }
    return origSend.apply(this, arguments);
  };
})();
</script>
"""
