from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import requests

from src.auth import validateApiKey
from src.db import getDb

router = APIRouter(prefix="/api")

@router.get("/github_info")
async def getGithubInfo(username: str, apiKey: str, db: Session = Depends(getDb)):
    await validateApiKey(apiKey, db)

    url = f"https://api.github.com/users/{username}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"GitHub user '{username}' not found")
        response.raise_for_status()

        data = response.json()
        return {
            "success": True,
            "owner": "VuXuanKien1997",
            "userInfo": {
                "login": data.get("login"),
                "id": data.get("id"),
                "name": data.get("name"),
                "bio": data.get("bio"),
                "company": data.get("company"),
                "location": data.get("location"),
                "email": data.get("email"),
                "blog": data.get("blog"),
                "twitterUsername": data.get("twitter_username"),
                "publicRepos": data.get("public_repos"),
                "publicGists": data.get("public_gists"),
                "followers": data.get("followers"),
                "following": data.get("following"),
                "createdAt": data.get("created_at"),
                "updatedAt": data.get("updated_at"),
                "avatarUrl": data.get("avatar_url"),
                "htmlUrl": data.get("html_url")
            }
        }

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}")
