import requests
import json
from sqlalchemy.orm import Session
from ..auth import validateApiKey

async def run(params: dict, db: Session):
    await validateApiKey(params["apiKey"], db)
    url = params.get("url")
    if not url:
        return {"error": "Missing url parameter"}
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://ssvid.net/'
        }
        
        data = {'query': url, 'vt': 'home'}
        
        response = requests.post(
            'https://ssvid.net/api/ajax/search?hl=en',
            headers=headers,
            data=data,
            timeout=30
        )
        
        if response.text.strip().startswith(('<!DOCTYPE', '<html')):
            return {"error": "Service unavailable"}
        
        json_data = response.json()
        
        if json_data.get("status") == "ok":
            return {"data": json_data}
        
        return {"error": json_data.get("mess", "Unknown error")}
        
    except requests.exceptions.Timeout:
        return {"error": "Request timeout"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except json.JSONDecodeError:
        return {"error": "Invalid response format"}
    except Exception as e:
        return {"error": f"Failed to fetch: {str(e)}"}
