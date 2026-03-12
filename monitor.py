# monitor.py
import requests
import os

REPO = "topscoder/nuclei-wordfence-cve"
# 使用环境变量获取上次记录的 SHA
LAST_SHA = os.getenv("LAST_SHA")

def get_latest_commit():
    url = f"https://api.github.com{REPO}/commits?per_page=1"
    resp = requests.get(url)
    if resp.status_code == 200:
        return resp.json()[0]['sha']
    return None

current_sha = get_latest_commit()

if current_sha and current_sha != LAST_SHA:
    print(f"NEW_COMMIT_DETECTED=true")
    print(f"COMMIT_SHA={current_sha}")
    # 在这里添加你的通知代码（如 Webhook）
else:
    print(f"NEW_COMMIT_DETECTED=false")
