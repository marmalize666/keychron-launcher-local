// Angular 的 layoutCount=43 说明: 页面里的请求没走被 hook 的 window.fetch
// Angular HttpClient 默认用 XHR! 但我们的 XHR hook 用了 defineProperty 覆盖实例属性
// 问题可能在: Angular 的 XHR 观察者读 response 时用的不是实例属性
// 最干净的修法: 不 hook 运行时, 直接在 service worker / 或把 XHR open 的 URL 改写成本地路径
// —— 改写 URL 方案: XHR open 时把官方 vapi URL 重写为 /apiproxy/... 由本地 server 应答
// fetch 同理. 这样 Angular 内部逻辑完全不变, 走标准通道
(function () {
  'use strict';
  var LOCAL_MAP = {
    'https://launcher.keychron.cn/vapi/': '/apiproxy/',
    'https://launcher.keychron.com/vapi/': '/apiproxy/',
    'https://erpapik.keychron.cn/': '/apiproxy/telemetry/'
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
})();
