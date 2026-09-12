import os, urllib.request, time
out = r'C:/Users/O/WorkBuddy/2026-09-13-03-00-13/_work/keychron'
BASE = 'https://launcher.keychron.cn/'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

missing = [
 'assets/outline/sync.svg',
 'chevron.e81e64764c57d381.svg',
 'assets/keyboard/keycap.png',
 'assets/keyboard/enter.png',
 'assets/keyboard/tab.png',
 'assets/keyboard/space.png',
 'assets/keyboard/magnet/axis/purple/axis.png',
 'assets/keyboard/magnet/axis/purple/axis1.png',
 'assets/keyboard/magnet/axis/purple/axis2.png',
 'assets/keyboard/magnet/axis/purple/axis3.png',
 'assets/keyboard/magnet/axis/purple/axis4.png',
 'assets/slider/thumb-vertical.svg',
 'assets/outline/plus.svg',
 'assets/outline/minus.svg',
]
ok, fail = 0, []
for rel in missing:
    p = os.path.join(out, rel.replace('/', os.sep))
    if os.path.exists(p):
        ok += 1
        continue
    os.makedirs(os.path.dirname(p), exist_ok=True)
    try:
        req = urllib.request.Request(BASE + rel, headers=UA)
        d = urllib.request.urlopen(req, timeout=30).read()
        open(p, 'wb').write(d)
        ok += 1
        print('OK', rel, len(d))
    except Exception as e:
        fail.append((rel, str(e)))
print('ok:', ok, 'fail:', len(fail))
for f, e in fail:
    print('FAIL:', f, e)
