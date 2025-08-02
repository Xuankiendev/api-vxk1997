from sqlalchemy.orm import Session
from ..auth import validateApiKey
import requests

async def run(params: dict, db: Session):
    await validateApiKey(params["apiKey"], db)

    username = params["username"]
    url = f"https://api.github.com/users/{username}"

    response = requests.get(url)

    if response.status_code != 200:
        return {"error": f"GitHub user '{username}' not found"}

    return response.json()
