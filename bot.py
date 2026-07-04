import os
import json
import time
import requests
import schedule
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "apify_api_1GYfv901Vf2w8ykSW8ND5kiwVe7SQz21WTmW")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8950937975:AAHbS2kOXx4g5LlMBM8r3V8jovyFqb18wkw")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "1221757263")
SENT_JOBS_FILE = "sent_jobs.json"
APIFY_ACTOR = "solidcode~justjoin-it-scraper"

def load_sent_jobs():
    if os.path.exists(SENT_JOBS_FILE):
        with open(SENT_JOBS_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_sent_jobs(sent_jobs):
    with open(SENT_JOBS_FILE, "w") as f:
        json.dump(list(sent_jobs), f)

def run_apify_actor():
    url = f"https://api.apify.com/v2/acts/{APIFY_ACTOR}/runs?token={APIFY_TOKEN}"
    payload = {"keywords": "react native", "seniority": ["senior"]}
    response = requests.post(url, json=payload)
    data = response.json()
    return data["data"]["defaultDatasetId"]

def wait_for_actor(dataset_id, max_wait=180):
    time.sleep(max_wait)

def fetch_results(dataset_id):
    url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_TOKEN}"
    return requests.get(url).json()

def filter_jobs(jobs):
    return [j for j in jobs if "react native" in j.get("title","").lower() and j.get("country") == "PL"]

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True})

def format_job(job):
    return (f"🆕 <b>{job.get('title','N/A')}</b>\n"
            f"🏢 {job.get('company','N/A')}\n"
            f"📍 {job.get('city','N/A')} · {job.get('workingMode','N/A')}\n"
            f"💰 {job.get('salary','N/A')}\n"
            f"📅 {(job.get('datePosted','')[:10])}\n"
            f"🔗 {job.get('url','')}")

def check_and_send_jobs():
    sent_jobs = load_sent_jobs()
    new_count = 0
    try:
        dataset_id = run_apify_actor()
        wait_for_actor(dataset_id)
        jobs = fetch_results(dataset_id)
        filtered = filter_jobs(jobs)
        for job in filtered:
            job_id = job.get("id")
            if job_id and job_id not in sent_jobs:
                send_telegram(format_job(job))
                sent_jobs.add(job_id)
                new_count += 1
                time.sleep(1)
        save_sent_jobs(sent_jobs)
        if new_count == 0:
            send_telegram("✅ No new React Native jobs found.")
    except Exception as e:
        send_telegram(f"⚠️ Error: {e}")

def main():
    check_and_send_jobs()
    schedule.every().day.at("09:00").do(check_and_send_jobs)
    schedule.every().day.at("17:00").do(check_and_send_jobs)
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
