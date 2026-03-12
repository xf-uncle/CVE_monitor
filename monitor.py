import os
import time
import hmac
import hashlib
import base64
import requests
import json
import sys

# 配置
REPO = "/topscoder/nuclei-wordfence-cve"
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
    # 确保路径中包含 /repos/
    api_url = f"https://api.github.com/repos{REPO}/commits?per_page=1"
    
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    # 这里的 GITHUB_TOKEN 建议改用环境变量中的那个
    token = os.getenv('GITHUB_TOKEN')
    print(f'get_latest_commit - token -> {token}')
    if token:
        headers["Authorization"] = f"token {token}"
        
    try:
        resp = requests.get(api_url, headers=headers)
        # 调试用：如果报错，打印出状态码和响应内容
        if resp.status_code != 200:
            print(f"API Error: Status {resp.status_code}, Response: {resp.text}", file=sys.stderr)
            return None
            
        data = resp.json()
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        else:
            print(f"API Error: Unexpected data format: {data}", file=sys.stderr)
            return None
    except Exception as e:
        print(f"Request Exception: {e}", file=sys.stderr)
        return None

if __name__ == "__main__":
    last_sha = os.getenv("LAST_SHA", "").strip()
    latest = get_latest_commit()
    print(f"DEBUG: last_sha='{last_sha}', latest_sha='{latest['sha']}'")
    if latest and latest['sha'] != last_sha:
        # 使用新的 GitHub Actions 输出语法
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(f"NEW_COMMIT_DETECTED=true\n")
            f.write(f"COMMIT_SHA={latest['sha']}\n")
        
        if WEBHOOK_URL and SECRET:
            pass
           # send_dingtalk_msg(latest)
    else:
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(f"NEW_COMMIT_DETECTED=false\n")
