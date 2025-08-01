from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import requests
from ..auth import validateApiKey
from ..db import getDb

router = APIRouter(prefix="/api")

@router.get("/github-info")
async def get_github_info(username: str, apiKey: str, db: Session = Depends(getDb)):
    await validateApiKey(apiKey, db)
    
    github_api_url = f"https://api.github.com/users/{username}"
    
    try:
        response = requests.get(github_api_url)
        
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"GitHub user '{username}' not found")
        elif response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"GitHub API error: {response.status_code}")
        
        user_data = response.json()
            
            return {
                "success": True,
                "owner": "VuXuanKien1997",
                "user_info": {
                    "login": user_data.get("login"),
                    "id": user_data.get("id"),
                    "name": user_data.get("name"),
                    "bio": user_data.get("bio"),
                    "company": user_data.get("company"),
                    "location": user_data.get("location"),
                    "email": user_data.get("email"),
                    "blog": user_data.get("blog"),
                    "twitter_username": user_data.get("twitter_username"),
                    "public_repos": user_data.get("public_repos"),
                    "public_gists": user_data.get("public_gists"),
                    "followers": user_data.get("followers"),
                    "following": user_data.get("following"),
                    "created_at": user_data.get("created_at"),
                    "updated_at": user_data.get("updated_at"),
                    "avatar_url": user_data.get("avatar_url"),
                    "html_url": user_data.get("html_url")
                }
            }
            
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {str(e)}")
