import os
import threading
import time
import requests
from pydantic import BaseModel
import datetime
from concurrent.futures import ThreadPoolExecutor
import pymongo
import uuid
from dotenv import load_dotenv
from fastapi import FastAPI

app = FastAPI()


load_dotenv()

#global stack
global_stack = ['AIzaSyDQhjplnu0FY0IsAC49kGCrW0vPX5IaV-g', 'AIzaSyCHRvWcsqAlovat4qVZ7tVFy3itcUqg0mY', 'AIzaSyCQqmO0r3AS2xPs0uEQr_pEikbyBCV7Cp8', 'AIzaSyCcJT6plV8QrkoMM3f_ET8Xoq84-NXAkVo', 'AIzaSyAouhADKbHtlVXwOSN9Qxhvh_xJ2vf3QRI', 'AIzaSyDaEYgk_in3NTxfCujFTLOe7V1rNifRHac', 'AIzaSyBQY2oTzDLgeCK18RCX_cbtI-X-2Err-5c', 'AIzaSyB4GmdQBehzM1P4y3drFo6zpOXIg0G6dnE', 'AIzaSyCOu9sesADH6srp3kD_Yk9DKaTcERss_e0','AIzaSyAf39UpAsg_oealZIX9QHegLSdwoDiMWQ0','AIzaSyDxW0bPlyGlhQhR2V47bNhtU5i1CHvq2L0','AIzaSyBn9a1Pv5CYPer_g1GDrTbeyPC-SkZfhmE','AIzaSyBaxelFPgrG4mmU_6xrZGCOlVnGkO7mBiM','AIzaSyAbUa9PZldv-GcowrhzUtO7PR2sPCwR-NA','AIzaSyDpGLxBOY3SjRHvmtRGQtiLf11DtGDfIaQ','AIzaSyBwjRDajvkp5u2OCCFa1fiYHrNZoxsmN2c','AIzaSyCwTtFTZjqd3e8kgtb_1ygkO-Uox0VacSQ','AIzaSyC1cPkTYgYWHQy597CzTV39wrKo14jxzdE','AIzaSyCj3x85B8f53TpGhTXQACCcbHMlAAs5frY','AIzaSyAQMCVytKzO2ppXw8I2NAbImdVEk7QJ9Ic']

#push data
def push_to_global_stack(data):
    global global_stack
    global_stack.append(data)

#pop data
def pop_from_global_stack():
    global global_stack
    if global_stack:
        return global_stack.pop()
    else:
        return None

# Replace with your actual Google PageSpeed Insights API key
API_KEY = os.getenv("API_KEY")
# PageSpeed Insights API endpoint
API_ENDPOINT = os.getenv("API_ENDPOINT")

client = pymongo.MongoClient(
    os.getenv("MONGO_CLIENT"),maxPoolSize=100)  # Replace with your MongoDB connection string


def get_mongodb_collection():
    db = client[os.getenv("DB_NAME")]
    collection = db[os.getenv("COLLECTION")]
    return collection


class Item(BaseModel):
    urls: list = []
    task_id: int
    userId: int

#db interaction task
def save_pagespeed_data(result, url, userid, audit_id,collection):
    data = {
        "url": url,
        "pagespeed_data": result['lighthouseResult']['categories']['performance']['score'],
        "userid": userid,
        "audit_id": audit_id,
        "create_at": datetime.datetime.now()
    }
    try:
        collection.insert_one(data)
    except Exception as e:
        print(f"Error saving data to MongoDB: {str(e)}")

# Time-consuming task function
def send_requests_batch(task_id, batch, threadnum, userid, audit_id,collection):
    print(f"Starting Task {threadnum} for userid{userid}")
    print(f"Stack Count {len(global_stack)}")
    start_time = time.time()
    api_key = pop_from_global_stack()
    key=""
    isUsingStackKey=True

    if api_key:
        key=api_key
    else:
        key=API_KEY
        isUsingStackKey=False


    for url in batch:
        try:
            print(f"the value of key in thread {threadnum} is {key}. an stack left {len(global_stack)}")
            params = {
                "url": url,
                "key": key,
            }
            response = requests.get(API_ENDPOINT, params=params)
            if response.status_code == 200:
                result = response.json()
                print(
                    f"Task {threadnum} - URL: {url} - PageSpeed Score: {result['lighthouseResult']['categories']['performance']['score']} userid={userid}")
                save_pagespeed_data(result, url, userid, audit_id, collection)
            else:
                print(f"Task {threadnum} - URL: {url} - Request failed with status code: {response.status_code}")
        except Exception as e:
            print(f"Error saving data from iteration: {str(e)}")

    if isUsingStackKey:
        push_to_global_stack(key)

    print(f"Now Stack count added {len(global_stack)}")
    print(f"Finished Task {threadnum} userid={userid}")
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Thread {threadnum} execution time: {execution_time} seconds userid={userid}")
#Background task
def run_background_task(audit_id, task_id, urls, userid,collection):
    with ThreadPoolExecutor(max_workers=10) as executor:
        batch_size = 5
        threadnum = 0
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]
            threadnum = threadnum + 1
            executor.submit(send_requests_batch, task_id, batch, threadnum, userid, audit_id,collection)

@app.post("/task")
async def run_task_in_background(item: Item):
    user_id= str(uuid.uuid4())
    item.userId=user_id
    print(f"User Id={item.userId}")
    audit_id = str(uuid.uuid4())
    collection = get_mongodb_collection()
    # Create and start a background thread to run the task
    threading.Thread(target=run_background_task, args=(audit_id, item.task_id, item.urls, item.userId,collection)).start()
    return {"message": f"Task porcessing"}


