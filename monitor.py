import os
import time
import hmac
import hashlib
import base64
import requests
import json

# 配置（建议通过 GitHub Secrets 传入）
REPO = "topscoder/nuclei-wordfence-cve"
WEBHOOK_URL = os.getenv("DINGTALK_WEBHOOK")
SECRET = os.getenv("DINGTALK_SECRET")  # 钉钉机器人安全设置里的“加签”密钥

def get_dingtalk_url():
    """生成带签名的钉钉 Webhook URL"""
    timestamp = str(round(time.time() * 1000))
    secret_enc = SECRET.encode('utf-8')
    string_to_sign = f'{timestamp}\n{SECRET}'
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = base64.b64encode(hmac_code).decode('utf-8')
    return f"{WEBHOOK_URL}&timestamp={timestamp}&sign={sign}"

def send_dingtalk_msg(commit_node):
    """发送 Markdown 格式消息，加入具体的 Commit 信息"""
    sha = commit_node['sha'][:7]
    message = commit_node['commit']['message'].split('\n')[0] # 只取首行
    author = commit_node['commit']['author']['name']
    
    url = get_dingtalk_url()
    data = {
        "msgtype": "markdown",
        "markdown": {
            "title": "Repo 更新提醒",
            "text": (f"### 🚀 Nuclei 模板更新\n\n"
                     f"**项目:** `{REPO}`\n\n"
                     f"**提交内容:** {message}\n\n"
                     f"**提交者:** {author} ({sha})\n\n"
                     f"[查看详情](https://github.com/{REPO}/commit/{sha})\n\n"
                     f"> 检测时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        }
    }
    r = requests.post(url, json=data) # requests 会自动处理 json.dumps 和 headers
    print(f"[+] DingTalk Response: {r.text}")

def get_latest_commit():
    api_url = f"https://api.github.com/{REPO}/commits?per_page=1"
    # 推荐传入 GITHUB_TOKEN 避免 API 频率限制
    headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"} if os.getenv('GITHUB_TOKEN') else {}
    resp = requests.get(api_url, headers=headers)
    if resp.status_code == 200:
        return resp.json()[0]
    return None

if __name__ == "__main__":
    last_sha = os.getenv("LAST_SHA")
    latest = get_latest_commit()
    
    if latest and latest['sha'] != last_sha:
        print(f"NEW_COMMIT_DETECTED=true")
        print(f"COMMIT_SHA={latest['sha']}")
        if WEBHOOK_URL and SECRET:
            send_dingtalk_msg(latest)
    else:
        print(f"NEW_COMMIT_DETECTED=false")
