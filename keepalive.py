import os
import time
import requests
from playwright.sync_api import sync_playwright

# 🔧 从环境变量读取信息
SITE_URL = os.environ.get("SITE_URL", "")
USERNAME = os.environ.get("USERNAME", "")
PASSWORD = os.environ.get("PASSWORD", "")
USERNAME_SELECTOR = os.environ.get("USERNAME_SELECTOR", "")   # 例如 input[name="username"]
PASSWORD_SELECTOR = os.environ.get("PASSWORD_SELECTOR", "")   # 例如 input[name="password"]
LOGIN_BUTTON_SELECTOR = os.environ.get("LOGIN_BUTTON_SELECTOR", "")  # 例如 button[type="submit"]
SUCCESS_TEXT = os.environ.get("SUCCESS_TEXT", "Dashboard")   # 登录后页面出现的文本
FAIL_TEXTS = os.environ.get("FAIL_TEXTS", "Invalid,Error,Failed").split(",")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

report = []

def login_and_check(playwright):
    report.append(f"🌐 {SITE_URL} 登录保活检测开始")
    try:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.goto(SITE_URL)
        time.sleep(3)

        # ✨ 如果有“Login”按钮，先点击
        if page.query_selector("text=Login"):
            report.append("👆 正在点击登录按钮")
            page.click("text=Login")
            page.wait_for_selector(USERNAME_SELECTOR, timeout=10000)

        report.append("✍️ 输入账号密码")
        page.fill(USERNAME_SELECTOR, USERNAME)
        time.sleep(1)
        page.fill(PASSWORD_SELECTOR, PASSWORD)
        time.sleep(1)
        page.click(LOGIN_BUTTON_SELECTOR)
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        if page.query_selector(f"text={SUCCESS_TEXT}"):
            report.append(f"✅ 登录成功: {USERNAME}")
        else:
            failed = None
            for t in FAIL_TEXTS:
                if page.query_selector(f"text={t.strip()}"):
                    failed = t.strip()
                    break
            if failed:
                report.append(f"❌ 登录失败: {failed}")
            else:
                report.append(f"⚠️ 未检测到成功标志，可能登录失败")

        context.close()
        browser.close()

    except Exception as e:
        report.append(f"💥 执行异常: {e}")


def send_to_telegram(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ 未配置 Telegram，不发送通知")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        res = requests.post(url, data=payload)
        if res.status_code == 200:
            print("📨 Telegram 通知已发送")
        else:
            print(f"⚠️ Telegram 发送失败: {res.text}")
    except Exception as e:
        print(f"⚠️ Telegram 异常: {e}")

def main():
    with sync_playwright() as playwright:
        login_and_check(playwright)
        final_msg = "\n".join(report)
        print(final_msg)
        send_to_telegram(final_msg)

if __name__ == "__main__":
    main()
