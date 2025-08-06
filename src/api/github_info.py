from sqlalchemy.orm import Session
from ..auth import validateApiKey
import requests

async def run(params: dict, db: Session):
    await validateApiKey(params["apiKey"], db)

    userName = params["userName"]
    url = f"https://api.github.com/users/{userName}"

    response = requests.get(url)

    if response.status_code != 200:
        return {"error": f"User '{userName}' not found"}

    return response.json()
