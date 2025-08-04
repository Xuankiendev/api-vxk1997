from sqlalchemy.orm import Session
from ..auth import validateApiKey
import requests
import asyncio
import aiohttp
from typing import Dict, Any, Optional
import json
import time

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
        try:
            async with session.get(checkUrl, params=params, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"Check-host.net returned status {response.status}")
                
                responseData = await response.json()
                
                if responseData.get("ok") != 1:
                    raise Exception("Check request failed")
                
                requestId = responseData["request_id"]
                permanentLink = responseData.get("permanent_link")
                nodes = responseData.get("nodes", {})
                
                results = await waitForResults(session, requestId)
                
                return {
                    "requestId": requestId,
                    "permanentLink": permanentLink,
                    "nodes": nodes,
                    "results": results,
                    "summary": generateSummary(results, method, nodes)
                }
                
        except aiohttp.ClientError as e:
            raise Exception(f"Network error: {str(e)}")
        except json.JSONDecodeError:
            raise Exception("Invalid JSON response from check-host.net")

async def waitForResults(session: aiohttp.ClientSession, requestId: str, maxWaitTime: int = 30) -> Dict[str, Any]:
    resultUrl = f"https://check-host.net/check-result/{requestId}"
    headers = {"Accept": "application/json"}
    startTime = time.time()
    
    while time.time() - startTime < maxWaitTime:
        try:
            async with session.get(resultUrl, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data and not all(value is None for value in data.values()):
                        return processResults(data)
                    
                await asyncio.sleep(2)
                
        except Exception:
            await asyncio.sleep(2)
            continue
    
    raise Exception("Timeout waiting for results from check-host.net")

def processResults(rawResults: Dict[str, Any]) -> Dict[str, Any]:
    processedResults = {}
    
    for nodeId, result in rawResults.items():
        nodeInfo = {
            "nodeId": nodeId,
            "status": "pending" if result is None else "unknown",
            "responseTime": None,
            "error": None,
            "details": None
        }
        
        if result is None:
            nodeInfo["status"] = "pending"
        elif isinstance(result, list) and len(result) > 0:
            resultData = result[0]
            
            if isinstance(resultData, list):
                if len(resultData) >= 3:
                    nodeInfo["status"] = "success" if resultData[0] == 0 else "failed"
                    nodeInfo["responseTime"] = resultData[1]
                    if resultData[2]:
                        nodeInfo["error"] = resultData[2]
                elif len(resultData) >= 2:
                    nodeInfo["status"] = "success" if resultData[0] == 0 else "failed"
                    nodeInfo["responseTime"] = resultData[1]
            elif isinstance(resultData, dict):
                if "error" in resultData:
                    nodeInfo["status"] = "failed"
                    nodeInfo["error"] = resultData["error"]
                elif "time" in resultData:
                    nodeInfo["status"] = "success"
                    nodeInfo["responseTime"] = resultData["time"]
                    if "address" in resultData:
                        nodeInfo["details"] = {"address": resultData["address"]}
                elif "A" in resultData or "AAAA" in resultData:
                    nodeInfo["status"] = "success"
                    nodeInfo["details"] = {
                        "A": resultData.get("A", []),
                        "AAAA": resultData.get("AAAA", []),
                        "TTL": resultData.get("TTL")
                    }
                    if not resultData.get("A") and not resultData.get("AAAA"):
                        nodeInfo["status"] = "failed"
                        nodeInfo["error"] = "Unable to resolve domain"
        
        processedResults[nodeId] = nodeInfo
    
    return processedResults

def generateSummary(results: Dict[str, Any], method: str, nodes: Dict[str, Any]) -> Dict[str, Any]:
    totalNodes = len(results)
    successfulNodes = sum(1 for r in results.values() if r.get("status") == "success")
    failedNodes = sum(1 for r in results.values() if r.get("status") == "failed")
    pendingNodes = sum(1 for r in results.values() if r.get("status") == "pending")
    
    responseTimes = [
        r.get("responseTime") for r in results.values() 
        if r.get("responseTime") is not None and isinstance(r.get("responseTime"), (int, float))
    ]
    
    avgResponseTime = sum(responseTimes) / len(responseTimes) if responseTimes else None
    minResponseTime = min(responseTimes) if responseTimes else None
    maxResponseTime = max(responseTimes) if responseTimes else None
    
    successRate = (successfulNodes / totalNodes * 100) if totalNodes > 0 else 0
    
    nodeLocations = []
    for nodeId, nodeData in results.items():
        if nodeId in nodes:
            location = nodes[nodeId]
            if isinstance(location, list) and len(location) >= 3:
                nodeLocations.append({
                    "nodeId": nodeId,
                    "country": location[1],
                    "city": location[2],
                    "status": nodeData.get("status")
                })
    
    return {
        "method": method,
        "totalNodes": totalNodes,
        "successfulNodes": successfulNodes,
        "failedNodes": failedNodes,
        "pendingNodes": pendingNodes,
        "successRate": round(successRate, 2),
        "avgResponseTime": round(avgResponseTime, 3) if avgResponseTime else None,
        "minResponseTime": minResponseTime,
        "maxResponseTime": maxResponseTime,
        "status": "healthy" if successRate >= 70 else "degraded" if successRate >= 30 else "down",
        "nodeLocations": nodeLocations
    }
