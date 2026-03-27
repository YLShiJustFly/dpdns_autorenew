#!/usr/bin/env python3
"""
DPDNS 自动续期脚本 - 使用 DrissionPage
DrissionPage 是一个专门用于绕过自动化检测的库
"""

import requests
import json
import os
import sys
import time
from pathlib import Path

EMAIL = os.environ.get('EMAIL', '')
PASSWORD = os.environ.get('PASSWORD', '')
DOMAIN = os.environ.get('DOMAIN', 'youseeicanfly.dpdns.org')
TOKEN_FILE = "/config/.dpdns_token.json"
COOKIES_FILE = "/config/.dpdns_cookies.json"


def save_cookies(session):
    """保存 cookies 到文件"""
    try:
        cookies = {cookie.name: cookie.value for cookie in session.cookies}
        with open(COOKIES_FILE, 'w') as f:
            json.dump({'cookies': cookies, 'updated_at': time.time()}, f)
        print(f"Cookies 已保存到 {COOKIES_FILE}")
    except Exception as e:
        print(f"保存 cookies 失败: {e}")


def load_cookies():
    """从文件加载 cookies"""
    if os.path.exists(COOKIES_FILE):
        try:
            with open(COOKIES_FILE, 'r') as f:
                data = json.load(f)
                if time.time() - data.get('updated_at', 0) < 7 * 24 * 3600:
                    return data.get('cookies')
        except:
            pass
    return None


def try_login_with_cookies():
    """尝试使用保存的 cookies 登录"""
    cookies = load_cookies()
    if not cookies:
        return None

    print("尝试使用保存的 cookies 登录...")
    session = requests.Session()

    for name, value in cookies.items():
        session.cookies.set(name, value, domain='dash.domain.digitalplat.org')

    test_url = f"https://dash.domain.digitalplat.org/_panel_api/api/domains/{DOMAIN}"
    try:
        resp = session.get(test_url, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('ok') and data.get('domain'):
                print("使用 cookies 登录成功")
                return session
    except Exception as e:
        print(f"Cookies 登录失败: {e}")

    return None


def get_turnstile_token_with_drission():
    """使用 DrissionPage 获取 turnstile token"""
    print("启动 DrissionPage...")

    try:
        from DrissionPage import ChromiumPage, ChromiumOptions
    except ImportError:
        print("未安装 DrissionPage")
        return None

    co = ChromiumOptions()
    co.headless(False)  # 必须有头模式
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    co.set_argument('--disable-gpu')
    co.set_argument('--window-size', '1920,1080')

    page = None
    try:
        page = ChromiumPage(co)
        print("浏览器启动成功")

        # 访问登录页
        print("访问登录页面...")
        page.get('https://dash.domain.digitalplat.org/auth/login')
        time.sleep(5)

        # 填写账号密码
        print("填写登录信息...")
        page.ele('css:input[type=email]').input(EMAIL)
        page.ele('css:input[type=password]').input(PASSWORD)

        # 截图
        page.get_screenshot('/config/login_initial.png')
        print("截图已保存: /config/login_initial.png")

        # 等待 Turnstile 完成
        print("等待 Turnstile 验证完成...")
        max_wait = 120
        waited = 0
        token = None

        while waited < max_wait:
            try:
                turnstile_input = page.ele('css:input[name=cf-turnstile-response]')
                token = turnstile_input.attr('value')
                if token and len(token) > 100:
                    print(f"检测到 Turnstile token（长度: {len(token)}）")
                    break
            except:
                pass

            # 检查登录按钮是否启用
            try:
                login_btn = page.ele('css:button[type=submit]')
                if not login_btn.attr('disabled'):
                    print(f"登录按钮已启用（等待了 {waited} 秒）")
                    # 再获取一次token
                    try:
                        turnstile_input = page.ele('css:input[name=cf-turnstile-response]')
                        token = turnstile_input.attr('value')
                        if token and len(token) > 100:
                            print(f"检测到 Turnstile token（长度: {len(token)}）")
                    except:
                        pass
                    break
            except:
                pass

            time.sleep(2)
            waited += 2

        page.get_screenshot('/config/login_final.png')
        print(f"最终 token 长度: {len(token) if token else 0}")

        return token

    except Exception as e:
        print(f"浏览器启动失败: {e}")
        return None

    finally:
        if page:
            page.quit()


def login_with_token(turnstile_token):
    """使用 token 登录"""
    url = "https://dash.domain.digitalplat.org/_panel_api/api/auth/login"

    headers = {
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Content-Type": "application/json",
        "Origin": "https://dash.domain.digitalplat.org",
        "Referer": "https://dash.domain.digitalplat.org/auth/login",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    data = {
        "email": EMAIL,
        "password": PASSWORD,
        "turnstile_token": turnstile_token
    }

    session = requests.Session()
    resp = session.post(url, headers=headers, json=data)
    print(f"登录响应: {resp.status_code}")

    if resp.status_code == 200:
        result = resp.json()
        if result.get('ok'):
            print("登录成功")
            save_cookies(session)
            return session
        else:
            print(f"登录失败: {result.get('error', '未知错误')}")
            return None
    else:
        print(f"登录失败: {resp.text}")
        return None


def renew_domain(session):
    """续期域名"""
    url = f"https://dash.domain.digitalplat.org/_panel_api/api/domains/{DOMAIN}/renew"

    headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
        "Referer": f"https://dash.domain.digitalplat.org/domains/{DOMAIN}",
    }

    resp = session.post(url, headers=headers, json={})
    print(f"续期响应: {resp.status_code}")

    try:
        data = resp.json()
    except:
        data = {"error": resp.text}

    if resp.status_code == 200 and data.get("ok"):
        print("续期成功！")
        return True
    elif "more than 180 days" in str(data):
        print("还未到续期时间（180天内）")
        return True
    else:
        print(f"续期失败: {data.get('error', resp.text)}")
        return False


def main():
    print("=" * 60)
    print("DPDNS 自动续期工具 (DrissionPage 版)")
    print("=" * 60)

    if not EMAIL or not PASSWORD:
        print("请设置 EMAIL 和 PASSWORD 环境变量")
        return 1

    # 首先尝试使用 cookies 登录
    session = try_login_with_cookies()

    if not session:
        # 使用 DrissionPage 获取 token
        print("\n[开始] 使用 DrissionPage 获取 Turnstile Token...")
        new_token = get_turnstile_token_with_drission()

        if not new_token:
            print("\n无法获取 turnstile_token")
            return 1

        print(f"\n[登录] 使用 Token 登录并续期...")
        session = login_with_token(new_token)

    if not session:
        print("\n登录失败")
        return 1

    success = renew_domain(session)

    if success:
        print("\n续期成功！")
        return 0
    else:
        print("\n续期失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
