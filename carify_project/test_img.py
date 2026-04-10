import urllib.request
import re

html = urllib.request.urlopen('http://127.0.0.1:8000/').read().decode()
matches = re.findall(r'<img[^>]+class="shop-img"[^>]*>', html)
if not matches:
    matches = re.findall(r'<img[^>]+>', html)

for m in matches:
    if "shop-img" in m:
        print(m)
