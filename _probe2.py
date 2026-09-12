import re
out = r'C:/Users/O/WorkBuddy/2026-09-13-03-00-13/_work/keychron'
data = open(out + '/main.34cd9f0e4e8b0d59.js', 'rb').read().decode('utf-8', errors='replace')

# 直接找 not-connect 组件类: selectors [["not-connect"]] 之后找类方法 (goDemo / setDemo)
i = data.find('selectors:[["not-connect"]]')
seg = data[i:i+80000]
# 类里有连接到 demo 的函数: 找 connectDemo / demoStatus / 'demo'
for m in re.finditer(r'([a-zA-Z_$]+)\(\)\{[^{}]{0,80}deviceStatus[^{}]{0,120}\}', seg):
    print(repr(m.group(0)[:250]))
    print('---')

# 更直接: 找 "demo" 字符串在 not-connect 段内的赋值
end = seg.find('selectors:[[')  # 下一个组件
demo_assign = [m.start() for m in re.finditer(r'deviceStatus="demo"|deviceStatus\s*=\s*"demo"|"demo"===[a-zA-Z_.]+|===."demo"', seg[:30000])]
print('assign hits:', demo_assign[:5])
for h in demo_assign[:5]:
    print(repr(seg[max(0,h-250):h+250]))
    print('===')
