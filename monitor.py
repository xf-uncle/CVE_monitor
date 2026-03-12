import os
import time
import hmac
import hashlib
import base64
import requests
import json
import sys

# 配置
REPO = "topscoder/nuclei-wordfence-cve"
WEBHOOK_URL = os.getenv("DINGTALK_WEBHOOK")
SECRET = os.getenv("DINGTALK_SECRET")

def get_dingtalk_url():
    timestamp = str(round(time.time() * 1000))
    secret_enc = SECRET.encode('utf-8')
    string_to_sign = f'{timestamp}\n{SECRET}'
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = base64.b64encode(hmac_code).decode('utf-8')
    return f"{WEBHOOK_URL}&timestamp={timestamp}&sign={sign}"

def send_dingtalk_msg(latest_commit):
    """发送包含具体 Commit 信息的 Markdown"""
    url = get_dingtalk_url()
    sha = latest_commit['sha'][:7]
    # 获取提交信息（取第一行避免过长）
    msg_summary = latest_commit['commit']['message'].split('\n')[0]
    author = latest_commit['commit']['author']['name']
    
    data = {
        "msgtype": "markdown",
        "markdown": {
            "title": "Repo 更新提醒",
            "text": (f"### 🚀 Nuclei 模板更新\n\n"
                     f"**项目:** `{REPO}`\n\n"
                     f"**内容:** {msg_summary}\n\n"
                     f"**提交者:** {author} ({sha})\n\n"
                     f"**详情:** [点击查看提交](https://github.com{REPO}/commit/{sha})\n\n"
                     f"> 检测时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        }
    }
    r = requests.post(url, json=data)
    print(f"DingTalk Response: {r.text}", file=sys.stderr)

def get_latest_commit():
    api_url = f"https://api.github.com{REPO}/commits?per_page=1" # 修复了API路径
    headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"} if os.getenv('GITHUB_TOKEN') else {}
    resp = requests.get(api_url, headers=headers)
    if resp.status_code == 200:
        return resp.json()[0]
    return None

if __name__ == "__main__":
    last_sha = os.getenv("LAST_SHA", "").strip()
    latest = get_latest_commit()
    
    if latest and latest['sha'] != last_sha:
        # 使用新的 GitHub Actions 输出语法
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(f"NEW_COMMIT_DETECTED=true\n")
            f.write(f"COMMIT_SHA={latest['sha']}\n")
        
        if WEBHOOK_URL and SECRET:
            send_dingtalk_msg(latest)
    else:
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(f"NEW_COMMIT_DETECTED=false\n")
