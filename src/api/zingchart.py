from sqlalchemy.orm import Session
from ..auth import validateApiKey
import requests
import hashlib
import hmac
import time

URL = "https://zingmp3.vn"
API_KEY = "X5BM3w8N7MKozC0B85o4KMlzLZKhV00y"
SECRET_KEY = "acOrvUS15XRW2o9JksiK1KgQ6Vbds8ZW"
VERSION = "1.16.1"

def getHash256(string):
    return hashlib.sha256(string.encode()).hexdigest()

def getHmac512(string, key):
    return hmac.new(key.encode(), string.encode(), hashlib.sha512).hexdigest()

def getSig(path, params):
    paramString = ''.join(f"{key}={params[key]}" for key in sorted(params.keys()) if key in ["ctime", "id", "week", "year", "version"])
    return getHmac512(path + getHash256(paramString), SECRET_KEY)

def getHeaders():
    return {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json;charset=utf-8',
        'Host': 'zingmp3.vn',
        'Pragma': 'no-cache',
        'Referer': 'https://zingmp3.vn/',
        'Sec-Ch-Ua': '"Chromium";v="137"; "Not/A)Brand";v="24"',
        'Sec-Ch-Ua-Mobile': '0',
        'Sec-Ch-Ua-Platform': '"Linux"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        'X-Server': 'ZingMp3-api-v2'
    }

def getCookie():
    try:
        response = requests.get(URL, headers=getHeaders(), timeout=10)
        return response.cookies.get_dict()
    except:
        return {}

def requestZingMp3(path, params):
    cookies = getCookie()
    headers = getHeaders()
    response = requests.get(f"{URL}{path}", params=params, cookies=cookies, headers=headers, timeout=15)
    return response.json()

async def run(params: dict, db: Session):
    await validateApiKey(params["apiKey"], db)
    
    chartId = "IWZ9Z08I"
    week = 0
    year = 0
    
    ctime = str(int(time.time()))
    path = "/api/v2/page/get/week-chart"
    requestParams = {
        "id": chartId,
        "week": week,
        "year": year,
        "ctime": ctime,
        "version": VERSION,
        "apiKey": API_KEY,
        "sig": getSig(path, {
            "id": chartId,
            "week": week,
            "year": year,
            "ctime": ctime,
            "version": VERSION
        })
    }
    
    try:
        result = requestZingMp3(path, requestParams)
        return result
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}
