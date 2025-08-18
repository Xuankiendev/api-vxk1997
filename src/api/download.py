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
        response = requests.post(
            "https://ssvid.net/api/ajax/search?hl=en",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"query": url}
        )
        if response.status_code != 200:
            return {"error": f"Failed with status {response.status_code}"}
        try:
            data = response.json()
        except Exception:
            data = response.text
        return {"data": data}
    except Exception as e:
        return {"error": f"Failed to fetch: {str(e)}"}
