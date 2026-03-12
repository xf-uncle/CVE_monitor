import os
import time
import hmac
import hashlib
import base64
import requests
import json
import sys

repos_env = os.getenv("MONITOR_REPOS", "")
REPOS = [r.strip() for r in repos_env.split('\n') if r.strip()]
WEBHOOK_URL = os.getenv("DINGTALK_WEBHOOK")
SECRET = os.getenv("DINGTALK_SECRET")
SHA_FILE = "last_sha.json" # 改用 JSON 存储多个 SHA

def get_dingtalk_url():
    timestamp = str(round(time.time() * 1000))
    secret_enc = SECRET.encode('utf-8')
    string_to_sign = f'{timestamp}\n{SECRET}'
    hmac_code = hmac.new(secret_enc, string_to_sign.encode('utf-8'), digestmod=hashlib.sha256).digest()
    sign = base64.b64encode(hmac_code).decode('utf-8')
    return f"{WEBHOOK_URL}&timestamp={timestamp}&sign={sign}"

def send_dingtalk_msg(repo_name, commit_node):
    url = get_dingtalk_url()
    sha = commit_node['sha'][:7]
    msg = commit_node['commit']['message'].split('\n')[0]
    author = commit_node['commit']['author']['name']
    
    data = {
        "msgtype": "markdown",
        "markdown": {
            "title": f"Repo 更新: {repo_name}",
            "text": (f"### 🚀 模板仓库更新\n\n"
                     f"**项目:** `{repo_name}`\n\n"
                     f"**内容:** {msg}\n\n"
                     f"**提交者:** {author} ({sha})\n\n"
                     f"**详情:** [点击查看](https://github.com{repo_name}/commit/{sha})\n\n"
                     f"> 检测时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        }
    }
    requests.post(url, json=data)

def get_latest_commit(repo):
    api_url = f"https://api.github.com/repos/{repo}/commits?per_page=1"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if os.getenv('GITHUB_TOKEN'):
        headers["Authorization"] = f"token {os.getenv('GITHUB_TOKEN')}"
    
    try:
        resp = requests.get(api_url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            return data[0] if data else None
    except:
        return None

if __name__ == "__main__":
    # 读取历史记录
    history = {}
    if os.path.exists(SHA_FILE):
        with open(SHA_FILE, 'r') as f:
            try: history = json.load(f)
            except: history = {}

    updated_any = False
    
    for repo in REPOS:
        print(f"Checking {repo}...")
        latest = get_latest_commit(repo)
        if not latest: continue
        
        current_sha = latest['sha']
        old_sha = history.get(repo)
        
        if current_sha != old_sha:
            print(f"New commit found for {repo}!")
            #send_dingtalk_msg(repo, latest)
            history[repo] = current_sha
            updated_any = True
        
    # 如果有任何更新，保存并通知 GitHub Action
    if updated_any:
        with open(SHA_FILE, 'w') as f:
            json.dump(history, f, indent=2)
        
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write("ANY_UPDATED=true\n")
