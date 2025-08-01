from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import requests
from ..auth import validateApiKey
from ..db import getDb

router = APIRouter(prefix="/api")

@router.get("/github-info")
async def getGithubInfo(username: str, apiKey: str, db: Session = Depends(getDb)):
    await validateApiKey(apiKey, db)
    
    githubApiUrl = f"https://api.github.com/users/{username}"
    
    try:
        response = requests.get(githubApiUrl)
        
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"GitHub user '{username}' not found")
        elif response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"GitHub API error: {response.status_code}")
        
        userData = response.json()
        
        return {
            "success": True,
            "owner": "VuXuanKien1997",
            "userInfo": {
                "login": userData.get("login"),
                "id": userData.get("id"),
                "name": userData.get("name"),
                "bio": userData.get("bio"),
                "company": userData.get("company"),
                "location": userData.get("location"),
                "email": userData.get("email"),
                "blog": userData.get("blog"),
                "twitterUsername": userData.get("twitter_username"),
                "publicRepos": userData.get("public_repos"),
                "publicGists": userData.get("public_gists"),
                "followers": userData.get("followers"),
                "following": userData.get("following"),
                "createdAt": userData.get("created_at"),
                "updatedAt": userData.get("updated_at"),
                "avatarUrl": userData.get("avatar_url"),
                "htmlUrl": userData.get("html_url")
            }
        }
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {str(e)}")
