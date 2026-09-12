import json, re
# 从 _layouts_api.json 生成干净的官方 layouts 列表 (与官网 loadLayouts 映射一致)
data = json.load(open(r'C:/Users/O/WorkBuddy/2026-09-13-03-00-13/_work/keychron/_layouts_api.json', encoding='utf-8'))
bad = re.compile(r"['\"`]|SLEEP|BENCHMARK|extractvalue|updatexml|OR|AND|SELECT", re.I)
items = []
for x in data.get('data') or []:
    if not x.get('layout') or not x.get('langs'):
        continue
    if bad.search(x.get('layout_name') or '') or bad.search(x.get('layout') or ''):
        continue
    items.append({'id': x['id'], 'layout_name': x['layout_name'], 'layout': x['layout'], 'langs': x['langs'], 'sort': x.get('sort', 0)})
# 按 sort 排序, English (US) 优先
items.sort(key=lambda a: a.get('sort', 0))
# 去掉 sort=0 的注入垃圾后重排 index: 官网逻辑 index=数组下标+1
seen = set()
final = []
for x in items:
    key = (x['layout_name'], x['layout'])
    if key in seen:
        continue
    seen.add(key)
    final.append(x)
out = {'code': 200, 'msg': 'success', 'data': final}
p = r'C:/Users/O/WorkBuddy/2026-09-13-03-00-13/_work/keychron/api_cache/v2/layouts.json'
import os
os.makedirs(os.path.dirname(p), exist_ok=True)
json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('final layouts:', len(final))
for x in final:
    print(f"  {x['layout_name']:20s} -> keycode-{x['layout']}-win")
