from sqlalchemy.orm import Session
from ..auth import validateApiKey
import requests
from urllib.parse import urlparse
import socket
from bs4 import BeautifulSoup

async def run(params: dict, db: Session):
    await validateApiKey(params["apiKey"], db)
    url = params["url"]
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        response = requests.get(url, timeout=10, allow_redirects=True)
        if response.status_code != 200:
            return {"error": f"Failed to fetch URL. Status code: {response.status_code}"}
        
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        
        try:
            ip_address = socket.gethostbyname(hostname)
        except socket.gaierror:
            ip_address = "Unknown"
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title = soup.find('title')
        title_text = title.get_text().strip() if title else "No title found"
        
        meta_description = soup.find('meta', attrs={'name': 'description'})
        description = meta_description.get('content', '').strip() if meta_description else ""
        
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        keywords = meta_keywords.get('content', '').strip() if meta_keywords else ""
        
        meta_tags = {}
        for meta in soup.find_all('meta'):
            if meta.get('name'):
                meta_tags[meta.get('name')] = meta.get('content', '')
            elif meta.get('property'):
                meta_tags[meta.get('property')] = meta.get('content', '')
        
        headers = dict(response.headers)
        
        has_js = bool(soup.find_all('script'))
        has_forms = bool(soup.find_all('form'))
        has_ajax_indicators = any([
            'XMLHttpRequest' in response.text,
            'fetch(' in response.text,
            'axios' in response.text,
            'jQuery.ajax' in response.text,
            '$.ajax' in response.text
        ])
        
        is_dynamic = has_js or has_forms or has_ajax_indicators
        
        links = []
        for link in soup.find_all('a', href=True):
            links.append(link['href'])
        
        images = []
        for img in soup.find_all('img', src=True):
            images.append(img['src'])
        
        return {
            "url": response.url,
            "original_url": params["url"],
            "status_code": response.status_code,
            "title": title_text,
            "description": description,
            "keywords": keywords,
            "hostname": hostname,
            "ip_address": ip_address,
            "is_dynamic": is_dynamic,
            "website_type": "Dynamic" if is_dynamic else "Static",
            "has_javascript": has_js,
            "has_forms": has_forms,
            "content_length": len(response.content),
            "content_type": response.headers.get('content-type', ''),
            "encoding": response.encoding,
            "headers": headers,
            "meta_tags": meta_tags,
            "links_count": len(links),
            "images_count": len(images),
            "links": links[:50],
            "images": images[:20],
            "response_time_ms": response.elapsed.total_seconds() * 1000,
            "redirected": response.url != url,
            "final_url": response.url if response.url != url else None
        }
        
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}
