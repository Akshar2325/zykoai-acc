import requests
import time
import re
import random
import string
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import os

logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURATION
# ============================================================
MAIL_TM_URL = "https://api.mail.tm"
SUPABASE_URL = "https://ofvmcbqqwziashqoabaw.supabase.co"
SUPABASE_API_KEY = "sb_publishable_deUz8hivqth0C1y_MJigLQ_EUysTT-q"
ROTATE_URL = "https://api.zyloai.net/v1/auth/rotate"
CHAT_URL = "https://api.zyloai.net/v1/chat/completions"

# ============================================================
# MAIL.TM HELPERS
# ============================================================
def get_mail_domain():
    resp = requests.get(f"{MAIL_TM_URL}/domains")
    return resp.json()['hydra:member'][0]['domain']

def create_mail_account(email, password):
    payload = {"address": email, "password": password}
    headers = {"Content-Type": "application/ld+json", "accept": "application/ld+json"}
    resp = requests.post(f"{MAIL_TM_URL}/accounts", json=payload, headers=headers)
    return resp.status_code == 201

def get_mail_token(email, password):
    payload = {"address": email, "password": password}
    resp = requests.post(f"{MAIL_TM_URL}/token", json=payload)
    return resp.json().get("token")

def wait_for_otp(token, timeout=120):
    start = time.time()
    headers = {"Authorization": f"Bearer {token}"}
    while time.time() - start < timeout:
        resp = requests.get(f"{MAIL_TM_URL}/messages", headers=headers)
        messages = resp.json().get("hydra:member", [])
        for msg in messages:
            intro = msg.get("intro", "")
            match = re.search(r"\b(\d{6})\b", intro)
            if match:
                return match.group(1)
        time.sleep(5)
    raise RuntimeError("OTP timeout: No email received from Zylo AI")

# ============================================================
# TEST LOGIC
# ============================================================
def run_one_account(index, max_workers, chat_model, chat_message):
    session = requests.Session()
    session.headers.update({"user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"})

    result = {"index": index, "email": "", "password": "", "api_key": "", "chat_success": False, "error": None}

    try:
        domain = get_mail_domain()
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        email = f"tester_{random_str}@{domain}"
        password = email
        result["email"] = email
        result["password"] = password

        if not create_mail_account(email, password): raise RuntimeError("Mail creation failed")
        mail_token = get_mail_token(email, password)

        headers = {
            "apikey": SUPABASE_API_KEY,
            "authorization": f"Bearer {SUPABASE_API_KEY}",
            "content-type": "application/json;charset=UTF-8",
            "x-client-info": "supabase-js-web/2.45.4"
        }
        otp_req = session.post(f"{SUPABASE_URL}/auth/v1/otp", headers=headers, json={
            "email": email, "data": {"username": email}, "create_user": True
        })

        otp_code = wait_for_otp(mail_token)

        verify_req = session.post(f"{SUPABASE_URL}/auth/v1/verify", headers=headers, json={
            "email": email, "token": otp_code, "type": "email"
        })
        access_token = verify_req.json().get("access_token")

        rotate_headers = {"authorization": f"Bearer {access_token}", "content-type": "application/json"}
        rotate_resp = session.post(ROTATE_URL, headers=rotate_headers)
        api_key = rotate_resp.json().get("api_key")
        result["api_key"] = api_key

        chat_headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        chat_resp = session.post(CHAT_URL, headers=chat_headers, json={
            "model": chat_model, "messages": [{"role": "user", "content": chat_message}]
        })
        result["chat_success"] = "choices" in chat_resp.json()

    except Exception as e:
        result["error"] = str(e)

    return result

def run(parameters: dict) -> str:
    number_of_accounts = parameters.get("number_of_accounts", 2)
    max_workers = parameters.get("max_workers", 1)
    chat_model = parameters.get("chat_model", "nemotron-3-ultra")
    chat_message = parameters.get("chat_message", "Hello! What can you do?")
    output_file = f"output_{random.getrandbits(32):08x}.txt"

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(run_one_account, i, max_workers, chat_model, chat_message) for i in range(1, number_of_accounts + 1)]
        for f in as_completed(futures):
            results.append(f.result())

    with open(output_file, "w") as f:
        for r in sorted(results, key=lambda x: x['index']):
            f.write(f"Account Email: {r['email']}\n")
            f.write(f"Account Password: {r['password']}\n")
            f.write(f"API key: {r['api_key'] or 'FAILED'}\n")
            status = "SUCCESS" if r['chat_success'] else "FAILED"
            f.write(f"Our Testing on llm api call of chat completion successed or not: {status}\n")
            if r['error']: f.write(f"Error Details: {r['error']}\n")
            f.write("="*70 + "\n\n")
    
    logger.info(f"Results written to {output_file}")
    return output_file