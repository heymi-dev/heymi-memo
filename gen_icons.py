"""Flaticon uicons를 PNG로 변환 — Playwright 사용"""
import subprocess, os, json, time

ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
os.makedirs(ICON_DIR, exist_ok=True)

# 아이콘 매핑: name → uicon class
ICONS = {
    "plus": "fi-br-plus",
    "pin": "fi-br-thumbtack",
    "bold": "fi-br-bold",
    "list": "fi-br-list-check",
    "number": "fi-br-list-ol",
    "color": "fi-br-palette",
    "alpha": "fi-br-eye",
    "delete": "fi-br-trash",
}

# HTML 생성 — 각 아이콘을 개별 div로
html = """<!DOCTYPE html>
<html><head>
<link rel='stylesheet' href='https://cdn-uicons.flaticon.com/2.6.0/uicons-bold-rounded/css/uicons-bold-rounded.css'>
<style>
body { background: transparent; margin: 0; padding: 20px; display: flex; gap: 40px; flex-wrap: wrap; }
.icon-box { width: 64px; height: 64px; display: flex; align-items: center; justify-content: center; }
.icon-box i { font-size: 32px; color: #CCCCCC; }
</style>
</head><body>
"""
for name, cls in ICONS.items():
    html += f'<div class="icon-box" id="{name}"><i class="fi {cls}"></i></div>\n'
html += "</body></html>"

html_path = os.path.join(ICON_DIR, "_icons.html")
with open(html_path, "w") as f:
    f.write(html)

print(f"HTML: {html_path}")
print(f"Icons: {list(ICONS.keys())}")
print("Now use Playwright to screenshot each icon")
