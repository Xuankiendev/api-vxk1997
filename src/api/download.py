from sqlalchemy.orm import Session
from ..auth import validateApiKey
import requests
import re
import json
import asyncio
import aiohttp
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, Optional
import yt_dlp

async def run(params: dict, db: Session):
    await validateApiKey(params["apiKey"], db)
    
    url = params.get("url")
    try:
        platform = detectPlatform(url)
        if platform == "unsupported":
            return {"error": "Unsupported platform or invalid URL"}
        
        result = await extractAllLinks(url)
        return {
            "success": True,
            "platform": platform,
            "data": result
        }
        
    except Exception as e:
        return {"error": f"Failed to process URL: {str(e)}"}

def detectPlatform(url: str) -> str:
    url = url.lower()
    platforms = {
        "youtube": ["youtube.com", "youtu.be", "m.youtube.com"],
        "tiktok": ["tiktok.com", "vm.tiktok.com", "vt.tiktok.com"],
        "soundcloud": ["soundcloud.com", "m.soundcloud.com"],
        "instagram": ["instagram.com", "instagr.am"],
        "twitter": ["twitter.com", "t.co", "x.com"],
        "facebook": ["facebook.com", "fb.watch", "m.facebook.com"],
        "twitch": ["twitch.tv", "clips.twitch.tv"],
        "vimeo": ["vimeo.com"],
        "dailymotion": ["dailymotion.com"],
        "reddit": ["reddit.com", "v.redd.it"],
        "pinterest": ["pinterest.com", "pin.it"],
        "linkedin": ["linkedin.com"],
        "spotify": ["open.spotify.com"],
        "bandcamp": ["bandcamp.com"],
    }
    
    for platform, domains in platforms.items():
        if any(domain in url for domain in domains):
            return platform
    return "unsupported"

async def extractAllLinks(url: str) -> Dict[str, Any]:
    ydlOpts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'no_check_certificate': True,
        'ignoreerrors': True,
        'writesubtitles': False,
        'writeautomaticsub': False,
        'writethumbnail': False,
        'writeinfojson': False,
        'writedescription': False,
        'writeannotations': False,
        'skip_download': True,
        'format_sort': ['res:720', 'ext:mp4:m4a'],
        'format_sort_force': False,
        'concurrent_fragment_downloads': 1,
        'retries': 3,
        'fragment_retries': 3,
        'http_chunk_size': 10485760,
        'extractor_retries': 2,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydlOpts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if 'entries' in info:
                entries = []
                for entry in info['entries'][:10]:
                    if entry:
                        entries.append(processSingleEntry(entry))
                
                return {
                    "type": "playlist",
                    "title": info.get('title', 'Unknown Playlist'),
                    "uploader": info.get('uploader', 'Unknown'),
                    "entryCount": len(info['entries']),
                    "entries": entries
                }
            else:
                return {
                    "type": "single",
                    **processSingleEntry(info)
                }
            
    except Exception as e:
        raise Exception(f"yt-dlp extraction failed: {str(e)}")

def processSingleEntry(entry: Dict[str, Any]) -> Dict[str, Any]:
    videoLinks = []
    audioLinks = []
    bestThumbnail = None
    
    if 'formats' in entry and entry['formats']:
        for fmt in entry['formats']:
            if not fmt.get('url'):
                continue
                
            linkData = {
                "url": fmt['url'],
                "formatId": fmt.get('format_id'),
                "ext": fmt.get('ext'),
                "filesize": fmt.get('filesize'),
                "quality": fmt.get('format_note', 'Unknown'),
            }
            
            if fmt.get('vcodec') != 'none' and fmt.get('acodec') != 'none':
                linkData.update({
                    "type": "videoAudio",
                    "width": fmt.get('width'),
                    "height": fmt.get('height'),
                    "fps": fmt.get('fps'),
                    "vbr": fmt.get('vbr'),
                    "abr": fmt.get('abr'),
                })
                videoLinks.append(linkData)
            elif fmt.get('vcodec') != 'none':
                linkData.update({
                    "type": "videoOnly",
                    "width": fmt.get('width'),
                    "height": fmt.get('height'),
                    "fps": fmt.get('fps'),
                    "vbr": fmt.get('vbr'),
                })
                videoLinks.append(linkData)
            elif fmt.get('acodec') != 'none':
                linkData.update({
                    "type": "audioOnly",
                    "abr": fmt.get('abr'),
                    "asr": fmt.get('asr'),
                })
                audioLinks.append(linkData)
    
    if 'thumbnails' in entry and entry['thumbnails']:
        maxResolution = 0
        for thumb in entry['thumbnails']:
            if thumb.get('url'):
                width = thumb.get('width', 0) or 0
                height = thumb.get('height', 0) or 0
                resolution = width * height
                
                if resolution > maxResolution:
                    maxResolution = resolution
                    bestThumbnail = {
                        "url": thumb['url'],
                        "width": width,
                        "height": height,
                        "id": thumb.get('id'),
                        "type": "thumbnail"
                    }
    
    videoLinks.sort(key=lambda x: (x.get('height', 0) or 0), reverse=True)
    audioLinks.sort(key=lambda x: (x.get('abr', 0) or 0), reverse=True)
    
    return {
        "id": entry.get('id'),
        "title": entry.get('title', 'Unknown Title'),
        "uploader": entry.get('uploader', 'Unknown'),
        "uploaderId": entry.get('uploader_id'),
        "uploadDate": entry.get('upload_date'),
        "duration": entry.get('duration'),
        "viewCount": entry.get('view_count'),
        "likeCount": entry.get('like_count'),
        "commentCount": entry.get('comment_count'),
        "description": entry.get('description', '')[:500] if entry.get('description') else '',
        "tags": entry.get('tags', [])[:10] if entry.get('tags') else [],
        "webpageUrl": entry.get('webpage_url'),
        
        "videoLinks": videoLinks,
        "audioLinks": audioLinks,
        "thumbnail": bestThumbnail,
        
        "bestVideoLink": videoLinks[0] if videoLinks else None,
        "bestAudioLink": audioLinks[0] if audioLinks else None,
        
        "totalFormats": len(videoLinks) + len(audioLinks),
        "hasVideo": len(videoLinks) > 0,
        "hasAudio": len(audioLinks) > 0,
        "hasThumbnail": bestThumbnail is not None,
    }
