from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import json
import time
import re

app = Flask(__name__)

def resolve_stream(page_url):
    chrome_options = Options()
    
    # ক্লাউড সার্ভারের জন্য প্রয়োজনীয় সেটিংস
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # পারফরম্যান্স লগ এনাবল করা ট্রাফিক ট্র্যাক করার জন্য
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    # Render-এ ক্রোম ও ড্রাইভার অটোমেটিক ডিটেক্ট হবে
    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(page_url)
        time.sleep(10)  # পেজ লোড ও ট্রাফিক জেনারেট হওয়ার জন্য অপেক্ষা

        # ভিডিও প্লে করার জাভাস্ক্রিপ্ট চেষ্টা
        try:
            driver.execute_script("var vid = document.querySelector('video'); if(vid){vid.play();}")
        except:
            pass

        logs = driver.get_log('performance')
        for entry in logs:
            try:
                log_data = json.loads(entry['message'])
                message = log_data['message']
                if message['method'] == 'Network.requestWillBeSent':
                    request_url = message['params']['request']['url']
                    
                    # mp4 বা m3u8 লিংক খোঁজা
                    matches = re.findall(r'(https?://[^\s"\']+\.(?:mp4|m3u8)[^\s"\']*)', request_url, re.I)
                    for match in matches:
                        if any(x in match.lower() for x in ["poster", "thumb", "sprite", "logo", "favicon", "analytics"]):
                            continue
                        return match
            except:
                pass
        return None
    except Exception as e:
        return None
    finally:
        driver.quit()

@app.route("/")
def home():
    return "Resolver Running Successfully on Render!"

@app.route("/resolve")
def resolve():
    url = request.args.get("url")
    if not url:
        return jsonify({"status": "error", "message": "No URL provided"})
    
    stream = resolve_stream(url)
    if stream:
        return jsonify({"status": "success", "stream_url": stream})
    return jsonify({"status": "error", "message": "Stream not found"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
