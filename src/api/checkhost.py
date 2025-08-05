from sqlalchemy.orm import Session
from ..auth import validateApiKey
import requests
import re
import json
import asyncio
import aiohttp
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, Optional

async def run(params: dict, db: Session):
    await validateApiKey(params["apiKey"], db)
    
    method = params.get("method", "http")
    url = params.get("url")
    
    if not url:
        return {"error": "URL parameter is required"}
    
    if method not in ["http", "ping", "tcp", "udp", "dns", "smtp"]:
        return {"error": "Invalid method. Supported methods: http, ping, tcp, udp, dns, smtp"}
    
    try:
        result = await performCheck(method, url)
        return {
            "success": True,
            "method": method,
            "url": url,
            "data": result
        }
        
    except Exception as e:
        return {"error": f"Failed to check host: {str(e)}"}

async def performCheck(method: str, targetUrl: str) -> Dict[str, Any]:
    checkUrl = f"https://check-host.net/check-{method}"
    
    params = {
        "host": targetUrl,
        "max_nodes": 10
    }
    
    headers = {
        "Accept": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(checkUrl, params=params, headers=headers) as response:
            responseData = await response.json()
            
            requestId = responseData["request_id"]
            permanentLink = responseData.get("permanent_link")
            nodes = responseData.get("nodes", {})
            
            results = await waitForResults(session, requestId)
            
            return {
                "requestId": requestId,
                "permanentLink": permanentLink,
                "nodes": nodes,
                "results": results
            }

async def waitForResults(session: aiohttp.ClientSession, requestId: str) -> Dict[str, Any]:
    resultUrl = f"https://check-host.net/check-result/{requestId}"
    headers = {"Accept": "application/json"}
    
    for i in range(15):
        async with session.get(resultUrl, headers=headers) as response:
            data = await response.json()
            
            if data and not all(value is None for value in data.values()):
                return data
                
            await asyncio.sleep(2)
    
    return {"error": "Timeout waiting for results"}
