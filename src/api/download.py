import subprocess
import json
from sqlalchemy.orm import Session
from ..auth import validateApiKey

async def run(params: dict, db: Session):
    await validateApiKey(params["apiKey"], db)
    url = params.get("url")
    if not url:
        return {"error": "Missing url parameter"}
    try:
        result = subprocess.run(
            [
                "curl", "-s", "-X", "POST",
                "https://ssvid.net/api/ajax/search?hl=en",
                "-H", "Content-Type: application/x-www-form-urlencoded",
                "-d", f"query={url}"
            ],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            return {"error": f"Error: {result.stderr}"}
        try:
            data = json.loads(result.stdout)
        except Exception:
            data = result.stdout
        return {
            "data": data
        }
    except Exception as e:
        return {"error": f"Failed to fetch: {str(e)}"}
}"}
